from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from .deps import get_knowledge_graph_service, get_logger

from ..services.database.knowledge_graph_service import KnowledgeGraphService
from .base_router import BaseRouter
from .schemas import GraphDataResponse, GraphNode, GraphEdge, GraphStats


class VisualizationRouter(BaseRouter):
    def __init__(self):
        """初始化可视化路由"""
        super().__init__(prefix="/visualize", tags=["visualization"])
        self.setup_routes()

    def setup_routes(self):
        """设置路由"""
        logger = get_logger("visualization")

        @self.router.get("/graph-data", response_model=GraphDataResponse)
        async def get_graph_data(
            kg_service: KnowledgeGraphService = Depends(get_knowledge_graph_service)
        ):
            """
            获取用于可视化的知识图谱数据
            
            返回包含节点和边的图形数据结构，用于前端可视化组件渲染
            """
            logger.info("Starting to retrieve graph data for visualization")
            
            # 获取所有实体
            entities = await kg_service.entity_service.get_all_entities()
            
            # 获取所有关系
            relations = await kg_service.relation_service.get_all_relations()
            
            # 构建节点列表
            nodes = []
            for entity in entities:
                nodes.append(
                    GraphNode(
                        id=entity.id,
                        label=entity.name,
                        value=1.0,
                        group=entity.type
                    )
                )
            
            # 构建边列表
            edges = []
            for relation in relations:
                edges.append(
                    GraphEdge(
                        id=relation.id,
                        from_id=relation.source_entity_id,
                        to_id=relation.target_entity_id,
                        label=relation.relation_type,
                        value=1.0
                    )
                )
            
            # 构建统计信息
            entity_types = list(set([node.group for node in nodes]))
            relation_types = list(set([edge.label for edge in edges]))
            
            stats = GraphStats(
                total_nodes=len(nodes),
                total_edges=len(edges),
                entity_types=entity_types,
                relation_types=relation_types
            )
            
            logger.info(f"Graph data retrieved successfully: {len(nodes)} nodes, {len(edges)} edges")
            
            return GraphDataResponse(success=True, nodes=nodes, edges=edges, stats=stats)


# 创建路由实例
visualization_router = VisualizationRouter().router
