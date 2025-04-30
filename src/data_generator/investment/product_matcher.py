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
        
    def find_matching_products(self, customer_info, exclude_products=None, limit=10):
        """
        查找匹配客户风险偏好的产品
        
        Args:
            customer_info (dict): 客户信息，包含风险偏好等级、财务状况等
            exclude_products (list): 需要排除的产品ID列表，可选
            limit (int): 返回结果数量限制，默认10个
            
        Returns:
            list: 匹配的产品列表，按匹配度降序排序
        """
        # 如果风险映射未初始化，先初始化
        if not self.risk_mapping:
            self.initialize_risk_mapping()
        
        # 获取客户风险等级（从risk_level字段）
        customer_risk = customer_info.get('risk_level', 'R3')  # 默认为中等风险(R3)
        
        # 获取客户投资能力
        investment_capacity = self.calculate_investment_capacity(customer_info)
        min_investment_amount = investment_capacity.get('min_amount', 0)
        max_investment_amount = investment_capacity.get('max_amount', float('inf'))
        
        # 构建查询产品的SQL语句
        sql = """
        SELECT * FROM cdp_product_archive 
        WHERE marketing_status = '在售' 
        AND minimum_investment <= %s
        """
        
        params = [max_investment_amount]
        
        # 如果有需要排除的产品，添加到查询条件
        if exclude_products and len(exclude_products) > 0:
            placeholders = ', '.join(['%s'] * len(exclude_products))
            sql += f" AND base_id NOT IN ({placeholders})"
            params.extend(exclude_products)
        
        # 根据客户风险等级筛选产品
        if customer_risk:
            # 根据客户风险等级获取可接受的产品风险等级
            acceptable_risks = self._get_acceptable_risk_levels(customer_risk)
            if acceptable_risks and len(acceptable_risks) > 0:
                risk_placeholders = ', '.join(['%s'] * len(acceptable_risks))
                sql += f" AND risk_level IN ({risk_placeholders})"
                params.extend(acceptable_risks)
        
        # 添加排序和限制条件
        sql += " ORDER BY expected_yield DESC LIMIT %s"
        params.append(limit * 3)  # 获取更多产品，然后进行更精细的排序
        
        # 执行数据库查询
        try:
            self.logger.debug(f"Executing SQL: {sql} with params: {params}")
            results = self.db_manager.execute_query(sql, params)
            self.logger.info(f"Found {len(results)} available products from database")
        except Exception as e:
            self.logger.error(f"Error querying products from database: {str(e)}")
            results = []
        
        # 匹配产品并计算匹配分数
        matched_products = []
        for product in results:
            # 检查最低投资额是否符合客户能力
            product_min_investment = product.get('minimum_investment', 0)
            if product_min_investment < min_investment_amount:
                continue
            
            # 获取产品风险等级
            product_risk = product.get('risk_level', 'R1')
            
            # 将产品风险等级映射到low/medium/high
            if product_risk in ['R1', 'R2']:
                product_risk_category = 'low'
            elif product_risk == 'R3':
                product_risk_category = 'medium'
            else:  # R4, R5
                product_risk_category = 'high'
            
            # 检查风险等级是否匹配
            is_matched, match_score = self.match_risk_level(customer_risk, product_risk_category)
            
            if is_matched:
                # 检查产品购买约束条件
                constraints_met, constraints_score = self.check_product_purchase_constraints(
                    customer_info, product)
                
                # 如果满足约束条件，计算最终匹配分数
                if constraints_met:
                    # 检查客户历史投资记录
                    history_score = self.check_investment_history(
                        customer_info.get('base_id'), product.get('base_id'))
                    
                    # 计算投资期限适配分数
                    term_score = self._calculate_term_score(customer_info, product)
                    
                    # 计算综合匹配分数，注意权重调整
                    final_score = (match_score * 0.5 + 
                                constraints_score * 0.2 + 
                                history_score * 0.15 + 
                                term_score * 0.15)
                    
                    # 添加到匹配产品列表
                    matched_products.append({
                        'product': product,
                        'match_score': final_score,
                        'risk_match': match_score,
                        'constraints_match': constraints_score,
                        'history_match': history_score,
                        'term_match': term_score
                    })
        
        # 按匹配分数降序排序
        matched_products.sort(key=lambda x: x['match_score'], reverse=True)
        
        # 记录匹配结果
        self.logger.info(f"Found {len(matched_products)} matching products for customer {customer_info.get('base_id')}")
        
        # 限制返回数量
        return matched_products[:limit]

    def _get_acceptable_risk_levels(self, customer_risk):
        """
        根据客户风险等级获取可接受的产品风险等级列表
        
        Args:
            customer_risk (str): 客户风险等级
        
        Returns:
            list: 可接受的产品风险等级列表
        """
        # 默认映射关系，可根据业务规则调整
        risk_mapping = {
            'R1': ['R1'],
            'R2': ['R1', 'R2'],
            'R3': ['R1', 'R2', 'R3'],
            'R4': ['R1', 'R2', 'R3', 'R4'],
            'R5': ['R1', 'R2', 'R3', 'R4', 'R5']
        }
        
        return risk_mapping.get(customer_risk, ['R1', 'R2', 'R3'])  # 默认返回中低风险产品

    def _calculate_term_score(self, customer_info, product):
        """
        计算投资期限适配分数
        
        Args:
            customer_info (dict): 客户信息
            product (dict): 产品信息
        
        Returns:
            float: 期限适配分数 (0-1)
        """
        # 获取产品期限(月)
        product_term = product.get('investment_period', 0)
        
        # 根据客户类型判断适合的期限
        customer_type = customer_info.get('customer_type', 'personal')
        is_vip = customer_info.get('is_vip', False)
        
        # 根据客户特征推断适合的期限范围
        if customer_type == 'corporate':
            # 企业客户偏好中短期投资
            if product_term <= 3:
                score = 0.9  # 短期(3个月以下)
            elif product_term <= 6:
                score = 1.0  # 中短期(3-6个月)
            elif product_term <= 12:
                score = 0.8  # 中期(6-12个月)
            else:
                score = 0.4  # 长期(12个月以上)
        else:  # 个人客户
            if is_vip:
                # VIP个人客户通常更偏好中长期投资产品
                if product_term <= 3:
                    score = 0.7  # 短期
                elif product_term <= 12:
                    score = 0.9  # 中期
                else:
                    score = 1.0  # 长期
            else:
                # 普通个人客户偏好短中期投资
                if product_term <= 3:
                    score = 1.0  # 短期
                elif product_term <= 12:
                    score = 0.8  # 中期
                else:
                    score = 0.5  # 长期
        
        return score
        
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
        """
        检查客户的历史投资记录，评估产品与客户投资习惯的匹配度
        
        Args:
            customer_id (str): 客户ID
            product_id (str): 产品ID
            
        Returns:
            float: 历史匹配分数 (0-1)，越高表示越匹配
        """
        # 如果没有提供有效的客户ID或产品ID，返回默认分数
        if not customer_id or not product_id:
            return 0.5
        
        try:
            # 查询客户的历史投资记录
            query = """
            SELECT io.*, p.product_type, p.risk_level 
            FROM cdp_investment_order io
            JOIN cdp_product_archive p ON io.product_id = p.base_id
            WHERE io.base_id = %s
            ORDER BY io.detail_time DESC
            LIMIT 10
            """
            
            investment_history = self.db_manager.execute_query(query, (customer_id,))
            
            # 如果没有投资历史，返回中等分数
            if not investment_history:
                return 0.5
            
            # 获取目标产品信息
            product_query = "SELECT * FROM cdp_product_archive WHERE base_id = %s"
            product_results = self.db_manager.execute_query(product_query, (product_id,))
            
            if not product_results:
                return 0.5
                
            target_product = product_results[0]
            target_product_type = target_product.get('product_type')
            target_risk_level = target_product.get('risk_level')
            
            # 计算各种匹配因素的得分
            type_match_score = 0.0
            risk_match_score = 0.0
            repeat_purchase_score = 0.0
            success_rate_score = 0.0
            
            # 相同类型产品计数
            same_type_count = 0
            same_risk_count = 0
            same_product_count = 0
            
            # 统计成功交易的比例
            success_count = 0
            
            # 分析投资历史
            for record in investment_history:
                # 检查产品类型匹配
                if record.get('product_type') == target_product_type:
                    same_type_count += 1
                    
                # 检查风险等级匹配
                if record.get('risk_level') == target_risk_level:
                    same_risk_count += 1
                    
                # 检查是否曾经购买过相同产品
                if record.get('product_id') == product_id:
                    same_product_count += 1
                    
                # 检查交易是否成功
                if record.get('status') in ['成功', '持有', '部分卖出', '完全赎回']:
                    success_count += 1
            
            # 计算产品类型匹配分数
            type_match_score = same_type_count / len(investment_history)
            
            # 计算风险等级匹配分数
            risk_match_score = same_risk_count / len(investment_history)
            
            # 计算重复购买分数
            repeat_purchase_score = 1.0 if same_product_count > 0 else 0.0
            
            # 计算交易成功率分数
            success_rate_score = success_count / len(investment_history)
            
            # 合并各因素得分，可以根据业务需要调整权重
            final_score = (
                type_match_score * 0.4 +
                risk_match_score * 0.3 +
                repeat_purchase_score * 0.2 +
                success_rate_score * 0.1
            )
            
            # 增加一些随机性，避免完全相同的推荐结果
            import random
            random_factor = random.uniform(0.95, 1.05)
            adjusted_score = final_score * random_factor
            
            # 确保分数在0-1范围内
            return max(0.0, min(1.0, adjusted_score))
            
        except Exception as e:
            self.logger.error(f"检查投资历史时出错: {str(e)}")
            # 出错时返回中等分数
            return 0.5
        
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
        
    def check_product_purchase_constraints(self, customer_info, product):
        """
        检查产品购买约束条件
        
        Args:
            customer_info (dict): 客户信息
            product (dict): 产品信息
            
        Returns:
            tuple: (是否满足约束条件, 约束条件匹配分数0-1)
        """
        # 获取产品和客户的基本信息
        product_id = product.get('base_id')
        customer_id = customer_info.get('base_id')
        
        # 获取约束检查所需的客户属性
        customer_type = customer_info.get('customer_type', 'personal')  # 个人/企业
        is_vip = customer_info.get('is_vip', False)  # VIP状态
        customer_risk_level = customer_info.get('risk_level', 'R3')  # 风险等级
        
        # 获取产品的约束条件
        min_investment = product.get('minimum_investment', 0)  # 最低投资金额
        product_risk_level = product.get('risk_level', 'R1')  # 产品风险等级
        product_type = product.get('product_type', '')  # 产品类型
        
        # 定义约束条件检查项及其权重
        constraints = []
        
        # 1. 风险等级约束
        if not self._check_risk_constraint(customer_risk_level, product_risk_level):
            return False, 0.0  # 风险等级不匹配，直接返回不满足
        constraints.append(('risk_level', 1.0))  # 风险约束满足
        
        # 2. 投资金额约束
        investment_capacity = self.calculate_investment_capacity(customer_info)
        min_amount = investment_capacity.get('min_amount', 0)
        max_amount = investment_capacity.get('max_amount', float('inf'))
        
        if min_investment > max_amount:
            return False, 0.0  # 最低投资金额超过客户投资能力
        
        # 计算金额适配度分数
        if min_investment <= min_amount:
            amount_match_score = 1.0  # 完美匹配
        else:
            # 金额接近度
            amount_match_score = 1.0 - ((min_investment - min_amount) / (max_amount - min_amount + 1))
        constraints.append(('investment_amount', amount_match_score))
        
        # 3. 客户类型约束
        customer_type_match = True
        customer_type_score = 1.0
        
        # 检查产品是否仅对某类客户开放
        # 假设产品表中有customer_type_limit字段表示客户类型限制
        customer_type_limit = product.get('customer_type_limit', '')
        
        if customer_type_limit and customer_type_limit != customer_type:
            customer_type_match = False
            customer_type_score = 0.0
        constraints.append(('customer_type', customer_type_score))
        
        if not customer_type_match:
            return False, 0.0  # 客户类型不满足要求
        
        # 4. VIP专属产品约束
        is_vip_only = product.get('is_vip_only', False)
        if is_vip_only and not is_vip:
            return False, 0.0  # 非VIP客户不能购买VIP专属产品
        constraints.append(('vip_status', 1.0))
        
        # 5. 渠道约束（可选）
        # 如果产品有渠道限制，检查客户是否可以通过该渠道购买
        
        # 6. 季节性约束（可选）
        # 如果产品有季节性销售限制，检查当前是否在销售期内
        
        # 7. 检查客户是否已达到该产品的购买上限
        purchase_limit_met = self._check_purchase_limit(customer_id, product_id)
        if purchase_limit_met:
            return False, 0.0  # 已达购买上限
        constraints.append(('purchase_limit', 1.0))
        
        # 8. 地区约束检查
        location_match, location_score = self._check_location_constraint(customer_info, product)
        constraints.append(('location', location_score))
        if not location_match:
            return False, 0.0  # 地区不匹配
        
        # 9. 客户财富阶段约束
        wealth_phase_match, wealth_phase_score = self._check_wealth_phase_constraint(customer_info, product)
        constraints.append(('wealth_phase', wealth_phase_score))
        if not wealth_phase_match:
            return False, 0.0  # 财富阶段不匹配
        
        # 计算约束条件的总体匹配分数
        total_weight = sum(weight for _, weight in constraints)
        total_score = sum(score * weight for (_, score), weight in zip(constraints, [w for _, w in constraints]))
        
        # 避免除以零
        if total_weight > 0:
            final_score = total_score / total_weight
        else:
            final_score = 0.0
        
        return True, final_score

    def _check_risk_constraint(self, customer_risk_level, product_risk_level):
        """
        检查风险等级约束
        
        Args:
            customer_risk_level (str): 客户风险等级
            product_risk_level (str): 产品风险等级
            
        Returns:
            bool: 是否满足风险约束
        """
        # 定义风险等级映射关系
        risk_mapping = {
            'R1': ['R1'],
            'R2': ['R1', 'R2'],
            'R3': ['R1', 'R2', 'R3'],
            'R4': ['R1', 'R2', 'R3', 'R4'],
            'R5': ['R1', 'R2', 'R3', 'R4', 'R5']
        }
        
        # 获取客户可接受的风险等级
        acceptable_risks = risk_mapping.get(customer_risk_level, ['R1'])
        
        # 检查产品风险是否在客户接受范围内
        return product_risk_level in acceptable_risks

    def _check_purchase_limit(self, customer_id, product_id):
        """
        检查客户是否已达到产品购买上限
        
        Args:
            customer_id (str): 客户ID
            product_id (str): 产品ID
            
        Returns:
            bool: 是否已达到购买上限
        """
        try:
            # 查询客户已购买的该产品数量
            query = """
            SELECT COUNT(*) as purchase_count 
            FROM cdp_investment_order 
            WHERE base_id = %s AND product_id = %s
            AND wealth_status IN ('持有', '部分卖出')
            """
            
            result = self.db_manager.execute_query(query, (customer_id, product_id))
            
            if result and result[0].get('purchase_count', 0) > 0:
                # 查询产品购买上限
                product_query = """
                SELECT purchase_limit 
                FROM cdp_product_archive 
                WHERE base_id = %s
                """
                
                product_result = self.db_manager.execute_query(product_query, (product_id,))
                
                if product_result and 'purchase_limit' in product_result[0]:
                    purchase_limit = product_result[0]['purchase_limit']
                    
                    # 如果产品没有设置购买上限或购买次数未达上限
                    if purchase_limit is None or result[0]['purchase_count'] < purchase_limit:
                        return False
                    return True
            
            return False  # 未达到购买上限
            
        except Exception as e:
            self.logger.error(f"检查购买上限时出错: {str(e)}")
            return False  # 出错时假设未达上限

    def _check_location_constraint(self, customer_info, product):
        """
        检查地区约束
        
        Args:
            customer_info (dict): 客户信息
            product (dict): 产品信息
            
        Returns:
            tuple: (是否满足地区约束, 地区匹配分数0-1)
        """
        # 假设产品有销售区域限制字段
        sale_regions = product.get('sale_regions', '')
        
        # 如果没有区域限制，返回匹配
        if not sale_regions:
            return True, 1.0
        
        # 获取客户所在区域
        customer_province = customer_info.get('province', '')
        customer_city = customer_info.get('city', '')
        
        # 如果销售区域字段是JSON格式的字符串，需要解析
        try:
            import json
            if isinstance(sale_regions, str):
                sale_regions = json.loads(sale_regions)
        except:
            # 解析失败时假设没有区域限制
            return True, 1.0
        
        # 检查客户所在区域是否在销售区域内
        if isinstance(sale_regions, list):
            if customer_province in sale_regions or customer_city in sale_regions:
                return True, 1.0
            return False, 0.0
        
        # 假设sale_regions是字典形式，包含provinces和cities两个列表
        if isinstance(sale_regions, dict):
            provinces = sale_regions.get('provinces', [])
            cities = sale_regions.get('cities', [])
            
            if customer_province in provinces or customer_city in cities:
                return True, 1.0
            
            # 部分匹配情况，比如客户所在城市不在列表但省份在列表
            if customer_province in provinces:
                return True, 0.8
        
        return False, 0.0

    def _check_wealth_phase_constraint(self, customer_info, product):
        """
        检查客户财富阶段约束
        
        Args:
            customer_info (dict): 客户信息
            product (dict): 产品信息
            
        Returns:
            tuple: (是否满足财富阶段约束, 财富阶段匹配分数0-1)
        """
        # 获取客户财富阶段
        wealth_phase = customer_info.get('wealth_customer_phase', '')
        
        # 假设产品有目标财富阶段字段
        target_phases = product.get('target_wealth_phases', '')
        
        # 如果产品没有设置目标阶段，则认为适合所有阶段
        if not target_phases:
            return True, 1.0
        
        # 将目标阶段转为列表（如果是字符串）
        if isinstance(target_phases, str):
            try:
                import json
                target_phases = json.loads(target_phases)
            except:
                target_phases = target_phases.split(',')
        
        # 检查客户阶段是否在目标阶段内
        if not wealth_phase or not isinstance(target_phases, list):
            return True, 0.5  # 信息不完整时返回中等匹配度
        
        if wealth_phase in target_phases:
            return True, 1.0
        
        # 如果是"老客"，对大多数产品都适用
        if wealth_phase == "老客":
            return True, 0.8
        
        # 如果是"首投"，适合低风险产品
        if wealth_phase == "首投" and product.get('risk_level') in ['R1', 'R2']:
            return True, 0.7
        
        # 其他情况不匹配
        return False, 0.0
    
    def score_product_match(self, customer_info, product_info):
        """
        对产品匹配度进行评分
        
        Args:
            customer_info (dict): 客户信息
            product_info (dict): 产品信息
            
        Returns:
            float: 匹配分数 (0-1)，分数越高表示匹配度越高
        """
        # 获取客户和产品ID（用于日志和调试）
        customer_id = customer_info.get('base_id', 'unknown')
        product_id = product_info.get('base_id', 'unknown')
        
        # 预先检查基本条件
        # 1. 风险等级匹配检查
        customer_risk = customer_info.get('risk_level', 'R3')
        product_risk = product_info.get('risk_level', 'R1')
        
        # 将产品风险等级转换为类别
        if product_risk in ['R1', 'R2']:
            product_risk_category = 'low'
        elif product_risk == 'R3':
            product_risk_category = 'medium'
        else:  # R4, R5
            product_risk_category = 'high'
        
        # 检查风险是否匹配
        is_risk_matched, risk_match_score = self.match_risk_level(customer_risk, product_risk_category)
        
        # 如果风险不匹配，直接返回0分
        if not is_risk_matched:
            self.logger.debug(f"产品 {product_id} 风险等级不匹配客户 {customer_id} 的风险偏好")
            return 0.0
        
        # 2. 检查约束条件
        constraints_met, constraints_score = self.check_product_purchase_constraints(
            customer_info, product_info)
        
        # 如果不满足约束条件，直接返回0分
        if not constraints_met:
            self.logger.debug(f"产品 {product_id} 不满足客户 {customer_id} 的购买约束条件")
            return 0.0
        
        # 3. 检查历史投资行为匹配度
        history_score = self.check_investment_history(customer_id, product_id)
        
        # 4. 计算产品特性匹配分数
        feature_scores = self._calculate_feature_match_scores(customer_info, product_info)
        
        # 5. 计算市场行情匹配分数（可选）
        market_score = self._calculate_market_match_score(customer_info, product_info)
        
        # 6. 计算时机匹配分数（如季节性、活动期等）
        timing_score = self._calculate_timing_match_score(customer_info, product_info)
        
        # 综合计算最终分数，各因素权重可根据业务需求调整
        weights = {
            'risk': 0.25,             # 风险匹配
            'constraints': 0.15,      # 约束条件
            'history': 0.20,          # 历史行为
            'features': 0.25,         # 产品特性
            'market': 0.10,           # 市场行情
            'timing': 0.05            # 时机因素
        }
        
        # 计算加权平均分数
        final_score = (
            risk_match_score * weights['risk'] +
            constraints_score * weights['constraints'] +
            history_score * weights['history'] +
            feature_scores['total'] * weights['features'] +
            market_score * weights['market'] +
            timing_score * weights['timing']
        )
        
        # 记录匹配结果
        self.logger.debug(
            f"产品 {product_id} 与客户 {customer_id} 的匹配分数: {final_score:.4f} "
            f"(风险: {risk_match_score:.2f}, 约束: {constraints_score:.2f}, "
            f"历史: {history_score:.2f}, 特性: {feature_scores['total']:.2f}, "
            f"市场: {market_score:.2f}, 时机: {timing_score:.2f})"
        )
        
        return final_score

    def _calculate_feature_match_scores(self, customer_info, product_info):
        """
        计算产品特性匹配分数
        
        Args:
            customer_info (dict): 客户信息
            product_info (dict): 产品信息
            
        Returns:
            dict: 包含各特性分数和总分的字典
        """
        # 初始化特性分数
        feature_scores = {
            'term': 0.0,              # 期限匹配
            'yield': 0.0,             # 收益率偏好
            'product_type': 0.0,      # 产品类型偏好
            'redemption_way': 0.0,    # 赎回方式偏好
            'bank': 0.0,              # 银行偏好
            'total': 0.0              # 总分
        }
        
        # 1. 期限匹配度
        term_score = self._calculate_term_preference_match(customer_info, product_info)
        feature_scores['term'] = term_score
        
        # 2. 收益率偏好匹配
        yield_score = self._calculate_yield_preference_match(customer_info, product_info)
        feature_scores['yield'] = yield_score
        
        # 3. 产品类型偏好匹配
        product_type_score = self._calculate_product_type_preference_match(customer_info, product_info)
        feature_scores['product_type'] = product_type_score
        
        # 4. 赎回方式偏好匹配
        redemption_score = self._calculate_redemption_preference_match(customer_info, product_info)
        feature_scores['redemption_way'] = redemption_score
        
        # 5. 银行偏好匹配
        bank_score = self._calculate_bank_preference_match(customer_info, product_info)
        feature_scores['bank'] = bank_score
        
        # 计算总分（各特性权重可根据业务需求调整）
        weights = {
            'term': 0.25,
            'yield': 0.30,
            'product_type': 0.25,
            'redemption_way': 0.15,
            'bank': 0.05
        }
        
        total_score = sum(score * weights[key] for key, score in feature_scores.items() if key != 'total')
        feature_scores['total'] = total_score
        
        return feature_scores

    def _calculate_term_preference_match(self, customer_info, product_info):
        """计算期限偏好匹配分数"""
        # 获取产品期限(月)
        product_term = product_info.get('investment_period', 0)
        
        # 获取客户信息
        customer_type = customer_info.get('customer_type', 'personal')
        is_vip = customer_info.get('is_vip', False)
        
        # 根据客户类型设置期限偏好
        term_preference = {}
        
        if customer_type == 'corporate':
            # 企业客户通常偏好中短期
            term_preference = {
                'short': (0, 3, 0.9),     # 0-3个月，偏好度0.9
                'medium': (4, 12, 1.0),   # 4-12个月，偏好度1.0
                'long': (13, 999, 0.5)    # 13个月以上，偏好度0.5
            }
        elif is_vip:
            # VIP个人客户通常偏好中长期
            term_preference = {
                'short': (0, 3, 0.7),
                'medium': (4, 12, 0.9),
                'long': (13, 999, 1.0)
            }
        else:
            # 普通个人客户通常偏好短期
            term_preference = {
                'short': (0, 3, 1.0),
                'medium': (4, 12, 0.8),
                'long': (13, 999, 0.6)
            }
        
        # 根据产品期限匹配相应偏好
        for _, (min_term, max_term, score) in term_preference.items():
            if min_term <= product_term <= max_term:
                return score
        
        # 默认返回中等匹配度
        return 0.5

    def _calculate_market_match_score(self, customer_info, product_info):
        """
        根据当前市场情况计算匹配分数
        
        实际实现可能需要考虑市场指标和趋势数据
        这里提供简化版本
        """
        # 简化实现，实际应考虑市场数据
        return 0.8

    def _calculate_timing_match_score(self, customer_info, product_info):
        """
        根据时机因素计算匹配分数
        
        考虑季节性、活动期等因素
        """
        # 简化实现，实际应考虑时间因素
        return 0.7

    def _calculate_yield_preference_match(self, customer_info, product_info):
        """计算收益率偏好匹配分数"""
        # 获取产品预期收益率
        expected_yield = product_info.get('expected_yield', 0)
        
        # 获取客户风险等级（用于推断收益率偏好）
        risk_level = customer_info.get('risk_level', 'R3')
        
        # 根据风险等级设置收益率偏好范围
        yield_preferences = {
            'R1': (0.01, 0.03, 0.04),     # (min_preferred, ideal, max_acceptable)
            'R2': (0.02, 0.04, 0.05),
            'R3': (0.03, 0.05, 0.07),
            'R4': (0.04, 0.07, 0.10),
            'R5': (0.05, 0.10, 0.15)
        }
        
        # 获取客户的收益率偏好
        min_yield, ideal_yield, max_yield = yield_preferences.get(
            risk_level, (0.02, 0.04, 0.06))
        
        # 计算匹配分数
        if expected_yield < min_yield:
            # 收益率过低
            return max(0, 0.5 - (min_yield - expected_yield) * 10)
        elif min_yield <= expected_yield <= ideal_yield:
            # 收益率在理想范围内，线性增长
            return 0.8 + 0.2 * (expected_yield - min_yield) / (ideal_yield - min_yield)
        elif ideal_yield < expected_yield <= max_yield:
            # 收益率在可接受范围内，线性下降
            return 1.0 - 0.2 * (expected_yield - ideal_yield) / (max_yield - ideal_yield)
        else:
            # 收益率过高
            return max(0, 0.8 - (expected_yield - max_yield) * 5)

    def _calculate_product_type_preference_match(self, customer_info, product_info):
        """计算产品类型偏好匹配分数"""
        # 获取产品类型
        product_type = product_info.get('product_type', '')
        
        # 查询客户历史购买的产品类型偏好
        try:
            # 获取客户ID
            customer_id = customer_info.get('base_id')
            
            if not customer_id:
                return 0.5  # 无法确定偏好时返回中等分数
            
            query = """
            SELECT p.product_type, COUNT(*) as purchase_count
            FROM cdp_investment_order io
            JOIN cdp_product_archive p ON io.product_id = p.base_id
            WHERE io.base_id = %s
            GROUP BY p.product_type
            ORDER BY purchase_count DESC
            """
            
            results = self.db_manager.execute_query(query, (customer_id,))
            
            if not results:
                # 无购买历史，根据风险等级推断偏好
                risk_level = customer_info.get('risk_level', 'R3')
                
                # 风险等级与产品类型偏好的默认映射
                default_preferences = {
                    'R1': {'货币型基金': 0.9, '债券型基金': 0.7, '其他': 0.5},
                    'R2': {'债券型基金': 0.9, '货币型基金': 0.8, '其他': 0.6},
                    'R3': {'混合型基金': 0.9, '债券型基金': 0.8, '指数型基金': 0.7},
                    'R4': {'指数型基金': 0.9, '混合型基金': 0.8, '股票型基金': 0.7},
                    'R5': {'股票型基金': 0.9, '指数型基金': 0.8, '混合型基金': 0.7}
                }
                
                preferences = default_preferences.get(risk_level, {})
                return preferences.get(product_type, 0.5)
            
            # 计算各产品类型的购买比例
            total_purchases = sum(result['purchase_count'] for result in results)
            type_preferences = {}
            
            for result in results:
                type_name = result['product_type']
                purchase_ratio = result['purchase_count'] / total_purchases
                
                # 设置偏好分数
                # 购买比例越高，偏好分数越高
                type_preferences[type_name] = min(1.0, 0.6 + purchase_ratio * 2)
            
            # 返回匹配分数，如果没有该类型的历史则返回中等分数
            return type_preferences.get(product_type, 0.5)
            
        except Exception as e:
            self.logger.error(f"计算产品类型偏好时出错: {str(e)}")
            return 0.5

    def _calculate_redemption_preference_match(self, customer_info, product_info):
        """计算赎回方式偏好匹配分数"""
        # 获取产品赎回方式
        redemption_way = product_info.get('redemption_way', '')
        
        # 根据客户类型和历史赎回行为判断偏好
        customer_type = customer_info.get('customer_type', 'personal')
        is_vip = customer_info.get('is_vip', False)
        
        # 设置默认偏好
        preferences = {}
        
        if customer_type == 'corporate':
            # 企业客户通常偏好灵活赎回
            preferences = {
                '随时赎回': 0.9,
                '固定赎回': 0.6
            }
        elif is_vip:
            # VIP客户通常更能接受固定赎回（长期投资能力更强）
            preferences = {
                '随时赎回': 0.8,
                '固定赎回': 0.8
            }
        else:
            # 普通个人客户偏好随时赎回
            preferences = {
                '随时赎回': 0.9,
                '固定赎回': 0.5
            }
        
        # 返回匹配分数
        return preferences.get(redemption_way, 0.5)

    def _calculate_bank_preference_match(self, customer_info, product_info):
        """计算银行偏好匹配分数"""
        # 获取产品发行银行
        bank_name = product_info.get('bank_name', '')
        
        # 获取客户ID
        customer_id = customer_info.get('base_id')
        
        if not customer_id or not bank_name:
            return 0.5  # 信息不完整时返回中等分数
        
        try:
            # 查询客户在各银行的投资情况
            query = """
            SELECT p.bank_name, COUNT(*) as purchase_count
            FROM cdp_investment_order io
            JOIN cdp_product_archive p ON io.product_id = p.base_id
            WHERE io.base_id = %s
            GROUP BY p.bank_name
            ORDER BY purchase_count DESC
            """
            
            results = self.db_manager.execute_query(query, (customer_id,))
            
            if not results:
                return 0.5  # 无购买历史时返回中等分数
            
            # 计算各银行的购买比例
            total_purchases = sum(result['purchase_count'] for result in results)
            bank_preferences = {}
            
            for result in results:
                bank = result['bank_name']
                purchase_ratio = result['purchase_count'] / total_purchases
                
                # 设置偏好分数
                bank_preferences[bank] = min(1.0, 0.7 + purchase_ratio * 1.5)
            
            # 返回匹配分数
            return bank_preferences.get(bank_name, 0.5)
            
        except Exception as e:
            self.logger.error(f"计算银行偏好时出错: {str(e)}")
            return 0.5
        
    def _calculate_risk_match_score(self, customer_risk_level, product_risk_level):
        """
        计算客户风险等级与产品风险等级的匹配分数
        
        Args:
            customer_risk_level (str): 客户风险等级 (R1-R5)
            product_risk_level (str): 产品风险等级 (R1-R5)
            
        Returns:
            float: 匹配分数 (0-1)，值越高表示匹配度越高
        """
        # 风险等级数值映射
        risk_values = {'R1': 1, 'R2': 2, 'R3': 3, 'R4': 4, 'R5': 5}
        
        # 获取风险等级数值
        customer_value = risk_values.get(customer_risk_level, 3)  # 默认R3
        product_value = risk_values.get(product_risk_level, 3)    # 默认R3
        
        # 风险容忍度: 客户通常可以接受等于或低于自身风险等级的产品
        # 保守客户(R1-R2)可能更倾向于选择低风险产品
        # 平衡型客户(R3)可以接受相近风险等级的产品
        # 进取型客户(R4-R5)可能更倾向于高风险高收益产品
        
        # 计算风险差异
        risk_diff = abs(customer_value - product_value)
        
        # 基础匹配分数
        if risk_diff == 0:
            # 风险等级完全匹配
            base_score = 1.0
        elif risk_diff == 1:
            # 风险等级差一级
            base_score = 0.8
        elif risk_diff == 2:
            # 风险等级差两级
            base_score = 0.5
        else:
            # 风险等级差距较大
            base_score = 0.3
        
        # 调整因子: 考虑客户风险偏好特性
        adjustment = 0.0
        
        # 保守型客户(R1-R2)更偏好低风险产品
        if customer_value <= 2 and product_value <= customer_value:
            adjustment = 0.1
            
        # 平衡型客户(R3)偏好匹配风险的产品
        elif customer_value == 3 and risk_diff <= 1:
            adjustment = 0.05
            
        # 进取型客户(R4-R5)更偏好较高风险产品
        elif customer_value >= 4 and product_value >= customer_value - 1:
            adjustment = 0.15
            
        # 保守客户一般不接受高风险产品
        if customer_value <= 2 and product_value >= 4:
            adjustment = -0.2
            
        # 进取型客户可能对低风险产品兴趣较低
        elif customer_value >= 4 and product_value <= 2:
            adjustment = -0.1
        
        # 计算最终分数并确保在0-1范围内
        final_score = max(0.0, min(1.0, base_score + adjustment))
        
        return final_score
    
    def calculate_investment_capacity(self, customer):
        """
        计算客户的投资能力
        
        考虑客户类型、收入水平、VIP状态、风险等级等因素
        
        Args:
            customer (dict): 客户信息
            
        Returns:
            dict: 包含最小金额、最大金额和建议金额的字典
        """
        # 获取客户基本信息
        customer_type = customer.get('customer_type', 'personal')
        is_vip = customer.get('is_vip', False)
        risk_level = customer.get('risk_level', 'R3')
        
        # 获取金额配置
        amount_config = self.config.get('amount_config', {})
        
        # 根据客户类型获取基础金额配置
        if customer_type == 'corporate':
            # 企业客户
            base_config = amount_config.get('corporate', {
                'min': 100000,   # 默认最低10万
                'max': 2000000,  # 默认最高200万
                'mean': 500000,  # 默认平均50万
                'std_dev': 300000  # 默认标准差30万
            })
        else:
            # 个人客户
            base_config = amount_config.get('personal', {
                'min': 10000,    # 默认最低1万
                'max': 200000,   # 默认最高20万
                'mean': 50000,   # 默认平均5万
                'std_dev': 30000  # 默认标准差3万
            })
        
        # 获取基础金额范围
        min_amount = base_config.get('min', 10000)
        max_amount = base_config.get('max', 200000)
        mean_amount = base_config.get('mean', 50000)
        std_dev = base_config.get('std_dev', 30000)
        
        # VIP客户调整 - 增加投资金额上限和平均值
        if is_vip:
            vip_multiplier = amount_config.get('vip_multiplier', 1.5)
            max_amount = max_amount * vip_multiplier
            mean_amount = mean_amount * vip_multiplier
        
        # 风险等级调整
        # 高风险等级的客户可能有更高的投资能力
        risk_multipliers = {
            'R1': 0.8,  # 保守型客户可能投资金额相对较小
            'R2': 0.9,
            'R3': 1.0,  # 标准基准
            'R4': 1.1,
            'R5': 1.3   # 激进型客户可能投资金额相对较大
        }
        
        risk_multiplier = risk_multipliers.get(risk_level, 1.0)
        max_amount = max_amount * risk_multiplier
        mean_amount = mean_amount * risk_multiplier
        
        # 收入水平调整 (如果有收入信息)
        income_category = customer.get('salarycategory', '')
        income_multipliers = {
            '1级': 0.7,   # 低收入
            '2级': 0.8,
            '3级': 0.9,
            '4级': 1.0,   # 中等收入
            '5级': 1.2,
            '6级': 1.4,
            '7级': 1.7,
            '8级': 2.0    # 高收入
        }
        
        income_multiplier = income_multipliers.get(income_category, 1.0)
        max_amount = max_amount * income_multiplier
        mean_amount = mean_amount * income_multiplier
        
        # 考虑历史购买行为 (如果可用)
        if 'wealthamount' in customer and customer['wealthamount']:
            historical_amount = float(customer['wealthamount'])
            if historical_amount > 0:
                # 历史购买金额对建议金额有一定影响
                mean_amount = (mean_amount + historical_amount) / 2
        
        # 确保最终金额在合理范围内
        min_amount = max(min_amount, base_config.get('min', 10000))
        max_amount = max(max_amount, min_amount * 1.5)
        suggested_amount = max(min_amount, min(max_amount, mean_amount))
        
        return {
            'min_amount': round(min_amount, 2),
            'max_amount': round(max_amount, 2),
            'suggested_amount': round(suggested_amount, 2)
        }
    
    def find_matching_products(self, customer, products=None, limit=10):
        """
        根据客户特征查找匹配的产品
        
        Args:
            customer (dict): 客户信息
            products (list, optional): 可选的产品列表，如不提供则从数据库查询
            limit (int): 最多返回的产品数量
            
        Returns:
            list: 匹配的产品列表，每项包含产品信息和匹配分数
        """
        try:
            # 获取客户风险等级
            customer_risk = customer.get('risk_level', 'R3')
            customer_type = customer.get('customer_type', 'personal')
            
            # 如果未提供产品列表，从数据库查询
            if products is None:
                products = self._get_available_products()
                
                # 如果查询失败或没有产品，返回空列表
                if not products:
                    self.logger.warning("没有可用的产品")
                    return []
            
            # 计算客户投资能力
            investment_capacity = self.calculate_investment_capacity(customer)
            min_investment = investment_capacity['min_amount']
            max_investment = investment_capacity['max_amount']
            
            # 筛选满足最低投资需求的产品
            eligible_products = []
            for product in products:
                # 检查最低投资要求
                product_min_investment = product.get('minimum_investment', 0)
                if product_min_investment > max_investment:
                    # 客户投资能力不足
                    continue
                
                # 风险等级匹配检查
                product_risk = product.get('risk_level', 'R1')
                risk_match_score = self._calculate_risk_match_score(customer_risk, product_risk)
                
                # 风险匹配分数太低的产品直接排除
                if risk_match_score < 0.3:
                    continue
                
                # 计算产品特征匹配分数
                feature_match_score = self._calculate_feature_match_score(customer, product)
                
                # 计算预期收益匹配分数
                return_match_score = self._calculate_return_match_score(customer, product)
                
                # 计算最终匹配分数 (加权平均)
                # 风险匹配占50%，特征匹配占30%，收益匹配占20%
                match_score = (
                    0.5 * risk_match_score + 
                    0.3 * feature_match_score + 
                    0.2 * return_match_score
                )
                
                # 添加到合格产品列表
                eligible_products.append({
                    'product': product,
                    'match_score': match_score,
                    'risk_match': risk_match_score,
                    'feature_match': feature_match_score,
                    'return_match': return_match_score
                })
            
            # 按匹配分数排序
            eligible_products.sort(key=lambda x: x['match_score'], reverse=True)
            
            # 返回指定数量的产品
            return eligible_products[:limit]
        
        except Exception as e:
            self.logger.error(f"查找匹配产品时出错: {str(e)}")
            return []


    def _calculate_feature_match_score(self, customer, product):
        """
        计算客户与产品特征的匹配程度
        
        考虑产品类型、期限、赎回方式等与客户偏好的匹配
        
        Args:
            customer (dict): 客户信息
            product (dict): 产品信息
            
        Returns:
            float: 匹配分数 (0-1)
        """
        # 初始分数
        score = 0.5
        
        # 获取产品特征
        product_type = product.get('product_type', '')
        investment_period = product.get('investment_period', 0)  # 以月为单位
        redemption_way = product.get('redemption_way', '随时赎回')
        
        # 1. 产品类型偏好匹配
        # 检查客户是否有首次购买记录
        first_purchase_type = customer.get('firstpurchasetype', None)
        if first_purchase_type and first_purchase_type == product_type:
            # 客户可能偏好与首次购买相同类型的产品
            score += 0.1
        
        # 2. 期限偏好匹配
        customer_type = customer.get('customer_type', 'personal')
        if customer_type == 'personal':
            # 个人客户可能更偏好中短期产品
            if 3 <= investment_period <= 12:
                score += 0.1
            elif investment_period > 24:
                score -= 0.1
        else:
            # 企业客户根据不同规模可能有不同偏好
            company_size = customer.get('company_size', 'medium')
            if company_size == 'small':
                # 小型企业可能偏好短期灵活产品
                if investment_period <= 6:
                    score += 0.1
            elif company_size == 'large':
                # 大型企业可能更能接受长期产品
                if investment_period >= 12:
                    score += 0.1
        
        # 3. 赎回方式偏好
        is_vip = customer.get('is_vip', False)
        if is_vip and redemption_way == '随时赎回':
            # VIP客户可能更看重灵活性
            score += 0.1
        
        # 4. 考虑客户历史行为 (如果有)
        if 'nousedays' in customer:
            try:
                unused_days = int(customer['nousedays'])
                if unused_days > 60 and redemption_way == '随时赎回':
                    # 长期未操作客户可能更需要灵活性
                    score += 0.05
            except (ValueError, TypeError):
                pass
        
        # 确保最终分数在0-1范围内
        return max(0.0, min(1.0, score))


    def _calculate_return_match_score(self, customer, product):
        """
        计算预期收益与客户偏好的匹配程度
        
        Args:
            customer (dict): 客户信息
            product (dict): 产品信息
            
        Returns:
            float: 匹配分数 (0-1)
        """
        # 初始分数
        score = 0.5
        
        # 获取产品预期收益率
        expected_yield = product.get('expected_yield', 0)
        
        # 获取客户风险等级
        risk_level = customer.get('risk_level', 'R3')
        
        # 根据风险等级确定预期收益范围
        expected_return_ranges = {
            'R1': (0.015, 0.035),  # 保守型 1.5%-3.5%
            'R2': (0.025, 0.045),  # 稳健型 2.5%-4.5%
            'R3': (0.035, 0.060),  # 平衡型 3.5%-6.0%
            'R4': (0.050, 0.080),  # 积极型 5.0%-8.0%
            'R5': (0.070, 0.120)   # 激进型 7.0%-12.0%
        }
        
        # 获取客户风险等级对应的收益范围
        min_return, max_return = expected_return_ranges.get(risk_level, (0.035, 0.060))
        
        # 收益在客户预期范围内，得分提高
        if min_return <= expected_yield <= max_return:
            score += 0.3
        elif expected_yield < min_return:
            # 收益低于预期，得分降低（与差距成正比）
            score -= 0.2 * (min_return - expected_yield) / min_return
        elif expected_yield > max_return:
            # 收益高于预期，可能有额外风险，得分小幅提高
            score += 0.1
        
        # 收益率极端情况处理
        if expected_yield > 0.15:  # 超高收益率（可能有风险）
            score -= 0.2
        
        # 考虑客户类型
        customer_type = customer.get('customer_type', 'personal')
        if customer_type == 'corporate':
            # 企业客户可能更注重稳定性
            if expected_yield < 0.06:
                score += 0.05
        
        # 考虑是否VIP客户
        is_vip = customer.get('is_vip', False)
        if is_vip:
            # VIP客户可能对高收益产品更感兴趣
            if expected_yield > max_return:
                score += 0.05
        
        # 确保最终分数在0-1范围内
        return max(0.0, min(1.0, score))


    def _get_available_products(self):
        """
        从数据库获取当前可用的产品列表
        
        Returns:
            list: 可用产品列表
        """
        try:
            query = """
            SELECT * FROM cdp_product_archive
            WHERE marketing_status = '在售'
            AND (end_date IS NULL OR end_date >= CURDATE())
            """
            
            products = self.db_manager.execute_query(query)
            return products
        
        except Exception as e:
            self.logger.error(f"获取可用产品时出错: {str(e)}")
            return []