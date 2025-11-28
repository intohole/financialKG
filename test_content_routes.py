#!/usr/bin/env python3
"""
测试知识图谱内容处理路由

测试新创建的 /api/kg/process-content 端点
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any

# 测试配置
BASE_URL = "http://localhost:8001"
PROCESS_CONTENT_ENDPOINT = f"{BASE_URL}/api/kg/process-content"

# 测试内容示例
test_contents = [
    "苹果公司发布了新款iPhone 15。",
    "人工智能技术在医疗领域的应用越来越广泛。",
    "全球气候变化对农业生产产生了重大影响。"
]


async def test_process_content_endpoint():
    """测试内容处理端点"""
    print("开始测试知识图谱内容处理路由...")
    
    async with aiohttp.ClientSession() as session:
        for i, content in enumerate(test_contents, 1):
            print(f"\n{'='*60}")
            print(f"测试 {i}: 处理内容 (长度: {len(content)} 字符)")
            print(f"{'='*60}")
            
            try:
                # 准备请求数据
                data = {
                    "content": content.strip(),
                    "content_id": f"test_content_{i}"
                }
                
                # 发送POST请求
                async with session.post(
                    PROCESS_CONTENT_ENDPOINT,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=300)  # 5分钟超时
                ) as response:
                    
                    print(f"状态码: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        print("✅ 请求成功!")
                        
                        # 解析响应结果
                        entities = result.get("entities", [])
                        relations = result.get("relations", [])
                        metadata = result.get("metadata", {})
                        category = result.get("category")
                        
                        print(f"分类: {category}")
                        print(f"提取实体数量: {len(entities)}")
                        print(f"提取关系数量: {len(relations)}")
                        
                        if entities:
                            print("\n主要实体:")
                            for entity in entities[:5]:  # 只显示前5个实体
                                print(f"  - {entity.get('name')} ({entity.get('type')}): {entity.get('description', '无描述')}")
                        
                        if relations:
                            print("\n主要关系:")
                            for relation in relations[:5]:  # 只显示前5个关系
                                print(f"  - {relation.get('subject')} -> {relation.get('predicate')} -> {relation.get('object')}")
                        
                        if metadata:
                            print(f"\n元数据:")
                            print(f"  - 内容ID: {metadata.get('content_id')}")
                            print(f"  - 内容长度: {metadata.get('content_length')}")
                            print(f"  - 处理时间戳: {metadata.get('extraction_timestamp')}")
                            if metadata.get('summary'):
                                print(f"  - 摘要: {metadata['summary']}")
                        
                    else:
                        error_text = await response.text()
                        print(f"❌ 请求失败!")
                        print(f"错误信息: {error_text}")
                        
            except asyncio.TimeoutError:
                print(f"❌ 请求超时!")
            except Exception as e:
                print(f"❌ 测试失败: {str(e)}")
                import traceback
                traceback.print_exc()


async def test_health_check():
    """测试服务健康状态"""
    print("\n测试服务健康状态...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/") as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ 服务运行正常: {result.get('message', 'Unknown')}")
                    return True
                else:
                    print(f"❌ 服务状态异常: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ 无法连接服务: {str(e)}")
        return False


async def main():
    """主测试函数"""
    print("知识图谱内容处理路由测试")
    print("=" * 60)
    
    # 检查服务健康状态
    if not await test_health_check():
        print("\n服务未运行，请先启动服务:")
        print("cd /Users/intoblack/workspace/graph && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload")
        return
    
    # 测试内容处理端点
    await test_process_content_endpoint()
    
    print(f"\n{'='*60}")
    print("测试完成!")


if __name__ == "__main__":
    asyncio.run(main())