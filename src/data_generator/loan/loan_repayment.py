#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
贷款还款行为模型

负责模拟贷款还款行为，包括正常还款、逾期和提前还款。
"""

import random
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Union
from decimal import Decimal, ROUND_HALF_UP

class LoanRepaymentModel:
    """
    贷款还款模型，负责生成和模拟贷款还款行为：
    - 还款计划生成
    - 还款行为模拟（按时还款、逾期、提前还款）
    - 还款记录生成
    - 逾期处理和计算
    """
    
    def __init__(self, config: Dict[str, Any], parameter_model=None):
        """
        初始化贷款还款模型
        
        Args:
            config: 配置参数
            parameter_model: 参数模型实例，用于计算还款相关参数
        """
        self.config = config
        self.parameter_model = parameter_model
        
        # 从配置中获取逾期概率分布
        self.overdue_probabilities = {
            'low_risk': 0.03,     # 低风险客户逾期概率
            'medium_risk': 0.08,  # 中风险客户逾期概率
            'high_risk': 0.15,    # 高风险客户逾期概率
            'very_high_risk': 0.25  # 极高风险客户逾期概率
        }
        
        # 从配置中获取逾期天数分布
        self.overdue_days_distribution = {
            'short': {'min': 1, 'max': 7, 'weight': 0.6},     # 短期逾期 (1-7天)
            'medium': {'min': 8, 'max': 30, 'weight': 0.3},   # 中期逾期 (8-30天)
            'long': {'min': 31, 'max': 90, 'weight': 0.1}     # 长期逾期 (31-90天)
        }
        
        # 从配置中获取提前还款概率分布
        self.early_repayment_probabilities = {
            'partial': 0.08,  # 部分提前还款概率
            'full': 0.03      # 全额提前还款概率
        }
        
        # 滞纳金率 (每天)
        self.late_fee_daily_rate = 0.0005  # 0.05%每天
        
        # 罚息率 (每天)
        self.penalty_interest_daily_rate = 0.0001  # 0.01%每天
    
    def generate_repayment_schedule(self, loan_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        生成贷款还款计划
        
        Args:
            loan_data: 贷款数据，包含金额、利率、期限等
            
        Returns:
            List[Dict[str, Any]]: 还款计划列表，每个元素包含期次、日期、本金、利息等信息
        """
        # 获取贷款基本信息
        loan_amount = float(loan_data.get('loan_amount', 0))
        loan_term_months = int(loan_data.get('loan_term_months', 0))
        interest_rate = float(loan_data.get('interest_rate', 0))  # 年利率
        repayment_method = loan_data.get('repayment_method', '等额本息')
        disbursement_date = loan_data.get('disbursement_date', datetime.now())
        
        # 确保有合理的值
        if loan_amount <= 0 or loan_term_months <= 0:
            raise ValueError("贷款金额和期限必须大于0")
        
        # 确定首次还款日期
        # 通常是下个月的固定日期
        repayment_day = loan_data.get('repayment_day', disbursement_date.day)
        first_payment_date = disbursement_date.replace(day=1) + timedelta(days=32)  # 下个月
        first_payment_date = first_payment_date.replace(day=min(repayment_day, 28))  # 设置为还款日
        
        # 初始化还款计划列表
        schedule = []
        
        # 根据不同的还款方式生成还款计划
        if repayment_method == '等额本息':
            schedule = self._generate_equal_installment_schedule(
                loan_amount, interest_rate, loan_term_months, first_payment_date
            )
        elif repayment_method == '等额本金':
            schedule = self._generate_equal_principal_schedule(
                loan_amount, interest_rate, loan_term_months, first_payment_date
            )
        elif repayment_method == '先息后本':
            schedule = self._generate_interest_only_schedule(
                loan_amount, interest_rate, loan_term_months, first_payment_date
            )
        elif repayment_method == '一次性还本付息':
            schedule = self._generate_balloon_payment_schedule(
                loan_amount, interest_rate, loan_term_months, first_payment_date
            )
        else:
            # 默认使用等额本息
            schedule = self._generate_equal_installment_schedule(
                loan_amount, interest_rate, loan_term_months, first_payment_date
            )
        
        # 添加贷款基本信息到每个还款计划
        for payment in schedule:
            payment['loan_id'] = loan_data.get('loan_id', '')
            payment['payment_id'] = f"PAY-{loan_data.get('loan_id', '')}-{payment['period']:03d}"
        
        return schedule
    
    def _generate_equal_installment_schedule(self, loan_amount: float, annual_interest_rate: float,
                                          loan_term_months: int, first_payment_date: datetime) -> List[Dict[str, Any]]:
        """生成等额本息还款计划"""
        # 将年利率转换为月利率
        monthly_rate = annual_interest_rate / 12
        
        # 计算每月还款额
        if monthly_rate > 0:
            # 等额本息公式：每月还款额 = 本金 × 月利率 × (1+月利率)^期限 / [(1+月利率)^期限 - 1]
            monthly_payment = loan_amount * monthly_rate * (1 + monthly_rate) ** loan_term_months / \
                           ((1 + monthly_rate) ** loan_term_months - 1)
        else:
            # 零利率情况
            monthly_payment = loan_amount / loan_term_months
        
        schedule = []
        remaining_principal = loan_amount
        
        for period in range(1, loan_term_months + 1):
            # 计算当期利息
            interest = remaining_principal * monthly_rate
            
            # 计算当期本金
            principal = monthly_payment - interest
            
            # 如果是最后一期，处理舍入误差
            if period == loan_term_months:
                principal = remaining_principal
                monthly_payment = principal + interest
            
            # 更新剩余本金
            remaining_principal -= principal
            
            # 确保剩余本金不为负
            remaining_principal = max(0, remaining_principal)
            
            # 计算还款日期
            payment_date = self._add_months(first_payment_date, period - 1)
            
            # 四舍五入到小数点后2位
            principal = self._round_amount(principal)
            interest = self._round_amount(interest)
            monthly_payment = self._round_amount(monthly_payment)
            remaining_principal = self._round_amount(remaining_principal)
            
            # 添加到还款计划
            schedule.append({
                'period': period,
                'payment_date': payment_date,
                'principal': principal,
                'interest': interest,
                'total_payment': monthly_payment,
                'remaining_principal': remaining_principal,
                'status': 'scheduled'  # 初始状态为已安排
            })
        
        return schedule
    
    def _generate_equal_principal_schedule(self, loan_amount: float, annual_interest_rate: float,
                                        loan_term_months: int, first_payment_date: datetime) -> List[Dict[str, Any]]:
        """生成等额本金还款计划"""
        # 将年利率转换为月利率
        monthly_rate = annual_interest_rate / 12
        
        # 计算每月本金
        monthly_principal = loan_amount / loan_term_months
        
        schedule = []
        remaining_principal = loan_amount
        
        for period in range(1, loan_term_months + 1):
            # 计算当期利息
            interest = remaining_principal * monthly_rate
            
            # 如果是最后一期，处理舍入误差
            if period == loan_term_months:
                monthly_principal = remaining_principal
            
            # 计算当期总还款额
            monthly_payment = monthly_principal + interest
            
            # 更新剩余本金
            remaining_principal -= monthly_principal
            
            # 确保剩余本金不为负
            remaining_principal = max(0, remaining_principal)
            
            # 计算还款日期
            payment_date = self._add_months(first_payment_date, period - 1)
            
            # 四舍五入到小数点后2位
            monthly_principal_rounded = self._round_amount(monthly_principal)
            interest = self._round_amount(interest)
            monthly_payment = self._round_amount(monthly_payment)
            remaining_principal = self._round_amount(remaining_principal)
            
            # 添加到还款计划
            schedule.append({
                'period': period,
                'payment_date': payment_date,
                'principal': monthly_principal_rounded,
                'interest': interest,
                'total_payment': monthly_payment,
                'remaining_principal': remaining_principal,
                'status': 'scheduled'  # 初始状态为已安排
            })
        
        return schedule
    
    def _generate_interest_only_schedule(self, loan_amount: float, annual_interest_rate: float,
                                      loan_term_months: int, first_payment_date: datetime) -> List[Dict[str, Any]]:
        """生成先息后本还款计划"""
        # 将年利率转换为月利率
        monthly_rate = annual_interest_rate / 12
        
        # 计算每月利息
        monthly_interest = loan_amount * monthly_rate
        
        schedule = []
        
        for period in range(1, loan_term_months + 1):
            # 计算还款日期
            payment_date = self._add_months(first_payment_date, period - 1)
            
            # 如果是最后一期，还本金；否则只还利息
            if period == loan_term_months:
                principal = loan_amount
                total_payment = loan_amount + monthly_interest
                remaining_principal = 0
            else:
                principal = 0
                total_payment = monthly_interest
                remaining_principal = loan_amount
            
            # 四舍五入到小数点后2位
            principal = self._round_amount(principal)
            monthly_interest_rounded = self._round_amount(monthly_interest)
            total_payment = self._round_amount(total_payment)
            
            # 添加到还款计划
            schedule.append({
                'period': period,
                'payment_date': payment_date,
                'principal': principal,
                'interest': monthly_interest_rounded,
                'total_payment': total_payment,
                'remaining_principal': remaining_principal,
                'status': 'scheduled'  # 初始状态为已安排
            })
        
        return schedule
    
    def _generate_balloon_payment_schedule(self, loan_amount: float, annual_interest_rate: float,
                                        loan_term_months: int, first_payment_date: datetime) -> List[Dict[str, Any]]:
        """生成一次性还本付息还款计划"""
        # 计算总利息
        total_interest = loan_amount * annual_interest_rate * loan_term_months / 12
        
        # 一次性还款金额
        total_payment = loan_amount + total_interest
        
        # 计算还款日期（期限结束日）
        payment_date = self._add_months(first_payment_date, loan_term_months - 1)
        
        # 四舍五入到小数点后2位
        loan_amount = self._round_amount(loan_amount)
        total_interest = self._round_amount(total_interest)
        total_payment = self._round_amount(total_payment)
        
        # 创建一次性还款计划
        schedule = [{
            'period': 1,
            'payment_date': payment_date,
            'principal': loan_amount,
            'interest': total_interest,
            'total_payment': total_payment,
            'remaining_principal': 0,
            'status': 'scheduled'  # 初始状态为已安排
        }]
        
        return schedule
    
    def _add_months(self, date: datetime, months: int) -> datetime:
        """添加月份到日期，处理月末问题"""
        month = date.month - 1 + months
        year = date.year + month // 12
        month = month % 12 + 1
        
        # 处理月末（例如：1月31日 + 1个月 = 2月28/29日）
        day = min(date.day, self._get_days_in_month(year, month))
        
        return date.replace(year=year, month=month, day=day)
    
    def _get_days_in_month(self, year: int, month: int) -> int:
        """获取指定年月的天数"""
        if month in [4, 6, 9, 11]:
            return 30
        elif month == 2:
            if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
                return 29
            else:
                return 28
        else:
            return 31
    
    def _round_amount(self, amount: float) -> float:
        """四舍五入金额到小数点后2位"""
        return float(Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    

    def simulate_repayment_behavior(self, loan_data: Dict[str, Any], 
                              repayment_schedule: List[Dict[str, Any]],
                              customer_data: Dict[str, Any],
                              current_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        模拟贷款还款行为，生成真实的还款记录
        
        Args:
            loan_data: 贷款数据
            repayment_schedule: 原始还款计划
            customer_data: 客户数据
            current_date: 当前日期，默认为系统当前日期
            
        Returns:
            List[Dict[str, Any]]: 模拟的实际还款记录
        """
        # 确保还款计划不为空
        if not repayment_schedule:
            return []
        
        # 如果没有提供当前日期，使用系统当前日期
        if current_date is None:
            current_date = datetime.now()
        
        # 获取贷款基本信息
        loan_id = loan_data.get('loan_id', '')
        customer_id = customer_data.get('customer_id', '')
        risk_level = loan_data.get('risk_level', 'medium')
        is_vip = customer_data.get('is_vip', False)
        
        # 复制原始还款计划以进行模拟
        simulated_payments = []
        
        # 跟踪上一次的还款状态，初始为正常
        previous_payment_status = 'normal'  # 'normal', 'overdue', 'severely_overdue'
        
        # 跟踪提前还清状态
        early_settled = False
        
        # 按期次处理每个还款
        for i, scheduled_payment in enumerate(repayment_schedule):
            period = scheduled_payment['period']
            scheduled_date = scheduled_payment['payment_date']
            scheduled_principal = scheduled_payment['principal']
            scheduled_interest = scheduled_payment['interest']
            scheduled_total = scheduled_payment['total_payment']
            
            # 仅处理截止到当前日期的还款期次
            if scheduled_date > current_date:
                # 将未到期的还款保存为计划中的状态
                payment_record = scheduled_payment.copy()
                payment_record['actual_payment_date'] = None
                payment_record['actual_payment'] = 0
                payment_record['status'] = 'scheduled'
                payment_record['is_overdue'] = False
                payment_record['days_overdue'] = 0
                payment_record['late_fee'] = 0
                payment_record['penalty_interest'] = 0
                
                simulated_payments.append(payment_record)
                continue
            
            # 检查是否已经提前还清
            if early_settled:
                # 贷款已提前结清，不再生成后续还款
                continue
            
            # 初始化支付记录
            payment_record = {
                'loan_id': loan_id,
                'payment_id': scheduled_payment['payment_id'],
                'customer_id': customer_id,
                'period': period,
                'scheduled_date': scheduled_date,
                'scheduled_principal': scheduled_principal,
                'scheduled_interest': scheduled_interest,
                'scheduled_total': scheduled_total,
                'remaining_principal_before': scheduled_payment['remaining_principal'] + scheduled_principal
            }
            
            # 1. 确定是否会发生提前还款 (全额或部分)
            early_repayment = self._determine_early_repayment(
                loan_data, customer_data, period, len(repayment_schedule)
            )
            
            # 2. 如果决定提前全额还款
            if early_repayment == 'full' and period < len(repayment_schedule):
                # 计算剩余本金和利息
                remaining_principal = sum(payment['principal'] for payment in repayment_schedule[i:])
                
                # 计算提前还款费用（通常是剩余本金的一定比例）
                early_repayment_fee = remaining_principal * loan_data.get('early_repayment_penalty', 0.01)
                early_repayment_fee = self._round_amount(early_repayment_fee)
                
                # 设置提前还款记录
                payment_record.update({
                    'is_early_repayment': True,
                    'early_repayment_type': 'full',
                    'actual_payment_date': self._generate_actual_payment_date(scheduled_date, 'early'),
                    'actual_principal': remaining_principal,
                    'actual_interest': scheduled_interest,
                    'early_repayment_fee': early_repayment_fee,
                    'actual_payment': remaining_principal + scheduled_interest + early_repayment_fee,
                    'status': 'paid',
                    'is_overdue': False,
                    'days_overdue': 0,
                    'late_fee': 0,
                    'penalty_interest': 0,
                    'payment_method': self._generate_payment_method(customer_data),
                    'remaining_principal_after': 0
                })
                
                # 标记为已提前还清
                early_settled = True
            
            # 3. 如果决定部分提前还款
            elif early_repayment == 'partial':
                # 生成部分提前还款金额（通常是剩余本金的一定比例）
                # 这里设定为剩余本金的20%-50%
                remaining_principal_before = payment_record['remaining_principal_before']
                additional_principal_ratio = random.uniform(0.2, 0.5)
                additional_principal = remaining_principal_before * additional_principal_ratio
                
                # 四舍五入到整百
                additional_principal = round(additional_principal / 100) * 100
                additional_principal = min(additional_principal, remaining_principal_before - scheduled_principal)
                
                # 确保额外本金为正数且不超过剩余本金
                additional_principal = max(0, min(additional_principal, remaining_principal_before - scheduled_principal))
                
                # 计算提前还款费用
                early_repayment_fee = additional_principal * loan_data.get('early_repayment_penalty', 0.01)
                early_repayment_fee = self._round_amount(early_repayment_fee)
                
                # 设置部分提前还款记录
                total_principal = scheduled_principal + additional_principal
                remaining_after = remaining_principal_before - total_principal
                
                payment_record.update({
                    'is_early_repayment': True,
                    'early_repayment_type': 'partial',
                    'additional_principal': additional_principal,
                    'actual_payment_date': self._generate_actual_payment_date(scheduled_date, 'early'),
                    'actual_principal': total_principal,
                    'actual_interest': scheduled_interest,
                    'early_repayment_fee': early_repayment_fee,
                    'actual_payment': total_principal + scheduled_interest + early_repayment_fee,
                    'status': 'paid',
                    'is_overdue': False,
                    'days_overdue': 0,
                    'late_fee': 0,
                    'penalty_interest': 0,
                    'payment_method': self._generate_payment_method(customer_data),
                    'remaining_principal_after': remaining_after
                })
                
                # 需要重新计算后续还款计划（实际系统中会这样做）
                # 这里简化处理，不重新计算后续还款
            
            # 4. 正常还款或逾期还款
            else:
                # 确定是否逾期及逾期天数
                is_overdue, days_overdue = self._determine_overdue(
                    loan_data, customer_data, scheduled_date, previous_payment_status
                )
                
                if is_overdue:
                    # 计算逾期费用
                    late_fee = self._calculate_late_fee(scheduled_total, days_overdue)
                    penalty_interest = self._calculate_penalty_interest(scheduled_principal, days_overdue)
                    
                    # 生成实际支付日期（逾期后的日期）
                    actual_payment_date = scheduled_date + timedelta(days=days_overdue)
                    
                    # 更新逾期状态
                    if days_overdue > 30:
                        payment_status = 'severely_overdue'
                    else:
                        payment_status = 'overdue'
                    
                    # 设置逾期还款记录
                    payment_record.update({
                        'is_early_repayment': False,
                        'actual_payment_date': actual_payment_date,
                        'actual_principal': scheduled_principal,
                        'actual_interest': scheduled_interest,
                        'late_fee': late_fee,
                        'penalty_interest': penalty_interest,
                        'actual_payment': scheduled_total + late_fee + penalty_interest,
                        'status': 'paid_late',
                        'is_overdue': True,
                        'days_overdue': days_overdue,
                        'payment_method': self._generate_payment_method(customer_data),
                        'remaining_principal_after': scheduled_payment['remaining_principal']
                    })
                else:
                    # 生成正常还款日期（可能会提前几天）
                    actual_payment_date = self._generate_actual_payment_date(scheduled_date, 'normal')
                    
                    # 设置正常还款记录
                    payment_record.update({
                        'is_early_repayment': False,
                        'actual_payment_date': actual_payment_date,
                        'actual_principal': scheduled_principal,
                        'actual_interest': scheduled_interest,
                        'late_fee': 0,
                        'penalty_interest': 0,
                        'actual_payment': scheduled_total,
                        'status': 'paid',
                        'is_overdue': False,
                        'days_overdue': 0,
                        'payment_method': self._generate_payment_method(customer_data),
                        'remaining_principal_after': scheduled_payment['remaining_principal']
                    })
                    
                    # 更新状态为正常
                    payment_status = 'normal'
                
                # 更新上一次支付状态
                previous_payment_status = payment_status
            
            # 添加到模拟还款记录
            simulated_payments.append(payment_record)
        
        return simulated_payments

    def _determine_early_repayment(self, loan_data: Dict[str, Any], 
                                customer_data: Dict[str, Any],
                                current_period: int, total_periods: int) -> Optional[str]:
        """确定是否会发生提前还款（全额或部分）"""
        # 获取基础提前还款概率
        partial_prob = self.early_repayment_probabilities.get('partial', 0.08)
        full_prob = self.early_repayment_probabilities.get('full', 0.03)
        
        # 调整因素
        
        # 1. 贷款进度因素（贷款进行到中期更容易提前还款）
        progress_ratio = current_period / total_periods
        progress_factor = 1.0
        
        if progress_ratio < 0.2:
            # 贷款初期，提前还款概率低
            progress_factor = 0.5
        elif 0.2 <= progress_ratio < 0.7:
            # 贷款中期，提前还款概率高
            progress_factor = 1.5
        else:
            # 贷款后期，全额提前还款概率高，部分提前还款概率低
            progress_factor = 0.7
            full_prob *= 2.0  # 贷款接近结束时，全额提前还款概率翻倍
        
        # 2. 客户风险等级因素
        risk_level = loan_data.get('risk_level', 'medium')
        risk_factor = {
            'low': 1.2,        # 低风险客户更可能提前还款
            'medium': 1.0,     # 中风险客户正常概率
            'high': 0.8,       # 高风险客户较少提前还款
            'very_high': 0.5   # 极高风险客户很少提前还款
        }.get(risk_level, 1.0)
        
        # 3. 贷款类型因素
        loan_type = loan_data.get('loan_type', 'personal_consumption')
        type_factor = {
            'mortgage': 1.5,    # 房贷更可能提前还款（利率调整、再融资等原因）
            'car': 1.2,         # 车贷适中可能性
            'personal_consumption': 0.8,  # 消费贷较少提前还款
            'small_business': 1.0,        # 小微企业贷款正常概率
            'education': 0.7               # 教育贷款较少提前还款
        }.get(loan_type, 1.0)
        
        # 4. VIP客户因素
        vip_factor = 1.3 if customer_data.get('is_vip', False) else 1.0
        
        # 计算最终概率
        final_partial_prob = partial_prob * progress_factor * risk_factor * type_factor * vip_factor
        final_full_prob = full_prob * progress_factor * risk_factor * type_factor * vip_factor
        
        # 确保概率不超过合理范围
        final_partial_prob = min(0.5, max(0.01, final_partial_prob))
        final_full_prob = min(0.3, max(0.005, final_full_prob))
        
        # 随机决定是否提前还款
        rand = random.random()
        
        if rand < final_full_prob:
            return 'full'
        elif rand < final_full_prob + final_partial_prob:
            return 'partial'
        else:
            return None

    def _determine_overdue(self, loan_data: Dict[str, Any], customer_data: Dict[str, Any],
                        scheduled_date: datetime, previous_status: str) -> Tuple[bool, int]:
        """确定是否逾期及逾期天数"""
        # 获取基础逾期概率
        risk_level = loan_data.get('risk_level', 'medium')
        base_overdue_prob = self.overdue_probabilities.get(f"{risk_level}_risk", 0.08)
        
        # 调整因素
        
        # 1. 上次还款状态的影响
        previous_factor = {
            'normal': 1.0,            # 上次正常还款
            'overdue': 3.0,           # 上次逾期还款，本次逾期概率增加
            'severely_overdue': 5.0   # 上次严重逾期，本次逾期概率大幅增加
        }.get(previous_status, 1.0)
        
        # 2. 客户信用评分的影响
        credit_score = customer_data.get('credit_score', 700)
        credit_factor = 1.0
        
        if credit_score >= 750:
            credit_factor = 0.5       # 高信用分，逾期概率减半
        elif credit_score < 600:
            credit_factor = 2.0       # 低信用分，逾期概率翻倍
        
        # 3. VIP客户因素
        vip_factor = 0.5 if customer_data.get('is_vip', False) else 1.0
        
        # 4. 还款金额因素（简化处理，实际系统可能基于还款额占收入比例）
        amount_factor = 1.0
        
        # 5. 季节性因素（例如年末可能逾期增加）
        month = scheduled_date.month
        seasonal_factor = 1.2 if month in [1, 12] else 1.0  # 元旦和春节前后逾期率略高
        
        # 计算最终逾期概率
        final_overdue_prob = base_overdue_prob * previous_factor * credit_factor * vip_factor * amount_factor * seasonal_factor
        
        # 确保概率在合理范围内
        final_overdue_prob = min(0.9, max(0.01, final_overdue_prob))
        
        # 随机决定是否逾期
        is_overdue = random.random() < final_overdue_prob
        
        # 如果逾期，确定逾期天数
        days_overdue = 0
        if is_overdue:
            # 根据逾期分布随机生成逾期天数
            overdue_categories = list(self.overdue_days_distribution.keys())
            overdue_weights = [self.overdue_days_distribution[cat]['weight'] for cat in overdue_categories]
            
            # 选择逾期类别
            category = random.choices(overdue_categories, weights=overdue_weights, k=1)[0]
            
            # 在所选类别范围内随机生成天数
            min_days = self.overdue_days_distribution[category]['min']
            max_days = self.overdue_days_distribution[category]['max']
            days_overdue = random.randint(min_days, max_days)
            
            # 前期状态影响逾期天数
            if previous_status == 'overdue':
                days_overdue = int(days_overdue * 1.5)  # 上次逾期，本次逾期天数可能更长
            elif previous_status == 'severely_overdue':
                days_overdue = int(days_overdue * 2.0)  # 上次严重逾期，本次逾期天数可能更长
            
            # 确保逾期天数在合理范围内
            days_overdue = min(180, max(1, days_overdue))  # 最长逾期半年，再长就是违约了
        
        return is_overdue, days_overdue

    def _generate_actual_payment_date(self, scheduled_date: datetime, payment_type: str) -> datetime:
        """生成实际的还款日期"""
        if payment_type == 'early':
            # 提前还款通常在还款日前1-10天
            days_early = random.randint(1, 10)
            return scheduled_date - timedelta(days=days_early)
        elif payment_type == 'normal':
            # 正常还款通常在还款日前后3天内
            days_offset = random.randint(-3, 0)  # 不会晚于还款日，但可能提前几天
            return scheduled_date + timedelta(days=days_offset)
        else:
            # 默认返回计划日期
            return scheduled_date

    def _calculate_late_fee(self, scheduled_amount: float, days_overdue: int) -> float:
        """计算逾期滞纳金"""
        # 滞纳金计算：本金 * 日滞纳金率 * 逾期天数
        late_fee = scheduled_amount * self.late_fee_daily_rate * days_overdue
        
        # 四舍五入到小数点后2位
        return self._round_amount(late_fee)

    def _calculate_penalty_interest(self, principal: float, days_overdue: int) -> float:
        """计算逾期罚息"""
        # 罚息计算：本金 * 日罚息率 * 逾期天数
        penalty_interest = principal * self.penalty_interest_daily_rate * days_overdue
        
        # 四舍五入到小数点后2位
        return self._round_amount(penalty_interest)

    def _generate_payment_method(self, customer_data: Dict[str, Any]) -> str:
        """生成支付方式"""
        # 基础支付方式选择概率
        payment_methods = {
            'auto_deduction': 0.5,    # 自动扣款
            'online_banking': 0.2,    # 网银支付
            'mobile_app': 0.15,       # 手机APP支付
            'counter': 0.05,          # 柜台支付
            'third_party': 0.1        # 第三方支付平台
        }
        
        # 根据客户特征调整概率
        age = customer_data.get('age', 35)
        is_vip = customer_data.get('is_vip', False)
        
        # 年轻客户更倾向于移动支付
        if age < 30:
            payment_methods['mobile_app'] *= 1.5
            payment_methods['third_party'] *= 1.3
            payment_methods['counter'] *= 0.5
        # 年长客户更倾向于柜台和自动扣款
        elif age > 60:
            payment_methods['counter'] *= 2.0
            payment_methods['mobile_app'] *= 0.7
            payment_methods['third_party'] *= 0.7
        
        # VIP客户更倾向于自动扣款
        if is_vip:
            payment_methods['auto_deduction'] *= 1.3
        
        # 归一化概率
        total = sum(payment_methods.values())
        normalized_methods = {k: v/total for k, v in payment_methods.items()}
        
        # 根据概率选择支付方式
        methods = list(normalized_methods.keys())
        weights = list(normalized_methods.values())
        
        return random.choices(methods, weights=weights, k=1)[0]
    
    def generate_overdue_report(self, loan_data: Dict[str, Any], 
                          payment_history: List[Dict[str, Any]],
                          current_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        生成逾期还款的详细报告，用于贷后管理和风险监控
        
        Args:
            loan_data: 贷款数据
            payment_history: 还款历史记录
            current_date: 当前日期，默认为系统当前日期
            
        Returns:
            Dict[str, Any]: 逾期报告数据
        """
        # 如果没有提供当前日期，使用系统当前日期
        if current_date is None:
            current_date = datetime.now()
        
        # 获取贷款基础信息
        loan_id = loan_data.get('loan_id', '')
        customer_id = loan_data.get('customer_id', '')
        loan_amount = loan_data.get('loan_amount', 0)
        loan_type = loan_data.get('loan_type', 'personal_consumption')
        
        # 初始化报告
        report = {
            'loan_id': loan_id,
            'customer_id': customer_id,
            'report_date': current_date,
            'report_id': f"OVD-{loan_id}-{current_date.strftime('%Y%m%d')}",
            'loan_info': {
                'loan_type': loan_type,
                'loan_amount': loan_amount,
                'disbursement_date': loan_data.get('disbursement_date'),
                'maturity_date': loan_data.get('maturity_date')
            },
            'overdue_summary': {},
            'overdue_history': [],
            'current_overdue': {},
            'risk_indicators': {},
            'action_recommendations': []
        }
        
        # 如果没有还款历史，返回空报告
        if not payment_history:
            report['overdue_summary'] = {
                'has_overdue': False,
                'total_overdue_count': 0,
                'max_overdue_days': 0,
                'total_late_fees': 0,
                'total_penalty_interest': 0
            }
            return report
        
        # 分析还款历史中的逾期情况
        overdue_payments = [p for p in payment_history if p.get('is_overdue', False)]
        current_payment = self._get_current_payment(payment_history, current_date)
        
        # 当前是否存在逾期
        current_overdue = False
        current_overdue_days = 0
        
        if current_payment:
            scheduled_date = current_payment.get('scheduled_date')
            if scheduled_date and scheduled_date < current_date and current_payment.get('status') in ['scheduled', 'overdue']:
                current_overdue = True
                current_overdue_days = (current_date - scheduled_date).days
        
        # 计算逾期汇总数据
        total_overdue_count = len(overdue_payments)
        max_overdue_days = max([p.get('days_overdue', 0) for p in overdue_payments], default=0)
        
        if current_overdue and current_overdue_days > max_overdue_days:
            max_overdue_days = current_overdue_days
        
        total_late_fees = sum(p.get('late_fee', 0) for p in overdue_payments)
        total_penalty_interest = sum(p.get('penalty_interest', 0) for p in overdue_payments)
        
        # 设置逾期汇总
        report['overdue_summary'] = {
            'has_overdue': total_overdue_count > 0 or current_overdue,
            'total_overdue_count': total_overdue_count,
            'max_overdue_days': max_overdue_days,
            'total_late_fees': self._round_amount(total_late_fees),
            'total_penalty_interest': self._round_amount(total_penalty_interest),
            'current_overdue': current_overdue,
            'current_overdue_days': current_overdue_days
        }
        
        # 设置逾期历史
        for payment in overdue_payments:
            report['overdue_history'].append({
                'period': payment.get('period'),
                'scheduled_date': payment.get('scheduled_date'),
                'actual_payment_date': payment.get('actual_payment_date'),
                'days_overdue': payment.get('days_overdue', 0),
                'late_fee': payment.get('late_fee', 0),
                'penalty_interest': payment.get('penalty_interest', 0),
                'total_payment': payment.get('actual_payment', 0)
            })
        
        # 如果当前存在逾期，设置当前逾期详情
        if current_overdue and current_payment:
            # 计算截至当前的滞纳金和罚息
            current_scheduled_amount = current_payment.get('scheduled_total', 0)
            current_principal = current_payment.get('scheduled_principal', 0)
            
            current_late_fee = self._calculate_late_fee(current_scheduled_amount, current_overdue_days)
            current_penalty_interest = self._calculate_penalty_interest(current_principal, current_overdue_days)
            
            report['current_overdue'] = {
                'period': current_payment.get('period'),
                'scheduled_date': current_payment.get('scheduled_date'),
                'scheduled_amount': current_scheduled_amount,
                'days_overdue': current_overdue_days,
                'current_late_fee': current_late_fee,
                'current_penalty_interest': current_penalty_interest,
                'total_due': current_scheduled_amount + current_late_fee + current_penalty_interest,
                'payment_id': current_payment.get('payment_id', '')
            }
        
        # 计算风险指标
        # 1. 逾期率 = 逾期次数 / 总还款次数
        total_payments = len([p for p in payment_history if p.get('status') != 'scheduled'])
        overdue_rate = total_overdue_count / max(1, total_payments)
        
        # 2. 平均逾期天数
        avg_overdue_days = sum(p.get('days_overdue', 0) for p in overdue_payments) / max(1, total_overdue_count)
        
        # 3. 最近3期逾期次数
        recent_payments = [p for p in payment_history if p.get('status') != 'scheduled'][-3:]
        recent_overdue_count = sum(1 for p in recent_payments if p.get('is_overdue', False))
        
        # 4. 逾期严重程度
        severity = 'none'
        if max_overdue_days > 90:
            severity = 'severe'
        elif max_overdue_days > 30:
            severity = 'high'
        elif max_overdue_days > 7:
            severity = 'medium'
        elif max_overdue_days > 0:
            severity = 'low'
        
        # 5. 逾期趋势（最近是否恶化）
        trend = 'stable'
        if recent_overdue_count > 0 and total_overdue_count > recent_overdue_count:
            # 检查最近的逾期是否比早期的更严重
            recent_overdue_days = [p.get('days_overdue', 0) for p in recent_payments if p.get('is_overdue', False)]
            earlier_overdue_days = [p.get('days_overdue', 0) for p in overdue_payments if p not in recent_payments]
            
            if recent_overdue_days and earlier_overdue_days:
                recent_avg = sum(recent_overdue_days) / len(recent_overdue_days)
                earlier_avg = sum(earlier_overdue_days) / len(earlier_overdue_days)
                
                if recent_avg > earlier_avg * 1.2:
                    trend = 'worsening'
                elif recent_avg < earlier_avg * 0.8:
                    trend = 'improving'
        elif recent_overdue_count == 0 and total_overdue_count > 0:
            trend = 'improving'
        elif current_overdue and current_overdue_days > avg_overdue_days:
            trend = 'worsening'
        
        # 6. 风险评分（简化版，实际系统可能更复杂）
        risk_score = 0
        # 基于逾期率加分
        risk_score += overdue_rate * 40
        # 基于最大逾期天数加分
        risk_score += min(40, max_overdue_days / 3)
        # 基于最近逾期情况加分
        risk_score += recent_overdue_count * 10
        # 如果当前逾期，额外加分
        if current_overdue:
            risk_score += min(10, current_overdue_days / 3)
        
        # 确保评分在0-100范围内
        risk_score = min(100, max(0, risk_score))
        
        # 风险等级
        risk_level = 'low'
        if risk_score >= 80:
            risk_level = 'critical'
        elif risk_score >= 60:
            risk_level = 'high'
        elif risk_score >= 30:
            risk_level = 'medium'
        
        report['risk_indicators'] = {
            'overdue_rate': round(overdue_rate, 2),
            'avg_overdue_days': round(avg_overdue_days, 1),
            'recent_overdue_count': recent_overdue_count,
            'severity': severity,
            'trend': trend,
            'risk_score': round(risk_score, 1),
            'risk_level': risk_level
        }
        
        # 生成行动建议
        action_recommendations = []
        
        if current_overdue:
            # 当前存在逾期
            if current_overdue_days <= 7:
                action_recommendations.append({
                    'action_type': 'contact',
                    'priority': 'medium',
                    'description': '发送短信或APP提醒，提醒客户尽快还款'
                })
            elif current_overdue_days <= 30:
                action_recommendations.append({
                    'action_type': 'contact',
                    'priority': 'high',
                    'description': '电话联系客户，了解逾期原因并催促还款'
                })
            else:
                action_recommendations.append({
                    'action_type': 'escalation',
                    'priority': 'critical',
                    'description': '启动催收流程，考虑专人上门催收'
                })
        
        if risk_level in ['high', 'critical']:
            action_recommendations.append({
                'action_type': 'risk_management',
                'priority': 'high',
                'description': '将客户列入高风险监控名单，限制新增信贷'
            })
        
        if trend == 'worsening':
            action_recommendations.append({
                'action_type': 'analysis',
                'priority': 'medium',
                'description': '分析客户还款能力变化，评估是否需要贷款重组'
            })
        
        if total_overdue_count >= 3:
            action_recommendations.append({
                'action_type': 'legal',
                'priority': 'medium',
                'description': '准备法律文件，必要时启动法律程序'
            })
        
        # 添加行动建议
        report['action_recommendations'] = action_recommendations
        
        return report

    def _get_current_payment(self, payment_history: List[Dict[str, Any]], 
                        current_date: datetime) -> Optional[Dict[str, Any]]:
        """获取当前期次的还款"""
        # 按期次排序
        sorted_payments = sorted(payment_history, key=lambda x: x.get('period', 0))
        
        # 查找当前日期对应的还款期次
        for payment in sorted_payments:
            scheduled_date = payment.get('scheduled_date')
            if scheduled_date and scheduled_date <= current_date and payment.get('status') in ['scheduled', 'overdue']:
                return payment
        
        # 如果所有期次都已还款或当前日期早于第一期，查找最近的未还款期次
        future_payments = [p for p in sorted_payments if p.get('status') == 'scheduled']
        if future_payments:
            return min(future_payments, key=lambda x: x.get('scheduled_date'))
        
        # 如果没有未来还款，返回最后一期
        if sorted_payments:
            return sorted_payments[-1]
        
        return None
    
    def generate_repayment_summary(self, loan_data: Dict[str, Any], 
                             payment_history: List[Dict[str, Any]],
                             current_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        生成贷款还款摘要报告，提供贷款还款进度和状态概览
        
        Args:
            loan_data: 贷款数据
            payment_history: 还款历史记录
            current_date: 当前日期，默认为系统当前日期
            
        Returns:
            Dict[str, Any]: 还款摘要报告
        """
        # 如果没有提供当前日期，使用系统当前日期
        if current_date is None:
            current_date = datetime.now()
        
        # 获取贷款基础信息
        loan_id = loan_data.get('loan_id', '')
        customer_id = loan_data.get('customer_id', '')
        loan_amount = loan_data.get('loan_amount', 0)
        interest_rate = loan_data.get('interest_rate', 0)
        loan_term_months = loan_data.get('loan_term_months', 0)
        disbursement_date = loan_data.get('disbursement_date', current_date)
        maturity_date = loan_data.get('maturity_date', current_date)
        
        # 初始化摘要
        summary = {
            'loan_id': loan_id,
            'customer_id': customer_id,
            'summary_date': current_date,
            'loan_status': 'active',
            'loan_info': {
                'loan_amount': loan_amount,
                'interest_rate': interest_rate,
                'loan_term_months': loan_term_months,
                'disbursement_date': disbursement_date,
                'maturity_date': maturity_date,
                'loan_age_days': (current_date - disbursement_date).days,
                'remaining_term_days': max(0, (maturity_date - current_date).days)
            },
            'payment_progress': {},
            'financial_summary': {},
            'recent_payments': [],
            'next_payment': {}
        }
        
        # 如果没有还款历史，返回基础摘要
        if not payment_history:
            summary['payment_progress'] = {
                'total_payments': 0,
                'completed_payments': 0,
                'progress_percentage': 0,
                'overdue_payments': 0
            }
            
            summary['financial_summary'] = {
                'total_paid_principal': 0,
                'total_paid_interest': 0,
                'total_paid_fees': 0,
                'total_paid_amount': 0,
                'remaining_principal': loan_amount,
                'remaining_interest': 0,
                'estimated_total_interest': 0
            }
            
            return summary
        
        # 计算付款进度
        total_payments = len(payment_history)
        completed_payments = len([p for p in payment_history if p.get('status') in ['paid', 'paid_late']])
        overdue_payments = len([p for p in payment_history if p.get('is_overdue', False)])
        
        # 查找当前是否存在逾期
        current_payment = self._get_current_payment(payment_history, current_date)
        current_overdue = False
        current_overdue_days = 0
        
        if current_payment:
            scheduled_date = current_payment.get('scheduled_date')
            if scheduled_date and scheduled_date < current_date and current_payment.get('status') in ['scheduled', 'overdue']:
                current_overdue = True
                current_overdue_days = (current_date - scheduled_date).days
        
        # 计算进度百分比
        progress_percentage = (completed_payments / max(1, total_payments)) * 100
        
        # 计算贷款状态
        if current_overdue and current_overdue_days > 90:
            loan_status = 'defaulted'  # 逾期超过90天视为违约
        elif current_overdue:
            loan_status = 'overdue'    # 当前存在逾期
        elif all(p.get('status') in ['paid', 'paid_late'] for p in payment_history):
            loan_status = 'completed'  # 所有还款已完成
        else:
            loan_status = 'active'     # 正常进行中
        
        # 设置付款进度
        summary['payment_progress'] = {
            'total_payments': total_payments,
            'completed_payments': completed_payments,
            'progress_percentage': round(progress_percentage, 1),
            'overdue_payments': overdue_payments,
            'current_overdue': current_overdue,
            'current_overdue_days': current_overdue_days
        }
        
        # 计算财务摘要
        paid_principal = sum(p.get('actual_principal', 0) for p in payment_history if p.get('status') in ['paid', 'paid_late'])
        paid_interest = sum(p.get('actual_interest', 0) for p in payment_history if p.get('status') in ['paid', 'paid_late'])
        paid_fees = sum((p.get('late_fee', 0) + p.get('penalty_interest', 0) + p.get('early_repayment_fee', 0)) 
                    for p in payment_history if p.get('status') in ['paid', 'paid_late'])
        
        # 计算总支付金额
        total_paid = paid_principal + paid_interest + paid_fees
        
        # 计算剩余本金
        remaining_principal = loan_amount - paid_principal
        
        # 计算总利息（已付+预估剩余）
        # 对于已支付部分，使用实际数值；对于未支付部分，使用预估值
        unpaid_payments = [p for p in payment_history if p.get('status') not in ['paid', 'paid_late']]
        remaining_interest = sum(p.get('scheduled_interest', 0) for p in unpaid_payments)
        
        total_interest = paid_interest + remaining_interest
        
        # 设置财务摘要
        summary['financial_summary'] = {
            'total_paid_principal': self._round_amount(paid_principal),
            'total_paid_interest': self._round_amount(paid_interest),
            'total_paid_fees': self._round_amount(paid_fees),
            'total_paid_amount': self._round_amount(total_paid),
            'remaining_principal': self._round_amount(remaining_principal),
            'remaining_interest': self._round_amount(remaining_interest),
            'estimated_total_interest': self._round_amount(total_interest),
            'loan_to_interest_ratio': round(loan_amount / (total_interest or 1), 2)
        }
        
        # 更新贷款状态
        summary['loan_status'] = loan_status
        
        # 添加最近付款
        recent_payments = sorted(
            [p for p in payment_history if p.get('status') in ['paid', 'paid_late']], 
            key=lambda x: x.get('actual_payment_date', datetime.min), 
            reverse=True
        )[:3]  # 最近3笔还款
        
        for payment in recent_payments:
            summary['recent_payments'].append({
                'period': payment.get('period'),
                'payment_date': payment.get('actual_payment_date'),
                'amount': payment.get('actual_payment', 0),
                'is_overdue': payment.get('is_overdue', False),
                'payment_method': payment.get('payment_method', '')
            })
        
        # 添加下一次还款信息
        next_payment = None
        future_payments = [p for p in payment_history if p.get('status') == 'scheduled']
        
        if future_payments:
            next_payment = min(future_payments, key=lambda x: x.get('scheduled_date', datetime.max))
        
        if next_payment:
            days_until_next = max(0, (next_payment.get('scheduled_date', current_date) - current_date).days)
            
            summary['next_payment'] = {
                'period': next_payment.get('period'),
                'scheduled_date': next_payment.get('scheduled_date'),
                'amount': next_payment.get('scheduled_total', 0),
                'days_until_due': days_until_next,
                'payment_id': next_payment.get('payment_id', '')
            }
        
        # 添加提前还清分析
        if loan_status == 'active' and remaining_principal > 0:
            # 简化计算：假设提前还清只需支付剩余本金和一定比例的违约金
            early_settlement_fee = remaining_principal * loan_data.get('early_repayment_penalty', 0.01)
            early_settlement_amount = remaining_principal + early_settlement_fee
            
            savings = remaining_interest - early_settlement_fee
            
            summary['early_settlement_analysis'] = {
                'remaining_principal': self._round_amount(remaining_principal),
                'early_settlement_fee': self._round_amount(early_settlement_fee),
                'early_settlement_amount': self._round_amount(early_settlement_amount),
                'potential_interest_savings': self._round_amount(max(0, savings)),
                'is_beneficial': savings > 0
            }
        
        return summary