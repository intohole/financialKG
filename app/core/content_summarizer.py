"""
内容摘要模块 - 基于大模型prompt的文本摘要生成
"""
import re
from typing import List, Dict, Any, Optional

from app.core.base_service import BaseService
from app.core.extract_models import ContentSummary
from app.llm.llm_service import LLMService
from app.utils.logging_utils import get_logger

logger = get_logger(__name__)


class ContentSummarizer(BaseService):
    """
    内容摘要模块，提供基于大模型的文本摘要生成功能
    
    功能：
    - 单文本摘要：为单个文本生成简洁准确的摘要
    - 批量摘要：为多个文本批量生成摘要
    
    使用示例：
        summarizer = ContentSummarizer()
        
        # 单文本摘要
        summary = await summarizer.generate_summary("苹果公司发布了新款iPhone...", max_length=100)
        
        # 批量摘要
        texts = ["文本1...", "文本2...", "文本3..."]
        summaries = await summarizer.generate_batch_summaries(texts, max_length=80)
    """
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        """初始化内容摘要器"""
        super().__init__(llm_service=llm_service)
        logger.info("初始化 ContentSummarizer")
    
    async def generate_summary(self, text: str, max_length: int = 100) -> ContentSummary:
        """
        为单个文本生成摘要
        
        Args:
            text: 要摘要的文本内容
            max_length: 摘要的最大长度（字符数）
            
        Returns:
            ContentSummary: 摘要结果，包含摘要文本、关键词、重要性评分等
            
        Raises:
            ValueError: 当文本为空或max_length无效时
            RuntimeError: 当LLM调用失败时
        """
        try:
            if not text or not text.strip():
                raise ValueError("文本内容不能为空")
            
            if max_length <= 0:
                raise ValueError("摘要长度必须大于0")
            
            logger.info(f"开始生成摘要，文本长度: {len(text)}, 最大长度: {max_length}")
            
            # 使用大模型生成摘要
            response = await self.generate_with_prompt(
                'news_summary_extraction',
                text=text,
                max_length=max_length
            )
            
            # 解析响应
            return await self._parse_summary_response(response, text, max_length)
            
        except Exception as e:
            logger.error(f"摘要生成失败: {e}")
            raise RuntimeError(f"摘要生成失败: {str(e)}")
    
    async def generate_batch_summaries(self, texts: List[str], max_length: int = 100) -> List[ContentSummary]:
        """
        批量为多个文本生成摘要
        
        Args:
            texts: 要摘要的文本列表
            max_length: 每个摘要的最大长度（字符数）
            
        Returns:
            List[ContentSummary]: 摘要结果列表，与输入文本顺序对应
            
        Raises:
            ValueError: 当输入参数无效时
            RuntimeError: 当LLM调用失败时
        """
        try:
            if not texts:
                return []
            
            if max_length <= 0:
                raise ValueError("摘要长度必须大于0")
            
            logger.info(f"开始批量生成摘要，文本数: {len(texts)}")
            
            # 构建批量prompt
            batch_prompts = []
            for text in texts:
                if text and text.strip():
                    prompt = self.prompt_manager.format_prompt(
                        'news_summary_extraction',
                        text=text,
                        max_length=max_length
                    )
                    batch_prompts.append(prompt)
            
            if not batch_prompts:
                return []
            
            # 批量调用LLM
            responses = await self.llm_service.generate_batch(batch_prompts)
            
            # 解析响应
            summaries = []
            for i, response in enumerate(responses):
                try:
                    summary = await self._parse_summary_response(response, texts[i], max_length)
                    summaries.append(summary)
                except Exception as e:
                    logger.warning(f"解析单个摘要失败: {e}")
                    continue
            
            logger.info(f"批量摘要生成完成，成功数: {len(summaries)}")
            return summaries
            
        except Exception as e:
            logger.error(f"批量摘要生成失败: {e}")
            raise RuntimeError(f"批量摘要生成失败: {str(e)}")
    
    async def _parse_summary_response(self, response: str, original_text: str, max_length: int) -> ContentSummary:
        """
        解析摘要生成响应
        
        Args:
            response: 大模型响应文本
            original_text: 原始输入文本
            max_length: 最大摘要长度
            
        Returns:
            ContentSummary: 解析后的摘要结果
        """
        try:
            # 清理响应文本，提取JSON部分
            json_str = self._extract_json_from_response(response)
            if not json_str:
                raise ValueError("无法从响应中提取JSON数据")
            
            # 解析JSON数据
            import json
            data = json.loads(json_str)
            
            # 验证必需字段
            if 'summary' not in data:
                raise ValueError("JSON数据中缺少'summary'字段")
            
            # 提取字段
            summary = data.get('summary', '')
            keywords = data.get('keywords', [])
            importance = data.get('importance', 5)
            reasoning = data.get('reasoning', '')
            
            # 确保关键词是列表格式
            if isinstance(keywords, str):
                keywords = [k.strip() for k in keywords.split('，') if k.strip()]
            elif not isinstance(keywords, list):
                keywords = []
            
            # 确保重要性评分在有效范围内
            if not isinstance(importance, int) or importance < 1 or importance > 5:
                importance = 5
            
            return ContentSummary(
                summary=summary,
                keywords=keywords,
                importance_score=importance,
                importance_reason=reasoning
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            raise ValueError(f"JSON解析失败: {str(e)}")
        except Exception as e:
            logger.error(f"解析摘要响应失败: {e}")
            raise ValueError(f"解析摘要响应失败: {str(e)}")
    
    def _extract_json_from_response(self, response: str) -> Optional[str]:
        """
        从响应文本中提取JSON部分（已废弃，使用json_extractor模块）
        
        Args:
            response: 大模型响应文本
            
        Returns:
            Optional[str]: 提取的JSON字符串，失败时返回None
        """
        logger.warning("_extract_json_from_response 方法已废弃，使用 extract_json_robust 替代")
        try:
            from app.utils.json_extractor import extract_json_robust
            result = extract_json_robust(response)
            if result:
                import json
                return json.dumps(result)
            return None
        except Exception as e:
            logger.warning(f"提取JSON失败: {e}")
            return None
    
    def _extract_field(self, text: str, field_name: str, separators: List[str]) -> Optional[str]:
        """
        从文本中提取指定字段的值
        
        Args:
            text: 要提取的文本
            field_name: 字段名称
            separators: 分隔符列表
            
        Returns:
            Optional[str]: 提取的字段值，失败时返回None
        """
        try:
            lines = text.split('\n')
            for line in lines:
                for separator in separators:
                    if separator in line:
                        content = line.split(separator, 1)[1].strip()
                        if content:
                            return content
            
            logger.warning(f"未找到字段 '{field_name}' 的内容")
            return None
            
        except Exception as e:
            logger.warning(f"提取字段 '{field_name}' 失败: {e}")
            return None
    
    def _extract_number_from_text(self, text: str) -> int:
        """
        从文本中提取数字
        
        Args:
            text: 包含数字的文本
            
        Returns:
            int: 提取的数字，失败时返回0
        """
        try:
            import re
            number_match = re.search(r'\d+', text)
            if number_match:
                return int(number_match.group())
            return None
            
        except Exception as e:
            logger.warning(f"提取数字失败: {e}")
            return None
    
    def parse_llm_response(self, response: str) -> dict:
        """
        实现基础类的抽象方法
        
        Args:
            response: 大模型响应文本
            
        Returns:
            dict: 空字典，摘要器使用专门的解析方法
        """
        # 内容摘要器有专门的解析方法，这里返回空字典
        return {}