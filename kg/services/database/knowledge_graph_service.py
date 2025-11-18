import logging
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from kg.database.models import News, Entity, Relation, EntityGroup, RelationGroup
from kg.database.repositories import EntityGroupRepository, RelationGroupRepository
from kg.database.connection import get_db_session
from kg.utils.db_utils import handle_db_errors, handle_db_errors_with_reraise
from .entity_service import EntityService
from .relation_service import RelationService
from .news_service import NewsService

# 配置日志
logger = logging.getLogger(__name__)

class KnowledgeGraphService:
    """
    知识图谱服务类，提供知识图谱的综合操作
    """
    
    def __init__(self, session: Session):
        self.session = session
        self.entity_service = EntityService(self.session)
        self.relation_service = RelationService(self.session)
        self.news_service = NewsService(self.session)
    
    @handle_db_errors_with_reraise()
    async def create_news(self, title: str, content: str, url: str = None, publish_time: Optional[datetime] = None, source: str = "unknown", author: str = None) -> News:
        """
        创建新闻
        
        Args:
            title: 新闻标题
            content: 新闻内容
            url: 新闻URL（可选）
            publish_time: 发布时间（默认：当前时间）
            source: 新闻来源（默认：unknown）
            author: 作者（可选）
            
        Returns:
            News: 创建的新闻对象
        """
        return await self.news_service.create_news(title, content, url, publish_time, source, author)
    
    @handle_db_errors(default_return=(None, [], []))
    async def store_llm_extracted_data(self, news_id: int, entities: List[Dict[str, Any]], relations: List[Dict[str, Any]]) -> Tuple[Optional[News], List[Entity], List[Relation]]:
        """
        存储LLM提取的实体和关系到数据库
        
        Args:
            news_id: 新闻ID
            entities: LLM提取的实体列表
            relations: LLM提取的关系列表
            
        Returns:
            Tuple[Optional[News], List[Entity], List[Relation]]: 新闻对象、存储的实体列表、存储的关系列表
        """
        logger.info(f"开始存储LLM提取的数据，新闻ID: {news_id}")
        
        # 获取或创建新闻
        news = await self.news_service.get_news_by_id(news_id)
        if not news:
            logger.error(f"新闻不存在，新闻ID: {news_id}")
            return (None, [], [])
        
        # 批量存储实体并建立映射关系
        stored_entities = []
        entity_map = {}  # 用于将实体名称映射到ID
        entity_news_links = []  # 收集所有实体-新闻关联
        
        for entity in entities:
            entity_name = entity.get("name")
            entity_type = entity.get("type", "entity")
            confidence = entity.get("confidence", 1.0)
            properties = entity.copy()
            properties.pop("name", None)
            properties.pop("type", None)
            properties.pop("confidence", None)
            
            if entity_name and entity_type:
                # 获取或创建实体
                db_entity = await self.entity_service.get_or_create_entity(
                    name=entity_name,
                    entity_type=entity_type,
                    properties=properties,
                    confidence_score=confidence,
                    source="llm"
                )
                stored_entities.append(db_entity)
                entity_map[entity_name] = db_entity.id
                
                # 收集实体与新闻的关联数据
                entity_news_links.append({
                    "entity_id": db_entity.id,
                    "news_id": news_id,
                    "properties": properties
                })
        
        # 批量创建实体-新闻关联
        if entity_news_links:
            await self._batch_create_entity_news_links(entity_news_links)
        
        logger.info(f"存储实体完成，共 {len(stored_entities)} 个实体")
        
        # 批量存储关系
        stored_relations = []
        
        # 首先收集所有需要的实体名称
        entity_names = set()
        for relation in relations:
            source_name = relation.get("source_entity")
            target_name = relation.get("target_entity")
            if source_name:
                entity_names.add(source_name)
            if target_name:
                entity_names.add(target_name)
        
        # 批量获取已存在的实体，避免重复查询
        existing_entities = await self._batch_get_entities_by_names(list(entity_names))
        existing_entity_map = {e.name: e for e in existing_entities}
        
        # 创建关系
        for relation in relations:
            source_name = relation.get("source_entity")
            target_name = relation.get("target_entity")
            relation_type = relation.get("relation_type")
            confidence = relation.get("confidence", 1.0)
            
            if source_name and target_name and relation_type:
                # 优先从已存在的实体中获取
                source_id = entity_map.get(source_name) or (existing_entity_map.get(source_name).id if existing_entity_map.get(source_name) else None)
                target_id = entity_map.get(target_name) or (existing_entity_map.get(target_name).id if existing_entity_map.get(target_name) else None)
                
                if source_id and target_id:
                    # 使用get_or_create_relation方法，自动检查并创建关系
                    new_relation = await self.relation_service.get_or_create_relation(
                        source_entity_id=source_id,
                        target_entity_id=target_id,
                        relation_type=relation_type,
                        properties=relation,
                        weight=confidence,
                        source="llm"
                    )
                    stored_relations.append(new_relation)
        
        logger.info(f"存储关系完成，共 {len(stored_relations)} 个关系")
        
        # 更新新闻状态为已提取
        await self.news_service.update_news(news_id, extraction_status="completed", extracted_at=datetime.now())
        
        logger.info(f"存储LLM提取的数据完成，新闻ID: {news_id}")
        return (news, stored_entities, stored_relations)
    
    async def _batch_create_entity_news_links(self, entity_news_links: List[Dict[str, Any]]) -> None:
        """
        批量创建实体-新闻关联
        
        Args:
            entity_news_links: 实体-新闻关联数据列表
        """
        for link_data in entity_news_links:
            await self.news_service.link_entity_to_news(
                news_id=link_data["news_id"],
                entity_id=link_data["entity_id"]
            )
    
    async def _batch_get_entities_by_names(self, entity_names: List[str]) -> List[Entity]:
        """
        批量根据名称获取实体
        
        Args:
            entity_names: 实体名称列表
            
        Returns:
            List[Entity]: 实体列表
        """
        # 使用正确的方法名get_entities_by_names进行批量查询
        entities = await self.entity_service.get_entities_by_names(entity_names)
        return entities
    
    @handle_db_errors_with_reraise()
    async def extract_and_store_entities(self, news_id: int, entities: List[Dict[str, Any]]) -> List[Entity]:
        """
        提取并存储实体
        
        Args:
            news_id: 新闻ID
            entities: 实体列表
            
        Returns:
            List[Entity]: 存储的实体列表
        """
        stored_entities = []
        
        for entity_data in entities:
            # 创建或获取实体
            entity = await self.entity_service.get_or_create_entity(
                name=entity_data.get("name", ""),
                entity_type=entity_data.get("type", ""),
                properties=entity_data.get("properties", {})
            )
            stored_entities.append(entity)
            
            # 建立新闻与实体的关联
            await self.news_service.link_entity_to_news(
                entity_id=entity.id,
                news_id=news_id,
                context=entity_data.get("context")
            )
        
        return stored_entities
    
    @handle_db_errors_with_reraise()
    async def extract_and_store_relations(self, news_id: int, relations: List[Dict[str, Any]]) -> List[Relation]:
        """
        从新闻中提取并存储关系
        
        Args:
            news_id: 新闻ID
            relations: 关系列表，每个关系包含source_entity、target_entity、type等属性
            
        Returns:
            List[Relation]: 创建或获取的关系列表
        """
        logger.info(f"开始从新闻 {news_id} 中提取并存储 {len(relations)} 个关系")
        stored_relations = []
        
        for relation_data in relations:
            # 获取或创建源实体和目标实体
            source_entity = await self.entity_service.get_or_create_entity(
                name=relation_data.get('source_entity').get('name'),
                entity_type=relation_data.get('source_entity').get('type'),
                canonical_name=relation_data.get('source_entity').get('canonical_name'),
                properties=relation_data.get('source_entity').get('properties'),
                confidence_score=relation_data.get('source_entity').get('confidence_score', 0.0),
                source=relation_data.get('source_entity').get('source')
            )
            
            target_entity = await self.entity_service.get_or_create_entity(
                name=relation_data.get('target_entity').get('name'),
                entity_type=relation_data.get('target_entity').get('type'),
                canonical_name=relation_data.get('target_entity').get('canonical_name'),
                properties=relation_data.get('target_entity').get('properties'),
                confidence_score=relation_data.get('target_entity').get('confidence_score', 0.0),
                source=relation_data.get('target_entity').get('source')
            )
            
            # 获取或创建关系
            relation = await self.relation_service.get_or_create_relation(
                source_entity_id=source_entity.id,
                target_entity_id=target_entity.id,
                relation_type=relation_data.get('type'),
                canonical_relation=relation_data.get('canonical_type'),
                properties=relation_data.get('properties'),
                weight=relation_data.get('weight', 1.0),
                source=relation_data.get('source')
            )
            
            # 将源实体和目标实体链接到新闻
            await self.news_service.link_entity_to_news(
                entity_id=source_entity.id,
                news_id=news_id,
                context=relation_data.get('context')
            )
            
            await self.news_service.link_entity_to_news(
                entity_id=target_entity.id,
                news_id=news_id,
                context=relation_data.get('context')
            )
            
            stored_relations.append(relation)
        
        logger.info(f"成功从新闻 {news_id} 中提取并存储 {len(stored_relations)} 个关系")
        return stored_relations
    
    @handle_db_errors_with_reraise()
    async def process_news(self, news_id: int, entities: List[Dict[str, Any]], 
                    relations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        处理新闻，提取并存储实体和关系
        
        Args:
            news_id: 新闻ID
            entities: 实体列表
            relations: 关系列表
            
        Returns:
            Dict[str, Any]: 处理结果，包含实体和关系的数量
        """
        logger.info(f"开始处理新闻 {news_id}，包含 {len(entities)} 个实体和 {len(relations)} 个关系")
        
        # 提取并存储实体
        stored_entities = await self.extract_and_store_entities(news_id, entities)
        
        # 提取并存储关系
        stored_relations = await self.extract_and_store_relations(news_id, relations)
        
        # 更新新闻的提取状态
        await self.news_service.update_news(news_id, extraction_status='completed')
        
        result = {
            'news_id': news_id,
            'entities_count': len(stored_entities),
            'relations_count': len(stored_relations),
            'entities': [entity.id for entity in stored_entities],
            'relations': [relation.id for relation in stored_relations]
        }
        
        logger.info(f"成功处理新闻 {news_id}，提取了 {len(stored_entities)} 个实体和 {len(stored_relations)} 个关系")
        return result
    
    @handle_db_errors(default_return={})
    async def get_entity_neighbors(self, entity_id: int, max_depth: int = 1) -> Dict[str, Any]:
        """
        获取实体的邻居节点
        
        Args:
            entity_id: 实体ID
            max_depth: 最大深度
            
        Returns:
            Dict[str, Any]: 邻居节点信息
        """
        logger.info(f"开始获取实体 {entity_id} 的邻居节点，最大深度: {max_depth}")
        
        # 获取实体信息
        entity = await self.entity_service.get_entity_by_id(entity_id)
        if not entity:
            logger.warning(f"未找到实体 {entity_id}")
            return {}
        
        # 初始化结果
        result = {
            'entity': entity.to_dict(),
            'neighbors': {},
            'relations': []
        }
        
        # 使用BFS获取邻居节点
        visited = {entity_id}
        queue = [(entity_id, 0)]  # (entity_id, depth)
        
        while queue:
            current_entity_id, depth = queue.pop(0)
            
            if depth >= max_depth:
                continue
            
            # 获取当前实体的所有关系
            relations = await self.relation_service.get_relations_by_entity(current_entity_id)
            
            for relation in relations:
                # 确定邻居实体ID
                neighbor_id = relation.target_entity_id if relation.source_entity_id == current_entity_id else relation.source_entity_id
                
                # 如果邻居节点未访问过，添加到队列
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, depth + 1))
                    
                    # 获取邻居实体信息
                    neighbor_entity = await self.entity_service.get_entity_by_id(neighbor_id)
                    if neighbor_entity:
                        result['neighbors'][neighbor_id] = {
                            'entity': neighbor_entity.to_dict(),
                            'depth': depth + 1
                        }
                
                # 添加关系信息
                result['relations'].append({
                    'id': relation.id,
                    'source_entity_id': relation.source_entity_id,
                    'target_entity_id': relation.target_entity_id,
                    'relation_type': relation.relation_type,
                    'weight': relation.weight,
                    'properties': relation.properties
                })
        
        logger.info(f"成功获取实体 {entity_id} 的邻居节点，共找到 {len(result['neighbors'])} 个邻居")
        return result
    
    @handle_db_errors(default_return=None)
    async def get_relation_by_id(self, relation_id: int) -> Optional[Relation]:
        """
        根据ID获取单个关系
        
        Args:
            relation_id: 关系ID
            
        Returns:
            Optional[Relation]: 关系信息
        """
        logger.info(f"开始根据ID获取关系，ID: {relation_id}")
        relation = await self.relation_service.get_relation_by_id(relation_id)
        logger.info(f"完成根据ID获取关系: {relation}")
        return relation
    
    @handle_db_errors(default_return=[])
    async def get_relations(self, relation_type: Optional[str] = None, source_entity_id: Optional[int] = None, target_entity_id: Optional[int] = None, page: int = 1, page_size: int = 10, order_by: Optional[str] = None) -> List[Relation]:
        """
        获取关系列表
        
        Args:
            relation_type: 关系类型
            source_entity_id: 源实体ID
            target_entity_id: 目标实体ID
            page: 页码
            page_size: 每页大小
            order_by: 排序字段
            
        Returns:
            List[Relation]: 关系列表
        """
        logger.info(f"开始获取关系列表，类型: {relation_type}, 源实体ID: {source_entity_id}, 目标实体ID: {target_entity_id}, 页码: {page}, 每页大小: {page_size}, 排序: {order_by}")
        
        # 获取所有关系
        relations = await self.relation_service.relation_repo.get_all()
        
        # 根据类型过滤
        if relation_type:
            relations = [r for r in relations if r.relation_type == relation_type]
        
        # 根据源实体ID过滤
        if source_entity_id:
            relations = [r for r in relations if r.source_entity_id == source_entity_id]
        
        # 根据目标实体ID过滤
        if target_entity_id:
            relations = [r for r in relations if r.target_entity_id == target_entity_id]
        
        # 排序
        if order_by:
            if order_by == 'created_at':
                relations.sort(key=lambda r: r.created_at)
            elif order_by == 'updated_at':
                relations.sort(key=lambda r: r.updated_at)
            elif order_by == 'weight':
                relations.sort(key=lambda r: r.weight, reverse=True)
        
        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        paginated_relations = relations[start:end]
        
        logger.info(f"获取关系列表完成，共找到 {len(relations)} 个关系，返回 {len(paginated_relations)} 个关系")
        return paginated_relations
    
    @handle_db_errors(default_return=None)
    async def update_relation(self, relation_id: int, **kwargs) -> Optional[Relation]:
        """
        更新关系
        
        Args:
            relation_id: 关系ID
            **kwargs: 更新参数
            
        Returns:
            Optional[Relation]: 更新后的关系
        """
        logger.info(f"开始更新关系，ID: {relation_id}, 参数: {kwargs}")
        
        # 处理properties字段
        if 'properties' in kwargs and kwargs['properties']:
            kwargs['properties'] = json.dumps(kwargs['properties'], ensure_ascii=False)
        
        updated_relation = await self.relation_service.relation_repo.update(relation_id, **kwargs)
        logger.info(f"更新关系完成: {updated_relation}")
        return updated_relation
    
    @handle_db_errors(default_return=False)
    async def delete_relation(self, relation_id: int) -> bool:
        """
        删除关系
        
        Args:
            relation_id: 关系ID
            
        Returns:
            bool: 是否删除成功
        """
        logger.info(f"开始删除关系，ID: {relation_id}")
        result = await self.relation_service.relation_repo.delete(relation_id)
        logger.info(f"删除关系完成，结果: {result}")
        return result
    
    @handle_db_errors(default_return=[])
    async def deduplicate_entities(self, similarity_threshold: float = 0.8) -> List[EntityGroup]:
        """
        实体去重
        
        Args:
            similarity_threshold: 相似度阈值
            
        Returns:
            List[EntityGroup]: 创建的实体分组列表
        """
        logger.info(f"开始进行实体去重，相似度阈值: {similarity_threshold}")
        
        # 获取所有实体
        all_entities = await self.entity_service.entity_repo.get_all()
        logger.info(f"获取到 {len(all_entities)} 个实体进行去重")
        
        # 按类型分组
        entities_by_type = {}
        for entity in all_entities:
            entity_type = entity.type
            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []
            entities_by_type[entity_type].append(entity)
        
        # 对每种类型的实体进行去重
        entity_groups = []
        for entity_type, entities in entities_by_type.items():
            logger.debug(f"对 {entity_type} 类型的 {len(entities)} 个实体进行去重")
            
            # 使用名称前缀分组
            name_prefixes = {}
            
            for entity in entities:
                # 使用名称的前2个字符作为前缀
                prefix = entity.name[:2]
                if prefix not in name_prefixes:
                    name_prefixes[prefix] = []
                name_prefixes[prefix].append(entity)
            
            # 对每个前缀分组进行合并
            for prefix, group_entities in name_prefixes.items():
                if len(group_entities) > 1:
                    # 选择置信度最高的实体作为主要实体
                    primary_entity = max(group_entities, key=lambda e: e.confidence_score)
                    
                    # 创建实体分组
                    entity_group = await self.entity_service.merge_entities(
                        entity_ids=[e.id for e in group_entities],
                        canonical_name=primary_entity.name,
                        description=f"合并自前缀为'{prefix}'的{entity_type}实体"
                    )
                    
                    entity_groups.append(entity_group)
        
        logger.info(f"完成实体去重，创建了 {len(entity_groups)} 个实体分组")
        return entity_groups
    
    @handle_db_errors(default_return=[])
    async def deduplicate_relations(self, similarity_threshold: float = 0.8) -> List[RelationGroup]:
        """
        关系去重
        
        Args:
            similarity_threshold: 相似度阈值
            
        Returns:
            List[RelationGroup]: 创建的关系分组列表
        """
        logger.info(f"开始进行关系去重，相似度阈值: {similarity_threshold}")
        
        # 获取所有关系
        all_relations = await self.relation_service.relation_repo.get_all()
        logger.info(f"获取到 {len(all_relations)} 个关系进行去重")
        
        # 按实体对分组
        entity_pairs = {}
        
        for relation in all_relations:
            # 创建实体对的键（排序后确保一致性）
            source_id = relation.source_entity_id
            target_id = relation.target_entity_id
            
            # 确保source_id <= target_id，以便统一排序
            if source_id > target_id:
                source_id, target_id = target_id, source_id
            
            pair_key = f"{source_id}_{target_id}"
            
            if pair_key not in entity_pairs:
                entity_pairs[pair_key] = []
            entity_pairs[pair_key].append(relation)
        
        # 对每个实体对的关系进行去重
        relation_groups = []
        for pair_key, relations in entity_pairs.items():
            if len(relations) > 1:
                # 按关系类型分组
                relation_types = {}
                
                for relation in relations:
                    relation_type = relation.relation_type
                    if relation_type not in relation_types:
                        relation_types[relation_type] = []
                    relation_types[relation_type].append(relation)
                
                # 对每种关系类型进行合并
                for relation_type, type_relations in relation_types.items():
                    if len(type_relations) > 1:
                        # 选择权重最高的关系作为主要关系
                        primary_relation = max(type_relations, key=lambda r: r.weight)
                        
                        # 创建关系分组
                        relation_group = await self.relation_service.merge_relations(
                            relation_ids=[r.id for r in type_relations],
                            canonical_relation=relation_type,
                            description=f"合并自实体对{pair_key}的{relation_type}关系"
                        )
                        
                        relation_groups.append(relation_group)
        
        logger.info(f"完成关系去重，创建了 {len(relation_groups)} 个关系分组")
        return relation_groups
    
    @handle_db_errors(default_return={})
    async def get_statistics(self) -> Dict[str, Any]:
        """
        获取知识图谱统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        logger.info("开始获取知识图谱统计信息")
        
        # 获取实体统计
        entity_count = await self.entity_service.entity_repo.count()
        entity_type_counts = await self.entity_service.entity_repo.count_by_type()
        
        # 获取关系统计
        relation_count = await self.relation_service.relation_repo.count()
        relation_type_counts = await self.relation_service.relation_repo.count_by_type()
        
        # 获取新闻统计
        news_count = await self.news_service.news_repo.count()
        news_status_counts = await self.news_service.news_repo.count_by_status()
        
        # 获取实体组统计
        entity_group_count = await self.entity_service.entity_group_repo.count()
        
        # 获取关系组统计
        relation_group_count = await self.relation_service.relation_group_repo.count()
        
        statistics = {
            'entities': {
                'total': entity_count,
                'by_type': entity_type_counts
            },
            'relations': {
                'total': relation_count,
                'by_type': relation_type_counts
            },
            'news': {
                'total': news_count,
                'by_status': news_status_counts
            },
            'entity_groups': entity_group_count,
            'relation_groups': relation_group_count
        }
        logger.info(f"完成获取知识图谱统计信息: {statistics}")
        return statistics
    
    @handle_db_errors(default_return=None)
    async def get_news_by_id(self, news_id: int) -> Optional[News]:
        """
        根据ID获取新闻
        
        Args:
            news_id: 新闻ID
            
        Returns:
            Optional[News]: 新闻信息
        """
        logger.info(f"开始根据ID获取新闻，ID: {news_id}")
        news = await self.news_service.get_news_by_id(news_id)
        logger.info(f"完成根据ID获取新闻: {news}")
        return news

    @handle_db_errors(default_return=None)
    async def get_entity_by_id(self, entity_id: int) -> Optional[Entity]:
        """根据ID获取单个实体"""
        logger.info(f"获取实体 ID: {entity_id}")
        return await self.entity_service.get_entity_by_id(entity_id)

    @handle_db_errors(default_return=None)
    async def update_entity(self, entity_id: int, **kwargs) -> Optional[Entity]:
        """更新实体信息"""
        logger.info(f"更新实体 ID: {entity_id}")
        logger.debug(f"更新参数: {kwargs}")
        return await self.entity_service.update_entity(entity_id, **kwargs)

    @handle_db_errors(default_return=False)
    async def delete_entity(self, entity_id: int) -> bool:
        """删除实体"""
        logger.info(f"删除实体 ID: {entity_id}")
        return await self.entity_service.delete_entity(entity_id)
    
    @handle_db_errors(default_return=[])
    async def get_entities_by_type(self, entity_type: str, page: int = 1, page_size: int = 10) -> List[Entity]:
        """
        根据类型获取实体列表
        
        Args:
            entity_type: 实体类型
            page: 页码
            page_size: 每页大小
            
        Returns:
            List[Entity]: 实体列表
        """
        logger.info(f"开始根据类型获取实体列表，类型: {entity_type}, 页码: {page}, 每页大小: {page_size}")
        entities = await self.entity_service.get_entities_by_type(entity_type)
        
        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        paginated_entities = entities[start:end]
        
        logger.info(f"完成根据类型获取实体列表，共找到 {len(entities)} 个实体，返回 {len(paginated_entities)} 个实体")
        return paginated_entities

    @handle_db_errors(default_return=[])
    async def get_entities(self, name: Optional[str] = None, entity_type: Optional[str] = None, 
                          page: int = 1, page_size: int = 10, order_by: Optional[str] = None) -> List[Entity]:
        """
        获取实体列表
        
        Args:
            name: 实体名称（模糊匹配）
            entity_type: 实体类型
            page: 页码
            page_size: 每页大小
            order_by: 排序字段
            
        Returns:
            List[Entity]: 实体列表
        """
        logger.info(f"开始获取实体列表，名称: {name}, 类型: {entity_type}, 页码: {page}, 每页大小: {page_size}, 排序: {order_by}")
        
        # 获取所有实体
        entities = await self.entity_service.entity_repo.get_all()
        
        # 根据名称过滤
        if name:
            entities = [e for e in entities if name in e.name or name in (e.canonical_name or '')]
        
        # 根据类型过滤
        if entity_type:
            entities = [e for e in entities if e.type == entity_type]
        
        # 排序
        if order_by:
            if order_by == 'name':
                entities.sort(key=lambda e: e.name)
            elif order_by == 'created_at':
                entities.sort(key=lambda e: e.created_at)
            elif order_by == 'updated_at':
                entities.sort(key=lambda e: e.updated_at)
        
        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        paginated_entities = entities[start:end]
        
        logger.info(f"获取实体列表完成，共找到 {len(entities)} 个实体，返回 {len(paginated_entities)} 个实体")
        return paginated_entities
    
    @handle_db_errors(default_return=[])
    async def get_entities_by_group(self, group_name: str) -> List[Entity]:
        """
        根据分组名称获取实体列表
        
        Args:
            group_name: 实体分组名称
            
        Returns:
            List[Entity]: 实体列表
        """
        logger.info(f"开始根据分组名称获取实体列表，分组名称: {group_name}")
        
        # 首先根据名称获取实体分组
        entity_groups = await self.entity_service.entity_group_repo.find_by_name(group_name)
        if not entity_groups:
            logger.info(f"未找到名为 {group_name} 的实体分组")
            return []
        
        entity_group_id = entity_groups[0].id
        
        # 根据分组ID获取实体
        entities = await self.entity_service.entity_repo.find_by_group_id(entity_group_id)
        
        logger.info(f"根据分组名称 {group_name} 获取实体列表完成，共找到 {len(entities)} 个实体")
        return entities
