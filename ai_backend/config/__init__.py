"""
配置模块
包含所有配置常量
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# Excel数据配置
# 支持两种方式：
# 1. 文件路径：直接指定Excel文件，如 "./历史会话导出2025-11-051762328066536.xlsx"
# 2. 文件夹路径：指定包含Excel文件的文件夹，会自动加载文件夹下所有.xlsx和.xls文件并合并
EXCEL_FILE_PATH = "./excel_data/"

# Excel列名映射配置（从JSON文件加载）
EXCEL_COLUMN_MAPPING = {}
_mapping_file = Path(__file__).parent / "excel_column_mapping.json"
if _mapping_file.exists():
    try:
        with open(_mapping_file, 'r', encoding='utf-8') as f:
            EXCEL_COLUMN_MAPPING = json.load(f)
    except Exception as e:
        print(f"警告: 加载Excel列名映射配置失败: {e}")
        EXCEL_COLUMN_MAPPING = {}

# OpenAI配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# ========== 向量化配置 ==========
# 嵌入服务配置
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "ollama")  # ollama, openai, dashscope, qwen
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
EMBEDDING_HOST = os.getenv("EMBEDDING_HOST", "http://172.31.198.110:11434")  # Ollama服务地址或DashScope base_url
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", None)  # OpenAI/DashScope等服务的API密钥
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", None)  # DashScope API密钥（如果未设置EMBEDDING_API_KEY，会使用此值）
EMBEDDING_TIMEOUT = int(os.getenv("EMBEDDING_TIMEOUT", "30"))  # 超时时间（秒）
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", 0)) or None  # 向量维度（仅对支持自定义维度的模型有效，如DashScope text-embedding-v4，设置为2048可获得2048维向量）

# RAG配置
RAG_COLLECTION_NAME = os.getenv("RAG_COLLECTION_NAME", "customer_service_kb")
RAG_N_SEARCH_RESULTS = int(os.getenv("RAG_N_SEARCH_RESULTS", "3"))  # 检索结果数量
RAG_SIMILARITY_THRESHOLD = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.7"))  # 相似度阈值
RAG_DB_PATH = os.getenv("RAG_DB_PATH", "./chroma_db")  # ChromaDB持久化存储路径

# 向量数据库配置
VECTOR_DB_PROVIDER = os.getenv("VECTOR_DB_PROVIDER", "chromadb")  # chromadb, milvus

# Milvus配置
MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = int(os.getenv("MILVUS_PORT", "19530"))
MILVUS_USER = os.getenv("MILVUS_USER", None)  # 可选，如果Milvus启用了认证
MILVUS_PASSWORD = os.getenv("MILVUS_PASSWORD", None)  # 可选
MILVUS_DATABASE = os.getenv("MILVUS_DATABASE", None)  # 可选，指定使用的数据库

# 日志配置
LOG_DIR = os.getenv("LOG_DIR", "./logs")
LOG_FILE = os.path.join(LOG_DIR, "app.log")
LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", "10485760"))  # 10MB
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))  # 保留5个备份文件

# 确保日志目录存在
os.makedirs(LOG_DIR, exist_ok=True)

__all__ = [
    "EXCEL_FILE_PATH", 
    "EXCEL_COLUMN_MAPPING",
    # OpenAI配置
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "OPENAI_MODEL",
    # 向量化配置
    "EMBEDDING_PROVIDER",
    "EMBEDDING_MODEL",
    "EMBEDDING_HOST",
    "EMBEDDING_API_KEY",
    "DASHSCOPE_API_KEY",
    "EMBEDDING_TIMEOUT",
    "EMBEDDING_DIMENSIONS",
    # RAG配置
    "RAG_COLLECTION_NAME",
    "RAG_N_SEARCH_RESULTS",
    "RAG_SIMILARITY_THRESHOLD",
    "RAG_DB_PATH",
    # 向量数据库配置
    "VECTOR_DB_PROVIDER",
    "MILVUS_HOST",
    "MILVUS_PORT",
    "MILVUS_USER",
    "MILVUS_PASSWORD",
    "MILVUS_DATABASE",
    # 日志配置
    "LOG_DIR",
    "LOG_FILE",
    "LOG_MAX_BYTES",
    "LOG_BACKUP_COUNT",
]

