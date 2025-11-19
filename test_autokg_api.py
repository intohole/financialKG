import asyncio
import httpx
import pytest
import pytest_asyncio

# 定义测试数据
news_test_data = [
    {
        "title": "特斯拉发布全新Model Y车型",
        "content": "特斯拉今日正式发布全新Model Y车型，该车采用最新的电池技术和自动驾驶系统。新车续航里程可达600公里，支持超级快充技术。特斯拉CEO埃隆·马斯克表示，这款车型将成为公司未来的销量主力。",
        "source": "科技日报",
        "source_url": "https://techdaily.com/tesla-model-y-launch",
        "author": "张三",
        "publish_date": "2023-10-15T14:30:00"
    }
]

@pytest.mark.asyncio
async def test_process_news():
    """测试新闻处理接口"""
    async with httpx.AsyncClient(base_url="http://localhost:8000/api/v1", timeout=30.0) as client:
        for i, news_data in enumerate(news_test_data):
            print(f"Testing process_news {i+1}: {news_data['title']}")
            try:
                response = await client.post("/autokg/process-news", json=news_data)
                print(f"Response status: {response.status_code}")
                print(f"Response content: {response.text[:500]}...")  # 只显示前500字符
                if response.status_code == 201:
                    result = response.json()
                    print(f"✓ Success! News ID: {result['news_id']}, Entities: {len(result['entities'])}, Relations: {len(result['relations'])}")
                else:
                    print(f"✗ Failed: {response.status_code}, {response.text}")
            except Exception as e:
                print(f"✗ Error: {type(e).__name__}: {str(e)}")
                import traceback
                traceback.print_exc()
            print()

@pytest.mark.asyncio
async def test_extract_entities():
    """测试实体抽取接口"""
    async with httpx.AsyncClient(base_url="http://localhost:8000/api/v1", timeout=10.0) as client:
        test_text = "特斯拉发布全新Model Y车型"
        try:
            response = await client.post("/autokg/extract-entities", json={"text": test_text})
            if response.status_code == 200:
                result = response.json()
                print(f"Entities extraction result: {result}")
            else:
                print(f"Entities extraction failed: {response.status_code}, {response.text}")
        except Exception as e:
            print(f"Entities extraction error: {str(e)}")

@pytest.mark.asyncio
async def test_extract_relations():
    """测试关系抽取接口"""
    async with httpx.AsyncClient(base_url="http://localhost:8000/api/v1", timeout=10.0) as client:
        test_text = "特斯拉发布全新Model Y车型"
        try:
            response = await client.post("/autokg/extract-relations", json={"text": test_text})
            if response.status_code == 200:
                result = response.json()
                print(f"Relations extraction result: {result}")
            else:
                print(f"Relations extraction failed: {response.status_code}, {response.text}")
        except Exception as e:
            print(f"Relations extraction error: {str(e)}")

@pytest.mark.asyncio
async def test_process_text():
    """测试文本处理接口"""
    async with httpx.AsyncClient(base_url="http://localhost:8000/api/v1", timeout=10.0) as client:
        test_text = "特斯拉发布全新Model Y车型，续航可达600公里"
        try:
            response = await client.post("/autokg/process-text", json={"text": test_text})
            if response.status_code == 200:
                result = response.json()
                print(f"Text processing result: {result}")
            else:
                print(f"Text processing failed: {response.status_code}, {response.text}")
        except Exception as e:
            print(f"Text processing error: {str(e)}")

@pytest.mark.asyncio
async def test_bulk_process():
    """测试批量处理接口"""
    async with httpx.AsyncClient(base_url="http://localhost:8000/api/v1", timeout=15.0) as client:
        bulk_data = {
            "items": [
                {"text": "特斯拉发布Model Y"},
                {"text": "中国空间站对接成功"}
            ]
        }
        try:
            response = await client.post("/autokg/bulk-process", json=bulk_data)
            if response.status_code == 200:
                result = response.json()
                print(f"Bulk processing result: {result}")
            else:
                print(f"Bulk processing failed: {response.status_code}, {response.text}")
        except Exception as e:
            print(f"Bulk processing error: {str(e)}")

async def main():
    """运行所有测试"""
    print("=== Testing AutoKG API ===\n")
    
    await test_process_news()
    await test_extract_entities()
    await test_extract_relations()
    await test_process_text()
    await test_bulk_process()
    
    print("=== All tests completed ===")

if __name__ == "__main__":
    asyncio.run(main())
