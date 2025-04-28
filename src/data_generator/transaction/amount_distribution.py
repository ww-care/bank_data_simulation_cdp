#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
交易金额分布模型

负责生成符合客户特征的交易金额分布。
"""

import random
import math
from typing import Dict, List, Tuple, Optional, Any, Union


class AmountDistribution:
    """交易金额分布模型，用于生成符合客户特征的交易金额"""
    
    def __init__(self, config: Dict):
        """
        初始化金额分布模型
        
        Args:
            config: 配置字典，包含交易金额分布规则
        """
        self.config = config
        
        # 从配置中加载金额分布规则
        self.amount_config = config.get('amount', {})
        
        # 不同客户类型的金额分布
        self.personal_amount = self.amount_config.get('personal', {})
        self.corporate_amount = self.amount_config.get('corporate', {})
    
    def generate_transaction_amount(self, account_info: Dict, transaction_type: str) -> float:
        """
        生成交易金额
        
        Args:
            account_info: 账户信息
            transaction_type: 交易类型
            
        Returns:
            float 交易金额
        """
        # 确定客户类型
        is_corporate = account_info.get('customer_type') == 'corporate'
        is_vip = account_info.get('is_vip', False)
        account_type = account_info.get('account_type', 'current')
        
        # 选择对应的金额范围配置
        if is_corporate:
            amount_ranges = self.corporate_amount
        else:
            amount_ranges = self.personal_amount
        
        # 根据交易类型和账户类型调整金额
        if transaction_type in ['deposit', 'transfer_in']:
            # 存款或转入交易
            direction_multiplier = 1.0
        elif transaction_type in ['withdrawal', 'transfer_out', 'consumption']:
            # 取款、转出或消费交易
            direction_multiplier = 0.8  # 支出交易的平均金额通常略小
            
            # 确保不会超过账户余额
            max_possible_amount = account_info.get('balance', float('inf'))
        else:
            # 其他类型交易，使用中性乘数
            direction_multiplier = 1.0
        
        # 根据金额区间分类选择交易金额范围
        small_range = amount_ranges.get('small', {}).get('range', [100, 1000])
        small_ratio = amount_ranges.get('small', {}).get('ratio', 0.6)
        
        medium_range = amount_ranges.get('medium', {}).get('range', [1000, 10000])
        medium_ratio = amount_ranges.get('medium', {}).get('ratio', 0.3)
        
        large_range = amount_ranges.get('large', {}).get('range', [10000, 100000])
        large_ratio = amount_ranges.get('large', {}).get('ratio', 0.1)
        
        # 根据分布随机选择金额分类
        amount_type = random.choices(
            ['small', 'medium', 'large'],
            weights=[small_ratio, medium_ratio, large_ratio],
            k=1
        )[0]
        
        # 根据选中的金额分类确定范围
        if amount_type == 'small':
            min_amount, max_amount = small_range
        elif amount_type == 'medium':
            min_amount, max_amount = medium_range
        else:  # large
            min_amount, max_amount = large_range
        
        # VIP客户的金额通常更高
        if is_vip:
            vip_multiplier = 1.5
            min_amount *= vip_multiplier
            max_amount *= vip_multiplier
        
        # 应用交易类型乘数
        min_amount *= direction_multiplier
        max_amount *= direction_multiplier
        
        # 如果是取款/转出交易，确保不超过账户余额
        if transaction_type in ['withdrawal', 'transfer_out'] and 'balance' in account_info:
            max_amount = min(max_amount, account_info['balance'] * 0.9)  # 留10%的余额
            
            # 如果余额不足，生成更小的金额
            if max_amount < min_amount:
                max_amount = account_info['balance'] * 0.8
                min_amount = min(min_amount, max_amount)
                
                # 如果余额极低，生成极小金额
                if max_amount < 10:
                    return round(max_amount * 0.5, 2)
        
        # 使用对数正态分布生成金额
        # 这种分布在金融交易中更常见，大多数交易集中在较小金额，少数交易为大金额
        mean = (math.log(min_amount) + math.log(max_amount)) / 2
        sigma = (math.log(max_amount) - math.log(min_amount)) / 4  # 确保约95%的值在范围内
        
        amount = math.exp(random.normalvariate(mean, sigma))
        
        # 确保金额在范围内
        amount = max(min_amount, min(amount, max_amount))
        
        # 特殊规则：工资转入类交易
        if transaction_type == 'deposit' and random.random() < 0.15:  # 15%的概率是工资转入
            if not is_corporate:  # 只适用于个人账户
                # 获取客户薪资分类
                salary_category = account_info.get('salary_category', '4级')  # 默认4级
                
                # 根据薪资等级生成工资金额
                salary_levels = {
                    '1级': (2000, 4000),
                    '2级': (4000, 6000),
                    '3级': (6000, 10000),
                    '4级': (10000, 15000),
                    '5级': (15000, 25000),
                    '6级': (25000, 40000),
                    '7级': (40000, 60000),
                    '8级': (60000, 100000)
                }
                
                salary_range = salary_levels.get(salary_category, (10000, 15000))
                
                # 工资通常是整数，且月度相对稳定
                amount = random.randint(int(salary_range[0]), int(salary_range[1]))
                amount = round(amount, -2)  # 舍入到百位
        
        # 针对不同交易类型的金额优化
        if transaction_type == 'consumption':
            # 消费交易通常有较多"整数"金额和较多小数点后有数字的情况
            if random.random() < 0.3:  # 30%的概率是整数金额
                amount = round(amount)
            elif random.random() < 0.4:  # 40%的概率是带角的金额
                amount = round(amount, 1)
            else:  # 30%的概率是带分的金额
                amount = round(amount, 2)
        else:
            # 其他类型交易，大多数是整数或一位小数
            if random.random() < 0.7:  # 70%的概率是整数金额
                amount = round(amount)
            elif random.random() < 0.2:  # 20%的概率是带角的金额
                amount = round(amount, 1)
            else:  # 10%的概率是带分的金额
                amount = round(amount, 2)
        
        # 确保金额为正数
        amount = max(0.01, amount)
        
        return amount
    
    def generate_batch_amounts(self, account_info: Dict, transaction_type: str, count: int) -> List[float]:
        """
        批量生成交易金额
        
        Args:
            account_info: 账户信息
            transaction_type: 交易类型
            count: 数量
            
        Returns:
            List[float] 交易金额列表
        """
        amounts = []
        
        # 如果是取款/转出交易，需要跟踪剩余余额
        remaining_balance = account_info.get('balance', float('inf'))
        if transaction_type not in ['withdrawal', 'transfer_out', 'consumption']:
            # 如果不是支出交易，不需要跟踪余额
            for _ in range(count):
                amounts.append(self.generate_transaction_amount(account_info, transaction_type))
        else:
            # 支出交易需要考虑余额限制
            for _ in range(count):
                # 更新账户信息中的余额
                temp_account = account_info.copy()
                temp_account['balance'] = remaining_balance
                
                # 生成不超过剩余余额的金额
                amount = self.generate_transaction_amount(temp_account, transaction_type)
                amounts.append(amount)
                
                # 更新剩余余额
                remaining_balance -= amount
                
                # 如果余额不足，停止生成
                if remaining_balance <= 0:
                    break
        
        return amounts
