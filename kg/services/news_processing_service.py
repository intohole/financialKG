import logging
import dateutil.parser
from datetime import datetime
from typing import Dict, Any, Optional, List
import asyncio
import json

from .llm_service import LLMService, create_llm_service
from kg.interfaces.news_processing_service import NewsProcessingServiceInterface
from kg.utils import handle_errors
from kg.utils.service_utils import register_service, global_service_registry

# 使用全局服务注册表实例
service_registry = global_service_registry

logger = logging.getLogger(__name__)

class NewsProcessingService(NewsProcessingServiceInterface):
    """
    新闻处理服务，整合LLM提取和数据存储功能
    实现 NewsProcessingServiceInterface 接口
    """
    def __init__(self, data_services: Any, llm_service: Optional[LLMService] = None):
        """
        初始化新闻处理服务
        
        Args:
            data_services: 知识图谱服务实例，用于数据库操作
            llm_service: LLM服务实例，用于实体、关系提取和摘要生成（可选）
        """
        self.logger = logging.getLogger(__name__)
        self.data_services = data_services
        self._llm_service = llm_service
        self._is_initialized = False
    
    @handle_errors(log_error=True, log_message="新闻处理服务初始化失败: {error}")
    async def initialize(self) -> bool:
        """
        初始化服务
        
        Returns:
            bool: 初始化是否成功
        """
        # 懒加载创建LLM服务
        if self._llm_service is None:
            self._llm_service = create_llm_service()
            self.logger.info("LLM服务已创建")
        
        # 确保LLM服务已初始化
        if hasattr(self._llm_service, 'initialize'):
            if asyncio.iscoroutinefunction(self._llm_service.initialize):
                await self._llm_service.initialize()
            else:
                self._llm_service.initialize()
        
        self._is_initialized = True
        self.logger.info("新闻处理服务初始化成功")
        return True
    
    @handle_errors(log_error=True, log_message="处理新闻并存储失败: {error}")
    async def process_and_store_news(self, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理新闻并存储到知识库
        
        Args:
            news_data: 新闻数据，包含标题、内容、来源、发布时间等信息
            
        Returns:
            Dict[str, Any]: 处理结果，包含新闻对象、提取的实体、关系和摘要
        
        Raises:
            ValueError: 当输入数据无效时
            RuntimeError: 当处理过程中发生错误时
        """
        # 参数验证
        if not news_data or not isinstance(news_data, dict):
            raise ValueError("无效的新闻数据格式")
            
        title = news_data.get("title", "")
        content = news_data.get("content", "")
        source_url = news_data.get("source_url", "")
        publish_date = news_data.get("publish_date", None)
        source = news_data.get("source", "unknown")
        author = news_data.get("author", None)

        # 内容验证
        if not title or not content:
            raise ValueError("新闻标题和内容不能为空")
            
        # Convert string publish_date to datetime object if needed
        if publish_date and isinstance(publish_date, str):
            try:
                publish_date = dateutil.parser.isoparse(publish_date)
            except ValueError:
                self.logger.warning(f"Invalid publish_date format: {publish_date}, using None instead")
                publish_date = None
        
        self.logger.info(f"开始处理新闻: {title[:20]}...")
        
        # 1. 存储新闻基本信息
        news = await self.data_services.create_news(title, content, source_url, publish_date, source, author)
        self.logger.info(f"新闻基本信息已存储，新闻ID: {news.id}")
        
        # 2. 确保LLM服务已初始化
        if not self._is_initialized:
            if not await self.initialize():
                self.logger.error("LLM服务初始化失败，无法继续处理")
                raise RuntimeError("LLM服务初始化失败，无法继续处理新闻")
        
        # 3. 并行执行LLM提取任务（实体、关系、摘要）
        self.logger.info("开始并行执行LLM提取任务...")
        
        # 确保LLM服务可用
        if self._llm_service is None:
            self.logger.error("LLM服务未正确初始化")
            raise RuntimeError("LLM服务未正确初始化，无法提取实体")
        
        # 实体、关系、摘要并行提取
        tasks = [
            self._llm_service.extract_entities(content),
            self._llm_service.extract_relations(content),  # 关系提取内部会自动处理实体
            self._llm_service.summarize_text(content)
        ]
        
        # 等待所有任务完成
        entities_result, relations_result, summary_result = await asyncio.gather(
            *tasks, return_exceptions=True
        )
        
        # 处理异常结果
        if isinstance(entities_result, Exception):
            self.logger.error(f"实体提取失败: {entities_result}")
            entities = []
        else:
            entities = entities_result.get('entities', [])
            self.logger.info(f"原始实体数量: {len(entities)}")
            
            # 确保实体数据格式正确
            entities = self._validate_entity_format(entities)
            self.logger.info(f"已提取实体: {len(entities)} 个")
        
        if isinstance(relations_result, Exception):
            self.logger.error(f"关系提取失败: {relations_result}")
            relations = []
        else:
            relations = relations_result.get('relations', [])
            self.logger.info(f"原始关系数量: {len(relations)}")
            
            # 确保关系数据格式正确
            relations = self._validate_relation_format(relations)
            self.logger.info(f"已提取关系: {len(relations)} 个")
        
        if isinstance(summary_result, Exception):
            self.logger.error(f"摘要生成失败: {summary_result}")
            summary = ""
        else:
            summary = summary_result.get('summary', "")
            self.logger.info(f"已生成新闻摘要")
        
        # 3. 存储提取的实体和关系到数据库
        stored_news, stored_entities, stored_relations = await self.data_services.store_llm_extracted_data(news.id, entities, relations)
        self.logger.info(f"提取数据已存储，实体: {len(stored_entities)}, 关系: {len(stored_relations)}")
        
        # 4. 返回处理结果
        return {
            "news_id": news.id,
            "news": news,
            "entities": stored_entities,
            "relations": stored_relations,
            "summary": summary,
            "status": "success"
        }
    
    @handle_errors(log_error=True, log_message="验证新闻数据失败: {error}")
    async def validate_news_data(self, news_data: Dict[str, Any]) -> bool:
        """
        验证新闻数据格式
        
        Args:
            news_data: 要验证的新闻数据
            
        Returns:
            bool: 数据是否有效
            
        Raises:
            ValueError: 当数据格式严重错误时
        """
        if not news_data or not isinstance(news_data, dict):
            raise ValueError("新闻数据必须是非空字典")
            
        # 检查必要字段
        if not news_data.get("title") or not news_data.get("content"):
            return False
            
        # 检查标题和内容长度
        title = news_data.get("title", "")
        content = news_data.get("content", "")
        
        if len(title) < 2 or len(title) > 1000:
            return False
            
        if len(content) < 10 or len(content) > 100000:
            return False
            
        # 检查发布日期格式（如果提供）
        publish_date = news_data.get("publish_date")
        if publish_date and isinstance(publish_date, str):
            try:
                dateutil.parser.isoparse(publish_date)
            except ValueError:
                return False
                
        # 检查来源URL格式（如果提供）
        source_url = news_data.get("source_url", "")
        if source_url and not (source_url.startswith("http://") or source_url.startswith("https://")):
            return False
            
        return True
    
    @handle_errors(log_error=True, log_message="获取新闻处理状态失败: {error}")
    async def get_processing_status(self, news_id: str) -> Dict[str, Any]:
        """
        获取新闻处理状态
        
        Args:
            news_id: 新闻ID
            
        Returns:
            Dict[str, Any]: 处理状态信息
            
        Raises:
            ValueError: 当新闻ID无效时
            RuntimeError: 当查询失败时
        """
        if not news_id or not isinstance(news_id, str):
            raise ValueError("无效的新闻ID")
            
        try:
            # 从数据库获取新闻信息
            news = await self.data_services.get_news_by_id(news_id)
            if not news:
                raise ValueError(f"未找到ID为 {news_id} 的新闻")
                
            # 获取相关实体和关系
            entities = await self.data_services.get_entities_by_news_id(news_id)
            relations = await self.data_services.get_relations_by_news_id(news_id)
            
            # 确定处理状态
            status = "completed"
            if not entities and not relations:
                status = "pending"
            elif not (entities and relations):
                status = "partial"
                
            return {
                "news_id": news_id,
                "title": news.title,
                "status": status,
                "processed_at": news.created_at.isoformat() if hasattr(news, 'created_at') else None,
                "entities_count": len(entities),
                "relations_count": len(relations)
            }
            
        except Exception as e:
            self.logger.error(f"获取新闻处理状态失败: {e}")
            raise RuntimeError(f"查询新闻处理状态失败: {str(e)}") from e
    
    @handle_errors(log_error=True, log_message="批量处理新闻失败: {error}")
    async def batch_process_news(self, news_list: list[Dict[str, Any]], batch_size: int = 10) -> list[Dict[str, Any]]:
        """
        批量处理新闻列表
        
        Args:
            news_list: 新闻数据列表
            batch_size: 批次大小
            
        Returns:
            list[Dict[str, Any]]: 处理结果列表
            
        Raises:
            ValueError: 当输入列表无效时
            RuntimeError: 当批量处理失败时
        """
        if not isinstance(news_list, list):
            raise ValueError("news_list必须是列表类型")
            
        if batch_size <= 0 or not isinstance(batch_size, int):
            raise ValueError("batch_size必须是正整数")
            
        if not news_list:
            return []
            
        results = []
        total_news = len(news_list)
        self.logger.info(f"开始批量处理 {total_news} 条新闻，批次大小: {batch_size}")
        
        # 分批处理
        for i in range(0, total_news, batch_size):
            batch = news_list[i:i + batch_size]
            batch_results = []
            
            # 创建当前批次的所有处理任务
            tasks = []
            for news_data in batch:
                # 先验证数据
                try:
                    if await self.validate_news_data(news_data):
                        tasks.append(self.process_and_store_news(news_data))
                    else:
                        # 无效数据，添加错误结果
                        batch_results.append({
                            "status": "error",
                            "error": "无效的新闻数据格式",
                            "news_data": {"title": news_data.get("title", "未知标题")}
                        })
                except Exception as e:
                    batch_results.append({
                        "status": "error",
                        "error": str(e),
                        "news_data": {"title": news_data.get("title", "未知标题")}
                    })
            
            # 并行处理当前批次的有效数据
            if tasks:
                # 使用并发限制处理当前批次
                batch_process_results = await self._process_tasks_with_concurrency_limit(tasks, batch_size)
                
                # 处理每个任务的结果
                for j, result in enumerate(batch_process_results):
                    if isinstance(result, Exception):
                        batch_results.append({
                            "status": "error",
                            "error": str(result),
                            "news_data": {"title": batch[j].get("title", "未知标题")}
                        })
                    else:
                        batch_results.append(result)
            
            results.extend(batch_results)
            self.logger.info(f"已完成批次处理，进度: {min(i + batch_size, total_news)}/{total_news}")
            
        self.logger.info(f"批量处理完成，共 {len(results)} 条结果")
        return results


    def _validate_entity_format(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        验证并修正实体数据格式
        
        Args:
            entities: 实体列表
            
        Returns:
            修正后的实体列表
        """
        for entity in entities:
            # 确保properties字段是字典类型
            props = entity.get('properties', {})
            if isinstance(props, str):
                try:
                    entity['properties'] = json.loads(props)
                except (json.JSONDecodeError, TypeError):
                    entity['properties'] = {}
            elif not isinstance(props, dict):
                entity['properties'] = {}
            
            # 确保有entity_type字段
            if 'type' in entity and 'entity_type' not in entity:
                entity['entity_type'] = entity['type']
            if 'entity_type' not in entity:
                entity['entity_type'] = 'default'
        
        return entities
    
    def _validate_relation_format(self, relations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        验证并修正关系数据格式
        
        Args:
            relations: 关系列表
            
        Returns:
            修正后的关系列表
        """
        for relation in relations:
            # 确保properties字段是字典类型
            props = relation.get('properties', {})
            if isinstance(props, str):
                try:
                    relation['properties'] = json.loads(props)
                except (json.JSONDecodeError, TypeError):
                    relation['properties'] = {}
            elif not isinstance(props, dict):
                relation['properties'] = {}
        
        return relations
    
    async def _process_tasks_with_concurrency_limit(self, tasks: List[asyncio.Task], limit: int) -> List[Any]:
        """
        限制并发数处理任务列表
        
        Args:
            tasks: 任务列表
            limit: 最大并发数
            
        Returns:
            任务结果列表
        """
        # 如果任务数少于限制，直接处理
        if len(tasks) <= limit:
            return await asyncio.gather(*tasks, return_exceptions=True)
        
        # 分批处理以控制并发
        results = []
        for i in range(0, len(tasks), limit):
            batch = tasks[i:i + limit]
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            results.extend(batch_results)
        
        return results

def create_news_processing_service(data_services: Any, llm_service: Optional[LLMService] = None) -> NewsProcessingServiceInterface:
    """
    创建新闻处理服务实例的工厂函数
    
    Args:
        data_services: 数据服务实例，用于数据库操作
        llm_service: LLM服务实例（可选，如果不提供则自动创建）
        
    Returns:
        NewsProcessingServiceInterface: 新闻处理服务实例
        
    Raises:
        RuntimeError: 当创建服务实例失败时
    """
    @handle_errors(log_error=True, log_message="创建新闻处理服务失败: {error}")
    def create_service(data_services: Any, llm_service: Optional[LLMService] = None) -> NewsProcessingServiceInterface:
        """
        内部函数：创建新闻处理服务实例
        """
        # 创建新闻处理服务实例
        service = NewsProcessingService(data_services, llm_service)
        
        # 注册服务到服务注册表
        register_service('news_processing_service', service)
        logger.info("新闻处理服务已成功创建并注册")
        
        return service
    
    # 调用内部函数并返回结果
    return create_service(data_services, llm_service)
