"""
LangChain基础服务
封装LangChain的通用功能
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from langchain_core.messages import SystemMessage
from langchain_core.prompts import (ChatPromptTemplate,
                                    HumanMessagePromptTemplate, PromptTemplate)
from langchain_core.runnables import RunnablePassthrough

from .base_service import BaseLLMService
from .json_parser import json_parser
from .langchain_config import langchain_config


class LangChainBaseService(BaseLLMService):
    """LangChain基础服务类"""

    def __init__(self):
        """初始化LangChain基础服务"""
        super().__init__()  # 调用BaseLLMService的初始化方法
        self.llm_config = langchain_config
        self.llm = (
            self.llm_config.get_llm()
        )  # Initialize LLM instance using lazy initialization
        self.json_parser = json_parser

    def get_llm(self):
        """
        获取LLM实例

        Returns:
            LLM实例
        """
        return self.llm

    async def extract_structured_data(
        self,
        system_prompt: str,
        human_prompt: str,
        input_data: Dict[str, Any],
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Extract structured data from text using LLM

        Args:
            system_prompt (str): System prompt
            human_prompt (str): Human prompt template or pre-formatted string
            input_data (dict): Input data for prompt template
            **kwargs: Additional parameters for LLM

        Returns:
            dict: Structured data extracted from text
        """
        try:
            # 组合系统提示词与JSON格式说明
            full_system_prompt = (
                system_prompt + "\n\n" + self.json_parser.get_format_instructions()
            )

            # 创建系统消息（原始字符串，不是模板）
            system_message = SystemMessage(content=full_system_prompt)

            # 创建人类提示模板（从模板推断变量）
            human_message_prompt = HumanMessagePromptTemplate.from_template(
                template=human_prompt
            )

            # 创建聊天提示模板
            chat_prompt = ChatPromptTemplate(
                messages=[system_message, human_message_prompt]
            )

            # 创建链
            chain = chat_prompt | self.llm

            # 生成响应 - only pass input_data if there are variables to replace
            if (
                hasattr(human_message_prompt.prompt, "input_variables")
                and len(human_message_prompt.prompt.input_variables) > 0
            ):
                response = await chain.ainvoke(input_data)
            else:
                response = await chain.ainvoke({})

            # 调试：打印响应内容
            print("LLM Response:", response.content)

            # 解析JSON响应
            return self.json_parser.parse(response.content)
        except Exception as e:
            raise Exception(f"提取结构化数据失败: {str(e)}") from e

    async def generate_response(
        self, system_prompt, user_prompt, input_data=None, stream=False
    ):
        """
        Generate response from LLM

        Args:
            system_prompt (str): System prompt
            user_prompt (str): User prompt
            input_data (dict, optional): Input data for prompt template. Defaults to None.
            stream (bool, optional): Whether to stream response. Defaults to False.

        Returns:
            Response: Standardized response object
        """
        # Create prompt template
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", user_prompt),
            ]
        )

        # Create chain
        chain = prompt | self.llm

        # Use input_data if provided, otherwise empty dict
        prompt_input = input_data or {}

        # Generate response
        if stream:
            # Handle streaming response
            response_chunks = []
            async for chunk in chain.astream(prompt_input):
                response_chunks.append(chunk.content)
            content = "".join(response_chunks)
        else:
            # Handle regular response
            response = await chain.ainvoke(prompt_input)
            content = response.content

        # 标准化响应格式
        return {
            "content": content,
            "model": self.llm_config.model,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }
