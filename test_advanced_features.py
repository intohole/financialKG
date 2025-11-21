#!/usr/bin/env python3
"""高级功能测试：实体消歧、新闻摘要、量化信息处理"""

import asyncio
from app.core.knowledge_graph_service import KnowledgeGraphService
from app.core.models import Entity

async def test_advanced_features():
    """测试高级功能"""
    
    print("=== 高级功能测试 ===\n")
    
    service = KnowledgeGraphService()
    
    # 1. 测试新闻摘要提取
    print("1. 新闻摘要提取测试:")
    news_text = """
    苹果公司今日发布2024年第四季度财报，营收达到1234亿美元，同比增长8%。
    其中iPhone销售额为678亿美元，服务业务营收达到234亿美元，创下历史新高。
    公司CEO蒂姆·库克表示，这一成绩主要得益于iPhone 15系列的强劲表现和服务生态系统的持续扩张。
    财报发布后，苹果股价在盘后交易中上涨3.5%，市值突破3万亿美元。
    """
    
    summary_result = await service.extract_news_summary(news_text, max_length=150)
    print(f"摘要: {summary_result['summary']}")
    print(f"关键词: {summary_result['keywords']}")
    print(f"重要性评分: {summary_result['importance_score']}")
    print(f"压缩率: {summary_result['compression_ratio']:.1%}")
    print()
    
    # 2. 测试实体消歧
    print("2. 实体消歧测试:")
    
    # 创建"苹果"的不同候选实体
    apple_candidates = [
        Entity(
            name="苹果",
            type="水果",
            description="蔷薇科苹果属植物的果实，富含维生素，可食用",
            category="food"
        ),
        Entity(
            name="苹果公司",
            type="科技公司",
            description="美国苹果公司(Apple Inc.)，全球知名科技公司，生产iPhone、Mac等产品",
            category="technology"
        ),
        Entity(
            name="苹果日报",
            type="媒体",
            description="香港的一份中文报纸，已停刊",
            category="media"
        )
    ]
    
    # 测试不同上下文下的消歧
    test_contexts = [
        "我今天吃了一个苹果，味道很甜",
        "苹果公司发布了新款iPhone，股价上涨了5%",
        "苹果日报报道了这次事件"
    ]
    
    for context in test_contexts:
        print(f"上下文: {context}")
        resolution = await service.smart_entity_resolution("苹果", apple_candidates, context)
        if resolution['resolved_entity']:
            print(f"  解析结果: {resolution['resolved_entity'].name} ({resolution['resolved_entity'].type})")
            print(f"  置信度: {resolution['confidence']}")
            print(f"  推理: {resolution['reasoning']}")
        else:
            print(f"  无法确定具体指代")
        print()
    
    # 3. 测试量化信息提取
    print("3. 量化信息处理测试:")
    financial_text = """
    腾讯控股2024年第三季度营收达到1540亿元人民币，同比增长10%。
    其中游戏业务营收450亿元，广告业务营收300亿元。
    公司净利润400亿元，较去年同期增长15%。
    截至9月30日，公司现金储备为2500亿元。
    """
    
    # 提取知识图谱
    extraction_result = await service.extract_knowledge_from_text(financial_text, 'financial')
    
    if extraction_result['success']:
        print(f"提取到 {len(extraction_result['entities'])} 个实体:")
        for entity in extraction_result['entities']:
            print(f"  - {entity['name']} ({entity['type']})")
        
        print(f"提取到 {len(extraction_result['relations'])} 个关系:")
        for relation in extraction_result['relations']:
            print(f"  - {relation['subject']} -> {relation['predicate']} -> {relation['object']}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    asyncio.run(test_advanced_features())