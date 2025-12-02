"""
新闻搜索服务
结合向量搜索和数据库查询实现智能新闻搜索
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass

from app.store.hybrid_store_core_implement import HybridStoreCore
from app.store.store_base_abstract import SearchResult
from app.database.repositories import NewsEventRepository
from app.utils.logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class NewsSearchConfig:
    """新闻搜索配置"""
    enable_vector_search: bool = True
    enable_database_search: bool = True
    vector_weight: float = 0.7  # 向量搜索权重
    database_weight: float = 0.3  # 数据库搜索权重
    max_results: int = 100
    min_score: float = 0.1  # 最小相关性分数


class NewsSearchService:
    """新闻搜索服务"""
    
    def __init__(self, session, hybrid_store: Optional[HybridStoreCore] = None):
        """
        初始化新闻搜索服务
        
        Args:
            session: 数据库会话
            hybrid_store: 混合存储实例（可选）
        """
        self.session = session
        self.news_repo = NewsEventRepository(session)
        self.hybrid_store = hybrid_store
        self.config = NewsSearchConfig()
    
    def set_hybrid_store(self, hybrid_store: HybridStoreCore) -> None:
        """设置混合存储实例"""
        self.hybrid_store = hybrid_store
    
    async def search_news(
        self,
        query: str,
        top_k: int = 20,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        enable_hybrid: bool = True
    ) -> Dict[str, Any]:
        """
        搜索新闻
        
        Args:
            query: 搜索查询词
            top_k: 返回结果数量
            start_date: 开始日期
            end_date: 结束日期
            enable_hybrid: 是否启用混合搜索
            
        Returns:
            Dict[str, Any]: 搜索结果
        """
        logger.info(f"搜索新闻: query='{query}', top_k={top_k}, hybrid={enable_hybrid}")
        
        try:
            if enable_hybrid and self.hybrid_store and self.config.enable_vector_search:
                # 混合搜索：向量搜索 + 数据库搜索
                return await self._hybrid_search(query, top_k, start_date, end_date)
            else:
                # 纯数据库搜索
                return await self._database_search(query, top_k, start_date, end_date)
                
        except Exception as e:
            logger.error(f"搜索新闻失败: {e}")
            # 降级到数据库搜索
            return await self._database_search(query, top_k, start_date, end_date)
    
    async def _hybrid_search(
        self,
        query: str,
        top_k: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """混合搜索"""
        logger.info("执行混合搜索")
        
        # 1. 向量搜索
        vector_results = await self._vector_search(query, top_k * 2, start_date, end_date)
        
        # 2. 数据库搜索
        db_results = await self._database_search(query, top_k, start_date, end_date)
        
        # 3. 融合结果
        return self._merge_search_results(vector_results, db_results, top_k)
    
    async def _vector_search(
        self,
        query: str,
        top_k: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[SearchResult]:
        """向量搜索"""
        if not self.hybrid_store:
            return []
        
        try:
            # 使用HybridStoreCore的搜索功能
            search_results = await self.hybrid_store.search_news_events(
                query=query,
                top_k=top_k,
                start_date=start_date,
                end_date=end_date
            )
            
            logger.info(f"向量搜索完成: 找到{len(search_results)}个结果")
            return search_results
            
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            return []
    
    async def _database_search(
        self,
        query: str,
        top_k: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """数据库搜索"""
        logger.info("执行数据库搜索")
        
        try:
            # 使用内容搜索功能
            news_events = await self.news_repo.search_by_content(
                query=query,
                skip=0,
                limit=top_k
            )
            
            # 转换为搜索结果格式
            results = []
            for news in news_events:
                # 计算相关性分数（简单的关键词匹配分数）
                score = self._calculate_relevance_score(query, news)
                
                result = SearchResult(
                    news_event=news,
                    score=score,
                    metadata={
                        "search_type": "database",
                        "relevance_score": score
                    }
                )
                results.append(result)
            
            # 按分数排序
            results.sort(key=lambda x: x.score, reverse=True)
            
            logger.info(f"数据库搜索完成: 找到{len(results)}个结果")
            return {
                "results": results,
                "total": len(results),
                "search_type": "database"
            }
            
        except Exception as e:
            logger.error(f"数据库搜索失败: {e}")
            return {"results": [], "total": 0, "search_type": "database"}
    
    def _calculate_relevance_score(self, query: str, news_event) -> float:
        """计算相关性分数"""
        query_lower = query.lower()
        title_lower = (news_event.title or "").lower()
        content_lower = (news_event.content or "").lower()
        
        score = 0.0
        
        # 标题匹配权重更高
        if query_lower in title_lower:
            score += 0.7
            
        # 内容匹配
        if query_lower in content_lower:
            score += 0.3
            
        # 关键词出现频率
        title_count = title_lower.count(query_lower)
        content_count = content_lower.count(query_lower)
        score += min((title_count + content_count * 0.5) * 0.1, 0.5)
        
        return min(score, 1.0)
    
    def _merge_search_results(
        self,
        vector_results: List[SearchResult],
        db_results: Dict[str, Any],
        top_k: int
    ) -> Dict[str, Any]:
        """融合搜索结果"""
        logger.info("融合搜索结果")
        
        # 创建新闻ID到结果的映射
        merged_results = {}
        
        # 添加向量搜索结果
        for result in vector_results:
            if result.news_event:
                news_id = result.news_event.id
                if news_id not in merged_results:
                    merged_results[news_id] = {
                        "news_event": result.news_event,
                        "vector_score": result.score,
                        "db_score": 0.0,
                        "metadata": result.metadata or {}
                    }
        
        # 添加数据库搜索结果
        for result in db_results.get("results", []):
            if result.news_event:
                news_id = result.news_event.id
                if news_id in merged_results:
                    merged_results[news_id]["db_score"] = result.score
                else:
                    merged_results[news_id] = {
                        "news_event": result.news_event,
                        "vector_score": 0.0,
                        "db_score": result.score,
                        "metadata": result.metadata or {}
                    }
        
        # 计算综合分数并排序
        final_results = []
        for news_id, data in merged_results.items():
            # 加权综合分数
            final_score = (
                data["vector_score"] * self.config.vector_weight +
                data["db_score"] * self.config.database_weight
            )
            
            if final_score >= self.config.min_score:
                final_results.append({
                    "news_event": data["news_event"],
                    "score": final_score,
                    "metadata": {
                        **data["metadata"],
                        "final_score": final_score,
                        "vector_score": data["vector_score"],
                        "db_score": data["db_score"],
                        "search_type": "hybrid"
                    }
                })
        
        # 按分数排序并限制数量
        final_results.sort(key=lambda x: x["score"], reverse=True)
        final_results = final_results[:top_k]
        
        logger.info(f"搜索结果融合完成: {len(final_results)}个结果")
        return {
            "results": final_results,
            "total": len(final_results),
            "search_type": "hybrid",
            "fusion_weights": {
                "vector": self.config.vector_weight,
                "database": self.config.database_weight
            }
        }
    
    async def get_recent_news(
        self,
        days: int = 7,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        获取最近的新闻
        
        Args:
            days: 最近天数
            limit: 返回数量限制
            
        Returns:
            List[Dict[str, Any]]: 最近新闻列表
        """
        try:
            recent_news = await self.news_repo.get_recent_events(
                days=days,
                limit=limit
            )
            
            # 转换为前端友好的格式
            return [
                {
                    "id": getattr(news, 'id', None),
                    "title": getattr(news, 'title', None),
                    "content": (getattr(news, 'content', '')[:300] + "..." if len(getattr(news, 'content', '')) > 300 else getattr(news, 'content', '')),
                    "source": getattr(news, 'source', None),
                    "published_at": getattr(news, 'publish_time', None).isoformat() if getattr(news, 'publish_time', None) else None,
                    "created_at": getattr(news, 'created_at', None).isoformat() if getattr(news, 'created_at', None) else None,
                    "updated_at": getattr(news, 'updated_at', None).isoformat() if getattr(news, 'updated_at', None) else None
                }
                for news in recent_news
            ]
        except Exception as e:
            logger.error(f"获取最近新闻失败: {e}")
            return []