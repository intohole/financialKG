#!/usr/bin/env python3
"""知识图谱服务测试运行器

直接运行测试，无需pytest依赖
"""

import asyncio
import logging
import sys
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 设置特定模块的调试日志
logging.getLogger('app.core.entity_extractor').setLevel(logging.DEBUG)
logging.getLogger('app.core.relation_extractor').setLevel(logging.DEBUG)

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.knowledge_graph_service import KnowledgeGraphService
from app.core.models import KnowledgeExtractionResult, ContentClassification


async def test_knowledge_extraction():
    """测试知识图谱提取功能"""
    logger.info("开始测试知识图谱提取功能...")
    
    # 初始化服务
    service = KnowledgeGraphService()
    
    # 测试文本 - 金融新闻
    test_text = """
    阿里巴巴集团是中国最大的电子商务公司之一，总部位于杭州。
    腾讯控股有限公司也是一家大型科技公司，总部位于深圳。
    两家公司都在人工智能领域进行投资，并生产各种数字产品。
    阿里巴巴与蚂蚁集团有合作关系，蚂蚁集团属于金融科技行业。
    """
    
    logger.info(f"测试文本: {test_text[:100]}...")
    
    # 提取知识图谱
    result = await service.extract_knowledge_from_text(test_text)
    
    logger.info(f"内容分类结果: {result.content_classification}")
    logger.info(f"提取的实体数量: {len(result.knowledge_graph.entities)}")
    logger.info(f"提取的关系数量: {len(result.knowledge_graph.relations)}")
    logger.info(f"处理时间: {result.processing_time:.2f}秒")
    
    # 打印实体
    logger.info("提取的实体:")
    for entity in result.knowledge_graph.entities:
        logger.info(f"  - {entity.name} ({entity.type}): {entity.description}")
    
    # 打印关系
    logger.info("提取的关系:")
    for relation in result.knowledge_graph.relations:
        logger.info(f"  - {relation.subject} -> {relation.predicate} -> {relation.object}")
    
    return result


async def test_non_financial_content():
    """测试非金融内容"""
    logger.info("开始测试非金融内容...")
    
    service = KnowledgeGraphService()
    
    # 测试文本 - 非金融内容
    test_text = """
    今天天气很好，适合出去散步。
    我喜欢在公园里看书，感觉非常放松。
    晚上准备和朋友一起吃饭，讨论周末的计划。
    """
    
    result = await service.extract_knowledge_from_text(test_text)
    
    logger.info(f"内容分类结果: {result.content_classification}")
    logger.info(f"是否为金融内容: {result.content_classification.is_financial_content}")
    logger.info(f"置信度: {result.content_classification.confidence}")
    logger.info(f"推理: {result.content_classification.reasoning}")
    
    return result


async def test_real_financial_news():
    """测试真实金融新闻"""
    logger.info("开始测试真实金融新闻...")
    
    service = KnowledgeGraphService()
    
    # 真实金融新闻文本
    news_text = """
    中国证监会近日发布新规，加强对上市公司财务信息披露的监管。
    新规要求上市公司在年报中详细披露ESG相关信息。
    上海证券交易所和深圳证券交易所将同步实施该规定。
    此举旨在提高市场透明度，保护投资者权益。
    多家券商分析师表示，这将推动企业治理水平提升。
    中信证券、华泰证券等头部券商将受益于监管趋严。
    """
    
    result = await service.extract_knowledge_from_text(news_text)
    
    logger.info(f"内容分类结果: {result.content_classification}")
    logger.info(f"提取的实体数量: {len(result.knowledge_graph.entities)}")
    logger.info(f"提取的关系数量: {len(result.knowledge_graph.relations)}")
    
    # 打印详细结果
    logger.info("详细提取结果:")
    for entity in result.knowledge_graph.entities:
        logger.info(f"  实体: {entity.name} ({entity.type})")
    
    for relation in result.knowledge_graph.relations:
        logger.info(f"  关系: {relation.subject} -> {relation.predicate} -> {relation.object}")
    
    return result


async def main():
    """主测试函数"""
    logger.info("=" * 60)
    logger.info("开始知识图谱服务测试")
    logger.info("=" * 60)
    
    try:
        # 测试1: 基础知识提取
        logger.info("\n" + "="*50)
        logger.info("测试1: 基础知识提取")
        logger.info("="*50)
        result1 = await test_knowledge_extraction()
        
        # 测试2: 非金融内容
        logger.info("\n" + "="*50)
        logger.info("测试2: 非金融内容")
        logger.info("="*50)
        result2 = await test_non_financial_content()
        
        # 测试3: 真实金融新闻
        logger.info("\n" + "="*50)
        logger.info("测试3: 真实金融新闻")
        logger.info("="*50)
        result3 = await test_real_financial_news()
        
        logger.info("\n" + "="*60)
        logger.info("所有测试完成！")
        logger.info("="*60)
        
        return {
            "basic_extraction": result1,
            "non_financial": result2,
            "real_news": result3
        }
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        logger.exception(e)
        return None


if __name__ == "__main__":
    # 运行测试
    result = asyncio.run(main())
    
    if result:
        logger.info("测试成功完成！")
    else:
        logger.error("测试失败！")