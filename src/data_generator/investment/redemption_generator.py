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
                "early_redemption_base_prob": 0.02,  # 每日提前赎回基础概率
                "partial_redemption_prob": 0.4,      # 部分赎回概率
                "partial_redemption_range": [0.2, 0.7],  # 部分赎回金额比例范围
                "market_volatility_impact": 0.5      # 市场波动对赎回的影响系数
            }
        
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
        
    def generate_early_redemptions(self, investments, date_range):
        """
        生成提前赎回行为
        
        Args:
            investments (list): 投资记录列表，包含持有中的理财产品信息
            date_range (tuple): 日期范围，格式为(start_date, end_date)
            
        Returns:
            list: 生成的赎回记录列表
        """
        import random
        import datetime
        
        # 验证输入参数
        if not investments:
            self.logger.debug("没有投资记录，无法生成赎回行为")
            return []
        
        # 解析日期范围
        start_date, end_date = date_range
        
        # 确保日期类型一致
        if isinstance(start_date, str):
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # 初始化结果列表
        redemption_records = []
        
        # 从配置获取赎回参数
        early_redemption_base_prob = self.redemption_config.get('early_redemption_base_prob', 0.02)
        partial_redemption_prob = self.redemption_config.get('partial_redemption_prob', 0.4)
        
        self.logger.info(f"开始生成提前赎回记录，投资记录数: {len(investments)}, 日期范围: {start_date} 至 {end_date}")
        
        # 按日期遍历，每天检查可能的赎回事件
        current_date = start_date
        while current_date <= end_date:
            # 当日可能赎回的投资列表（状态为持有或部分卖出）
            valid_investments = [
                inv for inv in investments
                if (inv.get('wealth_status') in ['持有', '部分卖出']) and
                (self._parse_date(inv.get('wealth_date')) < current_date)  # 购买日期早于当前日期
            ]
            
            # 如果没有有效投资，跳过当天
            if not valid_investments:
                current_date += datetime.timedelta(days=1)
                continue
            
            self.logger.debug(f"处理日期 {current_date}, 有效投资记录数: {len(valid_investments)}")
            
            # 当日赎回记录
            day_redemptions = []
            
            # 遍历每笔投资，计算赎回概率
            for investment in valid_investments:
                # 获取购买日期
                purchase_date = self._parse_date(investment.get('wealth_date'))
                
                # 计算持有天数
                days_held = (current_date - purchase_date).days
                
                # 获取投资信息
                investment_id = investment.get('detail_id')
                customer_id = investment.get('base_id')
                product_id = investment.get('product_id')
                hold_amount = investment.get('hold_amount', 0)
                
                # 如果持有金额为0，跳过
                if hold_amount <= 0:
                    continue
                
                # 检查赎回约束条件
                can_redeem, reason = self.check_redemption_constraints(investment, current_date)
                if not can_redeem:
                    self.logger.debug(f"投资 {investment_id} 不满足赎回条件: {reason}")
                    continue
                
                # 计算赎回概率
                redemption_prob = self.calculate_redemption_probability(investment, days_held)
                
                # 考虑市场因素和季节性因素调整概率
                market_factor = self._get_market_factor(current_date)
                seasonal_factor = self._get_seasonal_factor(current_date)
                
                adjusted_prob = redemption_prob * market_factor * seasonal_factor
                
                # 随机决定是否赎回
                if random.random() < adjusted_prob:
                    # 决定是部分赎回还是全部赎回
                    is_partial = random.random() < partial_redemption_prob
                    
                    if is_partial and hold_amount > 1000:  # 只有金额足够大时才考虑部分赎回
                        # 确定部分赎回
                        is_partial = self.determine_partial_redemption(investment)
                        
                        if is_partial:
                            # 计算部分赎回金额
                            redemption_amount = self.calculate_partial_amount(investment)
                        else:
                            # 全额赎回
                            redemption_amount = hold_amount
                    else:
                        # 金额较小或概率不满足，全额赎回
                        is_partial = False
                        redemption_amount = hold_amount
                    
                    # 创建赎回记录
                    redemption_time = self._generate_redemption_time(current_date, customer_id)
                    
                    redemption_record = {
                        'investment_id': investment_id,
                        'customer_id': customer_id,
                        'product_id': product_id,
                        'redemption_date': current_date,
                        'redemption_time': redemption_time,
                        'redemption_timestamp': int(redemption_time.timestamp() * 1000),  # 13位时间戳
                        'redemption_amount': round(redemption_amount, 2),
                        'is_full_redemption': not is_partial,
                        'redemption_type': 'early',  # 提前赎回
                        'channel': self._get_redemption_channel(investment),
                        'remaining_amount': round(hold_amount - redemption_amount, 2) if is_partial else 0
                    }
                    
                    # 添加到当日赎回记录
                    day_redemptions.append(redemption_record)
                    
                    # 更新投资记录的持有金额和状态
                    if is_partial:
                        investment['hold_amount'] = round(hold_amount - redemption_amount, 2)
                        investment['wealth_status'] = '部分卖出'
                    else:
                        investment['hold_amount'] = 0
                        investment['wealth_status'] = '完全赎回'
                        investment['wealth_all_redeem_time'] = redemption_record['redemption_timestamp']
            
            # 处理当日赎回记录
            if day_redemptions:
                self.logger.info(f"日期 {current_date} 生成赎回记录 {len(day_redemptions)} 条")
                
                # 记录赎回流水
                self._record_redemption_transactions(day_redemptions)
                
                # 添加到总结果
                redemption_records.extend(day_redemptions)
            
            # 移动到下一天
            current_date += datetime.timedelta(days=1)
        
        self.logger.info(f"提前赎回记录生成完成，总生成记录数: {len(redemption_records)}")
        
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
