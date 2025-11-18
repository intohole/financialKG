import requests
import json

# 测试去重操作
def test_deduplication_endpoints():
    base_url = "http://localhost:8000/api/v1"
    
    # 1. 测试完整去重流程（使用Query参数而非请求体）
    url = f"{base_url}/deduplicate/full"
    # 使用查询参数而不是请求体
    params = {
        "similarity_threshold": 0.8,
        "batch_size": 100,
        "skip_entities": False,
        "skip_relations": False
    }
    print(f"\n测试完整去重流程: {url}")
    try:
        response = requests.post(url, params=params)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.json()}")
    except Exception as e:
        print(f"请求异常: {e}")
    
    # 2. 测试实体去重（添加limit参数）
    url = f"{base_url}/entities/deduplicate"
    headers = {"Content-Type": "application/json"}
    data = {
        "entity_type": "公司",  # 使用entity_type而非entity_types
        "similarity_threshold": 0.85,
        "batch_size": 100,
        "limit": 500  # 添加limit参数以匹配router实现
    }
    print(f"\n测试实体去重: {url}")
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.json()}")
    except Exception as e:
        print(f"请求异常: {e}")
    
    # 3. 测试关系去重（添加entity_id和limit参数）
    url = f"{base_url}/relations/deduplicate"
    data = {
        "entity_id": 1,  # 添加entity_id参数以匹配router实现
        "relation_type": "投资",  # 使用relation_type而非relation_types
        "similarity_threshold": 0.8,
        "batch_size": 100,
        "limit": 500  # 添加limit参数以匹配router实现
    }
    print(f"\n测试关系去重: {url}")
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.json()}")
    except Exception as e:
        print(f"请求异常: {e}")

if __name__ == "__main__":
    print("开始测试去重API端点...")
    test_deduplication_endpoints()
    print("测试完成。")
