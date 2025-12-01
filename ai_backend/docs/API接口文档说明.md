# CS Assist AI Backend API 接口文档

> 本文档面向前端开发者，提供完整的 API 接口说明和使用指南

## 目录

- [基础信息](#基础信息)
- [数据模型](#数据模型)
- [核心接口](#核心接口)
- [系统接口](#系统接口)
- [错误处理](#错误处理)
- [代码示例](#代码示例)
- [常见问题](#常见问题)

---

## 基础信息

### 服务器地址

- **开发环境**: `http://localhost:8003`
- **生产环境**: 根据实际部署情况配置

### 请求格式

- **Content-Type**: `application/json`
- **请求方法**: 支持 `GET` 和 `POST`
- **字符编码**: `UTF-8`

### CORS 配置

后端已配置 CORS，支持跨域请求：

- `allow_origins`: `["*"]` (允许所有来源)
- `allow_methods`: `["*"]` (允许所有方法)
- `allow_headers`: `["*"]` (允许所有请求头)

### 响应格式

所有接口统一返回 JSON 格式：

```json
{
  "status": "success",
  "data": {},
  "message": "操作成功"
}
```

---

## 数据模型

### Message（消息）

```typescript
interface Message {
  role: "customer" | "agent" | "群聊成员";  // 消息角色
  content: string;                          // 消息内容
  sender?: string;                          // 发送者名称（可选，群聊时使用）
  timestamp?: number;                       // 时间戳（可选，Unix 时间戳）
}
```

**字段说明**：
- `role`: 消息角色
  - `"customer"`: 客户消息
  - `"agent"`: 客服消息
  - `"群聊成员"`: 群聊中的成员消息
- `content`: 消息文本内容
- `sender`: 发送者名称，群聊时用于区分不同成员
- `timestamp`: 消息时间戳（可选）

### SessionInfo（会话信息）

```typescript
interface SessionInfo {
  id: string;                    // 会话ID（必需）
  type: "group" | "personal";    // 会话类型
  is_group: boolean;             // 是否为群聊
  group_name?: string;           // 群聊名称（群聊时使用）
  phone?: string;                 // 手机号（个人会话时使用）
  last_message_time?: string;    // 最后一条消息时间（ISO 格式）
}
```

### CustomerData（客户数据）

```typescript
interface CustomerData {
  type: "group" | "personal";              // 客户类型
  phone?: string;                          // 手机号
  basic_info?: Record<string, any>;        // 基本信息
  business_info?: Record<string, any>;     // 业务信息
  tags?: string[];                         // 客户标签
  service_history?: Array<Record<string, any>>;  // 服务历史
  group_name?: string;                     // 群聊名称（群聊时使用）
  member_count?: string;                   // 群成员数量（群聊时使用）
}
```

---

## 核心接口

### 1. AI建议生成

根据对话历史和客户信息生成AI回复建议。

**接口地址**: `POST /suggest`

**请求参数**:

```typescript
interface SuggestionRequest {
  customer_id: string;                    // 客户ID（必需）
  conversation: Message[];                // 对话历史（必需）
  session_info?: SessionInfo;             // 会话信息（可选）
  customer_data?: CustomerData;           // 客户数据（可选）
  use_rag?: boolean;                      // 是否使用RAG增强（默认: true）
}
```

**请求示例**:

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
      "content": "您好，很高兴为您服务。请问您想了解哪个产品的价格呢？",
      "sender": "客服小张",
      "timestamp": null
    },
    {
      "role": "customer",
      "content": "我想了解一下你们的新款手机的价格",
      "sender": null,
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
    "basic_info": {
      "name": "张三",
      "age": 30
    },
    "tags": ["VIP", "老客户"],
    "service_history": []
  },
  "use_rag": true
}
```

**响应参数**:

```typescript
interface SuggestionResponse {
  suggestion: string;                      // AI生成的建议内容
  rag_enhanced: boolean;                   // 是否使用了RAG增强
  method: "RAG_Enhanced" | "Original";    // 使用的方法
  rag_status?: {                           // RAG状态（使用RAG时返回）
    status: string;
    knowledge_base: {
      collection_name: string;
      total_entries: number;
      status: string;
    };
    vector_db_service: {
      provider: string;
      initialized: boolean;
      collection_name: string;
    };
    embedding_service: {
      provider: string;
      model: string;
      initialized: boolean;
      dimension: number;
    };
  };
}
```

**响应示例**:

```json
{
  "suggestion": "感谢您的咨询，我们新款手机的价格是3999元，现在有优惠活动，可以享受9折优惠。如果您需要了解更多详情，我可以为您详细介绍。",
  "rag_enhanced": true,
  "method": "RAG_Enhanced",
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
      "provider": "dashscope",
      "model": "text-embedding-v4",
      "initialized": true,
      "dimension": 2048
    }
  }
}
```

**使用说明**:

1. **对话历史**: `conversation` 数组应按照时间顺序排列，最新的消息在最后
2. **RAG增强**: 设置 `use_rag: true` 时，系统会从知识库检索相关信息，提升建议质量
3. **客户数据**: 提供 `customer_data` 可以帮助AI更好地理解客户背景，生成更个性化的建议
4. **会话信息**: `session_info` 用于关联历史会话数据，提升上下文理解

**JavaScript 示例**:

```javascript
async function getAISuggestion(customerId, conversation, sessionInfo, customerData) {
  const response = await fetch('http://localhost:8003/suggest', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      customer_id: customerId,
      conversation: conversation,
      session_info: sessionInfo,
      customer_data: customerData,
      use_rag: true
    })
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  const data = await response.json();
  return data;
}
```

---

### 2. 提交反馈

提交用户对AI建议的反馈。

**接口地址**: `POST /feedback`

**请求参数**:

```typescript
interface FeedbackRequest {
  customer_id: string;        // 客户ID（必需）
  conversation: Message[];  // 对话历史（必需）
  suggestion: string;        // AI建议内容（必需）
  feedback: "positive" | "negative";  // 反馈类型（必需）
  timestamp?: number;        // 时间戳（可选，Unix 时间戳）
}
```

**请求示例**:

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
  "suggestion": "感谢您的咨询，我们新款手机的价格是3999元，现在有优惠活动。",
  "feedback": "positive",
  "timestamp": 1704067200
}
```

**响应参数**:

```typescript
interface FeedbackResponse {
  status: "success";
  message: "反馈已记录";
}
```

**响应示例**:

```json
{
  "status": "success",
  "message": "反馈已记录"
}
```

**JavaScript 示例**:

```javascript
async function submitFeedback(customerId, conversation, suggestion, feedback) {
  const response = await fetch('http://localhost:8003/feedback', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      customer_id: customerId,
      conversation: conversation,
      suggestion: suggestion,
      feedback: feedback,
      timestamp: Math.floor(Date.now() / 1000)
    })
  });
  
  return await response.json();
}
```

---

### 3. 采纳建议

记录用户采纳的AI建议。

**接口地址**: `POST /accept`

**请求参数**:

```typescript
interface AcceptSuggestionRequest {
  customer_id: string;           // 客户ID（必需）
  conversation: Message[];       // 对话历史（必需）
  suggestion: string;            // 被采纳的建议内容（必需）
  session_info?: SessionInfo;    // 会话信息（可选）
  customer_data?: CustomerData;  // 客户数据（可选）
  timestamp?: string;            // 时间戳（可选，ISO 格式）
}
```

**请求示例**:

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
  "suggestion": "感谢您的咨询，我们新款手机的价格是3999元，现在有优惠活动。",
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
    "tags": ["VIP"]
  },
  "timestamp": "2024-01-01T10:05:00"
}
```

**响应参数**:

```typescript
interface AcceptSuggestionResponse {
  status: "success";
  message: "采纳记录已保存";
  session_id: string;      // 会话ID
  timestamp: string;       // 时间戳（ISO 格式）
}
```

**响应示例**:

```json
{
  "status": "success",
  "message": "采纳记录已保存",
  "session_id": "session_001",
  "timestamp": "2024-01-01T10:05:00"
}
```

**JavaScript 示例**:

```javascript
async function acceptSuggestion(customerId, conversation, suggestion, sessionInfo, customerData) {
  const response = await fetch('http://localhost:8003/accept', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      customer_id: customerId,
      conversation: conversation,
      suggestion: suggestion,
      session_info: sessionInfo,
      customer_data: customerData,
      timestamp: new Date().toISOString()
    })
  });
  
  return await response.json();
}
```

---

## 系统接口

### 4. 获取RAG系统状态

获取RAG知识库和向量数据库的状态信息。

**接口地址**: `GET /rag/status`

**请求参数**: 无

**响应参数**:

```typescript
interface RAGStatusResponse {
  status: string;                    // 系统状态（"就绪" | "未初始化" | "错误"）
  knowledge_base?: {
    collection_name: string;        // 集合名称
    total_entries: number;          // 知识库条目数量
    status: string;                  // 状态
  };
  vector_db_service?: {
    provider: string;                // 向量数据库类型（"chromadb" | "milvus"）
    initialized: boolean;            // 是否已初始化
    collection_name: string;        // 集合名称
  };
  embedding_service?: {
    provider: string;                // 嵌入服务提供者
    model: string;                    // 模型名称
    initialized: boolean;            // 是否已初始化
    dimension: number;              // 向量维度
  };
}
```

**响应示例**:

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

**JavaScript 示例**:

```javascript
async function getRAGStatus() {
  const response = await fetch('http://localhost:8003/rag/status');
  return await response.json();
}
```

---

### 5. 重新加载Excel数据

重新加载Excel数据，刷新缓存。

**接口地址**: `POST /api/excel/reload`

**请求参数**: 无

**响应参数**:

```typescript
interface ReloadExcelResponse {
  status: "success";
  message: "Excel数据已重新加载";
  excel_data_loaded: boolean;    // 数据是否已加载
  excel_records: number;        // Excel记录数量
  excel_file_path: string;      // Excel文件路径
}
```

**响应示例**:

```json
{
  "status": "success",
  "message": "Excel数据已重新加载",
  "excel_data_loaded": true,
  "excel_records": 1500,
  "excel_file_path": "./excel_data/"
}
```

**JavaScript 示例**:

```javascript
async function reloadExcelData() {
  const response = await fetch('http://localhost:8003/api/excel/reload', {
    method: 'POST'
  });
  return await response.json();
}
```

---

### 6. 健康检查

检查服务运行状态。

**接口地址**: `GET /health`

**请求参数**: 无

**响应参数**:

```typescript
interface HealthCheckResponse {
  status: "healthy";
  timestamp: string;              // 时间戳（ISO 格式）
  service: string;                // 服务名称
  excel_data_loaded: boolean;     // Excel数据是否已加载
  excel_records: number;          // Excel记录数量
}
```

**响应示例**:

```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T10:00:00",
  "service": "CS Assist AI Backend",
  "excel_data_loaded": true,
  "excel_records": 1500
}
```

**JavaScript 示例**:

```javascript
async function healthCheck() {
  const response = await fetch('http://localhost:8003/health');
  return await response.json();
}
```

---

### 7. 根路径

获取服务信息和可用接口列表。

**接口地址**: `GET /`

**请求参数**: 无

**响应参数**:

```typescript
interface RootResponse {
  service: string;
  version: string;
  endpoints: {
    suggest: string;
    feedback: string;
    rag_status: string;
    health: string;
  };
}
```

**响应示例**:

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

---

## 错误处理

### HTTP 状态码

- `200 OK`: 请求成功
- `400 Bad Request`: 请求参数错误
- `500 Internal Server Error`: 服务器内部错误

### 错误响应格式

```typescript
interface ErrorResponse {
  detail: string;  // 错误详情
}
```

**错误响应示例**:

```json
{
  "detail": "AI返回内容为空"
}
```

### 错误处理示例

```javascript
async function handleRequest(url, options) {
  try {
    const response = await fetch(url, options);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Request failed:', error);
    throw error;
  }
}
```

---

## 代码示例

### TypeScript 完整示例

```typescript
// api.ts

const API_BASE_URL = 'http://localhost:8003';

// 类型定义
interface Message {
  role: 'customer' | 'agent' | '群聊成员';
  content: string;
  sender?: string;
  timestamp?: number;
}

interface SessionInfo {
  id: string;
  type: 'group' | 'personal';
  is_group: boolean;
  group_name?: string;
  phone?: string;
  last_message_time?: string;
}

interface CustomerData {
  type: 'group' | 'personal';
  phone?: string;
  basic_info?: Record<string, any>;
  business_info?: Record<string, any>;
  tags?: string[];
  service_history?: Array<Record<string, any>>;
  group_name?: string;
  member_count?: string;
}

interface SuggestionRequest {
  customer_id: string;
  conversation: Message[];
  session_info?: SessionInfo;
  customer_data?: CustomerData;
  use_rag?: boolean;
}

interface SuggestionResponse {
  suggestion: string;
  rag_enhanced: boolean;
  method: 'RAG_Enhanced' | 'Original';
  rag_status?: any;
}

// API 客户端类
class CSAssistAPIClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  /**
   * 获取AI建议
   */
  async getSuggestion(
    customerId: string,
    conversation: Message[],
    sessionInfo?: SessionInfo,
    customerData?: CustomerData,
    useRAG: boolean = true
  ): Promise<SuggestionResponse> {
    const response = await fetch(`${this.baseURL}/suggest`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        customer_id: customerId,
        conversation,
        session_info: sessionInfo,
        customer_data: customerData,
        use_rag: useRAG,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get suggestion');
    }

    return await response.json();
  }

  /**
   * 提交反馈
   */
  async submitFeedback(
    customerId: string,
    conversation: Message[],
    suggestion: string,
    feedback: 'positive' | 'negative'
  ): Promise<{ status: string; message: string }> {
    const response = await fetch(`${this.baseURL}/feedback`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        customer_id: customerId,
        conversation,
        suggestion,
        feedback,
        timestamp: Math.floor(Date.now() / 1000),
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to submit feedback');
    }

    return await response.json();
  }

  /**
   * 采纳建议
   */
  async acceptSuggestion(
    customerId: string,
    conversation: Message[],
    suggestion: string,
    sessionInfo?: SessionInfo,
    customerData?: CustomerData
  ): Promise<{ status: string; message: string; session_id: string; timestamp: string }> {
    const response = await fetch(`${this.baseURL}/accept`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        customer_id: customerId,
        conversation,
        suggestion,
        session_info: sessionInfo,
        customer_data: customerData,
        timestamp: new Date().toISOString(),
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to accept suggestion');
    }

    return await response.json();
  }

  /**
   * 获取RAG系统状态
   */
  async getRAGStatus(): Promise<any> {
    const response = await fetch(`${this.baseURL}/rag/status`);
    if (!response.ok) {
      throw new Error('Failed to get RAG status');
    }
    return await response.json();
  }

  /**
   * 健康检查
   */
  async healthCheck(): Promise<any> {
    const response = await fetch(`${this.baseURL}/health`);
    if (!response.ok) {
      throw new Error('Health check failed');
    }
    return await response.json();
  }
}

// 导出单例
export const apiClient = new CSAssistAPIClient();
export default CSAssistAPIClient;
```

### React Hook 示例

```typescript
// useAISuggestion.ts
import { useState, useCallback } from 'react';
import { apiClient } from './api';

export function useAISuggestion() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getSuggestion = useCallback(async (
    customerId: string,
    conversation: Message[],
    sessionInfo?: SessionInfo,
    customerData?: CustomerData,
    useRAG: boolean = true
  ) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await apiClient.getSuggestion(
        customerId,
        conversation,
        sessionInfo,
        customerData,
        useRAG
      );
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { getSuggestion, loading, error };
}
```

---

## 常见问题

### Q1: 如何处理请求超时？

**A**: 可以在前端设置请求超时：

```javascript
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 30000); // 30秒超时

try {
  const response = await fetch(url, {
    ...options,
    signal: controller.signal
  });
  clearTimeout(timeoutId);
  return await response.json();
} catch (error) {
  if (error.name === 'AbortError') {
    throw new Error('Request timeout');
  }
  throw error;
}
```

### Q2: 对话历史应该包含多少条消息？

**A**: 建议包含最近 10-20 条消息，既能提供足够的上下文，又不会让请求过大。系统会自动处理消息内容。

### Q3: RAG增强和普通模式有什么区别？

**A**: 
- **RAG增强模式** (`use_rag: true`): 系统会从知识库检索相关信息，生成更准确、更符合知识库内容的建议
- **普通模式** (`use_rag: false`): 仅基于对话历史和客户数据生成建议，速度更快但可能不够准确

建议在重要场景下使用RAG增强模式。

### Q4: 如何判断RAG系统是否可用？

**A**: 可以调用 `GET /rag/status` 接口检查系统状态。如果 `status` 为 `"就绪"`，则可以使用RAG功能。

### Q5: 消息中的 `role` 字段有哪些可选值？

**A**: 
- `"customer"`: 客户消息
- `"agent"`: 客服消息
- `"群聊成员"`: 群聊中的成员消息（群聊场景）

### Q6: 如何处理接口返回的错误？

**A**: 所有接口在出错时都会返回标准的错误响应，包含 `detail` 字段说明错误原因。前端应该捕获这些错误并给用户友好的提示。

---

## 更新日志

### v1.0 (2025-12-01)
- 初始版本发布
- 支持AI建议生成、反馈提交、建议采纳等核心功能
- 支持RAG增强模式
- 支持Excel数据关联

---

## 相关文档

- [Postman 测试指南](./POSTMAN_GUIDE.md) - Postman 接口测试说明
- [配置文档](./CONFIG.md) - 环境变量配置说明
- [项目 README](../README.md) - 项目总体说明

---

## 技术支持

如有问题或建议，请联系后端开发团队。

