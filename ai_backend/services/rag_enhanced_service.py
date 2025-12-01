import os
import re
import json
from typing import List, Dict, Any, Optional
import logging
from dataclasses import dataclass
from enum import Enum

# 导入嵌入服务抽象层
from .embedding_service import (
    EmbeddingService,
    EmbeddingConfig,
    create_embedding_service
)

# 导入向量数据库服务抽象层
from .vector_db_service import (
    VectorDBService,
    VectorDBConfig,
    create_vector_db_service
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 设置httpx日志级别为WARNING，隐藏INFO级别的HTTP请求日志
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

class RAGStatus(Enum):
    """RAG系统状态"""
    INITIALIZING = "初始化中"
    READY = "就绪"
    ERROR = "错误"
    NO_KNOWLEDGE = "无知识库"

@dataclass
class RAGConfig:
    """RAG配置"""
    # 从config模块导入默认配置
    from config import (
        EMBEDDING_PROVIDER, EMBEDDING_MODEL, EMBEDDING_HOST,
        RAG_COLLECTION_NAME, RAG_N_SEARCH_RESULTS, RAG_SIMILARITY_THRESHOLD,
        RAG_DB_PATH, VECTOR_DB_PROVIDER, MILVUS_HOST, MILVUS_PORT,
        MILVUS_USER, MILVUS_PASSWORD, MILVUS_DATABASE
    )
    
    # 嵌入服务配置（向后兼容，保留旧字段）
    ollama_host: str = EMBEDDING_HOST
    embedding_model: str = EMBEDDING_MODEL
    
    # 新的嵌入服务配置（优先使用）
    embedding_provider: str = EMBEDDING_PROVIDER  # ollama, openai, dashscope, qwen
    embedding_service_config: Optional[EmbeddingConfig] = None
    
    # 向量数据库配置
    vector_db_provider: str = VECTOR_DB_PROVIDER  # chromadb, milvus
    vector_db_config: Optional[VectorDBConfig] = None
    
    # 其他配置
    collection_name: str = RAG_COLLECTION_NAME
    generation_model: str = "qwen2.5:7b"
    n_search_results: int = RAG_N_SEARCH_RESULTS  # 从知识库中检索的最相关文档数量
    similarity_threshold: float = RAG_SIMILARITY_THRESHOLD
    db_path: str = RAG_DB_PATH  # ChromaDB持久化存储路径或Milvus数据库名

class CustomerServiceRAG:
    """增强的客服RAG系统"""

    def __init__(self, config: RAGConfig = None):
        self.config = config or RAGConfig()
        self.embedding_service: Optional[EmbeddingService] = None
        self.vector_db_service: Optional[VectorDBService] = None
        self.status = RAGStatus.INITIALIZING
        self.knowledge_base_stats = {}
    
    def _initialize_embedding_service(self) -> bool:
        """初始化嵌入服务"""
        try:
            # 如果提供了自定义配置，使用自定义配置
            if self.config.embedding_service_config:
                embedding_config = self.config.embedding_service_config
            else:
                # 否则从旧配置构建（向后兼容）
                embedding_config = EmbeddingConfig(
                    provider=self.config.embedding_provider,
                    model=self.config.embedding_model,
                    host=self.config.ollama_host
                )
            
            logger.info(f"初始化嵌入服务: provider={embedding_config.provider}, model={embedding_config.model}")
            self.embedding_service = create_embedding_service(embedding_config)
            logger.info("✅ 嵌入服务初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 嵌入服务初始化失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise

    def _initialize_vector_db_service(self) -> bool:
        """初始化向量数据库服务"""
        try:
            # 如果提供了自定义配置，使用自定义配置
            if self.config.vector_db_config:
                vector_db_config = self.config.vector_db_config
            else:
                # 否则从config模块导入配置并构建
                from config import (
                    MILVUS_HOST, MILVUS_PORT, MILVUS_USER, 
                    MILVUS_PASSWORD, MILVUS_DATABASE
                )
                vector_db_config = VectorDBConfig(
                    provider=self.config.vector_db_provider,
                    collection_name=self.config.collection_name,
                    db_path=self.config.db_path,
                    milvus_host=MILVUS_HOST,
                    milvus_port=MILVUS_PORT,
                    milvus_user=MILVUS_USER,
                    milvus_password=MILVUS_PASSWORD,
                    milvus_database=MILVUS_DATABASE,
                )
            
            logger.info(f"初始化向量数据库服务: provider={vector_db_config.provider}, collection={vector_db_config.collection_name}")
            self.vector_db_service = create_vector_db_service(vector_db_config)
            logger.info("✅ 向量数据库服务初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 向量数据库服务初始化失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise

    def initialize(self) -> bool:
        """初始化RAG系统"""
        try:
            logger.info("初始化RAG系统...")
            
            # 初始化嵌入服务
            self._initialize_embedding_service()

            # 初始化向量数据库服务
            self._initialize_vector_db_service()

            # 获取嵌入向量维度（用于创建集合）
            embedding_dim = self.embedding_service.get_embedding_dimension()
            logger.info(f"嵌入向量维度: {embedding_dim}")

            # 检查现有知识库
            collection_exists = self.vector_db_service.collection_exists(self.config.collection_name)

            if collection_exists:
                count = self.vector_db_service.get_collection_count(self.config.collection_name)
                self.knowledge_base_stats = {
                    "collection_name": self.config.collection_name,
                    "total_entries": count,
                    "status": "已加载" if count > 0 else "空知识库"
                }
                logger.info(f"✓ 加载现有知识库: {self.knowledge_base_stats}")
                
                # 如果知识库已有数据，跳过自动加载
                if count > 0:
                    logger.info("✓ 知识库已有数据，跳过自动加载")
                else:
                    # 知识库为空，尝试加载
                    logger.info("知识库为空，开始自动加载...")
                    self._auto_load_knowledge_base()
            else:
                # 创建新集合
                success = self.vector_db_service.create_collection(
                    self.config.collection_name,
                    embedding_dim
                )
                if not success:
                    raise RuntimeError("创建集合失败")
                
                self.knowledge_base_stats = {
                    "collection_name": self.config.collection_name,
                    "total_entries": 0,
                    "status": "新创建"
                }
                logger.info(f"✓ 创建新知识库: {self.config.collection_name}")
                
                # 新创建的知识库，自动加载文件
                logger.info("新知识库，开始自动加载...")
                self._auto_load_knowledge_base()

            self.status = RAGStatus.READY
            return True

        except Exception as e:
            logger.error(f"初始化RAG系统失败: {e}")
            self.status = RAGStatus.ERROR
            return False

    def search_knowledge(self, query: str) -> Dict[str, Any]:
        """搜索知识库"""
        if self.status != RAGStatus.READY:
            return {"error": "RAG系统未就绪", "status": self.status.value}

        if self.knowledge_base_stats["total_entries"] == 0:
            return {"error": "知识库为空", "status": RAGStatus.NO_KNOWLEDGE.value}

        try:
            # 检查查询是否为空
            if not query or len(query.strip()) < 2:
                logger.warning(f"查询过短或为空: '{query}'")
                return {"error": "查询过短", "total_results": 0}

            logger.info(f"搜索知识库: '{query}'")

            # 使用嵌入服务生成查询嵌入向量
            if not self.embedding_service or not self.embedding_service.is_initialized():
                return {"error": "嵌入服务未初始化", "total_results": 0}
            
            query_embedding = self.embedding_service.embed(query)
            
            # 检查嵌入向量是否有效
            if not query_embedding or len(query_embedding) == 0:
                logger.error("生成的查询嵌入向量为空")
                return {"error": "嵌入向量生成失败", "total_results": 0}

            logger.info(f"查询嵌入向量维度: {len(query_embedding)}")

            # 使用向量数据库服务搜索相关文档
            results = self.vector_db_service.search(
                collection_name=self.config.collection_name,
                query_embeddings=[query_embedding],
                n_results=self.config.n_search_results
            )

            # 应用 Parent-Child 召回逻辑
            # 注意：向量搜索已经过滤，只检索 child 和 structure 类型
            # 这里只需要处理 child 类型，将其替换为 parent 内容
            collection_name = results.get('_collection_name')
            if collection_name:
                from .parent_child_retrieval import create_parent_child_retrieval
                parent_child_retrieval = create_parent_child_retrieval(collection_name)
                
                # 准备待处理的项
                items_to_resolve = list(zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0] if 'distances' in results else [0] * len(results['documents'][0])
                ))
                
                # 批量解析 parent 内容
                # 只有 child 类型会被处理，structure 类型直接返回
                resolved_items = parent_child_retrieval.resolve_multiple_items(items_to_resolve)
                
                # 统计处理情况
                child_count = sum(1 for item in resolved_items 
                                 if item[1].get('chunk_method') == 'parent_child_split' 
                                 and item[1].get('pc_type') == 'child')
                structure_count = sum(1 for item in resolved_items 
                                     if item[1].get('chunk_method') == 'structure')
                
                # 更新结果
                resolved_docs = [item[0] for item in resolved_items]
                resolved_metas = [item[1] for item in resolved_items]
                resolved_distances = [item[2] for item in resolved_items]
                
                results['documents'][0] = resolved_docs
                results['metadatas'][0] = resolved_metas
                results['distances'][0] = resolved_distances
                
                logger.info(f"[检索结果] 共 {len(resolved_items)} 条: child类型 {child_count} 条, structure类型 {structure_count} 条")
                if child_count > 0:
                    logger.info(f"[Parent-Child召回] 已处理 {child_count} 条 child，返回对应的 parent 内容")

            # 格式化结果
            knowledge_items = []
            logger.info("=" * 80)
            logger.info(f"[RAG检索详情] 找到 {len(results['documents'][0])} 条相关文档:")
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0], 
                results['metadatas'][0],
                results['distances'][0] if 'distances' in results else [0] * len(results['documents'][0])
            )):
                # 检查是否使用了 parent 内容
                is_parent_resolved = metadata.get('_is_parent_resolved', False)
                chunk_method = metadata.get('chunk_method', '')
                pc_type = metadata.get('pc_type', '')
                
                item = {
                    "rank": i + 1,
                    "content": doc,
                    "source": metadata.get('source', metadata.get('file_name', '未知')),
                    "type": metadata.get('type', 'unknown'),
                    "question": metadata.get('question', ''),
                    "title": metadata.get('title', ''),
                    "distance": float(distance) if distance else 0.0,
                    "chunk_method": chunk_method,
                    "pc_type": pc_type
                }
                
                # 如果使用了 parent 内容，添加标记
                if is_parent_resolved:
                    item["_parent_resolved"] = True
                    item["_child_id"] = metadata.get('_child_id')
                    item["_parent_id"] = metadata.get('_parent_id')
                
                knowledge_items.append(item)
                
                # 记录每条检索到的知识内容
                log_prefix = f"  [{i + 1}]"
                if is_parent_resolved:
                    log_prefix += " [Parent-Child召回]"
                logger.info(f"{log_prefix} 来源: {item['source']} | 类型: {item['type']} | 相似度: {1 - item['distance']:.4f}")
                
                if chunk_method == 'parent_child_split':
                    logger.info(f"      分块方法: {chunk_method} | PC类型: {pc_type}")
                    if is_parent_resolved:
                        logger.info(f"      ✓ 已使用 parent 内容 (Parent ID: {metadata.get('_parent_id')}, Child ID: {metadata.get('_child_id')})")
                
                if item['title']:
                    logger.info(f"      标题: {item['title']}")
                if item['question']:
                    logger.info(f"      问题: {item['question']}")
                content_preview = doc[:300] + "..." if len(doc) > 300 else doc
                logger.info(f"      内容: {content_preview}")
            logger.info("=" * 80)

            return {
                "query": query,
                "total_results": len(knowledge_items),
                "knowledge_items": knowledge_items
            }

        except Exception as e:
            logger.error(f"搜索知识库失败: {e}")
            return {"error": f"搜索失败: {str(e)}"}

    def format_knowledge_for_prompt(self, knowledge_data: Dict[str, Any]) -> str:
        """格式化知识为提示词友好的格式"""
        if "error" in knowledge_data:
            return ""

        if knowledge_data["total_results"] == 0:
            return ""

        knowledge_text = "【RAG知识库信息】\n"

        for item in knowledge_data["knowledge_items"]:
            if item["type"] == "qa_pair":
                knowledge_text += f"📋 标准问答:\n"
                knowledge_text += f"问题: {item['question']}\n"
                knowledge_text += f"答案: {item['content']}\n\n"
            else:
                knowledge_text += f"📄 {item['title']} (来源: {item['source']}):\n"
                knowledge_text += f"{item['content']}\n\n"

        return knowledge_text

    def get_status(self) -> Dict[str, Any]:
        """获取RAG系统状态"""
        embedding_info = {}
        if self.embedding_service:
            embedding_info = {
                "provider": self.config.embedding_provider,
                "model": self.config.embedding_model,
                "initialized": self.embedding_service.is_initialized(),
                "dimension": self.embedding_service.get_embedding_dimension() if self.embedding_service.is_initialized() else None
            }
        
        vector_db_info = {}
        if self.vector_db_service:
            vector_db_info = {
                "provider": self.config.vector_db_provider,
                "initialized": self.vector_db_service.is_initialized(),
                "collection_name": self.config.collection_name
            }
        
        return {
            "status": self.status.value,
            "knowledge_base": self.knowledge_base_stats,
            "embedding_service": embedding_info,
            "vector_db_service": vector_db_info,
            "config": {
                "embedding_model": self.config.embedding_model,
                "embedding_provider": self.config.embedding_provider,
                "vector_db_provider": self.config.vector_db_provider,
                "generation_model": self.config.generation_model,
                "n_search_results": self.config.n_search_results
            }
        }



class MarkdownProcessor:
    """Markdown文档处理器"""

    def __init__(self):
        pass

    def extract_text_from_markdown(self, file_path: str) -> List[Dict[str, Any]]:
        """从Markdown文件提取结构化文本块"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        chunks = []

        # 处理问答对格式的文档（农行小豆常见问题）
        if "常见问题" in file_path or "问题：" in content:
            chunks.extend(self._extract_qa_pairs(content, file_path))
        else:
            # 处理普通Markdown文档
            chunks.extend(self._extract_markdown_sections(content, file_path))

        return chunks

    def _extract_qa_pairs(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """提取问答对"""
        chunks = []

        # 更灵活的正则表达式匹配问答对
        qa_patterns = [
            r'# 问题：(.*?)\n\n答案：(.*?)(?=\n\n# 问题：|$)',
            r'## 问题：(.*?)\n\n答案：(.*?)(?=\n\n# 问题：|\n\n## 问题：|$)'
        ]

        for pattern in qa_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            for i, (question, answer) in enumerate(matches):
                question = self._clean_text(question.strip())
                answer = self._clean_text(answer.strip())

                if question and answer:
                    qa_content = f"问题：{question}\n答案：{answer}"
                    chunks.append({
                        "id": f"qa_{os.path.basename(file_path)}_{i}",
                        "content": qa_content,
                        "metadata": {
                            "source": os.path.basename(file_path),
                            "type": "qa_pair",
                            "question": question,
                            "chunk_id": f"qa_{os.path.basename(file_path)}_{i}"
                        }
                    })

        return chunks

    def _extract_markdown_sections(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """提取Markdown章节"""
        chunks = []

        lines = content.split('\n')
        sections = []
        current_section = ""
        current_title = "文档开始"

        for line in lines:
            if line.strip().startswith('#'):
                # 保存之前的section
                if current_section.strip():
                    sections.append({
                        "title": current_title,
                        "content": self._clean_text(current_section.strip())
                    })
                # 开始新的section
                current_title = line.strip('#').strip()
                current_section = line + '\n'
            else:
                current_section += line + '\n'

        # 保存最后一个section
        if current_section.strip():
            sections.append({
                "title": current_title,
                "content": self._clean_text(current_section.strip())
            })

        # 创建chunks，过滤太短的内容
        for i, section in enumerate(sections):
            if len(section["content"]) > 50:  # 只保留有意义的内容
                chunks.append({
                    "id": f"section_{os.path.basename(file_path)}_{i}",
                    "content": section["content"],
                    "metadata": {
                        "source": os.path.basename(file_path),
                        "type": "section",
                        "title": section["title"],
                        "chunk_id": f"section_{os.path.basename(file_path)}_{i}"
                    }
                })

        return chunks

    def _clean_text(self, text: str) -> str:
        """清理文本"""
        # 移除图片标记
        text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
        # 移除链接但保留文本
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        # 处理表格 - 保留内容但简化格式
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            if '|' in line and not line.strip().startswith('|'):
                # 可能是表格行，保留文本内容
                cells = line.split('|')
                cleaned_cells = [cell.strip() for cell in cells if cell.strip()]
                if cleaned_cells:
                    cleaned_lines.append(' | '.join(cleaned_cells))
            else:
                cleaned_lines.append(line)

        text = '\n'.join(cleaned_lines)

        # 清理多余空白
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        return text

# 为 CustomerServiceRAG 类添加知识库加载方法
def _auto_load_knowledge_base(self):
    """自动加载知识库文件"""
    try:
        logger.info("检查并加载知识库文件...")

        # 定义知识库文件路径
        kb_files = [
            "./data/外-农行小豆客户常见问题.md",
            "./data/38女神节营销活动策划方案V4.0.md"
        ]

        processor = MarkdownProcessor()
        total_loaded = 0

        for file_path in kb_files:
            if os.path.exists(file_path):
                logger.info(f"加载文件: {os.path.basename(file_path)}")
                chunks = processor.extract_text_from_markdown(file_path)

                logger.info(f"开始向量化 {len(chunks)} 个知识条目...")

                for i, chunk in enumerate(chunks):
                    try:
                        # 显示进度（每10个条目显示一次，或第一个和最后一个）
                        if (i + 1) % 10 == 0 or i == 0 or i == len(chunks) - 1:
                            logger.info(f"正在处理第 {i + 1}/{len(chunks)} 个条目...")
                            # 记录加载的内容（前3个和每10个）
                            if i < 3 or (i + 1) % 10 == 0:
                                content_preview = chunk['content'][:200] + "..." if len(chunk['content']) > 200 else chunk['content']
                                logger.info(f"[知识库加载] 条目 {i + 1} 内容预览: {content_preview}")
                        
                        # 使用嵌入服务生成嵌入向量
                        if not self.embedding_service or not self.embedding_service.is_initialized():
                            raise RuntimeError("嵌入服务未初始化")
                        
                        embedding = self.embedding_service.embed(chunk['content'])

                        # 添加到向量数据库
                        success = self.vector_db_service.add_documents(
                            collection_name=self.config.collection_name,
                            ids=[chunk['metadata']['chunk_id']],
                            embeddings=[embedding],
                            documents=[chunk['content']],
                            metadatas=[chunk['metadata']]
                        )
                        
                        if not success:
                            raise RuntimeError("添加文档到向量数据库失败")

                        total_loaded += 1

                    except Exception as e:
                        logger.warning(f"加载知识条目 {i + 1} 失败: {e}")
                        import traceback
                        logger.debug(traceback.format_exc())

                logger.info(f"✅ 完成加载 {len(chunks)} 个知识条目")
            else:
                logger.warning(f"文件不存在: {file_path}")

        if total_loaded > 0:
            logger.info(f"✅ 知识库加载完成，共加载 {total_loaded} 个条目")
            # 更新统计信息
            self.knowledge_base_stats["total_entries"] = total_loaded
            self.knowledge_base_stats["status"] = "已加载"
        else:
            logger.warning("⚠️ 没有加载任何知识条目")

    except Exception as e:
        logger.error(f"知识库加载失败: {e}")

# 将方法动态添加到类中
CustomerServiceRAG._auto_load_knowledge_base = _auto_load_knowledge_base


# 全局RAG系统实例
_rag_system = None
_rag_initializing = False

def get_rag_system() -> CustomerServiceRAG:
    """获取RAG系统实例（单例）"""
    global _rag_system, _rag_initializing
    
    # 如果正在初始化，等待完成
    if _rag_initializing:
        logger.warning("RAG系统正在初始化中，请稍候...")
        # 简单等待，最多等待5秒
        import time
        for _ in range(50):  # 50次 * 0.1秒 = 5秒
            time.sleep(0.1)
            if _rag_system and _rag_system.status != RAGStatus.INITIALIZING:
                break
        if _rag_system and _rag_system.status == RAGStatus.INITIALIZING:
            logger.warning("RAG系统初始化超时，返回当前状态")
    
    if _rag_system is None:
        _rag_initializing = True
        try:
            logger.info("创建RAG系统实例...")
            _rag_system = CustomerServiceRAG()
            logger.info("开始初始化RAG系统...")
            success = _rag_system.initialize()
            if not success:
                logger.error("RAG系统初始化失败，但继续返回实例（可能无法使用）")
        except Exception as e:
            logger.error(f"RAG系统初始化异常: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # 即使初始化失败，也返回实例，但状态会是ERROR
            if _rag_system is None:
                _rag_system = CustomerServiceRAG()
                _rag_system.status = RAGStatus.ERROR
        finally:
            _rag_initializing = False
    
    return _rag_system

if __name__ == "__main__":
    # 测试代码
    print("测试RAG系统...")

    # 初始化
    rag = get_rag_system()
    print(f"RAG系统状态: {rag.get_status()}")