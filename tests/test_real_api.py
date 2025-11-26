"""
测试真实的Embedding API调用
"""

import asyncio
from app.config.config_manager import ConfigManager
from app.embedding.embedding_service import EmbeddingService
from app.embedding.exceptions import EmbeddingError
from app.utils.logging_utils import get_logger

logger = get_logger(__name__)


def test_real_embedding_api():
    """
    测试真实的Embedding API调用
    """
    logger.info("===== 测试真实的Embedding API调用 =====\n")
    
    try:
        # 初始化配置管理器
        logger.info("1. 初始化配置管理器...")
        config_manager = ConfigManager()
        
        # 初始化嵌入服务
        logger.info("2. 初始化嵌入服务...")
        embedding_service = EmbeddingService(config_manager)
        
        # 获取服务统计信息
        stats = embedding_service.get_stats()
        logger.info(f"3. 服务统计信息:")
        logger.info(f"   - 使用模型: {stats['model']}")
        logger.info(f"   - 缓存大小: {stats['cache_size']}/{stats['max_cache_size']}")
        logger.info(f"   - 配置详情: {embedding_service._client._config}")
        logger.info("")
        
        # 准备测试文本
        test_text = "你好，今天天气怎么样。"
        logger.info(f"4. 测试文本: {test_text}")
        logger.info("")
        
        # 执行嵌入
        logger.info("5. 执行嵌入调用...")
        embedding = embedding_service.embed_text(test_text)
        
        # 输出结果
        logger.info("6. 嵌入结果:")
        logger.info(f"   - 嵌入向量: {embedding}")
        logger.info(f"   - 向量维度: {len(embedding)}")
        logger.info(f"   - 向量和: {sum(embedding):.6f}")
        logger.info(f"   - 向量平方和: {sum(x*x for x in embedding):.6f}")
        logger.info("")
        
        # 测试批量嵌入
        logger.info("7. 测试批量嵌入...")
        batch_texts = [
            "你好，今天天气怎么样。",
            "这是第二条测试文本。",
            "测试智谱AI的embedding-3模型。"
        ]
        
        batch_embeddings = embedding_service.embed_batch(batch_texts)
        logger.info(f"   - 批量嵌入完成，文本数量: {len(batch_texts)}")
        logger.info(f"   - 向量数量: {len(batch_embeddings)}")
        logger.info(f"   - 第一个向量: {batch_embeddings[0]}")
        logger.info(f"   - 第一个向量维度: {len(batch_embeddings[0])}")
        logger.info("")
        
        # 测试相似度
        if len(batch_embeddings) >= 2:
            logger.info("8. 测试相似度计算...")
            similarity = embedding_service.calculate_similarity(batch_embeddings[0], batch_embeddings[1])
            logger.info(f"   - 文本1: {batch_texts[0]}")
            logger.info(f"   - 文本2: {batch_texts[1]}")
            logger.info(f"   - 相似度: {similarity:.6f}")
            logger.info("")
        
        logger.info("✅ 测试成功完成！")
        return embedding
        
    except EmbeddingError as e:
        logger.error(f"❌ 嵌入错误: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        raise


async def test_async_embedding():
    """
    测试异步嵌入
    """
    logger.info("\n===== 测试异步Embedding API调用 =====\n")
    
    try:
        config_manager = ConfigManager()
        embedding_service = EmbeddingService(config_manager)
        
        test_text = "异步测试文本"
        logger.info(f"测试文本: {test_text}")
        
        embedding = await embedding_service.aembed_text(test_text)
        logger.info(f"异步嵌入结果: {embedding}")
        logger.info(f"向量维度: {len(embedding)}")
        
        logger.info("✅ 异步测试成功完成！")
        return embedding
        
    except Exception as e:
        logger.error(f"❌ 异步测试失败: {e}")
        raise


async def main():
    """
    主函数
    """
    # 运行同步测试
    embedding = test_real_embedding_api()
    
    # 运行异步测试
    await test_async_embedding()
    
    logger.info("\n🎉 所有测试都已成功完成！")


if __name__ == "__main__":
    # 运行主函数
    asyncio.run(main())
