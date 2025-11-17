# API设计规范

## 1. RESTful API 设计原则
- **资源命名**: 使用名词复数形式命名资源(如`/users`、`/posts`)
- **HTTP方法**: 使用HTTP方法表示操作类型
  - `GET`: 获取资源
  - `POST`: 创建资源
  - `PUT`: 更新资源(完整更新)
  - `PATCH`: 更新资源(部分更新)
  - `DELETE`: 删除资源
- **状态码**: 使用标准HTTP状态码
  - `200 OK`: 成功获取资源
  - `201 Created`: 成功创建资源
  - `204 No Content`: 成功删除或更新资源(无返回内容)
  - `400 Bad Request`: 请求参数错误
  - `401 Unauthorized`: 未授权访问
  - `403 Forbidden`: 权限不足
  - `404 Not Found`: 资源不存在
  - `500 Internal Server Error`: 服务器内部错误

## 2. 统一响应格式
- **成功响应**: 
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "id": 1,
      "name": "test",
      "email": "test@example.com"
    }
  }
  ```

- **列表响应**: 
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "items": [
        {"id": 1, "name": "test1"},
        {"id": 2, "name": "test2"}
      ],
      "total": 2,
      "page": 1,
      "size": 10
    }
  }
  ```

- **错误响应**: 
  ```json
  {
    "code": 400,
    "message": "参数错误",
    "data": null
  }
  ```

## 3. API版本管理
- **版本号**: 使用URL路径方式(如`/v1/users`)
- **版本更新**: 不兼容的API变更需要升级版本

## 4. 请求参数
- **查询参数**: 用于过滤、排序、分页等
- **路径参数**: 用于标识资源ID(如`/users/{id}`)
- **请求体**: 用于创建或更新资源(使用JSON格式)
- **验证**: 必须对所有请求参数进行验证

## 5. 认证与授权
- **认证方式**: JWT令牌认证
- **授权方式**: 基于角色的访问控制(RBAC)
- **安全头**: 使用HTTPS确保通信安全

## 6. 错误处理
- **统一错误格式**: 使用标准的JSON错误响应格式
- **错误信息**: 提供清晰的错误信息，帮助开发者定位问题
- **日志记录**: 记录所有API请求和错误信息

## 7. 分页设计
- **分页参数**: `page`(页码)、`size`(每页数量)
- **默认值**: 默认为第1页，每页10条记录
- **返回结果**: 包含总记录数、当前页码、每页数量和数据列表

## 8. 排序设计
- **排序参数**: `sort`(排序字段)、`order`(排序方向: asc/desc)
- **示例**: `/users?sort=created_at&order=desc`

## 9. 过滤设计
- **过滤参数**: 使用字段名作为参数名
- **示例**: `/users?name=test&email=test@example.com`

## 10. API文档
- **自动生成**: 使用FastAPI的自动文档生成功能
- **Swagger UI**: 提供交互式API文档
- **OpenAPI**: 提供OpenAPI规范

## 11. 性能优化
- **响应缓存**: 对频繁访问的API进行缓存
- **请求限制**: 对API请求进行限流
- **压缩**: 使用Gzip压缩响应

## 12. 测试要求
- **单元测试**: 对API的每个端点进行单元测试
- **集成测试**: 测试API与其他服务的集成
- **端到端测试**: 测试完整的API流程

## 13. 框架无关要求
- **异步支持**: 如果使用支持异步的框架，优先使用异步方式实现API端点
- **类型安全**: 建议使用类型注解或数据验证模型定义请求和响应
- **响应格式**: 统一使用JSON格式响应
- **框架选择**: 根据项目需求选择合适的API框架

## 14. 代码示例
```python
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="API", version="v1")

class UserCreate(BaseModel):
    name: str
    email: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: str

@app.post("/v1/users", status_code=201, response_model=UserResponse)
async def create_user(user: UserCreate):
    # 创建用户逻辑
    return UserResponse(
        id=1,
        name=user.name,
        email=user.email,
        created_at="2023-01-01T00:00:00Z"
    )

@app.get("/v1/users", response_model=List[UserResponse])
async def get_users(page: int = 1, size: int = 10):
    # 获取用户列表逻辑
    return [
        UserResponse(
            id=1,
            name="test",
            email="test@example.com",
            created_at="2023-01-01T00:00:00Z"
        )
    ]

@app.get("/v1/users/{id}", response_model=UserResponse)
async def get_user(id: int):
    # 获取用户逻辑
    return UserResponse(
        id=id,
        name="test",
        email="test@example.com",
        created_at="2023-01-01T00:00:00Z"
    )
```
