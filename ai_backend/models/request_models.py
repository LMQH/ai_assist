"""
请求数据模型
定义API请求和响应的数据结构
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class Message(BaseModel):
    """消息模型"""
    role: str  # "customer" or "agent"
    content: str
    sender: Optional[str] = None  # 发送者名称（支持群聊中的不同发送者）
    timestamp: Optional[float] = None  # 消息时间戳（可选，用于排序）


class SessionInfo(BaseModel):
    """会话信息"""
    id: str
    type: str  # "group" or "personal"
    is_group: bool
    group_name: Optional[str] = None
    phone: Optional[str] = None
    last_message_time: Optional[str] = None


class CustomerData(BaseModel):
    """客户数据"""
    type: str  # "group" or "personal"
    phone: Optional[str] = None
    basic_info: Dict[str, Any] = {}
    business_info: Dict[str, Any] = {}
    tags: List[str] = []
    service_history: List[Dict[str, Any]] = []
    group_name: Optional[str] = None
    member_count: Optional[str] = None


class SuggestionRequest(BaseModel):
    """AI建议请求"""
    customer_id: str
    conversation: List[Message]
    session_info: Optional[SessionInfo] = None
    customer_data: Optional[CustomerData] = None
    use_rag: Optional[bool] = True  # 是否使用RAG增强


class FeedbackRequest(BaseModel):
    """反馈请求"""
    customer_id: str
    conversation: List[Message]
    suggestion: str
    feedback: str  # "positive" or "negative"
    timestamp: Optional[int] = None


class AcceptSuggestionRequest(BaseModel):
    """采纳建议请求"""
    customer_id: str
    conversation: List[Message]
    suggestion: str  # 被采纳的AI建议内容
    session_info: Optional[SessionInfo] = None
    customer_data: Optional[CustomerData] = None
    timestamp: Optional[str] = None  # ISO格式的时间戳

