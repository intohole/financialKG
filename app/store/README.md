# Core Store Module

## 概述

Core Store模块是知识图谱系统的核心存储层，提供统一的数据存储和检索接口。该模块采用分层架构设计，实现了实体、关系、新闻事件等数据的CRUD操作，同时集成了向量索引和混合搜索能力。

## 核心架构

### 1. 抽象层 (Abstract Layer)

#### StoreBase - 存储抽象基类
- **文件**: `store_base_abstract.py`
- **功能**: 定义统一的存储接口规范
- **核心数据模型**:
  - `Entity`: 实体数据模型
  - `Relation`: 关系数据模型  
  - `NewsEvent`: 新闻事件数据模型
  - `SearchResult`: 搜索结果模型
  - `StoreConfig`: 存储配置模型

#### 核心接口方法
```python
# 实体操作
async def create_entity(self, entity: Entity) -> Entity
async def get_entity(self, entity_id: int) -> Optional[Entity]
async def update_entity(self, entity_id: int, updates: Dict[str, Any]) -> Entity
async def delete_entity(self, entity_id: int) -> bool
async def search_entities(self, query: str, ...) -> List[SearchResult]

# 关系操作
async def create_relation(self, relation: Relation) -> Relation
async def get_relation(self, relation_id: int) -> Optional[Relation]
async def get_entity_relations(self, entity_id: int, ...) -> List[Relation]
async def delete_relation(self, relation_id: int) -> bool

# 新闻事件操作
async def create_news_event(self, news_event: NewsEvent) -> NewsEvent
async def get_news_event(self, news_event_id: int) -> Optional[NewsEvent]
async def search_news_events(self, query: str, ...) -> List[SearchResult]

# 向量操作
async def add_to_vector_index(self, content: str, ...) -> str
async def search_vectors(self, query: str, ...) -> List[SearchResult]

# 事务管理
async def begin_transaction(self) -> None
async def commit_transaction(self) -> None
async def rollback_transaction(self) -> None

# 健康检查
async def health_check(self) -> Dict[str, Any]
```

### 2. 实现层 (Implementation Layer)

#### HybridStoreCore - 核心存储实现
- **文件**: `hybrid_store_core_implement.py`
- **功能**: 提供完整的存储实现，支持混合存储（数据库+向量索引）
- **设计原则**:
  - 单一职责：只提供基础存储能力
  - 业务逻辑上移：复杂业务逻辑由服务层处理
  - 接口清晰：明确定义输入输出
  - 异常处理：统一的异常处理机制

#### 核心能力
1. **实体CRUD**: 创建、读取、更新、删除实体
2. **关系CRUD**: 创建、读取、更新、删除关系
3. **新闻事件CRUD**: 创建、读取、更新、删除新闻事件
4. **向量操作**: 添加、搜索向量
5. **事务管理**: 开始、提交、回滚事务
6. **健康检查**: 检查存储系统状态

#### HybridStore - 向后兼容类
- **文件**: `hybrid_store_compat.py`
- **功能**: 保持向后兼容性，继承自HybridStoreCore

### 3. 工具层 (Utility Layer)

#### VectorIndexManager - 向量索引管理器
- **文件**: `vector_index_manage.py`
- **功能**: 核心向量操作管理
- **核心方法**:
  - `add_to_index()`: 添加到向量索引
  - `update_vector()`: 更新向量
  - `delete_vector()`: 删除向量
  - `search_vectors()`: 向量搜索
  - `get_vector_count()`: 获取向量数量

#### DataConverter - 数据转换工具
- **文件**: `store_data_convert.py`
- **功能**: 负责数据库模型和业务模型之间的转换
- **转换方法**:
  - `db_entity_to_entity()`: 数据库实体转业务实体
  - `entity_to_db_entity()`: 业务实体转数据库实体
  - `db_relation_to_relation()`: 数据库关系转业务关系
  - `relation_to_db_relation()`: 业务关系转数据库关系

### 4. 异常定义 (Exception Layer)

#### Store层异常体系
- **文件**: `store_exceptions_define.py`
- **异常类**:
  - `StoreError`: 存储层基础异常
  - `EntityNotFoundError`: 实体不存在异常
  - `RelationNotFoundError`: 关系不存在异常
  - `VectorStoreError`: 向量存储异常
  - `MetadataStoreError`: 元数据存储异常
  - `ValidationError`: 数据验证异常
  - `ConnectionError`: 数据库连接异常
  - `TransactionError`: 事务处理异常

## 使用方式

### 1. 基本初始化

```python
from app.store import HybridStore
from app.database.manager import DatabaseManager
from app.vector.chroma_vector_search import ChromaVectorSearch
from app.embedding import EmbeddingService

# 初始化组件
db_manager = DatabaseManager()
vector_store = ChromaVectorSearch()
embedding_service = EmbeddingService()

# 创建存储实例
store = HybridStore(
    db_manager=db_manager,
    vector_store=vector_store,
    embedding_service=embedding_service
)

# 初始化存储
await store.initialize()
```

### 2. 实体操作

```python
from app.store.store_base_abstract import Entity
from datetime import datetime

# 创建实体
entity = Entity(
    name="苹果公司",
    type="公司",
    description="全球知名科技公司",
    created_at=datetime.now()
)

created_entity = await store.create_entity(entity)
print(f"创建实体ID: {created_entity.id}")

# 获取实体
fetched_entity = await store.get_entity(created_entity.id)
print(f"实体名称: {fetched_entity.name}")

# 更新实体
updates = {"description": "全球领先的科技创新公司"}
updated_entity = await store.update_entity(created_entity.id, updates)

# 删除实体
success = await store.delete_entity(created_entity.id)
print(f"删除成功: {success}")
```

### 3. 关系操作

```python
from app.store.store_base_abstract import Relation

# 创建关系
relation = Relation(
    subject_id=1,  # 主体实体ID
    predicate="拥有",
    object_id=2,   # 客体实体ID
    description="苹果公司拥有iPhone产品线"
)

created_relation = await store.create_relation(relation)

# 获取实体关系
relations = await store.get_entity_relations(1)
for relation in relations:
    print(f"关系: {relation.predicate} -> 实体ID: {relation.object_id}")

# 删除关系
success = await store.delete_relation(created_relation.id)
```

### 4. 新闻事件操作

```python
from app.store.store_base_abstract import NewsEvent

# 创建新闻事件
news_event = NewsEvent(
    title="苹果发布新产品",
    content="苹果公司今日发布了最新的iPhone系列...",
    source="科技日报",
    publish_time=datetime.now()
)

created_news = await store.create_news_event(news_event)

# 搜索新闻事件
search_results = await store.search_news_events("苹果 iPhone")
for result in search_results:
    print(f"新闻标题: {result.news_event.title}")
```

### 5. 混合搜索

```python
# 实体搜索 - 支持向量和全文搜索
results = await store.search_entities(
    query="科技公司",
    entity_type="公司",
    top_k=10,
    include_vector_search=True,
    include_full_text_search=True
)

for result in results:
    if result.entity:
        print(f"实体: {result.entity.name}, 分数: {result.score}")

# 向量搜索
vector_results = await store.search_vectors(
    query="人工智能",
    content_type="entity",
    top_k=5
)

for result in vector_results:
    print(f"向量搜索结果: {result.get('content')}")
```

### 6. 事务管理

```python
# 使用事务确保数据一致性
try:
    await store.begin_transaction()
    
    # 执行多个操作
    entity1 = await store.create_entity(entity1_data)
    entity2 = await store.create_entity(entity2_data)
    relation = await store.create_relation(relation_data)
    
    # 提交事务
    await store.commit_transaction()
    print("事务提交成功")
    
except Exception as e:
    # 回滚事务
    await store.rollback_transaction()
    print(f"事务回滚: {e}")
```

### 7. 异步上下文管理器

```python
# 使用异步上下文管理器自动管理资源
async with HybridStore(db_manager, vector_store, embedding_service) as store:
    await store.initialize()
    
    # 执行存储操作
    entity = await store.create_entity(entity_data)
    results = await store.search_entities("查询内容")
    
    # 自动关闭连接
```

## 配置选项

### StoreConfig 配置模型

```python
from app.store.store_base_abstract import StoreConfig

config = StoreConfig(
    vector_store_config={
        "collection_name": "knowledge_graph",
        "embedding_model": "text-embedding-ada-002"
    },
    metadata_store_config={
        "database_url": "sqlite:///knowledge_graph.db",
        "echo": False
    },
    enable_vector_index=True,
    enable_full_text_search=True,
    sync_mode="async"  # async, sync, eventual
)

await store.initialize(config)
```

## 错误处理

```python
from app.store.store_exceptions_define import (
    EntityNotFoundError,
    RelationNotFoundError,
    StoreError
)

try:
    entity = await store.get_entity(999)
    if not entity:
        raise EntityNotFoundError(999)
        
except EntityNotFoundError as e:
    print(f"实体不存在: {e.entity_id}")
    
except StoreError as e:
    print(f"存储操作失败: {e}")
    
except Exception as e:
    print(f"未知错误: {e}")
```

## 性能优化建议

1. **批量操作**: 对于大量数据操作，考虑使用批量接口
2. **索引优化**: 合理配置向量索引参数，平衡精度和性能
3. **缓存策略**: 在业务层实现缓存机制，减少重复查询
4. **连接池**: 使用数据库连接池管理连接资源
5. **异步并发**: 充分利用异步特性，提高并发处理能力

## 模块导出

```python
from app.store import (
    HybridStore,           # 主存储类（向后兼容）
    HybridStoreCore,       # 核心存储实现
    DataConverter,         # 数据转换工具
    VectorIndexManager     # 向量索引管理器
)
```

## 依赖关系

- **数据库层**: `app.database.*` - 提供数据持久化能力
- **向量层**: `app.vector.*` - 提供向量存储和搜索能力
- **嵌入层**: `app.embedding.*` - 提供文本嵌入能力
- **异常定义**: `app.store.store_exceptions_define` - 统一异常处理

## 设计原则

1. **单一职责**: 每个类只负责特定的功能领域
2. **接口隔离**: 通过抽象基类定义清晰的接口契约
3. **依赖倒置**: 依赖抽象而不是具体实现
4. **开闭原则**: 对扩展开放，对修改关闭
5. **异常处理**: 统一异常体系，提供清晰的错误信息
6. **异步优先**: 所有操作都采用异步实现
7. **类型安全**: 充分使用类型注解提高代码质量

## 扩展指南

要扩展存储功能，可以：

1. **继承StoreBase**: 实现自定义的存储后端
2. **扩展数据模型**: 在抽象层添加新的数据模型
3. **自定义搜索**: 实现特定的搜索算法和策略
4. **插件机制**: 通过依赖注入添加新的功能模块