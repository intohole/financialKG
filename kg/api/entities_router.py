"""实体相关路由"""

from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from ..services.database.knowledge_graph_service import KnowledgeGraphService
from . import schemas
from .deps import get_db, get_knowledge_graph_service
from .base_router import BaseRouter


# 路由日志记录通过父类BaseRouter处理

# 创建路由实例
class EntityRouter(BaseRouter):
    """实体路由类"""
    
    def __init__(self):
        super().__init__(prefix="/entities", tags=["entities"])
        self._register_routes()
    
    def _register_routes(self):
        """注册路由"""
        router = self.get_router()
        
        @router.post("", response_model=schemas.Entity, status_code=201)
        async def create_entity(
            entity: schemas.EntityCreate,
            kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
            db: AsyncSession = Depends(get_db)
        ):
            """创建新实体"""
            return await self.handle_create(
                db=db,
                create_data=entity,
                service_method=kg_service.add_new_entity,
                response_model=schemas.Entity
            )
        
        @router.get("/{entity_id}", response_model=schemas.Entity)
        async def get_entity(
            entity_id: int,
            kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
            db: AsyncSession = Depends(get_db)
        ):
            """获取单个实体"""
            return await self.handle_get(
                db=db,
                item_id=entity_id,
                service_method=kg_service.get_entity_by_id,
                response_model=schemas.Entity
            )
        
        @router.get("", response_model=List[schemas.Entity])
        async def get_entities(
            name: Optional[str] = None,
            entity_type: Optional[str] = None,
            page: int = 1,
            page_size: int = 10,
            sort_by: Optional[str] = None,
            kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
            db: AsyncSession = Depends(get_db)
        ):
            """获取实体列表"""
            return await self.handle_list(
                db=db,
                service_method=kg_service.entity_service.search_entities,
                response_model=schemas.Entity,
                keyword=name,
                entity_type=entity_type,
                limit=page_size,
                page=page
            )
        
        @router.put("/{entity_id}", response_model=schemas.Entity)
        async def update_entity(
            entity_id: int,
            entity_update: schemas.EntityUpdate,
            kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
            db: AsyncSession = Depends(get_db)
        ):
            """更新实体"""
            return await self.handle_update(
                db=db,
                item_id=entity_id,
                update_data=entity_update,
                service_method=kg_service.update_entity,
                response_model=schemas.Entity
            )
        
        @router.delete("/{entity_id}", status_code=204)
        async def delete_entity(
            entity_id: int,
            kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
            db: AsyncSession = Depends(get_db)
        ):
            """删除实体"""
            return await self.handle_delete(
                db=db,
                item_id=entity_id,
                service_method=kg_service.delete_entity
            )
        
        @router.get("/{entity_id}/neighbors", response_model=schemas.EntityNeighborsResponse)
        async def get_entity_neighbors(
            entity_id: int,
            max_depth: int = Query(1, gt=0, le=3),
            relation_types: Optional[list[str]] = Query(None),
            kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service),
            db: AsyncSession = Depends(get_db)
        ):
            """获取实体的邻居实体"""
            try:
                neighbors = await kg_service.get_entity_neighbors(
                    entity_id=entity_id,
                    max_depth=max_depth,
                    relation_types=relation_types
                )
                return await self.handle_response(neighbors, message="获取邻居成功")
            except ValueError as e:
                from ..utils.exception_handlers import handle_value_error
                raise handle_value_error(e, self.logger)
            except Exception as e:
                from ..utils.exception_handlers import handle_generic_exception
                raise handle_generic_exception(e, self.logger, "获取邻居")


# 创建路由实例
entity_router_instance = EntityRouter()
entities_router = entity_router_instance.get_router()