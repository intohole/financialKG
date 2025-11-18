"""
基于LangChain的大模型服务配置模块
提供LangChain与OpenAI API的集成配置
"""
import os
from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import BaseOutputParser
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
import yaml
from pathlib import Path
from kg.core.config import BaseConfig


class LangChainConfig(BaseConfig):
    """LangChain配置类"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化LangChain配置
        
        Args:
            config_path: 配置文件路径，默认为项目根目录下的config.yaml
        """
        super().__init__(config_path)
        self._llm = None  # 延迟初始化LLM实例
    
    def _init_llm(self) -> ChatOpenAI:
        """初始化LangChain的OpenAI模型"""
        if not self.api_key:
            raise ValueError("未找到OpenAI API密钥，请在配置文件中设置或通过环境变量OPENAI_API_KEY提供")
        
        llm_config = {
            'model_name': self.model,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'openai_api_key': self.api_key
        }
        
        if self.base_url:
            llm_config['openai_api_base'] = self.base_url
            
        return ChatOpenAI(**llm_config)
    
    def get_llm(self) -> ChatOpenAI:
        """获取LangChain的LLM实例"""
        if self._llm is None:
            self._llm = self._init_llm()
        return self._llm
    
    def create_prompt_template(self, template: str, input_variables: list) -> PromptTemplate:
        """
        创建提示词模板
        
        Args:
            template: 提示词模板字符串
            input_variables: 输入变量列表
            
        Returns:
            PromptTemplate实例
        """
        return PromptTemplate(
            template=template,
            input_variables=input_variables
        )
    
    def create_chat_prompt_template(self, system_template: str, human_template: str) -> ChatPromptTemplate:
        """
        创建聊天提示词模板
        
        Args:
            system_template: 系统提示词模板
            human_template: 用户提示词模板
            
        Returns:
            ChatPromptTemplate实例
        """
        return ChatPromptTemplate.from_messages([
            ("system", system_template),
            ("human", human_template)
        ])
    
    def create_chain(self, prompt: PromptTemplate):
        """
        创建LLM链
        
        Args:
            prompt: 提示词模板
            
        Returns:
            可运行链实例
        """
        return prompt | self.get_llm() | RunnablePassthrough()


class JsonOutputParser(BaseOutputParser):
    """JSON输出解析器"""
    
    def parse(self, text: str) -> Dict[str, Any]:
        """解析文本为JSON格式"""
        import json
        import re
        
        # 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # 尝试从文本中提取JSON部分
        json_pattern = r'```json\s*(.*?)\s*```'
        match = re.search(json_pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        
        # 尝试查找JSON对象
        json_pattern = r'\{.*\}'
        match = re.search(json_pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        
        # 如果无法解析，返回原始文本
        return {"result": text}
    
    def get_format_instructions(self) -> str:
        """获取格式说明"""
        return "请以JSON格式返回结果"


# 全局配置实例
langchain_config = LangChainConfig()