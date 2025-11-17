"""
LangChain基础服务
封装LangChain的通用功能
"""
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.chains import LLMChain
from .base_service import BaseLLMService
from .langchain_config import langchain_config
from .json_parser import json_parser


class LangChainBaseService(BaseLLMService):
    """LangChain基础服务类"""
    
    def __init__(self):
        """初始化LangChain基础服务"""
        super().__init__()  # 调用BaseLLMService的初始化方法
        self.llm_config = langchain_config
        self.llm = self.llm_config.get_llm()  # Initialize LLM instance using lazy initialization
        self.json_parser = json_parser
    
    def get_llm(self):
        """
        获取LLM实例
        
        Returns:
            LLM实例
        """
        return self.llm
    
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
    
    def create_chain(self, prompt: PromptTemplate) -> LLMChain:
        """
        创建LLM链
        
        Args:
            prompt: 提示词模板
            
        Returns:
            LLMChain实例
        """
        return LLMChain(llm=self.llm, prompt=prompt)
    
    def run_chain(self, chain: LLMChain, input_data: dict) -> Dict[str, Any]:
        """
        运行LLM链
        
        Args:
            chain: LLM链实例
            input_data: 输入数据
            
        Returns:
            运行结果
        """
        try:
            return chain.invoke(input_data)
        except Exception as e:
            raise RuntimeError(f"运行LLM链失败: {e}")
    
    def extract_structured_data(self, system_prompt: str, human_prompt: str, input_data: dict) -> Dict[str, Any]:
        """
        提取结构化数据
        
        Args:
            system_prompt: 系统提示词
            human_prompt: 人类提示词
            input_data: 输入数据
            
        Returns:
            结构化数据
        """
        # 创建聊天提示词模板
        chat_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt + "\n\n" + self.json_parser.get_format_instructions()),
            ("human", human_prompt)
        ])
        
        # 创建LLM链
        chain = LLMChain(llm=self.llm, prompt=chat_prompt)
        
        # 运行LLM链
        response = chain.invoke(input_data)
        
        # 解析JSON结果
        return self.json_parser.parse(response["text"])
    
    def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        生成LLM响应
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Returns:
            响应结果
        """
        # 转换为LangChain格式
        chat_prompt = ChatPromptTemplate.from_messages(messages)
        chain = LLMChain(llm=self.llm, prompt=chat_prompt)
        response = chain.invoke({})
        
        # 标准化响应格式
        return {
            "content": response["text"],
            "model": self.llm_config.model,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }