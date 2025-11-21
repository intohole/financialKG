"""
Prompt Manager 单元测试
测试提示词管理器的各项功能
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest import mock

from app.llm.prompt_manager import PromptManager
from app.llm.exceptions import PromptError


@pytest.fixture
def temp_prompt_dir():
    """临时提示词目录"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建测试提示词文件
        prompt_dir = Path(temp_dir)
        
        # 创建基础提示词文件
        with open(prompt_dir / "test_prompt.txt", "w") as f:
            f.write("这是一个测试提示词，包含变量 {variable}")
        
        # 创建不同扩展名的提示词文件
        with open(prompt_dir / "test_prompt.md", "w") as f:
            f.write("# Markdown 提示词\n这是一个 {format} 的提示词")
        
        # 创建无变量的提示词文件
        with open(prompt_dir / "fixed_prompt.txt", "w") as f:
            f.write("这是一个固定的提示词，不包含任何变量")
        
        # 创建子目录和其中的提示词
        sub_dir = prompt_dir / "subdirectory"
        sub_dir.mkdir()
        with open(sub_dir / "sub_prompt.txt", "w") as f:
            f.write("子目录中的提示词: {value}")
        
        yield temp_dir


@pytest.fixture
def prompt_manager(temp_prompt_dir):
    """PromptManager实例"""
    return PromptManager(prompt_dir=temp_prompt_dir)


class TestPromptManager:
    """PromptManager测试类"""
    
    def test_initialization(self, temp_prompt_dir):
        """测试初始化"""
        # 正常初始化
        manager = PromptManager(prompt_dir=temp_prompt_dir)
        assert manager._prompt_dir == temp_prompt_dir
        assert isinstance(manager._prompts, dict)
        
        # 非存在目录初始化
        non_existent_dir = os.path.join(temp_prompt_dir, "non_existent")
        with pytest.raises(ValueError):
            PromptManager(prompt_dir=non_existent_dir)
    
    def test_load_prompts(self, prompt_manager, temp_prompt_dir):
        """测试加载提示词"""
        # 检查是否加载了所有提示词
        assert "test_prompt" in prompt_manager._prompts
        assert "test_prompt.md" in prompt_manager._prompts
        assert "fixed_prompt" in prompt_manager._prompts
        assert "subdirectory/sub_prompt" in prompt_manager._prompts
        
        # 检查提示词内容
        assert prompt_manager._prompts["test_prompt"] == "这是一个测试提示词，包含变量 {variable}"
    
    def test_get_prompt(self, prompt_manager):
        """测试获取提示词"""
        # 获取存在的提示词
        prompt = prompt_manager.get_prompt("test_prompt")
        assert prompt == "这是一个测试提示词，包含变量 {variable}"
        
        # 获取带扩展名的提示词
        prompt = prompt_manager.get_prompt("test_prompt.md")
        assert prompt == "# Markdown 提示词\n这是一个 {format} 的提示词"
        
        # 获取子目录中的提示词
        prompt = prompt_manager.get_prompt("subdirectory/sub_prompt")
        assert prompt == "子目录中的提示词: {value}"
        
        # 获取不存在的提示词
        with pytest.raises(PromptError):
            prompt_manager.get_prompt("non_existent_prompt")
    
    def test_format_prompt(self, prompt_manager):
        """测试格式化提示词"""
        # 测试基本格式化
        formatted = prompt_manager.format_prompt("test_prompt", variable="测试值")
        assert formatted == "这是一个测试提示词，包含变量 测试值"
        
        # 测试多个变量格式化
        formatted = prompt_manager.format_prompt(
            "test_prompt.md", 
            format="Markdown格式"
        )
        assert formatted == "# Markdown 提示词\n这是一个 Markdown格式 的提示词"
        
        # 测试无变量格式化
        formatted = prompt_manager.format_prompt("fixed_prompt")
        assert formatted == "这是一个固定的提示词，不包含任何变量"
        
        # 测试缺少变量的情况
        with pytest.raises(PromptError):
            prompt_manager.format_prompt("test_prompt")
        
        # 测试额外变量的情况
        formatted = prompt_manager.format_prompt(
            "test_prompt", 
            variable="测试值", 
            extra_var="额外值"
        )
        assert formatted == "这是一个测试提示词，包含变量 测试值"
    
    def test_get_all_prompts(self, prompt_manager):
        """测试获取所有提示词"""
        prompts = prompt_manager.get_all_prompts()
        expected_prompts = [
            "test_prompt", 
            "test_prompt.md", 
            "fixed_prompt", 
            "subdirectory/sub_prompt"
        ]
        
        for prompt_name in expected_prompts:
            assert prompt_name in prompts
        assert len(prompts) == len(expected_prompts)
    
    def test_add_prompt(self, prompt_manager, temp_prompt_dir):
        """测试添加提示词"""
        # 添加新提示词
        new_prompt_content = "新添加的提示词，变量: {new_var}"
        prompt_manager.add_prompt("new_prompt", new_prompt_content)
        
        # 检查内存中是否存在
        assert "new_prompt" in prompt_manager._prompts
        assert prompt_manager._prompts["new_prompt"] == new_prompt_content
        
        # 检查文件是否创建
        new_prompt_path = os.path.join(temp_prompt_dir, "new_prompt.txt")
        assert os.path.exists(new_prompt_path)
        with open(new_prompt_path, "r") as f:
            assert f.read() == new_prompt_content
        
        # 添加到子目录
        prompt_manager.add_prompt("new_subdir/new_prompt", "子目录中的新提示词")
        assert "new_subdir/new_prompt" in prompt_manager._prompts
        new_sub_prompt_path = os.path.join(temp_prompt_dir, "new_subdir", "new_prompt.txt")
        assert os.path.exists(new_sub_prompt_path)
    
    def test_delete_prompt(self, prompt_manager, temp_prompt_dir):
        """测试删除提示词"""
        # 删除存在的提示词
        prompt_manager.delete_prompt("test_prompt")
        
        # 检查内存中是否移除
        assert "test_prompt" not in prompt_manager._prompts
        
        # 检查文件是否删除
        test_prompt_path = os.path.join(temp_prompt_dir, "test_prompt.txt")
        assert not os.path.exists(test_prompt_path)
        
        # 删除不存在的提示词
        with pytest.raises(PromptError):
            prompt_manager.delete_prompt("non_existent_prompt")
    
    def test_update_prompt(self, prompt_manager, temp_prompt_dir):
        """测试更新提示词"""
        # 更新存在的提示词
        updated_content = "更新后的提示词，变量: {updated_var}"
        prompt_manager.update_prompt("test_prompt", updated_content)
        
        # 检查内存中是否更新
        assert prompt_manager._prompts["test_prompt"] == updated_content
        
        # 检查文件内容是否更新
        test_prompt_path = os.path.join(temp_prompt_dir, "test_prompt.txt")
        with open(test_prompt_path, "r") as f:
            assert f.read() == updated_content
        
        # 更新不存在的提示词
        with pytest.raises(PromptError):
            prompt_manager.update_prompt("non_existent_prompt", "内容")
    
    def test_prompt_exists(self, prompt_manager):
        """测试提示词是否存在"""
        # 存在的提示词
        assert prompt_manager.prompt_exists("test_prompt")
        
        # 不存在的提示词
        assert not prompt_manager.prompt_exists("non_existent_prompt")
    
    @mock.patch('os.path.getmtime')
    def test_check_for_updates(self, mock_getmtime, prompt_manager):
        """测试检查提示词更新"""
        # 设置初始的修改时间
        mock_getmtime.return_value = 1000
        
        # 首次检查不会重新加载
        with mock.patch.object(prompt_manager, '_load_prompts') as mock_load:
            prompt_manager.check_for_updates()
            mock_load.assert_not_called()
        
        # 模拟文件修改
        mock_getmtime.return_value = 2000
        
        # 再次检查应该重新加载
        with mock.patch.object(prompt_manager, '_load_prompts') as mock_load:
            prompt_manager.check_for_updates()
            mock_load.assert_called_once()
    
    def test_clear_cache(self, prompt_manager):
        """测试清除缓存"""
        # 确认缓存不为空
        assert len(prompt_manager._prompts) > 0
        
        # 清除缓存
        prompt_manager.clear_cache()
        
        # 确认缓存已清空
        assert len(prompt_manager._prompts) == 0
        assert len(prompt_manager._last_modified) == 0
    
    def test_invalid_prompt_format(self, prompt_manager):
        """测试无效的提示词格式"""
        # 测试无效的变量格式
        with pytest.raises(PromptError):
            prompt_manager.format_prompt("test_prompt", **{"invalid{var}": "值"})
    
    def test_prompt_with_special_characters(self, prompt_manager, temp_prompt_dir):
        """测试包含特殊字符的提示词"""
        # 添加包含特殊字符的提示词
        special_content = "特殊字符测试: !@#$%^&*()_+{}[]|\\:;\"'<>,.?/~`"
        prompt_manager.add_prompt("special_prompt", special_content)
        
        # 获取并验证
        assert prompt_manager.get_prompt("special_prompt") == special_content
        
        # 格式化包含特殊字符的提示词
        special_template = "特殊模板 {var} 包含 & < > ""
        prompt_manager.add_prompt("special_template", special_template)
        formatted = prompt_manager.format_prompt("special_template", var="测试")
        assert formatted == "特殊模板 测试 包含 & < > ""