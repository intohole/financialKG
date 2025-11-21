"""
配置管理模块
提供类型安全的配置读取和管理功能
"""

from .config_manager import ConfigManager, ConfigError

__all__ = ["ConfigManager", "ConfigError"]