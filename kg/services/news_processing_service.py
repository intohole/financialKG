import logging
import dateutil.parser
from datetime import datetime
from typing import Dict, Any, Optional, List
import asyncio
from .llm_service import LLMService
# 移除KnowledgeGraphService导入，避免循环导入

class NewsProcessingService:
    """
    新闻处理服务，整合LLM提取和数据存储功能
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
        self.llm_service = llm_service or LLMService()
    
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
        try:
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
            
            # 2. 并行执行LLM提取任务（实体、关系、摘要）
            self.logger.info("开始并行执行LLM提取任务...")
            entities_task = self.llm_service.extract_entities(content)
            relations_task = self.llm_service.extract_relations(content, None)  # 先不传入实体，让LLM自行提取
            summary_task = self.llm_service.generate_news_summary(content)
            
            # 等待所有任务完成
            entities_result, relations_result, summary_result = await asyncio.gather(
                entities_task, relations_task, summary_task, return_exceptions=True
            )
            
            # 处理异常结果
            if isinstance(entities_result, Exception):
                self.logger.error(f"实体提取失败: {entities_result}")
                entities = []
            else:
                import json
                entities = entities_result.get('entities', [])
                self.logger.info(f"原始实体数量: {len(entities)}")
                # 确保实体数据格式正确
                for i, entity in enumerate(entities):
                    # 确保properties字段是字典类型
                    props = entity.get('properties', {})
                    self.logger.info(f"实体 {i} 原始properties类型: {type(props).__name__}")
                    
                    if isinstance(props, str):
                        try:
                            entity['properties'] = json.loads(props)
                            self.logger.info(f"实体 {i} properties转换成功")
                        except (json.JSONDecodeError, TypeError) as e:
                            self.logger.warning(f"实体 {i} properties解析失败: {e}")
                            entity['properties'] = {}
                    elif not isinstance(props, dict):
                        self.logger.warning(f"实体 {i} properties不是字典，重置为空字典")
                        entity['properties'] = {}
                    
                    # 确保有entity_type字段，如果只有type则进行映射
                    if 'type' in entity and 'entity_type' not in entity:
                        entity['entity_type'] = entity['type']
                    # 如果没有类型信息，设置默认值
                    if 'entity_type' not in entity:
                        entity['entity_type'] = 'default'
                self.logger.info(f"已提取实体: {len(entities)} 个")
            
            if isinstance(relations_result, Exception):
                self.logger.error(f"关系提取失败: {relations_result}")
                relations = []
            else:
                import json
                relations = relations_result.get('relations', [])
                self.logger.info(f"原始关系数量: {len(relations)}")
                # 确保关系数据格式正确
                for i, relation in enumerate(relations):
                    # 确保properties字段是字典类型
                    props = relation.get('properties', {})
                    self.logger.info(f"关系 {i} 原始properties类型: {type(props).__name__}")
                    
                    if isinstance(props, str):
                        try:
                            relation['properties'] = json.loads(props)
                            self.logger.info(f"关系 {i} properties转换成功")
                        except (json.JSONDecodeError, TypeError) as e:
                            self.logger.warning(f"关系 {i} properties解析失败: {e}")
                            relation['properties'] = {}
                    elif not isinstance(props, dict):
                        self.logger.warning(f"关系 {i} properties不是字典，重置为空字典")
                        relation['properties'] = {}
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
            
        except ValueError as e:
            self.logger.error(f"参数验证失败: {e}")
            raise
        except Exception as e:
            self.logger.error(f"处理新闻时发生错误: {e}")
            # 对于其他异常，包装成RuntimeError并提供更详细的信息
            raise RuntimeError(f"新闻处理失败: {str(e)}") from e
