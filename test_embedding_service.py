import asyncio
import logging
from kg.services.embedding_service import ThirdPartyEmbeddingService
from kg.utils.embedding_utils import validate_embedding, aggregate_embeddings

# 设置日志级别为WARNING，减少干扰
logging.basicConfig(level=logging.WARNING)

class MockEmbeddingClient:
    """模拟嵌入服务客户端，符合AsyncOpenAI接口规范"""
    class MockEmbeddings:
        """模拟嵌入服务接口"""
        def __init__(self, client):
            self.client = client
        
        async def create(self, input, model):
            """创建嵌入向量"""
            return MockEmbeddingClient.MockResponse(input)
    
    class MockResponse:
        """模拟API响应"""
        def __init__(self, texts):
            self.data = [MockEmbeddingClient.MockEmbeddingData(i, text) for i, text in enumerate(texts)]
    
    class MockEmbeddingData:
        """模拟嵌入数据"""
        def __init__(self, index, text):
            # 生成固定维度(1536)的模拟嵌入向量
            self.embedding = [0.1 + (index * 0.01) for _ in range(1536)]
    
    @property
    def embeddings(self):
        """获取嵌入服务接口"""
        return self.MockEmbeddings(self)

class MockEmbeddingConfig:
    """模拟嵌入配置"""
    def __init__(self):
        self.embedding_model = "mock-embedding-model"
        self.embedding_dimension = 1536
        self.client = MockEmbeddingClient()

async def test_embedding_service():
    """测试嵌入服务的功能"""
    print("=== 开始测试嵌入服务（使用模拟客户端）===")
    
    # 1. 创建并初始化嵌入服务，使用模拟配置
    mock_config = MockEmbeddingConfig()
    embedding_service = ThirdPartyEmbeddingService(mock_config)
    
    # 初始化服务
    is_initialized = await embedding_service.initialize()
    if not is_initialized:
        print("❌ 嵌入服务初始化失败")
        return
    
    print("✅ 嵌入服务初始化成功")
    
    # 2. 测试获取单个文本的embedding
    test_text = "华为于2023年发布了Mate 60 Pro手机，搭载了自主研发的麒麟芯片。"
    print(f"\n测试文本: {test_text}")
    
    try:
        single_embedding = await embedding_service.get_embedding(test_text)
        print(f"✅ 成功获取单个文本embedding，维度: {len(single_embedding)}")
        print(f"✅ 前5个值: {single_embedding[:5]}")
        
        # 验证embedding有效性
        is_valid = embedding_service.is_valid_embedding(single_embedding)
        print(f"✅ 向量有效性验证: {'通过' if is_valid else '失败'}")
        
    except Exception as e:
        print(f"❌ 获取单个文本embedding失败: {str(e)}")
        return
    
    # 3. 测试获取多个文本的embedding
    test_texts = [
        "华为于2023年发布了Mate 60 Pro手机",
        "麒麟芯片是华为自主研发的处理器",
        "2023年是科技发展的重要一年"
    ]
    
    print("\n测试批量文本embedding:")
    for i, text in enumerate(test_texts):
        print(f"文本 {i+1}: {text}")
    
    try:
        batch_embeddings = await embedding_service.get_embeddings(test_texts)
        print(f"✅ 成功获取{len(batch_embeddings)}个文本的embedding")
        
        # 验证所有embedding的维度一致
        dimensions = [len(emb) for emb in batch_embeddings]
        if all(dim == dimensions[0] for dim in dimensions):
            print(f"✅ 所有embedding维度一致: {dimensions[0]}")
        else:
            print(f"❌ embedding维度不一致: {dimensions}")
            
        # 验证每个embedding的有效性
        all_valid = all(validate_embedding(emb) for emb in batch_embeddings)
        print(f"✅ 所有向量有效性验证: {'通过' if all_valid else '失败'}")
        
    except Exception as e:
        print(f"❌ 获取批量文本embedding失败: {str(e)}")
        return
    
    # 4. 测试获取维度功能
    try:
        dimension = embedding_service.get_dimension()
        print(f"\n✅ 嵌入服务配置的维度: {dimension}")
        print(f"✅ 实际生成的维度: {len(single_embedding)}")
        
        if dimension == len(single_embedding):
            print("✅ 配置维度与实际维度匹配")
        else:
            print("⚠️  配置维度与实际维度不匹配")
            
    except Exception as e:
        print(f"❌ 获取维度失败: {str(e)}")
    
    # 5. 测试空文本处理
    try:
        empty_embedding = await embedding_service.get_embedding("")
        print(f"\n✅ 空文本处理测试: {'通过' if len(empty_embedding) == 0 else '失败'}")
    except Exception as e:
        print(f"❌ 空文本处理失败: {str(e)}")
    
    # 6. 测试向量聚合功能（使用utils中的函数）
    try:
        aggregated = aggregate_embeddings(batch_embeddings, method="mean")
        print(f"\n✅ 向量聚合测试成功，维度: {len(aggregated)}")
        print(f"✅ 聚合后的前5个值: {aggregated[:5]}")
    except Exception as e:
        print(f"❌ 向量聚合失败: {str(e)}")
    
    print("\n=== 嵌入服务测试完成 ===")

if __name__ == "__main__":
    asyncio.run(test_embedding_service())
