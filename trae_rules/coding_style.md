# Python代码风格与开发规范

## 代码风格规范

### 命名约定

- **变量和函数**：使用snake_case命名
  ```python
  user_name = 'john'
  def get_user_info():
      pass
  ```

- **类名**：使用PascalCase命名
  ```python
  class UserService:
      pass
  
  class ApiResponse:
      pass
  ```

- **常量**：使用SCREAMING_SNAKE_CASE
  ```python
  API_BASE_URL = 'https://api.example.com'
  MAX_RETRY_COUNT = 3
  ```

- **私有属性**：使用单下划线前缀
  ```python
  class User:
      def __init__(self):
          self._private_attr = None
          self.__very_private = None  # 名称改写
  ```

### 代码格式

- **行长度**：最大88字符（Black默认）
- **缩进**：使用4个空格，不使用Tab
- **空行规则**：
  - 顶级函数和类定义前后2个空行
  - 类内方法定义前后1个空行
  - 逻辑相关的代码块之间1个空行

- **导入规范**：
  ```python
  # 标准库
  import os
  import sys
  from pathlib import Path
  
  # 第三方库
  import requests
  from flask import Flask
  
  # 本地模块 （假设项目结构为 app/）
  from app.models import User
  from app.utils import logger
  ```

### 字符串和注释

- **字符串引号**：优先使用单引号，包含单引号时使用双引号
  ```python
  message = 'Hello world'
  quote = "He said 'Hello'"
  ```

- **文档字符串**：使用三重双引号
  ```python
  def calculate_total(items: list[dict]) -> float:
      """计算商品总价。
      
      Args:
          items: 商品列表，每个商品包含price字段
          
      Returns:
          商品总价
          
      Raises:
          ValueError: 当商品价格为负数时
      """
      pass
  ```

## 类型注解规范

### 基础类型注解

```python
from typing import List, Dict, Optional, Union, Callable
from collections.abc import Sequence, Mapping

# 基础类型
def process_data(data: str, count: int) -> bool:
    pass

# 容器类型（Python 3.9+）
def filter_users(users: list[dict]) -> list[dict]:
    pass

# 可选类型
def find_user(user_id: str) -> Optional[dict]:
    pass

# 联合类型（Python 3.10+）
def parse_value(value: str | int) -> float:
    pass
```

### 复杂类型注解

```python
from typing import TypeVar, Generic, Protocol
from dataclasses import dataclass

# 泛型
T = TypeVar('T')

class Repository(Generic[T]):
    def save(self, entity: T) -> T:
        pass

# 协议
class Drawable(Protocol):
    def draw(self) -> None:
        ...

# 数据类
@dataclass
class User:
    id: str
    name: str
    email: str
    age: Optional[int] = None
```

## 开发规范

### 错误处理

- **异常层次**：使用内置异常或自定义异常
  ```python
  class UserNotFoundError(ValueError):
      """用户未找到异常。"""
      pass
  
  def get_user(user_id: str) -> User:
      if not user_id:
          raise ValueError("User ID cannot be empty")
      
      user = database.find_user(user_id)
      if not user:
          raise UserNotFoundError(f"User {user_id} not found")
      
      return user
  ```

- **资源管理**：使用上下文管理器
  ```python
  # 文件操作
  with open('data.txt', 'r') as file:
      content = file.read()
  
  # 数据库连接
  with get_db_connection() as conn:
      result = conn.execute(query)
  ```

### 函数设计

- **纯函数优先**：避免副作用
- **参数设计**：使用关键字参数提高可读性
  ```python
  def create_user(
      name: str,
      email: str,
      *,  # 强制关键字参数
      age: Optional[int] = None,
      is_active: bool = True
  ) -> User:
      pass
  
  # 调用
  user = create_user(
      'John Doe',
      'john@example.com',
      age=25,
      is_active=True
  )
  ```

### 类设计

- **数据类优先**：简单数据结构使用dataclass
- **属性访问**：使用property装饰器
  ```python
  from dataclasses import dataclass
  from datetime import datetime
  
  @dataclass
  class User:
      name: str
      email: str
      created_at: datetime = None
      
      def __post_init__(self):
          if self.created_at is None:
              self.created_at = datetime.now()
      
      @property
      def display_name(self) -> str:
          return self.name.title()
  ```

## 工具配置

### Black配置（pyproject.toml）

```toml
[tool.black]
line-length = 88
target-version = ['py39']
include = '\.pyi?$'
extend-exclude = '''
(
  /(
      \.eggs
    | \.git
    | \.venv
    | build
    | dist
  )/
)
'''
```

### isort配置

```toml
[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["myproject"]
```

### pylint配置

```toml
[tool.pylint.messages_control]
disable = [
    "missing-docstring",
    "too-few-public-methods",
]

[tool.pylint.format]
max-line-length = 88
```

### mypy配置

```toml
[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
```

## 测试规范

### 测试文件组织

```
project/
├── src/
│   └── myproject/
│       ├── __init__.py
│       ├── models.py
│       └── services.py
└── tests/
    ├── __init__.py
    ├── test_models.py
    └── test_services.py
```

### 测试编写

```python
import pytest
from unittest.mock import Mock, patch

from myproject.services import UserService
from myproject.models import User

class TestUserService:
    """用户服务测试类。"""
    
    def setup_method(self):
        """每个测试方法前的设置。"""
        self.user_service = UserService()
    
    def test_create_user_with_valid_data(self):
        """测试使用有效数据创建用户。"""
        # Arrange
        user_data = {
            'name': 'John Doe',
            'email': 'john@example.com'
        }
        
        # Act
        result = self.user_service.create_user(user_data)
        
        # Assert
        assert isinstance(result, User)
        assert result.name == user_data['name']
        assert result.email == user_data['email']
    
    def test_create_user_with_invalid_email_raises_error(self):
        """测试使用无效邮箱创建用户抛出异常。"""
        user_data = {
            'name': 'John Doe',
            'email': 'invalid-email'
        }
        
        with pytest.raises(ValueError, match="Invalid email format"):
            self.user_service.create_user(user_data)
    
    @patch('myproject.services.database')
    def test_get_user_calls_database(self, mock_database):
        """测试获取用户调用数据库。"""
        # Arrange
        user_id = 'user123'
        mock_database.find_user.return_value = {'id': user_id}
        
        # Act
        self.user_service.get_user(user_id)
        
        # Assert
        mock_database.find_user.assert_called_once_with(user_id)
```

## 性能优化

### 数据结构选择

```python
# 大量查找操作使用set
valid_ids = {'id1', 'id2', 'id3'}
if user_id in valid_ids:  # O(1)
    pass

# 有序数据使用bisect
import bisect
sorted_list = [1, 3, 5, 7, 9]
index = bisect.bisect_left(sorted_list, 5)

# 计数操作使用Counter
from collections import Counter
counts = Counter(items)
```

### 内存优化

```python
# 使用生成器处理大数据
def process_large_file(filename: str):
    with open(filename, 'r') as file:
        for line in file:  # 逐行处理，不加载整个文件
            yield process_line(line)

# 使用__slots__减少内存占用
class Point:
    __slots__ = ['x', 'y']
    
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
```

## 代码审查清单

### 代码质量
- [ ] 遵循PEP 8代码规范
- [ ] 所有函数都有类型注解
- [ ] 文档字符串完整
- [ ] 没有未使用的导入
- [ ] 变量命名清晰

### 功能正确性
- [ ] 错误处理完善
- [ ] 边界条件考虑
- [ ] 测试覆盖率达标
- [ ] 没有硬编码值

### 性能考虑
- [ ] 算法复杂度合理
- [ ] 内存使用优化
- [ ] 避免不必要的循环
- [ ] 合理使用缓存

### 安全性
- [ ] 输入验证
- [ ] SQL注入防护
- [ ] 敏感信息保护
- [ ] 依赖包安全检查

版本：1.0.0 | 最后修改：2025-09-09