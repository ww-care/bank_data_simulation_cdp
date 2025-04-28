    # 辅助方法
    def _get_product_type(self, product_id):
        """获取产品类型信息辅助方法"""
        # TODO: 实际实现时需要从数据库获取
        # 这里仅作为框架设计示例
        return "monetary_fund"  # 默认返回值
    
    def _get_customer_info(self, customer_id):
        """获取客户信息辅助方法"""
        # TODO: 实际实现时需要从数据库获取
        # 这里仅作为框架设计示例
        return {"is_vip": False}  # 默认返回值
    
    def _get_product_info(self, product_id):
        """获取产品信息辅助方法"""
        # TODO: 实际实现时需要从数据库获取
        # 这里仅作为框架设计示例
        return {
            "minimuminvestment": 1000,
            "lock_period_days": 7,
            "redemptionway": "随时赎回"
        }  # 默认返回值
    
    def _get_active_investments(self):
        """获取所有未完全赎回的投资记录"""
        # TODO: 实际实现时需要从数据库获取
        # 这里仅作为框架设计示例
        return []  # 默认返回空列表"""
理财赎回行为生成器
模拟客户的理财产品赎回行为，包括到期自动赎回、提前赎回和部分赎回
"""


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
        """生成提前赎回行为"""
        # TODO: 实现提前赎回行为生成逻辑
        pass
        
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
        """更新投资状态"""
        # TODO: 实现投资状态更新逻辑
        pass
        
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
