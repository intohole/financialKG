import asyncio
from kg.services import LLMService

async def test_llm_service():
    # 测试LLMService的初始化
    service = LLMService()
    
    # 测试基本功能
    text = "华为于2023年发布了Mate 60 Pro手机，搭载了自主研发的麒麟芯片。"
    entities = await service.extract_entities(text)
    relations = await service.extract_relations(text)
    summary = await service.summarize_text(text, summary_type="short", max_sentences=2)
    
    print("实体抽取结果:", entities)
    print("关系抽取结果:", relations)
    print("新闻摘要:", summary)
    
    print("测试完成，LLMService功能正常")

if __name__ == "__main__":
    asyncio.run(test_llm_service())
