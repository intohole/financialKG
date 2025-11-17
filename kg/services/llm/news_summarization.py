"""
基于LangChain的新闻摘要服务
使用大模型生成新闻摘要
"""
from typing import Dict, Any, List, Optional
from .langchain_base_service import LangChainBaseService


class NewsSummarizationService(LangChainBaseService):
    """新闻摘要服务类"""
    
    def __init__(self, config=None):
        """初始化新闻摘要服务"""
        super().__init__()
        self.llm_config = config or self.llm_config
        self.system_prompt = """
你是一个专业的新闻摘要专家，专门为新闻文章生成简洁、准确、全面的摘要。

请根据给定的新闻文本，生成包含以下内容的摘要：
1. 主要事件：新闻的核心事件或主题
2. 关键信息：涉及的人物、组织、地点、时间等关键信息
3. 事件背景：事件的背景和上下文
4. 影响和意义：事件可能带来的影响和意义
5. 未来展望：可能的发展趋势或后续影响

摘要应该：
- 简洁明了，避免冗余信息
- 客观准确，不添加主观判断
- 结构清晰，逻辑连贯
- 保留关键细节和重要信息

请以JSON格式返回结果，包含以下字段：
- title: 摘要标题
- main_event: 主要事件描述
- key_info: 关键信息列表
- background: 事件背景
- impact: 影响和意义
- outlook: 未来展望
- summary: 整体摘要（3-5句话）
"""
        
        self.human_prompt = """
请为以下新闻文章生成摘要：

{text}

请确保：
1. 摘要内容准确反映原文主旨
2. 包含所有关键信息点
3. 语言简洁明了，结构清晰
4. 返回有效的JSON格式
"""
    
    def generate_summary(self, text: str) -> Dict[str, Any]:
        """
        生成新闻摘要
        
        Args:
            text: 新闻文本
            
        Returns:
            包含摘要信息的字典
        """
        inputs = {"text": text}
        return self.extract_structured_data(
            self.system_prompt,
            self.human_prompt,
            inputs
        )
    
    def generate_short_summary(self, text: str, max_sentences: int = 3) -> Dict[str, Any]:
        """
        生成简短摘要
        
        Args:
            text: 新闻文本
            max_sentences: 最大句子数
            
        Returns:
            包含简短摘要的字典
        """
        short_prompt = f"""
你是一个专业的新闻摘要专家，专门为新闻文章生成简洁的摘要。

请为给定的新闻文本生成一个不超过{max_sentences}句话的简短摘要，突出新闻的核心内容和关键信息。

请以JSON格式返回结果，包含以下字段：
- title: 摘要标题
- summary: 简短摘要（不超过{max_sentences}句话）
"""
        
        human_prompt = f"""
请为以下新闻文章生成一个不超过{max_sentences}句话的简短摘要：

{{text}}

请确保：
1. 摘要内容准确反映原文主旨
2. 突出核心内容和关键信息
3. 语言简洁明了
4. 不超过{max_sentences}句话
5. 返回有效的JSON格式
"""
        
        inputs = {"text": text}
        return self.extract_structured_data(
            short_prompt,
            human_prompt,
            inputs
        )
    
    def generate_topic_summary(self, text: str, topic: str) -> Dict[str, Any]:
        """
        生成特定主题的摘要
        
        Args:
            text: 新闻文本
            topic: 特定主题
            
        Returns:
            包含主题摘要的字典
        """
        topic_prompt = f"""
你是一个专业的新闻摘要专家，专门从新闻文章中提取特定主题的信息并生成摘要。

请从给定的新闻文本中提取与"{topic}"相关的信息，并生成一个专门针对该主题的摘要。

摘要应该：
- 聚焦于"{topic}"相关的内容
- 包含该主题的关键信息和细节
- 提供与该主题相关的背景和影响
- 结构清晰，逻辑连贯

请以JSON格式返回结果，包含以下字段：
- topic: 摘要主题
- title: 摘要标题
- key_points: 关键信息点列表
- background: 主题相关背景
- impact: 主题相关影响
- summary: 主题摘要
"""
        
        human_prompt = f"""
请从以下新闻文章中提取与"{topic}"相关的信息，并生成一个专门针对该主题的摘要：

新闻文本：
{{text}}

请确保：
1. 摘要内容聚焦于"{topic}"相关的内容
2. 包含该主题的关键信息和细节
3. 提供与该主题相关的背景和影响
4. 结构清晰，逻辑连贯
5. 返回有效的JSON格式
"""
        
        inputs = {"text": text}
        return self.extract_structured_data(
            topic_prompt,
            human_prompt,
            inputs
        )
    
    def generate_multi_view_summary(self, text: str, perspectives: List[str]) -> Dict[str, Any]:
        """
        生成多角度摘要
        
        Args:
            text: 新闻文本
            perspectives: 不同角度/视角列表
            
        Returns:
            包含多角度摘要的字典
        """
        perspective_list = "\n".join([f"- {p}" for p in perspectives])
        
        multi_view_prompt = f"""
你是一个专业的新闻摘要专家，能够从多个角度分析新闻文章并生成摘要。

请从以下多个角度分析给定的新闻文本，并为每个角度生成专门的摘要：
{perspective_list}

对于每个角度，请提供：
- 该角度的关键信息
- 该角度的背景和上下文
- 该角度的影响和意义

请以JSON格式返回结果，包含以下字段：
- title: 整体摘要标题
- overall_summary: 整体摘要
- perspectives: 各角度摘要列表，每个包含：
  - perspective: 角度名称
  - summary: 该角度的摘要
  - key_points: 关键信息点
"""
        
        human_prompt = f"""
请从以下多个角度分析新闻文章，并为每个角度生成专门的摘要：

分析角度：
{perspective_list}

新闻文本：
{{text}}

请确保：
1. 从每个指定角度进行分析
2. 每个角度的摘要准确反映该视角的内容
3. 提供整体摘要和各角度摘要
4. 结构清晰，逻辑连贯
5. 返回有效的JSON格式
"""
        
        inputs = {"text": text}
        return self.extract_structured_data(
            multi_view_prompt,
            human_prompt,
            inputs
        )