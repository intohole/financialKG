# Core 模块 - 知识图谱核心处理引擎

## 模块概述

Core模块是知识图谱系统的核心处理引擎，提供基于大模型的内容分析、实体关系提取、内容摘要生成、实体消歧等核心功能。该模块采用模块化设计，支持可扩展的提示词参数构建机制，为上层应用提供统一的AI能力接口。

## 核心架构

### 1. 服务层 (Services)
- **BaseService**: 抽象基类，提供大模型调用和响应处理的基础能力
- **ContentProcessor**: 内容处理器，提供内容分类和实体关系提取功能
- **ContentSummarizer**: 内容摘要器，提供单文本和批量文本摘要生成
- **EntityAnalyzer**: 实体分析器，提供实体消歧、相似度比较和语义关联分析

### 2. 模型层 (Models)
定义了统一的数据模型和结构：
- **Entity**: 实体模型，表示知识图谱中的实体
- **Relation**: 关系模型，表示实体间的关系
- **KnowledgeGraph**: 知识图谱模型，包含实体和关系集合
- **ContentClassification/ContentClassificationResult**: 内容分类结果模型
- **ContentSummary**: 内容摘要结果模型
- **EntityResolutionResult**: 实体消歧结果模型
- **EntityComparisonResult**: 实体比较结果模型
- **SimilarEntityResult**: 相似实体结果模型

### 3. 参数构建层 (Parameter Builders)
提供可扩展的提示词参数构建机制：
- **PromptParameterBuilder**: 抽象基类，定义参数构建接口
- **DefaultParameterBuilder**: 默认参数构建器
- **ClassificationParameterBuilder**: 分类任务参数构建器
- **EntityRelationParameterBuilder**: 实体关系提取参数构建器
- **CompositeParameterBuilder**: 复合参数构建器，组合多个构建器

## 核心类和接口

### BaseService (base_service.py)
```python
class BaseService:
    """基础服务类，提供大模型调用和响应处理功能"""
    
    def __init__(self, llm_service: Optional[LLMService] = None)
    async def generate_with_prompt(self, prompt_key: str, **kwargs) -> str
    def extract_json_from_response(self, response: str) -> Optional[Dict[str, Any]]
    def extract_json_array_from_response(self, response: str) -> Optional[List[Dict[str, Any]]]
    def validate_response_data(self, data: Dict[str, Any], required_fields: List[str]) -> bool
    def parse_llm_response(self, response: str) -> dict  # 抽象方法
```

### ContentProcessor (content_processor.py)
```python
class ContentProcessor(BaseService):
    """内容处理器，提供内容分类和实体关系提取功能"""
    
    def __init__(self, llm_service: Optional[LLMService] = None, 
                 parameter_builder: Optional[PromptParameterBuilder] = None)
    
    # 内容分类
    async def classify_content(self, text: str, categories: Optional[List[str]] = None) -> ContentClassificationResult
    async def classify_content_with_config(self, text: str, category_config: Optional[Dict[str, Dict]] = None) -> ContentClassificationResult
    
    # 实体关系提取
    async def extract_entities_and_relations(self, text: str, entity_types: Optional[List[str]] = None, relation_types: Optional[List[str]] = None) -> KnowledgeExtractionResult
    async def extract_entities_and_relations_enhanced(self, text: str, entity_types: Optional[List[str]] = None, relation_types: Optional[List[str]] = None) -> KnowledgeExtractionResult
    async def extract_knowledge_graph(self, text: str, entity_types: Optional[List[str]] = None, relation_types: Optional[List[str]] = None) -> KnowledgeGraph
    
    # 批处理
    async def process_batch_content(self, texts: List[str], batch_size: int = 5) -> List[KnowledgeExtractionResult]
```

### ContentSummarizer (content_summarizer.py)
```python
class ContentSummarizer(BaseService):
    """内容摘要器，提供单文本和批量文本摘要生成功能"""
    
    def __init__(self, llm_service: Optional[LLMService] = None)
    
    # 单文本摘要
    async def summarize_content(self, text: str, max_length: Optional[int] = None) -> ContentSummary
    async def generate_summary_with_keywords(self, text: str, max_keywords: int = 10) -> ContentSummary
    
    # 批量摘要
    async def summarize_batch_content(self, texts: List[str], batch_size: int = 5) -> List[ContentSummary]
    
    # 摘要评估
    def evaluate_summary_quality(self, original_text: str, summary: str, keywords: List[str]) -> Dict[str, float]
```

### EntityAnalyzer (entity_analyzer.py)
```python
class EntityAnalyzer(BaseService):
    """实体分析器，提供实体关系判断和语义关联分析功能"""
    
    def __init__(self, llm_service: Optional[LLMService] = None)
    
    # 实体消歧
    async def resolve_entity_ambiguity(self, entity: Entity, candidate_entities: List[Entity]) -> EntityResolutionResult
    
    # 实体比较
    async def compare_entities(self, entities: List[Entity]) -> List[EntityComparisonResult]
    
    # 相似实体查找
    async def find_similar_entities(self, target_entity: Entity, candidate_entities: List[Entity], similarity_threshold: float = 0.7) -> List[SimilarEntityResult]
```

## 使用方式

### 1. 基本初始化
```python
from app.core import ContentProcessor, ContentSummarizer, EntityAnalyzer
from app.llm.llm_service import LLMService

# 初始化LLM服务
llm_service = LLMService()

# 初始化核心处理器
content_processor = ContentProcessor(llm_service=llm_service)
summarizer = ContentSummarizer(llm_service=llm_service)
entity_analyzer = EntityAnalyzer(llm_service=llm_service)
```

### 2. 内容分类
```python
# 简单分类
text = "苹果公司发布了新款iPhone，股价上涨了5%"
result = await content_processor.classify_content(text)
print(f"分类结果: {result.category.value}, 置信度: {result.confidence}")

# 自定义分类
custom_categories = ["科技", "金融", "医疗", "教育"]
result = await content_processor.classify_content(text, categories=custom_categories)
```

### 3. 实体关系提取
```python
text = "苹果公司由史蒂夫·乔布斯创立，主要生产iPhone手机"

# 基础提取
result = await content_processor.extract_entities_and_relations(text)
print(f"提取到 {len(result.knowledge_graph.entities)} 个实体")
print(f"提取到 {len(result.knowledge_graph.relations)} 个关系")

# 增强提取（带默认实体和关系类型）
result = await content_processor.extract_entities_and_relations_enhanced(text)

# 自定义实体和关系类型
entity_types = ["公司", "人物", "产品"]
relation_types = ["创立", "生产", "投资"]
result = await content_processor.extract_entities_and_relations(
    text, entity_types=entity_types, relation_types=relation_types
)
```

### 4. 内容摘要生成
```python
text = "一篇很长的文章内容..."

# 生成摘要
summary = await summarizer.summarize_content(text)
print(f"摘要: {summary.summary}")
print(f"关键词: {summary.keywords}")
print(f"重要性评分: {summary.importance_score}")

# 带关键词的摘要
summary = await summarizer.generate_summary_with_keywords(text, max_keywords=8)

# 批量摘要
texts = ["文章1...", "文章2...", "文章3..."]
summaries = await summarizer.summarize_batch_content(texts)
```

### 5. 实体分析
```python
from app.core.models import Entity

# 实体消歧
target_entity = Entity(name="苹果", type="公司", description="科技公司")
candidates = [
    Entity(name="苹果公司", type="公司", description="科技公司"),
    Entity(name="苹果水果", type="食物", description="水果"),
    Entity(name="苹果音乐", type="服务", description="音乐服务")
]

result = await entity_analyzer.resolve_entity_ambiguity(target_entity, candidates)
if result.selected_entity:
    print(f"选择实体: {result.selected_entity.name}, 置信度: {result.confidence}")

# 实体比较
entities = [
    Entity(name="腾讯", type="公司", description="互联网公司"),
    Entity(name="阿里巴巴", type="公司", description="电商公司"),
    Entity(name="百度", type="公司", description="搜索引擎公司")
]
comparisons = await entity_analyzer.compare_entities(entities)
for comp in comparisons:
    print(f"{comp.entity1.name} vs {comp.entity2.name}: 相似度 {comp.similarity_score}")

# 查找相似实体
similar_entities = await entity_analyzer.find_similar_entities(
    target_entity, candidates, similarity_threshold=0.8
)
```

### 6. 批处理操作
```python
# 批量内容处理
texts = ["文本1...", "文本2...", "文本3..."]
results = await content_processor.process_batch_content(texts, batch_size=3)

# 批量摘要生成
summaries = await summarizer.summarize_batch_content(texts, batch_size=2)
```

### 7. 自定义参数构建器
```python
from app.core.prompt_parameter_builder import CompositeParameterBuilder, ClassificationParameterBuilder

# 创建自定义参数构建器
builder = CompositeParameterBuilder([
    ClassificationParameterBuilder(),
    # 可以添加自定义构建器
])

# 使用自定义构建器初始化处理器
processor = ContentProcessor(
    llm_service=llm_service,
    parameter_builder=builder
)
```

## 配置选项

### 环境变量
```bash
# LLM服务配置
LLM_PROVIDER=openai              # LLM提供商
OPENAI_API_KEY=your_api_key     # OpenAI API密钥
OPENAI_MODEL=gpt-4              # 使用的模型
MAX_TOKENS=4000                 # 最大token数
TEMPERATURE=0.3                 # 温度参数

# 处理配置
DEFAULT_BATCH_SIZE=5            # 默认批处理大小
MAX_SUMMARY_LENGTH=500          # 最大摘要长度
DEFAULT_SIMILARITY_THRESHOLD=0.7 # 默认相似度阈值
```

### 分类配置
```python
# 自定义分类配置
category_config = {
    "financial": {
        "name": "金融财经",
        "description": "金融、财经、股票、证券等相关内容",
        "entity_types": ["公司", "股票", "基金", "银行"],
        "relation_types": ["投资", "收购", "合并", "竞争"]
    },
    "technology": {
        "name": "科技互联网", 
        "description": "科技、互联网、人工智能等相关内容",
        "entity_types": ["公司", "产品", "技术", "平台"],
        "relation_types": ["开发", "收购", "合作", "竞争"]
    }
}
```

## 错误处理

模块定义了完善的错误处理机制：

```python
from app.core.models import ContentClassificationResult

# 处理分类结果
result = await content_processor.classify_content(text)
if not result.supported:
    print(f"内容不支持，原因: {result.reasoning}")

# 处理摘要结果
summary = await summarizer.summarize_content(text)
if not summary.success:
    print(f"摘要生成失败，错误: {summary.error}")

# 异常处理
try:
    result = await content_processor.extract_entities_and_relations(text)
except ValueError as e:
    print(f"参数错误: {e}")
except RuntimeError as e:
    print(f"处理错误: {e}")
```

## 性能优化建议

1. **批处理使用**：对于大量文本处理，使用批处理接口减少LLM调用次数
2. **缓存机制**：对频繁查询的结果实现缓存，避免重复调用LLM
3. **异步处理**：充分利用异步特性，提高并发处理能力
4. **参数优化**：根据具体场景调整temperature、max_tokens等参数
5. **模型选择**：根据任务复杂度选择合适的模型，平衡质量和成本

## 依赖关系

```
core/
├── base_service.py          # 基础服务抽象类
├── content_processor.py     # 内容处理器
├── content_summarizer.py    # 内容摘要器  
├── entity_analyzer.py      # 实体分析器
├── models.py               # 数据模型定义
├── prompt_parameter_builder.py  # 参数构建器
└── __init__.py            # 模块导出
```

**依赖模块**:
- `app.llm`: LLM服务模块，提供大模型调用能力
- `app.store`: 存储模块，提供数据持久化能力（可选）

## 设计原则

1. **单一职责原则**：每个类只负责一个核心功能
2. **开闭原则**：通过抽象类和接口支持功能扩展
3. **依赖倒置原则**：依赖抽象而非具体实现
4. **接口隔离原则**：提供精简的专用接口
5. **异步优先**：所有IO操作都采用异步实现

## 最佳实践

1. **错误处理**：始终检查返回结果的成功状态
2. **参数验证**：在调用前验证输入参数的有效性
3. **日志记录**：使用适当的日志级别记录关键操作
4. **性能监控**：监控LLM调用次数和响应时间
5. **资源管理**：合理管理LLM连接和资源生命周期

## 模块导出

```python
from app.core import (
    # 核心服务类
    ContentProcessor,           # 内容处理器
    ContentSummarizer,         # 内容摘要器
    EntityAnalyzer,            # 实体分析器
    
    # 数据模型
    ContentClassificationResult, # 内容分类结果
    ContentSummary,            # 内容摘要结果
    Entity,                    # 实体模型
    EntityResolutionResult,    # 实体消歧结果
    EntityComparisonResult,    # 实体比较结果
    SimilarEntityResult,       # 相似实体结果
    KnowledgeExtractionResult, # 知识提取结果
    Relation                   # 关系模型
)
```

## 版本信息

- **版本**: 1.0.0
- **最后更新**: 2024年
- **维护团队**: 知识图谱团队
- **文档状态**: 活跃维护