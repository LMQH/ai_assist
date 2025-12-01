# 嵌入服务抽象层使用说明

## 概述

嵌入服务已从 RAG 系统中抽象出来，成为一个独立的模块。这样可以：
- 灵活切换不同的嵌入服务提供者（Ollama、OpenAI等）
- 便于测试和维护
- 支持未来扩展新的嵌入服务

## 架构

```
embedding_service.py          # 抽象层和实现
├── EmbeddingService (抽象基类)
├── OllamaEmbeddingService    # Ollama实现
├── OpenAIEmbeddingService    # OpenAI实现（预留）
└── create_embedding_service() # 工厂函数

rag_enhanced_service.py        # RAG系统（使用嵌入服务）
└── CustomerServiceRAG
    └── 使用 EmbeddingService 接口
```

## 使用方式

### 方式1：使用默认配置（向后兼容）

```python
from rag_enhanced_service import CustomerServiceRAG, RAGConfig

# 使用默认配置（自动使用Ollama）
rag = CustomerServiceRAG()
rag.initialize()
```

### 方式2：自定义嵌入服务配置

```python
from rag_enhanced_service import CustomerServiceRAG, RAGConfig
from embedding_service import EmbeddingConfig

# 创建自定义嵌入服务配置
embedding_config = EmbeddingConfig(
    provider="ollama",
    model="nomic-embed-text",
    host="http://172.31.198.110:11434"
)

# 创建RAG配置
rag_config = RAGConfig(
    embedding_provider="ollama",
    embedding_service_config=embedding_config
)

# 初始化RAG系统
rag = CustomerServiceRAG(config=rag_config)
rag.initialize()
```

### 方式3：直接使用嵌入服务

```python
from embedding_service import EmbeddingConfig, create_embedding_service

# 创建配置
config = EmbeddingConfig(
    provider="ollama",
    model="nomic-embed-text",
    host="http://localhost:11434"
)

# 创建服务
embedding_service = create_embedding_service(config)

# 使用服务
text = "这是一个测试文本"
embedding = embedding_service.embed(text)
print(f"嵌入向量维度: {len(embedding)}")

# 批量处理
texts = ["文本1", "文本2", "文本3"]
embeddings = embedding_service.embed_batch(texts)
```

## 切换不同的嵌入服务

### 切换到 OpenAI

```python
from embedding_service import EmbeddingConfig
from rag_enhanced_service import RAGConfig, CustomerServiceRAG

# 配置OpenAI嵌入服务
embedding_config = EmbeddingConfig(
    provider="openai",
    model="text-embedding-ada-002",
    api_key="your-api-key"
)

rag_config = RAGConfig(
    embedding_provider="openai",
    embedding_service_config=embedding_config
)

rag = CustomerServiceRAG(config=rag_config)
rag.initialize()
```

## 配置说明

### EmbeddingConfig

```python
@dataclass
class EmbeddingConfig:
    provider: str = "ollama"      # 服务提供者: "ollama", "openai"
    model: str = "nomic-embed-text"  # 模型名称
    host: Optional[str] = None     # 服务地址（Ollama需要）
    api_key: Optional[str] = None  # API密钥（OpenAI等需要）
    timeout: int = 30              # 超时时间（秒）
```

### RAGConfig（向后兼容）

```python
@dataclass
class RAGConfig:
    # 旧配置（向后兼容）
    ollama_host: str = "http://172.31.198.110:11434"
    embedding_model: str = "nomic-embed-text"
    
    # 新配置（优先使用）
    embedding_provider: str = "ollama"
    embedding_service_config: Optional[EmbeddingConfig] = None
    
    # 其他配置
    collection_name: str = "customer_service_kb"
    generation_model: str = "qwen2.5:7b"
    n_search_results: int = 3
    similarity_threshold: float = 0.7
```

## 扩展新的嵌入服务

要添加新的嵌入服务提供者，只需：

1. 继承 `EmbeddingService` 基类
2. 实现所有抽象方法
3. 在 `create_embedding_service()` 工厂函数中注册

示例：

```python
class CustomEmbeddingService(EmbeddingService):
    def initialize(self) -> bool:
        # 初始化逻辑
        pass
    
    def embed(self, text: str) -> List[float]:
        # 生成嵌入向量
        pass
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        # 批量生成
        pass
    
    def get_embedding_dimension(self) -> int:
        # 返回维度
        pass
```

## 优势

1. **解耦**：RAG系统不再直接依赖Ollama，通过接口交互
2. **灵活**：可以轻松切换不同的嵌入服务
3. **可测试**：可以创建Mock服务进行单元测试
4. **可扩展**：添加新服务只需实现接口
5. **向后兼容**：旧代码无需修改即可继续工作

