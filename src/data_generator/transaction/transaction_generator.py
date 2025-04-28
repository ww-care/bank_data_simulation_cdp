#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
账户交易生成器模块

负责生成符合CDP业务单据范式的账户交易数据。
"""

import uuid
import random
import datetime
import faker
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union

from src.time_manager.time_manager import get_time_manager
from src.logger import get_logger
from src.data_generator.base_generators import BaseDocGenerator
from src.data_generator.transaction.amount_distribution import AmountDistribution
from src.data_generator.transaction.time_distribution import TimeDistribution
from src.data_generator.transaction.transaction_types import TransactionTypeManager
from src.data_generator.transaction.transaction_description import TransactionDescriptionGenerator
from src.data_generator.transaction.transaction_channel import TransactionChannelManager


class AccountTransactionGenerator(BaseDocGenerator):
    """账户交易生成器，生成符合CDP业务单据范式的交易数据"""
    
    def __init__(self, fake_generator: faker.Faker, config_manager):
        """
        初始化账户交易生成器
        
        Args:
            fake_generator: Faker实例，用于生成随机数据
            config_manager: 配置管理器实例
        """
        super().__init__(fake_generator, config_manager)
        
        # 获取交易相关配置
        self.transaction_config = self.config_manager.get_entity_config('transaction')
        
        # 获取交易表配置
        cdp_model_config = self.config_manager.get_entity_config('cdp_model')
        transaction_tables = cdp_model_config.get('business_doc', {}).get('tables', [])
        
        # 查找交易表配置
        self.transaction_table_config = next(
            (table for table in transaction_tables if table.get('entity') == 'transaction'), 
            {'name': 'cdp_account_transaction', 'id_prefix': 'T'}
        )
        
        # 初始化子模块
        self.amount_distribution = AmountDistribution(self.transaction_config)
        self.time_distribution = TimeDistribution(self.transaction_config)
        self.transaction_type_manager = TransactionTypeManager(self.transaction_config)
        self.transaction_description_generator = TransactionDescriptionGenerator(
            fake_generator, self.transaction_config
        )
        self.transaction_channel_manager = TransactionChannelManager(self.transaction_config)
        
        # 初始化日志
        self.logger = get_logger('AccountTransactionGenerator')
    
    def generate(self, accounts: List[Dict], start_time: datetime.datetime, 
                end_time: datetime.datetime) -> List[Dict]:
        """
        为指定账户生成交易数据
        
        Args:
            accounts: 账户数据列表
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            交易数据列表
        """
        self.logger.info(f"开始生成账户交易数据，时间范围: {start_time} ~ {end_time}")
        
        all_transactions = []
        
        # 为每个账户生成交易
        for account in accounts:
            account_transactions = self._generate_account_transactions(
                account, start_time, end_time
            )
            all_transactions.extend(account_transactions)
        
        # 清洗并验证数据
        transactions = self.clean_docs(all_transactions)
        
        self.logger.info(f"成功生成 {len(transactions)} 条交易数据")
        
        return transactions
    
    def _generate_account_transactions(self, account: Dict, start_time: datetime.datetime, 
                                     end_time: datetime.datetime) -> List[Dict]:
        """
        为单个账户生成交易数据
        
        Args:
            account: 账户数据
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            该账户的交易数据列表
        """
        transactions = []
        
        # 获取账户类型
        account_type = account.get('account_type', 'current')
        
        # 获取客户信息
        customer_id = account.get('customer_id')
        customer_type = account.get('customer_type', 'personal')
        is_vip = account.get('is_vip', False)
        
        # 构建账户信息字典，用于生成交易
        account_info = {
            'account_id': account.get('base_id'),
            'account_type': account_type,
            'customer_id': customer_id,
            'customer_type': customer_type,
            'is_vip': is_vip,
            'balance': account.get('balance', 0),
            'currency': account.get('currency', 'CNY'),
            'status': account.get('status', 'active')
        }
        
        # 检查账户状态，非活跃账户减少交易量
        if account_info['status'] != 'active':
            if account_info['status'] == 'dormant':
                # 休眠账户生成少量交易
                return self._generate_dormant_account_transactions(account_info, start_time, end_time)
            elif account_info['status'] == 'frozen':
                # 冻结账户只生成查询类交易
                return self._generate_frozen_account_transactions(account_info, start_time, end_time)
            elif account_info['status'] == 'closed':
                # 关闭账户不生成交易
                return []
        
        # 确定交易频率
        frequency_config = self.transaction_config.get('frequency', {}).get(account_type, {})
        
        if account_type == 'current':
            # 活期账户月交易频率
            freq_key = 'transactions_per_month'
            time_unit = 30  # 天
        elif account_type == 'fixed':
            # 定期账户季度交易频率
            freq_key = 'transactions_per_quarter'
            time_unit = 90  # 天
        else:
            # 其他类型账户默认月交易频率
            freq_key = 'transactions_per_month'
            time_unit = 30  # 天
        
        # 获取交易频率配置
        frequency_range = frequency_config.get(freq_key, {}).get(customer_type, {})
        min_freq = frequency_range.get('min', 10)
        max_freq = frequency_range.get('max', 30)
        mean_freq = frequency_range.get('mean', 20)
        
        # VIP客户交易频率加成
        vip_multiplier = self.transaction_config.get('frequency', {}).get('vip_multiplier', 1.25)
        if is_vip:
            mean_freq *= vip_multiplier
        
        # 计算时间范围内的交易数量
        days_span = (end_time - start_time).total_seconds() / (24 * 3600)
        base_frequency = mean_freq * (days_span / time_unit)
        
        # 根据时间段和账户信息调整频率
        adjusted_frequency = self.time_distribution.adjust_frequency_by_timespan(
            base_frequency, start_time, end_time, account_info
        )
        
        # 考虑随机波动，生成最终交易数量
        transaction_count = max(0, int(np.random.normal(adjusted_frequency, adjusted_frequency * 0.2)))
        
        # 生成交易记录
        account_balance = account_info['balance']
        
        # 根据交易类型的分布权重，确定各类型交易的数量
        transaction_types = self.transaction_type_manager.distribute_transaction_types(transaction_count)
        
        # 生成各类型的交易
        for transaction_type, count in transaction_types.items():
            # 根据交易类型获取交易金额分布
            amounts = self.amount_distribution.generate_batch_amounts(
                account_info, transaction_type, count
            )
            
            # 依次生成每笔交易
            for amount in amounts:
                # 生成交易时间
                transaction_time = self.time_distribution.generate_transaction_time(
                    start_time, end_time, customer_type
                )
                
                # 生成交易渠道
                channel = self.transaction_channel_manager.get_transaction_channel(
                    transaction_type, transaction_time, account_info
                )
                
                # 生成交易状态（大部分成功）
                status = 'success' if random.random() < 0.98 else 'failed'
                
                # 生成交易描述
                description = self.transaction_description_generator.generate_description(
                    transaction_type, amount, channel
                )
                
                # 更新账户余额
                if status == 'success':
                    if transaction_type in ['deposit', 'transfer_in']:
                        account_balance += amount
                    elif transaction_type in ['withdrawal', 'transfer_out', 'consumption']:
                        account_balance -= amount
                
                # 创建交易记录
                transaction = self._create_transaction_record(
                    account_info, transaction_type, amount, transaction_time,
                    status, channel, description, account_balance
                )
                
                # 添加到交易列表
                transactions.append(transaction)
        
        # 按时间排序
        transactions.sort(key=lambda x: x['detail_time'])
        
        # 重新计算余额，确保正确
        self._recalculate_balances(transactions, account_info['balance'])
        
        return transactions
    
    def _generate_dormant_account_transactions(self, account_info: Dict, 
                                            start_time: datetime.datetime,
                                            end_time: datetime.datetime) -> List[Dict]:
        """
        为休眠账户生成少量交易
        
        Args:
            account_info: 账户信息
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            交易数据列表
        """
        # 休眠账户生成的交易数量较少
        transaction_count = random.randint(0, 2)
        
        transactions = []
        account_balance = account_info['balance']
        
        # 只生成查询和小额存款交易
        for _ in range(transaction_count):
            # 生成交易时间
            transaction_time = self.time_distribution.generate_transaction_time(
                start_time, end_time
            )
            
            # 随机选择交易类型（只有查询和小额存款）
            transaction_type = random.choice(['inquiry', 'deposit'])
            
            # 生成交易金额（存款很小）
            if transaction_type == 'deposit':
                amount = random.uniform(10, 100)
                account_balance += amount
            else:  # inquiry查询没有金额
                amount = 0
            
            # 生成交易渠道（主要是柜台）
            channel = random.choice(['counter', 'atm']) if random.random() < 0.8 else 'online_banking'
            
            # 生成交易描述
            description = self.transaction_description_generator.generate_description(
                transaction_type, amount, channel
            )
            
            # 创建交易记录
            transaction = self._create_transaction_record(
                account_info, transaction_type, amount, transaction_time,
                'success', channel, description, account_balance
            )
            
            # 添加到交易列表
            transactions.append(transaction)
        
        # 按时间排序
        transactions.sort(key=lambda x: x['detail_time'])
        
        return transactions
    
    def _generate_frozen_account_transactions(self, account_info: Dict, 
                                           start_time: datetime.datetime,
                                           end_time: datetime.datetime) -> List[Dict]:
        """
        为冻结账户生成查询类交易
        
        Args:
            account_info: 账户信息
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            交易数据列表
        """
        # 冻结账户只生成查询类交易
        transaction_count = random.randint(1, 3)
        
        transactions = []
        account_balance = account_info['balance']
        
        # 只生成查询交易
        for _ in range(transaction_count):
            # 生成交易时间
            transaction_time = self.time_distribution.generate_transaction_time(
                start_time, end_time
            )
            
            # 交易类型固定为查询
            transaction_type = 'inquiry'
            
            # 查询没有金额
            amount = 0
            
            # 生成交易渠道
            channel = random.choice(['counter', 'online_banking', 'mobile_app'])
            
            # 生成交易描述
            description = self.transaction_description_generator.generate_description(
                transaction_type, amount, channel, frozen=True
            )
            
            # 创建交易记录
            transaction = self._create_transaction_record(
                account_info, transaction_type, amount, transaction_time,
                'success', channel, description, account_balance
            )
            
            # 添加到交易列表
            transactions.append(transaction)
        
        # 按时间排序
        transactions.sort(key=lambda x: x['detail_time'])
        
        return transactions
    
    def _create_transaction_record(self, account_info: Dict, transaction_type: str,
                                 amount: float, transaction_time: datetime.datetime,
                                 status: str, channel: str, description: str,
                                 balance: float) -> Dict:
        """
        创建交易记录
        
        Args:
            account_info: 账户信息
            transaction_type: 交易类型
            amount: 交易金额
            transaction_time: 交易时间
            status: 交易状态
            channel: 交易渠道
            description: 交易描述
            balance: 交易后余额
            
        Returns:
            交易记录字典
        """
        # 基础信息字段生成
        transaction = {}
        
        # 添加分区字段
        transaction['pt'] = self.get_partition_date()
        
        # 添加客户ID
        transaction['base_id'] = account_info['customer_id']
        
        # 生成交易ID
        id_prefix = self.transaction_table_config.get('id_prefix', 'T')
        transaction['detail_id'] = self.generate_id(id_prefix)
        
        # 添加账户ID
        transaction['account_id'] = account_info['account_id']
        
        # 添加交易类型
        transaction['transaction_type'] = transaction_type
        
        # 添加交易金额
        transaction['amount'] = amount
        
        # 添加交易时间
        transaction['detail_time'] = self.datetime_to_timestamp(transaction_time)
        
        # 添加交易状态
        transaction['status'] = status
        
        # 添加交易描述
        transaction['description'] = description
        
        # 添加交易渠道
        transaction['channel'] = channel
        
        # 添加交易后余额
        transaction['balance'] = balance
        
        # 添加货币类型
        transaction['currency'] = account_info['currency']
        
        return transaction
    
    def _recalculate_balances(self, transactions: List[Dict], initial_balance: float) -> None:
        """
        重新计算交易余额，确保一致性
        
        Args:
            transactions: 交易数据列表
            initial_balance: 初始余额
            
        Returns:
            None，原地修改transactions列表
        """
        current_balance = initial_balance
        
        for transaction in transactions:
            transaction_type = transaction['transaction_type']
            amount = transaction['amount']
            status = transaction['status']
            
            # 只有成功的交易才影响余额
            if status == 'success':
                if transaction_type in ['deposit', 'transfer_in']:
                    current_balance += amount
                elif transaction_type in ['withdrawal', 'transfer_out', 'consumption']:
                    current_balance -= amount
            
            # 更新交易记录中的余额
            transaction['balance'] = current_balance
    
    def generate_period_transactions(self, accounts: List[Dict], 
                                   start_time: datetime.datetime,
                                   end_time: datetime.datetime) -> List[Dict]:
        """
        为指定时间段生成交易数据
        
        Args:
            accounts: 账户数据列表
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            交易数据列表
        """
        return self.generate(accounts, start_time, end_time)