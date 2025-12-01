"""
对话处理工具函数
"""
from typing import List, Optional
from models.request_models import Message, SessionInfo, CustomerData


def conversation_to_text(conversation: List[Message]) -> str:
    """将对话列表转换成带角色标记的纯文本。"""
    # 如果消息有时间戳，按时间戳排序；否则保持原顺序
    if any(item.timestamp for item in conversation):
        # 按时间戳排序，没有时间戳的消息排在最后
        sorted_conversation = sorted(
            conversation,
            key=lambda x: (x.timestamp if x.timestamp is not None else float('inf'))
        )
    else:
        # 如果都没有时间戳，保持原顺序
        sorted_conversation = conversation

    lines = []
    for item in sorted_conversation:
        if item.role == "agent":
            speaker = "客服"
        else:
            speaker = "客户"
        lines.append(f"{speaker}: {item.content}")
    return "\n".join(lines)


def build_context_prompt(session_info: Optional[SessionInfo], customer_data: Optional[CustomerData]) -> str:
    """构建上下文提示信息。"""
    context_parts = []

    if session_info:
        if session_info.is_group and session_info.group_name:
            context_parts.append(f"当前会话类型：群聊（{session_info.group_name}）")
        elif not session_info.is_group and session_info.phone:
            context_parts.append(f"当前会话类型：个人会话（客户：{session_info.phone}）")
        else:
            context_parts.append(f"当前会话类型：{'群聊' if session_info.is_group else '个人会话'}")

    if customer_data:
        if customer_data.type == "group":
            if customer_data.group_name:
                context_parts.append(f"群名称：{customer_data.group_name}")
            if customer_data.member_count:
                context_parts.append(f"群成员数：{customer_data.member_count}")
            if customer_data.tags:
                context_parts.append(f"群标签：{', '.join(customer_data.tags)}")
        else:
            # 个人客户信息
            if customer_data.basic_info:
                basic_info = []
                for key, value in customer_data.basic_info.items():
                    if value:
                        basic_info.append(f"{key}：{value}")
                if basic_info:
                    context_parts.append(f"客户基本信息：{'; '.join(basic_info)}")

            if customer_data.business_info:
                business_info = []
                for key, value in customer_data.business_info.items():
                    if value:
                        business_info.append(f"{key}：{value}")
                if business_info:
                    context_parts.append(f"业务信息：{'; '.join(business_info)}")

            if customer_data.tags:
                context_parts.append(f"客户标签：{', '.join(customer_data.tags)}")

            if customer_data.service_history:
                recent_history = customer_data.service_history[:3]  # 最近3条记录
                history_summary = []
                for record in recent_history:
                    if record.get("time") and record.get("summary"):
                        history_summary.append(f"{record['time']} - {record['summary']}")
                if history_summary:
                    context_parts.append(f"最近服务记录：{'; '.join(history_summary)}")

    return "\n".join(context_parts) if context_parts else "无额外上下文信息"

