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
        """
        生成历史理财购买记录
        
        Args:
            start_date (datetime.date/str): 开始日期
            end_date (datetime.date/str): 结束日期
            customer_ids (list, optional): 指定客户ID列表，如不提供则查询所有符合条件的客户
            
        Returns:
            int: 生成的记录数量
        """
        import random
        import datetime
        
        # 转换日期格式
        if isinstance(start_date, str):
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        
        self.logger.info(f"开始生成历史理财购买记录，时间范围: {start_date} 至 {end_date}")
        
        # 获取客户列表
        customers = self._get_eligible_customers(customer_ids)
        if not customers:
            self.logger.warning("没有找到符合条件的客户，无法生成理财购买记录")
            return 0
        
        self.logger.info(f"找到 {len(customers)} 个符合条件的客户")
        
        # 获取可用产品列表
        products = self._get_available_products(start_date, end_date)
        if not products:
            self.logger.warning("没有找到可用的理财产品，无法生成理财购买记录")
            return 0
        
        self.logger.info(f"找到 {len(products)} 个可用理财产品")
        
        # 计算时间范围
        date_range = (start_date, end_date)
        total_days = (end_date - start_date).days + 1
        if total_days <= 0:
            self.logger.error(f"日期范围无效: {start_date} 至 {end_date}")
            return 0
        
        # 初始化批处理和计数器
        batch_size = self.config.get('system', {}).get('batch_size', 1000)
        all_records = []
        total_generated = 0
        
        # 初始化进度跟踪
        total_customers = len(customers)
        processed_count = 0
        
        # 设置随机种子，确保结果可复现
        random_seed = self.config.get('system', {}).get('random_seed', None)
        if random_seed is not None:
            random.seed(random_seed)
        
        # 对每个客户生成投资记录
        for customer in customers:
            # 更新进度
            processed_count += 1
            if processed_count % 100 == 0 or processed_count == total_customers:
                self.logger.info(f"生成理财记录进度: {processed_count}/{total_customers}")
            
            # 获取客户ID和类型
            customer_id = customer.get('base_id')
            customer_type = customer.get('customer_type', 'personal')
            risk_level = customer.get('risk_level', 'R3')
            
            # 确定客户投资能力
            investment_capacity = self.product_matcher.calculate_investment_capacity(customer)
            
            # 确定该客户在时间范围内的投资次数
            min_purchases, max_purchases = self._get_purchase_count_range(customer, total_days)
            purchase_count = random.randint(min_purchases, max_purchases)
            
            # 如果购买次数为0，跳过该客户
            if purchase_count == 0:
                continue
            
            # 为客户选择购买日期
            purchase_dates = self._select_purchase_dates(start_date, end_date, purchase_count, customer_type)
            
            # 使用产品匹配器为客户找到合适的产品
            matched_products = self.product_matcher.find_matching_products(
                customer, limit=min(20, len(products))
            )
            
            if not matched_products:
                self.logger.debug(f"客户 {customer_id} 没有匹配的产品，跳过")
                continue
            
            # 为每个购买日期生成投资记录
            for purchase_date in purchase_dates:
                # 重新筛选当前可用的产品（考虑产品上架日期）
                current_matched_products = [
                    p for p in matched_products 
                    if self._is_product_available(p['product'], purchase_date)
                ]
                
                if not current_matched_products:
                    continue
                    
                # 从匹配的产品中选择一个产品
                selected_product = self._weighted_sample_products(
                    current_matched_products, 1
                )[0]['product']
                
                # 计算购买金额
                purchase_amount = self.calculate_investment_amount(customer, selected_product)
                
                # 生成购买时间
                purchase_time = self._generate_purchase_time(purchase_date, customer_type)
                
                # 计算到期日期
                investment_period = selected_product.get('investment_period', 0)
                maturity_date = InvestmentUtils.calculate_maturity_date(
                    purchase_date, term_months=investment_period
                )
                
                # 计算预期收益率
                expected_yield = selected_product.get('expected_yield', 0)
                
                # 创建理财购买记录
                investment_record = {
                    'detail_id': InvestmentUtils.generate_transaction_id(prefix="INV"),
                    'base_id': customer_id,
                    'detail_time': int(purchase_time.timestamp() * 1000),  # 13位时间戳
                    'product_id': selected_product.get('base_id'),
                    'purchase_amount': purchase_amount,
                    'hold_amount': purchase_amount,  # 初始持有金额等于购买金额
                    'term': investment_period * 30 if investment_period else 0,  # 转换为天数
                    'wealth_purchase_time': int(purchase_time.timestamp() * 1000),
                    'wealth_all_redeem_time': None,  # 初始未赎回
                    'wealth_date': purchase_date,
                    'wealth_status': '持有',  # 初始状态为持有
                    'maturity_time': int(datetime.datetime.combine(
                        maturity_date, datetime.time(0, 0)).timestamp() * 1000) if maturity_date else None,
                    'status': '成功',
                    'channel': self._generate_purchase_channel(customer),
                    'expected_return': expected_yield,
                    'account_id': self._get_customer_account(customer_id)
                }
                
                # 添加到结果列表
                all_records.append(investment_record)
                total_generated += 1
                
                # 批量处理，当记录达到batch_size时导入数据库
                if len(all_records) >= batch_size:
                    self._import_batch_records(all_records)
                    all_records = []
            
        # 处理剩余记录
        if all_records:
            self._import_batch_records(all_records)
        
        self.logger.info(f"历史理财购买记录生成完成，总生成记录数: {total_generated}")
        
        # 生成与购买相关的事件
        if self.events_generator and total_generated > 0:
            self.logger.info("开始生成理财购买相关事件")
            event_count = self._generate_purchase_events(start_date, end_date)
            self.logger.info(f"共生成 {event_count} 条理财购买相关事件")
        
        return total_generated

    def _get_eligible_customers(self, customer_ids=None):
        """
        获取符合条件的客户列表
        
        Args:
            customer_ids (list, optional): 指定客户ID列表
            
        Returns:
            list: 客户信息列表
        """
        try:
            # 构建查询条件
            conditions = []
            params = []
            
            # 如果指定了客户ID列表
            if customer_ids:
                id_placeholders = ', '.join(['%s'] * len(customer_ids))
                conditions.append(f"base_id IN ({id_placeholders})")
                params.extend(customer_ids)
            
            # 基本筛选条件：状态为正常
            conditions.append("status = 'active'")
            
            # 构建完整查询语句
            query = """
            SELECT * FROM cdp_customer_profile
            WHERE """ + " AND ".join(conditions)
            
            # 执行查询
            customers = self.db_manager.execute_query(query, params)
            
            return customers
        except Exception as e:
            self.logger.error(f"获取符合条件的客户时出错: {str(e)}")
            return []

    def _get_available_products(self, start_date, end_date):
        """
        获取时间范围内可用的理财产品
        
        Args:
            start_date (datetime.date): 开始日期
            end_date (datetime.date): 结束日期
            
        Returns:
            list: 产品信息列表
        """
        try:
            # 构建查询条件
            conditions = ["marketing_status = '在售'"]
            params = []
            
            # 上架日期范围条件（如果产品有上架日期字段）
            if start_date:
                conditions.append("(launch_date IS NULL OR launch_date <= %s)")
                params.append(end_date)
            
            # 下架日期范围条件（如果产品有下架日期字段）
            if end_date:
                conditions.append("(end_date IS NULL OR end_date >= %s)")
                params.append(start_date)
            
            # 构建完整查询语句
            query = """
            SELECT * FROM cdp_product_archive
            WHERE """ + " AND ".join(conditions)
            
            # 执行查询
            products = self.db_manager.execute_query(query, params)
            
            return products
        except Exception as e:
            self.logger.error(f"获取可用产品时出错: {str(e)}")
            return []

    def _get_purchase_count_range(self, customer, total_days):
        """
        根据客户特征和时间范围长度确定购买次数范围
        
        Args:
            customer (dict): 客户信息
            total_days (int): 总天数
            
        Returns:
            tuple: (最小购买次数, 最大购买次数)
        """
        # 获取客户类型和VIP状态
        customer_type = customer.get('customer_type', 'personal')
        is_vip = customer.get('is_vip', False)
        
        # 基础购买频率（次数/年）
        if customer_type == 'corporate':
            # 企业客户基础购买频率
            base_min = 2
            base_max = 12
        else:
            # 个人客户基础购买频率
            base_min = 0
            base_max = 8
        
        # VIP客户购买频率提升
        if is_vip:
            base_min += 1
            base_max += 4
        
        # 考虑风险偏好（高风险偏好的客户购买频率略高）
        risk_level = customer.get('risk_level', 'R3')
        risk_levels = {'R1': 0, 'R2': 0, 'R3': 1, 'R4': 2, 'R5': 3}
        risk_factor = risk_levels.get(risk_level, 0)
        
        base_min += risk_factor // 2
        base_max += risk_factor
        
        # 根据时间范围调整购买次数
        days_factor = total_days / 365.0  # 转换为年
        
        min_purchases = max(0, round(base_min * days_factor))
        max_purchases = max(min_purchases, round(base_max * days_factor))
        
        return min_purchases, max_purchases

    def _select_purchase_dates(self, start_date, end_date, count, customer_type='personal'):
        """
        为客户选择购买日期
        
        考虑工作日/非工作日分布，月初/月末特征等
        
        Args:
            start_date (datetime.date): 开始日期
            end_date (datetime.date): 结束日期
            count (int): 购买次数
            customer_type (str): 客户类型
            
        Returns:
            list: 购买日期列表
        """
        import random
        import datetime
        
        # 计算日期范围
        total_days = (end_date - start_date).days + 1
        if total_days <= 0 or count <= 0:
            return []
        
        # 工作日偏好因子（工作日的权重）
        if customer_type == 'corporate':
            workday_weight = 0.9  # 企业客户更偏好工作日
        else:
            workday_weight = 0.8  # 个人客户工作日权重略低
        
        # 构建日期列表及其权重
        dates = []
        weights = []
        
        current_date = start_date
        while current_date <= end_date:
            is_workday = current_date.weekday() < 5  # 周一至周五为工作日
            is_month_end = current_date.day >= 25
            is_month_start = current_date.day <= 5
            
            # 基础权重
            if is_workday:
                weight = workday_weight
            else:
                weight = 1 - workday_weight
            
            # 月末个人客户购买概率提高（工资发放后）
            if customer_type == 'personal' and is_month_end:
                weight *= 1.5
            
            # 月初企业客户购买概率提高（月初资金规划）
            if customer_type == 'corporate' and is_month_start:
                weight *= 1.4
            
            dates.append(current_date)
            weights.append(weight)
            
            current_date += datetime.timedelta(days=1)
        
        # 归一化权重
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]
        
        # 随机选择日期（不重复）
        if count >= len(dates):
            return dates  # 如果要求的次数超过日期范围，返回所有日期
        
        selected_dates = []
        remaining_dates = list(dates)  # 创建副本
        remaining_weights = list(weights)  # 创建副本
        
        for _ in range(count):
            if not remaining_dates:
                break
                
            # 根据权重随机选择一个日期
            selected_index = random.choices(
                range(len(remaining_dates)), 
                weights=remaining_weights, 
                k=1
            )[0]
            
            selected_dates.append(remaining_dates.pop(selected_index))
            remaining_weights.pop(selected_index)
        
        # 按日期排序
        selected_dates.sort()
        
        return selected_dates

    def _is_product_available(self, product, date):
        """
        检查产品在指定日期是否可用
        
        Args:
            product (dict): 产品信息
            date (datetime.date): 检查日期
            
        Returns:
            bool: 是否可用
        """
        # 检查产品上架日期
        launch_date = product.get('launch_date')
        if launch_date:
            if isinstance(launch_date, str):
                launch_date = datetime.datetime.strptime(launch_date, '%Y-%m-%d').date()
            if date < launch_date:
                return False
        
        # 检查产品下架日期
        end_date = product.get('end_date')
        if end_date:
            if isinstance(end_date, str):
                end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
            if date > end_date:
                return False
        
        # 检查产品状态
        status = product.get('marketing_status')
        if status and status != '在售':
            return False
        
        return True

    def _generate_purchase_events(self, start_date, end_date):
        """
        为指定时间范围内的购买记录生成相关事件
        
        Args:
            start_date (datetime.date): 开始日期
            end_date (datetime.date): 结束日期
            
        Returns:
            int: 生成的事件数量
        """
        if not self.events_generator:
            return 0
        
        # 转换为时间戳格式，用于查询
        start_timestamp = int(datetime.datetime.combine(
            start_date, datetime.time(0, 0)).timestamp() * 1000)
        end_timestamp = int(datetime.datetime.combine(
            end_date, datetime.time(23, 59, 59)).timestamp() * 1000)
        
        try:
            # 查询时间范围内的所有购买记录
            query = """
            SELECT * FROM cdp_investment_order
            WHERE detail_time BETWEEN %s AND %s
            ORDER BY detail_time
            """
            
            investments = self.db_manager.execute_query(query, (start_timestamp, end_timestamp))
            
            if not investments:
                self.logger.info(f"时间范围内没有购买记录，跳过事件生成")
                return 0
            
            self.logger.info(f"为 {len(investments)} 条购买记录生成事件")
            
            # 批量处理
            batch_size = 100
            total_events = 0
            
            for i in range(0, len(investments), batch_size):
                batch = investments[i:i+batch_size]
                for investment in batch:
                    # 生成购买相关事件
                    events = self.events_generator.generate_purchase_events(investment)
                    if events:
                        # 这里假设事件生成器内部会处理事件的保存
                        total_events += len(events)
                
                self.logger.debug(f"已处理 {i + len(batch)}/{len(investments)} 条记录")
            
            return total_events
            
        except Exception as e:
            self.logger.error(f"生成购买事件时出错: {str(e)}")
            return 0
    
    def generate_realtime_investments(self, date_range=None):
        """
        生成实时增量理财记录
        
        根据指定的日期范围或系统当前时间，生成新增的理财购买记录
        
        Args:
            date_range (tuple, optional): 日期范围元组(start_date, end_date)，
                                        如未提供则根据系统当前时间和上次生成时间自动计算
        
        Returns:
            int: 生成的记录数量
        """
        import datetime
        
        self.logger.info("开始生成实时增量理财记录")
        
        # 如果未提供日期范围，自动计算
        if not date_range:
            date_range = self._calculate_realtime_date_range()
        
        start_date, end_date = date_range
        
        # 转换日期格式
        if isinstance(start_date, str):
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # 检查日期范围有效性
        if start_date > end_date:
            self.logger.error(f"无效的日期范围: {start_date} 至 {end_date}")
            return 0
        
        total_days = (end_date - start_date).days + 1
        if total_days <= 0:
            self.logger.warning(f"日期范围为0天，无需生成数据: {start_date} 至 {end_date}")
            return 0
        
        self.logger.info(f"将生成 {start_date} 至 {end_date} 的增量理财记录")
        
        # 获取活跃客户列表（近期有交易或查询行为的客户更可能购买理财产品）
        active_customers = self._get_active_customers(start_date, limit=500)
        if not active_customers:
            self.logger.warning("没有找到活跃客户，将尝试获取普通客户")
            # 如果没有活跃客户，使用普通客户选择逻辑
            active_customers = self._get_eligible_customers(limit=300)
        
        self.logger.info(f"找到 {len(active_customers)} 个活跃客户")
        
        # 获取当前销售中的产品列表
        available_products = self._get_available_products(start_date, end_date)
        if not available_products:
            self.logger.warning("没有找到可用的理财产品，无法生成理财购买记录")
            return 0
        
        self.logger.info(f"找到 {len(available_products)} 个可用理财产品")
        
        # 计算有多少客户会在此期间购买理财产品
        purchase_ratio = self._get_purchase_ratio(start_date, end_date)
        max_customers = max(1, int(len(active_customers) * purchase_ratio))
        
        # 随机选择客户子集
        import random
        selected_customers = random.sample(active_customers, min(max_customers, len(active_customers)))
        
        self.logger.info(f"将为 {len(selected_customers)} 个客户生成理财购买记录")
        
        # 初始化批处理和计数器
        batch_size = self.config.get('system', {}).get('batch_size', 1000)
        all_records = []
        total_generated = 0
        
        # 为选定的客户生成购买记录
        for customer in selected_customers:
            # 获取客户信息
            customer_id = customer.get('base_id')
            customer_type = customer.get('customer_type', 'personal')
            
            # 确定购买日期（每个客户在此期间只生成一条记录）
            purchase_date = self._select_realtime_purchase_date(start_date, end_date, customer_type)
            
            # 使用产品匹配器为客户找到合适的产品
            matched_products = self.product_matcher.find_matching_products(
                customer, limit=min(10, len(available_products))
            )
            
            if not matched_products:
                self.logger.debug(f"客户 {customer_id} 没有匹配的产品，跳过")
                continue
            
            # 从匹配的产品中选择一个
            selected_product = self._weighted_sample_products(matched_products, 1)[0]['product']
            
            # 计算购买金额
            purchase_amount = self.calculate_investment_amount(customer, selected_product)
            
            # 生成购买时间
            purchase_time = self._generate_purchase_time(purchase_date, customer_type)
            
            # 计算到期日期
            investment_period = selected_product.get('investment_period', 0)
            maturity_date = InvestmentUtils.calculate_maturity_date(
                purchase_date, term_months=investment_period
            )
            
            # 计算预期收益率
            expected_yield = selected_product.get('expected_yield', 0)
            
            # 创建理财购买记录
            investment_record = {
                'detail_id': InvestmentUtils.generate_transaction_id(prefix="INV"),
                'base_id': customer_id,
                'detail_time': int(purchase_time.timestamp() * 1000),  # 13位时间戳
                'product_id': selected_product.get('base_id'),
                'purchase_amount': purchase_amount,
                'hold_amount': purchase_amount,  # 初始持有金额等于购买金额
                'term': investment_period * 30 if investment_period else 0,  # 转换为天数
                'wealth_purchase_time': int(purchase_time.timestamp() * 1000),
                'wealth_all_redeem_time': None,  # 初始未赎回
                'wealth_date': purchase_date,
                'wealth_status': '持有',  # 初始状态为持有
                'maturity_time': int(datetime.datetime.combine(
                    maturity_date, datetime.time(0, 0)).timestamp() * 1000) if maturity_date else None,
                'status': '成功',
                'channel': self._generate_purchase_channel(customer),
                'expected_return': expected_yield,
                'account_id': self._get_customer_account(customer_id)
            }
            
            # 添加到结果列表
            all_records.append(investment_record)
            total_generated += 1
            
            # 批量处理，当记录达到batch_size时导入数据库
            if len(all_records) >= batch_size:
                self._import_batch_records(all_records)
                all_records = []
        
        # 处理剩余记录
        if all_records:
            self._import_batch_records(all_records)
        
        self.logger.info(f"实时理财购买记录生成完成，总生成记录数: {total_generated}")
        
        # 生成与购买相关的事件
        if self.events_generator and total_generated > 0:
            self.logger.info("开始生成理财购买相关事件")
            event_count = self._generate_purchase_events(start_date, end_date)
            self.logger.info(f"共生成 {event_count} 条理财购买相关事件")
        
        # 更新最后生成的时间戳
        self._update_last_generation_timestamp(end_date)
        
        return total_generated

    def _calculate_realtime_date_range(self):
        """
        计算实时数据生成的日期范围
        
        根据当前系统时间和调度规则，计算需要生成的增量数据日期范围
        
        Returns:
            tuple: (start_date, end_date) 日期范围
        """
        import datetime
        
        current_time = datetime.datetime.now()
        current_hour = current_time.hour
        
        # 获取上次生成数据的时间戳
        last_timestamp = self._get_last_generation_timestamp()
        
        # 如果没有上次生成记录，默认使用最近7天
        if not last_timestamp:
            self.logger.warning("没有找到上次生成时间戳，默认使用当前日期前7天作为开始时间")
            start_date = (current_time - datetime.timedelta(days=7)).date()
        else:
            # 将时间戳转换为日期
            last_date = datetime.datetime.fromtimestamp(last_timestamp / 1000).date()
            # 使用上次生成日期的后一天作为开始时间
            start_date = last_date + datetime.timedelta(days=1)
        
        # 默认使用昨天作为结束日期
        end_date = (current_time - datetime.timedelta(days=1)).date()
        
        # 调整日期范围，根据调度时间确定生成范围
        # 如果是13点执行，生成当天0-12点数据
        if current_hour == 13:
            # 使用当天作为结束日期
            end_date = current_time.date()
            # 如果开始日期晚于结束日期（说明已经处理到当天），则从当天开始
            if start_date > end_date:
                start_date = end_date
        # 如果是1点执行，生成前一天13-23点数据
        elif current_hour == 1:
            # 使用前一天作为结束日期
            end_date = (current_time - datetime.timedelta(days=1)).date()
            # 确保开始日期不晚于结束日期
            start_date = min(start_date, end_date)
        
        self.logger.info(f"计算的实时数据生成日期范围: {start_date} 至 {end_date}")
        return (start_date, end_date)

    def _get_last_generation_timestamp(self):
        """
        获取上次生成数据的时间戳
        
        从数据库或配置中读取上次增量数据生成的时间戳
        
        Returns:
            int: 上次生成时间的时间戳（毫秒级）
        """
        try:
            # 尝试从数据库获取状态记录
            query = """
            SELECT value 
            FROM cdp_system_state 
            WHERE key = 'last_investment_generation_timestamp'
            """
            
            result = self.db_manager.execute_query(query)
            
            if result and len(result) > 0 and 'value' in result[0]:
                timestamp = int(result[0]['value'])
                self.logger.debug(f"从数据库获取到上次生成时间戳: {timestamp}")
                return timestamp
            
            # 如果数据库中没有记录，尝试从配置中获取
            if self.time_manager:
                timestamp = self.time_manager.get_last_timestamp('investment_generation')
                if timestamp:
                    self.logger.debug(f"从时间管理器获取到上次生成时间戳: {timestamp}")
                    return timestamp
            
            self.logger.warning("未找到上次生成时间戳")
            return None
            
        except Exception as e:
            self.logger.error(f"获取上次生成时间戳时出错: {str(e)}")
            return None

    def _update_last_generation_timestamp(self, end_date):
        """
        更新最后一次数据生成的时间戳
        
        将最新的生成时间记录到数据库或配置中，用于下次增量生成的起始时间确定
        
        Args:
            end_date (datetime.date): 本次生成的结束日期
        """
        import datetime
        
        # 将结束日期转换为毫秒级时间戳（使用23:59:59作为时间）
        end_datetime = datetime.datetime.combine(end_date, datetime.time(23, 59, 59))
        timestamp = int(end_datetime.timestamp() * 1000)
        
        try:
            # 尝试更新数据库中的状态记录
            update_query = """
            INSERT INTO cdp_system_state (key, value, update_time)
            VALUES ('last_investment_generation_timestamp', %s, %s)
            ON DUPLICATE KEY UPDATE value = %s, update_time = %s
            """
            
            current_time = datetime.datetime.now()
            params = (
                str(timestamp),
                current_time,
                str(timestamp),
                current_time
            )
            
            self.db_manager.execute_update(update_query, params)
            
            # 同时更新时间管理器中的记录（如果有）
            if self.time_manager:
                self.time_manager.update_last_timestamp('investment_generation', timestamp)
            
            self.logger.info(f"已更新上次生成时间戳为: {timestamp} ({end_date})")
            
        except Exception as e:
            self.logger.error(f"更新上次生成时间戳时出错: {str(e)}")

    def _get_active_customers(self, reference_date, days_lookback=30, limit=500):
        """
        获取活跃客户列表
        
        查询最近一段时间内有交易或查询行为的客户，这些客户更可能购买理财产品
        
        Args:
            reference_date (datetime.date): 参考日期
            days_lookback (int): 向前查询的天数
            limit (int): 返回客户数量限制
            
        Returns:
            list: 活跃客户信息列表
        """
        import datetime
        
        # 计算查询的起始日期
        start_date = reference_date - datetime.timedelta(days=days_lookback)
        
        # 转换为时间戳格式，用于查询
        start_timestamp = int(datetime.datetime.combine(
            start_date, datetime.time(0, 0)).timestamp() * 1000)
        reference_timestamp = int(datetime.datetime.combine(
            reference_date, datetime.time(23, 59, 59)).timestamp() * 1000)
        
        try:
            # 查询最近有交易的客户
            transaction_query = """
            SELECT DISTINCT c.* 
            FROM cdp_customer_profile c
            JOIN cdp_account_flow f ON c.base_id = f.base_id
            WHERE f.detail_time BETWEEN %s AND %s
            AND c.status = 'active'
            ORDER BY f.detail_time DESC
            LIMIT %s
            """
            
            transaction_customers = self.db_manager.execute_query(
                transaction_query, (start_timestamp, reference_timestamp, limit)
            )
            
            # 查询最近有产品查询行为的客户
            query_event_query = """
            SELECT DISTINCT c.* 
            FROM cdp_customer_profile c
            JOIN cdp_customer_event e ON c.base_id = e.base_id
            WHERE e.event_time BETWEEN %s AND %s
            AND e.event IN ('product_detail_view_event', 'product_list_view_event', 'weatlth_product_click_event')
            AND c.status = 'active'
            ORDER BY e.event_time DESC
            LIMIT %s
            """
            
            query_customers = self.db_manager.execute_query(
                query_event_query, (start_timestamp, reference_timestamp, limit)
            )
            
            # 合并两部分客户并去重
            all_customers = transaction_customers + query_customers
            customer_ids = set()
            unique_customers = []
            
            for customer in all_customers:
                if customer['base_id'] not in customer_ids:
                    customer_ids.add(customer['base_id'])
                    unique_customers.append(customer)
            
            # 限制返回数量
            return unique_customers[:limit]
            
        except Exception as e:
            self.logger.error(f"获取活跃客户时出错: {str(e)}")
            return []

    def _get_purchase_ratio(self, start_date, end_date):
        """
        计算该时间段内客户购买理财产品的比例
        
        根据历史数据、时间段特征（工作日/节假日、月初/月末等）计算购买比例
        
        Args:
            start_date (datetime.date): 开始日期
            end_date (datetime.date): 结束日期
            
        Returns:
            float: 购买比例 (0-1)
        """
        import datetime
        
        # 计算时间段天数
        days = (end_date - start_date).days + 1
        
        # 基础购买比例（每日约0.5%的活跃客户会购买理财产品）
        base_ratio = 0.005 * days
        
        # 检查是否包含月末（25日以后）
        has_month_end = False
        current_date = start_date
        while current_date <= end_date:
            if current_date.day >= 25:
                has_month_end = True
                break
            current_date += datetime.timedelta(days=1)
        
        # 月末购买比例提高
        if has_month_end:
            base_ratio *= 1.3
        
        # 检查是否包含月初（1-5日）
        has_month_start = False
        current_date = start_date
        while current_date <= end_date:
            if 1 <= current_date.day <= 5:
                has_month_start = True
                break
            current_date += datetime.timedelta(days=1)
        
        # 月初购买比例略有提高（企业客户资金规划）
        if has_month_start:
            base_ratio *= 1.1
        
        # 检查工作日占比
        workday_count = 0
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() < 5:  # 周一至周五
                workday_count += 1
            current_date += datetime.timedelta(days=1)
        
        workday_ratio = workday_count / days if days > 0 else 0
        
        # 工作日占比高，购买比例略有提高
        if workday_ratio > 0.7:
            base_ratio *= 1.1
        
        # 确保比例合理（不超过活跃客户的30%）
        return min(0.3, max(0.01, base_ratio))

    def _select_realtime_purchase_date(self, start_date, end_date, customer_type='personal'):
        """
        为实时生成选择购买日期
        
        Args:
            start_date (datetime.date): 开始日期
            end_date (datetime.date): 结束日期
            customer_type (str): 客户类型
            
        Returns:
            datetime.date: 选择的购买日期
        """
        import random
        import datetime
        
        # 获取日期范围内的所有日期
        date_list = []
        current_date = start_date
        while current_date <= end_date:
            date_list.append(current_date)
            current_date += datetime.timedelta(days=1)
        
        if not date_list:
            return start_date  # 如果没有有效日期，返回开始日期
        
        # 计算各日期的权重
        weights = []
        for date in date_list:
            is_workday = date.weekday() < 5  # 周一至周五为工作日
            is_month_end = date.day >= 25
            is_month_start = date.day <= 5
            
            # 基础权重
            weight = 1.0
            
            # 工作日权重调整
            if is_workday:
                weight *= 1.2 if customer_type == 'corporate' else 1.1
            else:
                weight *= 0.8 if customer_type == 'corporate' else 0.9
            
            # 月末个人客户购买概率提高（工资发放后）
            if customer_type == 'personal' and is_month_end:
                weight *= 1.5
            
            # 月初企业客户购买概率提高（月初资金规划）
            if customer_type == 'corporate' and is_month_start:
                weight *= 1.4
            
            weights.append(weight)
        
        # 归一化权重
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]
        
        # 根据权重随机选择一个日期
        selected_date = random.choices(date_list, weights=weights, k=1)[0]
        
        return selected_date
        
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
        """
        验证生成的数据合法性
        
        执行多项检查确保生成的理财数据质量和完整性，包括必填字段、金额范围、
        引用完整性、时间逻辑、业务规则等方面的验证
        
        Args:
            investments (list): 待验证的理财购买记录列表
            
        Returns:
            dict: 包含验证结果和详细统计信息的字典
        """
        self.logger.info(f"开始验证 {len(investments)} 条理财购买记录")
        
        # 初始化验证结果
        validation_result = {
            'is_valid': True,
            'total_records': len(investments),
            'valid_records': 0,
            'invalid_records': 0,
            'error_summary': {},
            'field_stats': {},
            'warnings': [],
            'validation_details': []
        }
        
        # 如果没有记录，直接返回
        if not investments:
            self.logger.warning("没有记录需要验证")
            validation_result['warnings'].append("没有记录需要验证")
            return validation_result
        
        # 定义必填字段列表
        required_fields = [
            'detail_id', 'base_id', 'product_id', 'detail_time', 
            'purchase_amount', 'wealth_date', 'wealth_status'
        ]
        
        # 定义字段验证规则
        field_validators = {
            'detail_id': {
                'validator': lambda x: isinstance(x, str) and len(x) > 5,
                'error_message': "交易ID无效或长度不足"
            },
            'base_id': {
                'validator': lambda x: isinstance(x, str) and len(x) > 5,
                'error_message': "客户ID无效或长度不足"
            },
            'product_id': {
                'validator': lambda x: isinstance(x, str) and len(x) > 2,
                'error_message': "产品ID无效或长度不足"
            },
            'detail_time': {
                'validator': lambda x: isinstance(x, (int, float)) and x > 1000000000000,
                'error_message': "交易时间戳无效或格式错误"
            },
            'purchase_amount': {
                'validator': lambda x: isinstance(x, (int, float)) and x > 0,
                'error_message': "购买金额无效或非正数"
            },
            'hold_amount': {
                'validator': lambda x: isinstance(x, (int, float)) and x >= 0,
                'error_message': "持有金额无效或为负数"
            },
            'wealth_date': {
                'validator': lambda x: x is not None,
                'error_message': "购买日期不能为空"
            },
            'wealth_status': {
                'validator': lambda x: x in ['持有', '部分卖出', '完全赎回'],
                'error_message': "理财状态无效，必须是持有、部分卖出或完全赎回之一"
            }
        }
        
        # 初始化字段统计
        for field in required_fields + list(field_validators.keys()):
            if field not in validation_result['field_stats']:
                validation_result['field_stats'][field] = {
                    'missing': 0,
                    'invalid': 0,
                    'valid': 0
                }
        
        # 验证每条记录
        valid_records = []
        
        for idx, record in enumerate(investments):
            record_errors = []
            record_is_valid = True
            
            # 1. 必填字段验证
            for field in required_fields:
                if field not in record or record[field] is None:
                    record_errors.append(f"缺少必填字段: {field}")
                    validation_result['field_stats'][field]['missing'] += 1
                    record_is_valid = False
            
            # 2. 字段验证
            for field, validator_info in field_validators.items():
                if field in record and record[field] is not None:
                    if not validator_info['validator'](record[field]):
                        record_errors.append(f"{field}: {validator_info['error_message']}")
                        validation_result['field_stats'][field]['invalid'] += 1
                        record_is_valid = False
                    else:
                        validation_result['field_stats'][field]['valid'] += 1
            
            # 3. 业务规则验证
            
            # 3.1 持有金额不能大于购买金额
            if 'purchase_amount' in record and 'hold_amount' in record:
                if record['hold_amount'] > record['purchase_amount']:
                    record_errors.append("持有金额大于购买金额，数据不一致")
                    record_is_valid = False
            
            # 3.2 如果状态是'完全赎回'，持有金额应为0
            if 'wealth_status' in record and 'hold_amount' in record:
                if record['wealth_status'] == '完全赎回' and record['hold_amount'] > 0:
                    record_errors.append("状态为完全赎回但持有金额不为0，数据不一致")
                    record_is_valid = False
            
            # 3.3 如果存在完全赎回时间，状态应为'完全赎回'
            if 'wealth_all_redeem_time' in record and record['wealth_all_redeem_time']:
                if 'wealth_status' in record and record['wealth_status'] != '完全赎回':
                    record_errors.append("存在完全赎回时间但状态不是完全赎回，数据不一致")
                    record_is_valid = False
            
            # 将结果添加到验证详情
            validation_record = {
                'record_index': idx,
                'detail_id': record.get('detail_id', None),
                'base_id': record.get('base_id', None),
                'is_valid': record_is_valid,
                'errors': record_errors
            }
            validation_result['validation_details'].append(validation_record)
            
            # 统计有效和无效记录数
            if record_is_valid:
                validation_result['valid_records'] += 1
                valid_records.append(record)
            else:
                validation_result['invalid_records'] += 1
                
                # 统计错误类型
                for error in record_errors:
                    error_key = error.split(':')[0] if ':' in error else error
                    if error_key not in validation_result['error_summary']:
                        validation_result['error_summary'][error_key] = 0
                    validation_result['error_summary'][error_key] += 1
        
        # 4. 跨记录验证
        
        # 4.1 验证客户引用
        self._validate_customer_references(valid_records, validation_result)
        
        # 4.2 验证产品引用
        self._validate_product_references(valid_records, validation_result)
        
        # 4.3 验证时间分布
        self._validate_time_distribution(valid_records, validation_result)
        
        # 更新整体验证结果
        validation_result['is_valid'] = validation_result['invalid_records'] == 0 and len(validation_result['warnings']) == 0
        
        # 记录验证结果
        self.logger.info(f"理财数据验证完成: 总共 {validation_result['total_records']} 条记录, "
                    f"有效 {validation_result['valid_records']} 条, "
                    f"无效 {validation_result['invalid_records']} 条")
        
        if not validation_result['is_valid']:
            self.logger.warning(f"验证发现问题: {validation_result['error_summary']}")
        
        return validation_result

    def _validate_customer_references(self, records, validation_result):
        """
        验证客户引用的有效性
        
        Args:
            records (list): 需要验证的有效记录列表
            validation_result (dict): 验证结果字典，将被修改
        """
        if not records:
            return
        
        # 提取所有客户ID
        customer_ids = {record['base_id'] for record in records if 'base_id' in record}
        
        if not customer_ids:
            return
        
        try:
            # 检查这些客户是否存在于数据库中
            placeholders = ', '.join(['%s'] * len(customer_ids))
            query = f"""
            SELECT base_id FROM cdp_customer_profile
            WHERE base_id IN ({placeholders})
            """
            
            results = self.db_manager.execute_query(query, list(customer_ids))
            
            # 统计找到的客户ID
            found_customer_ids = {row['base_id'] for row in results}
            
            # 检查是否有未找到的客户ID
            not_found_ids = customer_ids - found_customer_ids
            
            if not_found_ids:
                warning_message = f"发现 {len(not_found_ids)} 个无效的客户ID"
                validation_result['warnings'].append(warning_message)
                
                # 限制日志中显示的ID数量
                display_ids = list(not_found_ids)[:10]
                if len(not_found_ids) > 10:
                    display_ids.append("...")
                    
                self.logger.warning(f"{warning_message}: {', '.join(str(id) for id in display_ids)}")
        
        except Exception as e:
            self.logger.error(f"验证客户引用时出错: {str(e)}")
            validation_result['warnings'].append(f"验证客户引用时出错: {str(e)}")

    def _validate_product_references(self, records, validation_result):
        """
        验证产品引用的有效性
        
        Args:
            records (list): 需要验证的有效记录列表
            validation_result (dict): 验证结果字典，将被修改
        """
        if not records:
            return
        
        # 提取所有产品ID
        product_ids = {record['product_id'] for record in records if 'product_id' in record}
        
        if not product_ids:
            return
        
        try:
            # 检查这些产品是否存在于数据库中
            placeholders = ', '.join(['%s'] * len(product_ids))
            query = f"""
            SELECT base_id FROM cdp_product_archive
            WHERE base_id IN ({placeholders})
            """
            
            results = self.db_manager.execute_query(query, list(product_ids))
            
            # 统计找到的产品ID
            found_product_ids = {row['base_id'] for row in results}
            
            # 检查是否有未找到的产品ID
            not_found_ids = product_ids - found_product_ids
            
            if not_found_ids:
                warning_message = f"发现 {len(not_found_ids)} 个无效的产品ID"
                validation_result['warnings'].append(warning_message)
                
                # 限制日志中显示的ID数量
                display_ids = list(not_found_ids)[:10]
                if len(not_found_ids) > 10:
                    display_ids.append("...")
                    
                self.logger.warning(f"{warning_message}: {', '.join(str(id) for id in display_ids)}")
        
        except Exception as e:
            self.logger.error(f"验证产品引用时出错: {str(e)}")
            validation_result['warnings'].append(f"验证产品引用时出错: {str(e)}")

    def _validate_time_distribution(self, records, validation_result):
        """
        验证记录时间分布的合理性
        
        检查工作日/非工作日、交易时间分布等是否符合预期
        
        Args:
            records (list): 需要验证的有效记录列表
            validation_result (dict): 验证结果字典，将被修改
        """
        import datetime
        import collections
        
        if not records:
            return
        
        # 初始化统计数据
        time_stats = {
            'weekday_count': 0,
            'weekend_count': 0,
            'hour_distribution': collections.defaultdict(int),
            'day_distribution': collections.defaultdict(int),
            'month_distribution': collections.defaultdict(int)
        }
        
        # 遍历记录统计时间分布
        for record in records:
            if 'detail_time' in record and record['detail_time']:
                try:
                    # 解析时间戳
                    ts = record['detail_time']
                    if isinstance(ts, (int, float)) and ts > 1000000000000:  # 毫秒级时间戳
                        dt = datetime.datetime.fromtimestamp(ts / 1000)
                    else:
                        dt = datetime.datetime.fromtimestamp(ts)
                    
                    # 统计工作日/周末
                    if dt.weekday() < 5:  # 周一至周五
                        time_stats['weekday_count'] += 1
                    else:  # 周六、周日
                        time_stats['weekend_count'] += 1
                    
                    # 统计小时分布
                    time_stats['hour_distribution'][dt.hour] += 1
                    
                    # 统计日期分布
                    time_stats['day_distribution'][dt.day] += 1
                    
                    # 统计月份分布
                    time_stats['month_distribution'][dt.month] += 1
                    
                except Exception as e:
                    self.logger.error(f"解析时间戳出错: {str(e)}, 时间戳值: {record['detail_time']}")
        
        # 计算总记录数
        total_records = len(records)
        
        # 验证工作日/周末比例
        if total_records > 0:
            weekday_ratio = time_stats['weekday_count'] / total_records
            
            # 预期工作日占比约为0.7-0.85，如果偏离太多可能有问题
            if weekday_ratio < 0.65 or weekday_ratio > 0.9:
                warning_message = f"工作日占比异常: {weekday_ratio:.2f}, 工作日: {time_stats['weekday_count']}, 周末: {time_stats['weekend_count']}"
                validation_result['warnings'].append(warning_message)
                self.logger.warning(warning_message)
        
        # 验证时间分布
        if total_records > 10:  # 只有记录足够多时才验证时间分布
            # 检查夜间交易比例（0-6点）
            night_hours = [0, 1, 2, 3, 4, 5]
            night_count = sum(time_stats['hour_distribution'].get(hour, 0) for hour in night_hours)
            night_ratio = night_count / total_records if total_records > 0 else 0
            
            # 夜间交易比例不应过高（通常不超过5%）
            if night_ratio > 0.1:
                warning_message = f"夜间交易(0-6点)比例过高: {night_ratio:.2f}, 共 {night_count} 笔"
                validation_result['warnings'].append(warning_message)
                self.logger.warning(warning_message)
            
            # 检查是否有极不均匀的时间分布（某小时占比过高）
            for hour, count in time_stats['hour_distribution'].items():
                hour_ratio = count / total_records
                if hour_ratio > 0.25:  # 单小时占比超过25%
                    warning_message = f"时间分布异常: {hour}点的交易占比为 {hour_ratio:.2f}, 共 {count} 笔"
                    validation_result['warnings'].append(warning_message)
                    self.logger.warning(warning_message)
        
        # 将时间统计添加到验证结果
        validation_result['time_distribution'] = {
            'weekday_ratio': time_stats['weekday_count'] / total_records if total_records > 0 else 0,
            'weekend_ratio': time_stats['weekend_count'] / total_records if total_records > 0 else 0,
            'hour_distribution': dict(time_stats['hour_distribution']),
            'day_distribution': dict(time_stats['day_distribution']),
            'month_distribution': dict(time_stats['month_distribution'])
        }
        
    def update_customer_wealth_status(self, customer_id, investment_info):
        """
        更新客户理财状态信息
        
        根据最新的理财购买或赎回记录，更新客户档案中的财富相关属性，
        包括财富阶段、首次购买类型、清仓日期等信息
        
        Args:
            customer_id (str): 客户ID
            investment_info (dict): 最新的理财交易信息
            
        Returns:
            bool: 更新是否成功
        """
        if not customer_id or not investment_info:
            self.logger.warning("更新客户理财状态时参数无效")
            return False
        
        try:
            # 获取客户当前信息
            customer_info = self._get_customer_info(customer_id)
            if not customer_info:
                self.logger.warning(f"未找到客户信息，客户ID: {customer_id}")
                return False
            
            # 获取客户所有投资记录（按时间排序）
            investments = self._get_customer_investments(customer_id)
            
            # 检查操作类型（购买或赎回）
            is_purchase = 'purchase_amount' in investment_info and investment_info.get('wealth_status', '') == '持有'
            is_redemption = 'wealth_all_redeem_time' in investment_info and investment_info.get('wealth_all_redeem_time')
            
            # 需要更新的属性
            updates = {}
            
            # 1. 处理购买记录
            if is_purchase:
                # 获取产品信息
                product_id = investment_info.get('product_id')
                product_info = self._get_product_info(product_id)
                product_type = product_info.get('product_type', '未知')
                
                # 1.1 更新首次产品购买类型
                if not customer_info.get('firstpurchasetype'):
                    updates['firstpurchasetype'] = product_type
                    self.logger.debug(f"更新客户首次产品购买类型: {product_type}")
                
                # 1.2 更新是否曾持有财富产品标识
                updates['havewealth'] = '是'
                
                # 1.3 更新理财金额
                current_wealth_amount = float(customer_info.get('wealthamount', 0) or 0)
                purchase_amount = float(investment_info.get('purchase_amount', 0))
                updates['wealthamount'] = current_wealth_amount + purchase_amount
            
            # 2. 处理赎回记录
            if is_redemption:
                redemption_time = investment_info.get('wealth_all_redeem_time')
                if isinstance(redemption_time, (int, float)) and redemption_time > 1000000000000:  # 13位时间戳
                    redemption_date = datetime.datetime.fromtimestamp(redemption_time / 1000).date()
                else:
                    redemption_date = datetime.datetime.now().date()
                
                # 2.1 更新用户最近一次理财产品清仓日
                # 只有全部赎回且比当前记录的清仓日更新才更新
                if investment_info.get('wealth_status') == '完全赎回':
                    current_sell_date = self._parse_date(customer_info.get('sellwealthdate'))
                    
                    # 如果没有记录过清仓日期或新的清仓日期更晚
                    if not current_sell_date or redemption_date > current_sell_date:
                        updates['sellwealthdate'] = redemption_date.strftime('%Y-%m-%d')
                        self.logger.debug(f"更新客户最近一次理财产品清仓日: {redemption_date}")
                
                # 2.2 更新理财金额（减去赎回金额）
                current_wealth_amount = float(customer_info.get('wealthamount', 0) or 0)
                redemption_amount = float(investment_info.get('redemption_amount', 0))
                new_wealth_amount = max(0, current_wealth_amount - redemption_amount)
                updates['wealthamount'] = new_wealth_amount
                
                # 2.3 检查是否全部清仓（所有产品都已赎回）
                has_active_investments = any(
                    inv.get('wealth_status') in ['持有', '部分卖出']
                    for inv in investments
                    if inv.get('detail_id') != investment_info.get('detail_id')  # 排除当前记录
                )
                
                # 如果没有活跃投资且当前为完全赎回，更新用户最近一次清仓日期
                if not has_active_investments and investment_info.get('wealth_status') == '完全赎回':
                    updates['sellalldate'] = redemption_date.strftime('%Y-%m-%d')
                    self.logger.debug(f"更新客户最近一次清仓日: {redemption_date}")
            
            # 3. 更新财富客户阶段（不管是购买还是赎回都需要更新）
            
            # 获取当前财富阶段
            current_phase = customer_info.get('wealthcustomerphase', '')
            
            # 计算新的财富阶段
            new_phase = self._calculate_wealth_phase(customer_info, investments, investment_info)
            
            # 如果阶段有变化，更新
            if new_phase != current_phase:
                updates['wealthcustomerphase'] = new_phase
                self.logger.debug(f"更新客户财富阶段: {current_phase} -> {new_phase}")
            
            # 4. 更新资金未发生支用天数
            if is_purchase:
                # 购买行为重置未支用天数
                updates['nousedays'] = 0
            else:
                # 获取最近交易日期
                last_transaction_date = self._get_last_transaction_date(customer_id)
                if last_transaction_date:
                    today = datetime.datetime.now().date()
                    unused_days = (today - last_transaction_date).days
                    updates['nousedays'] = unused_days
            
            # 5. 执行数据库更新
            if updates:
                self._update_customer_info(customer_id, updates)
                self.logger.info(f"客户{customer_id}理财状态更新成功: {updates}")
                return True
            else:
                self.logger.debug(f"客户{customer_id}理财状态无需更新")
                return True
                
        except Exception as e:
            self.logger.error(f"更新客户理财状态时出错: {str(e)}")
            return False

    def _get_customer_info(self, customer_id):
        """
        获取客户信息
        
        Args:
            customer_id (str): 客户ID
            
        Returns:
            dict: 客户信息字典
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

    def _get_customer_investments(self, customer_id):
        """
        获取客户所有投资记录
        
        Args:
            customer_id (str): 客户ID
            
        Returns:
            list: 投资记录列表
        """
        try:
            query = """
            SELECT * FROM cdp_investment_order 
            WHERE base_id = %s 
            ORDER BY detail_time DESC
            """
            
            investments = self.db_manager.execute_query(query, (customer_id,))
            return investments
            
        except Exception as e:
            self.logger.error(f"获取客户投资记录时出错: {str(e)}")
            return []

    def _parse_date(self, date_str):
        """
        解析日期字符串为日期对象
        
        Args:
            date_str (str): 日期字符串
            
        Returns:
            datetime.date: 日期对象，无法解析则返回None
        """
        if not date_str:
            return None
        
        import datetime
        
        # 如果已经是日期对象
        if isinstance(date_str, datetime.date):
            return date_str
        
        # 如果是字符串
        if isinstance(date_str, str):
            try:
                return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                try:
                    return datetime.datetime.strptime(date_str, '%Y/%m/%d').date()
                except ValueError:
                    return None
        
        return None

    def _calculate_wealth_phase(self, customer_info, investments, current_investment=None):
        """
        计算客户财富阶段
        
        根据客户投资历史和当前交易，确定客户所处的财富阶段
        
        Args:
            customer_info (dict): 客户信息
            investments (list): 客户历史投资记录
            current_investment (dict, optional): 当前正在处理的投资记录
            
        Returns:
            str: 财富客户阶段（注册/首投/老客/召回/流失）
        """
        import datetime
        
        # 如果没有投资记录且当前不是购买交易，客户处于注册阶段
        if not investments and (not current_investment or 'purchase_amount' not in current_investment):
            # 检查注册时间，如果注册超过30天，视为流失客户
            registration_date = self._parse_date(customer_info.get('registration_date'))
            if registration_date:
                days_since_registration = (datetime.datetime.now().date() - registration_date).days
                if days_since_registration > 30:
                    return "流失"
            
            return "注册"
        
        # 如果只有一条投资记录，且是当前处理的记录，客户处于首投阶段
        if len(investments) == 1 and current_investment and 'purchase_amount' in current_investment:
            # 确认这条记录是否就是当前交易
            is_same_transaction = (
                investments[0].get('detail_id') == current_investment.get('detail_id') or
                investments[0].get('detail_time') == current_investment.get('detail_time')
            )
            
            if is_same_transaction:
                return "首投"
        
        # 检查是否所有投资都已赎回（全部清仓）
        all_redeemed = all(
            inv.get('wealth_status') == '完全赎回'
            for inv in investments
        )
        
        if all_redeemed:
            # 获取最近的赎回时间
            redemption_dates = [
                self._parse_timestamp(inv.get('wealth_all_redeem_time'))
                for inv in investments
                if inv.get('wealth_all_redeem_time')
            ]
            
            if redemption_dates:
                latest_redemption = max(redemption_dates)
                days_since_redemption = (datetime.datetime.now().date() - latest_redemption.date()).days
                
                # 根据清仓时间判断是召回还是流失
                if days_since_redemption <= 90:
                    return "召回"  # 90天内有过完全赎回，需要召回
                else:
                    return "流失"  # 超过90天无活动，视为流失
        
        # 其他情况视为老客户
        return "老客"

    def _parse_timestamp(self, timestamp):
        """
        解析时间戳为datetime对象
        
        Args:
            timestamp: 时间戳，可能是整数、浮点数或字符串
            
        Returns:
            datetime.datetime: 时间对象，无法解析则返回None
        """
        if not timestamp:
            return None
        
        import datetime
        
        # 如果已经是datetime对象
        if isinstance(timestamp, datetime.datetime):
            return timestamp
        
        # 如果是整数或浮点数时间戳
        if isinstance(timestamp, (int, float)):
            # 判断是秒级还是毫秒级时间戳
            if timestamp > 1000000000000:  # 13位毫秒级
                return datetime.datetime.fromtimestamp(timestamp / 1000)
            else:  # 10位秒级
                return datetime.datetime.fromtimestamp(timestamp)
        
        # 如果是字符串
        if isinstance(timestamp, str):
            try:
                # 尝试转换为数字
                num_timestamp = float(timestamp)
                return self._parse_timestamp(num_timestamp)
            except ValueError:
                # 尝试解析日期时间字符串
                formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d']
                for fmt in formats:
                    try:
                        return datetime.datetime.strptime(timestamp, fmt)
                    except ValueError:
                        continue
        
        return None

    def _get_last_transaction_date(self, customer_id):
        """
        获取客户最近一次交易日期
        
        Args:
            customer_id (str): 客户ID
            
        Returns:
            datetime.date: 最近交易日期，无交易则返回None
        """
        try:
            query = """
            SELECT detail_time 
            FROM cdp_account_flow 
            WHERE base_id = %s 
            ORDER BY detail_time DESC 
            LIMIT 1
            """
            
            results = self.db_manager.execute_query(query, (customer_id,))
            
            if results and len(results) > 0 and 'detail_time' in results[0]:
                timestamp = results[0]['detail_time']
                return self._parse_timestamp(timestamp).date()
            
            return None
            
        except Exception as e:
            self.logger.error(f"获取客户最后交易日期时出错: {str(e)}")
            return None

    def _update_customer_info(self, customer_id, updates):
        """
        更新客户信息
        
        Args:
            customer_id (str): 客户ID
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
            params.append(customer_id)  # WHERE条件参数
            
            # 构建更新语句
            update_query = f"""
            UPDATE cdp_customer_profile 
            SET {set_clause} 
            WHERE base_id = %s
            """
            
            # 执行更新
            result = self.db_manager.execute_update(update_query, params)
            
            return result
            
        except Exception as e:
            self.logger.error(f"更新客户信息时出错: {str(e)}")
            return False
