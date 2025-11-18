"""
测试实体和关系去重合并服务
"""
import unittest
import asyncio
import json
from unittest.mock import patch, MagicMock
from datetime import datetime

from kg.services.entity_relation_deduplication_service import EntityRelationDeduplicationService
from kg.database.models import Entity, Relation, EntityGroup, RelationGroup


class TestEntityRelationDeduplicationService(unittest.TestCase):
    """测试实体和关系去重合并服务"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建模拟的数据库会话
        self.mock_session = MagicMock()
        
        # 创建模拟的LLM服务
        self.mock_llm_service = MagicMock()
        
        # 创建服务实例
        self.service = EntityRelationDeduplicationService(
            session=self.mock_session,
            llm_service=self.mock_llm_service
        )
        
        # 模拟各种服务和仓库
        self.service.entity_service = MagicMock()
        self.service.relation_service = MagicMock()
        self.service.entity_repo = MagicMock()
        self.service.relation_repo = MagicMock()
        self.service.entity_group_repo = MagicMock()
        self.service.relation_group_repo = MagicMock()
    
    @patch('kg.services.database.entity_relation_deduplication_service.handle_db_errors_with_reraise')
    async def test_deduplicate_entities_by_type(self, mock_decorator):
        """测试按类型去重实体"""
        # 配置装饰器返回原函数
        mock_decorator.return_value = lambda f: f
        
        # 模拟实体数据
        mock_entity1 = MagicMock(spec=Entity)
        mock_entity1.id = 1
        mock_entity1.name = "阿里巴巴"
        mock_entity1.type = "公司"
        mock_entity1.properties = json.dumps({"股票代码": "BABA", "成立时间": "1999年"})
        mock_entity1.confidence_score = 0.9
        mock_entity1.source = "财报"
        
        mock_entity2 = MagicMock(spec=Entity)
        mock_entity2.id = 2
        mock_entity2.name = "阿里巴巴集团"
        mock_entity2.type = "公司"
        mock_entity2.properties = json.dumps({"股票代码": "9988.HK", "成立时间": "1999年"})
        mock_entity2.confidence_score = 0.85
        mock_entity2.source = "新闻"
        
        # 设置服务返回值
        self.service.entity_service.get_entities_by_type.return_value = [mock_entity1, mock_entity2]
        
        # 设置LLM服务返回值
        self.mock_llm_service.aggregate_entities.return_value = {
            "duplicate_groups": [
                {
                    "entities": [
                        {"id": 1, "name": "阿里巴巴", "confidence_score": 0.9},
                        {"id": 2, "name": "阿里巴巴集团", "confidence_score": 0.85}
                    ],
                    "similarity_score": 0.92
                }
            ]
        }
        
        # 模拟处理重复组的方法
        self.service._process_entity_duplicate_group = MagicMock()
        
        # 执行测试
        result = await self.service.deduplicate_entities_by_type(
            entity_type="公司",
            similarity_threshold=0.8,
            batch_size=100
        )
        
        # 验证结果
        self.assertEqual(result["entity_type"], "公司")
        self.assertEqual(result["total_entities_processed"], 2)
        self.assertEqual(result["total_duplicate_groups"], 1)
        self.assertEqual(result["total_duplicate_entities"], 2)
        self.assertEqual(result["similarity_threshold"], 0.8)
        
        # 验证方法调用
        self.service.entity_service.get_entities_by_type.assert_called_once_with("公司", limit=None)
        self.mock_llm_service.aggregate_entities.assert_called_once()
        self.service._process_entity_duplicate_group.assert_called_once()
    
    @patch('kg.services.database.entity_relation_deduplication_service.handle_db_errors_with_reraise')
    async def test_process_entity_duplicate_group(self, mock_decorator):
        """测试处理实体重复组"""
        # 配置装饰器返回原函数
        mock_decorator.return_value = lambda f: f
        
        # 模拟重复组数据
        duplicate_group = {
            "entities": [
                {"id": 1, "name": "阿里巴巴", "confidence_score": 0.9},
                {"id": 2, "name": "阿里巴巴集团", "confidence_score": 0.85}
            ],
            "similarity_score": 0.92
        }
        
        # 设置LLM服务返回值
        self.mock_llm_service.aggregate_entities.return_value = {
            "merged_entity": {
                "canonical_name": "阿里巴巴集团"
            }
        }
        
        # 设置实体服务返回值
        mock_entity_group = MagicMock(spec=EntityGroup)
        self.service.entity_service.merge_entities.return_value = mock_entity_group
        
        # 执行测试
        result = await self.service._process_entity_duplicate_group(duplicate_group, "公司")
        
        # 验证结果
        self.assertEqual(result, mock_entity_group)
        
        # 验证方法调用
        self.mock_llm_service.aggregate_entities.assert_called_once()
        self.service.entity_service.merge_entities.assert_called_once_with(
            entity_ids=[1, 2],
            canonical_name="阿里巴巴集团",
            description="自动合并的公司类型实体组，包含2个实体"
        )
    
    @patch('kg.services.database.entity_relation_deduplication_service.handle_db_errors_with_reraise')
    async def test_deduplicate_relations_by_type(self, mock_decorator):
        """测试按类型去重关系"""
        # 配置装饰器返回原函数
        mock_decorator.return_value = lambda f: f
        
        # 模拟关系数据
        mock_relation1 = MagicMock(spec=Relation)
        mock_relation1.id = 1
        mock_relation1.source_entity_id = 1
        mock_relation1.target_entity_id = 2
        mock_relation1.relation_type = "控股"
        mock_relation1.properties = json.dumps({"持股比例": "51%", "生效日期": "2020-01-01"})
        mock_relation1.weight = 0.9
        mock_relation1.source = "财报"
        
        mock_relation2 = MagicMock(spec=Relation)
        mock_relation2.id = 2
        mock_relation2.source_entity_id = 1
        mock_relation2.target_entity_id = 2
        mock_relation2.relation_type = "全资控股"
        mock_relation2.properties = json.dumps({"持股比例": "100%", "生效日期": "2020-01-01"})
        mock_relation2.weight = 0.85
        mock_relation2.source = "新闻"
        
        # 设置服务返回值
        self.service.relation_service.get_relations_by_type.return_value = [mock_relation1, mock_relation2]
        
        # 模拟实体数据
        mock_entity1 = MagicMock(spec=Entity)
        mock_entity1.id = 1
        mock_entity1.name = "阿里巴巴"
        mock_entity1.type = "公司"
        
        mock_entity2 = MagicMock(spec=Entity)
        mock_entity2.id = 2
        mock_entity2.name = "蚂蚁集团"
        mock_entity2.type = "公司"
        
        self.service.entity_service.get_entity_by_id.side_effect = lambda entity_id: {
            1: mock_entity1,
            2: mock_entity2
        }.get(entity_id)
        
        # 设置LLM服务返回值
        self.mock_llm_service.aggregate_relations.return_value = {
            "duplicate_groups": [
                {
                    "relations": [
                        {"id": 1, "relation_type": "控股", "weight": 0.9},
                        {"id": 2, "relation_type": "全资控股", "weight": 0.85}
                    ],
                    "similarity_score": 0.88
                }
            ]
        }
        
        # 模拟处理重复组的方法
        self.service._process_relation_duplicate_group = MagicMock()
        
        # 执行测试
        result = await self.service.deduplicate_relations_by_type(
            relation_type="控股",
            similarity_threshold=0.8,
            batch_size=100
        )
        
        # 验证结果
        self.assertEqual(result["relation_type"], "控股")
        self.assertEqual(result["total_relations_processed"], 2)
        self.assertEqual(result["total_duplicate_groups"], 1)
        self.assertEqual(result["total_duplicate_relations"], 2)
        self.assertEqual(result["similarity_threshold"], 0.8)
        
        # 验证方法调用
        self.service.relation_service.get_relations_by_type.assert_called_once_with("控股", limit=None)
        self.mock_llm_service.aggregate_relations.assert_called_once()
        self.service._process_relation_duplicate_group.assert_called_once()
    
    @patch('kg.services.database.entity_relation_deduplication_service.handle_db_errors_with_reraise')
    async def test_process_relation_duplicate_group(self, mock_decorator):
        """测试处理关系重复组"""
        # 配置装饰器返回原函数
        mock_decorator.return_value = lambda f: f
        
        # 模拟重复组数据
        duplicate_group = {
            "relations": [
                {"id": 1, "relation_type": "控股", "weight": 0.9},
                {"id": 2, "relation_type": "全资控股", "weight": 0.85}
            ],
            "similarity_score": 0.88
        }
        
        # 设置LLM服务返回值
        self.mock_llm_service.aggregate_relations.return_value = {
            "merged_relation": {
                "canonical_relation": "控股"
            }
        }
        
        # 设置关系服务返回值
        mock_relation_group = MagicMock(spec=RelationGroup)
        self.service.relation_service.merge_relations.return_value = mock_relation_group
        
        # 执行测试
        result = await self.service._process_relation_duplicate_group(duplicate_group, "控股")
        
        # 验证结果
        self.assertEqual(result, mock_relation_group)
        
        # 验证方法调用
        self.mock_llm_service.aggregate_relations.assert_called_once()
        self.service.relation_service.merge_relations.assert_called_once_with(
            relation_ids=[1, 2],
            canonical_relation="控股",
            description="自动合并的控股类型关系组，包含2个关系"
        )
    
    @patch('kg.services.database.entity_relation_deduplication_service.handle_db_errors_with_reraise')
    async def test_consolidate_relations_after_entity_merging(self, mock_decorator):
        """测试实体合并后的关系整合"""
        # 配置装饰器返回原函数
        mock_decorator.return_value = lambda f: f
        
        # 模拟实体组
        mock_entity_group = MagicMock(spec=EntityGroup)
        mock_entity_group.primary_entity_id = 1
        self.service.entity_group_repo.get.return_value = mock_entity_group
        
        # 模拟实体数据
        mock_entity1 = MagicMock(spec=Entity)
        mock_entity1.id = 1
        mock_entity1.name = "阿里巴巴集团"
        mock_entity1.type = "公司"
        
        mock_entity2 = MagicMock(spec=Entity)
        mock_entity2.id = 2
        mock_entity2.name = "阿里巴巴"
        mock_entity2.type = "公司"
        
        # 设置实体服务返回值
        self.service.entity_service.get_entities_by_group.return_value = [mock_entity1, mock_entity2]
        self.service.entity_service.get_entity_by_id.return_value = mock_entity1
        
        # 模拟关系数据
        mock_relation1 = MagicMock(spec=Relation)
        mock_relation1.id = 1
        mock_relation1.source_entity_id = 1
        mock_relation1.target_entity_id = 3
        mock_relation1.relation_type = "投资"
        mock_relation1.properties = json.dumps({"金额": "10亿"})
        mock_relation1.weight = 1.0
        mock_relation1.source = "财报"
        
        mock_relation2 = MagicMock(spec=Relation)
        mock_relation2.id = 2
        mock_relation2.source_entity_id = 2
        mock_relation2.target_entity_id = 3
        mock_relation2.relation_type = "战略投资"
        mock_relation2.properties = json.dumps({"金额": "10亿元"})
        mock_relation2.weight = 0.9
        mock_relation2.source = "新闻"
        
        # 设置关系服务返回值
        self.service.relation_service.get_relations_by_entity.side_effect = [
            [mock_relation1],  # entity1的关系
            [mock_relation2]   # entity2的关系
        ]
        
        # 设置LLM服务返回值
        self.mock_llm_service.aggregate_relations.return_value = {
            "consolidated_relations": [
                {
                    "source_entity_id": 1,
                    "target_entity_id": 3,
                    "relation_type": "投资",
                    "properties": {"金额": "10亿元", "类型": "战略投资"},
                    "weight": 1.0
                }
            ]
        }
        
        # 执行测试
        result = await self.service.consolidate_relations_after_entity_merging(1)
        
        # 验证结果
        self.assertEqual(result["entity_group_id"], 1)
        self.assertEqual(result["primary_entity_id"], 1)
        self.assertEqual(result["primary_entity_name"], "阿里巴巴集团")
        self.assertEqual(result["total_relations_processed"], 2)
        self.assertEqual(result["total_relations_consolidated"], 1)
        
        # 验证方法调用
        self.service.entity_group_repo.get.assert_called_once_with(1)
        self.service.entity_service.get_entities_by_group.assert_called_once_with(1)
        self.mock_llm_service.aggregate_relations.assert_called_once()
    
    @patch('kg.services.database.entity_relation_deduplication_service.handle_db_errors_with_reraise')
    async def test_full_deduplication(self, mock_decorator):
        """测试完整去重流程"""
        # 配置装饰器返回原函数
        mock_decorator.return_value = lambda f: f
        
        # 模拟实体去重结果
        entity_result = {
            "total_entities_processed": 100,
            "total_duplicate_groups": 10,
            "total_duplicate_entities": 20
        }
        
        # 模拟关系去重结果
        relation_result = {
            "total_relations_processed": 200,
            "total_duplicate_groups": 20,
            "total_duplicate_relations": 50
        }
        
        # 设置服务方法返回值
        self.service.deduplicate_all_entities = MagicMock(return_value=entity_result)
        self.service.deduplicate_all_relations = MagicMock(return_value=relation_result)
        
        # 执行测试
        result = await self.service.full_deduplication(
            similarity_threshold=0.85,
            batch_size=50
        )
        
        # 验证结果
        self.assertEqual(result["similarity_threshold"], 0.85)
        self.assertEqual(result["entity_deduplication"], entity_result)
        self.assertEqual(result["relation_deduplication"], relation_result)
        
        # 验证方法调用
        self.service.deduplicate_all_entities.assert_called_once_with(
            similarity_threshold=0.85,
            batch_size=50,
            entity_types=None
        )
        self.service.deduplicate_all_relations.assert_called_once_with(
            similarity_threshold=0.85,
            batch_size=50,
            relation_types=None
        )


if __name__ == '__main__':
    # 运行异步测试
    async def run_tests():
        await unittest.main()
    
    # 注意：在实际运行时，可能需要使用更适合异步测试的方式
    unittest.main()
