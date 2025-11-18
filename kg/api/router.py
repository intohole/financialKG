from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional, List, Dict, Any

from ..services.database.knowledge_graph_service import KnowledgeGraphService
from ..services.news_processing_service import NewsProcessingService
from ..services.entity_relation_deduplication_service import EntityRelationDeduplicationService

from . import schemas

router = APIRouter(tags=["knowledge_graph"])

# 数据库会话依赖
from ..database import db_session

async def get_db_session():
    async with db_session() as session:
        yield session

# 去重服务依赖
async def get_deduplication_service(
    request: Request
) -> EntityRelationDeduplicationService:
    """从请求中获取去重服务实例"""
    if not hasattr(request.app.state, 'deduplication_service'):
        raise HTTPException(status_code=500, detail="去重服务未初始化")
    return request.app.state.deduplication_service

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
    entity_id: int,
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
    entity_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
    sort_by: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
):
    kg_service = KnowledgeGraphService(db)
    entities = await kg_service.get_entities(
        name=name,
        entity_type=entity_type,
        page=page,
        page_size=page_size,
        order_by=sort_by
    )
    return entities

@router.put("/entities/{entity_id}", response_model=schemas.Entity)
async def update_entity(
    entity_id: int,
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
    entity_id: int,
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
    relation_id: int,
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
    source_entity_id: Optional[int] = None,
    target_entity_id: Optional[int] = None,
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
    relation_id: int,
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
    relation_id: int,
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
    news_id: int,
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

@router.post("/news/{news_id}/process", response_model=schemas.NewsProcessingResponse)
async def process_news(
    news_id: int,
    llm_data: schemas.LLMExtractedData,
    db: AsyncSession = Depends(get_db_session)
):
    kg_service = KnowledgeGraphService(db)
    processed_result = await kg_service.process_news(news_id, llm_data.entities, llm_data.relations)
    if not processed_result:
        raise HTTPException(status_code=404, detail="News not found or processing failed")
    return processed_result

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

@router.post("/knowledge/submit", response_model=Dict[str, Any], status_code=201)
async def submit_knowledge(
    submission: Dict[str, Any],
    db: AsyncSession = Depends(get_db_session)
):
    """Submit knowledge extracted by LLM"""
    kg_service = KnowledgeGraphService(db)
    news_id = submission.get("news_id")
    entities = submission.get("entities", [])
    relations = submission.get("relations", [])
    
    if not news_id:
        raise HTTPException(status_code=400, detail="Missing news_id")
    
    news, stored_entities, stored_relations = await kg_service.store_llm_extracted_data(news_id, entities, relations)
    
    return {
        "success": True,
        "message": "Knowledge submitted successfully",
        "news_id": news.id if news else None,
        "entities_count": len(stored_entities),
        "relations_count": len(stored_relations)
    }

# 实体邻居查询端点
@router.get("/entities/{entity_id}/neighbors", response_model=schemas.EntityNeighborsResponse)
async def get_entity_neighbors(
    entity_id: int,
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
@router.post("/entities/deduplicate", response_model=schemas.EntityDeduplicationResponse)
async def deduplicate_entities(
    request: schemas.EntityDeduplicationRequest,
    deduplication_service: EntityRelationDeduplicationService = Depends(get_deduplication_service)
):
    """实体去重端点"""
    try:
        # 根据请求参数选择不同的去重方法
        if request.keyword:
            # 根据关键词去重
            result = await deduplication_service.deduplicate_entities_by_keyword(
                keyword=request.keyword,
                entity_type=request.entity_type,
                similarity_threshold=request.similarity_threshold,
                limit=getattr(request, 'limit', None)
            )
        elif request.entity_type:
            # 根据实体类型去重
            result = await deduplication_service.deduplicate_entities_by_type(
                entity_type=request.entity_type,
                similarity_threshold=request.similarity_threshold,
                limit=getattr(request, 'limit', None)
            )
        else:
            # 去重所有实体
            result = await deduplication_service.deduplicate_all_entities(
                similarity_threshold=request.similarity_threshold,
                entity_types=request.entity_types
            )
        return schemas.EntityDeduplicationResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/relations/deduplicate", response_model=schemas.RelationDeduplicationResponse)
async def deduplicate_relations(
    request: schemas.RelationDeduplicationRequest,
    deduplication_service: EntityRelationDeduplicationService = Depends(get_deduplication_service)
):
    """关系去重端点"""
    try:
        # 根据请求参数选择不同的去重方法
        if request.entity_id is not None:
            # 根据实体ID去重相关关系
            result = await deduplication_service.deduplicate_relations_by_entity(
                entity_id=request.entity_id,
                relation_type=request.relation_type,
                similarity_threshold=request.similarity_threshold
            )
        elif request.relation_type:
            # 根据关系类型去重
            result = await deduplication_service.deduplicate_relations_by_type(
                relation_type=request.relation_type,
                similarity_threshold=request.similarity_threshold,
                limit=getattr(request, 'limit', None)
            )
        else:
            # 去重所有关系
            result = await deduplication_service.deduplicate_all_relations(
                similarity_threshold=request.similarity_threshold,
                relation_types=request.relation_types
            )
        return schemas.RelationDeduplicationResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 知识图谱统计信息端点
@router.get("/statistics", response_model=schemas.KGStatistics)
async def get_statistics(
    db: AsyncSession = Depends(get_db_session)
):
    kg_service = KnowledgeGraphService(db)
    statistics = await kg_service.get_statistics()
    return statistics


# 完整去重流程端点
@router.post("/deduplicate/full", response_model=Dict[str, Any])
async def full_deduplication(
    similarity_threshold: float = Query(0.8, ge=0.5, le=1.0),
    batch_size: int = Query(100, ge=10, le=500),
    skip_entities: bool = Query(False),
    skip_relations: bool = Query(False),
    deduplication_service: EntityRelationDeduplicationService = Depends(get_deduplication_service)
):
    """执行完整的实体和关系去重流程"""
    try:
        result = await deduplication_service.full_deduplication(
            similarity_threshold=similarity_threshold,
            batch_size=batch_size,
            skip_entities=skip_entities,
            skip_relations=skip_relations
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 新闻处理服务相关端点
# 创建NewsProcessingService的依赖项
async def get_news_processing_service(db: AsyncSession = Depends(get_db_session)):
    kg_service = KnowledgeGraphService(db)
    news_processing_service = NewsProcessingService(data_services=kg_service)
    return news_processing_service


@router.post("/news/process", response_model=schemas.NewsProcessingResponse)
async def process_news_with_llm(
    request: schemas.NewsProcessingRequest,
    news_processing_service: NewsProcessingService = Depends(get_news_processing_service)
):
    """
    处理新闻并使用LLM提取实体、关系和生成摘要
    
    - **title**: 新闻标题
    - **content**: 新闻内容
    - **source_url**: 新闻来源URL
    - **publish_date**: 发布日期（ISO格式字符串）
    - **source**: 新闻来源
    - **author**: 作者
    """
    try:
        # 将请求模型转换为字典，以便传递给服务
        news_data = request.model_dump()
        
        # 调用新闻处理服务
        result = await news_processing_service.process_and_store_news(news_data)
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"新闻处理过程中发生错误: {str(e)}")
