#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
贷款审批流程模型

负责模拟贷款审批过程中的决策和时间控制。
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any

class LoanApprovalModel:
    """
    贷款审批模型，负责处理贷款审批过程的数据生成：
    - 审批流程和规则
    - 审批决策和审批条件
    - 审批人员和角色
    - 审批记录和历史
    """
    
    def __init__(self, config: Dict[str, Any], risk_model=None, parameter_model=None):
        """
        初始化贷款审批模型
        
        Args:
            config: 配置参数
            risk_model: 风险模型实例，用于评估风险和计算违约概率
            parameter_model: 参数模型实例，用于计算贷款参数
        """
        self.config = config
        self.risk_model = risk_model
        self.parameter_model = parameter_model
        
        # 审批流程设置
        self.approval_flows = {
            'express': {  # 快速审批流程（小额贷款）
                'steps': ['document_check', 'automated_review', 'approval_decision'],
                'max_loan_amount': 50000,
                'avg_processing_days': 2
            },
            'standard': {  # 标准审批流程（中等金额贷款）
                'steps': ['document_check', 'credit_review', 'risk_assessment', 'approval_decision'],
                'max_loan_amount': 300000,
                'avg_processing_days': 5
            },
            'enhanced': {  # 增强审批流程（大额贷款）
                'steps': ['document_check', 'credit_review', 'risk_assessment', 'senior_review', 'committee_approval'],
                'min_loan_amount': 300001,
                'avg_processing_days': 8
            }
        }
        
        # 审批角色
        self.approval_roles = [
            'document_officer',       # 文档审核人员
            'credit_officer',         # 信贷审核人员
            'risk_officer',           # 风险评估人员
            'senior_credit_officer',  # 高级信贷审核人员
            'approval_manager',       # 审批经理
            'committee_member'        # 审批委员会成员
        ]
        
        # 审批结果概率（基础概率，会根据风险等级调整）
        self.approval_probabilities = {
            'low_risk': 0.95,         # 低风险申请批准率
            'medium_risk': 0.80,      # 中风险申请批准率
            'high_risk': 0.40,        # 高风险申请批准率
            'very_high_risk': 0.15    # 极高风险申请批准率
        }
    
    def determine_approval_flow(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据申请数据确定合适的审批流程
        
        Args:
            application_data: 贷款申请数据
            
        Returns:
            Dict[str, Any]: 审批流程信息，包括流程类型、步骤和预计完成时间
        """
        # 获取贷款金额和类型
        loan_amount = application_data.get('loan_amount', 0)
        loan_type = application_data.get('loan_type', 'personal_consumption')
        is_vip = application_data.get('is_vip_customer', False)
        
        # 根据金额确定基础流程类型
        if loan_amount <= self.approval_flows['express']['max_loan_amount']:
            flow_type = 'express'
        elif loan_amount <= self.approval_flows['standard']['max_loan_amount']:
            flow_type = 'standard'
        else:
            flow_type = 'enhanced'
        
        # 根据贷款类型可能会调整流程
        if loan_type == 'mortgage':
            # 房贷通常需要更严格的审核，除非是小额贷款
            if flow_type == 'express':
                flow_type = 'standard'
        elif loan_type == 'small_business':
            # 小微企业贷款通常需要更详细的风险评估
            if flow_type == 'express':
                flow_type = 'standard'
        
        # VIP客户可能获得更快的审批流程
        if is_vip and flow_type == 'standard' and loan_amount <= self.approval_flows['standard']['max_loan_amount'] * 0.8:
            flow_type = 'express'
        
        # 获取流程信息
        flow_info = self.approval_flows[flow_type].copy()
        
        # 计算预计完成时间
        avg_days = flow_info['avg_processing_days']
        
        # VIP客户处理时间更短
        if is_vip:
            avg_days = max(1, avg_days * 0.7)
        
        # 考虑一些随机因素
        min_days = max(1, int(avg_days * 0.8))
        max_days = int(avg_days * 1.2)
        
        processing_days = random.randint(min_days, max_days)
        expected_completion_date = datetime.now() + timedelta(days=processing_days)
        
        # 添加到流程信息
        flow_info['flow_type'] = flow_type
        flow_info['expected_processing_days'] = processing_days
        flow_info['expected_completion_date'] = expected_completion_date
        
        # 生成审批流程追踪ID
        flow_info['approval_flow_id'] = f"APF-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
        
        return flow_info
    
    def generate_approval_process(self, application_data: Dict[str, Any], 
                            approval_flow: Dict[str, Any],
                            start_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        生成贷款审批流程的详细数据
        
        Args:
            application_data: 贷款申请数据
            approval_flow: 审批流程信息
            start_date: 审批流程开始日期，如果不提供则使用当前日期
            
        Returns:
            List[Dict[str, Any]]: 审批流程的详细步骤数据
        """
        # 如果没有提供开始日期，使用当前日期
        if start_date is None:
            start_date = datetime.now()
        
        # 获取基本信息
        application_id = application_data.get('application_id', '')
        flow_type = approval_flow.get('flow_type', 'standard')
        steps = approval_flow.get('steps', [])
        
        # 初始化结果列表
        approval_steps = []
        
        # 获取初始风险评级
        initial_risk_level = application_data.get('initial_risk_assessment', {}).get('initial_risk_level', 'medium')
        
        # 当前日期，用于累计计算每个步骤的日期
        current_date = start_date
        
        # 是否为VIP客户
        is_vip = application_data.get('is_vip_customer', False)
        
        # 遍历每个审批步骤
        for i, step_type in enumerate(steps):
            # 创建步骤基本信息
            step = {
                'step_id': f"STEP-{application_id}-{i+1:02d}",
                'application_id': application_id,
                'approval_flow_id': approval_flow.get('approval_flow_id', ''),
                'step_type': step_type,
                'step_name': self._get_step_name(step_type),
                'step_order': i + 1,
                'total_steps': len(steps)
            }
            
            # 为每个步骤分配处理人员
            step['assignee'] = self._assign_step_handler(step_type)
            
            # 计算步骤开始日期
            step['start_date'] = current_date
            
            # 计算步骤持续时间（天数）
            duration_days = self._calculate_step_duration(step_type, flow_type, is_vip)
            step_end_date = current_date + timedelta(days=duration_days)
            
            # 更新当前日期为这个步骤的结束日期，用于下一个步骤的开始日期
            current_date = step_end_date
            
            # 设置步骤结束日期
            step['end_date'] = step_end_date
            step['duration_days'] = duration_days
            
            # 生成步骤状态（最后一个步骤可能是待处理状态）
            if i < len(steps) - 1:
                step['status'] = 'completed'
            else:
                # 最后一个步骤可能是完成或待处理
                step['status'] = random.choices(
                    ['completed', 'pending'],
                    weights=[0.7, 0.3],
                    k=1
                )[0]
            
            # 生成步骤数据：根据步骤类型生成不同的数据
            step_data = self._generate_step_data(
                step_type, application_data, initial_risk_level, step['status']
            )
            step['step_data'] = step_data
            
            # 生成步骤结果
            if step['status'] == 'completed':
                step_result = step_data.get('result', {})
                step['result'] = step_result
                
                # 如果风险评估步骤完成，更新风险等级
                if step_type == 'risk_assessment' and 'risk_level' in step_result:
                    initial_risk_level = step_result['risk_level']
            else:
                step['result'] = {'status': 'pending'}
            
            # 添加步骤到结果列表
            approval_steps.append(step)
        
        return approval_steps

    def _get_step_name(self, step_type: str) -> str:
        """获取步骤的显示名称"""
        step_names = {
            'document_check': '文档审核',
            'automated_review': '自动审核',
            'credit_review': '信用审核',
            'risk_assessment': '风险评估',
            'senior_review': '高级审核',
            'approval_decision': '审批决策',
            'committee_approval': '委员会审批'
        }
        return step_names.get(step_type, step_type)

    def _assign_step_handler(self, step_type: str) -> Dict[str, Any]:
        """为审批步骤分配处理人员"""
        # 根据步骤类型分配适当的角色
        role_mapping = {
            'document_check': 'document_officer',
            'automated_review': 'system',
            'credit_review': 'credit_officer',
            'risk_assessment': 'risk_officer',
            'senior_review': 'senior_credit_officer',
            'approval_decision': 'approval_manager',
            'committee_approval': 'committee_member'
        }
        
        role = role_mapping.get(step_type, 'credit_officer')
        
        # 为系统执行的步骤设置特殊处理器
        if role == 'system':
            return {
                'type': 'system',
                'id': 'SYSTEM',
                'name': '自动审批系统'
            }
        
        # 为委员会审批生成多个处理人
        if role == 'committee_member':
            committee_members = []
            for i in range(3):  # 通常3人委员会
                member_id = f"{role.upper()}-{random.randint(1000, 9999)}"
                member_name = f"审批委员{i+1}"
                committee_members.append({
                    'type': 'user',
                    'id': member_id,
                    'name': member_name,
                    'role': role
                })
            return {
                'type': 'committee',
                'members': committee_members,
                'committee_id': f"COM-{random.randint(100, 999)}"
            }
        
        # 为普通角色生成处理人
        handler_id = f"{role.upper()}-{random.randint(1000, 9999)}"
        handler_name = self._generate_handler_name(role)
        
        return {
            'type': 'user',
            'id': handler_id,
            'name': handler_name,
            'role': role
        }

    def _generate_handler_name(self, role: str) -> str:
        """根据角色生成处理人姓名"""
        # 姓氏列表
        surnames = ['张', '王', '李', '赵', '陈', '刘', '杨', '黄', '周', '吴']
        # 名字列表
        names = ['明', '华', '强', '伟', '芳', '娟', '秀英', '丽', '静', '磊']
        
        # 根据角色设置职位
        positions = {
            'document_officer': '文档专员',
            'credit_officer': '信贷专员',
            'risk_officer': '风险分析师',
            'senior_credit_officer': '高级信贷经理',
            'approval_manager': '审批主管',
            'committee_member': '委员会成员'
        }
        
        # 生成随机姓名
        full_name = random.choice(surnames) + random.choice(names)
        
        # 添加职位
        position = positions.get(role, '审核员')
        
        return f"{full_name}（{position}）"

    def _calculate_step_duration(self, step_type: str, flow_type: str, is_vip: bool) -> int:
        """计算步骤持续时间（天数）"""
        # 基础持续时间（天）
        base_durations = {
            'document_check': 1,
            'automated_review': 0.5,
            'credit_review': 1.5,
            'risk_assessment': 1,
            'senior_review': 1.5,
            'approval_decision': 1,
            'committee_approval': 2
        }
        
        # 根据流程类型调整持续时间
        flow_multiplier = {
            'express': 0.7,  # 快速流程处理更快
            'standard': 1.0,  # 标准流程正常处理时间
            'enhanced': 1.2   # 增强流程处理更慢
        }
        
        # 获取基础持续时间
        duration = base_durations.get(step_type, 1)
        
        # 应用流程乘数
        duration *= flow_multiplier.get(flow_type, 1.0)
        
        # VIP客户处理更快
        if is_vip:
            duration *= 0.7
        
        # 添加随机变化（±20%）
        random_factor = random.uniform(0.8, 1.2)
        duration *= random_factor
        
        # 返回整数天数，至少0.5天（转换为1天）
        return max(1, int(round(duration)))

    def _generate_step_data(self, step_type: str, application_data: Dict[str, Any],
                        risk_level: str, status: str) -> Dict[str, Any]:
        """根据步骤类型生成步骤数据"""
        # 初始化结果
        step_data = {'notes': []}
        
        # 根据步骤类型生成不同的数据
        if step_type == 'document_check':
            # 文档审核数据
            document_status = application_data.get('document_status', {})
            
            # 统计文档状态
            submitted = sum(1 for status in document_status.values() if status == 'submitted')
            pending = sum(1 for status in document_status.values() if status == 'pending')
            issues = sum(1 for status in document_status.values() if status == 'issue')
            
            step_data['documents_checked'] = list(document_status.keys())
            
            result = {
                'total_documents': len(document_status),
                'submitted_documents': submitted,
                'pending_documents': pending,
                'documents_with_issues': issues,
                'is_complete': pending == 0 and issues == 0,
                'requires_additional_docs': pending > 0 or issues > 0
            }
            
            if result['requires_additional_docs'] and status == 'completed':
                step_data['notes'].append("客户需要补充材料，已发送通知。")
            elif status == 'completed':
                step_data['notes'].append("所有必要文档已审核通过。")
            
            step_data['result'] = result
        
        elif step_type == 'automated_review':
            # 自动审核数据
            credit_score = application_data.get('credit_score', 700)
            loan_amount = application_data.get('loan_amount', 100000)
            
            # 自动规则检查
            rules_checked = [
                {'rule': '信用评分检查', 'result': 'pass' if credit_score >= 600 else 'fail'},
                {'rule': '贷款金额检查', 'result': 'pass' if loan_amount <= 50000 else 'warning'},
                {'rule': '黑名单检查', 'result': 'pass'},
                {'rule': '欺诈风险检查', 'result': 'pass'}
            ]
            
            # 检查是否所有规则都通过
            all_passed = all(rule['result'] == 'pass' for rule in rules_checked)
            has_warning = any(rule['result'] == 'warning' for rule in rules_checked)
            has_failure = any(rule['result'] == 'fail' for rule in rules_checked)
            
            result = {
                'rules_checked': rules_checked,
                'all_passed': all_passed,
                'has_warning': has_warning,
                'has_failure': has_failure,
                'recommendation': 'approve' if all_passed else 'review' if has_warning else 'reject'
            }
            
            if status == 'completed':
                step_data['notes'].append(
                    "自动审核完成，系统建议：" + 
                    ("通过" if result['recommendation'] == 'approve' else 
                    "人工审核" if result['recommendation'] == 'review' else 
                    "拒绝")
                )
            
            step_data['result'] = result
        
        elif step_type == 'credit_review':
            # 信用审核数据
            credit_score = application_data.get('credit_score', 700)
            annual_income = application_data.get('annual_income', 100000)
            existing_debt = application_data.get('existing_debt', 0)
            
            # 计算债务收入比
            monthly_income = annual_income / 12
            monthly_debt = existing_debt / 12
            
            debt_to_income = monthly_debt / monthly_income if monthly_income > 0 else 1.0
            
            # 支付能力评估
            affordability_checks = [
                {'check': '债务收入比', 'value': debt_to_income, 'threshold': 0.4, 
                'result': 'pass' if debt_to_income <= 0.4 else 'fail'},
                {'check': '信用评分', 'value': credit_score, 'threshold': 600, 
                'result': 'pass' if credit_score >= 600 else 'fail'},
                {'check': '收入稳定性', 'value': '良好', 'threshold': None, 
                'result': 'pass'}
            ]
            
            all_passed = all(check['result'] == 'pass' for check in affordability_checks)
            
            result = {
                'credit_score': credit_score,
                'debt_to_income': debt_to_income,
                'affordability_checks': affordability_checks,
                'all_checks_passed': all_passed,
                'credit_assessment': 'good' if all_passed else 'marginal' if debt_to_income <= 0.5 else 'poor'
            }
            
            if status == 'completed':
                step_data['notes'].append(
                    f"信用审核完成，评估结果：" + 
                    ("良好" if result['credit_assessment'] == 'good' else 
                    "一般" if result['credit_assessment'] == 'marginal' else 
                    "较差")
                )
            
            step_data['result'] = result
        
        elif step_type == 'risk_assessment':
            # 风险评估数据
            # 如果有风险模型，使用模型计算风险
            if self.risk_model and status == 'completed':
                customer_data = {k: v for k, v in application_data.items() 
                            if k in ['customer_id', 'credit_score', 'annual_income', 'existing_debt']}
                loan_data = {k: v for k, v in application_data.items() 
                        if k in ['loan_type', 'loan_amount', 'loan_term_months']}
                
                default_probability = self.risk_model.calculate_default_probability(customer_data, loan_data)
                calculated_risk_level = self.risk_model.determine_risk_level(default_probability, loan_data)
                
                # 与初始风险评级比较
                risk_change = self._compare_risk_levels(risk_level, calculated_risk_level)
                
                result = {
                    'initial_risk_level': risk_level,
                    'calculated_risk_level': calculated_risk_level,
                    'default_probability': default_probability,
                    'risk_change': risk_change,
                    'risk_factors': self.risk_model.analyze_risk_factors(customer_data, loan_data)
                                    if hasattr(self.risk_model, 'analyze_risk_factors') else {}
                }
                
                step_data['notes'].append(
                    f"风险评估完成，风险等级：{calculated_risk_level}，" + 
                    (f"较初始评估{risk_change}" if risk_change != '不变' else "与初始评估一致")
                )
            else:
                # 没有风险模型或步骤未完成，生成模拟数据
                risk_levels = ['low', 'medium', 'high', 'very_high']
                current_index = risk_levels.index(risk_level) if risk_level in risk_levels else 1
                
                # 大多数情况下风险等级保持不变
                change_probability = 0.3
                if random.random() < change_probability:
                    # 有变化时，大多数情况是小幅变化
                    change = random.choices([-1, 1], weights=[0.4, 0.6], k=1)[0]
                    new_index = max(0, min(len(risk_levels) - 1, current_index + change))
                    calculated_risk_level = risk_levels[new_index]
                else:
                    calculated_risk_level = risk_level
                
                default_probability = random.uniform(0.05, 0.4)
                risk_change = self._compare_risk_levels(risk_level, calculated_risk_level)
                
                result = {
                    'initial_risk_level': risk_level,
                    'calculated_risk_level': calculated_risk_level,
                    'default_probability': default_probability,
                    'risk_change': risk_change
                }
                
                if status == 'completed':
                    step_data['notes'].append(
                        f"风险评估完成，风险等级：{calculated_risk_level}，" + 
                        (f"较初始评估{risk_change}" if risk_change != '不变' else "与初始评估一致")
                    )
            
            step_data['result'] = result
        
        elif step_type in ['senior_review', 'approval_decision', 'committee_approval']:
            # 决策相关步骤
            loan_amount = application_data.get('loan_amount', 100000)
            
            # 决策可能的结果
            approval_probability = self._calculate_approval_probability(risk_level)
            decision = 'approved' if random.random() < approval_probability else 'rejected'
            
            if decision == 'approved':
                # 可能会有条件调整
                adjustments = []
                
                # 根据风险等级可能调整利率
                if risk_level == 'medium':
                    adjustments.append({'type': 'interest_rate', 'adjustment': 0.005, 'reason': '风险定价'})
                elif risk_level == 'high':
                    adjustments.append({'type': 'interest_rate', 'adjustment': 0.01, 'reason': '风险定价'})
                    
                    # 高风险可能降低贷款金额
                    if random.random() < 0.3:
                        amount_reduction = random.uniform(0.1, 0.3)
                        adjustments.append({
                            'type': 'loan_amount', 
                            'adjustment': -amount_reduction,
                            'reason': '风险控制'
                        })
                elif risk_level == 'very_high':
                    adjustments.append({'type': 'interest_rate', 'adjustment': 0.02, 'reason': '风险定价'})
                    
                    # 极高风险很可能降低贷款金额
                    if random.random() < 0.7:
                        amount_reduction = random.uniform(0.2, 0.5)
                        adjustments.append({
                            'type': 'loan_amount', 
                            'adjustment': -amount_reduction,
                            'reason': '风险控制'
                        })
                
                result = {
                    'decision': decision,
                    'has_adjustments': len(adjustments) > 0,
                    'adjustments': adjustments,
                    'approval_conditions': self._generate_approval_conditions(risk_level)
                }
            else:
                # 拒绝理由
                rejection_reasons = [
                    {'reason': '信用评分不足', 'details': '申请人信用评分低于最低要求'},
                    {'reason': '债务收入比过高', 'details': '申请人当前债务负担已接近或超过收入能力'},
                    {'reason': '风险等级过高', 'details': '根据风险评估，申请人违约风险超出可接受范围'},
                    {'reason': '提供材料不充分', 'details': '申请人提供的证明文件无法满足审核要求'}
                ]
                
                # 根据风险等级选择更合适的拒绝理由
                if risk_level == 'high' or risk_level == 'very_high':
                    likely_reasons = rejection_reasons[:3]  # 前三个原因更可能
                else:
                    likely_reasons = rejection_reasons
                
                selected_reason = random.choice(likely_reasons)
                
                result = {
                    'decision': decision,
                    'rejection_reason': selected_reason['reason'],
                    'rejection_details': selected_reason['details'],
                    'can_reapply_after_days': random.randint(30, 90)
                }
            
            if status == 'completed':
                if decision == 'approved':
                    note = "审批通过"
                    if result['has_adjustments']:
                        adjustments_desc = []
                        for adj in result['adjustments']:
                            if adj['type'] == 'interest_rate':
                                adjustments_desc.append(f"利率上浮{adj['adjustment']:.1%}")
                            elif adj['type'] == 'loan_amount':
                                adjustments_desc.append(f"贷款金额减少{-adj['adjustment']:.0%}")
                        
                        if adjustments_desc:
                            note += f"，但有以下调整：{', '.join(adjustments_desc)}"
                    
                    step_data['notes'].append(note)
                else:
                    step_data['notes'].append(f"审批拒绝，原因：{result['rejection_reason']}")
            
            step_data['result'] = result
        
        # 为所有步骤添加一些通用数据
        step_data['created_at'] = datetime.now()
        if status == 'completed':
            step_data['completed_at'] = datetime.now()
        
        # 添加系统生成的注释
        if status == 'pending':
            step_data['notes'].append("步骤进行中，等待处理。")
        
        return step_data

    def _compare_risk_levels(self, initial_level: str, calculated_level: str) -> str:
        """比较两个风险等级的变化"""
        risk_levels = ['low', 'medium', 'high', 'very_high']
        
        if initial_level == calculated_level:
            return "不变"
        
        if initial_level not in risk_levels or calculated_level not in risk_levels:
            return "不可比"
        
        initial_index = risk_levels.index(initial_level)
        calculated_index = risk_levels.index(calculated_level)
        
        if calculated_index > initial_index:
            return "上升"
        else:
            return "下降"

    def _calculate_approval_probability(self, risk_level: str) -> float:
        """计算审批通过概率"""
        # 基础概率
        base_prob = self.approval_probabilities.get(risk_level + '_risk', 0.5)
        
        # 添加随机波动（±10%）
        random_factor = random.uniform(0.9, 1.1)
        
        return min(0.99, max(0.01, base_prob * random_factor))

    def _generate_approval_conditions(self, risk_level: str) -> List[Dict[str, str]]:
        """生成审批条件"""
        conditions = []
        
        # 基础条件
        conditions.append({'type': 'standard', 'description': '按时还款，避免逾期'})
        
        # 根据风险等级添加额外条件
        if risk_level == 'medium':
            if random.random() < 0.3:
                conditions.append({'type': 'documentation', 'description': '提供最近3个月的银行流水'})
        elif risk_level == 'high':
            conditions.append({'type': 'documentation', 'description': '提供最近6个月的银行流水'})
            if random.random() < 0.5:
                conditions.append({'type': 'guarantor', 'description': '需要提供担保人'})
        elif risk_level == 'very_high':
            conditions.append({'type': 'documentation', 'description': '提供最近12个月的银行流水'})
            conditions.append({'type': 'guarantor', 'description': '需要提供担保人'})
            if random.random() < 0.7:
                conditions.append({'type': 'collateral', 'description': '需要提供抵押物'})
        
        return conditions
    
    def generate_approval_decision(self, application_data: Dict[str, Any], 
                            approval_process: List[Dict[str, Any]],
                            customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成最终的审批决策和结果
        
        Args:
            application_data: 贷款申请数据
            approval_process: 审批流程数据
            customer_data: 客户相关数据
            
        Returns:
            Dict[str, Any]: 审批决策和结果数据
        """
        # 初始化结果字典
        decision_result = {
            'application_id': application_data.get('application_id', ''),
            'customer_id': application_data.get('customer_id', ''),
            'decision_date': datetime.now(),
            'decision_id': f"DEC-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
        }
        
        # 检查所有审批步骤是否已完成
        all_steps_completed = all(step['status'] == 'completed' for step in approval_process)
        
        # 如果有未完成的步骤，设置为待决策
        if not all_steps_completed:
            decision_result['status'] = 'pending'
            decision_result['pending_reason'] = '审批流程尚未完成'
            return decision_result
        
        # 获取最后一个审批步骤的结果
        final_step = next((step for step in reversed(approval_process) 
                        if step['step_type'] in ['approval_decision', 'committee_approval']), None)
        
        # 如果没有最终审批步骤，无法生成决策
        if not final_step or 'result' not in final_step:
            decision_result['status'] = 'error'
            decision_result['error_reason'] = '审批流程缺少最终决策步骤'
            return decision_result
        
        # 获取风险评估步骤的结果
        risk_step = next((step for step in approval_process if step['step_type'] == 'risk_assessment'), None)
        risk_level = None
        default_probability = None
        
        if risk_step and 'result' in risk_step:
            risk_result = risk_step['result']
            risk_level = risk_result.get('calculated_risk_level', 
                                    risk_result.get('initial_risk_level', 'medium'))
            default_probability = risk_result.get('default_probability', 0.1)
        
        # 获取最终审批决定
        final_result = final_step['result']
        decision = final_result.get('decision', 'rejected')
        
        # 设置决策结果
        decision_result['decision'] = decision
        decision_result['status'] = 'completed'
        
        # 根据决策结果添加不同的信息
        if decision == 'approved':
            # 批准决策
            # 获取原始申请信息
            loan_type = application_data.get('loan_type', 'personal_consumption')
            loan_amount = application_data.get('loan_amount', 100000)
            loan_term_months = application_data.get('loan_term_months', 36)
            
            # 合并所有步骤中的调整
            adjustments = []
            for step in approval_process:
                if 'result' in step and 'adjustments' in step['result']:
                    adjustments.extend(step['result']['adjustments'])
            
            # 应用调整
            approved_amount = loan_amount
            base_interest_rate = self._get_base_interest_rate(loan_type, loan_term_months, customer_data)
            approved_interest_rate = base_interest_rate
            
            for adj in adjustments:
                if adj['type'] == 'loan_amount' and 'adjustment' in adj:
                    if isinstance(adj['adjustment'], float) and adj['adjustment'] < 0:
                        # 减少贷款金额（负的调整值表示减少比例）
                        approved_amount = approved_amount * (1 + adj['adjustment'])
                    elif isinstance(adj['adjustment'], (int, float)) and adj['adjustment'] > 0:
                        # 直接设置金额
                        approved_amount = adj['adjustment']
                
                if adj['type'] == 'interest_rate' and 'adjustment' in adj:
                    # 增加利率
                    approved_interest_rate += adj['adjustment']
            
            # 四舍五入金额
            approved_amount = round(approved_amount)
            
            # 合并所有审批条件
            conditions = []
            for step in approval_process:
                if 'result' in step and 'approval_conditions' in step['result']:
                    conditions.extend(step['result']['approval_conditions'])
            
            # 去除重复条件
            unique_conditions = []
            condition_descriptions = set()
            for condition in conditions:
                if condition['description'] not in condition_descriptions:
                    unique_conditions.append(condition)
                    condition_descriptions.add(condition['description'])
            
            # 计算年化百分比利率（APR）- 通常比名义利率略高
            apr = approved_interest_rate + 0.003  # 添加0.3%的费用
            
            # 生成有效期（通常为30天）
            validity_period_days = 30
            expiration_date = decision_result['decision_date'] + timedelta(days=validity_period_days)
            
            # 设置批准详情
            decision_result['approval_details'] = {
                'approved_amount': approved_amount,
                'approved_term_months': loan_term_months,  # 假设期限不变
                'base_interest_rate': base_interest_rate,
                'approved_interest_rate': approved_interest_rate,
                'annual_percentage_rate': apr,
                'approval_conditions': unique_conditions,
                'adjustments': adjustments,
                'validity_period_days': validity_period_days,
                'expiration_date': expiration_date,
                'risk_level': risk_level,
                'default_probability': default_probability,
                'requires_guarantor': any(c['type'] == 'guarantor' for c in unique_conditions),
                'requires_collateral': any(c['type'] == 'collateral' for c in unique_conditions)
            }
        else:
            # 拒绝决策
            # 获取拒绝原因
            rejection_reason = final_result.get('rejection_reason', '未指明原因')
            rejection_details = final_result.get('rejection_details', '')
            
            # 设置再申请等待期（通常30-90天）
            reapply_wait_days = final_result.get('can_reapply_after_days', random.randint(30, 90))
            earliest_reapply_date = decision_result['decision_date'] + timedelta(days=reapply_wait_days)
            
            # 设置拒绝详情
            decision_result['rejection_details'] = {
                'reason': rejection_reason,
                'details': rejection_details,
                'risk_level': risk_level,
                'default_probability': default_probability,
                'earliest_reapply_date': earliest_reapply_date,
                'reapply_wait_days': reapply_wait_days,
                'rejection_code': f"REJ-{random.randint(100, 999)}"
            }
        
        # 添加审批摘要
        decision_result['approval_summary'] = self._generate_approval_summary(
            decision, approval_process, decision_result
        )
        
        return decision_result

    def _get_base_interest_rate(self, loan_type: str, loan_term_months: int, 
                            customer_data: Dict[str, Any]) -> float:
        """获取基础利率"""
        # 如果有参数模型，使用模型计算
        if self.parameter_model and hasattr(self.parameter_model, 'calculate_interest_rate'):
            return self.parameter_model.calculate_interest_rate(
                loan_type, 
                customer_data.get('credit_score', 700),
                loan_term_months
            )
        
        # 否则使用默认利率
        base_rates = {
            'mortgage': 0.0425,         # 房贷基准利率
            'car': 0.0475,              # 车贷基准利率
            'personal_consumption': 0.055,  # 消费贷基准利率
            'small_business': 0.06,     # 小微企业贷基准利率
            'education': 0.045          # 教育贷基准利率
        }
        
        # 根据期限调整
        term_adjustment = 0.0
        if loan_term_months <= 12:
            term_adjustment = -0.002    # 短期贷款利率略低
        elif loan_term_months > 60:
            term_adjustment = 0.003     # 长期贷款利率略高
        
        # 获取基础利率
        base_rate = base_rates.get(loan_type, 0.055) + term_adjustment
        
        return base_rate

    def _generate_approval_summary(self, decision: str, approval_process: List[Dict[str, Any]],
                                decision_result: Dict[str, Any]) -> str:
        """生成审批摘要"""
        if decision == 'approved':
            approval_details = decision_result.get('approval_details', {})
            
            # 获取调整信息
            adjustments_desc = []
            if 'adjustments' in approval_details and approval_details['adjustments']:
                for adj in approval_details['adjustments']:
                    if adj['type'] == 'interest_rate':
                        adjustments_desc.append(f"利率上浮{adj['adjustment']:.1%}")
                    elif adj['type'] == 'loan_amount' and adj['adjustment'] < 0:
                        adjustments_desc.append(f"贷款金额减少{-adj['adjustment']:.0%}")
            
            # 获取条件信息
            conditions_desc = []
            if 'approval_conditions' in approval_details:
                for condition in approval_details['approval_conditions']:
                    if condition['type'] != 'standard':  # 跳过标准条件
                        conditions_desc.append(condition['description'])
            
            # 构建摘要
            summary = f"贷款申请已获批准，金额{approval_details.get('approved_amount', 0):,.2f}元，"
            summary += f"期限{approval_details.get('approved_term_months', 0)}个月，"
            summary += f"年利率{approval_details.get('approved_interest_rate', 0):.2%}。"
            
            if adjustments_desc:
                summary += f"有以下调整：{', '.join(adjustments_desc)}。"
            
            if conditions_desc:
                summary += f"批准条件：{', '.join(conditions_desc)}。"
                
            summary += f"批准有效期为{approval_details.get('validity_period_days', 30)}天，"
            summary += f"请在有效期内完成后续手续。"
        else:
            rejection_details = decision_result.get('rejection_details', {})
            
            # 构建摘要
            summary = f"很遗憾，贷款申请未获批准。拒绝原因：{rejection_details.get('reason', '未指明')}。"
            if 'details' in rejection_details and rejection_details['details']:
                summary += f"{rejection_details['details']}。"
                
            summary += f"您可在{rejection_details.get('reapply_wait_days', 30)}天后重新申请。"
            
            # 添加改进建议
            suggestions = self._generate_improvement_suggestions(
                rejection_details.get('reason', ''), approval_process
            )
            
            if suggestions:
                summary += f"建议：{suggestions}"
        
        return summary

    def _generate_improvement_suggestions(self, rejection_reason: str, 
                                        approval_process: List[Dict[str, Any]]) -> str:
        """根据拒绝原因生成改进建议"""
        suggestions = []
        
        if '信用评分' in rejection_reason:
            suggestions.append("提高信用评分，确保按时还款，降低信用卡使用率")
        
        if '债务收入比' in rejection_reason:
            suggestions.append("减少现有债务，或提高收入水平")
        
        if '材料不充分' in rejection_reason:
            # 查找文档检查步骤
            doc_step = next((step for step in approval_process if step['step_type'] == 'document_check'), None)
            if doc_step and 'result' in doc_step:
                missing_docs = []
                doc_result = doc_step['result']
                if 'pending_documents' in doc_result and doc_result['pending_documents'] > 0:
                    missing_docs.append("补充所有所需文档")
                
                if missing_docs:
                    suggestions.append(", ".join(missing_docs))
                else:
                    suggestions.append("提供更详细的收入证明和资产证明")
        
        if '风险等级' in rejection_reason:
            suggestions.append("考虑提供担保人或抵押物，降低贷款风险")
        
        if not suggestions:
            suggestions.append("改善个人收入稳定性和信用记录，或考虑降低贷款金额")
        
        return "；".join(suggestions) + "。"
    
    def generate_complete_approval(self, application_data: Dict[str, Any], 
                             customer_data: Dict[str, Any],
                             start_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        生成完整的贷款审批流程数据
        
        Args:
            application_data: 贷款申请数据
            customer_data: 客户相关数据
            start_date: 审批开始日期，如果不提供则使用当前日期
            
        Returns:
            Dict[str, Any]: 完整的审批流程数据，包括流程、步骤和决策
        """
        # 如果没有提供开始日期，使用当前日期
        if start_date is None:
            start_date = datetime.now()
        
        # 1. 确定审批流程
        approval_flow = self.determine_approval_flow(application_data)
        
        # 2. 生成审批流程详细数据
        approval_process = self.generate_approval_process(
            application_data, approval_flow, start_date
        )
        
        # 3. 生成审批决策
        approval_decision = self.generate_approval_decision(
            application_data, approval_process, customer_data
        )
        
        # 4. 整合结果
        complete_approval = {
            'application_id': application_data.get('application_id', ''),
            'customer_id': application_data.get('customer_id', ''),
            'approval_flow': approval_flow,
            'approval_process': approval_process,
            'approval_decision': approval_decision,
            'start_date': start_date,
            'end_date': approval_decision.get('decision_date', datetime.now()),
            'duration_days': (approval_decision.get('decision_date', datetime.now()) - start_date).days,
            'final_status': 'approved' if approval_decision.get('decision') == 'approved' else 'rejected',
            'processed_by': self._extract_processors(approval_process)
        }
        
        return complete_approval

    def _extract_processors(self, approval_process: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从审批流程中提取处理人员信息"""
        processors = []
        
        for step in approval_process:
            assignee = step.get('assignee', {})
            
            if assignee.get('type') == 'user':
                processors.append({
                    'id': assignee.get('id', ''),
                    'name': assignee.get('name', ''),
                    'role': assignee.get('role', ''),
                    'step': step.get('step_name', '')
                })
            elif assignee.get('type') == 'committee':
                for member in assignee.get('members', []):
                    processors.append({
                        'id': member.get('id', ''),
                        'name': member.get('name', ''),
                        'role': member.get('role', ''),
                        'step': step.get('step_name', ''),
                        'committee_id': assignee.get('committee_id', '')
                    })
        
        return processors