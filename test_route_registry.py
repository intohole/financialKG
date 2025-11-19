#!/usr/bin/env python3
"""
测试路由注册表和路由对象
"""

from kg.api.base_router import global_route_registry, global_duplicate_routes, reset_global_route_registry
from kg.api.entities_router import EntityRouter, get_entities_router

def test_route_registry():
    print("重置全局路由注册表...")
    reset_global_route_registry()
    print("创建EntityRouter实例...")
    entity_router_instance = EntityRouter()
    router = entity_router_instance.router
    
    print(f"\n路由数量: {len(router.routes)}")
    
    print("\n路由详细信息:")
    for i, route in enumerate(router.routes):
        print(f"\n路由 #{i+1}:")
        print(f"  路径: {route.path}")
        print(f"  方法: {route.methods}")
        print(f"  端点: {route.endpoint.__name__}")
        print(f"  标签: {route.tags}")
        
    # 获取完整路由
    full_router = entity_router_instance.get_router()
    
    print(f"\n\n完整路由数量: {len(full_router.routes)}")
    
    print("\n完整路由详细信息:")
    for i, route in enumerate(full_router.routes):
        print(f"\n路由 #{i+1}:")
        print(f"  路径: {route.path}")
        print(f"  方法: {route.methods}")
        print(f"  端点: {route.endpoint.__name__}")
        print(f"  标签: {route.tags}")
    
    print(f"\n\n全局路由注册表大小: {len(global_route_registry)}")
    print(f"全局重复路由数量: {len(global_duplicate_routes)}")
    
    if global_duplicate_routes:
        print("\n全局重复路由详细信息:")
        for route_key, routes in global_duplicate_routes.items():
            print(f"\n路由键: {route_key}")
            for router_instance, route_info in routes:
                print(f"  路由来源: {router_instance.__class__.__name__}")
                print(f"  路径: {route_info['path']}")
                print(f"  方法: {route_info['method']}")
                print(f"  端点: {route_info['endpoint']}")

if __name__ == "__main__":
    test_route_registry()