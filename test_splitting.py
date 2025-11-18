import asyncio
from sqlalchemy.orm import Session
from kg.database.connection import db_session
from kg.services.database.knowledge_graph_service import KnowledgeGraphService
from kg.services.database.deduplication_service import DeduplicationService
from kg.services.database.statistics_service import StatisticsService

async def test_statistics_service():
    """测试统计服务"""
    async with db_session() as session:
        knowledge_graph_service = KnowledgeGraphService(session)
        statistics_service = StatisticsService(knowledge_graph_service.entity_service, knowledge_graph_service.relation_service, knowledge_graph_service.news_service)
        
        print("=== Testing Statistics Service ===")
        
        # 获取统计信息
        stats = await knowledge_graph_service.get_statistics()
        stats2 = await statistics_service.get_statistics()
        
        print(f"KnowledgeGraphService.get_statistics(): {stats}")
        print(f"StatisticsService.get_statistics(): {stats2}")
        
        # 验证结果一致
        assert stats == stats2, "统计信息不一致"
        print("✓ 统计服务测试通过")

async def test_deduplication_service():
    """测试去重服务"""
    async with db_session() as session:
        knowledge_graph_service = KnowledgeGraphService(session)
        deduplication_service = DeduplicationService(knowledge_graph_service.entity_service, knowledge_graph_service.relation_service)
        
        print("\n=== Testing Deduplication Service ===")
        
        # 测试实体去重
        entity_groups1 = await knowledge_graph_service.deduplicate_entities()
        entity_groups2 = await deduplication_service.deduplicate_entities()
        
        print(f"KnowledgeGraphService.deduplicate_entities(): {len(entity_groups1)} groups")
        print(f"DeduplicationService.deduplicate_entities(): {len(entity_groups2)} groups")
        
        # 验证结果一致
        assert len(entity_groups1) == len(entity_groups2), "实体去重结果数量不一致"
        print("✓ 实体去重测试通过")
        
        # 测试关系去重
        relation_groups1 = await knowledge_graph_service.deduplicate_relations()
        relation_groups2 = await deduplication_service.deduplicate_relations()
        
        print(f"KnowledgeGraphService.deduplicate_relations(): {len(relation_groups1)} groups")
        print(f"DeduplicationService.deduplicate_relations(): {len(relation_groups2)} groups")
        
        # 验证结果一致
        assert len(relation_groups1) == len(relation_groups2), "关系去重结果数量不一致"
        print("✓ 关系去重测试通过")

async def test_other_methods():
    """测试其他方法"""
    async with db_session() as session:
        knowledge_graph_service = KnowledgeGraphService(session)
        
        print("\n=== Testing Other Methods ===")
        
        # 测试获取新闻方法
        news = await knowledge_graph_service.get_news_by_id(1)
        print(f"get_news_by_id(1): {news}")
        
        # 测试获取实体方法
        entity = await knowledge_graph_service.get_entity_by_id(1)
        print(f"get_entity_by_id(1): {entity}")
        
        # 测试获取实体列表方法
        entities = await knowledge_graph_service.get_entities(page=1, page_size=5)
        print(f"get_entities(): {len(entities)} entities")
        
        print("✓ 其他方法测试通过")

async def main():
    """运行所有测试"""
    await test_statistics_service()
    await test_deduplication_service()
    await test_other_methods()
    print("\n🎉 所有测试通过！")

if __name__ == "__main__":
    asyncio.run(main())