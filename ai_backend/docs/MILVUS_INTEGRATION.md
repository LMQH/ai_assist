# Milvus 向量数据库集成说明

## 改动概述

已成功将向量数据库抽象化，支持通过配置在 ChromaDB 和 Milvus 之间切换，无需修改核心代码。

## 新增文件

1. **`backend/services/vector_db_service.py`**
   - 向量数据库服务抽象层
   - 实现了 `ChromaDBVectorDBService` 和 `MilvusVectorDBService`
   - 提供统一的接口用于集合管理、文档添加和搜索

## 修改的文件

1. **`backend/config/__init__.py`**
   - 新增向量数据库相关配置项：
     - `VECTOR_DB_PROVIDER`: 向量数据库类型（chromadb/milvus）
     - `MILVUS_HOST`: Milvus 服务地址
     - `MILVUS_PORT`: Milvus 服务端口
     - `MILVUS_USER`: Milvus 用户名（可选）
     - `MILVUS_PASSWORD`: Milvus 密码（可选）
     - `MILVUS_DATABASE`: Milvus 数据库名（可选）

2. **`backend/services/rag_enhanced_service.py`**
   - 移除了对 ChromaDB 的直接依赖
   - 使用 `VectorDBService` 抽象层
   - 保持原有接口不变，确保向后兼容

## 快速开始

### 1. 安装 Milvus 依赖（可选）

如果使用 Milvus，需要安装：

```bash
pip install pymilvus
```

### 2. 配置环境变量

在 `.env` 文件中添加：

```bash
# 切换到 Milvus
VECTOR_DB_PROVIDER=milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530

# 或者继续使用 ChromaDB（默认）
VECTOR_DB_PROVIDER=chromadb
```

### 3. 启动服务

服务会自动检测配置并使用对应的向量数据库。首次使用 Milvus 时，系统会自动创建集合并加载知识库。

## 设计优势

1. **最小化改动**：核心 RAG 逻辑保持不变，只替换了向量数据库访问层
2. **可配置切换**：通过环境变量即可切换，无需修改代码
3. **统一接口**：所有向量数据库操作通过统一接口，便于扩展
4. **向后兼容**：默认仍使用 ChromaDB，不影响现有部署

## 接口说明

`VectorDBService` 抽象类提供以下方法：

- `initialize()`: 初始化向量数据库连接
- `collection_exists(name)`: 检查集合是否存在
- `create_collection(name, embedding_dim)`: 创建集合
- `get_collection_count(name)`: 获取集合文档数量
- `add_documents(...)`: 添加文档
- `search(...)`: 搜索相似文档

## 注意事项

1. **数据迁移**：不同向量数据库之间的数据不会自动迁移，需要重新加载知识库
2. **性能差异**：Milvus 适合大规模数据，ChromaDB 适合中小规模
3. **依赖安装**：使用 Milvus 需要额外安装 `pymilvus` 包
4. **Milvus 服务**：使用 Milvus 需要先启动 Milvus 服务（Docker 或本地安装）

## 验证配置

启动服务后，访问 `/rag/status` 端点查看向量数据库状态：

```bash
curl http://localhost:8003/rag/status
```

在返回的 JSON 中查看 `vector_db_service.provider` 字段确认当前使用的向量数据库类型。

