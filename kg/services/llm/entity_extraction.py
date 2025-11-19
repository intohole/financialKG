"""
基于LangChain的实体抽取服务
使用大模型从新闻文本中抽取实体
"""

from typing import Any, Dict, List, Optional

from .langchain_base_service import LangChainBaseService


class EntityExtractionService(LangChainBaseService):
    """实体抽取服务类"""

    def __init__(self, config=None):
        """初始化实体抽取服务"""
        super().__init__()
        self.llm_config = config or self.llm_config
        self.system_prompt = """
你是一个专业的实体抽取专家，专门从新闻文本中抽取实体信息。

请从给定的新闻文本中抽取以下类型的实体：
1. 人物 (Person): 人名、职位等
2. 组织 (Organization): 公司、机构、政府部门等
3. 地点 (Location): 国家、城市、地区、具体地址等
4. 产品 (Product): 产品名称、品牌等
5. 事件 (Event): 会议、活动、事件等
6. 时间 (Time): 日期、时间段等
7. 数值 (Number): 数量、金额、比例等

对于每个实体，请提供以下信息：
- name: 实体名称
- type: 实体类型
- description: 实体描述（可选）
- confidence: 置信度（0-1之间的浮点数）

请以JSON格式返回结果，包含一个"entities"数组，数组中每个元素是一个实体对象。
"""

        self.human_prompt = """
请从以下新闻文本中抽取实体：

{text}

请确保：
1. 抽取的实体准确且完整
2. 实体类型分类正确
3. 置信度评估合理
4. 返回有效的JSON格式
"""

    async def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        从文本中抽取实体

        Args:
            text: 新闻文本

        Returns:
            包含实体列表的字典
        """
        inputs = {"text": text}
        return await self.extract_structured_data(
            self.system_prompt, self.human_prompt, inputs
        )

    async def extract_entities_by_type(
        self, text: str, entity_types: List[str]
    ) -> Dict[str, Any]:
        """
        按指定类型抽取实体

        Args:
            text: 新闻文本
            entity_types: 要抽取的实体类型列表

        Returns:
            包含指定类型实体列表的字典
        """
        type_specific_prompt = f"""
你是一个专业的实体抽取专家，专门从新闻文本中抽取指定类型的实体。

请从给定的新闻文本中只抽取以下类型的实体：
{', '.join(entity_types)}

对于每个实体，请提供以下信息：
- name: 实体名称
- type: 实体类型
- description: 实体描述（可选）
- confidence: 置信度（0-1之间的浮点数）

请以JSON格式返回结果，包含一个"entities"数组，数组中每个元素是一个实体对象。
"""

        human_prompt = f"""
请从以下新闻文本中只抽取{', '.join(entity_types)}类型的实体：

{text}

请确保：
1. 只抽取指定类型的实体
2. 抽取的实体准确且完整
3. 实体类型分类正确
4. 置信度评估合理
5. 返回有效的JSON格式
"""

        inputs = {"text": text}
        return await self.extract_structured_data(
            type_specific_prompt, human_prompt, inputs
        )

    async def extract_entities_with_context(
        self, text: str, context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        带上下文的实体抽取

        Args:
            text: 新闻文本
            context: 上下文信息（可选）

        Returns:
            包含实体列表的字典
        """
        context_prompt = self.system_prompt

        if context:
            context_prompt += f"\n\n上下文信息：{context}"

        human_prompt = self.human_prompt

        if context:
            human_prompt = f"""
请结合以下上下文信息，从新闻文本中抽取实体：

上下文信息：
{context}

新闻文本：
{text}

请确保：
1. 结合上下文信息准确抽取实体
2. 抽取的实体准确且完整
3. 实体类型分类正确
4. 置信度评估合理
5. 返回有效的JSON格式
"""

        inputs = {"text": text}
        return await self.extract_structured_data(context_prompt, human_prompt, inputs)
