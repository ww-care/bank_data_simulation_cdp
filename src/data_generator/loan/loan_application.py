#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
贷款申请流程模型

负责模拟贷款申请过程中的各种决策和参数生成。
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any

class LoanApplicationModel:
    """
    贷款申请模型，负责生成贷款申请数据和处理申请流程：
    - 申请信息生成
    - 申请来源渠道
    - 申请文档生成
    - 申请流程跟踪
    """
    
    def __init__(self, config: Dict[str, Any], risk_model=None, parameter_model=None):
        """
        初始化贷款申请模型
        
        Args:
            config: 配置参数，包含申请渠道分布、申请材料等
            risk_model: 风险模型实例，用于评估申请风险
            parameter_model: 参数模型实例，用于计算贷款参数
        """
        self.config = config
        self.risk_model = risk_model
        self.parameter_model = parameter_model
        
        # 申请渠道分布
        self.channel_distribution = {
            'online_banking': 0.30,    # 网银渠道
            'mobile_app': 0.35,        # 手机银行APP
            'branch': 0.20,            # 银行网点
            'third_party': 0.15        # 第三方平台
        }
        
        # 如果配置中有指定，则覆盖默认值
        if 'application' in config and 'channel_distribution' in config['application']:
            self.channel_distribution = config['application']['channel_distribution']
        
        # 申请所需文档类型
        self.required_documents = {
            'mortgage': [
                '身份证明', '收入证明', '房产信息', '资产证明', 
                '个人征信报告', '购房合同', '首付款证明'
            ],
            'car': [
                '身份证明', '收入证明', '驾驶证', '购车协议', 
                '个人征信报告', '首付款证明'
            ],
            'personal_consumption': [
                '身份证明', '收入证明', '个人征信报告'
            ],
            'small_business': [
                '身份证明', '营业执照', '财务报表', '经营场所证明', 
                '税务登记证', '企业征信报告', '业务计划书'
            ],
            'education': [
                '身份证明', '学生证/录取通知书', '成绩单', 
                '收入证明（担保人）', '个人征信报告'
            ]
        }
        
        # 申请处理时间参数（天数）
        self.processing_time = {
            'mortgage': {'min': 5, 'max': 15, 'mean': 8},
            'car': {'min': 2, 'max': 7, 'mean': 4},
            'personal_consumption': {'min': 1, 'max': 5, 'mean': 2},
            'small_business': {'min': 3, 'max': 10, 'mean': 6},
            'education': {'min': 2, 'max': 7, 'mean': 4}
        }
    
    def generate_application_data(self, customer_data: Dict[str, Any], 
                                loan_data: Dict[str, Any], 
                                application_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        生成贷款申请数据
        
        Args:
            customer_data: 客户相关数据
            loan_data: 贷款相关数据
            application_date: 可选的申请日期，如果不提供则生成一个合理的日期
            
        Returns:
            Dict[str, Any]: 贷款申请数据
        """
        # 获取基础信息
        customer_id = customer_data.get('customer_id', str(uuid.uuid4())[:8])
        credit_score = customer_data.get('credit_score', 700)
        is_vip = customer_data.get('is_vip', False)
        
        loan_type = loan_data.get('loan_type', 'personal_consumption')
        loan_amount = loan_data.get('loan_amount', 100000)
        loan_term_months = loan_data.get('loan_term_months', 36)
        
        # 生成申请ID
        application_id = f"LOAN-{datetime.now().strftime('%Y%m%d')}-{random.randint(10000, 99999)}"
        
        # 如果没有提供申请日期，生成一个合理的日期
        if application_date is None:
            # 默认为当前日期前1-30天
            days_ago = random.randint(1, 30)
            application_date = datetime.now() - timedelta(days=days_ago)
        
        # 选择申请渠道
        channel = self._select_application_channel(customer_data)
        
        # 生成申请文档列表
        documents = self._generate_application_documents(loan_type)
        
        # 确定是首次申请还是再次申请
        is_first_application = random.random() < 0.7  # 70%概率是首次申请
        previous_applications = []
        
        if not is_first_application:
            # 生成1-3个历史申请记录
            num_previous = random.randint(1, 3)
            for i in range(num_previous):
                days_before = random.randint(60, 365)  # 60-365天前
                prev_date = application_date - timedelta(days=days_before)
                
                # 历史申请可能被拒绝或者客户主动取消
                prev_status = random.choice(['rejected', 'cancelled', 'approved_not_taken'])
                
                # 拒绝原因
                rejection_reason = ""
                if prev_status == 'rejected':
                    reasons = [
                        '信用评分不足', '收入证明不足', '负债比例过高', 
                        '申请材料不完整', '不符合贷款条件'
                    ]
                    rejection_reason = random.choice(reasons)
                
                previous_applications.append({
                    'application_id': f"LOAN-{prev_date.strftime('%Y%m%d')}-{random.randint(10000, 99999)}",
                    'application_date': prev_date,
                    'loan_type': loan_type,  # 简化处理，假设申请同类型贷款
                    'loan_amount': loan_amount * random.uniform(0.8, 1.2),  # 金额有所变化
                    'status': prev_status,
                    'rejection_reason': rejection_reason
                })
        
        # 如果有风险模型，计算申请风险初步评估
        risk_assessment = {}
        if self.risk_model:
            default_probability = self.risk_model.calculate_default_probability(customer_data, loan_data)
            risk_level = self.risk_model.determine_risk_level(default_probability, loan_data)
            
            risk_assessment = {
                'initial_risk_level': risk_level,
                'default_probability': default_probability,
                'auto_approval_eligibility': default_probability < 0.08  # 低风险可考虑自动审批
            }
        
        # 计算预计处理时间
        processing_time_params = self.processing_time.get(loan_type, 
                                                        {'min': 1, 'max': 7, 'mean': 3})
        
        # VIP客户处理时间缩短
        if is_vip:
            processing_time_params = {
                'min': max(1, int(processing_time_params['min'] * 0.7)),
                'max': max(3, int(processing_time_params['max'] * 0.7)),
                'mean': max(2, int(processing_time_params['mean'] * 0.7))
            }
        
        expected_processing_days = random.randint(
            processing_time_params['min'], 
            processing_time_params['max']
        )
        
        expected_decision_date = application_date + timedelta(days=expected_processing_days)
        
        # 构建申请数据
        application_data = {
            'application_id': application_id,
            'customer_id': customer_id,
            'application_date': application_date,
            'channel': channel,
            'loan_type': loan_type,
            'loan_amount': loan_amount,
            'loan_term_months': loan_term_months,
            'purpose': self._generate_loan_purpose(loan_type),
            'is_first_application': is_first_application,
            'previous_applications': previous_applications,
            'documents': documents,
            'document_status': self._generate_document_status(documents),
            'expected_processing_days': expected_processing_days,
            'expected_decision_date': expected_decision_date,
            'initial_risk_assessment': risk_assessment,
            'application_status': 'submitted',
            'application_notes': [],
            'is_vip_customer': is_vip
        }
        
        # 添加一些申请备注
        if is_vip:
            application_data['application_notes'].append("VIP客户申请，优先处理。")
        
        if not is_first_application:
            application_data['application_notes'].append("客户有历史申请记录，需参考历史情况进行评估。")
        
        if credit_score < 600:
            application_data['application_notes'].append("客户信用评分偏低，需重点关注收入证明和负债情况。")
        
        if loan_amount > 500000:
            application_data['application_notes'].append("大额贷款申请，需多人审核。")
        
        return application_data
    
    def _select_application_channel(self, customer_data: Dict[str, Any]) -> str:
        """选择申请渠道"""
        # 提取客户特征，可能影响渠道偏好
        age = customer_data.get('age', 35)
        is_vip = customer_data.get('is_vip', False)
        is_corporate = customer_data.get('is_corporate', False)
        
        # 调整渠道概率
        channel_probs = self.channel_distribution.copy()
        
        # 年轻客户更倾向于线上渠道
        if age < 30:
            channel_probs['mobile_app'] = channel_probs.get('mobile_app', 0) * 1.3
            channel_probs['online_banking'] = channel_probs.get('online_banking', 0) * 1.2
            channel_probs['branch'] = channel_probs.get('branch', 0) * 0.7
        
        # 年长客户更倾向于线下渠道
        elif age > 55:
            channel_probs['branch'] = channel_probs.get('branch', 0) * 1.5
            channel_probs['mobile_app'] = channel_probs.get('mobile_app', 0) * 0.7
        
        # VIP客户更倾向于网点渠道（可能获得专属服务）
        if is_vip:
            channel_probs['branch'] = channel_probs.get('branch', 0) * 1.4
        
        # 企业客户更倾向于网点和网银
        if is_corporate:
            channel_probs['branch'] = channel_probs.get('branch', 0) * 1.3
            channel_probs['online_banking'] = channel_probs.get('online_banking', 0) * 1.2
            channel_probs['mobile_app'] = channel_probs.get('mobile_app', 0) * 0.8
        
        # 归一化概率
        total = sum(channel_probs.values())
        normalized_probs = {k: v/total for k, v in channel_probs.items()}
        
        # 根据概率选择渠道
        channels = list(normalized_probs.keys())
        weights = list(normalized_probs.values())
        
        return random.choices(channels, weights=weights, k=1)[0]
    
    def _generate_application_documents(self, loan_type: str) -> List[str]:
        """生成申请所需文档列表"""
        # 获取特定贷款类型所需的文档
        required_docs = self.required_documents.get(loan_type, [])
        
        # 如果没有预定义文档，返回默认文档集
        if not required_docs:
            return ['身份证明', '收入证明', '个人征信报告']
        
        return required_docs.copy()
    
    def _generate_document_status(self, documents: List[str]) -> Dict[str, str]:
        """生成文档状态"""
        status_dict = {}
        
        for doc in documents:
            # 大部分文档已提交(85%)，少部分待提交(10%)或有问题(5%)
            rand = random.random()
            if rand < 0.85:
                status = 'submitted'
            elif rand < 0.95:
                status = 'pending'
            else:
                status = 'issue'
            
            status_dict[doc] = status
        
        return status_dict
    
    def _generate_loan_purpose(self, loan_type: str) -> str:
        """根据贷款类型生成贷款用途"""
        purposes = {
            'mortgage': [
                '购买首套住房', '购买二套住房', '住房装修', '住房翻新',
                '购买投资性房产', '置换住房'
            ],
            'car': [
                '购买新车', '购买二手车', '汽车置换', '汽车改装'
            ],
            'personal_consumption': [
                '日常消费', '大额消费', '医疗支出', '旅游度假',
                '婚庆支出', '教育支出', '家庭装修', '偿还其他债务'
            ],
            'small_business': [
                '经营周转', '扩大生产', '购买设备', '店面装修',
                '增加库存', '新产品研发', '支付员工工资', '偿还供应商'
            ],
            'education': [
                '本科学费', '研究生学费', '出国留学', '职业培训',
                '技能提升', '证书考试'
            ]
        }
        
        # 获取特定贷款类型的用途列表
        type_purposes = purposes.get(loan_type, ['个人消费'])
        
        return random.choice(type_purposes)
    
    def update_application_status(self, application_data: Dict[str, Any], 
                            current_date: datetime, 
                            loan_data: Dict[str, Any],
                            customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新贷款申请状态，模拟申请处理流程
        
        Args:
            application_data: 当前申请数据
            current_date: 当前日期
            loan_data: 贷款相关数据
            customer_data: 客户相关数据
            
        Returns:
            Dict[str, Any]: 更新后的申请数据
        """
        # 获取当前申请状态
        current_status = application_data.get('application_status', 'submitted')
        application_date = application_data.get('application_date', current_date - timedelta(days=1))
        expected_decision_date = application_data.get('expected_decision_date', current_date + timedelta(days=7))
        
        # 如果已经是终态，不再更新
        terminal_statuses = ['approved', 'rejected', 'cancelled', 'expired']
        if current_status in terminal_statuses:
            return application_data
        
        # 创建一份副本进行更新
        updated_application = application_data.copy()
        
        # 检查文档状态，如果有待提交或有问题的文档，可能需要补充材料
        document_status = application_data.get('document_status', {})
        incomplete_docs = [doc for doc, status in document_status.items() 
                        if status in ['pending', 'issue']]
        
        # 如果当前状态是已提交，且有不完整的文档，转为需要补充材料状态
        if current_status == 'submitted' and incomplete_docs and random.random() < 0.9:
            updated_application['application_status'] = 'additional_documents_required'
            updated_application['application_notes'].append(
                f"需要客户补充以下材料: {', '.join(incomplete_docs)}"
            )
            
            # 生成补充材料请求日期（通常在提交后1-3天）
            days_since_submission = (current_date - application_date).days
            if days_since_submission >= 1:
                updated_application['document_request_date'] = application_date + timedelta(days=min(days_since_submission, 3))
                # 预计决策日期可能延后
                updated_application['expected_decision_date'] = expected_decision_date + timedelta(days=5)
            
            return updated_application
        
        # 如果状态是需要补充材料，检查是否已更新文档
        if current_status == 'additional_documents_required':
            # 模拟客户补充材料的过程
            document_request_date = application_data.get('document_request_date')
            days_since_request = (current_date - document_request_date).days if document_request_date else 0
            
            # 客户通常在请求后3-10天内补充材料
            if 3 <= days_since_request <= 10:
                # 有80%的概率补充所有材料，20%的概率部分补充或放弃
                if random.random() < 0.8:
                    # 更新所有文档状态为已提交
                    updated_document_status = {doc: 'submitted' for doc in document_status}
                    updated_application['document_status'] = updated_document_status
                    updated_application['application_status'] = 'under_review'
                    updated_application['documents_completed_date'] = current_date
                    updated_application['application_notes'].append("客户已补充所有所需材料，申请进入审核阶段。")
                else:
                    # 随机更新部分文档状态
                    updated_document_status = document_status.copy()
                    for doc in incomplete_docs:
                        if random.random() < 0.5:
                            updated_document_status[doc] = 'submitted'
                    
                    updated_application['document_status'] = updated_document_status
                    
                    # 如果还有未提交的文档
                    still_incomplete = [doc for doc, status in updated_document_status.items() 
                                    if status in ['pending', 'issue']]
                    
                    if still_incomplete:
                        updated_application['application_notes'].append(
                            f"客户部分补充材料，仍缺: {', '.join(still_incomplete)}"
                        )
                    else:
                        updated_application['application_status'] = 'under_review'
                        updated_application['documents_completed_date'] = current_date
                        updated_application['application_notes'].append("客户已补充所有所需材料，申请进入审核阶段。")
            
            # 如果超过15天未补充材料，可能会被取消
            elif days_since_request > 15:
                if random.random() < 0.7:  # 70%的概率取消
                    updated_application['application_status'] = 'cancelled'
                    updated_application['cancellation_date'] = current_date
                    updated_application['cancellation_reason'] = '客户长时间未补充所需材料'
                    updated_application['application_notes'].append("申请因客户长时间未补充材料而被取消。")
            
            return updated_application
        
        # 如果状态是审核中，根据时间推进到下一个状态
        if current_status == 'under_review':
            # 获取开始审核日期（文档完成日期或申请日期）
            review_start_date = application_data.get('documents_completed_date', application_date)
            days_in_review = (current_date - review_start_date).days
            
            # 通常审核需要3-7天
            review_period = application_data.get('expected_processing_days', 5)
            
            # 根据风险评估结果调整审核时间
            risk_level = application_data.get('initial_risk_assessment', {}).get('initial_risk_level', 'medium')
            if risk_level == 'high' or risk_level == 'very_high':
                review_period += 2  # 高风险申请审核时间延长
            
            # VIP客户审核加速
            if application_data.get('is_vip_customer', False):
                review_period = max(2, review_period - 2)
            
            # 如果审核时间足够，进入决策阶段
            if days_in_review >= review_period:
                # 进入风险评估或直接决策
                if risk_level in ['high', 'very_high'] and random.random() < 0.8:
                    updated_application['application_status'] = 'risk_assessment'
                    updated_application['application_notes'].append("申请风险等级较高，需进一步风险评估。")
                else:
                    updated_application['application_status'] = 'pending_decision'
                    updated_application['application_notes'].append("申请审核完成，等待最终决策。")
                    updated_application['review_completed_date'] = current_date
            
            return updated_application
        
        # 如果状态是风险评估
        if current_status == 'risk_assessment':
            # 风险评估通常需要1-3天
            risk_start_date = application_data.get('review_completed_date', 
                                                application_date + timedelta(days=5))
            days_in_risk_assessment = (current_date - risk_start_date).days
            
            if days_in_risk_assessment >= random.randint(1, 3):
                updated_application['application_status'] = 'pending_decision'
                updated_application['risk_assessment_completed_date'] = current_date
                
                # 更新风险评估结果
                if self.risk_model:
                    default_probability = self.risk_model.calculate_default_probability(customer_data, loan_data)
                    risk_level = self.risk_model.determine_risk_level(default_probability, loan_data)
                    
                    # 可能调整初始评估结果
                    initial_risk = application_data.get('initial_risk_assessment', {}).get('initial_risk_level', 'medium')
                    
                    if risk_level != initial_risk:
                        updated_application['application_notes'].append(
                            f"风险评估结果从{initial_risk}调整为{risk_level}，调整原因：详细审核后重新评估。"
                        )
                    
                    # 更新风险评估部分
                    updated_application['risk_assessment'] = {
                        'risk_level': risk_level,
                        'default_probability': default_probability,
                        'assessment_date': current_date,
                        'assessor_id': f"RA-{random.randint(1000, 9999)}"
                    }
                
                updated_application['application_notes'].append("风险评估完成，申请进入最终决策阶段。")
            
            return updated_application
        
        # 如果状态是等待决策
        if current_status == 'pending_decision':
            # 决策通常需要1-2天
            decision_start_date = application_data.get('risk_assessment_completed_date', 
                                                application_data.get('review_completed_date', 
                                                                    application_date + timedelta(days=6)))
            days_in_decision = (current_date - decision_start_date).days
            
            if days_in_decision >= random.randint(1, 2):
                # 做出决策：批准或拒绝
                # 获取风险等级
                risk_assessment = application_data.get('risk_assessment', 
                                                application_data.get('initial_risk_assessment', {}))
                risk_level = risk_assessment.get('risk_level', 'medium')
                default_probability = risk_assessment.get('default_probability', 0.1)
                
                # 计算批准概率
                approve_probability = self._calculate_approval_probability(
                    risk_level, default_probability, application_data, customer_data
                )
                
                # 决定是否批准
                if random.random() < approve_probability:
                    updated_application['application_status'] = 'approved'
                    updated_application['decision_date'] = current_date
                    updated_application['approval_details'] = self._generate_approval_details(
                        loan_data, application_data, risk_level
                    )
                    updated_application['application_notes'].append("申请已批准，等待放款。")
                else:
                    updated_application['application_status'] = 'rejected'
                    updated_application['decision_date'] = current_date
                    updated_application['rejection_reason'] = self._generate_rejection_reason(
                        risk_level, document_status, application_data
                    )
                    updated_application['application_notes'].append(
                        f"申请被拒绝，原因：{updated_application['rejection_reason']}"
                    )
            
            return updated_application
        
        # 默认情况，保持当前状态
        return updated_application

    def _calculate_approval_probability(self, risk_level: str, default_probability: float,
                                    application_data: Dict[str, Any], 
                                    customer_data: Dict[str, Any]) -> float:
        """计算申请获批的概率"""
        # 基础批准概率与风险等级相关
        base_probabilities = {
            'low': 0.95,        # 低风险申请几乎都会批准
            'medium': 0.75,     # 中风险申请大部分会批准
            'high': 0.40,       # 高风险申请不太容易批准
            'very_high': 0.15   # 极高风险申请很难批准
        }
        
        base_prob = base_probabilities.get(risk_level, 0.5)
        
        # 调整因素：文档完整性
        document_status = application_data.get('document_status', {})
        incomplete_docs = [doc for doc, status in document_status.items() 
                        if status in ['pending', 'issue']]
        
        doc_factor = 1.0 - (len(incomplete_docs) / max(1, len(document_status))) * 0.5
        
        # 调整因素：VIP客户
        vip_factor = 1.2 if customer_data.get('is_vip', False) else 1.0
        
        # 调整因素：历史申请记录
        previous_applications = application_data.get('previous_applications', [])
        history_factor = 1.0
        
        if previous_applications:
            # 有历史拒绝记录的客户获批率降低
            rejected_count = sum(1 for app in previous_applications if app.get('status') == 'rejected')
            if rejected_count > 0:
                history_factor = max(0.6, 1.0 - (rejected_count * 0.2))
        
        # 调整因素：贷款金额
        amount_factor = 1.0
        loan_amount = application_data.get('loan_amount', 100000)
        if loan_amount > 500000:
            amount_factor = 0.9  # 大额贷款批准概率略低
        
        # 计算最终批准概率
        final_probability = base_prob * doc_factor * vip_factor * history_factor * amount_factor
        
        # 确保概率在有效范围内
        return max(0.05, min(0.98, final_probability))

    def _generate_approval_details(self, loan_data: Dict[str, Any], 
                                application_data: Dict[str, Any],
                                risk_level: str) -> Dict[str, Any]:
        """生成贷款批准详情"""
        # 原始申请信息
        requested_amount = application_data.get('loan_amount', 100000)
        requested_term = application_data.get('loan_term_months', 36)
        
        # 根据风险等级可能调整贷款条件
        approved_amount = requested_amount
        approved_term = requested_term
        
        # 高风险贷款可能减少金额或期限
        if risk_level == 'high':
            if random.random() < 0.3:
                approved_amount = requested_amount * random.uniform(0.7, 0.9)
        elif risk_level == 'very_high':
            if random.random() < 0.6:
                approved_amount = requested_amount * random.uniform(0.5, 0.8)
            if random.random() < 0.4:
                approved_term = max(12, int(requested_term * 0.8))
        
        # 四舍五入金额到整数
        approved_amount = round(approved_amount)
        
        # 获取基础利率
        base_interest_rate = loan_data.get('interest_rate', 0.05)
        
        # 根据风险等级调整利率
        interest_adjustment = 0.0
        if risk_level == 'medium':
            interest_adjustment = 0.005  # 上浮0.5%
        elif risk_level == 'high':
            interest_adjustment = 0.01   # 上浮1%
        elif risk_level == 'very_high':
            interest_adjustment = 0.02   # 上浮2%
        
        adjusted_interest_rate = base_interest_rate + interest_adjustment
        
        # 是否需要担保
        requires_guarantor = risk_level in ['high', 'very_high']
        
        # 是否需要抵押
        requires_collateral = risk_level == 'very_high' or (
            risk_level == 'high' and requested_amount > 300000
        )
        
        # 生成批准条件
        approval_details = {
            'approved_amount': approved_amount,
            'approved_term_months': approved_term,
            'interest_rate': adjusted_interest_rate,
            'annual_percentage_rate': adjusted_interest_rate + 0.003,  # APR通常略高于利率
            'requires_guarantor': requires_guarantor,
            'requires_collateral': requires_collateral,
            'approval_date': datetime.now(),
            'validity_period_days': 30,  # 批准有效期30天
            'early_repayment_penalty': 0.02 if adjusted_interest_rate > 0.06 else 0.01,  # 提前还款违约金
            'special_conditions': []
        }
        
        # 添加特殊条件
        if approved_amount < requested_amount:
            approval_details['special_conditions'].append(
                f"批准金额({approved_amount:,.2f}元)低于申请金额({requested_amount:,.2f}元)，原因：风险控制"
            )
        
        if approved_term < requested_term:
            approval_details['special_conditions'].append(
                f"批准期限({approved_term}个月)短于申请期限({requested_term}个月)，原因：风险控制"
            )
        
        if interest_adjustment > 0:
            approval_details['special_conditions'].append(
                f"利率上浮{interest_adjustment:.1%}，原因：风险定价"
            )
        
        if requires_guarantor:
            approval_details['special_conditions'].append(
                "需要提供担保人，担保人须满足：年收入不低于10万元，信用评分不低于650分"
            )
        
        if requires_collateral:
            approval_details['special_conditions'].append(
                "需要提供抵押物，抵押物价值不低于贷款金额的120%"
            )
        
        return approval_details

    def _generate_rejection_reason(self, risk_level: str, 
                                document_status: Dict[str, str],
                                application_data: Dict[str, Any]) -> str:
        """生成拒绝原因"""
        # 可能的拒绝原因
        reasons = [
            '申请人信用评分不足',
            '收入证明不足以支持贷款额度',
            '债务收入比过高',
            '申请材料不完整或有误',
            '申请人当前负债水平过高',
            '无法验证申请人的收入来源',
            '申请人就业历史不稳定',
            '申请人有严重的历史逾期记录'
        ]
        
        # 根据风险等级和文档状态选择更可能的原因
        if risk_level in ['high', 'very_high']:
            # 高风险申请可能因信用问题被拒
            high_risk_reasons = [
                '申请人信用评分不足',
                '申请人有严重的历史逾期记录',
                '申请人当前负债水平过高',
                '债务收入比过高'
            ]
            return random.choice(high_risk_reasons)
        
        # 检查文档状态问题
        incomplete_docs = [doc for doc, status in document_status.items() 
                        if status in ['pending', 'issue']]
        
        if incomplete_docs:
            return f"申请材料不完整，缺少：{', '.join(incomplete_docs)}"
        
        # 检查历史申请
        if not application_data.get('is_first_application', True):
            previous_applications = application_data.get('previous_applications', [])
            rejected_apps = [app for app in previous_applications if app.get('status') == 'rejected']
            
            if rejected_apps and random.random() < 0.4:
                previous_reason = rejected_apps[0].get('rejection_reason', '')
                if previous_reason:
                    return f"与之前申请拒绝原因相同：{previous_reason}"
        
        # 随机选择一个一般原因
        return random.choice(reasons)
    
    def generate_application_tracking(self, application_data: Dict[str, Any], 
                                include_internal_events: bool = True) -> List[Dict[str, Any]]:
        """
        生成申请跟踪记录，记录申请处理过程中的各种事件和活动
        
        Args:
            application_data: 申请数据
            include_internal_events: 是否包含内部处理事件
            
        Returns:
            List[Dict[str, Any]]: 申请跟踪记录列表
        """
        tracking_records = []
        
        # 获取基本信息
        application_id = application_data.get('application_id', '')
        customer_id = application_data.get('customer_id', '')
        application_date = application_data.get('application_date')
        current_status = application_data.get('application_status', 'submitted')
        
        # 1. 申请提交事件
        tracking_records.append({
            'event_id': f"EVT-{application_id}-{1:03d}",
            'application_id': application_id,
            'customer_id': customer_id,
            'event_type': 'application_submitted',
            'event_date': application_date,
            'event_details': {
                'channel': application_data.get('channel', '网银'),
                'loan_type': application_data.get('loan_type', '个人消费贷'),
                'loan_amount': application_data.get('loan_amount', 0),
                'submitted_documents': [doc for doc, status in 
                                    application_data.get('document_status', {}).items() 
                                    if status == 'submitted']
            },
            'actor': 'customer',
            'visibility': 'public'  # 客户可见
        })
        
        # 2. 申请接收确认事件
        confirmation_date = application_date + timedelta(minutes=random.randint(5, 60))
        tracking_records.append({
            'event_id': f"EVT-{application_id}-{2:03d}",
            'application_id': application_id,
            'customer_id': customer_id,
            'event_type': 'application_received',
            'event_date': confirmation_date,
            'event_details': {
                'confirmation_code': f"CNF-{application_id[:8]}",
                'expected_processing_days': application_data.get('expected_processing_days', 5),
                'expected_decision_date': application_data.get('expected_decision_date')
            },
            'actor': 'system',
            'visibility': 'public'  # 客户可见
        })
        
        # 3. 文档接收和验证事件
        if include_internal_events:
            doc_verification_date = confirmation_date + timedelta(hours=random.randint(1, 24))
            tracking_records.append({
                'event_id': f"EVT-{application_id}-{3:03d}",
                'application_id': application_id,
                'customer_id': customer_id,
                'event_type': 'document_verification',
                'event_date': doc_verification_date,
                'event_details': {
                    'verified_documents': list(application_data.get('document_status', {}).keys()),
                    'document_issues': [doc for doc, status in 
                                    application_data.get('document_status', {}).items() 
                                    if status == 'issue']
                },
                'actor': f"AGENT-{random.randint(1000, 9999)}",
                'visibility': 'internal'  # 仅内部可见
            })
        
        # 4. 文档补充请求事件
        if 'document_request_date' in application_data:
            doc_request_date = application_data['document_request_date']
            incomplete_docs = [doc for doc, status in 
                            application_data.get('document_status', {}).items() 
                            if status in ['pending', 'issue']]
            
            tracking_records.append({
                'event_id': f"EVT-{application_id}-{4:03d}",
                'application_id': application_id,
                'customer_id': customer_id,
                'event_type': 'additional_documents_requested',
                'event_date': doc_request_date,
                'event_details': {
                    'requested_documents': incomplete_docs,
                    'reason': '审核过程中发现文档不完整或存在问题',
                    'deadline': doc_request_date + timedelta(days=10)
                },
                'actor': f"AGENT-{random.randint(1000, 9999)}",
                'visibility': 'public'  # 客户可见
            })
        
        # 5. 文档补充完成事件
        if 'documents_completed_date' in application_data:
            docs_completed_date = application_data['documents_completed_date']
            tracking_records.append({
                'event_id': f"EVT-{application_id}-{5:03d}",
                'application_id': application_id,
                'customer_id': customer_id,
                'event_type': 'documents_completed',
                'event_date': docs_completed_date,
                'event_details': {
                    'submitted_documents': [doc for doc, status in 
                                        application_data.get('document_status', {}).items() 
                                        if status == 'submitted'],
                    'next_step': '申请进入审核阶段'
                },
                'actor': 'customer',
                'visibility': 'public'  # 客户可见
            })
        
        # 6. 初步审核事件
        if current_status in ['under_review', 'risk_assessment', 'pending_decision', 'approved', 'rejected']:
            review_start_date = application_data.get('documents_completed_date', 
                                                application_date + timedelta(days=1))
            
            if include_internal_events:
                tracking_records.append({
                    'event_id': f"EVT-{application_id}-{6:03d}",
                    'application_id': application_id,
                    'customer_id': customer_id,
                    'event_type': 'initial_review',
                    'event_date': review_start_date + timedelta(days=1),
                    'event_details': {
                        'reviewer_id': f"REVIEWER-{random.randint(1000, 9999)}",
                        'review_result': '通过初审，进入详细审核',
                        'initial_risk_level': application_data.get('initial_risk_assessment', {}).get('initial_risk_level', 'medium')
                    },
                    'actor': 'credit_officer',
                    'visibility': 'internal'  # 仅内部可见
                })
            
            # 客户可见的审核进度更新
            tracking_records.append({
                'event_id': f"EVT-{application_id}-{7:03d}",
                'application_id': application_id,
                'customer_id': customer_id,
                'event_type': 'application_status_update',
                'event_date': review_start_date + timedelta(days=2),
                'event_details': {
                    'status': '审核中',
                    'message': '您的贷款申请正在审核中，请耐心等待',
                    'expected_completion_date': application_data.get('expected_decision_date')
                },
                'actor': 'system',
                'visibility': 'public'  # 客户可见
            })
        
        # 7. 风险评估事件
        if 'risk_assessment' in application_data or current_status in ['risk_assessment', 'pending_decision', 'approved', 'rejected']:
            risk_assessment_date = application_data.get('risk_assessment_completed_date', 
                                                    application_date + timedelta(days=5))
            
            if include_internal_events:
                risk_assessment = application_data.get('risk_assessment', 
                                                application_data.get('initial_risk_assessment', {}))
                tracking_records.append({
                    'event_id': f"EVT-{application_id}-{8:03d}",
                    'application_id': application_id,
                    'customer_id': customer_id,
                    'event_type': 'risk_assessment',
                    'event_date': risk_assessment_date,
                    'event_details': {
                        'risk_level': risk_assessment.get('risk_level', 'medium'),
                        'default_probability': risk_assessment.get('default_probability', 0.1),
                        'assessor_id': risk_assessment.get('assessor_id', f"RA-{random.randint(1000, 9999)}"),
                        'assessment_notes': '详细风险评估已完成'
                    },
                    'actor': 'risk_officer',
                    'visibility': 'internal'  # 仅内部可见
                })
        
        # 8. 最终审批事件
        if current_status in ['pending_decision', 'approved', 'rejected']:
            decision_date = application_data.get('decision_date', 
                                            application_date + timedelta(days=7))
            
            if include_internal_events:
                tracking_records.append({
                    'event_id': f"EVT-{application_id}-{9:03d}",
                    'application_id': application_id,
                    'customer_id': customer_id,
                    'event_type': 'approval_committee',
                    'event_date': decision_date - timedelta(hours=random.randint(1, 24)),
                    'event_details': {
                        'committee_id': f"COM-{random.randint(100, 999)}",
                        'members': [f"MEMBER-{random.randint(1000, 9999)}" for _ in range(3)],
                        'decision': '批准' if current_status == 'approved' else '拒绝',
                        'notes': '贷款审批委员会已做出最终决定'
                    },
                    'actor': 'approval_committee',
                    'visibility': 'internal'  # 仅内部可见
                })
        
        # 9. 决策通知事件
        if current_status in ['approved', 'rejected']:
            decision_date = application_data.get('decision_date')
            
            if decision_date:
                tracking_records.append({
                    'event_id': f"EVT-{application_id}-{10:03d}",
                    'application_id': application_id,
                    'customer_id': customer_id,
                    'event_type': 'decision_notification',
                    'event_date': decision_date,
                    'event_details': {
                        'decision': '批准' if current_status == 'approved' else '拒绝',
                        'reason': application_data.get('rejection_reason', '') if current_status == 'rejected' else '',
                        'approved_amount': application_data.get('approval_details', {}).get('approved_amount', 0) 
                                    if current_status == 'approved' else 0,
                        'notification_method': random.choice(['短信', '邮件', 'APP推送'])
                    },
                    'actor': 'system',
                    'visibility': 'public'  # 客户可见
                })
        
        # 10. 审批详情发送事件
        if current_status == 'approved':
            approval_details = application_data.get('approval_details', {})
            if approval_details:
                detail_notification_date = application_data.get('decision_date') + timedelta(hours=random.randint(1, 24))
                tracking_records.append({
                    'event_id': f"EVT-{application_id}-{11:03d}",
                    'application_id': application_id,
                    'customer_id': customer_id,
                    'event_type': 'approval_details_sent',
                    'event_date': detail_notification_date,
                    'event_details': {
                        'approved_amount': approval_details.get('approved_amount', 0),
                        'approved_term_months': approval_details.get('approved_term_months', 0),
                        'interest_rate': approval_details.get('interest_rate', 0),
                        'special_conditions': approval_details.get('special_conditions', []),
                        'contract_url': f"https://bank.example.com/contracts/{application_id}",
                        'validity_period_days': approval_details.get('validity_period_days', 30)
                    },
                    'actor': 'system',
                    'visibility': 'public'  # 客户可见
                })
        
        # 11. 客户取消申请事件
        if current_status == 'cancelled':
            cancellation_date = application_data.get('cancellation_date')
            if cancellation_date:
                tracking_records.append({
                    'event_id': f"EVT-{application_id}-{12:03d}",
                    'application_id': application_id,
                    'customer_id': customer_id,
                    'event_type': 'application_cancelled',
                    'event_date': cancellation_date,
                    'event_details': {
                        'reason': application_data.get('cancellation_reason', '客户要求取消'),
                        'cancellation_method': random.choice(['电话', '网银', 'APP'])
                    },
                    'actor': 'customer' if 'customer' in application_data.get('cancellation_reason', '').lower() else 'system',
                    'visibility': 'public'  # 客户可见
                })
        
        # 12. 添加申请备注的事件
        notes = application_data.get('application_notes', [])
        for i, note in enumerate(notes):
            if include_internal_events:
                # 为每条备注创建一个事件，但要确保事件时间符合逻辑顺序
                note_date = application_date + timedelta(days=i+1, hours=random.randint(0, 8))
                
                # 根据备注内容确定actor
                actor = 'system'
                if 'VIP' in note:
                    actor = 'relationship_manager'
                elif '补充材料' in note:
                    actor = 'document_officer'
                elif '风险' in note:
                    actor = 'risk_officer'
                elif '审核' in note:
                    actor = 'credit_officer'
                
                tracking_records.append({
                    'event_id': f"EVT-{application_id}-NOTE-{i+1:03d}",
                    'application_id': application_id,
                    'customer_id': customer_id,
                    'event_type': 'application_note',
                    'event_date': note_date,
                    'event_details': {
                        'note': note,
                        'note_category': self._categorize_note(note)
                    },
                    'actor': actor,
                    'visibility': 'internal'  # 仅内部可见
                })
        
        # 按事件日期排序
        tracking_records.sort(key=lambda x: x['event_date'])
        
        # 更新事件ID以反映正确的顺序
        for i, record in enumerate(tracking_records):
            record['event_id'] = f"EVT-{application_id}-{i+1:03d}"
        
        return tracking_records

    def _categorize_note(self, note: str) -> str:
        """根据备注内容分类"""
        if '补充材料' in note or '文档' in note:
            return '文档相关'
        elif 'VIP' in note:
            return '客户关系'
        elif '风险' in note:
            return '风险评估'
        elif '审核' in note or '批准' in note or '拒绝' in note:
            return '审批决策'
        else:
            return '一般备注'
        
    def generate_loan_record_from_application(self, application_data: Dict[str, Any], 
                                        customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据批准的申请生成完整的贷款记录
        
        Args:
            application_data: 已批准的申请数据
            customer_data: 客户相关数据
            
        Returns:
            Dict[str, Any]: 贷款记录数据
        """
        # 检查申请是否已批准
        if application_data.get('application_status') != 'approved':
            raise ValueError("只能从已批准的申请生成贷款记录")
        
        # 获取申请和批准详情
        application_id = application_data.get('application_id', '')
        customer_id = application_data.get('customer_id', '')
        approval_details = application_data.get('approval_details', {})
        
        # 生成贷款ID
        loan_id = f"LOAN-{datetime.now().strftime('%Y%m%d')}-{random.randint(10000, 99999)}"
        
        # 确定放款日期（通常是决策后1-3天）
        decision_date = application_data.get('decision_date')
        disbursement_date = decision_date + timedelta(days=random.randint(1, 3))
        
        # 确定首个还款日期（通常是下个月的固定日期）
        # 选择1-28之间的一个日期作为每月还款日
        repayment_day = random.randint(1, 28)
        first_payment_date = disbursement_date.replace(day=1) + timedelta(days=32)  # 下个月
        first_payment_date = first_payment_date.replace(day=min(repayment_day, 28))  # 设置为还款日
        
        # 生成贷款记录
        loan_record = {
            'loan_id': loan_id,
            'application_id': application_id,
            'customer_id': customer_id,
            'loan_type': application_data.get('loan_type', 'personal_consumption'),
            'account_id': f"ACC-{random.randint(100000, 999999)}",
            'loan_amount': approval_details.get('approved_amount'),
            'loan_term_months': approval_details.get('approved_term_months'),
            'interest_rate': approval_details.get('interest_rate'),
            'annual_percentage_rate': approval_details.get('annual_percentage_rate'),
            'repayment_method': self._determine_repayment_method(application_data),
            'disbursement_date': disbursement_date,
            'maturity_date': disbursement_date + timedelta(days=30 * approval_details.get('approved_term_months', 36)),
            'repayment_day': repayment_day,
            'first_payment_date': first_payment_date,
            'status': 'active',
            'current_balance': approval_details.get('approved_amount'),
            'next_payment_amount': self._calculate_monthly_payment(
                approval_details.get('approved_amount'),
                approval_details.get('interest_rate'),
                approval_details.get('approved_term_months')
            ),
            'next_payment_date': first_payment_date,
            'payment_history': [],
            'early_repayment_penalty': approval_details.get('early_repayment_penalty', 0.01),
            'special_conditions': approval_details.get('special_conditions', []),
            'created_at': datetime.now(),
            'risk_level': application_data.get('risk_assessment', {}).get('risk_level', 
                                                                    application_data.get('initial_risk_assessment', {}).get('initial_risk_level', 'medium'))
        }
        
        # 添加担保和抵押信息（如果适用）
        if approval_details.get('requires_guarantor', False):
            loan_record['guarantor'] = {
                'required': True,
                'status': 'pending',  # 担保人信息尚未提供
                'requirements': '年收入不低于10万元，信用评分不低于650分'
            }
        
        if approval_details.get('requires_collateral', False):
            loan_record['collateral'] = {
                'required': True,
                'status': 'pending',  # 抵押物信息尚未提供
                'requirements': '抵押物价值不低于贷款金额的120%'
            }
        
        return loan_record

    def _determine_repayment_method(self, application_data: Dict[str, Any]) -> str:
        """根据申请信息确定还款方式"""
        # 如果申请中已经有指定的还款方式，优先使用
        if 'repayment_method' in application_data:
            return application_data['repayment_method']
        
        # 根据贷款类型选择合适的还款方式
        loan_type = application_data.get('loan_type', 'personal_consumption')
        loan_term = application_data.get('approval_details', {}).get('approved_term_months', 36)
        
        if loan_type == 'mortgage':
            # 房贷通常使用等额本息或等额本金
            return random.choice(['等额本息', '等额本金'])
        elif loan_type == 'car':
            # 车贷通常使用等额本息
            return '等额本息'
        elif loan_term <= 6:
            # 短期贷款可能使用一次性还本付息
            return random.choice(['等额本息', '一次性还本付息'])
        else:
            # 默认使用等额本息
            return '等额本息'

    def _calculate_monthly_payment(self, loan_amount: float, interest_rate: float, term_months: int) -> float:
        """计算月供"""
        # 转换年利率为月利率
        monthly_rate = interest_rate / 12
        
        # 等额本息计算公式
        if monthly_rate > 0:
            payment = loan_amount * monthly_rate * (1 + monthly_rate) ** term_months / \
                    ((1 + monthly_rate) ** term_months - 1)
        else:
            # 零利率情况
            payment = loan_amount / term_months
        
        return round(payment, 2)