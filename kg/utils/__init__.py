"""
工具函数模块

提供系统各组件共享的通用功能和辅助函数
"""

import logging
from functools import wraps
from typing import Any, Callable, Optional

from sqlalchemy.exc import SQLAlchemyError

# 导入数据库相关工具
from .db_utils import (handle_db_errors, handle_db_errors_with_reraise,
                       jsonify_properties)
# 导入嵌入向量处理工具
from .embedding_utils import (aggregate_embeddings, batch_normalize_embeddings,
                              calculate_cosine_similarity, normalize_embedding,
                              validate_embedding)
# 导入实体关系处理工具
from .entity_relation_utils import (create_id_mapping,
                                    deduplicate_entities_by_name,
                                    deduplicate_relations,
                                    enrich_entity_with_relation_info,
                                    find_entity_by_id, find_entity_duplicates,
                                    group_entities_by_type,
                                    merge_entity_duplicates, validate_entity,
                                    validate_relation)
# 导入服务管理工具
from .service_utils import (ServiceRegistry, create_service_factory,
                            get_service, global_service_registry,
                            register_service, retry_on_failure,
                            service_lifecycle, validate_service_config)
# 导入文本处理工具
from .text_processing_utils import (chunk_text, clean_text,
                                    extract_keywords_from_text, normalize_text,
                                    split_text_into_chunks, truncate_text,
                                    validate_text_input)

# 配置日志
logger = logging.getLogger(__name__)


def handle_errors(
    error_types: tuple = (Exception,),
    default_return: Any = None,
    log_error: bool = True,
    log_message: Optional[str] = None,
):
    """
    通用异常处理装饰器

    Args:
        error_types: 要捕获的异常类型元组
        default_return: 发生异常时的默认返回值
        log_error: 是否记录错误日志
        log_message: 自定义错误日志消息模板，可以使用{func_name}和{error}占位符

    Returns:
        装饰器函数
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except error_types as e:
                if log_error:
                    if log_message:
                        message = log_message.format(func_name=func.__name__, error=e)
                        logger.error(message)
                    else:
                        # 默认日志消息
                        context_parts = []
                        context_parts.append(f"函数: {func.__name__}")

                        # 添加有意义的参数
                        if args:
                            for i, arg in enumerate(args[1:], 1):
                                if isinstance(arg, (str, int, float)):
                                    context_parts.append(f"参数{i}: {arg}")

                        # 添加关键字参数
                        for key, value in kwargs.items():
                            if isinstance(value, (str, int, float)):
                                context_parts.append(f"{key}: {value}")

                        context = ", ".join(context_parts)
                        logger.error(f"操作失败, {context}, 错误: {e}")
                return default_return

        return wrapper

    return decorator


__all__ = [
    # 通用工具
    "handle_errors",
    # 数据库工具
    "handle_db_errors",
    "handle_db_errors_with_reraise",
    "jsonify_properties",
    # embedding_utils
    "calculate_cosine_similarity",
    "validate_embedding",
    "normalize_embedding",
    "aggregate_embeddings",
    "batch_normalize_embeddings",
    # entity_relation_utils
    "validate_entity",
    "validate_relation",
    "group_entities_by_type",
    "find_entity_by_id",
    "deduplicate_entities_by_name",
    "deduplicate_relations",
    "find_entity_duplicates",
    "merge_entity_duplicates",
    "enrich_entity_with_relation_info",
    "create_id_mapping",
    # text_processing_utils
    "clean_text",
    "split_text_into_chunks",
    "extract_keywords_from_text",
    "normalize_text",
    "truncate_text",
    "validate_text_input",
    "chunk_text",
    # service_utils
    "ServiceRegistry",
    "global_service_registry",
    "get_service",
    "register_service",
    "create_service_factory",
    "retry_on_failure",
    "service_lifecycle",
    "validate_service_config",
]
