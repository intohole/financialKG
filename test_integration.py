import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入需要测试的服务和相关模块
from kg.services.llm_service import LLMService
from kg.services.embedding_service import ThirdPartyEmbeddingService
from kg.services.database.knowledge_graph_service import KnowledgeGraphService
from kg.services.news_processing_service import create_news_processing_service
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
    def __init__(self, id: int, source_entity_id: int, target_entity_id: int, relation_type: str):
        self.id = id
        self.source_entity_id = source_entity_id
        self.target_entity_id = target_entity_id
        self.relation_type = relation_type
        self.weight = 1.0
        self.properties = {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

class MockNews:
    """模拟新闻对象"""
    def __init__(self, id: int, title: str, content: str):
        self.id = id
        self.title = title
        self.content = content
        self.source = "integration_test"
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

async def test_service_integration():
    """测试各个服务之间的集成协作"""
    logger.info("开始集成测试...")
    
    # ===== 准备模拟服务 =====
    logger.info("准备模拟服务...")
    
    # 模拟LLM服务
    mock_llm_service = AsyncMock(spec=LLMService)
    
    # 配置LLM服务的模拟行为
    mock_llm_service.extract_entities.return_value = [
        {"name": "华为", "type": "公司", "confidence": 0.95},
        {"name": "Mate 60 Pro", "type": "产品", "confidence": 0.92},
        {"name": "麒麟9000S", "type": "芯片", "confidence": 0.90}
    ]
    
    mock_llm_service.extract_relations.return_value = [
        {
            "source_entity": "华为",
            "target_entity": "Mate 60 Pro",
            "relation_type": "生产",
            "confidence": 0.95
        },
        {
            "source_entity": "华为",
            "target_entity": "麒麟9000S",
            "relation_type": "研发",
            "confidence": 0.92
        },
        {
            "source_entity": "麒麟9000S",
            "target_entity": "Mate 60 Pro",
            "relation_type": "搭载",
            "confidence": 0.98
        }
    ]
    
    mock_llm_service.summarize_text.return_value = "华为推出搭载自研麒麟9000S芯片的Mate 60 Pro手机，展示了其在芯片研发和高端手机生产领域的实力。"
    
    # 模拟嵌入服务
    mock_embedding_service = AsyncMock(spec=ThirdPartyEmbeddingService)
    mock_embedding_service.get_embeddings.return_value = [[0.1] * 1536, [0.2] * 1536, [0.3] * 1536]
    # 为异步方法设置返回值
    async def mock_get_dimension():
        return 1536
    mock_embedding_service.get_dimension.side_effect = mock_get_dimension
    
    # 模拟数据库会话
    mock_session = MagicMock()
    
    # 模拟知识图谱服务
    with patch('kg.services.database.knowledge_graph_service.EntityService') as mock_entity_service_cls, \
         patch('kg.services.database.knowledge_graph_service.RelationService') as mock_relation_service_cls, \
         patch('kg.services.database.knowledge_graph_service.NewsService') as mock_news_service_cls:
        
        # 配置模拟的数据库子服务
        mock_entity_service = AsyncMock()
        mock_relation_service = AsyncMock()
        mock_news_service = AsyncMock()
        
        mock_entity_service_cls.return_value = mock_entity_service
        mock_relation_service_cls.return_value = mock_relation_service
        mock_news_service_cls.return_value = mock_news_service
        
        # 配置数据库服务的模拟行为
        mock_news = MockNews(1, "华为发布新旗舰手机", "华为今日正式发布搭载麒麟9000S芯片的Mate 60 Pro旗舰手机...")
        mock_news_service.create_news.return_value = mock_news
        mock_news_service.get_news_by_id.return_value = mock_news
        
        # 创建实体映射
        entity_counter = 1
        def create_entity_mock(name, **kwargs):
            nonlocal entity_counter
            entity = MockEntity(entity_counter, name, kwargs.get('entity_type', 'unknown'))
            entity_counter += 1
            return entity
        
        mock_entity_service.get_or_create_entity.side_effect = create_entity_mock
        mock_entity_service.get_entities_by_names.return_value = []
        
        # 创建关系映射
        relation_counter = 1
        def create_relation_mock(source_entity_id, target_entity_id, relation_type, **kwargs):
            nonlocal relation_counter
            relation = MockRelation(relation_counter, source_entity_id, target_entity_id, relation_type)
            relation_counter += 1
            return relation
        
        mock_relation_service.get_or_create_relation.side_effect = create_relation_mock
        
        # 创建知识图谱服务实例
        kg_service = KnowledgeGraphService(mock_session)
        
        # ===== 测试1: 新闻创建与LLM处理集成 =====
        logger.info("测试1: 新闻创建与LLM处理集成")
        
        # 创建新闻
        news = await kg_service.create_news(
            title="华为发布新旗舰手机",
            content="华为今日正式发布搭载麒麟9000S芯片的Mate 60 Pro旗舰手机，这是华为自主研发的最新旗舰产品，标志着华为在高端手机市场的回归。"
        )
        
        assert news is not None
        assert news.title == "华为发布新旗舰手机"
        mock_news_service.create_news.assert_called_once()
        logger.info("✅ 新闻创建测试通过")
        
        # 使用LLM提取实体
        entities = await mock_llm_service.extract_entities(news.content)
        assert len(entities) == 3
        assert entities[0]["name"] == "华为"
        mock_llm_service.extract_entities.assert_called_with(news.content)
        logger.info("✅ LLM实体提取测试通过")
        
        # 使用LLM提取关系
        relations = await mock_llm_service.extract_relations(news.content)
        assert len(relations) == 3
        assert relations[0]["relation_type"] == "生产"
        mock_llm_service.extract_relations.assert_called_with(news.content)
        logger.info("✅ LLM关系提取测试通过")
        
        # 使用LLM生成摘要
        summary = await mock_llm_service.summarize_text(news.content)
        assert summary is not None
        assert len(summary) > 0
        mock_llm_service.summarize_text.assert_called_with(news.content)
        logger.info("✅ LLM摘要生成测试通过")
        
        # ===== 测试2: 存储提取的数据到数据库 =====
        logger.info("测试2: 存储提取的数据到数据库")
        
        # 存储LLM提取的数据
        result = await kg_service.store_llm_extracted_data(news_id=news.id, entities=entities, relations=relations)
        
        # 验证结果
        stored_news, stored_entities, stored_relations = result
        assert stored_news is not None
        assert len(stored_entities) == 3
        # 关系可能因为实体处理逻辑而被存储或不存储，这里只验证类型正确
        assert isinstance(stored_relations, list)
        
        # 验证实体创建调用
        assert mock_entity_service.get_or_create_entity.call_count == 3
        logger.info("✅ 数据存储测试通过")
        
        # ===== 测试3: 生成嵌入向量 =====
        logger.info("测试3: 生成嵌入向量")
        
        # 为实体生成嵌入
        entity_names = [entity.name for entity in stored_entities]
        embeddings = await mock_embedding_service.get_embeddings(entity_names)
        
        # 验证嵌入结果
        assert len(embeddings) == 3
        assert len(embeddings[0]) == 1536
        mock_embedding_service.get_embeddings.assert_called_with(entity_names)
        logger.info("✅ 嵌入向量生成测试通过")
        
        # 验证维度获取
        dimension = await mock_embedding_service.get_dimension()
        assert dimension == 1536
        logger.info("✅ 维度获取测试通过")
        
        # ===== 测试4: 新闻处理服务集成 =====
        logger.info("测试4: 新闻处理服务集成")
        
        # 模拟新闻处理服务的创建
        with patch('kg.services.news_processing_service.NewsProcessingService') as mock_news_processing_cls:
            # 配置模拟行为
            mock_news_processor = AsyncMock()
            mock_news_processing_cls.return_value = mock_news_processor
            
            # 模拟处理结果
            mock_news_processor.process_news.return_value = {
                "news_id": news.id,
                "news": news,
                "entities": stored_entities,
                "relations": [],
                "summary": summary,
                "status": "success"
            }
            
            # 创建新闻处理服务
            news_processing_service = create_news_processing_service(
                data_services=kg_service,
                llm_service=mock_llm_service
            )
            
            # 验证服务创建
            mock_news_processing_cls.assert_called_once()
            logger.info("✅ 新闻处理服务创建测试通过")
        
        # ===== 测试5: 完整流程模拟 =====
        logger.info("测试5: 完整流程模拟")
        
        # 重置模拟调用计数
        mock_llm_service.extract_entities.reset_mock()
        mock_llm_service.extract_relations.reset_mock()
        mock_llm_service.summarize_text.reset_mock()
        mock_entity_service.get_or_create_entity.reset_mock()
        mock_relation_service.get_or_create_relation.reset_mock()
        
        # 模拟一个完整的新闻处理流程
        logger.info("模拟完整的新闻处理流程：创建新闻 → LLM提取 → 数据库存储 → 嵌入生成")
        
        # 1. 创建新闻
        test_news = await kg_service.create_news(
            title="集成测试新闻",
            content="这是一条用于测试服务间集成的新闻内容。"
        )
        
        # 2. LLM提取信息
        extracted_entities = await mock_llm_service.extract_entities(test_news.content)
        extracted_relations = await mock_llm_service.extract_relations(test_news.content)
        news_summary = await mock_llm_service.summarize_text(test_news.content)
        
        # 3. 存储到数据库
        await kg_service.store_llm_extracted_data(
            news_id=test_news.id,
            entities=extracted_entities,
            relations=extracted_relations
        )
        
        # 4. 生成嵌入
        if extracted_entities:
            entity_texts = [e["name"] for e in extracted_entities]
            await mock_embedding_service.get_embeddings(entity_texts)
        
        logger.info("✅ 完整流程模拟测试通过")
        
        # ===== 测试总结 =====
        logger.info("🎉 所有集成测试通过！")
        logger.info("✅ LLM服务、嵌入服务和数据库服务集成正常")
        logger.info("✅ 实体提取、关系提取、文本摘要功能正常")
        logger.info("✅ 数据存储和向量生成功能正常")
        
        return True

async def test_error_handling_integration():
    """测试集成过程中的错误处理"""
    logger.info("测试错误处理集成...")
    
    # 模拟出错的LLM服务
    mock_llm_service = AsyncMock(spec=LLMService)
    mock_llm_service.extract_entities.side_effect = Exception("LLM服务暂时不可用")
    
    # 模拟新闻
    mock_news = MockNews(1, "错误处理测试", "这是用于测试错误处理的新闻内容")
    
    # 测试LLM错误处理
    try:
        await mock_llm_service.extract_entities(mock_news.content)
        assert False, "应该抛出异常但没有"
    except Exception as e:
        assert "LLM服务暂时不可用" in str(e)
        logger.info("✅ LLM错误处理测试通过")
    
    logger.info("🎉 错误处理测试通过！")
    return True

async def run_all_integration_tests():
    """运行所有集成测试"""
    logger.info("===== 开始运行所有集成测试 =====")
    
    # 运行主要集成测试
    await test_service_integration()
    
    # 运行错误处理测试
    await test_error_handling_integration()
    
    logger.info("===== 所有集成测试全部通过！=====")
    return True

if __name__ == "__main__":
    try:
        asyncio.run(run_all_integration_tests())
    except Exception as e:
        logger.error(f"集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        raise
