#!/usr/bin/env python3
"""
新闻处理服务详细测试脚本
测试新闻处理服务的各种功能和场景
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

from kg.services.news_processing_service import NewsProcessingService
from kg.services.data_services import KnowledgeGraphService
from kg.database.connection import init_database_async


async def test_basic_news_processing():
    """测试基本新闻处理功能"""
    print("=" * 60)
    print("测试基本新闻处理功能")
    print("=" * 60)
    
    # 初始化数据库
    await init_database_async()
    
    # 创建服务实例
    kg_service = KnowledgeGraphService()
    news_service = NewsProcessingService(kg_service)
    
    # 测试新闻数据
    test_news = {
        "title": "特斯拉发布2023年第四季度财报",
        "content": """
        特斯拉公司今日发布了2023年第四季度财报，显示该季度营收达到251.7亿美元，同比增长3%，略高于分析师预期的245.1亿美元。
        净利润为79.06亿美元，同比增长115%。特斯拉表示，尽管面临全球经济挑战，但公司通过降价策略成功提升了销量。
        Model Y成为全球最畅销的电动汽车车型，全年销量超过120万辆。公司CEO埃隆·马斯克在财报电话会议上表示，
        2024年将继续专注于降低生产成本和提高自动驾驶技术。特斯拉还宣布将在墨西哥新建一座超级工厂，
        预计2025年开始生产。投资者对财报反应积极，盘后股价上涨超过5%。
        """,
        "source": "财经新闻网",
        "source_url": f"https://example.com/news/tesla-q4-2023-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "publish_time": "2024-01-25T09:30:00Z",
        "author": "李财经",
        "category": "科技",
        "tags": ["特斯拉", "财报", "电动汽车"]
    }
    
    # 处理新闻
    result = await news_service.process_and_store_news(test_news)
    
    # 打印结果
    print(f"新闻标题: {test_news['title']}")
    print(f"来源: {test_news['source']}")
    print(f"发布时间: {test_news['publish_time']}")
    print(f"作者: {test_news['author']}")
    print()
    print("新闻处理成功！")
    print(f"新闻ID: {result['news_id']}")
    print(f"新闻摘要: {result['summary']}")
    print(f"提取实体数量: {len(result['entities'])}")
    print()
    print("提取的实体:")
    for entity in result['entities']:
        print(f"- {entity.name} ({entity.type})")
    print()
    print(f"提取关系数量: {len(result['relations'])}")
    print()
    print("提取的关系:")
    for relation in result['relations']:
        print(f"- {relation.source_entity_id} -> {relation.relation_type} -> {relation.target_entity_id}")
    print()
    
    return result


async def test_financial_news():
    """测试金融新闻处理"""
    print("=" * 60)
    print("测试金融新闻处理")
    print("=" * 60)
    
    # 创建服务实例
    kg_service = KnowledgeGraphService()
    news_service = NewsProcessingService(kg_service)
    
    # 金融新闻测试数据
    financial_news = {
        "title": "美联储宣布加息25个基点，符合市场预期",
        "content": """
        美联储在最新的货币政策会议上宣布加息25个基点，将联邦基金利率目标区间上调至5.25%-5.5%，符合市场普遍预期。
        这是美联储自2022年3月以来的第11次加息，旨在抑制持续高企的通胀。美联储主席鲍威尔在新闻发布会上表示，
        通胀率仍然"过高"，但已有所缓和。他强调，美联储将继续密切关注经济数据，并保持政策的灵活性。
        市场反应积极，标普500指数上涨0.8%，纳斯达克指数上涨1.2%。分析师普遍认为，这可能预示着美联储加息周期接近尾声。
        高盛集团首席经济学家表示，预计美联储将在今年下半年开始降息。美元指数小幅下跌，而黄金价格则上涨1.5%。
        """,
        "source": "华尔街日报",
        "source_url": f"https://example.com/news/fed-rate-hike-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "publish_time": "2023-07-26T18:00:00Z",
        "author": "王金融",
        "category": "金融",
        "tags": ["美联储", "加息", "货币政策"]
    }
    
    # 处理新闻
    result = await news_service.process_and_store_news(financial_news)
    
    # 打印结果
    print(f"新闻标题: {financial_news['title']}")
    print(f"新闻摘要: {result['summary']}")
    print(f"提取实体数量: {len(result['entities'])}")
    print(f"提取关系数量: {len(result['relations'])}")
    print()
    print("提取的关键实体:")
    for entity in result['entities'][:5]:  # 只显示前5个实体
        print(f"- {entity.name} ({entity.type})")
    print()
    print("提取的关键关系:")
    for relation in result['relations'][:5]:  # 只显示前5个关系
        print(f"- {relation.source_entity_id} -> {relation.relation_type} -> {relation.target_entity_id}")
    print()
    
    return result


async def test_tech_news():
    """测试科技新闻处理"""
    print("=" * 60)
    print("测试科技新闻处理")
    print("=" * 60)
    
    # 创建服务实例
    kg_service = KnowledgeGraphService()
    news_service = NewsProcessingService(kg_service)
    
    # 科技新闻测试数据
    tech_news = {
        "title": "谷歌推出Gemini AI模型，挑战GPT-4",
        "content": """
        谷歌今日发布了其最新的人工智能模型Gemini，声称在多项基准测试中表现优于OpenAI的GPT-4。
        Gemini是谷歌迄今为止最先进的AI模型，具有多模态理解能力，可以同时处理文本、图像、音频和视频。
        谷歌CEO桑达尔·皮查伊在发布会上表示，Gemini代表了AI技术的重大突破，将为用户带来更自然的交互体验。
        Gemini分为三个版本：Ultra、Pro和Nano，分别适用于不同场景。谷歌计划将Gemini集成到搜索、助手、Workspace等产品中。
        分析人士认为，Gemini的发布标志着AI竞争进入新阶段，可能对OpenAI的市场地位构成挑战。
        微软CEO萨提亚·纳德拉表示，将继续与OpenAI合作，将GPT-4集成到更多产品中。
        """,
        "source": "科技前沿",
        "source_url": f"https://example.com/news/google-gemini-ai-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "publish_time": "2023-12-06T14:30:00Z",
        "author": "张科技",
        "category": "科技",
        "tags": ["谷歌", "Gemini", "人工智能"]
    }
    
    # 处理新闻
    result = await news_service.process_and_store_news(tech_news)
    
    # 打印结果
    print(f"新闻标题: {tech_news['title']}")
    print(f"新闻摘要: {result['summary']}")
    print(f"提取实体数量: {len(result['entities'])}")
    print(f"提取关系数量: {len(result['relations'])}")
    print()
    print("提取的关键实体:")
    for entity in result['entities'][:5]:  # 只显示前5个实体
        print(f"- {entity.name} ({entity.type})")
    print()
    print("提取的关键关系:")
    for relation in result['relations'][:5]:  # 只显示前5个关系
        print(f"- {relation.source_entity_id} -> {relation.relation_type} -> {relation.target_entity_id}")
    print()
    
    return result


async def test_news_with_quotes():
    """测试包含引语的新闻处理"""
    print("=" * 60)
    print("测试包含引语的新闻处理")
    print("=" * 60)
    
    # 创建服务实例
    kg_service = KnowledgeGraphService()
    news_service = NewsProcessingService(kg_service)
    
    # 包含引语的新闻测试数据
    quote_news = {
        "title": "巴菲特在伯克希尔股东大会上分享投资智慧",
        "content": """
        沃伦·巴菲特在伯克希尔·哈撒韦公司年度股东大会上分享了他的投资智慧。
        当被问及对当前市场的看法时，巴菲特表示："别人贪婪时我恐惧，别人恐惧时我贪婪。"这句话再次强调了他逆向投资的哲学。
        他还补充道："投资的第一条原则是永远不要亏钱，第二条原则是永远不要忘记第一条原则。"
        巴菲特还谈到了他对科技股的看法，承认他错过了早期的投资机会，但现在对苹果公司持乐观态度。
        "苹果是一家非凡的公司，拥有强大的品牌和忠诚的客户群，"他说。
        伯克希尔副董事长查理·芒格也分享了他的观点："投资的关键是找到伟大的公司，然后以合理的价格买入。"
        股东大会吸引了数万名投资者参加，他们希望从这两位投资大师的智慧中获益。
        """,
        "source": "投资日报",
        "source_url": f"https://example.com/news/buffett-shareholder-meeting-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "publish_time": "2023-05-06T16:00:00Z",
        "author": "赵投资",
        "category": "投资",
        "tags": ["巴菲特", "伯克希尔", "股东大会", "投资智慧"]
    }
    
    # 处理新闻
    result = await news_service.process_and_store_news(quote_news)
    
    # 打印结果
    print(f"新闻标题: {quote_news['title']}")
    print(f"新闻摘要: {result['summary']}")
    print(f"提取实体数量: {len(result['entities'])}")
    print(f"提取关系数量: {len(result['relations'])}")
    print()
    print("提取的关键实体:")
    for entity in result['entities'][:5]:  # 只显示前5个实体
        print(f"- {entity.name} ({entity.type})")
    print()
    print("提取的关键关系:")
    for relation in result['relations'][:5]:  # 只显示前5个关系
        print(f"- {relation.source_entity_id} -> {relation.relation_type} -> {relation.target_entity_id}")
    print()
    
    return result


async def test_news_with_numbers_and_dates():
    """测试包含数字和日期的新闻处理"""
    print("=" * 60)
    print("测试包含数字和日期的新闻处理")
    print("=" * 60)
    
    # 创建服务实例
    kg_service = KnowledgeGraphService()
    news_service = NewsProcessingService(kg_service)
    
    # 包含数字和日期的新闻测试数据
    number_news = {
        "title": "中国2023年GDP增长5.2%，超过预期目标",
        "content": """
        中国国家统计局今日公布数据显示，2023年国内生产总值(GDP)达到126.06万亿元人民币，同比增长5.2%，超过年初设定的5%左右的目标。
        分季度看，一季度GDP同比增长4.5%，二季度增长6.3%，三季度增长4.9%，四季度增长5.2%。
        国家统计局局长康义在新闻发布会上表示，2023年中国经济顶住外部压力，克服内部困难，实现回升向好。
        具体来看，第一产业增加值8.97万亿元，增长4.1%；第二产业增加值48.26万亿元，增长4.7%；第三产业增加值68.83万亿元，增长5.8%。
        全年社会消费品零售总额47.15万亿元，同比增长7.2%。固定资产投资50.3万亿元，增长3.0%。
        出口23.77万亿元，增长0.6%；进口17.99万亿元，下降0.5%。贸易顺差5.78万亿元。
        城镇调查失业率平均值为5.2%，比上年下降0.4个百分点。居民消费价格(CPI)上涨0.2%。
        康义表示，2024年中国经济将继续坚持稳中求进工作总基调，预计GDP增长目标将设定在5%左右。
        """,
        "source": "经济参考报",
        "source_url": f"https://example.com/news/china-gdp-2023-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "publish_time": "2024-01-17T10:00:00Z",
        "author": "钱经济",
        "category": "经济",
        "tags": ["GDP", "经济增长", "统计数据"]
    }
    
    # 处理新闻
    result = await news_service.process_and_store_news(number_news)
    
    # 打印结果
    print(f"新闻标题: {number_news['title']}")
    print(f"新闻摘要: {result['summary']}")
    print(f"提取实体数量: {len(result['entities'])}")
    print(f"提取关系数量: {len(result['relations'])}")
    print()
    print("提取的关键实体:")
    for entity in result['entities'][:8]:  # 显示前8个实体
        print(f"- {entity.name} ({entity.type})")
    print()
    print("提取的关键关系:")
    for relation in result['relations'][:5]:  # 只显示前5个关系
        print(f"- {relation.source_entity_id} -> {relation.relation_type} -> {relation.target_entity_id}")
    print()
    
    return result


async def main():
    """主测试函数"""
    print("开始新闻处理服务详细测试...")
    print()
    
    # 测试不同类型的新闻
    await test_basic_news_processing()
    await test_financial_news()
    await test_tech_news()
    await test_news_with_quotes()
    await test_news_with_numbers_and_dates()
    
    print("=" * 60)
    print("所有测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())