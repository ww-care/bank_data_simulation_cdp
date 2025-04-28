#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
配置管理模块

负责读取和管理系统的各类配置信息。
"""

import os
import yaml
import configparser
from typing import Dict, List, Any, Optional


class ConfigManager:
    """配置管理器类，处理系统各类配置"""
    
    def __init__(self, config_dir: str = None):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录，默认为项目根目录下的config目录
        """
        if config_dir is None:
            # 默认配置目录为当前工作目录的config子目录
            self.config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config')
        else:
            self.config_dir = config_dir
            
        # 加载系统配置
        self.config = self._load_system_config()
        
        # 加载数据库配置
        self.db_config = self._load_db_config()
        
    def _load_system_config(self) -> Dict:
        """
        加载系统配置文件
        
        Returns:
            系统配置字典
        """
        config_path = os.path.join(self.config_dir, 'bank_data_simulation_config.yaml')
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config
        except Exception as e:
            print(f"Error loading system config: {str(e)}")
            return {}
    
    def _load_db_config(self) -> Dict:
        """
        加载数据库配置文件
        
        Returns:
            数据库配置字典
        """
        db_config_path = os.path.join(self.config_dir, 'database.ini')
        
        try:
            config = configparser.ConfigParser()
            config.read(db_config_path)
            
            # 读取MySQL配置段
            if 'mysql' in config:
                return dict(config['mysql'])
            else:
                print("MySQL configuration section not found")
                return {}
        except Exception as e:
            print(f"Error loading database config: {str(e)}")
            return {}
    
    def get_system_config(self) -> Dict:
        """
        获取系统配置
        
        Returns:
            系统配置字典
        """
        return self.config
    
    def get_db_config(self) -> Dict:
        """
        获取数据库配置
        
        Returns:
            数据库配置字典
        """
        return self.db_config
    
    def get_entity_config(self, entity_name: str) -> Dict:
        """
        获取指定实体的配置
        
        Args:
            entity_name: 实体名称
            
        Returns:
            实体配置字典
        """
        if entity_name in self.config:
            return self.config[entity_name]
        return {}
    
    def get_cdp_model_config(self, model_type: str) -> Dict:
        """
        获取指定CDP模型类型的配置
        
        Args:
            model_type: CDP模型类型 (customer_profile, business_doc, event, general_archive)
            
        Returns:
            模型配置字典
        """
        if 'cdp_model' in self.config and model_type in self.config['cdp_model']:
            return self.config['cdp_model'][model_type]
        return {}


# 单例模式
_instance = None

def get_config_manager() -> ConfigManager:
    """
    获取ConfigManager的单例实例
    
    Returns:
        ConfigManager实例
    """
    global _instance
    if _instance is None:
        _instance = ConfigManager()
    return _instance


if __name__ == "__main__":
    # 简单测试
    config_manager = get_config_manager()
    print("系统配置:", config_manager.get_system_config().keys())
    print("数据库配置:", config_manager.get_db_config())
