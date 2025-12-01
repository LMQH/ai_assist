"""
服务层模块
包含RAG、嵌入服务等核心业务服务
"""

from .embedding_service import (
    EmbeddingService,
    EmbeddingConfig,
    OllamaEmbeddingService,
    OpenAIEmbeddingService,
    DashScopeEmbeddingService,
    create_embedding_service
)

from .rag_enhanced_service import (
    RAGStatus,
    RAGConfig,
    CustomerServiceRAG,
    get_rag_system
)

__all__ = [
    # 嵌入服务
    "EmbeddingService",
    "EmbeddingConfig",
    "OllamaEmbeddingService",
    "OpenAIEmbeddingService",
    "DashScopeEmbeddingService",
    "create_embedding_service",
    # RAG服务
    "RAGStatus",
    "RAGConfig",
    "CustomerServiceRAG",
    "get_rag_system",
]

