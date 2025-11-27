# 数据库操作规范

## 1. 数据库连接管理
- **连接选择**: 根据项目需求选择同步或异步数据库连接
- **连接配置**: 通过环境变量管理数据库连接信息
- **示例配置**:
  ```python
  # 异步数据库连接URL
  DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
  ```

## 2. 会话管理
- **使用上下文管理器**: 提供`session_scope`上下文管理器来管理数据库会话
- **示例实现**:
  ```python
  from typing import AsyncIterator
  from sqlalchemy.ext.asyncio import AsyncSession
  
  async def session_scope() -> AsyncIterator[AsyncSession]:
      """数据库会话上下文管理器"""
      async with AsyncSessionLocal() as session:
          try:
              yield session
              await session.commit()
          except Exception:
              await session.rollback()
              raise
  ```

## 3. 异步操作规范
- **所有数据库操作必须使用异步方式**
- **使用SQLAlchemy的异步API**: 如`AsyncSession`, `select`, `insert`, `update`, `delete`等
- **示例查询**:
  ```python
  from sqlalchemy import select
  
  async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
      result = await session.execute(select(User).where(User.id == user_id))
      return result.scalar_one_or_none()
  ```

## 4. 数据模型定义
- **使用SQLAlchemy的异步模型**
- **继承自Base类**: 所有数据模型必须继承自统一的Base类
- **示例模型**:
  ```python
  from sqlalchemy.ext.declarative import declarative_base
  from sqlalchemy import Column, Integer, String, DateTime
  from datetime import datetime
  
  Base = declarative_base()
  
  class User(Base):
      __tablename__ = "users"
      
      id = Column(Integer, primary_key=True, index=True)
      name = Column(String(100), index=True)
      email = Column(String(100), unique=True, index=True)
      created_at = Column(DateTime, default=datetime.utcnow)
  ```

## 5. 存储库模式
- **使用BaseRepository**: 所有数据访问类必须继承自BaseRepository
- **单一职责**: 每个存储库对应一个数据模型
- **示例实现**:
  ```python
  from typing import TypeVar, Generic, List, Optional
  from sqlalchemy.ext.asyncio import AsyncSession
  from sqlalchemy import select
  
  ModelType = TypeVar("ModelType")
  
  class BaseRepository(Generic[ModelType]):
      def __init__(self, model: Type[ModelType], session: AsyncSession):
          self.model = model
          self.session = session
      
      async def get(self, id: int) -> Optional[ModelType]:
          return await self.session.get(self.model, id)
      
      async def get_all(self) -> List[ModelType]:
          result = await self.session.execute(select(self.model))
          return result.scalars().all()
  ```

## 6. 事务处理
- **自动事务管理**: 使用`session_scope`上下文管理器自动处理事务
- **手动事务**: 复杂事务需要手动管理时，使用`session.begin()`和`session.commit()`
- **示例**:
  ```python
  async def create_user_and_post(session: AsyncSession, user_data: UserCreate, post_data: PostCreate) -> Tuple[User, Post]:
      async with session.begin():
          user = User(**user_data.dict())
          session.add(user)
          await session.flush()
          
          post = Post(**post_data.dict(), user_id=user.id)
          session.add(post)
          await session.flush()
          
      return user, post
  ```

## 7. 错误处理
- **捕获数据库特定异常**: 使用`SQLAlchemyError`捕获数据库操作异常
- **回滚事务**: 发生异常时必须回滚事务
- **转换为业务异常**: 将数据库异常转换为业务异常后再向上抛出
- **示例**:
  ```python
  from sqlalchemy.exc import SQLAlchemyError
  
  async def create_user(session: AsyncSession, user_data: UserCreate) -> User:
      try:
          user = User(**user_data.dict())
          session.add(user)
          await session.commit()
          await session.refresh(user)
          return user
      except SQLAlchemyError as e:
          await session.rollback()
          raise DatabaseError(f"创建用户失败: {e}") from e
  ```

## 8. 查询优化
- **使用索引**: 对经常查询的字段创建索引
- **限制查询结果**: 使用`limit`和`offset`实现分页
- **避免N+1查询**: 使用`join`或`selectinload`加载关联数据
- **示例**: 
  ```python
  from sqlalchemy.orm import selectinload
  
  async def get_user_with_posts(session: AsyncSession, user_id: int) -> Optional[User]:
      result = await session.execute(
          select(User)
          .where(User.id == user_id)
          .options(selectinload(User.posts))
      )
      return result.scalar_one_or_none()
  ```

## 9. 数据库迁移
- **使用Alembic**: 使用Alembic进行数据库迁移
- **迁移文件**: 所有迁移文件必须提交到版本控制系统
- **示例命令**:
  ```bash
  # 初始化Alembic
  alembic init migrations
  
  # 创建迁移文件
  alembic revision --autogenerate -m "create users table"
  
  # 执行迁移
  alembic upgrade head
  ```


## 11. 通用最佳实践
- **异步优先**: 推荐使用异步数据库操作以提高性能
- **ORM选择**: 根据项目需求选择合适的ORM框架
- **会话管理**: 始终使用上下文管理器管理数据库会话
- **分层设计**: 推荐使用存储库模式封装数据访问逻辑
