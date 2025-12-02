"""
测试新闻事件转换功能
"""

from datetime import datetime
from app.store.store_data_convert import DataConverter
from app.store.store_base_abstract import NewsEvent
from app.database.models import NewsEvent as DBNewsEvent


async def test_news_event_conversion():
    """测试新闻事件转换功能"""
    print("开始测试新闻事件转换功能...")
    
    # 创建一个业务层的新闻事件对象
    business_news = NewsEvent(
        title="测试新闻标题",
        content="这是一条测试新闻内容",
        source="测试来源",
        publish_time=datetime.now(),
        vector_id="test_vector_id"
    )
    
    print("1. 测试业务新闻事件转换为数据库数据字典")
    # 测试业务新闻事件转换为数据库数据字典
    db_data = DataConverter.news_event_to_db_news_event(business_news)
    print(f"   转换结果: {db_data}")
    
    # 验证转换结果
    assert db_data['title'] == business_news.title
    assert db_data['content'] == business_news.content
    assert db_data['source'] == business_news.source
    assert db_data['publish_time'] == business_news.publish_time
    assert db_data['vector_id'] == business_news.vector_id
    print("   验证通过!")
    
    print("\n2. 测试数据库新闻事件转换为业务新闻事件")
    # 模拟数据库对象
    class MockDBNewsEvent:
        def __init__(self):
            self.id = 1
            self.title = "数据库新闻标题"
            self.content = "数据库中的新闻内容"
            self.source = "数据库来源"
            self.publish_time = datetime.now()
            self.created_at = datetime.now()
            self.updated_at = datetime.now()
    
    db_news = MockDBNewsEvent()
    vector_id = "test_vector_id_from_db"
    
    # 测试数据库新闻事件转换为业务新闻事件
    business_result = DataConverter.db_news_event_to_news_event(db_news, vector_id)
    print(f"   转换结果: ID={business_result.id}, 标题={business_result.title}, 向量ID={business_result.vector_id}")
    
    # 验证转换结果
    assert business_result.id == db_news.id
    assert business_result.title == db_news.title
    assert business_result.content == db_news.content
    assert business_result.source == db_news.source
    assert business_result.publish_time == db_news.publish_time
    assert business_result.created_at == db_news.created_at
    assert business_result.updated_at == db_news.updated_at
    assert business_result.vector_id == vector_id
    print("   验证通过!")
    
    print("\n3. 测试错误处理")
    try:
        DataConverter.db_news_event_to_news_event(None)
        print("   测试失败: 应该抛出ValueError")
    except ValueError as e:
        print(f"   测试通过: 正确抛出ValueError: {e}")
    
    try:
        DataConverter.news_event_to_db_news_event(None)
        print("   测试失败: 应该抛出ValueError")
    except ValueError as e:
        print(f"   测试通过: 正确抛出ValueError: {e}")
    
    print("\n所有测试通过！")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_news_event_conversion())
