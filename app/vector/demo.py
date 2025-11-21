"""
向量搜索功能演示脚本
演示基于Chroma的向量搜索功能的使用方法
"""

import os
import sys
import logging
import numpy as np
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("vector_search_demo")

# 导入向量搜索模块
from app.vector import VectorSearchService, VectorSearchError


def generate_random_vectors(count: int, dimension: int) -> list:
    """
    生成随机向量
    
    Args:
        count: 向量数量
        dimension: 向量维度
        
    Returns:
        list: 向量列表
    """
    vectors = []
    for _ in range(count):
        # 生成随机向量
        vector = np.random.rand(dimension).tolist()
        # 归一化向量
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = (np.array(vector) / norm).tolist()
        vectors.append(vector)
    return vectors


def demo_vector_search_basic():
    """
    基本向量搜索功能演示
    """
    logger.info("===== 开始向量搜索基本功能演示 =====")
    
    try:
        # 1. 初始化向量搜索服务
        logger.info("1. 初始化向量搜索服务...")
        vector_service = VectorSearchService()
        logger.info("向量搜索服务初始化成功")
        
        # 获取向量搜索实例
        vector_search = vector_service.get_vector_search()
        
        # 2. 创建索引
        index_name = "demo_index"
        dimension = 1536
        logger.info(f"2. 创建索引: {index_name}, 维度: {dimension}")
        
        # 检查索引是否存在，如果存在先删除
        if vector_search.index_exists(index_name):
            logger.info(f"索引 {index_name} 已存在，尝试删除...")
            vector_search.delete_index(index_name)
            logger.info(f"索引 {index_name} 删除成功")
        
        # 创建新索引
        success = vector_search.create_index(index_name, dimension)
        if success:
            logger.info(f"索引 {index_name} 创建成功")
        else:
            logger.error(f"索引 {index_name} 创建失败")
            return
        
        # 3. 准备测试数据
        logger.info("3. 准备测试数据...")
        vector_count = 5
        vectors = generate_random_vectors(vector_count, dimension)
        ids = [f"doc_{i}" for i in range(vector_count)]
        
        # 添加元数据
        metadatas = [
            {"category": "finance", "source": "news", "timestamp": str(datetime.now())},
            {"category": "tech", "source": "article", "timestamp": str(datetime.now())},
            {"category": "health", "source": "research", "timestamp": str(datetime.now())},
            {"category": "finance", "source": "report", "timestamp": str(datetime.now())},
            {"category": "tech", "source": "blog", "timestamp": str(datetime.now())}
        ]
        
        # 4. 添加向量
        logger.info(f"4. 添加 {vector_count} 个向量到索引 {index_name}...")
        add_success = vector_search.add_vectors(index_name, vectors, ids, metadatas=metadatas)
        if add_success:
            logger.info("向量添加成功")
            # 检查向量数量
            count = vector_search.count_vectors(index_name)
            logger.info(f"索引中的向量数量: {count}")
        else:
            logger.error("向量添加失败")
            return
        
        # 5. 向量搜索
        logger.info("5. 执行向量搜索...")
        # 使用第一个向量作为查询向量
        query_vector = vectors[0]
        top_k = 3
        
        # 基本搜索
        results = vector_search.search_vectors(index_name, query_vector, top_k)
        logger.info(f"搜索结果 (Top {top_k}):")
        for i, result in enumerate(results):
            logger.info(f"  结果 {i+1}:")
            logger.info(f"    ID: {result.get('id')}")
            logger.info(f"    相似度: {result.get('score'):.6f}")
            logger.info(f"    元数据: {result.get('metadata')}")
        
        # 带过滤条件的搜索
        logger.info("\n带过滤条件的搜索 (category='finance'):")
        filter_condition = {"category": "finance"}
        filtered_results = vector_search.search_vectors(
            index_name, query_vector, top_k, where=filter_condition
        )
        
        if filtered_results:
            for i, result in enumerate(filtered_results):
                logger.info(f"  过滤结果 {i+1}:")
                logger.info(f"    ID: {result.get('id')}")
                logger.info(f"    相似度: {result.get('score'):.6f}")
                logger.info(f"    元数据: {result.get('metadata')}")
        else:
            logger.info("  没有符合过滤条件的结果")
        
        # 6. 获取向量
        logger.info("\n6. 获取指定ID的向量...")
        vector_info = vector_search.get_vector(index_name, "doc_0")
        if vector_info:
            logger.info(f"  ID: {vector_info.get('id')}")
            logger.info(f"  向量维度: {len(vector_info.get('vector', []))}")
            logger.info(f"  元数据: {vector_info.get('metadata')}")
        else:
            logger.error("  获取向量失败")
        
        # 7. 更新向量
        logger.info("\n7. 更新向量...")
        updated_vector = generate_random_vectors(1, dimension)[0]
        updated_metadata = {"category": "updated", "source": "demo", "updated_at": str(datetime.now())}
        
        update_success = vector_search.update_vector(
            index_name, "doc_1", updated_vector, metadata=updated_metadata
        )
        
        if update_success:
            logger.info("  向量更新成功")
            # 验证更新
            updated_info = vector_search.get_vector(index_name, "doc_1")
            logger.info(f"  更新后的元数据: {updated_info.get('metadata')}")
        else:
            logger.error("  向量更新失败")
        
        # 8. 删除向量
        logger.info("\n8. 删除向量...")
        delete_success = vector_search.delete_vector(index_name, "doc_2")
        
        if delete_success:
            logger.info("  向量删除成功")
            # 检查剩余向量数量
            remaining_count = vector_search.count_vectors(index_name)
            logger.info(f"  删除后向量数量: {remaining_count}")
        else:
            logger.error("  向量删除失败")
        
        # 9. 列出索引
        logger.info("\n9. 列出所有索引...")
        indices = vector_search.list_indices()
        logger.info(f"  索引列表: {indices}")
        
        # 10. 批量删除向量
        logger.info("\n10. 批量删除向量...")
        batch_delete_ids = ["doc_3", "doc_4"]
        batch_delete_success = vector_search.delete_vectors(index_name, batch_delete_ids)
        
        if batch_delete_success:
            logger.info(f"  批量删除 {len(batch_delete_ids)} 个向量成功")
            remaining_count = vector_search.count_vectors(index_name)
            logger.info(f"  批量删除后向量数量: {remaining_count}")
        else:
            logger.error("  批量删除向量失败")
        
        # 11. 删除索引（清理测试数据）
        logger.info("\n11. 清理测试数据，删除索引...")
        delete_index_success = vector_search.delete_index(index_name)
        if delete_index_success:
            logger.info(f"  索引 {index_name} 删除成功")
        else:
            logger.error(f"  索引 {index_name} 删除失败")
        
        # 12. 关闭服务
        logger.info("\n12. 关闭向量搜索服务...")
        vector_service.close_all()
        logger.info("向量搜索服务已关闭")
        
        logger.info("\n===== 向量搜索基本功能演示完成 =====")
        
    except VectorSearchError as e:
        logger.error(f"向量搜索错误: {str(e)}")
    except Exception as e:
        logger.error(f"演示过程中发生错误: {str(e)}", exc_info=True)


def demo_vector_service_context_manager():
    """
    演示向量搜索服务的上下文管理器功能
    """
    logger.info("\n===== 开始演示上下文管理器功能 =====")
    
    try:
        with VectorSearchService() as vector_service:
            logger.info("使用上下文管理器初始化向量搜索服务")
            vector_search = vector_service.get_vector_search()
            
            # 检查服务是否正常
            logger.info("检查向量搜索服务状态...")
            # 列出索引（即使为空也会返回）
            indices = vector_search.list_indices()
            logger.info(f"当前索引列表: {indices}")
        
        logger.info("上下文管理器退出，向量搜索服务已自动关闭")
        logger.info("===== 上下文管理器功能演示完成 =====")
        
    except Exception as e:
        logger.error(f"演示上下文管理器功能时发生错误: {str(e)}")


def demo_multiple_instances():
    """
    演示多实例管理功能
    """
    logger.info("\n===== 开始演示多实例管理功能 =====")
    
    try:
        vector_service = VectorSearchService()
        
        # 创建多个命名实例
        logger.info("创建多个命名实例...")
        instance1 = vector_service.get_vector_search("instance1")
        instance2 = vector_service.get_vector_search("instance2")
        
        # 列出所有实例
        instances = vector_service.list_instances()
        logger.info(f"当前管理的实例列表: {instances}")
        
        # 关闭特定实例
        logger.info("关闭instance1...")
        vector_service.close_instance("instance1")
        
        # 再次列出实例
        instances_after_close = vector_service.list_instances()
        logger.info(f"关闭后实例列表: {instances_after_close}")
        
        # 关闭所有实例
        vector_service.close_all()
        logger.info("所有实例已关闭")
        
        logger.info("===== 多实例管理功能演示完成 =====")
        
    except Exception as e:
        logger.error(f"演示多实例管理功能时发生错误: {str(e)}")


def main():
    """
    演示主函数
    """
    logger.info("开始向量搜索功能演示")
    
    # 确保有足够的权限和依赖
    try:
        # 导入chromadb检查依赖
        import chromadb
        logger.info(f"ChromaDB版本: {chromadb.__version__}")
        
        # 创建演示数据目录
        data_dir = "./data/chroma"
        os.makedirs(data_dir, exist_ok=True)
        logger.info(f"创建数据目录: {os.path.abspath(data_dir)}")
        
        # 运行各项演示
        demo_vector_search_basic()
        demo_vector_service_context_manager()
        demo_multiple_instances()
        
        logger.info("所有演示完成！")
        
    except ImportError:
        logger.error("错误: 未找到ChromaDB模块，请先安装: pip install chromadb")
        sys.exit(1)
    except Exception as e:
        logger.error(f"演示启动失败: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
