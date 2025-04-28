#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
时间管理模块

负责处理系统中所有时间相关的计算，包括时间戳转换、时间范围计算等。
"""

import time
import datetime
import calendar
from typing import Dict, List, Tuple, Any, Optional, Union

from src.config_manager import get_config_manager
from src.logger import get_logger


class TimeManager:
    """时间管理器类，处理系统中的时间相关计算"""
    
    def __init__(self):
        """初始化时间管理器"""
        self.logger = get_logger('time_manager')
        self.config_manager = get_config_manager()
        self.system_config = self.config_manager.get_system_config()
    
    def get_current_time(self) -> datetime.datetime:
        """
        获取当前时间
        
        Returns:
            当前时间
        """
        return datetime.datetime.now()
    
    def calculate_historical_period(self) -> Tuple[datetime.date, datetime.date]:
        """
        计算历史数据的时间范围
        
        Returns:
            (开始日期, 结束日期)的元组
        """
        # 从配置中获取历史数据的开始和结束日期
        start_date_str = self.system_config.get('system', {}).get('historical_start_date')
        end_date_str = self.system_config.get('system', {}).get('historical_end_date')
        
        # 如果没有配置，默认为一年前到昨天
        today = datetime.date.today()
        
        if not start_date_str:
            start_date = today - datetime.timedelta(days=365)
        else:
            try:
                start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                self.logger.warning(f"无效的历史开始日期格式: {start_date_str}，使用默认值(一年前)")
                start_date = today - datetime.timedelta(days=365)
        
        if not end_date_str:
            end_date = today - datetime.timedelta(days=1)
        else:
            try:
                end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                self.logger.warning(f"无效的历史结束日期格式: {end_date_str}，使用默认值(昨天)")
                end_date = today - datetime.timedelta(days=1)
        
        # 确保开始日期不晚于结束日期
        if start_date > end_date:
            self.logger.warning("历史开始日期晚于结束日期，使用交换后的日期")
            start_date, end_date = end_date, start_date
        
        return start_date, end_date
    
    def get_time_range_for_generation(self, mode: str = 'realtime') -> Tuple[datetime.datetime, datetime.datetime]:
        """
        获取数据生成的时间范围
        
        Args:
            mode: 数据生成模式，'historical'或'realtime'
            
        Returns:
            (开始时间, 结束时间)的元组
        """
        if mode == 'historical':
            start_date, end_date = self.calculate_historical_period()
            start_time = datetime.datetime.combine(start_date, datetime.time.min)
            end_time = datetime.datetime.combine(end_date, datetime.time.max)
        else:  # realtime
            # 默认实时模式为当前时间的前一个小时
            now = self.get_current_time()
            hour_ago = now - datetime.timedelta(hours=1)
            current_hour = datetime.datetime(
                now.year, now.month, now.day, now.hour, 0, 0)
            previous_hour = datetime.datetime(
                hour_ago.year, hour_ago.month, hour_ago.day, hour_ago.hour, 0, 0)
            
            start_time = previous_hour
            end_time = current_hour - datetime.timedelta(seconds=1)
        
        return start_time, end_time
    
    def get_last_generated_timestamp(self) -> Optional[int]:
        """
        获取最后生成数据的时间戳
        
        Returns:
            最后生成数据的时间戳(13位)，如果没有则返回None
        """
        # 实际项目中，这个时间戳应该从数据库或文件中读取
        # 这里简化为返回None，表示需要重新计算时间范围
        return None
    
    def datetime_to_timestamp(self, dt: datetime.datetime) -> int:
        """
        将datetime转换为13位时间戳
        
        Args:
            dt: datetime对象
            
        Returns:
            13位时间戳
        """
        return int(dt.timestamp() * 1000)
    
    def timestamp_to_datetime(self, ts: int) -> datetime.datetime:
        """
        将13位时间戳转换为datetime
        
        Args:
            ts: 13位时间戳
            
        Returns:
            datetime对象
        """
        return datetime.datetime.fromtimestamp(ts / 1000)
    
    def format_time_for_db(self, dt: datetime.datetime) -> str:
        """
        将datetime格式化为数据库可用的时间字符串
        
        Args:
            dt: datetime对象
            
        Returns:
            格式化的时间字符串
        """
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    
    def is_workday(self, date: datetime.date) -> bool:
        """
        判断日期是否为工作日
        
        Args:
            date: 日期
            
        Returns:
            是否为工作日
        """
        # 简化判断，周一至周五为工作日
        return date.weekday() < 5
    
    def get_date_weight(self, date: datetime.date) -> float:
        """
        获取日期权重因子
        
        根据日期特征(工作日/周末、月初/月末等)计算权重因子，
        用于调整不同日期的数据生成量。
        
        Args:
            date: 日期
            
        Returns:
            权重因子(大于0的浮点数)
        """
        weight = 1.0
        
        # 判断是否工作日
        if self.is_workday(date):
            weight *= 1.2
        else:
            weight *= 0.8
        
        # 判断是否月初
        if date.day <= 5:
            weight *= 1.3  # 月初交易量较大
        
        # 判断是否月末
        days_in_month = calendar.monthrange(date.year, date.month)[1]
        if date.day >= days_in_month - 2:
            weight *= 1.4  # 月末交易量较大
        
        # 判断是否季末
        if date.month in [3, 6, 9, 12] and date.day >= days_in_month - 5:
            weight *= 1.5  # 季末交易量较大
        
        # 随机波动因子(0.95-1.05之间)
        import random
        random_factor = 0.95 + random.random() * 0.1
        weight *= random_factor
        
        return weight


# 单例模式
_instance = None

def get_time_manager() -> TimeManager:
    """
    获取TimeManager的单例实例
    
    Returns:
        TimeManager实例
    """
    global _instance
    if _instance is None:
        _instance = TimeManager()
    return _instance


if __name__ == "__main__":
    # 简单测试
    time_manager = get_time_manager()
    
    # 测试历史时间范围计算
    start_date, end_date = time_manager.calculate_historical_period()
    print(f"历史数据时间范围: {start_date} ~ {end_date}")
    
    # 测试时间戳转换
    now = datetime.datetime.now()
    timestamp = time_manager.datetime_to_timestamp(now)
    dt = time_manager.timestamp_to_datetime(timestamp)
    print(f"当前时间: {now}")
    print(f"转换为时间戳: {timestamp}")
    print(f"转换回datetime: {dt}")
