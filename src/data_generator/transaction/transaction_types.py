#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
交易类型管理器模块

负责管理不同类型的交易，以及它们的分布和特性。
"""

import random
from typing import Dict, List, Tuple, Optional, Any, Union


class TransactionTypeManager:
    """交易类型管理器，处理不同类型交易的分布和特性"""
    
    def __init__(self, config: Dict):
        """
        初始化交易类型管理器
        
        Args:
            config: 配置字典，包含交易类型分布规则
        """
        self.config = config
        
        # 从配置中加载交易类型分布
        self.type_distribution = config.get('type_distribution', {})
        
        # 定义交易类型映射关系
        self.transaction_types = {
            'deposit': '存款',
            'withdrawal': '取款',
            'transfer_in': '转入',
            'transfer_out': '转出',
            'consumption': '消费',
            'inquiry': '查询',
            'other': '其他'
        }
        
        # 定义交易类型类别
        self.inflow_types = ['deposit', 'transfer_in']  # 资金流入
        self.outflow_types = ['withdrawal', 'transfer_out', 'consumption']  # 资金流出
        self.neutral_types = ['inquiry', 'other']  # 不影响余额的交易
    
    def get_transaction_type_name(self, transaction_type: str) -> str:
        """
        获取交易类型的中文名称
        
        Args:
            transaction_type: 交易类型代码
            
        Returns:
            交易类型中文名称
        """
        return self.transaction_types.get(transaction_type, '未知类型')
    
    def is_inflow_type(self, transaction_type: str) -> bool:
        """
        判断是否是资金流入类型
        
        Args:
            transaction_type: 交易类型
            
        Returns:
            是否是资金流入类型
        """
        return transaction_type in self.inflow_types
    
    def is_outflow_type(self, transaction_type: str) -> bool:
        """
        判断是否是资金流出类型
        
        Args:
            transaction_type: 交易类型
            
        Returns:
            是否是资金流出类型
        """
        return transaction_type in self.outflow_types
    
    def is_neutral_type(self, transaction_type: str) -> bool:
        """
        判断是否是中性类型（不影响余额）
        
        Args:
            transaction_type: 交易类型
            
        Returns:
            是否是中性类型
        """
        return transaction_type in self.neutral_types
    
    def distribute_transaction_types(self, total_count: int) -> Dict[str, int]:
        """
        根据配置的分布规则分配各类型交易的数量
        
        Args:
            total_count: 总交易数量
            
        Returns:
            各类型交易的数量字典
        """
        type_counts = {}
        remaining = total_count
        
        # 标准类型的分布
        standard_types = ['deposit', 'withdrawal', 'transfer_in', 'transfer_out', 
                         'consumption', 'inquiry', 'other']
        
        for transaction_type in standard_types:
            ratio = self.type_distribution.get(transaction_type, 0.1)  # 默认比例0.1
            count = int(total_count * ratio)
            type_counts[transaction_type] = count
            remaining -= count
        
        # 分配剩余的交易
        if remaining > 0:
            # 随机分配剩余交易到各类型
            for _ in range(remaining):
                transaction_type = random.choice(standard_types)
                type_counts[transaction_type] = type_counts.get(transaction_type, 0) + 1
        
        return type_counts
    
    def get_random_transaction_type(self, account_info: Dict = None) -> str:
        """
        随机获取一个交易类型
        
        Args:
            account_info: 账户信息，可选
            
        Returns:
            随机交易类型
        """
        # 根据配置的分布随机选择类型
        transaction_types = list(self.type_distribution.keys())
        weights = list(self.type_distribution.values())
        
        # 如果账户余额很低，减少流出类型的权重
        if account_info and account_info.get('balance', 0) < 500:
            for i, transaction_type in enumerate(transaction_types):
                if transaction_type in self.outflow_types:
                    weights[i] *= 0.3  # 减少权重
        
        # 归一化权重
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]
        
        # 随机选择
        return random.choices(transaction_types, weights=weights, k=1)[0]