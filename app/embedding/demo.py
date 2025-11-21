"""
Embedding 服务演示脚本

此脚本演示如何使用 EmbeddingService 进行文本嵌入和相似度计算。
"""

import asyncio
from typing import List

from app.config.config_manager import ConfigManager
from app.embedding.embedding_service import EmbeddingService
from app.embedding.exceptions import EmbeddingError


def demo_embedding_service():
    """
    演示EmbeddingService的基本功能
    """
    print("===== Embedding 服务演示 =====\n")
    
    try:
        # 初始化配置管理器
        print("1. 初始化配置管理器...")
        config_manager = ConfigManager()
        
        # 初始化嵌入服务
        print("2. 初始化嵌入服务...")
        embedding_service = EmbeddingService(config_manager)
        
        # 获取服务统计信息
        stats = embedding_service.get_stats()
        print(f"3. 服务统计信息:")
        print(f"   - 使用模型: {stats['model']}")
        print(f"   - 缓存大小: {stats['cache_size']}/{stats['max_cache_size']}")
        print()
        
        # 单个文本嵌入示例
        print("4. 单个文本嵌入:")
        text = "金融知识图谱是一种用于表示金融领域实体及其关系的数据结构。"
        embedding = embedding_service.embed_text(text)
        print(f"   - 文本: {text}")
        print(f"   - 嵌入向量维度: {len(embedding)}")
        print(f"   - 嵌入向量前5个元素: {embedding[:5]}")
        print()
        
        # 批量文本嵌入示例
        print("5. 批量文本嵌入:")
        texts = [
            "人工智能在金融领域的应用越来越广泛。",
            "风险管理是金融机构的核心业务之一。",
            "知识图谱可以帮助分析复杂的金融关系网络。"
        ]
        
        embeddings = embedding_service.embed_batch(texts)
        print(f"   - 文本数量: {len(texts)}")
        print(f"   - 嵌入向量数量: {len(embeddings)}")
        for i, (text, embedding) in enumerate(zip(texts, embeddings)):
            print(f"   - 文本{i+1}嵌入向量维度: {len(embedding)}")
        print()
        
        # 缓存功能演示
        print("6. 缓存功能演示:")
        print("   - 再次嵌入相同文本...")
        start_time = asyncio.get_event_loop().time()
        embedding_cached = embedding_service.embed_text(text)
        end_time = asyncio.get_event_loop().time()
        print(f"   - 缓存嵌入耗时: {end_time - start_time:.6f}秒")
        print(f"   - 两次嵌入结果是否相同: {embedding == embedding_cached}")
        print()
        
        # 相似度计算演示
        print("7. 文本相似度计算:")
        text1 = "股票市场波动很大"
        text2 = "股市价格不稳定"
        text3 = "今天天气很好"
        
        embed1 = embedding_service.embed_text(text1)
        embed2 = embedding_service.embed_text(text2)
        embed3 = embedding_service.embed_text(text3)
        
        sim1_2 = embedding_service.calculate_similarity(embed1, embed2)
        sim1_3 = embedding_service.calculate_similarity(embed1, embed3)
        
        print(f"   - 文本1: {text1}")
        print(f"   - 文本2: {text2}")
        print(f"   - 文本3: {text3}")
        print(f"   - 文本1与文本2相似度: {sim1_2:.4f}")
        print(f"   - 文本1与文本3相似度: {sim1_3:.4f}")
        print()
        
        # 清空缓存演示
        print("8. 清空缓存:")
        embedding_service.clear_cache()
        new_stats = embedding_service.get_stats()
        print(f"   - 清空后缓存大小: {new_stats['cache_size']}")
        print()
        
        print("演示完成！")
        
    except EmbeddingError as e:
        print(f"嵌入错误: {e}")
    except Exception as e:
        print(f"发生错误: {e}")


async def demo_async_embedding():
    """
    演示异步嵌入功能
    """
    print("\n===== 异步嵌入功能演示 =====\n")
    
    try:
        # 初始化配置管理器和嵌入服务
        config_manager = ConfigManager()
        embedding_service = EmbeddingService(config_manager)
        
        # 异步单个文本嵌入
        print("1. 异步单个文本嵌入:")
        text = "异步嵌入演示文本"
        embedding = await embedding_service.aembed_text(text)
        print(f"   - 文本: {text}")
        print(f"   - 嵌入向量维度: {len(embedding)}")
        print()
        
        # 异步批量文本嵌入
        print("2. 异步批量文本嵌入:")
        texts = ["异步文本1", "异步文本2", "异步文本3"]
        embeddings = await embedding_service.aembed_batch(texts)
        print(f"   - 文本数量: {len(texts)}")
        print(f"   - 嵌入向量数量: {len(embeddings)}")
        print()
        
        print("异步演示完成！")
        
    except EmbeddingError as e:
        print(f"嵌入错误: {e}")
    except Exception as e:
        print(f"发生错误: {e}")


async def main():
    """
    主函数
    """
    # 运行同步演示
    demo_embedding_service()
    
    # 运行异步演示
    await demo_async_embedding()


if __name__ == "__main__":
    # 运行主函数
    asyncio.run(main())
