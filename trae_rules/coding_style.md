# Python代码风格规范

## 1. PEP 8 基础规范
- **缩进**: 使用4个空格进行缩进，禁止使用制表符
- **行长度**: 每行代码最多120个字符
- **空行**: 模块级函数和类定义之间空两行，类内部方法定义之间空一行
- **导入**: 按标准库→第三方库→本地库的顺序导入，每组之间空一行

## 2. 类型注解
- **必须为所有函数和方法添加类型注解**
- **使用`typing`模块的类型**: 如`List`, `Dict`, `Optional`, `Any`, `Union`等
- **示例**:
  ```python
  def get_user(id: int) -> Optional[User]:
      pass
  
  async def create_post(data: PostCreate) -> Post:
      pass
  ```

## 3. 异步编程规范
- **正确使用`async/await`**: 异步函数必须用`async def`定义，调用时必须使用`await`
- **避免阻塞操作**: 在异步代码中禁止使用同步IO操作
- **异步选择**: 根据项目需求和技术栈选择同步或异步编程方式

## 4. 命名规范
- **类名**: 使用大驼峰式命名(如`UserRepository`)
- **函数/方法名**: 使用小写字母加下划线分隔(如`get_user_by_id`)
- **变量名**: 使用小写字母加下划线分隔(如`user_name`)
- **常量**: 使用全大写字母加下划线分隔(如`DATABASE_URL`)
- **模块名**: 使用小写字母加下划线分隔(如`user_repository`)

## 5. 注释和文档字符串
- **模块注释**: 每个模块开头添加模块说明
- **类注释**: 每个类添加文档字符串，说明类的作用
- **函数/方法注释**: 每个函数添加文档字符串，说明参数、返回值和功能
- **使用Google风格文档字符串**:
  ```python
  def get_user(id: int) -> Optional[User]:
      """
      根据ID获取用户
      
      Args:
          id: 用户ID
      
      Returns:
          Optional[User]: 用户对象或None
      """
      pass
  ```

## 6. 错误处理
- **使用特定异常**: 避免使用泛泛的`Exception`
- **自定义异常**: 为特定业务逻辑创建自定义异常
- **异常处理**: 仅捕获需要处理的异常，避免空的`except`块
- **示例**:
  ```python
  from sqlalchemy.exc import SQLAlchemyError
  
  async def create_user(user: UserCreate) -> User:
      try:
          db_user = User(**user.dict())
          db.add(db_user)
          await db.commit()
          await db.refresh(db_user)
          return db_user
      except SQLAlchemyError as e:
          await db.rollback()
          raise DatabaseError(f"创建用户失败: {e}")
  ```

## 7. 日志记录
- **使用Python标准库`logging`**
- **日志级别**: DEBUG(开发), INFO(正常), WARNING(警告), ERROR(错误), CRITICAL(严重错误)
- **日志格式**: 包含时间、级别、模块、函数名和消息
- **示例**:
  ```python
  import logging
  
  logger = logging.getLogger(__name__)
  
  async def get_user(id: int) -> Optional[User]:
      logger.debug(f"获取用户ID: {id}")
      user = await db.query(User).filter(User.id == id).first()
      if not user:
          logger.warning(f"未找到用户ID: {id}")
      return user
  ```

## 8. 模块结构
- **单一职责原则**: 每个模块只负责一个功能
- **避免循环导入**: 使用延迟导入或重构代码
- **__all__变量**: 明确导出的模块成员

## 9. 测试规范
- **测试文件命名**: `test_*.py`
- **测试框架**: 使用`pytest`
- **测试类型**: 单元测试、集成测试、端到端测试
- **异步测试**: 使用`pytest-asyncio`插件

## 10. 配置管理
- **环境变量**: 所有配置必须通过环境变量管理
- **禁止硬编码**: 禁止在代码中直接写入配置值
- **使用`python-dotenv`**: 本地开发时加载`.env`文件

## 11. 通用建议
- **Python版本**: 推荐使用Python 3.10+以利用最新特性
- **框架选择**: 根据项目需求选择合适的框架
- **遵循架构**: 遵循项目架构设计和技术栈选择
- **保持一致性**: 与团队约定的代码风格保持一致

## 12. 代码审查要点
- PEP 8合规性
- 类型注解完整性
- 异步操作正确性
- 错误处理的完整性
- 代码可读性和可维护性

## 13. package说明
- 在package下生成该package的说明文档 package.md，要求语言精炼，需要使用时进行查阅