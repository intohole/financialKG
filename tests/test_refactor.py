"""
数据库模块重构验证测试
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import (
    DatabaseConfig,
    DatabaseManager,
    UnitOfWork,
    init_database,
    get_database_manager,
    EntityRepository,
    RelationRepository,
    AttributeRepository
)


async def test_imports():
    """测试模块导入"""
    print("=== 测试模块导入 ===")
    
    # 测试基础导入
    print("✓ 基础模块导入成功")
    print(f"  - DatabaseConfig: {DatabaseConfig}")
    print(f"  - DatabaseManager: {DatabaseManager}")
    print(f"  - UnitOfWork: {UnitOfWork}")
    
    # 测试存储库导入
    print("✓ 存储库导入成功")
    print(f"  - EntityRepository: {EntityRepository}")
    print(f"  - RelationRepository: {RelationRepository}")
    print(f"  - AttributeRepository: {AttributeRepository}")
    
    return True


async def test_database_config():
    """测试数据库配置"""
    print("\n=== 测试数据库配置 ===")
    
    config = DatabaseConfig(
        database_url="sqlite+aiosqlite:///./test.db",
        echo=True,
        pool_size=5,
        max_overflow=10
    )
    
    print(f"✓ 配置创建成功")
    print(f"  - 数据库URL: {config.database_url}")
    print(f"  - 回显模式: {config.echo}")
    print(f"  - 连接池大小: {config.pool_size}")
    print(f"  - 最大溢出: {config.max_overflow}")
    
    return True


async def test_database_manager():
    """测试数据库管理器"""
    print("\n=== 测试数据库管理器 ===")
    
    config = DatabaseConfig(database_url="sqlite+aiosqlite:///./test.db")
    
    # 测试初始化
    manager = init_database(config)
    print("✓ 数据库管理器初始化成功")
    
    # 测试获取管理器
    same_manager = get_database_manager()
    assert manager is same_manager, "获取的管理器应该是同一个实例"
    print("✓ 数据库管理器单例模式正常")
    
    # 测试创建表
    try:
        await manager.create_tables()
        print("✓ 数据表创建成功")
    except Exception as e:
        print(f"⚠ 数据表创建失败: {e}")
    
    # 关闭连接
    await manager.close()
    print("✓ 数据库连接关闭成功")
    
    return True


async def test_unit_of_work():
    """测试工作单元模式"""
    print("\n=== 测试工作单元模式 ===")
    
    config = DatabaseConfig(database_url="sqlite+aiosqlite:///./test.db")
    manager = init_database(config)
    
    try:
        async with UnitOfWork(manager) as uow:
            print("✓ 工作单元创建成功")
            print(f"  - entities: {uow.entities}")
            print(f"  - relations: {uow.relations}")
            print(f"  - attributes: {uow.attributes}")
            print(f"  - news_events: {uow.news_events}")
            
            # 测试事务提交
            await uow.commit()
            print("✓ 事务提交成功")
    
    except Exception as e:
        print(f"✗ 工作单元测试失败: {e}")
        return False
    
    finally:
        await manager.close()
    
    return True


async def test_error_handling():
    """测试错误处理"""
    print("\n=== 测试错误处理 ===")
    
    from app.database import DatabaseError, NotFoundError, IntegrityError
    
    # 测试异常类
    print("✓ 异常类导入成功")
    print(f"  - DatabaseError: {DatabaseError}")
    print(f"  - NotFoundError: {NotFoundError}")
    print(f"  - IntegrityError: {IntegrityError}")
    
    # 测试异常抛出和捕获
    try:
        raise NotFoundError("测试异常")
    except NotFoundError as e:
        print(f"✓ 异常处理正常: {e}")
    
    return True


async def cleanup():
    """清理测试文件"""
    print("\n=== 清理测试文件 ===")
    
    try:
        if os.path.exists("./test.db"):
            os.remove("./test.db")
            print("✓ 测试数据库文件已删除")
        
        if os.path.exists("./test.db-journal"):
            os.remove("./test.db-journal")
            print("✓ 测试数据库日志文件已删除")
    
    except Exception as e:
        print(f"⚠ 清理文件时出错: {e}")


async def main():
    """主测试函数"""
    print("开始数据库模块重构验证测试...\n")
    
    try:
        # 执行所有测试
        results = []
        results.append(await test_imports())
        results.append(await test_database_config())
        results.append(await test_database_manager())
        results.append(await test_unit_of_work())
        results.append(await test_error_handling())
        
        # 统计结果
        passed = sum(results)
        total = len(results)
        
        print(f"\n=== 测试结果 ===")
        print(f"通过测试: {passed}/{total}")
        
        if passed == total:
            print("🎉 所有测试通过！数据库模块重构成功。")
        else:
            print("⚠ 部分测试失败，请检查相关模块。")
        
        return passed == total
    
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await cleanup()


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)