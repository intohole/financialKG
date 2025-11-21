"""
测试内容处理器的新配置功能

验证内容处理器支持：
1. 自定义类别配置
2. 自定义实体和关系类型
3. 自定义prompt键
4. 向后兼容性
"""

import asyncio
import pytest
from typing import Dict, List, Optional

from app.core.content_processor import ContentProcessor
from app.core.models import ContentClassificationResult, KnowledgeExtractionResult


class TestContentProcessorEnhanced:
    """测试增强版内容处理器"""
    
    @pytest.fixture
    def processor(self):
        """创建内容处理器实例"""
        return ContentProcessor()
    
    @pytest.fixture
    def sample_category_config(self) -> Dict[str, Dict]:
        """示例类别配置"""
        return {
            "financial": {
                "name": "金融财经",
                "description": "金融、财经、股票、证券等相关内容",
                "entity_types": ["公司", "人物", "行业", "产品", "地点", "事件"],
                "relation_types": ["属于", "位于", "生产", "投资", "合作", "竞争"]
            },
            "technology": {
                "name": "科技互联网",
                "description": "科技、互联网、人工智能等相关内容",
                "entity_types": ["公司", "人物", "技术", "产品", "平台", "概念"],
                "relation_types": ["开发", "投资", "收购", "合作", "竞争", "应用"]
            }
        }
    
    @pytest.mark.asyncio
    async def test_classify_content_with_category_config(self, processor, sample_category_config):
        """测试使用类别配置进行分类"""
        text = "苹果公司发布了新款iPhone，采用了最新的人工智能技术"
        
        result = await processor.classify_content(
            text=text,
            category_config=sample_category_config
        )
        
        assert isinstance(result, ContentClassificationResult)
        assert result.category is not None
        assert 0.0 <= result.confidence <= 1.0
        assert len(result.reasoning) > 0
        print(f"分类结果: {result.category.value}, 置信度: {result.confidence}")
    
    @pytest.mark.asyncio
    async def test_classify_content_with_custom_categories(self, processor):
        """测试使用自定义类别列表"""
        text = "苹果公司发布了新款iPhone"
        custom_categories = ["科技", "金融", "医疗"]
        
        result = await processor.classify_content(
            text=text,
            categories=custom_categories
        )
        
        assert isinstance(result, ContentClassificationResult)
        assert result.category is not None
        print(f"自定义类别分类结果: {result.category.value}")
    
    @pytest.mark.asyncio
    async def test_classify_content_with_custom_prompt(self, processor):
        """测试使用自定义prompt键"""
        text = "比特币价格今日上涨10%"
        
        # 使用默认prompt
        result_default = await processor.classify_content(text=text)
        
        # 使用增强prompt
        result_enhanced = await processor.classify_content(
            text=text,
            prompt_key='content_classification_enhanced'
        )
        
        assert isinstance(result_default, ContentClassificationResult)
        assert isinstance(result_enhanced, ContentClassificationResult)
        print(f"默认prompt结果: {result_default.category.value}")
        print(f"增强prompt结果: {result_enhanced.category.value}")
    
    @pytest.mark.asyncio
    async def test_extract_entities_with_custom_types(self, processor):
        """测试使用自定义实体和关系类型"""
        text = "腾讯公司投资了京东集团，双方建立了战略合作关系"
        
        custom_entity_types = ["公司", "人物", "品牌"]
        custom_relation_types = ["投资", "合作", "竞争"]
        
        result = await processor.extract_entities_and_relations(
            text=text,
            entity_types=custom_entity_types,
            relation_types=custom_relation_types
        )
        
        assert isinstance(result, KnowledgeExtractionResult)
        assert len(result.entities) > 0
        assert len(result.relations) > 0
        
        # 验证实体类型是否在自定义列表中
        for entity in result.entities:
            assert entity.type in custom_entity_types
        
        print(f"提取到 {len(result.entities)} 个实体, {len(result.relations)} 个关系")
    
    @pytest.mark.asyncio
    async def test_extract_entities_with_enhanced_prompt(self, processor):
        """测试使用增强版实体提取prompt"""
        text = "阿里巴巴和蚂蚁集团宣布达成新的合作协议"
        
        result = await processor.extract_entities_and_relations(
            text=text,
            prompt_key='entity_relation_extraction_enhanced'
        )
        
        assert isinstance(result, KnowledgeExtractionResult)
        assert len(result.entities) > 0
        print(f"增强prompt提取到 {len(result.entities)} 个实体")
    
    @pytest.mark.asyncio
    async def test_backward_compatibility(self, processor):
        """测试向后兼容性"""
        text = "中国平安保险公司今日发布财报"
        
        # 测试原始调用方式
        result_classify = await processor.classify_content(text=text)
        result_extract = await processor.extract_entities_and_relations(text=text)
        
        assert isinstance(result_classify, ContentClassificationResult)
        assert isinstance(result_extract, KnowledgeExtractionResult)
        print("向后兼容性测试通过")
    
    @pytest.mark.asyncio
    async def test_empty_text_handling(self, processor):
        """测试空文本处理"""
        with pytest.raises(ValueError, match="文本内容不能为空"):
            await processor.classify_content(text="")
        
        with pytest.raises(ValueError, match="文本内容不能为空"):
            await processor.extract_entities_and_relations(text="   ")
    
    @pytest.mark.asyncio
    async def test_complex_category_config(self, processor):
        """测试复杂的类别配置"""
        complex_config = {
            "financial": {
                "name": "金融财经",
                "description": "金融、财经、股票、证券等相关内容",
                "entity_types": ["银行", "保险公司", "证券公司", "基金公司"],
                "relation_types": ["控股", "投资", "合并", "分拆"]
            },
            "medical": {
                "name": "医疗健康",
                "description": "医疗、健康、药品、生物科技等相关内容",
                "entity_types": ["医院", "制药公司", "医疗器械", "药品"],
                "relation_types": ["生产", "研发", "销售", "合作"]
            },
            "education": {
                "name": "教育培训",
                "description": "教育、培训、学术等相关内容",
                "entity_types": ["学校", "培训机构", "教育平台", "课程"],
                "relation_types": ["提供", "合作", "投资", "认证"]
            }
        }
        
        text = "协和医院与辉瑞制药合作开发新药，同时获得了红杉资本的投资"
        
        result = await processor.classify_content(
            text=text,
            category_config=complex_config
        )
        
        assert isinstance(result, ContentClassificationResult)
        print(f"复杂配置分类结果: {result.category.value}")


if __name__ == "__main__":
    # 运行基础测试
    pytest.main([__file__, "-v", "-s"])