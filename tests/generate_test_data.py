#!/usr/bin/env python3
"""
测试数据生成脚本
生成模拟的新闻、实体、关系数据用于测试
"""

import asyncio
import random
import traceback
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.manager import DatabaseManager
from app.database.models import Entity, Relation, NewsEvent
from app.database.repositories import EntityRepository, RelationRepository, NewsEventRepository
from app.store.hybrid_store_core_implement import HybridStoreCore
from app.embedding.embedding_service import EmbeddingService
from app.utils.logging_utils import get_logger

logger = get_logger(__name__)


class TestDataGenerator:
    """测试数据生成器"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        # 暂时不初始化HybridStoreCore，避免依赖问题
        self.hybrid_store = None
        self.embedding_service = None
        
        # 测试数据模板
        self.tech_companies = [
            "苹果公司", "谷歌", "微软", "亚马逊", "腾讯", "阿里巴巴", "百度", "字节跳动",
            "华为", "小米", "特斯拉", "英伟达", "英特尔", "AMD", "高通", "三星"
        ]
        
        self.ai_concepts = [
            "人工智能", "机器学习", "深度学习", "神经网络", "自然语言处理", "计算机视觉",
            "大语言模型", "GPT", "ChatGPT", "生成式AI", "强化学习", "迁移学习", "联邦学习",
            "边缘计算", "云计算", "量子计算", "区块链", "物联网", "5G", "6G"
        ]
        
        self.news_sources = [
            "科技日报", "人民日报", "新华社", "央视新闻", "第一财经", "36氪", "虎嗅网",
            "钛媒体", "雷锋网", "极客公园", "IT桔子", "创业邦", "投资界", "网易科技"
        ]
        
        self.news_templates = [
            "{company}发布新一代{ai_concept}产品，引领行业创新",
            "{company}宣布重大技术突破，{ai_concept}领域迎来新机遇",
            "{company}与{company2}达成战略合作，共同推进{ai_concept}发展",
            "{company}获得{ai_concept}相关专利，技术实力再获认可",
            "{company}在{ai_concept}领域投资加码，布局未来科技发展",
            "{company}发布{ai_concept}研究报告，深度解析行业趋势",
            "{company}举办{ai_concept}技术峰会，汇聚行业精英",
            "{company}的{ai_concept}技术获得国际认可，彰显中国科技实力",
            "{company}推出基于{ai_concept}的新服务，用户体验大幅提升",
            "{company}在{ai_concept}竞赛中夺冠，技术实力获全球关注"
        ]
        
        self.news_contents = [
            """近日，{company}正式发布了其最新的{ai_concept}产品，这一创新成果标志着公司在人工智能领域的技术实力再次获得重大突破。
            
            据悉，该产品采用了最先进的{ai_concept}算法，能够实现{feature1}、{feature2}和{feature3}等多项核心功能。公司首席技术官表示，这项技术将在未来{timeframe}内彻底改变相关行业格局。
            
            业内专家认为，{company}此次发布的新产品不仅体现了其在{ai_concept}领域的深厚技术积累，更将为整个行业带来新的发展机遇。预计该产品将在{application_field}领域发挥重要作用。
            
            目前，该产品已经开始接受预订，预计将在{launch_time}正式推向市场。""",
            
            """{company}今日宣布，公司在{ai_concept}技术方面取得重大突破性进展，相关研究成果已发表在国际顶级学术期刊上。
            
            据公司研发负责人介绍，这项新技术能够{technical_advantage}，相比现有技术具有{performance_improvement}倍的性能提升。该技术主要应用于{application_scenario}等场景。
            
            {company}董事长兼CEO表示："我们一直致力于{ai_concept}技术的研发和创新，此次突破是公司多年来持续投入的结果。我们相信这项技术将为{target_industry}行业带来革命性的变化。"
            
            市场分析师指出，{company}此次技术突破不仅巩固了其在{ai_concept}领域的领先地位，更将为公司未来发展提供强劲动力。""",
            
            """在今日举行的{event_name}大会上，{company}与{company2}正式签署战略合作协议，双方将在{ai_concept}领域展开深度合作。
            
            根据协议内容，两家公司将充分发挥各自在{field1}和{field2}方面的优势，共同推进{ai_concept}技术的产业化应用。合作范围涵盖{cooperation_area1}、{cooperation_area2}和{cooperation_area3}等多个方面。
            
            {company}CEO表示："我们非常高兴能够与{company2}达成战略合作。双方在{ai_concept}领域具有很强的互补性，这次合作将为行业发展注入新的活力。"
            
            {company2}相关负责人也表示，期待通过双方的深度合作，共同推动{ai_concept}技术的创新与应用，为用户创造更大价值。"""
        ]
    
    async def generate_entities(self, count: int = 20):
        """生成实体数据"""
        logger.info(f"开始生成 {count} 个实体...")
        entities = []
        
        # 获取数据库会话
        async with self.db_manager.get_session() as session:
            entity_repo = EntityRepository(session)
            
            # 生成科技公司实体
            for company in random.sample(self.tech_companies, min(8, len(self.tech_companies))):
                entity = await entity_repo.create({
                    "name": company,
                    "type": "科技公司",
                    "description": f"{company}是一家专注于人工智能和高科技产品研发的公司",
                    "meta_data": {"industry": "科技", "focus": "AI", "scale": "large"}
                })
                entities.append(entity)
                logger.info(f"创建实体: {company}")
            
            # 生成AI概念实体
            for concept in random.sample(self.ai_concepts, min(8, len(self.ai_concepts))):
                entity = await entity_repo.create({
                    "name": concept,
                    "type": "技术概念",
                    "description": f"{concept}是人工智能领域的重要技术分支",
                    "meta_data": {"category": "AI", "maturity": "developing", "applications": ["industry", "research"]}
                })
                entities.append(entity)
                logger.info(f"创建实体: {concept}")
            
            # 生成人物实体
            ai_experts = ["李飞飞", "吴恩达", "Hinton", "LeCun", "Bengio", "何恺明", "颜水成", "张潼"]
            for expert in random.sample(ai_experts, min(4, len(ai_experts))):
                entity = await entity_repo.create(
                    name=expert,
                    type="人物",
                    description=f"{expert}是人工智能领域的知名专家和学者",
                    meta_data={"role": "researcher", "field": "AI", "nationality": "international"}
                )
                entities.append(entity)
                logger.info(f"创建实体: {expert}")
        
        logger.info(f"实体生成完成，共创建 {len(entities)} 个实体")
        return entities
    
    async def generate_relations(self, entities: list, count: int = 30):
        """生成关系数据"""
        logger.info(f"开始生成 {count} 个关系...")
        relations = []
        
        # 获取数据库会话
        async with self.db_manager.get_session() as session:
            relation_repo = RelationRepository(session)
            
            # 定义关系类型
            relation_types = [
                "研发", "投资", "合作", "收购", "竞争", "领导", "创新", "应用",
                "支持", "推动", "专注于", "致力于", "在...领域领先", "拥有...技术"
            ]
            
            for i in range(count):
                # 随机选择两个实体
                entity1, entity2 = random.sample(entities, 2)
                predicate = random.choice(relation_types)
                
                # 根据实体类型生成合适的描述
                if entity1.type == "科技公司" and entity2.type == "技术概念":
                    description = f"{entity1.name}在{entity2.name}领域有重要布局和投资"
                elif entity1.type == "人物" and entity2.type == "技术概念":
                    description = f"{entity1.name}是{entity2.name}领域的专家和推动者"
                elif entity1.type == "科技公司" and entity2.type == "科技公司":
                    description = f"{entity1.name}与{entity2.name}在AI领域存在{predicate}关系"
                else:
                    description = f"{entity1.name}与{entity2.name}之间存在{predicate}关系"
                
                relation = await relation_repo.create(
                    subject_id=entity1.id,
                    predicate=predicate,
                    object_id=entity2.id,
                    description=description,
                    meta_data={"confidence": random.uniform(0.7, 1.0), "source": "test_data"}
                )
                relations.append(relation)
                logger.info(f"创建关系: {entity1.name} {predicate} {entity2.name}")
            
            await session.flush()
        
        logger.info(f"关系生成完成，共创建 {len(relations)} 个关系")
        return relations
    
    async def generate_news_events(self, entities: list, count: int = 50):
        """生成新闻事件数据"""
        logger.info(f"开始生成 {count} 条新闻...")
        news_events = []
        
        # 获取数据库会话
        async with self.db_manager.get_session() as session:
            news_repo = NewsEventRepository(session)
            
            for i in range(count):
                # 随机选择公司和AI概念
                company = random.choice([e for e in entities if e.type == "科技公司"])
                ai_concept = random.choice([e for e in entities if e.type == "技术概念"])
                
                # 生成标题
                template = random.choice(self.news_templates)
                if "{company2}" in template:
                    company2 = random.choice([e for e in entities if e.type == "科技公司" and e.id != company.id])
                    title = template.format(company=company.name, ai_concept=ai_concept.name, company2=company2.name)
                else:
                    title = template.format(company=company.name, ai_concept=ai_concept.name)
                
                # 生成内容
                content_template = random.choice(self.news_contents)
                
                # 填充内容模板中的变量
                features = ["智能识别", "自动优化", "精准预测", "实时分析", "深度学习"]
                application_fields = ["医疗健康", "金融服务", "教育培训", "智能制造", "自动驾驶"]
                
                content = content_template.format(
                    company=company.name,
                    ai_concept=ai_concept.name,
                    feature1=random.choice(features),
                    feature2=random.choice(features),
                    feature3=random.choice(features),
                    timeframe="2-3年",
                    application_field=random.choice(application_fields),
                    launch_time="明年第一季度",
                    technical_advantage="显著提升计算效率",
                    performance_improvement="5-10",
                    application_scenario="大规模数据处理",
                    target_industry=random.choice(application_fields),
                    company2=company2.name if "{company2}" in content_template else "",
                    field1="算法研发",
                    field2="产品应用",
                    cooperation_area1="技术研发",
                    cooperation_area2="市场推广",
                    cooperation_area3="标准制定",
                    event_name="全球人工智能"
                )
                
                # 生成发布时间（最近一年内随机）
                publish_time = datetime.now() - timedelta(days=random.randint(1, 365))
                
                # 创建新闻事件
                news_event = await news_repo.create(
                    title=title,
                    content=content,
                    source=random.choice(self.news_sources),
                    publish_time=publish_time
                )
                
                # 关联相关实体
                await news_repo.add_entity_relation(news_event.id, company.id)
                await news_repo.add_entity_relation(news_event.id, ai_concept.id)
                
                # 随机添加更多相关实体
                if random.random() > 0.5 and len(entities) > 2:
                    extra_entity = random.choice([e for e in entities if e.id not in [company.id, ai_concept.id]])
                    await news_repo.add_entity_relation(news_event.id, extra_entity.id)
                
                news_events.append(news_event)
                logger.info(f"创建新闻: {title[:50]}...")
            
            await session.flush()
        
        logger.info(f"新闻生成完成，共创建 {len(news_events)} 条新闻")
        return news_events
    
    async def generate_vector_embeddings(self, news_events: list):
        """为新闻生成向量嵌入"""
        logger.info(f"开始为 {len(news_events)} 条新闻生成向量嵌入...")
        
        try:
            # 批量生成嵌入
            texts = [f"{news.title} {news.content[:200]}" for news in news_events]
            embeddings = await self.embedding_service.generate_embeddings(texts)
            
            # 存储到向量数据库
            for i, news in enumerate(news_events):
                vector_id = await self.hybrid_store.add_news_event(
                    news_id=news.id,
                    title=news.title,
                    content=news.content,
                    embedding=embeddings[i],
                    metadata={
                        "source": news.source,
                        "publish_time": news.publish_time.isoformat() if news.publish_time else None,
                        "entities": [e.name for e in news.entities] if hasattr(news, 'entities') else []
                    }
                )
                
                # 更新新闻的向量ID
                news.vector_id = vector_id
                logger.info(f"生成向量嵌入: {news.title[:30]}...")
            
            await self.session.flush()
            logger.info("向量嵌入生成完成")
            
        except Exception as e:
            logger.error(f"生成向量嵌入失败: {e}")
            # 不中断测试，继续执行
    
    async def generate_all_test_data(self):
        """生成所有测试数据"""
        logger.info("开始生成完整的测试数据...")
        
        try:
            # 生成实体
            entities = await self.generate_entities(20)
            
            # 生成关系
            relations = await self.generate_relations(entities)
            
            # 生成新闻事件
            news_events = await self.generate_news_events(entities, 50)
            
            # 生成向量嵌入（暂时注释掉）
            # await self.generate_vector_embeddings(news_events)
            
            logger.info("测试数据生成完成！")
            logger.info(f"实体数量: {len(entities)}")
            logger.info(f"关系数量: {len(relations)}")
            logger.info(f"新闻数量: {len(news_events)}")
            
            return {
                "entities": entities,
                "relations": relations,
                "news_events": news_events
            }
            
        except Exception as e:
            logger.error(f"生成测试数据时出错: {e}")
            raise


async def main():
    """主函数"""
    print("🚀 开始生成测试数据...")
    
    # 初始化数据库配置
    from app.database.core import DatabaseConfig
    from app.database.manager import init_database
    
    # 初始化数据库管理器
    config = DatabaseConfig()
    db_manager = init_database(config)
    
    # 创建数据生成器
    generator = TestDataGenerator(db_manager)
    
    try:
        # 生成测试数据
        result = await generator.generate_all_test_data()
        
        logger.info("✅ 测试数据生成成功")
        logger.info(f"📊 数据概览: {result}")
        
    except Exception as e:
        logger.error(f"❌ 程序执行失败: {e}")
        logger.error(traceback.format_exc())
        return 1
    finally:
        # 清理资源
        if 'db_manager' in locals():
            await db_manager.close()


if __name__ == "__main__":
    asyncio.run(main())