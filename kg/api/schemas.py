import json
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field, field_validator

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """统一API响应格式"""
    success: bool = Field(..., description="请求是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")
    code: int = Field(200, description="响应状态码")
    timestamp: int = Field(..., description="时间戳")

    class Config:
        populate_by_name = True
        from_attributes = True


class EntityBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=500, description="实体名称")
    entity_type: str = Field(
        ..., alias="type", min_length=1, max_length=100, description="实体类型"
    )
    canonical_name: Optional[str] = Field(
        None, max_length=500, description="规范实体名称"
    )
    entity_group_id: Optional[int] = Field(None, description="实体分组ID")
    weight: float = Field(1.0, description="实体权重")
    source: Optional[str] = Field(None, max_length=100, description="实体来源")
    properties: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="实体属性"
    )

    @field_validator("properties", mode="before")
    @classmethod
    def validate_properties(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        elif v is None:
            return {}
        elif isinstance(v, dict):
            return v
        else:
            return {}


class EntityCreate(EntityBase):
    pass


class EntityUpdate(BaseModel):
    name: Optional[str] = Field(
        None, min_length=1, max_length=500, description="实体名称"
    )
    entity_type: Optional[str] = Field(
        None, min_length=1, max_length=100, description="实体类型"
    )
    canonical_name: Optional[str] = Field(
        None, max_length=500, description="规范实体名称"
    )
    entity_group_id: Optional[int] = Field(None, description="实体分组ID")
    weight: Optional[float] = Field(None, description="实体权重")
    source: Optional[str] = Field(None, max_length=100, description="实体来源")
    properties: Optional[Dict[str, Any]] = Field(None, description="实体属性")


class Entity(EntityBase):
    id: int = Field(..., description="实体ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True
        populate_by_name = True


class RelationBase(BaseModel):
    source_entity_id: int = Field(..., description="源实体ID")
    target_entity_id: int = Field(..., description="目标实体ID")
    relation_type: str = Field(
        ..., min_length=1, max_length=200, description="关系类型"
    )
    canonical_relation: Optional[str] = Field(
        None, max_length=200, description="规范关系类型"
    )
    relation_group_id: Optional[int] = Field(None, description="关系分组ID")
    weight: float = Field(1.0, description="关系权重")
    source: Optional[str] = Field(None, max_length=100, description="关系来源")
    properties: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="关系属性"
    )

    @field_validator("source_entity_id")
    def source_not_equal_target(cls, v, info):
        target_entity_id = info.data.get("target_entity_id")
        if target_entity_id is not None and v == target_entity_id:
            raise ValueError("源实体ID和目标实体ID不能相同")
        return v

    @field_validator("properties", mode="before")
    @classmethod
    def validate_properties(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        elif v is None:
            return {}
        elif isinstance(v, dict):
            return v
        else:
            return {}


class RelationCreate(RelationBase):
    pass


class RelationUpdate(BaseModel):
    relation_type: Optional[str] = Field(
        None, min_length=1, max_length=200, description="关系类型"
    )
    canonical_relation: Optional[str] = Field(
        None, max_length=200, description="规范关系类型"
    )
    relation_group_id: Optional[int] = Field(None, description="关系分组ID")
    weight: Optional[float] = Field(None, description="关系权重")
    source: Optional[str] = Field(None, max_length=100, description="关系来源")
    properties: Optional[Dict[str, Any]] = Field(None, description="关系属性")


class Relation(RelationBase):
    id: int = Field(..., description="关系ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class NewsBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500, description="新闻标题")
    content: str = Field(..., min_length=1, description="新闻内容")
    url: Optional[str] = Field(None, max_length=500, description="新闻URL")
    source: Optional[str] = Field(None, max_length=100, description="新闻来源")
    publish_time: Optional[datetime] = Field(None, description="新闻发布时间")
    extraction_status: str = Field("pending", description="实体关系提取状态")
    properties: Optional[Dict[str, Any]] = Field(None, description="新闻属性")


class NewsCreate(NewsBase):
    pass


class NewsUpdate(BaseModel):
    title: Optional[str] = Field(
        None, min_length=1, max_length=500, description="新闻标题"
    )
    content: Optional[str] = Field(None, min_length=1, description="新闻内容")
    url: Optional[str] = Field(None, max_length=500, description="新闻URL")
    source: Optional[str] = Field(None, max_length=100, description="新闻来源")
    publish_time: Optional[datetime] = Field(None, description="新闻发布时间")
    extraction_status: Optional[str] = Field(None, description="实体关系提取状态")
    properties: Optional[Dict[str, Any]] = Field(None, description="新闻属性")


class News(NewsBase):
    id: int = Field(..., description="新闻ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class EntityNewsBase(BaseModel):
    entity_id: int = Field(..., description="实体ID")
    news_id: int = Field(..., description="新闻ID")
    weight: float = Field(1.0, description="权重")
    properties: Optional[Dict[str, Any]] = Field(None, description="属性")


class EntityNewsCreate(EntityNewsBase):
    pass


class EntityNews(EntityNewsBase):
    id: int = Field(..., description="实体新闻ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class EntityGroupBase(BaseModel):
    group_name: str = Field(..., min_length=1, max_length=500, description="分组名称")
    description: Optional[str] = Field(None, description="分组描述")
    primary_entity_id: Optional[int] = Field(None, description="主要实体ID")
    entity_count: int = Field(1, description="实体数量")
    properties: Optional[Dict[str, Any]] = Field(None, description="分组属性")


class EntityGroup(EntityGroupBase):
    id: int = Field(..., description="实体分组ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class RelationGroupBase(BaseModel):
    group_name: str = Field(..., min_length=1, max_length=200, description="分组名称")
    description: Optional[str] = Field(None, description="分组描述")
    relation_count: int = Field(1, description="关系数量")
    properties: Optional[Dict[str, Any]] = Field(None, description="分组属性")


class RelationGroup(RelationGroupBase):
    id: int = Field(..., description="关系分组ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class LLMEntityExtraction(BaseModel):
    name: str = Field(..., description="实体名称")
    type: str = Field(..., description="实体类型")
    properties: Optional[Dict[str, Any]] = Field(None, description="实体属性")
    weight: Optional[float] = Field(1.0, description="实体权重")


class LLMRelationExtraction(BaseModel):
    source: str = Field(..., description="源实体名称")
    target: str = Field(..., description="目标实体名称")
    type: str = Field(..., description="关系类型")
    properties: Optional[Dict[str, Any]] = Field(None, description="关系属性")
    weight: Optional[float] = Field(1.0, description="关系权重")


class LLMExtractedData(BaseModel):
    entities: List[LLMEntityExtraction] = Field(..., description="提取的实体列表")
    relations: List[LLMRelationExtraction] = Field(..., description="提取的关系列表")


class EntityNeighbor(BaseModel):
    entity: Entity = Field(..., description="邻居实体")
    relation: Relation = Field(..., description="关系")


class EntityNeighborsResponse(BaseModel):
    entity: Entity = Field(..., description="实体")
    neighbors: List[EntityNeighbor] = Field(..., description="邻居列表")


class KGStatistics(BaseModel):
    total_entities: int = Field(..., description="总实体数")
    total_relations: int = Field(..., description="总关系数")
    total_news: int = Field(..., description="总新闻数")


class GraphNode(BaseModel):
    id: int = Field(..., description="节点ID")
    label: str = Field(..., description="节点标签")
    value: float = Field(..., description="节点值")
    group: str = Field(..., description="节点组")


class GraphEdge(BaseModel):
    id: int = Field(..., description="边ID")
    from_id: int = Field(..., alias="from", description="边的起始节点ID")
    to_id: int = Field(..., alias="to", description="边的目标节点ID")
    label: str = Field(..., description="边标签")
    value: float = Field(..., description="边值")

    class Config:
        populate_by_name = True


class GraphStats(BaseModel):
    total_nodes: int = Field(..., description="总节点数")
    total_edges: int = Field(..., description="总边数")
    entity_types: List[str] = Field(..., description="实体类型列表")
    relation_types: List[str] = Field(..., description="关系类型列表")


class GraphDataResponse(BaseModel):
    success: bool = Field(..., description="请求是否成功")
    nodes: List[GraphNode] = Field(..., description="节点列表")
    edges: List[GraphEdge] = Field(..., description="边列表")
    stats: GraphStats = Field(..., description="统计信息")
    entity_types: Dict[str, int] = Field(..., description="实体类型分布")
    relation_types: Dict[str, int] = Field(..., description="关系类型分布")
    recent_news: int = Field(..., description="最近7天的新闻数")


class PaginationResponse(BaseModel, Generic[T]):
    items: List[T] = Field(..., description="数据列表")
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    total_pages: Optional[int] = Field(None, description="总页数")

    @field_validator("total_pages", mode="before")
    def calculate_total_pages(cls, v, values):
        """Calculate total pages based on total items and page size"""
        if v is None:
            total = values.data.get("total", 0)
            size = values.data.get("size", 10)
            if size <= 0:
                return 0
            return (total + size - 1) // size
        return v

    class Config:
        from_attributes = True


# 新闻处理服务相关模型
class NewsProcessingRequest(BaseModel):
    """新闻处理请求模型"""

    title: str = Field(..., min_length=1, max_length=500, description="新闻标题")
    content: str = Field(..., min_length=1, description="新闻内容")
    source_url: Optional[str] = Field(None, max_length=1000, description="新闻来源URL")
    publish_date: Optional[str] = Field(None, description="发布日期，ISO格式字符串")
    source: Optional[str] = Field(None, max_length=100, description="新闻来源")
    author: Optional[str] = Field(None, max_length=200, description="作者")


class NewsProcessingResponse(BaseModel):
    """新闻处理响应模型"""

    news_id: int = Field(..., description="新闻ID")
    news: News = Field(..., description="新闻对象")
    entities: List[Entity] = Field(..., description="提取并存储的实体列表")
    relations: List[Relation] = Field(..., description="提取并存储的关系列表")
    summary: Optional[str] = Field(None, description="生成的新闻摘要")
    status: str = Field(..., description="处理状态")


# 去重服务相关模型
class EntityDeduplicationRequest(BaseModel):
    """实体去重请求模型"""

    keyword: Optional[str] = None
    entity_type: Optional[str] = None
    entity_types: Optional[List[str]] = None
    similarity_threshold: float = 0.85
    batch_size: int = 100
    limit: Optional[int] = None
    skip_entities: bool = False
    skip_relations: bool = False


class EntityDeduplicationResponse(BaseModel):
    """实体去重响应模型"""

    deduplicated_groups: int = Field(..., description="去重的实体组数")
    merged_entities: int = Field(..., description="合并的实体数量")
    preserved_entities: int = Field(..., description="保留的实体数量")
    operation_time: float = Field(..., description="操作耗时(秒)")
    success: bool = Field(..., description="操作是否成功")
    message: Optional[str] = Field(None, description="操作消息")


class RelationDeduplicationRequest(BaseModel):
    """关系去重请求模型"""

    keyword: Optional[str] = None
    relation_type: Optional[str] = None
    relation_types: Optional[List[str]] = None
    entity_id: Optional[int] = None
    similarity_threshold: float = 0.85
    batch_size: int = 100
    limit: Optional[int] = None


class RelationDeduplicationResponse(BaseModel):
    """关系去重响应模型"""

    deduplicated_groups: int = Field(..., description="去重的关系组数")
    merged_relations: int = Field(..., description="合并的关系数量")
    preserved_relations: int = Field(..., description="保留的关系数量")
    operation_time: float = Field(..., description="操作耗时(秒)")
    success: bool = Field(..., description="操作是否成功")
    message: Optional[str] = Field(None, description="操作消息")


class FullDeduplicationResponse(BaseModel):
    """完整去重流程响应模型"""

    entity_deduplication: EntityDeduplicationResponse = Field(
        ..., description="实体去重结果"
    )
    relation_deduplication: RelationDeduplicationResponse = Field(
        ..., description="关系去重结果"
    )
    total_time: float = Field(..., description="总耗时(秒)")
    timestamp: datetime = Field(..., description="执行时间戳")


class DeduplicationConfigRequest(BaseModel):
    """去重配置请求模型"""

    similarity_threshold: float = Field(0.85, ge=0.0, le=1.0, description="相似度阈值")
    batch_size: int = Field(100, ge=1, le=1000, description="批处理大小")
    limit: Optional[int] = Field(None, ge=1, description="处理限制")
    entity_types: Optional[List[str]] = Field(None, description="实体类型过滤")
    keyword: Optional[str] = Field(None, description="关键词过滤")
    auto_merge: bool = Field(False, description="是否自动合并")
    use_vector_search: bool = Field(True, description="是否使用向量搜索")
    fallback_to_string_similarity: bool = Field(
        True, description="是否回退到字符串相似度"
    )
    min_entities_for_duplication: int = Field(
        2, ge=2, description="进行重复检测的最小实体数"
    )


class DeduplicationResult(BaseModel):
    """去重操作结果模型"""

    deduplicated_groups: int = Field(..., description="去重的组数")
    merged_items: int = Field(..., description="合并的项目数")
    preserved_items: int = Field(..., description="保留的项目数")
    operation_time: float = Field(..., description="操作耗时(秒)")
    success: bool = Field(..., description="操作是否成功")
    message: Optional[str] = Field(None, description="操作消息")
    details: Optional[Dict[str, Any]] = Field(None, description="详细信息")


class TextInput(BaseModel):
    """文本输入模型"""

    text: str = Field(..., min_length=1, description="输入文本")


class BulkItemText(BaseModel):
    """批量处理文本项模型"""

    text: str = Field(..., min_length=1, description="文本内容")


class BulkItemNews(BaseModel):
    """批量处理新闻项模型"""

    title: str = Field(..., min_length=1, max_length=500, description="新闻标题")
    content: str = Field(..., min_length=1, description="新闻内容")
    source_url: Optional[str] = Field(None, max_length=500, description="新闻来源URL")
    publish_date: Optional[datetime] = Field(None, description="新闻发布时间")
    source: Optional[str] = Field(None, max_length=100, description="新闻来源")
    author: Optional[str] = Field(None, max_length=100, description="新闻作者")


class BulkInput(BaseModel):
    """批量处理输入模型"""

    items: List[Any] = Field(..., description="批量处理项目列表")
