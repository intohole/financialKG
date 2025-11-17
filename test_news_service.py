import asyncio
import sys
import os
import uuid

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from kg.services.news_processing_service import NewsProcessingService
from kg.services.database.knowledge_graph_service import KnowledgeGraphService
from kg.database.connection import db_session, init_database_async

async def test_news_processing():
    """
    测试新闻处理服务
    """
    print("开始测试新闻处理服务...")
    
    try:
        # 初始化数据库
        await init_database_async()
        
        # 获取数据库会话
        async with db_session() as session:
            # 创建服务实例
            kg_service = KnowledgeGraphService(session)
            news_service = NewsProcessingService(kg_service)
            
            # 准备测试新闻数据
            unique_id = uuid.uuid4()
            test_news = {
                "title": "2023年中国经济增长强劲",
                "content": "2023年中国GDP同比增长5.2%，达到126.06万亿元。经济增长主要得益于消费复苏和科技创新。",
                "source_url": f"https://example.com/news/2023-economy-{unique_id}",
                "publish_date": "2024-01-17T10:00:00",
                "source": "人民日报",
                "author": "经济部记者"
            }
            
            print(f"测试新闻标题: {test_news['title']}")
            print(f"测试新闻来源: {test_news['source']}")
            print(f"测试新闻发布日期: {test_news['publish_date']}")
            print(f"测试新闻URL: {test_news['source_url']}")
            
            # 处理新闻
            result = await news_service.process_and_store_news(test_news)
            
            print(f"\n处理结果:")
            print(f"新闻ID: {result['news_id']}")
            print(f"存储的实体数量: {len(result['entities'])}")
            print(f"存储的关系数量: {len(result['relations'])}")
            print(f"新闻摘要: {result['summary']}")
            
            # 验证实体和关系
            if result['entities']:
                print(f"\n示例实体:")
                for entity in result['entities'][:2]:  # 显示前两个实体
                    print(f"  - {entity.name} (类型: {entity.type})")
            
            if result['relations']:
                print(f"\n示例关系:")
                for relation in result['relations'][:2]:  # 显示前两个关系
                    print(f"  - {relation.source_entity_id} -> {relation.target_entity_id} ({relation.relation_type})")
            
            print(f"\n测试成功！新闻已处理并存储到数据库。")
            
    except Exception as e:
        print(f"测试失败: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_news_processing())