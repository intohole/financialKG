#!/usr/bin/env python3
"""
调试脚本：用于调试KGCoreImplService的process_content方法

该脚本创建一个完整的调试环境，可以在PyCharm中设置断点进行调试，
不需要手动输入，直接运行即可。
"""

import asyncio
import logging
from typing import Optional
from datetime import datetime

# 设置日志级别
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入必要的模块
from app.services.kg_core_impl import KGCoreImplService
from app.config.config_manager import ConfigManager


async def debug_process_content():
    """
    调试process_content方法的主函数
    """
    logger.info("开始调试process_content方法")
    
    try:
        # 1. 初始化配置管理器
        config_manager = ConfigManager()
        logger.info("配置管理器初始化完成")
        
        # 2. 创建KGCoreImplService实例
        # 注意：这里使用默认的auto_init_store=True，让服务自动初始化存储
        kg_service = KGCoreImplService()
        logger.info("KGCoreImplService实例创建完成")
        
        # 3. 手动初始化服务（确保store被正确初始化）
        logger.info("开始初始化服务...")
        await kg_service.initialize()
        logger.info("服务初始化完成")
        
        # 4. 准备测试内容（可以根据需要修改）
        test_content = """
        特斯拉公司（Tesla Inc.）今日宣布，其2024年第二季度的全球汽车交付量达到443,956辆，
        同比增长5.5%，环比增长3.7%。这一数据超出了市场分析师的预期。
        
        特斯拉CEO埃隆·马斯克（Elon Musk）表示，这一成绩得益于上海超级工厂和柏林超级工厂的产能提升，
        以及Model Y和Model 3的持续热销。特别是在中国市场，特斯拉的销量同比增长了23.4%。
        
        此外，特斯拉还宣布将在2024年第四季度推出新一代低成本车型，预计售价将低于2.5万美元。
        这将使特斯拉进入更广阔的大众市场，进一步扩大市场份额。
        
        分析师认为，特斯拉的强劲表现表明电动汽车市场需求依然旺盛，
        尽管面临来自传统汽车制造商和新兴电动车企业的激烈竞争。
        """
        
        logger.info(f"测试内容准备完成，长度：{len(test_content)} 字符")
        
        # 5. 调用process_content方法（在这里可以设置断点）
        logger.info("开始调用process_content方法...")
        # 【建议断点位置】：在下面这行代码设置断点，然后可以单步执行整个处理流程
        knowledge_graph = await kg_service.process_content(test_content)
        
        # 6. 打印处理结果
        logger.info("process_content方法执行完成")
        logger.info(f"提取到的实体数量：{len(knowledge_graph.entities)}")
        logger.info(f"提取到的关系数量：{len(knowledge_graph.relations)}")
        logger.info(f"内容分类：{knowledge_graph.category}")
        
        # 打印实体信息
        logger.info("提取的实体列表：")
        for i, entity in enumerate(knowledge_graph.entities[:5]):  # 只打印前5个
            logger.info(f"  {i+1}. {entity.name} (类型: {entity.type}, ID: {entity.id})")
        
        # 打印关系信息
        logger.info("提取的关系列表：")
        for i, relation in enumerate(knowledge_graph.relations[:5]):  # 只打印前5个
            logger.info(f"  {i+1}. {relation.subject} -> {relation.predicate} -> {relation.object}")
        
        # 打印元数据
        if knowledge_graph.metadata:
            logger.info("元数据信息：")
            for key, value in knowledge_graph.metadata.items():
                logger.info(f"  {key}: {value}")
        
        return knowledge_graph
        
    except Exception as e:
        logger.error(f"调试过程中发生错误：{e}", exc_info=True)
        raise


async def debug_specific_step():
    """
    用于调试特定步骤的函数（如果需要单独调试某个子方法）
    """
    logger.info("开始调试特定步骤")
    
    try:
        # 这里可以添加针对特定方法的调试代码
        # 例如：_process_entities_with_vector_search, _process_relations 等
        
        kg_service = KGCoreImplService()
        await kg_service.initialize()
        
        # 示例：调试实体处理
        # entities = [Entity(...)]  # 准备测试实体
        # processed = await kg_service._process_entities_with_vector_search(entities)
        
    except Exception as e:
        logger.error(f"特定步骤调试失败：{e}", exc_info=True)


if __name__ == "__main__":
    """
    主函数入口
    
    使用说明：
    1. 在PyCharm中打开此文件
    2. 在需要调试的位置设置断点（建议在调用process_content的位置）
    3. 右键选择"Debug 'debug_process_content'"
    4. 程序会在断点处暂停，可以进行单步调试、查看变量值等操作
    """
    
    logger.info("=== 调试脚本启动 ===")
    
    # 运行主调试函数
    try:
        # 选择要运行的调试函数
        asyncio.run(debug_process_content())
        # 或者运行特定步骤调试
        # asyncio.run(debug_specific_step())
    except KeyboardInterrupt:
        logger.info("调试脚本被用户中断")
    except Exception as e:
        logger.error(f"脚本执行失败：{e}", exc_info=True)
    finally:
        logger.info("=== 调试脚本结束 ===")
