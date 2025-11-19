"""
基于LangChain的关系聚合服务
对相似关系进行聚合处理
"""

from typing import Any, Dict, List, Optional, Tuple

from .langchain_base_service import LangChainBaseService


class RelationAggregationService(LangChainBaseService):
    """关系聚合服务类"""

    def __init__(self, config=None):
        """初始化关系聚合服务"""
        super().__init__()
        self.llm_config = config or self.llm_config
        self.system_prompt = """
你是一个专业的关系聚合专家，专门对相似关系进行识别、分析和聚合。

请分析给定的关系列表，识别相似的关系并将它们聚合在一起。聚合时考虑以下因素：
1. 关系类型的相似性（同义词、上下位关系）
2. 关系主体的相似性（实体变体、聚合实体）
3. 关系属性的相似性
4. 关系强度和方向的一致性
5. 上下文关联性
6. 语义相似性

对于每个聚合组，请：
1. 确定一个代表性关系类型
2. 标准化关系主体
3. 合并关系属性
4. 提供聚合的理由和依据
5. 标注聚合的置信度
6. 计算聚合后的关系强度

请以JSON格式返回结果，包含以下字段：
- aggregated_relations: 聚合后的关系列表，每个包含：
  - relation_type: 代表性关系类型
  - subject: 标准化主体实体
  - object: 标准化客体实体
  - confidence: 聚合置信度（0-1）
  - strength: 关系强度（0-1）
  - reasoning: 聚合理由
  - attributes: 合并后的属性
  - source_relations: 原始关系列表
- unaggregated_relations: 未能聚合的关系列表
- statistics: 聚合统计信息
"""

        self.human_prompt = """
请对以下关系列表进行聚合分析：

{relations}

请确保：
1. 识别所有相似的关系并进行合理聚合
2. 标准化关系主体和关系类型
3. 提供详细的聚合理由和置信度
4. 合并关系属性并计算关系强度
5. 返回有效的JSON格式
"""

    def aggregate_relations(self, relations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        聚合相似关系

        Args:
            relations: 关系列表，每个关系包含subject、object、relation_type等属性

        Returns:
            包含聚合结果的字典
        """
        # 将关系列表格式化为字符串
        relations_str = "\n".join(
            [
                f"- {i+1}. 主体: {rel.get('subject', '未知')}, "
                f"客体: {rel.get('object', '未知')}, "
                f"关系类型: {rel.get('relation_type', '未知')}, "
                f"属性: {str(rel.get('attributes', {})).replace('{', '{{').replace('}', '}}')}"
                for i, rel in enumerate(relations)
            ]
        )

        inputs = {"relations": relations_str}
        return self.extract_structured_data(
            self.system_prompt, self.human_prompt, inputs
        )

    def aggregate_relations_by_type(
        self, relations: List[Dict[str, Any]], relation_type: str
    ) -> Dict[str, Any]:
        """
        按关系类型聚合相似关系

        Args:
            relations: 关系列表
            relation_type: 要聚合的关系类型

        Returns:
            包含聚合结果的字典
        """
        # 过滤出指定类型的关系
        filtered_relations = [
            r for r in relations if r.get("relation_type") == relation_type
        ]

        # 将关系列表格式化为字符串
        relations_str = "\n".join(
            [
                f"- {i+1}. 主体: {rel.get('subject', '未知')}, "
                f"客体: {rel.get('object', '未知')}, "
                f"属性: {str(rel.get('attributes', {})).replace('{', '{{').replace('}', '}}')}"
                for i, rel in enumerate(filtered_relations)
            ]
        )

        type_specific_prompt = f"""
你是一个专业的关系聚合专家，专门对{relation_type}类型的相似关系进行识别、分析和聚合。

请分析给定的{relation_type}关系列表，识别相似的关系并将它们聚合在一起。聚合时特别关注：
1. {relation_type}关系的特有属性和特征
2. {relation_type}关系的主体和客体特征
3. {relation_type}关系的强度和方向
4. {relation_type}关系的上下文信息

对于每个聚合组，请：
1. 确定标准的{relation_type}关系表示
2. 标准化关系主体和客体
3. 合并{relation_type}关系的特有属性
4. 提供聚合的理由和依据
5. 计算聚合后的{relation_type}关系强度

请以JSON格式返回结果，包含以下字段：
- relation_type: 关系类型
- aggregated_relations: 聚合后的关系列表，每个包含：
  - subject: 标准化主体实体
  - object: 标准化客体实体
  - confidence: 聚合置信度（0-1）
  - strength: 关系强度（0-1）
  - reasoning: 聚合理由
  - attributes: 合并后的属性
  - source_relations: 原始关系列表
- unaggregated_relations: 未能聚合的关系列表
- statistics: 聚合统计信息
"""

        human_prompt = f"""
请对以下{relation_type}关系列表进行聚合分析：

{relations_str}

请确保：
1. 识别所有相似的{relation_type}关系并进行合理聚合
2. 标准化关系主体和客体
3. 提供详细的聚合理由和置信度
4. 合并{relation_type}关系的特有属性
5. 返回有效的JSON格式
"""

        inputs = {"relations": relations_str}
        return self.extract_structured_data(type_specific_prompt, human_prompt, inputs)

    async def find_duplicate_relations(
        self, relations: List[Dict[str, Any]], similarity_threshold: float = 0.8
    ) -> Dict[str, Any]:
        """
        查找重复或高度相似的关系

        Args:
            relations: 关系列表
            similarity_threshold: 相似度阈值

        Returns:
            包含重复关系的字典
        """
        # 将关系列表格式化为字符串
        relations_str = "\n".join(
            [
                f"- {i+1}. 主体: {rel.get('subject', '未知')}, "
                f"客体: {rel.get('object', '未知')}, "
                f"关系类型: {rel.get('relation_type', '未知')}, "
                f"属性: {str(rel.get('attributes', {})).replace('{', '{{').replace('}', '}}')}"
                for i, rel in enumerate(relations)
            ]
        )

        duplicate_prompt = f"""
你是一个专业的关系重复检测专家，专门识别关系列表中的重复或高度相似的关系。

请分析给定的关系列表，识别重复或高度相似的关系（相似度阈值: {similarity_threshold}）。识别时考虑：
1. 关系主体的完全匹配或高度相似
2. 关系客体的完全匹配或高度相似
3. 关系类型的完全匹配或高度相似
4. 关系属性的高度重叠
5. 关系方向的一致性

对于每组重复关系，请：
1. 标记重复的关系
2. 确定保留的关系
3. 提供重复的依据和相似度
4. 建议如何合并这些关系

请以JSON格式返回结果，包含以下字段：
- duplicate_groups: 重复关系组列表，每个包含：
  - relations: 重复关系列表
  - similarity: 相似度估计
  - recommended_relation: 推荐保留的关系
  - reasoning: 重复判断依据
- unique_relations: 唯一关系列表
- statistics: 重复统计信息
"""

        human_prompt = f"""
请从以下关系列表中识别重复或高度相似的关系（相似度阈值: {similarity_threshold}）：

{relations_str}

请确保：
1. 准确识别所有重复或高度相似的关系
2. 提供详细的重复判断依据
3. 给出合理的关系合并建议
4. 返回有效的JSON格式
"""

        # 将关系列表格式化为字符串
        relations_str = "\n".join(
            [
                f"- {i+1}. 主体: {rel.get('subject', '未知')}, "
                f"客体: {rel.get('object', '未知')}, "
                f"关系类型: {rel.get('relation_type', '未知')}, "
                f"属性: {str(rel.get('attributes', {})).replace('{', '{{').replace('}', '}}')}"
                for i, rel in enumerate(relations)
            ]
        )

        inputs = {"relations": relations_str}
        return await self.extract_structured_data(
            duplicate_prompt, human_prompt, inputs
        )

    def merge_relation_attributes(
        self, relations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        合并关系的属性

        Args:
            relations: 关系列表

        Returns:
            包含合并后属性的字典
        """
        merge_prompt = """
你是一个专业的关系属性合并专家，专门合并相似关系的属性。

请分析给定的关系列表，合并相似关系的属性。合并时考虑：
1. 属性名称的相似性
2. 属性值的一致性和互补性
3. 属性的重要性和优先级
4. 属性冲突的解决策略
5. 关系强度和方向的计算

对于每个属性，请：
1. 识别相似的属性
2. 解决属性值冲突
3. 确定最终的属性值
4. 计算关系强度和方向
5. 提供合并的理由

请以JSON格式返回结果，包含以下字段：
- merged_relations: 合并后的关系列表，每个包含：
  - subject: 主体实体
  - object: 客体实体
  - relation_type: 关系类型
  - merged_attributes: 合并后的属性
  - strength: 关系强度（0-1）
  - direction: 关系方向
  - merge_reasoning: 属性合并说明
- conflicts: 属性冲突及解决方案
- statistics: 合并统计信息
"""

        human_prompt = """
请合并以下关系的属性：

{relations}

请确保：
1. 合理合并相似关系的属性
2. 妥善解决属性值冲突
3. 计算关系强度和方向
4. 保留重要的属性信息
5. 提供详细的合并说明
6. 返回有效的JSON格式
"""

        # 将关系列表格式化为字符串
        relations_str = "\n".join(
            [
                f"- {i+1}. 主体: {rel.get('subject', '未知')}, "
                f"客体: {rel.get('object', '未知')}, "
                f"关系类型: {rel.get('relation_type', '未知')}, "
                f"属性: {str(rel.get('attributes', {})).replace('{', '{{').replace('}', '}}')}"
                for i, rel in enumerate(relations)
            ]
        )

        inputs = {"relations": relations_str}
        return self.extract_structured_data(merge_prompt, human_prompt, inputs)

    def consolidate_relations(
        self, relations: List[Dict[str, Any]], entities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        整合关系，考虑实体聚合结果

        Args:
            relations: 关系列表
            entities: 已聚合的实体列表

        Returns:
            包含整合后关系的字典
        """
        consolidate_prompt = """
你是一个专业的关系整合专家，专门根据实体聚合结果整合关系。

请分析给定的关系列表和已聚合的实体列表，整合关系以反映实体聚合的结果。整合时考虑：
1. 将关系中的实体替换为聚合后的代表性实体
2. 合并因实体聚合而产生的冗余关系
3. 调整关系强度以反映实体聚合的影响
4. 更新关系属性以反映实体聚合的结果
5. 识别并解决关系冲突

对于每个整合后的关系，请：
1. 使用聚合后的代表性实体
2. 合并相似关系的属性
3. 计算整合后的关系强度
4. 提供整合的理由和依据

请以JSON格式返回结果，包含以下字段：
- consolidated_relations: 整合后的关系列表，每个包含：
  - subject: 聚合后的主体实体
  - object: 聚合后的客体实体
  - relation_type: 关系类型
  - strength: 整合后的关系强度（0-1）
  - attributes: 整合后的属性
  - source_relations: 原始关系列表
  - consolidation_reasoning: 整合说明
- entity_mapping: 实体映射关系
- statistics: 整合统计信息
"""

        human_prompt = """
请根据以下实体聚合结果，整合关系：

实体聚合结果：
{entities}

关系列表：
{relations}

请确保：
1. 将关系中的实体替换为聚合后的代表性实体
2. 合并因实体聚合而产生的冗余关系
3. 调整关系强度以反映实体聚合的影响
4. 更新关系属性以反映实体聚合的结果
5. 提供详细的整合说明
6. 返回有效的JSON格式
"""

        # 将实体列表格式化为字符串
        entities_str = "\n".join(
            [
                f"- {i+1}. 代表性名称: {entity.get('representative_name', '未知')}, "
                f"类型: {entity.get('entity_type', '未知')}, "
                f"变体: {entity.get('variants', [])}"
                for i, entity in enumerate(entities)
            ]
        )

        # 将关系列表格式化为字符串
        relations_str = "\n".join(
            [
                f"- {i+1}. 主体: {rel.get('subject', '未知')}, "
                f"客体: {rel.get('object', '未知')}, "
                f"关系类型: {rel.get('relation_type', '未知')}, "
                f"属性: {rel.get('attributes', {})}"
                for i, rel in enumerate(relations)
            ]
        )

        inputs = {"entities": entities_str, "relations": relations_str}
        return self.extract_structured_data(consolidate_prompt, human_prompt, inputs)
