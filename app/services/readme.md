# KG Query Service 包

知识图谱查询服务包，专为前端展示优化的数据API服务。

## 功能概述

本包提供知识图谱的数据查询服务，所有API都经过精心设计，确保对前端展示友好：

### 核心查询功能

1. **实体查询**
   - 实体列表分页查询（支持搜索、过滤、排序）
   - 实体详细信息查询（包含关联统计）

2. **关系查询**
   - 关系列表查询（支持按实体和关系类型过滤）
   - 关系网络展示（包含源实体和目标实体信息）

3. **实体网络分析**
   - 实体深度遍历（广度优先搜索）
   - 邻居网络构建（适合图可视化）
   - 支持关系类型过滤和遍历深度控制

4. **实体-新闻关联**
   - 实体关联新闻查询（支持时间范围过滤）
   - 多实体共同新闻分析（交集查询）
   - 新闻相关实体推荐（按相关性排序）

### 前端友好特性

- **统一分页格式**：所有列表查询返回统一的分页数据结构
- **图数据格式**：网络查询返回nodes和edges格式，直接支持图可视化库
- **时间格式化**：所有时间字段自动转换为ISO格式字符串
- **内容截断**：长文本自动截断，适合前端展示
- **统计信息**：提供关联数据的统计信息，便于前端展示

## 使用方式

### 基本使用

```python
from app.database.manager import DatabaseManager
from app.services.kg_query_service import KGQueryService

# 获取数据库会话
session = await DatabaseManager.get_session()

# 创建查询服务
query_service = KGQueryService(session)

# 查询实体列表
entities = await query_service.get_entity_list(
    page=1,
    page_size=20,
    search="人工智能",
    entity_type="技术"
)

# 查询实体网络
network = await query_service.get_entity_neighbors(
    entity_id=123,
    depth=2,
    max_entities=50
)
```

### FastAPI集成

```python
from fastapi import APIRouter, Depends
from app.services.kg_query_service import KGQueryService
from app.database.manager import DatabaseManager

router = APIRouter()

@router.get("/entities")
async def get_entities(
    page: int = 1,
    page_size: int = 20,
    search: str = None,
    db_session = Depends(DatabaseManager.get_session)
):
    query_service = KGQueryService(db_session)
    return await query_service.get_entity_list(
        page=page,
        page_size=page_size,
        search=search
    )
```

## API设计原则

1. **性能优化**：使用JOIN查询减少数据库访问次数
2. **分页支持**：所有列表查询都支持分页，防止大数据量问题
3. **灵活过滤**：支持多种过滤条件组合
4. **错误处理**：完善的异常捕获和日志记录
5. **数据安全**：自动截断敏感或过长内容

## 扩展建议

- 可以添加缓存机制提升查询性能
- 支持更复杂的关系网络分析算法
- 添加实体重要性评分机制
- 支持自定义排序和过滤规则