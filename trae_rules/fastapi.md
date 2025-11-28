# FastAPI框架规范

FastAPI项目结构应遵循以下原则：
1. **模块化设计**：按照功能模块组织代码，提高可维护性
2. **清晰分层**：分离路由、业务逻辑和数据模型
3. **版本控制**：对API进行版本管理，确保向后兼容性
4. **可扩展性**：便于添加新功能和模块
5. **一致性**：与Python项目结构规范保持一致

## 1. 路由设计
路由设计应遵循通用API设计规范（参考 `api_design.md`），以下是FastAPI特定的路由实现规范：

- **路由文件组织**: 每个功能模块对应一个路由文件，如`api/v1/users.py`
- **路由前缀**: 为每个版本设置统一的路由前缀
- **路由标签**: 使用 `tags` 参数为路由分组，便于文档组织

## 2. 请求与响应处理
请求与响应处理应遵循通用API设计规范（参考 `api_design.md`），以下是FastAPI特定的请求与响应处理规范：

- **请求体**: 使用Pydantic模型定义请求结构
- **响应模型**: 使用Pydantic模型定义响应结构
- **参数验证**: FastAPI自动验证请求参数（路径、查询、请求体）
- **类型注解**: 必须为所有函数和参数添加类型注解



## 4. 依赖管理
- **依赖注入**: 使用FastAPI的`Depends`进行依赖注入
- **数据库会话**: 提供数据库会话的依赖函数
- **权限认证**: 实现认证和授权的依赖函数



## 5. 中间件
- **全局中间件**: 应用于所有请求和响应
- **功能中间件**: 实现日志记录、性能监控、CORS等功能

### 5.1 中间件示例
```python
# core/main.py
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
import logging

app = FastAPI(title="My API", version="v1")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] ,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 自定义日志中间件
@app.middleware("http")
async def log_request(request, call_next):
    logging.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logging.info(f"Response: {response.status_code}")
    return response
```

## 6. 错误处理
- **HTTP异常**: 使用`HTTPException`处理API异常
- **自定义异常**: 创建自定义异常类处理业务逻辑异常
- **异常处理中间件**: 统一处理所有异常，返回一致的错误格式



## 7. 文档规范
- **自动文档**: FastAPI自动生成Swagger UI和Redoc文档
- **文档配置**: 在创建FastAPI实例时配置文档信息
- **API描述**: 为路由和模型添加详细描述

### 7.1 文档配置示例
```python
# core/main.py
from fastapi import FastAPI

app = FastAPI(
    title="我的API",
    version="v1",
    description="这是一个基于FastAPI的示例API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 路由描述示例
@app.get("/users/{user_id}", response_model=User, description="根据ID获取用户信息")
async def get_user(user_id: int, session: AsyncSession = Depends(get_session)):
    ...
```

## 8. 性能优化
- **异步操作**: 数据库操作和IO操作必须使用异步方式
- **响应缓存**: 使用FastAPI-Cache2等库实现API响应缓存
