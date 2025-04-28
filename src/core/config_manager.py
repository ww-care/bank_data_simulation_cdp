#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
配置管理模块

负责读取、验证和管理系统的各类配置信息，支持文件配置和环境变量覆盖。
"""

import os
import yaml
import json
import configparser
import re
from typing import Dict, List, Any, Optional, Union

from src.logger import get_logger


class ConfigManager:
    """配置管理器类，管理系统的各类配置"""
    
    def __init__(self, config_dir: str = None, env_prefix: str = "BANK_SIM_"):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录，默认为项目根目录下的config目录
            env_prefix: 环境变量前缀，用于识别系统配置的环境变量
        """
        self.logger = get_logger('config_manager')
        self.env_prefix = env_prefix
        
        if config_dir is None:
            # 默认配置目录为当前工作目录的config子目录
            self.config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config')
        else:
            self.config_dir = config_dir
            
        # 加载系统配置
        self.config = self._load_system_config()
        
        # 加载数据库配置
        self.db_config = self._load_db_config()
        
        # 加载日志配置
        self.log_config = self._load_log_config()
        
        # 验证配置有效性
        self._validate_config()
        
        # 应用环境变量覆盖
        self._apply_env_overrides()
        
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
                self.logger.info(f"已加载系统配置文件: {config_path}")
                return config or {}
        except FileNotFoundError:
            self.logger.warning(f"系统配置文件不存在: {config_path}，将使用默认配置")
            return self._get_default_system_config()
        except Exception as e:
            self.logger.error(f"加载系统配置文件失败: {str(e)}")
            return self._get_default_system_config()
    
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
                self.logger.info(f"已加载数据库配置文件: {db_config_path}")
                return dict(config['mysql'])
            else:
                self.logger.warning("MySQL配置段不存在，将使用默认配置")
                return self._get_default_db_config()
        except Exception as e:
            self.logger.error(f"加载数据库配置文件失败: {str(e)}")
            return self._get_default_db_config()
    
    def _load_log_config(self) -> Dict:
        """
        加载日志配置文件
        
        Returns:
            日志配置字典
        """
        log_config_path = os.path.join(self.config_dir, 'logging.yaml')
        
        try:
            if os.path.exists(log_config_path):
                with open(log_config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    self.logger.info(f"已加载日志配置文件: {log_config_path}")
                    return config or {}
            else:
                self.logger.info(f"日志配置文件不存在: {log_config_path}，将使用默认配置")
                return self._get_default_log_config()
        except Exception as e:
            self.logger.error(f"加载日志配置文件失败: {str(e)}")
            return self._get_default_log_config()
    
    def _get_default_system_config(self) -> Dict:
        """
        获取默认系统配置
        
        Returns:
            默认系统配置字典
        """
        return {
            "system": {
                "random_seed": 42,
                "locale": "zh_CN",
                "historical_start_date": (
                    (datetime.datetime.now() - datetime.timedelta(days=365)).strftime('%Y-%m-%d')
                    if datetime else "2024-01-01"
                ),
                "historical_end_date": (
                    (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
                    if datetime else "2024-12-31"
                ),
                "batch_size": 1000
            },
            "cdp_model": {
                "customer_profile": {
                    "tables": [
                        {"name": "cdp_customer_profile", "entity": "customer", "id_prefix": "C"},
                        {"name": "cdp_manager_profile", "entity": "manager", "id_prefix": "M"}
                    ]
                },
                "business_doc": {
                    "tables": [
                        {"name": "cdp_account_transaction", "entity": "transaction", "id_prefix": "T"},
                        {"name": "cdp_loan_application", "entity": "loan", "id_prefix": "L"},
                        {"name": "cdp_investment_order", "entity": "investment", "id_prefix": "I"}
                    ]
                },
                "event": {
                    "tables": [
                        {"name": "cdp_customer_event", "entity": "customer_event", "id_prefix": "E"},
                        {"name": "cdp_app_event", "entity": "app_event", "id_prefix": "AE"},
                        {"name": "cdp_web_event", "entity": "web_event", "id_prefix": "WE"}
                    ]
                },
                "general_archive": {
                    "tables": [
                        {"name": "cdp_product_archive", "entity": "product", "id_prefix": "P"},
                        {"name": "cdp_deposit_type_archive", "entity": "deposit_type", "id_prefix": "DT"},
                        {"name": "cdp_branch_archive", "entity": "branch", "id_prefix": "B"},
                        {"name": "cdp_account_archive", "entity": "account", "id_prefix": "A"}
                    ]
                }
            }
        }
    
    def _get_default_db_config(self) -> Dict:
        """
        获取默认数据库配置
        
        Returns:
            默认数据库配置字典
        """
        return {
            "host": "localhost",
            "port": "3306",
            "user": "bank_user",
            "password": "bank_password",
            "database": "bank_data_simulation_cdp",
            "charset": "utf8mb4",
            "timeout": "10"
        }
    
    def _get_default_log_config(self) -> Dict:
        """
        获取默认日志配置
        
        Returns:
            默认日志配置字典
        """
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                },
                "detailed": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "INFO",
                    "formatter": "standard",
                    "stream": "ext://sys.stdout"
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "INFO",
                    "formatter": "detailed",
                    "filename": "logs/bank_data_simulation.log",
                    "maxBytes": 10485760,
                    "backupCount": 5,
                    "encoding": "utf8"
                }
            },
            "loggers": {
                "": {
                    "handlers": ["console", "file"],
                    "level": "INFO",
                    "propagate": True
                }
            }
        }
    
    def _validate_config(self) -> None:
        """
        验证配置的有效性
        
        检查必要的配置项是否存在，配置值是否有效。
        如果发现问题，会记录警告日志，但不会抛出异常。
        """
        # 验证系统配置
        if not self.config.get('system'):
            self.logger.warning("缺少系统配置部分，使用默认配置")
            self.config['system'] = self._get_default_system_config()['system']
        
        # 验证CDP模型配置
        if not self.config.get('cdp_model'):
            self.logger.warning("缺少CDP模型配置部分，使用默认配置")
            self.config['cdp_model'] = self._get_default_system_config()['cdp_model']
        
        # 验证数据库配置
        required_db_fields = ['host', 'port', 'user', 'password', 'database']
        missing_fields = [field for field in required_db_fields if field not in self.db_config]
        if missing_fields:
            self.logger.warning(f"数据库配置缺少以下字段: {', '.join(missing_fields)}，将使用默认值")
            for field in missing_fields:
                self.db_config[field] = self._get_default_db_config()[field]
    
    def _apply_env_overrides(self) -> None:
        """
        应用环境变量覆盖配置
        
        环境变量命名规则：
        - 系统配置：{env_prefix}SYSTEM_{key}，例如 BANK_SIM_SYSTEM_BATCH_SIZE
        - 数据库配置：{env_prefix}DB_{key}，例如 BANK_SIM_DB_HOST
        """
        # 处理系统配置覆盖
        for env_var, value in os.environ.items():
            # 系统配置
            if env_var.startswith(f"{self.env_prefix}SYSTEM_"):
                key = env_var[len(f"{self.env_prefix}SYSTEM_"):].lower()
                path = key.split('_')
                
                # 递归设置嵌套配置
                self._set_nested_config(self.config['system'], path, value)
                self.logger.info(f"环境变量 {env_var} 覆盖系统配置 {'.'.join(['system'] + path)} = {value}")
            
            # 数据库配置
            elif env_var.startswith(f"{self.env_prefix}DB_"):
                key = env_var[len(f"{self.env_prefix}DB_"):].lower()
                self.db_config[key] = value
                self.logger.info(f"环境变量 {env_var} 覆盖数据库配置 {key} = {value}")
            
            # 日志配置
            elif env_var.startswith(f"{self.env_prefix}LOG_"):
                key = env_var[len(f"{self.env_prefix}LOG_"):].lower()
                if key == "level":
                    self.log_config["loggers"][""]["level"] = value
                    self.logger.info(f"环境变量 {env_var} 覆盖日志配置 level = {value}")
    
    def _set_nested_config(self, config: Dict, path: List[str], value: str) -> None:
        """
        递归设置嵌套配置
        
        Args:
            config: 配置字典
            path: 配置路径
            value: 配置值
        """
        if len(path) == 1:
            # 尝试转换值类型
            config[path[0]] = self._convert_value(value)
        else:
            if path[0] not in config:
                config[path[0]] = {}
            self._set_nested_config(config[path[0]], path[1:], value)
    
    def _convert_value(self, value: str) -> Any:
        """
        转换值类型，尝试将字符串转换为适当的数据类型
        
        Args:
            value: 字符串值
            
        Returns:
            转换后的值
        """
        # 布尔值
        if value.lower() in ('true', 'yes', '1'):
            return True
        if value.lower() in ('false', 'no', '0'):
            return False
        
        # 整数
        try:
            return int(value)
        except ValueError:
            pass
        
        # 浮点数
        try:
            return float(value)
        except ValueError:
            pass
        
        # JSON对象或数组
        if (value.startswith('{') and value.endswith('}')) or (value.startswith('[') and value.endswith(']')):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
        
        # 保持原始字符串
        return value
    
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
    
    def get_log_config(self) -> Dict:
        """
        获取日志配置
        
        Returns:
            日志配置字典
        """
        return self.log_config
    
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
    
    def get_config_value(self, path: str, default: Any = None) -> Any:
        """
        获取指定路径的配置值
        
        Args:
            path: 配置路径，使用点号分隔，例如 'system.batch_size'
            default: 默认值，如果路径不存在则返回此值
            
        Returns:
            配置值
        """
        parts = path.split('.')
        config = self.config
        
        for part in parts:
            if isinstance(config, dict) and part in config:
                config = config[part]
            else:
                return default
        
        return config
    
    def save_config(self, config_type: str = 'system') -> bool:
        """
        保存配置到文件
        
        Args:
            config_type: 配置类型，'system', 'db' 或 'log'
            
        Returns:
            是否保存成功
        """
        try:
            if config_type == 'system':
                config_path = os.path.join(self.config_dir, 'bank_data_simulation_config.yaml')
                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
                self.logger.info(f"系统配置已保存到: {config_path}")
                return True
            
            elif config_type == 'db':
                db_config_path = os.path.join(self.config_dir, 'database.ini')
                config = configparser.ConfigParser()
                config['mysql'] = self.db_config
                with open(db_config_path, 'w', encoding='utf-8') as f:
                    config.write(f)
                self.logger.info(f"数据库配置已保存到: {db_config_path}")
                return True
            
            elif config_type == 'log':
                log_config_path = os.path.join(self.config_dir, 'logging.yaml')
                with open(log_config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(self.log_config, f, default_flow_style=False, allow_unicode=True)
                self.logger.info(f"日志配置已保存到: {log_config_path}")
                return True
            
            else:
                self.logger.error(f"未知的配置类型: {config_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"保存配置失败: {str(e)}")
            return False


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


# 导入系统模块，避免循环导入
try:
    import datetime
except ImportError:
    pass


if __name__ == "__main__":
    # 简单测试
    config_manager = get_config_manager()
    print("系统配置:", config_manager.get_system_config().keys())
    print("数据库配置:", config_manager.get_db_config())
    
    # 获取特定配置
    batch_size = config_manager.get_config_value('system.batch_size', 500)
    print(f"批处理大小: {batch_size}")
    
    # 测试环境变量覆盖
    os.environ['BANK_SIM_SYSTEM_BATCH_SIZE'] = '2000'
    os.environ['BANK_SIM_DB_HOST'] = 'testdb.example.com'
    
    config_manager = ConfigManager()  # 创建新实例以应用环境变量
    print(f"环境变量覆盖后的批处理大小: {config_manager.get_config_value('system.batch_size')}")
    print(f"环境变量覆盖后的数据库主机: {config_manager.get_db_config().get('host')}")
