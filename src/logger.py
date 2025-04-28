#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
日志管理模块

提供统一的日志记录功能，支持不同级别的日志、文件轮转，以及结构化日志格式。
"""

import os
import sys
import json
import logging
import logging.handlers
import yaml
import time
import datetime
import atexit
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

# 日志默认目录
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')

# 默认日志格式
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# 日志对象缓存
loggers = {}


class StructuredLogFormatter(logging.Formatter):
    """结构化日志格式化器，生成JSON格式的日志"""
    
    def __init__(self, include_extra_fields=True):
        """
        初始化结构化日志格式化器
        
        Args:
            include_extra_fields: 是否包含额外字段
        """
        super().__init__()
        self.include_extra_fields = include_extra_fields
    
    def format(self, record):
        """
        格式化日志记录为JSON
        
        Args:
            record: 日志记录
        
        Returns:
            格式化的日志字符串
        """
        log_data = {
            'timestamp': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'name': record.name,
            'message': record.getMessage(),
        }
        
        # 添加异常信息
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # 添加额外字段
        if self.include_extra_fields and hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        # 添加上下文信息
        if hasattr(record, 'task_id'):
            log_data['task_id'] = record.task_id
            
        # 添加代码位置信息
        log_data['location'] = {
            'file': record.pathname,
            'line': record.lineno,
            'function': record.funcName
        }
        
        return json.dumps(log_data, ensure_ascii=False)


class LogManager:
    """日志管理器，负责创建和配置日志记录器"""
    
    def __init__(self):
        """初始化日志管理器"""
        self.initialized = False
        self.config = None
        self.log_dir = LOG_DIR
        
        # 确保日志目录存在
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 注册清理函数
        atexit.register(self.cleanup_old_logs)
    
    def init_from_config(self):
        """从配置文件初始化日志系统"""
        try:
            # 尝试从配置管理器获取日志配置
            from src.core.config_manager import get_config_manager
            config_manager = get_config_manager()
            self.config = config_manager.get_log_config()
            
            # 配置日志系统
            if self.config:
                # 设置日志文件路径，替换相对路径
                for handler_name, handler_config in self.config.get('handlers', {}).items():
                    if 'filename' in handler_config:
                        filename = handler_config['filename']
                        if not os.path.isabs(filename):
                            # 替换为绝对路径
                            handler_config['filename'] = os.path.join(self.log_dir, os.path.basename(filename))
                
                # 创建日志目录
                for handler in self.config.get('handlers', {}).values():
                    if 'filename' in handler:
                        log_path = os.path.dirname(handler['filename'])
                        os.makedirs(log_path, exist_ok=True)
                
                # 应用配置
                logging.config.dictConfig(self.config)
                self.initialized = True
                
                # 创建一个根日志记录器以记录初始化成功
                root_logger = logging.getLogger()
                root_logger.info("日志系统已从配置初始化")
                
                return True
        except (ImportError, Exception) as e:
            # 如果导入配置管理器失败或配置无效，使用默认配置
            print(f"从配置初始化日志系统失败: {str(e)}，使用默认配置")
        
        return False
    
    def init_default_logging(self):
        """初始化默认日志配置"""
        # 设置根日志记录器级别
        root_logger = logging.getLogger()
        if not root_logger.handlers:  # 避免重复配置
            root_logger.setLevel(logging.INFO)
            
            # 创建控制台处理器
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter(DEFAULT_LOG_FORMAT)
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)
            
            # 创建文件处理器
            log_file = os.path.join(self.log_dir, 'bank_data_simulation.log')
            file_handler = logging.handlers.RotatingFileHandler(
                log_file, 
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.INFO)
            file_formatter = logging.Formatter(DEFAULT_LOG_FORMAT)
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
            
            # 创建错误日志处理器
            error_log_file = os.path.join(self.log_dir, 'error.log')
            error_handler = logging.handlers.RotatingFileHandler(
                error_log_file, 
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s'
            )
            error_handler.setFormatter(error_formatter)
            root_logger.addHandler(error_handler)
            
            # 创建JSON日志处理器
            json_log_file = os.path.join(self.log_dir, 'structured.json')
            json_handler = logging.handlers.RotatingFileHandler(
                json_log_file, 
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            json_handler.setLevel(logging.INFO)
            json_formatter = StructuredLogFormatter()
            json_handler.setFormatter(json_formatter)
            root_logger.addHandler(json_handler)
            
            root_logger.info("日志系统已初始化默认配置")
            self.initialized = True
    
    def get_logger(self, name: str, level: int = None) -> logging.Logger:
        """
        获取日志记录器
        
        Args:
            name: 日志记录器名称
            level: 日志级别，如果为None则使用配置或默认值
            
        Returns:
            日志记录器实例
        """
        global loggers
        
        # 检查是否已经创建过该名称的logger
        if name in loggers:
            return loggers[name]
        
        # 确保日志系统已初始化
        if not self.initialized:
            if not self.init_from_config():
                self.init_default_logging()
        
        # 创建日志记录器
        logger = logging.getLogger(name)
        
        # 设置自定义级别（如果提供）
        if level is not None:
            logger.setLevel(level)
        
        # 缓存日志记录器
        loggers[name] = logger
        
        return logger
    
    def cleanup_old_logs(self, days: int = 30):
        """
        清理旧日志文件
        
        Args:
            days: 保留的天数，默认30天
        """
        try:
            # 当前时间
            now = time.time()
            cutoff = now - (days * 86400)  # 86400秒 = 1天
            
            # 寻找所有日志文件
            for root, dirs, files in os.walk(self.log_dir):
                for file in files:
                    if file.endswith('.log') or file.endswith('.json'):
                        file_path = os.path.join(root, file)
                        
                        # 检查文件修改时间
                        file_mtime = os.path.getmtime(file_path)
                        if file_mtime < cutoff:
                            # 将旧日志移动到归档目录
                            try:
                                archive_dir = os.path.join(self.log_dir, 'archive')
                                os.makedirs(archive_dir, exist_ok=True)
                                
                                # 目标文件路径，添加日期后缀
                                date_str = datetime.datetime.fromtimestamp(file_mtime).strftime('%Y%m%d')
                                archive_file = f"{os.path.splitext(file)[0]}_{date_str}{os.path.splitext(file)[1]}"
                                archive_path = os.path.join(archive_dir, archive_file)
                                
                                # 移动文件
                                shutil.move(file_path, archive_path)
                                print(f"已归档旧日志: {file} -> {archive_file}")
                            except Exception as e:
                                print(f"归档日志文件失败: {str(e)}")
        
        except Exception as e:
            print(f"清理旧日志文件失败: {str(e)}")
    
    def archive_logs(self, archive_name: str = None):
        """
        将当前日志归档
        
        Args:
            archive_name: 归档名称，默认为当前时间戳
        """
        try:
            if not archive_name:
                archive_name = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 创建归档目录
            archive_dir = os.path.join(self.log_dir, 'archive', archive_name)
            os.makedirs(archive_dir, exist_ok=True)
            
            # 寻找当前日志文件
            for file in os.listdir(self.log_dir):
                if file.endswith('.log') or file.endswith('.json'):
                    file_path = os.path.join(self.log_dir, file)
                    archive_path = os.path.join(archive_dir, file)
                    
                    # 复制文件到归档目录
                    shutil.copy2(file_path, archive_path)
                    
                    # 清空原文件但保留文件
                    with open(file_path, 'w') as f:
                        f.truncate(0)
            
            print(f"已归档当前日志到: {archive_dir}")
            
            # 记录归档事件
            root_logger = logging.getLogger()
            root_logger.info(f"日志已归档到: {archive_dir}")
            
            return archive_dir
            
        except Exception as e:
            print(f"归档日志失败: {str(e)}")
            return None
    
    def set_task_context(self, task_id: str):
        """
        设置任务上下文过滤器
        
        Args:
            task_id: 任务ID
        """
        class TaskContextFilter(logging.Filter):
            def __init__(self, task_id):
                super().__init__()
                self.task_id = task_id
            
            def filter(self, record):
                record.task_id = self.task_id
                return True
        
        # 为所有日志记录器添加过滤器
        task_filter = TaskContextFilter(task_id)
        for logger in logging.Logger.manager.loggerDict.values():
            if isinstance(logger, logging.Logger):
                logger.addFilter(task_filter)
    
    def clear_task_context(self):
        """清除任务上下文过滤器"""
        for logger in logging.Logger.manager.loggerDict.values():
            if isinstance(logger, logging.Logger):
                for filter in logger.filters:
                    if hasattr(filter, 'task_id'):
                        logger.removeFilter(filter)


# 创建全局LogManager实例
log_manager = LogManager()

def get_logger(name: str, level: int = None) -> logging.Logger:
    """
    获取日志记录器的简便函数
    
    Args:
        name: 日志记录器名称
        level: 日志级别，如果为None则使用配置或默认值
        
    Returns:
        日志记录器实例
    """
    return log_manager.get_logger(name, level)

def set_task_context(task_id: str):
    """
    设置任务上下文
    
    Args:
        task_id: 任务ID
    """
    log_manager.set_task_context(task_id)

def clear_task_context():
    """清除任务上下文"""
    log_manager.clear_task_context()

def archive_logs(archive_name: str = None) -> Optional[str]:
    """
    归档日志
    
    Args:
        archive_name: 归档名称，默认为当前时间戳
        
    Returns:
        归档目录路径，如果失败则返回None
    """
    return log_manager.archive_logs(archive_name)

def cleanup_old_logs(days: int = 30):
    """
    清理旧日志
    
    Args:
        days: 保留的天数，默认30天
    """
    log_manager.cleanup_old_logs(days)


class LoggingContext:
    """日志上下文管理器，用于临时改变日志配置"""
    
    def __init__(self, logger, level=None, handler=None, close=True):
        """
        初始化日志上下文
        
        Args:
            logger: 日志记录器
            level: 临时日志级别
            handler: 临时日志处理器
            close: 是否在退出时关闭处理器
        """
        self.logger = logger
        self.level = level
        self.handler = handler
        self.close = close

    def __enter__(self):
        """进入上下文"""
        if self.level is not None:
            self.old_level = self.logger.level
            self.logger.setLevel(self.level)
        if self.handler:
            self.logger.addHandler(self.handler)
        return self.logger

    def __exit__(self, et, ev, tb):
        """退出上下文"""
        if self.level is not None:
            self.logger.setLevel(self.old_level)
        if self.handler:
            self.logger.removeHandler(self.handler)
            if self.close:
                self.handler.close()


class StructuredLogAdapter(logging.LoggerAdapter):
    """结构化日志适配器，用于添加结构化字段"""
    
    def __init__(self, logger, extra=None):
        """
        初始化适配器
        
        Args:
            logger: 日志记录器
            extra: 额外字段
        """
        super().__init__(logger, extra or {})
    
    def process(self, msg, kwargs):
        """
        处理日志消息
        
        Args:
            msg: 日志消息
            kwargs: 关键字参数
            
        Returns:
            处理后的(msg, kwargs)元组
        """
        # 添加额外字段
        kwargs.setdefault('extra', {}).setdefault('extra_fields', {})
        kwargs['extra']['extra_fields'].update(self.extra)
        return msg, kwargs

def get_structured_logger(name, **extra):
    """
    获取结构化日志记录器
    
    Args:
        name: 日志记录器名称
        **extra: 额外字段
        
    Returns:
        结构化日志适配器
    """
    logger = get_logger(name)
    return StructuredLogAdapter(logger, extra)


if __name__ == "__main__":
    # 简单测试
    logger = get_logger('test')
    logger.info("这是一条普通信息日志")
    logger.warning("这是一条警告日志")
    logger.error("这是一条错误日志")
    
    # 使用结构化日志
    structured_logger = get_structured_logger('structured_test', user_id='12345', module='测试模块')
    structured_logger.info("这是一条带有额外字段的结构化日志")
    
    # 设置任务上下文
    set_task_context('TASK123')
    logger.info("这是一条带有任务上下文的日志")
    
    # 使用日志上下文管理器
    with LoggingContext(logger, level=logging.DEBUG):
        logger.debug("这是一条DEBUG级别的日志，通常不会显示")
    
    # 清理和归档
    archive_logs('test_archive')
    cleanup_old_logs(days=7)
