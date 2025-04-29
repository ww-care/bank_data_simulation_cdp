"""
理财购买生成相关工具类
提供一系列用于理财购买生成的辅助功能
"""

import uuid
import datetime
import random
from datetime import timedelta


class InvestmentUtils:
    """理财生成相关工具类"""

    @staticmethod
    def calculate_expected_return(amount, rate, days):
        """
        计算理财产品的预期收益
        
        Args:
            amount (float): 投资金额
            rate (float): 年化收益率，例如0.045表示4.5%
            days (int): 持有天数
        
        Returns:
            float: 预期收益金额
        """
        if amount <= 0 or rate < 0 or days <= 0:
            return 0
        
        # 标准计算方式：投资金额 * 年化收益率 * (持有天数/365)
        # 考虑闰年，更准确的计算可以使用实际天数
        expected_return = amount * rate * (days / 365.0)
        
        # 对于大额投资，进行精确计算（考虑复利）
        if amount >= 100000 and days > 90:  # 10万以上且超过90天
            # 使用复利公式：本金 * (1 + 收益率)^(天数/365) - 本金
            import math
            compounded_return = amount * (math.pow(1 + rate, days / 365.0) - 1)
            
            # 如果投资期限较长，使用复利计算结果
            if days >= 365:
                return round(compounded_return, 2)
            else:
                # 短期内使用平均值
                return round((expected_return + compounded_return) / 2, 2)
        
        # 一般情况下，使用简单计算方式，保留两位小数
        return round(expected_return, 2)
        
    @staticmethod
    def get_risk_level_mapping():
        """
        获取风险等级映射的默认值
        
        风险等级映射定义了客户风险偏好等级(R1-R5)与产品风险等级(low/medium/high)的对应关系
        和匹配权重
        
        Returns:
            dict: 风险等级映射关系字典
        """
        # 默认的风险等级映射
        default_mapping = {
            "R1": {
                "acceptable_risk": ["low"],  # R1客户只能接受低风险产品
                "weight": 1.0,               # 完全匹配权重
                "description": "保守型投资者，风险承受能力极低，只适合货币型、债券型等低风险产品"
            },
            "R2": {
                "acceptable_risk": ["low"], 
                "weight": 0.9,
                "description": "稳健型投资者，风险承受能力较低，主要适合低风险产品"
            },
            "R3": {
                "acceptable_risk": ["low", "medium"],  # R3客户可接受低风险和中风险产品
                "weight": 0.8,
                "description": "平衡型投资者，能够承受中等风险，适合低风险和中风险产品"
            },
            "R4": {
                "acceptable_risk": ["low", "medium", "high"],  # R4客户可接受所有风险等级产品
                "weight": 0.7,
                "description": "成长型投资者，风险承受能力较高，适合大部分产品类型"
            },
            "R5": {
                "acceptable_risk": ["low", "medium", "high"],
                "weight": 0.6,
                "description": "进取型投资者，风险承受能力高，适合所有产品类型，尤其适合高风险高收益产品"
            }
        }
        
        # 添加风险等级的数值映射，用于计算匹配分数
        risk_level_values = {
            "R1": 1,
            "R2": 2,
            "R3": 3,
            "R4": 4,
            "R5": 5
        }
        
        # 添加产品风险等级的数值映射
        product_risk_values = {
            "low": 1,
            "medium": 3,
            "high": 5
        }
        
        # 将数值映射加入到返回结果中
        return {
            "mappings": default_mapping,
            "risk_level_values": risk_level_values,
            "product_risk_values": product_risk_values
        }
        
    @staticmethod
    def normalize_amount(amount, min_investment=1000, rounding_base=100):
        """
        标准化投资金额，确保金额满足最低要求并符合常见投资行为
        
        Args:
            amount (float): 原始投资金额
            min_investment (float): 最低投资金额
            rounding_base (int): 取整基数，如100表示取整到百元
        
        Returns:
            float: 标准化后的投资金额
        """
        # 确保金额至少达到最低投资要求
        if amount < min_investment:
            return min_investment
        
        # 根据金额大小调整取整基数
        if amount >= 1000000:  # 百万以上按1万取整
            rounding_base = 10000
        elif amount >= 100000:  # 十万以上按千元取整
            rounding_base = 1000
        
        # 将金额调整为取整基数的倍数
        rounded_amount = round(amount / rounding_base) * rounding_base
        
        # 如果是大额资金，避免出现过于整的数字（如1000000），增加真实感
        if rounded_amount >= 100000:
            # 获取调整范围（基数的10%）
            adjustment_range = rounding_base * 0.1
            
            # 根据金额可能上下浮动一些，增加真实感
            import random
            adjustment = random.uniform(-adjustment_range, adjustment_range)
            
            # 确保调整后的金额仍是合理的
            adjusted_amount = rounded_amount + adjustment
            
            # 确保不低于最低投资金额
            return max(min_investment, adjusted_amount)
        
        # 对于较小金额，直接返回取整后的值
        return rounded_amount
        
    @staticmethod
    def generate_transaction_id(prefix="INV", length=15):
        """
        生成唯一的理财交易ID
        
        Args:
            prefix (str): ID前缀，默认为"INV"(Investment的缩写)
            length (int): ID总长度，包含前缀，默认为15
        
        Returns:
            str: 生成的交易ID
        """
        import uuid
        import time
        
        # 获取当前时间戳（毫秒级）
        timestamp = int(time.time() * 1000)
        
        # 生成UUID的一部分（去掉横线后取前8位）
        short_uuid = str(uuid.uuid4()).replace('-', '')[:8]
        
        # 计算剩余长度（总长度减去前缀和已使用的时间戳、UUID部分）
        timestamp_str = str(timestamp)
        remaining_length = length - len(prefix) - len(short_uuid)
        
        # 如果剩余长度大于等于时间戳长度，使用完整时间戳
        if remaining_length >= len(timestamp_str):
            # 组合ID: 前缀 + 时间戳 + UUID
            transaction_id = f"{prefix}{timestamp_str}{short_uuid}"
            
            # 如果总长度还不够，用0填充
            if len(transaction_id) < length:
                transaction_id += '0' * (length - len(transaction_id))
            
            # 如果超出指定长度，截取到指定长度
            return transaction_id[:length]
        else:
            # 剩余长度不够放完整时间戳，使用时间戳的后几位
            timestamp_part = timestamp_str[-(remaining_length):]
            
            # 组合ID: 前缀 + UUID + 部分时间戳
            return f"{prefix}{short_uuid}{timestamp_part}"
        
    @staticmethod
    def calculate_maturity_date(purchase_date, term_months=0, term_days=0):
        """
        计算理财产品的到期日期
        
        Args:
            purchase_date (datetime.date/datetime.datetime): 购买日期
            term_months (int): 产品期限(月)，默认为0
            term_days (int): 产品期限(天)，默认为0
        
        Returns:
            datetime.date: 到期日期
        """
        import datetime
        import calendar
        
        # 确保purchase_date是日期类型
        if isinstance(purchase_date, str):
            try:
                # 尝试解析字符串格式的日期
                if 'T' in purchase_date or ' ' in purchase_date:  # 含时间部分
                    purchase_date = datetime.datetime.fromisoformat(purchase_date.replace('Z', '+00:00'))
                else:  # 只有日期部分
                    purchase_date = datetime.datetime.strptime(purchase_date, '%Y-%m-%d')
            except ValueError:
                # 尝试其他常见日期格式
                try:
                    purchase_date = datetime.datetime.strptime(purchase_date, '%Y/%m/%d')
                except ValueError:
                    raise ValueError(f"无法解析日期格式: {purchase_date}")
        
        # 提取date部分（如果是datetime类型）
        if isinstance(purchase_date, datetime.datetime):
            purchase_date = purchase_date.date()
        
        # 如果同时提供了月和天，将天数转换为月数的小数部分
        if term_months > 0 and term_days > 0:
            term_months += term_days / 30.0
            term_days = 0
        
        maturity_date = None
        
        # 按月计算到期日
        if term_months > 0:
            # 计算目标月份
            target_month = purchase_date.month + term_months
            target_year = purchase_date.year
            
            # 处理跨年的情况
            while target_month > 12:
                target_month -= 12
                target_year += 1
            
            # 获取当月最后一天
            last_day_of_month = calendar.monthrange(target_year, int(target_month))[1]
            
            # 确保日期有效（处理2月29日等特殊情况）
            target_day = min(purchase_date.day, last_day_of_month)
            
            # 处理月份的小数部分（转换为天数）
            fractional_months = term_months % 1
            additional_days = int(fractional_months * 30)
            
            # 创建目标日期
            maturity_date = datetime.date(target_year, int(target_month), target_day)
            
            # 添加额外天数
            if additional_days > 0:
                maturity_date += datetime.timedelta(days=additional_days)
        
        # 按天计算到期日
        elif term_days > 0:
            maturity_date = purchase_date + datetime.timedelta(days=term_days)
        
        # 如果没有提供有效期限，返回原日期
        else:
            maturity_date = purchase_date
        
        return maturity_date
        
    @staticmethod
    def get_redemption_time_distribution(product_type=None, is_workday=True):
        """
        获取赎回时间分布模型
        
        Args:
            product_type (str): 产品类型，如'monetary_fund'、'bond_fund'等
            is_workday (bool): 是否工作日，默认为True
        
        Returns:
            dict: 赎回时间分布模型，包含各时间段的权重
        """
        # 基础时间段分布（工作日）
        workday_distribution = {
            'morning': {  # 9:00-12:00
                'weight': 0.35,
                'peak_time': '10:30',
                'hours': list(range(9, 12))
            },
            'lunch': {  # 12:00-14:00
                'weight': 0.10,
                'peak_time': '13:00',
                'hours': [12, 13]
            },
            'afternoon': {  # 14:00-17:00
                'weight': 0.40,
                'peak_time': '15:30',
                'hours': list(range(14, 17))
            },
            'evening': {  # 17:00-21:00
                'weight': 0.15,
                'peak_time': '19:00',
                'hours': list(range(17, 21))
            }
        }
        
        # 非工作日分布
        weekend_distribution = {
            'morning': {  # 9:00-12:00
                'weight': 0.30,
                'peak_time': '11:00',
                'hours': list(range(9, 12))
            },
            'afternoon': {  # 12:00-17:00
                'weight': 0.45,
                'peak_time': '14:30',
                'hours': list(range(12, 17))
            },
            'evening': {  # 17:00-21:00
                'weight': 0.25,
                'peak_time': '18:30',
                'hours': list(range(17, 21))
            }
        }
        
        # 根据产品类型调整分布
        if product_type:
            base_distribution = workday_distribution if is_workday else weekend_distribution
            
            if product_type == 'monetary_fund':
                # 货币基金赎回更集中在下午（资金需求）
                if is_workday:
                    base_distribution['afternoon']['weight'] += 0.10
                    base_distribution['morning']['weight'] -= 0.05
                    base_distribution['evening']['weight'] -= 0.05
                    
            elif product_type == 'bond_fund':
                # 债券基金赎回比较均匀分布
                pass  # 保持默认分布
                
            elif product_type == 'stock_fund':
                # 股票型基金赎回更可能在上午（市场波动后反应）
                if is_workday:
                    base_distribution['morning']['weight'] += 0.10
                    base_distribution['afternoon']['weight'] -= 0.05
                    base_distribution['evening']['weight'] -= 0.05
                    
            elif product_type == 'mixed_fund':
                # 混合型基金介于债券和股票之间
                if is_workday:
                    base_distribution['morning']['weight'] += 0.05
                    base_distribution['afternoon']['weight'] -= 0.05
            
            # 归一化权重
            total_weight = sum(period['weight'] for period in base_distribution.values())
            if total_weight != 1.0:
                factor = 1.0 / total_weight
                for period in base_distribution.values():
                    period['weight'] *= factor
            
            return base_distribution
        
        # 返回基础分布
        return workday_distribution if is_workday else weekend_distribution
        
    @staticmethod
    def calculate_wealth_phase(customer_info, investments, reference_date=None):
        """
        计算财富客户阶段
        
        Args:
            customer_info (dict): 客户基本信息
            investments (list): 客户的投资记录列表
            reference_date (datetime.date, optional): 参考日期，默认为当前日期
        
        Returns:
            str: 财富客户阶段（注册/首投/老客/召回/流失）
        """
        import datetime
        
        # 使用当前日期作为默认参考日期
        if reference_date is None:
            reference_date = datetime.date.today()
        elif isinstance(reference_date, datetime.datetime):
            reference_date = reference_date.date()
        elif isinstance(reference_date, str):
            # 尝试解析字符串日期
            try:
                reference_date = datetime.datetime.strptime(reference_date, '%Y-%m-%d').date()
            except ValueError:
                try:
                    reference_date = datetime.datetime.strptime(reference_date, '%Y/%m/%d').date()
                except ValueError:
                    raise ValueError(f"无法解析日期格式: {reference_date}")
        
        # 如果没有投资记录，判断是否为新注册客户
        if not investments or len(investments) == 0:
            registration_date = customer_info.get('registration_date')
            
            # 转换注册日期格式（如果需要）
            if isinstance(registration_date, str):
                try:
                    registration_date = datetime.datetime.strptime(registration_date, '%Y-%m-%d').date()
                except ValueError:
                    try:
                        registration_date = datetime.datetime.strptime(registration_date, '%Y/%m/%d').date()
                    except ValueError:
                        # 无法解析日期，默认为较早日期
                        registration_date = datetime.date(2000, 1, 1)
            
            # 判断是新注册还是长期未投资客户
            if registration_date and (reference_date - registration_date).days <= 30:
                return "注册"  # 30天内注册的新客户
            else:
                return "流失"  # 长期无投资行为
        
        # 对投资记录按购买日期排序
        sorted_investments = sorted(investments, 
                                key=lambda x: x.get('purchase_date', datetime.date(2000, 1, 1)) 
                                if not isinstance(x.get('purchase_date'), str) 
                                else datetime.datetime.strptime(x.get('purchase_date'), '%Y-%m-%d').date())
        
        # 获取最早和最近的投资日期
        first_investment_date = sorted_investments[0].get('purchase_date')
        latest_investment_date = sorted_investments[-1].get('purchase_date')
        
        # 确保日期格式一致
        if isinstance(first_investment_date, str):
            first_investment_date = datetime.datetime.strptime(first_investment_date, '%Y-%m-%d').date()
        if isinstance(latest_investment_date, str):
            latest_investment_date = datetime.datetime.strptime(latest_investment_date, '%Y-%m-%d').date()
        
        # 获取最近的完全赎回日期（如果有）
        full_redeemed_investments = [inv for inv in investments if inv.get('status') == '完全赎回']
        latest_redeem_date = None
        
        if full_redeemed_investments:
            latest_redeem_dates = [inv.get('full_redeem_time') for inv in full_redeemed_investments if inv.get('full_redeem_time')]
            if latest_redeem_dates:
                latest_redeem_date = max(latest_redeem_dates)
                if isinstance(latest_redeem_date, str):
                    latest_redeem_date = datetime.datetime.strptime(latest_redeem_date, '%Y-%m-%d').date()
        
        # 计算相关时间间隔
        days_since_latest_investment = (reference_date - latest_investment_date).days
        
        # 如果最近一次投资在30天内，视为活跃客户
        if days_since_latest_investment <= 30:
            # 如果只有一笔投资且为30天内，视为首投客户
            if len(investments) == 1 and (reference_date - first_investment_date).days <= 30:
                return "首投"
            else:
                return "老客"  # 多笔投资或非首次投资的活跃客户
        
        # 如果最近投资在30-180天内，视为半活跃客户
        elif days_since_latest_investment <= 180:
            return "老客"  # 较长时间内有投资的老客户
        
        # 如果最近投资在180天以上，但有持仓，视为低活跃老客户
        else:
            # 检查是否有未完全赎回的投资
            has_holding = any(inv.get('status') in ['持有', '部分卖出'] for inv in investments)
            
            if has_holding:
                return "老客"  # 虽长期无新投资，但仍有持仓的客户
            
            # 如果最近赎回在90天内，视为可能召回客户
            if latest_redeem_date and (reference_date - latest_redeem_date).days <= 90:
                return "召回"  # 近期有赎回行为，需要召回的客户
            else:
                return "流失"  # 长期无投资且无持仓的流失客户
        
    @staticmethod
    def get_investment_time_distribution(customer_type='personal', is_workday=True, month_end=False):
        """
        获取投资时间分布
        
        Args:
            customer_type (str): 客户类型，'personal'个人客户或'corporate'企业客户
            is_workday (bool): 是否工作日，默认为True
            month_end (bool): 是否月末，默认为False
        
        Returns:
            dict: 投资时间分布模型，包含各时间段的权重
        """
        # 基础时间段分布（工作日-个人客户）
        personal_workday_distribution = {
            'early_morning': {  # 7:00-9:00
                'weight': 0.05,
                'peak_time': '8:30',
                'hours': [7, 8]
            },
            'morning': {  # 9:00-12:00
                'weight': 0.25,
                'peak_time': '10:30',
                'hours': list(range(9, 12))
            },
            'lunch': {  # 12:00-14:00
                'weight': 0.15,
                'peak_time': '13:00',
                'hours': [12, 13]
            },
            'afternoon': {  # 14:00-17:00
                'weight': 0.30,
                'peak_time': '15:30',
                'hours': list(range(14, 17))
            },
            'evening': {  # 17:00-21:00
                'weight': 0.20,
                'peak_time': '19:30',
                'hours': list(range(17, 21))
            },
            'night': {  # 21:00-23:00
                'weight': 0.05,
                'peak_time': '22:00',
                'hours': [21, 22]
            }
        }
        
        # 基础时间段分布（工作日-企业客户）
        corporate_workday_distribution = {
            'early_morning': {  # 7:00-9:00
                'weight': 0.05,
                'peak_time': '8:30',
                'hours': [7, 8]
            },
            'morning': {  # 9:00-12:00
                'weight': 0.40,  # 企业客户更集中在上午处理财务
                'peak_time': '10:00',
                'hours': list(range(9, 12))
            },
            'lunch': {  # 12:00-14:00
                'weight': 0.10,
                'peak_time': '13:30',
                'hours': [12, 13]
            },
            'afternoon': {  # 14:00-17:00
                'weight': 0.35,  # 企业客户下午也较活跃
                'peak_time': '15:00',
                'hours': list(range(14, 17))
            },
            'evening': {  # 17:00-19:00
                'weight': 0.08,  # 企业客户晚上活动较少
                'peak_time': '18:00',
                'hours': [17, 18]
            },
            'night': {  # 19:00-23:00
                'weight': 0.02,  # 企业客户夜间很少投资
                'peak_time': '20:00',
                'hours': list(range(19, 23))
            }
        }
        
        # 基础时间段分布（非工作日-个人客户）
        personal_weekend_distribution = {
            'morning': {  # 9:00-12:00
                'weight': 0.30,
                'peak_time': '11:00',
                'hours': list(range(9, 12))
            },
            'afternoon': {  # 12:00-17:00
                'weight': 0.40,
                'peak_time': '14:30',
                'hours': list(range(12, 17))
            },
            'evening': {  # 17:00-21:00
                'weight': 0.25,
                'peak_time': '19:00',
                'hours': list(range(17, 21))
            },
            'night': {  # 21:00-23:00
                'weight': 0.05,
                'peak_time': '22:00',
                'hours': [21, 22]
            }
        }
        
        # 基础时间段分布（非工作日-企业客户）
        corporate_weekend_distribution = {
            'morning': {  # 9:00-12:00
                'weight': 0.45,  # 企业周末主要上午处理
                'peak_time': '10:30',
                'hours': list(range(9, 12))
            },
            'afternoon': {  # 12:00-17:00
                'weight': 0.40,
                'peak_time': '14:00',
                'hours': list(range(12, 17))
            },
            'evening': {  # 17:00-21:00
                'weight': 0.15,  # 企业周末晚上很少处理财务
                'peak_time': '18:00',
                'hours': list(range(17, 21))
            }
        }
        
        # 选择适当的基础分布
        if customer_type == 'corporate':
            base_distribution = corporate_workday_distribution if is_workday else corporate_weekend_distribution
        else:  # 默认为personal
            base_distribution = personal_workday_distribution if is_workday else personal_weekend_distribution
        
        # 月末调整（工资发放、财务结算等因素导致投资增加）
        if month_end and is_workday:
            if customer_type == 'personal':
                # 个人客户月末更倾向于晚上投资（收到工资后）
                base_distribution['evening']['weight'] += 0.10
                base_distribution['afternoon']['weight'] -= 0.05
                base_distribution['morning']['weight'] -= 0.05
            else:  # corporate
                # 企业客户月末更倾向于下午投资（月底结算）
                base_distribution['afternoon']['weight'] += 0.10
                base_distribution['morning']['weight'] -= 0.05
                base_distribution['evening']['weight'] -= 0.05
        
        # 归一化权重
        total_weight = sum(period['weight'] for period in base_distribution.values())
        if abs(total_weight - 1.0) > 0.001:  # 允许小误差
            factor = 1.0 / total_weight
            for period in base_distribution.values():
                period['weight'] *= factor
        
        return base_distribution
