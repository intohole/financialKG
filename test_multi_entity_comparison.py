#!/usr/bin/env python3
"""测试多实体比较功能"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.knowledge_graph_service import KnowledgeGraphService
from app.core.models import Entity


async def test_multi_entity_comparison():
    """测试多实体比较功能"""
    print("=== 测试多实体比较功能 ===\n")
    
    # 创建知识图谱服务
    kg_service = KnowledgeGraphService()
    
    # 创建测试实体列表（包含可能相同的实体）
    test_entities = [
        Entity(
            name="阿里巴巴",
            type="公司",
            category="technology",
            description="中国大型电商平台公司"
        ),
        Entity(
            name="阿里巴巴集团",
            type="公司",
            category="technology", 
            description="阿里巴巴集团有限公司，电商巨头"
        ),
        Entity(
            name="腾讯",
            type="公司",
            category="technology",
            description="中国大型互联网公司，社交和游戏业务"
        ),
        Entity(
            name="深圳市腾讯计算机系统有限公司",
            type="公司",
            category="technology",
            description="腾讯公司全称，互联网服务提供商"
        ),
        Entity(
            name="百度",
            type="公司", 
            category="technology",
            description="中国搜索引擎公司"
        )
    ]
    
    print("测试实体列表:")
    for i, entity in enumerate(test_entities, 1):
        print(f"{i}. {entity.name} ({entity.type}) - {entity.description}")
    print()
    
    try:
        # 执行多实体比较
        results = await kg_service.compare_entities_in_same_category(test_entities)
        
        print("=== 多实体比较结果 ===\n")
        
        if not results:
            print("未获得比较结果")
            return
            
        # 显示比较结果
        for result in results:
            entity1_name = result["entity1"]["name"]
            entity2_name = result["entity2"]["name"]
            similarity_score = result["similarity_score"]
            is_same = result["is_same_entity"]
            reasoning = result["reasoning"]
            
            print(f"实体对比: {entity1_name} vs {entity2_name}")
            print(f"相似度评分: {similarity_score}")
            print(f"是否相同: {'是' if is_same else '否'}")
            print(f"推理: {reasoning}")
            print("-" * 50)
            
        # 统计结果
        total_comparisons = len(results)
        same_entity_count = sum(1 for r in results if r["is_same_entity"])
        
        print(f"\n=== 统计信息 ===")
        print(f"总比较对数: {total_comparisons}")
        print(f"判断为相同实体: {same_entity_count} 对")
        print(f"判断为不同实体: {total_comparisons - same_entity_count} 对")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


async def test_smart_entity_resolution():
    """测试智能实体解析"""
    print("\n=== 测试智能实体解析 ===\n")
    
    kg_service = KnowledgeGraphService()
    
    # 创建候选实体
    candidates = [
        Entity(
            name="阿里巴巴",
            type="公司",
            category="technology",
            description="中国电商巨头"
        ),
        Entity(
            name="腾讯",
            type="公司", 
            category="technology",
            description="中国互联网公司"
        ),
        Entity(
            name="百度",
            type="公司",
            category="technology", 
            description="中国搜索引擎公司"
        )
    ]
    
    context = "这家科技公司在电商领域占据重要地位，近年来也涉足云计算业务"
    
    try:
        result = await kg_service.smart_entity_resolution(
            entity_name="阿里",
            candidates=candidates,
            context=context
        )
        
        print(f"待解析实体: 阿里")
        print(f"上下文: {context}")
        print(f"候选实体: {[c.name for c in candidates]}")
        print()
        
        if result["resolved_entity"]:
            print(f"解析结果: {result['resolved_entity'].name}")
            print(f"置信度: {result['confidence']}")
            print(f"推理: {result['reasoning']}")
        else:
            print("未能解析到具体实体")
            print(f"原因: {result['reasoning']}")
            
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("开始测试知识图谱多实体比较功能...\n")
    
    # 运行测试
    asyncio.run(test_multi_entity_comparison())
    asyncio.run(test_smart_entity_resolution())
    
    print("\n测试完成!")