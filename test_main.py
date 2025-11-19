import pytest
from fastapi.testclient import TestClient
from kg.main import app
from kg.api.deps import get_entity_extraction_service, get_relation_extraction_service
from unittest.mock import AsyncMock

# Debug: Print all routes
print("=== Application Routes ===")
for route in app.routes:
    print(f"Path: {route.path}, Name: {route.name}")
print("========================")


client = TestClient(app)

# Mock the entity extraction service
mock_entity_service = AsyncMock()
async def mock_extract_entities(text):
    print(f"Entity extraction called for: {text}")
    return {
        "entities": [
            {"name": "Apple Inc.", "type": "公司", "properties": {}, "weight": 1.0}
        ]
    }
mock_entity_service.extract_entities = mock_extract_entities

# Mock the relation extraction service  
mock_relation_service = AsyncMock()
async def mock_extract_relations(text):
    print(f"Relation extraction called for: {text}")
    return {
        "relations": [
            {"source": "Apple Inc.", "target": "Steve Jobs", "type": "创始人", "properties": {}, "weight": 1.0}
        ]
    }
mock_relation_service.extract_relations = mock_extract_relations

# Override the dependencies
app.dependency_overrides[get_entity_extraction_service] = lambda: mock_entity_service
app.dependency_overrides[get_relation_extraction_service] = lambda: mock_relation_service


def test_health_check():
    """测试健康检查端点"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Financial Knowledge Graph Service is running"}


def test_non_existent_endpoint():
    """测试404错误处理"""
    response = client.get("/non_existent_endpoint")
    assert response.status_code == 404
    assert response.json() == {"status": "error", "message": "Not Found", "code": 404}


def test_extract_entities():
    """测试实体抽取接口"""
    response = client.post("/api/v1/autokg/extract-entities", json={"text": "Apple Inc. was founded by Steve Jobs."})
    assert response.status_code == 200
    response_json = response.json()
    assert "entities" in response_json
    assert len(response_json["entities"]) == 2
    assert response_json["entities"][0]["name"] == "Apple Inc."


def test_extract_relations():
    """测试关系抽取接口"""
    response = client.post("/api/v1/autokg/extract-relations", json={"text": "苹果公司由史蒂夫·乔布斯创立。"})
    assert response.status_code == 200
    response_json = response.json()
    assert "relations" in response_json
    assert len(response_json["relations"]) >= 1
    assert "relation_type" in response_json["relations"][0]


def test_process_text():
    """测试文本处理接口（实体和关系）"""
    response = client.post("/api/v1/autokg/process-text", json={"text": "Apple Inc. was founded by Steve Jobs."})
    assert response.status_code == 200
    response_json = response.json()
    assert "entities" in response_json
    assert "relations" in response_json
    assert len(response_json["entities"]) == 2
    assert len(response_json["relations"]) == 1


def test_bulk_process():
    """测试批量文本处理接口"""
    response = client.post(
        "/api/v1/autokg/bulk-process",
        json={
            "items": [
                {"text": "Apple Inc. was founded by Steve Jobs."},
                {"text": "Microsoft was founded by Bill Gates."}
            ]
        }
    )
    assert response.status_code == 200
    response_json = response.json()
    print("Bulk Process Response:", response_json)
    assert "results" in response_json
    assert len(response_json["results"]) >= 1
    assert "entities" in response_json["results"][0]
    assert "relations" in response_json["results"][0]


if __name__ == "__main__":
    test_health_check()
    print("✓ 健康检查测试通过")
    
    test_non_existent_endpoint()
    print("✓ 404错误处理测试通过")
    
    test_extract_entities()
    print("✓ 实体抽取接口测试通过")
    
    test_extract_relations()
    print("✓ 关系抽取接口测试通过")
    
    test_process_text()
    print("✓ 文本处理接口测试通过")
    
    test_bulk_process()
    print("✓ 批量文本处理接口测试通过")
    
    print("\n所有测试通过！🎉")
