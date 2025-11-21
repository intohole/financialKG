"""
简单测试内容处理器配置功能
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Optional

from app.core.content_processor import ContentProcessor
from app.core.base_service import BaseService


class TestContentProcessorSimple:
    """简单测试内容处理器配置功能"""
    
    @pytest.fixture
    def content_processor(self):
        """创建内容处理器实例"""
        processor = ContentProcessor()
        
        # Mock generate_with_prompt方法
        processor.generate_with_prompt = AsyncMock()
        
        # Mock解析方法
        processor._parse_classification_response = MagicMock(return_value=MagicMock(
            category="financial",
            confidence=0.9,
            reasoning="测试理由"
        ))
        
        processor._parse_extraction_response = MagicMock(return_value=MagicMock(
            is_financial_content=True,
            confidence=0.8,
            entities=[],
            relations=[]
        ))
        
        return processor
    
    async def test_custom_category_config_parameter_passing(self, content_processor):
        """测试自定义类别配置参数传递"""
        test_text = "测试文本"
        category_config = {
            "financial": {
                "name": "金融财经",
                "description": "金融、财经、股票、证券等相关内容"
            },
            "technology": {
                "name": "科技互联网",
                "description": "科技、互联网、人工智能等相关内容"
            }
        }
        
        # 调用分类方法
        await content_processor.classify_content(
            test_text,
            category_config=category_config
        )
        
        # 验证generate_with_prompt被正确调用
        content_processor.generate_with_prompt.assert_called_once_with(
            "content_classification",
            text=test_text,
            categories="financial(金融财经): 金融、财经、股票、证券等相关内容; technology(科技互联网): 科技、互联网、人工智能等相关内容"
        )
    
    async def test_custom_prompt_key_parameter_passing(self, content_processor):
        """测试自定义prompt key参数传递"""
        test_text = "测试文本"
        
        # 调用分类方法
        await content_processor.classify_content(
            test_text,
            prompt_key="content_classification_enhanced"
        )
        
        # 验证generate_with_prompt被正确调用
        content_processor.generate_with_prompt.assert_called_once_with(
            "content_classification_enhanced",
            text=test_text,
            categories="financial(金融财经): 金融、财经、股票、证券等相关内容; technology(科技互联网): 科技、互联网、人工智能等相关内容; medical(医疗健康): 医疗、健康、药品、生物科技等相关内容; education(教育培训): 教育、培训、学术等相关内容"
        )
    
    async def test_custom_entity_relation_types_parameter_passing(self, content_processor):
        """测试自定义实体和关系类型参数传递"""
        test_text = "测试文本"
        custom_entity_types = ["科技公司", "产品", "人物", "价格"]
        custom_relation_types = ["发布", "生产", "投资", "定价"]
        
        # 调用实体关系提取方法
        await content_processor.extract_entities_and_relations(
            test_text,
            entity_types=custom_entity_types,
            relation_types=custom_relation_types
        )
        
        # 验证generate_with_prompt被正确调用
        content_processor.generate_with_prompt.assert_called_once_with(
            "entity_relation_extraction",
            text=test_text,
            entity_types="科技公司, 产品, 人物, 价格",
            relation_types="发布, 生产, 投资, 定价"
        )
    
    async def test_backward_compatibility_parameter_passing(self, content_processor):
        """测试向后兼容性参数传递"""
        test_text = "测试文本"
        
        # 测试不传入新参数的调用
        await content_processor.classify_content(test_text)
        
        # 验证generate_with_prompt被正确调用（使用默认参数）
        content_processor.generate_with_prompt.assert_called_once_with(
            "content_classification",
            text=test_text,
            categories="financial(金融财经): 金融、财经、股票、证券等相关内容; technology(科技互联网): 科技、互联网、人工智能等相关内容; medical(医疗健康): 医疗、健康、药品、生物科技等相关内容; education(教育培训): 教育、培训、学术等相关内容"
        )
        
        # 重置mock
        content_processor.generate_with_prompt.reset_mock()
        
        # 测试实体关系提取
        await content_processor.extract_entities_and_relations(test_text)
        
        # 验证generate_with_prompt被正确调用（使用默认参数）
        content_processor.generate_with_prompt.assert_called_once_with(
            "entity_relation_extraction",
            text=test_text,
            entity_types="公司/企业, 人物, 产品/服务, 地点, 事件, 概念/术语",
            relation_types="属于/子公司, 投资/收购, 合作/竞争, 位于, 参与, 影响"
        )
    
    async def test_category_config_with_categories_priority(self, content_processor):
        """测试categories和category_config同时存在时的优先级"""
        test_text = "测试文本"
        categories = ["financial", "technology"]
        category_config = {
            "financial": {
                "name": "金融财经",
                "description": "金融、财经、股票、证券等相关内容"
            },
            "technology": {
                "name": "科技互联网",
                "description": "科技、互联网、人工智能等相关内容"
            }
        }
        
        # 调用分类方法
        await content_processor.classify_content(
            test_text,
            categories=categories,
            category_config=category_config
        )
        
        # 验证generate_with_prompt被正确调用（categories优先）
        content_processor.generate_with_prompt.assert_called_once_with(
            "content_classification",
            text=test_text,
            categories="financial, technology"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])