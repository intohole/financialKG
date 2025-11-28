#!/usr/bin/env python3
"""
知识图谱查询路由测试脚本

测试KGQueryService的所有API端点，验证路由功能是否正常工作
"""

import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, Any, List

# 测试配置
BASE_URL = "http://localhost:8001"
TEST_TIMEOUT = 30.0

class KGRouteTester:
    """知识图谱路由测试器"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=TEST_TIMEOUT)
        self.test_results = []
    
    async def test_endpoint(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """测试单个端点"""
        url = f"{self.base_url}{endpoint}"
        start_time = datetime.now()
        
        try:
            response = await self.client.request(method, url, **kwargs)
            duration = (datetime.now() - start_time).total_seconds()
            
            result = {
                "endpoint": endpoint,
                "method": method,
                "status_code": response.status_code,
                "duration": duration,
                "success": response.status_code == 200,
                "response_data": response.json() if response.status_code == 200 else None,
                "error": response.text if response.status_code != 200 else None
            }
            
            self.test_results.append(result)
            return result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            result = {
                "endpoint": endpoint,
                "method": method,
                "status_code": 0,
                "duration": duration,
                "success": False,
                "response_data": None,
                "error": str(e)
            }
            self.test_results.append(result)
            return result
    
    async def test_entity_endpoints(self):
        """测试实体相关端点"""
        print("\n=== 测试实体相关端点 ===")
        
        # 测试获取实体列表
        print("1. 测试获取实体列表...")
        result = await self.test_endpoint("GET", "/api/kg/entities", params={"page": 1, "page_size": 10})
        print(f"   状态: {'✓' if result['success'] else '✗'} {result['status_code']} ({result['duration']:.2f}s)")
        
        if result['success'] and result['response_data'] and result['response_data']['items']:
            first_entity = result['response_data']['items'][0]
            entity_id = first_entity['id']
            
            # 测试获取实体详情
            print(f"2. 测试获取实体详情 (ID: {entity_id})...")
            detail_result = await self.test_endpoint("GET", f"/api/kg/entities/{entity_id}")
            print(f"   状态: {'✓' if detail_result['success'] else '✗'} {detail_result['status_code']} ({detail_result['duration']:.2f}s)")
            
            # 测试获取实体邻居网络
            print(f"3. 测试获取实体邻居网络 (ID: {entity_id})...")
            neighbors_result = await self.test_endpoint("GET", f"/api/kg/entities/{entity_id}/neighbors", params={"depth": 2})
            print(f"   状态: {'✓' if neighbors_result['success'] else '✗'} {neighbors_result['status_code']} ({neighbors_result['duration']:.2f}s)")
            
            # 测试获取实体关联新闻
            print(f"4. 测试获取实体关联新闻 (ID: {entity_id})...")
            news_result = await self.test_endpoint("GET", f"/api/kg/entities/{entity_id}/news", params={"page": 1, "page_size": 5})
            print(f"   状态: {'✓' if news_result['success'] else '✗'} {news_result['status_code']} ({news_result['duration']:.2f}s)")
    
    async def test_relation_endpoints(self):
        """测试关系相关端点"""
        print("\n=== 测试关系相关端点 ===")
        
        # 测试获取关系列表
        print("1. 测试获取关系列表...")
        result = await self.test_endpoint("GET", "/api/kg/relations", params={"page": 1, "page_size": 10})
        print(f"   状态: {'✓' if result['success'] else '✗'} {result['status_code']} ({result['duration']:.2f}s)")
    
    async def test_news_endpoints(self):
        """测试新闻相关端点"""
        print("\n=== 测试新闻相关端点 ===")
        
        # 首先获取一些新闻ID
        print("1. 获取实体关联新闻以测试新闻端点...")
        entities_result = await self.test_endpoint("GET", "/api/kg/entities", params={"page": 1, "page_size": 5})
        
        if entities_result['success'] and entities_result['response_data'] and entities_result['response_data']['items']:
            # 获取第一个实体的关联新闻
            first_entity = entities_result['response_data']['items'][0]
            entity_id = first_entity['id']
            
            news_result = await self.test_endpoint("GET", f"/api/kg/entities/{entity_id}/news", params={"page": 1, "page_size": 1})
            
            if news_result['success'] and news_result['response_data'] and news_result['response_data']['items']:
                first_news = news_result['response_data']['items'][0]
                news_id = first_news['id']
                
                # 测试获取新闻相关实体
                print(f"2. 测试获取新闻相关实体 (ID: {news_id})...")
                news_entities_result = await self.test_endpoint("GET", f"/api/kg/news/{news_id}/entities", params={"limit": 10})
                print(f"   状态: {'✓' if news_entities_result['success'] else '✗'} {news_entities_result['status_code']} ({news_entities_result['duration']:.2f}s)")
    
    async def test_common_news_endpoint(self):
        """测试多实体共同新闻端点"""
        print("\n=== 测试多实体共同新闻端点 ===")
        
        # 获取一些实体ID
        entities_result = await self.test_endpoint("GET", "/api/kg/entities", params={"page": 1, "page_size": 5})
        
        if entities_result['success'] and entities_result['response_data'] and len(entities_result['response_data']['items']) >= 2:
            entity_ids = [entity['id'] for entity in entities_result['response_data']['items'][:2]]
            
            print(f"1. 测试获取多实体共同新闻 (实体IDs: {entity_ids})...")
            result = await self.test_endpoint("POST", "/api/kg/entities/common-news", params={"entity_ids": entity_ids, "page": 1, "page_size": 10})
            print(f"   状态: {'✓' if result['success'] else '✗'} {result['status_code']} ({result['duration']:.2f}s)")
    
    async def test_statistics_endpoint(self):
        """测试统计端点"""
        print("\n=== 测试统计端点 ===")
        
        print("1. 测试获取知识图谱概览统计...")
        result = await self.test_endpoint("GET", "/api/kg/statistics/overview")
        print(f"   状态: {'✓' if result['success'] else '✗'} {result['status_code']} ({result['duration']:.2f}s)")
    
    async def test_error_handling(self):
        """测试错误处理"""
        print("\n=== 测试错误处理 ===")
        
        print("1. 测试错误处理端点...")
        result = await self.test_endpoint("GET", "/api/kg/test/error-handling")
        is_correct_error = result['status_code'] == 500
        print(f"   状态: {'✓' if is_correct_error else '✗'} {result['status_code']} (应该是500错误)")
        # 修正测试结果，让正确的错误处理显示为成功
        if is_correct_error:
            result['success'] = True
        
        print("2. 测试不存在的实体...")
        result = await self.test_endpoint("GET", "/api/kg/entities/99999")
        is_correct_error = result['status_code'] == 404
        print(f"   状态: {'✓' if is_correct_error else '✗'} {result['status_code']} (应该是404错误)")
        # 修正测试结果，让正确的错误处理显示为成功
        if is_correct_error:
            result['success'] = True
    
    async def test_search_and_filtering(self):
        """测试搜索和过滤功能"""
        print("\n=== 测试搜索和过滤功能 ===")
        
        # 测试实体搜索
        print("1. 测试实体搜索...")
        result = await self.test_endpoint("GET", "/api/kg/entities", params={"search": "公司", "page": 1, "page_size": 5})
        print(f"   状态: {'✓' if result['success'] else '✗'} {result['status_code']} ({result['duration']:.2f}s)")
        
        # 测试实体类型过滤
        print("2. 测试实体类型过滤...")
        result = await self.test_endpoint("GET", "/api/kg/entities", params={"entity_type": "公司", "page": 1, "page_size": 5})
        print(f"   状态: {'✓' if result['success'] else '✗'} {result['status_code']} ({result['duration']:.2f}s)")
        
        # 测试关系类型过滤
        print("3. 测试关系类型过滤...")
        result = await self.test_endpoint("GET", "/api/kg/relations", params={"relation_type": "投资", "page": 1, "page_size": 5})
        print(f"   状态: {'✓' if result['success'] else '✗'} {result['status_code']} ({result['duration']:.2f}s)")
    
    async def run_all_tests(self):
        """运行所有测试"""
        print(f"开始测试知识图谱查询路由...")
        print(f"基础URL: {self.base_url}")
        
        # 首先检查服务是否可用
        print("\n检查服务可用性...")
        health_result = await self.test_endpoint("GET", "/")
        if not health_result['success']:
            print(f"❌ 服务不可用: {health_result['error']}")
            return
        print("✓ 服务正常运行")
        
        # 运行所有测试
        await self.test_entity_endpoints()
        await self.test_relation_endpoints()
        await self.test_news_endpoints()
        await self.test_common_news_endpoint()
        await self.test_statistics_endpoint()
        await self.test_error_handling()
        await self.test_search_and_filtering()
        
        # 打印测试总结
        self.print_test_summary()
    
    def print_test_summary(self):
        """打印测试总结"""
        print("\n" + "="*60)
        print("测试总结")
        print("="*60)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - successful_tests
        
        print(f"总测试数: {total_tests}")
        print(f"成功: {successful_tests}")
        print(f"失败: {failed_tests}")
        print(f"成功率: {(successful_tests/total_tests)*100:.1f}%")
        
        # 平均响应时间
        avg_duration = sum(result['duration'] for result in self.test_results) / total_tests
        print(f"平均响应时间: {avg_duration:.2f}秒")
        
        # 失败的测试详情
        if failed_tests > 0:
            print("\n失败的测试:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['method']} {result['endpoint']}: {result['status_code']}")
                    if result['error']:
                        print(f"    错误: {result['error'][:100]}...")
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()


async def main():
    """主测试函数"""
    tester = KGRouteTester()
    
    try:
        await tester.run_all_tests()
    finally:
        await tester.close()


if __name__ == "__main__":
    # 运行测试
    asyncio.run(main())