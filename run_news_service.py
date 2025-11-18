#!/path/to/venv/bin/python
"""
运行新闻处理服务的简单测试脚本
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

from kg.services.news_processing_service import NewsProcessingService
from kg.services.data_services import KnowledgeGraphService
from kg.database.connection import init_database_async

async def test_news_processing():
    """测试新闻处理服务"""
    print("初始化数据库...")
    await init_database_async()
    
    print("创建知识图谱服务...")
    kg_service = KnowledgeGraphService()
    
    print("创建新闻处理服务...")
    news_service = NewsProcessingService(kg_service)
    
    # 准备测试数据
    from datetime import datetime
    test_news_data = {
        "title": "苹果公司发布新款iPhone 15系列",
        "content": "苹果公司今日在加州库比蒂诺特别活动中发布了备受期待的iPhone 15系列。新系列包括四款型号：iPhone 15、iPhone 15 Plus、iPhone 15 Pro和iPhone 15 Pro Max。主要特性包括USB-C连接、改进的摄像头以及Pro型号更快的A17 Pro芯片。苹果公司CEO蒂姆·库克强调了公司对可持续发展的承诺，所有新款iPhone都使用100%回收稀土元素制造磁铁。iPhone 15系列将于9月22日开始销售，9月15日开始预购。",
        "source": "科技新闻",
        "source_url": f"https://example.com/news/apple-iphone-15-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "publish_date": "2023-09-12T10:30:00Z",
        "author": "张三"
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
    asyncio.run(test_news_processing())