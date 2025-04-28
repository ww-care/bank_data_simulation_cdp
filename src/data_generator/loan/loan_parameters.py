#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
贷款参数计算模型

负责计算贷款利率、费用等参数。
"""

import random
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any

class LoanParametersModel:
    """
    贷款参数模型，负责计算和生成贷款相关的参数：
    - 利率计算
    - 贷款期限选择
    - 贷款金额范围确定
    - 费用计算
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化贷款参数模型
        
        Args:
            config: 贷款配置参数，包含默认利率范围、期限选项等
        """
        self.config = config
        
        # 从配置中获取贷款配置
        self.loan_config = config.get('loan', {})
        
        # 基准利率
        self.base_rate = self.loan_config.get('interest_rate', {}).get('base_rate', 0.0325)
        
        # 各类贷款利率调整参数
        self.interest_rate_adjustments = self.loan_config.get('interest_rate', {})
        
        # 贷款期限
        self.term_distribution = self.loan_config.get('term_distribution', {})
        
        # 贷款类型分布
        self.type_distribution = self.loan_config.get('type_distribution', {})
        
        # 信用评分对利率的影响系数
        self.credit_score_impact = self.loan_config.get('interest_rate', {}).get('credit_score_impact', 0.20)
    
    def calculate_interest_rate(self, loan_type: str, credit_score: int, 
                               loan_amount: float, loan_term_months: int) -> float:
        """
        根据贷款类型、客户信用评分、贷款金额和期限计算利率
        
        Args:
            loan_type: 贷款类型（个人消费贷、住房贷款等）
            credit_score: 客户信用评分（通常350-850范围）
            loan_amount: 贷款金额
            loan_term_months: 贷款期限（月）
            
        Returns:
            float: 计算的年化利率（小数形式，如0.05表示5%）
        """
        # 获取基准利率
        rate = self.base_rate
        
        # 获取该贷款类型的利率调整范围
        adjustment_config = self.interest_rate_adjustments.get(loan_type, {})
        min_adjustment = adjustment_config.get('min_adjustment', 0.02)
        max_adjustment = adjustment_config.get('max_adjustment', 0.04)
        
        # 如果没有找到特定类型，使用个人消费贷的调整值作为默认
        if not adjustment_config:
            min_adjustment = self.interest_rate_adjustments.get('personal_consumption', {}).get('min_adjustment', 0.02)
            max_adjustment = self.interest_rate_adjustments.get('personal_consumption', {}).get('max_adjustment', 0.04)
        
        # 信用评分影响
        # 将信用评分范围(350-850)映射到0-1范围内，信用越高，值越大
        credit_score_normalized = (credit_score - 350) / 500  # 假设信用分范围是350-850
        credit_score_normalized = max(0, min(credit_score_normalized, 1))  # 确保在0-1范围内
        
        # 信用评分对利率的影响（越高信用评分，利率越低）
        credit_adjustment = (max_adjustment - min_adjustment) * (1 - credit_score_normalized) * self.credit_score_impact
        
        # 贷款期限影响（期限越长，可能利率略微提高）
        term_factor = 0
        if loan_term_months > 240:  # 20年以上
            term_factor = 0.003
        elif loan_term_months > 120:  # 10年以上
            term_factor = 0.002
        elif loan_term_months > 60:  # 5年以上
            term_factor = 0.001
        
        # 贷款金额影响（金额越大，可能享受更优惠的利率）
        amount_factor = 0
        if loan_type == 'mortgage' and loan_amount > 2000000:
            amount_factor = -0.002
        elif loan_amount > 1000000:
            amount_factor = -0.001
        
        # 添加随机波动，使数据更自然
        random_factor = random.uniform(-0.002, 0.002)
        
        # 计算最终利率
        final_rate = rate + min_adjustment + credit_adjustment + term_factor + amount_factor + random_factor
        
        # 确保利率在合理范围内
        final_rate = max(rate + min_adjustment, min(rate + max_adjustment, final_rate))
        
        return round(final_rate, 4)  # 四舍五入到万分位
    
    def select_loan_term(self, loan_type: str, customer_preference: Optional[str] = None) -> int:
        """
        为特定贷款类型选择合适的贷款期限（以月为单位）
        
        Args:
            loan_type: 贷款类型（个人消费贷、住房贷款等）
            customer_preference: 可选的客户偏好期限类型（'short_term', 'medium_term', 'long_term'）
            
        Returns:
            int: 选择的贷款期限（月）
        """
        # 获取贷款期限配置
        term_config = self.term_distribution
        
        # 如果没有客户偏好，根据配置的分布随机选择一个期限类型
        if not customer_preference:
            # 计算累积概率
            short_term_ratio = term_config.get('short_term', {}).get('ratio', 0.25)
            medium_term_ratio = term_config.get('medium_term', {}).get('ratio', 0.45)
            long_term_ratio = term_config.get('long_term', {}).get('ratio', 0.30)
            
            # 确保比例总和为1
            total_ratio = short_term_ratio + medium_term_ratio + long_term_ratio
            short_term_ratio /= total_ratio
            medium_term_ratio /= total_ratio
            long_term_ratio /= total_ratio
            
            # 随机选择期限类型
            rand = random.random()
            if rand < short_term_ratio:
                customer_preference = 'short_term'
            elif rand < short_term_ratio + medium_term_ratio:
                customer_preference = 'medium_term'
            else:
                customer_preference = 'long_term'
        
        # 根据贷款类型调整期限选择逻辑
        if loan_type == 'mortgage':
            # 房贷通常是长期的
            if customer_preference == 'short_term':
                # 即使客户偏好短期，房贷也至少是中期
                customer_preference = 'medium_term'
            
            # 对于房贷，增加长期的概率
            if random.random() < 0.7 and customer_preference == 'medium_term':
                customer_preference = 'long_term'
        
        elif loan_type == 'car':
            # 车贷通常是中期的
            if customer_preference == 'long_term':
                # 车贷很少超过5年
                customer_preference = 'medium_term'
        
        elif loan_type == 'personal_consumption':
            # 个人消费贷通常是短期或中期的
            if customer_preference == 'long_term' and random.random() < 0.8:
                customer_preference = 'medium_term'
        
        # 从选定的期限类型中获取可用的月数列表
        available_months = term_config.get(customer_preference, {}).get('months', [])
        
        # 如果没有可用月数，使用默认值
        if not available_months:
            if customer_preference == 'short_term':
                available_months = [3, 6, 12]
            elif customer_preference == 'medium_term':
                available_months = [24, 36, 48, 60]
            else:  # long_term
                available_months = [72, 84, 120, 180, 240, 300, 360]
        
        # 根据贷款类型进一步过滤可用月数
        if loan_type == 'mortgage' and customer_preference == 'long_term':
            # 房贷长期通常是10年以上
            available_months = [m for m in available_months if m >= 120]
        elif loan_type == 'car':
            # 车贷通常不超过5年
            available_months = [m for m in available_months if m <= 60]
        elif loan_type == 'personal_consumption':
            # 个人消费贷通常不超过3年
            available_months = [m for m in available_months if m <= 36]
        
        # 如果过滤后没有可用月数，返回该类型的典型期限
        if not available_months:
            if loan_type == 'mortgage':
                return 240  # 20年
            elif loan_type == 'car':
                return 36   # 3年
            elif loan_type == 'personal_consumption':
                return 12   # 1年
            elif loan_type == 'small_business':
                return 36   # 3年
            else:
                return 24   # 2年默认
        
        # 随机选择一个可用期限
        return random.choice(available_months)
    
    def calculate_loan_amount_range(self, loan_type: str, annual_income: float, 
                              credit_score: int, is_corporate: bool = False) -> Tuple[float, float]:
        """
        根据贷款类型、年收入和信用评分计算适当的贷款金额范围
        
        Args:
            loan_type: 贷款类型（个人消费贷、住房贷款等）
            annual_income: 申请人年收入
            credit_score: 申请人信用评分
            is_corporate: 是否为企业客户
            
        Returns:
            Tuple[float, float]: 贷款金额范围（最小值，最大值）
        """
        # 基本收入倍数范围
        base_multiplier_min = 0.5
        base_multiplier_max = 3.0
        
        # 根据贷款类型调整倍数
        if loan_type == 'mortgage':
            # 住房贷款通常是年收入的4-8倍
            base_multiplier_min = 4.0
            base_multiplier_max = 8.0
        elif loan_type == 'car':
            # 车贷通常是年收入的0.5-1.5倍
            base_multiplier_min = 0.5
            base_multiplier_max = 1.5
        elif loan_type == 'personal_consumption':
            # 消费贷通常是年收入的0.3-1.0倍
            base_multiplier_min = 0.3
            base_multiplier_max = 1.0
        elif loan_type == 'small_business':
            # The following code block is indented with spaces
            # 小微企业贷款通常是年收入的1.0-3.0倍
            base_multiplier_min = 1.0
            base_multiplier_max = 3.0
        elif loan_type == 'education':
            # 教育贷款通常较小
            base_multiplier_min = 0.2
            base_multiplier_max = 0.8
        
        # 企业客户通常可以获得更高的贷款额度
        if is_corporate:
            base_multiplier_min *= 2.0
            base_multiplier_max *= 2.0
        
        # 根据信用评分调整倍数
        # 将信用评分归一化到0-1范围
        credit_score_normalized = (credit_score - 350) / 500  # 假设信用分范围是350-850
        credit_score_normalized = max(0, min(credit_score_normalized, 1))
        
        # 信用评分对贷款金额的影响（越高的信用评分，可获得的贷款额度越高）
        credit_multiplier = 0.5 + credit_score_normalized * 0.5  # 0.5 - 1.0
        
        # 应用信用分调整
        min_multiplier = base_multiplier_min * credit_multiplier
        max_multiplier = base_multiplier_max * credit_multiplier
        
        # 计算贷款金额范围
        min_amount = annual_income * min_multiplier
        max_amount = annual_income * max_multiplier
        
        # 根据贷款类型设置绝对上下限
        absolute_min = 10000  # 默认最低贷款额
        absolute_max = 10000000  # 默认最高贷款额
        
        if loan_type == 'mortgage':
            absolute_min = 100000
            absolute_max = 5000000
        elif loan_type == 'car':
            absolute_min = 50000
            absolute_max = 1000000
        elif loan_type == 'personal_consumption':
            absolute_min = 10000
            absolute_max = 500000
        elif loan_type == 'small_business':
            absolute_min = 50000
            absolute_max = 2000000
        elif loan_type == 'education':
            absolute_min = 10000
            absolute_max = 300000
        
        # 应用绝对上下限
        min_amount = max(min_amount, absolute_min)
        max_amount = min(max_amount, absolute_max)
        
        # 企业客户的最高贷款额度可以更高
        if is_corporate:
            max_amount = min(max_amount * 2, absolute_max * 2)
        
        # 确保最小值不大于最大值
        if min_amount > max_amount:
            min_amount = max_amount
        
        # 四舍五入到整百
        min_amount = round(min_amount / 100) * 100
        max_amount = round(max_amount / 100) * 100
        
        return min_amount, max_amount
    
    def select_loan_amount(self, loan_type: str, min_amount: float, max_amount: float, 
                        credit_score: int, preferred_amount: Optional[float] = None) -> float:
        """
        在给定范围内选择具体的贷款金额
        
        Args:
            loan_type: 贷款类型（个人消费贷、住房贷款等）
            min_amount: 最小贷款金额
            max_amount: 最大贷款金额
            credit_score: 申请人信用评分
            preferred_amount: 申请人偏好的贷款金额（可选）
            
        Returns:
            float: 选择的贷款金额
        """
        # 如果提供了偏好金额，检查是否在范围内并调整
        if preferred_amount is not None:
            if preferred_amount < min_amount:
                # 如果偏好金额低于最小额度，有80%概率升至最小额度，20%概率使用偏好金额
                if random.random() < 0.8:
                    return min_amount
                else:
                    return preferred_amount
            elif preferred_amount > max_amount:
                # 如果偏好金额高于最大额度，根据信用评分决定是否批准更高额度
                credit_score_normalized = (credit_score - 350) / 500  # 350-850范围归一化到0-1
                
                # 信用越好，获得更高额度的可能性越大
                approval_chance = 0.1 + credit_score_normalized * 0.4  # 0.1-0.5的批准概率
                
                if random.random() < approval_chance:
                    # 批准高于标准的额度，但不超过最大值的20%
                    return min(preferred_amount, max_amount * 1.2)
                else:
                    # 不批准更高额度，给予最大额度
                    return max_amount
            else:
                # 偏好金额在范围内，直接使用
                return preferred_amount
        
        # 根据贷款类型和信用评分确定分布的偏向性
        # 默认情况下，我们使用正态分布模拟更自然的选择
        # 不同贷款类型的分布中心点不同
        
        # 信用评分影响分布的位置（信用越好，可能获得更高额度）
        credit_score_normalized = (credit_score - 350) / 500
        credit_score_normalized = max(0, min(credit_score_normalized, 1))
        
        # 计算分布均值位置（0为最小值，1为最大值）
        if loan_type == 'mortgage':
            # 房贷通常偏向较高额度
            mean_position = 0.6 + credit_score_normalized * 0.2  # 0.6-0.8
        elif loan_type == 'car':
            # 车贷分布相对均匀
            mean_position = 0.5 + credit_score_normalized * 0.1  # 0.5-0.6
        elif loan_type == 'personal_consumption':
            # 消费贷偏向中低额度
            mean_position = 0.4 + credit_score_normalized * 0.2  # 0.4-0.6
        elif loan_type == 'small_business':
            # 小微企业贷款分布相对均匀
            mean_position = 0.5 + credit_score_normalized * 0.2  # 0.5-0.7
        else:
            # 其他贷款默认分布
            mean_position = 0.5
        
        # 标准差决定分布的集中度
        std_dev = 0.15
        
        # 生成正态分布的随机数，限制在0-1范围内
        position = -1
        while position < 0 or position > 1:
            position = random.normalvariate(mean_position, std_dev)
        
        # 插值计算具体金额
        amount = min_amount + position * (max_amount - min_amount)
        
        # 特殊处理：对某些贷款类型进行金额调整
        if loan_type == 'mortgage':
            # 房贷金额通常是整10万的倍数
            amount = round(amount / 100000) * 100000
        elif loan_type == 'car':
            # 车贷通常是整万的倍数
            amount = round(amount / 10000) * 10000
        else:
            # 其他贷款通常是整千的倍数
            amount = round(amount / 1000) * 1000
        
        # 确保最终金额在范围内
        amount = max(min_amount, min(amount, max_amount))
        
        return amount

    def select_repayment_method(self, loan_type: str, loan_term_months: int, 
                          is_corporate: bool = False) -> str:
        """
        根据贷款类型和期限选择合适的还款方式
        
        Args:
            loan_type: 贷款类型（个人消费贷、住房贷款等）
            loan_term_months: 贷款期限（月）
            is_corporate: 是否为企业客户
            
        Returns:
            str: 选择的还款方式
        """
        # 定义常见的还款方式
        repayment_methods = [
            '等额本息',   # 每月还款额相同，本金逐月递增，利息逐月递减
            '等额本金',   # 每月本金相同，利息逐月递减，总还款额逐月递减
            '先息后本',   # 月还息，到期还本
            '一次性还本付息'  # 到期一次性还本付息
        ]
        
        # 根据贷款类型设置各种还款方式的概率权重
        if loan_type == 'mortgage':
            # 房贷通常使用等额本息或等额本金
            weights = [0.65, 0.35, 0.0, 0.0]
        elif loan_type == 'car':
            # 车贷通常使用等额本息
            weights = [0.8, 0.15, 0.05, 0.0]
        elif loan_type == 'personal_consumption':
            # 个人消费贷较灵活
            if loan_term_months <= 6:
                # 短期消费贷可能使用一次性还本付息
                weights = [0.4, 0.1, 0.2, 0.3]
            else:
                weights = [0.6, 0.15, 0.25, 0.0]
        elif loan_type == 'small_business':
            # 小微企业贷款更灵活
            if loan_term_months <= 12:
                weights = [0.3, 0.2, 0.3, 0.2]
            else:
                weights = [0.45, 0.35, 0.2, 0.0]
        elif loan_type == 'education':
            # 教育贷款通常是等额本息，可能有宽限期（这里简化为先息后本）
            weights = [0.7, 0.1, 0.2, 0.0]
        else:
            # 默认权重
            weights = [0.5, 0.2, 0.2, 0.1]
        
        # 企业客户可能更倾向于灵活的还款方式
        if is_corporate:
            # 增加先息后本的概率
            if weights[2] > 0:
                weights[2] += 0.1
                # 相应减少等额本息的概率
                weights[0] -= 0.1
        
        # 根据期限调整
        if loan_term_months <= 3:
            # 极短期贷款更可能使用一次性还本付息
            weights[3] += 0.2
            # 相应减少其他方式的概率
            total_decrease = 0.2
            for i in range(3):
                if weights[i] > 0:
                    decrease = min(weights[i], total_decrease * weights[i] / sum(weights[:3]))
                    weights[i] -= decrease
        elif loan_term_months >= 240:
            # 超长期贷款（20年以上）几乎一定是等额本息或等额本金
            weights = [0.7, 0.3, 0.0, 0.0]
        
        # 规范化权重
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]
        else:
            # 避免除以零错误
            weights = [0.25, 0.25, 0.25, 0.25]
        
        # 根据权重随机选择还款方式
        selected_method = random.choices(repayment_methods, weights=weights)[0]
        
        return selected_method

    def calculate_repayment_schedule(self, loan_amount: float, interest_rate: float, 
                                loan_term_months: int, repayment_method: str) -> List[Dict[str, float]]:
        """
        计算贷款的还款计划
        
        Args:
            loan_amount: 贷款金额
            interest_rate: 年化利率（小数形式，如0.05表示5%）
            loan_term_months: 贷款期限（月）
            repayment_method: 还款方式
            
        Returns:
            List[Dict[str, float]]: 还款计划，每个元素包含月份、应还本金、应还利息和剩余本金
        """
        # 将年化利率转换为月利率
        monthly_rate = interest_rate / 12
        
        # 初始化还款计划列表
        schedule = []
        
        # 根据不同的还款方式计算还款计划
        if repayment_method == '等额本息':
            # 等额本息：每月还款额相同，本金逐月递增，利息逐月递减
            # 月还款额 = 贷款本金 × 月利率 × (1+月利率)^贷款期限 / [(1+月利率)^贷款期限 - 1]
            if monthly_rate > 0:
                monthly_payment = loan_amount * monthly_rate * ((1 + monthly_rate) ** loan_term_months) / \
                                (((1 + monthly_rate) ** loan_term_months) - 1)
            else:
                # 处理零利率情况
                monthly_payment = loan_amount / loan_term_months
            
            remaining_principal = loan_amount
            
            for month in range(1, loan_term_months + 1):
                # 计算当月利息
                interest = remaining_principal * monthly_rate
                
                # 计算当月本金
                principal = monthly_payment - interest
                
                # 更新剩余本金
                remaining_principal -= principal
                
                # 处理最后一个月的舍入误差
                if month == loan_term_months:
                    principal += remaining_principal
                    remaining_principal = 0
                
                # 添加到还款计划
                schedule.append({
                    'month': month,
                    'principal': round(principal, 2),
                    'interest': round(interest, 2),
                    'remaining_principal': round(remaining_principal, 2)
                })
        
        elif repayment_method == '等额本金':
            # 等额本金：每月本金相同，利息逐月递减，总还款额逐月递减
            # 每月本金 = 贷款本金 / 贷款期限
            # 每月利息 = 剩余本金 × 月利率
            
            monthly_principal = loan_amount / loan_term_months
            remaining_principal = loan_amount
            
            for month in range(1, loan_term_months + 1):
                # 计算当月利息
                interest = remaining_principal * monthly_rate
                
                # 更新剩余本金
                remaining_principal -= monthly_principal
                
                # 处理最后一个月的舍入误差
                if month == loan_term_months:
                    monthly_principal += remaining_principal
                    remaining_principal = 0
                
                # 添加到还款计划
                schedule.append({
                    'month': month,
                    'principal': round(monthly_principal, 2),
                    'interest': round(interest, 2),
                    'remaining_principal': round(remaining_principal, 2)
                })
        
        elif repayment_method == '先息后本':
            # 先息后本：每月只还利息，本金到期一次性偿还
            # 月利息 = 贷款本金 × 月利率
            
            monthly_interest = loan_amount * monthly_rate
            
            for month in range(1, loan_term_months + 1):
                if month < loan_term_months:
                    # 前面的月份只还利息
                    principal = 0
                    remaining_principal = loan_amount
                else:
                    # 最后一个月还本金
                    principal = loan_amount
                    remaining_principal = 0
                
                # 添加到还款计划
                schedule.append({
                    'month': month,
                    'principal': round(principal, 2),
                    'interest': round(monthly_interest, 2),
                    'remaining_principal': round(remaining_principal, 2)
                })
        
        elif repayment_method == '一次性还本付息':
            # 一次性还本付息：到期一次性还本付息
            # 总利息 = 贷款本金 × 月利率 × 贷款期限
            
            total_interest = loan_amount * monthly_rate * loan_term_months
            
            for month in range(1, loan_term_months + 1):
                if month < loan_term_months:
                    # 前面的月份不还款
                    principal = 0
                    interest = 0
                    remaining_principal = loan_amount
                else:
                    # 最后一个月还本金和所有利息
                    principal = loan_amount
                    interest = total_interest
                    remaining_principal = 0
                
                # 添加到还款计划
                schedule.append({
                    'month': month,
                    'principal': round(principal, 2),
                    'interest': round(interest, 2),
                    'remaining_principal': round(remaining_principal, 2)
                })
        
        else:
            # 默认使用等额本息
            return self.calculate_repayment_schedule(
                loan_amount, interest_rate, loan_term_months, '等额本息')
        
        return schedule
    
    def calculate_loan_fees(self, loan_type: str, loan_amount: float, 
                      loan_term_months: int, is_vip: bool = False) -> Dict[str, float]:
        """
        计算贷款相关的各种费用
        
        Args:
            loan_type: 贷款类型（个人消费贷、住房贷款等）
            loan_amount: 贷款金额
            loan_term_months: 贷款期限（月）
            is_vip: 是否为VIP客户
            
        Returns:
            Dict[str, float]: 各种费用的字典，包括手续费、提前还款违约金率等
        """
        # 初始化费用字典
        fees = {
            'application_fee': 0.0,           # 申请费
            'service_fee': 0.0,               # 服务费/手续费
            'service_fee_rate': 0.0,          # 服务费率
            'early_repayment_penalty_rate': 0.0,  # 提前还款违约金率
            'late_payment_penalty_rate': 0.0,     # 逾期罚息率
            'insurance_fee': 0.0,             # 保险费（如有）
            'guarantee_fee': 0.0,             # 担保费（如有）
        }
        
        # 根据贷款类型设置基础手续费率
        base_service_fee_rate = 0.0
        if loan_type == 'mortgage':
            # 房贷通常有固定的手续费
            base_service_fee_rate = 0.003   # 0.3%
        elif loan_type == 'car':
            # 车贷手续费率通常较高
            base_service_fee_rate = 0.005   # 0.5%
        elif loan_type == 'personal_consumption':
            # 个人消费贷手续费率更高
            base_service_fee_rate = 0.01    # 1.0%
        elif loan_type == 'small_business':
            # 小微企业贷款手续费率适中
            base_service_fee_rate = 0.006   # 0.6%
        elif loan_type == 'education':
            # 教育贷款手续费率较低
            base_service_fee_rate = 0.002   # 0.2%
        
        # VIP客户享受优惠
        if is_vip:
            base_service_fee_rate *= 0.8  # 20%的折扣
        
        # 贷款期限对手续费的影响
        term_factor = 1.0
        if loan_term_months <= 6:
            # 极短期贷款手续费率可能更高
            term_factor = 1.2
        elif loan_term_months >= 120:
            # 长期贷款手续费率可能有优惠
            term_factor = 0.9
        
        # 计算最终手续费率
        final_service_fee_rate = base_service_fee_rate * term_factor
        
        # 设置手续费上下限
        min_service_fee = 100  # 最低手续费
        max_service_fee = 10000  # 最高手续费
        
        # 计算手续费
        service_fee = loan_amount * final_service_fee_rate
        service_fee = max(min_service_fee, min(service_fee, max_service_fee))
        
        # 根据贷款类型设置申请费
        if loan_type == 'mortgage':
            application_fee = 500
        elif loan_type == 'car':
            application_fee = 300
        elif loan_type == 'small_business':
            application_fee = 400
        else:
            application_fee = 200
        
        # VIP客户可能免申请费
        if is_vip:
            application_fee = 0
        
        # 设置提前还款违约金率
        early_repayment_penalty_rate = 0.0
        if loan_type == 'mortgage':
            # 房贷提前还款违约金通常较低
            early_repayment_penalty_rate = 0.01  # 1%
        elif loan_type == 'car':
            early_repayment_penalty_rate = 0.02  # 2%
        elif loan_type == 'personal_consumption':
            early_repayment_penalty_rate = 0.03  # 3%
        elif loan_type == 'small_business':
            early_repayment_penalty_rate = 0.02  # 2%
        
        # 设置逾期罚息率（通常是借款利率的一定倍数）
        late_payment_penalty_rate = 0.5  # 默认是借款利率的1.5倍（这里是增加的部分，即0.5）
        
        # 某些贷款可能需要保险
        insurance_fee = 0.0
        if loan_type == 'mortgage':
            # 房贷可能需要房屋保险
            insurance_fee = loan_amount * 0.001  # 0.1%
        elif loan_type == 'car':
            # 车贷通常需要车辆保险
            insurance_fee = loan_amount * 0.004  # 0.4%
        
        # 小微企业贷款可能需要担保费
        guarantee_fee = 0.0
        if loan_type == 'small_business':
            guarantee_fee = loan_amount * 0.005  # 0.5%
        
        # 更新费用字典
        fees['application_fee'] = round(application_fee, 2)
        fees['service_fee'] = round(service_fee, 2)
        fees['service_fee_rate'] = round(final_service_fee_rate, 4)
        fees['early_repayment_penalty_rate'] = round(early_repayment_penalty_rate, 4)
        fees['late_payment_penalty_rate'] = round(late_payment_penalty_rate, 4)
        fees['insurance_fee'] = round(insurance_fee, 2)
        fees['guarantee_fee'] = round(guarantee_fee, 2)
        
        return fees

    def generate_loan_parameters(self, loan_type: str, customer_data: Dict[str, Any], 
                           preferred_amount: Optional[float] = None,
                           preferred_term: Optional[int] = None) -> Dict[str, Any]:
        """
        根据客户数据和贷款类型生成完整的贷款参数集
        
        Args:
            loan_type: 贷款类型（个人消费贷、住房贷款等）
            customer_data: 客户相关数据，包括年收入、信用评分、是否VIP等
            preferred_amount: 客户偏好的贷款金额（可选）
            preferred_term: 客户偏好的贷款期限（可选）
            
        Returns:
            Dict[str, Any]: 包含所有贷款参数的字典
        """
        # 从客户数据中提取必要信息
        annual_income = customer_data.get('annual_income', 60000)
        credit_score = customer_data.get('credit_score', 700)
        is_corporate = customer_data.get('is_corporate', False)
        is_vip = customer_data.get('is_vip', False)
        
        # 生成贷款期限
        if preferred_term is not None:
            # 使用客户偏好的期限
            loan_term_months = preferred_term
        else:
            # 根据贷款类型确定合适的期限
            if loan_type == 'mortgage' and random.random() < 0.8:
                # 大部分房贷使用长期
                term_preference = 'long_term'
            elif loan_type == 'car' and random.random() < 0.7:
                # 大部分车贷使用中期
                term_preference = 'medium_term'
            elif loan_type == 'personal_consumption' and random.random() < 0.6:
                # 大部分消费贷使用短期或中期
                term_preference = random.choice(['short_term', 'medium_term'])
            else:
                # 随机选择期限偏好
                term_preference = None
            
            loan_term_months = self.select_loan_term(loan_type, term_preference)
        
        # 计算贷款金额范围
        min_amount, max_amount = self.calculate_loan_amount_range(
            loan_type, annual_income, credit_score, is_corporate)
        
        # 选择具体贷款金额
        loan_amount = self.select_loan_amount(
            loan_type, min_amount, max_amount, credit_score, preferred_amount)
        
        # 计算利率
        interest_rate = self.calculate_interest_rate(
            loan_type, credit_score, loan_amount, loan_term_months)
        
        # 选择还款方式
        repayment_method = self.select_repayment_method(
            loan_type, loan_term_months, is_corporate)
        
        # 计算还款计划
        repayment_schedule = self.calculate_repayment_schedule(
            loan_amount, interest_rate, loan_term_months, repayment_method)
        
        # 计算费用
        fees = self.calculate_loan_fees(
            loan_type, loan_amount, loan_term_months, is_vip)
        
        # 计算总还款额
        total_principal = sum(month['principal'] for month in repayment_schedule)
        total_interest = sum(month['interest'] for month in repayment_schedule)
        total_repayment = total_principal + total_interest
        
        # 构建完整的贷款参数字典
        loan_parameters = {
            'loan_type': loan_type,
            'loan_amount': loan_amount,
            'interest_rate': interest_rate,
            'loan_term_months': loan_term_months,
            'repayment_method': repayment_method,
            'annual_percentage_rate': round(interest_rate + fees['service_fee_rate'] / loan_term_months * 12, 4),  # 年化总费率
            'monthly_payment': round(repayment_schedule[0]['principal'] + repayment_schedule[0]['interest'], 2) if repayment_method in ['等额本息', '等额本金'] else None,
            'total_principal': round(total_principal, 2),
            'total_interest': round(total_interest, 2),
            'total_repayment': round(total_repayment, 2),
            'repayment_schedule': repayment_schedule,
            'fees': fees,
            # 元数据，用于记录参数生成过程
            'metadata': {
                'min_amount': min_amount,
                'max_amount': max_amount,
                'credit_score': credit_score,
                'annual_income': annual_income,
                'is_corporate': is_corporate,
                'is_vip': is_vip
            }
        }
        
        return loan_parameters