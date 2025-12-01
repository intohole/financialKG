#!/usr/bin/env python3
"""
带测试数据的新闻搜索功能测试
先生成测试数据，然后进行功能测试
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from generate_test_data import TestDataGenerator, main as generate_data
from test_news_search import NewsSearchTester, main as test_search


async def run_full_test():
    """运行完整的测试流程"""
    print("🚀 开始完整的新闻搜索功能测试...")
    print("=" * 60)
    
    # 步骤1: 生成测试数据
    print("\n📊 步骤1: 生成测试数据")
    print("-" * 30)
    
    try:
        await generate_data()
        print("✅ 测试数据生成完成")
    except Exception as e:
        print(f"❌ 测试数据生成失败: {e}")
        return False
    
    # 步骤2: 运行功能测试
    print("\n🔍 步骤2: 运行功能测试")
    print("-" * 30)
    
    try:
        # 等待一下确保数据完全写入
        await asyncio.sleep(2)
        
        # 运行测试
        await test_search()
        print("✅ 功能测试完成")
        return True
    except Exception as e:
        print(f"❌ 功能测试失败: {e}")
        return False


async def run_individual_tests():
    """运行单独的测试用例"""
    print("\n🧪 运行单独测试用例")
    print("=" * 50)
    
    from app.database.manager import DatabaseManager
    from app.database.repositories import NewsEventRepository
    
    db_manager = DatabaseManager()
    
    async with db_manager.get_session() as session:
        news_repo = NewsEventRepository(session)
        
        # 测试1: 检查新闻总数
        print("\n📈 测试1: 检查新闻总数")
        try:
            from sqlalchemy import select, func
            from app.database.models import NewsEvent
            
            stmt = select(func.count(NewsEvent.id))
            result = await session.execute(stmt)
            total_news = result.scalar()
            print(f"数据库中新闻总数: {total_news}")
            
            if total_news > 0:
                print("✅ 新闻数据存在")
            else:
                print("⚠️  未找到新闻数据")
                
        except Exception as e:
            print(f"❌ 检查新闻总数失败: {e}")
        
        # 测试2: 检查最近新闻
        print("\n📅 测试2: 检查最近新闻")
        try:
            recent_news = await news_repo.get_recent_events(days=30, limit=5)
            print(f"最近30天的新闻数量: {len(recent_news)}")
            
            if recent_news:
                print("最新5条新闻:")
                for i, news in enumerate(recent_news, 1):
                    print(f"  {i}. {news.title}")
                    print(f"     来源: {news.source}, 发布时间: {news.publish_time}")
            else:
                print("⚠️  未找到最近新闻")
                
        except Exception as e:
            print(f"❌ 检查最近新闻失败: {e}")
        
        # 测试3: 搜索测试
        print("\n🔎 测试3: 搜索功能测试")
        try:
            search_results = await news_repo.search_by_content("人工智能", limit=5)
            print(f"搜索'人工智能'结果数量: {len(search_results)}")
            
            if search_results:
                print("搜索结果:")
                for i, news in enumerate(search_results, 1):
                    print(f"  {i}. {news.title}")
            else:
                print("⚠️  未找到相关新闻")
                
        except Exception as e:
            print(f"❌ 搜索功能测试失败: {e}")


async def main():
    """主函数"""
    print("🎯 新闻搜索功能完整测试")
    print("=" * 60)
    
    # 询问用户选择
    print("请选择测试模式:")
    print("1. 完整测试 (生成数据 + 功能测试)")
    print("2. 仅功能测试 (假设数据已存在)")
    print("3. 单独测试用例")
    print("4. 仅生成测试数据")
    
    choice = input("\n请输入选择 (1-4): ").strip()
    
    if choice == "1":
        success = await run_full_test()
    elif choice == "2":
        print("\n🔍 运行功能测试 (假设数据已存在)")
        await test_search()
        success = True
    elif choice == "3":
        await run_individual_tests()
        success = True
    elif choice == "4":
        print("\n📊 仅生成测试数据")
        await generate_data()
        success = True
    else:
        print("❌ 无效选择")
        success = False
    
    print(f"\n{'='*60}")
    if success:
        print("✅ 测试完成！")
    else:
        print("❌ 测试失败！")
    
    return success


if __name__ == "__main__":
    asyncio.run(main())