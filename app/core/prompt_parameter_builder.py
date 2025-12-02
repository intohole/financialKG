"""
提示词参数构建器接口和默认实现

提供可扩展的参数构建机制，将提示词参数构建逻辑从ContentProcessor中解耦
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

from app.utils.logging_utils import get_logger

logger = get_logger(__name__)


class ParameterBuilderLogger:
    """参数构建器日志工具 - 用于详细记录参数构建过程"""
    
    @staticmethod
    def log_parameter_building(
        prompt_key: str,
        text_length: int,
        entity_types: Optional[str],
        relation_types: Optional[str],
        final_params: Dict[str, Any]
    ) -> None:
        """记录参数构建的完整过程"""
        logger.info("=" * 60)
        logger.info(f"参数构建详情 - prompt_key: {prompt_key}")
        logger.info(f"文本长度: {text_length}")

        # 记录实体类型决策过程
        if entity_types is not None:
            logger.info(f"✓ 使用用户指定的实体类型: {entity_types}")

        # 记录关系类型决策过程
        if relation_types is not None:
            logger.info(f"✓ 使用用户指定的关系类型: {relation_types}")

        # 记录最终参数
        logger.info(f"最终实体类型: {final_params.get('entity_types', 'N/A')}")
        logger.info(f"最终关系类型: {final_params.get('relation_types', 'N/A')}")
        logger.info("=" * 60)


class PromptParameterBuilder(ABC):
    """提示词参数构建器抽象基类"""
    
    @abstractmethod
    def build_parameters(self, 
                        text: str,
                        prompt_key: str,
                        **kwargs) -> Dict[str, Any]:
        """
        构建提示词参数
        
        Args:
            text: 输入文本
            prompt_key: 提示词键名
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: 构建好的参数字典
        """
        pass
    
    @abstractmethod
    def supports_prompt_key(self, prompt_key: str) -> bool:
        """
        检查是否支持指定的提示词键名
        
        Args:
            prompt_key: 提示词键名
            
        Returns:
            bool: 是否支持
        """
        pass


class DefaultParameterBuilder(PromptParameterBuilder):
    """默认参数构建器 - 处理基础参数构建"""
    
    def build_parameters(self, 
                        text: str,
                        prompt_key: str,
                        **kwargs) -> Dict[str, Any]:
        """构建基础参数 - 只包含文本"""
        return {'text': text}
    
    def supports_prompt_key(self, prompt_key: str) -> bool:
        """支持所有提示词键名作为默认回退"""
        return True


class ClassificationParameterBuilder(PromptParameterBuilder):
    """分类任务参数构建器"""
    
    def build_parameters(self, 
                        text: str,
                        prompt_key: str,
                        categories: Optional[List[str]] = None,
                        categories_prompt:str = None,
                        category_config: Optional[Dict[str, Dict]] = None,
                        **kwargs) -> Dict[str, Any]:
        """构建分类任务参数"""
        # 基础内容分类只需要文本参数，类别定义在prompt模板中
        params = {'text': text}
        
        # 只有增强版分类才需要额外的类别参数
            # 处理自定义类别 - categories优先于category_config
        if categories_prompt:
            params['categories'] = categories_prompt
        elif categories:
            params['categories'] = ", ".join(categories)
        elif category_config:
                # 使用配置中的类别信息，包含名称和描述
            category_info_parts = []
            for category_key, category_data in category_config.items():
                name = category_data.get('name', category_key)
                description = category_data.get('description', '')
                category_info_parts.append(f"{category_key}({name}): {description}")
                params['categories'] = "; ".join(category_info_parts)
        else:
            raise ValueError("No categories defined")
        return params
    
    def supports_prompt_key(self, prompt_key: str) -> bool:
        """支持分类相关提示词"""
        return prompt_key in ['content_classification', 'content_classification_enhanced']


class EntityRelationParameterBuilder(PromptParameterBuilder):
    """实体关系提取参数构建器 - 统一版本"""
    


    def build_parameters(self, 
                        text: str,
                        prompt_key: str,
                        entity_types: Optional[str] = None,
                        relation_types: Optional[str] = None,
                        **kwargs) -> Dict[str, Any]:
        """构建实体关系提取参数 - 确保动态性和可追踪性"""
        params = {'text': text}
        

        # 处理实体类型 - 严格的动态参数传递
        if entity_types is not None:
            # 用户明确指定了实体类型（包括空列表）
            params['entity_types'] = entity_types
            logger.debug(f"使用用户指定的实体类型: {entity_types}")
        else:
            raise ValueError("No entity types defined")
        
        # 处理关系类型 - 严格的动态参数传递
        if relation_types is not None:
            params['relation_types'] = relation_types
            logger.debug(f"使用用户指定的关系类型: {relation_types}")
        else:
            raise ValueError("No relation types defined")
        
        # 添加调试信息，便于问题排查
        logger.info(f"实体关系提取参数构建完成 - prompt_key: {prompt_key}, "
                   f"entity_types: {params['entity_types']}, "
                   f"relation_types: {params['relation_types']}")
        
        # 使用详细的日志工具记录参数构建过程
        ParameterBuilderLogger.log_parameter_building(
            prompt_key=prompt_key,
            text_length=len(text),
            entity_types=entity_types,
            relation_types=relation_types,
            final_params=params
        )
        
        return params
    
    def supports_prompt_key(self, prompt_key: str) -> bool:
        """支持实体关系提取相关提示词 - 统一为单一prompt"""
        supported_keys = [
            'entity_relation_extraction_unified',  # 新的统一版本
            'entity_relation_extraction',           # 兼容旧版本
            'entity_relation_extraction_enhanced', # 兼容旧版本
            'knowledge_graph_extraction'            # 兼容旧版本
        ]
        return prompt_key in supported_keys
    
    def get_supported_prompt_keys(self) -> List[str]:
        """返回支持的提示词键名列表，便于调试和文档"""
        return [
            'entity_relation_extraction_unified',
            'entity_relation_extraction',
            'entity_relation_extraction_enhanced',
            'knowledge_graph_extraction'
        ]


class CompositeParameterBuilder(PromptParameterBuilder):
    """复合参数构建器 - 组合多个构建器"""
    
    def __init__(self, builders: Optional[List[PromptParameterBuilder]] = None):
        """
        初始化复合构建器
        
        Args:
            builders: 构建器列表，按优先级排序
        """
        self.builders = builders or [
            ClassificationParameterBuilder(),
            EntityRelationParameterBuilder(),
            DefaultParameterBuilder()  # 默认构建器放在最后作为回退
        ]
    
    def build_parameters(self, 
                        text: str,
                        prompt_key: str,
                        **kwargs) -> Dict[str, Any]:
        """使用合适的构建器构建参数"""
        for builder in self.builders:
            if builder.supports_prompt_key(prompt_key):
                logger.debug(f"使用构建器 {builder.__class__.__name__} 处理提示词 {prompt_key}")
                return builder.build_parameters(text, prompt_key, **kwargs)
        
        # 不应该到达这里，因为DefaultParameterBuilder支持所有提示词
        logger.warning(f"没有找到支持提示词 {prompt_key} 的构建器，使用空参数")
        return {'text': text}
    
    def supports_prompt_key(self, prompt_key: str) -> bool:
        """只要有一个构建器支持就返回True"""
        return any(builder.supports_prompt_key(prompt_key) for builder in self.builders)
    
    def add_builder(self, builder: PromptParameterBuilder, index: Optional[int] = None):
        """
        添加新的构建器
        
        Args:
            builder: 要添加的构建器
            index: 插入位置，None表示添加到末尾
        """
        if index is None:
            # 添加到倒数第二个位置，保持DefaultParameterBuilder在最后
            self.builders.insert(-1, builder)
        else:
            self.builders.insert(index, builder)
    
    def remove_builder(self, builder_type: type):
        """
        移除指定类型的构建器
        
        Args:
            builder_type: 要移除的构建器类型
        """
        self.builders = [b for b in self.builders if not isinstance(b, builder_type)]