import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from unittest import TestCase
from fastapi import APIRouter
from kg.api.base_router import BaseRouter
from kg.api.base_router import global_route_registry, global_duplicate_routes, reset_global_route_registry


class TestRouterDuplication(TestCase):
    """
    测试重复路由检测和删除功能
    """
    
    def setUp(self):
        """测试前重置全局注册表"""
        reset_global_route_registry()
        
    def tearDown(self):
        """测试后重置全局注册表"""
        reset_global_route_registry()
        
    def test_internal_duplicate_routes(self):
        """
        测试同一路由类内部的重复路由检测
        """
        # 创建一个路由类，定义两个相同的路由
        class TestRouter(BaseRouter):
            def __init__(self):
                super().__init__(prefix="/test", tags=["test"])
                # 定义两个相同的GET路由
                self.router.get("/items")(self.get_items)
                self.router.get("/items")(self.get_items_duplicate)
            
            async def get_items(self):
                return {"message": "get items"}
            
            async def get_items_duplicate(self):
                return {"message": "get items duplicate"}
        
        # 创建路由实例
        test_router = TestRouter()
        router = test_router.router
        
        # 检测重复路由
        duplicates = test_router.detect_and_remove_duplicates()
        
        # 验证内部重复路由被检测到
        self.assertIn("internal_duplicates", duplicates)
        self.assertIn("GET", duplicates["internal_duplicates"])
        self.assertIn("/test/items", duplicates["internal_duplicates"]["GET"])
        
        # 验证只有一个路由被保留
        self.assertEqual(len(router.routes), 1)
    
    def test_cross_router_duplicates(self):
        """
        测试跨路由类的重复路由检测
        """
        # 创建第一个路由类
        class TestRouter1(BaseRouter):
            def __init__(self):
                super().__init__(prefix="/test", tags=["test1"])
                self.router.get("/items")(self.get_items)
            
            async def get_items(self):
                return {"message": "get items from router1"}
        
        # 创建第二个路由类
        class TestRouter2(BaseRouter):
            def __init__(self):
                super().__init__(prefix="/test", tags=["test2"])
                self.router.get("/items")(self.get_items)
            
            async def get_items(self):
                return {"message": "get items from router2"}
        
        # 创建路由实例
        router1 = TestRouter1()
        router2 = TestRouter2()
        
        # 获取路由
        router1_instance = router1.router
        router2_instance = router2.router
        
        # 验证全局重复路由被检测到
        self.assertGreater(len(global_duplicate_routes), 0)
        
        # 验证两个路由实例都有相同的路径
        self.assertEqual(len(router1_instance.routes), 1)
        self.assertEqual(len(router2_instance.routes), 1)
    
    def test_remove_global_duplicates(self):
        """
        测试全局重复路由移除功能
        """
        from kg.api.base_router import remove_global_duplicate_routes
        
        # 创建第一个路由类
        class TestRouter1(BaseRouter):
            def __init__(self):
                super().__init__(prefix="/test", tags=["test1"])
                self.router.get("/items")(self.get_items)
            
            async def get_items(self):
                return {"message": "get items from router1"}
        
        # 创建第二个路由类
        class TestRouter2(BaseRouter):
            def __init__(self):
                super().__init__(prefix="/test", tags=["test2"])
                self.router.get("/items")(self.get_items)
            
            async def get_items(self):
                return {"message": "get items from router2"}
        
        # 创建路由实例
        router1 = TestRouter1()
        router2 = TestRouter2()
        
        # 获取路由
        router1_instance = router1.router
        router2_instance = router2.router
        
        # 移除重复路由
        removed_count = remove_global_duplicate_routes()
        
        # 验证至少有一个路由被移除
        self.assertGreater(removed_count, 0)
        
        # 验证只有一个路由实例保留了路由
        total_routes = len(router1_instance.routes) + len(router2_instance.routes)
        self.assertEqual(total_routes, 1)
    
    def test_duplicate_routes_with_different_methods(self):
        """
        测试不同HTTP方法的路由不算重复
        """
        class TestRouter(BaseRouter):
            def __init__(self):
                super().__init__(prefix="/test", tags=["test"])
                self.router.get("/items")(self.get_items)
                self.router.post("/items")(self.create_item)
            
            async def get_items(self):
                return {"message": "get items"}
            
            async def create_item(self):
                return {"message": "create item"}
        
        # 创建路由实例
        test_router = TestRouter()
        router = test_router.router
        
        # 检测重复路由
        duplicates = test_router.detect_and_remove_duplicates()
        
        # 验证没有重复路由
        self.assertEqual(len(duplicates["internal_duplicates"]), 0)
        self.assertEqual(len(router.routes), 2)
    
    def test_duplicate_routes_with_different_prefixes(self):
        """
        测试不同前缀的路由不算重复
        """
        # 创建第一个路由类
        class TestRouter1(BaseRouter):
            def __init__(self):
                super().__init__(prefix="/test1", tags=["test1"])
                self.router.get("/items")(self.get_items)
            
            async def get_items(self):
                return {"message": "get items from router1"}
        
        # 创建第二个路由类
        class TestRouter2(BaseRouter):
            def __init__(self):
                super().__init__(prefix="/test2", tags=["test2"])
                self.router.get("/items")(self.get_items)
            
            async def get_items(self):
                return {"message": "get items from router2"}
        
        # 创建路由实例
        router1 = TestRouter1()
        router2 = TestRouter2()
        
        # 获取路由
        router1_instance = router1.router
        router2_instance = router2.router
        
        # 验证没有全局重复路由
        self.assertEqual(len(global_duplicate_routes), 0)
        
        # 验证两个路由实例都有自己的路由
        self.assertEqual(len(router1_instance.routes), 1)
        self.assertEqual(len(router2_instance.routes), 1)

if __name__ == "__main__":
    import unittest
    unittest.main()