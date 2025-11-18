import asyncio
from kg.core.config import embedding_config
from kg.services.embedding_service import create_embedding_service
from kg.services.chroma_service import create_chroma_service

async def test_embedding_chroma_integration():
    """测试嵌入服务与Chroma向量数据库的集成"""
    try:
        # 创建嵌入服务实例
        embedding_service = create_embedding_service(config=embedding_config)
        
        # 创建Chroma服务实例
        chroma_service = create_chroma_service()
        
        # 测试文本
        test_texts = [
            "这是一段需要向量化的文本",
            "另一段用于测试的文本",
            "知识图谱实体去重",
            "大模型嵌入服务集成",
            "Chroma向量数据库"
        ]
        
        print("开始测试嵌入服务与Chroma向量数据库的集成...")
        print(f"测试文本: {test_texts}")
        print()
        
        # 调用嵌入服务获取向量
        print("1. 调用嵌入服务生成向量...")
        embeddings = await embedding_service.get_embeddings(test_texts)
        print(f"   ✓ 嵌入获取成功! 生成的嵌入数量: {len(embeddings)}")
        print(f"   ✓ 每个嵌入的维度: {len(embeddings[0])}")
        print()
        
        # 准备文档ID
        doc_ids = [f"doc_{i}" for i in range(len(test_texts))]
        
        # 向Chroma集合添加嵌入
        print("2. 向Chroma集合添加嵌入...")
        success = await chroma_service.add_embeddings(
            collection_name="test_collection",
            documents=test_texts,
            embeddings=embeddings,
            ids=doc_ids
        )
        print(f"   ✓ 嵌入添加成功! 结果: {success}")
        print()
        
        # 测试相似度查询
        print("3. 测试相似度查询...")
        # 对第一个文本进行相似度查询
        query_embeddings = [embeddings[0]]
        results = await chroma_service.query_similar_embeddings(
            collection_name="test_collection",
            query_embeddings=query_embeddings,
            n_results=3
        )
        
        print(f"   ✓ 查询成功! 结果数量: {len(results.get('ids', []))}")
        print()
        
        # 打印查询结果
        if results.get('ids'):
            print("4. 查询结果详情:")
            for i, (ids, distances, documents) in enumerate(zip(results['ids'], results['distances'], results['documents'])):
                print(f"   查询 {i+1}:")
                for doc_id, distance, doc in zip(ids, distances, documents):
                    print(f"     - 文档ID: {doc_id}")
                    print(f"     - 相似度: {distance:.4f}")
                    print(f"     - 文本: {doc}")
                    print()
        
        print("✅ 嵌入服务与Chroma向量数据库集成测试完成!")
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_embedding_chroma_integration())