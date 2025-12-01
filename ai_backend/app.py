"""
FastAPI应用主文件
简洁清晰的结构
"""
import time
import logging
import traceback
from datetime import datetime
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

# 导入配置
from config import (
    OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL,
    EXCEL_FILE_PATH, LOG_FILE, LOG_MAX_BYTES, LOG_BACKUP_COUNT
)

# 导入模型
from models import (
    SuggestionRequest, FeedbackRequest, AcceptSuggestionRequest
)

# 导入服务
from services import get_rag_system

# 导入工具函数
from utils import (
    conversation_to_text, build_context_prompt,
    parse_suggestion, load_excel_data, reload_excel_data,
    build_suggestion_prompt,
    extract_session_ids_from_conversation,
    find_session_data_by_id
)

# 加载环境变量
load_dotenv()

# 配置日志
# 创建日志格式
log_format = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
date_format = '%Y-%m-%d %H:%M:%S'

# 配置根日志记录器
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# 清除已有的处理器
root_logger.handlers.clear()

# 控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(log_format, date_format))
root_logger.addHandler(console_handler)

# 文件处理器（带轮转）
file_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=LOG_MAX_BYTES,
    backupCount=LOG_BACKUP_COUNT,
    encoding='utf-8'
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(log_format, date_format))
root_logger.addHandler(file_handler)

logger = logging.getLogger(__name__)
logger.info(f"日志文件: {LOG_FILE}")

# 设置第三方库日志级别
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

# 创建FastAPI应用
app = FastAPI(title="CS Assist AI Backend")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 初始化OpenAI客户端
if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY in .env")
client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    request_id = f"{int(time.time() * 1000)}"
    
    logger.info(f"[请求开始] ID={request_id} | {request.method} {request.url.path} | "
                f"客户端={request.client.host if request.client else 'unknown'}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"[请求完成] ID={request_id} | 状态码={response.status_code} | "
                    f"耗时={process_time:.3f}秒")
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"[请求异常] ID={request_id} | 异常={str(e)} | 耗时={process_time:.3f}秒")
        logger.error(f"[异常堆栈] ID={request_id} | {traceback.format_exc()}")
        raise


# ========== 路由 ==========

@app.post("/suggest")
async def suggest_reply(request: SuggestionRequest):
    """AI建议接口"""
    request_start_time = time.time()
    logger.info("=" * 80)
    logger.info("[AI建议请求] 收到新的建议请求")
    logger.info(f"[AI建议请求] 客户ID: {request.customer_id}")
    logger.info(f"[AI建议请求] 使用RAG增强: {request.use_rag}")
    
    try:
        # 记录对话内容
        logger.info("=" * 80)
        logger.info("[对话内容] 完整对话记录:")
        for i, msg in enumerate(request.conversation, 1):
            role_name = "客服" if msg.role == "agent" else "客户"
            sender_info = f" ({msg.sender})" if msg.sender else ""
            logger.info(f"  [{i}] {role_name}{sender_info}: {msg.content}")
        logger.info("=" * 80)
        
        # 构建基础上下文（先不包含Excel和RAG信息）
        context_info = build_context_prompt(request.session_info, request.customer_data)
        conversation_text = conversation_to_text(request.conversation)
        logger.debug(f"[上下文信息] 基础上下文: {context_info}")
        
        # 提取客户最新问题
        customer_last_message = ""
        customer_last_role = ""
        if request.conversation:
            # 从后往前找第一条客户消息
            for msg in reversed(request.conversation):
                if msg.role == "customer" or msg.role == "群聊成员":
                    customer_last_message = msg.content
                    customer_last_role = msg.role
                    # 清理消息内容，移除用户名前缀
                    if ": " in customer_last_message and not customer_last_message.startswith("客户:"):
                        parts = customer_last_message.split(": ", 1)
                        if len(parts) > 1:
                            customer_last_message = parts[1].strip()
                    break
        
        if not customer_last_message and request.conversation:
            # 如果没找到客户消息，使用最后一条消息
            last_msg = request.conversation[-1]
            customer_last_message = last_msg.content
            customer_last_role = last_msg.role
        
        logger.info(f"[客户最新问题] 角色: {customer_last_role}, 内容: '{customer_last_message}'")
        
        # 查询Excel中的历史会话数据
        excel_search_start = time.time()
        
        # 优先从对话历史中提取会话ID
        conversation_session_ids = extract_session_ids_from_conversation(request.conversation)
        logger.info(f"[Excel查询] 从对话历史中提取到 {len(conversation_session_ids)} 个会话ID: {conversation_session_ids}")
        
        # 尝试匹配对话历史中的会话ID
        matched_session_data = None
        for session_id in conversation_session_ids:
            logger.debug(f"[Excel查询] 尝试匹配会话ID: {session_id}")
            session_data = find_session_data_by_id(session_id)
            if session_data:
                logger.info(f"[Excel查询] ✅ 在Excel中找到对话历史中的会话ID {session_id} 的数据")
                matched_session_data = session_data
                break
            else:
                logger.debug(f"[Excel查询] ❌ 会话ID {session_id} 在Excel中未找到")
        
        # 如果对话历史中没有匹配的，再尝试使用请求中的会话ID
        if not matched_session_data:
            session_id_to_match = request.session_info.id if request.session_info else request.customer_id
            if session_id_to_match:
                logger.info(f"[Excel查询] 对话历史中无匹配，尝试使用请求中的会话ID: {session_id_to_match}")
                matched_session_data = find_session_data_by_id(session_id_to_match)
                if matched_session_data: # 如果找到，则记录日志
                    logger.info(f"[Excel查询] ✅ 在Excel中找到请求中的会话ID {session_id_to_match} 的数据")
                else: # 如果未找到，则记录日志
                    logger.info(f"[Excel查询] ❌ 未找到会话ID {session_id_to_match} 的Excel数据")
            else:
                logger.warning("[Excel查询] 没有可用的会话ID进行匹配")
        
        excel_search_time = time.time() - excel_search_start
        logger.debug(f"[Excel查询] Excel查询耗时: {excel_search_time:.3f}秒")
        
        # 构建Excel上下文信息
        excel_info = ""
        if matched_session_data:
            excel_info = "\n".join([
                "【历史会话数据】",
                f"会话ID: {matched_session_data['session_id']}",
                f"用户唯一标识: {matched_session_data['user_unique_id']}",
                f"手机号: {matched_session_data['phone']}",
                f"客户标签: {matched_session_data['customer_tags']}",
                f"问题分类: {matched_session_data['first_category']}",
                f"会话开始时间: {matched_session_data['start_time']}",
                f"会话结束时间: {matched_session_data['end_time']}",
                f"对话回合数: {matched_session_data.get('dialogue_rounds', '')}",
                f"会话结束原因: {matched_session_data.get('session_end_reason', '')}",
                f"评价结果: {matched_session_data.get('evaluation_status', '')}",
            ])
            
            # 添加历史消息摘要
            if 'recent_messages' in matched_session_data and matched_session_data['recent_messages']:
                excel_info += "\n最近历史对话摘要:"
                # 只显示前3条消息作为参考
                for msg in matched_session_data['recent_messages'][:3]:
                    if msg.strip() and not msg.startswith('{') and not msg.startswith('20'):  # 过滤掉JSON和时间戳
                        excel_info += f"\n  - {msg.strip()}"
            
            logger.info(f"[Excel查询] Excel上下文信息长度: {len(excel_info)} 字符")
            logger.debug(f"[Excel查询] Excel上下文内容: {excel_info[:200]}...")
        else:
            logger.info("[Excel查询] 对话历史和请求中都未找到匹配的Excel数据")
        
        # RAG增强
        rag_knowledge = ""
        knowledge_data = None
        rag_similarity_warning = ""
        rag_enhanced = False # 是否使用RAG增强
        rag_status = {}
        if request.use_rag and customer_last_message:
            try:
                rag_system = get_rag_system()
                if rag_system.status.value == "就绪":
                    logger.info(f"[RAG搜索] 搜索查询: '{customer_last_message}'")
                    knowledge_data = rag_system.search_knowledge(customer_last_message)
                    
                    if knowledge_data.get("total_results", 0) > 0:
                        logger.info(f"[RAG检索] ✅ 找到 {knowledge_data['total_results']} 条相关知识")
                        
                        # 检查相似度，如果太低则警告
                        knowledge_items = knowledge_data.get("knowledge_items", [])
                        if knowledge_items:
                            # 获取最高相似度的结果
                            max_similarity = 1.0 - min([item.get("distance", 1.0) for item in knowledge_items])
                            logger.info(f"[RAG相似度] 最高相似度: {max_similarity:.4f}")
                            
                            # 如果相似度太低，添加警告
                            if max_similarity < 0.3:
                                rag_similarity_warning = f"\n⚠️ 注意：检索到的知识库内容与客户问题相似度较低（{max_similarity:.2%}），可能不完全匹配，请优先根据客户的具体问题回答。"
                                logger.warning(f"[RAG相似度] ⚠️ 相似度较低: {max_similarity:.4f}，可能不匹配")
                        
                        rag_knowledge = rag_system.format_knowledge_for_prompt(knowledge_data)
                        if rag_knowledge:
                            logger.info("=" * 80)
                            logger.info("[RAG知识内容] 检索到的知识库内容:")
                            logger.info(rag_knowledge)
                            logger.info("=" * 80)
                            # 注意：不要在这里添加到context_info，让prompt_builder统一处理
                            rag_enhanced = True
                            rag_status = rag_system.get_status()
                        else:
                            logger.warning("[RAG检索] ⚠️ 知识库内容为空")
                    else:
                        logger.info("[RAG检索] ⚠️ 未找到相关知识")
            except Exception as e:
                logger.warning(f"[RAG搜索] 失败: {e}")
        
        # 构建提示词（使用提示词构建器）
        prompt = build_suggestion_prompt(
            context_info=context_info,
            conversation_text=conversation_text,
            customer_question=customer_last_message,
            rag_knowledge=rag_knowledge if rag_knowledge else None,
            rag_similarity_warning=rag_similarity_warning if rag_similarity_warning else None,
            excel_info=excel_info if excel_info else None
        )

        logger.info("=" * 80)
        logger.info("[AI提示词] 发送给AI的完整提示词:")
        logger.info(prompt)
        logger.info("=" * 80)

        # 调用OpenAI
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        
        raw_content = response.choices[0].message.content
        if not raw_content:
            raise ValueError("AI返回内容为空")
        
        suggestion = parse_suggestion(raw_content)
        
        logger.info("=" * 80)
        logger.info("[AI建议] 最终回复内容:")
        logger.info(suggestion)
        logger.info("=" * 80)
        
        # 记录请求信息用于调试
        session_id = request.session_info.id if request.session_info else 'unknown'
        session_type = 'group' if request.session_info and request.session_info.is_group else 'personal'
        total_time = time.time() - request_start_time
        
        logger.info(f"[AI建议请求] 会话ID: {session_id}")
        logger.info(f"[AI建议请求] 会话类型: {session_type}")
        logger.info(f"[AI建议请求] 生成的建议: '{suggestion}'")
        logger.info(f"[AI建议请求] 总耗时: {total_time:.3f}秒")
        
        # 构建返回结果
        result = {
            "suggestion": suggestion,
            "rag_enhanced": rag_enhanced,
            "method": "RAG_Enhanced" if rag_enhanced else "Original"
        }
        
        if rag_enhanced:
            result["rag_status"] = rag_status
            logger.info(f"[AI建议请求] ✅ RAG增强建议生成成功")
        else:
            logger.info(f"[AI建议请求] 📝 使用原始方法生成建议")
        
        logger.info("=" * 80)
        return result

    except Exception as e:
        total_time = time.time() - request_start_time
        logger.error(f"[AI建议请求] ❌ 失败: {e} | 耗时: {total_time:.3f}秒")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """反馈接口"""
    logger.info(f"[反馈] 收到反馈: {request.feedback}")
    # TODO: 保存反馈到数据库
    return {"status": "success", "message": "反馈已记录"}


@app.post("/accept")
async def accept_suggestion(request: AcceptSuggestionRequest):
    """采纳建议接口 - 记录用户采纳的AI建议"""
    request_start_time = time.time()
    logger.info("=" * 80)
    logger.info("[采纳建议] 收到采纳请求")
    logger.info(f"[采纳建议] 客户ID: {request.customer_id}")
    logger.info(f"[采纳建议] 建议内容: {request.suggestion[:100]}...")
    
    try:
        # 记录会话信息
        session_id = request.session_info.id if request.session_info else request.customer_id
        session_type = 'group' if request.session_info and request.session_info.is_group else 'personal'
        
        logger.info(f"[采纳建议] 会话ID: {session_id}")
        logger.info(f"[采纳建议] 会话类型: {session_type}")
        logger.info(f"[采纳建议] 对话消息数: {len(request.conversation)}")
        
        # 记录对话内容摘要
        if request.conversation:
            logger.info("[采纳建议] 对话内容摘要:")
            for i, msg in enumerate(request.conversation[-5:], 1):  # 只记录最后5条消息
                role_name = "客服" if msg.role == "agent" else "客户"
                sender_info = f" ({msg.sender})" if msg.sender else ""
                content_preview = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
                logger.info(f"  [{i}] {role_name}{sender_info}: {content_preview}")
        
        # 记录客户信息
        if request.customer_data:
            if request.customer_data.type == "group":
                logger.info(f"[采纳建议] 群聊名称: {request.customer_data.group_name or '未知'}")
            else:
                logger.info(f"[采纳建议] 客户手机: {request.customer_data.phone or '未知'}")
        
        # TODO: 这里可以保存到数据库或文件
        # 例如：保存到JSON文件、数据库、或用于后续的模型优化
        
        total_time = time.time() - request_start_time
        logger.info(f"[采纳建议] ✅ 采纳记录成功 | 耗时: {total_time:.3f}秒")
        logger.info("=" * 80)
        
        return {
            "status": "success",
            "message": "采纳记录已保存",
            "session_id": session_id,
            "timestamp": request.timestamp or datetime.now().isoformat()
        }
        
    except Exception as e:
        total_time = time.time() - request_start_time
        logger.error(f"[采纳建议] ❌ 失败: {e} | 耗时: {total_time:.3f}秒")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/rag/status")
async def get_rag_status():
    """获取RAG系统状态"""
    try:
        rag_system = get_rag_system()
        return rag_system.get_status()
    except Exception as e:
        logger.error(f"获取RAG状态失败: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/api/excel/reload")
async def reload_excel():
    """重新加载Excel数据（刷新缓存）"""
    try:
        logger.info("[API] 收到重新加载Excel数据的请求")
        reload_excel_data()
        
        from utils.excel_utils import excel_data, excel_data_loaded
        return {
            "status": "success",
            "message": "Excel数据已重新加载",
            "excel_data_loaded": excel_data_loaded,
            "excel_records": len(excel_data) if excel_data is not None and not excel_data.empty else 0,
            "excel_file_path": EXCEL_FILE_PATH
        }
    except Exception as e:
        logger.error(f"[API] 重新加载Excel数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"重新加载Excel数据失败: {str(e)}")


@app.on_event("startup")
async def startup_event():
    """启动时初始化"""
    logger.info("=" * 80)
    logger.info("=== 启动CS Assist AI Backend ===")
    logger.info(f"[启动] Excel文件路径: {EXCEL_FILE_PATH}")
    logger.info(f"[启动] OpenAI模型: {OPENAI_MODEL}")
    logger.info(f"[启动] OpenAI Base URL: {OPENAI_BASE_URL}")
    
    # 预加载Excel数据（强制重新加载，确保使用最新配置）
    reload_excel_data()
    
    logger.info("=== 后端服务启动完成 ===")
    logger.info("=" * 80)


@app.get("/health")
async def health_check():
    """健康检查"""
    from utils.excel_utils import excel_data, excel_data_loaded
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "CS Assist AI Backend",
        "excel_data_loaded": excel_data_loaded,
        "excel_records": len(excel_data) if excel_data is not None and not excel_data.empty else 0
    }


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "CS Assist AI Backend",
        "version": "1.0",
        "endpoints": {
            "suggest": "/suggest",
            "feedback": "/feedback",
            "rag_status": "/rag/status",
            "health": "/health"
        }
    }
