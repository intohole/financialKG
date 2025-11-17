import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from .llm_service import LLMService

class NewsProcessingService:
    """
    新闻处理服务，整合LLM提取和数据存储功能
    """
    def __init__(self, data_services):
        """
        初始化新闻处理服务
        
        Args:
            data_services: 数据服务实例，用于数据库操作
        """
        self.logger = logging.getLogger(__name__)
        self.data_services = data_services
        self.llm_service = LLMService()
    
    async def process_and_store_news(self, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理新闻并存储到知识库
        
        Args:
            news_data: 新闻数据，包含标题、内容、来源、发布时间等信息
            
        Returns:
            Dict[str, Any]: 处理结果，包含新闻对象、提取的实体、关系和摘要
        """
        title = news_data.get("title", "")
        content = news_data.get("content", "")
        source_url = news_data.get("source_url", "")
        publish_date = news_data.get("publish_date", None)
        source = news_data.get("source", "unknown")
        author = news_data.get("author", None)
        
        self.logger.info(f"开始处理新闻: {title[:20]}...")
        
        # 1. 存储新闻基本信息
        news = await self.data_services.create_news(title, content, source, publish_date, author, source_url)
        self.logger.info(f"新闻基本信息已存储，新闻ID: {news.id}")
        
        # 2. 使用LLM提取实体
        entities_result = await self.llm_service.extract_entities(content)
        entities = entities_result['entities']
        self.logger.info(f"已提取实体: {len(entities)} 个")
        
        # 3. 使用LLM提取关系
        relations_result = await self.llm_service.extract_relations(content, entities)
        relations = relations_result['relations']
        self.logger.info(f"已提取关系: {len(relations)} 个")
        
        # 4. 使用LLM生成摘要
        summary_result = await self.llm_service.generate_news_summary(content)
        summary = summary_result['summary']
        self.logger.info(f"已生成新闻摘要")
        
        # 5. 存储提取的实体和关系到数据库
        stored_news, stored_entities, stored_relations = await self.data_services.store_llm_extracted_data(news.id, entities, relations)
        self.logger.info(f"提取数据已存储，实体: {len(stored_entities)}, 关系: {len(stored_relations)}")
        
        # 6. 返回处理结果
        return {
            "news_id": news.id,
            "news": news,
            "entities": stored_entities,
            "relations": stored_relations,
            "summary": summary
        }
