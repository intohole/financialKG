"""
KG核心抽象服务接口
"""

class KGCoreAbstractService:
    """KG核心抽象服务接口"""


    async def process_content(self, content: str) -> None:
        """
        处理输入内容，构建知识图谱
        
        Args:
            content: 输入的文本内容
        """
        raise NotImplementedError("process_content 方法必须在子类中实现")

    
    async def query_knowledge(self, query: str) -> str:
        """
        查询知识图谱
        
        Args:
            query: 查询语句
            
        Returns:
            查询结果
        """
        raise NotImplementedError("query_knowledge 方法必须在子类中实现")