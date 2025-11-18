#!/usr/bin/env python3
"""
测试API提交功能
"""

import asyncio
import json
from datetime import datetime
from kg.services.news_processing_service import NewsProcessingService
from kg.services.database.knowledge_graph_service import KnowledgeGraphService
from kg.database.connection import get_db_session


async def test_api_submission():
    """测试API提交功能"""
    print("开始测试API提交功能...")
    
    # 初始化服务
    session = get_db_session()
    kg_service = KnowledgeGraphService(session)
    news_service = NewsProcessingService(kg_service)
    
    # 测试新闻数据
    test_news = {
        "title": "测试API提交功能",
        "content": "这是一个测试API提交功能的新闻。苹果公司发布了最新财报，显示营收增长10%。CEO蒂姆·库克表示对未来的增长充满信心。",
        "source": "测试来源",
        "author": "测试作者",
        "publish_time": datetime.now().isoformat(),
        "source_url": f"https://test.example.com/api-test-{datetime.now().timestamp()}"
    }
    
    # 处理新闻
    print("\n处理新闻...")
    result = await news_service.process_and_store_news(test_news)
    
    if result:
        print("新闻处理成功！")
        print(f"新闻ID: {result['news_id']}")
        print(f"提取实体数量: {len(result['entities'])}")
        print(f"提取关系数量: {len(result['relations'])}")
        
        # 准备API提交数据
        submission_data = {
            "news_id": result['news_id'],
            "entities": [
                {
                    "name": entity.name,
                    "type": entity.type,
                    "canonical_name": entity.canonical_name,
                    "source": entity.source
                }
                for entity in result['entities']
            ],
            "relations": [
                {
                    "source_entity_id": relation.source_entity_id,
                    "target_entity_id": relation.target_entity_id,
                    "relation_type": relation.relation_type,
                    "canonical_relation": relation.canonical_relation,
                    "source": relation.source
                }
                for relation in result['relations']
            ]
        }
        
        # 保存提交数据到文件
        with open("api_submission_test.json", "w", encoding="utf-8") as f:
            json.dump(submission_data, f, ensure_ascii=False, indent=2)
        
        print("\nAPI提交数据已保存到 api_submission_test.json")
        print("可以使用以下命令测试API提交:")
        print('curl -X POST http://localhost:8000/api/v1/knowledge/submit \\')
        print('  -H "Content-Type: application/json" \\')
        print('  -d @api_submission_test.json')
    else:
        print("新闻处理失败")


if __name__ == "__main__":
    asyncio.run(test_api_submission())