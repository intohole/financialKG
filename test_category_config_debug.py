"""
测试类别配置在prompt中的实际应用
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.content_processor import ContentProcessor


class TestCategoryConfigDebug:
    """测试类别配置调试"""
    
    @pytest.fixture
    def mock_llm_service(self):
        """Mock LLM服务，捕获实际调用的prompt"""
        mock = MagicMock()
        
        # 创建一个可以捕获实际调用参数的mock
        async def mock_generate(*args, **kwargs):
            # 打印实际调用的prompt内容
            print(f"\n=== 实际调用的prompt参数 ===")
            print(f"args: {args}")
            print(f"kwargs: {kwargs}")
            
            # 返回一个基本的响应
            response = MagicMock()
            response.content = '''```json
            {
                "category": "technology",
                "confidence": 0.9,
                "reasoning": "包含科技相关词汇",
                "is_financial_content": false,
                "supported": true
            }
            ```'''
            return response
        
        mock.async_generate = mock_generate
        return mock
    
    @pytest.fixture
    def content_processor(self, mock_llm_service):
        """创建内容处理器实例"""
        processor = ContentProcessor()
        processor.llm_service = mock_llm_service
        return processor
    
    async def test_category_config_in_prompt(self, content_processor):
        """测试类别配置是否正确传入prompt"""
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
            "custom_tech": {
                "name": "自定义科技",
                "description": "这是自定义的科技类别"
            }
        }
        
        test_text = "苹果公司发布新款iPhone，售价5999元起。"
        
        # 调用分类方法，使用增强版prompt
        result = await content_processor.classify_content(
            test_text,
            category_config=category_config,
            prompt_key='content_classification_enhanced'
        )
        
        # 验证结果
        assert result is not None
        print(f"\n=== 分类结果 ===")
        print(f"类别: {result.category}")
        print(f"置信度: {result.confidence}")
        print(f"推理: {result.reasoning}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])