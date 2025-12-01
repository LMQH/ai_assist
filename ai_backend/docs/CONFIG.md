# 环境变量配置说明

## 向量化配置

所有向量化相关的配置都通过环境变量管理，配置文件位于 `.env` 文件中。

### 嵌入服务配置

| 环境变量 | 说明 | 默认值 | 示例 |
|---------|------|--------|------|
| `EMBEDDING_PROVIDER` | 嵌入服务提供者 | `ollama` | `ollama` 或 `openai` |
| `EMBEDDING_MODEL` | 嵌入模型名称 | `nomic-embed-text` | `nomic-embed-text` (Ollama) 或 `text-embedding-ada-002` (OpenAI) |
| `EMBEDDING_HOST` | Ollama服务地址 | `http://172.31.198.110:11434` | `http://localhost:11434` |
| `EMBEDDING_API_KEY` | API密钥（OpenAI等需要） | `None` | `sk-...` |
| `EMBEDDING_TIMEOUT` | 超时时间（秒） | `30` | `30` |

### RAG配置

| 环境变量 | 说明 | 默认值 | 示例 |
|---------|------|--------|------|
| `RAG_COLLECTION_NAME` | 向量数据库集合名称 | `customer_service_kb` | `customer_service_kb` |
| `RAG_N_SEARCH_RESULTS` | 检索结果数量 | `3` | `3` |
| `RAG_SIMILARITY_THRESHOLD` | 相似度阈值（0.0-1.0） | `0.7` | `0.7` |

## 配置示例

### 使用 Ollama（默认）

```bash
# .env 文件
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_HOST=http://172.31.198.110:11434
EMBEDDING_TIMEOUT=30

RAG_COLLECTION_NAME=customer_service_kb
RAG_N_SEARCH_RESULTS=3
RAG_SIMILARITY_THRESHOLD=0.7
```

### 使用 OpenAI

```bash
# .env 文件
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-ada-002
EMBEDDING_API_KEY=sk-your-api-key-here
EMBEDDING_TIMEOUT=30

RAG_COLLECTION_NAME=customer_service_kb
RAG_N_SEARCH_RESULTS=5
RAG_SIMILARITY_THRESHOLD=0.75
```

## 如何修改配置

1. **编辑 `.env` 文件**
   ```bash
   vim .env
   # 或
   nano .env
   ```

2. **修改对应的环境变量值**

3. **重启服务**使配置生效
   ```bash
   # 如果使用启动脚本
   ./setup/start_server.sh
   
   # 或直接使用 uvicorn
   uvicorn app:app --reload
   ```

## 配置验证

启动服务后，可以通过以下方式验证配置：

1. **查看日志**：服务启动时会输出配置信息
2. **API检查**：访问 `GET /rag/status` 查看RAG系统状态和配置

## 注意事项

- `.env` 文件包含敏感信息，不要提交到版本控制系统
- 修改配置后需要重启服务才能生效
- 如果环境变量未设置，将使用代码中的默认值
- `EMBEDDING_API_KEY` 仅在需要使用 OpenAI 等服务时设置

