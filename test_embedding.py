import asyncio
from kg.core.config import embedding_config
from kg.services.embedding_service import create_embedding_service

async def test_embedding():
    """测试嵌入模型功能"""
    try:
        # 创建嵌入服务实例
        embedding_service = create_embedding_service(config=embedding_config)
        
        # 测试文本
        test_texts = [
            "这是一段需要向量化的文本",
            "另一段用于测试的文本",
            "知识图谱实体去重"
        ]
        
        print("开始测试嵌入模型...")
        print(f"测试文本: {test_texts}")
        print()
        
        # 调用嵌入服务获取向量
        embeddings = await embedding_service.get_embeddings(test_texts)
        
        # 验证结果
        if embeddings:
            print("✓ 嵌入获取成功!")
            print(f"✓ 生成的嵌入数量: {len(embeddings)}")
            print(f"✓ 每个嵌入的维度: {len(embeddings[0])}")
            print()
            
            # 打印每个嵌入的前10个值
            for i, (text, embedding) in enumerate(zip(test_texts, embeddings)):
                print(f"文本 {i+1}: {text[:20]}...")
                print(f"嵌入向量前10值: {embedding[:10]}...")
                print()
        else:
            print("✗ 未获取到嵌入向量")
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_embedding())