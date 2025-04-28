#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
交易渠道管理器模块

负责管理不同交易渠道的分布和特性。
"""

import random
import datetime
from typing import Dict, List, Tuple, Optional, Any, Union


class TransactionChannelManager:
    """交易渠道管理器，处理不同渠道的分布和特性"""
    
    def __init__(self, config: Dict):
        """
        初始化交易渠道管理器
        
        Args:
            config: 配置字典，包含交易渠道分布规则
        """
        self.config = config
        
        # 从配置中加载交易渠道分布
        self.channel_distribution = config.get('channel_distribution', {})
        
        # 交易类型与渠道的相关性
        self.type_channel_correlation = {
            'deposit': {
                'counter': 0.3,      # 柜台存款概率较高
                'atm': 0.3,          # ATM存款概率较高
                'online_banking': 0.2,
                'mobile_app': 0.1,
                'third_party': 0.1
            },
            'withdrawal': {
                'counter': 0.2,
                'atm': 0.4,          # ATM取款概率最高
                'online_banking': 0.2,
                'mobile_app': 0.1,
                'third_party': 0.1
            },
            'transfer_in': {
                'counter': 0.1,
                'atm': 0.0,          # ATM不能转入
                'online_banking': 0.4, # 网银转入概率高
                'mobile_app': 0.4,     # 手机银行转入概率高
                'third_party': 0.1
            },
            'transfer_out': {
                'counter': 0.1,
                'atm': 0.0,          # ATM不能转出
                'online_banking': 0.4, # 网银转出概率高
                'mobile_app': 0.4,     # 手机银行转出概率高
                'third_party': 0.1
            },
            'consumption': {
                'counter': 0.05,
                'atm': 0.0,           # ATM不能消费
                'online_banking': 0.3,
                'mobile_app': 0.4,     # 手机银行消费概率最高
                'third_party': 0.25    # 第三方消费较高
            },
            'inquiry': {
                'counter': 0.05,
                'atm': 0.25,          # ATM查询较高
                'online_banking': 0.3,
                'mobile_app': 0.4,     # 手机银行查询最高
                'third_party': 0.0
            }
        }
        
        # 时间段与渠道的相关性
        self.time_channel_correlation = {
            'morning': {             # 早上9:00-12:00
                'counter': 1.2,      # 柜台业务较多
                'atm': 1.0,
                'online_banking': 0.8,
                'mobile_app': 1.0,
                'third_party': 0.8
            },
            'lunch': {               # 中午12:00-14:00
                'counter': 0.7,      # 柜台业务减少
                'atm': 1.1,
                'online_banking': 1.2,
                'mobile_app': 1.3,    # 手机银行使用增加
                'third_party': 1.2
            },
            'afternoon': {           # 下午14:00-17:00
                'counter': 1.1,      # 柜台业务回升
                'atm': 1.0,
                'online_banking': 0.9,
                'mobile_app': 1.0,
                'third_party': 0.9
            },
            'evening': {             # 晚上17:00-22:00
                'counter': 0.3,      # 柜台业务很少（多已下班）
                'atm': 1.2,          # ATM使用增加
                'online_banking': 1.3,
                'mobile_app': 1.5,    # 手机银行使用大增
                'third_party': 1.3
            },
            'night': {               # 深夜22:00-次日9:00
                'counter': 0.0,      # 无柜台业务
                'atm': 0.5,          # ATM使用减少
                'online_banking': 0.7,
                'mobile_app': 1.0,    # 手机银行依然活跃
                'third_party': 0.6
            }
        }
        
        # 客户类型与渠道的相关性
        self.customer_channel_correlation = {
            'personal': {
                'counter': 1.0,
                'atm': 1.0,
                'online_banking': 1.0,
                'mobile_app': 1.0,
                'third_party': 1.0
            },
            'corporate': {
                'counter': 1.5,      # 企业客户柜台业务较多
                'atm': 0.5,          # 企业客户ATM业务较少
                'online_banking': 1.5, # 企业客户网银业务较多
                'mobile_app': 0.7,    # 企业客户手机银行较少
                'third_party': 0.8
            },
            'vip': {
                'counter': 1.2,      # VIP客户柜台业务略多
                'atm': 0.8,          # VIP客户ATM业务略少
                'online_banking': 1.2, # VIP客户网银业务略多
                'mobile_app': 1.2,    # VIP客户手机银行略多
                'third_party': 1.0
            }
        }
    
    def get_transaction_channel(self, transaction_type: str, 
                              transaction_time: datetime.datetime,
                              account_info: Dict) -> str:
        """
        根据交易类型、时间和账户信息获取交易渠道
        
        Args:
            transaction_type: 交易类型
            transaction_time: 交易时间
            account_info: 账户信息
            
        Returns:
            交易渠道
        """
        # 基础渠道分布
        channel_weights = self.channel_distribution.copy()
        
        # 调整基于交易类型的权重
        type_correlation = self.type_channel_correlation.get(transaction_type, {})
        for channel, correlation in type_correlation.items():
            if channel in channel_weights:
                channel_weights[channel] *= correlation
        
        # 确定时间段
        hour = transaction_time.hour
        if 9 <= hour < 12:
            time_period = 'morning'
        elif 12 <= hour < 14:
            time_period = 'lunch'
        elif 14 <= hour < 17:
            time_period = 'afternoon'
        elif 17 <= hour < 22:
            time_period = 'evening'
        else:
            time_period = 'night'
        
        # 调整基于时间段的权重
        time_correlation = self.time_channel_correlation.get(time_period, {})
        for channel, correlation in time_correlation.items():
            if channel in channel_weights:
                channel_weights[channel] *= correlation
        
        # 调整基于客户类型的权重
        customer_type = account_info.get('customer_type', 'personal')
        is_vip = account_info.get('is_vip', False)
        
        if is_vip:
            customer_correlation = self.customer_channel_correlation.get('vip', {})
        else:
            customer_correlation = self.customer_channel_correlation.get(customer_type, {})
        
        for channel, correlation in customer_correlation.items():
            if channel in channel_weights:
                channel_weights[channel] *= correlation
        
        # 确保权重非负
        for channel in channel_weights:
            channel_weights[channel] = max(0, channel_weights[channel])
        
        # 如果所有权重都为0，使用均匀分布
        if sum(channel_weights.values()) == 0:
            for channel in channel_weights:
                channel_weights[channel] = 1.0
        
        # 根据权重随机选择渠道
        channels = list(channel_weights.keys())
        weights = list(channel_weights.values())
        
        # 归一化权重
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]
        
        # 随机选择
        return random.choices(channels, weights=weights, k=1)[0]