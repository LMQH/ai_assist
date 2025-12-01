"""
JSON处理工具函数
"""
from json_repair import loads as json_repair_loads


def extract_json_fragment(raw_content: str) -> str:
    """截取模型回复中的 JSON 片段。"""
    start = raw_content.find("{")
    end = raw_content.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("模型响应不包含 JSON 数据")
    return raw_content[start : end + 1]


def parse_suggestion(raw_content: str) -> str:
    """解析模型返回的 JSON，提取 suggestion 字段。"""
    fragment = extract_json_fragment(raw_content)
    try:
        payload = json_repair_loads(fragment)
    except Exception as error:
        raise ValueError("无法解析模型返回的 JSON") from error

    suggestion = payload.get("suggestion")
    if not isinstance(suggestion, str) or not suggestion.strip():
        raise ValueError("模型响应缺少 suggestion 字段")
    return suggestion.strip()

