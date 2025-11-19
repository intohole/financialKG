import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入被测试的服务类
from kg.services.database.knowledge_graph_service import KnowledgeGraphService
from kg.database.models import News, Entity, Relation

class MockEntity:
    """模拟实体对象"""
    def __init__(self, id: int, name: str, entity_type: str, properties: Dict[str, Any] = None):
        self.id = id
        self.name = name
        self.type = entity_type
        self.properties = properties or {}
        self.confidence_score = 1.0
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "properties": self.properties
        }

class MockRelation:
    """模拟关系对象"""
    def __init__(self, id: int, source_entity_id: int, target_entity_id: int, relation_type: str, properties: Dict[str, Any] = None):
        self.id = id
        self.source_entity_id = source_entity_id
        self.target_entity_id = target_entity_id
        self.relation_type = relation_type
        self.properties = properties or {}
        self.weight = 1.0
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

class MockNews:
    """模拟新闻对象"""
    def __init__(self, id: int, title: str, content: str, source: str = "unknown"):
        self.id = id
        self.title = title
        self.content = content
        self.source = source
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

async def test_knowledge_graph_service():
    """测试KnowledgeGraphService的主要异步数据库操作功能"""
    logger.info("开始测试KnowledgeGraphService...")
    
    # 创建模拟的数据库会话
    mock_session = MagicMock()
    
    # 创建模拟的服务实例
    with patch('kg.services.database.knowledge_graph_service.EntityService') as mock_entity_service_cls, \
         patch('kg.services.database.knowledge_graph_service.RelationService') as mock_relation_service_cls, \
         patch('kg.services.database.knowledge_graph_service.NewsService') as mock_news_service_cls:
        
        # 配置模拟的子服务
        mock_entity_service = AsyncMock()
        mock_relation_service = AsyncMock()
        mock_news_service = AsyncMock()
        
        mock_entity_service_cls.return_value = mock_entity_service
        mock_relation_service_cls.return_value = mock_relation_service
        mock_news_service_cls.return_value = mock_news_service
        
        # 创建KnowledgeGraphService实例
        kg_service = KnowledgeGraphService(mock_session)
        
        # 测试1: 创建新闻
        logger.info("测试: 创建新闻")
        mock_news = MockNews(1, "测试新闻标题", "这是测试新闻内容", "测试来源")
        mock_news_service.create_news.return_value = mock_news
        
        news = await kg_service.create_news(
            title="测试新闻标题",
            content="这是测试新闻内容",
            source="测试来源"
        )
        
        assert news is not None
        assert news.title == "测试新闻标题"
        mock_news_service.create_news.assert_called_once()
        logger.info("✅ 新闻创建测试通过")
        
        # 测试2: 存储LLM提取的数据
        logger.info("测试: 存储LLM提取的数据")
        # 配置模拟行为
        mock_news_service.get_news_by_id.return_value = mock_news
        
        # 模拟实体创建/获取
        mock_entity = MockEntity(1, "华为", "公司")
        mock_entity_service.get_or_create_entity.return_value = mock_entity
        
        # 模拟实体批量获取
        mock_entity_service.get_entities_by_names.return_value = []
        
        # 模拟关系创建/获取
        mock_relation = MockRelation(1, 1, 2, "生产")
        mock_relation_service.get_or_create_relation.return_value = mock_relation
        
        # 测试数据
        entities = [{"name": "华为", "type": "公司", "confidence": 0.95}]
        relations = [{
            "source_entity": "华为",
            "target_entity": "Mate 60 Pro", 
            "relation_type": "生产",
            "confidence": 0.9
        }]
        
        result = await kg_service.store_llm_extracted_data(news_id=1, entities=entities, relations=relations)
        
        assert len(result) == 3
        assert result[0] is not None  # news
        assert len(result[1]) == 1    # entities
        assert len(result[2]) == 0    # relations (由于目标实体不存在)
        logger.info("✅ LLM数据存储测试通过")
        
        # 测试3: 获取实体
        logger.info("测试: 获取实体")
        mock_entity_service.get_entity_by_id.return_value = mock_entity
        
        entity = await kg_service.get_entity_by_id(entity_id=1)
        
        assert entity is not None
        assert entity.name == "华为"
        mock_entity_service.get_entity_by_id.assert_called_with(1)
        logger.info("✅ 获取实体测试通过")
        
        # 测试4: 更新实体
        logger.info("测试: 更新实体")
        updated_entity = MockEntity(1, "华为技术有限公司", "公司", {"description": "中国科技公司"})
        mock_entity_service.update_entity.return_value = updated_entity
        
        result = await kg_service.update_entity(entity_id=1, name="华为技术有限公司", properties={"description": "中国科技公司"})
        
        assert result is not None
        assert result.name == "华为技术有限公司"
        mock_entity_service.update_entity.assert_called_once()
        logger.info("✅ 更新实体测试通过")
        
        # 测试5: 获取实体邻居
        logger.info("测试: 获取实体邻居")
        # 配置更多模拟行为
        mock_entity_service.get_entity_by_id.side_effect = lambda id: {
            1: MockEntity(1, "华为", "公司"),
            2: MockEntity(2, "Mate 60 Pro", "产品")
        }.get(id)
        
        mock_relation_service.get_relations_by_entity.return_value = [
            MockRelation(1, 1, 2, "生产")
        ]
        
        neighbors = await kg_service.get_entity_neighbors(entity_id=1, max_depth=1)
        
        assert neighbors is not None
        assert 'entity' in neighbors
        assert 'neighbors' in neighbors
        assert len(neighbors['neighbors']) == 1
        logger.info("✅ 获取实体邻居测试通过")
        
        # 测试6: 获取关系列表
        logger.info("测试: 获取关系列表")
        mock_relation_service.relation_repo.get_all.return_value = [
            MockRelation(1, 1, 2, "生产"),
            MockRelation(2, 1, 3, "研发")
        ]
        
        relations = await kg_service.get_relations(relation_type="生产")
        
        assert len(relations) == 1
        assert relations[0].relation_type == "生产"
        logger.info("✅ 获取关系列表测试通过")
        
        # 测试7: 处理新闻
        logger.info("测试: 处理新闻")
        # 重置模拟调用计数
        mock_entity_service.get_or_create_entity.reset_mock()
        mock_relation_service.get_or_create_relation.reset_mock()
        mock_news_service.link_entity_to_news.reset_mock()
        mock_news_service.update_news.reset_mock()
        
        # 配置模拟行为
        mock_entity_service.get_or_create_entity.side_effect = lambda **kwargs: {
            "华为": MockEntity(1, "华为", "公司"),
            "Mate 60 Pro": MockEntity(2, "Mate 60 Pro", "产品")
        }.get(kwargs.get('name', ''), MockEntity(3, kwargs.get('name', ''), kwargs.get('entity_type', '')))
        
        mock_relation_service.get_or_create_relation.return_value = MockRelation(1, 1, 2, "生产")
        
        # 测试数据
        test_entities = [
            {"name": "华为", "type": "公司", "properties": {}}
        ]
        test_relations = [{
            "source_entity": {"name": "华为", "type": "公司"},
            "target_entity": {"name": "Mate 60 Pro", "type": "产品"},
            "type": "生产"
        }]
        
        result = await kg_service.process_news(news_id=1, entities=test_entities, relations=test_relations)
        
        assert result is not None
        assert result['news_id'] == 1
        assert result['entities_count'] == 1
        assert result['relations_count'] == 1
        logger.info("✅ 处理新闻测试通过")
        
        # 测试8: 实体去重
        logger.info("测试: 实体去重")
        mock_deduplication_service = AsyncMock()
        mock_deduplication_service.deduplicate_entities.return_value = []
        kg_service.deduplication_service = mock_deduplication_service
        
        result = await kg_service.deduplicate_entities(similarity_threshold=0.8)
        
        assert isinstance(result, list)
        mock_deduplication_service.deduplicate_entities.assert_called_with(0.8)
        logger.info("✅ 实体去重测试通过")
        
        # 测试9: 关系去重
        logger.info("测试: 关系去重")
        mock_deduplication_service.deduplicate_relations.return_value = []
        
        result = await kg_service.deduplicate_relations(similarity_threshold=0.8)
        
        assert isinstance(result, list)
        mock_deduplication_service.deduplicate_relations.assert_called_with(0.8)
        logger.info("✅ 关系去重测试通过")
        
        logger.info("🎉 所有KnowledgeGraphService测试通过！")
        return True

if __name__ == "__main__":
    try:
        asyncio.run(test_knowledge_graph_service())
    except Exception as e:
        logger.error(f"测试失败: {e}")
        raise
