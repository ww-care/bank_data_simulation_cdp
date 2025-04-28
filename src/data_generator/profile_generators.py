#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
客户档案范式数据生成器

负责生成符合CDP客户档案范式的数据，包括客户档案、银行经理档案等。
"""

import uuid
import random
import datetime
import faker
import numpy as np
import re
from typing import Dict, List, Tuple, Optional, Any, Union

from src.time_manager.time_manager import get_time_manager
from src.logger import get_logger
from src.data_generator.base_generators import BaseProfileGenerator


class CustomerProfileGenerator(BaseProfileGenerator):
    """客户档案生成器，生成符合CDP客户档案范式的数据"""
    
    def __init__(self, fake_generator: faker.Faker, config_manager):
        """
        初始化客户档案生成器
        
        Args:
            fake_generator: Faker实例，用于生成随机数据
            config_manager: 配置管理器实例
        """
        super().__init__(fake_generator, config_manager)
        
        # 获取客户相关配置
        self.customer_config = self.config_manager.get_entity_config('customer')
        
        # 获取客户档案表配置
        cdp_model_config = self.config_manager.get_entity_config('cdp_model')
        customer_profile_tables = cdp_model_config.get('customer_profile', {}).get('tables', [])
        
        # 查找客户表配置
        self.customer_table_config = next(
            (table for table in customer_profile_tables if table.get('entity') == 'customer'), 
            {'name': 'cdp_customer_profile', 'id_prefix': 'C'}
        )
        
        # 证件类型
        self.id_types = ['身份证', '护照', '军官证', '港澳通行证', '台胞证']
        self.id_types_weights = [0.90, 0.04, 0.01, 0.03, 0.02]
        
        # 初始化日志
        self.logger = get_logger('CustomerProfileGenerator')
        
        # 信用评分区间映射
        self.credit_score_ranges = {}
        if 'credit_score' in self.customer_config:
            score_dist = self.customer_config['credit_score'].get('distribution', {})
            for level, info in score_dist.items():
                if 'range' in info:
                    self.credit_score_ranges[level] = info['range']
    
    def generate(self, count: Optional[int] = None) -> List[Dict]:
        """
        生成客户档案数据
        
        Args:
            count: 生成的客户数量，如果为None则使用配置中的值
            
        Returns:
            客户档案数据列表
        """
        # 确定生成数量
        if count is None:
            count = self.customer_config.get('total_count', 1000)
        
        self.logger.info(f"开始生成 {count} 条客户档案数据")
        
        # 基于配置获取客户类型分布
        type_distribution = self.customer_config.get('type_distribution', {'personal': 0.8, 'corporate': 0.2})
        
        # 计算各类型客户数量
        type_counts = self.distribute_by_ratio(type_distribution, count)
        
        self.logger.info(f"客户类型分布: {type_counts}")
        
        customers = []
        
        # 生成个人客户
        if 'personal' in type_counts and type_counts['personal'] > 0:
            personal_customers = self._generate_personal_customers(type_counts['personal'])
            customers.extend(personal_customers)
        
        # 生成企业客户（暂不实现，留空）
        if 'corporate' in type_counts and type_counts['corporate'] > 0:
            corporate_customers = []  # 暂时置空，后续实现
            # corporate_customers = self._generate_corporate_customers(type_counts['corporate'])
            customers.extend(corporate_customers)
        
        # 清洗并验证数据
        customers = self.clean_profiles(customers)
        
        self.logger.info(f"成功生成 {len(customers)} 条客户档案数据")
        
        return customers
    
    def _generate_personal_customers(self, count: int) -> List[Dict]:
        """
        生成个人客户数据
        
        Args:
            count: 生成的个人客户数量
            
        Returns:
            个人客户数据列表
        """
        customers = []
        
        # 获取个人客户配置
        personal_config = self.customer_config.get('personal', {})
        
        # 获取VIP比例
        vip_ratio = self.customer_config.get('vip_ratio', {}).get('personal', 0.15)
        
        # 分配VIP客户数量
        vip_count = int(count * vip_ratio)
        
        # 获取性别分布
        gender_distribution = personal_config.get('gender_distribution', {'male': 0.52, 'female': 0.48})
        
        # 获取年龄分布
        age_distribution = personal_config.get('age_distribution', {'18-25': 0.15, '26-40': 0.40, '41-60': 0.35, '60+': 0.10})
        
        # 获取职业分布
        occupation_distribution = personal_config.get('occupation_distribution', {
            'professional': 0.25,
            'technical': 0.15,
            'service': 0.20,
            'sales': 0.10, 
            'administrative': 0.15,
            'manual_labor': 0.10,
            'retired': 0.05
        })
        
        # 城市分布列表（基于中国主要城市人口比例）
        cities = [
            ('北京市', '北京', '中国'),
            ('上海市', '上海', '中国'),
            ('广州市', '广东', '中国'),
            ('深圳市', '广东', '中国'),
            ('重庆市', '重庆', '中国'),
            ('成都市', '四川', '中国'),
            ('杭州市', '浙江', '中国'),
            ('武汉市', '湖北', '中国'),
            ('西安市', '陕西', '中国'),
            ('南京市', '江苏', '中国'),
            ('天津市', '天津', '中国'),
            ('苏州市', '江苏', '中国'),
            ('郑州市', '河南', '中国'),
            ('长沙市', '湖南', '中国'),
            ('东莞市', '广东', '中国'),
            ('沈阳市', '辽宁', '中国'),
            ('青岛市', '山东', '中国'),
            ('合肥市', '安徽', '中国'),
            ('佛山市', '广东', '中国'),
            ('宁波市', '浙江', '中国')
        ]
        
        # 城市权重（基于人口规模粗略设置）
        city_weights = [0.1, 0.1, 0.08, 0.08, 0.07, 0.06, 0.06, 0.05, 0.05, 0.05, 
                       0.04, 0.04, 0.04, 0.04, 0.03, 0.03, 0.03, 0.03, 0.02, 0.02]
        
        # 获取理财产品类型分布（用于首次产品购买类型）
        first_product_types = [
            '股票型基金', '货币型基金', '债券型基金', '混合型基金', '指数基金', '其他'
        ]
        first_product_weights = [0.20, 0.35, 0.25, 0.10, 0.05, 0.05]
        
        # 财富客户阶段分布
        wealth_phases = ['注册', '首投', '老客', '召回', '流失']
        wealth_phases_weights = [0.15, 0.25, 0.40, 0.10, 0.10]
        
        # 当前日期，用于计算出生日期和其他时间相关字段
        current_date = datetime.date.today()
        
        # 历史数据起始日期
        historical_start_date_str = self.config_manager.get_system_config().get('system', {}).get('historical_start_date')
        historical_start_date = datetime.datetime.strptime(historical_start_date_str, '%Y-%m-%d').date() if historical_start_date_str else (current_date - datetime.timedelta(days=365))
        
        # 历史数据结束日期
        historical_end_date_str = self.config_manager.get_system_config().get('system', {}).get('historical_end_date')
        historical_end_date = datetime.datetime.strptime(historical_end_date_str, '%Y-%m-%d').date() if historical_end_date_str else (current_date - datetime.timedelta(days=1))
        
        for i in range(count):
            # 基础信息字段生成
            customer = {}
            
            # 添加分区字段
            customer['pt'] = self.get_partition_date()
            
            # 生成客户ID
            id_prefix = self.customer_table_config.get('id_prefix', 'C')
            customer['base_id'] = self.generate_id(id_prefix)
            
            # 生成会员ID
            customer['member_id'] = f"MEM{uuid.uuid4().hex[:9].upper()}"
            
            # 生成客户名称（中文名）
            customer['name'] = self.faker.name()
            
            # 生成客户性别
            gender_code = self.random_choice(list(gender_distribution.keys()), 
                                          list(gender_distribution.values()))
            customer['gender'] = 'M' if gender_code == 'male' else 'F'
            
            # 生成证件类型和证件号码
            id_type = self.random_choice(self.id_types, self.id_types_weights)
            customer['id_type'] = id_type
            
            if id_type == '身份证':
                # 生成18位身份证号
                customer['id_number'] = self._generate_id_card()
                
                # 从身份证号提取出生日期
                birth_date_str = customer['id_number'][6:14]
                birth_date = datetime.datetime.strptime(birth_date_str, '%Y%m%d').date()
                customer['birth_date'] = birth_date
            else:
                # 随机选择年龄段
                age_range = self.random_choice(list(age_distribution.keys()), 
                                            list(age_distribution.values()))
                
                # 计算出生日期范围
                if age_range == '18-25':
                    min_birth_year = current_date.year - 25
                    max_birth_year = current_date.year - 18
                elif age_range == '26-40':
                    min_birth_year = current_date.year - 40
                    max_birth_year = current_date.year - 26
                elif age_range == '41-60':
                    min_birth_year = current_date.year - 60
                    max_birth_year = current_date.year - 41
                else:  # 60+
                    min_birth_year = current_date.year - 90
                    max_birth_year = current_date.year - 60
                
                min_birth_date = datetime.date(min_birth_year, 1, 1)
                max_birth_date = datetime.date(max_birth_year, 12, 31)
                
                # 随机生成出生日期
                birth_date = self.random_date(min_birth_date, max_birth_date)
                customer['birth_date'] = birth_date
                
                # 生成其他类型证件号码
                if id_type == '护照':
                    customer['id_number'] = f"P{self.faker.bothify('?########')}"
                elif id_type == '军官证':
                    customer['id_number'] = f"J{self.faker.bothify('########?')}"
                elif id_type == '港澳通行证':
                    customer['id_number'] = f"H{self.faker.numerify('##########')}"
                elif id_type == '台胞证':
                    customer['id_number'] = f"T{self.faker.numerify('##########')}"
            
            # 生成注册日期（必要字段，在历史数据范围内）
            customer['registration_date'] = self.random_date(historical_start_date, historical_end_date)
            
            # 设置客户类型
            customer['customer_type'] = '个人'
            
            # 设置VIP标识
            customer['is_vip'] = i < vip_count
            
            # 生成信用评分
            customer['credit_score'] = self._generate_credit_score(is_vip=customer['is_vip'])
            
            # 生成风险偏好等级R1-R5
            customer['risk_level'] = self._get_risk_level_from_credit_score(customer['credit_score'])
            
            # ===== 联系信息生成 =====
            
            # 生成手机号码
            customer['phone'] = self._generate_phone_number()
            
            # 生成电子邮箱
            customer['email'] = self._generate_email(customer['name'])
            
            # 生成地理位置信息
            city_data = self.random_choice(cities, city_weights)
            customer['city'] = city_data[0]
            customer['province'] = city_data[1]
            customer['country'] = city_data[2]
            
            # 生成详细地址
            customer['address'] = self._generate_address(customer['city'])
            
            # 生成职业
            customer['occupation'] = self.random_choice(
                list(occupation_distribution.keys()),
                list(occupation_distribution.values())
            )
            
            # 生成年收入（基于职业和年龄）
            customer['annual_income'] = self._generate_annual_income(
                customer['occupation'],
                customer['birth_date'],
                customer['is_vip']
            )
            
            # 设置工资分类等级(1-8级)
            customer['salary_category'] = self._get_salary_category(customer['annual_income'])
            
            # ===== 金融属性生成 =====
            
            # 会员相关属性
            # 生成会员等级(1-5级)
            customer['member_level'] = self._generate_member_level(customer['is_vip'], customer['credit_score'])
            
            # 生成会员上月等级(确保不高于当前等级)
            customer['member_last_month_level'] = self._generate_last_month_member_level(customer['member_level'])
            
            # 确定会员等级是否提升
            customer['is_member_level_up'] = self._is_member_level_up(customer['member_level'], customer['member_last_month_level'])
            
            # 财富相关属性
            # 生成客户月均消费
            customer['monthly_average_amount'] = self._generate_monthly_average_amount(customer['annual_income'])
            
            # 随机生成是否存在单笔高额消费
            customer['is_high_consumption'] = self._generate_is_high_consumption(customer)
            
            # 生成客户流失标志
            customer['customer_churn_tag'] = self._generate_customer_churn_tag(customer)
            
            # 生成本周新增流失客户标志
            customer['is_churn_this_week'] = self._generate_is_churn_this_week(customer['customer_churn_tag'])
            
            # 生成清仓日期
            has_clearance_date = random.random() < 0.6  # 60%的客户有清仓记录
            if has_clearance_date:
                customer['clearance_date'] = self._generate_clearance_date(historical_start_date, historical_end_date)
            
            # 生成财富产品清仓日期
            has_wealth_clearance = random.random() < 0.5  # 50%的客户有理财产品清仓记录
            if has_wealth_clearance:
                customer['sell_wealth_date'] = self._generate_clearance_date(historical_start_date, historical_end_date)
            
            # 存款产品清仓日期
            has_savings_clearance = random.random() < 0.4  # 40%的客户有存款产品清仓记录
            if has_savings_clearance:
                customer['savings_sell_all_date'] = self._generate_clearance_date(historical_start_date, historical_end_date)
            
            # 最近一次清仓日期
            customer['sell_all_date'] = self._get_most_recent_date([customer.get('sell_wealth_date'), customer.get('savings_sell_all_date')])
            
            # 资金未发生支用天数
            last_transaction_days_ago = random.randint(0, 180)
            if last_transaction_days_ago > 30:  # 如果超过30天没有交易，则记录这个值
                customer['no_use_days'] = last_transaction_days_ago
            
            # 曾持有财富产品标识
            customer['have_wealth'] = random.random() < 0.7  # 70%的客户曾持有财富产品
            
            # 首次产品购买类型
            if customer['have_wealth']:
                customer['first_purchase_type'] = self.random_choice(first_product_types, first_product_weights)
            
            # 财富客户阶段
            customer['wealth_customer_phase'] = self.random_choice(wealth_phases, wealth_phases_weights)
            
            # 授信相关属性
            # 授信账户ID
            if random.random() < 0.8:  # 80%的客户有授信账户
                customer['credit_account_id'] = f"CA{uuid.uuid4().hex[:10].upper()}"
                
                # 授信金额（基于信用评分和收入）
                customer['credit_amount'] = self._generate_credit_amount(customer)
                
                # 授信是否使用中
                customer['is_credit_in_use'] = random.random() < 0.6  # 60%的授信账户在使用中
                
                # 如果授信正在使用，生成剩余额度和使用率
                if customer['is_credit_in_use']:
                    utilization_rate = random.uniform(0.1, 0.9)  # 10%-90%的使用率
                    customer['limit_utilization_rate'] = round(utilization_rate * 100, 2)  # 转为百分比
                    customer['remaining_limit'] = round(customer['credit_amount'] * (1 - utilization_rate), 2)
                else:
                    customer['limit_utilization_rate'] = 0
                    customer['remaining_limit'] = customer['credit_amount']
            
            # 将用户添加到列表
            customers.append(customer)
        
        return customers
    
    def _generate_id_card(self) -> str:
        """
        生成符合规则的18位身份证号
        
        Returns:
            身份证号
        """
        # 随机选择一个省份代码
        province_codes = [
            '11', '12', '13', '14', '15', '21', '22', '23', '31', '32', '33', '34', 
            '35', '36', '37', '41', '42', '43', '44', '45', '46', '50', '51', '52', 
            '53', '54', '61', '62', '63', '64', '65', '71', '81', '82'
        ]
        province_code = random.choice(province_codes)
        
        # 随机生成地区代码（4位，前2位是省份代码）
        area_code = province_code + self.faker.numerify('##')
        
        # 随机生成出生日期（8位，格式为YYYYMMDD）
        # 从1970年到20年前的日期
        current_date = datetime.date.today()
        min_birth_year = 1970
        max_birth_year = current_date.year - 18
        
        birth_date = self.random_date(
            datetime.date(min_birth_year, 1, 1),
            datetime.date(max_birth_year, 12, 31)
        )
        birth_date_str = birth_date.strftime('%Y%m%d')
        
        # 随机生成顺序码（3位）
        sequence_code = self.faker.numerify('###')
        
        # 前17位
        id_number_17 = f"{area_code}{birth_date_str}{sequence_code}"
        
        # 计算校验码
        factors = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        checksum = sum(int(id_number_17[i]) * factors[i] for i in range(17))
        remainder = checksum % 11
        check_codes = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']
        check_code = check_codes[remainder]
        
        # 完整18位身份证号
        id_number = f"{id_number_17}{check_code}"
        
        return id_number
    
    def _generate_credit_score(self, is_vip: bool = False) -> int:
        """
        生成信用评分，VIP客户有分数加成
        
        Args:
            is_vip: 是否VIP客户
            
        Returns:
            信用评分
        """
        credit_config = self.customer_config.get('credit_score', {})
        
        # 获取评分范围
        min_score = credit_config.get('range', {}).get('min', 350)
        max_score = credit_config.get('range', {}).get('max', 850)
        
        # 获取分布配置
        distribution = credit_config.get('distribution', {})
        
        # 根据比例随机选择信用级别
        credit_levels = list(distribution.keys())
        credit_ratios = [info.get('ratio', 0) for info in distribution.values()]
        
        # 归一化比例
        total_ratio = sum(credit_ratios)
        if total_ratio > 0:
            credit_ratios = [r / total_ratio for r in credit_ratios]
        
        # 随机选择信用级别
        credit_level = self.random_choice(credit_levels, credit_ratios)
        
        # 获取该级别的分数范围
        level_range = distribution.get(credit_level, {}).get('range', [min_score, max_score])
        
        # 在范围内随机生成分数
        score = random.randint(level_range[0], level_range[1])
        
        # VIP客户加分
        vip_bonus = credit_config.get('vip_bonus', 0)
        if is_vip:
            score = min(score + vip_bonus, max_score)
        
        return score
    
    def _get_risk_level_from_credit_score(self, credit_score: int) -> str:
        """
        根据信用评分确定风险等级
        
        Args:
            credit_score: 信用评分
            
        Returns:
            风险等级 (R1-R5)
        """
        # 风险等级对应关系：R1-最低风险，R5-最高风险
        if credit_score >= 700:
            return 'R1'
        elif credit_score >= 640:
            return 'R2'
        elif credit_score >= 580:
            return 'R3'
        elif credit_score >= 520:
            return 'R4'
        else:
            return 'R5'
    
    def _generate_phone_number(self) -> str:
        """
        生成中国手机号码
        
        Returns:
            手机号码
        """
        # 中国手机号前三位运营商号段
        prefixes = [
            # 移动
            '134', '135', '136', '137', '138', '139', '150', '151', '152', '157', '158', '159',
            '182', '183', '184', '187', '188', '147', '178', '198',
            # 联通
            '130', '131', '132', '155', '156', '185', '186', '145', '176', '166',
            # 电信
            '133', '153', '180', '181', '189', '177', '173', '199',
            # 虚拟运营商
            '170', '171'
        ]
        
        # 随机选择前缀
        prefix = random.choice(prefixes)
        
        # 生成后8位数字
        suffix = self.faker.numerify('########')
        
        return f"{prefix}{suffix}"
    
    def _generate_email(self, name: str) -> str:
        """
        基于姓名生成电子邮箱
        
        Args:
            name: 客户姓名
            
        Returns:
            电子邮箱地址
        """
        # 常见邮箱域名
        domains = [
            '163.com', 'qq.com', '126.com', 'gmail.com', 'hotmail.com', 'sina.com',
            'sohu.com', 'yahoo.com', '139.com', 'outlook.com', 'foxmail.com', 'aliyun.com'
        ]
        
        # 域名权重
        domain_weights = [0.25, 0.25, 0.12, 0.08, 0.05, 0.06, 0.04, 0.03, 0.04, 0.03, 0.03, 0.02]
        
        # 随机选择域名
        domain = self.random_choice(domains, domain_weights)
        
        # 生成用户名
        # 方法1: 直接使用姓名拼音（简化处理，实际需要引入拼音转换库）
        username_type = random.randint(1, 5)
        if username_type == 1:
            # 直接使用faker生成用户名
            username = self.faker.user_name()
        elif username_type == 2:
            # 使用随机字母数字组合
            username = self.faker.bothify('?????##')
        elif username_type == 3:
            # 简单英文名+数字
            username = f"{self.faker.first_name().lower()}{random.randint(100, 9999)}"
        elif username_type == 4:
            # 年份组合
            birth_year = random.randint(1970, 2000)
            username = f"{self.faker.word()}{birth_year}"
        else:
            # 随机单词组合
            username = f"{self.faker.word()}_{self.faker.word()}"
        
        return f"{username}@{domain}"
    
    def _generate_address(self, city: str) -> str:
        """
        生成详细地址
        
        Args:
            city: 城市名称
            
        Returns:
            详细地址
        """
        # 生成随机小区名
        communities = [
            '阳光花园', '翰林苑', '金色家园', '绿景花园', '丽景华庭', '紫荆花园',
            '龙湖花园', '万科城市花园', '保利花园', '碧桂园', '恒大华府', '金地国际城',
            '星河湾', '中海康城', '珠江新城', '雅居乐花园', '招商小区', '华润万家',
            '富力城', '佳兆业金域', '世纪城', '锦绣花园', '御景华庭', '香樟园'
        ]
        community = random.choice(communities)
        
        # 随机楼栋号
        building = f"{random.randint(1, 20)}栋"
        
        # 随机单元号
        unit = f"{random.randint(1, 6)}单元"
        
        # 随机房号
        room = f"{random.randint(101, 2599)}"
        
        # 随机道路
        roads = [
            '中山路', '解放路', '人民路', '建设路', '和平路', '兴华路', '长江路',
            '黄河路', '南京路', '北京路', '上海路', '广州路', '深圳路', '天府大道',
            '望江路', '科华路', '东风路', '西二环', '金融街', '体育路', '教育路'
        ]
        road = random.choice(roads)
        
        # 随机号码
        number = random.randint(1, 999)
        
        # 随机模式
        if random.random() < 0.6:  # 60%概率是小区+楼栋+单元+房号
            return f"{city}{road}{number}号，{community}{building}{unit}{room}"
        else:  # 40%概率是路+号
            return f"{city}{road}{number}号"
    
    def _generate_annual_income(self, occupation: str, birth_date: datetime.date, is_vip: bool) -> float:
        """
        生成年收入
        
        Args:
            occupation: 职业
            birth_date: 出生日期，用于计算年龄
            is_vip: 是否VIP客户
            
        Returns:
            年收入
        """
        # 获取收入配置
        income_config = self.customer_config.get('personal', {}).get('annual_income', {})
        
        # 从配置中获取收入范围
        min_income = income_config.get('min', 20000)
        max_income = income_config.get('max', 300000)
        mean_income = income_config.get('mean', 60000)
        std_dev = income_config.get('std_dev', 30000)
        
        # 根据职业调整收入范围
        occupation_multipliers = {
            'professional': 1.5,      # 专业人士
            'technical': 1.3,         # 技术人员
            'service': 0.8,           # 服务业
            'sales': 1.2,             # 销售
            'administrative': 1.0,     # 行政
            'manual_labor': 0.7,       # 体力劳动
            'retired': 0.6            # 退休人员
        }
        
        multiplier = occupation_multipliers.get(occupation, 1.0)
        
        # 根据年龄调整收入
        age = (datetime.date.today() - birth_date).days // 365
        age_factor = 1.0
        
        if age < 25:
            age_factor = 0.6
        elif age < 35:
            age_factor = 0.9
        elif age < 45:
            age_factor = 1.1
        elif age < 55:
            age_factor = 1.2
        elif age < 65:
            age_factor = 1.0
        else:
            age_factor = 0.7
        
        # VIP客户收入倍增
        vip_factor = 1.8 if is_vip else 1.0
        
        # 计算调整后的收入参数
        adjusted_mean = mean_income * multiplier * age_factor * vip_factor
        adjusted_std_dev = std_dev * 0.5 * multiplier  # 降低标准差，使分布更集中
        
        # 生成随机收入
        income = self.normal_distribution_value(
            adjusted_mean, adjusted_std_dev, min_income, max_income
        )
        
        # 四舍五入到整数
        return round(income, 2)
    
    def _get_salary_category(self, annual_income: float) -> str:
        """
        根据年收入确定工资分类等级
        
        Args:
            annual_income: 年收入
            
        Returns:
            工资分类等级(1-8级)
        """
        if annual_income < 30000:
            return '1级'
        elif annual_income < 60000:
            return '2级'
        elif annual_income < 100000:
            return '3级'
        elif annual_income < 150000:
            return '4级'
        elif annual_income < 200000:
            return '5级'
        elif annual_income < 300000:
            return '6级'
        elif annual_income < 500000:
            return '7级'
        else:
            return '8级'
    
    def _generate_member_level(self, is_vip: bool, credit_score: int) -> str:
        """
        生成会员等级(1-5级)
        
        Args:
            is_vip: 是否VIP客户
            credit_score: 信用评分
            
        Returns:
            会员等级
        """
        if is_vip:
            # VIP客户等级分布：4-5级占比更高
            level_weights = [0.0, 0.0, 0.1, 0.3, 0.6]  # 1-5级的权重
        else:
            # 非VIP客户以信用分决定会员等级
            if credit_score >= 700:  # 优秀
                level_weights = [0.0, 0.1, 0.2, 0.5, 0.2]
            elif credit_score >= 640:  # 良好
                level_weights = [0.0, 0.2, 0.5, 0.3, 0.0]
            elif credit_score >= 580:  # 一般
                level_weights = [0.1, 0.6, 0.3, 0.0, 0.0]
            else:  # 较差
                level_weights = [0.7, 0.3, 0.0, 0.0, 0.0]
        
        # 随机选择会员等级
        level = self.random_choice([1, 2, 3, 4, 5], level_weights)
        return f'{level}级'
    
    def _generate_last_month_member_level(self, current_level: str) -> str:
        """
        生成上月会员等级(不高于当前等级)
        
        Args:
            current_level: 当前会员等级
            
        Returns:
            上月会员等级
        """
        # 解析当前等级
        current_level_value = int(current_level.replace('级', ''))
        
        # 生成上月等级（可能降级）
        if current_level_value == 1:
            # 已经是最低级别，无法再降
            return current_level
        
        # 70%概率保持不变，30%概率降一级
        if random.random() < 0.7:
            return current_level
        else:
            return f'{current_level_value - 1}级'
    
    def _is_member_level_up(self, current_level: str, last_month_level: str) -> bool:
        """
        判断会员等级是否提升
        
        Args:
            current_level: 当前会员等级
            last_month_level: 上月会员等级
            
        Returns:
            是否提升
        """
        current_level_value = int(current_level.replace('级', ''))
        last_month_level_value = int(last_month_level.replace('级', ''))
        
        return current_level_value > last_month_level_value
    
    def _generate_monthly_average_amount(self, annual_income: float) -> float:
        """
        生成客户月均消费
        
        Args:
            annual_income: 年收入
            
        Returns:
            月均消费
        """
        # 月均消费一般为月收入的30%-70%
        monthly_income = annual_income / 12
        consumption_ratio = random.uniform(0.3, 0.7)
        
        return round(monthly_income * consumption_ratio, 2)
    
    def _generate_is_high_consumption(self, customer: Dict) -> bool:
        """
        生成是否存在单笔高额消费标识
        
        Args:
            customer: 客户数据
            
        Returns:
            是否存在单笔高额消费
        """
        # 高收入和高信用评分的客户更可能有高额消费
        probability = 0.1  # 基础概率
        
        # 提高VIP客户概率
        if customer.get('is_vip'):
            probability += 0.2
        
        # 根据收入调整概率
        annual_income = customer.get('annual_income', 0)
        if annual_income > 200000:
            probability += 0.3
        elif annual_income > 100000:
            probability += 0.2
        elif annual_income > 50000:
            probability += 0.1
        
        # 根据信用评分调整概率
        credit_score = customer.get('credit_score', 0)
        if credit_score > 700:
            probability += 0.1
        
        # 确保概率在有效范围内
        probability = min(probability, 0.95)
        
        return random.random() < probability
    
    def _generate_customer_churn_tag(self, customer: Dict) -> bool:
        """
        生成客户流失标志
        
        Args:
            customer: 客户数据
            
        Returns:
            是否流失
        """
        # 基础流失概率
        probability = 0.15
        
        # VIP客户流失概率降低
        if customer.get('is_vip'):
            probability -= 0.1
        
        # 根据信用评分调整
        credit_score = customer.get('credit_score', 0)
        if credit_score > 700:
            probability -= 0.05
        elif credit_score < 580:
            probability += 0.1
        
        # 根据会员等级调整
        member_level = customer.get('member_level', '1级')
        level = int(member_level.replace('级', ''))
        probability -= (level - 1) * 0.02  # 会员等级越高，流失概率越低
        
        # 确保概率在有效范围内
        probability = max(0.01, min(probability, 0.95))
        
        return random.random() < probability
    
    def _generate_is_churn_this_week(self, is_churn: bool) -> bool:
        """
        生成是否为本周新增流失客户
        
        Args:
            is_churn: 是否流失客户
            
        Returns:
            是否本周新增流失
        """
        # 如果不是流失客户，肯定不是本周新增流失
        if not is_churn:
            return False
        
        # 如果是流失客户，有20%是本周新增流失的
        return random.random() < 0.2
    
    def _generate_clearance_date(self, start_date: datetime.date, end_date: datetime.date) -> datetime.date:
        """
        生成清仓日期
        
        Args:
            start_date: 起始日期
            end_date: 结束日期
            
        Returns:
            清仓日期
        """
        # 在有效时间范围内随机生成日期
        return self.random_date(start_date, end_date)
    
    def _get_most_recent_date(self, date_list: List[Optional[datetime.date]]) -> Optional[datetime.date]:
        """
        获取最近的日期
        
        Args:
            date_list: 日期列表
            
        Returns:
            最近的日期，如果所有日期都为None则返回None
        """
        # 过滤掉None值
        valid_dates = [d for d in date_list if d is not None]
        
        if not valid_dates:
            return None
        
        # 返回最近的日期（最大的日期值）
        return max(valid_dates)
    
    def _generate_credit_amount(self, customer: Dict) -> float:
        """
        生成授信金额
        
        Args:
            customer: 客户数据
            
        Returns:
            授信金额
        """
        # 基础授信额度
        base_amount = 50000
        
        # 根据收入调整额度
        annual_income = customer.get('annual_income', 0)
        income_factor = min(annual_income / 50000, 10)  # 收入越高，额度越高，但有上限
        
        # 根据信用评分调整额度
        credit_score = customer.get('credit_score', 0)
        if credit_score >= 700:
            score_factor = 2.0
        elif credit_score >= 640:
            score_factor = 1.5
        elif credit_score >= 580:
            score_factor = 1.0
        else:
            score_factor = 0.5
        
        # VIP客户额度提升
        vip_factor = 2.0 if customer.get('is_vip') else 1.0
        
        # 计算最终授信额度
        amount = base_amount * income_factor * score_factor * vip_factor
        
        # 添加随机波动
        amount *= random.uniform(0.8, 1.2)
        
        # 限制最大额度，并四舍五入到整数
        max_amount = 1000000
        amount = min(amount, max_amount)
        
        return round(amount, 2)


class ManagerProfileGenerator(BaseProfileGenerator):
    """银行经理档案生成器，生成符合CDP客户档案范式的数据"""
    
    def __init__(self, fake_generator: faker.Faker, config_manager):
        """
        初始化银行经理档案生成器
        
        Args:
            fake_generator: Faker实例，用于生成随机数据
            config_manager: 配置管理器实例
        """
        super().__init__(fake_generator, config_manager)
        
        # 获取银行经理相关配置
        self.manager_config = self.config_manager.get_entity_config('manager') or {}
        
        # 获取银行经理档案表配置
        cdp_model_config = self.config_manager.get_entity_config('cdp_model')
        manager_profile_tables = cdp_model_config.get('customer_profile', {}).get('tables', [])
        
        # 查找经理表配置
        self.manager_table_config = next(
            (table for table in manager_profile_tables if table.get('entity') == 'manager'), 
            {'name': 'cdp_manager_profile', 'id_prefix': 'M'}
        )
        
        # 初始化日志
        self.logger = get_logger('ManagerProfileGenerator')
        
        # 初始化部门和职位数据
        self.departments = [
            '零售业务部', '对公业务部', '个人金融部', '信用卡中心', 
            '理财业务部', '网络金融部', '国际业务部', '资产管理部'
        ]
        self.positions = [
            '初级客户经理', '高级客户经理', '资深客户经理', '客户经理主管',
            '业务主管', '部门经理'
        ]
        self.position_weights = [0.4, 0.3, 0.15, 0.08, 0.05, 0.02]  # 职位的带权分布
        
        # 城市分布列表（基于中国主要城市人口比例）
        self.cities = [
            ('北京市', '北京', '中国'),
            ('上海市', '上海', '中国'),
            ('广州市', '广东', '中国'),
            ('深圳市', '广东', '中国'),
            ('重庆市', '重庆', '中国'),
            ('成都市', '四川', '中国'),
            ('杭州市', '浙江', '中国'),
            ('武汉市', '湖北', '中国'),
            ('西安市', '陕西', '中国'),
            ('南京市', '江苏', '中国'),
            ('天津市', '天津', '中国'),
            ('苏州市', '江苏', '中国'),
            ('郑州市', '河南', '中国'),
            ('长沙市', '湖南', '中国'),
            ('东莞市', '广东', '中国'),
            ('沈阳市', '辽宁', '中国'),
            ('青岛市', '山东', '中国'),
            ('合肥市', '安徽', '中国'),
            ('佛山市', '广东', '中国'),
            ('宁波市', '浙江', '中国')
        ]
        self.city_weights = [0.1, 0.1, 0.08, 0.08, 0.07, 0.06, 0.06, 0.05, 0.05, 0.05, 
                          0.04, 0.04, 0.04, 0.04, 0.03, 0.03, 0.03, 0.03, 0.02, 0.02]
    
    def _generate_branch_id(self) -> str:
        """
        从数据库中获取支行ID
    
        Returns:
        支行ID
        """
        try:
            # 获取数据库管理器实例
            from src.database_manager import get_database_manager
            db_manager = get_database_manager()
            
            # 查询所有可用的支行
            query = "SELECT base_id FROM cdp_branch_archive WHERE status = 'active'"
            results = db_manager.execute_query(query)
            
            if results and len(results) > 0:
                # 随机选择一个支行ID
                branch_id = random.choice(results)['base_id']
                return branch_id
            else:
                # 如果没有找到支行或查询错误，记录警告并生成临时ID
                self.logger.warning("未找到可用的支行记录，将生成临时支行ID")
                return f"B{self.faker.numerify('######')}"
        except Exception as e:
            # 发生错误时记录并生成临时ID
            self.logger.error(f"获取支行ID失败: {str(e)}")
            return f"B{self.faker.numerify('######')}"
        
    def _generate_annual_performance(self, position: str, hire_date: datetime.date) -> float:
        """
        根据职位和工作年限生成年度业绩
        
        Args:
            position: 职位级别
            hire_date: 入职日期
            
        Returns:
            年度业绩金额
        """
        # 职位基本业绩参考值
        position_base_performance = {
            '初级客户经理': 1000000,
            '高级客户经理': 2000000,
            '资深客户经理': 3000000,
            '客户经理主管': 4000000,
            '业务主管': 5000000,
            '部门经理': 8000000
        }
        
        # 获取基础业绩目标
        base_performance = position_base_performance.get(position, 1000000)
        
        # 根据工作年限调整基础业绩
        today = datetime.date.today()
        years_of_service = (today - hire_date).days // 365
        experience_factor = min(1 + years_of_service * 0.05, 2.0)  # 每工作一年增加5%，最多翻倍
        
        # 计算年度业绩
        annual_performance = base_performance * experience_factor
        
        # 添加随机波动(±20%)
        annual_performance *= random.uniform(0.8, 1.2)
        
        return round(annual_performance, 2)
    
    def _generate_monthly_target(self, annual_performance: float) -> float:
        """
        根据年度业绩生成月度目标
        
        Args:
            annual_performance: 年度业绩金额
            
        Returns:
            月度目标金额
        """
        # 月度目标一般是年度目标的1/12，再加上季节性波动
        base_monthly_target = annual_performance / 12
        
        # 获取当前月份，不同月份有不同的季节性调整
        current_month = datetime.date.today().month
        
        # 季节性调整因子
        # Q1: 开年业务相对平缓
        # Q2: 业务逐步上升
        # Q3: 暑期特殊产品推广
        # Q4: 冲刺年度目标
        season_factors = {
            1: 0.85, 2: 0.9, 3: 0.95,     # Q1
            4: 1.0, 5: 1.05, 6: 1.1,      # Q2
            7: 1.05, 8: 1.0, 9: 1.1,      # Q3
            10: 1.2, 11: 1.15, 12: 1.0    # Q4
        }
        
        season_factor = season_factors.get(current_month, 1.0)
        
        # 计算调整后的月度目标
        monthly_target = base_monthly_target * season_factor
        
        # 添加随机波动(±10%)
        monthly_target *= random.uniform(0.9, 1.1)
        
        return round(monthly_target, 2)
    
    def _generate_client_count(self, position: str) -> tuple:
        """
        根据职位生成客户数量统计
        
        Args:
            position: 职位级别
            
        Returns:
            (当前管理客户数量, 活跃客户数量)
        """
        # 职位等级与客户数量的对应关系
        position_client_capacity = {
            '初级客户经理': (50, 100),
            '高级客户经理': (80, 150),
            '资深客户经理': (120, 200),
            '客户经理主管': (80, 120),
            '业务主管': (50, 80),
            '部门经理': (20, 40)
        }
        
        # 获取该职位的客户容量范围
        min_clients, max_clients = position_client_capacity.get(position, (50, 100))
        
        # 随机生成当前管理的客户数量
        current_client_count = random.randint(min_clients, max_clients)
        
        # 活跃客户数量一般是总数的60%-90%
        active_ratio = random.uniform(0.6, 0.9)
        active_client_count = int(current_client_count * active_ratio)
        
        return current_client_count, active_client_count
    
    def _get_last_quarter_end(self) -> datetime.date:
        """
        获取上一个季度末的日期，作为业绩评估日期
        
        Returns:
            上一个季度末的日期
        """
        today = datetime.date.today()
        current_month = today.month
        current_year = today.year
        
        # 确定上一个季度末
        if current_month in [1, 2, 3]:
            # 上一个季度是上一年的Q4
            quarter_end_month = 12
            quarter_end_year = current_year - 1
        elif current_month in [4, 5, 6]:
            # 上一个季度是本年的Q1
            quarter_end_month = 3
            quarter_end_year = current_year
        elif current_month in [7, 8, 9]:
            # 上一个季度是本年的Q2
            quarter_end_month = 6
            quarter_end_year = current_year
        else:
            # 上一个季度是本年的Q3
            quarter_end_month = 9
            quarter_end_year = current_year
        
        # 确定季度末的具体日期
        if quarter_end_month in [3, 6, 9]:
            quarter_end_day = 30 if quarter_end_month == 6 else 31
        else:  # 12月
            quarter_end_day = 31
        
        # 创建日期对象
        quarter_end_date = datetime.date(quarter_end_year, quarter_end_month, quarter_end_day)
        
        # 如果季度末是周末，调整到最近的工作日
        weekday = quarter_end_date.weekday()
        if weekday == 5:  # 周六
            quarter_end_date = quarter_end_date - datetime.timedelta(days=1)
        elif weekday == 6:  # 周日
            quarter_end_date = quarter_end_date - datetime.timedelta(days=2)
        
        return quarter_end_date
        
    def _generate_manager_notes(self, position: str, annual_performance: float, hire_date: datetime.date) -> str:
        """
        生成经理备注信息
        
        Args:
            position: 职位级别
            annual_performance: 年度业绩
            hire_date: 入职日期
            
        Returns:
            备注信息
        """
        # 计算工作年限
        years_of_service = (datetime.date.today() - hire_date).days // 365
        
        # 备注信息模板
        templates = [
            "业绩表现{performance_desc}，{specialty_desc}，客户服务满意度{satisfaction}。",
            "{specialty_desc}，团队协作能力{team_desc}，{development_desc}。",
            "专长于{specialty}产品销售，{personality_desc}，{future_desc}。",
            "工作{years_of_service}年，{performance_desc}，{training_desc}。"
        ]
        
        # 业绩描述
        if annual_performance > 5000000:
            performance_desc = "出色"
        elif annual_performance > 3000000:
            performance_desc = "良好"
        elif annual_performance > 1000000:
            performance_desc = "达标"
        else:
            performance_desc = "一般"
        
        # 专长描述
        specialties = [
            "个人理财",
            "企业金融",
            "财富管理",
            "信用卡业务",
            "个人贷款",
            "企业贷款",
            "外汇业务",
            "投资顾问"
        ]
        specialty = random.choice(specialties)
        specialty_desc = f"专长于{specialty}业务"
        
        # 满意度
        satisfactions = ["优秀", "良好", "中等", "需要提升"]
        satisfaction = self.random_choice(satisfactions, [0.3, 0.4, 0.2, 0.1])
        
        # 团队协作
        team_descs = ["强", "良好", "一般", "需要提升"]
        team_desc = random.choice(team_descs)
        
        # 发展描述
        development_descs = [
            "具有高管潜力",
            "可培养为团队主管",
            "专业能力需进一步提升",
            "建议加强客户服务技能"
        ]
        development_desc = random.choice(development_descs)
        
        # 个性描述
        personality_descs = [
            "沟通能力强",
            "注重细节",
            "积极主动",
            "分析能力强",
            "关系维护好"
        ]
        personality_desc = random.choice(personality_descs)
        
        # 未来展望
        future_descs = [
            "有望提升为团队负责人",
            "可重点培养",
            f"建议转岗至{random.choice(self.departments)}",
            "需加强培训提高业绩",
            "可作为新人导师"
        ]
        future_desc = random.choice(future_descs)
        
        # 培训描述
        training_descs = [
            "需要加强产品知识培训",
            "建议参加高级客户经理培训",
            "已完成所有必要培训",
            "可作为内部培训讲师"
        ]
        training_desc = random.choice(training_descs)
        
        # 随机选择一个模板填充
        template = random.choice(templates)
        notes = template.format(
            performance_desc=performance_desc,
            specialty_desc=specialty_desc,
            satisfaction=satisfaction,
            team_desc=team_desc,
            development_desc=development_desc,
            specialty=specialty,
            personality_desc=personality_desc,
            future_desc=future_desc,
            years_of_service=years_of_service,
            training_desc=training_desc
        )
        
        return notes
    
    def generate(self, count: Optional[int] = None) -> List[Dict]:
        """
        生成银行经理档案数据
        
        Args:
            count: 生成的经理数量，如果为None则用配置中的值
            
        Returns:
            经理档案数据列表
        """
        # 确定生成数量
        if count is None:
            count = self.manager_config.get('total_count', 200)  # 默认200条
        
        self.logger.info(f"开始生成 {count} 条银行经理档案数据")
        
        managers = []
        
        # 生成经理数据
        for i in range(count):
            manager = self._generate_manager()
            managers.append(manager)
        
        # 清洗并验证数据
        managers = self.clean_profiles(managers)
        
        self.logger.info(f"成功生成 {len(managers)} 条银行经理档案数据")
        
        return managers
    
    def _generate_manager(self) -> Dict:
        """
        生成单个银行经理数据
        
        Returns:
            银行经理数据字典
        """
        # 基础信息字段生成
        manager = {}
        
        # 添加分区字段
        manager['pt'] = self.get_partition_date()
        
        # 生成经理ID
        id_prefix = self.manager_table_config.get('id_prefix', 'M')
        manager['base_id'] = self.generate_id(id_prefix)
        
        # 生成标准的经理ID（managerid字段）
        manager['managerid'] = manager['base_id']
        
        # 生成经理名称（中文名）
        manager['name'] = self.faker.name()
        
        # 生成性别
        gender = random.choice(['M', 'F'])
        manager['gender'] = gender
        
        # 生成出生日期（经理年龄一般在25-55岁之间）
        current_date = datetime.date.today()
        min_birth_year = current_date.year - 55
        max_birth_year = current_date.year - 25
        
        birth_date = self.random_date(
            datetime.date(min_birth_year, 1, 1),
            datetime.date(max_birth_year, 12, 31)
        )
        manager['birth_date'] = birth_date
        
        # 生成入职日期（基于出生日期，至少大学22岁）
        min_hire_date = max(datetime.date(birth_date.year + 22, birth_date.month, birth_date.day), 
                           datetime.date(2000, 1, 1))  # 不早于2000年
        hire_date = self.random_date(min_hire_date, current_date - datetime.timedelta(days=30))  # 至少入职了30天
        manager['hire_date'] = hire_date
        
        # 生成部门
        manager['department'] = random.choice(self.departments)
        
        # 生成职位（基于带权分布）
        manager['position'] = self.random_choice(self.positions, self.position_weights)
        
        # 生成联系电话
        manager['contact_number'] = self._generate_phone_number()
        
        # 生成电子邮箱（使用公司邮箱格式）
        manager['email'] = self._generate_company_email(manager['name'])
        
        # 生成地理位置信息
        city_data = self.random_choice(self.cities, self.city_weights)
        
        # 生成家庭地址
        manager['address'] = self._generate_address(city_data[0])
        
        # 生成支行ID
        manager['branch_id'] = self._generate_branch_id()
        
        # 生成年度业绩
        manager['annual_performance'] = self._generate_annual_performance(
            manager['position'], manager['hire_date'])
        
        # 生成月度目标
        manager['monthly_target'] = self._generate_monthly_target(manager['annual_performance'])
        
        # 生成客户数量统计
        manager['current_client_count'], manager['active_client_count'] = self._generate_client_count(
            manager['position'])
        
        # 生成上次业绩评估日期
        manager['last_performance_review_date'] = self._get_last_quarter_end()
        
        # 生成备注信息
        manager['notes'] = self._generate_manager_notes(
            manager['position'], manager['annual_performance'], manager['hire_date'])
        
        # 生成记录创建和更新时间
        current_datetime = datetime.datetime.now()
        manager['created_at'] = current_datetime
        manager['updated_at'] = current_datetime
        
        return manager
    
    def _generate_phone_number(self) -> str:
        """
        生成手机号码
        
        Returns:
            手机号码
        """
        # 中国手机号前三位运营商号段
        prefixes = [
            # 移动
            '134', '135', '136', '137', '138', '139', '150', '151', '152', '157', '158', '159',
            '182', '183', '184', '187', '188', '147', '178', '198',
            # 联通
            '130', '131', '132', '155', '156', '185', '186', '145', '176', '166',
            # 电信
            '133', '153', '180', '181', '189', '177', '173', '199'
        ]
        
        # 随机选择前缀
        prefix = random.choice(prefixes)
        
        # 生成后8位数字
        suffix = self.faker.numerify('########')
        
        return f"{prefix}{suffix}"
    
    def _generate_company_email(self, name: str) -> str:
        """
        生成公司邮箱
        
        Args:
            name: 经理姓名
            
        Returns:
            公司邮箱地址
        """
        # 简化处理，使用英文用户名
        # 实际应用中可以引入拼音转换库将中文名转为拼音
        username_types = [
            lambda n: self.faker.user_name(),  # 随机用户名
            lambda n: f"{self.faker.last_name().lower()}.{self.faker.first_name().lower()}",  # 姓.名
            lambda n: f"{self.faker.first_name().lower()}{random.randint(1, 99)}",  # 名+数字
            lambda n: f"{self.faker.last_name().lower()}{self.faker.first_name().lower()[0]}",  # 姓+名首字母
        ]
        
        username_generator = random.choice(username_types)
        username = username_generator(name)
        
        # 银行域名
        bank_domains = [
            'bank.com', 'bankgroup.cn', 'finance-bank.com', 'bank-finance.cn',
            'bankchina.com', 'nationalbank.cn', 'citybank.com', 'bank-online.cn'
        ]
        domain = random.choice(bank_domains)
        
        return f"{username}@{domain}"
    
    def _generate_address(self, city: str) -> str:
        """
        生成地址
        
        Args:
            city: 城市
            
        Returns:
            完整地址
        """
        # 生成随机小区名
        communities = [
            '阳光花园', '翰林苑', '金色家园', '绿景花园', '丽景华庭', '紫荆花园',
            '龙湖花园', '万科城市花园', '保利花园', '碧桂园', '恒大华府', '金地国际城',
            '星河湾', '中海康城', '珠江新城', '雅居乐花园', '招商小区', '华润万家',
            '富力城', '佳兆业金域', '世纪城', '锦绣花园', '御景华庭', '香樟园'
        ]
        community = random.choice(communities)
        
        # 随机楼栋号
        building = f"{random.randint(1, 20)}栋"
        
        # 随机单元号
        unit = f"{random.randint(1, 6)}单元"
        
        # 随机房号
        room = f"{random.randint(101, 2599)}"
        
        # 随机道路
        roads = [
            '中山路', '解放路', '人民路', '建设路', '和平路', '兴华路', '长江路',
            '黄河路', '南京路', '北京路', '上海路', '广州路', '深圳路', '天府大道',
            '望江路', '科华路', '东风路', '西二环', '金融街', '体育路', '教育路'
        ]
        road = random.choice(roads)
        
        # 随机号码
        number = random.randint(1, 999)
        
        return f"{city}{road}{number}号，{community}{building}{unit}{room}"
