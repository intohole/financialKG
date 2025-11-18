#!/path/to/venv/bin/python
"""
测试新闻处理服务的脚本
"""
import asyncio
import sys
import os
import time

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

from kg.services.news_processing_service import NewsProcessingService
from kg.services.database.knowledge_graph_service import KnowledgeGraphService
from kg.database.connection import init_database_async

async def test_news_processing_service():
    """测试新闻处理服务"""
    print("初始化数据库...")
    await init_database_async()
    
    print("创建知识图谱服务...")
    kg_service = KnowledgeGraphService()
    
    print("创建新闻处理服务...")
    news_service = NewsProcessingService(kg_service)
    
    # 准备测试数据 - 使用唯一的URL避免重复插入
    test_news_data = {
        "title": "Apple Unveils New iPhone 15 Series",
        "content": "Apple today unveiled its highly anticipated iPhone 15 series at a special event held in Cupertino, California. The new lineup includes four models: iPhone 15, iPhone 15 Plus, iPhone 15 Pro, and iPhone 15 Pro Max. Key features include USB-C connectivity, improved cameras, and faster A17 Pro chips for the Pro models. Tim Cook, Apple's CEO, emphasized the company's commitment to sustainability with all new iPhones using 100% recycled rare earth elements in their magnets. The iPhone 15 series is set to go on sale starting September 22, with pre-orders beginning on September 15.",
        "source": "TechCrunch",
        "source_url": f"https://techcrunch.com/2023/09/12/apple-iphone-15-series-{int(time.time())}",
        "publish_date": "2023-09-12T10:30:00Z",
        "author": "John Doe"
    }
    
    print("开始处理测试新闻...")
    print(f"新闻标题: {test_news_data['title']}")
    print(f"来源: {test_news_data['source']}")
    print(f"发布时间: {test_news_data['publish_date']}")
    print(f"作者: {test_news_data['author']}")
    print("\n" + "="*50 + "\n")
    
    try:
        result = await news_service.process_and_store_news(test_news_data)
        print("新闻处理成功！")
        print(f"新闻ID: {result['news_id']}")
        print(f"新闻摘要: {result['summary']}")
        print(f"提取实体数量: {len(result['entities'])}")
        
        # 打印提取的实体
        print("\n提取的实体:")
        for entity in result['entities']:
            print(f"- {entity.name} ({entity.type})")
        
        print(f"提取关系数量: {len(result['relations'])}")
        
        # 打印提取的关系
        print("\n提取的关系:")
        for relation in result['relations']:
            # 获取实体名称以便更好地显示
            source_name = relation.source_entity.name if hasattr(relation, 'source_entity') else f"ID:{relation.source_entity_id}"
            target_name = relation.target_entity.name if hasattr(relation, 'target_entity') else f"ID:{relation.target_entity_id}"
            print(f"- {source_name} -> {relation.relation_type} -> {target_name}")
            
    except Exception as e:
        print(f"处理新闻时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_news_processing_service())
