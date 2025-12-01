# CS Assist AI Backend

智能客服助手后端服务 - 基于FastAPI的RESTful API服务

## 项目简介

本项目是一个纯后端API服务，为智能客服系统提供AI回复建议功能。支持RAG（检索增强生成）技术，能够从知识库中检索相关信息，生成更准确的客服回复建议。

## 项目结构

```
cs_assist_ai/
└── backend/              # 后端服务目录（所有代码和配置都在这里）
    ├── app.py           # FastAPI应用主入口
    ├── requirements.txt # Python依赖（统一管理）
    ├── config.json      # 服务配置
    ├── README.md        # 本文档
    │
    ├── config/          # 配置模块
    ├── models/          # 数据模型
    ├── services/        # 服务层
    ├── utils/           # 工具函数
    ├── scripts/         # 部署脚本
    ├── docs/            # 文档目录
    ├── data/            # 数据目录
    ├── logs/            # 日志目录
    ├── excel_data/      # Excel数据目录
    └── chroma_db/       # 向量数据库存储
```

**所有代码和配置都在 `backend/` 目录下，请进入该目录进行操作。**

## 目录结构详情

```
backend/
├── app.py                    # FastAPI应用主入口
├── config.json               # 服务配置（端口等）
├── requirements.txt           # Python依赖
├── .env.example              # 环境变量模板
├── .gitignore                # Git忽略文件
│
├── config/                   # 配置模块
│   ├── __init__.py          # 配置常量
│   └── excel_column_mapping.json
│
├── models/                   # 数据模型
│   ├── __init__.py
│   └── request_models.py    # API请求/响应模型
│
├── services/                 # 服务层
│   ├── __init__.py
│   ├── embedding_service.py # 嵌入向量服务
│   ├── rag_enhanced_service.py # RAG增强服务
│   ├── vector_db_service.py # 向量数据库服务
│   └── parent_child_retrieval.py
│
├── utils/                    # 工具函数
│   ├── __init__.py
│   ├── conversation_utils.py # 对话处理工具
│   ├── excel_utils.py        # Excel数据处理工具
│   ├── json_utils.py         # JSON处理工具
│   └── prompt_builder.py     # 提示词构建器
│
├── scripts/                  # 部署脚本
│   ├── server.sh            # 服务管理脚本
│   └── README.md            # 脚本使用说明
│
├── docs/                     # 文档目录
│   ├── CONFIG.md            # 配置说明
│   ├── EMBEDDING_SERVICE_README.md # 嵌入服务说明
│   ├── VECTOR_DB_CONFIG.md  # 向量数据库配置
│   ├── MILVUS_INTEGRATION.md # Milvus集成说明
│   ├── MILVUS_USER_CONFIG.md # Milvus用户配置
│   ├── QUICK_START_MILVUS.md # Milvus快速开始
│   ├── app.py问题分析.md    # 代码分析文档
│   ├── 数据流转分析文档.md   # 数据流转分析
│   └── 项目架构分析文档.md   # 项目架构分析
│
├── data/                     # 数据目录
├── logs/                     # 日志目录
├── excel_data/               # Excel数据目录
└── chroma_db/                # 向量数据库存储
```

## 快速开始

### 1. 环境要求

- Python 3.8+
- conda（推荐）或 virtualenv

### 2. 安装依赖

```bash
# 创建conda环境（推荐）
conda create -n cs-assist-ai python=3.10
conda activate cs-assist-ai

# 安装依赖（所有依赖都在requirements.txt中）
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，填入必要的配置
# 至少需要配置 OPENAI_API_KEY
```

### 4. 启动服务

**方式1：使用启动脚本（推荐）**

```bash
# 启动服务（使用默认端口8003）
./scripts/server.sh start

# 或指定端口
./scripts/server.sh start 8003
```

**方式2：直接使用uvicorn**

```bash
uvicorn app:app --host 0.0.0.0 --port 8003 --reload
```

### 5. 验证服务

访问以下地址验证服务是否正常：

- API文档: http://localhost:8003/docs
- 健康检查: http://localhost:8003/health
- 根路径: http://localhost:8003/

## 主要功能

- **AI建议生成**: 根据对话历史和客户信息生成智能回复建议
- **RAG增强**: 支持从知识库检索相关信息，提升回复准确性
- **Excel数据集成**: 支持从Excel文件加载历史会话数据
- **向量数据库**: 支持ChromaDB和Milvus向量数据库
- **多嵌入服务**: 支持Ollama、OpenAI、DashScope等多种嵌入服务

## 主要API端点

### 核心接口

- `POST /suggest` - AI建议生成
  - 根据对话历史和客户信息生成回复建议
  - 支持RAG增强模式

- `POST /feedback` - 反馈提交
  - 提交用户对AI建议的反馈

- `POST /accept` - 采纳建议
  - 记录用户采纳的AI建议

- `GET /rag/status` - RAG系统状态
  - 获取RAG知识库和向量数据库状态

- `POST /api/excel/reload` - 重新加载Excel数据
  - 刷新Excel数据缓存

- `GET /health` - 健康检查
  - 检查服务运行状态

## 配置说明

### 环境变量配置

详细配置说明请参考：
- `.env.example` - 环境变量模板
- `docs/CONFIG.md` - 配置文档
- `docs/VECTOR_DB_CONFIG.md` - 向量数据库配置
- `docs/MILVUS_INTEGRATION.md` - Milvus集成指南
- `docs/MILVUS_USER_CONFIG.md` - Milvus用户配置

主要配置项：

- **OpenAI配置**: API密钥、模型、Base URL
- **嵌入服务配置**: 支持Ollama、OpenAI、DashScope等
- **RAG配置**: 知识库集合、检索参数
- **向量数据库配置**: ChromaDB或Milvus

### 服务配置

编辑 `config.json` 配置服务端口等：

```json
{
  "backend": {
    "port": 8003,
    "host": "0.0.0.0",
    "api_base_url": "http://localhost:8003"
  }
}
```

## 服务管理

使用 `scripts/server.sh` 管理服务：

```bash
# 启动服务
./scripts/server.sh start [端口号]

# 停止服务
./scripts/server.sh stop [端口号]

# 重启服务
./scripts/server.sh restart [端口号]

# 查看状态
./scripts/server.sh status [端口号]

# 查看日志
./scripts/server.sh logs

# 更新配置
./scripts/server.sh config <端口号>
```

详细说明请参考 `scripts/README.md`

## 模块说明

### config/
集中管理所有配置常量，包括环境变量加载、OpenAI配置、RAG配置等。

### models/
使用Pydantic定义API请求和响应的数据模型，提供类型安全的数据验证。

### services/
核心业务服务层：
- **embedding_service.py**: 嵌入向量服务抽象层，支持多种嵌入服务提供商
- **rag_enhanced_service.py**: RAG增强服务，提供知识库搜索和检索功能
- **vector_db_service.py**: 向量数据库服务，支持ChromaDB和Milvus

### utils/
通用工具函数：
- **conversation_utils.py**: 对话处理工具
- **excel_utils.py**: Excel数据处理工具
- **json_utils.py**: JSON处理工具
- **prompt_builder.py**: 提示词构建器

## 代码特点

1. **模块化清晰** - 按功能划分目录，职责分离
2. **标准分层** - 配置、模型、服务、工具函数分层明确
3. **易于维护** - 代码结构清晰，便于扩展
4. **类型安全** - 使用Pydantic进行数据验证
5. **文档完善** - 提供详细的API文档和配置说明

## 依赖管理

**所有Python依赖统一在 `requirements.txt` 中管理**，包括：

- Web框架（FastAPI、Uvicorn）
- OpenAI客户端
- 向量数据库（ChromaDB、Milvus）
- RAG相关依赖
- 数据处理工具

## 开发说明

### 添加新的API端点

1. 在 `app.py` 中添加路由函数
2. 在 `models/request_models.py` 中定义请求/响应模型
3. 在 `services/` 中实现业务逻辑（如需要）
4. 更新API文档

### 添加新的服务

1. 在 `services/` 目录下创建新的服务文件
2. 在 `services/__init__.py` 中导出
3. 在需要的地方导入使用

## 许可证

[根据实际情况填写]
