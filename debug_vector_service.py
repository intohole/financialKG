#!/usr/bin/env python3
"""
向量服务调试脚本 - 检查ChromaDB连接和基本功能
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from app.config.config_manager import ConfigManager
from app.vector.chroma_vector_search import ChromaVectorSearch
from app.embedding.embedding_service import EmbeddingService
from app.vector.exceptions import VectorSearchError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_vector_service():
    """测试向量服务"""
    try:
        logger.info("=== 开始测试向量服务 ===")
        
        # 加载配置
        config_manager = ConfigManager()
        
        # 初始化嵌入服务
        embedding_service = EmbeddingService(config_manager)
        logger.info("✓ 嵌入服务初始化成功")
        
        # 测试嵌入生成
        test_text = "这是一段测试文本"
        embedding = await embedding_service.embed_text(test_text)
        logger.info(f"✓ 嵌入生成成功，维度: {len(embedding)}")
        
        # 初始化向量存储
        vector_store = ChromaVectorSearch(config)
        logger.info("✓ 向量存储初始化成功")
        
        # 测试创建索引
        index_name = "debug_test"
        await vector_store.create_index(index_name, dimension=len(embedding))
        logger.info(f"✓ 索引创建成功: {index_name}")
        
        # 测试添加向量
        test_id = "test_001"
        metadata = {"content_type": "test", "content_id": "123"}
        await vector_store.add_vector(index_name, embedding, test_id, metadata, test_text)
        logger.info("✓ 向量添加成功")
        
        # 测试搜索
        search_results = await vector_store.search_vectors(index_name, embedding, top_k=5)
        logger.info(f"✓ 向量搜索成功，返回结果数量: {len(search_results)}")
        
        if search_results:
            logger.info(f"  第一个结果: ID={search_results[0]['id']}, Score={search_results[0]['score']}")
            if 'metadata' in search_results[0]:
                logger.info(f"  元数据: {search_results[0]['metadata']}")
        
        # 测试获取索引信息
        index_info = await vector_store.get_index_info(index_name)
        logger.info(f"✓ 索引信息获取成功: {index_info}")
        
        # 清理测试数据
        await vector_store.delete_index(index_name)
        logger.info("✓ 测试索引清理成功")
        
        logger.info("=== 向量服务测试全部通过 ===")
        return True
        
    except Exception as e:
        logger.error(f"✗ 向量服务测试失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_vector_service())
    sys.exit(0 if success else 1)