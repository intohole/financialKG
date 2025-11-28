#!/usr/bin/env python3
"""
简单的知识图谱内容处理路由测试
"""

import requests
import json

# API端点
BASE_URL = "http://localhost:8001"
PROCESS_CONTENT_ENDPOINT = f"{BASE_URL}/api/kg/process-content"

def test_process_content():
    """测试内容处理功能"""
    print("测试知识图谱内容处理路由...")
    print("=" * 60)
    
    # 测试数据
    test_content = "苹果公司发布了新款iPhone 15。"
    
    data = {
        "content": test_content,
        "content_id": "simple_test"
    }
    
    try:
        response = requests.post(PROCESS_CONTENT_ENDPOINT, json=data, timeout=60)
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 请求成功!")
            print(f"分类: {result.get('category', '未知')}")
            print(f"提取实体数量: {len(result.get('entities', []))}")
            print(f"提取关系数量: {len(result.get('relations', []))}")
            
            if result.get('entities'):
                print("\n主要实体:")
                for entity in result['entities'][:3]:  # 显示前3个实体
                    print(f"  - {entity.get('name', '未知')} ({entity.get('type', '未知')}): {entity.get('description', '无描述')[:50]}...")
            
            if result.get('relations'):
                print("\n主要关系:")
                for relation in result['relations'][:3]:  # 显示前3个关系
                    print(f"  - {relation.get('source', '未知')} -> {relation.get('relation', '未知')} -> {relation.get('target', '未知')}")
            
            if result.get('metadata'):
                print("\n元数据:")
                metadata = result['metadata']
                for key, value in metadata.items():
                    print(f"  - {key}: {value}")
            
            return True
        else:
            print(f"❌ 请求失败!")
            print(f"错误信息: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时!")
        return False
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

if __name__ == "__main__":
    print("知识图谱内容处理路由简单测试")
    print("=" * 60)
    
    # 测试服务健康状态
    try:
        health_response = requests.get(BASE_URL, timeout=10)
        if health_response.status_code == 200:
            service_info = health_response.json()
            print(f"✅ 服务运行正常: {service_info.get('message', '未知服务')}")
        else:
            print(f"❌ 服务状态异常: {health_response.status_code}")
            exit(1)
    except Exception as e:
        print(f"❌ 无法连接服务: {e}")
        exit(1)
    
    # 测试内容处理
    success = test_process_content()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 测试完成 - 知识图谱内容处理路由运行正常!")
    else:
        print("❌ 测试失败 - 需要检查配置和日志")