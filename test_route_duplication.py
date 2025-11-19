#!/usr/bin/env python3
"""
测试路由是否存在重复定义
"""

from fastapi import FastAPI
from kg.api import include_routers

def test_route_duplication():
    """测试路由是否存在重复定义"""
    app = FastAPI()
    
    try:
        include_routers(app)
        print("✓ 路由注册成功，没有重复定义")
    except AssertionError as e:
        print(f"✗ 路由存在重复定义: {e}")
        return False
    except Exception as e:
        print(f"✗ 路由注册失败: {e}")
        return False
    
    # 打印所有路由
    print("\n所有注册的路由:")
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            methods = ','.join(route.methods)
            print(f"  {methods.ljust(15)} {route.path}")
    
    return True

if __name__ == "__main__":
    test_route_duplication()