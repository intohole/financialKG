"""
基于LangChain的关系抽取服务
使用大模型从新闻文本中抽取实体间关系
"""
from typing import Dict, Any, List, Optional
from .langchain_base_service import LangChainBaseService


class RelationExtractionService(LangChainBaseService):
    """关系抽取服务类"""
    
    def __init__(self, config=None):
        """初始化关系抽取服务"""
        super().__init__()
        self.llm_config = config or self.llm_config
        self.system_prompt = """
你是一个专业的关系抽取专家，专门从新闻文本中抽取实体之间的关系。

请从给定的新闻文本中抽取实体之间的关系，包括：
1. 人物关系：如"是...的CEO"、"与...合作"、"担任...职位"等
2. 组织关系：如"是...的子公司"、"与...合作"、"投资..."等
3. 地点关系：如"位于..."、"在...举办"等
4. 产品关系：如"发布..."、"使用..."等
5. 事件关系：如"参与..."、"导致..."等
6. 时间关系：如"在...发生"、"持续..."等
7. 数值关系：如"增长..."、"占比..."等

对于每个关系，请提供以下信息：
- source_entity: 源实体名称
- target_entity: 目标实体名称
- relation_type: 关系类型
- relation_description: 关系描述
- confidence: 置信度（0-1之间的浮点数）

请以JSON格式返回结果，包含一个"relations"数组，数组中每个元素是一个关系对象。
"""
        
        self.human_prompt = """
请从以下新闻文本中抽取实体之间的关系：

{text}

请确保：
1. 抽取的关系准确且完整
2. 源实体和目标实体正确
3. 关系类型分类合理
4. 置信度评估合理
5. 返回有效的JSON格式
"""
    
    def extract_relations(self, text: str) -> Dict[str, Any]:
        """
        从文本中抽取关系
        
        Args:
            text: 新闻文本
            
        Returns:
            包含关系列表的字典
        """
        inputs = {"text": text}
        return self.extract_structured_data(
            self.system_prompt,
            self.human_prompt,
            inputs
        )
    
    def extract_relations_with_entities(self, text: str, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        基于给定实体列表抽取关系
        
        Args:
            text: 新闻文本
            entities: 实体列表，每个实体包含name和type
            
        Returns:
            包含关系列表的字典
        """
        entity_list = "\n".join([f"- {e['name']} ({e.get('type', 'Unknown')})" for e in entities])
        
        entity_specific_prompt = f"""
你是一个专业的关系抽取专家，专门从新闻文本中抽取给定实体之间的关系。

请从给定的新闻文本中只抽取以下实体之间的关系：
{entity_list}

对于每个关系，请提供以下信息：
- source_entity: 源实体名称（必须来自上述实体列表）
- target_entity: 目标实体名称（必须来自上述实体列表）
- relation_type: 关系类型
- relation_description: 关系描述
- confidence: 置信度（0-1之间的浮点数）

请以JSON格式返回结果，包含一个"relations"数组，数组中每个元素是一个关系对象。
"""
        
        human_prompt = f"""
请从以下新闻文本中抽取给定实体之间的关系：

给定实体列表：
{entity_list}

新闻文本：
{{text}}

请确保：
1. 只抽取给定实体之间的关系
2. 源实体和目标实体必须来自给定实体列表
3. 抽取的关系准确且完整
4. 关系类型分类合理
5. 置信度评估合理
6. 返回有效的JSON格式
"""
        
        inputs = {"text": text}
        return self.extract_structured_data(
            entity_specific_prompt,
            human_prompt,
            inputs
        )
    
    def extract_relations_by_type(self, text: str, relation_types: List[str]) -> Dict[str, Any]:
        """
        按指定类型抽取关系
        
        Args:
            text: 新闻文本
            relation_types: 要抽取的关系类型列表
            
        Returns:
            包含指定类型关系列表的字典
        """
        type_specific_prompt = f"""
你是一个专业的关系抽取专家，专门从新闻文本中抽取指定类型的关系。

请从给定的新闻文本中只抽取以下类型的关系：
{', '.join(relation_types)}

对于每个关系，请提供以下信息：
- source_entity: 源实体名称
- target_entity: 目标实体名称
- relation_type: 关系类型（必须来自上述类型列表）
- relation_description: 关系描述
- confidence: 置信度（0-1之间的浮点数）

请以JSON格式返回结果，包含一个"relations"数组，数组中每个元素是一个关系对象。
"""
        
        human_prompt = f"""
请从以下新闻文本中只抽取{', '.join(relation_types)}类型的关系：

新闻文本：
{{text}}

请确保：
1. 只抽取指定类型的关系
2. 抽取的关系准确且完整
3. 源实体和目标实体正确
4. 关系类型必须来自指定类型列表
5. 置信度评估合理
6. 返回有效的JSON格式
"""
        
        inputs = {"text": text}
        return self.extract_structured_data(
            type_specific_prompt,
            human_prompt,
            inputs
        )
    
    def extract_relations_with_context(self, text: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        带上下文的关系抽取
        
        Args:
            text: 新闻文本
            context: 上下文信息（可选）
            
        Returns:
            包含关系列表的字典
        """
        context_prompt = self.system_prompt
        
        if context:
            context_prompt += f"\n\n上下文信息：{context}"
        
        human_prompt = self.human_prompt
        
        if context:
            human_prompt = f"""
请结合以下上下文信息，从新闻文本中抽取实体之间的关系：

上下文信息：
{context}

新闻文本：
{{text}}

请确保：
1. 结合上下文信息准确抽取关系
2. 抽取的关系准确且完整
3. 源实体和目标实体正确
4. 关系类型分类合理
5. 置信度评估合理
6. 返回有效的JSON格式
"""
        
        inputs = {"text": text}
        return self.extract_structured_data(
            context_prompt,
            human_prompt,
            inputs
        )