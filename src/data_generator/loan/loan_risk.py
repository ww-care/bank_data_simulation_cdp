#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
贷款风险评估模型

负责评估贷款的风险级别和相关参数。
"""

import random
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any

class LoanRiskModel:
    """
    贷款风险模型，负责计算和评估贷款的风险相关指标：
    - 违约概率评估
    - 风险等级分类
    - 风险因素分析
    - 预警指标计算
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化贷款风险模型
        
        Args:
            config: 配置参数，包含风险评估规则和阈值等
        """
        self.config = config
        
        # 从配置中获取客户信用评分分布
        self.credit_score_config = config.get('customer', {}).get('credit_score', {})
        
        # 风险等级定义
        self.risk_levels = {
            'low': 1,       # 低风险
            'medium': 2,    # 中风险
            'high': 3,      # 高风险
            'very_high': 4  # 极高风险
        }
        
        # 风险因素权重
        self.risk_factor_weights = {
            'credit_score': 0.35,       # 信用评分
            'income_debt_ratio': 0.20,  # 收入负债比
            'loan_value_ratio': 0.15,   # 贷款价值比
            'payment_history': 0.20,    # 历史还款记录
            'employment_stability': 0.10 # 就业稳定性
        }
    
    def calculate_default_probability(self, customer_data: Dict[str, Any], 
                                    loan_data: Dict[str, Any]) -> float:
        """
        计算贷款违约概率
        
        Args:
            customer_data: 客户相关数据，包括信用评分、收入、负债等
            loan_data: 贷款相关数据，包括贷款类型、金额、期限等
            
        Returns:
            float: 违约概率（0-1之间的小数）
        """
        # 从客户数据中提取风险相关因素
        credit_score = customer_data.get('credit_score', 700)
        annual_income = customer_data.get('annual_income', 60000)
        existing_debt = customer_data.get('existing_debt', 0)
        employment_years = customer_data.get('employment_years', 3)
        payment_history = customer_data.get('payment_history', [])
        is_vip = customer_data.get('is_vip', False)
        
        # 从贷款数据中提取相关信息
        loan_type = loan_data.get('loan_type', 'personal_consumption')
        loan_amount = loan_data.get('loan_amount', 100000)
        loan_term_months = loan_data.get('loan_term_months', 36)
        interest_rate = loan_data.get('interest_rate', 0.05)
        
        # 1. 信用评分影响（信用越高，风险越低）
        # 将信用评分映射到概率区间（850分为最低违约概率0.01，350分为最高违约概率0.5）
        credit_score_factor = 0.5 - min(0.49, (credit_score - 350) / 500 * 0.49)
        
        # 2. 收入负债比（包括本次贷款）
        # 假设贷款每月等额本息还款
        monthly_payment = loan_amount * (interest_rate / 12) * (1 + interest_rate / 12) ** loan_term_months / \
                        ((1 + interest_rate / 12) ** loan_term_months - 1)
        
        monthly_income = annual_income / 12
        monthly_debt = existing_debt / 12 + monthly_payment
        
        debt_to_income_ratio = monthly_debt / monthly_income if monthly_income > 0 else 1.0
        
        # 收入负债比影响
        # 正常范围：0.36以下为低风险，0.36-0.42为中风险，0.42-0.5为高风险，0.5以上为极高风险
        if debt_to_income_ratio < 0.36:
            dti_factor = 0.1
        elif debt_to_income_ratio < 0.42:
            dti_factor = 0.2
        elif debt_to_income_ratio < 0.5:
            dti_factor = 0.35
        else:
            dti_factor = 0.5
        
        # 3. 贷款价值比（贷款金额与客户年收入的比值）
        loan_to_income_ratio = loan_amount / annual_income if annual_income > 0 else 10.0
        
        # 根据不同贷款类型，设置合理的贷款收入比阈值
        if loan_type == 'mortgage':
            # 房贷通常可以接受更高的贷款收入比
            if loan_to_income_ratio < 3:
                lti_factor = 0.1
            elif loan_to_income_ratio < 5:
                lti_factor = 0.2
            elif loan_to_income_ratio < 7:
                lti_factor = 0.35
            else:
                lti_factor = 0.5
        else:
            # 其他贷款类型
            if loan_to_income_ratio < 1:
                lti_factor = 0.1
            elif loan_to_income_ratio < 2:
                lti_factor = 0.2
            elif loan_to_income_ratio < 3:
                lti_factor = 0.35
            else:
                lti_factor = 0.5
        
        # 4. 历史还款记录
        # 计算历史逾期率
        late_payments = 0
        total_payments = max(1, len(payment_history))
        
        for payment in payment_history:
            if payment.get('is_late', False):
                late_payments += 1
        
        late_payment_ratio = late_payments / total_payments
        
        # 历史还款记录影响
        if late_payment_ratio == 0:
            # 无逾期记录
            payment_history_factor = 0.05
        elif late_payment_ratio < 0.1:
            # 偶尔逾期
            payment_history_factor = 0.2
        elif late_payment_ratio < 0.2:
            # 经常逾期
            payment_history_factor = 0.35
        else:
            # 频繁逾期
            payment_history_factor = 0.5
        
        # 5. 就业稳定性
        # 根据就业年限判断
        if employment_years < 1:
            employment_factor = 0.4  # 工作不满一年风险较高
        elif employment_years < 3:
            employment_factor = 0.25
        elif employment_years < 5:
            employment_factor = 0.15
        else:
            employment_factor = 0.1  # 工作5年以上较稳定
        
        # 6. 特殊调整因素
        # VIP客户可能有额外保障
        vip_adjustment = -0.05 if is_vip else 0
        
        # 根据贷款类型调整
        loan_type_adjustment = 0
        if loan_type == 'mortgage':
            loan_type_adjustment = -0.1  # 房贷有抵押物，违约风险较低
        elif loan_type == 'car':
            loan_type_adjustment = -0.05  # 车贷有抵押物，但贬值较快
        elif loan_type == 'small_business':
            loan_type_adjustment = 0.05   # 小微企业贷款风险略高
        
        # 加权计算最终违约概率
        default_probability = (
            self.risk_factor_weights['credit_score'] * credit_score_factor +
            self.risk_factor_weights['income_debt_ratio'] * dti_factor +
            self.risk_factor_weights['loan_value_ratio'] * lti_factor +
            self.risk_factor_weights['payment_history'] * payment_history_factor +
            self.risk_factor_weights['employment_stability'] * employment_factor
        )
        
        # 应用特殊调整
        default_probability += vip_adjustment + loan_type_adjustment
        
        # 确保概率在合理范围内
        default_probability = max(0.01, min(0.95, default_probability))
        
        # 添加随机波动（±5%），使数据更自然
        random_adjustment = random.uniform(-0.05, 0.05) * default_probability
        default_probability += random_adjustment
        
        # 再次确保范围合理
        default_probability = max(0.01, min(0.95, default_probability))
        
        return round(default_probability, 4)
    
    def determine_risk_level(self, default_probability: float, loan_data: Dict[str, Any]) -> str:
        """
        根据违约概率和贷款信息确定风险等级
        
        Args:
            default_probability: 计算的违约概率
            loan_data: 贷款相关数据
            
        Returns:
            str: 风险等级（'low', 'medium', 'high', 'very_high'）
        """
        # 基础风险阈值
        thresholds = {
            'low': 0.05,      # 低于5%为低风险
            'medium': 0.15,   # 5%-15%为中风险
            'high': 0.30      # 15%-30%为高风险，高于30%为极高风险
        }
        
        # 根据贷款类型调整阈值
        loan_type = loan_data.get('loan_type', 'personal_consumption')
        loan_amount = loan_data.get('loan_amount', 100000)
        
        # 房贷通常有抵押物，风险阈值可以适当提高
        if loan_type == 'mortgage':
            thresholds['low'] = 0.08
            thresholds['medium'] = 0.18
            thresholds['high'] = 0.35
        
        # 小微企业贷款风险较高，阈值降低
        elif loan_type == 'small_business':
            thresholds['low'] = 0.04
            thresholds['medium'] = 0.12
            thresholds['high'] = 0.25
        
        # 根据贷款金额调整阈值
        # 贷款金额大，风险容忍度降低
        if loan_amount > 500000:
            thresholds['low'] = max(0.02, thresholds['low'] - 0.02)
            thresholds['medium'] = max(0.05, thresholds['medium'] - 0.02)
            thresholds['high'] = max(0.15, thresholds['high'] - 0.02)
        
        # 根据违约概率确定风险等级
        if default_probability < thresholds['low']:
            return 'low'
        elif default_probability < thresholds['medium']:
            return 'medium'
        elif default_probability < thresholds['high']:
            return 'high'
        else:
            return 'very_high'
        
    def analyze_risk_factors(self, customer_data: Dict[str, Any], 
                        loan_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        分析贷款的风险因素，识别主要风险点和影响程度
        
        Args:
            customer_data: 客户相关数据
            loan_data: 贷款相关数据
            
        Returns:
            Dict[str, Dict[str, Any]]: 风险因素分析结果，包括各因素的风险等级和描述
        """
        # 初始化风险因素结果字典
        risk_factors = {}
        
        # 从客户数据中提取风险相关因素
        credit_score = customer_data.get('credit_score', 700)
        annual_income = customer_data.get('annual_income', 60000)
        existing_debt = customer_data.get('existing_debt', 0)
        employment_years = customer_data.get('employment_years', 3)
        payment_history = customer_data.get('payment_history', [])
        
        # 从贷款数据中提取相关信息
        loan_type = loan_data.get('loan_type', 'personal_consumption')
        loan_amount = loan_data.get('loan_amount', 100000)
        loan_term_months = loan_data.get('loan_term_months', 36)
        interest_rate = loan_data.get('interest_rate', 0.05)
        
        # 1. 分析信用评分风险
        if credit_score >= 750:
            risk_level = 'low'
            description = '客户信用评分优秀，历史信用记录良好，信用风险较低。'
        elif credit_score >= 650:
            risk_level = 'medium'
            description = '客户信用评分良好，有一定的信用基础，信用风险可控。'
        elif credit_score >= 550:
            risk_level = 'high'
            description = '客户信用评分一般，可能存在不良信用记录，需要关注信用风险。'
        else:
            risk_level = 'very_high'
            description = '客户信用评分较低，信用风险明显，建议谨慎审批。'
        
        risk_factors['credit_score'] = {
            'factor_name': '信用评分',
            'value': credit_score,
            'risk_level': risk_level,
            'description': description,
            'impact': self.risk_factor_weights['credit_score']
        }
        
        # 2. 分析收入负债比风险
        # 计算月还款
        monthly_payment = loan_amount * (interest_rate / 12) * (1 + interest_rate / 12) ** loan_term_months / \
                        ((1 + interest_rate / 12) ** loan_term_months - 1)
        
        monthly_income = annual_income / 12
        monthly_debt = existing_debt / 12 + monthly_payment
        
        debt_to_income_ratio = monthly_debt / monthly_income if monthly_income > 0 else 1.0
        
        if debt_to_income_ratio < 0.36:
            risk_level = 'low'
            description = '客户收入负债比健康，有足够的收入覆盖债务，偿还能力强。'
        elif debt_to_income_ratio < 0.42:
            risk_level = 'medium'
            description = '客户收入负债比适中，收入基本能覆盖债务，偿还能力一般。'
        elif debt_to_income_ratio < 0.5:
            risk_level = 'high'
            description = '客户收入负债比偏高，债务负担较重，偿还能力受限。'
        else:
            risk_level = 'very_high'
            description = '客户收入负债比过高，债务负担严重，偿还能力不足。'
        
        risk_factors['income_debt_ratio'] = {
            'factor_name': '收入负债比',
            'value': round(debt_to_income_ratio, 2),
            'risk_level': risk_level,
            'description': description,
            'impact': self.risk_factor_weights['income_debt_ratio']
        }
        
        # 3. 分析贷款价值比风险
        loan_to_income_ratio = loan_amount / annual_income if annual_income > 0 else 10.0
        
        # 根据贷款类型设置不同的阈值
        if loan_type == 'mortgage':
            if loan_to_income_ratio < 3:
                risk_level = 'low'
                description = '贷款金额与收入比例合理，属于常规房贷范围。'
            elif loan_to_income_ratio < 5:
                risk_level = 'medium'
                description = '贷款金额与收入比例尚可接受，但已接近房贷上限。'
            elif loan_to_income_ratio < 7:
                risk_level = 'high'
                description = '贷款金额与收入比例偏高，超出常规房贷标准。'
            else:
                risk_level = 'very_high'
                description = '贷款金额与收入比例过高，明显超出客户还款能力。'
        else:
            if loan_to_income_ratio < 1:
                risk_level = 'low'
                description = '贷款金额与年收入比例合理，客户还款压力较小。'
            elif loan_to_income_ratio < 2:
                risk_level = 'medium'
                description = '贷款金额与年收入比例适中，但已增加客户财务负担。'
            elif loan_to_income_ratio < 3:
                risk_level = 'high'
                description = '贷款金额与年收入比例偏高，客户还款压力较大。'
            else:
                risk_level = 'very_high'
                description = '贷款金额与年收入比例过高，超出客户合理负担范围。'
        
        risk_factors['loan_value_ratio'] = {
            'factor_name': '贷款价值比',
            'value': round(loan_to_income_ratio, 2),
            'risk_level': risk_level,
            'description': description,
            'impact': self.risk_factor_weights['loan_value_ratio']
        }
        
        # 4. 分析历史还款记录风险
        # 计算历史逾期率
        late_payments = 0
        total_payments = max(1, len(payment_history))
        
        for payment in payment_history:
            if payment.get('is_late', False):
                late_payments += 1
        
        late_payment_ratio = late_payments / total_payments
        
        if late_payment_ratio == 0:
            risk_level = 'low'
            description = '客户历史还款记录良好，无逾期情况，还款意愿强。'
        elif late_payment_ratio < 0.1:
            risk_level = 'medium'
            description = '客户历史有少量逾期记录，但总体还款意愿良好。'
        elif late_payment_ratio < 0.2:
            risk_level = 'high'
            description = '客户历史逾期次数较多，还款习惯不佳，需要关注。'
        else:
            risk_level = 'very_high'
            description = '客户历史频繁逾期，还款意愿或能力存在明显问题。'
        
        risk_factors['payment_history'] = {
            'factor_name': '历史还款记录',
            'value': round(late_payment_ratio, 2),
            'risk_level': risk_level,
            'description': description,
            'impact': self.risk_factor_weights['payment_history']
        }
        
        # 5. 分析就业稳定性风险
        if employment_years < 1:
            risk_level = 'high'
            description = '客户当前工作不满一年，就业稳定性较低，收入可能不稳定。'
        elif employment_years < 3:
            risk_level = 'medium'
            description = '客户工作年限1-3年，就业稳定性一般，收入相对稳定。'
        elif employment_years < 5:
            risk_level = 'low'
            description = '客户工作年限3-5年，就业较为稳定，收入来源可靠。'
        else:
            risk_level = 'very_low'
            description = '客户工作年限超过5年，就业十分稳定，收入来源可靠。'
        
        risk_factors['employment_stability'] = {
            'factor_name': '就业稳定性',
            'value': employment_years,
            'risk_level': risk_level,
            'description': description,
            'impact': self.risk_factor_weights['employment_stability']
        }
        
        # 6. 附加风险因素：贷款期限
        if loan_term_months <= 12:
            risk_level = 'low'
            description = '短期贷款，风险暴露时间短，市场变化影响较小。'
        elif loan_term_months <= 36:
            risk_level = 'medium'
            description = '中期贷款，风险暴露时间适中，需关注市场变化影响。'
        elif loan_term_months <= 60:
            risk_level = 'medium_high'
            description = '中长期贷款，风险暴露时间较长，市场变化可能带来不确定性。'
        else:
            risk_level = 'high'
            description = '长期贷款，风险暴露时间长，市场变化带来较大不确定性。'
        
        risk_factors['loan_term'] = {
            'factor_name': '贷款期限',
            'value': loan_term_months,
            'risk_level': risk_level,
            'description': description,
            'impact': 0.05  # 附加因素，影响权重较小
        }
        
        return risk_factors
    
    def generate_risk_warning_indicators(self, customer_data: Dict[str, Any], 
                                    loan_data: Dict[str, Any], 
                                    loan_status: str = 'repaying') -> Dict[str, Any]:
        """
        生成贷款的风险预警指标，用于贷后风险监控
        
        Args:
            customer_data: 客户相关数据
            loan_data: 贷款相关数据
            loan_status: 当前贷款状态
            
        Returns:
            Dict[str, Any]: 风险预警指标，包括预警等级和各项指标的评分
        """
        # 初始化预警指标字典
        warning_indicators = {
            'overall_warning_level': 'normal',  # 默认为正常
            'warning_score': 0,                # 预警总分
            'indicators': {}                   # 具体指标
        }
        
        # 如果贷款状态已经是逾期或违约，直接设置为高风险
        if loan_status in ['overdue', 'defaulted']:
            warning_indicators['overall_warning_level'] = 'high' if loan_status == 'overdue' else 'critical'
            warning_indicators['warning_score'] = 80 if loan_status == 'overdue' else 100
        else:
            # 从客户数据中提取风险预警相关因素
            credit_score = customer_data.get('credit_score', 700)
            annual_income = customer_data.get('annual_income', 60000)
            existing_debt = customer_data.get('existing_debt', 0)
            recent_inquiries = customer_data.get('recent_inquiries', 0)  # 最近信用查询次数
            recent_new_accounts = customer_data.get('recent_new_accounts', 0)  # 最近新开账户数
            
            # 从贷款数据中提取相关信息
            loan_amount = loan_data.get('loan_amount', 100000)
            months_since_disbursement = loan_data.get('months_since_disbursement', 0)
            payment_history = loan_data.get('payment_history', [])
            
            # 1. 还款行为异常指标
            payment_indicator = {
                'name': '还款行为',
                'status': 'normal',
                'score': 0,
                'description': ''
            }
            
            # 获取最近6期或全部历史（取较小值）的还款记录
            recent_history = payment_history[-min(6, len(payment_history)):]
            recent_late_payments = sum(1 for payment in recent_history if payment.get('is_late', False))
            
            if recent_late_payments == 0:
                payment_indicator['status'] = 'normal'
                payment_indicator['score'] = 0
                payment_indicator['description'] = '近期无逾期还款，还款行为正常。'
            elif recent_late_payments == 1:
                payment_indicator['status'] = 'attention'
                payment_indicator['score'] = 20
                payment_indicator['description'] = '近期出现1次逾期还款，需要关注。'
            elif recent_late_payments == 2:
                payment_indicator['status'] = 'warning'
                payment_indicator['score'] = 40
                payment_indicator['description'] = '近期出现2次逾期还款，显示客户还款能力可能下降。'
            else:
                payment_indicator['status'] = 'high'
                payment_indicator['score'] = 60
                payment_indicator['description'] = f'近期出现{recent_late_payments}次逾期还款，客户还款行为异常，风险明显。'
            
            warning_indicators['indicators']['payment_behavior'] = payment_indicator
            
            # 2. 信用变化指标
            credit_indicator = {
                'name': '信用状况',
                'status': 'normal',
                'score': 0,
                'description': ''
            }
            
            # 信用查询次数和新开账户数可能表明客户正在大量申请新债务
            credit_risk_score = recent_inquiries * 5 + recent_new_accounts * 10
            
            if credit_risk_score < 10:
                credit_indicator['status'] = 'normal'
                credit_indicator['score'] = 0
                credit_indicator['description'] = '客户信用状况稳定，无异常信用活动。'
            elif credit_risk_score < 20:
                credit_indicator['status'] = 'attention'
                credit_indicator['score'] = 15
                credit_indicator['description'] = '客户近期有少量信用查询或新账户，需要关注。'
            elif credit_risk_score < 30:
                credit_indicator['status'] = 'warning'
                credit_indicator['score'] = 30
                credit_indicator['description'] = '客户近期信用查询或新账户数量较多，可能增加债务负担。'
            else:
                credit_indicator['status'] = 'high'
                credit_indicator['score'] = 50
                credit_indicator['description'] = '客户近期信用活动频繁，显示可能正在大量申请新债务，风险上升。'
            
            warning_indicators['indicators']['credit_change'] = credit_indicator
            
            # 3. 收入负债变化指标
            income_debt_indicator = {
                'name': '收入负债',
                'status': 'normal',
                'score': 0,
                'description': ''
            }
            
            # 计算当前月收入和负债
            monthly_income = annual_income / 12
            monthly_debt = existing_debt / 12
            
            # 计算当前收入负债比
            current_dti = monthly_debt / monthly_income if monthly_income > 0 else 1.0
            
            # 假设我们有过去的收入负债比记录
            previous_dti = customer_data.get('previous_dti', current_dti * 0.9)  # 默认假设轻微增长
            
            # 计算变化百分比
            dti_change = (current_dti - previous_dti) / previous_dti if previous_dti > 0 else 0
            
            if dti_change < 0.1:
                income_debt_indicator['status'] = 'normal'
                income_debt_indicator['score'] = 0
                income_debt_indicator['description'] = '客户收入负债比变化不大，财务状况稳定。'
            elif dti_change < 0.2:
                income_debt_indicator['status'] = 'attention'
                income_debt_indicator['score'] = 15
                income_debt_indicator['description'] = '客户收入负债比有所上升，财务压力增加。'
            elif dti_change < 0.3:
                income_debt_indicator['status'] = 'warning'
                income_debt_indicator['score'] = 30
                income_debt_indicator['description'] = '客户收入负债比明显上升，财务状况恶化。'
            else:
                income_debt_indicator['status'] = 'high'
                income_debt_indicator['score'] = 50
                income_debt_indicator['description'] = '客户收入负债比大幅上升，财务风险显著增加。'
            
            warning_indicators['indicators']['income_debt_change'] = income_debt_indicator
            
            # 4. 外部经济环境指标（简化处理）
            economy_indicator = {
                'name': '经济环境',
                'status': 'normal',
                'score': 0,
                'description': ''
            }
            
            # 这里简化处理，实际应考虑失业率、GDP增长等宏观指标
            # 随机生成一个经济环境指标，实际应该从外部数据源获取
            economy_risk = random.uniform(0, 0.3)
            
            if economy_risk < 0.1:
                economy_indicator['status'] = 'normal'
                economy_indicator['score'] = 0
                economy_indicator['description'] = '当前经济环境稳定，对贷款风险影响有限。'
            elif economy_risk < 0.2:
                economy_indicator['status'] = 'attention'
                economy_indicator['score'] = 10
                economy_indicator['description'] = '经济环境有波动，可能间接增加贷款风险。'
            else:
                economy_indicator['status'] = 'warning'
                economy_indicator['score'] = 20
                economy_indicator['description'] = '经济环境趋势不佳，可能显著增加贷款风险。'
            
            warning_indicators['indicators']['economy'] = economy_indicator
            
            # 5. 贷款期限风险指标
            # 贷款进行到一半之后，风险通常降低
            term_progress = months_since_disbursement / loan_data.get('loan_term_months', 36)
            
            term_indicator = {
                'name': '贷款进度',
                'status': 'normal',
                'score': 0,
                'description': ''
            }
            
            if term_progress < 0.25:
                term_indicator['status'] = 'attention'
                term_indicator['score'] = 10
                term_indicator['description'] = '贷款处于初期阶段，风险暴露时间较长。'
            elif term_progress < 0.5:
                term_indicator['status'] = 'normal'
                term_indicator['score'] = 5
                term_indicator['description'] = '贷款进度适中，风险逐步降低。'
            elif term_progress < 0.75:
                term_indicator['status'] = 'normal'
                term_indicator['score'] = 0
                term_indicator['description'] = '贷款已过半，风险明显降低。'
            else:
                term_indicator['status'] = 'normal'
                term_indicator['score'] = 0
                term_indicator['description'] = '贷款接近到期，风险较低。'
            
            warning_indicators['indicators']['term_progress'] = term_indicator
            
            # 计算总预警分数
            total_score = sum(indicator['score'] for indicator in warning_indicators['indicators'].values())
            warning_indicators['warning_score'] = total_score
            
            # 确定总体预警等级
            if total_score < 20:
                warning_indicators['overall_warning_level'] = 'normal'
            elif total_score < 40:
                warning_indicators['overall_warning_level'] = 'attention'
            elif total_score < 60:
                warning_indicators['overall_warning_level'] = 'warning'
            else:
                warning_indicators['overall_warning_level'] = 'high'
        
        return warning_indicators
    
    def is_eligible_for_approval(self, default_probability: float, risk_level: str, 
                           customer_data: Dict[str, Any], loan_data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        根据风险评估结果判断贷款是否有资格获得批准
        
        Args:
            default_probability: 违约概率
            risk_level: 风险等级
            customer_data: 客户相关数据
            loan_data: 贷款相关数据
            
        Returns:
            Tuple[bool, str, Dict[str, Any]]: 
                - 是否批准
                - 拒绝原因（如果适用）
                - a 批准的条件（如批准额度、利率调整等）
        """
        # 初始化审批结果
        is_approved = False
        rejection_reason = ""
        approval_conditions = {}
        
        # 从客户数据中提取相关信息
        credit_score = customer_data.get('credit_score', 700)
        annual_income = customer_data.get('annual_income', 60000)
        existing_debt = customer_data.get('existing_debt', 0)
        is_vip = customer_data.get('is_vip', False)
        
        # 从贷款数据中提取相关信息
        loan_type = loan_data.get('loan_type', 'personal_consumption')
        loan_amount = loan_data.get('loan_amount', 100000)
        loan_term_months = loan_data.get('loan_term_months', 36)
        interest_rate = loan_data.get('interest_rate', 0.05)
        
        # 计算月收入和月债务
        monthly_income = annual_income / 12
        monthly_debt = existing_debt / 12
        
        # 计算这笔贷款的每月还款（简化计算）
        if loan_term_months > 0 and interest_rate > 0:
            monthly_payment = loan_amount * (interest_rate / 12) * (1 + interest_rate / 12) ** loan_term_months / \
                            ((1 + interest_rate / 12) ** loan_term_months - 1)
        else:
            monthly_payment = loan_amount / loan_term_months if loan_term_months > 0 else loan_amount
        
        # 计算贷后债务收入比
        post_loan_dti = (monthly_debt + monthly_payment) / monthly_income if monthly_income > 0 else 1.0
        
        # 设置审批标准
        # 1. 基于风险等级的最高违约概率阈值
        max_default_prob = {
            'low': 0.15,       # 低风险贷款可接受最高15%违约概率
            'medium': 0.10,    # 中风险贷款可接受最高10%违约概率
            'high': 0.05,      # 高风险贷款可接受最高5%违约概率
            'very_high': 0.02  # 极高风险贷款可接受最高2%违约概率
        }
        
        # 2. 基于贷款类型的最高债务收入比阈值
        max_dti = {
            'mortgage': 0.50,            # 房贷可接受最高50%的债务收入比
            'car': 0.45,                 # 车贷可接受最高45%的债务收入比
            'personal_consumption': 0.40, # 消费贷可接受最高40%的债务收入比
            'small_business': 0.45,      # A 小微企业贷可接受最高45%的债务收入比
            'education': 0.40            # 教育贷可接受最高40%的债务收入比
        }
        
        # 3. 基于贷款类型的最低信用评分要求
        min_credit_score = {
            'mortgage': 620,            # 房贷最低信用要求
            'car': 600,                 # 车贷最低信用要求
            'personal_consumption': 580, # 消费贷最低信用要求
            'small_business': 650,      # 小微企业贷最低信用要求
            'education': 580            # 教育贷最低信用要求
        }
        
        # 针对VIP客户的调整
        if is_vip:
            # VIP客户获得更宽松的审批标准
            for key in max_default_prob:
                max_default_prob[key] += 0.03  # 提高违约概率容忍度
            
            for key in max_dti:
                max_dti[key] += 0.05  # 提高债务收入比容忍度
            
            for key in min_credit_score:
                min_credit_score[key] = max(500, min_credit_score[key] - 30)  # 降低信用分要求，但不低于500
        
        # 检查贷款申请是否符合审批标准
        # 1. 检查违约概率
        default_prob_threshold = max_default_prob.get(risk_level, 0.05)
        if default_probability > default_prob_threshold:
            is_approved = False
            rejection_reason = f"违约概率({default_probability:.2%})高于可接受阈值({default_prob_threshold:.2%})"
            return is_approved, rejection_reason, approval_conditions
        
        # 2. 检查债务收入比
        dti_threshold = max_dti.get(loan_type, 0.40)
        if post_loan_dti > dti_threshold:
            is_approved = False
            rejection_reason = f"贷后债务收入比({post_loan_dti:.2%})高于可接受阈值({dti_threshold:.2%})"
            
            # 计算可批准的最大金额
            max_affordable_payment = monthly_income * dti_threshold - monthly_debt
            
            if max_affordable_payment > 0:
                # 根据最大可承受的月还款，计算最大可贷款金额（简化计算）
                if loan_term_months > 0:
                    if interest_rate > 0:
                        max_loan_amount = max_affordable_payment * ((1 + interest_rate / 12) ** loan_term_months - 1) / \
                                        ((interest_rate / 12) * (1 + interest_rate / 12) ** loan_term_months)
                    else:
                        max_loan_amount = max_affordable_payment * loan_term_months
                else:
                    max_loan_amount = max_affordable_payment
                
                # 建议降低贷款金额
                approval_conditions['suggested_loan_amount'] = round(max_loan_amount, 2)
                approval_conditions['suggestion'] = f"建议降低贷款金额至{max_loan_amount:,.2f}元以满足债务收入比要求"
            
            return is_approved, rejection_reason, approval_conditions
        
        # 3. 检查信用评分
        credit_threshold = min_credit_score.get(loan_type, 600)
        if credit_score < credit_threshold:
            is_approved = False
            rejection_reason = f"信用评分({credit_score})低于最低要求({credit_threshold})"
            return is_approved, rejection_reason, approval_conditions
        
        # 通过基本审核标准，贷款可以批准
        is_approved = True
        
        # 设置批准条件和调整事项
        approval_conditions['approved_amount'] = loan_amount
        approval_conditions['approved_term'] = loan_term_months
        
        # 根据风险等级调整利率
        rate_adjustment = 0
        if risk_level == 'medium':
            rate_adjustment = 0.005  # 中风险上浮0.5%
        elif risk_level == 'high':
            rate_adjustment = 0.01   # 高风险上浮1%
        elif risk_level == 'very_high':
            rate_adjustment = 0.02   # 极高风险上浮2%
        
        adjusted_rate = interest_rate + rate_adjustment
        approval_conditions['approved_interest_rate'] = adjusted_rate
        
        if rate_adjustment > 0:
            approval_conditions['rate_adjustment'] = f"根据风险评估，利率上浮{rate_adjustment:.2%}"
        
        # 可能需要的额外条件
        if risk_level in ['high', 'very_high']:
            # 高风险贷款可能需要担保
            approval_conditions['requires_guarantor'] = True
            approval_conditions['requires_collateral'] = loan_type not in ['mortgage', 'car']  # 非抵押贷款可能需要额外抵押物
        
        if post_loan_dti > 0.4:
            # 债务收入比较高但尚在接受范围内，可能需要提高首付比例
            if loan_type in ['mortgage', 'car']:
                approval_conditions['suggested_down_payment'] = f"建议首付比例不低于{30 if loan_type == 'mortgage' else 20}%"
        
        return is_approved, rejection_reason, approval_conditions
    
    def generate_risk_assessment_report(self, customer_data: Dict[str, Any], 
                                   loan_data: Dict[str, Any], 
                                   is_approved: bool,
                                   approval_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成风险评估报告，包含风险分析结果和审批建议
        
        Args:
            customer_data: 客户相关数据
            loan_data: 贷款相关数据
            is_approved: 是否批准贷款
            approval_info: 审批相关信息（包括拒绝原因或批准条件）
            
        Returns:
            Dict[str, Any]: 风险评估报告
        """
        # 计算违约概率
        default_probability = self.calculate_default_probability(customer_data, loan_data)
        
        # 确定风险等级
        risk_level = self.determine_risk_level(default_probability, loan_data)
        
        # 分析风险因素
        risk_factors = self.analyze_risk_factors(customer_data, loan_data)
        
        # 获取客户基本信息
        customer_id = customer_data.get('customer_id', 'Unknown')
        customer_name = customer_data.get('name', 'Unknown')
        credit_score = customer_data.get('credit_score', 0)
        
        # 获取贷款基本信息
        loan_id = loan_data.get('loan_id', 'Unknown')
        loan_type = loan_data.get('loan_type', 'Unknown')
        loan_amount = loan_data.get('loan_amount', 0)
        loan_term_months = loan_data.get('loan_term_months', 0)
        
        # 构建报告
        report = {
            # 基本信息部分
            'report_id': f"RA-{loan_id}-{datetime.now().strftime('%Y%m%d')}",
            'report_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'customer_info': {
                'customer_id': customer_id,
                'customer_name': customer_name,
                'credit_score': credit_score
            },
            'loan_info': {
                'loan_id': loan_id,
                'loan_type': loan_type,
                'loan_amount': loan_amount,
                'loan_term_months': loan_term_months
            },
            
            # 风险评估部分
            'risk_assessment': {
                'default_probability': default_probability,
                'risk_level': risk_level,
                'risk_factors': risk_factors,
            },
            
            # 审批结果部分
            'approval_result': {
                'is_approved': is_approved,
                'rejection_reason': approval_info.get('rejection_reason', '') if not is_approved else '',
                'approval_conditions': approval_info.get('approval_conditions', {}) if is_approved else {},
                'decision_notes': []
            }
        }
        
        # 添加决策说明
        if is_approved:
            report['approval_result']['decision_notes'].append(
                f"贷款申请已批准。风险评级: {risk_level}，违约概率: {default_probability:.2%}"
            )
            
            # 添加利率调整说明
            if 'rate_adjustment' in approval_info.get('approval_conditions', {}):
                report['approval_result']['decision_notes'].append(
                    approval_info['approval_conditions']['rate_adjustment']
                )
            
            # 添加其他条件说明
            if approval_info.get('approval_conditions', {}).get('requires_guarantor', False):
                report['approval_result']['decision_notes'].append(
                    "需要提供担保人，以降低贷款风险。"
                )
            
            if approval_info.get('approval_conditions', {}).get('requires_collateral', False):
                report['approval_result']['decision_notes'].append(
                    "需要提供额外抵押物，以降低贷款风险。"
                )
            
            if 'suggested_down_payment' in approval_info.get('approval_conditions', {}):
                report['approval_result']['decision_notes'].append(
                    approval_info['approval_conditions']['suggested_down_payment']
                )
        else:
            report['approval_result']['decision_notes'].append(
                f"贷款申请被拒绝。原因: {approval_info.get('rejection_reason', '未指明')}"
            )
            
            # 添加建议（如果有）
            if 'suggestion' in approval_info:
                report['approval_result']['decision_notes'].append(
                    approval_info['suggestion']
                )
        
        # 添加风险分析摘要
        risk_summary = []
        
        # 找出最主要的风险因素（按影响排序）
        sorted_factors = sorted(
            risk_factors.items(), 
            key=lambda x: self.risk_factor_weights.get(x[0], 0) if x[1]['risk_level'] in ['high', 'very_high'] else 0,
            reverse=True
        )
        
        # 添加最重要的风险因素（最多3个）
        high_risk_factors = [f for f in sorted_factors if f[1]['risk_level'] in ['high', 'very_high']]
        for i, (factor_key, factor_data) in enumerate(high_risk_factors[:3]):
            risk_summary.append(f"风险因素 {i+1}: {factor_data['factor_name']} - {factor_data['description']}")
        
        if not high_risk_factors:
            risk_summary.append("未发现高风险因素。")
        
        report['risk_assessment']['risk_summary'] = risk_summary
        
        return report