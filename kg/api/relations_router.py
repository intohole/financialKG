"""关系相关路由"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..services.database.knowledge_graph_service import KnowledgeGraphService
from ..services.entity_relation_deduplication_service import \
    EntityRelationDeduplicationService
from . import schemas
from .base_router import BaseRouter
from .deps import (get_db, get_entity_relation_deduplication_service,
                   get_knowledge_graph_service)


# 创建关系路由类
class RelationRouter(BaseRouter):
    """关系路由类"""

    def __init__(self):
        super().__init__(prefix="/relations", tags=["relations"])
        self._register_routes()

    def _register_routes(self):
        """注册路由"""
        router = self.router

        @router.post("", response_model=schemas.Relation, status_code=201)
        async def create_relation(
            relation: schemas.RelationCreate,
            kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
            db: AsyncSession = Depends(get_db),
        ):
            """创建新关系"""
            created_relation = await kg_service.add_new_relation(
                source_entity_id=relation.source_entity_id,
                target_entity_id=relation.target_entity_id,
                relation_type=relation.relation_type,
                weight=relation.weight,
                description=relation.description,
                properties=relation.properties,
                source=relation.source,
                confidence_score=relation.confidence_score,
            )
            if not created_relation:
                raise ValueError("Failed to create relation")
            return await self.handle_response(created_relation, message="创建成功")

        @router.get("/{relation_id}", response_model=schemas.Relation)
        async def get_relation(
            relation_id: int,
            kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
            db: AsyncSession = Depends(get_db),
        ):
            """获取单个关系"""
            return await self.handle_get(
                db=db,
                item_id=relation_id,
                service_method=kg_service.get_relation_by_id,
                response_model=schemas.Relation,
            )

        @router.get("", response_model=List[schemas.Relation])
        async def get_relations(
            relation_type: Optional[str] = None,
            source_entity_id: Optional[int] = None,
            target_entity_id: Optional[int] = None,
            page: int = 1,
            page_size: int = 10,
            sort_by: Optional[str] = None,
            kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
            db: AsyncSession = Depends(get_db),
        ):
            """获取关系列表"""
            return await self.handle_list(
                db=db,
                service_method=kg_service.get_relations,
                response_model=schemas.Relation,
                relation_type=relation_type,
                source_entity_id=source_entity_id,
                target_entity_id=target_entity_id,
                page=page,
                page_size=page_size,
                order_by=sort_by,
            )

        @router.put("/{relation_id}", response_model=schemas.Relation)
        async def update_relation(
            relation_id: int,
            relation_update: schemas.RelationUpdate,
            kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
            db: AsyncSession = Depends(get_db),
        ):
            """更新关系"""
            updated_relation = await kg_service.update_relation(
                relation_id=relation_id,
                relation_type=relation_update.relation_type,
                weight=relation_update.weight,
                description=relation_update.description,
                properties=relation_update.properties,
            )
            if not updated_relation:
                raise HTTPException(status_code=404, detail="Relation not found")
            return await self.handle_response(updated_relation, message="更新成功")

        @router.delete("/{relation_id}", status_code=204)
        async def delete_relation(
            relation_id: int,
            kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
            db: AsyncSession = Depends(get_db),
        ):
            """删除关系"""
            return await self.handle_delete(
                db=db, item_id=relation_id, service_method=kg_service.delete_relation
            )

        @router.post(
            "/deduplicate", response_model=schemas.RelationDeduplicationResponse
        )
        async def deduplicate_relations(
            request: schemas.RelationDeduplicationRequest,
            deduplication_service: EntityRelationDeduplicationService = Depends(
                get_entity_relation_deduplication_service
            ),
        ):
            """关系去重端点"""
            self.logger.debug(f"关系去重请求: {request.model_dump()}")

            # 根据请求参数选择不同的去重方法
            if request.entity_id is not None:
                self.logger.debug(f"按实体ID去重关系: entity_id={request.entity_id}")
                result = await deduplication_service.deduplicate_relations_by_entity(
                    entity_id=request.entity_id,
                    relation_type=request.relation_type,
                    similarity_threshold=request.similarity_threshold,
                )
            elif request.relation_type:
                self.logger.debug(
                    f"按关系类型去重: relation_type={request.relation_type}"
                )
                result = await deduplication_service.deduplicate_relations_by_type(
                    relation_type=request.relation_type,
                    similarity_threshold=request.similarity_threshold,
                )
            else:
                self.logger.debug("去重所有关系")
                result = await deduplication_service.deduplicate_all_relations(
                    similarity_threshold=request.similarity_threshold,
                    relation_types=request.relation_types,
                )

            self.logger.info(
                f"关系去重完成，处理关系数量: {result.get('processed_count', 0)}"
            )
            return schemas.RelationDeduplicationResponse(**result)


def get_router_instance() -> APIRouter:
    """获取路由实例，延迟创建以避免循环导入问题"""
    relation_router_instance = RelationRouter()
    return relation_router_instance.get_router()


# 模块级路由实例
relations_router = get_router_instance()
