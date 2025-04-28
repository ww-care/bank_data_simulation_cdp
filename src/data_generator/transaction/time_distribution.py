#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
交易时间分布模型

负责生成符合银行业务规律的交易时间分布。
"""

import random
import datetime
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime, date, time, timedelta

from src.time_manager.time_manager import get_time_manager


class TimeDistribution:
    """交易时间分布模型，用于生成符合业务规律的交易时间"""
    
    def __init__(self, config: Dict, time_manager=None):
        """
        初始化时间分布模型
        
        Args:
            config: 配置字典，包含交易时间分布规则
            time_manager: 时间管理器实例，如果为None则自动获取
        """
        self.config = config
        self.time_manager = time_manager or get_time_manager()
        
        # 从配置中加载时间分布规则
        self.time_config = config.get('time_distribution', {})
        
        # 工作日和周末时间段分布
        self.workday_periods = self.time_config.get('workday', {})
        self.weekend_periods = self.time_config.get('weekend', {})
        
        # 工作日交易占比
        self.workday_ratio = self.time_config.get('workday_ratio', 0.8)
    
    def generate_transaction_time(self, start_time: datetime, end_time: datetime, 
                                 customer_type: str = None) -> datetime:
        """
        生成交易时间
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            customer_type: 客户类型，可选
            
        Returns:
            datetime 交易时间
        """
        # 基于权重选择日期
        selected_date = self._select_date_with_weight(start_time.date(), end_time.date())
        
        # 判断该日期是工作日还是周末
        is_weekend = selected_date.weekday() >= 5
        
        # 根据日期类型选择时间段分布
        if is_weekend:
            periods = self.weekend_periods
        else:
            periods = self.workday_periods
        
        # 基于权重选择时间段
        period_weights = []
        period_ranges = []
        
        for period_name, period_info in periods.items():
            ratio = period_info.get('ratio', 0)
            period_weights.append(ratio)
            
            # 解析时间范围
            peak_time_str = period_info.get('peak_time', '12:00')
            peak_hour, peak_minute = map(int, peak_time_str.split(':'))
            
            if period_name == 'morning':
                start_hour, end_hour = 9, 12
            elif period_name == 'lunch':
                start_hour, end_hour = 12, 14
            elif period_name == 'afternoon':
                start_hour, end_hour = 14, 17
            elif period_name == 'evening':
                start_hour, end_hour = 17, 22
            elif period_name == 'night':
                start_hour, end_hour = 22, 9  # 注意跨天处理
            else:
                # 默认时间范围，整天
                start_hour, end_hour = 0, 24
            
            period_ranges.append((start_hour, end_hour, peak_hour, peak_minute))
        
        # 选择时间段
        selected_idx = random.choices(range(len(period_weights)), weights=period_weights, k=1)[0]
        start_hour, end_hour, peak_hour, peak_minute = period_ranges[selected_idx]
        
        # 生成具体时间
        if start_hour < end_hour:
            # 不跨天的情况
            hour = self._normal_distribution_int(peak_hour, 1.5, start_hour, end_hour-1)
            if hour == peak_hour:
                minute = self._normal_distribution_int(peak_minute, 15, 0, 59)
            else:
                minute = random.randint(0, 59)
            
            result_time = datetime.combine(selected_date, time(hour, minute))
        else:
            # 跨天的情况
            # 判断是生成当天的夜间还是次日的早晨
            if random.random() < 0.7:  # 70%的概率是当天夜间
                hour = self._normal_distribution_int(peak_hour, 1.5, start_hour, 23)
                if hour == peak_hour:
                    minute = self._normal_distribution_int(peak_minute, 15, 0, 59)
                else:
                    minute = random.randint(0, 59)
                
                result_time = datetime.combine(selected_date, time(hour, minute))
            else:  # 30%的概率是次日早晨
                next_day = selected_date + timedelta(days=1)
                hour = self._normal_distribution_int(7, 1.5, 0, end_hour-1)
                minute = random.randint(0, 59)
                
                result_time = datetime.combine(next_day, time(hour, minute))
        
        # 确保生成的时间在有效范围内
        if result_time < start_time:
            result_time = start_time
        if result_time > end_time:
            result_time = end_time
        
        # 添加随机秒数
        seconds = random.randint(0, 59)
        result_time = result_time.replace(second=seconds)
        
        return result_time
    
    def _select_date_with_weight(self, start_date: date, end_date: date) -> date:
        """
        根据权重选择日期
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            date 选中的日期
        """
        # 计算日期范围内的天数
        delta_days = (end_date - start_date).days + 1
        if delta_days <= 0:
            return start_date
        
        # 如果只有一天的范围，直接返回
        if delta_days == 1:
            return start_date
        
        # 为每一天分配权重
        dates = []
        weights = []
        
        current_date = start_date
        while current_date <= end_date:
            # 判断是否为工作日
            is_workday = current_date.weekday() < 5
            
            # 根据是否工作日分配基础权重
            if is_workday:
                weight = self.workday_ratio / (delta_days * self.workday_ratio)
            else:
                weight = (1 - self.workday_ratio) / (delta_days * (1 - self.workday_ratio))
            
            # 使用日期权重函数进一步调整
            weight *= self.time_manager.get_date_weight(current_date)
            
            dates.append(current_date)
            weights.append(weight)
            
            current_date += timedelta(days=1)
        
        # 确保权重之和为1
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]
        
        # 根据权重选择日期
        return random.choices(dates, weights=weights, k=1)[0]
    
    def _normal_distribution_int(self, mean: float, sigma: float, min_val: int, max_val: int) -> int:
        """
        生成正态分布的整数
        
        Args:
            mean: 均值
            sigma: 标准差
            min_val: 最小值
            max_val: 最大值
            
        Returns:
            int 生成的整数
        """
        while True:
            value = int(round(random.normalvariate(mean, sigma)))
            if min_val <= value <= max_val:
                return value
    
    def is_business_hour(self, dt: datetime) -> bool:
        """
        判断是否是营业时间
        
        Args:
            dt: 日期时间
            
        Returns:
            bool 是否是营业时间
        """
        # 判断是否是工作日
        is_workday = dt.weekday() < 5
        
        # 非工作日不是营业时间
        if not is_workday:
            return False
        
        # 工作日的9:00-17:00是营业时间
        return 9 <= dt.hour < 17
    
    def adjust_frequency_by_timespan(self, base_frequency: float, start_time: datetime, 
                                   end_time: datetime, account_info: Dict) -> float:
        """
        根据时间段调整交易频率
        
        Args:
            base_frequency: 基础频率（每天平均交易次数）
            start_time: 开始时间
            end_time: 结束时间
            account_info: 账户信息
            
        Returns:
            调整后的频率
        """
        # 计算时间段内工作日和非工作日的天数
        workday_count = 0
        total_days = 0
        
        current_date = start_time.date()
        end_date = end_time.date()
        
        while current_date <= end_date:
            total_days += 1
            if current_date.weekday() < 5:  # 0-4是工作日
                workday_count += 1
            current_date += timedelta(days=1)
        
        # 工作日占比
        if total_days == 0:
            workday_ratio = 0.7  # 默认工作日占比
        else:
            workday_ratio = workday_count / total_days
        
        # 从配置中获取工作日和非工作日的频率乘数
        workday_multiplier = self.config.get('frequency', {}).get('workday_multiplier', 1.2)
        weekend_multiplier = self.config.get('frequency', {}).get('weekend_multiplier', 0.8)
        
        # 计算平均频率乘数
        avg_multiplier = workday_ratio * workday_multiplier + (1 - workday_ratio) * weekend_multiplier
        
        # 应用客户特性的调整因子
        if account_info.get('is_vip', False):
            vip_multiplier = self.config.get('frequency', {}).get('vip_multiplier', 1.25)
            avg_multiplier *= vip_multiplier
        
        if account_info.get('customer_type') == 'corporate':
            corporate_multiplier = self.config.get('frequency', {}).get('corporate_multiplier', 1.5)
            avg_multiplier *= corporate_multiplier
        
        # 应用时间段时长的调整
        hours_span = (end_time - start_time).total_seconds() / 3600  # 小时数
        if hours_span < 24:
            # 短时间段的频率需要按比例缩减
            day_fraction = hours_span / 24
            avg_multiplier *= day_fraction
        
        # 返回调整后的频率
        return base_frequency * avg_multiplier
