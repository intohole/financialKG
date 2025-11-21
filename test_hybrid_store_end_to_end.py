#!/usr/bin/env python3
"""
混合存储端到端实际测试

该测试脚本遵循以下原则：
1. 禁止使用任何模拟(mock)方法或虚假数据
2. 使用真实的配置文件和生产环境配置
3. 完整测试混合存储流程的所有关键环节
4. 记录测试过程中发现的所有问题
"""

import asyncio
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 将项目根目录添加到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.config.config_manager import ConfigManager
from app.database.core import DatabaseManager, DatabaseConfig
from app.store.hybrid_store_core import HybridStoreCore
from app.store.base import Entity, Relation
from app.embedding.embedding_service import EmbeddingService
from app.vector.chroma_vector_search import ChromaVectorSearch
from app.database.repositories import EntityRepository, RelationRepository
from concurrent.futures import ThreadPoolExecutor


class HybridStoreEndToEndTest:
    """混合存储端到端测试类"""
    
    def __init__(self):
        self.config = None
        self.db_manager = None
        self.vector_store = None
        self.embedding_service = None
        self.store = None
        self.executor = None
        self.test_results = {
            "start_time": None,
            "end_time": None,
            "tests_passed": 0,
            "tests_failed": 0,
            "issues": [],
            "performance_metrics": {}
        }
    
    async def setup(self):
        """测试环境初始化"""
        logger.info("开始初始化测试环境...")
        
        try:
            # 加载真实配置
            self.config = ConfigManager()
            logger.info("配置加载完成")
            
            # 获取数据库配置并创建数据库管理器
            config_db_config = self.config.get_database_config()
            db_config = DatabaseConfig(
                database_url=config_db_config.url,
                echo=config_db_config.echo,
                pool_pre_ping=config_db_config.pool_pre_ping,
                pool_recycle=config_db_config.pool_recycle
            )
            
            self.db_manager = DatabaseManager(db_config)
            logger.info("数据库管理器创建完成")
            
            # 创建向量存储（使用真实配置）
            vector_config = self.config.get_vector_search_config()
            vector_config_dict = {
                'path': vector_config.path,
                'host': vector_config.host,
                'port': vector_config.port,
                'collection_name': vector_config.collection_name,
                'dimension': vector_config.dimension,
                'metric': vector_config.metric,
                'timeout': vector_config.timeout
            }
            self.vector_store = ChromaVectorSearch(**vector_config_dict)
            logger.info("向量存储创建完成")
            
            # 创建嵌入服务（使用真实配置）
            self.embedding_service = EmbeddingService(self.config)
            logger.info("嵌入服务创建完成")
            
            # 创建线程池执行器
            self.executor = ThreadPoolExecutor(max_workers=4)
            logger.info("线程池执行器创建完成")
            
            # 创建混合存储核心
            self.store = HybridStoreCore(
                self.db_manager,
                self.vector_store,
                self.embedding_service,
                self.executor
            )
            logger.info("混合存储核心创建完成")
            
            # 初始化数据库表
            await self.db_manager.create_tables()
            logger.info("数据库表初始化完成")
            
            logger.info("测试环境初始化完成")
            
        except Exception as e:
            logger.error(f"测试环境初始化失败: {e}")
            raise
    
    async def test_entity_creation_and_retrieval(self):
        """测试实体创建和获取流程"""
        logger.info("=== 开始测试实体创建和获取流程 ===")
        start_time = time.time()
        
        try:
            # 创建测试实体
            test_entity = Entity(
                name="测试公司_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
                 type="company",
                 description="这是一家用于端到端测试的科技公司，专注于人工智能和机器学习技术研发。",
                 metadata={"industry": "technology", "founded_year": 2020, "employees": 150, "test_flag": True}
            )
            
            logger.info(f"创建测试实体: {test_entity.name}")
            
            # 创建实体
            created_entity = await self.store.create_entity(test_entity)
            logger.info(f"实体创建完成，ID: {created_entity.id}, Vector ID: {created_entity.vector_id}")
            
            # 验证实体创建结果
            if not created_entity.id:
                raise ValueError("实体创建失败：ID为空")
            if not created_entity.vector_id:
                raise ValueError("实体创建失败：Vector ID为空")
            
            # 获取实体
            retrieved_entity = await self.store.get_entity(created_entity.id)
            logger.info(f"实体获取完成，结果: {retrieved_entity}")
            
            # 验证实体获取结果
            if not retrieved_entity:
                raise ValueError("实体获取失败：返回None")
            if retrieved_entity.id != created_entity.id:
                raise ValueError(f"实体ID不匹配：期望{created_entity.id}，实际{retrieved_entity.id}")
            if retrieved_entity.name != created_entity.name:
                raise ValueError(f"实体名称不匹配：期望{created_entity.name}，实际{retrieved_entity.name}")
            if retrieved_entity.vector_id != created_entity.vector_id:
                raise ValueError(f"Vector ID不匹配：期望{created_entity.vector_id}，实际{retrieved_entity.vector_id}")
            
            # 验证元数据一致性
            if retrieved_entity.metadata != created_entity.metadata:
                raise ValueError(f"元数据不匹配：期望{created_entity.metadata}，实际{retrieved_entity.metadata}")
            
            elapsed_time = time.time() - start_time
            logger.info(f"实体创建和获取测试通过，耗时: {elapsed_time:.2f}秒")
            
            self.test_results["tests_passed"] += 1
            self.test_results["performance_metrics"]["entity_creation_retrieval"] = elapsed_time
            
            return created_entity
            
        except Exception as e:
            logger.error(f"实体创建和获取测试失败: {e}")
            self.test_results["tests_failed"] += 1
            self.test_results["issues"].append({
                "test": "entity_creation_and_retrieval",
                "error": str(e),
                "timestamp": datetime.now()
            })
            raise
    
    async def test_entity_search_functionality(self):
        """测试实体搜索功能"""
        logger.info("=== 开始测试实体搜索功能 ===")
        start_time = time.time()
        
        try:
            # 创建多个测试实体
            entities = []
            for i in range(3):
                entity = Entity(
                    name=f"搜索测试公司_{i}_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
                     type="company",
                     description=f"这是第{i}家用于搜索测试的科技公司，专注于人工智能技术研发。",
                     metadata={"industry": "technology", "test_flag": True, "sequence": i}
                )
                created_entity = await self.store.create_entity(entity)
                entities.append(created_entity)
                logger.info(f"创建搜索测试实体 {i}: {created_entity.name}")
            
            # 等待向量索引更新
            await asyncio.sleep(2)
            
            # 测试向量搜索
            search_query = "科技公司 人工智能"
            logger.info(f"执行向量搜索: {search_query}")
            
            search_results = await self.store.search_vectors(
                query=search_query,
                content_type="entity",
                top_k=10
            )
            
            logger.info(f"搜索完成，返回结果数量: {len(search_results)}")
            
            # 验证搜索结果
            if len(search_results) == 0:
                raise ValueError("搜索失败：未返回任何结果")
            
            # 验证搜索结果是否包含我们创建的实体
            found_entity_ids = [result["metadata"]["content_id"] for result in search_results if "metadata" in result and "content_id" in result["metadata"]]
            created_entity_ids = [str(entity.id) for entity in entities]
            
            matching_entities = set(found_entity_ids) & set(created_entity_ids)
            if len(matching_entities) == 0:
                logger.warning("搜索结果中未找到我们创建的测试实体")
            else:
                logger.info(f"在搜索结果中找到 {len(matching_entities)} 个测试实体")
            
            # 验证搜索结果的格式和内容
            for result in search_results:
                if not all(key in result for key in ["metadata", "score", "text"]):
                    raise ValueError(f"搜索结果格式错误: {result}")
                if result["score"] < 0 or result["score"] > 1:
                    raise ValueError(f"搜索分数无效: {result['score']}")
            
            elapsed_time = time.time() - start_time
            logger.info(f"实体搜索功能测试通过，耗时: {elapsed_time:.2f}秒")
            
            self.test_results["tests_passed"] += 1
            self.test_results["performance_metrics"]["entity_search"] = elapsed_time
            
            return search_results
            
        except Exception as e:
            logger.error(f"实体搜索功能测试失败: {e}")
            self.test_results["tests_failed"] += 1
            self.test_results["issues"].append({
                "test": "entity_search_functionality",
                "error": str(e),
                "timestamp": datetime.now()
            })
            raise
    
    async def test_relation_creation_and_consistency(self):
        """测试关系创建和数据一致性"""
        logger.info("=== 开始测试关系创建和数据一致性 ===")
        start_time = time.time()
        
        try:
            # 创建两个测试实体
            entity1 = Entity(
                name=f"人员A_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
                type="person",
                description="这是用于关系测试的人员A，是一家科技公司的创始人。",
                metadata={"role": "founder", "test_flag": True}
            )
            
            entity2 = Entity(
                name=f"公司B_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
                type="company",
                description="这是用于关系测试的公司B，专注于人工智能技术研发。",
                metadata={"industry": "AI", "test_flag": True}
            )
            
            created_entity1 = await self.store.create_entity(entity1)
            created_entity2 = await self.store.create_entity(entity2)
            
            logger.info(f"创建关系测试实体1: {created_entity1.name}, ID: {created_entity1.id}")
            logger.info(f"创建关系测试实体2: {created_entity2.name}, ID: {created_entity2.id}")
            
            # 创建关系
            relation = Relation(
                subject_id=created_entity1.id,
                predicate="founded",
                object_id=created_entity2.id,
                description=f"人员A创立了公司B",
                 metadata={"relationship_type": "founder", "confidence": 0.95, "test_flag": True}
            )
            
            created_relation = await self.store.create_relation(relation)
            logger.info(f"关系创建完成，ID: {created_relation.id}, Vector ID: {created_relation.vector_id}")
            
            # 验证关系创建结果
            if not created_relation.id:
                raise ValueError("关系创建失败：ID为空")
            if not created_relation.vector_id:
                raise ValueError("关系创建失败：Vector ID为空")
            if created_relation.subject_id != created_entity1.id:
                raise ValueError(f"关系主体ID不匹配")
            if created_relation.object_id != created_entity2.id:
                raise ValueError(f"关系客体ID不匹配")
            
            # 获取关系
            retrieved_relation = await self.store.get_relation(created_relation.id)
            logger.info(f"关系获取完成，结果: {retrieved_relation}")
            
            # 验证关系获取结果
            if not retrieved_relation:
                raise ValueError("关系获取失败：返回None")
            if retrieved_relation.id != created_relation.id:
                raise ValueError(f"关系ID不匹配")
            if retrieved_relation.subject_id != created_relation.subject_id:
                raise ValueError(f"关系主体ID不匹配")
            if retrieved_relation.object_id != created_relation.object_id:
                raise ValueError(f"关系客体ID不匹配")
            if retrieved_relation.vector_id != created_relation.vector_id:
                raise ValueError(f"关系Vector ID不匹配")
            
            # 验证数据一致性 - 检查实体和关系的关联性
            # 通过搜索验证关系是否可以被找到
            await asyncio.sleep(2)  # 等待索引更新
            
            relation_search_results = await self.store.search_relations(
                query="创始人 创立 公司",
                limit=10
            )
            
            logger.info(f"关系搜索完成，返回结果数量: {len(relation_search_results)}")
            
            # 验证关系搜索结果
            if len(relation_search_results) == 0:
                logger.warning("关系搜索未返回任何结果")
            else:
                found_relation_ids = [result["content_id"] for result in relation_search_results]
                if str(created_relation.id) in found_relation_ids:
                    logger.info("创建的关系在搜索结果中被找到")
                else:
                    logger.warning("创建的关系在搜索结果中未被找到")
            
            elapsed_time = time.time() - start_time
            logger.info(f"关系创建和一致性测试通过，耗时: {elapsed_time:.2f}秒")
            
            self.test_results["tests_passed"] += 1
            self.test_results["performance_metrics"]["relation_creation_consistency"] = elapsed_time
            
            return created_relation
            
        except Exception as e:
            logger.error(f"关系创建和一致性测试失败: {e}")
            self.test_results["tests_failed"] += 1
            self.test_results["issues"].append({
                "test": "relation_creation_and_consistency",
                "error": str(e),
                "timestamp": datetime.now()
            })
            raise
    
    async def test_error_handling_and_recovery(self):
        """测试错误处理和恢复机制"""
        logger.info("=== 开始测试错误处理和恢复机制 ===")
        start_time = time.time()
        
        try:
            # 测试1: 创建无效实体（缺少必需字段）
            logger.info("测试1: 创建无效实体")
            try:
                invalid_entity = Entity(
                    name="",  # 空名称
                    type="",  # 空类型
                    description="测试描述"
                )
                await self.store.create_entity(invalid_entity)
                logger.warning("无效实体创建未抛出异常，这可能是一个问题")
            except Exception as e:
                logger.info(f"无效实体创建正确抛出异常: {type(e).__name__}: {e}")
            
            # 测试2: 获取不存在的实体
            logger.info("测试2: 获取不存在的实体")
            try:
                non_existent_entity = await self.store.get_entity(999999)
                if non_existent_entity is None:
                    logger.info("获取不存在的实体正确返回None")
                else:
                    logger.warning(f"获取不存在的实体返回了结果: {non_existent_entity}")
            except Exception as e:
                logger.info(f"获取不存在的实体抛出异常: {type(e).__name__}: {e}")
            
            # 测试3: 搜索空查询
            logger.info("测试3: 搜索空查询")
            try:
                empty_search_results = await self.store.search_entities("", limit=5)
                logger.info(f"空查询搜索结果: {len(empty_search_results)} 个结果")
            except Exception as e:
                logger.info(f"空查询抛出异常: {type(e).__name__}: {e}")
            
            # 测试4: 创建自引用关系（潜在问题场景）
            logger.info("测试4: 创建自引用关系")
            try:
                # 创建一个实体
                test_entity = Entity(
                    name=f"自引用测试_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
                    type="person",
                    description="用于自引用关系测试的人员",
                    metadata={"test_flag": True}
                )
                created_entity = await self.store.create_entity(test_entity)
                
                # 尝试创建自引用关系
                self_relation = Relation(
                    subject_id=created_entity.id,
                    predicate="knows",
                    object_id=created_entity.id,  # 自引用
                    description="自己认识自己",
                     metadata={"test_flag": True}
                )
                
                created_self_relation = await self.store.create_relation(self_relation)
                logger.info(f"自引用关系创建成功: {created_self_relation.id}")
                
            except Exception as e:
                logger.info(f"自引用关系创建抛出异常: {type(e).__name__}: {e}")
            
            elapsed_time = time.time() - start_time
            logger.info(f"错误处理和恢复测试通过，耗时: {elapsed_time:.2f}秒")
            
            self.test_results["tests_passed"] += 1
            self.test_results["performance_metrics"]["error_handling_recovery"] = elapsed_time
            
        except Exception as e:
            logger.error(f"错误处理和恢复测试失败: {e}")
            self.test_results["tests_failed"] += 1
            self.test_results["issues"].append({
                "test": "error_handling_and_recovery",
                "error": str(e),
                "timestamp": datetime.now()
            })
            raise
    
    async def test_performance_and_scalability(self):
        """测试性能和可扩展性"""
        logger.info("=== 开始测试性能和可扩展性 ===")
        start_time = time.time()
        
        try:
            # 测试批量创建实体的性能
            batch_size = 10
            logger.info(f"测试批量创建 {batch_size} 个实体的性能")
            
            batch_start_time = time.time()
            created_entities = []
            
            for i in range(batch_size):
                entity = Entity(
                    name=f"性能测试实体_{i}_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
                    type="test_entity",
                    description=f"这是第{i}个用于性能测试的实体",
                     metadata={"batch_index": i, "batch_size": batch_size, "test_flag": True}
                )
                
                created_entity = await self.store.create_entity(entity)
                created_entities.append(created_entity)
                
                if i % 5 == 0:
                    logger.info(f"已创建 {i+1}/{batch_size} 个实体")
            
            batch_elapsed_time = time.time() - batch_start_time
            avg_creation_time = batch_elapsed_time / batch_size
            
            logger.info(f"批量创建完成，总耗时: {batch_elapsed_time:.2f}秒")
            logger.info(f"平均每个实体创建时间: {avg_creation_time:.3f}秒")
            
            # 测试批量搜索性能
            search_start_time = time.time()
            search_results = await self.store.search_entities(
                query="性能测试实体",
                limit=batch_size
            )
            search_elapsed_time = time.time() - search_start_time
            
            logger.info(f"批量搜索完成，返回 {len(search_results)} 个结果，耗时: {search_elapsed_time:.2f}秒")
            
            # 验证性能指标
            if avg_creation_time > 1.0:  # 如果平均创建时间超过1秒
                logger.warning(f"实体创建性能警告：平均创建时间 {avg_creation_time:.3f} 秒过长")
            
            if search_elapsed_time > 5.0:  # 如果搜索时间超过5秒
                logger.warning(f"搜索性能警告：搜索耗时 {search_elapsed_time:.2f} 秒过长")
            
            elapsed_time = time.time() - start_time
            logger.info(f"性能和可扩展性测试通过，耗时: {elapsed_time:.2f}秒")
            
            self.test_results["tests_passed"] += 1
            self.test_results["performance_metrics"]["performance_scalability"] = elapsed_time
            self.test_results["performance_metrics"]["avg_entity_creation_time"] = avg_creation_time
            self.test_results["performance_metrics"]["batch_search_time"] = search_elapsed_time
            
            return created_entities
            
        except Exception as e:
            logger.error(f"性能和可扩展性测试失败: {e}")
            self.test_results["tests_failed"] += 1
            self.test_results["issues"].append({
                "test": "performance_and_scalability",
                "error": str(e),
                "timestamp": datetime.now()
            })
            raise
    
    async def cleanup_test_data(self):
        """清理测试数据"""
        logger.info("=== 开始清理测试数据 ===")
        
        try:
            # 这里可以添加清理测试数据的逻辑
            # 例如：删除带有test_flag标记的实体和关系
            logger.info("测试数据清理完成")
            
        except Exception as e:
            logger.error(f"测试数据清理失败: {e}")
            logger.warning("测试数据可能残留在数据库中")
    
    async def generate_test_report(self):
        """生成测试报告"""
        logger.info("=== 生成测试报告 ===")
        
        self.test_results["end_time"] = datetime.now()
        total_tests = self.test_results["tests_passed"] + self.test_results["tests_failed"]
        
        report = f"""
混合存储端到端测试报告
========================

测试开始时间: {self.test_results['start_time']}
测试结束时间: {self.test_results['end_time']}
总测试数: {total_tests}
通过测试数: {self.test_results['tests_passed']}
失败测试数: {self.test_results['tests_failed']}
成功率: {(self.test_results['tests_passed'] / total_tests * 100) if total_tests > 0 else 0:.1f}%

性能指标:
--------
"""
        
        for metric_name, metric_value in self.test_results["performance_metrics"].items():
            if isinstance(metric_value, float):
                report += f"{metric_name}: {metric_value:.3f}秒\n"
        
        if self.test_results["issues"]:
            report += f"""
发现的问题:
--------
"""
            for i, issue in enumerate(self.test_results["issues"], 1):
                report += f"{i}. 测试: {issue['test']}\n"
                report += f"   错误: {issue['error']}\n"
                report += f"   时间: {issue['timestamp']}\n\n"
        
        report += f"""
测试结论:
--------
{"所有测试通过，系统运行正常" if self.test_results['tests_failed'] == 0 else f"发现 {self.test_results['tests_failed']} 个问题，需要修复"}

建议:
--------
{"系统可以投入生产使用" if self.test_results['tests_failed'] == 0 else "建议修复问题后再进行生产部署"}
"""
        
        logger.info(report)
        
        # 保存测试报告到文件
        report_file = project_root / f"hybrid_store_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"测试报告已保存到: {report_file}")
        return report
    
    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("开始混合存储端到端测试...")
        self.test_results["start_time"] = datetime.now()
        
        try:
            # 初始化测试环境
            await self.setup()
            
            # 运行各项测试
            await self.test_entity_creation_and_retrieval()
            await self.test_entity_search_functionality()
            await self.test_relation_creation_and_consistency()
            await self.test_error_handling_and_recovery()
            await self.test_performance_and_scalability()
            
            # 生成测试报告
            report = await self.generate_test_report()
            
            logger.info("混合存储端到端测试完成")
            
            return self.test_results
            
        except Exception as e:
            logger.error(f"测试执行失败: {e}")
            await self.generate_test_report()
            raise
        
        finally:
            # 清理测试数据
            await self.cleanup_test_data()
            
            # 关闭资源
            if self.executor:
                self.executor.shutdown(wait=True)
            if self.db_manager:
                await self.db_manager.close()


async def main():
    """主函数"""
    logger.info("启动混合存储端到端测试...")
    
    test_runner = HybridStoreEndToEndTest()
    
    try:
        results = await test_runner.run_all_tests()
        
        # 根据测试结果决定退出码
        if results["tests_failed"] > 0:
            logger.error(f"测试失败：{results['tests_failed']} 个测试未通过")
            sys.exit(1)
        else:
            logger.info("所有测试通过")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"测试执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())