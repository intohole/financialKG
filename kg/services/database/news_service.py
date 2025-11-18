import logging
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from kg.database.models import News, EntityNews, Entity
from kg.database.repositories import NewsRepository, EntityNewsRepository
from kg.database.connection import get_db_session
from kg.utils.db_utils import handle_db_errors, handle_db_errors_with_reraise
from .entity_service import EntityService

# 配置日志
logger = logging.getLogger(__name__)

class NewsService:
    """新闻服务类，提供新闻相关的高级操作"""
    
    def __init__(self, session: Optional[Session] = None):
        self.session = session or get_db_session()
        self.news_repo = NewsRepository(self.session)
        self.entity_news_repo = EntityNewsRepository(self.session)
        self.entity_service = EntityService(self.session)
    
    @handle_db_errors_with_reraise()
    async def create_news(self, title: str, content: str, url: Optional[str] = None,
                   publish_time: Optional[datetime] = None, source: Optional[str] = None,
                   category: Optional[str] = None) -> News:
        """
        创建新闻
        
        Args:
            title: 新闻标题
            content: 新闻内容
            url: 新闻URL
            publish_time: 发布时间
            source: 新闻来源
            category: 新闻类别
            
        Returns:
            News: 创建的新闻对象
        """
        news = await self.news_repo.create(
            title=title,
            content=content,
            url=url,
            publish_time=publish_time,
            source=source,
            category=category
        )
        logger.info(f"创建新闻成功: {title} (ID: {news.id})")
        return news
    
    @handle_db_errors_with_reraise()
    def get_or_create_news(self, title: str, content: str, url: Optional[str] = None,
                          publish_time: Optional[datetime] = None, source: Optional[str] = None,
                          category: Optional[str] = None) -> News:
        """
        获取或创建新闻
        
        Args:
            title: 新闻标题
            content: 新闻内容
            url: 新闻URL
            publish_time: 发布时间
            source: 新闻来源
            category: 新闻类别
            
        Returns:
            News: 获取或创建的新闻对象
        """
        # 如果有URL，先根据URL查找
        if url:
            news = self.news_repo.find_by_url(url)
            if news:
                logger.debug(f"找到已存在新闻: {title} (ID: {news.id})")
                return news
        
        # 创建新新闻
        news = self.news_repo.create(
            title=title,
            content=content,
            url=url,
            publish_time=publish_time,
            source=source,
            category=category
        )
        logger.info(f"创建新新闻: {title} (ID: {news.id})")
        return news
    
    @handle_db_errors(default_return=None)
    async def get_news_by_id(self, news_id: int) -> Optional[News]:
        """根据ID获取新闻"""
        return await self.news_repo.get(news_id)
    
    @handle_db_errors(default_return=[])
    def get_news_by_status(self, status: str, limit: Optional[int] = None) -> List[News]:
        """根据提取状态获取新闻"""
        return self.news_repo.find_by_extraction_status(status, limit)
    
    @handle_db_errors(default_return=[])
    def get_recent_news(self, days: int = 7, limit: Optional[int] = None) -> List[News]:
        """获取最近几天的新闻"""
        return self.news_repo.get_recent_news(days, limit)
    
    @handle_db_errors(default_return=[])
    def search_news(self, keyword: str, limit: Optional[int] = None) -> List[News]:
        """搜索新闻"""
        return self.news_repo.search_news(keyword, limit)
    
    @handle_db_errors(default_return=None)
    def update_extraction_status(self, news_id: int, status: str) -> Optional[News]:
        """更新新闻的提取状态"""
        return self.news_repo.update(news_id, extraction_status=status, extracted_at=datetime.utcnow())
    
    @handle_db_errors_with_reraise()
    async def link_entity_to_news(self, entity_id: int, news_id: int, 
                           context: Optional[str] = None) -> EntityNews:
        """
        将实体链接到新闻
        
        Args:
            entity_id: 实体ID
            news_id: 新闻ID
            context: 实体在新闻中的上下文
            
        Returns:
            EntityNews: 创建的实体-新闻关联对象
        """
        return await self.entity_news_repo.get_or_create(
            entity_id=entity_id,
            news_id=news_id,
            context=context
        )
    
    @handle_db_errors(default_return=[]) 
    async def get_news_entities(self, news_id: int, limit: Optional[int] = None) -> List[Entity]:
        """
        获取新闻中的实体
        """
        # 获取新闻与实体的关联记录
        entity_news_list = await self.entity_news_repo.find_by_news(news_id, limit)
        # 获取所有实体ID
        entity_ids = [en.entity_id for en in entity_news_list]
        # 获取实体对象
        entities = []
        for entity_id in entity_ids:
            entity = await self.entity_service.get_entity_by_id(entity_id)
            if entity:
                entities.append(entity)
        return entities
    
    @handle_db_errors(default_return=None)
    def update_news(self, news_id: int, **kwargs) -> Optional[News]:
        """更新新闻"""
        return self.news_repo.update(news_id, **kwargs)
