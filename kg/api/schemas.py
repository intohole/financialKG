from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime


class EntityBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=500, description="实体名称")
    entity_type: str = Field(..., min_length=1, max_length=100, description="实体类型")
    canonical_name: Optional[str] = Field(None, max_length=500, description="规范实体名称")
    entity_group_id: Optional[int] = Field(None, description="实体分组ID")
    weight: float = Field(1.0, description="实体权重")
    source: Optional[str] = Field(None, max_length=100, description="实体来源")
    properties: Optional[Dict[str, Any]] = Field(None, description="实体属性")


class EntityCreate(EntityBase):
    pass


class EntityUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=500, description="实体名称")
    entity_type: Optional[str] = Field(None, min_length=1, max_length=100, description="实体类型")
    canonical_name: Optional[str] = Field(None, max_length=500, description="规范实体名称")
    entity_group_id: Optional[int] = Field(None, description="实体分组ID")
    weight: Optional[float] = Field(None, description="实体权重")
    source: Optional[str] = Field(None, max_length=100, description="实体来源")
    properties: Optional[Dict[str, Any]] = Field(None, description="实体属性")


class Entity(EntityBase):
    id: int = Field(..., description="实体ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        orm_mode = True
        from_attributes = True  # 兼容Pydantic v2


class RelationBase(BaseModel):
    source_entity_id: int = Field(..., description="源实体ID")
    target_entity_id: int = Field(..., description="目标实体ID")
    relation_type: str = Field(..., min_length=1, max_length=200, description="关系类型")
    canonical_relation: Optional[str] = Field(None, max_length=200, description="规范关系类型")
    relation_group_id: Optional[int] = Field(None, description="关系分组ID")
    weight: float = Field(1.0, description="关系权重")
    source: Optional[str] = Field(None, max_length=100, description="关系来源")
    properties: Optional[Dict[str, Any]] = Field(None, description="关系属性")

    @field_validator('source_entity_id')
    def source_not_equal_target(cls, v, info):
        target_entity_id = info.data.get('target_entity_id')
        if target_entity_id is not None and v == target_entity_id:
            raise ValueError("源实体ID和目标实体ID不能相同")
        return v


class RelationCreate(RelationBase):
    pass


class RelationUpdate(BaseModel):
    relation_type: Optional[str] = Field(None, min_length=1, max_length=200, description="关系类型")
    canonical_relation: Optional[str] = Field(None, max_length=200, description="规范关系类型")
    relation_group_id: Optional[int] = Field(None, description="关系分组ID")
    weight: Optional[float] = Field(None, description="关系权重")
    source: Optional[str] = Field(None, max_length=100, description="关系来源")
    properties: Optional[Dict[str, Any]] = Field(None, description="关系属性")


class Relation(RelationBase):
    id: int = Field(..., description="关系ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        orm_mode = True
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
    title: Optional[str] = Field(None, min_length=1, max_length=500, description="新闻标题")
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
        orm_mode = True
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
        orm_mode = True
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
        orm_mode = True
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
        orm_mode = True
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
    entity_types: Dict[str, int] = Field(..., description="实体类型分布")
    relation_types: Dict[str, int] = Field(..., description="关系类型分布")
    recent_news: int = Field(..., description="最近7天的新闻数")


class PaginationResponse(BaseModel):
    items: List[Any] = Field(..., description="数据列表")
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")