# Milvus 连接配置指南

根据您提供的 Milvus 数据库信息，以下是配置步骤：

## 您的 Milvus 数据库信息

- **地址**: 139.9.63.194:32017
- **数据库名**: rag
- **集合名**: kefubuzhishiku1028ban_20251028155535
- **用户名**: root
- **密码**: Milvus
- **表结构**: 
  - id (Int64)
  - content (VarChar)
  - embedding (FloatVector 2048维)
  - file_name (VarChar)
  - chunk_method (VarChar)
  - pc_type (VarChar)
  - index (Int32)
  - Column (VarChar)
  - **距离度量**: COSINE

## 配置步骤

### 1. 在 `.env` 文件中添加配置

在项目根目录的 `.env` 文件中添加以下配置：

```bash
# 向量数据库类型
VECTOR_DB_PROVIDER=milvus

# Milvus 连接配置
MILVUS_HOST=139.9.63.194
MILVUS_PORT=32017
MILVUS_USER=root
MILVUS_PASSWORD=Milvus
MILVUS_DATABASE=rag

# RAG 集合名称
RAG_COLLECTION_NAME=kefubuzhishiku1028ban_20251028155535

# 嵌入服务配置（根据您的实际情况调整）
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_HOST=http://172.31.198.110:11434
```

### 2. 安装依赖

确保已安装 pymilvus：

```bash
pip install pymilvus
```

### 3. 测试连接

运行测试脚本验证连接：

```bash
cd backend
python3 test_milvus_connection.py
```

如果连接成功，您应该看到：
- ✅ Milvus 连接成功
- ✅ 集合存在信息
- ✅ 样本数据查询结果
- ✅ 向量搜索测试结果

### 4. 测试 RAG 集成

运行 RAG 集成测试：

```bash
cd backend
python3 test_rag_with_milvus.py
```

### 5. 启动服务

配置完成后，正常启动服务：

```bash
./setup/start_server.sh
```

## 代码适配说明

代码已自动适配您的表结构：

1. **字段映射**：
   - `content` 字段会自动映射为文档内容
   - `file_name` 会映射为 `source`（来源）
   - 其他元数据字段（`chunk_method`, `pc_type`, `index`, `Column`）会保留

2. **ID 类型处理**：
   - 支持 Int64 类型的 id 字段
   - 添加文档时会自动转换 id 类型

3. **距离度量**：
   - 自动检测并使用 COSINE 距离度量
   - 支持 COSINE 距离的向量搜索

4. **查询适配**：
   - 自动根据表结构选择输出字段
   - 兼容不同的字段组合

## 注意事项

1. **嵌入向量维度**：确保您的嵌入服务生成的向量维度是 2048，与您的表结构匹配

2. **集合已存在**：由于集合已存在，系统不会尝试重新创建，会直接使用现有集合

3. **数据添加**：如果需要添加新数据到现有集合，系统会自动适配字段映射

4. **查询格式**：搜索结果会自动适配返回格式，保持与原有代码兼容

## 验证配置

启动服务后，访问状态接口：

```bash
curl http://localhost:8003/rag/status
```

查看返回的 JSON，确认：
- `vector_db_service.provider` 为 `milvus`
- `vector_db_service.initialized` 为 `true`
- `knowledge_base.total_entries` 显示正确的文档数量

## 常见问题

### 1. 连接失败

检查：
- Milvus 服务是否可访问（`139.9.63.194:32017`）
- 用户名和密码是否正确
- 网络连接是否正常

### 2. 集合不存在

确认集合名称是否正确：`kefubuzhishiku1028ban_20251028155535`

### 3. 向量维度不匹配

确保嵌入服务生成的向量维度为 2048，与表结构一致。

### 4. 距离度量问题

代码会自动检测索引使用的距离度量（COSINE），无需手动配置。

