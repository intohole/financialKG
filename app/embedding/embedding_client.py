"""
Embedding 客户端
负责与第三方大模型API交互，获取文本嵌入向量
"""

import logging
import time
from typing import List, Dict, Any, Optional
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import (HuggingFaceBgeEmbeddings,
                                          QianfanEmbeddingsEndpoint,
                                          ZhipuAIEmbeddings)

from app.config.config_manager import ConfigManager
from .exceptions import EmbeddingError

logger = logging.getLogger(__name__)


class EmbeddingClient:
    """
    Embedding 客户端类
    封装不同大模型的嵌入接口，提供统一的调用方式
    """
    
    def __init__(self, config_manager: ConfigManager):
        """
        初始化 Embedding 客户端
        
        Args:
            config_manager: 配置管理器实例
        """
        self._config_manager = config_manager
        self._embeddings: Optional[Embeddings] = None
        self._config: Dict[str, Any] = {}
        self._init_embeddings()
    
    def _init_embeddings(self):
        """
        初始化嵌入模型
        根据配置选择不同的嵌入模型提供商
        """
        try:
            # 使用类型安全的配置访问方法
            embedding_config = self._config_manager.get_embedding_config()
            
            # 构建配置字典
            self._config = {
                'model': embedding_config.model,
                'api_key': embedding_config.api_key,
                'base_url': embedding_config.base_url,
                'timeout': embedding_config.timeout,
                'max_retries': embedding_config.max_retries,
                'dimension': embedding_config.dimension,
                'normalize': embedding_config.normalize,
                'secret_key': embedding_config.secret_key,
                'endpoint': embedding_config.endpoint
            }
            
            # 根据模型名称判断使用哪个提供商的嵌入模型
            model_name = self._config['model'].lower()
            
            # 特殊处理embedding-3模型
            if model_name == 'embedding-3':
                # embedding-3模型使用OpenAI兼容接口
                self._embeddings = OpenAIEmbeddings(
                    model=self._config['model'],
                    api_key=self._config['api_key'],
                    base_url=self._config['base_url'] or None,
                    timeout=self._config['timeout']
                )
                logger.info(f"初始化 embedding-3 模型: {self._config['model']}")
                
            elif 'openai' in model_name or 'ada' in model_name:
                # OpenAI Embedding
                self._embeddings = OpenAIEmbeddings(
                    model=self._config['model'],
                    api_key=self._config['api_key'],
                    base_url=self._config['base_url'] or None,
                    timeout=self._config['timeout']
                )
                logger.info(f"初始化 OpenAI Embedding: {self._config['model']}")
                
            elif 'glm' in model_name or 'zhipu' in model_name:
                # 智谱AI Embedding
                self._embeddings = ZhipuAIEmbeddings(
                    model=self._config['model'],
                    api_key=self._config['api_key'],
                    base_url=self._config['base_url'] or None
                )
                logger.info(f"初始化 ZhipuAI Embedding: {self._config['model']}")
                
            elif 'qianfan' in model_name or 'baidu' in model_name:
                # 百度千帆 Embedding
                self._embeddings = QianfanEmbeddingsEndpoint(
                    model=self._config['model'],
                    api_key=self._config['api_key'],
                    secret_key=embedding_config.get('secret_key', ''),
                    endpoint=embedding_config.get('endpoint', '')
                )
                logger.info(f"初始化 Qianfan Embedding: {self._config['model']}")
                
            elif 'bge' in model_name:
                # HuggingFace BGE Embedding
                self._embeddings = HuggingFaceBgeEmbeddings(
                    model_name=self._config['model'],
                    model_kwargs={'device': 'cpu'},
                    encode_kwargs={'normalize_embeddings': True}
                )
                logger.info(f"初始化 HuggingFace BGE Embedding: {self._config['model']}")
                
            else:
                # 默认使用OpenAI
                self._embeddings = OpenAIEmbeddings(
                    model=self._config['model'],
                    api_key=self._config['api_key'],
                    base_url=self._config['base_url'] or None,
                    timeout=self._config['timeout']
                )
                logger.info(f"默认使用 OpenAI Embedding: {self._config['model']}")
                
        except Exception as e:
            logger.error(f"初始化嵌入模型失败: {e}")
            raise EmbeddingError(f"初始化嵌入模型失败: {str(e)}")
    
    def embed_text(self, text: str) -> List[float]:
        """
        为单个文本生成嵌入向量
        
        Args:
            text: 要嵌入的文本
            
        Returns:
            嵌入向量列表
            
        Raises:
            EmbeddingError: 嵌入过程中发生错误
        """
        try:
            if not self._embeddings:
                self._init_embeddings()
            
            start_time = time.time()
            
            # 对于embedding-3模型，使用自定义调用以支持dimensions参数
            if self._config['model'].lower() == 'embedding-3' and self._config.get('dimension'):
                embedding = self._embed_text_with_dimensions(text)
            else:
                embedding = self._embeddings.embed_query(text)
            
            # 如果需要归一化
            if self._config.get('normalize', False):
                embedding = self._normalize_vector(embedding)
            
            end_time = time.time()
            logger.debug(f"生成文本嵌入完成，耗时: {end_time - start_time:.3f}s")
            return embedding
            
        except Exception as e:
            logger.error(f"生成文本嵌入失败: {e}")
            raise EmbeddingError(f"生成文本嵌入失败: {str(e)}")
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量为多个文本生成嵌入向量
        
        Args:
            texts: 要嵌入的文本列表
            
        Returns:
            嵌入向量列表的列表
            
        Raises:
            EmbeddingError: 嵌入过程中发生错误
        """
        try:
            if not self._embeddings:
                self._init_embeddings()
            
            start_time = time.time()
            
            # 对于embedding-3模型，使用自定义调用以支持dimensions参数
            if self._config['model'].lower() == 'embedding-3' and self._config.get('dimension'):
                embeddings = [self._embed_text_with_dimensions(text) for text in texts]
            else:
                embeddings = self._embeddings.embed_documents(texts)
            
            # 如果需要归一化
            if self._config.get('normalize', False):
                embeddings = [self._normalize_vector(emb) for emb in embeddings]
            
            end_time = time.time()
            logger.debug(f"批量生成文本嵌入完成，文本数量: {len(texts)}，耗时: {end_time - start_time:.3f}s")
            return embeddings
            
        except Exception as e:
            logger.error(f"批量生成文本嵌入失败: {e}")
            raise EmbeddingError(f"批量生成文本嵌入失败: {str(e)}")
    
    def get_config(self) -> Dict[str, Any]:
        """
        获取客户端配置
        
        Returns:
            配置字典
        """
        return self._config
    
    def refresh_config(self):
        """
        刷新配置并重新初始化嵌入模型
        """
        logger.info("刷新嵌入客户端配置")
        self._init_embeddings()
    
    def _normalize_vector(self, vector: List[float]) -> List[float]:
        """
        归一化向量
        
        Args:
            vector: 输入向量
            
        Returns:
            归一化后的向量
        """
        import numpy as np
        
        vec_np = np.array(vector)
        norm = np.linalg.norm(vec_np)
        
        # 避免除以0
        if norm == 0:
            return vector
        
        return (vec_np / norm).tolist()
    
    def _embed_text_with_dimensions(self, text: str) -> List[float]:
        """
        使用dimensions参数嵌入文本（主要用于embedding-3模型）
        
        Args:
            text: 要嵌入的文本
            
        Returns:
            嵌入向量
        """
        import requests
        import json
        
        # 准备请求参数
        url = f"{self._config['base_url']}embeddings"
        headers = {
            "Authorization": f"Bearer {self._config['api_key']}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self._config["model"],
            "input": text,
            "dimensions": self._config["dimension"]
        }
        
        try:
            # 发送请求
            response = requests.post(
                url=url,
                headers=headers,
                data=json.dumps(data),
                timeout=self._config["timeout"]
            )
            
            # 检查响应状态
            if response.status_code != 200:
                raise EmbeddingError(f"API请求失败: {response.status_code} {response.text}")
            
            # 解析响应
            result = response.json()
            embedding = result["data"][0]["embedding"]
            
            return embedding
        except requests.exceptions.RequestException as e:
            raise EmbeddingError(f"网络请求失败: {str(e)}")
        except (KeyError, IndexError) as e:
            raise EmbeddingError(f"解析响应失败: {str(e)}")
        except Exception as e:
            raise EmbeddingError(f"嵌入文本失败: {str(e)}")
