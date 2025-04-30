import random
import datetime

from src.data_generator.investment.utils import InvestmentUtils

class RedemptionGenerator:
    """理财赎回行为生成器"""
    
    def __init__(self, db_manager, config, logger, time_manager=None):
        """初始化赎回生成器
        
        Args:
            db_manager: 数据库管理器
            config: 理财生成器配置
            logger: 日志对象
            time_manager: 时间管理器
        """
        self.db_manager = db_manager
        self.config = config
        self.logger = logger
        self.time_manager = time_manager
        
        # 获取赎回相关配置
        self.redemption_config = self.config.get('redemption_config', {})
        
        # 如果配置中没有赎回配置，使用默认配置
        if not self.redemption_config:
            self.logger.warning("No redemption config found, using default config")
            self.redemption_config = {
                # 提前赎回基础概率(每日)
                'early_redemption_base_prob': 0.002,
                
                # 部分赎回概率
                'partial_redemption_prob': 0.4,
                
                # 部分赎回金额范围(占持有金额比例)
                'partial_redemption_range': [0.2, 0.7],
                
                # 持有期调整因子
                'holding_period_factors': {
                    'short': 0.2,   # 刚购买不久(<=15%)
                    'middle': 1.0,  # 中期持有(15%-70%)
                    'late': 1.5     # 接近到期(>70%)
                },
                
                # 客户类型调整因子
                'customer_type_factors': {
                    'personal': 1.0,
                    'personal_vip': 0.8,  # VIP客户提前赎回概率略低
                    'corporate': 1.2      # 企业客户提前赎回概率略高
                },
                
                # 风险偏好调整因子
                'risk_level_factors': {
                    'R1': 0.8,  # 保守型客户赎回概率低
                    'R2': 0.9,
                    'R3': 1.0,  # 基准
                    'R4': 1.1,
                    'R5': 1.2   # 激进型客户赎回概率高
                },
                
                # 产品类型调整因子
                'product_type_factors': {
                    '债券型基金': 0.9,    # 较稳定
                    '货币型基金': 1.2,    # 流动性高
                    '股票型基金': 1.3,    # 波动大，赎回概率高
                    '混合型基金': 1.1
                },
                
                # 市场情况调整因子(暂时简化)
                'market_condition_factors': {
                    'bull': 0.8,    # 牛市，赎回概率低
                    'normal': 1.0,  # 平稳市场
                    'bear': 1.3     # 熊市，赎回概率高
                }
            }
        
        # 初始化事件生成器(如果需要)
        self.events_generator = None
        
    def process_matured_investments(self, date=None):
        """处理已到期的投资记录
        
        查找到期日小于等于指定日期的持有状态投资记录，生成赎回记录
        
        Args:
            date (datetime.date, optional): 处理日期，默认为当前日期
            
        Returns:
            int: 处理的记录数量
        """
        # 如果未提供日期，使用当前日期
        if date is None:
            date = datetime.datetime.now().date()
        
        # 确保日期格式一致
        if isinstance(date, str):
            date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
            
        self.logger.info(f"开始处理截至 {date} 到期的投资记录")
        
        try:
            # 计算查询的时间戳上限
            # 转换为当天23:59:59的时间戳，单位为毫秒
            end_timestamp = int(datetime.datetime.combine(
                date, datetime.time(23, 59, 59)).timestamp() * 1000)
            
            # 查询所有到期且未赎回的投资记录
            query = """
            SELECT * FROM cdp_investment_order
            WHERE maturity_time <= %s
            AND wealth_status = '持有'
            ORDER BY maturity_time
            """
            
            matured_investments = self.db_manager.execute_query(query, (end_timestamp,))
            
            if not matured_investments:
                self.logger.info(f"没有找到截至 {date} 到期的投资记录")
                return 0
            
            self.logger.info(f"找到 {len(matured_investments)} 条到期投资记录")
            
            # 批量处理到期记录
            processed_count = 0
            redemption_records = []
            
            for investment in matured_investments:
                try:
                    # 创建赎回记录
                    redemption_record = self._create_redemption_record(
                        investment, 'full', date, is_matured=True)
                    
                    if redemption_record:
                        redemption_records.append(redemption_record)
                        processed_count += 1
                except Exception as e:
                    self.logger.error(f"处理投资记录 {investment.get('detail_id')} 时出错: {str(e)}")
            
            # 更新数据库
            if redemption_records:
                self._update_investment_records(redemption_records)
                
                # 更新客户财富状态
                self._update_customer_wealth_status(redemption_records)
                
                # 生成赎回相关事件
                if self.events_generator:
                    self._generate_redemption_events(redemption_records)
            
            self.logger.info(f"成功处理 {processed_count} 条到期投资记录")
            return processed_count
            
        except Exception as e:
            self.logger.error(f"处理到期投资记录时出错: {str(e)}")
            return 0
    
    def _create_redemption_record(self, investment, redemption_type, redemption_date, is_matured=False):
        """创建赎回记录
        
        根据赎回类型和日期创建赎回记录
        
        Args:
            investment (dict): 原始投资记录
            redemption_type (str): 赎回类型('partial' 或 'full')
            redemption_date (datetime.date): 赎回日期
            is_matured (bool): 是否因到期而赎回
            
        Returns:
            dict: 赎回记录
        """
        try:
            # 获取必要信息
            investment_id = investment.get('detail_id')
            customer_id = investment.get('base_id')
            product_id = investment.get('product_id')
            hold_amount = float(investment.get('hold_amount', 0))
            
            # 检查持有金额
            if hold_amount <= 0:
                self.logger.warning(f"投资记录 {investment_id} 持有金额为0或负数，跳过赎回处理")
                return None
            
            # 创建赎回时间
            redemption_time = self._generate_redemption_time(redemption_date, customer_id)
            redemption_timestamp = int(redemption_time.timestamp() * 1000)
            
            # 根据赎回类型计算赎回金额
            if redemption_type == 'full':
                redemption_amount = hold_amount
                new_status = '完全赎回'
                new_hold_amount = 0
            else:  # partial
                redemption_amount = self._calculate_partial_redemption_amount(investment)
                new_status = '部分卖出'
                new_hold_amount = max(0, hold_amount - redemption_amount)
            
            # 创建赎回记录（实际上是更新原记录）
            redemption_record = {
                'detail_id': investment_id,
                'base_id': customer_id,
                'wealth_status': new_status,
                'hold_amount': new_hold_amount,
                'wealth_all_redeem_time': redemption_timestamp if redemption_type == 'full' else None,
                'redemption_amount': redemption_amount,
                'redemption_time': redemption_timestamp,
                'is_matured': is_matured
            }
            
            return redemption_record
            
        except Exception as e:
            self.logger.error(f"创建赎回记录时出错: {str(e)}")
            return None
    
    def _generate_redemption_time(self, redemption_date, customer_id=None):
        """生成赎回时间
        
        在赎回日期的合理时间范围内生成赎回时间
        
        Args:
            redemption_date (datetime.date): 赎回日期
            customer_id (str, optional): 客户ID，用于确保同一客户的赎回时间一致性
            
        Returns:
            datetime.datetime: 赎回时间
        """
        # 赎回主要发生在工作时间(9:00-17:00)
        if customer_id and hash(customer_id) % 10 < 8:  # 80%的客户在工作时间赎回
            hour = random.randint(9, 16)
            minute = random.randint(0, 59)
        else:  # 20%的客户在其他时间赎回
            hour = random.randint(7, 21)  # 早7点到晚9点
            minute = random.randint(0, 59)
        
        second = random.randint(0, 59)
        
        return datetime.datetime.combine(redemption_date, datetime.time(hour, minute, second))
    
    def _calculate_partial_redemption_amount(self, investment):
        """计算部分赎回金额
        
        Args:
            investment (dict): 投资记录
            
        Returns:
            float: 赎回金额
        """
        # 获取持有金额
        hold_amount = float(investment.get('hold_amount', 0))
        
        # 获取部分赎回比例范围配置
        redemption_range = self.redemption_config.get('partial_redemption_range', [0.2, 0.7])
        min_ratio, max_ratio = redemption_range
        
        # 随机确定赎回比例
        ratio = random.uniform(min_ratio, max_ratio)
        
        # 计算赎回金额
        redemption_amount = hold_amount * ratio
        
        # 确保赎回金额合理（最小1元，最大不超过持有金额）
        redemption_amount = max(1, min(hold_amount - 1, redemption_amount))
        
        # 取整处理
        customer_type = investment.get('customer_type', 'personal')
        if customer_type == 'corporate':
            # 企业客户往往赎回金额为整万
            redemption_amount = round(redemption_amount / 10000) * 10000
        else:
            # 个人客户通常赎回金额为整百
            redemption_amount = round(redemption_amount / 100) * 100
        
        # 确保最终金额不超过持有金额
        return min(redemption_amount, hold_amount)
    
    def _update_investment_records(self, redemption_records):
        """更新投资记录
        
        将赎回信息更新到数据库
        
        Args:
            redemption_records (list): 赎回记录列表
            
        Returns:
            int: 更新的记录数量
        """
        if not redemption_records:
            return 0
        
        try:
            updated_count = 0
            
            for record in redemption_records:
                investment_id = record.get('detail_id')
                
                # 构建更新语句
                update_fields = []
                params = []
                
                if 'wealth_status' in record:
                    update_fields.append("wealth_status = %s")
                    params.append(record['wealth_status'])
                
                if 'hold_amount' in record:
                    update_fields.append("hold_amount = %s")
                    params.append(record['hold_amount'])
                
                if 'wealth_all_redeem_time' in record:
                    update_fields.append("wealth_all_redeem_time = %s")
                    params.append(record['wealth_all_redeem_time'])
                
                if not update_fields:
                    continue
                
                # 添加WHERE条件参数
                params.append(investment_id)
                
                # 构建完整更新语句
                update_query = f"""
                UPDATE cdp_investment_order
                SET {", ".join(update_fields)}
                WHERE detail_id = %s
                """
                
                # 执行更新
                result = self.db_manager.execute_update(update_query, params)
                
                if result:
                    updated_count += 1
                
            return updated_count
            
        except Exception as e:
            self.logger.error(f"更新投资记录时出错: {str(e)}")
            return 0
    
    def _update_customer_wealth_status(self, redemption_records):
        """更新客户财富状态
        
        Args:
            redemption_records (list): 赎回记录列表
            
        Returns:
            int: 更新的客户数量
        """
        if not redemption_records:
            return 0
        
        # 此方法需要调用InvestmentRecordGenerator的方法，
        # 暂时使用一个占位实现，后续完善
        # 实际实现时，应该集成到InvestmentRecordGenerator中
        # 或者通过回调方式进行更新
        
        # 记录已处理的客户ID，避免重复处理
        processed_customers = set()
        
        for record in redemption_records:
            customer_id = record.get('base_id')
            if customer_id in processed_customers:
                continue
                
            try:
                # 这里应该调用客户财富状态更新方法
                # self.investment_generator.update_customer_wealth_status(customer_id, record)
                
                # 暂时只记录日志
                self.logger.info(f"更新客户 {customer_id} 的财富状态（赎回处理）")
                processed_customers.add(customer_id)
                
            except Exception as e:
                self.logger.error(f"更新客户 {customer_id} 财富状态时出错: {str(e)}")
        
        return len(processed_customers)
        
    def generate_redemptions(self, investment_records, end_date):
        """生成赎回记录"""
        # TODO: 实现赎回记录生成逻辑
        pass
        
    def process_maturity_redemptions(self, investments, date):
        """处理到期自动赎回
        
        Args:
            investments: 投资记录列表
            date: 当前处理日期
            
        Returns:
            list: 处理后的赎回记录列表
        """
        # 处理结果列表
        redemption_records = []
        
        # 遍历投资记录，找出到期的产品
        for investment in investments:
            maturity_date = investment.get('maturity_date')
            status = investment.get('status')
            
            # 如果有到期日期且今天是到期日且当前状态为持有或部分卖出
            if (maturity_date and maturity_date == date and 
                status in ['holding', 'partial_redeemed']):
                
                # 创建赎回记录
                redemption_record = {
                    'investment_id': investment.get('investment_id'),
                    'customer_id': investment.get('customer_id'),
                    'product_id': investment.get('product_id'),
                    'redemption_date': date,
                    'redemption_amount': investment.get('hold_amount'),  # 赎回全部剩余金额
                    'is_full_redemption': True,  # 到期肯定是全额赎回
                    'redemption_type': 'maturity'  # 到期赎回
                }
                
                redemption_records.append(redemption_record)
        
        return redemption_records

    def _parse_date(self, date_value):
        """
        解析日期值为标准日期对象
        
        Args:
            date_value: 日期值，可能是字符串、日期或时间戳
            
        Returns:
            datetime.date: 标准日期对象
        """
        import datetime
        
        if not date_value:
            return datetime.date(2000, 1, 1)  # 默认日期
        
        # 如果已经是日期对象，直接返回
        if isinstance(date_value, datetime.date):
            return date_value
        
        # 如果是datetime对象，转换为date
        if isinstance(date_value, datetime.datetime):
            return date_value.date()
        
        # 如果是字符串，尝试解析
        if isinstance(date_value, str):
            try:
                return datetime.datetime.strptime(date_value, '%Y-%m-%d').date()
            except ValueError:
                try:
                    return datetime.datetime.strptime(date_value, '%Y/%m/%d').date()
                except ValueError:
                    self.logger.error(f"无法解析日期: {date_value}")
                    return datetime.date(2000, 1, 1)  # 默认日期
        
        # 如果是时间戳（整数或浮点数）
        if isinstance(date_value, (int, float)):
            try:
                # 假设是毫秒级时间戳
                if date_value > 1000000000000:  # 13位时间戳
                    date_value /= 1000
                return datetime.datetime.fromtimestamp(date_value).date()
            except:
                self.logger.error(f"无法从时间戳解析日期: {date_value}")
                return datetime.date(2000, 1, 1)  # 默认日期
        
        # 其他情况，返回默认日期
        return datetime.date(2000, 1, 1)

    def _generate_redemption_time(self, redemption_date, customer_id):
        """
        生成赎回时间
        
        Args:
            redemption_date (datetime.date): 赎回日期
            customer_id (str): 客户ID
            
        Returns:
            datetime.datetime: 赎回时间
        """
        import random
        import datetime
        
        # 获取客户信息，确定客户类型
        customer_info = self._get_customer_info(customer_id)
        customer_type = customer_info.get('customer_type', 'personal')
        
        # 确定是否工作日
        is_workday = redemption_date.weekday() < 5  # 周一至周五
        
        # 获取赎回时间分布模型
        time_distribution = InvestmentUtils.get_redemption_time_distribution(None, is_workday)
        
        # 按权重随机选择时间段
        time_periods = list(time_distribution.keys())
        period_weights = [period_info['weight'] for period_info in time_distribution.values()]
        
        selected_period = random.choices(time_periods, weights=period_weights, k=1)[0]
        period_info = time_distribution[selected_period]
        
        # 获取该时间段的小时范围和高峰时间
        hours = period_info.get('hours', [9, 10, 11])  # 默认上午9-11点
        peak_time = period_info.get('peak_time', '10:30')
        
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
        redemption_time = datetime.datetime.combine(
            redemption_date, datetime.time(hour, minute, second))
        
        return redemption_time

    def _get_market_factor(self, date):
        """
        获取市场因素对赎回的影响因子
        
        Args:
            date (datetime.date): 日期
            
        Returns:
            float: 市场因子 (0.7-1.3)
        """
        import random
        
        # 实际实现应考虑历史市场数据
        # 这里使用简化实现，模拟市场波动
        
        # 每月1-5日赎回概率略高（月初资金需求）
        if 1 <= date.day <= 5:
            return random.uniform(1.1, 1.3)
        
        # 每月25-30/31日赎回概率略高（月末资金需求）
        if date.day >= 25:
            return random.uniform(1.1, 1.3)
        
        # 其他日期正常波动
        return random.uniform(0.7, 1.1)

    def _get_seasonal_factor(self, date):
        """
        获取季节性因素对赎回的影响因子
        
        Args:
            date (datetime.date): 日期
            
        Returns:
            float: 季节性因子 (0.8-1.2)
        """
        # 月份因素
        month = date.month
        
        # 春节前（1月）赎回率高
        if month == 1:
            return 1.2
        
        # 年中（6月）和年末（12月）赎回率高
        if month in [6, 12]:
            return 1.15
        
        # 3、9月开学季赎回率略高
        if month in [3, 9]:
            return 1.1
        
        # 其他月份正常
        return 0.9

    def _get_redemption_channel(self, investment):
        """
        确定赎回渠道，通常与购买渠道相同
        
        Args:
            investment (dict): 投资记录
            
        Returns:
            str: 赎回渠道
        """
        import random
        
        # 获取购买渠道
        purchase_channel = investment.get('channel')
        
        # 90%的概率使用相同渠道赎回
        if purchase_channel and random.random() < 0.9:
            return purchase_channel
        
        # 10%的概率使用其他渠道
        channels = ['mobile_app', 'online_banking', 'counter', 'phone_banking']
        weights = [0.5, 0.3, 0.15, 0.05]  # 偏好更方便的渠道
        
        return random.choices(channels, weights=weights, k=1)[0]

    def _record_redemption_transactions(self, redemption_records):
        """
        记录赎回交易流水
        
        Args:
            redemption_records (list): 赎回记录列表
        """
        # 实际实现应创建资金流水记录
        # 这里只记录日志
        self.logger.debug(f"记录 {len(redemption_records)} 条赎回交易流水")
        
        # TODO: 添加资金流水记录逻辑
        # 例如调用db_manager创建资金账户流水记录
        
    def calculate_redemption_probability(self, investment, days_held):
        """计算赎回概率
        
        Args:
            investment: 投资记录
            days_held: 持有天数
            
        Returns:
            float: 赎回概率(0-1)
        """
        # 从配置中获取基础赎回概率
        base_prob = self.redemption_config.get('early_redemption_base_prob', 0.02)
        
        # 计算持有时间影响因素
        # 持有天数越短，赎回概率应该越低
        term_days = investment.get('term', 90)  # 默认为90天
        time_factor = min(1.0, days_held / (term_days * 0.3))  # 至少要持有期限界30%才开始有较高概率赎回
        
        # 产品类型影响因素
        product_id = investment.get('product_id')
        product_type = self._get_product_type(product_id)
        product_factor = 1.0  # 默认因子
        
        # 不同产品类型的赎回概率有所不同
        if product_type == 'monetary_fund':  # 货币基金类较容易赎回
            product_factor = 2.0
        elif product_type == 'bond_fund':  # 债券基金较为稳定
            product_factor = 1.2
        elif product_type == 'stock_fund':  # 股票基金波动性大
            product_factor = 0.8
        
        # 客户类型影响因子
        customer_id = investment.get('customer_id')
        customer_info = self._get_customer_info(customer_id)
        customer_factor = 1.0  # 默认因子
        
        # VIP客户通常更有认知，赎回决策更理性
        if customer_info.get('is_vip', False):
            customer_factor = 0.8
        
        # 最终赎回概率计算 = 基础概率 * 时间因素 * 产品因素 * 客户因素
        final_probability = base_prob * time_factor * product_factor * customer_factor
        
        # 限制概率范围在0-1之间
        return min(1.0, max(0.0, final_probability))
        
    def determine_partial_redemption(self, investment):
        """决定是否部分赎回
        
        Args:
            investment: 投资记录
            
        Returns:
            bool: 是否进行部分赎回
        """
        # 从配置获取部分赎回概率
        partial_redemption_prob = self.redemption_config.get('partial_redemption_prob', 0.4)
        
        # 判断因素：投资金额
        # 大额投资更倾向于部分赎回
        amount = investment.get('hold_amount', 0)
        amount_threshold = 100000  # 假设10万以上的大额投资更可能部分赎回
        if amount > amount_threshold:
            partial_redemption_prob *= 1.5
        
        # 判断因素：产品类型
        product_id = investment.get('product_id')
        product_type = self._get_product_type(product_id)
        
        # 不同产品类型的部分赎回特征不同
        if product_type == 'monetary_fund':  # 货币基金部分赎回性强
            partial_redemption_prob *= 1.3
        elif product_type == 'bond_fund':  # 债券基金适中
            partial_redemption_prob *= 1.0
        elif product_type == 'stock_fund':  # 股票基金较少部分赎回
            partial_redemption_prob *= 0.7
        
        # 随机决定是否部分赎回
        return random.random() < partial_redemption_prob
        
    def calculate_partial_amount(self, investment):
        """计算部分赎回金额
        
        Args:
            investment: 投资记录
            
        Returns:
            float: 部分赎回金额
        """
        # 从配置获取部分赎回比例范围
        min_ratio, max_ratio = self.redemption_config.get('partial_redemption_range', [0.2, 0.7])
        
        # 获取当前持有金额
        hold_amount = investment.get('hold_amount', 0)
        
        # 产品最低持有金额
        product_id = investment.get('product_id')
        product_info = self._get_product_info(product_id)
        min_investment = product_info.get('minimuminvestment', 1000)  # 默认最低1000
        
        # 随机生成部分赎回比例
        redemption_ratio = random.uniform(min_ratio, max_ratio)
        
        # 计算赎回金额
        redemption_amount = hold_amount * redemption_ratio
        
        # 查看赎回后剩余金额是否低于最低持有金额
        remaining_amount = hold_amount - redemption_amount
        
        # 如果剩余金额低于最低持有金额，则全额赎回
        if remaining_amount < min_investment:
            return hold_amount
        
        # 如果赎回金额太小，还不如不赎回，这个逻辑在整体赎回决策中已经处理
        min_redemption = 100  # 假设最小赎回金额为100
        if redemption_amount < min_redemption:
            redemption_amount = min_redemption
            
            # 再次检查剩余金额
            remaining_amount = hold_amount - redemption_amount
            if remaining_amount < min_investment:
                return hold_amount
        
        return redemption_amount
        
    def update_investment_status(self, investment_id, redemption_info):
        """
        更新投资状态
        
        根据赎回信息更新投资记录的状态、持有金额和赎回时间
        
        Args:
            investment_id (str): 投资记录ID
            redemption_info (dict): 赎回信息，包含赎回金额、类型等
            
        Returns:
            bool: 更新是否成功
            dict: 更新后的投资记录
        """
        if not investment_id or not redemption_info:
            self.logger.error("更新投资状态的参数无效")
            return False, None
        
        try:
            # 获取当前投资记录
            investment = self._get_investment_info(investment_id)
            if not investment:
                self.logger.error(f"未找到投资记录，ID: {investment_id}")
                return False, None
            
            # 获取赎回信息
            redemption_amount = float(redemption_info.get('redemption_amount', 0))
            is_full_redemption = redemption_info.get('is_full_redemption', False)
            redemption_timestamp = redemption_info.get('redemption_timestamp')
            
            # 验证赎回金额
            current_hold_amount = float(investment.get('hold_amount', 0))
            
            if redemption_amount <= 0:
                self.logger.error(f"赎回金额无效: {redemption_amount}")
                return False, None
                
            if redemption_amount > current_hold_amount:
                self.logger.error(f"赎回金额({redemption_amount})大于当前持有金额({current_hold_amount})")
                return False, None
            
            # 准备更新内容
            updates = {}
            
            # 更新持有金额
            new_hold_amount = current_hold_amount - redemption_amount
            updates['hold_amount'] = round(new_hold_amount, 2)
            
            # 更新状态
            if is_full_redemption or new_hold_amount <= 0:
                # 全部赎回
                updates['wealth_status'] = '完全赎回'
                updates['wealth_all_redeem_time'] = redemption_timestamp
                updates['hold_amount'] = 0  # 确保持有金额为0
            else:
                # 部分赎回
                updates['wealth_status'] = '部分卖出'
            
            # 执行更新
            success = self._update_investment_record(investment_id, updates)
            
            if success:
                # 合并原记录和更新内容，返回更新后的记录
                updated_investment = {**investment, **updates}
                
                # 记录日志
                self.logger.info(f"投资记录 {investment_id} 状态更新成功: {updates}")
                
                # 更新客户财富状态
                if self._update_customer_wealth_status(investment, redemption_info):
                    self.logger.info(f"客户 {investment.get('base_id')} 财富状态更新成功")
                
                return True, updated_investment
            else:
                self.logger.error(f"投资记录 {investment_id} a状态更新失败")
                return False, None
            
        except Exception as e:
            self.logger.error(f"更新投资状态时出错: {str(e)}")
            return False, None

    def _get_investment_info(self, investment_id):
        """
        获取投资记录信息
        
        Args:
            investment_id (str): 投资记录ID
            
        Returns:
            dict: 投资记录信息
        """
        try:
            query = """
            SELECT * FROM cdp_investment_order 
            WHERE detail_id = %s
            """
            
            results = self.db_manager.execute_query(query, (investment_id,))
            
            if results and len(results) > 0:
                return results[0]
            
            return None
            
        except Exception as e:
            self.logger.error(f"获取投资记录时出错: {str(e)}")
            return None

    def _update_investment_record(self, investment_id, updates):
        """
        更新投资记录
        
        Args:
            investment_id (str): 投资记录ID
            updates (dict): 需要更新的字段和值
            
        Returns:
            bool: 更新是否成功
        """
        try:
            if not updates:
                return True
            
            # 构建SET子句
            set_clause = ", ".join([f"{field} = %s" for field in updates.keys()])
            
            # 构建参数列表
            params = list(updates.values())
            params.append(investment_id)  # WHERE条件参数
            
            # 构建更新语句
            update_query = f"""
            UPDATE cdp_investment_order 
            SET {set_clause} 
            WHERE detail_id = %s
            """
            
            # 执行更新
            result = self.db_manager.execute_update(update_query, params)
            
            return result
            
        except Exception as e:
            self.logger.error(f"更新投资记录时出错: {str(e)}")
            return False

    def _update_customer_wealth_status(self, investment, redemption_info):
        """
        更新客户财富状态
        
        Args:
            investment (dict): 投资记录
            redemption_info (dict): 赎回信息
            
        Returns:
            bool: 更新是否成功
        """
        # 获取客户ID
        customer_id = investment.get('base_id')
        if not customer_id:
            self.logger.warning("投资记录中没有客户ID，无法更新客户财富状态")
            return False
        
        # 构建包含赎回信息的完整记录
        combined_info = {
            **investment,
            'redemption_amount': redemption_info.get('redemption_amount'),
            'is_full_redemption': redemption_info.get('is_full_redemption'),
            'wealth_all_redeem_time': redemption_info.get('redemption_timestamp')
        }
        
        # 调用投资记录生成器的客户状态更新方法
        if hasattr(self, 'investment_generator') and self.investment_generator:
            # 如果有引用投资记录生成器，直接调用
            return self.investment_generator.update_customer_wealth_status(customer_id, combined_info)
        else:
            # 否则尝试导入并创建一个实例
            try:
                from src.data_generator.investment.investment_record_generator import InvestmentRecordGenerator
                generator = InvestmentRecordGenerator(self.db_manager, self.config, self.logger, self.time_manager)
                return generator.update_customer_wealth_status(customer_id, combined_info)
            except Exception as e:
                self.logger.error(f"创建投资记录生成器实例时出错: {str(e)}")
                return False
        
    def check_redemption_constraints(self, investment, redemption_date):
        """检查赎回约束条件
        
        Args:
            investment: 投资记录
            redemption_date: 赎回日期
            
        Returns:
            bool: 是否可以赎回
            str: 不可赎回原因
        """
        # 检查投资状态
        status = investment.get('status')
        if status not in ['holding', 'partial_redeemed']:
            return False, f"Investment status '{status}' does not allow redemption"
        
        # 检查是否在锁定期内
        purchase_date = investment.get('purchase_date')
        if not purchase_date:
            return False, "Purchase date is missing"
        
        # 获取产品锁定期信息
        product_id = investment.get('product_id')
        product_info = self._get_product_info(product_id)
        lock_period_days = product_info.get('lock_period_days', 0)  # 默认无锁定期
        
        # 计算持有天数
        days_held = (redemption_date - purchase_date).days
        
        # 检查是否超过锁定期
        if days_held < lock_period_days:
            return False, f"Still in lock period, {lock_period_days - days_held} days remaining"
        
        # 检查赎回方式
        redemption_way = product_info.get('redemptionway', '随时赎回')
        if redemption_way == '固定赎回':
            # 检查是否是允许赎回的日期
            # 这里可以根据具体产品规则进行判断
            # 简化处理：假设只有每月固定日期可赎回
            allowed_days = product_info.get('redemption_days', [15])  # 默认每月15号
            if redemption_date.day not in allowed_days:
                return False, f"Fixed redemption only allowed on days: {allowed_days}"
        
        # 检查赎回是否在交易时间内
        hour = redemption_date.hour
        if not (9 <= hour < 15):  # 假设交易时间为9点到15点
            return False, "Redemption only allowed during trading hours (9:00-15:00)"
        
        # 通过所有检查
        return True, ""
        
    def generate_redemption_batch(self, date):
        """批量生成某日赎回记录
        
        Args:
            date: 当前处理日期
            
        Returns:
            list: 生成的赎回记录列表
        """
        # 获取所有未完全赎回的投资记录
        active_investments = self._get_active_investments()
        
        # 先处理到期赎回
        maturity_redemptions = self.process_maturity_redemptions(active_investments, date)
        
        # 处理提前赎回
        early_redemptions = self.generate_early_redemptions(active_investments, date)
        
        # 合并所有赎回记录
        all_redemptions = maturity_redemptions + early_redemptions
        
        return all_redemptions
    
    def calculate_early_redemption_probability(self, investment, customer_info, current_date):
        """计算投资提前赎回的概率
        
        考虑多种因素计算特定投资提前赎回的概率
        
        Args:
            investment (dict): 投资记录
            customer_info (dict): 客户信息
            current_date (datetime.date): 当前日期
            
        Returns:
            float: 提前赎回概率(0-1)
        """
        try:
            # 1. 获取基础赎回概率
            base_probability = self.redemption_config.get('early_redemption_base_prob', 0.002)
            
            # 如果基础概率不合理，使用默认值
            if not isinstance(base_probability, (int, float)) or base_probability <= 0 or base_probability > 1:
                base_probability = 0.002  # 每日约0.2%的基础赎回概率
            
            # 2. 计算持有期因子
            holding_period_factor = self._calculate_holding_period_factor(investment, current_date)
            
            # 3. 计算客户特征因子
            customer_factor = self._calculate_customer_factor(customer_info)
            
            # 4. 计算产品特征因子
            product_factor = self._calculate_product_factor(investment)
            
            # 5. 计算市场因素因子
            market_factor = self._calculate_market_factor(current_date)
            
            # 6. 计算最终概率
            final_probability = (
                base_probability * 
                holding_period_factor * 
                customer_factor * 
                product_factor * 
                market_factor
            )
            
            # 确保概率在合理范围内
            final_probability = max(0.0, min(0.5, final_probability))  # 单日最高50%的概率
            
            # 记录详细计算过程（调试级别）
            self.logger.debug(
                f"赎回概率计算 - ID: {investment.get('detail_id')}, "
                f"基础: {base_probability:.4f}, "
                f"持有期: {holding_period_factor:.2f}, "
                f"客户: {customer_factor:.2f}, "
                f"产品: {product_factor:.2f}, "
                f"市场: {market_factor:.2f}, "
                f"最终: {final_probability:.4f}"
            )
            
            return final_probability
            
        except Exception as e:
            self.logger.error(f"计算提前赎回概率时出错: {str(e)}")
            return base_probability  # 发生错误时返回基础概率
        
    def _calculate_holding_period_factor(self, investment, current_date):
        """计算持有期因子
        
        投资持有时间占总期限的比例影响赎回概率
        
        Args:
            investment (dict): 投资记录
            current_date (datetime.date): 当前日期
            
        Returns:
            float: 持有期因子
        """
        try:
            # 获取购买日期和到期日期
            purchase_time = investment.get('wealth_purchase_time')
            maturity_time = investment.get('maturity_time')
            
            # 如果没有到期日期，使用中等因子
            if not maturity_time:
                return 1.0
            
            # 转换时间戳为日期对象
            if isinstance(purchase_time, (int, float)):
                if purchase_time > 1000000000000:  # 13位毫秒级时间戳
                    purchase_date = datetime.datetime.fromtimestamp(purchase_time / 1000).date()
                else:  # 10位秒级时间戳
                    purchase_date = datetime.datetime.fromtimestamp(purchase_time).date()
            else:
                # 如果时间字段无效，使用默认因子
                return 1.0
                
            if isinstance(maturity_time, (int, float)):
                if maturity_time > 1000000000000:  # 13位毫秒级时间戳
                    maturity_date = datetime.datetime.fromtimestamp(maturity_time / 1000).date()
                else:  # 10位秒级时间戳
                    maturity_date = datetime.datetime.fromtimestamp(maturity_time).date()
            else:
                # 如果时间字段无效，使用默认因子
                return 1.0
            
            # 计算总投资期限（天数）
            total_period = (maturity_date - purchase_date).days
            if total_period <= 0:
                return 1.0  # 避免除以零
            
            # 计算已持有期限（天数）
            elapsed_period = (current_date - purchase_date).days
            if elapsed_period < 0:
                elapsed_period = 0  # 防止负数
            
            # 计算持有期比例
            holding_ratio = elapsed_period / total_period
            
            # 获取持有期因子配置
            holding_factors = self.redemption_config.get('holding_period_factors', {
                'short': 0.2,   # 刚购买不久(<=15%)
                'middle': 1.0,  # 中期持有(15%-70%)
                'late': 1.5     # 接近到期(>70%)
            })
            
            # 根据持有期比例确定因子
            if holding_ratio <= 0.15:
                # 持有时间不长，赎回概率低
                return holding_factors.get('short', 0.2)
            elif holding_ratio <= 0.7:
                # 中期持有，正常赎回概率
                # 随着持有时间增加，概率逐渐提高
                middle_factor = holding_factors.get('middle', 1.0)
                ratio_within_range = (holding_ratio - 0.15) / (0.7 - 0.15)
                return middle_factor * (0.8 + 0.4 * ratio_within_range)
            else:
                # 接近到期，赎回概率高
                # 特别是接近到期但又不想等到最后的情况
                return holding_factors.get('late', 1.5)
                
        except Exception as e:
            self.logger.error(f"计算持有期因子时出错: {str(e)}")
            return 1.0  # 发生错误时返回默认因子
        
    def _calculate_customer_factor(self, customer_info):
        """计算客户特征因子
        
        客户特征（类型、风险偏好等）影响赎回概率
        
        Args:
            customer_info (dict): 客户信息
            
        Returns:
            float: 客户特征因子
        """
        try:
            # 基础因子
            factor = 1.0
            
            # 获取客户类型调整因子配置
            customer_type_factors = self.redemption_config.get('customer_type_factors', {
                'personal': 1.0,
                'personal_vip': 0.8,  # VIP客户提前赎回概率略低
                'corporate': 1.2      # 企业客户提前赎回概率略高
            })
            
            # 获取风险等级调整因子配置
            risk_level_factors = self.redemption_config.get('risk_level_factors', {
                'R1': 0.8,  # 保守型客户赎回概率低
                'R2': 0.9,
                'R3': 1.0,  # 基准
                'R4': 1.1,
                'R5': 1.2   # 激进型客户赎回概率高
            })
            
            # 应用客户类型因子
            customer_type = customer_info.get('customer_type', 'personal')
            is_vip = customer_info.get('is_vip', False)
            
            if customer_type == 'personal' and is_vip:
                # VIP个人客户
                type_factor = customer_type_factors.get('personal_vip', 0.8)
            else:
                # 普通个人客户或企业客户
                type_factor = customer_type_factors.get(customer_type, 1.0)
            
            # 应用风险等级因子
            risk_level = customer_info.get('risk_level', 'R3')
            risk_factor = risk_level_factors.get(risk_level, 1.0)
            
            # 考虑历史行为 (如果可用)
            if 'nousedays' in customer_info:
                try:
                    # 资金未发生支用天数
                    nousedays = int(customer_info.get('nousedays', 0))
                    # 长时间未操作的客户可能更倾向于继续持有
                    if nousedays > 180:  # 超过半年未操作
                        unused_factor = 0.8
                    elif nousedays > 90:  # 超过3个月未操作
                        unused_factor = 0.9
                    else:
                        unused_factor = 1.0
                        
                    # 应用未操作因子
                    factor *= unused_factor
                except (ValueError, TypeError):
                    # 无法解析未操作天数，使用默认因子
                    pass
            
            # 合并类型因子和风险因子
            factor *= type_factor * risk_factor
            
            # 确保因子在合理范围内
            return max(0.5, min(2.0, factor))
                
        except Exception as e:
            self.logger.error(f"计算客户特征因子时出错: {str(e)}")
            return 1.0  # 发生错误时返回默认因子
        
    def _calculate_product_factor(self, investment):
        """计算产品特征因子
        
        产品特征（类型、流动性等）影响赎回概率
        
        Args:
            investment (dict): 投资记录
            
        Returns:
            float: 产品特征因子
        """
        try:
            # 基础因子
            factor = 1.0
            
            # 获取产品类型调整因子配置
            product_type_factors = self.redemption_config.get('product_type_factors', {
                '债券型基金': 0.9,    # 较稳定
                '货币型基金': 1.2,    # 流动性高
                '股票型基金': 1.3,    # 波动大，赎回概率高
                '混合型基金': 1.1
            })
            
            # 应用产品类型因子
            product_type = investment.get('product_type', '')
            # 如果没有产品类型，可能需要查询产品信息
            if not product_type and 'product_id' in investment:
                product_info = self._get_product_info(investment.get('product_id'))
                if product_info:
                    product_type = product_info.get('product_type', '')
            
            # 应用产品类型因子
            type_factor = product_type_factors.get(product_type, 1.0)
            factor *= type_factor
            
            # 考虑赎回方式
            redemption_way = investment.get('redemption_way', '')
            # 如果没有赎回方式，可能需要查询产品信息
            if not redemption_way and 'product_id' in investment:
                product_info = self._get_product_info(investment.get('product_id'))
                if product_info:
                    redemption_way = product_info.get('redemption_way', '')
            
            # 随时赎回的产品赎回概率高于固定赎回
            if redemption_way == '随时赎回':
                factor *= 1.2
            elif redemption_way == '固定赎回':
                factor *= 0.8
            
            # 考虑投资金额
            purchase_amount = float(investment.get('purchase_amount', 0))
            if purchase_amount > 1000000:  # 100万以上大额投资
                factor *= 0.9  # 大额投资赎回概率较低
            elif purchase_amount < 50000:  # 5万以下小额投资
                factor *= 1.1  # 小额投资赎回概率较高
            
            # 确保因子在合理范围内
            return max(0.5, min(2.0, factor))
                
        except Exception as e:
            self.logger.error(f"计算产品特征因子时出错: {str(e)}")
            return 1.0  # 发生错误时返回默认因子
        
    def _calculate_market_factor(self, current_date):
        """计算市场因素因子
        
        市场环境（牛熊市、利率变化等）影响赎回概率
        
        Args:
            current_date (datetime.date): 当前日期
            
        Returns:
            float: 市场因素因子
        """
        try:
            # 简化实现：目前使用月份作为市场条件的简易指标
            # 实际系统中，可能需要基于外部市场数据或更复杂的模型
            
            # 获取月份
            month = current_date.month
            
            # 获取市场条件因子配置
            market_condition_factors = self.redemption_config.get('market_condition_factors', {
                'bull': 0.8,    # 牛市，赎回概率低
                'normal': 1.0,  # 平稳市场
                'bear': 1.3     # 熊市，赎回概率高
            })
            
            # 简化模型：根据月份判断市场状况
            # 实际应该基于市场指标和经济数据
            if month in [1, 2, 11, 12]:  # 年初年末通常较好
                market_condition = 'bull'
            elif month in [6, 7, 8]:     # 夏季可能波动较大
                market_condition = 'bear'
            else:                         # 其他时间正常
                market_condition = 'normal'
            
            # 应用市场条件因子
            factor = market_condition_factors.get(market_condition, 1.0)
            
            # 月初月末效应
            day = current_date.day
            if day <= 5:  # 月初
                factor *= 0.9  # 月初赎回概率较低
            elif day >= 25:  # 月末
                factor *= 1.1  # 月末赎回概率较高
            
            # 确保因子在合理范围内
            return max(0.5, min(1.5, factor))
                
        except Exception as e:
            self.logger.error(f"计算市场因素因子时出错: {str(e)}")
            return 1.0  # 发生错误时返回默认因子
        
    def _get_product_info(self, product_id):
        """获取产品信息
        
        Args:
            product_id (str): 产品ID
            
        Returns:
            dict: 产品信息字典，如果未找到返回None
        """
        try:
            query = "SELECT * FROM cdp_product_archive WHERE base_id = %s"
            results = self.db_manager.execute_query(query, (product_id,))
            
            if results and len(results) > 0:
                return results[0]
            
            return None
                
        except Exception as e:
            self.logger.error(f"获取产品信息时出错: {str(e)}")
            return None
        
    def generate_early_redemptions(self, date_range, customer_ids=None):
        """生成提前赎回记录
        
        根据各种因素计算提前赎回概率，生成提前赎回记录
        
        Args:
            date_range (tuple): 日期范围(start_date, end_date)
            customer_ids (list, optional): 客户ID列表，如不提供则处理所有符合条件的客户
            
        Returns:
            int: 生成的提前赎回记录数量
        """
        import random
        import datetime
        
        start_date, end_date = date_range
        
        # 确保日期格式一致
        if isinstance(start_date, str):
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # 检查日期范围有效性
        if start_date > end_date:
            self.logger.error(f"无效的日期范围: {start_date} 至 {end_date}")
            return 0
        
        self.logger.info(f"开始生成 {start_date} 至 {end_date} 期间的提前赎回记录")
        
        try:
            # 获取活跃投资记录
            active_investments = self._get_active_investments(date_range, customer_ids)
            
            if not active_investments:
                self.logger.info("没有找到符合条件的活跃投资记录")
                return 0
            
            self.logger.info(f"找到 {len(active_investments)} 条活跃投资记录")
            
            # 获取当前系统时间，用于后续时间戳计算
            current_time = datetime.datetime.now()
            
            # 初始化统计变量
            total_generated = 0
            redemption_records = []
            
            # 设置随机种子以确保可重复性
            random_seed = self.config.get('system', {}).get('random_seed', None)
            if random_seed is not None:
                random.seed(random_seed)
            
            # 对每条投资记录计算提前赎回概率
            for investment in active_investments:
                try:
                    customer_id = investment.get('base_id')
                    investment_id = investment.get('detail_id')
                    
                    # 获取客户信息
                    customer_info = self._get_customer_info(customer_id)
                    if not customer_info:
                        self.logger.warning(f"未找到客户信息，客户ID: {customer_id}，跳过赎回计算")
                        continue
                    
                    # 计算该日期范围内的赎回概率
                    # 遍历日期范围中的每一天
                    current_date = start_date
                    while current_date <= end_date:
                        # 检查该投资在当前日期是否满足提前赎回条件
                        
                        # 1. 计算提前赎回概率
                        redemption_prob = self.calculate_early_redemption_probability(
                            investment, customer_info, current_date)
                        
                        # 2. 根据概率决定是否赎回
                        if random.random() < redemption_prob:
                            # 决定赎回类型：部分赎回或全额赎回
                            redemption_type = self.decide_redemption_type(investment, customer_info)
                            
                            # 创建赎回记录
                            redemption_record = self._create_redemption_record(
                                investment, redemption_type, current_date)
                            
                            if redemption_record:
                                redemption_records.append(redemption_record)
                                total_generated += 1
                                
                                # 记录生成的赎回
                                self.logger.debug(
                                    f"生成提前赎回记录 - 客户: {customer_id}, "
                                    f"投资ID: {investment_id}, "
                                    f"类型: {redemption_type}, "
                                    f"日期: {current_date}"
                                )
                                
                                # 如果是全额赎回，不再考虑后续日期
                                if redemption_type == 'full':
                                    break
                        
                        # 移动到下一天
                        current_date += datetime.timedelta(days=1)
                
                except Exception as e:
                    self.logger.error(f"处理投资记录 {investment.get('detail_id')} 赎回时出错: {str(e)}")
            
            # 更新数据库
            if redemption_records:
                self._update_investment_records(redemption_records)
                
                # 更新客户财富状态
                self._update_customer_wealth_status(redemption_records)
                
                # 生成赎回相关事件
                if self.events_generator:
                    self._generate_redemption_events(redemption_records)
            
            self.logger.info(f"成功生成 {total_generated} 条提前赎回记录")
            return total_generated
                
        except Exception as e:
            self.logger.error(f"生成提前赎回记录时出错: {str(e)}")
            return 0
        
    def _get_active_investments(self, date_range, customer_ids=None):
        """获取活跃投资记录
        
        查询符合条件的、状态为"持有"的投资记录
        
        Args:
            date_range (tuple): 日期范围(start_date, end_date)
            customer_ids (list, optional): 客户ID列表
            
        Returns:
            list: 投资记录列表
        """
        start_date, end_date = date_range
        
        try:
            # 构建基本查询条件：只查询持有状态的记录
            conditions = ["wealth_status = '持有'"]
            params = []
            
            # 构建客户ID条件
            if customer_ids:
                id_placeholders = ', '.join(['%s'] * len(customer_ids))
                conditions.append(f"base_id IN ({id_placeholders})")
                params.extend(customer_ids)
            
            # 构建到期日条件：筛选出没有到期或到期日在开始日期之后的记录
            # 将日期转换为毫秒级时间戳
            start_timestamp = int(datetime.datetime.combine(
                start_date, datetime.time(0, 0, 0)).timestamp() * 1000)
            
            conditions.append("(maturity_time IS NULL OR maturity_time > %s)")
            params.append(start_timestamp)
            
            # 购买日期条件：确保购买日期在结束日期之前
            end_timestamp = int(datetime.datetime.combine(
                end_date, datetime.time(23, 59, 59)).timestamp() * 1000)
            
            conditions.append("wealth_purchase_time < %s")
            params.append(end_timestamp)
            
            # 构建查询语句
            query = """
            SELECT i.*, p.product_type, p.redemption_way
            FROM cdp_investment_order i
            LEFT JOIN cdp_product_archive p ON i.product_id = p.base_id
            WHERE """ + " AND ".join(conditions)
            
            # 执行查询
            investments = self.db_manager.execute_query(query, params)
            
            return investments
            
        except Exception as e:
            self.logger.error(f"获取活跃投资记录时出错: {str(e)}")
            return []
        
    def decide_redemption_type(self, investment, customer_info):
        """决定赎回类型：部分赎回或全额赎回
        
        Args:
            investment (dict): 投资记录
            customer_info (dict): 客户信息
            
        Returns:
            str: 赎回类型('partial' 或 'full')
        """
        # 获取部分赎回概率
        partial_redemption_prob = self.redemption_config.get('partial_redemption_prob', 0.4)
        
        # 调整因素列表及其权重
        adjustment_factors = []
        
        # 1. 投资金额：大额投资更倾向于部分赎回
        purchase_amount = float(investment.get('purchase_amount', 0))
        if purchase_amount > 500000:  # 50万以上
            adjustment_factors.append(0.2)  # 增加部分赎回概率
        elif purchase_amount > 100000:  # 10万以上
            adjustment_factors.append(0.1)  # 小幅增加部分赎回概率
        elif purchase_amount < 30000:  # 3万以下
            adjustment_factors.append(-0.15)  # 减少部分赎回概率
        
        # 2. 客户类型：企业客户更倾向于部分赎回
        customer_type = customer_info.get('customer_type', 'personal')
        if customer_type == 'corporate':
            adjustment_factors.append(0.15)  # 增加部分赎回概率
        
        # 3. 投资期限：长期投资更可能部分赎回
        purchase_time = investment.get('wealth_purchase_time')
        maturity_time = investment.get('maturity_time')
        
        if purchase_time and maturity_time:
            try:
                # 转换为日期对象
                if purchase_time > 1000000000000:  # 13位毫秒级时间戳
                    purchase_time /= 1000
                if maturity_time > 1000000000000:  # 13位毫秒级时间戳
                    maturity_time /= 1000
                    
                total_days = (maturity_time - purchase_time) / (24 * 3600)  # 秒转换为天
                
                if total_days > 365:  # 超过1年的投资
                    adjustment_factors.append(0.15)  # 增加部分赎回概率
                elif total_days > 180:  # 超过半年的投资
                    adjustment_factors.append(0.05)  # 小幅增加部分赎回概率
            except:
                # 时间计算出错，不调整概率
                pass
        
        # 4. VIP客户更倾向于灵活理财方式
        is_vip = customer_info.get('is_vip', False)
        if is_vip:
            adjustment_factors.append(0.1)  # VIP客户增加部分赎回概率
        
        # 5. 风险等级：高风险等级客户可能更倾向于全额赎回以规避风险
        risk_level = customer_info.get('risk_level', 'R3')
        if risk_level in ['R4', 'R5']:
            adjustment_factors.append(-0.1)  # 减少部分赎回概率（增加全额赎回概率）
        
        # 应用所有调整因素
        for factor in adjustment_factors:
            partial_redemption_prob += factor
        
        # 确保概率在有效范围内
        partial_redemption_prob = max(0.1, min(0.9, partial_redemption_prob))
        
        # 根据概率决定赎回类型
        if random.random() < partial_redemption_prob:
            return 'partial'
        else:
            return 'full'
        
    def _get_customer_info(self, customer_id):
        """获取客户信息
        
        Args:
            customer_id (str): 客户ID
            
        Returns:
            dict: 客户信息字典，如果未找到返回None
        """
        try:
            query = "SELECT * FROM cdp_customer_profile WHERE base_id = %s"
            results = self.db_manager.execute_query(query, (customer_id,))
            
            if results and len(results) > 0:
                return results[0]
            
            return None
                
        except Exception as e:
            self.logger.error(f"获取客户信息时出错: {str(e)}")
            return None
