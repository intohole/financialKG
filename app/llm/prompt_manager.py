"""提示词管理器

负责从文件系统加载、缓存和管理提示词模板
"""

import os
from pathlib import Path
from typing import Dict, Optional, Union, Any
from contextlib import contextmanager
from app.exceptions import PromptError

from app.utils.logging_utils import get_logger


logger = get_logger(__name__)


class PromptManager:
    """提示词管理器
    
    提供从文件系统加载和管理提示词模板的功能
    """
    
    def __init__(self, prompt_dir: Optional[Union[str, Path]] = None):
        """初始化提示词管理器
        
        Args:
            prompt_dir: 提示词文件目录，默认为项目根目录下的prompt文件夹
        """
        self._prompt_dir = Path(prompt_dir or self._get_default_prompt_dir())
        self._prompts: Dict[str, str] = {}
        self._last_loaded: Dict[str, float] = {}
        
        # 确保提示词目录存在
        if not self._prompt_dir.exists():
            raise PromptError(f"提示词目录不存在: {self._prompt_dir}")
        
        # 初始加载所有提示词
        self.load_all_prompts()
    
    def _get_default_prompt_dir(self) -> Path:
        """获取默认提示词目录
        
        Returns:
            Path: 默认提示词目录路径
        """
        # 项目根目录下的prompt文件夹
        return Path(__file__).parent.parent.parent / 'prompt'
    
    def load_prompt(self, prompt_name: str) -> str:
        """加载指定名称的提示词
        
        Args:
            prompt_name: 提示词名称（不含扩展名）
            
        Returns:
            str: 提示词内容
            
        Raises:
            PromptError: 当提示词文件不存在或读取失败时
        """
        logger.info(f"开始加载提示词: {prompt_name}")
        
        # 尝试不同的扩展名
        for ext in ['.txt', '.md', '.prompt']:
            prompt_file = self._prompt_dir / f"{prompt_name}{ext}"
            if prompt_file.exists():
                try:
                    logger.info(f"找到提示词文件: {prompt_file}")
                    with open(prompt_file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                    self._prompts[prompt_name] = content
                    self._last_loaded[prompt_name] = prompt_file.stat().st_mtime
                    logger.info(f"成功加载提示词: {prompt_name}, 内容长度: {len(content)}, 内容预览: {content[:100]}...")
                    return content
                except Exception as e:
                    raise PromptError(f"读取提示词文件失败: {prompt_file}", prompt_name=prompt_name)
        
        # 尝试直接匹配文件名（包含扩展名）
        prompt_file = self._prompt_dir / prompt_name
        if prompt_file.exists():
            try:
                logger.info(f"找到提示词文件: {prompt_file}")
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                self._prompts[prompt_name] = content
                self._last_loaded[prompt_name] = prompt_file.stat().st_mtime
                logger.info(f"成功加载提示词: {prompt_name}, 内容长度: {len(content)}, 内容预览: {content[:100]}...")
                return content
            except Exception as e:
                raise PromptError(f"读取提示词文件失败: {prompt_file}", prompt_name=prompt_name)
        
        logger.error(f"提示词文件不存在: {prompt_name}")
        raise PromptError(f"提示词文件不存在: {prompt_name}", prompt_name=prompt_name)
    
    def load_all_prompts(self) -> Dict[str, str]:
        """加载所有提示词文件
        
        Returns:
            Dict[str, str]: 所有提示词的字典
        """
        if not self._prompt_dir.exists():
            logger.warning(f"提示词目录不存在: {self._prompt_dir}")
            return {}
        
        for file_path in self._prompt_dir.glob('*'):
            if file_path.is_file():
                try:
                    # 获取文件名（不含扩展名）作为提示词名称
                    prompt_name = file_path.stem
                    self.load_prompt(prompt_name)
                except Exception as e:
                    logger.error(f"加载提示词失败: {file_path}, 错误: {e}")
        
        logger.info(f"成功加载 {len(self._prompts)} 个提示词")
        return self._prompts.copy()
    
    def get_prompt(self, prompt_name: str, reload: bool = False) -> str:
        """获取指定提示词
        
        Args:
            prompt_name: 提示词名称
            reload: 是否强制重新加载
            
        Returns:
            str: 提示词内容
        """
        logger.info(f"获取提示词: {prompt_name}, 重新加载: {reload}, 缓存中是否存在: {prompt_name in self._prompts}")
        
        if reload or prompt_name not in self._prompts:
            logger.info(f"重新加载提示词: {prompt_name}")
            return self.load_prompt(prompt_name)
        
        # 检查文件是否被修改
        for ext in ['.txt', '.md', '.prompt']:
            prompt_file = self._prompt_dir / f"{prompt_name}{ext}"
            if prompt_file.exists():
                if prompt_file.stat().st_mtime > self._last_loaded.get(prompt_name, 0):
                    logger.info(f"提示词文件已修改，重新加载: {prompt_name}")
                    return self.load_prompt(prompt_name)
        
        logger.info(f"从缓存返回提示词: {prompt_name}")
        result = self._prompts[prompt_name]
        logger.info(f"提示词内容预览: {result[:100]}...")
        return result
    
    def format_prompt(self, prompt_name: str, **kwargs) -> str:
        """格式化提示词模板
        
        Args:
            prompt_name: 提示词名称
            **kwargs: 用于格式化的变量
            
        Returns:
            str: 格式化后的提示词
        """
        prompt = self.get_prompt(prompt_name)
        try:
            return prompt.format(**kwargs)
        except KeyError as e:
            raise PromptError(f"提示词格式化失败: 缺少变量 {e}", prompt_name=prompt_name)
        except Exception as e:
            raise PromptError(f"提示词格式化失败: {e}", prompt_name=prompt_name)
    
    def add_prompt(self, prompt_name: str, content: str, save_to_file: bool = False) -> None:
        """添加或更新提示词
        
        Args:
            prompt_name: 提示词名称
            content: 提示词内容
            save_to_file: 是否保存到文件
        """
        self._prompts[prompt_name] = content
        self._last_loaded[prompt_name] = 0
        
        if save_to_file:
            prompt_file = self._prompt_dir / f"{prompt_name}.txt"
            try:
                with open(prompt_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                self._last_loaded[prompt_name] = prompt_file.stat().st_mtime
                logger.info(f"提示词已保存到文件: {prompt_file}")
            except Exception as e:
                raise PromptError(f"保存提示词文件失败: {e}", prompt_name=prompt_name)
    
    def remove_prompt(self, prompt_name: str, remove_file: bool = False) -> bool:
        """移除提示词
        
        Args:
            prompt_name: 提示词名称
            remove_file: 是否同时删除文件
            
        Returns:
            bool: 是否成功移除
        """
        if prompt_name in self._prompts:
            del self._prompts[prompt_name]
            if prompt_name in self._last_loaded:
                del self._last_loaded[prompt_name]
            
            if remove_file:
                for ext in ['.txt', '.md', '.prompt']:
                    prompt_file = self._prompt_dir / f"{prompt_name}{ext}"
                    if prompt_file.exists():
                        try:
                            prompt_file.unlink()
                            logger.info(f"已删除提示词文件: {prompt_file}")
                            return True
                        except Exception as e:
                            logger.error(f"删除提示词文件失败: {e}")
            return True
        
        return False
    
    def list_prompts(self) -> list[str]:
        """列出所有已加载的提示词名称
        
        Returns:
            list[str]: 提示词名称列表
        """
        return list(self._prompts.keys())
    
    def get_prompt_dir(self) -> Path:
        """获取当前提示词目录
        
        Returns:
            Path: 提示词目录路径
        """
        return self._prompt_dir
    
    def set_prompt_dir(self, prompt_dir: Union[str, Path]) -> None:
        """设置新的提示词目录
        
        Args:
            prompt_dir: 新的提示词目录路径
        """
        self._prompt_dir = Path(prompt_dir)
        if not self._prompt_dir.exists():
            raise PromptError(f"提示词目录不存在: {self._prompt_dir}")
        
        # 重置并加载新目录中的提示词
        self._prompts.clear()
        self._last_loaded.clear()
        self.load_all_prompts()
    
    @contextmanager
    def temporary_prompt_dir(self, prompt_dir: Union[str, Path]):
        """临时切换提示词目录
        
        Args:
            prompt_dir: 临时提示词目录路径
        """
        original_dir = self._prompt_dir
        try:
            self.set_prompt_dir(prompt_dir)
            yield self
        finally:
            self._prompt_dir = original_dir
            self._prompts.clear()
            self._last_loaded.clear()
            self.load_all_prompts()