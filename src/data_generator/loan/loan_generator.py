#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
借款记录生成器模块

负责生成符合CDP业务单据范式的借款记录数据。
"""

from src.time_manager.time_manager import get_time_manager
from src.logger import get_logger
from src.data_generator.base_generators import BaseDocGenerator
from src.data_generator.loan.loan_application import LoanApplicationModel
from src.data_generator.loan.loan_approval import LoanApprovalModel
from src.data_generator.loan.loan_repayment import LoanRepaymentModel
from src.data_generator.loan.loan_risk import LoanRiskModel
from src.data_generator.loan.loan_parameters import LoanParametersModel
from src.data_generator.loan.loan_status import LoanStatusModel


import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Union

class LoanRecordGenerator:
    """
    贷款记录生成器，负责整合各个模块，生成完整的贷款记录：
    - 调用各子模块生成数据
    - 确保数据一致性和完整性
    - 支持历史数据和实时数据生成
    - 处理异常情况和边界条件
    """
    
    def __init__(self, config: Dict[str, Any], 
                parameter_model=None, 
                application_model=None, 
                approval_model=None, 
                repayment_model=None, 
                risk_model=None, 
                status_model=None):
        """
        初始化贷款记录生成器
        
        Args:
            config: 配置参数
            parameter_model: 贷款参数模型
            application_model: 贷款申请模型
            approval_model: 贷款审批模型
            repayment_model: 贷款还款模型
            risk_model: 贷款风险模型
            status_model: 贷款状态模型
        """
        self.config = config
        self.parameter_model = parameter_model
        self.application_model = application_model
        self.approval_model = approval_model
        self.repayment_model = repayment_model
        self.risk_model = risk_model
        self.status_model = status_model
        
        # 贷款ID计数器
        self.loan_id_counter = random.randint(10000, 99999)
        
        # 从配置中获取贷款类型分布
        self.loan_type_distribution = config.get('loan', {}).get('type_distribution', {
            'personal_consumption': 0.40,  # 个人消费贷
            'mortgage': 0.30,              # 住房贷款
            'car': 0.12,                   # 汽车贷款
            'education': 0.08,             # 教育贷款
            'small_business': 0.10         # 小微企业贷
        })
    
    def generate_loan(self, customer_data: Dict[str, Any], 
                    start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None,
                    loan_type: Optional[str] = None,
                    loan_amount: Optional[float] = None,
                    loan_term_months: Optional[int] = None) -> Dict[str, Any]:
        """
        生成完整的贷款记录，包括申请、审批、还款等全流程数据
        
        Args:
            customer_data: 客户数据
            start_date: 贷款开始日期，默认为随机生成
            end_date: 贷款结束日期，默认为当前日期
            loan_type: 指定贷款类型，默认随机选择
            loan_amount: 指定贷款金额，默认基于客户数据计算
            loan_term_months: 指定贷款期限(月)，默认基于贷款类型决定
            
        Returns:
            Dict[str, Any]: 完整的贷款记录
        """
        # 如果没有指定结束日期，默认为当前日期
        if end_date is None:
            end_date = datetime.now()
        
        # 如果没有指定开始日期，默认在结束日期之前随机选择
        if start_date is None:
            # 随机选择1-365天之前的日期
            days_ago = random.randint(30, 365)
            start_date = end_date - timedelta(days=days_ago)
        
        # 确保开始日期早于结束日期
        if start_date >= end_date:
            raise ValueError("开始日期必须早于结束日期")
        
        # 1. 确定贷款类型（如果未指定）
        if loan_type is None:
            loan_type = self._select_loan_type(customer_data)
        
        # 2. 生成贷款参数（利率、金额、期限等）
        loan_parameters = self._generate_loan_parameters(
            customer_data, loan_type, loan_amount, loan_term_months
        )
        
        # 3. 生成贷款申请数据
        application_data = self._generate_application_data(
            customer_data, loan_parameters, start_date
        )
        
        # 4. 生成贷款审批数据
        approval_data = self._generate_approval_data(
            customer_data, application_data, loan_parameters
        )
        
        # 5. 基于审批结果生成贷款记录
        if approval_data.get('final_status') == 'approved':
            # 审批通过，生成贷款记录
            loan_record = self._generate_approved_loan_record(
                customer_data, application_data, approval_data, loan_parameters, start_date
            )
            
            # 6. 生成还款计划和还款记录
            repayment_data = self._generate_repayment_data(
                customer_data, loan_record, end_date
            )
            
            # 7. 更新贷款状态和状态历史
            status_data = self._generate_status_data(
                customer_data, loan_record, repayment_data, end_date
            )
            
            # 8. 合并所有数据到最终记录
            final_loan_record = self._merge_loan_data(
                loan_record, repayment_data, status_data
            )
            
            return final_loan_record
        else:
            # 审批拒绝，只返回申请和审批数据
            rejected_record = {
                'loan_id': f"LOAN-{start_date.strftime('%Y%m%d')}-{self._get_next_id()}",
                'customer_id': customer_data.get('customer_id', ''),
                'application_data': application_data,
                'approval_data': approval_data,
                'status': 'rejected',
                'rejection_reason': approval_data.get('rejection_details', {}).get('reason', '未指明原因'),
                'application_date': application_data.get('application_date'),
                'rejection_date': approval_data.get('decision_date'),
                'loan_type': loan_type
            }
            
            return rejected_record
    
    def _select_loan_type(self, customer_data: Dict[str, Any]) -> str:
        """选择合适的贷款类型"""
        # 获取贷款类型分布
        type_distribution = self.loan_type_distribution.copy()
        
        # 调整因素：客户特征可能影响贷款类型选择
        income = customer_data.get('annual_income', 60000)
        age = customer_data.get('age', 35)
        is_corporate = customer_data.get('is_corporate', False)
        
        # 企业客户更可能申请小微企业贷款
        if is_corporate:
            # 增加小微企业贷款概率，减少其他类型
            type_distribution['small_business'] = type_distribution.get('small_business', 0.1) * 5
            for k in ['personal_consumption', 'mortgage', 'car', 'education']:
                if k in type_distribution:
                    type_distribution[k] *= 0.2
        else:
            # 个人客户，根据收入和年龄调整
            if income > 200000:
                # 高收入更可能申请房贷
                type_distribution['mortgage'] = type_distribution.get('mortgage', 0.3) * 1.5
            elif income < 50000:
                # 低收入更可能申请消费贷
                type_distribution['personal_consumption'] = type_distribution.get('personal_consumption', 0.4) * 1.3
            
            # 年轻人更可能申请教育贷款
            if age < 25:
                type_distribution['education'] = type_distribution.get('education', 0.08) * 2
            
            # 中年人更可能申请房贷和车贷
            if 30 <= age <= 45:
                type_distribution['mortgage'] = type_distribution.get('mortgage', 0.3) * 1.2
                type_distribution['car'] = type_distribution.get('car', 0.12) * 1.2
        
        # 归一化概率
        total = sum(type_distribution.values())
        normalized_dist = {k: v/total for k, v in type_distribution.items()}
        
        # 根据概率选择类型
        types = list(normalized_dist.keys())
        weights = list(normalized_dist.values())
        
        return random.choices(types, weights=weights, k=1)[0]
    
    def _generate_loan_parameters(self, customer_data: Dict[str, Any], 
                                loan_type: str, 
                                loan_amount: Optional[float] = None,
                                loan_term_months: Optional[int] = None) -> Dict[str, Any]:
        """生成贷款参数"""
        # 如果有参数模型，使用模型生成
        if self.parameter_model:
            # 设置客户偏好（如果有指定金额或期限）
            preferred_amount = loan_amount
            preferred_term = loan_term_months
            
            # 使用参数模型生成完整参数
            return self.parameter_model.generate_loan_parameters(
                loan_type, customer_data, preferred_amount, preferred_term
            )
        
        # 没有参数模型，手动生成基础参数
        # 1. 贷款金额
        if loan_amount is None:
            # 基于客户收入和贷款类型估算合理金额
            annual_income = customer_data.get('annual_income', 60000)
            
            if loan_type == 'mortgage':
                # 住房贷款通常是年收入的4-6倍
                loan_amount = annual_income * random.uniform(4, 6)
            elif loan_type == 'car':
                # 车贷通常是年收入的0.5-1倍
                loan_amount = annual_income * random.uniform(0.5, 1)
            elif loan_type == 'personal_consumption':
                # 消费贷通常是年收入的0.3-0.8倍
                loan_amount = annual_income * random.uniform(0.3, 0.8)
            elif loan_type == 'education':
                # 教育贷款通常较小
                loan_amount = annual_income * random.uniform(0.2, 0.6)
            elif loan_type == 'small_business':
                # 小微企业贷款金额较大
                loan_amount = annual_income * random.uniform(1, 3)
            else:
                # 默认情况
                loan_amount = annual_income * random.uniform(0.5, 1)
            
            # 四舍五入到整百
            loan_amount = round(loan_amount / 100) * 100
        
        # 2. 贷款期限
        if loan_term_months is None:
            if loan_type == 'mortgage':
                # 住房贷款期限较长，通常15-30年
                loan_term_months = random.choice([180, 240, 300, 360])
            elif loan_type == 'car':
                # 车贷通常3-5年
                loan_term_months = random.choice([36, 48, 60])
            elif loan_type == 'personal_consumption':
                # 消费贷通常1-3年
                loan_term_months = random.choice([12, 24, 36])
            elif loan_type == 'education':
                # 教育贷款期限中等
                loan_term_months = random.choice([24, 36, 48])
            elif loan_type == 'small_business':
                # 小微企业贷款期限通常1-5年
                loan_term_months = random.choice([12, 24, 36, 48, 60])
            else:
                # 默认情况
                loan_term_months = random.choice([12, 24, 36])
        
        # 3. 利率
        # 基准利率
        base_rates = {
            'mortgage': 0.045,            # 房贷基准利率
            'car': 0.055,                 # 车贷基准利率
            'personal_consumption': 0.065, # 消费贷基准利率
            'education': 0.05,            # 教育贷基准利率
            'small_business': 0.06        # 小微企业贷基准利率
        }
        
        base_rate = base_rates.get(loan_type, 0.06)
        
        # 基于信用评分调整利率
        credit_score = customer_data.get('credit_score', 700)
        credit_adjustment = 0.0
        
        if credit_score >= 800:
            credit_adjustment = -0.01     # 优秀信用减息1%
        elif credit_score >= 700:
            credit_adjustment = -0.005    # 良好信用减息0.5%
        elif credit_score <= 600:
            credit_adjustment = 0.01      # 较差信用加息1%
        elif credit_score <= 500:
            credit_adjustment = 0.02      # 很差信用加息2%
        
        interest_rate = max(0.01, base_rate + credit_adjustment)
        
        # 4. 还款方式
        if loan_type == 'mortgage':
            # 房贷通常使用等额本息或等额本金
            repayment_method = random.choice(['等额本息', '等额本金'])
        elif loan_type == 'personal_consumption' and loan_term_months <= 12:
            # 短期消费贷可能使用一次性还本付息
            repayment_method = random.choice(['等额本息', '一次性还本付息'])
        else:
            # 大多数情况使用等额本息
            repayment_method = '等额本息'
        
        # 组合参数
        parameters = {
            'loan_type': loan_type,
            'loan_amount': loan_amount,
            'loan_term_months': loan_term_months,
            'interest_rate': interest_rate,
            'repayment_method': repayment_method,
            'annual_percentage_rate': interest_rate + 0.003,  # APR通常比名义利率高一些
            'early_repayment_penalty': 0.01  # 提前还款违约金通常为1%
        }
        
        return parameters
    
    def _get_next_id(self) -> str:
        """获取下一个贷款ID"""
        self.loan_id_counter += 1
        return str(self.loan_id_counter)
    
    def _generate_application_data(self, customer_data: Dict[str, Any], 
                             loan_parameters: Dict[str, Any], 
                             start_date: datetime) -> Dict[str, Any]:
        """
        生成贷款申请数据
        
        Args:
            customer_data: 客户数据
            loan_parameters: 贷款参数
            start_date: 申请开始日期
            
        Returns:
            Dict[str, Any]: 贷款申请数据
        """
        # 如果有申请模型，使用模型生成
        if self.application_model:
            # 组合贷款信息
            application_input = {
                'customer_id': customer_data.get('customer_id', ''),
                'loan_type': loan_parameters.get('loan_type', ''),
                'loan_amount': loan_parameters.get('loan_amount', 0),
                'loan_term_months': loan_parameters.get('loan_term_months', 0),
                'repayment_method': loan_parameters.get('repayment_method', '等额本息'),
                'is_vip_customer': customer_data.get('is_vip', False),
                'credit_score': customer_data.get('credit_score', 700),
                'annual_income': customer_data.get('annual_income', 60000),
                'is_corporate': customer_data.get('is_corporate', False)
            }
            
            # 使用申请模型生成数据
            return self.application_model.generate_application_data(
                customer_data, application_input, start_date
            )
        
        # 没有申请模型，手动生成基础申请数据
        loan_type = loan_parameters.get('loan_type', '')
        loan_amount = loan_parameters.get('loan_amount', 0)
        
        # 生成申请ID
        application_id = f"APP-{start_date.strftime('%Y%m%d')}-{self._get_next_id()}"
        
        # 选择申请渠道
        channels = ['网银', '手机APP', '网点柜台', '第三方平台']
        channel_weights = [0.3, 0.4, 0.2, 0.1]
        
        # 调整渠道权重基于客户属性
        age = customer_data.get('age', 35)
        if age < 30:
            # 年轻人更倾向于使用APP
            channel_weights = [0.2, 0.6, 0.1, 0.1]
        elif age > 60:
            # 老年人更倾向于使用柜台
            channel_weights = [0.1, 0.2, 0.6, 0.1]
        
        channel = random.choices(channels, weights=channel_weights, k=1)[0]
        
        # 生成申请所需文档
        documents = self._generate_required_documents(loan_type)
        
        # 模拟文档状态
        document_status = {}
        for doc in documents:
            # 大部分文档已提交，小部分待提交或有问题
            status = random.choices(
                ['submitted', 'pending', 'issue'],
                weights=[0.85, 0.10, 0.05],
                k=1
            )[0]
            document_status[doc] = status
        
        # 生成贷款用途
        purpose = self._generate_loan_purpose(loan_type)
        
        # 计算预计处理时间（天）
        processing_days = {
            'mortgage': random.randint(5, 15),
            'car': random.randint(3, 7),
            'personal_consumption': random.randint(1, 5),
            'education': random.randint(2, 7),
            'small_business': random.randint(5, 10)
        }.get(loan_type, random.randint(3, 7))
        
        # VIP客户处理时间缩短
        if customer_data.get('is_vip', False):
            processing_days = max(1, int(processing_days * 0.7))
        
        # 生成申请数据
        application_data = {
            'application_id': application_id,
            'customer_id': customer_data.get('customer_id', ''),
            'application_date': start_date,
            'channel': channel,
            'loan_type': loan_type,
            'loan_amount': loan_amount,
            'loan_term_months': loan_parameters.get('loan_term_months', 0),
            'purpose': purpose,
            'is_first_application': random.random() < 0.7,  # 70%概率是首次申请
            'documents': documents,
            'document_status': document_status,
            'expected_processing_days': processing_days,
            'expected_decision_date': start_date + timedelta(days=processing_days),
            'application_status': 'submitted',
            'is_vip_customer': customer_data.get('is_vip', False),
            'application_notes': []
        }
        
        # 添加申请备注
        if customer_data.get('is_vip', False):
            application_data['application_notes'].append("VIP客户申请，优先处理。")
        
        if customer_data.get('credit_score', 700) < 600:
            application_data['application_notes'].append("客户信用评分偏低，需重点关注收入证明和负债情况。")
        
        if loan_amount > 500000:
            application_data['application_notes'].append("大额贷款申请，需多人审核。")
        
        return application_data

    def _generate_required_documents(self, loan_type: str) -> List[str]:
        """生成贷款所需文档列表"""
        # 基础文档，所有贷款都需要
        base_documents = [
            '身份证明',
            '收入证明',
            '个人征信报告'
        ]
        
        # 根据贷款类型添加特定文档
        if loan_type == 'mortgage':
            additional_docs = [
                '房产信息',
                '购房合同',
                '首付款证明',
                '房产评估报告'
            ]
        elif loan_type == 'car':
            additional_docs = [
                '购车协议',
                '驾驶证',
                '首付款证明'
            ]
        elif loan_type == 'education':
            additional_docs = [
                '学生证/录取通知书',
                '学费单',
                '在校证明'
            ]
        elif loan_type == 'small_business':
            additional_docs = [
                '营业执照',
                '财务报表',
                '业务计划书',
                '税务登记证'
            ]
        else:
            # 个人消费贷等其他贷款
            additional_docs = [
                '工作证明',
                '银行流水'
            ]
        
        # 随机决定是否需要担保人
        if random.random() < 0.3:
            additional_docs.append('担保人资料')
        
        # 合并文档列表
        return base_documents + additional_docs

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
            'education': [
                '本科学费', '研究生学费', '出国留学', '职业培训',
                '技能提升', '证书考试'
            ],
            'small_business': [
                '经营周转', '扩大生产', '购买设备', '店面装修',
                '增加库存', '新产品研发', '支付员工工资', '偿还供应商'
            ]
        }
        
        # 获取特定贷款类型的用途列表，如果没有则使用默认列表
        type_purposes = purposes.get(loan_type, ['个人消费'])
        
        return random.choice(type_purposes)
    
    def _generate_approval_data(self, customer_data: Dict[str, Any],
                          application_data: Dict[str, Any],
                          loan_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成贷款审批数据
        
        Args:
            customer_data: 客户数据
            application_data: 申请数据
            loan_parameters: 贷款参数
            
        Returns:
            Dict[str, Any]: 贷款审批数据
        """
        # 如果有审批模型，使用模型生成
        if self.approval_model:
            # 准备申请数据
            application_for_approval = application_data.copy()
            # 在申请时可能没有风险评估，添加初步风险评估
            if 'initial_risk_assessment' not in application_for_approval and self.risk_model:
                default_probability = self.risk_model.calculate_default_probability(
                    customer_data, loan_parameters
                )
                risk_level = self.risk_model.determine_risk_level(
                    default_probability, loan_parameters
                )
                application_for_approval['initial_risk_assessment'] = {
                    'initial_risk_level': risk_level,
                    'default_probability': default_probability
                }
            
            # 使用审批模型生成完整审批流程
            approval_flow = self.approval_model.determine_approval_flow(application_for_approval)
            approval_process = self.approval_model.generate_approval_process(
                application_for_approval, approval_flow, application_data.get('application_date')
            )
            approval_decision = self.approval_model.generate_approval_decision(
                application_for_approval, approval_process, customer_data
            )
            
            # 生成完整审批数据
            return self.approval_model.generate_complete_approval(
                application_for_approval, customer_data, application_data.get('application_date')
            )
        
        # 没有审批模型，手动生成基础审批数据
        application_date = application_data.get('application_date', datetime.now())
        loan_type = loan_parameters.get('loan_type', '')
        loan_amount = loan_parameters.get('loan_amount', 0)
        
        # 计算审批处理时间（天）
        processing_days = application_data.get('expected_processing_days', 5)
        decision_date = application_date + timedelta(days=processing_days)
        
        # 获取风险等级
        risk_level = 'medium'  # 默认中等风险
        default_probability = 0.1  # 默认违约概率
        
        if self.risk_model:
            # 使用风险模型计算风险等级
            default_probability = self.risk_model.calculate_default_probability(
                customer_data, loan_parameters
            )
            risk_level = self.risk_model.determine_risk_level(
                default_probability, loan_parameters
            )
        else:
            # 简单风险评估
            credit_score = customer_data.get('credit_score', 700)
            if credit_score >= 750:
                risk_level = 'low'
                default_probability = 0.05
            elif credit_score >= 650:
                risk_level = 'medium'
                default_probability = 0.1
            elif credit_score >= 550:
                risk_level = 'high'
                default_probability = 0.2
            else:
                risk_level = 'very_high'
                default_probability = 0.3
        
        # 计算批准概率
        base_approval_probs = {
            'low': 0.95,      # 低风险批准率高
            'medium': 0.8,    # 中风险批准率适中
            'high': 0.4,      # 高风险批准率低
            'very_high': 0.15  # 极高风险很难批准
        }
        
        approval_prob = base_approval_probs.get(risk_level, 0.7)
        
        # 调整因素：贷款金额
        if loan_amount > 1000000:
            approval_prob *= 0.9  # 大额贷款批准率降低
        
        # 调整因素：VIP客户
        if customer_data.get('is_vip', False):
            approval_prob = min(0.98, approval_prob * 1.2)  # VIP客户批准率提高，但不超过98%
        
        # 决定是否批准
        is_approved = random.random() < approval_prob
        
        # 基础审批数据
        approval_data = {
            'application_id': application_data.get('application_id', ''),
            'customer_id': customer_data.get('customer_id', ''),
            'decision_date': decision_date,
            'decision_id': f"DEC-{decision_date.strftime('%Y%m%d')}-{self._get_next_id()}",
            'risk_level': risk_level,
            'default_probability': default_probability,
            'decision': 'approved' if is_approved else 'rejected',
            'final_status': 'approved' if is_approved else 'rejected'
        }
        
        # 如果批准，添加批准详情
        if is_approved:
            # 根据风险等级可能调整贷款条件
            approved_amount = loan_amount
            approved_interest_rate = loan_parameters.get('interest_rate', 0.05)
            
            if risk_level == 'high':
                # 高风险可能降低贷款额度或提高利率
                if random.random() < 0.5:
                    approved_amount = loan_amount * random.uniform(0.7, 0.9)
                    approved_amount = round(approved_amount / 100) * 100  # 四舍五入到整百
                
                approved_interest_rate += 0.01  # 高风险加息1%
            elif risk_level == 'very_high':
                # 极高风险一定会调整条件
                approved_amount = loan_amount * random.uniform(0.5, 0.8)
                approved_amount = round(approved_amount / 100) * 100  # 四舍五入到整百
                
                approved_interest_rate += 0.02  # 极高风险加息2%
            
            # 计算年化总费率
            service_fee_rate = 0.003  # 0.3%服务费
            annual_percentage_rate = approved_interest_rate + service_fee_rate
            
            # 是否需要担保人和抵押物
            requires_guarantor = risk_level in ['high', 'very_high']
            requires_collateral = risk_level == 'very_high' or (risk_level == 'high' and loan_amount > 300000)
            
            approval_data['approval_details'] = {
                'approved_amount': approved_amount,
                'approved_term_months': loan_parameters.get('loan_term_months', 36),
                'interest_rate': approved_interest_rate,
                'annual_percentage_rate': annual_percentage_rate,
                'requires_guarantor': requires_guarantor,
                'requires_collateral': requires_collateral,
                'validity_period_days': 30,  # 批准有效期30天
                'expiration_date': decision_date + timedelta(days=30),
                'special_conditions': []
            }
            
            # 添加特殊条件
            if approved_amount < loan_amount:
                approval_data['approval_details']['special_conditions'].append(
                    f"批准金额({approved_amount:,.2f}元)低于申请金额({loan_amount:,.2f}元)，原因：风险控制"
                )
            
            if approved_interest_rate > loan_parameters.get('interest_rate', 0.05):
                diff = approved_interest_rate - loan_parameters.get('interest_rate', 0.05)
                approval_data['approval_details']['special_conditions'].append(
                    f"利率上浮{diff:.1%}，原因：风险定价"
                )
            
            if requires_guarantor:
                approval_data['approval_details']['special_conditions'].append(
                    "需要提供担保人，担保人须满足：年收入不低于10万元，信用评分不低于650分"
                )
            
            if requires_collateral:
                approval_data['approval_details']['special_conditions'].append(
                    "需要提供抵押物，抵押物价值不低于贷款金额的120%"
                )
        else:
            # 拒绝原因
            reasons = [
                '信用评分不足',
                '收入证明不足以支持贷款额度',
                '债务收入比过高',
                '申请材料不完整或有误',
                '申请人当前负债水平过高',
                '无法验证申请人的收入来源'
            ]
            
            # 根据风险等级选择更可能的原因
            if risk_level in ['high', 'very_high']:
                high_risk_reasons = [
                    '信用评分不足',
                    '申请人有严重的历史逾期记录',
                    '申请人当前负债水平过高',
                    '债务收入比过高'
                ]
                reason = random.choice(high_risk_reasons)
            else:
                reason = random.choice(reasons)
            
            # 拒绝详情
            approval_data['rejection_details'] = {
                'reason': reason,
                'details': f"经审核，您的{reason}，不符合我行贷款条件。",
                'earliest_reapply_date': decision_date + timedelta(days=random.randint(30, 90)),
                'rejection_code': f"REJ-{random.randint(100, 999)}"
            }
        
        return approval_data
    
    def _generate_approved_loan_record(self, customer_data: Dict[str, Any],
                                 application_data: Dict[str, Any],
                                 approval_data: Dict[str, Any],
                                 loan_parameters: Dict[str, Any],
                                 start_date: datetime) -> Dict[str, Any]:
        """
        根据批准的申请生成贷款记录
        
        Args:
            customer_data: 客户数据
            application_data: 申请数据
            approval_data: 审批数据
            loan_parameters: 贷款参数
            start_date: 贷款开始日期
            
        Returns:
            Dict[str, Any]: 贷款记录
        """
        # 确保审批已批准
        if approval_data.get('decision') != 'approved':
            raise ValueError("只能从已批准的申请生成贷款记录")
        
        # 获取基本信息
        application_id = application_data.get('application_id', '')
        customer_id = customer_data.get('customer_id', '')
        approval_details = approval_data.get('approval_details', {})
        decision_date = approval_data.get('decision_date', start_date + timedelta(days=7))
        
        # 生成贷款ID
        loan_id = f"LOAN-{decision_date.strftime('%Y%m%d')}-{self._get_next_id()}"
        
        # 确定放款日期（通常是决策后1-3天）
        disbursement_date = decision_date + timedelta(days=random.randint(1, 3))
        
        # 确定首个还款日期（通常是下个月的固定日期）
        # 选择1-28之间的一个日期作为每月还款日
        repayment_day = random.randint(1, 28)
        first_payment_date = disbursement_date.replace(day=1) + timedelta(days=32)  # 下个月
        first_payment_date = first_payment_date.replace(day=min(repayment_day, 28))  # 设置为还款日
        
        # 确定到期日期
        loan_term_months = approval_details.get('approved_term_months', 
                                            loan_parameters.get('loan_term_months', 36))
        maturity_date = self._add_months(disbursement_date, loan_term_months)
        
        # 获取审批后的贷款金额和利率
        loan_amount = approval_details.get('approved_amount', 
                                        loan_parameters.get('loan_amount', 0))
        interest_rate = approval_details.get('interest_rate', 
                                        loan_parameters.get('interest_rate', 0.05))
        
        # 获取还款方式
        repayment_method = loan_parameters.get('repayment_method', '等额本息')
        
        # 贷款账户信息
        account_id = f"ACC-{random.randint(100000, 999999)}"
        
        # 生成贷款记录
        loan_record = {
            'loan_id': loan_id,
            'application_id': application_id,
            'customer_id': customer_id,
            'loan_type': loan_parameters.get('loan_type', '个人消费贷'),
            'account_id': account_id,
            'loan_amount': loan_amount,
            'interest_rate': interest_rate,
            'annual_percentage_rate': approval_details.get('annual_percentage_rate', 
                                                        interest_rate + 0.003),
            'loan_term_months': loan_term_months,
            'repayment_method': repayment_method,
            'disbursement_date': disbursement_date,
            'first_payment_date': first_payment_date,
            'maturity_date': maturity_date,
            'repayment_day': repayment_day,
            'creation_date': decision_date,
            'early_repayment_penalty': loan_parameters.get('early_repayment_penalty', 0.01),
            'special_conditions': approval_details.get('special_conditions', []),
            'risk_level': approval_data.get('risk_level', 'medium'),
            'initial_status': 'active',
            'is_vip_customer': customer_data.get('is_vip', False),
            'purpose': application_data.get('purpose', '个人消费')
        }
        
        # 添加担保和抵押信息（如果需要）
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
        
    def _generate_repayment_data(self, customer_data: Dict[str, Any],
                           loan_record: Dict[str, Any],
                           end_date: datetime) -> Dict[str, Any]:
        """
        生成贷款还款数据
        
        Args:
            customer_data: 客户数据
            loan_record: 贷款记录
            end_date: 截止日期
            
        Returns:
            Dict[str, Any]: 还款数据
        """
        # 如果有还款模型，使用模型生成
        if self.repayment_model:
            # 1. 生成还款计划
            repayment_schedule = self.repayment_model.generate_repayment_schedule(loan_record)
            
            # 2. 模拟实际还款行为
            repayment_history = self.repayment_model.simulate_repayment_behavior(
                loan_record, repayment_schedule, customer_data, end_date
            )
            
            # 3. 生成逾期报告（如果有逾期）
            overdue_records = [p for p in repayment_history if p.get('is_overdue', False)]
            overdue_report = None
            if overdue_records:
                overdue_report = self.repayment_model.generate_overdue_report(
                    loan_record, repayment_history, end_date
                )
            
            # 4. 生成还款摘要
            repayment_summary = self.repayment_model.generate_repayment_summary(
                loan_record, repayment_history, end_date
            )
            
            # 返回完整的还款数据
            return {
                'repayment_schedule': repayment_schedule,
                'repayment_history': repayment_history,
                'overdue_report': overdue_report,
                'repayment_summary': repayment_summary
            }
        
        # 没有还款模型，生成简单的还款数据
        # 贷款基本信息
        loan_amount = loan_record.get('loan_amount', 0)
        interest_rate = loan_record.get('interest_rate', 0.05)
        loan_term_months = loan_record.get('loan_term_months', 36)
        disbursement_date = loan_record.get('disbursement_date', datetime.now())
        repayment_method = loan_record.get('repayment_method', '等额本息')
        first_payment_date = loan_record.get('first_payment_date')
        
        # 简单的还款计划
        schedule = []
        
        # 将年利率转换为月利率
        monthly_rate = interest_rate / 12
        
        # 生成还款计划
        if repayment_method == '等额本息':
            # 计算月还款额
            if monthly_rate > 0:
                monthly_payment = loan_amount * monthly_rate * (1 + monthly_rate) ** loan_term_months / \
                                ((1 + monthly_rate) ** loan_term_months - 1)
            else:
                monthly_payment = loan_amount / loan_term_months
            
            remaining_principal = loan_amount
            
            for period in range(1, loan_term_months + 1):
                # 计算还款日期
                if period == 1:
                    payment_date = first_payment_date
                else:
                    payment_date = self._add_months(first_payment_date, period - 1)
                
                # 计算利息和本金
                interest = remaining_principal * monthly_rate
                principal = monthly_payment - interest
                
                # 如果是最后一期，处理舍入误差
                if period == loan_term_months:
                    principal = remaining_principal
                    monthly_payment = principal + interest
                
                # 更新剩余本金
                remaining_principal -= principal
                remaining_principal = max(0, remaining_principal)  # 确保不为负
                
                # 添加到计划
                schedule.append({
                    'period': period,
                    'payment_date': payment_date,
                    'principal': round(principal, 2),
                    'interest': round(interest, 2),
                    'total_payment': round(monthly_payment, 2),
                    'remaining_principal': round(remaining_principal, 2),
                    'status': 'scheduled'
                })
        
        # 模拟实际还款记录
        repayment_history = []
        
        for payment in schedule:
            # 仅处理截止日期之前的还款
            if payment['payment_date'] > end_date:
                # 将未到期的还款保存为计划中状态
                repayment_history.append(payment.copy())
                continue
            
            # 决定是否逾期
            is_overdue = False
            days_overdue = 0
            
            # 根据信用评分和风险等级决定逾期概率
            credit_score = customer_data.get('credit_score', 700)
            risk_level = loan_record.get('risk_level', 'medium')
            
            base_overdue_prob = {
                'low': 0.03,
                'medium': 0.08,
                'high': 0.15,
                'very_high': 0.25
            }.get(risk_level, 0.08)
            
            # 信用评分调整
            if credit_score >= 750:
                base_overdue_prob *= 0.5
            elif credit_score <= 600:
                base_overdue_prob *= 2
            
            # VIP客户调整
            if loan_record.get('is_vip_customer', False):
                base_overdue_prob *= 0.5
            
            # 随机决定是否逾期
            if random.random() < base_overdue_prob:
                is_overdue = True
                days_overdue = random.randint(1, 30)  # 1-30天的逾期
            
            # 创建实际还款记录
            actual_payment = payment.copy()
            
            if is_overdue:
                # 逾期还款
                actual_payment_date = payment['payment_date'] + timedelta(days=days_overdue)
                
                # 计算滞纳金和罚息
                late_fee = payment['total_payment'] * 0.0005 * days_overdue  # 0.05%每天
                penalty_interest = payment['principal'] * 0.0001 * days_overdue  # 0.01%每天
                
                actual_payment.update({
                    'actual_payment_date': actual_payment_date,
                    'actual_principal': payment['principal'],
                    'actual_interest': payment['interest'],
                    'late_fee': round(late_fee, 2),
                    'penalty_interest': round(penalty_interest, 2),
                    'actual_payment': round(payment['total_payment'] + late_fee + penalty_interest, 2),
                    'status': 'paid_late',
                    'is_overdue': True,
                    'days_overdue': days_overdue
                })
            else:
                # 正常还款
                # 生成实际还款日期（可能提前1-3天）
                days_early = random.randint(0, 3)
                actual_payment_date = payment['payment_date'] - timedelta(days=days_early)
                
                actual_payment.update({
                    'actual_payment_date': actual_payment_date,
                    'actual_principal': payment['principal'],
                    'actual_interest': payment['interest'],
                    'late_fee': 0,
                    'penalty_interest': 0,
                    'actual_payment': payment['total_payment'],
                    'status': 'paid',
                    'is_overdue': False,
                    'days_overdue': 0
                })
            
            repayment_history.append(actual_payment)
        
        # 简单的还款摘要
        # 计算已还款的数量
        completed_payments = len([p for p in repayment_history if p.get('status') in ['paid', 'paid_late']])
        total_payments = len(repayment_history)
        progress_percentage = (completed_payments / max(1, total_payments)) * 100
        
        # 计算已还本金和利息
        paid_principal = sum(p.get('actual_principal', 0) for p in repayment_history if p.get('status') in ['paid', 'paid_late'])
        paid_interest = sum(p.get('actual_interest', 0) for p in repayment_history if p.get('status') in ['paid', 'paid_late'])
        
        repayment_summary = {
            'total_payments': total_payments,
            'completed_payments': completed_payments,
            'progress_percentage': round(progress_percentage, 1),
            'total_paid_principal': round(paid_principal, 2),
            'total_paid_interest': round(paid_interest, 2),
            'remaining_principal': round(loan_amount - paid_principal, 2)
        }
        
        # 返回还款数据
        return {
            'repayment_schedule': schedule,
            'repayment_history': repayment_history,
            'repayment_summary': repayment_summary
        }
    
    def _generate_status_data(self, customer_data: Dict[str, Any],
                        loan_record: Dict[str, Any],
                        repayment_data: Dict[str, Any],
                        end_date: datetime) -> Dict[str, Any]:
        """
        生成贷款状态数据
        
        Args:
            customer_data: 客户数据
            loan_record: 贷款记录
            repayment_data: 还款数据
            end_date: 截止日期
            
        Returns:
            Dict[str, Any]: 状态数据
        """
        # 如果有状态模型，使用模型生成
        if self.status_model:
            # 获取贷款初始状态
            loan_type = loan_record.get('loan_type', 'personal_consumption')
            credit_score = customer_data.get('credit_score', 700)
            
            initial_status = self.status_model.get_initial_status(
                loan_type, credit_score, is_historical=True
            )
            
            # 生成状态时间线
            status_timeline = self.status_model.generate_status_timeline(
                initial_status, loan_record.get('disbursement_date', datetime.now()),
                loan_record, is_historical=True
            )
            
            # 生成状态事件
            status_events = self.status_model.generate_status_events(
                status_timeline, loan_record
            )
            
            # 获取当前状态
            current_status = self.status_model.get_status_at_date(
                status_timeline, end_date
            )
            
            # 生成状态摘要
            status_summary = self.status_model.get_status_summary(
                loan_record.get('loan_id', ''), loan_record, status_timeline
            )
            
            return {
                'current_status': current_status,
                'status_timeline': status_timeline,
                'status_events': status_events,
                'status_summary': status_summary
            }
        
        # 没有状态模型，根据还款情况生成基础状态数据
        repayment_history = repayment_data.get('repayment_history', [])
        repayment_summary = repayment_data.get('repayment_summary', {})
        
        # 贷款基本信息
        loan_amount = loan_record.get('loan_amount', 0)
        disbursement_date = loan_record.get('disbursement_date', datetime.now())
        maturity_date = loan_record.get('maturity_date', datetime.now())
        
        # 已还本金
        paid_principal = repayment_summary.get('total_paid_principal', 0)
        
        # 确定当前状态
        current_status = 'active'  # 默认状态
        
        # 检查是否已结清
        if paid_principal >= loan_amount * 0.99:  # 允许1%的舍入误差
            if end_date < maturity_date - timedelta(days=30):
                current_status = 'early_settled'  # 提前结清
            else:
                current_status = 'settled'  # 正常结清
        else:
            # 检查是否存在逾期
            current_overdue = False
            current_overdue_days = 0
            
            # 查找当前应还但未还的还款
            for payment in repayment_history:
                if payment.get('status') == 'scheduled' and payment.get('payment_date') < end_date:
                    current_overdue = True
                    current_overdue_days = (end_date - payment.get('payment_date')).days
                    break
            
            if current_overdue:
                if current_overdue_days > 90:
                    current_status = 'defaulted'  # 逾期超过90天视为违约
                else:
                    current_status = 'overdue'  # 逾期状态
        
        # 生成状态时间线
        status_timeline = []
        
        # 添加发放状态
        status_timeline.append({
            'status': 'disbursed',
            'start_date': disbursement_date,
            'end_date': disbursement_date + timedelta(days=1),
            'duration_days': 1
        })
        
        # 添加活动状态
        active_start = disbursement_date + timedelta(days=1)
        active_end = end_date
        
        # 如果当前不是活动状态，找到状态改变的时间点
        if current_status != 'active':
            # 查找状态改变的时间点
            if current_status in ['settled', 'early_settled']:
                # 最后一次成功还款日期视为结清日期
                last_payment = next((p for p in reversed(repayment_history) 
                                if p.get('status') in ['paid', 'paid_late']), None)
                if last_payment:
                    active_end = last_payment.get('actual_payment_date', end_date)
            elif current_status in ['overdue', 'defaulted']:
                # 第一次逾期的计划还款日期
                first_overdue = next((p for p in repayment_history 
                                if p.get('status') == 'scheduled' and p.get('payment_date') < end_date), None)
                if first_overdue:
                    active_end = first_overdue.get('payment_date', end_date)
        
        # 添加活动状态
        status_timeline.append({
            'status': 'active',
            'start_date': active_start,
            'end_date': active_end,
            'duration_days': (active_end - active_start).days
        })
        
        # 如果当前不是活动状态，添加当前状态
        if current_status != 'active':
            status_timeline.append({
                'status': current_status,
                'start_date': active_end,
                'end_date': end_date,
                'duration_days': (end_date - active_end).days
            })
        
        # 生成简单的状态摘要
        status_summary = {
            'loan_id': loan_record.get('loan_id', ''),
            'customer_id': customer_data.get('customer_id', ''),
            'current_status': current_status,
            'days_in_current_status': (end_date - status_timeline[-1]['start_date']).days,
            'has_risk': current_status in ['overdue', 'defaulted'],
            'completion_percentage': repayment_summary.get('progress_percentage', 0)
        }
        
        return {
            'current_status': current_status,
            'status_timeline': status_timeline,
            'status_summary': status_summary
        }
    
    def _merge_loan_data(self, loan_record: Dict[str, Any],
                    repayment_data: Dict[str, Any],
                    status_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        合并所有贷款数据到最终记录
        
        Args:
            loan_record: 贷款记录
            repayment_data: 还款数据
            status_data: 状态数据
            
        Returns:
            Dict[str, Any]: 最终的贷款记录
        """
        # 创建最终记录的副本
        final_record = loan_record.copy()
        
        # 添加还款数据
        final_record['repayment_schedule'] = repayment_data.get('repayment_schedule', [])
        final_record['repayment_history'] = repayment_data.get('repayment_history', [])
        final_record['repayment_summary'] = repayment_data.get('repayment_summary', {})
        
        # 如果有逾期报告，添加到记录
        if 'overdue_report' in repayment_data and repayment_data['overdue_report']:
            final_record['overdue_report'] = repayment_data['overdue_report']
        
        # 添加状态数据
        final_record['current_status'] = status_data.get('current_status', 'active')
        final_record['status_timeline'] = status_data.get('status_timeline', [])
        
        if 'status_events' in status_data:
            final_record['status_events'] = status_data['status_events']
        
        final_record['status_summary'] = status_data.get('status_summary', {})
        
        # 添加最后更新时间
        final_record['last_updated'] = datetime.now()
        
        # 计算并添加总体统计
        # 1. 已还本金和利息
        paid_principal = sum(p.get('actual_principal', 0) for p in final_record['repayment_history'] 
                        if p.get('status') in ['paid', 'paid_late'])
        paid_interest = sum(p.get('actual_interest', 0) for p in final_record['repayment_history'] 
                        if p.get('status') in ['paid', 'paid_late'])
        total_paid = paid_principal + paid_interest
        
        # 2. 逾期情况
        overdue_payments = sum(1 for p in final_record['repayment_history'] if p.get('is_overdue', False))
        overdue_fees = sum((p.get('late_fee', 0) + p.get('penalty_interest', 0)) 
                        for p in final_record['repayment_history'] if p.get('is_overdue', False))
        
        # 3. 剩余金额
        loan_amount = loan_record.get('loan_amount', 0)
        remaining_principal = loan_amount - paid_principal
        
        # 添加统计数据
        final_record['statistics'] = {
            'total_paid': round(total_paid, 2),
            'paid_principal': round(paid_principal, 2),
            'paid_interest': round(paid_interest, 2),
            'remaining_principal': round(max(0, remaining_principal), 2),
            'overdue_payments': overdue_payments,
            'overdue_fees': round(overdue_fees, 2),
            'completion_percentage': round((paid_principal / loan_amount) * 100 if loan_amount > 0 else 0, 1)
        }
        
        return final_record
    
    def generate_loans_batch(self, customer_data: Dict[str, Any],
                       count: int = 1,
                       start_date_range: Tuple[datetime, datetime] = None,
                       end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        批量生成多笔贷款记录
        
        Args:
            customer_data: 客户数据
            count: 生成贷款的数量
            start_date_range: 贷款开始日期范围，格式为(最早日期, 最晚日期)
            end_date: 贷款结束日期，默认为当前日期
            
        Returns:
            List[Dict[str, Any]]: 贷款记录列表
        """
        # 如果没有指定结束日期，默认为当前日期
        if end_date is None:
            end_date = datetime.now()
        
        # 如果没有指定开始日期范围，默认为结束日期前1-365天
        if start_date_range is None:
            earliest_date = end_date - timedelta(days=365)
            latest_date = end_date - timedelta(days=30)
            start_date_range = (earliest_date, latest_date)
        
        # 生成贷款记录
        loans = []
        
        for _ in range(count):
            # 随机选择开始日期
            days_range = (start_date_range[1] - start_date_range[0]).days
            if days_range <= 0:
                # 如果范围无效，使用默认范围
                days_ago = random.randint(30, 365)
                start_date = end_date - timedelta(days=days_ago)
            else:
                days_ago = random.randint(0, days_range)
                start_date = start_date_range[0] + timedelta(days=days_ago)
            
            # 生成贷款记录
            try:
                loan = self.generate_loan(customer_data, start_date, end_date)
                loans.append(loan)
            except Exception as e:
                print(f"生成贷款记录时出错：{e}")
        
        return loans