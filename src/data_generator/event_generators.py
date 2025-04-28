#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
行为事件范式数据生成器

负责生成符合CDP行为事件范式的数据，包括客户行为事件、APP行为事件、网银行为事件等。
"""

import uuid
import random
import datetime
import faker
import numpy as np
import json
from typing import Dict, List, Tuple, Optional, Any, Union

from src.time_manager.time_manager import get_time_manager


class BaseEventGenerator:
    """行为事件范式生成器基类"""
    
    def __init__(self, fake_generator: faker.Faker, config_manager):
        """
        初始化事件生成器
        
        Args:
            fake_generator: Faker实例，用于生成随机数据
            config_manager: 配置管理器实例
        """
        self.faker = fake_generator
        self.config_manager = config_manager
        self.time_manager = get_time_manager()
    
    def generate_id(self, prefix: str = '') -> str:
        """
        生成事件ID
        
        Args:
            prefix: ID前缀
            
        Returns:
            生成的ID
        """
        id_value = uuid.uuid4().hex[:16].upper()
        if prefix:
            return f"{prefix}{id_value}"
        return id_value
    
    def get_partition_date(self) -> str:
        """
        获取分区日期，用于设置pt字段
        
        Returns:
            分区日期字符串，格式为YYYY-MM-DD
        """
        return datetime.date.today().strftime('%Y-%m-%d')
    
    def datetime_to_timestamp(self, dt: datetime.datetime) -> int:
        """
        将datetime转换为13位时间戳
        
        Args:
            dt: datetime对象
            
        Returns:
            13位时间戳
        """
        return self.time_manager.datetime_to_timestamp(dt)
    
    def create_event_property(self, data: Dict) -> str:
        """
        创建事件属性JSON字符串
        
        Args:
            data: 事件属性数据字典
            
        Returns:
            事件属性JSON字符串
        """
        return json.dumps(data, ensure_ascii=False)


class CustomerEventGenerator(BaseEventGenerator):
    """客户行为事件生成器，生成符合CDP行为事件范式的数据"""
    
    def generate(self, customers: List[Dict], products: List[Dict], 
                start_date: datetime.date, end_date: datetime.date, 
                mode: str = 'historical') -> List[Dict]:
        """
        生成客户行为事件数据
        
        Args:
            customers: 客户数据列表
            products: 产品数据列表
            start_date: 开始日期
            end_date: 结束日期
            mode: 数据生成模式
            
        Returns:
            客户行为事件数据列表
        """
        # 将在后续实现
        return []


class AppEventGenerator(BaseEventGenerator):
    """APP行为事件生成器，生成符合CDP行为事件范式的数据"""
    
    def generate(self, customers: List[Dict], app_users: List[Dict], 
                start_date: datetime.date, end_date: datetime.date) -> List[Dict]:
        """
        生成APP行为事件数据
        
        Args:
            customers: 客户数据列表
            app_users: APP用户数据列表
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            APP行为事件数据列表
        """
        # 将在后续实现
        return []


class WebEventGenerator(BaseEventGenerator):
    """网银行为事件生成器，生成符合CDP行为事件范式的数据"""
    
    def generate(self, customers: List[Dict], 
                start_date: datetime.date, end_date: datetime.date) -> List[Dict]:
        """
        生成网银行为事件数据
        
        Args:
            customers: 客户数据列表
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            网银行为事件数据列表
        """
        # 将在后续实现
        return []
