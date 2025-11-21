"""
项目统一日志工具使用示例

本示例展示了如何使用项目统一的日志工具进行各种日志记录
"""

import asyncio
import time
from app.config.config_manager import ConfigManager
from app.utils.logging_utils import (
    initialize_logging,
    get_logger,
    performance_logger,
    performance_context,
    set_request_id,
    clear_request_id,
    log_error_with_details,
    log_database_operation,
    log_llm_operation,
    log_vector_operation
)


# 示例1: 基本日志记录
def example_basic_logging():
    """基本日志记录示例"""
    logger = get_logger(__name__)
    
    # 基本信息记录
    logger.info("应用启动成功")
    logger.debug("调试信息")
    logger.warning("警告信息")
    logger.error("错误信息")
    
    # 带上下文的日志
    logger.log_with_context(
        logging.INFO,
        "用户登录成功",
        context={"user_id": "12345", "ip": "192.168.1.1"}
    )


# 示例2: 异常日志记录
def example_error_logging():
    """异常日志记录示例"""
    logger = get_logger(__name__)
    
    try:
        # 模拟一个异常
        result = 10 / 0
    except Exception as e:
        # 记录详细的异常信息
        logger.log_error_with_details(
            e,
            "计算失败",
            context={"operation": "division", "operands": [10, 0]}
        )
        
        # 或者使用便捷函数
        log_error_with_details(e, "计算失败")


# 示例3: 性能监控
def example_performance_logging():
    """性能监控示例"""
    
    # 使用装饰器进行性能监控
    @performance_logger("数据库查询")
    def query_database():
        time.sleep(0.1)  # 模拟数据库查询
        return {"data": "result"}
    
    # 使用上下文管理器进行性能监控
    def process_data():
        logger = get_logger(__name__)
        
        with performance_context("数据处理"):
            time.sleep(0.05)  # 模拟数据处理
            logger.info("数据处理完成")
    
    # 手动性能监控
    def manual_performance():
        logger = get_logger(__name__)
        
        start_time = time.time()
        time.sleep(0.2)  # 模拟操作
        duration_ms = (time.time() - start_time) * 1000
        
        logger.log_performance("手动监控", duration_ms, success=True)
    
    query_database()
    process_data()
    manual_performance()


# 示例4: 数据库操作日志
def example_database_logging():
    """数据库操作日志示例"""
    logger = get_logger(__name__)
    
    # 记录数据库查询
    logger.log_database_operation(
        operation="SELECT",
        table="users",
        duration_ms=45.2,
        rows_affected=10,
        success=True,
        context={"query": "SELECT * FROM users WHERE age > 18"}
    )
    
    # 使用便捷函数
    log_database_operation(
        operation="INSERT",
        table="orders",
        duration_ms=23.5,
        rows_affected=1,
        success=True
    )


# 示例5: 大模型操作日志
def example_llm_logging():
    """大模型操作日志示例"""
    logger = get_logger(__name__)
    
    # 记录LLM请求
    logger.log_llm_operation(
        model="glm-4-flash",
        operation="文本生成",
        tokens_used={"prompt": 100, "completion": 50},
        cost=0.0012,
        duration_ms=1250.5,
        success=True,
        context={"temperature": 0.7, "max_tokens": 2048}
    )
    
    # 使用便捷函数
    log_llm_operation(
        model="embedding-3",
        operation="文本嵌入",
        tokens_used={"total": 200},
        cost=0.0008,
        duration_ms=850.3,
        success=True
    )


# 示例6: 向量操作日志
def example_vector_logging():
    """向量操作日志示例"""
    logger = get_logger(__name__)
    
    # 记录向量搜索
    logger.log_vector_operation(
        operation="search",
        collection="financial_docs",
        dimension=1536,
        duration_ms=234.7,
        success=True,
        context={"top_k": 10, "metric": "cosine"}
    )
    
    # 使用便捷函数
    log_vector_operation(
        operation="insert",
        collection="news_embeddings",
        dimension=1536,
        duration_ms=156.3,
        success=True
    )


# 示例7: 请求追踪
def example_request_tracking():
    """请求追踪示例"""
    logger = get_logger(__name__)
    
    # 设置请求ID
    set_request_id("req-123456")
    
    try:
        logger.info("开始处理请求")
        
        # 模拟请求处理
        time.sleep(0.1)
        
        logger.info("请求处理完成")
        
    finally:
        # 清除请求ID
        clear_request_id()


# 示例8: 完整应用初始化
def example_full_application():
    """完整应用初始化示例"""
    
    # 1. 初始化配置管理器
    config_manager = ConfigManager()
    
    # 2. 初始化日志系统
    initialize_logging(config_manager)
    
    # 3. 获取日志器
    logger = get_logger("main")
    
    logger.info("应用启动中...")
    
    # 获取配置
    api_config = config_manager.get_api_config()
    db_config = config_manager.get_database_config()
    
    logger.info(f"API服务配置: {api_config.host}:{api_config.port}")
    logger.info(f"数据库配置: {db_config.url}")
    
    # 模拟应用启动过程
    with performance_context("应用启动"):
        time.sleep(0.5)  # 模拟启动时间
        logger.info("应用启动完成")


# 异步示例
async def example_async_logging():
    """异步日志记录示例"""
    logger = get_logger(__name__)
    
    logger.info("开始异步操作")
    
    # 模拟异步操作
    await asyncio.sleep(0.1)
    
    logger.info("异步操作完成")


if __name__ == "__main__":
    import logging
    
    print("=== 项目统一日志工具使用示例 ===\n")
    
    # 基本日志示例
    print("1. 基本日志记录:")
    example_basic_logging()
    print()
    
    # 异常日志示例
    print("2. 异常日志记录:")
    example_error_logging()
    print()
    
    # 性能监控示例
    print("3. 性能监控:")
    example_performance_logging()
    print()
    
    # 数据库操作日志示例
    print("4. 数据库操作日志:")
    example_database_logging()
    print()
    
    # 大模型操作日志示例
    print("5. 大模型操作日志:")
    example_llm_logging()
    print()
    
    # 向量操作日志示例
    print("6. 向量操作日志:")
    example_vector_logging()
    print()
    
    # 请求追踪示例
    print("7. 请求追踪:")
    example_request_tracking()
    print()
    
    # 完整应用示例
    print("8. 完整应用初始化:")
    try:
        example_full_application()
    except Exception as e:
        print(f"应用初始化失败: {e}")
    print()
    
    # 异步示例
    print("9. 异步日志记录:")
    asyncio.run(example_async_logging())
    
    print("\n=== 示例完成 ===")