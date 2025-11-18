import asyncio
from kg.services.llm_service import LLMService

async def main():
    llm_service = LLMService()
    text = """
北京市将于2023年9月21日举办2023年中国国际服务贸易交易会（简称“服贸会”）。
服贸会是全球服务贸易领域规模最大的综合性展会之一，今年的主题是“服务合作促发展 绿色创新迎未来”。
北京市商务局局长丁勇表示，服贸会将聚焦数字经济、绿色发展、服务业开放等重点领域，设置15个专题展区，预计吸引超过100个国家和地区的企业参展。
"""
    entities = await llm_service.extract_entities(text)
    print("Entities:", entities)

asyncio.run(main())