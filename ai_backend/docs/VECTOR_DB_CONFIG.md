# 向量数据库配置说明

本项目支持使用 ChromaDB 或 Milvus 作为向量数据库，可以通过配置轻松切换。

## 配置方式

### 环境变量配置

在 `.env` 文件中添加以下配置：

```bash
# 向量数据库类型：chromadb 或 milvus
VECTOR_DB_PROVIDER=chromadb

# 如果使用 Milvus，配置以下参数
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_USER=          # 可选，如果 Milvus 启用了认证
MILVUS_PASSWORD=      # 可选
MILVUS_DATABASE=      # 可选，指定使用的数据库名称
```

### 使用 ChromaDB（默认）

ChromaDB 是默认的向量数据库，使用本地文件存储，无需额外服务。

```bash
# .env 文件
VECTOR_DB_PROVIDER=chromadb
RAG_DB_PATH=./chroma_db  # ChromaDB 数据存储路径
```

### 使用 Milvus

如果切换到 Milvus，需要：

1. **安装 pymilvus 依赖**
   ```bash
   pip install pymilvus
   ```

2. **启动 Milvus 服务**
   - 使用 Docker 启动（推荐）：
     ```bash
     docker run -d \
       --name milvus-standalone \
       -p 19530:19530 \
       -p 9091:9091 \
       -v $(pwd)/volumes/milvus:/var/lib/milvus \
       milvusdb/milvus:latest
     ```
   - 或者使用 Milvus Lite（单机版）：
     ```bash
     pip install milvus
     ```

3. **配置环境变量**
   ```bash
   # .env 文件
   VECTOR_DB_PROVIDER=milvus
   MILVUS_HOST=localhost
   MILVUS_PORT=19530
   # 如果需要认证
   MILVUS_USER=root
   MILVUS_PASSWORD=your_password
   # 可选：指定数据库
   MILVUS_DATABASE=default
   ```

## 切换向量数据库

### 从 ChromaDB 切换到 Milvus

1. 配置 Milvus 连接信息（如上）
2. 设置 `VECTOR_DB_PROVIDER=milvus`
3. 重启服务
4. 系统会自动在 Milvus 中创建新的集合，并重新加载知识库

### 从 Milvus 切换回 ChromaDB

1. 设置 `VECTOR_DB_PROVIDER=chromadb`
2. 重启服务
3. 系统会使用 ChromaDB 本地存储

**注意**：不同向量数据库之间的数据不会自动迁移。如果需要保留数据，需要手动导出和导入。

## 配置参数说明

| 参数 | 说明 | 默认值 | 必需 |
|------|------|--------|------|
| `VECTOR_DB_PROVIDER` | 向量数据库类型 | `chromadb` | 是 |
| `MILVUS_HOST` | Milvus 服务地址 | `localhost` | 使用 Milvus 时必需 |
| `MILVUS_PORT` | Milvus 服务端口 | `19530` | 使用 Milvus 时必需 |
| `MILVUS_USER` | Milvus 用户名 | `None` | 可选 |
| `MILVUS_PASSWORD` | Milvus 密码 | `None` | 可选 |
| `MILVUS_DATABASE` | Milvus 数据库名 | `None` | 可选 |
| `RAG_DB_PATH` | ChromaDB 存储路径 | `./chroma_db` | 使用 ChromaDB 时使用 |

## 检查配置状态

启动服务后，可以通过以下 API 检查向量数据库状态：

```bash
curl http://localhost:8003/rag/status
```

返回示例：

```json
{
  "success": true,
  "rag_status": {
    "status": "就绪",
    "knowledge_base": {
      "collection_name": "customer_service_kb",
      "total_entries": 100,
      "status": "已加载"
    },
    "vector_db_service": {
      "provider": "milvus",
      "initialized": true,
      "collection_name": "customer_service_kb"
    },
    "embedding_service": {
      "provider": "ollama",
      "model": "nomic-embed-text",
      "initialized": true,
      "dimension": 768
    }
  }
}
```

## 常见问题

### 1. Milvus 连接失败

- 检查 Milvus 服务是否启动
- 确认 `MILVUS_HOST` 和 `MILVUS_PORT` 配置正确
- 检查防火墙设置

### 2. pymilvus 未安装错误

运行以下命令安装：
```bash
pip install pymilvus
```

### 3. 集合创建失败

- 检查 Milvus 版本兼容性
- 查看日志了解详细错误信息
- 确认嵌入向量维度设置正确

### 4. 数据不迁移

不同向量数据库之间的数据不会自动迁移。如果需要迁移：
1. 从旧数据库导出数据
2. 切换到新数据库
3. 重新加载知识库文件（系统会自动重新向量化）

