# FastAPI框架规范

FastAPI项目结构应遵循以下原则：
1. **模块化设计**：按照功能模块组织代码，提高可维护性
2. **清晰分层**：分离路由、业务逻辑和数据模型
3. **版本控制**：对API进行版本管理，确保向后兼容性
4. **可扩展性**：便于添加新功能和模块
5. **一致性**：与Python项目结构规范保持一致

## 2. 路由设计
路由设计应遵循通用API设计规范（参考 `api_design.md`），以下是FastAPI特定的路由实现规范：

- **路由文件组织**: 每个功能模块对应一个路由文件，如`api/v1/users.py`
- **路由前缀**: 为每个版本设置统一的路由前缀
- **路由标签**: 使用 `tags` 参数为路由分组，便于文档组织


### 3.1 FastAPI Pydantic模型示例
```python
# core/schemas/user.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    name: str
    email: EmailStr
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
```

## 4. 依赖管理
- **依赖注入**: 使用FastAPI的`Depends`进行依赖注入
- **数据库会话**: 提供数据库会话的依赖函数
- **权限认证**: 实现认证和授权的依赖函数

### 4.1 依赖函数示例
```python
# core/database/__init__.py
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncIterator

from core.database.connection import AsyncSessionLocal

async def get_session() -> AsyncIterator[AsyncSession]:
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

## 5. 中间件
- **全局中间件**: 应用于所有请求和响应
- **功能中间件**: 实现日志记录、性能监控、CORS等功能




## 6. 错误处理
- **HTTP异常**: 使用`HTTPException`处理API异常
- **自定义异常**: 创建自定义异常类处理业务逻辑异常
- **异常处理中间件**: 统一处理所有异常，返回一致的错误格式

### 6.1 异常处理示例
```python
# core/core/exceptions.py
from fastapi import HTTPException, status

class CustomException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)

def not_found_exception(detail: str = "资源未找到") -> CustomException:
    return CustomException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

def forbidden_exception(detail: str = "权限不足") -> CustomException:
    return CustomException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

def bad_request_exception(detail: str = "请求参数错误") -> CustomException:
    return CustomException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

# core/main.py
@app.exception_handler(CustomException)
async def custom_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "message": exc.detail, "data": None}
    )
```

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
- **请求限流**: 使用slowapi等库实现API请求限流
- **压缩响应**: 启用GZip压缩提高响应速度

### 8.1 异步操作示例
```python
# core/services/user_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from core.models.user import User
from core.schemas.user import UserCreate

class UserService:
    async def get_users(self, session: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
        result = await session.execute(select(User).offset(skip).limit(limit))
        return result.scalars().all()
    
    async def get_user(self, session: AsyncSession, user_id: int) -> Optional[User]:
        return await session.get(User, user_id)
    
    async def create_user(self, session: AsyncSession, user: UserCreate) -> User:
        db_user = User(**user.dict())
        session.add(db_user)
        await session.flush()
        return db_user
```

## 9. 测试规范
- **测试框架**: 使用`pytest`进行测试
- **异步测试**: 使用`pytest-asyncio`插件进行异步测试
- **API测试**: 使用`httpx`库测试API端点
- **测试文件结构**: 测试文件与源代码文件结构保持一致


## 10. 最佳实践
- **单一职责原则**: 每个路由文件和服务类只负责一个功能
- **依赖注入**: 避免直接在路由中实例化服务类
- **配置管理**: 使用环境变量管理配置，避免硬编码
- **日志记录**: 为所有重要操作添加日志
- **类型注解**: 必须为所有函数和参数添加类型注解
- **代码风格**: 遵循PEP 8代码风格指南
- **安全设计**: 实现认证、授权和输入验证