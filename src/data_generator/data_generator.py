#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据生成模块主控类

负责协调各类数据生成器的工作，实现历史数据和实时数据的生成。
"""

import os
import uuid
import random
import datetime
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union

# 导入项目模块
from src.config_manager import get_config_manager
from src.database_manager import get_database_manager
from src.time_manager.time_manager import get_time_manager
from src.logger import get_logger
# 导入各种生成器
from src.data_generator.profile_generators import CustomerProfileGenerator, ManagerProfileGenerator
# 文档类生成器
# from src.data_generator.doc_generators import InvestmentOrderGenerator
from src.data_generator.loan.loan_generator import LoanRecordGenerator
# 事件类生成器（将在完成后导入）
# from src.data_generator.event_generators import CustomerEventGenerator, AppEventGenerator, WebEventGenerator
# 通用档案类生成器
from src.data_generator.archive_generators import ProductArchiveGenerator, DepositTypeArchiveGenerator, BranchArchiveGenerator, AccountArchiveGenerator
# 交易相关生成器
from src.data_generator.transaction.transaction_generator import AccountTransactionGenerator
from src.data_generator.transaction.amount_distribution import AmountDistribution
from src.data_generator.transaction.time_distribution import TimeDistribution
from src.data_generator.transaction.transaction_types import TransactionTypeManager
from src.data_generator.transaction.transaction_description import TransactionDescriptionGenerator
from src.data_generator.transaction.transaction_channel import TransactionChannelManager
#档案类生成器
from src.data_generator.loan.loan_generator import LoanRecordGenerator



class DataGenerator:
    """数据生成器总控类，协调各CDP范式生成器的工作"""
    
    def __init__(self):
        """初始化数据生成器"""
        self.logger = get_logger('data_generator')
        self.config_manager = get_config_manager()
        self.time_manager = get_time_manager()
        self.db_manager = get_database_manager()
        
        # 获取系统配置
        self.system_config = self.config_manager.get_system_config()
        
        # 设置随机种子，确保可重复性
        random_seed = self.system_config.get('system', {}).get('random_seed', 42)
        random.seed(random_seed)
        np.random.seed(random_seed)
        
        # 获取批处理大小
        self.batch_size = self.system_config.get('system', {}).get('batch_size', 1000)
        
        # 初始化CDP范式生成器 (后续实现)
        self._init_cdp_generators()
        
        # 生成的数据缓存
        self.data_cache = {}
        
    def _init_cdp_generators(self):
        """初始化各CDP范式生成器"""
        # 创建Faker实例
        from faker import Faker
        locale = self.system_config.get('system', {}).get('locale', 'zh_CN')
        self.faker = Faker(locale)
        
        # 初始化各类生成器
        # 客户档案生成器
        self.customer_profile_generator = CustomerProfileGenerator(self.faker, self.config_manager)
        self.manager_profile_generator = ManagerProfileGenerator(self.faker, self.config_manager)
        
        # 通用档案生成器
        self.product_archive_generator = ProductArchiveGenerator(self.faker, self.config_manager)
        self.deposit_type_archive_generator = DepositTypeArchiveGenerator(self.faker, self.config_manager)
        self.branch_archive_generator = BranchArchiveGenerator(self.faker, self.config_manager)
        self.account_archive_generator = AccountArchiveGenerator(self.faker, self.config_manager)
        
        # 交易生成器
        self.account_transaction_generator = AccountTransactionGenerator(self.faker, self.config_manager)
        
        # 借款记录生成器
        self.loan_record_generator = LoanRecordGenerator(self.faker, self.config_manager)
        
        # 其他生成器将在后续实现
        # self.loan_application_generator = None
        # self.investment_order_generator = None
        # self.customer_event_generator = None
        # self.app_event_generator = None
        # self.web_event_generator = None
        # self.product_archive_generator = None
        # self.deposit_type_archive_generator = None
        # self.branch_archive_generator = None
        # self.account_archive_generator = None
    
    def generate_data(self, start_date: datetime.date, end_date: datetime.date, mode: str = 'historical') -> Dict[str, int]:
        """
        生成指定时间范围内的模拟数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            mode: 数据生成模式，'historical'或'realtime'
            
        Returns:
            各实体生成的记录数统计
        """
        self.logger.info(f"开始生成 {mode} 模式数据，时间范围: {start_date} 至 {end_date}")
        
        stats = {}
        
        try:
            if mode == 'historical':
                stats = self.generate_historical_data(start_date, end_date)
            elif mode == 'realtime':
                stats = self.generate_realtime_data(start_date, end_date)
            else:
                raise ValueError(f"未知的数据生成模式: {mode}")
        
        except Exception as e:
            self.logger.error(f"生成数据过程中出错: {str(e)}", exc_info=True)
            raise
        
        return stats
    
    def generate_historical_data(self, start_date: datetime.date, end_date: datetime.date) -> Dict[str, int]:
        """
        生成历史数据模式下的各类实体数据（CDP范式）
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            各实体生成的记录数统计
        """
        stats = {}
        
        # 1. 生成基础实体数据
        self.logger.info("开始生成基础客户档案数据")
        # 生成客户档案
        customers = self.customer_profile_generator.generate()
        self.data_cache['customers'] = customers
        stats['customers'] = len(customers)
        
        # 生成经理档案
        managers = self.manager_profile_generator.generate()
        self.data_cache['managers'] = managers
        stats['managers'] = len(managers)
        
        # 2. 生成关联实体数据
        # 生成产品档案
        products = self.product_archive_generator.generate()
        self.data_cache['products'] = products
        stats['products'] = len(products)
        
        # 生成存款类型档案
        deposit_types = self.deposit_type_archive_generator.generate()
        self.data_cache['deposit_types'] = deposit_types
        stats['deposit_types'] = len(deposit_types)
        
        # 生成支行档案
        branches = self.branch_archive_generator.generate()
        self.data_cache['branches'] = branches
        stats['branches'] = len(branches)
        
        # 生成账户档案
        accounts = self.account_archive_generator.generate(customers, deposit_types, branches)
        self.data_cache['accounts'] = accounts
        stats['accounts'] = len(accounts)
        
        # 3. 生成借款记录数据
        self.logger.info("开始生成历史借款记录数据")
        loans = self.generate_historical_loans(
            customers, 
            datetime.datetime.combine(start_date, datetime.time.min),
            datetime.datetime.combine(end_date, datetime.time.max)
        )
        self.data_cache['loans'] = loans
        stats['loans'] = len(loans)
        
        # 4. 生成交易数据
        if 'accounts' in self.data_cache and self.data_cache['accounts']:
            self.logger.info("开始生成历史交易数据")
            accounts = self.data_cache['accounts']
            
            # 转换日期为datetime
            start_datetime = datetime.datetime.combine(start_date, datetime.time.min)
            end_datetime = datetime.datetime.combine(end_date, datetime.time.max)
            
            # 分批处理账户，减少内存使用
            batch_size = min(self.batch_size, len(accounts))
            transaction_count = 0
            
            for i in range(0, len(accounts), batch_size):
                batch_accounts = accounts[i:i+batch_size]
                self.logger.info(f"处理第 {i//batch_size + 1} 批账户，共 {len(batch_accounts)} 个")
                
                # 生成该批账户的交易数据
                transactions = self.generate_historical_transactions(
                    batch_accounts, start_datetime, end_datetime
                )
                
                # 导入数据库
                if transactions:
                    imported = self.import_data('cdp_account_transaction', transactions)
                    transaction_count += imported
                    
                    # 清理内存
                    del transactions
            
            stats['transactions'] = transaction_count
        
        # 4. 记录统计信息
        self.logger.info(f"历史数据生成完成，统计: {stats}")
        
        return stats
    
    def generate_realtime_data(self, start_date: datetime.date, end_date: datetime.date) -> Dict[str, int]:
        """
        生成实时数据模式下的增量数据（CDP范式）
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            各实体生成的记录数统计
        """
        stats = {}
        
        # 1. 从数据库加载现有客户和账户数据
        self.logger.info("加载数据库中的客户和账户数据")
        
        # 获取活跃账户数据（这里需要数据库管理器支持）
        try:
            accounts = self.db_manager.get_active_accounts()
            if not accounts:
                self.logger.warning("未找到活跃账户数据，请先运行历史数据生成")
                return {}
        except Exception as e:
            self.logger.error(f"加载账户数据失败: {str(e)}")
            return {}
        
        # 3. 生成借款记录数据
        try:
            # 获取账户对应的客户数据
            customers_map = {account.get('customer_id'): None for account in accounts}
            
            customers_query = "SELECT * FROM cdp_customer_profile WHERE base_id IN ({})".\
                format(", ".join(["'" + cid + "'" for cid in customers_map.keys() if cid]))
            
            customers_data = self.db_manager.execute_query(customers_query)
            for customer in customers_data:
                customers_map[customer.get('base_id')] = customer
            
            # 过滤掉没有对应客户数据的账户
            valid_customers = [c for c in customers_data if c]
            
            if valid_customers:
                self.logger.info("开始生成实时借款记录数据")
                
                loans = self.generate_realtime_loans(
                    valid_customers,
                    start_datetime,
                    end_datetime
                )
                
                # 导入数据库
                if loans:
                    imported = self.import_data('cdp_loan_record', loans)
                    stats['loans'] = imported
                    
                    # 清理内存
                    del loans
            else:
                self.logger.warning("未找到有效客户数据，跳过借款记录生成")
        except Exception as e:
            self.logger.error(f"生成借款记录时出错: {str(e)}")
        
        # 4. 生成实时交易数据
        self.logger.info("开始生成实时交易数据")
        
        # 转换日期为datetime
        start_datetime = datetime.datetime.combine(start_date, datetime.time.min)
        end_datetime = datetime.datetime.combine(end_date, datetime.time.max)
        
        # 分批处理账户，减少内存使用
        batch_size = min(self.batch_size, len(accounts))
        transaction_count = 0
        
        for i in range(0, len(accounts), batch_size):
            batch_accounts = accounts[i:i+batch_size]
            self.logger.info(f"处理第 {i//batch_size + 1} 批账户，共 {len(batch_accounts)} 个")
            
            # 生成该批账户的交易数据
            transactions = self.generate_realtime_transactions(
                batch_accounts, start_datetime, end_datetime
            )
            
            # 导入数据库
            if transactions:
                imported = self.import_data('cdp_account_transaction', transactions)
                transaction_count += imported
                
                # 清理内存
                del transactions
        
        stats['transactions'] = transaction_count
        
        # 3. 记录生成的最后时间点
        self.time_manager.update_last_timestamp(end_datetime)
        
        # 4. 记录统计信息
        self.logger.info(f"实时数据生成完成，统计: {stats}")
        
        return stats
    
    def import_data(self, table_name: str, data: List[Dict]) -> int:
        """
        将生成的数据导入数据库
        
        Args:
            table_name: 表名
            data: 数据列表
            
        Returns:
            导入的记录数
        """
        if not data:
            return 0
            
        try:
            # 调用数据库管理器的导入方法
            imported_count = self.db_manager.import_data(table_name, data)
            self.logger.info(f"成功导入 {imported_count} 条数据到表 {table_name}")
            return imported_count
        except Exception as e:
            self.logger.error(f"导入数据到表 {table_name} 失败: {str(e)}")
            return 0
    
    def generate_data_for_timeperiod(self, start_time: datetime.datetime, 
                                   end_time: datetime.datetime, mode: str = 'realtime') -> Dict[str, int]:
        """
        为指定的时间段生成数据（包含时间信息）
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            mode: 数据生成模式
            
        Returns:
            各实体生成的记录数统计
        """
        return self.generate_data(start_time.date(), end_time.date(), mode)


# 单例模式
_instance = None

def get_data_generator() -> DataGenerator:
    """
    获取DataGenerator的单例实例
    
    Returns:
        DataGenerator实例
    """
    global _instance
    if _instance is None:
        _instance = DataGenerator()
    return _instance


    def generate_historical_transactions(self, accounts: List[Dict], start_time: datetime.datetime, 
                                     end_time: datetime.datetime) -> List[Dict]:
        """
        生成历史交易数据
        
        Args:
            accounts: 账户数据列表
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            交易数据列表
        """
        self.logger.info(f"开始生成历史交易数据，时间范围: {start_time} ~ {end_time}")
        
        # 使用账户交易生成器生成交易数据
        transactions = self.account_transaction_generator.generate(
            accounts, start_time, end_time
        )
        
        self.logger.info(f"成功生成 {len(transactions)} 条历史交易数据")
        
        return transactions
    
    def generate_historical_loans(self, customers: List[Dict], 
                               start_time: datetime.datetime, 
                               end_time: datetime.datetime) -> List[Dict]:
        """
        生成历史借款记录数据
        
        Args:
            customers: 客户数据列表
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            借款记录数据列表
        """
        self.logger.info(f"开始生成历史借款记录数据，时间范围: {start_time} ~ {end_time}")
        
        # 使用借款记录生成器生成借款数据
        loans = self.loan_record_generator.generate(
            customers, start_time, end_time
        )
        
        self.logger.info(f"成功生成 {len(loans)} 条历史借款记录数据")
        
        return loans
    
    def generate_realtime_loans(self, customers: List[Dict], 
                            start_time: datetime.datetime, 
                            end_time: datetime.datetime) -> List[Dict]:
        """
        生成实时借款记录数据
        
        Args:
            customers: 客户数据列表
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            借款记录数据列表
        """
        self.logger.info(f"开始生成实时借款记录数据，时间范围: {start_time} ~ {end_time}")
        
        # 使用借款记录生成器生成借款数据
        loans = self.loan_record_generator.generate_period_loans(
            customers, start_time, end_time
        )
        
        self.logger.info(f"成功生成 {len(loans)} 条实时借款记录数据")
        
        return loans
    
    def generate_realtime_transactions(self, accounts: List[Dict], start_time: datetime.datetime, 
                                    end_time: datetime.datetime) -> List[Dict]:
        """
        生成实时交易数据
        
        Args:
            accounts: 账户数据列表
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            交易数据列表
        """
        self.logger.info(f"开始生成实时交易数据，时间范围: {start_time} ~ {end_time}")
        
        # 使用账户交易生成器生成交易数据
        transactions = self.account_transaction_generator.generate_period_transactions(
            accounts, start_time, end_time
        )
        
        self.logger.info(f"成功生成 {len(transactions)} 条实时交易数据")
        
        return transactions
    
    # 添加借款记录生成方法
    def generate_historical_loans(self, customers: List[Dict], 
                                start_time: datetime.datetime, 
                                end_time: datetime.datetime) -> List[Dict]:
        """
        生成历史借款记录数据
        
        Args:
            customers: 客户数据列表
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            借款记录数据列表
        """
        self.logger.info(f"开始生成历史借款记录数据，时间范围: {start_time} ~ {end_time}")
        
        # 使用借款记录生成器生成借款数据
        loans = self.loan_record_generator.generate(
            customers, start_time, end_time
        )
        
        self.logger.info(f"成功生成 {len(loans)} 条历史借款记录数据")
        
        return loans

    def generate_realtime_loans(self, customers: List[Dict], 
                            start_time: datetime.datetime, 
                            end_time: datetime.datetime) -> List[Dict]:
        """
        生成实时借款记录数据
        
        Args:
            customers: 客户数据列表
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            借款记录数据列表
        """
        self.logger.info(f"开始生成实时借款记录数据，时间范围: {start_time} ~ {end_time}")
        
        # 使用借款记录生成器生成借款数据
        loans = self.loan_record_generator.generate_period_loans(
            customers, start_time, end_time
        )
        
        self.logger.info(f"成功生成 {len(loans)} 条实时借款记录数据")
        
        return loans


# 单例模式
_instance = None

def get_data_generator() -> DataGenerator:
    """
    获取DataGenerator的单例实例
    
    Returns:
        DataGenerator实例
    """
    global _instance
    if _instance is None:
        _instance = DataGenerator()
    return _instance


if __name__ == "__main__":
    # 简单测试
    generator = get_data_generator()
    
    # 计算测试时间范围
    time_manager = get_time_manager()
    start_date, end_date = time_manager.calculate_historical_period()
    
    print(f"测试时间范围: {start_date} 至 {end_date}")
    # 仅生成少量测试数据
    test_start_date = end_date - datetime.timedelta(days=7)
    
    # 生成测试数据
    generator.generate_data(test_start_date, end_date, mode='historical')
