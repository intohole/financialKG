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
    
    def __init__(self, session: Optional[Session] = None):
        self.session = session or get_db_session()
        self.entity_service = EntityService(self.session)
        self.relation_service = RelationService(self.session)
        self.news_service = NewsService(self.session)
    
    @handle_db_errors_with_reraise()
    async def create_news(self, title: str, content: str, source: str = "unknown", publish_time: Optional[datetime] = None, author: str = None, url: str = None) -> News:
        """
        创建新闻
        
        Args:
            title: 新闻标题
            content: 新闻内容
            source: 新闻来源（默认：unknown）
            publish_time: 发布时间（默认：当前时间）
            author: 作者（可选）
            url: 新闻URL（可选）
            
        Returns:
            News: 创建的新闻对象
        """
        return await self.news_service.create_news(title, content, url, publish_time, source)
    
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
        
        # 存储实体并建立映射关系
        stored_entities = []
        entity_map = {}  # 用于将实体名称映射到ID
        
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
                
                # 建立实体与新闻的关联
                await self.news_service.link_entity_to_news(news_id, db_entity.id)
        
        logger.info(f"存储实体完成，共 {len(stored_entities)} 个实体")
        
        # 存储关系
        stored_relations = []
        
        for relation in relations:
            source_name = relation.get("source_entity")
            target_name = relation.get("target_entity")
            relation_type = relation.get("relation_type")
            confidence = relation.get("confidence", 1.0)
            
            if source_name and target_name and relation_type:
                source_id = entity_map.get(source_name)
                target_id = entity_map.get(target_name)
                
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
    
    @handle_db_errors_with_reraise()
    def extract_and_store_entities(self, news_id: int, entities: List[Dict[str, Any]]) -> List[Entity]:
        """
        从新闻中提取并存储实体
        
        Args:
            news_id: 新闻ID
            entities: 实体列表，每个实体包含name、type等属性
            
        Returns:
            List[Entity]: 创建或获取的实体列表
        """
        logger.info(f"开始从新闻 {news_id} 中提取并存储 {len(entities)} 个实体")
        stored_entities = []
        
        for entity_data in entities:
            # 获取或创建实体
            entity = self.entity_service.get_or_create_entity(
                name=entity_data.get('name'),
                entity_type=entity_data.get('type'),
                canonical_name=entity_data.get('canonical_name'),
                properties=entity_data.get('properties'),
                confidence_score=entity_data.get('confidence_score', 0.0),
                source=entity_data.get('source')
            )
            
            # 将实体链接到新闻
            self.news_service.link_entity_to_news(
                entity_id=entity.id,
                news_id=news_id,
                context=entity_data.get('context')
            )
            
            stored_entities.append(entity)
        
        logger.info(f"成功从新闻 {news_id} 中提取并存储 {len(stored_entities)} 个实体")
        return stored_entities
    
    @handle_db_errors_with_reraise()
    def extract_and_store_relations(self, news_id: int, relations: List[Dict[str, Any]]) -> List[Relation]:
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
            source_entity = self.entity_service.get_or_create_entity(
                name=relation_data.get('source_entity').get('name'),
                entity_type=relation_data.get('source_entity').get('type'),
                canonical_name=relation_data.get('source_entity').get('canonical_name'),
                properties=relation_data.get('source_entity').get('properties'),
                confidence_score=relation_data.get('source_entity').get('confidence_score', 0.0),
                source=relation_data.get('source_entity').get('source')
            )
            
            target_entity = self.entity_service.get_or_create_entity(
                name=relation_data.get('target_entity').get('name'),
                entity_type=relation_data.get('target_entity').get('type'),
                canonical_name=relation_data.get('target_entity').get('canonical_name'),
                properties=relation_data.get('target_entity').get('properties'),
                confidence_score=relation_data.get('target_entity').get('confidence_score', 0.0),
                source=relation_data.get('target_entity').get('source')
            )
            
            # 获取或创建关系
            relation = self.relation_service.get_or_create_relation(
                source_entity_id=source_entity.id,
                target_entity_id=target_entity.id,
                relation_type=relation_data.get('type'),
                canonical_relation=relation_data.get('canonical_type'),
                properties=relation_data.get('properties'),
                weight=relation_data.get('weight', 1.0),
                source=relation_data.get('source')
            )
            
            # 将源实体和目标实体链接到新闻
            self.news_service.link_entity_to_news(
                entity_id=source_entity.id,
                news_id=news_id,
                context=relation_data.get('context')
            )
            
            self.news_service.link_entity_to_news(
                entity_id=target_entity.id,
                news_id=news_id,
                context=relation_data.get('context')
            )
            
            stored_relations.append(relation)
        
        logger.info(f"成功从新闻 {news_id} 中提取并存储 {len(stored_relations)} 个关系")
        return stored_relations
    
    @handle_db_errors_with_reraise()
    def process_news(self, news_id: int, entities: List[Dict[str, Any]], 
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
        stored_entities = self.extract_and_store_entities(news_id, entities)
        
        # 提取并存储关系
        stored_relations = self.extract_and_store_relations(news_id, relations)
        
        # 更新新闻的提取状态
        self.news_service.update_extraction_status(news_id, 'completed')
        
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
    def get_entity_neighbors(self, entity_id: int, max_depth: int = 1) -> Dict[str, Any]:
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
        entity = self.entity_service.get_entity_by_id(entity_id)
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
            relations = self.relation_service.get_relations_by_entity(current_entity_id)
            
            for relation in relations:
                # 确定邻居实体ID
                neighbor_id = relation.target_entity_id if relation.source_entity_id == current_entity_id else relation.source_entity_id
                
                # 如果邻居节点未访问过，添加到队列
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, depth + 1))
                    
                    # 获取邻居实体信息
                    neighbor_entity = self.entity_service.get_entity_by_id(neighbor_id)
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
    
    @handle_db_errors(default_return=[])
    def deduplicate_entities(self, similarity_threshold: float = 0.8) -> List[EntityGroup]:
        """
        实体去重
        
        Args:
            similarity_threshold: 相似度阈值
            
        Returns:
            List[EntityGroup]: 创建的实体分组列表
        """
        logger.info(f"开始进行实体去重，相似度阈值: {similarity_threshold}")
        
        # 获取所有实体
        all_entities = self.entity_service.entity_repo.get_all()
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
                    entity_group = self.entity_service.merge_entities(
                        entity_ids=[e.id for e in group_entities],
                        canonical_name=primary_entity.name,
                        description=f"合并自前缀为'{prefix}'的{entity_type}实体"
                    )
                    
                    entity_groups.append(entity_group)
        
        logger.info(f"完成实体去重，创建了 {len(entity_groups)} 个实体分组")
        return entity_groups
    
    @handle_db_errors(default_return=[])
    def deduplicate_relations(self, similarity_threshold: float = 0.8) -> List[RelationGroup]:
        """
        关系去重
        
        Args:
            similarity_threshold: 相似度阈值
            
        Returns:
            List[RelationGroup]: 创建的关系分组列表
        """
        logger.info(f"开始进行关系去重，相似度阈值: {similarity_threshold}")
        
        # 获取所有关系
        all_relations = self.relation_service.relation_repo.get_all()
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
                        relation_group = self.relation_service.merge_relations(
                            relation_ids=[r.id for r in type_relations],
                            canonical_relation=relation_type,
                            description=f"合并自实体对{pair_key}的{relation_type}关系"
                        )
                        
                        relation_groups.append(relation_group)
        
        logger.info(f"完成关系去重，创建了 {len(relation_groups)} 个关系分组")
        return relation_groups
    
    @handle_db_errors(default_return={})
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取知识图谱统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        logger.info("开始获取知识图谱统计信息")
        
        # 获取实体统计
        entity_count = self.entity_service.entity_repo.count()
        entity_type_counts = self.entity_service.entity_repo.count_by_type()
        
        # 获取关系统计
        relation_count = self.relation_service.relation_repo.count()
        relation_type_counts = self.relation_service.relation_repo.count_by_type()
        
        # 获取新闻统计
        news_count = self.news_service.news_repo.count()
        news_status_counts = self.news_service.news_repo.count_by_status()
        
        # 获取实体组统计
        entity_group_count = self.entity_service.entity_group_repo.count()
        
        # 获取关系组统计
        relation_group_count = self.relation_service.relation_group_repo.count()
        
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
        
        logger.info(f"获取知识图谱统计信息完成，实体: {entity_count}, 关系: {relation_count}, 新闻: {news_count}")
        return statistics
