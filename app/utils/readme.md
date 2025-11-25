# Utils Package

## 核心功能描述

工具类模块集合，提供项目中通用的工具函数和辅助功能。

## 模块说明

### json_extractor.py
- **功能**: JSON提取器，专门用于与大模型交互的场景中稳健地提取JSON数据
- **主要函数**:
  - `extract_json_with_langchain()`: 使用LangChain的JsonOutputParser提取JSON
  - `extract_json_fallback()`: 备用JSON提取方法
  - `extract_json_robust()`: 稳健的JSON提取方法，结合LangChain和备用方法

### logging_utils.py
- **功能**: 日志工具，提供统一的日志记录功能
- **主要函数**:
  - `get_logger()`: 获取配置好的logger实例

## 使用方式

```python
# JSON提取示例
from app.utils.json_extractor import extract_json_robust

json_data = extract_json_robust(llm_response_text)
if json_data:
    # 处理提取到的JSON数据
    pass

# 日志记录示例
from app.utils.logging_utils import get_logger

logger = get_logger(__name__)
logger.info("日志信息")
```

## 设计原则

1. **通用性**: 工具函数应具有通用性，不依赖具体业务逻辑
2. **健壮性**: 提供错误处理和降级机制
3. **可测试性**: 工具函数应易于单元测试
4. **文档完善**: 每个函数都应有详细的文档字符串