#!/usr/bin/env python3
"""多类别知识图谱测试脚本

测试多类别知识提取、类别兼容性检查和实体相似度比较功能
"""

import asyncio
import json
import sys
from typing import Dict, Any, List

from app.core.knowledge_graph_service import KnowledgeGraphService
from app.core.models import Entity


async def test_multi_category_extraction():
    """测试多类别知识提取"""
    print("=== 测试多类别知识提取 ===")
    
    kg_service = KnowledgeGraphService()
    
    # 测试不同类别的文本
    test_cases = [
        {
            "category": "financial",
            "text": "腾讯公司今日宣布，将投资10亿元人民币用于人工智能技术研发。该公司表示，这笔投资将在未来三年内完成，主要用于建设AI实验室和招募顶尖人才。",
            "description": "金融投资类文本"
        },
        {
            "category": "technology", 
            "text": "华为发布了最新的5G芯片麒麟9000，该芯片采用5纳米工艺制造，集成了超过150亿个晶体管，支持Sub-6GHz和毫米波频段。",
            "description": "科技产品类文本"
        },
        {
            "category": "medical",
            "text": "北京协和医院的研究团队发现，使用PD-1抑制剂治疗晚期肺癌患者，可以显著延长患者的无进展生存期，中位生存期从8个月提高到16个月。",
            "description": "医疗研究类文本"
        },
        {
            "category": "education",
            "text": "清华大学计算机系开设了人工智能专业，该专业涵盖机器学习、深度学习、自然语言处理等核心课程，旨在培养AI领域的高端人才。",
            "description": "教育培训类文本"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n--- 测试 {test_case['description']} ---")
        print(f"类别: {test_case['category']}")
        print(f"文本: {test_case['text'][:100]}...")
        
        # 测试指定类别的提取
        result = await kg_service.extract_knowledge_from_text(
            text=test_case['text'],
            category=test_case['category']
        )
        
        print(f"提取结果: {'成功' if result['success'] else '失败'}")
        print(f"消息: {result['message']}")
        
        if result['success']:
            print(f"提取实体数: {len(result['entities'])}")
            print(f"提取关系数: {len(result['relations'])}")
            
            # 显示提取的实体
            for i, entity in enumerate(result['entities'][:3]):  # 只显示前3个
                print(f"  实体{i+1}: {entity['name']} ({entity['type']}) - 类别: {entity.get('category', 'unknown')}")
        
        print("-" * 50)


async def test_category_compatibility():
    """测试类别兼容性检查"""
    print("\n=== 测试类别兼容性检查 ===")
    
    kg_service = KnowledgeGraphService()
    
    # 测试文本
    test_text = "苹果公司发布了新款iPhone，搭载了最新的A17处理器，性能比上一代提升了20%。"
    
    # 测试不同类别
    test_categories = ["financial", "technology", "medical", "education"]
    
    print(f"测试文本: {test_text}")
    print()
    
    for category in test_categories:
        print(f"检查类别 '{category}':")
        
        result = await kg_service.check_text_category_compatibility(
            text=test_text,
            category=category
        )
        
        print(f"  是否支持: {'是' if result['is_supported'] else '否'}")
        print(f"  是否兼容: {'是' if result['is_compatible'] else '否'}")
        print(f"  检测类别: {result['detected_category']}")
        print(f"  置信度: {result['confidence']:.2f}")
        print(f"  理由: {result['reasoning']}")
        print()


async def test_entity_similarity():
    """测试实体相似度比较"""
    print("\n=== 测试实体相似度比较 ===")
    
    kg_service = KnowledgeGraphService()
    
    # 创建测试实体
    test_entities = [
        Entity(
            name="腾讯科技",
            type="公司",
            description="中国领先的互联网科技公司",
            category="technology"
        ),
        Entity(
            name="腾讯公司",
            type="企业",
            description="中国大型互联网科技企业集团",
            category="technology"
        ),
        Entity(
            name="阿里巴巴",
            type="公司", 
            description="中国电商巨头",
            category="technology"
        ),
        Entity(
            name="清华大学",
            type="学校",
            description="中国顶尖高等学府",
            category="education"
        ),
        Entity(
            name="清华",
            type="大学",
            description="北京著名高校",
            category="education"
        )
    ]
    
    print(f"测试实体数量: {len(test_entities)}")
    print()
    
    # 比较实体
    comparisons = await kg_service.compare_entities_in_same_category(test_entities)
    
    print("实体比较结果:")
    for comparison in comparisons:
        entity1_name = comparison["entity1"]["name"]
        entity2_name = comparison["entity2"]["name"]
        similarity_score = comparison["similarity_score"]
        is_same = comparison["is_same_entity"]
        reasoning = comparison["reasoning"]
        
        print(f"\n'{entity1_name}' vs '{entity2_name}':")
        print(f"  相似度: {similarity_score:.2f}")
        print(f"  是否相同: {'是' if is_same else '否'}")
        print(f"  理由: {reasoning}")


async def test_get_supported_categories():
    """测试获取支持的类别"""
    print("\n=== 测试获取支持的类别 ===")
    
    kg_service = KnowledgeGraphService()
    
    categories = await kg_service.get_supported_categories()
    
    print("支持的类别:")
    for category in categories:
        print(f"  - {category}")
    
    print(f"\n总计: {len(categories)} 个类别")


async def test_mixed_category_extraction():
    """测试混合类别提取"""
    print("\n=== 测试混合类别提取（自动检测） ===")
    
    kg_service = KnowledgeGraphService()
    
    # 测试不指定类别的自动检测
    test_texts = [
        "中国平安保险公司今日发布财报，净利润同比增长15%，达到1200亿元人民币。",
        "华为公司发布了最新的鸿蒙操作系统，该系统支持手机、平板、智能手表等多种设备。",
        "上海瑞金医院成功完成了首例基因编辑治疗，为遗传性疾病患者带来了新的希望。",
        "北京大学开设了区块链技术课程，该课程涵盖密码学、分布式系统、智能合约等内容。"
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n--- 测试文本 {i} ---")
        print(f"文本: {text}")
        
        # 不指定类别，让系统自动检测
        result = await kg_service.extract_knowledge_from_text(text=text)
        
        print(f"提取结果: {'成功' if result['success'] else '失败'}")
        print(f"消息: {result['message']}")
        
        if result['success']:
            print(f"使用类别: {result.get('category', 'unknown')}")
            print(f"提取实体数: {len(result['entities'])}")
            print(f"提取关系数: {len(result['relations'])}")


async def main():
    """主测试函数"""
    print("多类别知识图谱系统测试")
    print("=" * 60)
    
    try:
        # 运行所有测试
        await test_get_supported_categories()
        await test_category_compatibility()
        await test_multi_category_extraction()
        await test_entity_similarity()
        await test_mixed_category_extraction()
        
        print("\n" + "=" * 60)
        print("所有测试完成！")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    # 运行异步主函数
    exit_code = asyncio.run(main())
    sys.exit(exit_code)