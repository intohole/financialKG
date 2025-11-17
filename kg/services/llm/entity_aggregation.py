"""
基于LangChain的实体聚合服务
对相似实体进行聚合处理
"""
from typing import Dict, Any, List, Optional, Tuple
from .langchain_base_service import LangChainBaseService


class EntityAggregationService(LangChainBaseService):
    """实体聚合服务类"""
    
    def __init__(self, config=None):
        """初始化实体聚合服务"""
        super().__init__()
        self.llm_config = config or self.llm_config
        self.system_prompt = """
你是一个专业的实体聚合专家，专门对相似实体进行识别、分析和聚合。

请分析给定的实体列表，识别相似的实体并将它们聚合在一起。聚合时考虑以下因素：
1. 实体名称的相似性（拼写、缩写、变体）
2. 实体类型的一致性
3. 实体属性的相似性
4. 上下文关联性
5. 语义相似性

对于每个聚合组，请：
1. 确定一个代表性实体名称
2. 列出聚合组中的所有实体变体
3. 提供聚合的理由和依据
4. 标注聚合的置信度
5. 保留实体的关键属性

请以JSON格式返回结果，包含以下字段：
- aggregated_entities: 聚合后的实体列表，每个包含：
  - representative_name: 代表性实体名称
  - variants: 实体变体列表
  - entity_type: 实体类型
  - confidence: 聚合置信度（0-1）
  - reasoning: 聚合理由
  - attributes: 合并后的属性
- unaggregated_entities: 未能聚合的实体列表
- statistics: 聚合统计信息
"""
        
        self.human_prompt = """
请对以下实体列表进行聚合分析：

{entities}

请确保：
1. 识别所有相似的实体并进行合理聚合
2. 每个聚合组有明确的代表性名称
3. 提供详细的聚合理由和置信度
4. 保留实体的关键属性和类型信息
5. 返回有效的JSON格式
"""
    
    def aggregate_entities(self, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        聚合相似实体
        
        Args:
            entities: 实体列表，每个实体包含name、type等属性
            
        Returns:
            包含聚合结果的字典
        """
        # 将实体列表格式化为字符串
        entities_str = "\n".join([
            f"- {i+1}. 名称: {entity.get('name', '未知')}, "
            f"类型: {entity.get('type', '未知')}, "
            f"属性: {entity.get('attributes', {})}"
            for i, entity in enumerate(entities)
        ])
        
        inputs = {"entities": entities_str}
        return self.extract_structured_data(
            self.system_prompt,
            self.human_prompt,
            inputs
        )
    
    def aggregate_entities_by_type(self, entities: List[Dict[str, Any]], entity_type: str) -> Dict[str, Any]:
        """
        按实体类型聚合相似实体
        
        Args:
            entities: 实体列表
            entity_type: 要聚合的实体类型
            
        Returns:
            包含聚合结果的字典
        """
        # 过滤出指定类型的实体
        filtered_entities = [e for e in entities if e.get('type') == entity_type]
        
        type_specific_prompt = f"""
你是一个专业的实体聚合专家，专门对{entity_type}类型的相似实体进行识别、分析和聚合。

请分析给定的{entity_type}实体列表，识别相似的实体并将它们聚合在一起。聚合时特别关注：
1. {entity_type}实体的命名规范和变体
2. {entity_type}实体的特有属性和特征
3. {entity_type}实体之间的关联性
4. {entity_type}实体的上下文信息

对于每个聚合组，请：
1. 确定一个标准的{entity_type}实体名称
2. 列出聚合组中的所有实体变体
3. 提供聚合的理由和依据
4. 标注聚合的置信度
5. 保留{entity_type}实体的关键属性

请以JSON格式返回结果，包含以下字段：
- entity_type: 实体类型
- aggregated_entities: 聚合后的实体列表，每个包含：
  - representative_name: 代表性实体名称
  - variants: 实体变体列表
  - confidence: 聚合置信度（0-1）
  - reasoning: 聚合理由
  - attributes: 合并后的属性
- unaggregated_entities: 未能聚合的实体列表
- statistics: 聚合统计信息
"""
        
        human_prompt = f"""
请对以下{entity_type}实体列表进行聚合分析：

{entities_str}

请确保：
1. 识别所有相似的{entity_type}实体并进行合理聚合
2. 每个聚合组有标准的{entity_type}实体名称
3. 提供详细的聚合理由和置信度
4. 保留{entity_type}实体的关键属性
5. 返回有效的JSON格式
"""
        
        # 将实体列表格式化为字符串
        entities_str = "\n".join([
            f"- {i+1}. 名称: {entity.get('name', '未知')}, "
            f"属性: {entity.get('attributes', {})}"
            for i, entity in enumerate(filtered_entities)
        ])
        
        inputs = {"entities": entities_str}
        return self.extract_structured_data(
            type_specific_prompt,
            human_prompt,
            inputs
        )
    
    def find_duplicate_entities(self, entities: List[Dict[str, Any]], similarity_threshold: float = 0.8) -> Dict[str, Any]:
        """
        查找重复或高度相似的实体
        
        Args:
            entities: 实体列表
            similarity_threshold: 相似度阈值
            
        Returns:
            包含重复实体的字典
        """
        duplicate_prompt = f"""
你是一个专业的实体重复检测专家，专门识别实体列表中的重复或高度相似的实体。

请分析给定的实体列表，识别重复或高度相似的实体（相似度阈值: {similarity_threshold}）。识别时考虑：
1. 实体名称的完全匹配或高度相似
2. 实体类型的匹配
3. 实体属性的高度重叠
4. 可能的缩写、别名或变体

对于每组重复实体，请：
1. 标记重复的实体
2. 确定保留的实体
3. 提供重复的依据和相似度
4. 建议如何合并这些实体

请以JSON格式返回结果，包含以下字段：
- duplicate_groups: 重复实体组列表，每个包含：
  - entities: 重复实体列表
  - similarity: 相似度估计
  - recommended_entity: 推荐保留的实体
  - reasoning: 重复判断依据
- unique_entities: 唯一实体列表
- statistics: 重复统计信息
"""
        
        human_prompt = f"""
请从以下实体列表中识别重复或高度相似的实体（相似度阈值: {similarity_threshold}）：

{entities_str}

请确保：
1. 准确识别所有重复或高度相似的实体
2. 提供详细的重复判断依据
3. 给出合理的实体合并建议
4. 返回有效的JSON格式
"""
        
        # 将实体列表格式化为字符串
        entities_str = "\n".join([
            f"- {i+1}. 名称: {entity.get('name', '未知')}, "
            f"类型: {entity.get('type', '未知')}, "
            f"属性: {entity.get('attributes', {})}"
            for i, entity in enumerate(entities)
        ])
        
        inputs = {"entities": entities_str}
        return self.extract_structured_data(
            duplicate_prompt,
            human_prompt,
            inputs
        )
    
    def merge_entity_attributes(self, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        合并实体的属性
        
        Args:
            entities: 实体列表
            
        Returns:
            包含合并后属性的字典
        """
        merge_prompt = """
你是一个专业的实体属性合并专家，专门合并相似实体的属性。

请分析给定的实体列表，合并相似实体的属性。合并时考虑：
1. 属性名称的相似性
2. 属性值的一致性和互补性
3. 属性的重要性和优先级
4. 属性冲突的解决策略

对于每个属性，请：
1. 识别相似的属性
2. 解决属性值冲突
3. 确定最终的属性值
4. 提供合并的理由

请以JSON格式返回结果，包含以下字段：
- merged_entities: 合并后的实体列表，每个包含：
  - name: 实体名称
  - type: 实体类型
  - merged_attributes: 合并后的属性
  - merge_reasoning: 属性合并说明
- conflicts: 属性冲突及解决方案
- statistics: 合并统计信息
"""
        
        human_prompt = """
请合并以下实体的属性：

{entities}

请确保：
1. 合理合并相似实体的属性
2. 妥善解决属性值冲突
3. 保留重要的属性信息
4. 提供详细的合并说明
5. 返回有效的JSON格式
"""
        
        # 将实体列表格式化为字符串
        entities_str = "\n".join([
            f"- {i+1}. 名称: {entity.get('name', '未知')}, "
            f"类型: {entity.get('type', '未知')}, "
            f"属性: {entity.get('attributes', {})}"
            for i, entity in enumerate(entities)
        ])
        
        inputs = {"entities": entities_str}
        return self.extract_structured_data(
            merge_prompt,
            human_prompt,
            inputs
        )