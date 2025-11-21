"""知识图谱API路由

提供多类别知识图谱的RESTful API接口，基于重构后的核心模块实现。
支持内容分类、实体关系提取、实体比较和内容摘要等功能。

主要功能：
- 从文本中提取知识图谱（实体和关系）
- 检查文本类别兼容性
- 比较和消歧实体
- 获取支持的类别配置
- 生成内容摘要

使用示例：
    >>> # 提取知识图谱
    >>> POST /api/v1/knowledge-graph/extract
    >>> {"text": "苹果公司发布了新款iPhone", "category": "technology"}
    
    >>> # 检查类别兼容性
    >>> POST /api/v1/knowledge-graph/check-category-compatibility
    >>> {"text": "股票价格上涨", "category": "financial"}
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field

from app.core.content_processor import ContentProcessor
from app.core.entity_analyzer import EntityAnalyzer
from app.core.content_summarizer import ContentSummarizer
from app.core.models import Entity, ContentCategory, ContentClassificationResult, ContentSummary


# 创建API路由
router = APIRouter(prefix="/api/v1/knowledge-graph", tags=["知识图谱"])

# 创建核心服务实例
content_processor = ContentProcessor()
entity_analyzer = EntityAnalyzer()
content_summarizer = ContentSummarizer()


class TextExtractionRequest(BaseModel):
    """文本提取请求"""
    text: str = Field(..., description="要提取知识的文本内容")
    category: Optional[str] = Field(None, description="指定内容类别（如 'financial', 'technology', 'medical', 'education'）")
    news_id: Optional[str] = Field(None, description="关联的新闻ID（可选）")


class TextExtractionResponse(BaseModel):
    """文本提取响应"""
    success: bool = Field(..., description="提取是否成功")
    message: str = Field(..., description="处理消息")
    entities: List[Dict[str, Any]] = Field(default_factory=list, description="提取的实体列表")
    relations: List[Dict[str, Any]] = Field(default_factory=list, description="提取的关系列表")
    category: Optional[str] = Field(None, description="使用的类别")
    classification: Optional[Dict[str, Any]] = Field(None, description="分类结果")


class CategoryCompatibilityRequest(BaseModel):
    """类别兼容性检查请求"""
    text: str = Field(..., description="要检查的文本")
    category: str = Field(..., description="目标类别")


class CategoryCompatibilityResponse(BaseModel):
    """类别兼容性检查响应"""
    text: str = Field(..., description="输入文本")
    target_category: str = Field(..., description="目标类别")
    detected_category: str = Field(..., description="检测到的类别")
    supported_categories: List[str] = Field(..., description="支持的类别列表")
    is_supported: bool = Field(..., description="类别是否受支持")
    is_compatible: bool = Field(..., description="内容是否与类别兼容")
    confidence: float = Field(..., description="分类置信度")
    reasoning: str = Field(..., description="判断理由")


class EntityComparisonRequest(BaseModel):
    """实体比较请求"""
    entities: List[Dict[str, Any]] = Field(..., description="要比较的实体列表")


class EntityComparisonResponse(BaseModel):
    """实体比较响应"""
    comparisons: List[Dict[str, Any]] = Field(..., description="实体比较结果")


class SupportedCategoriesResponse(BaseModel):
    """支持的类别响应"""
    categories: List[str] = Field(..., description="支持的类别列表")


@router.post("/extract", response_model=TextExtractionResponse)
async def extract_knowledge(request: TextExtractionRequest):
    """从文本中提取知识图谱
    
    支持多类别知识提取，可以指定类别或自动检测类别。
    """
    try:
        result = await kg_service.extract_knowledge_from_text(
            text=request.text,
            category=request.category,
            news_id=request.news_id
        )
        
        return TextExtractionResponse(
            success=result.get("success", False),
            message=result.get("message", ""),
            entities=result.get("entities", []),
            relations=result.get("relations", []),
            category=result.get("category"),
            classification=result.get("classification")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"知识提取失败: {str(e)}")


@router.post("/check-category-compatibility", response_model=CategoryCompatibilityResponse)
async def check_category_compatibility(request: CategoryCompatibilityRequest):
    """检查文本类别是否兼容指定的实体/关系类别
    
    用于判断文本内容是否适合指定类别的知识提取。
    """
    try:
        result = await kg_service.check_text_category_compatibility(
            text=request.text,
            category=request.category
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return CategoryCompatibilityResponse(
            text=result["text"],
            target_category=result["target_category"],
            detected_category=result["detected_category"],
            supported_categories=result["supported_categories"],
            is_supported=result["is_supported"],
            is_compatible=result["is_compatible"],
            confidence=result["confidence"],
            reasoning=result["reasoning"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"类别兼容性检查失败: {str(e)}")


@router.post("/compare-entities", response_model=EntityComparisonResponse)
async def compare_entities(request: EntityComparisonRequest):
    """比较同一类别中的多个实体，判断是否属于相同实体
    
    用于实体消歧和合并，支持批量实体比较。
    """
    try:
        # 将字典转换为Entity对象
        entities = []
        for entity_data in request.entities:
            entity = Entity(
                name=entity_data.get("name", ""),
                type=entity_data.get("type", ""),
                description=entity_data.get("description", ""),
                category=entity_data.get("category", "financial"),
                attributes=entity_data.get("attributes", {}),
                source_text=entity_data.get("source_text", "")
            )
            entities.append(entity)
        
        comparisons = await kg_service.compare_entities_in_same_category(entities)
        
        return EntityComparisonResponse(comparisons=comparisons)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"实体比较失败: {str(e)}")


@router.get("/supported-categories", response_model=SupportedCategoriesResponse)
async def get_supported_categories():
    """获取支持的文本类别列表
    
    返回系统支持的所有内容类别及其对应的实体和关系类型。
    """
    try:
        categories = await kg_service.get_supported_categories()
        
        return SupportedCategoriesResponse(categories=categories)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取支持的类别失败: {str(e)}")


@router.get("/category-config/{category}")
async def get_category_config(category: str):
    """获取指定类别的配置信息
    
    包括该类别支持的实体类型和关系类型。
    """
    try:
        # 从配置中获取类别信息
        config = kg_service.config.get('knowledge_graph', {})
        categories = config.get('categories', {})
        
        if category not in categories:
            raise HTTPException(status_code=404, detail=f"类别 '{category}' 不存在")
        
        category_config = categories[category]
        
        return {
            "category": category,
            "entity_types": category_config.get('entity_types', []),
            "relation_types": category_config.get('relation_types', []),
            "description": category_config.get('description', "")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取类别配置失败: {str(e)}")


@router.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "service": "knowledge-graph"}