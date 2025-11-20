# API接口设计规范

## 6. RESTful API设计

### 6.1 API设计原则

#### 6.1.1 统一接口规范
- **协议：** HTTPS
- **格式：** JSON
- **版本：** URL路径版本控制（/api/v1/）
- **编码：** UTF-8
- **时区：** UTC

#### 6.1.2 资源命名规范
- 使用复数名词表示资源集合
- 使用小写字母，多个单词用连字符连接
- 避免动词，使用HTTP方法表示操作

```
正确示例：
GET /api/v1/documents          # 获取文档列表
GET /api/v1/documents/{id}     # 获取特定文档
POST /api/v1/documents         # 创建文档
PUT /api/v1/documents/{id}     # 更新文档
DELETE /api/v1/documents/{id}   # 删除文档
```

#### 6.1.3 响应格式规范
**成功响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    // 具体数据
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "uuid-123456"
}
```

**错误响应：**
```json
{
  "code": 400,
  "message": "Invalid request parameters",
  "error": {
    "type": "ValidationError",
    "details": {
      "field": "filename",
      "message": "Filename is required"
    }
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "uuid-123456"
}
```

### 6.2 接口详细设计

#### 6.2.1 文档管理接口

**上传文档**
```http
POST /api/v1/documents
Content-Type: multipart/form-data

请求参数：
- file: 文件 (required)
- metadata: JSON字符串 (optional)
- tags: 标签数组 (optional)

响应：
{
  "code": 201,
  "message": "Document uploaded successfully",
  "data": {
    "document_id": 123,
    "filename": "example.pdf",
    "file_size": 1048576,
    "file_hash": "sha256:abc123...",
    "upload_time": "2024-01-01T12:00:00Z",
    "processing_status": "pending",
    "quality_score": 0.95
  }
}
```

**获取文档列表**
```http
GET /api/v1/documents?page=1&size=20&status=processed&sort=-created_at

查询参数：
- page: 页码 (default: 1)
- size: 每页数量 (default: 20, max: 100)
- status: 处理状态 (pending, processing, processed, failed)
- type: 文档类型 (pdf, word, txt, html)
- start_date: 开始时间 (ISO 8601)
- end_date: 结束时间 (ISO 8601)
- sort: 排序字段 (+asc, -desc)

响应：
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "document_id": 123,
        "filename": "example.pdf",
        "file_size": 1048576,
        "file_type": "pdf",
        "status": "processed",
        "created_at": "2024-01-01T12:00:00Z",
        "updated_at": "2024-01-01T12:30:00Z"
      }
    ],
    "total": 150,
    "page": 1,
    "size": 20,
    "pages": 8
  }
}
```

**获取文档详情**
```http
GET /api/v1/documents/{document_id}

响应：
{
  "code": 200,
  "message": "success",
  "data": {
    "document_id": 123,
    "filename": "example.pdf",
    "file_size": 1048576,
    "file_type": "pdf",
    "file_hash": "sha256:abc123...",
    "metadata": {
      "title": "Document Title",
      "author": "Author Name",
      "pages": 10
    },
    "processing_status": "processed",
    "processing_time": 45.2,
    "text_chunks": 25,
    "extracted_entities": 150,
    "extracted_relations": 200,
    "quality_score": 0.95,
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:30:00Z"
  }
}
```

**删除文档**
```http
DELETE /api/v1/documents/{document_id}

响应：
{
  "code": 200,
  "message": "Document deleted successfully",
  "data": {
    "document_id": 123,
    "deleted_at": "2024-01-01T12:00:00Z"
  }
}
```

#### 6.2.2 知识图谱接口

**获取实体列表**
```http
GET /api/v1/entities?type=Person&name=John&page=1&size=20

查询参数：
- type: 实体类型
- name: 实体名称（支持模糊匹配）
- confidence_min: 最小置信度
- source: 数据来源
- sort: 排序字段
- page: 页码
- size: 每页数量

响应：
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "entity_id": 456,
        "name": "John Doe",
        "type": "Person",
        "description": "Software engineer at Tech Corp",
        "confidence": 0.95,
        "source": "document_123",
        "created_at": "2024-01-01T12:00:00Z",
        "attributes": {
          "occupation": "Software Engineer",
          "company": "Tech Corp",
          "location": "San Francisco"
        }
      }
    ],
    "total": 500,
    "page": 1,
    "size": 20,
    "pages": 25
  }
}
```

**获取关系列表**
```http
GET /api/v1/relations?subject_type=Person&predicate=works_at&object_type=Organization

查询参数：
- subject_id: 主体实体ID
- subject_type: 主体实体类型
- predicate: 关系谓词
- object_id: 客体实体ID
- object_type: 客体实体类型
- confidence_min: 最小置信度

响应：
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "relation_id": 789,
        "subject": {
          "entity_id": 456,
          "name": "John Doe",
          "type": "Person"
        },
        "predicate": "works_at",
        "object": {
          "entity_id": 789,
          "name": "Tech Corp",
          "type": "Organization"
        },
        "description": "John Doe works at Tech Corp as a software engineer",
        "confidence": 0.92,
        "source": "document_123",
        "created_at": "2024-01-01T12:00:00Z"
      }
    ],
    "total": 1200,
    "page": 1,
    "size": 20,
    "pages": 60
  }
}
```

**图谱查询接口**
```http
POST /api/v1/graph/query
Content-Type: application/json

请求体：
{
  "query_type": "path_finding",
  "start_entity_id": 456,
  "end_entity_id": 789,
  "max_depth": 3,
  "relationship_types": ["works_at", "located_in"],
  "options": {
    "include_attributes": true,
    "confidence_threshold": 0.8
  }
}

响应：
{
  "code": 200,
  "message": "success",
  "data": {
    "paths": [
      {
        "path_id": "path_1",
        "length": 2,
        "entities": [
          {"entity_id": 456, "name": "John Doe", "type": "Person"},
          {"entity_id": 789, "name": "Tech Corp", "type": "Organization"}
        ],
        "relationships": [
          {
            "relation_id": 101,
            "predicate": "works_at",
            "confidence": 0.92
          }
        ],
        "confidence": 0.92
      }
    ],
    "total_paths": 1,
    "query_time": 0.245
  }
}
```

#### 6.2.3 向量搜索接口

**语义搜索**
```http
POST /api/v1/search/semantic
Content-Type: application/json

请求体：
{
  "query": "人工智能在医疗领域的应用",
  "search_type": "similar_documents",
  "top_k": 10,
  "filters": {
    "document_type": ["pdf", "word"],
    "date_range": {
      "start": "2023-01-01",
      "end": "2024-01-01"
    }
  },
  "options": {
    "include_text_snippets": true,
    "highlight_matches": true
  }
}

响应：
{
  "code": 200,
  "message": "success",
  "data": {
    "results": [
      {
        "document_id": 123,
        "filename": "ai_healthcare.pdf",
        "score": 0.95,
        "relevance": "high",
        "text_snippets": [
          {
            "text": "人工智能在医疗诊断中的应用越来越广泛...",
            "score": 0.92,
            "position": 150
          }
        ],
        "metadata": {
          "author": "Dr. Smith",
          "pages": 25
        }
      }
    ],
    "total_results": 50,
    "query_time": 0.156,
    "search_id": "search_123456"
  }
}
```

**实体搜索**
```http
POST /api/v1/search/entities
Content-Type: application/json

请求体：
{
  "query": "机器学习专家",
  "entity_types": ["Person", "Organization"],
  "top_k": 20,
  "filters": {
    "confidence_min": 0.8,
    "created_after": "2023-01-01"
  }
}

响应：
{
  "code": 200,
  "message": "success",
  "data": {
    "results": [
      {
        "entity": {
          "entity_id": 456,
          "name": "Andrew Ng",
          "type": "Person",
          "description": "Machine learning expert and entrepreneur"
        },
        "score": 0.98,
        "matches": [
          {
            "field": "description",
            "matched_text": "machine learning expert",
            "score": 0.95
          }
        ],
        "related_entities": [
          {
            "entity_id": 789,
            "name": "Stanford University",
            "type": "Organization",
            "relationship": "affiliated_with"
          }
        ]
      }
    ],
    "total_results": 15,
    "query_time": 0.089
  }
}
```

#### 6.2.4 知识抽取接口

**触发知识抽取**
```http
POST /api/v1/extraction/trigger
Content-Type: application/json

请求体：
{
  "document_ids": [123, 124, 125],
  "extraction_config": {
    "extract_entities": true,
    "extract_relations": true,
    "extract_attributes": true,
    "entity_types": ["Person", "Organization", "Location"],
    "relation_types": ["works_at", "located_in", "founded_by"],
    "confidence_threshold": 0.7,
    "use_llm_enhancement": true
  },
  "options": {
    "async_processing": true,
    "priority": "normal",
    "callback_url": "https://example.com/callback"
  }
}

响应：
{
  "code": 202,
  "message": "Extraction job accepted",
  "data": {
    "job_id": "job_123456",
    "status": "queued",
    "estimated_time": 300,
    "documents_count": 3,
    "tracking_url": "/api/v1/extraction/jobs/job_123456"
  }
}
```

**获取抽取任务状态**
```http
GET /api/v1/extraction/jobs/{job_id}

响应：
{
  "code": 200,
  "message": "success",
  "data": {
    "job_id": "job_123456",
    "status": "processing",
    "progress": {
      "total_documents": 3,
      "processed_documents": 2,
      "current_document": "document_124",
      "entities_extracted": 150,
      "relations_extracted": 200
    },
    "started_at": "2024-01-01T12:00:00Z",
    "estimated_completion": "2024-01-01T12:05:00Z",
    "results_preview": {
      "entities": [
        {"name": "John Doe", "type": "Person", "confidence": 0.95},
        {"name": "Tech Corp", "type": "Organization", "confidence": 0.92}
      ],
      "relations": [
        {"subject": "John Doe", "predicate": "works_at", "object": "Tech Corp", "confidence": 0.90}
      ]
    }
  }
}
```

#### 6.2.5 系统管理接口

**系统状态**
```http
GET /api/v1/system/status

响应：
{
  "code": 200,
  "message": "success",
  "data": {
    "system_status": "healthy",
    "version": "1.0.0",
    "uptime": 86400,
    "components": {
      "database": {"status": "healthy", "latency": 5},
      "vector_store": {"status": "healthy", "latency": 15},
      "llm_service": {"status": "healthy", "latency": 200}
    },
    "statistics": {
      "total_documents": 1250,
      "total_entities": 15600,
      "total_relations": 23400,
      "processing_queue": 5
    }
  }
}
```

**获取系统配置**
```http
GET /api/v1/system/config

响应：
{
  "code": 200,
  "message": "success",
  "data": {
    "extraction": {
      "entity_types": ["Person", "Organization", "Location", "Event"],
      "relation_types": ["works_at", "located_in", "founded_by", "participated_in"],
      "confidence_threshold": 0.7,
      "batch_size": 10
    },
    "vector_search": {
      "embedding_model": "text-embedding-ada-002",
      "similarity_threshold": 0.8,
      "max_results": 100
    },
    "processing": {
      "max_file_size": 52428800,
      "supported_formats": ["pdf", "docx", "txt", "html"],
      "quality_threshold": 0.7
    }
  }
}
```

### 6.3 错误处理规范

#### 6.3.1 错误码定义
```python
class ErrorCode:
    # 2xx Success
    SUCCESS = 200
    CREATED = 201
    ACCEPTED = 202
    
    # 4xx Client Error
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    TOO_MANY_REQUESTS = 429
    
    # 5xx Server Error
    INTERNAL_ERROR = 500
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504
```

#### 6.3.2 错误响应格式
```json
{
  "code": 400,
  "message": "Validation failed",
  "error": {
    "type": "ValidationError",
    "code": "INVALID_PARAMETER",
    "message": "One or more parameters are invalid",
    "details": [
      {
        "field": "filename",
        "message": "Filename cannot be empty",
        "value": ""
      },
      {
        "field": "file_size",
        "message": "File size exceeds maximum limit of 50MB",
        "value": 104857600,
        "limit": 52428800
      }
    ]
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "uuid-123456",
  "path": "/api/v1/documents",
  "method": "POST"
}
```

### 6.4 分页规范

#### 6.4.1 请求参数
```http
GET /api/v1/entities?page=2&size=50&sort=name,-created_at
```

- **page**: 页码，从1开始
- **size**: 每页数量，默认20，最大100
- **sort**: 排序字段，+asc升序，-desc降序

#### 6.4.2 响应格式
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [...],
    "pagination": {
      "page": 2,
      "size": 50,
      "total": 1250,
      "pages": 25,
      "has_next": true,
      "has_prev": true,
      "next_page": 3,
      "prev_page": 1,
      "first_page": 1,
      "last_page": 25
    }
  }
}
```

### 6.5 限流规范

#### 6.5.1 限流策略
- **匿名用户**: 100 requests/minute
- **认证用户**: 1000 requests/minute
- **批量操作**: 10 requests/minute

#### 6.5.2 限流响应
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1640995200

{
  "code": 429,
  "message": "Rate limit exceeded",
  "error": {
    "type": "RateLimitError",
    "retry_after": 60,
    "limit": 100,
    "window": "1 minute"
  }
}
```