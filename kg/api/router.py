from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional, List

from ..services.database.knowledge_graph_service import KnowledgeGraphService

from . import schemas

router = APIRouter(tags=["knowledge_graph"])

# 数据库会话依赖
from ..database import db_session

async def get_db_session():
    async with db_session() as session:
        yield session

# 实体相关端点
@router.post("/entities", response_model=schemas.Entity, status_code=201)
async def create_entity(
    entity: schemas.EntityCreate,
    db: AsyncSession = Depends(get_db_session)
):
    kg_service = KnowledgeGraphService(db)
    created_entity = await kg_service.add_new_entity(
        name=entity.name,
        type=entity.type,
        description=entity.description,
        properties=entity.properties,
        source=entity.source,
        confidence_score=entity.confidence_score
    )
    if not created_entity:
        raise HTTPException(status_code=400, detail="Failed to create entity")
    return created_entity

@router.get("/entities/{entity_id}", response_model=schemas.Entity)
async def get_entity(
    entity_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    kg_service = KnowledgeGraphService(db)
    entity = await kg_service.get_entity_by_id(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity

@router.get("/entities", response_model=List[schemas.Entity])
async def get_entities(
    name: Optional[str] = None,
    type: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
    sort_by: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
):
    kg_service = KnowledgeGraphService(db)
    entities = await kg_service.get_entities(
        name=name,
        type=type,
        page=page,
        page_size=page_size,
        order_by=sort_by
    )
    return entities

@router.put("/entities/{entity_id}", response_model=schemas.Entity)
async def update_entity(
    entity_id: UUID,
    entity: schemas.EntityUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    kg_service = KnowledgeGraphService(db)
    updated_entity = await kg_service.update_entity(
        entity_id=entity_id,
        name=entity.name,
        type=entity.type,
        description=entity.description,
        properties=entity.properties
    )
    if not updated_entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return updated_entity

@router.delete("/entities/{entity_id}", status_code=204)
async def delete_entity(
    entity_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    kg_service = KnowledgeGraphService(db)
    success = await kg_service.delete_entity(entity_id)
    if not success:
        raise HTTPException(status_code=404, detail="Entity not found")
    return

# 关系相关端点
@router.post("/relations", response_model=schemas.Relation, status_code=201)
async def create_relation(
    relation: schemas.RelationCreate,
    db: AsyncSession = Depends(get_db_session)
):
    kg_service = KnowledgeGraphService(db)
    created_relation = await kg_service.add_new_relation(
        source_entity_id=relation.source_entity_id,
        target_entity_id=relation.target_entity_id,
        relation_type=relation.relation_type,
        weight=relation.weight,
        description=relation.description,
        properties=relation.properties,
        source=relation.source,
        confidence_score=relation.confidence_score
    )
    if not created_relation:
        raise HTTPException(status_code=400, detail="Failed to create relation")
    return created_relation

@router.get("/relations/{relation_id}", response_model=schemas.Relation)
async def get_relation(
    relation_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    kg_service = KnowledgeGraphService(db)
    relation = await kg_service.get_relation_by_id(relation_id)
    if not relation:
        raise HTTPException(status_code=404, detail="Relation not found")
    return relation

@router.get("/relations", response_model=List[schemas.Relation])
async def get_relations(
    relation_type: Optional[str] = None,
    source_entity_id: Optional[UUID] = None,
    target_entity_id: Optional[UUID] = None,
    page: int = 1,
    page_size: int = 10,
    sort_by: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
):
    kg_service = KnowledgeGraphService(db)
    relations = await kg_service.get_relations(
        relation_type=relation_type,
        source_entity_id=source_entity_id,
        target_entity_id=target_entity_id,
        page=page,
        page_size=page_size,
        order_by=sort_by
    )
    return relations

@router.put("/relations/{relation_id}", response_model=schemas.Relation)
async def update_relation(
    relation_id: UUID,
    relation: schemas.RelationUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    kg_service = KnowledgeGraphService(db)
    updated_relation = await kg_service.update_relation(
        relation_id=relation_id,
        relation_type=relation.relation_type,
        weight=relation.weight,
        description=relation.description,
        properties=relation.properties
    )
    if not updated_relation:
        raise HTTPException(status_code=404, detail="Relation not found")
    return updated_relation

@router.delete("/relations/{relation_id}", status_code=204)
async def delete_relation(
    relation_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    kg_service = KnowledgeGraphService(db)
    success = await kg_service.delete_relation(relation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Relation not found")
    return

# 新闻相关端点
@router.post("/news", response_model=schemas.News, status_code=201)
async def create_news(
    news: schemas.NewsCreate,
    db: AsyncSession = Depends(get_db_session)
):
    kg_service = KnowledgeGraphService(db)
    created_news = await kg_service.create_news(
        title=news.title,
        content=news.content,
        source=news.source,
        publish_date=news.publish_date,
        category=news.category,
        author=news.author
    )
    if not created_news:
        raise HTTPException(status_code=400, detail="Failed to create news")
    return created_news

@router.get("/news/{news_id}", response_model=schemas.News)
async def get_news(
    news_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    kg_service = KnowledgeGraphService(db)
    news = await kg_service.get_news_by_id(news_id)
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    return news

@router.get("/news", response_model=List[schemas.News])
async def get_all_news(
    source: Optional[str] = None,
    category: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
    sort_by: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
):
    kg_service = KnowledgeGraphService(db)
    news_list = await kg_service.get_news(
        source=source,
        category=category,
        page=page,
        page_size=page_size,
        order_by=sort_by
    )
    return news_list

@router.post("/news/{news_id}/process", response_model=schemas.News)
async def process_news(
    news_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    kg_service = KnowledgeGraphService(db)
    processed_news = await kg_service.process_news(news_id)
    if not processed_news:
        raise HTTPException(status_code=404, detail="News not found or processing failed")
    return processed_news

# LLM数据提取和存储端点
@router.post("/entities/extract", response_model=schemas.LLMExtractedData, status_code=201)
async def extract_and_store_entities(
    llm_data: schemas.LLMExtractedData,
    db: AsyncSession = Depends(get_db_session)
):
    kg_service = KnowledgeGraphService(db)
    result = await kg_service.extract_and_store_entities(
        llm_data=llm_data.model_dump()
    )
    return result

# 实体邻居查询端点
@router.get("/entities/{entity_id}/neighbors", response_model=schemas.EntityNeighborsResponse)
async def get_entity_neighbors(
    entity_id: UUID,
    max_depth: int = Query(1, gt=0, le=3),
    relation_types: Optional[list[str]] = Query(None),
    db: AsyncSession = Depends(get_db_session)
):
    kg_service = KnowledgeGraphService(db)
    neighbors = await kg_service.get_entity_neighbors(
        entity_id=entity_id,
        max_depth=max_depth,
        relation_types=relation_types
    )
    return neighbors

# 实体和关系去重端点
@router.post("/entities/deduplicate", response_model=List[schemas.EntityGroup])
async def deduplicate_entities(
    threshold: float = Query(0.8, ge=0.5, le=1.0),
    db: AsyncSession = Depends(get_db_session)
):
    kg_service = KnowledgeGraphService(db)
    entity_groups = await kg_service.deduplicate_entities(
        similarity_threshold=threshold
    )
    return entity_groups

@router.post("/relations/deduplicate", response_model=List[schemas.RelationGroup])
async def deduplicate_relations(
    threshold: float = Query(0.8, ge=0.5, le=1.0),
    db: AsyncSession = Depends(get_db_session)
):
    kg_service = KnowledgeGraphService(db)
    relation_groups = await kg_service.deduplicate_relations(
        similarity_threshold=threshold
    )
    return relation_groups

# 知识图谱统计信息端点
@router.get("/statistics", response_model=schemas.KGStatistics)
async def get_statistics(
    db: AsyncSession = Depends(get_db_session)
):
    kg_service = KnowledgeGraphService(db)
    statistics = await kg_service.get_statistics()
    return statistics
