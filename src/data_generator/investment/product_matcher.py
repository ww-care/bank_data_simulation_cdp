"""
理财产品匹配逻辑
根据客户风险偏好、财力状况等因素匹配适合的理财产品
"""


class ProductMatcher:
    """理财产品匹配逻辑"""
    
    def __init__(self, db_manager, config, logger):
        """初始化匹配器
        
        Args:
            db_manager: 数据库管理器
            config: 理财生成器配置
            logger: 日志对象
        """
        self.db_manager = db_manager
        self.config = config
        self.logger = logger
        self.risk_mapping = {}
        
    def initialize_risk_mapping(self):
        """初始化风险等级映射"""
        # 从配置中获取风险等级映射
        self.risk_mapping = self.config.get('risk_level_mapping', {})
        
        # 如果配置中没有风险等级映射，使用默认映射
        if not self.risk_mapping:
            self.logger.warning("No risk level mapping found in config, using default mapping")
            self.risk_mapping = {
                "R1": {"acceptable_risk": ["low"], "weight": 1.0},
                "R2": {"acceptable_risk": ["low"], "weight": 0.9},
                "R3": {"acceptable_risk": ["low", "medium"], "weight": 0.8},
                "R4": {"acceptable_risk": ["low", "medium", "high"], "weight": 0.7},
                "R5": {"acceptable_risk": ["low", "medium", "high"], "weight": 0.6}
            }
            
        self.logger.info(f"Risk level mapping initialized: {self.risk_mapping}")
        
    def find_matching_products(self, customer_info, exclude_products=None):
        """查找匹配客户风险偏好的产品"""
        # TODO: 实现匹配产品查找逻辑
        pass
        
    def match_risk_level(self, customer_risk, product_risk):
        """风险等级匹配逻辑
        
        Args:
            customer_risk: 客户风险等级（如R1-R5）
            product_risk: 产品风险等级（如low/medium/high）
        
        Returns:
            bool: 是否匹配
            float: 匹配分数（0-1）
        """
        # 若风险映射还未初始化，先初始化
        if not self.risk_mapping:
            self.initialize_risk_mapping()
        
        # 获取客户风险等级对应的可接受产品风险等级
        customer_profile = self.risk_mapping.get(customer_risk, {})
        acceptable_risks = customer_profile.get('acceptable_risk', [])
        weight = customer_profile.get('weight', 0.0)
        
        # 检查产品风险是否在客户可接受范围内
        is_match = product_risk in acceptable_risks
        
        # 计算匹配分数
        # 例如：高风险承受能力客户购买低风险产品分数较低
        # 低风险承受能力客户购买低风险产品分数较高
        match_score = 0.0
        if is_match:
            risk_levels = {'low': 0, 'medium': 1, 'high': 2}
            product_risk_level = risk_levels.get(product_risk, 0)
            risk_preference_levels = {'R1': 0, 'R2': 1, 'R3': 2, 'R4': 3, 'R5': 4}
            customer_risk_level = risk_preference_levels.get(customer_risk, 0)
            
            # 风险偏好与产品风险越接近，分数越高
            # 重要：这里可以根据具体业务需求调整计算公式
            level_diff = abs(customer_risk_level / 4 - product_risk_level / 2)  # 归一化差异
            match_score = (1 - level_diff) * weight
        
        return is_match, match_score
        
    def check_investment_history(self, customer_id, product_id):
        """检查客户的历史投资记录"""
        # TODO: 实现历史投资记录检查逻辑
        pass
        
    def calculate_investment_capacity(self, customer_info):
        """计算客户的投资能力
        
        Args:
            customer_info: 客户信息字典
        
        Returns:
            dict: 包含最小、最大、建议投资金额的字典
        """
        # 获取客户类型
        customer_type = customer_info.get('customer_type', 'personal')
        is_vip = customer_info.get('is_vip', False)
        
        # 获取客户资产情况
        # 假设客户信息中包含以下字段，实际中可能需要从多个源获取或计算
        total_assets = customer_info.get('total_assets', 0)  # 总资产
        savingmount = customer_info.get('savingmount', 0)  # 存款金额
        wealthamount = customer_info.get('wealthamount', 0)  # 当前理财金额
        loanamount = customer_info.get('loanamount', 0)  # 贷款金额
        monthly_income = customer_info.get('monthly_income', 0)  # 月收入
        
        # 如果总资产为0，尝试计算
        if total_assets == 0:
            total_assets = savingmount + wealthamount
        
        # 如果仍为0，使用月收入估算
        if total_assets == 0 and monthly_income > 0:
            total_assets = monthly_income * 12
        
        # 从配置中获取购买金额配置
        amount_config = self.config.get('amount_config', {})
        vip_multiplier = amount_config.get('vip_multiplier', 1.5)
        
        # 获取特定客户类型的金额配置
        type_config = amount_config.get(customer_type, {})
        min_amount = type_config.get('min', 10000)
        max_amount = type_config.get('max', 100000)
        mean_amount = type_config.get('mean', 50000)
        
        # 根据客户资产调整投资能力
        if total_assets > 0:
            # 计算最小、最大投资金额
            # 最小金额不低于配置的最小值
            actual_min = max(min_amount, total_assets * 0.05)
            # 最大金额不超过资产的70%，且不超过配置的最大值
            actual_max = min(max_amount, total_assets * 0.7)
            # 建议金额为最小和最大的中间值
            suggested = (actual_min + actual_max) / 2
        else:
            # 没有资产信息时使用配置值
            actual_min = min_amount
            actual_max = max_amount
            suggested = mean_amount
        
        # VIP客户金额将提升
        if is_vip:
            actual_max *= vip_multiplier
            suggested *= vip_multiplier
        
        return {
            'min_amount': actual_min,
            'max_amount': actual_max,
            'suggested_amount': suggested
        }
        
    def filter_by_min_investment(self, products, customer_capacity):
        """根据最低投资额过滤产品
        
        Args:
            products: 产品列表
            customer_capacity: 客户投资能力字典
        
        Returns:
            list: 过滤后的产品列表
        """
        # 获取客户购买能力
        min_customer_amount = customer_capacity.get('min_amount', 0)
        max_customer_amount = customer_capacity.get('max_amount', float('inf'))
        
        # 过滤产品
        filtered_products = []
        for product in products:
            min_investment = product.get('minimuminvestment', 0)
            
            # 如果产品最低投资额小于等于客户最大能力且大于等于客户最小能力，则保留
            if min_investment <= max_customer_amount and min_investment >= min_customer_amount:
                filtered_products.append(product)
        
        return filtered_products
        
    def score_product_match(self, customer_info, product_info):
        """对产品匹配度进行评分"""
        # TODO: 实现产品匹配度评分逻辑
        pass
        
    def get_recommended_products(self, customer_info, count=3):
        """获取推荐产品列表"""
        # TODO: 实现推荐产品获取逻辑
        pass
        
    def check_product_purchase_constraints(self, customer_info, product_info):
        """检查产品购买约束条件"""
        # TODO: 实现产品购买约束检查逻辑
        pass
