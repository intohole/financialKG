# 项目统一日志工具文档

## 概述

本项目统一日志工具提供了完整的日志管理解决方案，支持结构化日志、性能监控、异常追踪等功能。日志工具基于项目配置文件动态设置，确保整个项目使用统一的日志标准。

## 主要特性

- **统一配置管理**: 基于 `config.yaml` 文件统一配置日志系统
- **结构化日志**: 支持 JSON 格式的结构化日志输出
- **性能监控**: 内置性能监控装饰器和上下文管理器
- **异常追踪**: 详细的异常信息记录和追踪
- **模块化日志**: 支持不同模块的独立日志配置
- **请求追踪**: 支持请求ID追踪，便于问题定位
- **热重载**: 支持日志配置的动态更新

## 快速开始

### 1. 初始化日志系统

```python
from app.config.config_manager import ConfigManager
from app.utils.logging_utils import initialize_logging

# 初始化配置管理器
config_manager = ConfigManager()

# 初始化日志系统
initialize_logging(config_manager)
```

### 2. 获取日志器

```python
from app.utils.logging_utils import get_logger

# 获取模块日志器
logger = get_logger(__name__)

# 记录日志
logger.info("应用启动成功")
logger.error("发生错误")
```

## 核心功能

### 基本日志记录

```python
logger = get_logger(__name__)

# 基本日志级别
logger.debug("调试信息")
logger.info("普通信息")
logger.warning("警告信息")
logger.error("错误信息")
logger.critical("严重错误")

# 带上下文的日志
logger.log_with_context(
    logging.INFO,
    "用户操作",
    context={"user_id": "12345", "action": "login"}
)
```

### 异常日志记录

```python
try:
    # 可能出错的代码
    result = risky_operation()
except Exception as e:
    # 记录详细异常信息
    logger.log_error_with_details(
        e,
        "操作失败",
        context={"operation": "data_processing"}
    )
    
    # 或者使用便捷函数
    log_error_with_details(e, "操作失败")
```

### 性能监控

#### 使用装饰器

```python
from app.utils.logging_utils import performance_logger

@performance_logger("数据库查询")
def query_database():
    # 数据库操作
    return fetch_data()
```

#### 使用上下文管理器

```python
from app.utils.logging_utils import performance_context

def process_data():
    with performance_context("数据处理"):
        # 耗时操作
        heavy_computation()
```

#### 手动性能监控

```python
import time

start_time = time.time()
# 执行操作
operation()
duration_ms = (time.time() - start_time) * 1000

logger.log_performance("自定义操作", duration_ms, success=True)
```

### 数据库操作日志

```python
# 记录数据库操作
logger.log_database_operation(
    operation="SELECT",
    table="users",
    duration_ms=45.2,
    rows_affected=10,
    success=True,
    context={"query": "SELECT * FROM users"}
)

# 使用便捷函数
log_database_operation(
    operation="INSERT",
    table="orders",
    duration_ms=23.5,
    rows_affected=1,
    success=True
)
```

### 大模型操作日志

```python
# 记录LLM操作
logger.log_llm_operation(
    model="glm-4-flash",
    operation="文本生成",
    tokens_used={"prompt": 100, "completion": 50},
    cost=0.0012,
    duration_ms=1250.5,
    success=True,
    context={"temperature": 0.7}
)

# 使用便捷函数
log_llm_operation(
    model="embedding-3",
    operation="文本嵌入",
    tokens_used={"total": 200},
    cost=0.0008,
    duration_ms=850.3,
    success=True
)
```

### 向量操作日志

```python
# 记录向量操作
logger.log_vector_operation(
    operation="search",
    collection="financial_docs",
    dimension=1536,
    duration_ms=234.7,
    success=True,
    context={"top_k": 10, "metric": "cosine"}
)

# 使用便捷函数
log_vector_operation(
    operation="insert",
    collection="news_embeddings",
    dimension=1536,
    duration_ms=156.3,
    success=True
)
```

### 请求追踪

```python
from app.utils.logging_utils import set_request_id, clear_request_id

def handle_request(request_id: str):
    # 设置请求ID
    set_request_id(request_id)
    
    try:
        logger.info("开始处理请求")
        # 处理请求
        process_request()
        logger.info("请求处理完成")
        
    finally:
        # 清除请求ID
        clear_request_id()
```

## 配置说明

日志配置在 `config.yaml` 文件的 `logging` 部分：

```yaml
logging:
  version: 1
  disable_existing_loggers: false
  formatters:
    default:
      format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    detailed:
      format: "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s"
  handlers:
    console:
      class: "logging.StreamHandler"
      level: "INFO"
      formatter: "default"
      stream: "ext://sys.stdout"
    file:
      class: "logging.handlers.RotatingFileHandler"
      level: "DEBUG"
      formatter: "detailed"
      filename: "logs/financial_kg.log"
      maxBytes: 10485760  # 10MB
      backupCount: 5
  loggers:
    kg:
      level: "DEBUG"
      handlers: ["console", "file"]
      propagate: false
  root:
    level: "INFO"
    handlers: ["console"]
```

### 配置字段说明

- **formatters**: 日志格式化器配置
  - `default`: 默认格式
  - `detailed`: 详细格式，包含模块和函数信息
  
- **handlers**: 日志处理器配置
  - `console`: 控制台输出
  - `file`: 文件输出，支持日志轮转
  
- **loggers**: 特定logger配置
  - `kg`: 项目主logger，使用DEBUG级别
  
- **root**: 根logger配置

## 最佳实践

### 1. 模块级日志器

在每个模块的顶部创建日志器：

```python
# module.py
from app.utils.logging_utils import get_logger

logger = get_logger(__name__)

def function():
    logger.info("函数执行")
```

### 2. 上下文信息

记录关键操作的上下文信息：

```python
def process_user(user_id: str, action: str):
    context = {"user_id": user_id, "action": action}
    
    logger.info("处理用户操作", extra={"context": context})
    
    try:
        # 操作逻辑
        result = perform_action(user_id, action)
        logger.info("用户操作成功", extra={"context": context, "result": result})
        
    except Exception as e:
        logger.log_error_with_details(e, "用户操作失败", context)
```

### 3. 性能监控

对关键操作进行性能监控：

```python
@performance_logger("API调用")
def call_external_api(data: dict):
    # API调用逻辑
    return requests.post(api_url, json=data)
```

### 4. 错误处理

统一处理异常并记录详细信息：

```python
def safe_operation():
    try:
        risky_operation()
        
    except ValidationError as e:
        logger.warning(f"验证失败: {e}")
        
    except Exception as e:
        logger.log_error_with_details(e, "操作失败")
        raise
```

## 日志输出示例

### 控制台输出

```
2024-01-20 10:30:45,123 - app.module - INFO - 应用启动成功
2024-01-20 10:30:45,234 - app.module - DEBUG - 调试信息
2024-01-20 10:30:45,345 - app.module - WARNING - 警告信息
2024-01-20 10:30:45,456 - app.module - ERROR - 错误信息
```

### 文件输出（详细格式）

```
2024-01-20 10:30:45,123 - app.module - INFO - module - function - 应用启动成功
2024-01-20 10:30:45,234 - app.module - DEBUG - module - function - 调试信息
```

### 结构化日志

```json
{
  "timestamp": "2024-01-20T10:30:45.123456",
  "level": "INFO",
  "logger": "app.module",
  "message": "应用启动成功",
  "context": {
    "user_id": "12345",
    "action": "login"
  }
}
```

## 注意事项

1. **日志级别**: 根据环境选择合适的日志级别
   - 开发环境: DEBUG
   - 测试环境: INFO
   - 生产环境: WARNING 或 ERROR

2. **敏感信息**: 避免在日志中记录敏感信息（密码、密钥等）

3. **日志轮转**: 配置文件处理器支持自动日志轮转，防止日志文件过大

4. **性能影响**: 高频操作的日志记录要考虑性能影响

5. **异步日志**: 对于高并发场景，考虑使用异步日志处理器

## 故障排除

### 日志不显示

1. 检查日志级别设置
2. 确认日志处理器配置正确
3. 检查日志文件权限

### 配置文件错误

1. 检查 YAML 语法
2. 确认配置字段名称正确
3. 查看初始化时的错误信息

### 性能问题

1. 避免在循环中记录过多日志
2. 使用合适的日志级别
3. 考虑异步日志处理