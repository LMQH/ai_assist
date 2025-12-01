"""
提示词构建器
用于构建AI建议生成的提示词
"""
from typing import Optional


def build_suggestion_prompt(
    context_info: str,
    conversation_text: str,
    customer_question: str,
    rag_knowledge: Optional[str] = None,
    rag_similarity_warning: Optional[str] = None,
    excel_info: Optional[str] = None
) -> str:
    """
    构建AI建议生成的提示词
    
    Args:
        context_info: 基础上下文信息（会话信息、客户数据等）
        excel_info: Excel历史会话数据（可选）
        conversation_text: 对话历史文本（来自前端请求的对话历史）
        customer_question: 客户最新问题
        rag_knowledge: RAG检索到的知识库内容（可选）
        rag_similarity_warning: RAG相似度警告（可选） 
        
    Returns:
        完整的提示词
    """
    # 构建知识库部分
    # 注意：rag_knowledge 已经包含了【RAG知识库信息】标题（由 format_knowledge_for_prompt 生成）
    knowledge_section = ""
    if rag_knowledge:
        knowledge_section = rag_knowledge.strip()
        if rag_similarity_warning:
            knowledge_section += rag_similarity_warning
    
    # 动态构建各部分内容（只在有内容时添加，避免显示空章节）
    sections = []
    
    # 基础上下文信息（始终存在）
    sections.append(f"【基础上下文信息】\n{context_info}")
    
    # Excel历史会话数据（可选）
    if excel_info and excel_info.strip():
        sections.append(f"【历史会话数据】\n{excel_info.strip()}")
    
    # RAG知识库信息（可选）
    if knowledge_section:
        sections.append(knowledge_section)
    
    # 对话历史（始终存在）
    sections.append(f"【对话历史】\n{conversation_text}")
    
    # 拼接所有信息部分
    context_sections = "\n\n".join(sections)
    
    # 构建完整的提示词
    prompt = f"""你是一位经验丰富的专业客服助手。请仔细分析以下信息，为客服人员提供精准、实用的回复建议。

{context_sections}

---

【任务说明】
客户当前提出的问题是："{customer_question}"

请基于以上所有信息，生成一条针对该问题的客服回复建议。

【回复要求】
1. **精准性**：必须直接回应客户当前提出的最新问题，不要偏离主题或重复对话历史中的无关内容
2. **专业性**：使用礼貌、专业、友好的服务用语，体现良好的服务态度
3. **实用性**：提供具体、可操作的解决方案或建议，避免空泛的回复
4. **简洁性**：回复长度适中（建议50-200字），重点突出，易于理解

【输出格式】
请严格以JSON格式返回，格式如下：
{{
    "suggestion": "你的回复建议内容"
}}"""
    
    return prompt

