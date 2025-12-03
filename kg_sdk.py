#!/usr/bin/env python3
"""
Knowledge Graph SDK

一个简单的Python SDK，用于调用知识图谱API，支持process_content接口
依赖：requests库
"""

from typing import Dict, Any

import requests


class KGSDK:
    """知识图谱SDK类
    
    简单易用的SDK，用于调用知识图谱API，支持process_content接口
    """
    
    def __init__(self, api_url: str = "http://localhost:8066/api/kg"):
        """初始化SDK
        
        Args:
            api_url: API基础URL，默认 http://localhost:8066/api/kg
        """
        self.api_url = api_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def process_content(self, content: str) -> Dict[str, Any]:
        """处理文本内容并构建知识图谱
        
        Args:
            content: 要处理的文本内容
            
        Returns:
            构建的知识图谱，包含实体、关系和元数据
            
        Raises:
            requests.exceptions.RequestException: 网络请求失败
            ValueError: 输入参数无效
        """
        if not isinstance(content, str) or not content.strip():
            raise ValueError("content必须是非空字符串")
        
        endpoint = f"{self.api_url}/process-content"
        payload = {
            "content": content
        }
        
        response = self.session.post(endpoint, json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'session'):
            self.session.close()


# 简单示例
if __name__ == "__main__":
    # 创建SDK实例
    sdk = KGSDK()
    
    # 示例文本内容
    sample_content = """特斯拉是一家美国电动汽车公司，总部位于加利福尼亚州帕洛阿尔托。
    特斯拉由埃隆·马斯克于2003年创立，主要生产电动汽车、太阳能板和储能设备。
    特斯拉的主要产品包括Model 3、Model Y、Model S和Model X等。"""
    
    try:
        # 调用process_content接口
        result = sdk.process_content(sample_content)
        
        # 打印结果
        print("知识图谱构建成功！")
        print(f"实体数量: {len(result.get('entities', []))}")
        print(f"关系数量: {len(result.get('relations', []))}")
        print(f"分类: {result.get('category', '未知')}")
        
        # 打印实体
        print("\n实体列表:")
        for entity in result.get('entities', [])[:5]:  # 只显示前5个实体
            print(f"- {entity.get('name')} ({entity.get('type')})")
            
    except Exception as e:
        print(f"调用失败: {e}")
