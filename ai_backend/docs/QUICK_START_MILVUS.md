# Milvus 快速开始指南

## 您的 Milvus 数据库配置

根据您提供的信息，以下是快速配置步骤：

### 1. 安装依赖

```bash
pip install pymilvus
```

### 2. 配置环境变量

在项目根目录的 `.env` 文件中添加：

```bash
# 切换到 Milvus
VECTOR_DB_PROVIDER=milvus

# 您的 Milvus 连接信息
MILVUS_HOST=139.9.63.194
MILVUS_PORT=32017
MILVUS_USER=root
MILVUS_PASSWORD=Milvus
MILVUS_DATABASE=rag

# 您的集合名称
RAG_COLLECTION_NAME=kefubuzhishiku1028ban_20251028155535
```

### 3. 测试连接

```bash
cd backend
python3 test_milvus_connection.py
```

### 4. 测试 RAG 集成

```bash
cd backend
python3 test_rag_with_milvus.py
```

### 5. 启动服务

```bash
./setup/start_server.sh
```

## 代码适配说明

代码已自动适配您的表结构，包括：

✅ **字段映射**
- `content` → 文档内容
- `file_name` → 来源信息
- 自动适配所有元数据字段

✅ **类型支持**
- Int64 类型的 id
- 2048 维向量
- COSINE 距离度量

✅ **自动检测**
- 自动检测表结构
- 自动适配字段映射
- 自动使用正确的距离度量

## 验证

启动服务后访问：
```bash
curl http://localhost:8003/rag/status
```

查看 `vector_db_service.provider` 应为 `milvus`。

## 详细文档

更多信息请查看：
- `docs/MILVUS_USER_CONFIG.md` - 详细配置说明
- `docs/VECTOR_DB_CONFIG.md` - 通用配置指南

