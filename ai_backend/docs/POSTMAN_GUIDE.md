# Postman 接口测试指南

## 文件说明

项目已包含 Postman Collection 配置文件：`CS_Assist_AI.postman_collection.json`

此文件包含了所有 API 接口的完整配置，可以直接导入到 Postman 进行接口测试。

## 导入方法

### 方法一：通过 Postman 界面导入

1. 打开 Postman 应用
2. 点击左上角的 **Import** 按钮
3. 选择 **File** 标签页
4. 点击 **Upload Files**，选择 `CS_Assist_AI.postman_collection.json` 文件
5. 点击 **Import** 完成导入

### 方法二：直接拖拽导入

1. 打开 Postman 应用
2. 直接将 `CS_Assist_AI.postman_collection.json` 文件拖拽到 Postman 窗口中
3. 自动完成导入

## 配置说明

### 环境变量

Collection 中已配置了基础 URL 变量：

- **变量名**: `base_url`
- **默认值**: `http://localhost:8003`

### 修改服务器地址

如果需要测试不同环境的服务器，可以：

1. 在 Postman 中点击 Collection 名称
2. 选择 **Variables** 标签
3. 修改 `base_url` 的值，例如：
   - 开发环境: `http://localhost:8003`
   - 测试环境: `http://test.example.com:8003`
   - 生产环境: `http://api.example.com:8003`

## 接口列表

### 核心接口

#### 1. AI建议生成 (POST /suggest)

根据对话历史和客户信息生成AI回复建议。

**请求示例**：
```json
{
  "customer_id": "customer_001",
  "conversation": [
    {
      "role": "customer",
      "content": "你好，我想咨询一下产品价格",
      "sender": null,
      "timestamp": null
    },
    {
      "role": "agent",
      "content": "您好，很高兴为您服务。",
      "sender": "客服小张",
      "timestamp": null
    }
  ],
  "session_info": {
    "id": "session_001",
    "type": "personal",
    "is_group": false,
    "phone": "13800138000",
    "last_message_time": "2024-01-01T10:00:00"
  },
  "customer_data": {
    "type": "personal",
    "phone": "13800138000",
    "basic_info": {},
    "business_info": {},
    "tags": ["VIP"],
    "service_history": []
  },
  "use_rag": true
}
```

**响应示例**：
```json
{
  "suggestion": "感谢您的咨询，我们新款手机的价格是3999元...",
  "rag_enhanced": true,
  "method": "RAG_Enhanced",
  "rag_status": {
    "status": "就绪",
    "knowledge_base": {
      "collection_name": "customer_service_kb",
      "total_entries": 100
    }
  }
}
```

#### 2. 提交反馈 (POST /feedback)

提交用户对AI建议的反馈。

**请求参数**：
- `customer_id`: 客户ID
- `conversation`: 对话历史
- `suggestion`: AI建议内容
- `feedback`: 反馈类型（"positive" 或 "negative"）
- `timestamp`: 时间戳（可选）

#### 3. 采纳建议 (POST /accept)

记录用户采纳的AI建议。

**请求参数**：
- `customer_id`: 客户ID
- `conversation`: 对话历史
- `suggestion`: 被采纳的建议内容
- `session_info`: 会话信息（可选）
- `customer_data`: 客户数据（可选）
- `timestamp`: 时间戳（可选）

### RAG系统

#### 4. 获取RAG系统状态 (GET /rag/status)

获取RAG知识库和向量数据库的状态信息。

**响应示例**：
```json
{
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
    "provider": "dashscope",
    "model": "text-embedding-v4",
    "initialized": true,
    "dimension": 2048
  }
}
```

### 数据管理

#### 5. 重新加载Excel数据 (POST /api/excel/reload)

重新加载Excel数据，刷新缓存。

**响应示例**：
```json
{
  "status": "success",
  "message": "Excel数据已重新加载",
  "excel_data_loaded": true,
  "excel_records": 1500,
  "excel_file_path": "./excel_data/"
}
```

### 系统监控

#### 6. 健康检查 (GET /health)

检查服务运行状态。

**响应示例**：
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T10:00:00",
  "service": "CS Assist AI Backend",
  "excel_data_loaded": true,
  "excel_records": 1500
}
```

#### 7. 根路径 (GET /)

获取服务信息和可用接口列表。

**响应示例**：
```json
{
  "service": "CS Assist AI Backend",
  "version": "1.0",
  "endpoints": {
    "suggest": "/suggest",
    "feedback": "/feedback",
    "rag_status": "/rag/status",
    "health": "/health"
  }
}
```

## 测试流程建议

### 1. 基础测试

1. 首先测试 **健康检查** 接口，确认服务正常运行
2. 测试 **获取RAG系统状态**，确认RAG系统已就绪
3. 测试 **根路径**，查看服务信息

### 2. 功能测试

1. 测试 **AI建议生成** 接口：
   - 测试不使用RAG的情况（`use_rag: false`）
   - 测试使用RAG的情况（`use_rag: true`）
   - 测试不同的对话场景

2. 测试 **提交反馈** 接口：
   - 测试正面反馈（`feedback: "positive"`）
   - 测试负面反馈（`feedback: "negative"`）

3. 测试 **采纳建议** 接口

### 3. 数据管理测试

1. 测试 **重新加载Excel数据** 接口
2. 验证数据是否成功加载

## 常见问题

### Q: 如何修改请求参数？

A: 在 Postman 中：
1. 选择对应的接口
2. 点击 **Body** 标签
3. 选择 **raw** 和 **JSON** 格式
4. 直接编辑 JSON 内容

### Q: 如何查看响应结果？

A: 发送请求后，在 Postman 底部会显示：
- **Status**: HTTP 状态码
- **Time**: 请求耗时
- **Size**: 响应大小
- **Body**: 响应内容（JSON格式）

### Q: 如何保存测试结果？

A: 在 Postman 中：
1. 点击 **Save Response** 按钮
2. 选择保存位置
3. 可以保存为示例响应，方便后续参考

### Q: 如何批量测试？

A: 可以使用 Postman 的 **Collection Runner**：
1. 点击 Collection 右侧的 **...** 菜单
2. 选择 **Run collection**
3. 选择要运行的接口
4. 点击 **Run** 开始批量测试

## 注意事项

1. **确保服务已启动**：在测试前，确保后端服务正在运行（默认端口 8003）

2. **检查环境变量**：如果服务运行在不同的地址或端口，记得修改 `base_url` 变量

3. **请求格式**：所有 POST 请求都需要设置 `Content-Type: application/json` 头

4. **数据格式**：确保 JSON 格式正确，特别是嵌套的对象和数组

5. **RAG功能**：使用 RAG 增强功能时，确保 RAG 系统已正确初始化

## 扩展功能

### 创建环境配置

可以在 Postman 中创建不同的环境（Environments）：

1. 点击右上角的 **Environments** 图标
2. 点击 **+** 创建新环境
3. 添加变量：
   - `base_url`: 服务器地址
   - `api_key`: API密钥（如果需要）
4. 在不同环境间切换进行测试

### 使用 Pre-request Scripts

可以在请求前执行脚本，例如：
- 自动生成时间戳
- 计算签名
- 设置动态变量

### 使用 Tests

可以在请求后执行测试脚本，例如：
- 验证响应状态码
- 检查响应内容
- 保存响应数据到变量

## 相关文档

- [API 文档](http://localhost:8003/docs) - FastAPI 自动生成的交互式文档
- [配置说明](CONFIG.md) - 环境变量配置说明
- [项目 README](../README.md) - 项目总体说明

