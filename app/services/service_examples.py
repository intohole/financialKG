"""
核心服务层接口文档和使用示例

本模块提供了知识图谱系统核心服务层的详细接口文档和使用示例，
帮助开发者快速理解和使用核心服务层功能。
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# 导入核心服务
from app.services.knowledge_graph_builder import KnowledgeGraphBuilder
from app.services.content_pipeline_service import ContentPipelineService
from app.services.entity_pipeline_service import EntityPipelineService
from app.services.relation_pipeline_service import RelationPipelineService
from app.services.service_config import ServiceConfigManager, ServiceException

# 导入基础层
from app.core.content_processor import ContentProcessor
from app.core.entity_analyzer import EntityAnalyzer
from app.core.content_summarizer import ContentSummarizer
from app.store.hybrid_store_core_implement import HybridStoreCore


logger = logging.getLogger(__name__)


class ServiceUsageExamples:
    """服务使用示例类"""
    
    def __init__(self):
        # 初始化基础层组件
        self.content_processor = ContentProcessor()
        self.entity_analyzer = EntityAnalyzer()
        self.content_summarizer = ContentSummarizer()
        self.store = HybridStoreCore()
        
        # 初始化核心服务层
        self.kg_builder = KnowledgeGraphBuilder(
            content_processor=self.content_processor,
            entity_analyzer=self.entity_analyzer,
            content_summarizer=self.content_summarizer,
            store=self.store
        )
        
        self.content_service = ContentPipelineService(
            content_processor=self.content_processor,
            content_summarizer=self.content_summarizer
        )
        
        self.entity_service = EntityPipelineService(
            entity_analyzer=self.entity_analyzer,
            store=self.store
        )
        
        self.relation_service = RelationPipelineService(
            store=self.store
        )
    
    async def example_knowledge_graph_building(self):
        """知识图谱构建示例"""
        print("=== 知识图谱构建示例 ===")
        
        # 示例内容
        content = """
        腾讯控股有限公司是一家中国科技公司，成立于1998年，总部位于深圳。
        公司主要业务包括社交网络、游戏、金融科技等。微信是腾讯旗下的核心产品，
        拥有超过12亿月活跃用户。腾讯还投资了多家游戏公司，包括Riot Games和Epic Games。
        """
        
        try:
            # 构建知识图谱
            result = await self.kg_builder.build_from_content(
                content=content,
                content_id="example_content_001",
                enable_validation=True,
                enable_deduplication=True
            )
            
            print(f"构建结果: {result.success}")
            print(f"提取实体数量: {len(result.entities)}")
            print(f"提取关系数量: {len(result.relations)}")
            print(f"处理时间: {result.processing_time:.2f}秒")
            
            # 显示提取的实体
            print("\n提取的实体:")
            for entity in result.entities[:5]:  # 显示前5个
                print(f"  - {entity['name']} ({entity['type']})")
            
            # 显示提取的关系
            print("\n提取的关系:")
            for relation in result.relations[:3]:  # 显示前3个
                print(f"  - {relation['source_entity']} -> {relation['target_entity']} "
                      f"({relation['relation_type']})")
            
            return result
            
        except ServiceException as e:
            print(f"构建失败: {e}")
            return None
    
    async def example_content_processing_pipeline(self):
        """内容处理管道示例"""
        print("\n=== 内容处理管道示例 ===")
        
        # 示例内容列表
        contents = [
            "苹果公司发布了新款iPhone，搭载了最新的A17芯片。",
            "阿里巴巴集团公布季度财报，营收增长15%。",
            "特斯拉在上海的超级工厂产能持续提升。"
        ]
        
        try:
            # 批量处理内容
            results = await self.content_service.process_batch_contents(
                contents=contents,
                enable_classification=True,
                enable_extraction=True,
                enable_summarization=True
            )
            
            print(f"批量处理完成，处理 {len(results)} 条内容")
            
            for i, result in enumerate(results):
                print(f"\n内容 {i+1} 处理结果:")
                print(f"  分类: {result.classification}")
                print(f"  实体数量: {len(result.entities)}")
                print(f"  关系数量: {len(result.relations)}")
                print(f"  摘要: {result.summary[:100]}...")
            
            return results
            
        except ServiceException as e:
            print(f"处理失败: {e}")
            return []
    
    async def example_entity_management(self):
        """实体管理示例"""
        print("\n=== 实体管理示例 ===")
        
        # 示例实体数据
        entities = [
            {
                "name": "腾讯",
                "type": "公司",
                "properties": {"industry": "科技", "founded": "1998"}
            },
            {
                "name": "阿里巴巴",
                "type": "公司", 
                "properties": {"industry": "电商", "founded": "1999"}
            }
        ]
        
        try:
            # 标准化实体
            standardized_entities = await self.entity_service.standardize_entities(
                entities=entities,
                enable_disambiguation=True,
                enable_enrichment=True
            )
            
            print(f"标准化实体数量: {len(standardized_entities)}")
            
            for entity in standardized_entities:
                print(f"实体: {entity['name']} ({entity['type']})")
                if entity.get('disambiguation_result'):
                    print(f"  消歧结果: {entity['disambiguation_result']}")
                if entity.get('enrichment_data'):
                    print(f"  增强数据: {len(entity['enrichment_data'])} 条")
            
            # 实体质量评估
            if standardized_entities:
                quality_result = await self.entity_service.assess_entity_quality(
                    entity_id=standardized_entities[0].get('id', ''),
                    quality_criteria={"completeness": 0.8, "accuracy": 0.9}
                )
                
                if quality_result:
                    print(f"\n实体质量评估:")
                    print(f"  质量分数: {quality_result.quality_score:.2f}")
                    print(f"  完整性: {quality_result.completeness_score:.2f}")
                    print(f"  准确性: {quality_result.accuracy_score:.2f}")
            
            return standardized_entities
            
        except ServiceException as e:
            print(f"实体管理失败: {e}")
            return []
    
    async def example_relation_management(self):
        """关系管理示例"""
        print("\n=== 关系管理示例 ===")
        
        # 示例关系数据
        relations = [
            {
                "source_entity": "腾讯",
                "target_entity": "微信",
                "relation_type": "拥有",
                "properties": {"confidence": 0.95, "source": "公开资料"}
            },
            {
                "source_entity": "阿里巴巴",
                "target_entity": "淘宝",
                "relation_type": "拥有",
                "properties": {"confidence": 0.90, "source": "公司年报"}
            }
        ]
        
        try:
            # 验证关系
            validation_results = []
            for relation in relations:
                validation_result = await self.relation_service.validate_relation(
                    relation=relation,
                    enable_semantic_check=True,
                    enable_structural_check=True
                )
                validation_results.append(validation_result)
                
                print(f"关系验证: {relation['source_entity']} -> {relation['target_entity']}")
                print(f"  有效: {validation_result.is_valid}")
                print(f"  分数: {validation_result.validation_score:.2f}")
                if validation_result.issues:
                    print(f"  问题: {', '.join(validation_result.issues)}")
            
            # 关系去重
            deduplication_result = await self.relation_service.deduplicate_relations(
                relations=relations,
                deduplication_threshold=0.85
            )
            
            print(f"\n关系去重结果:")
            print(f"  原始数量: {deduplication_result.original_count}")
            print(f"  去重后数量: {deduplication_result.deduplicated_count}")
            print(f"  处理时间: {deduplication_result.processing_time:.2f}秒")
            
            return validation_results
            
        except ServiceException as e:
            print(f"关系管理失败: {e}")
            return []
    
    async def example_error_handling(self):
        """错误处理示例"""
        print("\n=== 错误处理示例 ===")
        
        try:
            # 模拟错误情况：空内容
            result = await self.kg_builder.build_from_content(
                content="",
                content_id="empty_content"
            )
            
        except ServiceException as e:
            print(f"捕获服务异常:")
            print(f"  错误码: {e.error.code.value}")
            print(f"  消息: {e.error.message}")
            print(f"  服务: {e.error.service_name}")
            print(f"  操作: {e.error.operation}")
            print(f"  可恢复: {e.error.recoverable}")
    
    async def example_batch_processing(self):
        """批量处理示例"""
        print("\n=== 批量处理示例 ===")
        
        # 大量内容数据
        large_contents = [
            f"这是第{i}条测试内容，包含公司{i}的相关信息。" 
            for i in range(1, 21)  # 20条内容
        ]
        
        try:
            # 批量构建知识图谱
            batch_results = await self.kg_builder.build_from_contents_batch(
                contents=large_contents,
                content_ids=[f"batch_content_{i}" for i in range(len(large_contents))],
                batch_size=5,  # 每批处理5条
                enable_parallel=True
            )
            
            print(f"批量处理完成，共处理 {len(batch_results)} 批")
            
            total_entities = sum(len(result.entities) for result in batch_results)
            total_relations = sum(len(result.relations) for result in batch_results)
            
            print(f"总实体数量: {total_entities}")
            print(f"总关系数量: {total_relations}")
            
            # 统计处理时间
            total_time = sum(result.processing_time for result in batch_results)
            avg_time = total_time / len(batch_results) if batch_results else 0
            
            print(f"总处理时间: {total_time:.2f}秒")
            print(f"平均批处理时间: {avg_time:.2f}秒")
            
            return batch_results
            
        except ServiceException as e:
            print(f"批量处理失败: {e}")
            return []
    
    async def example_quality_assessment(self):
        """质量评估示例"""
        print("\n=== 质量评估示例 ===")
        
        try:
            # 构建知识图谱
            content = "苹果公司CEO蒂姆·库克宣布新产品发布。"
            build_result = await self.kg_builder.build_from_content(
                content=content,
                content_id="quality_test_001"
            )
            
            if build_result.success and build_result.entities:
                # 评估实体质量
                entity_quality = await self.entity_service.assess_entity_quality(
                    entity_id=build_result.entities[0].get('id', ''),
                    quality_criteria={
                        "completeness": 0.8,
                        "accuracy": 0.9,
                        "consistency": 0.85
                    }
                )
                
                if entity_quality:
                    print(f"实体质量评估:")
                    print(f"  综合质量: {entity_quality.quality_score:.2f}")
                    print(f"  完整性: {entity_quality.completeness_score:.2f}")
                    print(f"  准确性: {entity_quality.accuracy_score:.2f}")
                    print(f"  一致性: {entity_quality.consistency_score:.2f}")
                    
                    if entity_quality.issues:
                        print(f"  问题: {', '.join(entity_quality.issues)}")
                    
                    if entity_quality.suggestions:
                        print(f"  建议: {', '.join(entity_quality.suggestions)}")
            
            # 整体质量评估
            overall_quality = await self.kg_builder.assess_knowledge_graph_quality(
                content_id="quality_test_001"
            )
            
            if overall_quality:
                print(f"\n知识图谱整体质量:")
                print(f"  实体质量: {overall_quality.entity_quality_score:.2f}")
                print(f"  关系质量: {overall_quality.relation_quality_score:.2f}")
                print(f"  结构质量: {overall_quality.structural_quality_score:.2f}")
                print(f"  综合质量: {overall_quality.overall_quality_score:.2f}")
            
        except ServiceException as e:
            print(f"质量评估失败: {e}")


async def main():
    """主函数 - 运行所有示例"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("开始运行核心服务层使用示例...")
    
    # 创建示例实例
    examples = ServiceUsageExamples()
    
    try:
        # 运行各种示例
        await examples.example_knowledge_graph_building()
        await examples.example_content_processing_pipeline()
        await examples.example_entity_management()
        await examples.example_relation_management()
        await examples.example_error_handling()
        await examples.example_batch_processing()
        await examples.example_quality_assessment()
        
        print("\n=== 所有示例运行完成 ===")
        
    except Exception as e:
        print(f"运行示例时发生错误: {e}")
        logger.error("运行示例失败", exc_info=True)


if __name__ == "__main__":
    # 运行异步主函数
    asyncio.run(main())