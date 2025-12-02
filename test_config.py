"""
测试配置管理器是否正确处理更新后的KnowledgeGraphConfig结构
"""

from app.config.config_manager import ConfigManager, KnowledgeGraphConfig, CategoryConfigItem, ItemWithDescription, EntityMergingConfig

def test_knowledge_graph_config():
    """测试知识图谱配置加载和解析"""
    # 初始化配置管理器
    config_manager = ConfigManager()
    
    # 获取知识图谱配置
    kg_config = config_manager.get_knowledge_graph_config()
    
    # 验证配置类型
    assert isinstance(kg_config, KnowledgeGraphConfig)
    print("KnowledgeGraphConfig类型验证通过")
    
    # 验证类别配置
    assert isinstance(kg_config.categories, dict)
    print(f"类别数量: {len(kg_config.categories)}")
    
    # 验证每个类别配置项
    for category_key, category_item in kg_config.categories.items():
        assert isinstance(category_item, CategoryConfigItem)
        print(f"\n类别 '{category_key}':")
        print(f"  名称: {category_item.category.name}")
        print(f"  描述: {category_item.category.description}")
        print(f"  关系类型数量: {len(category_item.relation_types)}")
        print(f"  实体类型数量: {len(category_item.entity_types)}")
    
    # 验证默认类别
    assert kg_config.default_category == "financial"
    print(f"\n默认类别: {kg_config.default_category}")
    
    # 验证实体合并配置
    assert isinstance(kg_config.entity_merging, EntityMergingConfig)
    print(f"\n实体合并配置:")
    print(f"  启用: {kg_config.entity_merging.enabled}")
    print(f"  相似度阈值: {kg_config.entity_merging.similarity_threshold}")
    print(f"  最大候选数: {kg_config.entity_merging.max_candidates}")
    
    # 验证其他配置项
    assert isinstance(kg_config.similarity_threshold, float)
    assert isinstance(kg_config.max_entities_per_news, int)
    print(f"\n相似度阈值: {kg_config.similarity_threshold}")
    print(f"每条新闻最大实体数: {kg_config.max_entities_per_news}")
    
    print("\n所有测试通过！")

if __name__ == "__main__":
    test_knowledge_graph_config()
