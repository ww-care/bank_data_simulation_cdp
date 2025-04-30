#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
通用档案范式数据生成器

负责生成符合CDP通用档案范式的数据，包括产品档案、存款类型档案、支行档案、账户档案等。
"""

import uuid
import random
import datetime
import faker
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union

from src.time_manager.time_manager import get_time_manager
from src.config_manager import ConfigManager


class BaseArchiveGenerator:
    """通用档案范式生成器基类"""
    
    def __init__(self, fake_generator: faker.Faker, config_manager):
        """
        初始化档案生成器
        
        Args:
            fake_generator: Faker实例，用于生成随机数据
            config_manager: 配置管理器实例
        """
        self.faker = fake_generator
        self.config_manager = config_manager
        self.time_manager = get_time_manager()
    
    def generate_id(self, prefix: str = '') -> str:
        """
        生成档案ID
        
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
    
    def generate(self, count: Optional[int] = None) -> List[Dict]:
        """
        生成档案数据（基类方法，需要在子类中实现）
        
        Args:
            count: 生成的档案数量
            
        Returns:
            档案数据列表
        """
        raise NotImplementedError("子类必须实现此方法")


class ProductArchiveGenerator(BaseArchiveGenerator):
    """产品档案生成器，生成符合CDP通用档案范式的产品数据"""
    
    def __init__(self, fake_generator: faker.Faker, config_manager):
        """
        初始化产品档案生成器
        
        Args:
            fake_generator: Faker实例，用于生成随机数据
            config_manager: 配置管理器实例
        """
        super().__init__(fake_generator, config_manager)
        # 定义产品相关常量和配置
        self.bank_names = ['中国银行', '工商银行', '建设银行', '农业银行', '招商银行', 
                           '交通银行', '浦发银行', '兴业银行', '民生银行', '平安银行']
        self.product_types = ['股票型基金', '货币型基金', '债券型基金', '其他']
        self.risk_levels = ['R1', 'R2', 'R3', 'R4', 'R5']
        self.redemption_ways = ['随时赎回', '固定赎回']
        self.marketing_statuses = ['在售', '关闭']
        
        # 从配置文件中加载产品相关配置
        self.investment_config = config_manager.get_config().get('investment', {})
    
    def generate_product_id(self, product_type=''):
        """
        生成符合规范的产品ID
        产品ID格式：P + 产品类型代码(2位) + 随机数字(8位)
        
        Args:
            product_type: 产品类型，如 '股票型基金', '货币型基金', '债券型基金', '其他'
        
        Returns:
            符合规范的产品ID字符串
        """
        product_type_codes = {
            '股票型基金': 'ST',
            '货币型基金': 'MM',
            '债券型基金': 'BD',
            '其他': 'OT'
        }
        
        # 如果没有提供产品类型或提供的产品类型不在映射表中，则随机选择一种
        if not product_type or product_type not in product_type_codes:
            product_type = random.choice(list(product_type_codes.keys()))
        
        type_code = product_type_codes.get(product_type, 'OT')
        random_digits = ''.join([str(random.randint(0, 9)) for _ in range(8)])
        
        return f"P{type_code}{random_digits}"
    
    def generate_product_name(self, product_type='', bank_name=''):
        """
        生成符合金融产品命名特征的产品名称
        
        Args:
            product_type: 产品类型，如 '股票型基金', '货币型基金', '债券型基金', '其他'
            bank_name: 银行名称，如未提供则从银行列表中随机选择
        
        Returns:
            符合金融产品特征的产品名称
        """
        # 银行名称，如果未提供则随机选择
        if not bank_name:
            bank_name = random.choice(self.bank_names)
        
        # 产品类型，如果未提供则随机选择
        if not product_type or product_type not in self.product_types:
            product_type = random.choice(self.product_types)
        
        # 根据产品类型设置前缀词库
        prefix_words = {
            '股票型基金': ['稳健', '成长', '价值', '红利', '优选', '精选', '蓝筹', '创新', '领先', '核心'],
            '货币型基金': ['日盈', '周盈', '月盈', '年盈', '现金宝', '活期通', '财富宝', '理财通', '收益通', '增利'],
            '债券型基金': ['稳利', '恒利', '固收', '稳健', '双利', '增益', '安盈', '恒益', '优享', '尊享'],
            '其他': ['灵活', '多元', '智选', '臻选', '策略', '安泰', '优势', '远见', '睿智', '先机']
        }
        
        # 根据产品类型设置后缀词库
        suffix_words = {
            '股票型基金': ['基金', '股基', '股票基金', '价值投资', '成长基金', '精选', '战略配置'],
            '货币型基金': ['货币基金', '现金管理', '流动利', '低风险产品', '活期理财', '现金宝'],
            '债券型基金': ['债券型基金', '固定收益', '收益型产品', '债券基金', '安心回报', '稳健收益'],
            '其他': ['混合型基金', '灵活配置', '多元增利', '策略精选', '组合投资', '资产配置']
        }
        
        # 期限词库
        period_words = ['', '', '', '3个月', '6个月', '1年', '2年', '3年', '5年']  # 空字符串增加不带期限的概率
        
        # 系列号词库
        series_options = ['', '', '', '第一期', '第二期', '第三期', 'A款', 'B款', 'C款', '优享版', '尊享版']  # 空字符串增加不带系列号的概率
        
        # 根据产品类型选择前缀和后缀
        prefix = random.choice(prefix_words[product_type])
        suffix = random.choice(suffix_words[product_type])
        
        # 随机决定是否添加期限和系列号
        period = random.choice(period_words)
        series = random.choice(series_options)
        
        # 组合产品名称，根据不同组件的存在与否调整格式
        name_parts = [bank_name, prefix]
        
        if period:
            name_parts.append(period)
        
        name_parts.append(suffix)
        
        if series:
            name_parts.append(series)
        
        return "".join(name_parts)
    
    def generate_risk_level(self, product_type=''):
        """
        根据产品类型生成风险等级
        
        Args:
            product_type: 产品类型，不同类型产品有不同的风险等级分布
        
        Returns:
            风险等级字符串（R1-R5）
        """
        # 根据产品类型设置风险等级概率分布
        risk_probabilities = {
            '股票型基金': [0.05, 0.10, 0.20, 0.40, 0.25],  # R1到R5的概率
            '货币型基金': [0.60, 0.30, 0.10, 0.00, 0.00],
            '债券型基金': [0.20, 0.40, 0.30, 0.10, 0.00],
            '其他': [0.15, 0.25, 0.30, 0.20, 0.10]
        }
        
        # 如果未提供产品类型或类型不存在，使用默认分布
        if not product_type or product_type not in risk_probabilities:
            product_type = '其他'
        
        # 根据概率分布随机选择风险等级
        return random.choices(
            self.risk_levels,
            weights=risk_probabilities[product_type],
            k=1
        )[0]
    

    def generate_base_product_info(self) -> Dict:
        """
        生成产品基础信息
        
        Returns:
            包含产品基础信息的字典
        """
        # 随机选择产品类型
        product_type = random.choice(self.product_types)
        
        # 随机选择银行名称
        bank_name = random.choice(self.bank_names)
        
        # 生成产品ID
        base_id = self.generate_product_id(product_type)
        
        # 生成产品名称
        name = self.generate_product_name(product_type, bank_name)
        
        # 生成风险等级
        risk_level = self.generate_risk_level(product_type)
        
        # 生成基础产品信息字典
        product_info = {
            'pt': self.get_partition_date(),
            'base_id': base_id,
            'name': name,
            'bank_name': bank_name,
            'type': 'financial_product',  # 产品大类
            'product_type': product_type,  # 产品细分类型
            'risk_level': risk_level
        }
        
        return product_info
    
    def generate_product_attributes(self, product_info: Dict) -> Dict:
        """
        生成产品属性，包括投资期限、预期收益率、最低投资金额等
        
        Args:
            product_info: 包含产品基础信息的字典
            
        Returns:
            添加了产品属性的字典
        """
        product_type = product_info['product_type']
        risk_level = product_info['risk_level']
        
        # 生成投资期限(月)，不同产品类型有不同的期限分布
        investment_period_ranges = {
            '股票型基金': (12, 60),
            '货币型基金': (1, 12),
            '债券型基金': (3, 36),
            '其他': (6, 24)
        }
        
        period_range = investment_period_ranges.get(product_type, (3, 36))
        # 特殊处理货币型基金，更偏向短期
        if product_type == '货币型基金':
            investment_period = random.choice([1, 3, 6, 12])
        else:
            investment_period = random.randint(period_range[0], period_range[1])
            # 确保期限是3的倍数（3个月、6个月、9个月等）
            investment_period = (investment_period // 3) * 3
            if investment_period == 0:
                investment_period = 3
        
        # 生成预期收益率，基于风险等级和产品类型
        # 基础收益率范围
        base_yield_ranges = {
            'R1': (0.020, 0.035),  # 最低风险
            'R2': (0.030, 0.045),
            'R3': (0.040, 0.060),
            'R4': (0.055, 0.080),
            'R5': (0.070, 0.120)   # 最高风险
        }
        
        # 产品类型调整系数
        type_adjustment = {
            '股票型基金': 0.015,  # 股票型基金收益率上浮
            '货币型基金': -0.010,  # 货币型基金收益率下调
            '债券型基金': 0.000,   # 债券型基金无调整
            '其他': 0.005         # 其他类型小幅上浮
        }
        
        # 期限调整系数（期限越长，收益率越高）
        period_adjustment = min(investment_period / 12 * 0.005, 0.020)
        
        # 计算收益率范围
        base_range = base_yield_ranges.get(risk_level, (0.030, 0.050))
        adjustment = type_adjustment.get(product_type, 0.000) + period_adjustment
        
        # 生成最终收益率
        min_yield = max(0.010, base_range[0] + adjustment)  # 确保最低不小于1%
        max_yield = min(0.150, base_range[1] + adjustment)  # 确保最高不超过15%
        expected_yield = round(random.uniform(min_yield, max_yield), 4)
        
        # 生成最低投资金额
        min_investment_ranges = {
            '股票型基金': (1000, 10000),
            '货币型基金': (100, 1000),
            '债券型基金': (5000, 50000),
            '其他': (10000, 100000)
        }
        
        # 风险等级调整系数（风险越高，最低投资额越高）
        risk_multiplier = {
            'R1': 1.0,
            'R2': 1.2,
            'R3': 1.5,
            'R4': 2.0,
            'R5': 3.0
        }
        
        investment_range = min_investment_ranges.get(product_type, (5000, 50000))
        multiplier = risk_multiplier.get(risk_level, 1.0)
        
        # 计算最低投资金额并使其为整百或整千
        base_min_investment = random.randint(int(investment_range[0] * multiplier), 
                                            int(investment_range[1] * multiplier))
        
        # 调整为整数单位
        if base_min_investment < 10000:
            minimum_investment = round(base_min_investment / 100) * 100  # 整百
        else:
            minimum_investment = round(base_min_investment / 1000) * 1000  # 整千
        
        # 更新产品信息
        product_info.update({
            'investment_period': investment_period,
            'expected_yield': expected_yield,
            'minimum_investment': float(minimum_investment)
        })
        
        return product_info
    
    def generate_product_status_features(self, product_info: Dict) -> Dict:
        """
        生成产品状态与特性，包括赎回方式、营销状态、上架日期等
        
        Args:
            product_info: 包含产品基础信息和属性的字典
            
        Returns:
            添加了产品状态与特性的字典
        """
        product_type = product_info['product_type']
        risk_level = product_info['risk_level']
        
        # 生成赎回方式，不同产品类型有不同的赎回方式分布
        redemption_probabilities = {
            '股票型基金': {'随时赎回': 0.3, '固定赎回': 0.7},
            '货币型基金': {'随时赎回': 0.9, '固定赎回': 0.1},
            '债券型基金': {'随时赎回': 0.4, '固定赎回': 0.6},
            '其他': {'随时赎回': 0.5, '固定赎回': 0.5}
        }
        
        prob_dict = redemption_probabilities.get(product_type, {'随时赎回': 0.5, '固定赎回': 0.5})
        redemption_way = random.choices(
            list(prob_dict.keys()),
            weights=list(prob_dict.values()),
            k=1
        )[0]
        
        # 生成营销状态，根据历史时间和产品特性
        # 在售概率基础值
        base_on_sale_probability = 0.8
        
        # 风险等级调整（高风险产品在售比例低）
        risk_adjustment = {
            'R1': 0.1,   # 低风险产品在售比例提高
            'R2': 0.05,
            'R3': 0.0,
            'R4': -0.05,
            'R5': -0.1   # 高风险产品在售比例降低
        }
        
        # 计算最终在售概率
        on_sale_probability = base_on_sale_probability + risk_adjustment.get(risk_level, 0.0)
        on_sale_probability = min(max(on_sale_probability, 0.0), 1.0)  # 确保概率在0-1之间
        
        marketing_status = random.choices(
            ['在售', '关闭'],
            weights=[on_sale_probability, 1 - on_sale_probability],
            k=1
        )[0]
        
        # 生成上线日期：根据系统配置的历史起始日期往前推最多1年
        historical_start_date_str = self.config_manager.get_config().get('system', {}).get(
            'historical_start_date', '2024-04-01')
        
        # 转换为datetime对象
        try:
            historical_start_date = datetime.datetime.strptime(historical_start_date_str, '%Y-%m-%d').date()
        except:
            historical_start_date = datetime.date(2024, 4, 1)  # 默认值
        
        # 产品上线日期：从历史开始日期往前推0-360天
        days_before_start = random.randint(0, 360)
        launch_date = historical_start_date - datetime.timedelta(days=days_before_start)
        
        # 关闭产品的上线日期应该更早
        if marketing_status == '关闭':
            days_before_start = random.randint(180, 540)  # 关闭产品上线日期更早
            launch_date = historical_start_date - datetime.timedelta(days=days_before_start)
        
        # 生成利率（可选，主要用于存款产品）
        # 如果是货币型基金，利率通常等于预期收益率
        if product_type == '货币型基金':
            interest_rate = product_info['expected_yield']
        else:
            # 其他产品利率可以略低于预期收益率
            interest_rate = round(product_info['expected_yield'] * 0.9, 4)
        
        # 更新产品信息
        product_info.update({
            'redemption_way': redemption_way,
            'marketing_status': marketing_status,
            'launch_date': launch_date.strftime('%Y-%m-%d'),
            'interest_rate': interest_rate
        })
    
        return product_info
    
    def generate(self, count: Optional[int] = None) -> List[Dict]:
        """
        生成产品档案数据
        
        Args:
            count: 生成的产品数量
            
        Returns:
            产品档案数据列表
        """
        # 如果未指定数量，使用默认值
        if count is None:
            count = 100  # 默认生成100个产品
        
        products = []
        
        # 生成指定数量的产品
        for _ in range(count):
            # 1. 生成基础产品信息
            product = self.generate_base_product_info()
            
            # 2. 添加产品属性
            product = self.generate_product_attributes(product)
            
            # 3. 添加产品状态与特性
            product = self.generate_product_status_features(product)
            
            # 4. 添加创建时间
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            product['create_time'] = current_time
            product['update_time'] = current_time
            
            products.append(product)
        
        return products


class DepositTypeArchiveGenerator(BaseArchiveGenerator):
    """存款类型档案生成器，生成符合CDP通用档案范式的存款类型数据"""
    
    def __init__(self, fake_generator: faker.Faker, config_manager):
        """
        初始化存款类型档案生成器
        
        Args:
            fake_generator: Faker实例，用于生成随机数据
            config_manager: 配置管理器实例
        """
        super().__init__(fake_generator, config_manager)
        # 定义存款类型相关常量和配置
        self.deposit_types = ['活期存款', '定期存款', '大额存单', '智能存款', '结构性存款']
        self.term_options = [0, 3, 6, 12, 24, 36, 60]  # 0表示活期，其他表示月数
        
        # 从配置文件中加载存款相关配置
        self.account_config = config_manager.get_config().get('account', {})
    
    def generate_deposit_type_id(self, deposit_type=''):
        """
        生成符合规范的存款类型ID
        存款类型ID格式：DT + 存款类型代码(2位) + 随机数字(6位)
        
        Args:
            deposit_type: 存款类型，如 '活期存款', '定期存款', '大额存单'等
            
        Returns:
            符合规范的存款类型ID字符串
        """
        deposit_type_codes = {
            '活期存款': 'CD',  # Current Deposit
            '定期存款': 'TD',  # Time Deposit
            '大额存单': 'LD',  # Large Deposit
            '智能存款': 'SD',  # Smart Deposit
            '结构性存款': 'ST'   # Structured Deposit
        }
        
        # 如果没有提供存款类型或提供的类型不在映射表中，则随机选择一种
        if not deposit_type or deposit_type not in deposit_type_codes:
            deposit_type = random.choice(list(deposit_type_codes.keys()))
        
        type_code = deposit_type_codes.get(deposit_type, 'OT')
        random_digits = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        return f"DT{type_code}{random_digits}"
    
    def generate_deposit_type_name(self, deposit_type=''):
        """
        生成符合银行业务规范的存款类型名称
        
        Args:
            deposit_type: 存款类型，如未提供则随机选择
            
        Returns:
            符合银行业务规范的存款类型名称
        """
        # 存款类型，如果未提供则随机选择
        if not deposit_type or deposit_type not in self.deposit_types:
            deposit_type = random.choice(self.deposit_types)
        
        # 前缀词库
        prefix_words = {
            '活期存款': ['普通', '个人', '企业', '高息', '优享', '灵活'],
            '定期存款': ['整存整取', '零存整取', '整存零取', '存本取息', '递增利率'],
            '大额存单': ['高端', '尊享', '私人', '增利', '稳盈'],
            '智能存款': ['阶梯式', '靠档计息', '智盈', '灵活盈', '步步高'],
            '结构性存款': ['保本型', '非保本型', '挂钩型', '收益型', '双币种']
        }
        
        # 后缀词库
        suffix_words = {
            '活期存款': ['账户', '存款', '储蓄卡'],
            '定期存款': ['存款', '储蓄', '定期产品'],
            '大额存单': ['存单', '理财', '存款产品'],
            '智能存款': ['智能产品', '存款计划', '理财存款'],
            '结构性存款': ['理财产品', '增值存款', '组合产品']
        }
        
        # 期限词库，只用于非活期存款
        if deposit_type != '活期存款':
            term_words = ['三个月', '半年', '一年', '两年', '三年', '五年']
            term = random.choice(term_words)
        else:
            term = ""
        
        # 根据存款类型选择前缀和后缀
        prefix = random.choice(prefix_words[deposit_type])
        suffix = random.choice(suffix_words[deposit_type])
        
        # 组合名称
        if term:
            name = f"{prefix}{term}{suffix}"
        else:
            name = f"{prefix}{suffix}"
        
        return name
    
    def generate_base_interest_rate(self, deposit_type='', term=0):
        """
        生成基准利率
        
        Args:
            deposit_type: 存款类型
            term: 存款期限(月)
            
        Returns:
            基准利率值
        """
        # 央行基准利率参考值（根据不同期限和类型）
        base_rates = {
            '活期存款': 0.0025,  # 0.25%
            '定期存款': {
                3: 0.0150,   # 1.50%
                6: 0.0175,   # 1.75%
                12: 0.0225,  # 2.25%
                24: 0.0275,  # 2.75%
                36: 0.0325,  # 3.25%
                60: 0.0350   # 3.50%
            },
            '大额存单': {
                3: 0.0175,   # 1.75%
                6: 0.0200,   # 2.00%
                12: 0.0250,  # 2.50%
                24: 0.0300,  # 3.00%
                36: 0.0350,  # 3.50%
                60: 0.0375   # 3.75%
            },
            '智能存款': {
                3: 0.0160,   # 1.60%
                6: 0.0185,   # 1.85%
                12: 0.0235,  # 2.35%
                24: 0.0285,  # 2.85%
                36: 0.0335,  # 3.35%
                60: 0.0360   # 3.60%
            },
            '结构性存款': {
                3: 0.0180,   # 1.80%
                6: 0.0210,   # 2.10%
                12: 0.0260,  # 2.60%
                24: 0.0310,  # 3.10%
                36: 0.0360,  # 3.60%
                60: 0.0385   # 3.85%
            }
        }
        
        # 如果是活期存款，直接返回活期基准利率
        if deposit_type == '活期存款' or term == 0:
            return base_rates['活期存款']
        
        # 不同银行的上浮系数（上浮比例）
        bank_float_ratio = random.uniform(0.9, 1.2)
        
        # 获取该类型和期限的基准利率
        if deposit_type in base_rates and isinstance(base_rates[deposit_type], dict):
            # 找到最接近的期限
            terms = sorted(list(base_rates[deposit_type].keys()))
            closest_term = min(terms, key=lambda x: abs(x - term))
            base_rate = base_rates[deposit_type][closest_term]
        else:
            # 找不到对应类型，使用定期存款基准利率
            terms = sorted(list(base_rates['定期存款'].keys()))
            closest_term = min(terms, key=lambda x: abs(x - term))
            base_rate = base_rates['定期存款'][closest_term]
        
        # 计算最终利率，保留4位小数
        final_rate = round(base_rate * bank_float_ratio, 4)
        
        # 确保利率在合理范围内
        final_rate = max(0.001, min(0.05, final_rate))
        
        return final_rate
    
    def generate_deposit_terms(self, deposit_type=''):
        """
        生成存款期限参数
        
        Args:
            deposit_type: 存款类型
            
        Returns:
            包含最短期限和最长期限的元组(min_term, max_term)
        """
        if deposit_type == '活期存款':
            return (0, 0)  # 活期存款没有固定期限
        
        # 不同存款类型的期限范围
        term_ranges = {
            '定期存款': (3, 60),
            '大额存单': (3, 60),
            '智能存款': (3, 36),
            '结构性存款': (3, 24)
        }
        
        # 获取该类型的期限范围
        term_range = term_ranges.get(deposit_type, (3, 36))
        
        # 选择最小期限
        valid_terms = [t for t in self.term_options if t >= term_range[0] and t <= term_range[1]]
        if not valid_terms:
            valid_terms = [3, 6, 12]  # 默认值
        
        min_term = random.choice(valid_terms)
        
        # 选择最大期限
        valid_max_terms = [t for t in valid_terms if t >= min_term]
        if not valid_max_terms:
            max_term = min_term
        else:
            max_term = random.choice(valid_max_terms)
        
        return (min_term, max_term)
    
    def generate_min_amount(self, deposit_type=''):
        """
        生成最低存款金额
        
        Args:
            deposit_type: 存款类型
            
        Returns:
            最低存款金额
        """
        # 不同存款类型的最低金额范围
        min_amount_ranges = {
            '活期存款': (1, 100),
            '定期存款': (1000, 5000),
            '大额存单': (100000, 300000),
            '智能存款': (5000, 20000),
            '结构性存款': (50000, 100000)
        }
        
        # 获取该类型的金额范围
        amount_range = min_amount_ranges.get(deposit_type, (1000, 10000))
        
        # 生成最低金额，并调整为整数
        min_amount = random.randint(amount_range[0], amount_range[1])
        
        # 对于大额存单和结构性存款，调整为整万
        if deposit_type in ['大额存单', '结构性存款']:
            min_amount = (min_amount // 10000) * 10000
            if min_amount == 0:
                min_amount = 10000
        # 对于定期和智能存款，调整为整千或整百
        elif deposit_type in ['定期存款', '智能存款']:
            if min_amount >= 10000:
                min_amount = (min_amount // 1000) * 1000
            else:
                min_amount = (min_amount // 100) * 100
                if min_amount == 0:
                    min_amount = 100
        
        return float(min_amount)
    
    def generate_description(self, deposit_type='', name='', base_interest_rate=0, min_term=0, max_term=0, min_amount=0):
        """
        生成存款类型描述
        
        Args:
            deposit_type: 存款类型
            name: 存款类型名称
            base_interest_rate: 基准利率
            min_term: 最短期限
            max_term: 最长期限
            min_amount: 最低存款金额
            
        Returns:
            存款类型描述文本
        """
        # 基本产品描述模板
        templates = {
            '活期存款': [
                "{name}是一种随存随取的基础存款产品，年利率{rate}%，存取灵活方便，资金安全有保障。",
                "{name}提供灵活的资金管理，年利率{rate}%，最低起存金额{amount}元，支持随时存取。",
                "{name}是满足日常流动性需求的基础产品，年利率{rate}%，安全稳妥，便捷易用。"
            ],
            '定期存款': [
                "{name}是期限为{min_term}至{max_term}个月的定期存款产品，年利率高达{rate}%，最低起存金额{amount}元。",
                "{name}提供{min_term}至{max_term}个月的多种期限选择，年利率{rate}%，到期自动转存，收益稳健。",
                "{name}是一款存期{min_term}至{max_term}个月的定期产品，年利率{rate}%，本息保障，收益可观。"
            ],
            '大额存单': [
                "{name}是面向高端客户的大额存款产品，期限{min_term}至{max_term}个月，年利率高达{rate}%，最低起存金额{amount}元。",
                "{name}为您提供{min_term}至{max_term}个月的大额存单选择，年利率{rate}%，安全性高，收益稳健可观。",
                "{name}是一款高端定制存款产品，存期{min_term}至{max_term}个月，年利率{rate}%，尊享优质金融服务。"
            ],
            '智能存款': [
                "{name}是一款智能灵活的存款产品，期限{min_term}至{max_term}个月，年利率{rate}%，根据存款时间智能调整利率。",
                "{name}提供{min_term}至{max_term}个月的灵活存期，年利率最高{rate}%，智能阶梯计息，最低起存金额{amount}元。",
                "{name}是结合活期灵活性和定期高收益的智能产品，存期{min_term}至{max_term}个月，年利率{rate}%，满足多样化需求。"
            ],
            '结构性存款': [
                "{name}是与金融市场挂钩的结构性存款，期限{min_term}至{max_term}个月，年利率最高可达{rate}%，最低起存金额{amount}元。",
                "{name}为您提供{min_term}至{max_term}个月的结构性理财选择，年利率{rate}%，收益机会更多，风险可控。",
                "{name}是一款创新型存款产品，存期{min_term}至{max_term}个月，年利率{rate}%，灵活配置，潜在收益更高。"
            ]
        }
        
        # 获取对应存款类型的描述模板
        type_templates = templates.get(deposit_type, templates['定期存款'])
        
        # 随机选择一个模板
        template = random.choice(type_templates)
        
        # 填充模板
        description = template.format(
            name=name,
            rate=round(base_interest_rate * 100, 2),  # 转换为百分比
            min_term=min_term,
            max_term=max_term,
            amount=int(min_amount)
        )
        
        return description
    
    def generate_deposit_type(self) -> Dict:
        """
        生成一个完整的存款类型档案
        
        Returns:
            存款类型档案字典
        """
        # 选择存款类型
        deposit_type = random.choice(self.deposit_types)
        
        # 生成存款类型ID
        base_id = self.generate_deposit_type_id(deposit_type)
        
        # 生成存款类型名称
        name = self.generate_deposit_type_name(deposit_type)
        
        # 生成存款期限
        min_term, max_term = self.generate_deposit_terms(deposit_type)
        
        # 生成基准利率（取平均期限的利率）
        avg_term = (min_term + max_term) // 2 if min_term != max_term else min_term
        base_interest_rate = self.generate_base_interest_rate(deposit_type, avg_term)
        
        # 生成最低金额
        min_amount = self.generate_min_amount(deposit_type)
        
        # 生成描述
        description = self.generate_description(
            deposit_type, name, base_interest_rate, min_term, max_term, min_amount
        )
        
        # 创建存款类型数据字典
        deposit_type_data = {
            'pt': self.get_partition_date(),
            'base_id': base_id,
            'name': name,
            'description': description,
            'base_interest_rate': base_interest_rate,
            'min_term': min_term,
            'max_term': max_term,
            'min_amount': min_amount,
            'create_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'update_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return deposit_type_data
    
    def generate(self, count: Optional[int] = None) -> List[Dict]:
        """
        生成存款类型档案数据
        
        Args:
            count: 生成的存款类型数量
            
        Returns:
            存款类型档案数据列表
        """
        # 如果未指定数量，使用默认值
        if count is None:
            count = 20  # 默认生成20种存款类型
        
        deposit_types = []
        
        # 确保每种存款类型至少有一个
        for deposit_type in self.deposit_types:
            # 生成存款类型数据
            deposit_type_data = self.generate_deposit_type()
            deposit_types.append(deposit_type_data)
        
        # 生成剩余的存款类型
        remaining = count - len(self.deposit_types)
        for _ in range(max(0, remaining)):
            deposit_type_data = self.generate_deposit_type()
            deposit_types.append(deposit_type_data)
        
        return deposit_types


class BranchArchiveGenerator(BaseArchiveGenerator):
    """支行档案生成器，生成符合CDP通用档案范式的支行数据"""
    
    def __init__(self, fake_generator: faker.Faker, config_manager):
        """
        初始化支行档案生成器
        
        Args:
            fake_generator: Faker实例，用于生成随机数据
            config_manager: 配置管理器实例
        """
        super().__init__(fake_generator, config_manager)
        # 定义支行相关常量和配置
        self.bank_names = ['中国银行', '工商银行', '建设银行', '农业银行', '招商银行',
                           '交通银行', '浦发银行', '兴业银行', '民生银行', '平安银行']
        self.branch_types = ['总行', '一级分行', '二级分行', '支行', '社区网点']
        self.branch_statuses = ['正常营业', '装修中', '已关闭']
        
        # 从配置文件中加载支行相关配置
        self.branch_config = config_manager.get_config().get('branch', {})
    
    def generate_branch_id(self, branch_type=''):
        """
        生成符合规范的支行ID
        支行ID格式：B + 支行类型代码(2位) + 随机数字(8位)
        
        Args:
            branch_type: 支行类型，如 '总行', '一级分行', '二级分行', '支行', '社区网点'
            
        Returns:
            符合规范的支行ID字符串
        """
        branch_type_codes = {
            '总行': 'HQ',      # Headquarters
            '一级分行': 'FB',   # First-level Branch
            '二级分行': 'SB',   # Second-level Branch
            '支行': 'BR',      # Branch
            '社区网点': 'CB'    # Community Branch
        }
        
        # 如果没有提供支行类型或提供的类型不在映射表中，则随机选择一种
        if not branch_type or branch_type not in branch_type_codes:
            branch_type = random.choice(list(branch_type_codes.keys()))
        
        type_code = branch_type_codes.get(branch_type, 'BR')
        random_digits = ''.join([str(random.randint(0, 9)) for _ in range(8)])
        
        return f"B{type_code}{random_digits}"
    
    def generate_branch_name(self, bank_name='', city='', branch_type=''):
        """
        生成支行名称
        
        Args:
            bank_name: 银行名称
            city: 城市名称
            branch_type: 支行类型
            
        Returns:
            支行名称
        """
        # 如果未提供银行名称，随机选择一个
        if not bank_name:
            bank_name = random.choice(self.bank_names)
        
        # 如果未提供支行类型，随机选择一个
        if not branch_type or branch_type not in self.branch_types:
            branch_type = random.choice(self.branch_types)
        
        # 主要城市列表
        major_cities = ['北京', '上海', '广州', '深圳', '杭州', '南京', '成都', 
                        '武汉', '西安', '重庆', '天津', '苏州', '青岛', '长沙', '郑州']
        
        # 如果未提供城市，随机选择一个
        if not city:
            city = random.choice(major_cities)
        
        # 区域/街道名词库(中国城市常见区域名称)
        area_names = ['东方', '西城', '南湖', '北新', '中央', '高新', '经济开发', 
                    '工业园', '创业园', '金融', '科技', '商务', '文化', '河西', '湖滨']
        
        # 总行不需要城市和区域名称
        if branch_type == '总行':
            return f"{bank_name}总行"
        
        # 一级分行使用城市名称
        elif branch_type == '一级分行':
            return f"{bank_name}{city}分行"
        
        # 二级分行使用城市和区域名称
        elif branch_type == '二级分行':
            area = random.choice(area_names)
            return f"{bank_name}{city}{area}分行"
        
        # 支行使用城市、区域和序号
        elif branch_type == '支行':
            area = random.choice(area_names)
            # 分支行可能有序号，如"第一支行"、"第二支行"
            if random.random() < 0.5:  # 50%的概率使用序号
                ordinal = random.choice(['第一', '第二', '第三', '第四', '第五'])
                return f"{bank_name}{city}{area}{ordinal}支行"
            else:
                return f"{bank_name}{city}{area}支行"
        
        # 社区网点使用城市、区域和社区名
        else:  # branch_type == '社区网点'
            area = random.choice(area_names)
            # 社区名称词库
            community_names = ['康居', '明珠', '幸福', '和谐', '阳光', '绿园', 
                            '春晓', '望江', '丽景', '紫荆', '金沙', '银河']
            community = random.choice(community_names)
            return f"{bank_name}{city}{area}{community}社区支行"
    
    def generate_branch_address(self, province='', city=''):
        """
        生成支行地址
        
        Args:
            province: 省份，如未提供则随机选择
            city: 城市，如未提供则随机选择
            
        Returns:
            支行地址
        """
        # 省份-城市对应关系
        province_city_map = {
            '北京市': ['北京'],
            '上海市': ['上海'],
            '重庆市': ['重庆'],
            '天津市': ['天津'],
            '广东省': ['广州', '深圳', '珠海', '佛山', '东莞'],
            '江苏省': ['南京', '苏州', '无锡', '常州', '南通'],
            '浙江省': ['杭州', '宁波', '温州', '嘉兴', '湖州'],
            '山东省': ['济南', '青岛', '烟台', '威海', '临沂'],
            '四川省': ['成都', '绵阳', '德阳', '宜宾', '南充'],
            '湖北省': ['武汉', '宜昌', '襄阳', '荆州', '十堰'],
            '河南省': ['郑州', '洛阳', '开封', '新乡', '许昌'],
            '陕西省': ['西安', '咸阳', '宝鸡', '渭南', '延安']
        }
        
        # 如果未提供省份，随机选择一个
        if not province or province not in province_city_map:
            province = random.choice(list(province_city_map.keys()))
        
        # 如果未提供城市或城市不在选定省份的城市列表中，随机选择一个
        if not city or city not in province_city_map[province]:
            city = random.choice(province_city_map[province])
        
        # 区域名词库
        districts = ['东城区', '西城区', '南城区', '北城区', '中心区', 
                    '高新区', '经济开发区', '工业园区', '新区', '老城区']
        
        # 街道名词库
        streets = ['人民路', '解放大道', '和平路', '建设路', '中山路', 
                '长江路', '黄河路', '金融街', '科技大道', '商务大道']
        
        # 建筑物名词库
        buildings = ['国际大厦', '环球中心', '金融中心', '商务广场', '科技园', 
                    '创业大厦', '银座', '商城', '大厦', '广场']
        
        # 随机选择区域、街道和建筑物
        district = random.choice(districts)
        street = random.choice(streets)
        building = random.choice(buildings)
        
        # 随机生成门牌号
        building_number = random.randint(1, 999)
        
        # 随机生成楼层和房号
        floor = random.randint(1, 30)
        room = random.randint(1, 20)
        
        # 50%的概率生成包含楼层和房号的详细地址
        if random.random() < 0.5:
            address = f"{province}{city}{district}{street}{building_number}号{building}{floor}楼{room}室"
        else:
            address = f"{province}{city}{district}{street}{building_number}号{building}"
        
        return address
    
    def generate_business_hours(self, branch_type=''):
        """
        生成营业时间
        
        Args:
            branch_type: 支行类型
            
        Returns:
            营业时间字符串
        """
        # 根据支行类型设置不同的营业时间模式
        business_hours_patterns = {
            '总行': [
                '周一至周五 9:00-17:00',
                '周一至周五 8:30-17:30'
            ],
            '一级分行': [
                '周一至周五 9:00-17:00，周六 9:30-16:30',
                '周一至周五 9:00-17:30，周六 10:00-16:00'
            ],
            '二级分行': [
                '周一至周五 9:00-17:00，周六 9:30-16:30',
                '周一至周五 9:00-17:30，周六 9:00-16:00',
                '周一至周五 8:30-17:30，周六 9:00-16:00'
            ],
            '支行': [
                '周一至周五 9:00-17:00，周六日 9:30-16:30',
                '周一至周五 9:00-18:00，周六日 10:00-17:00',
                '周一至周日 9:00-17:30'
            ],
            '社区网点': [
                '周一至周日 9:00-18:00',
                '周一至周日 9:30-18:30',
                '周一至周五 9:00-19:00，周六日 10:00-18:00',
                '周一至周日 10:00-19:00'
            ]
        }
        
        # 如果未提供支行类型或类型不在模式列表中，使用支行的模式
        if not branch_type or branch_type not in business_hours_patterns:
            branch_type = '支行'
        
        # 随机选择该类型支行的一种营业时间模式
        business_hours = random.choice(business_hours_patterns[branch_type])
        
        return business_hours
    
    def generate_branch(self) -> Dict:
        """
        生成一个完整的支行档案
        
        Returns:
            支行档案字典
        """
        # 随机选择银行名称
        bank_name = random.choice(self.bank_names)
        
        # 随机选择支行类型
        branch_type = random.choice(self.branch_types)
        
        # 主要省份和城市
        provinces = ['北京市', '上海市', '广东省', '江苏省', '浙江省', '山东省', '四川省', '湖北省', '河南省', '陕西省']
        province = random.choice(provinces)
        
        # 根据省份确定城市
        province_city_map = {
            '北京市': ['北京'],
            '上海市': ['上海'],
            '广东省': ['广州', '深圳', '珠海', '佛山', '东莞'],
            '江苏省': ['南京', '苏州', '无锡', '常州', '南通'],
            '浙江省': ['杭州', '宁波', '温州', '嘉兴', '湖州'],
            '山东省': ['济南', '青岛', '烟台', '威海', '临沂'],
            '四川省': ['成都', '绵阳', '德阳', '宜宾', '南充'],
            '湖北省': ['武汉', '宜昌', '襄阳', '荆州', '十堰'],
            '河南省': ['郑州', '洛阳', '开封', '新乡', '许昌'],
            '陕西省': ['西安', '咸阳', '宝鸡', '渭南', '延安']
        }
        city = random.choice(province_city_map[province])
        
        # 生成支行ID
        base_id = self.generate_branch_id(branch_type)
        
        # 生成支行名称
        name = self.generate_branch_name(bank_name, city, branch_type)
        
        # 生成支行地址
        address = self.generate_branch_address(province, city)
        
        # 生成联系电话（固定电话格式）
        phone_area_codes = {
            '北京': '010', '上海': '021', '广州': '020', '深圳': '0755', '杭州': '0571',
            '南京': '025', '成都': '028', '武汉': '027', '西安': '029', '重庆': '023',
            '天津': '022', '苏州': '0512', '青岛': '0532', '长沙': '0731', '郑州': '0371'
        }
        area_code = phone_area_codes.get(city, '0' + str(random.randint(10, 99)))
        local_number = ''.join([str(random.randint(0, 9)) for _ in range(8)])
        phone = f"{area_code}-{local_number}"
        
        # 生成营业时间
        business_hours = self.generate_business_hours(branch_type)
        
        # 生成支行状态
        status = random.choice(self.branch_statuses)
        
        # 生成支行经理ID（假设已有经理数据）
        manager_id = f"M{''.join([str(random.randint(0, 9)) for _ in range(10)])}"
        
        # 生成支行建立日期
        # 假设支行类型等级越高，建立时间越早
        current_year = datetime.datetime.now().year
        type_age_map = {
            '总行': (30, 50),     # 总行成立30-50年
            '一级分行': (20, 40),  # 一级分行成立20-40年
            '二级分行': (10, 30),  # 二级分行成立10-30年
            '支行': (5, 20),      # 支行成立5-20年
            '社区网点': (1, 10)    # 社区网点成立1-10年
        }
        age_range = type_age_map.get(branch_type, (1, 20))
        years_ago = random.randint(age_range[0], age_range[1])
        establish_date = datetime.date(current_year - years_ago, 
                                    random.randint(1, 12), 
                                    random.randint(1, 28))
        
        # 创建支行档案字典
        branch_data = {
            'pt': self.get_partition_date(),
            'base_id': base_id,
            'name': name,
            'branch_type': branch_type,
            'address': address,
            'city': city,
            'province': province,
            'phone': phone,
            'business_hours': business_hours,
            'status': status,
            'manager_id': manager_id,
            'establish_date': establish_date.strftime('%Y-%m-%d'),
            'create_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'update_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return branch_data
    
    def generate(self, count: Optional[int] = None) -> List[Dict]:
        """
        生成支行档案数据
        
        Args:
            count: 生成的支行数量
            
        Returns:
            支行档案数据列表
        """
        # 如果未指定数量，使用默认值
        if count is None:
            count = 50  # 默认生成50个支行
        
        branches = []
        
        # 生成指定数量的支行
        for _ in range(count):
            branch = self.generate_branch()
            branches.append(branch)
        
        return branches


class AccountArchiveGenerator(BaseArchiveGenerator):
    """账户档案生成器，生成符合CDP通用档案范式的账户数据"""
    
    def __init__(self, fake_generator: faker.Faker, config_manager):
        """
        初始化账户档案生成器
        
        Args:
            fake_generator: Faker实例，用于生成随机数据
            config_manager: 配置管理器实例
        """
        super().__init__(fake_generator, config_manager)
        # 定义账户相关常量和配置
        self.account_types = ['活期账户', '定期账户', '贷款账户', '信用卡账户']
        self.account_statuses = ['正常', '冻结', '休眠', '注销']
        self.currencies = ['CNY', 'USD', 'EUR', 'JPY', 'GBP']
        
        # 从配置文件中加载账户相关配置
        self.account_config = config_manager.get_config().get('account', {})
    
    def generate_account_id(self, account_type=''):
        """
        生成符合规范的账户ID
        账户ID格式：A + 账户类型代码(2位) + 随机数字(16位)
        
        Args:
            account_type: 账户类型，如 '活期账户', '定期账户', '贷款账户', '信用卡账户'
            
        Returns:
            符合规范的账户ID字符串
        """
        account_type_codes = {
            '活期账户': 'CA',  # Current Account
            '定期账户': 'TD',  # Time Deposit
            '贷款账户': 'LA',  # Loan Account
            '信用卡账户': 'CC'  # Credit Card
        }
        
        # 如果没有提供账户类型或提供的类型不在映射表中，则随机选择一种
        if not account_type or account_type not in account_type_codes:
            account_type = random.choice(list(account_type_codes.keys()))
        
        type_code = account_type_codes.get(account_type, 'OT')
        
        # 生成16位随机数字，模拟银行卡号
        random_digits = ''.join([str(random.randint(0, 9)) for _ in range(16)])
        
        return f"A{type_code}{random_digits}"
    
    def generate_opening_date(self, customer_registration_date=None):
        """
        生成开户日期
        
        Args:
            customer_registration_date: 客户注册日期，开户日期不能早于客户注册日期
            
        Returns:
            开户日期，格式为'YYYY-MM-DD'
        """
        current_date = datetime.date.today()
        
        # 如果提供了客户注册日期，将其转换为datetime.date对象
        if customer_registration_date:
            try:
                if isinstance(customer_registration_date, str):
                    registration_date = datetime.datetime.strptime(customer_registration_date, '%Y-%m-%d').date()
                elif isinstance(customer_registration_date, datetime.date):
                    registration_date = customer_registration_date
                else:
                    # 如果无法转换，使用默认值
                    registration_date = current_date - datetime.timedelta(days=365 * 5)  # 默认5年前
            except ValueError:
                # 日期格式错误，使用默认值
                registration_date = current_date - datetime.timedelta(days=365 * 5)  # 默认5年前
        else:
            # 如果未提供客户注册日期，假设客户在1-10年前注册
            years_ago = random.randint(1, 10)
            registration_date = current_date - datetime.timedelta(days=365 * years_ago)
        
        # 计算开户日期：客户注册日期到当前日期之间的随机一天
        days_since_registration = (current_date - registration_date).days
        
        # 如果客户注册日期是今天或未来日期，则开户日期就是今天
        if days_since_registration <= 0:
            return current_date.strftime('%Y-%m-%d')
        
        # 随机选择客户注册日期到当前日期之间的一天
        days_after_registration = random.randint(0, days_since_registration)
        opening_date = registration_date + datetime.timedelta(days=days_after_registration)
        
        return opening_date.strftime('%Y-%m-%d')
    
    def generate_balance(self, account_type='', customer_type=''):
        """
        生成账户余额
        
        Args:
            account_type: 账户类型
            customer_type: 客户类型（个人/企业）
            
        Returns:
            账户余额
        """
        # 不同账户类型和客户类型的余额范围
        balance_ranges = {
            '活期账户': {
                'personal': (1000, 50000),  # 个人活期账户：1千-5万
                'corporate': (50000, 1000000)  # 企业活期账户：5万-100万
            },
            '定期账户': {
                'personal': (10000, 200000),  # 个人定期账户：1万-20万
                'corporate': (200000, 2000000)  # 企业定期账户：20万-200万
            },
            '贷款账户': {
                'personal': (10000, 500000),  # 个人贷款账户：1万-50万
                'corporate': (500000, 10000000)  # 企业贷款账户：50万-1000万
            },
            '信用卡账户': {
                'personal': (0, 50000),  # 个人信用卡账户：0-5万
                'corporate': (0, 200000)  # 企业信用卡账户：0-20万
            }
        }
        
        # 如果未提供账户类型或类型不存在，使用活期账户的范围
        if not account_type or account_type not in balance_ranges:
            account_type = '活期账户'
        
        # 如果未提供客户类型或类型不存在，使用个人客户的范围
        if not customer_type or customer_type.lower() not in ['personal', 'corporate']:
            customer_type = 'personal'
        
        # 获取该账户类型和客户类型的余额范围
        account_range = balance_ranges[account_type][customer_type.lower()]
        
        # 生成余额
        # 使用指数分布，使得大多数账户余额偏低，少数账户余额较高
        mean_value = (account_range[0] + account_range[1]) / 4  # 均值设为范围的1/4，使分布偏向低值
        balance = random.expovariate(1.0 / mean_value)
        
        # 确保余额在指定范围内
        balance = max(account_range[0], min(account_range[1], balance))
        
        # 贷款账户的余额是负数
        if account_type == '贷款账户':
            balance = -balance
        
        # 四舍五入到分
        balance = round(balance, 2)
        
        return balance
    
    def generate_account_for_customer(self, customer_id: str, customer_type: str, 
                               registration_date: str, is_vip: bool,
                               deposit_types: List[Dict],
                               branches: List[Dict]) -> Dict:
        """
        为指定客户生成账户
        
        Args:
            customer_id: 客户ID
            customer_type: 客户类型
            registration_date: 客户注册日期
            is_vip: 是否VIP客户
            deposit_types: 存款类型列表
            branches: 支行列表
            
        Returns:
            账户档案字典
        """
        # 选择账户类型
        account_type = random.choice(self.account_types)
        
        # 生成账户ID
        base_id = self.generate_account_id(account_type)
        
        # 生成开户日期
        opening_date = self.generate_opening_date(registration_date)
        
        # 生成账户余额
        balance = self.generate_balance(account_type, customer_type)
        
        # 选择货币类型（根据概率分布）
        currency_distribution = {
            'CNY': 0.88,  # 人民币
            'USD': 0.08,  # 美元
            'EUR': 0.02,  # 欧元
            'JPY': 0.01,  # 日元
            'GBP': 0.01   # 英镑
        }
        currency = random.choices(
            list(currency_distribution.keys()),
            weights=list(currency_distribution.values()),
            k=1
        )[0]
        
        # 生成账户状态（根据概率分布）
        status_distribution = {
            '正常': 0.75,
            '休眠': 0.18,
            '冻结': 0.04,
            '注销': 0.03
        }
        status = random.choices(
            list(status_distribution.keys()),
            weights=list(status_distribution.values()),
            k=1
        )[0]
        
        # 选择开户支行（随机选择一个）
        if branches and len(branches) > 0:
            branch = random.choice(branches)
            branch_id = branch.get('base_id', '')
        else:
            branch_id = ''
        
        # 选择存款类型（仅对定期账户和活期账户）
        deposit_type_id = ''
        if account_type in ['活期账户', '定期账户'] and deposit_types and len(deposit_types) > 0:
            # 根据账户类型筛选合适的存款类型
            suitable_deposit_types = []
            for dt in deposit_types:
                dt_name = dt.get('name', '')
                if account_type == '活期账户' and '活期' in dt_name:
                    suitable_deposit_types.append(dt)
                elif account_type == '定期账户' and '活期' not in dt_name:
                    suitable_deposit_types.append(dt)
            
            # 如果有合适的存款类型，随机选择一个
            if suitable_deposit_types:
                deposit_type = random.choice(suitable_deposit_types)
                deposit_type_id = deposit_type.get('base_id', '')
                
                # 如果是定期账户，还需设置期限和到期日期
                if account_type == '定期账户':
                    term = random.choice([3, 6, 12, 24, 36, 60])  # 月数
                    
                    # 计算到期日期
                    try:
                        opening_date_obj = datetime.datetime.strptime(opening_date, '%Y-%m-%d').date()
                        # 简单处理，假设每月30天
                        maturity_date = opening_date_obj + datetime.timedelta(days=term * 30)
                        maturity_date_str = maturity_date.strftime('%Y-%m-%d')
                    except:
                        # 如果日期转换出错，设置为一年后
                        maturity_date_str = ''
                        term = 0
                else:
                    term = 0
                    maturity_date_str = ''
        else:
            term = 0
            maturity_date_str = ''
        
        # 生成利率（根据账户类型和存款类型）
        if account_type == '活期账户':
            interest_rate = 0.0025  # 活期利率，通常为0.25%
        elif account_type == '定期账户':
            # 根据期限确定利率
            interest_rates = {
                3: 0.0150,   # 3个月定期利率
                6: 0.0175,   # 6个月定期利率
                12: 0.0225,  # 1年定期利率
                24: 0.0275,  # 2年定期利率
                36: 0.0325,  # 3年定期利率
                60: 0.0350   # 5年定期利率
            }
            interest_rate = interest_rates.get(term, 0.0225)
        elif account_type == '贷款账户':
            # 贷款利率通常较高
            interest_rate = random.uniform(0.04, 0.08)  # 4%-8%
        else:  # 信用卡账户
            interest_rate = random.uniform(0.06, 0.10)  # 6%-10%
        
        # 创建账户档案字典
        account_data = {
            'pt': self.get_partition_date(),
            'base_id': base_id,
            'customer_id': customer_id,
            'account_type': account_type,
            'opening_date': opening_date,
            'balance': float(balance),
            'currency': currency,
            'status': status,
            'branch_id': branch_id,
            'deposit_type_id': deposit_type_id,
            'interest_rate': float(interest_rate),
            'term': term,
            'maturity_date': maturity_date_str,
            'create_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'update_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return account_data
    
    def generate(self, customers: List[Dict], deposit_types: List[Dict], 
                branches: List[Dict]) -> List[Dict]:
        """
        生成账户档案数据
        
        Args:
            customers: 客户数据列表
            deposit_types: 存款类型数据列表
            branches: 支行数据列表
            
        Returns:
            账户档案数据列表
        """
        accounts = []
        
        # 为每个客户生成账户
        for customer in customers:
            # 确定为该客户生成的账户数量
            account_count = self._determine_account_count(customer)
            
            # 为客户生成账户
            for _ in range(account_count):
                account = self.generate_account_for_customer(
                    customer_id=customer['base_id'],
                    customer_type=customer.get('customer_type', 'personal'),
                    registration_date=customer.get('registration_date'),
                    is_vip=customer.get('is_vip', False),
                    deposit_types=deposit_types,
                    branches=branches
                )
                accounts.append(account)
        
        return accounts
    
    def _determine_account_count(self, customer: Dict) -> int:
        """
        确定为客户生成的账户数量
        
        Args:
            customer: 客户数据
            
        Returns:
            账户数量
        """
        # 获取客户类型和VIP状态
        customer_type = customer.get('customer_type', 'personal').lower()
        is_vip = customer.get('is_vip', False)
        
        # 从配置中获取账户数量分布参数
        account_config = self.account_config.get('count_per_customer', {})
        
        # 个人客户账户数量分布
        personal_config = account_config.get('personal', {})
        personal_mean = personal_config.get('mean', 2.0)
        personal_std_dev = personal_config.get('std_dev', 0.5)
        
        # 企业客户账户数量分布
        corporate_config = account_config.get('corporate', {})
        corporate_mean = corporate_config.get('mean', 3.2)
        corporate_std_dev = corporate_config.get('std_dev', 0.8)
        
        # VIP客户账户数量增加系数
        vip_multiplier = account_config.get('vip_multiplier', 1.4)
        
        # 根据客户类型选择参数
        if customer_type == 'corporate':
            base_count = max(1, int(random.normalvariate(corporate_mean, corporate_std_dev)))
        else:  # 默认为个人客户
            base_count = max(1, int(random.normalvariate(personal_mean, personal_std_dev)))
        
        # VIP客户账户数量增加
        if is_vip:
            final_count = max(1, int(base_count * vip_multiplier))
        else:
            final_count = base_count
        
        # 确保账户数量在合理范围内
        final_count = min(10, max(1, final_count))  # 最少1个，最多10个账户
        
        return final_count  