"""
测试内容处理器配置功能
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Optional

from app.core.content_processor import ContentProcessor
from app.core.base_service import BaseService
from app.core.models import ContentClassificationResult, KnowledgeExtractionResult, Entity, Relation


class TestContentProcessorConfig:
    """测试内容处理器配置功能"""
    
    @pytest.fixture
    def mock_llm_service(self):
        """Mock LLM服务"""
        mock = MagicMock()
        # 分类响应
        classification_response = MagicMock()
        classification_response.content = '''{"category": "financial", "confidence": 0.9, "reasoning": "包含金融相关词汇", "is_financial_content": true, "supported": true}'''
        
        # 实体关系提取响应
        extraction_response = MagicMock()
        extraction_response.content = '''{"is_financial_content": true, "confidence": 0.8, "entities": [{"name": "苹果公司", "type": "公司", "description": "科技公司"}], "relations": [{"source": "苹果公司", "target": "iPhone", "relation_type": "生产", "confidence": 0.7}]}'''
        
        mock.async_generate = AsyncMock(side_effect=[classification_response, extraction_response])
        return mock
    
    @pytest.fixture
    def content_processor(self, mock_llm_service):
        """创建内容处理器实例"""
        processor = ContentProcessor()
        processor.llm_service = mock_llm_service
        return processor
    
    async def test_custom_category_config(self, content_processor):
        """测试自定义类别配置"""
        # 定义自定义类别配置
        category_config = {
            "financial": {
                "name": "金融财经",
                "description": "金融、财经、股票、证券等相关内容"
            },
            "technology": {
                "name": "科技互联网",
                "description": "科技、互联网、人工智能等相关内容"
            },
            "medical": {
                "name": "医疗健康",
                "description": "医疗、健康、药品、生物科技等相关内容"
            }
        }
        
        # 测试文本
        test_text = "苹果公司发布新款iPhone，售价5999元起。"
        
        # 调用分类方法
        result = await content_processor.classify_content(
            test_text,
            category_config=category_config
        )
        
        # 验证结果
        assert isinstance(result, ContentClassificationResult)
        assert result.category in ["financial", "technology", "medical"]
        assert result.confidence > 0
        assert result.reasoning is not None
    
    async def test_custom_prompt_key(self, content_processor):
        """测试自定义prompt key"""
        test_text = "苹果公司发布新款iPhone，售价5999元起。"
        
        # 使用自定义prompt key
        result = await content_processor.classify_content(
            test_text,
            prompt_key="content_classification_enhanced"
        )
        
        # 验证结果
        assert isinstance(result, ContentClassificationResult)
        assert result.confidence > 0
    
    async def test_custom_entity_relation_types(self, content_processor):
        """测试自定义实体和关系类型"""
        # 定义自定义实体和关系类型
        custom_entity_types = ["科技公司", "产品", "人物", "价格"]
        custom_relation_types = ["发布", "生产", "投资", "定价"]
        
        test_text = "苹果公司发布新款iPhone，售价5999元起。"
        
        # Mock generate_with_prompt方法
        with patch.object(content_processor, 'generate_with_prompt') as mock_generate:
            mock_generate.return_value = '''{"is_financial_content": true, "confidence": 0.8, "entities": [{"name": "苹果公司", "type": "公司", "description": "科技公司", "properties": {}}], "relations": [{"source": "苹果公司", "target": "iPhone", "relation_type": "生产", "confidence": 0.7, "description": "", "properties": {}}]}'''
            
            # 调用实体关系提取方法
            result = await content_processor.extract_entities_and_relations(
                test_text,
                entity_types=custom_entity_types,
                relation_types=custom_relation_types
            )
            
            # 验证结果
            assert isinstance(result, KnowledgeExtractionResult)
            assert result.is_financial_content is not None
            assert result.confidence > 0
            assert result.entities is not None
            assert result.relations is not None
            
            # 验证generate_with_prompt被正确调用
            mock_generate.assert_called_once_with(
                "entity_relation_extraction",
                text=test_text,
                entity_types="科技公司, 产品, 人物, 价格",
                relation_types="发布, 生产, 投资, 定价"
            )
    
    async def test_backward_compatibility(self, content_processor):
        """测试向后兼容性"""
        test_text = "苹果公司发布新款iPhone，售价5999元起。"
        
        # Mock generate_with_prompt方法
        with patch.object(content_processor, 'generate_with_prompt') as mock_generate:
            mock_generate.return_value = '''{"category": "financial", "confidence": 0.9, "reasoning": "包含金融相关词汇", "is_financial_content": true, "supported": true}'''
            
            # 测试不传入新参数的调用
            result1 = await content_processor.classify_content(test_text)
            
            # 验证结果
            assert isinstance(result1, ContentClassificationResult)
            
            # 重置mock
            mock_generate.return_value = '''{"is_financial_content": true, "confidence": 0.8, "entities": [{"name": "苹果公司", "type": "公司", "description": "科技公司", "properties": {}}], "relations": [{"source": "苹果公司", "target": "iPhone", "relation_type": "生产", "confidence": 0.7, "description": "", "properties": {}}]}'''
            
            # 测试实体关系提取
            result2 = await content_processor.extract_entities_and_relations(test_text)
            
            # 验证结果
            assert isinstance(result2, KnowledgeExtractionResult)
    
    async def test_category_config_with_categories(self, content_processor):
        """测试同时传入categories和category_config"""
        test_text = "苹果公司发布新款iPhone，售价5999元起。"
        
        # 定义categories和category_config
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
        result = await content_processor.classify_content(
            test_text,
            categories=categories,
            category_config=category_config
        )
        
        # 验证结果
        assert isinstance(result, ContentClassificationResult)
        assert result.category in categories
    
    async def test_format_prompt_parameters(self, content_processor):
        """测试格式化prompt参数"""
        # Mock generate_with_prompt方法
        with patch.object(content_processor, 'generate_with_prompt') as mock_generate:
            mock_generate.return_value = '''{"category": "financial", "confidence": 0.9, "reasoning": "包含金融相关词汇", "is_financial_content": true, "supported": true}'''
            
            test_text = "测试文本"
            category_config = {
                "financial": {"name": "金融", "description": "金融相关内容"}
            }
            
            # 调用分类方法
            await content_processor.classify_content(
                test_text,
                category_config=category_config,
                prompt_key="content_classification_enhanced"
            )
            
            # 验证generate_with_prompt被正确调用
            mock_generate.assert_called_once_with(
                "content_classification_enhanced",
                text=test_text,
                categories="financial(金融): 金融相关内容"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])