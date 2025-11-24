"""
内容处理管道服务 - 内容处理流程编排

负责协调内容预处理、分类、实体提取、关系识别等处理步骤，
提供标准化的内容处理流程和结果验证机制。
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

from app.core.content_processor import ContentProcessor
from app.core.content_summarizer import ContentSummarizer
from app.core.models import ContentClassification
from app.services.service_models import NewsContent, SummaryResult, EntityExtraction, RelationExtraction


logger = logging.getLogger(__name__)


@dataclass
class ContentProcessingResult:
    """内容处理结果"""
    success: bool
    content_id: str
    classification: Optional[ContentClassification]
    entities: List[Dict[str, Any]]
    relations: List[Dict[str, Any]]
    summary: Optional[SummaryResult]
    processing_time: float
    errors: List[str]
    warnings: List[str]


@dataclass
class BatchProcessingResult:
    """批量处理结果"""
    success: bool
    total_items: int
    processed_items: int
    failed_items: int
    processing_time: float
    results: List[ContentProcessingResult]
    errors: List[str]


class ContentPipelineService:
    """内容处理管道服务"""
    
    def __init__(
        self,
        content_processor: ContentProcessor,
        content_summarizer: ContentSummarizer
    ):
        self.content_processor = content_processor
        self.content_summarizer = content_summarizer
        
        logger.info("内容处理管道服务初始化完成")
    
    async def process_single_content(
        self,
        content: NewsContent,
        enable_classification: bool = True,
        enable_extraction: bool = True,
        enable_summarization: bool = True,
        validation_rules: Optional[Dict[str, Any]] = None
    ) -> ContentProcessingResult:
        """
        处理单个内容
        
        Args:
            content: 新闻内容
            enable_classification: 是否启用分类
            enable_extraction: 是否启用实体关系提取
            enable_summarization: 是否启用摘要生成
            validation_rules: 验证规则配置
            
        Returns:
            处理结果
        """
        start_time = asyncio.get_event_loop().time()
        errors = []
        warnings = []
        
        try:
            logger.info(f"开始处理内容，ID: {content.id}")
            
            classification = None
            entities = []
            relations = []
            summary = None
            
            # 1. 内容预处理验证
            validation_result = await self._validate_content(content, validation_rules)
            if not validation_result['valid']:
                errors.extend(validation_result['errors'])
                return self._build_error_result(content.id, errors, start_time)
            
            warnings.extend(validation_result['warnings'])
            
            # 2. 内容分类
            if enable_classification:
                classification = await self._classify_content(content)
                if classification:
                    logger.debug(f"内容分类结果: {classification.classification}")
                else:
                    warnings.append("内容分类失败")
            
            # 3. 实体关系提取
            if enable_extraction:
                entities, relations = await self._extract_entities_and_relations(
                    content, classification
                )
                logger.debug(f"提取结果 - 实体: {len(entities)}, 关系: {len(relations)}")
            
            # 4. 摘要生成
            if enable_summarization:
                summary = await self._generate_summary(content)
                if summary:
                    logger.debug(f"摘要生成完成，长度: {len(summary.summary)}")
                else:
                    warnings.append("摘要生成失败")
            
            # 5. 结果验证
            validation_errors = await self._validate_processing_results(
                classification, entities, relations, summary, validation_rules
            )
            errors.extend(validation_errors)
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            result = ContentProcessingResult(
                success=len(errors) == 0,
                content_id=content.id,
                classification=classification,
                entities=entities,
                relations=relations,
                summary=summary,
                processing_time=processing_time,
                errors=errors,
                warnings=warnings
            )
            
            logger.info(f"内容处理完成，耗时: {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"内容处理失败: {str(e)}", exc_info=True)
            errors.append(f"处理过程异常: {str(e)}")
            return self._build_error_result(content.id, errors, start_time)
    
    async def process_batch_contents(
        self,
        contents: List[NewsContent],
        batch_size: int = 10,
        max_concurrent: int = 5,
        enable_classification: bool = True,
        enable_extraction: bool = True,
        enable_summarization: bool = True,
        validation_rules: Optional[Dict[str, Any]] = None
    ) -> BatchProcessingResult:
        """
        批量处理内容
        
        Args:
            contents: 内容列表
            batch_size: 每批处理数量
            max_concurrent: 最大并发数
            enable_classification: 是否启用分类
            enable_extraction: 是否启用实体关系提取
            enable_summarization: 是否启用摘要生成
            validation_rules: 验证规则配置
            
        Returns:
            批量处理结果
        """
        start_time = asyncio.get_event_loop().time()
        errors = []
        results = []
        
        try:
            total_items = len(contents)
            logger.info(f"开始批量处理，总数: {total_items}, 批次大小: {batch_size}")
            
            # 分批处理
            for i in range(0, total_items, batch_size):
                batch = contents[i:i + batch_size]
                logger.info(f"处理批次 {i//batch_size + 1}/{(total_items-1)//batch_size + 1}")
                
                # 并发处理批次内的内容
                batch_results = await self._process_batch_concurrently(
                    batch, max_concurrent, enable_classification,
                    enable_extraction, enable_summarization, validation_rules
                )
                
                results.extend(batch_results)
                
                # 检查是否有致命错误
                fatal_errors = [r for r in batch_results if len(r.errors) > 0]
                if len(fatal_errors) > len(batch) // 2:  # 超过一半失败
                    errors.append(f"批次 {i//batch_size + 1} 处理失败过多，停止处理")
                    break
            
            # 统计结果
            processed_items = len([r for r in results if r.success])
            failed_items = len([r for r in results if not r.success])
            processing_time = asyncio.get_event_loop().time() - start_time
            
            result = BatchProcessingResult(
                success=failed_items < total_items // 2,  # 失败率不超过50%
                total_items=total_items,
                processed_items=processed_items,
                failed_items=failed_items,
                processing_time=processing_time,
                results=results,
                errors=errors
            )
            
            logger.info(f"批量处理完成，总耗时: {processing_time:.2f}s，"
                       f"成功: {processed_items}, 失败: {failed_items}")
            
            return result
            
        except Exception as e:
            logger.error(f"批量处理失败: {str(e)}", exc_info=True)
            errors.append(f"批量处理异常: {str(e)}")
            
            processing_time = asyncio.get_event_loop().time() - start_time
            return BatchProcessingResult(
                success=False,
                total_items=len(contents),
                processed_items=len(results),
                failed_items=len(contents) - len(results),
                processing_time=processing_time,
                results=results,
                errors=errors
            )
    
    async def _process_batch_concurrently(
        self,
        batch: List[NewsContent],
        max_concurrent: int,
        enable_classification: bool,
        enable_extraction: bool,
        enable_summarization: bool,
        validation_rules: Optional[Dict[str, Any]]
    ) -> List[ContentProcessingResult]:
        """并发处理批次"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_semaphore(content: NewsContent):
            async with semaphore:
                return await self.process_single_content(
                    content, enable_classification, enable_extraction,
                    enable_summarization, validation_rules
                )
        
        tasks = [process_with_semaphore(content) for content in batch]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _validate_content(
        self, 
        content: NewsContent, 
        validation_rules: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """验证内容有效性"""
        errors = []
        warnings = []
        
        # 基本验证
        if not content.content or len(content.content.strip()) < 10:
            errors.append("内容太短或为空")
        
        if not content.title or len(content.title.strip()) < 2:
            warnings.append("标题太短")
        
        # 自定义验证规则
        if validation_rules:
            min_length = validation_rules.get('min_content_length', 0)
            max_length = validation_rules.get('max_content_length', 10000)
            
            content_length = len(content.content)
            if content_length < min_length:
                errors.append(f"内容长度不足，需要至少 {min_length} 字符")
            elif content_length > max_length:
                warnings.append(f"内容长度过长，建议不超过 {max_length} 字符")
            
            required_keywords = validation_rules.get('required_keywords', [])
            if required_keywords:
                has_required = any(keyword in content.content for keyword in required_keywords)
                if not has_required:
                    warnings.append("内容缺少必要关键词")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    async def _classify_content(self, content: NewsContent) -> Optional[ContentClassification]:
        """内容分类"""
        try:
            resultclassification = await self.content_processor.classify_content(
                text=content.content,
                categories=self.categories,
                category_config=self.category_config
            )
            return result if result else None
            
        except Exception as e:
            logger.error(f"内容分类失败: {str(e)}")
            return None
    
    async def _extract_entities_and_relations(
        self, 
        content: NewsContent, 
        classification: Optional[ContentClassification]
    ) -> Tuple[List[Dict], List[Dict]]:
        """提取实体和关系"""
        try:
            content_type = classification.classification if classification else "news"
            
            result = await self.content_processor.extract_entities_and_relations(
                text=content.content,
                entity_types=self.entity_types,
                relation_types=self.relation_types
            )
            
            entities = result.entities if result and hasattr(result, 'entities') else []
            relations = result.relations if result and hasattr(result, 'relations') else []
            
            return entities, relations
            
        except Exception as e:
            logger.error(f"实体关系提取失败: {str(e)}")
            return [], []
    
    async def _generate_summary(self, content: NewsContent) -> Optional[SummaryResult]:
        """生成摘要"""
        try:
            summary_result = await self.content_summarizer.generate_summary(
                text=content.content,
                max_length=200
            )
            
            if summary_result:
                return SummaryResult(
                    summary=summary_result.summary,
                    keywords=summary_result.keywords,
                    importance_score=summary_result.importance_score
                )
            return None
            
        except Exception as e:
            logger.error(f"摘要生成失败: {str(e)}")
            return None
    
    async def _validate_processing_results(
        self,
        classification: Optional[ContentClassification],
        entities: List[Dict],
        relations: List[Dict],
        summary: Optional[SummaryResult],
        validation_rules: Optional[Dict[str, Any]]
    ) -> List[str]:
        """验证处理结果"""
        errors = []
        
        if not validation_rules:
            return errors
        
        # 实体数量验证
        min_entities = validation_rules.get('min_entities', 0)
        max_entities = validation_rules.get('max_entities', 100)
        
        if len(entities) < min_entities:
            errors.append(f"实体数量不足，需要至少 {min_entities} 个")
        elif len(entities) > max_entities:
            errors.append(f"实体数量过多，建议不超过 {max_entities} 个")
        
        # 关系数量验证
        min_relations = validation_rules.get('min_relations', 0)
        if len(relations) < min_relations:
            errors.append(f"关系数量不足，需要至少 {min_relations} 个")
        
        # 分类置信度验证
        if classification and validation_rules.get('require_classification', False):
            min_confidence = validation_rules.get('min_classification_confidence', 0.7)
            if hasattr(classification, 'confidence') and classification.confidence < min_confidence:
                errors.append(f"分类置信度不足，需要至少 {min_confidence}")
        
        return errors
    
    def _build_error_result(
        self, 
        content_id: str, 
        errors: List[str], 
        start_time: float
    ) -> ContentProcessingResult:
        """构建错误结果"""
        processing_time = asyncio.get_event_loop().time() - start_time
        return ContentProcessingResult(
            success=False,
            content_id=content_id,
            classification=None,
            entities=[],
            relations=[],
            summary=None,
            processing_time=processing_time,
            errors=errors,
            warnings=[]
        )
    
    async def get_content_statistics(self, content_ids: List[str]) -> Dict[str, Any]:
        """
        获取内容统计信息
        
        Args:
            content_ids: 内容ID列表
            
        Returns:
            统计信息
        """
        try:
            # 这里可以扩展为从存储中获取详细统计信息
            # 目前返回基础统计
            return {
                'total_contents': len(content_ids),
                'processing_status': {
                    'pending': 0,
                    'processing': 0,
                    'completed': len(content_ids),
                    'failed': 0
                },
                'average_processing_time': 0.0,
                'entity_statistics': {
                    'total_entities': 0,
                    'average_entities_per_content': 0.0
                },
                'relation_statistics': {
                    'total_relations': 0,
                    'average_relations_per_content': 0.0
                }
            }
            
        except Exception as e:
            logger.error(f"获取内容统计失败: {str(e)}")
            return {
                'total_contents': len(content_ids),
                'processing_status': {'error': str(e)}
            }