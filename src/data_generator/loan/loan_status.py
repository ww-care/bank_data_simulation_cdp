#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
贷款状态转换模型

负责管理贷款的状态变化和生命周期。
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Set

class LoanStatusModel:
    """
    贷款状态模型，负责管理贷款状态的转换和状态相关的业务逻辑：
    - 贷款状态定义
    - 状态转换规则
    - 状态转换条件
    - 状态持续时间计算
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化贷款状态模型
        
        Args:
            config: 配置参数，包含状态转换规则和概率等
        """
        self.config = config
        
        # 定义所有可能的贷款状态
        self.loan_statuses = [
            'applying',      # 申请中
            'approved',      # 已批准
            'rejected',      # 拒绝
            'disbursed',     # 已放款
            'repaying',      # 还款中
            'overdue',       # 逾期
            'defaulted',     # 违约
            'settled',       # 已结清
            'early_settled'  # 提前结清
        ]
        
        # 从配置中获取状态分布（如果存在）
        self.status_distribution = config.get('loan', {}).get(
            'status_distribution', {
                'applying': 0.06,       # 申请中
                'approved': 0.04,       # 已批准
                'disbursed': 0.04,      # 已放款
                'repaying': 0.75,       # 还款中
                'settled': 0.07,        # 已结清
                'overdue': 0.03,        # 逾期
                'rejected': 0.01,       # 拒绝
            }
        )
        
        # 定义状态转换规则（从哪些状态可以转到哪些状态）
        self.state_transitions = {
            'applying': {'approved', 'rejected'},
            'approved': {'disbursed', 'rejected'},  # 批准后也可能因某些原因被拒绝
            'disbursed': {'repaying'},
            'repaying': {'overdue', 'settled', 'early_settled'},
            'overdue': {'repaying', 'defaulted', 'settled'},
            'defaulted': {'settled'},  # 违约后可以通过协商或催收最终结清
            'settled': set(),  # 终态，无后续转换
            'early_settled': set(),  # 终态，无后续转换
            'rejected': set()  # 终态，无后续转换
        }
    
    def get_initial_status(self, loan_type: str, credit_score: int, 
                          is_historical: bool = True) -> str:
        """
        获取贷款的初始状态，用于生成历史数据或新申请
        
        Args:
            loan_type: 贷款类型
            credit_score: 客户信用评分
            is_historical: 是否为历史数据生成（对于历史数据，通常直接生成后期状态）
            
        Returns:
            str: 初始贷款状态
        """
        if not is_historical:
            # 对于非历史数据（如实时生成），几乎总是从申请开始
            return 'applying'
            
        # 对于历史数据，根据配置的分布随机选择一个状态
        # 首先，提取状态和对应的概率
        statuses = list(self.status_distribution.keys())
        probabilities = list(self.status_distribution.values())
        
        # 确保概率总和为1
        prob_sum = sum(probabilities)
        if prob_sum > 0:
            probabilities = [p/prob_sum for p in probabilities]
        
        # 随机选择一个状态
        status = random.choices(statuses, weights=probabilities, k=1)[0]
        
        # 信用评分对初始状态的影响（高信用分不太可能是逾期或拒绝状态）
        if status in ['overdue', 'defaulted'] and credit_score > 700:
            # 高信用分客户，有80%概率不会是逾期或违约状态
            if random.random() < 0.8:
                # 改为还款中状态
                status = 'repaying'
                
        if status == 'rejected' and credit_score > 650:
            # 较高信用分客户，有90%概率不会是拒绝状态
            if random.random() < 0.9:
                # 改为批准或还款中状态
                status = random.choice(['approved', 'repaying'])
                
        # 根据贷款类型调整概率（例如，住房贷款可能有更低的拒绝率）
        if loan_type == 'mortgage' and status == 'rejected':
            # 房贷拒绝率较低
            if random.random() < 0.7:
                status = random.choice(['approved', 'repaying'])
        
        return status
    
    def get_possible_next_statuses(self, current_status: str, loan_data: Dict[str, Any]) -> Dict[str, float]:
        """
        获取当前状态可能转换到的下一个状态及其概率
        
        Args:
            current_status: 当前贷款状态
            loan_data: 贷款相关数据，包括贷款类型、金额、客户信用评分等
            
        Returns:
            Dict[str, float]: 可能的下一个状态及其概率字典
        """
        # 获取该状态允许的转换目标状态集合
        allowed_next_statuses = self.state_transitions.get(current_status, set())
        
        # 如果当前状态是终态或没有可用的下一状态，返回空字典
        if not allowed_next_statuses:
            return {}
        
        # 从贷款数据中提取可能影响转换概率的因素
        loan_type = loan_data.get('loan_type', 'personal_consumption')
        credit_score = loan_data.get('credit_score', 700)
        loan_amount = loan_data.get('loan_amount', 100000)
        repayment_method = loan_data.get('repayment_method', '等额本息')
        loan_term_months = loan_data.get('loan_term_months', 36)
        months_since_disbursement = loan_data.get('months_since_disbursement', 0)
        payment_history = loan_data.get('payment_history', [])  # 历史还款记录
        
        # 初始化概率字典
        probabilities = {status: 0.0 for status in allowed_next_statuses}
        
        # 根据当前状态设置基础转换概率
        if current_status == 'applying':
            # 申请 -> 批准/拒绝
            # 基础批准率基于信用评分
            approve_prob = self._calculate_approval_probability(credit_score, loan_type, loan_amount)
            probabilities['approved'] = approve_prob
            probabilities['rejected'] = 1.0 - approve_prob
        
        elif current_status == 'approved':
            # 批准 -> 放款/拒绝
            # 批准后大多会进入放款状态，少数因客户放弃或其他原因被拒
            probabilities['disbursed'] = 0.95
            probabilities['rejected'] = 0.05
        
        elif current_status == 'disbursed':
            # 放款 -> 还款中
            # 放款后必然进入还款阶段
            probabilities['repaying'] = 1.0
        
        elif current_status == 'repaying':
            # 还款中 -> 逾期/结清/提前结清
            # 基础逾期概率基于信用评分和贷款已进行时间
            overdue_prob = self._calculate_overdue_probability(
                credit_score, loan_type, months_since_disbursement, payment_history)
            
            # 计算提前结清的概率
            early_settle_prob = self._calculate_early_settlement_probability(
                loan_type, loan_term_months, months_since_disbursement, repayment_method)
            
            # 计算正常结清的概率（如果贷款接近到期）
            normal_settle_prob = 0.0
            if months_since_disbursement >= loan_term_months - 1:
                # 最后一个月有很高概率正常结清
                normal_settle_prob = 0.8
            elif months_since_disbursement >= loan_term_months - 3:
                # 接近到期时有一定概率结清
                normal_settle_prob = 0.4
            
            # 确保概率总和不超过1
            remaining_prob = 1.0 - min(1.0, overdue_prob + early_settle_prob + normal_settle_prob)
            if remaining_prob < 0:
                # 调整各概率，确保总和为1
                total = overdue_prob + early_settle_prob + normal_settle_prob
                overdue_prob = overdue_prob / total
                early_settle_prob = early_settle_prob / total
                normal_settle_prob = normal_settle_prob / total
                remaining_prob = 0
            
            # 分配概率
            probabilities['overdue'] = overdue_prob
            probabilities['early_settled'] = early_settle_prob
            probabilities['settled'] = normal_settle_prob
            
            # 剩余概率表示继续保持还款中状态
            if 'repaying' in probabilities:
                probabilities['repaying'] = remaining_prob
        
        elif current_status == 'overdue':
            # 逾期 -> 还款中/违约/结清
            # 拖欠时间和金额影响违约概率
            overdue_months = loan_data.get('overdue_months', 1)
            overdue_amount = loan_data.get('overdue_amount', 0)
            
            # 计算违约概率
            default_prob = self._calculate_default_probability(
                overdue_months, overdue_amount, credit_score, loan_amount)
            
            # 计算恢复正常还款的概率
            recover_prob = 0.4 - min(0.3, overdue_months * 0.1)  # 逾期时间越长，恢复概率越低
            recover_prob = max(0.1, recover_prob)  # 但仍有最低10%的恢复概率
            
            # 一次性结清逾期贷款的概率
            settle_prob = 0.05
            
            # 确保概率总和不超过1
            total_prob = default_prob + recover_prob + settle_prob
            if total_prob > 1.0:
                # 按比例调整
                default_prob = default_prob / total_prob
                recover_prob = recover_prob / total_prob
                settle_prob = settle_prob / total_prob
            
            probabilities['defaulted'] = default_prob
            probabilities['repaying'] = recover_prob
            probabilities['settled'] = settle_prob
        
        elif current_status == 'defaulted':
            # 违约 -> 结清
            # 违约后仍有小概率通过催收等方式结清
            probabilities['settled'] = 0.05  # 每个月有5%的概率结清
        
        # 移除概率为0的状态
        probabilities = {k: v for k, v in probabilities.items() if v > 0}
        
        return probabilities

    def _calculate_approval_probability(self, credit_score: int, loan_type: str, loan_amount: float) -> float:
        """计算贷款批准概率"""
        # 基础批准率基于信用评分
        # 假设信用评分范围为350-850，映射到概率范围0.2-0.95
        base_prob = 0.2 + (credit_score - 350) / 500 * 0.75
        
        # 根据贷款类型调整
        type_factor = 1.0
        if loan_type == 'mortgage':
            # 房贷通常审批较严格但批准率较高（对于合格申请人）
            type_factor = 1.1
        elif loan_type == 'car':
            # 车贷相对容易获批
            type_factor = 1.05
        elif loan_type == 'personal_consumption':
            # 消费贷相对更加宽松
            type_factor = 1.0
        elif loan_type == 'small_business':
            # 小微企业贷款审批较严格
            type_factor = 0.9
        
        # 根据贷款金额调整，金额越大，审批越严格
        amount_factor = 1.0
        if loan_type == 'mortgage':
            if loan_amount > 1000000:
                amount_factor = 0.9
        elif loan_type == 'personal_consumption':
            if loan_amount > 200000:
                amount_factor = 0.85
        
        # 计算最终概率
        final_prob = base_prob * type_factor * amount_factor
        
        # 确保概率在有效范围内
        return max(0.1, min(0.95, final_prob))

    def _calculate_overdue_probability(self, credit_score: int, loan_type: str, 
                                    months_since_disbursement: int, payment_history: List[Any]) -> float:
        """计算贷款逾期概率"""
        # 基础逾期率基于信用评分的反比（信用越高逾期率越低）
        # 假设信用评分范围为350-850，映射到逾期率范围0.3-0.01
        base_prob = 0.3 - (credit_score - 350) / 500 * 0.29
        
        # 根据贷款类型调整
        type_factor = 1.0
        if loan_type == 'mortgage':
            # 房贷逾期率较低
            type_factor = 0.7
        elif loan_type == 'car':
            # 车贷逾期率适中
            type_factor = 0.9
        elif loan_type == 'personal_consumption':
            # 消费贷逾期率较高
            type_factor = 1.2
        
        # 根据贷款已经进行的时间调整
        # 中间阶段逾期率可能更高，初期和接近结束时较低
        time_factor = 1.0
        if months_since_disbursement < 3:
            # 初期逾期率低
            time_factor = 0.7
        elif months_since_disbursement < 6:
            # 3-6个月逾期率升高
            time_factor = 1.1
        elif months_since_disbursement > 24:
            # 长期正常还款后逾期率降低
            time_factor = 0.8
        
        # 根据历史付款记录调整
        payment_factor = 1.0
        if payment_history:
            # 计算历史逾期率
            late_payments = sum(1 for payment in payment_history if payment.get('is_late', False))
            if late_payments > 0:
                # 有过逾期，提高未来逾期概率
                payment_factor = 1.0 + min(1.0, late_payments / len(payment_history) * 2)
        
        # 计算最终概率
        final_prob = base_prob * type_factor * time_factor * payment_factor
        
        # 确保概率在有效范围内
        return max(0.01, min(0.5, final_prob))

    def _calculate_early_settlement_probability(self, loan_type: str, loan_term_months: int, 
                                            months_since_disbursement: int, repayment_method: str) -> float:
        """计算提前结清概率"""
        # 基础提前结清概率
        base_prob = 0.01  # 每月1%的基础提前结清概率
        
        # 根据贷款类型调整
        type_factor = 1.0
        if loan_type == 'mortgage':
            # 房贷提前结清较常见，特别是利率下行时
            type_factor = 1.5
        elif loan_type == 'car':
            # 车贷提前结清适中
            type_factor = 1.2
        elif loan_type == 'personal_consumption':
            # 消费贷提前结清少见
            type_factor = 0.8
        
        # 根据贷款已进行时间调整
        # 贷款中期提前结清概率最高
        time_factor = 1.0
        loan_progress = months_since_disbursement / loan_term_months
        
        if loan_progress < 0.25:
            # 贷款初期提前结清概率低
            time_factor = 0.5
        elif 0.25 <= loan_progress < 0.75:
            # 贷款中期提前结清概率高
            time_factor = 1.5
        else:
            # 接近到期时提前结清概率降低
            time_factor = 0.7
        
        # 根据还款方式调整
        method_factor = 1.0
        if repayment_method == '等额本息':
            # 等额本息提前结清较常见（为了减少总利息）
            method_factor = 1.2
        elif repayment_method == '先息后本':
            # 先息后本贷款在本金到期前提前结清意义不大
            method_factor = 0.7
        
        # 计算最终概率
        final_prob = base_prob * type_factor * time_factor * method_factor
        
        # 确保概率在有效范围内
        return max(0.001, min(0.1, final_prob))

    def _calculate_default_probability(self, overdue_months: int, overdue_amount: float, 
                                    credit_score: int, loan_amount: float) -> float:
        """计算违约概率"""
        # 基础违约概率基于逾期时间
        if overdue_months <= 1:
            base_prob = 0.05  # 逾期1个月内违约概率较低
        elif overdue_months <= 3:
            base_prob = 0.15  # 逾期1-3个月违约概率增加
        elif overdue_months <= 6:
            base_prob = 0.30  # 逾期3-6个月违约概率较高
        else:
            base_prob = 0.50  # 逾期超过6个月违约概率很高
        
        # 根据逾期金额与贷款总额比例调整
        amount_ratio = min(1.0, overdue_amount / loan_amount)
        amount_factor = 0.5 + amount_ratio * 0.5  # 0.5-1.0
        
        # 根据信用评分调整
        # 高信用分客户即使逾期，也更有可能恢复还款
        credit_factor = 1.0 - (credit_score - 350) / 500 * 0.5  # 0.5-1.0
        
        # 计算最终概率
        final_prob = base_prob * amount_factor * credit_factor
        
        # 确保概率在有效范围内
        return max(0.01, min(0.95, final_prob))
    
    def calculate_status_duration(self, status: str, loan_data: Dict[str, Any]) -> int:
        """
        计算贷款状态的持续时间（天数）
        
        Args:
            status: 贷款状态
            loan_data: 贷款相关数据，包括贷款类型、金额、期限等
            
        Returns:
            int: 状态持续的天数
        """
        # 从贷款数据中提取可能影响状态持续时间的因素
        loan_type = loan_data.get('loan_type', 'personal_consumption')
        loan_amount = loan_data.get('loan_amount', 100000)
        loan_term_months = loan_data.get('loan_term_months', 36)
        
        # 根据不同状态计算合理的持续时间
        if status == 'applying':
            # 申请阶段的持续时间，通常从几小时到几天不等
            # 这里我们使用天作为单位，小额贷款处理更快
            if loan_type == 'personal_consumption' and loan_amount < 50000:
                # 小额消费贷审批快
                min_days, max_days = 1, 3
            elif loan_type == 'mortgage':
                # 房贷审批时间较长
                min_days, max_days = 5, 14
            elif loan_type == 'car':
                # 车贷审批时间适中
                min_days, max_days = 2, 7
            elif loan_type == 'small_business':
                # 小微企业贷款审批时间较长
                min_days, max_days = 3, 10
            else:
                # 默认审批时间
                min_days, max_days = 2, 5
            
            # 贷款金额对审批时间的影响
            if loan_amount > 500000:
                max_days += 3  # 大额贷款审批时间延长
            
            # 返回在范围内的随机天数
            return random.randint(min_days, max_days)
        
        elif status == 'approved':
            # 批准到放款的时间，通常也是几天
            if loan_type == 'mortgage':
                # 房贷放款时间较长
                min_days, max_days = 3, 10
            elif loan_type == 'car':
                # 车贷放款相对快些
                min_days, max_days = 1, 5
            else:
                # 其他类型贷款
                min_days, max_days = 1, 3
            
            return random.randint(min_days, max_days)
        
        elif status == 'disbursed':
            # 放款到开始还款的时间，通常是很短的
            # 大多数情况下当天或第二天就开始计入还款状态
            return random.randint(1, 2)
        
        elif status == 'repaying':
            # 还款状态的持续时间，通常是整个贷款期限（扣除已经经过的时间）
            months_elapsed = loan_data.get('months_since_disbursement', 0)
            remaining_months = max(1, loan_term_months - months_elapsed)
            
            # 返回剩余月数对应的天数（简化处理，按30天/月计算）
            return remaining_months * 30
        
        elif status == 'overdue':
            # 逾期状态持续时间，取决于客户补救措施和银行催收效果
            # 通常从几天到几个月不等
            credit_score = loan_data.get('credit_score', 700)
            
            # 信用分较高的客户，逾期时间可能较短（更快解决逾期问题）
            if credit_score > 750:
                min_days, max_days = 5, 30
            elif credit_score > 650:
                min_days, max_days = 10, 60
            else:
                min_days, max_days = 15, 90
            
            # 贷款金额对逾期时间的影响
            if loan_amount > 200000:
                max_days += 30  # 大额贷款逾期时间可能更长
            
            return random.randint(min_days, max_days)
        
        elif status == 'defaulted':
            # 违约状态通常会持续较长时间，直到债务重组或核销
            # 这里简化处理，设定一个较长的随机时间
            return random.randint(180, 365)
        
        elif status in ['settled', 'early_settled', 'rejected']:
            # 这些状态是终态，不需要计算持续时间
            # 但为了数据完整性，设置一个象征性的持续天数
            return 1
        
        # 默认返回一个合理的天数
        return random.randint(1, 30)

    def generate_status_timeline(self, initial_status: str, start_date: datetime,
                           loan_data: Dict[str, Any], is_historical: bool = True) -> List[Dict[str, Any]]:
        """
        生成贷款状态的时间线，模拟贷款从初始状态到最终状态的转换过程
        
        Args:
            initial_status: 初始贷款状态
            start_date: 贷款初始状态的起始日期
            loan_data: 贷款相关数据，包括贷款类型、金额、期限等
            is_historical: 是否为历史数据生成（影响是否生成完整的状态序列）
            
        Returns:
            List[Dict[str, Any]]: 贷款状态变化序列，每个元素包含状态、开始时间、结束时间等信息
        """
        # 定义结果列表
        timeline = []
        
        # 定义最终状态（到达这些状态后停止生成）
        final_statuses = {'settled', 'early_settled', 'rejected', 'defaulted'}
        
        # 如果是历史数据且初始状态已经是最终状态，直接返回该状态
        if is_historical and initial_status in final_statuses:
            duration_days = self.calculate_status_duration(initial_status, loan_data)
            end_date = start_date + timedelta(days=duration_days)
            
            timeline.append({
                'status': initial_status,
                'start_date': start_date,
                'end_date': end_date,
                'duration_days': duration_days
            })
            
            return timeline
    
        # 当前状态和时间
        current_status = initial_status
        current_date = start_date
        
        # 访问过的状态集合（防止状态循环）
        visited_statuses = {current_status}
        
        # 设置最大状态转换次数（避免无限循环）
        max_transitions = 10
        
        # 通过循环模拟状态转换
        for _ in range(max_transitions):
            # 计算当前状态的持续时间
            duration_days = self.calculate_status_duration(current_status, loan_data)
            
            # 如果是"还款中"状态，并且不是从历史数据生成的完整贷款周期
            # 则可能提前结束时间线（避免生成整个贷款期限的详细状态）
            if current_status == 'repaying' and is_historical and random.random() < 0.7:
                # 对于历史数据，通常不需要生成整个还款期的状态变化
                # 这里对于"还款中"状态特殊处理，可能提前结束
                end_date = current_date + timedelta(days=min(duration_days, random.randint(30, 180)))
            else:
                end_date = current_date + timedelta(days=duration_days)
            
            # 添加当前状态到时间线
            timeline.append({
                'status': current_status,
                'start_date': current_date,
                'end_date': end_date,
                'duration_days': (end_date - current_date).days
            })
            
            # 如果当前状态是最终状态，结束生成
            if current_status in final_statuses:
                break
                
            # 如果当前状态是"还款中"且是历史数据生成，可能提前结束
            if current_status == 'repaying' and is_historical and len(timeline) > 1:
                if random.random() < 0.5:  # 50%的概率提前结束
                    break
            
            # 获取可能的下一个状态及其概率
            next_status_probs = self.get_possible_next_statuses(current_status, loan_data)
            
            # 如果没有下一个状态，或者所有可能的下一个状态已经访问过，结束生成
            if not next_status_probs or all(s in visited_statuses for s in next_status_probs.keys()):
                break
            
            # 选择下一个状态
            statuses = list(next_status_probs.keys())
            probabilities = list(next_status_probs.values())
            
            # 确保概率总和为1
            total_prob = sum(probabilities)
            if total_prob > 0:
                probabilities = [p/total_prob for p in probabilities]
                next_status = random.choices(statuses, weights=probabilities, k=1)[0]
            else:
                # 如果无法根据概率选择，随机选择一个未访问的状态
                unvisited_statuses = [s for s in statuses if s not in visited_statuses]
                if unvisited_statuses:
                    next_status = random.choice(unvisited_statuses)
                else:
                    # 如果所有状态都已访问，随机选择一个
                    next_status = random.choice(statuses)
            
            # 更新当前状态和时间
            current_status = next_status
            current_date = end_date
            
            # 更新已访问状态集合
            visited_statuses.add(current_status)
            
            # 更新贷款数据以反映状态变化
            loan_data = self._update_loan_data_for_next_status(loan_data, current_status, timeline)
        
        return timeline

    def _update_loan_data_for_next_status(self, loan_data: Dict[str, Any], 
                                        next_status: str, timeline: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        根据下一个状态更新贷款数据，以便在计算状态概率和持续时间时使用
        
        Args:
            loan_data: 当前贷款数据
            next_status: 下一个状态
            timeline: 已生成的状态时间线
            
        Returns:
            Dict[str, Any]: 更新后的贷款数据
        """
        # 创建贷款数据的副本，避免修改原始数据
        updated_data = loan_data.copy()
        
        # 获取当前状态的持续时间（天数）
        if timeline:
            current_status_days = timeline[-1]['duration_days']
            current_status = timeline[-1]['status']
        else:
            current_status_days = 0
            current_status = ""
        
        # 如果进入还款状态，更新已经过的还款月数
        if next_status == 'repaying':
            months_since_disbursement = updated_data.get('months_since_disbursement', 0)
            # 添加当前状态的月数（简化处理，按30天/月计算）
            if current_status == 'repaying':
                months_since_disbursement += current_status_days / 30
            updated_data['months_since_disbursement'] = months_since_disbursement
        
        # 如果进入逾期状态，初始化逾期信息
        if next_status == 'overdue':
            # 设置初始逾期月数和金额
            updated_data['overdue_months'] = 1
            
            # 估算逾期金额（假设为一期的还款额）
            loan_amount = updated_data.get('loan_amount', 100000)
            loan_term_months = updated_data.get('loan_term_months', 36)
            monthly_payment = loan_amount / loan_term_months  # 简化计算，实际应考虑利息
            
            updated_data['overdue_amount'] = monthly_payment
        
        # 如果从逾期状态转为其他状态，更新逾期信息
        if current_status == 'overdue':
            if next_status == 'overdue':
                # 逾期状态持续，增加逾期月数和金额
                overdue_months = updated_data.get('overdue_months', 1)
                overdue_amount = updated_data.get('overdue_amount', 0)
                
                # 简化处理，每继续逾期30天，逾期月数+1
                additional_months = current_status_days / 30
                updated_data['overdue_months'] = overdue_months + additional_months
                
                # 逾期金额可能随时间增加（包括罚息）
                loan_amount = updated_data.get('loan_amount', 100000)
                loan_term_months = updated_data.get('loan_term_months', 36)
                monthly_payment = loan_amount / loan_term_months
                
                updated_data['overdue_amount'] = overdue_amount + monthly_payment * additional_months
        
        # 转到还款状态后，更新支付历史记录
        if next_status == 'repaying' and current_status == 'overdue':
            # 从逾期恢复正常还款，添加还款记录
            payment_history = updated_data.get('payment_history', [])
            payment_history.append({
                'payment_date': timeline[-1]['end_date'],
                'amount': updated_data.get('overdue_amount', 0),
                'is_late': True,
                'days_late': current_status_days
            })
            updated_data['payment_history'] = payment_history
            
            # 清除逾期信息
            updated_data['overdue_months'] = 0
            updated_data['overdue_amount'] = 0
        
        return updated_data 
    def get_status_at_date(self, timeline: List[Dict[str, Any]], target_date: datetime) -> Optional[str]:
        """
        获取贷款在指定日期的状态
        
        Args:
            timeline: 贷款状态时间线
            target_date: 目标日期
            
        Returns:
            Optional[str]: 在目标日期的贷款状态，如果日期不在时间线范围内则返回None
        """
        # 如果时间线为空，返回None
        if not timeline:
            return None
        
        # 检查目标日期是否在时间线的开始日期之前
        if target_date < timeline[0]['start_date']:
            return None
        
        # 检查目标日期是否在时间线的结束日期之后
        if target_date > timeline[-1]['end_date']:
            # 对于某些终态（如结清、拒绝），即使超过结束时间也可以返回该状态
            final_status = timeline[-1]['status']
            if final_status in {'settled', 'early_settled', 'rejected', 'defaulted'}:
                return final_status
            
            return None
        
        # 在时间线中查找匹配的状态
        for status_entry in timeline:
            start_date = status_entry['start_date']
            end_date = status_entry['end_date']
            
            # 检查目标日期是否在当前状态的时间范围内
            if start_date <= target_date <= end_date:
                return status_entry['status']
        
        # 如果没有找到匹配的状态（理论上不应该发生）
        return None
    
    def generate_status_events(self, timeline: List[Dict[str, Any]], loan_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        根据贷款状态时间线生成关键事件
        
        Args:
            timeline: 贷款状态时间线
            loan_data: 贷款相关数据
            
        Returns:
            List[Dict[str, Any]]: 关键事件列表，每个事件包含事件类型、时间、关联数据等
        """
        events = []
        
        # 贷款基本信息
        loan_id = loan_data.get('loan_id', '')
        customer_id = loan_data.get('customer_id', '')
        loan_type = loan_data.get('loan_type', '')
        loan_amount = loan_data.get('loan_amount', 0)
        
        # 遍历时间线，为状态变化生成事件
        for i, status_entry in enumerate(timeline):
            status = status_entry['status']
            start_date = status_entry['start_date']
            end_date = status_entry['end_date']
            
            # 为每种状态生成对应的事件
            if status == 'applying':
                # 贷款申请事件 - 发生在申请开始时
                events.append({
                    'event_type': 'loan_application',
                    'event_time': start_date,
                    'loan_id': loan_id,
                    'customer_id': customer_id,
                    'loan_type': loan_type,
                    'loan_amount': loan_amount,
                    'event_details': {
                        'channel': loan_data.get('application_channel', '网银'),
                        'is_first_application': loan_data.get('is_first_application', False)
                    }
                })
            
            elif status == 'approved':
                # 贷款批准事件 - 发生在批准状态的开始
                events.append({
                    'event_type': 'loan_approval',
                    'event_time': start_date,
                    'loan_id': loan_id,
                    'customer_id': customer_id,
                    'loan_type': loan_type,
                    'loan_amount': loan_amount,
                    'event_details': {
                        'approved_interest_rate': loan_data.get('interest_rate', 0),
                        'approved_term': loan_data.get('loan_term_months', 0),
                        'approval_channel': '自动审批' if random.random() < 0.7 else '人工审批'
                    }
                })
            
            elif status == 'rejected':
                # 贷款拒绝事件 - 发生在拒绝状态的开始
                # 确定拒绝原因
                reject_reasons = [
                    '信用评分不足',
                    '收入证明不足',
                    '负债比例过高',
                    '申请材料不完整',
                    '不符合贷款条件',
                    '历史逾期记录'
                ]
                
                events.append({
                    'event_type': 'loan_rejection',
                    'event_time': start_date,
                    'loan_id': loan_id,
                    'customer_id': customer_id,
                    'loan_type': loan_type,
                    'loan_amount': loan_amount,
                    'event_details': {
                        'reject_reason': random.choice(reject_reasons),
                        'can_reapply': random.random() < 0.7  # 70%的拒绝可以重新申请
                    }
                })
            
            elif status == 'disbursed':
                # 贷款放款事件 - 发生在放款状态的开始
                events.append({
                    'event_type': 'loan_disbursement',
                    'event_time': start_date,
                    'loan_id': loan_id,
                    'customer_id': customer_id,
                    'loan_type': loan_type,
                    'loan_amount': loan_amount,
                    'event_details': {
                        'disbursement_account': loan_data.get('account_id', ''),
                        'disbursement_channel': loan_data.get('disbursement_channel', '银行转账'),
                        'service_fee': loan_data.get('fees', {}).get('service_fee', 0)
                    }
                })
            
            elif status == 'repaying':
                # 还款事件 - 在还款期间定期生成
                # 获取还款计划
                repayment_schedule = loan_data.get('repayment_schedule', [])
                repayment_method = loan_data.get('repayment_method', '等额本息')
                
                # 计算还款事件的时间点
                if repayment_schedule and (end_date - start_date).days > 15:
                    # 确定还款日
                    repayment_day = start_date.day if start_date.day <= 28 else 28
                    
                    # 当前月和结束日期的月数差
                    current_month = start_date.month + start_date.year * 12
                    end_month = end_date.month + end_date.year * 12
                    months_between = end_month - current_month
                    
                    # 为每个月生成还款事件（最多12个）
                    for month_offset in range(min(months_between + 1, 12)):
                        # 计算还款日期
                        repayment_date = start_date.replace(day=1) + timedelta(days=repayment_day-1)
                        repayment_date = repayment_date.replace(month=((start_date.month + month_offset - 1) % 12) + 1)
                        if repayment_date.month != ((start_date.month + month_offset - 1) % 12) + 1:
                            # 处理月底日期问题（如2月30日）
                            repayment_date = repayment_date.replace(day=28)
                        
                        # 确保还款日期在时间范围内
                        if repayment_date > end_date:
                            break
                        
                        # 确定当前还款期次
                        payment_period = loan_data.get('months_since_disbursement', 0) + month_offset + 1
                        
                        # 获取当期应还金额
                        if 0 <= payment_period - 1 < len(repayment_schedule):
                            period_data = repayment_schedule[payment_period - 1]
                            principal = period_data.get('principal', 0)
                            interest = period_data.get('interest', 0)
                        else:
                            # 如果没有具体还款计划，估算还款金额
                            principal = loan_amount / loan_data.get('loan_term_months', 36)
                            interest = loan_amount * loan_data.get('interest_rate', 0.05) / 12
                        
                        # 生成还款事件
                        payment_amount = principal + interest
                        
                        # 随机决定是否按时还款
                        is_on_time = random.random() < 0.95  # 95%的概率按时还款
                        actual_payment_date = repayment_date
                        
                        if not is_on_time:
                            # 延迟1-7天
                            delay_days = random.randint(1, 7)
                            actual_payment_date = repayment_date + timedelta(days=delay_days)
                        
                        events.append({
                            'event_type': 'loan_repayment',
                            'event_time': actual_payment_date,
                            'loan_id': loan_id,
                            'customer_id': customer_id,
                            'event_details': {
                                'payment_period': payment_period,
                                'principal': round(principal, 2),
                                'interest': round(interest, 2),
                                'payment_amount': round(payment_amount, 2),
                                'is_on_time': is_on_time,
                                'payment_method': random.choice(['自动扣款', '银行转账', '网银支付', 'APP支付']),
                                'repayment_method': repayment_method
                            }
                        })
            
            elif status == 'overdue':
                # 逾期事件 - 发生在逾期状态的开始
                overdue_amount = loan_data.get('overdue_amount', 0)
                overdue_months = loan_data.get('overdue_months', 1)
                
                events.append({
                    'event_type': 'loan_overdue',
                    'event_time': start_date,
                    'loan_id': loan_id,
                    'customer_id': customer_id,
                    'event_details': {
                        'overdue_amount': round(overdue_amount, 2),
                        'overdue_days': overdue_months * 30,  # 简化计算
                        'late_fee': round(overdue_amount * 0.005 * overdue_months, 2),  # 0.5%每月的滞纳金
                        'contact_method': random.choice(['短信', '电话', '邮件', '信函'])
                    }
                })
                
                # 如果逾期时间较长，生成催收事件
                if overdue_months >= 2:
                    collection_date = start_date + timedelta(days=random.randint(5, 15))
                    
                    # 确保催收日期在逾期期间内
                    if collection_date <= end_date:
                        events.append({
                            'event_type': 'loan_collection',
                            'event_time': collection_date,
                            'loan_id': loan_id,
                            'customer_id': customer_id,
                            'event_details': {
                                'collection_method': random.choice(['电话催收', '短信催收', '上门催收', '委托催收']),
                                'collection_result': random.choice(['承诺还款', '无法联系', '拒绝还款', '部分还款'])
                            }
                        })
            
            elif status == 'defaulted':
                # 违约事件 - 发生在违约状态的开始
                events.append({
                    'event_type': 'loan_default',
                    'event_time': start_date,
                    'loan_id': loan_id,
                    'customer_id': customer_id,
                    'event_details': {
                        'default_amount': round(loan_data.get('overdue_amount', loan_amount * 0.3), 2),
                        'default_reason': random.choice(['长期逾期', '客户失联', '还款能力丧失', '拒绝还款']),
                        'action_taken': random.choice(['提交法律诉讼', '转交专业催收机构', '协商还款方案', '暂停催收'])
                    }
                })
            
            elif status == 'settled' or status == 'early_settled':
                # 结清事件 - 发生在结清状态的开始
                is_early = (status == 'early_settled')
                
                # 计算已还金额
                paid_amount = loan_amount
                if is_early:
                    # 提前结清可能有部分利息减免
                    interest_discount = loan_data.get('interest_rate', 0.05) * loan_amount * 0.1
                else:
                    interest_discount = 0
                
                events.append({
                    'event_type': 'loan_settlement',
                    'event_time': start_date,
                    'loan_id': loan_id,
                    'customer_id': customer_id,
                    'event_details': {
                        'is_early_settlement': is_early,
                        'settlement_amount': round(paid_amount, 2),
                        'interest_discount': round(interest_discount, 2),
                        'settlement_method': random.choice(['一次性结清', '余额结清', '转账结清']),
                        'settlement_channel': random.choice(['柜台', '网银', 'APP', '自动扣款'])
                    }
                })
        
        # 按事件时间排序
        events.sort(key=lambda x: x['event_time'])
        
        return events
    
    def generate_status_description(self, status: str, loan_data: Dict[str, Any], 
                              status_timeline: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        根据贷款状态和相关数据生成描述性文本
        
        Args:
            status: 贷款状态
            loan_data: 贷款相关数据
            status_timeline: 可选的状态时间线，用于获取状态变化的上下文信息
            
        Returns:
            str: 状态描述文本
        """
        # 从贷款数据中提取基本信息
        loan_type = loan_data.get('loan_type', '')
        loan_amount = loan_data.get('loan_amount', 0)
        interest_rate = loan_data.get('interest_rate', 0)
        loan_term_months = loan_data.get('loan_term_months', 36)
        
        # 将贷款类型转换为中文描述
        loan_type_cn = {
            'mortgage': '住房贷款',
            'car': '汽车贷款',
            'personal_consumption': '个人消费贷款',
            'small_business': '小微企业贷款',
            'education': '教育贷款'
        }.get(loan_type, '贷款')
        
        # 根据不同状态生成描述
        if status == 'applying':
            return f"{loan_type_cn}申请审核中，申请金额{loan_amount:,.2f}元，期限{loan_term_months}个月，预计{random.randint(1, 5)}个工作日内完成审核。"
        
        elif status == 'approved':
            return f"{loan_type_cn}审批已通过，批准金额{loan_amount:,.2f}元，年利率{interest_rate:.2%}，期限{loan_term_months}个月，等待放款。"
        
        elif status == 'rejected':
            reject_reasons = [
                '信用评分不足',
                '收入证明不足',
                '负债比例过高',
                '申请材料不完整',
                '不符合贷款条件',
                '历史逾期记录'
            ]
            reason = loan_data.get('reject_reason', random.choice(reject_reasons))
            return f"{loan_type_cn}申请被拒绝，原因：{reason}。建议改善相关条件后再次申请。"
        
        elif status == 'disbursed':
            account_id = loan_data.get('account_id', '********')
            disbursement_date = loan_data.get('disbursement_date', '最近')
            return f"{loan_type_cn}已放款，金额{loan_amount:,.2f}元已于{disbursement_date}转入账户{account_id}，贷款正式生效。"
        
        elif status == 'repaying':
            # 计算已还款期数和剩余期数
            months_since_disbursement = loan_data.get('months_since_disbursement', 0)
            remaining_months = max(0, loan_term_months - months_since_disbursement)
            
            # 计算剩余本金
            principal_paid = 0
            repayment_schedule = loan_data.get('repayment_schedule', [])
            if repayment_schedule and int(months_since_disbursement) < len(repayment_schedule):
                principal_paid = sum(payment.get('principal', 0) for payment in repayment_schedule[:int(months_since_disbursement)])
            
            remaining_principal = max(0, loan_amount - principal_paid)
            
            repayment_method = loan_data.get('repayment_method', '等额本息')
            repayment_day = loan_data.get('repayment_day', random.randint(1, 28))
            
            if months_since_disbursement < 1:
                return f"{loan_type_cn}进入还款期，总金额{loan_amount:,.2f}元，期限{loan_term_months}个月，采用{repayment_method}方式，每月{repayment_day}日为还款日。"
            else:
                return f"{loan_type_cn}正常还款中，已还{int(months_since_disbursement)}期，剩余{remaining_months}期，当前剩余本金{remaining_principal:,.2f}元，采用{repayment_method}方式还款。"
        
        elif status == 'overdue':
            overdue_amount = loan_data.get('overdue_amount', 0)
            overdue_months = loan_data.get('overdue_months', 1)
            late_fee = overdue_amount * 0.005 * overdue_months  # 假设0.5%每月的滞纳金
            
            if overdue_months < 1:
                days = int(overdue_months * 30)
                return f"{loan_type_cn}已逾期{days}天，逾期金额{overdue_amount:,.2f}元，产生滞纳金{late_fee:,.2f}元，请尽快还款以避免信用损失。"
            else:
                return f"{loan_type_cn}已逾期{int(overdue_months)}个月，逾期金额{overdue_amount:,.2f}元，产生滞纳金{late_fee:,.2f}元，已影响个人信用记录，请尽快联系银行处理。"
        
        elif status == 'defaulted':
            default_amount = loan_data.get('overdue_amount', loan_amount * 0.3)
            default_days = loan_data.get('default_days', 90)
            
            return f"{loan_type_cn}已违约，连续逾期{default_days}天，违约金额{default_amount:,.2f}元，已纳入不良信用记录，请尽快联系银行协商解决方案。"
        
        elif status == 'settled':
            settlement_date = loan_data.get('settlement_date', '近期')
            total_paid = loan_data.get('total_repayment', loan_amount * (1 + interest_rate * loan_term_months / 12))
            
            return f"{loan_type_cn}已结清，于{settlement_date}完成最后一期还款，累计还款总额{total_paid:,.2f}元，感谢您的按时还款。"
        
        elif status == 'early_settled':
            settlement_date = loan_data.get('settlement_date', '近期')
            original_term = loan_data.get('loan_term_months', 36)
            actual_term = loan_data.get('actual_term_months', int(original_term * 0.7))
            
            return f"{loan_type_cn}已提前结清，原定期限{original_term}个月，实际用时{actual_term}个月，于{settlement_date}办理结清手续，感谢您的选择。"
        
        else:
            # 未知状态
            return f"{loan_type_cn}当前状态：{status}，贷款金额{loan_amount:,.2f}元，期限{loan_term_months}个月。"

    def get_status_summary(self, loan_id: str, loan_data: Dict[str, Any], 
                        status_timeline: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        生成贷款状态的汇总信息
        
        Args:
            loan_id: 贷款ID
            loan_data: 贷款相关数据
            status_timeline: 状态时间线
            
        Returns:
            Dict[str, Any]: 贷款状态汇总信息
        """
        # 如果时间线为空，返回空汇总
        if not status_timeline:
            return {
                'loan_id': loan_id,
                'status': 'unknown',
                'description': '无贷款状态记录',
                'has_risk': False,
                'completion_percentage': 0,
                'days_in_current_status': 0
            }
        
        # 获取当前状态（时间线的最后一个状态）
        current_status_entry = status_timeline[-1]
        current_status = current_status_entry['status']
        
        # 计算当前状态已持续的天数
        current_date = datetime.now()
        start_date = current_status_entry['start_date']
        end_date = current_status_entry['end_date']
        
        if current_date < start_date:
            days_in_current_status = 0
        elif current_date > end_date:
            days_in_current_status = (end_date - start_date).days
        else:
            days_in_current_status = (current_date - start_date).days
        
        # 生成状态描述
        description = self.generate_status_description(current_status, loan_data, status_timeline)
        
        # 确定是否有风险
        has_risk = current_status in ['overdue', 'defaulted']
        
        # 计算贷款完成百分比
        completion_percentage = 0
        if current_status in ['settled', 'early_settled']:
            completion_percentage = 100
        elif current_status == 'defaulted':
            completion_percentage = 0  # 违约视为未完成
        else:
            # 计算已经过的贷款期限占总期限的比例
            loan_term_months = loan_data.get('loan_term_months', 36)
            months_since_disbursement = loan_data.get('months_since_disbursement', 0)
            
            if loan_term_months > 0:
                completion_percentage = min(100, int(months_since_disbursement / loan_term_months * 100))
        
        # 确定贷款的开始和结束日期
        start_event = status_timeline[0]['start_date'] if status_timeline else None
        end_event = None
        
        if current_status in ['settled', 'early_settled', 'rejected', 'defaulted']:
            end_event = current_status_entry['end_date']
        
        # 汇总历史状态信息
        status_history = []
        for entry in status_timeline:
            status_history.append({
                'status': entry['status'],
                'start_date': entry['start_date'],
                'end_date': entry['end_date'],
                'duration_days': entry['duration_days']
            })
        
        # 返回汇总信息
        return {
            'loan_id': loan_id,
            'status': current_status,
            'description': description,
            'has_risk': has_risk,
            'completion_percentage': completion_percentage,
            'days_in_current_status': days_in_current_status,
            'start_date': start_event,
            'end_date': end_event,
            'status_history': status_history
        }