#!/usr/bin/env python3
"""
KG核心实现的测试脚本
支持直接运行和详细日志输出
"""

import asyncio
import logging
import sys
import traceback
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.kg_core_impl import KGCoreImplService
from app.config.config_manager import ConfigManager

# 配置详细日志
logging.basicConfig(
    level=logging.INFO,  # 使用INFO级别，更简洁
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_debug.log', mode='w', encoding='utf-8')  # 同时输出到文件
    ]
)
logger = logging.getLogger(__name__)


async def test_process_content():
    """测试KG核心处理功能"""
    print("=== KG核心实现测试 ===")
    print("本脚本可直接运行，无需调试器")
    print()
    
    # 步骤1: 初始化配置管理器
    print("步骤1: 初始化配置管理器...")
    try:
        config_manager = ConfigManager()
        print("✓ 配置管理器初始化完成")
        print(f"  配置信息: {type(config_manager)}")
    except Exception as e:
        print(f"✗ 配置管理器初始化失败: {e}")
        traceback.print_exc()
        return False
    
    # 步骤2: 创建KG核心服务
    print("\n步骤2: 创建KG核心服务...")
    try:
        kg_service = KGCoreImplService(auto_init_store=False)
        kg_service.config = config_manager
        print("✓ KG核心服务创建完成")
        print(f"  服务类型: {type(kg_service)}")
        print(f"  自动初始化存储: {hasattr(kg_service, 'store') and kg_service.store is not None}")
    except Exception as e:
        print(f"✗ KG核心服务创建失败: {e}")
        traceback.print_exc()
        return False
    
    # 步骤3: 准备测试内容
    print("\n步骤3: 准备测试内容...")
    test_content = """
    苹果公司(Apple Inc.)是一家美国跨国科技公司，总部位于加利福尼亚州库比蒂诺。
    公司由史蒂夫·乔布斯、史蒂夫·沃兹尼亚克和罗纳德·韦恩于1976年创立。
    现任CEO是蒂姆·库克，他于2011年接替乔布斯担任此职位。
    苹果公司的主要产品包括iPhone智能手机、iPad平板电脑、Mac电脑等。
    iPhone是苹果公司最成功的消费电子产品，自2007年发布以来已经售出数十亿部。
    """
    print(f"✓ 测试内容准备完成")
    print(f"  内容长度: {len(test_content)} 字符")
    print(f"  内容预览: {test_content[:100]}...")
    
    # 步骤4: 初始化存储
    print("\n步骤4: 初始化存储...")
    try:
        print("正在调用 kg_service.initialize()...")
        await kg_service.initialize()
        print("✓ 存储初始化完成")
        print(f"  存储类型: {type(kg_service.store)}")
        print(f"  存储状态: {'已初始化' if kg_service.store else '未初始化'}")
    except Exception as e:
        print(f"✗ 存储初始化失败: {e}")
        print("详细错误信息:")
        traceback.print_exc()
        return False
    
    # 步骤5: 测试参数验证
    print("\n步骤5: 测试参数验证...")
    
    # 测试空内容
    print("  测试空内容验证...")
    try:
        await kg_service.process_content("")
        print("  ✗ 空内容验证失败 - 应该抛出ValueError")
    except ValueError as e:
        print(f"  ✓ 空内容验证通过: {e}")
    except Exception as e:
        print(f"  ✗ 空内容验证异常: {e}")
        traceback.print_exc()
    
    # 测试空白内容
    print("  测试空白内容验证...")
    try:
        await kg_service.process_content("   \n\t  ")
        print("  ✗ 空白内容验证失败 - 应该抛出ValueError")
    except ValueError as e:
        print(f"  ✓ 空白内容验证通过: {e}")
    except Exception as e:
        print(f"  ✗ 空白内容验证异常: {e}")
        traceback.print_exc()
    
    # 步骤6: 测试核心处理逻辑
    print("\n步骤6: 测试核心处理逻辑...")
    try:
        print("正在调用 kg_service.process_content(test_content)...")
        result = await kg_service.process_content(test_content)
        
        print("✓ 内容处理完成")
        print(f"  处理结果类型: {type(result)}")
        print(f"  处理结果状态: {'成功' if result else '失败'}")
        
        if result:
            print(f"  实体数量: {len(result.entities) if hasattr(result, 'entities') else 0}")
            print(f"  关系数量: {len(result.relations) if hasattr(result, 'relations') else 0}")
            print(f"  分类信息: {result.category if hasattr(result, 'category') else '无'}")
            
            # 详细输出实体信息
            if hasattr(result, 'entities') and result.entities:
                print("\n  提取的实体:")
                for i, entity in enumerate(result.entities[:5]):  # 只显示前5个
                    print(f"    {i+1}. {entity.name} ({entity.type})")
                if len(result.entities) > 5:
                    print(f"    ... 还有 {len(result.entities) - 5} 个实体")
            
            # 详细输出关系信息
            if hasattr(result, 'relations') and result.relations:
                print("\n  提取的关系:")
                for i, relation in enumerate(result.relations[:5]):  # 只显示前5个
                    print(f"    {i+1}. {relation.subject} -> {relation.predicate} -> {relation.object}")
                if len(result.relations) > 5:
                    print(f"    ... 还有 {len(result.relations) - 5} 个关系")
        
        return True
        
    except Exception as e:
        print(f"✗ 内容处理失败: {e}")
        print("详细错误信息:")
        traceback.print_exc()
        return False



def run_test():
    """运行测试的主函数"""
    print("=" * 60)
    print("KG核心实现测试脚本")
    print("=" * 60)
    print()
    print("运行提示:")
    print("1. 直接运行: python test_kg_core_debug.py")
    print("2. 查看详细日志: 检查 test_debug.log 文件")
    print()
    
    try:
        # 运行异步测试
        success = asyncio.run(test_process_content())
        
        print("\n" + "=" * 60)
        if success:
            print("✓ 测试完成 - 所有步骤执行成功")
            print("✓ 详细日志已保存到 test_debug.log")
        else:
            print("✗ 测试失败 - 某些步骤执行失败")
            print("✗ 请检查上面的错误信息和 test_debug.log")
        
        return success
        
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        return False
    except Exception as e:
        print(f"\n✗ 测试运行失败: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(test_process_content())
    sys.exit(0 if success else 1)