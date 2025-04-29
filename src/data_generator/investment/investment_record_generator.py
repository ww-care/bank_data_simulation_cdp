"""
理财购买记录生成器主类
负责协调产品匹配、购买记录生成和赎回行为生成
"""

import random
import datetime
from .product_matcher import ProductMatcher
from .redemption_generator import RedemptionGenerator
from .events_generator import InvestmentEventGenerator
from .utils import InvestmentUtils
from .models.investment_record import InvestmentRecord
from .config_adapter import InvestmentConfigAdapter


class InvestmentRecordGenerator:
    """理财购买记录生成器主类"""
    
    def __init__(self, db_manager, config_manager, logger, time_manager=None):
        """初始化生成器"""
        self.db_manager = db_manager
        self.config_manager = config_manager
        self.logger = logger
        self.time_manager = time_manager
        self.product_matcher = None
        self.redemption_generator = None
        self.events_generator = None
        
        # 初始化配置适配器并加载理财相关配置
        self.config_adapter = InvestmentConfigAdapter(config_manager)
        self.config = self.config_adapter.build_investment_generator_config()
        
    def initialize(self):
        """初始化子组件"""
        # 初始化产品匹配器
        self.product_matcher = ProductMatcher(self.db_manager, self.config, self.logger)
        self.product_matcher.initialize_risk_mapping()
        
        # 初始化赎回生成器
        self.redemption_generator = RedemptionGenerator(self.db_manager, self.config, self.logger, self.time_manager)
        
        # 初始化事件生成器
        self.events_generator = InvestmentEventGenerator(self.db_manager, self.config, self.logger)
        
    def generate_historical_investments(self, start_date, end_date, customer_ids=None):
        """生成历史理财购买记录"""
        # TODO: 实现历史理财购买记录生成逻辑
        pass
    
    def generate_realtime_investments(self, date_range):
        """生成实时增量理财记录"""
        # TODO: 实现实时增量理财记录生成逻辑
        pass
        
    def generate_customer_investments(self, customer_id, start_date, end_date):
        """为特定客户生成理财记录"""
        # TODO: 实现特定客户理财记录生成逻辑
        pass
        
    def generate_investment_batch(self, customers, products, date_range, batch_size=1000):
        """
        批量生成理财购买记录
        
        Args:
            customers (list): 客户信息列表
            products (list): 产品信息列表
            date_range (tuple): 日期范围，格式为(start_date, end_date)
            batch_size (int): 批处理大小，默认1000
            
        Returns:
            list: 生成的理财购买记录列表
        """
        import random
        import datetime
        
        # 验证输入参数
        if not customers or not products:
            self.logger.warning("客户列表或产品列表为空，无法生成理财购买记录")
            return []
        
        start_date, end_date = date_range
        
        # 确保日期类型一致
        if isinstance(start_date, str):
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # 初始化结果列表
        investment_records = []
        
        # 获取时间分布模型
        today = datetime.datetime.now().date()
        is_month_end = today.day >= 25  # 假设25号以后为月末
        
        # 初始化计数器和进度跟踪
        total_customers = len(customers)
        processed_count = 0
        
        self.logger.info(f"开始生成理财购买记录，客户数量: {total_customers}，日期范围: {start_date} 至 {end_date}")
        
        # 遍历每个客户
        for customer in customers:
            # 更新进度
            processed_count += 1
            if processed_count % 100 == 0 or processed_count == total_customers:
                self.logger.info(f"生成理财记录进度: {processed_count}/{total_customers}")
            
            # 获取客户信息
            customer_id = customer.get('base_id')
            customer_type = customer.get('customer_type', 'personal')
            
            # 确定该客户在时间范围内购买理财产品的次数
            if customer_type == 'corporate':
                # 企业客户购买次数分布范围
                min_purchases = 1
                max_purchases = 5
            else:
                # 个人客户购买次数分布范围
                min_purchases = 0
                max_purchases = 3
                
            # VIP客户购买次数增加
            if customer.get('is_vip', False):
                max_purchases += 2
            
            # 随机决定购买次数
            purchase_count = random.randint(min_purchases, max_purchases)
            
            # 如果购买次数为0，跳过该客户
            if purchase_count == 0:
                continue
            
            # 使用产品匹配器为客户找到合适的产品
            matched_products = self.product_matcher.find_matching_products(
                customer, limit=10)
            
            # 如果没有匹配的产品，跳过该客户
            if not matched_products:
                self.logger.debug(f"客户 {customer_id} 没有匹配的产品，跳过")
                continue
            
            # 从匹配的产品中选择指定数量的产品
            # 根据匹配分数加权随机选择
            selected_products = self._weighted_sample_products(
                matched_products, purchase_count)
            
            # 对每个选定的产品生成购买记录
            for product_match in selected_products:
                product = product_match['product']
                
                # 计算购买金额
                purchase_amount = self.calculate_investment_amount(customer, product)
                
                # 确定购买日期
                purchase_date = self._generate_purchase_date(
                    customer, start_date, end_date, customer_type, is_month_end)
                
                # 生成购买时间
                purchase_time = self._generate_purchase_time(purchase_date, customer_type)
                
                # 计算到期日期
                investment_period = product.get('investment_period', 0)
                maturity_date = InvestmentUtils.calculate_maturity_date(
                    purchase_date, term_months=investment_period)
                
                # 计算预期收益率
                expected_yield = product.get('expected_yield', 0)
                
                # 创建理财购买记录
                investment_record = {
                    'detail_id': InvestmentUtils.generate_transaction_id(prefix="INV"),
                    'base_id': customer_id,
                    'detail_time': int(purchase_time.timestamp() * 1000),  # 13位时间戳
                    'product_id': product.get('base_id'),
                    'purchase_amount': purchase_amount,
                    'hold_amount': purchase_amount,  # 初始持有金额等于购买金额
                    'term': investment_period * 30 if investment_period else 0,  # 转换为天数
                    'wealth_purchase_time': int(purchase_time.timestamp() * 1000),
                    'wealth_all_redeem_time': None,  # 初始未赎回
                    'wealth_date': purchase_date,
                    'wealth_status': '持有',  # 初始状态为持有
                    'maturity_time': int(datetime.datetime.combine(maturity_date, datetime.time(0, 0)).timestamp() * 1000) if maturity_date else None,
                    'status': '成功',
                    'channel': self._generate_purchase_channel(customer),
                    'expected_return': expected_yield,
                    'account_id': self._get_customer_account(customer_id)
                }
                
                # 添加到结果列表
                investment_records.append(investment_record)
                
                # 批量处理，当记录达到batch_size时导入数据库
                if len(investment_records) >= batch_size:
                    self._import_batch_records(investment_records)
                    investment_records = []
        
        # 处理剩余记录
        if investment_records:
            self._import_batch_records(investment_records)
        
        self.logger.info(f"理财购买记录生成完成，总生成记录数: {processed_count}")
        
        return investment_records

    def _weighted_sample_products(self, matched_products, sample_size):
        """
        根据匹配分数加权随机抽样产品
        
        Args:
            matched_products (list): 匹配的产品列表，每项包含'product'和'match_score'
            sample_size (int): 抽样数量
            
        Returns:
            list: 抽样结果
        """
        import random
        
        # 如果产品数量不足，直接返回全部
        if len(matched_products) <= sample_size:
            return matched_products
        
        # 提取匹配分数作为权重
        weights = [item['match_score'] for item in matched_products]
        
        # 归一化权重
        total_weight = sum(weights)
        if total_weight > 0:
            normalized_weights = [w / total_weight for w in weights]
        else:
            # 如果所有权重都是0，使用均匀分布
            normalized_weights = [1.0 / len(matched_products)] * len(matched_products)
        
        # 加权随机抽样
        selected_indices = random.choices(
            range(len(matched_products)), weights=normalized_weights, k=sample_size)
        
        # 返回选中的产品
        return [matched_products[i] for i in selected_indices]

    def _generate_purchase_date(self, customer, start_date, end_date, customer_type, is_month_end):
        """
        生成购买日期
        
        考虑工作日分布、月末分布等因素
        """
        import random
        import datetime
        
        # 计算日期范围内的天数
        date_range = (end_date - start_date).days
        
        # 如果日期范围小于等于0，使用起始日期
        if date_range <= 0:
            return start_date
        
        # 根据客户类型调整日期分布权重
        # 企业客户更可能在月初和月中购买
        # 个人客户更可能在月底购买（工资发放后）
        if customer_type == 'corporate':
            # 企业客户日期分布
            if is_month_end:
                # 月末企业购买概率降低
                days_from_start = random.randint(0, int(date_range * 0.7))
            else:
                # 非月末时正常分布
                days_from_start = random.randint(0, date_range)
        else:
            # 个人客户日期分布
            if is_month_end:
                # 月末个人购买概率提高，偏向日期范围后半段
                days_from_start = random.randint(int(date_range * 0.3), date_range)
            else:
                # 非月末时正常分布
                days_from_start = random.randint(0, date_range)
        
        # 计算购买日期
        purchase_date = start_date + datetime.timedelta(days=days_from_start)
        
        # 检查是否是工作日
        is_workday = self._is_workday(purchase_date)
        
        # 对于企业客户，强制转为工作日
        if customer_type == 'corporate' and not is_workday:
            # 找最近的工作日
            if purchase_date.weekday() == 5:  # 周六
                purchase_date += datetime.timedelta(days=2)  # 调整到下周一
            elif purchase_date.weekday() == 6:  # 周日
                purchase_date += datetime.timedelta(days=1)  # 调整到下周一
        
        return purchase_date

    def _generate_purchase_time(self, purchase_date, customer_type):
        """
        生成购买时间
        
        根据客户类型、是否工作日等因素生成具体时间
        """
        import random
        import datetime
        
        # 确定是否工作日
        is_workday = self._is_workday(purchase_date)
        
        # 获取月份信息，检查是否月末
        is_month_end = purchase_date.day >= 25
        
        # 获取时间分布模型
        time_distribution = InvestmentUtils.get_investment_time_distribution(
            customer_type, is_workday, is_month_end)
        
        # 按权重随机选择时间段
        time_periods = list(time_distribution.keys())
        period_weights = [period_info['weight'] for period_info in time_distribution.values()]
        
        selected_period = random.choices(time_periods, weights=period_weights, k=1)[0]
        period_info = time_distribution[selected_period]
        
        # 获取该时间段的小时范围和高峰时间
        hours = period_info.get('hours', [9, 10, 11])  # 默认上午9-11点
        peak_time = period_info.get('peak_time', '10:00')
        
        # 解析高峰时间
        peak_hour, peak_minute = map(int, peak_time.split(':'))
        
        # 生成具体时间
        # 70%的概率集中在高峰时间附近±1小时，30%的概率在整个时间段内随机分布
        if random.random() < 0.7:
            # 高峰时间附近
            hour = random.randint(max(hours[0], peak_hour - 1), min(hours[-1], peak_hour + 1))
            if hour == peak_hour:
                # 更集中在高峰分钟附近
                minute = random.randint(max(0, peak_minute - 15), min(59, peak_minute + 15))
            else:
                minute = random.randint(0, 59)
        else:
            # 整个时间段随机
            hour = random.choice(hours)
            minute = random.randint(0, 59)
        
        second = random.randint(0, 59)
        
        # 创建日期时间对象
        purchase_time = datetime.datetime.combine(
            purchase_date, datetime.time(hour, minute, second))
        
        return purchase_time

    def _is_workday(self, date):
        """
        判断日期是否是工作日
        
        简化实现，仅考虑周末，不考虑法定假日
        """
        # 周一至周五为工作日
        return date.weekday() < 5

    def _generate_purchase_channel(self, customer):
        """
        生成购买渠道
        
        根据客户特性确定购买渠道
        """
        import random
        
        # 默认渠道及其权重
        channels = {
            'mobile_app': 0.4,      # 手机银行APP
            'online_banking': 0.3,  # 网上银行
            'counter': 0.15,        # 柜台
            'phone_banking': 0.1,   # 电话银行
            'third_party': 0.05     # 第三方平台
        }
        
        # 根据客户特征调整渠道权重
        customer_type = customer.get('customer_type', 'personal')
        is_vip = customer.get('is_vip', False)
        age = self._calculate_age(customer.get('birth_date'))
        
        adjusted_channels = channels.copy()
        
        if customer_type == 'corporate':
            # 企业客户更倾向于柜台和网银
            adjusted_channels['counter'] += 0.2
            adjusted_channels['online_banking'] += 0.1
            adjusted_channels['mobile_app'] -= 0.2
            adjusted_channels['third_party'] -= 0.1
        
        if is_vip:
            # VIP客户更倾向于柜台（专属服务）
            adjusted_channels['counter'] += 0.15
            adjusted_channels['phone_banking'] += 0.05
            adjusted_channels['mobile_app'] -= 0.1
            adjusted_channels['third_party'] -= 0.1
        
        if age is not None:
            if age < 30:
                # 年轻客户更喜欢手机APP和第三方平台
                adjusted_channels['mobile_app'] += 0.15
                adjusted_channels['third_party'] += 0.05
                adjusted_channels['counter'] -= 0.15
                adjusted_channels['phone_banking'] -= 0.05
            elif age > 60:
                # 老年客户更喜欢柜台和电话银行
                adjusted_channels['counter'] += 0.2
                adjusted_channels['phone_banking'] += 0.1
                adjusted_channels['mobile_app'] -= 0.2
                adjusted_channels['third_party'] -= 0.1
        
        # 归一化权重
        total_weight = sum(adjusted_channels.values())
        normalized_channels = {k: v / total_weight for k, v in adjusted_channels.items()}
        
        # 按权重随机选择渠道
        channels_list = list(normalized_channels.keys())
        weights_list = list(normalized_channels.values())
        
        selected_channel = random.choices(channels_list, weights=weights_list, k=1)[0]
        
        return selected_channel

    def _calculate_age(self, birth_date):
        """
        计算年龄
        
        Args:
            birth_date: 出生日期
            
        Returns:
            int: 年龄，无法计算则返回None
        """
        if not birth_date:
            return None
        
        import datetime
        
        # 如果是字符串，转换为日期对象
        if isinstance(birth_date, str):
            try:
                birth_date = datetime.datetime.strptime(birth_date, '%Y-%m-%d').date()
            except ValueError:
                return None
        
        # 如果是datetime对象，转换为date对象
        if isinstance(birth_date, datetime.datetime):
            birth_date = birth_date.date()
        
        # 计算年龄
        today = datetime.date.today()
        age = today.year - birth_date.year
        
        # 检查是否已过生日
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1
        
        return age

    def _get_customer_account(self, customer_id):
        """
        获取客户资金账户ID
        
        如果客户有多个账户，选择合适的账户
        
        Args:
            customer_id: 客户ID
            
        Returns:
            str: 账户ID
        """
        try:
            # 查询客户的资金账户
            query = """
            SELECT base_id 
            FROM cdp_account_archive 
            WHERE customer_id = %s 
            AND status = 'active'
            ORDER BY balance DESC
            """
            
            results = self.db_manager.execute_query(query, (customer_id,))
            
            if results:
                # 返回余额最高的账户
                return results[0]['base_id']
            
            # 如果没有找到账户，返回空
            return None
            
        except Exception as e:
            self.logger.error(f"获取客户账户时出错: {str(e)}")
            return None

    def _import_batch_records(self, records):
        """
        批量导入理财购买记录到数据库
        
        Args:
            records (list): 理财购买记录列表
        """
        if not records:
            return
        
        try:
            # 使用数据库管理器导入数据
            table_name = 'cdp_investment_order'
            imported_count = self.db_manager.import_data(table_name, records)
            
            self.logger.info(f"成功导入 {imported_count} 条理财购买记录")
            
        except Exception as e:
            self.logger.error(f"导入理财购买记录时出错: {str(e)}")
        
    def calculate_investment_amount(self, customer_info, product_info):
        """
        计算客户购买特定产品的投资金额
        
        考虑客户投资能力、产品最低要求、风险偏好等因素
        
        Args:
            customer_info (dict): 客户信息
            product_info (dict): 产品信息
            
        Returns:
            float: 计算出的投资金额
        """
        import random
        
        # 获取产品最低投资金额
        min_investment = product_info.get('minimum_investment', 10000)
        
        # 如果最低投资金额不合理，设置默认值
        if min_investment <= 0:
            min_investment = 10000
            self.logger.warning(f"产品 {product_info.get('base_id')} 最低投资金额异常，使用默认值 10000")
        
        # 使用产品匹配器计算客户投资能力
        investment_capacity = self.product_matcher.calculate_investment_capacity(customer_info)
        min_amount = investment_capacity.get('min_amount', min_investment)
        max_amount = investment_capacity.get('max_amount', min_investment * 10)
        suggested_amount = investment_capacity.get('suggested_amount', (min_amount + max_amount) / 2)
        
        # 确保最低投资金额不低于产品要求
        min_amount = max(min_amount, min_investment)
        
        # 如果最低金额大于最大金额，调整最大金额
        if min_amount > max_amount:
            max_amount = min_amount * 1.5
        
        # 获取产品风险等级和客户风险偏好
        product_risk = product_info.get('risk_level', 'R1')
        customer_risk = customer_info.get('risk_level', 'R3')
        
        # 风险匹配因子：风险等级越匹配，投资金额倾向越高
        risk_match_factor = self._calculate_risk_match_factor(customer_risk, product_risk)
        
        # 根据客户类型和VIP状态调整投资行为
        customer_type = customer_info.get('customer_type', 'personal')
        is_vip = customer_info.get('is_vip', False)
        
        # 设置基础的金额分布特征
        if customer_type == 'corporate':
            # 企业客户倾向于更大金额，且更接近整数值
            base_amount_factor = 0.7  # 更接近最大值
            rounding_base = 10000     # 万元整数
            deviation_factor = 0.05   # 偏离量较小
        else:  # 个人客户
            if is_vip:
                # VIP个人客户也倾向于较大金额
                base_amount_factor = 0.6
                rounding_base = 5000  # 5000的整数倍
                deviation_factor = 0.1
            else:
                # 普通个人客户金额更分散
                base_amount_factor = 0.5  # 居中值
                rounding_base = 1000      # 1000的整数倍
                deviation_factor = 0.15   # 偏离量较大
        
        # 考虑历史投资行为模式（如果有）
        history_factor = self._get_investment_history_factor(customer_info.get('base_id'))
        
        # 计算基础金额：在最小和最大值之间，偏向特定位置
        # base_amount_factor越大，越靠近最大值；越小，越靠近最小值
        adjusted_factor = (base_amount_factor + history_factor) / 2  # 结合历史因子
        weighted_factor = adjusted_factor * risk_match_factor        # 结合风险匹配因子
        
        # 确保因子在0.1-0.9范围内，避免极端值
        weighted_factor = max(0.1, min(0.9, weighted_factor))
        
        # 计算基础金额
        base_amount = min_amount + weighted_factor * (max_amount - min_amount)
        
        # 对基础金额进行取整处理，增加真实感
        rounded_amount = round(base_amount / rounding_base) * rounding_base
        
        # 添加随机偏移，避免太多完全相同的金额
        # 偏移量受deviation_factor控制，值越大偏移越大
        deviation_range = rounded_amount * deviation_factor
        
        # 对于大额投资，降低偏移量以保持整数美感
        if rounded_amount >= 1000000:  # 百万以上
            deviation_range *= 0.3
        elif rounded_amount >= 100000:  # 十万以上
            deviation_range *= 0.5
        
        # 计算最终金额，加入随机偏移
        final_amount = rounded_amount + random.uniform(-deviation_range, deviation_range)
        
        # 确保最终金额不低于最低投资要求且不超过最大投资能力
        final_amount = max(min_amount, min(max_amount, final_amount))
        
        # 最后的取整处理，保证金额的合理性
        final_amount = round(final_amount, 2)  # 保留两位小数
        
        self.logger.debug(
            f"计算投资金额: 客户={customer_info.get('base_id')}, 产品={product_info.get('base_id')}, "
            f"金额={final_amount}, 范围=[{min_amount}, {max_amount}]"
        )
        
        return final_amount

    def _calculate_risk_match_factor(self, customer_risk, product_risk):
        """
        计算风险匹配因子
        
        风险匹配度越高，因子越大
        
        Args:
            customer_risk (str): 客户风险等级
            product_risk (str): 产品风险等级
            
        Returns:
            float: 风险匹配因子 (0.5-1.2)
        """
        # 将风险等级转换为数值
        risk_values = {'R1': 1, 'R2': 2, 'R3': 3, 'R4': 4, 'R5': 5}
        
        customer_risk_value = risk_values.get(customer_risk, 3)
        product_risk_value = risk_values.get(product_risk, 1)
        
        # 计算风险差异
        risk_diff = abs(customer_risk_value - product_risk_value)
        
        # 根据风险差异计算匹配因子
        if risk_diff == 0:
            # 完全匹配，因子最高
            return 1.2
        elif risk_diff == 1:
            # 差一级，较高匹配
            return 1.0
        elif risk_diff == 2:
            # 差两级，中等匹配
            return 0.8
        else:
            # 差距较大，低匹配
            return 0.5

    def _get_investment_history_factor(self, customer_id):
        """
        根据客户历史投资行为计算金额调整因子
        
        Args:
            customer_id (str): 客户ID
            
        Returns:
            float: 历史调整因子 (0-0.3)
        """
        try:
            if not customer_id:
                return 0.15  # 默认中等值
            
            # 查询客户历史投资记录
            query = """
            SELECT AVG(purchase_amount) as avg_amount,
                MAX(purchase_amount) as max_amount,
                COUNT(*) as count
            FROM cdp_investment_order
            WHERE base_id = %s
            """
            
            results = self.db_manager.execute_query(query, (customer_id,))
            
            if not results or not results[0]['count']:
                return 0.15  # 无历史记录时使用默认值
            
            # 获取历史平均和最大投资金额
            avg_amount = results[0]['avg_amount'] or 0
            max_amount = results[0]['max_amount'] or 0
            count = results[0]['count']
            
            # 客户交易频率因子（交易越多，对金额的把握越准确）
            frequency_factor = min(0.1, count / 100)
            
            # 金额水平因子（历史金额越大，新投资金额可能越大）
            amount_level = 0
            if max_amount > 1000000:  # 百万以上
                amount_level = 0.2
            elif max_amount > 100000:  # 十万以上
                amount_level = 0.15
            elif max_amount > 10000:   # 万元以上
                amount_level = 0.1
            else:
                amount_level = 0.05
            
            # 合并因子，范围控制在0-0.3
            combined_factor = frequency_factor + amount_level
            return min(0.3, combined_factor)
            
        except Exception as e:
            self.logger.error(f"获取投资历史因子时出错: {str(e)}")
            return 0.15  # 出错时使用默认值
        
    def validate_generated_data(self, investments):
        """验证生成的数据合法性"""
        # TODO: 实现数据合法性验证逻辑
        pass
        
    def update_customer_wealth_status(self, customer_id, investment_info):
        """更新客户理财状态信息"""
        # TODO: 实现客户理财状态信息更新逻辑
        pass
