# 大模型调用核心类文档

## 1. 系统概述

本文档描述了基于LangChain实现的大模型调用核心类系统，该系统提供了统一、高效、可靠的大语言模型调用接口，支持多种模型提供商、提示词管理、错误处理和重试策略。

### 主要特性

- **统一接口**：提供一致的API接口，支持多种大模型提供商
- **提示词管理**：支持从文件系统加载、管理和格式化提示词模板
- **错误处理**：完善的错误处理机制，自动转换和分类各类异常
- **重试策略**：智能重试机制，支持指数退避和条件重试
- **异步支持**：支持同步和异步调用模式
- **统计监控**：内置调用统计和健康检查功能
- **配置管理**：灵活的配置加载和更新机制

## 2. 目录结构

```
app/llm/
├── __init__.py          # 模块初始化文件
├── base.py              # 基础抽象类定义
├── llm_client.py        # LangChain大模型客户端实现
├── llm_service.py       # 集成服务层
├── prompt_manager.py    # 提示词管理器
├── error_handler.py     # 错误处理器
├── exceptions.py        # 异常类定义
└── logging_utils.py     # 日志工具
```

## 3. 快速开始

### 3.1 安装依赖

确保项目已安装必要的依赖：

```bash
pip install langchain openai
```

### 3.2 基本使用

```python
from app.llm import LLMService

# 初始化服务（单例模式）
service = LLMService()

# 生成文本
response = service.generate_text("请简要介绍人工智能的发展历程")
print(response)

# 使用提示词模板
template_response = service.generate_text_with_template(
    "summarize",
    content="这是一段需要总结的长文本...",
    max_length=200
)
print(template_response)
```

## 4. 核心组件

### 4.1 LLMService

集成服务层，提供高级API接口，是与大模型交互的主要入口。

**主要方法**：
- `generate_text(prompt, **kwargs)`: 生成文本
- `generate_text_with_template(template_name, **variables)`: 使用模板生成文本
- `generate_batch(prompts, **kwargs)`: 批量生成文本
- `validate_template(template_name, **variables)`: 验证模板变量
- `health_check()`: 健康检查
- `get_stats()`: 获取统计信息
- `get_available_templates()`: 获取可用模板

### 4.2 PromptManager

提示词管理器，负责从文件系统加载和管理提示词模板。

**主要方法**：
- `get_prompt(prompt_name)`: 获取提示词内容
- `format_prompt(prompt_name, **variables)`: 格式化提示词
- `add_prompt(prompt_name, content)`: 添加新提示词
- `update_prompt(prompt_name, content)`: 更新提示词
- `delete_prompt(prompt_name)`: 删除提示词
- `get_all_prompts()`: 获取所有提示词名称
- `prompt_exists(prompt_name)`: 检查提示词是否存在

### 4.3 LLMClient

基于LangChain实现的大模型客户端，负责与具体的大模型服务交互。

**主要方法**：
- `generate(prompt, **kwargs)`: 生成文本
- `generate_with_template(template_name, **variables)`: 使用模板生成
- `generate_batch(prompts, **kwargs)`: 批量生成
- `update_config(config)`: 更新配置
- `validate_config(config)`: 验证配置
- `get_config()`: 获取配置
- `health_check()`: 健康检查

### 4.4 ErrorHandler

错误处理器，提供统一的错误处理、重试策略和异常转换功能。

**主要方法**：
- `handle_error(exc, context=None)`: 处理异常
- `should_retry(exc, retry_config=None)`: 判断是否应该重试
- `get_retry_delay(attempt, retry_config=None)`: 计算重试延迟

**装饰器**：
- `retry(retry_config=None)`: 重试装饰器
- `catch_and_log(fallback_value=None, re_raise=False)`: 异常捕获装饰器
- `validate_arguments(**validators)`: 参数验证装饰器

## 5. 详细使用示例

### 5.1 基本文本生成

```python
from app.llm import LLMService

# 初始化服务
service = LLMService()

# 简单生成
response = service.generate_text("解释量子计算的基本原理")
print(f"生成结果: {response}")

# 使用额外参数
response = service.generate_text(
    "写一首关于人工智能的诗",
    temperature=0.8,  # 控制输出的随机性
    max_tokens=500    # 限制最大生成长度
)
print(f"诗歌生成: {response}")
```

### 5.2 使用提示词模板

**步骤1: 创建提示词文件**

在`/Users/lixuze/wordspace/financialKG/prompt`目录下创建提示词文件：

`summarize.txt`:
```
请将以下文本总结为简洁的摘要（不超过{max_length}字）：

{content}
```

**步骤2: 使用模板**

```python
from app.llm import LLMService

service = LLMService()

# 使用模板生成
long_text = "人工智能（Artificial Intelligence，简称AI）是计算机科学的一个分支，
它试图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器，
该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。"

# 使用模板生成摘要
summary = service.generate_text_with_template(
    "summarize",  # 模板名称（不含扩展名）
    content=long_text,
    max_length=100
)

print(f"摘要: {summary}")

# 验证模板变量
validation = service.validate_template(
    "summarize",
    content="测试内容"
)
print(f"模板验证结果: {validation}")
```

### 5.3 批量生成

```python
from app.llm import LLMService

service = LLMService()

# 准备多个提示词
prompts = [
    "解释机器学习的基本概念",
    "什么是深度学习？",
    "大语言模型的工作原理是什么？"
]

# 批量生成
responses = service.generate_batch(prompts)

# 处理结果
for i, response in enumerate(responses):
    print(f"问题 {i+1}: {prompts[i]}")
    print(f"回答 {i+1}: {response}")
    print("---")
```

### 5.4 异步使用

```python
import asyncio
from app.llm import LLMService

async def main():
    service = LLMService()
    
    # 异步生成
    response = await service.generate_text_async(
        "异步生成的示例文本"
    )
    print(f"异步生成结果: {response}")
    
    # 异步批量生成
    prompts = ["问题1", "问题2", "问题3"]
    responses = await service.generate_batch_async(prompts)
    print(f"异步批量结果: {responses}")

# 运行异步函数
asyncio.run(main())
```

### 5.5 错误处理

```python
from app.llm import LLMService
from app.llm.exceptions import (
    GenerationError,
    PromptError,
    RateLimitError,
    ServiceUnavailableError
)

service = LLMService()

try:
    # 尝试生成
    response = service.generate_text("测试错误处理")
    
except PromptError as e:
    print(f"提示词错误: {e}")
except RateLimitError as e:
    print(f"速率限制错误，建议{getattr(e, 'retry_after', '稍后')}后重试")
except ServiceUnavailableError as e:
    print(f"服务不可用: {e}")
except GenerationError as e:
    print(f"生成失败: {e}")
except Exception as e:
    print(f"未知错误: {e}")
```

### 5.6 使用错误处理器装饰器

```python
from app.llm.error_handler import retry_on_llm_error, safe_llm_call
from app.llm import LLMService

service = LLMService()

# 使用重试装饰器
@retry_on_llm_error(max_retries=3, base_delay=1.0)
def generate_with_retry(prompt):
    return service.generate_text(prompt)

# 使用安全调用装饰器
@safe_llm_call(fallback_value="生成失败，请稍后重试")
def generate_safely(prompt):
    return service.generate_text(prompt)

# 使用示例
try:
    result = generate_with_retry("可能失败的请求")
    print(f"重试后的结果: {result}")
except Exception as e:
    print(f"所有重试都失败了: {e}")

# 安全调用（不会抛出异常）
safe_result = generate_safely("可能失败的请求")
print(f"安全调用结果: {safe_result}")
```

## 6. 配置管理

系统使用ConfigManager加载和管理配置，主要配置项包括：

- **provider**: 模型提供商，如"openai"
- **model**: 模型名称，如"gpt-3.5-turbo"
- **temperature**: 生成温度，控制输出随机性
- **max_tokens**: 最大生成长度
- **timeout**: 请求超时时间
- **api_key**: API密钥
- **retry_attempts**: 重试次数
- **retry_delay**: 重试延迟时间

### 动态更新配置

```python
from app.llm import LLMService
from app.config.config_manager import LLMConfig

service = LLMService()

# 创建新配置
new_config = LLMConfig(
    provider="openai",
    model="gpt-4",  # 切换到更高级的模型
    temperature=0.5,
    max_tokens=2000,
    api_key="new-api-key"
)

# 更新服务配置（通过访问底层client）
service._client.update_config(new_config)

# 验证新配置
is_valid = service._client.validate_config(new_config)
print(f"配置有效性: {is_valid}")
```

## 7. 监控和统计

### 健康检查

```python
from app.llm import LLMService

service = LLMService()

# 执行健康检查
health_status = service.health_check()

print(f"服务状态: {health_status['status']}")
print(f"模型: {health_status['model']}")
print(f"响应时间: {health_status['response_time']:.2f}秒")

if health_status['status'] == 'unhealthy':
    print(f"错误信息: {health_status.get('error', '未知错误')}")
```

### 调用统计

```python
from app.llm import LLMService

service = LLMService()

# 执行一些调用
service.generate_text("测试统计1")
service.generate_text("测试统计2")

# 获取统计信息
stats = service.get_stats()

print(f"总调用次数: {stats['total_calls']}")
print(f"成功调用: {stats['successful_calls']}")
print(f"失败调用: {stats['failed_calls']}")
print(f"总消耗token: {stats['total_tokens']}")
print(f"成功率: {stats['success_rate']:.2f}%")

# 清除统计信息
service.clear_stats()
print(f"清除后调用次数: {service.get_stats()['total_calls']}")
```

## 8. 提示词管理

### 直接使用PromptManager

```python
from app.llm.prompt_manager import PromptManager

# 初始化提示词管理器
prompt_dir = "/Users/lixuze/wordspace/financialKG/prompt"
prompt_manager = PromptManager(prompt_dir=prompt_dir)

# 列出所有可用提示词
templates = prompt_manager.get_all_prompts()
print(f"可用提示词: {templates}")

# 添加新提示词
prompt_manager.add_prompt(
    "new_template",
    "这是一个新的提示词模板，包含变量：{variable}"
)

# 格式化提示词
formatted = prompt_manager.format_prompt(
    "new_template",
    variable="测试值"
)
print(f"格式化后的提示词: {formatted}")

# 更新提示词
prompt_manager.update_prompt(
    "new_template",
    "更新后的模板，包含变量：{variable} 和 {new_var}"
)

# 删除提示词
prompt_manager.delete_prompt("new_template")
```

## 9. 最佳实践

### 9.1 提示词设计

- **清晰具体**：提示词应明确表达任务需求
- **结构化**：使用分隔符和标题增强可读性
- **变量命名**：使用有意义的变量名，避免冲突
- **模板复用**：将通用提示词抽象为可复用模板

### 9.2 错误处理最佳实践

- **使用装饰器**：对关键操作使用retry_on_llm_error装饰器
- **分层异常处理**：区分不同类型的错误并分别处理
- **日志记录**：记录错误详情以便调试
- **降级策略**：为关键服务实现降级方案

### 9.3 性能优化

- **批量调用**：尽量使用批量API减少请求次数
- **缓存结果**：对相同输入缓存生成结果
- **控制tokens**：合理设置max_tokens避免浪费
- **异步操作**：对IO密集型任务使用异步API

### 9.4 安全注意事项

- **API密钥保护**：不要在代码中硬编码API密钥
- **输入验证**：对用户输入进行严格验证
- **速率限制**：实现客户端速率限制避免触发API限制
- **内容过滤**：对生成内容进行适当过滤

## 10. 常见问题

### Q: 如何添加新的模型提供商支持？
A: 继承BaseLLMService类，实现相应的接口方法，然后在LLMClient中添加提供商的条件分支。

### Q: 如何自定义重试策略？
A: 创建自定义的RetryConfig对象，然后使用@retry_on_llm_error装饰器时传入该配置。

### Q: 提示词模板支持哪些文件格式？
A: 默认支持.txt和.md格式，可以在PromptManager中扩展支持更多格式。

### Q: 如何监控大模型调用的性能？
A: 使用LLMService的get_stats()方法获取调用统计，或集成外部监控工具。

### Q: 系统支持哪些异步框架？
A: 系统使用Python标准的asyncio库，可与任何兼容asyncio的框架配合使用。