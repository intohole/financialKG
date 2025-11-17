# 通用LLM开发规范

## 1. 服务架构

### 1.1 核心组件设计
- **LLMService**：统一LLM服务入口，提供所有LLM相关功能的封装
- **EntityExtractionService**：实体抽取组件，负责从文本中提取结构化实体
- **RelationExtractionService**：关系抽取组件，负责提取实体间的语义关系
- **SummaryGenerationService**：文本摘要组件，负责生成文本摘要

### 1.2 技术栈选择
- LLM框架：LangChain、LlamaIndex等（根据项目需求选择）
- 结构化输出：JSONSchema、Pydantic等
- 类型支持：Python 3.9+（建议3.10+）

### 1.3 FastAPI集成示例
```python
# core/services/llm_service.py
from fastapi import Depends
from typing import Optional
from langchain import OpenAI
from pydantic import BaseModel

class LLMService:
    def __init__(self):
        self.llm = OpenAI(temperature=0.7)
    
    def generate_summary(self, text: str, max_tokens: int = 100) -> str:
        """生成文本摘要"""
        prompt = f"请将以下文本总结为{max_tokens}字以内的内容：\n{text}"
        return self.llm(prompt)

# 依赖注入
async def get_llm_service() -> LLMService:
    return LLMService()

# core/api/v1/llm.py
from fastapi import APIRouter, Depends
from core.services.llm_service import LLMService, get_llm_service

router = APIRouter(prefix="/v1/llm", tags=["llm"])

@router.post("/summary")
async def generate_summary(
    text: str, 
    max_tokens: Optional[int] = 100, 
    llm_service: LLMService = Depends(get_llm_service)
):
    """生成文本摘要"""
    summary = llm_service.generate_summary(text, max_tokens)
    return {"summary": summary}
```

## 2. 方法设计规范

### 2.1 方法命名原则
- 使用清晰、描述性的命名，体现方法的核心功能
- 采用动词+名词的命名风格，如：`extract_entities`, `generate_summary`, `analyze_sentiment`
- 避免使用缩写或模糊词汇

### 2.2 参数设计规范
- **必填参数前置**：将核心业务参数放在前面
- **默认参数合理**：为非必填参数提供合理的默认值
- **类型标注明确**：使用Python类型注解明确参数类型
- **输入验证**：对所有输入参数进行有效性验证

### 2.3 返回值设计规范
- **结构化输出**：优先使用Pydantic模型或字典返回结构化数据
- **统一格式**：遵循API设计规范的响应格式
- **错误明确**：遇到错误时抛出具体的异常类型，而非返回None

### 2.4 异步支持
- 对于IO密集型的LLM调用，必须提供异步方法
- 异步方法命名以`async_`为前缀，如：`async_extract_entities`

## 3. 提示工程规范

### 3.1 提示设计原则
1. **任务明确**：清晰说明LLM需要完成的具体任务
2. **约束清晰**：明确实体类型、关系类型等范围限制
3. **格式严格**：定义精确的输出格式要求
4. **示例引导**：提供符合要求的输出示例
5. **安全约束**：限制输出仅包含所需内容

### 3.2 通用提示示例
```json
{
  "system_prompt": "你是一个专业的实体抽取工具，能够从文本中提取指定类型的实体...",
  "entity_types": ["人物", "组织", "地点", "时间", "产品"],
  "output_format": {
    "entities": [
      {
        "name": "实体名称",
        "type": "实体类型",
        "attributes": {}
      }
    ]
  }
}
```

## 4. 输入输出格式规范

### 4.1 实体格式
```json
{
  "name": "实体名称",
  "type": "实体类型",
  "attributes": {
    "属性名": "属性值"
  }
}
```

### 4.2 关系格式
```json
{
  "subject": "主语实体",
  "object": "宾语实体",
  "relation_type": "关系类型",
  "attributes": {
    "属性名": "属性值"
  }
}
```

### 4.3 响应格式
```json
{
  "status": "success/error",
  "data": {},
  "message": "操作结果描述"
}
```

## 5. 错误处理规范

### 5.1 错误处理原则
1. **全面捕获**：对所有LLM调用和数据处理过程进行异常捕获
2. **详细日志**：记录错误信息、输入参数和上下文环境
3. **友好响应**：向调用者返回清晰的错误类型和描述
4. **快速恢复**：实现必要的降级策略

## 6. 性能优化规范

### 6.1 缓存策略
- **请求缓存**：对相同或相似的LLM请求进行缓存
- **结果缓存**：缓存LLM生成的结果，设置合理的过期时间
- **缓存键设计**：包含模型版本、提示词和输入参数等关键信息

### 6.2 批量处理
- 对批量请求进行合并处理，减少API调用次数
- 合理设置批量大小，平衡性能和延迟

### 6.3 模型优化
- 根据业务需求选择合适的模型大小和版本
- 使用模型量化、蒸馏等技术优化推理性能

### 6.4 令牌管理
- 限制输入令牌数量，避免超过模型上限
- 对长文本进行分段处理，确保完整语义
- 对输出令牌数量进行限制，防止生成过长内容

## 7. 安全与合规规范

### 7.1 数据隐私
- **输入过滤**：对输入文本进行敏感信息过滤
- **数据匿名**：对涉及个人信息的文本进行匿名化处理
- **输出检查**：对LLM生成的内容进行隐私检查

### 7.2 内容安全
- **有害内容过滤**：对LLM生成的内容进行有害信息检测
- **版权合规**：确保生成内容不侵犯知识产权
- **伦理规范**：避免生成违反伦理道德的内容

### 7.3 API密钥管理
- **环境变量存储**：将API密钥存储在环境变量中，禁止硬编码
- **密钥轮换**：定期轮换API密钥，提高安全性
- **权限控制**：限制API密钥的使用范围和权限

## 8. 测试与验证规范

### 8.1 提示词测试
- 对提示词进行多场景测试，确保输出符合预期
- 测试边缘输入情况，如空文本、超长文本等
- 维护测试用例库，定期执行回归测试

### 8.2 输出验证
- 使用JSON Schema或Pydantic模型验证输出格式
- 对输出内容的准确性和完整性进行验证

### 8.3 性能测试
- 测试LLM服务的响应时间和吞吐量
- 模拟高并发场景，确保系统稳定性

### 8.4 安全测试
- 测试输入的安全性，防止注入攻击
- 测试输出的安全性，防止生成有害内容

## 9. 通用最佳实践

1. **可配置性**：通过配置文件或环境变量管理LLM参数
2. **日志记录**：使用统一的日志框架记录所有操作
3. **监控告警**：实现LLM服务的监控和告警机制
4. **文档完善**：为所有公共方法提供详细的文档注释
5. **版本控制**：对提示词和模型版本进行管理
6. **持续优化**：定期评估和优化LLM性能