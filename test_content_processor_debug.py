"""
调试测试内容处理器配置功能
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Optional

from app.core.content_processor import ContentProcessor
from app.core.base_service import BaseService


class TestContentProcessorDebug:
    """调试测试内容处理器配置功能"""
    
    @pytest.fixture
    def mock_llm_service(self):
        """Mock LLM服务"""
        mock = AsyncMock()
        
        # 分类响应
        classification_response = MagicMock()
        classification_response.content = '''
        ```json
        {
            "category": "financial",
            "confidence": 0.9,
            "reasoning": "这是一个金融相关的文本",
            "is_financial_content": true,
            "supported": true
        }
        ```
        '''
        
        # 实体关系提取响应
        extraction_response = MagicMock()
        extraction_response.content = '''
        ```json
        {
            "is_financial_content": true,
            "confidence": 0.8,
            "entities": [
                {
                    "name": "苹果公司",
                    "type": "公司",
                    "description": "科技公司",
                    "properties": {}
                }
            ],
            "relations": [
                {
                    "source": "苹果公司",
                    "target": "iPhone",
                    "relation_type": "生产",
                    "confidence": 0.9,
                    "description": "苹果公司生产iPhone",
                    "properties": {}
                }
            ]
        }
        ```
        '''
        
        # 使用side_effect按顺序返回不同的响应
        mock.async_generate.side_effect = [classification_response, extraction_response]
        
        return mock
    
    @pytest.fixture
    def content_processor(self, mock_llm_service):
        """创建内容处理器实例"""
        processor = ContentProcessor()
        processor.llm_service = mock_llm_service
        return processor
    
    async def test_debug_entity_relation_extraction(self, content_processor):
        """调试实体关系提取"""
        test_text = "苹果公司生产iPhone手机"
        custom_entity_types = ["科技公司", "产品", "人物", "价格"]
        custom_relation_types = ["发布", "生产", "投资", "定价"]
        
        # 调用实体关系提取方法
        result = await content_processor.extract_entities_and_relations(
            test_text,
            entity_types=custom_entity_types,
            relation_types=custom_relation_types
        )
        
        # 验证结果
        assert result is not None
        assert result.is_financial_content is True
        assert result.confidence == 0.8
        assert len(result.entities) >= 0
        assert len(result.relations) >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])