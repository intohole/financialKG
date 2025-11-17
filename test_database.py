import asyncio
import os
import sys
from datetime import datetime

# 将项目根目录添加到Python路径
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from kg.database.connection import get_db_session
from kg.database.models import Entity, Relation, News, EntityNews, EntityGroup, RelationGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

async def create_tables():
    """创建数据库表"""
    from kg.database.connection import get_db_manager
    db_manager = get_db_manager()
    await db_manager._create_tables()
    print("✅ 成功创建数据库表")

async def test_database():
    print("=== 知识图谱数据库测试开始 ===")
    
    # 创建数据库表
    await create_tables()
    
    # 测试数据库连接
    async for session in get_db_session():
        assert isinstance(session, AsyncSession), "会话类型错误"
        print("✅ 成功获取异步数据库会话")
    
    # 测试实体相关功能
    await test_entity_operations()
    
    # 测试关系相关功能
    await test_relation_operations()
    
    # 测试新闻相关功能
    await test_news_operations()
    
    # 测试实体-新闻关联功能
    await test_entity_news_operations()
    
    # 测试实体分组功能
    await test_entity_group_operations()
    
    # 测试关系分组功能
    await test_relation_group_operations()
    
    print("=== 知识图谱数据库测试完成 ===")

async def test_entity_operations():
    print("\n--- 测试实体操作 ---")
    
    # 插入测试实体
    async for session in get_db_session():
        entity_data = {
            "name": "测试实体",
            "type": "test_type",
            "source": "test_source"
        }
        
        entity = Entity(**entity_data)
        session.add(entity)
        await session.commit()
        print("✅ 成功插入实体")
        
        # 查询实体
        retrieved_entity = await session.get(Entity, entity.id)
        assert retrieved_entity is not None
        assert retrieved_entity.name == "测试实体"
        print("✅ 成功查询实体")
        
        # 更新实体
        retrieved_entity.canonical_name = "测试实体规范名"
        await session.commit()
        updated_entity = await session.get(Entity, entity.id)
        assert updated_entity.canonical_name == "测试实体规范名"
        print("✅ 成功更新实体")
        
        # 删除实体
        await session.delete(updated_entity)
        await session.commit()
        deleted_entity = await session.get(Entity, entity.id)
        assert deleted_entity is None
        print("✅ 成功删除实体")

async def test_relation_operations():
    print("\n--- 测试关系操作 ---")
    
    async for session in get_db_session():
        # 创建两个实体用于测试关系
        entity1 = Entity(name="实体1", type="test_type", source="test_source")
        entity2 = Entity(name="实体2", type="test_type", source="test_source")
        session.add_all([entity1, entity2])
        await session.commit()
        
        # 插入关系
        relation_data = {
            "source_entity_id": entity1.id,
            "target_entity_id": entity2.id,
            "relation_type": "关联",
            "source": "test_source"
        }
        
        relation = Relation(**relation_data)
        session.add(relation)
        await session.commit()
        print("✅ 成功插入关系")
        
        # 查询关系
        retrieved_relation = await session.get(Relation, relation.id)
        assert retrieved_relation is not None
        assert retrieved_relation.relation_type == "关联"
        print("✅ 成功查询关系")
        
        # 更新关系
        retrieved_relation.canonical_relation = "关联规范名"
        retrieved_relation.weight = 0.8
        await session.commit()
        updated_relation = await session.get(Relation, relation.id)
        assert updated_relation.canonical_relation == "关联规范名"
        assert updated_relation.weight == 0.8
        print("✅ 成功更新关系")
        
        # 删除关系和测试实体
        await session.delete(updated_relation)
        await session.delete(entity1)
        await session.delete(entity2)
        await session.commit()
        print("✅ 成功删除关系和测试实体")

async def test_news_operations():
    print("\n--- 测试新闻操作 ---")
    
    async for session in get_db_session():
        # 插入新闻
        news_data = {
            "title": "测试新闻标题",
            "content": "测试新闻内容",
            "url": "http://test.com/news/1",
            "publish_time": datetime.utcnow(),
            "source": "test_source",
            "category": "test_category"
        }
        
        news = News(**news_data)
        session.add(news)
        await session.commit()
        print("✅ 成功插入新闻")
        
        # 查询新闻
        retrieved_news = await session.get(News, news.id)
        assert retrieved_news is not None
        assert retrieved_news.title == "测试新闻标题"
        print("✅ 成功查询新闻")
        
        # 更新新闻提取状态
        retrieved_news.extraction_status = "completed"
        retrieved_news.extracted_at = datetime.utcnow()
        await session.commit()
        updated_news = await session.get(News, news.id)
        assert updated_news.extraction_status == "completed"
        assert updated_news.extracted_at is not None
        print("✅ 成功更新新闻提取状态")
        
        # 删除新闻
        await session.delete(updated_news)
        await session.commit()
        deleted_news = await session.get(News, news.id)
        assert deleted_news is None
        print("✅ 成功删除新闻")

async def test_entity_news_operations():
    print("\n--- 测试实体-新闻关联操作 ---")
    
    async for session in get_db_session():
        # 创建测试实体和新闻
        entity = Entity(name="关联实体", type="test_type", source="test_source")
        news = News(title="关联新闻", content="关联新闻内容", source="test_source")
        session.add_all([entity, news])
        await session.commit()
        
        # 插入实体-新闻关联
        entity_news = EntityNews(entity_id=entity.id, news_id=news.id, context="测试上下文", occurrence_count=2)
        session.add(entity_news)
        await session.commit()
        print("✅ 成功插入实体-新闻关联")
        
        # 查询实体-新闻关联
        retrieved_relation = await session.get(EntityNews, entity_news.id)
        assert retrieved_relation is not None
        assert retrieved_relation.context == "测试上下文"
        assert retrieved_relation.occurrence_count == 2
        print("✅ 成功查询实体-新闻关联")
        
        # 删除关联及依赖项
        await session.delete(retrieved_relation)
        await session.delete(entity)
        await session.delete(news)
        await session.commit()
        print("✅ 成功删除实体-新闻关联")

async def test_entity_group_operations():
    print("\n--- 测试实体分组操作 ---")
    
    async for session in get_db_session():
        # 创建实体分组
        entity_group = EntityGroup(group_name="测试实体组", description="测试实体分组")
        session.add(entity_group)
        await session.commit()
        print("✅ 成功创建实体分组")
        
        # 创建实体并关联到分组
        entity = Entity(name="分组实体", type="test_type", source="test_source", entity_group_id=entity_group.id)
        session.add(entity)
        await session.commit()
        
        # 更新实体分组计数
        entity_group.entity_count += 1
        await session.commit()
        print("✅ 成功将实体关联到分组并更新计数")
        
        # 查询分组
        retrieved_group = await session.get(EntityGroup, entity_group.id)
        assert retrieved_group is not None
        assert retrieved_group.entity_count == 2
        print("✅ 成功查询实体分组")
        
        # 删除分组及实体
        await session.delete(entity)
        await session.delete(retrieved_group)
        await session.commit()
        print("✅ 成功删除实体分组")

async def test_relation_group_operations():
    print("\n--- 测试关系分组操作 ---")
    
    async for session in get_db_session():
        # 创建关系分组
        relation_group = RelationGroup(group_name="测试关系组", description="测试关系分组")
        session.add(relation_group)
        await session.commit()
        print("✅ 成功创建关系分组")
        
        # 查询关系分组
        retrieved_group = await session.get(RelationGroup, relation_group.id)
        assert retrieved_group is not None
        assert retrieved_group.group_name == "测试关系组"
        print("✅ 成功查询关系分组")
        
        # 删除关系分组
        await session.delete(retrieved_group)
        await session.commit()
        print("✅ 成功删除关系分组")

if __name__ == "__main__":
    asyncio.run(test_database())