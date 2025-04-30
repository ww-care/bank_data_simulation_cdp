"""
理财相关事件生成器
生成与理财购买、赎回相关的客户行为事件
"""
import uuid
import json
import datetime
import random


class InvestmentEventGenerator:
    """理财相关事件生成器"""
    
    def __init__(self, db_manager, config_manager, logger):
        """初始化事件生成器"""
        self.db_manager = db_manager
        self.config = config_manager
        self.logger = logger
        
    def generate_purchase_events(self, investment_record):
        """
        生成购买事件
        
        为一次理财购买生成完整的事件链，包括浏览、点击、购买、结果等事件
        
        Args:
            investment_record (dict): 理财购买记录
            
        Returns:
            list: 生成的事件列表
        """
        import random
        import datetime
        import json
        
        # 验证输入参数
        if not investment_record:
            self.logger.warning("输入的投资记录为空，无法生成事件")
            return []
        
        # 获取基本信息
        customer_id = investment_record.get('base_id')
        product_id = investment_record.get('product_id')
        purchase_time = self._parse_timestamp(investment_record.get('detail_time'))
        purchase_amount = investment_record.get('purchase_amount', 0)
        purchase_channel = investment_record.get('channel', 'mobile_app')
        
        # 获取产品信息
        product_info = self._get_product_info(product_id)
        product_name = product_info.get('name', '未知产品')
        
        # 初始化事件列表
        events = []
        
        # 生成事件的时间范围：购买前3天到购买时
        current_time = purchase_time - datetime.timedelta(days=3)
        
        # 决定购买前的浏览次数（2-5次）
        view_count = random.randint(2, 5)
        
        # 记录已生成的事件时间，确保时间顺序
        event_times = []
        
        # 1. 生成产品列表浏览事件（1-2次）
        list_view_count = random.randint(1, 2)
        for _ in range(list_view_count):
            # 生成浏览时间（购买前1-3天随机）
            days_before = random.uniform(1, 3)
            view_time = purchase_time - datetime.timedelta(days=days_before)
            
            # 避免时间冲突
            while view_time in event_times:
                # 调整几分钟避开冲突
                view_time += datetime.timedelta(minutes=random.randint(5, 20))
            
            event_times.append(view_time)
            
            # 创建产品列表浏览事件
            list_view_event = {
                'event_id': f"EV{uuid.uuid4().hex[:10]}",
                'base_id': customer_id,
                'event': 'product_list_view_event',
                'event_time': int(view_time.timestamp() * 1000),  # 13位时间戳
                'event_property': json.dumps({
                    'view_duration_seconds': random.randint(30, 180),  # 浏览时长30秒-3分钟
                    'view_date': view_time.strftime('%Y-%m-%d'),
                    'page_name': '理财产品列表',
                    'filter_applied': random.choice([True, False]),
                    'sort_by': random.choice(['expected_yield', 'term', 'popularity', None]),
                    'entry_source': random.choice(['homepage_banner', 'menu_navigation', 'recommendation'])
                })
            }
            
            events.append(list_view_event)
        
        # 2. 生成产品点击事件（每次详情浏览前都有点击）
        click_count = view_count
        
        for i in range(click_count):
            # 生成点击时间（浏览之前的几分钟）
            days_before = random.uniform(0.5, 2.5)
            click_time = purchase_time - datetime.timedelta(days=days_before)
            
            # 避免时间冲突
            while click_time in event_times:
                click_time += datetime.timedelta(minutes=random.randint(2, 10))
            
            event_times.append(click_time)
            
            # 创建产品点击事件
            click_event = {
                'event_id': f"EV{uuid.uuid4().hex[:10]}",
                'base_id': customer_id,
                'event': 'weatlth_product_click_event',
                'event_time': int(click_time.timestamp() * 1000),
                'event_property': json.dumps({
                    'product_id': product_id,
                    'product_name': product_name,
                    'click_date': click_time.strftime('%Y-%m-%d'),
                    'page_source': random.choice(['product_list', 'recommendation', 'search_result']),
                    'position': random.randint(1, 10)  # 在列表中的位置
                })
            }
            
            events.append(click_event)
            
            # 3. 产品详情页浏览事件（点击后立即浏览）
            view_time = click_time + datetime.timedelta(seconds=random.randint(1, 3))
            event_times.append(view_time)
            
            # 浏览时长随时间推移增加，表示兴趣增加
            view_duration = random.uniform(30, 60)
            if i > 0:
                view_duration *= (1 + i * 0.3)  # 随着接近购买，浏览时间增加
            
            view_event = {
                'event_id': f"EV{uuid.uuid4().hex[:10]}",
                'base_id': customer_id,
                'event': 'product_detail_view_event',
                'event_time': int(view_time.timestamp() * 1000),
                'event_property': json.dumps({
                    'product_id': product_id,
                    'product_name': product_name,
                    'time_length': round(view_duration, 1),  # 浏览时长(分钟)
                    'review_date': view_time.strftime('%Y-%m-%d'),
                    'page_ip': self._generate_random_ip(),
                    'view_complete': random.random() > 0.2,  # 80%概率完整浏览
                    'tab_viewed': json.dumps(random.sample(['overview', 'details', 'history', 'risk', 'comments'], 
                                            random.randint(1, 5)))
                })
            }
            
            events.append(view_event)
        
        # 4. 购买前咨询事件（可选，30%概率发生）
        if random.random() < 0.3:
            # 咨询发生在最后一次浏览后，购买前
            consult_time = view_time + datetime.timedelta(minutes=random.randint(5, 30))
            
            # 避免时间冲突
            while consult_time in event_times:
                consult_time += datetime.timedelta(minutes=random.randint(5, 15))
            
            event_times.append(consult_time)
            
            consult_event = {
                'event_id': f"EV{uuid.uuid4().hex[:10]}",
                'base_id': customer_id,
                'event': 'product_consult_event',
                'event_time': int(consult_time.timestamp() * 1000),
                'event_property': json.dumps({
                    'product_id': product_id,
                    'product_name': product_name,
                    'consult_type': random.choice(['online_chat', 'phone_call', 'message']),
                    'consult_topic': random.choice(['risk', 'return', 'term', 'redemption', 'general']),
                    'duration_seconds': random.randint(60, 600),  # 1-10分钟咨询时长
                    'satisfaction': random.randint(3, 5)  # 满意度3-5
                })
            }
            
            events.append(consult_event)
        
        # 5. 购买提交事件
        # 购买提交发生在购买记录时间前几秒到几分钟
        submit_time = purchase_time - datetime.timedelta(seconds=random.randint(5, 300))
        
        # 避免时间冲突
        while submit_time in event_times:
            submit_time += datetime.timedelta(seconds=random.randint(10, 30))
        
        event_times.append(submit_time)
        
        submit_event = {
            'event_id': f"EV{uuid.uuid4().hex[:10]}",
            'base_id': customer_id,
            'event': 'product_purchase_submit_event',
            'event_time': int(submit_time.timestamp() * 1000),
            'event_property': json.dumps({
                'product_id': product_id,
                'product_name': product_name,
                'purchase_amount': purchase_amount,
                'channel': purchase_channel,
                'payment_method': random.choice(['balance', 'quick_payment', 'transfer']),
                'agreement_accepted': True
            })
        }
        
        events.append(submit_event)
        
        # 6. 购买结果事件
        result_time = purchase_time
        event_times.append(result_time)
        
        # 查询客户信息
        customer_info = self._get_customer_info(customer_id)
        is_first_purchase = self._is_first_purchase(customer_id, product_id, purchase_time)
        
        result_event = {
            'event_id': f"EV{uuid.uuid4().hex[:10]}",
            'base_id': customer_id,
            'event': 'product_purchase_result_event',
            'event_time': int(result_time.timestamp() * 1000),
            'event_property': json.dumps({
                'product_id': product_id,
                'product_name': product_name,
                'purchase_status': 'success',  # 假设都成功了，否则不会有投资记录
                'purchase_amount': purchase_amount,
                'product_term': investment_record.get('term', 0),
                'is_first_time_purchase': is_first_purchase,
                'transaction_id': investment_record.get('detail_id'),
                'expected_yield': investment_record.get('expected_return'),
                'completion_time_ms': random.randint(500, 3000)  # 交易完成时间
            })
        }
        
        events.append(result_event)
        
        # 7. 购买成功通知事件
        if random.random() < 0.95:  # 95%概率收到通知
            notify_time = result_time + datetime.timedelta(seconds=random.randint(1, 5))
            event_times.append(notify_time)
            
            notify_event = {
                'event_id': f"EV{uuid.uuid4().hex[:10]}",
                'base_id': customer_id,
                'event': 'purchase_success_notification_event',
                'event_time': int(notify_time.timestamp() * 1000),
                'event_property': json.dumps({
                    'product_id': product_id,
                    'product_name': product_name,
                    'purchase_amount': purchase_amount,
                    'notification_type': random.choice(['push', 'sms', 'app_message']),
                    'notification_status': 'delivered',
                    'notification_read': random.choice([True, False])
                })
            }
            
            events.append(notify_event)
        
        # 排序事件，确保时间顺序
        events.sort(key=lambda x: x['event_time'])
        
        self.logger.debug(f"为投资记录 {investment_record.get('detail_id')} 生成了 {len(events)} 个事件")
        
        return events

    def _parse_timestamp(self, timestamp):
        """
        解析时间戳为datetime对象
        
        Args:
            timestamp: 时间戳，可能是13位毫秒时间戳或其他格式
            
        Returns:
            datetime.datetime: 解析后的时间
        """
        import datetime
        
        if not timestamp:
            return datetime.datetime.now()
        
        # 如果已经是datetime对象，直接返回
        if isinstance(timestamp, datetime.datetime):
            return timestamp
        
        # 处理13位毫秒级时间戳
        if isinstance(timestamp, (int, float)) and timestamp > 1000000000000:
            return datetime.datetime.fromtimestamp(timestamp / 1000)
        
        # 处理10位秒级时间戳
        if isinstance(timestamp, (int, float)):
            return datetime.datetime.fromtimestamp(timestamp)
        
        # 处理字符串格式
        if isinstance(timestamp, str):
            try:
                # 尝试解析ISO格式
                return datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                try:
                    # 尝试解析常见格式
                    return datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                except:
                    try:
                        # 尝试只有日期的格式
                        return datetime.datetime.strptime(timestamp, '%Y-%m-%d')
                    except:
                        self.logger.error(f"无法解析时间戳: {timestamp}")
                        return datetime.datetime.now()
        
        # 默认返回当前时间
        return datetime.datetime.now()

    def _generate_random_ip(self):
        """
        生成随机IP地址
        
        Returns:
            str: 随机IP地址
        """
        import random
        
        # 优先生成常见IP段
        if random.random() < 0.8:
            return f"192.168.{random.randint(0, 255)}.{random.randint(1, 254)}"
        else:
            return f"{random.randint(1, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"

    def _get_product_info(self, product_id):
        """
        获取产品信息
        
        Args:
            product_id (str): 产品ID
            
        Returns:
            dict: 产品信息
        """
        try:
            if not product_id:
                return {'name': '未知产品'}
            
            query = "SELECT * FROM cdp_product_archive WHERE base_id = %s"
            results = self.db_manager.execute_query(query, (product_id,))
            
            if results:
                return results[0]
            
            return {'name': '未知产品'}
            
        except Exception as e:
            self.logger.error(f"获取产品信息时出错: {str(e)}")
            return {'name': '未知产品'}

    def _get_customer_info(self, customer_id):
        """
        获取客户信息
        
        Args:
            customer_id (str): 客户ID
            
        Returns:
            dict: 客户信息
        """
        try:
            if not customer_id:
                return {}
            
            query = "SELECT * FROM cdp_customer_profile WHERE base_id = %s"
            results = self.db_manager.execute_query(query, (customer_id,))
            
            if results:
                return results[0]
            
            return {}
            
        except Exception as e:
            self.logger.error(f"获取客户信息时出错: {str(e)}")
            return {}

    def _is_first_purchase(self, customer_id, product_id, purchase_time):
        """
        检查是否是客户首次购买产品
        
        Args:
            customer_id (str): 客户ID
            product_id (str): 产品ID
            purchase_time (datetime.datetime): 购买时间
            
        Returns:
            bool: 是否首次购买
        """
        try:
            # 转换时间为时间戳
            purchase_timestamp = int(purchase_time.timestamp() * 1000)
            
            # 查询之前的购买记录
            query = """
            SELECT COUNT(*) as count 
            FROM cdp_investment_order 
            WHERE base_id = %s AND detail_time < %s
            """
            
            results = self.db_manager.execute_query(query, (customer_id, purchase_timestamp))
            
            if results and results[0]['count'] == 0:
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"检查首次购买时出错: {str(e)}")
            return False
        
    def generate_purchase_result_event(self, investment_record):
        """
        生成购买结果事件
        
        根据理财购买记录生成购买结果事件，记录交易成功与否、金额、产品信息等
        
        Args:
            investment_record (dict): 理财购买记录
            
        Returns:
            dict: 生成的购买结果事件
        """
        import json
        import uuid
        
        # 验证输入参数
        if not investment_record:
            self.logger.warning("输入的投资记录为空，无法生成购买结果事件")
            return None
        
        # 获取基本信息
        customer_id = investment_record.get('base_id')
        product_id = investment_record.get('product_id')
        purchase_time = investment_record.get('detail_time')
        purchase_amount = investment_record.get('purchase_amount', 0)
        transaction_id = investment_record.get('detail_id')
        
        # 获取产品信息
        product_info = self._get_product_info(product_id)
        product_name = product_info.get('name', '未知产品')
        
        # 获取客户信息
        customer_info = self._get_customer_info(customer_id)
        
        # 检查是否首次购买
        is_first_purchase = self._is_first_purchase(customer_id, product_id, self._parse_timestamp(purchase_time))
        
        # 创建事件ID
        event_id = f"EV{uuid.uuid4().hex[:10]}"
        
        # 构建事件属性
        event_properties = {
            'product_id': product_id,
            'product_name': product_name,
            'purchase_status': investment_record.get('status', '成功'),  # 假设都成功了，否则不会有投资记录
            'purchase_amount': purchase_amount,
            'product_term': investment_record.get('term', 0),
            'is_first_time_purchase': is_first_purchase,
            'transaction_id': transaction_id,
            'expected_yield': investment_record.get('expected_return', 0),
            'completion_time_ms': self._generate_random_processing_time(500, 3000)  # 交易完成时间
        }
        
        # 添加产品特定信息
        if product_info:
            event_properties['product_type'] = product_info.get('product_type', '')
            event_properties['risk_level'] = product_info.get('risk_level', '')
            event_properties['redemption_way'] = product_info.get('redemption_way', '')
        
        # 添加渠道信息
        event_properties['channel'] = investment_record.get('channel', 'mobile_app')
        
        # 添加支付方式信息（随机生成）
        event_properties['payment_method'] = self._generate_payment_method()
        
        # 创建购买结果事件
        purchase_result_event = {
            'event_id': event_id,
            'base_id': customer_id,
            'event': 'product_purchase_result_event',
            'event_time': purchase_time,  # 使用购买时间作为事件时间
            'event_property': json.dumps(event_properties)
        }
        
        try:
            # 保存事件到数据库
            self._save_event(purchase_result_event)
            self.logger.debug(f"生成购买结果事件成功: {event_id}, 客户: {customer_id}, 产品: {product_id}")
            return purchase_result_event
        except Exception as e:
            self.logger.error(f"保存购买结果事件时出错: {str(e)}")
            return None

    def generate_product_click_events(self, customer_id, product_id, purchase_date, count=1):
        """
        生成产品点击事件
        
        模拟客户在购买前点击产品的行为，可以生成单个或多个点击事件
        
        Args:
            customer_id (str): 客户ID
            product_id (str): 产品ID
            purchase_date (datetime.date): 购买日期，点击事件将生成在该日期之前
            count (int, optional): 生成的点击事件数量，默认为1
            
        Returns:
            list: 生成的点击事件列表
        """
        import json
        import uuid
        import random
        import datetime
        
        # 验证输入参数
        if not customer_id or not product_id or not purchase_date:
            self.logger.warning("生成产品点击事件的参数无效")
            return []
        
        # 确保count合法
        count = max(1, min(count, 10))  # 限制在1-10之间
        
        # 获取产品信息
        product_info = self._get_product_info(product_id)
        if not product_info:
            self.logger.warning(f"未找到产品信息，产品ID: {product_id}")
            return []
        
        product_name = product_info.get('name', '未知产品')
        
        # 将购买日期转换为datetime对象（如果是date类型）
        if isinstance(purchase_date, datetime.date) and not isinstance(purchase_date, datetime.datetime):
            purchase_date = datetime.datetime.combine(purchase_date, datetime.time(0, 0))
        
        # 生成点击事件列表
        click_events = []
        
        for i in range(count):
            # 生成点击时间（购买前0.5-3天之间的随机时间）
            days_before = random.uniform(0.5, 3.0)
            hours_variation = random.uniform(-4, 4)  # 小时级别的随机变化
            
            click_time = purchase_date - datetime.timedelta(days=days_before) + datetime.timedelta(hours=hours_variation)
            
            # 确保时间在合理范围（上午9点到晚上10点之间）
            while click_time.hour < 9 or click_time.hour > 22:
                # 调整到合理时间段
                if click_time.hour < 9:
                    click_time = click_time.replace(hour=9 + random.randint(0, 3))
                else:
                    click_time = click_time.replace(hour=19 + random.randint(0, 3))
            
            # 创建事件ID
            event_id = f"EV{uuid.uuid4().hex[:10]}"
            
            # 构建事件属性
            event_properties = {
                'product_id': product_id,
                'product_name': product_name,
                'click_date': click_time.strftime('%Y-%m-%d'),
                'page_source': random.choice(['product_list', 'recommendation', 'search_result', 'banner']),
                'position': random.randint(1, 10),  # 在列表中的位置
                'device_type': random.choice(['mobile', 'tablet', 'pc']),
                'session_id': f"SES{uuid.uuid4().hex[:8]}"
            }
            
            # 创建点击事件
            click_event = {
                'event_id': event_id,
                'base_id': customer_id,
                'event': 'weatlth_product_click_event',
                'event_time': int(click_time.timestamp() * 1000),  # 转换为13位时间戳
                'event_property': json.dumps(event_properties)
            }
            
            # 添加到列表
            click_events.append(click_event)
        
        try:
            # 批量保存事件到数据库
            for event in click_events:
                self._save_event(event)
            
            self.logger.debug(f"生成 {count} 条产品点击事件成功，客户: {customer_id}, 产品: {product_id}")
            return click_events
        except Exception as e:
            self.logger.error(f"保存产品点击事件时出错: {str(e)}")
            return []

    def generate_product_detail_view_events(self, customer_id, product_id, purchase_date, count=1):
        """
        生成产品详情页浏览事件
        
        模拟客户在购买前浏览产品详情页的行为，记录浏览时长、浏览页面等信息
        
        Args:
            customer_id (str): 客户ID
            product_id (str): 产品ID
            purchase_date (datetime.date): 购买日期，浏览事件将生成在该日期之前
            count (int, optional): 生成的浏览事件数量，默认为1
            
        Returns:
            list: 生成的产品详情页浏览事件列表
        """
        import json
        import uuid
        import random
        import datetime
        
        # 验证输入参数
        if not customer_id or not product_id or not purchase_date:
            self.logger.warning("生成产品详情页浏览事件的参数无效")
            return []
        
        # 确保count合法
        count = max(1, min(count, 5))  # 限制在1-5之间
        
        # 获取产品信息
        product_info = self._get_product_info(product_id)
        if not product_info:
            self.logger.warning(f"未找到产品信息，产品ID: {product_id}")
            return []
        
        product_name = product_info.get('name', '未知产品')
        
        # 将购买日期转换为datetime对象（如果是date类型）
        if isinstance(purchase_date, datetime.date) and not isinstance(purchase_date, datetime.datetime):
            purchase_date = datetime.datetime.combine(purchase_date, datetime.time(0, 0))
        
        # 生成详情页浏览事件列表
        view_events = []
        
        for i in range(count):
            # 浏览时间应该在点击后、购买前
            # 随着接近购买，浏览时间和深度会增加
            days_before = random.uniform(0.3, 2.5) - (i * 0.3)  # 随着循环增加，天数减少（更接近购买时间）
            days_before = max(0.1, days_before)  # 确保至少在购买前的0.1天
            hours_variation = random.uniform(-3, 3)  # 小时级别的随机变化
            
            view_time = purchase_date - datetime.timedelta(days=days_before) + datetime.timedelta(hours=hours_variation)
            
            # 确保时间在合理范围（上午9点到晚上10点之间）
            while view_time.hour < 9 or view_time.hour > 22:
                # 调整到合理时间段
                if view_time.hour < 9:
                    view_time = view_time.replace(hour=9 + random.randint(0, 3))
                else:
                    view_time = view_time.replace(hour=19 + random.randint(0, 3))
            
            # 浏览时长随接近购买时间增加（1-15分钟）
            view_duration = random.uniform(1, 5) + (i * 2)  # 随着循环增加，时长增加
            
            # 创建事件ID
            event_id = f"EV{uuid.uuid4().hex[:10]}"
            
            # 构建事件属性
            event_properties = {
                'product_id': product_id,
                'product_name': product_name,
                'time_length': round(view_duration, 1),  # 浏览时长(分钟)
                'review_date': view_time.strftime('%Y-%m-%d'),
                'page_ip': self._generate_random_ip(),
                'view_complete': random.random() > 0.2,  # 80%概率完整浏览
                'tab_viewed': json.dumps(random.sample(
                    ['overview', 'details', 'history', 'risk', 'comments', 'returns'], 
                    random.randint(1, min(i+1, 5))  # 随着循环增加，浏览的标签也增加
                )),
                'device_type': random.choice(['mobile', 'tablet', 'pc']),
                'session_id': f"SES{uuid.uuid4().hex[:8]}",
                'from_page': random.choice(['product_list', 'search_result', 'recommendation', 'banner'])
            }
            
            # 添加产品特定信息
            if product_info:
                event_properties['product_type'] = product_info.get('product_type', '')
                event_properties['risk_level'] = product_info.get('risk_level', '')
                event_properties['expected_yield'] = product_info.get('expected_yield', '')
            
            # 创建详情页浏览事件
            view_event = {
                'event_id': event_id,
                'base_id': customer_id,
                'event': 'product_detail_view_event',
                'event_time': int(view_time.timestamp() * 1000),  # 转换为13位时间戳
                'event_property': json.dumps(event_properties)
            }
            
            # 添加到列表
            view_events.append(view_event)
        
        try:
            # 批量保存事件到数据库
            for event in view_events:
                self._save_event(event)
            
            self.logger.debug(f"生成 {count} 条产品详情页浏览事件成功，客户: {customer_id}, 产品: {product_id}")
            return view_events
        except Exception as e:
            self.logger.error(f"保存产品详情页浏览事件时出错: {str(e)}")
            return []

    def _generate_random_processing_time(self, min_time=500, max_time=3000):
        """
        生成随机处理时间（毫秒）
        
        Args:
            min_time (int): 最小处理时间（毫秒）
            max_time (int): 最大处理时间（毫秒）
            
        Returns:
            int: 生成的处理时间
        """
        import random
        return random.randint(min_time, max_time)

    def _generate_payment_method(self):
        """
        生成随机支付方式
        
        Returns:
            str: 支付方式
        """
        import random
        payment_methods = ['balance', 'quick_payment', 'transfer', 'deposit_deduction']
        weights = [0.7, 0.15, 0.1, 0.05]  # 各支付方式的权重
        
        return random.choices(payment_methods, weights=weights, k=1)[0]

    def _save_event(self, event):
        """
        保存事件到数据库
        
        Args:
            event (dict): 事件数据
            
        Returns:
            bool: 保存是否成功
        """
        try:
            # 构建插入SQL
            fields = ', '.join(event.keys())
            placeholders = ', '.join(['%s'] * len(event))
            
            insert_query = f"""
            INSERT INTO cdp_customer_event ({fields})
            VALUES ({placeholders})
            """
            
            # 执行插入
            self.db_manager.execute_update(insert_query, list(event.values()))
            
            return True
            
        except Exception as e:
            self.logger.error(f"保存事件到数据库时出错: {str(e)}")
            raise
        
    def generate_product_click_events(self, customer_id, product_id, purchase_date):
        """生成产品点击事件"""
        # TODO: 实现产品点击事件生成逻辑
        pass
        
    def generate_product_detail_view_events(self, customer_id, product_id, purchase_date):
        """生成产品详情页浏览事件"""
        # TODO: 实现产品详情页浏览事件生成逻辑
        pass
        
    def generate_redemption_events(self, redemption_record):
        """
        生成赎回相关事件
        
        为一次理财赎回生成完整的事件链，包括查询、赎回操作、结果通知等事件
        
        Args:
            redemption_record (dict): 赎回记录
            
        Returns:
            list: 生成的事件列表
        """
        import random
        import datetime
        import json
        import uuid
        
        # 验证输入参数
        if not redemption_record:
            self.logger.warning("输入的赎回记录为空，无法生成事件")
            return []
        
        # 获取基本信息
        customer_id = redemption_record.get('customer_id')
        product_id = redemption_record.get('product_id')
        investment_id = redemption_record.get('investment_id')
        redemption_time = self._parse_timestamp(redemption_record.get('redemption_timestamp'))
        redemption_amount = redemption_record.get('redemption_amount', 0)
        is_full_redemption = redemption_record.get('is_full_redemption', True)
        redemption_type = redemption_record.get('redemption_type', 'early')  # early或maturity
        channel = redemption_record.get('channel', 'mobile_app')
        
        # 获取产品信息
        product_info = self._get_product_info(product_id)
        product_name = product_info.get('name', '未知产品')
        
        # 获取投资信息
        investment_info = self._get_investment_info(investment_id)
        
        # 初始化事件列表
        events = []
        
        # 记录已生成的事件时间，确保时间顺序
        event_times = []
        
        # 赎回事件前的行为特征取决于赎回类型
        if redemption_type == 'maturity':
            # 到期赎回：通常有到期提醒，查看产品状态，然后赎回
            # 这些事件由generate_due_notification_events单独处理
            pass
        else:
            # 提前赎回：通常会先查询持仓，查看产品页面，然后决定赎回
            
            # 1. 持仓查询事件（90%概率发生）
            if random.random() < 0.9:
                # 查询发生在赎回前几小时到1天内
                query_time = redemption_time - datetime.timedelta(hours=random.randint(1, 24))
                event_times.append(query_time)
                
                portfolio_query_event = {
                    'event_id': f"EV{uuid.uuid4().hex[:10]}",
                    'base_id': customer_id,
                    'event': 'portfolio_query_event',
                    'event_time': int(query_time.timestamp() * 1000),
                    'event_property': json.dumps({
                        'query_type': 'investment_holding',
                        'query_filter': random.choice(['all', 'active', product_id]),
                        'query_duration_seconds': random.randint(5, 60),
                        'sort_by': random.choice(['purchase_date', 'product_name', 'amount', None]),
                        'app_page': 'my_investments'
                    })
                }
                
                events.append(portfolio_query_event)
            
            # 2. 产品详情查看事件（70%概率发生）
            if random.random() < 0.7:
                # 详情查看发生在持仓查询后，赎回前
                if event_times:
                    detail_time = event_times[-1] + datetime.timedelta(minutes=random.randint(2, 30))
                else:
                    detail_time = redemption_time - datetime.timedelta(hours=random.randint(1, 12))
                
                # 避免时间冲突
                while detail_time in event_times:
                    detail_time += datetime.timedelta(minutes=random.randint(2, 10))
                
                event_times.append(detail_time)
                
                detail_view_event = {
                    'event_id': f"EV{uuid.uuid4().hex[:10]}",
                    'base_id': customer_id,
                    'event': 'product_detail_view_event',
                    'event_time': int(detail_time.timestamp() * 1000),
                    'event_property': json.dumps({
                        'product_id': product_id,
                        'product_name': product_name,
                        'time_length': random.randint(1, 10),  # 浏览时长(分钟)
                        'review_date': detail_time.strftime('%Y-%m-%d'),
                        'page_ip': self._generate_random_ip(),
                        'view_section': 'redemption_info',
                        'from_portfolio': True
                    })
                }
                
                events.append(detail_view_event)
            
            # 3. 收益计算事件（50%概率发生）
            if random.random() < 0.5:
                # 收益计算发生在详情查看后，赎回前
                if event_times:
                    calc_time = event_times[-1] + datetime.timedelta(minutes=random.randint(1, 15))
                else:
                    calc_time = redemption_time - datetime.timedelta(hours=random.randint(0, 6))
                
                # 避免时间冲突
                while calc_time in event_times:
                    calc_time += datetime.timedelta(minutes=random.randint(1, 5))
                
                event_times.append(calc_time)
                
                # 计算预期收益
                hold_days = (calc_time.date() - self._parse_timestamp(investment_info.get('purchase_time')).date()).days
                expected_yield = investment_info.get('expected_return', 0.04)
                principal = investment_info.get('purchase_amount', 10000)
                expected_interest = principal * expected_yield * (hold_days / 365)
                
                calc_event = {
                    'event_id': f"EV{uuid.uuid4().hex[:10]}",
                    'base_id': customer_id,
                    'event': 'investment_return_calculation_event',
                    'event_time': int(calc_time.timestamp() * 1000),
                    'event_property': json.dumps({
                        'product_id': product_id,
                        'investment_id': investment_id,
                        'hold_days': hold_days,
                        'principal': principal,
                        'expected_interest': round(expected_interest, 2),
                        'total_return': round(principal + expected_interest, 2),
                        'calculation_type': 'redemption_preview'
                    })
                }
                
                events.append(calc_event)
        
        # 4. 赎回提交事件（必定发生）
        # 赎回提交发生在赎回记录时间前几秒到几分钟
        submit_time = redemption_time - datetime.timedelta(seconds=random.randint(5, 300))
        
        # 避免时间冲突
        while submit_time in event_times:
            submit_time += datetime.timedelta(seconds=random.randint(10, 30))
        
        event_times.append(submit_time)
        
        submit_event = {
            'event_id': f"EV{uuid.uuid4().hex[:10]}",
            'base_id': customer_id,
            'event': 'product_redeem_submit_event',
            'event_time': int(submit_time.timestamp() * 1000),
            'event_property': json.dumps({
                'product_id': product_id,
                'product_name': product_name,
                'investment_id': investment_id,
                'redeem_amount': redemption_amount,
                'is_redeem_all': is_full_redemption,
                'channel': channel,
                'redemption_type': redemption_type,
                'agreement_accepted': True,
                'confirmation_required': redemption_amount > 10000  # 大额赎回需要二次确认
            })
        }
        
        events.append(submit_event)
        
        # 5. 大额赎回确认事件（针对大额赎回）
        if redemption_amount > 10000 and random.random() < 0.95:  # 95%概率进行确认
            confirm_time = submit_time + datetime.timedelta(seconds=random.randint(3, 30))
            event_times.append(confirm_time)
            
            confirm_event = {
                'event_id': f"EV{uuid.uuid4().hex[:10]}",
                'base_id': customer_id,
                'event': 'large_redemption_confirm_event',
                'event_time': int(confirm_time.timestamp() * 1000),
                'event_property': json.dumps({
                    'investment_id': investment_id,
                    'product_id': product_id,
                    'redeem_amount': redemption_amount,
                    'confirmation_type': random.choice(['sms_code', 'password', 'face_id']),
                    'attempt_count': random.choices([1, 2, 3], weights=[0.85, 0.1, 0.05], k=1)[0],
                    'confirmation_result': 'success'
                })
            }
            
            events.append(confirm_event)
        
        # 6. 赎回结果事件
        result_time = redemption_time
        event_times.append(result_time)
        
        result_event = {
            'event_id': f"EV{uuid.uuid4().hex[:10]}",
            'base_id': customer_id,
            'event': 'product_redeem_event',
            'event_time': int(result_time.timestamp() * 1000),
            'event_property': json.dumps({
                'product_id': product_id,
                'product_name': product_name,
                'investment_id': investment_id,
                'redeem_status': 'success',  # 假设都成功了
                'redeem_amount': redemption_amount,
                'is_redeem_all': is_full_redemption,
                'hold_days': (redemption_time.date() - self._parse_timestamp(investment_info.get('purchase_time')).date()).days,
                'transaction_id': f"RED{uuid.uuid4().hex[:8]}",
                'completion_time_ms': random.randint(500, 3000)  # 交易完成时间
            })
        }
        
        events.append(result_event)
        
        # 7. 赎回成功通知事件
        if random.random() < 0.95:  # 95%概率收到通知
            notify_time = result_time + datetime.timedelta(seconds=random.randint(1, 5))
            event_times.append(notify_time)
            
            notify_event = {
                'event_id': f"EV{uuid.uuid4().hex[:10]}",
                'base_id': customer_id,
                'event': 'redemption_success_notification_event',
                'event_time': int(notify_time.timestamp() * 1000),
                'event_property': json.dumps({
                    'product_id': product_id,
                    'product_name': product_name,
                    'redemption_amount': redemption_amount,
                    'notification_type': random.choice(['push', 'sms', 'app_message']),
                    'notification_status': 'delivered',
                    'expected_arrival_date': (notify_time + datetime.timedelta(days=random.randint(1, 3))).strftime('%Y-%m-%d'),
                    'notification_read': random.choice([True, False])
                })
            }
            
            events.append(notify_event)
        
        # 8. 资金到账通知事件（延迟1-3天发生）
        if random.random() < 0.9:  # 90%概率发生
            arrival_days = random.randint(1, 3)
            arrival_time = result_time + datetime.timedelta(days=arrival_days)
            
            arrival_event = {
                'event_id': f"EV{uuid.uuid4().hex[:10]}",
                'base_id': customer_id,
                'event': 'redemption_fund_arrival_event',
                'event_time': int(arrival_time.timestamp() * 1000),
                'event_property': json.dumps({
                    'product_id': product_id,
                    'product_name': product_name,
                    'redemption_amount': redemption_amount,
                    'arrival_account': self._get_customer_account(customer_id),
                    'transaction_reference': f"TR{uuid.uuid4().hex[:8]}",
                    'days_after_redemption': arrival_days,
                    'notification_sent': True
                })
            }
            
            events.append(arrival_event)
        
        # 排序事件，确保时间顺序
        events.sort(key=lambda x: x['event_time'])
        
        self.logger.debug(f"为赎回记录生成了 {len(events)} 个事件")
        
        return events

    def _get_investment_info(self, investment_id):
        """
        获取投资记录信息
        
        Args:
            investment_id (str): 投资记录ID
            
        Returns:
            dict: 投资记录信息
        """
        try:
            if not investment_id:
                return {}
            
            query = "SELECT * FROM cdp_investment_order WHERE detail_id = %s"
            results = self.db_manager.execute_query(query, (investment_id,))
            
            if results:
                return results[0]
            
            return {}
            
        except Exception as e:
            self.logger.error(f"获取投资记录信息时出错: {str(e)}")
            return {}

    def _get_customer_account(self, customer_id):
        """
        获取客户资金账户
        
        Args:
            customer_id (str): 客户ID
            
        Returns:
            str: 账户ID
        """
        try:
            if not customer_id:
                return ""
            
            query = """
            SELECT base_id 
            FROM cdp_account_archive 
            WHERE customer_id = %s AND status = 'active'
            ORDER BY balance DESC
            LIMIT 1
            """
            
            results = self.db_manager.execute_query(query, (customer_id,))
            
            if results:
                return results[0]['base_id']
            
            return ""
            
        except Exception as e:
            self.logger.error(f"获取客户账户时出错: {str(e)}")
            return ""
        
    def generate_due_notification_events(self, investment, due_date):
        """
        生成产品到期提醒事件
        
        Args:
            investment (dict): 投资记录信息
            due_date (datetime.date): 到期日期
            
        Returns:
            list: 生成的事件列表
        """
        import random
        import datetime
        import json
        import uuid
        
        # 验证输入参数
        if not investment or not due_date:
            self.logger.warning("投资记录或到期日期为空，无法生成到期提醒事件")
            return []
        
        # 获取基本信息
        customer_id = investment.get('base_id')
        product_id = investment.get('product_id')
        investment_id = investment.get('detail_id')
        purchase_amount = investment.get('purchase_amount', 0)
        hold_amount = investment.get('hold_amount', 0)
        
        # 如果已经全部赎回，不生成到期提醒
        if hold_amount <= 0:
            self.logger.debug(f"投资 {investment_id} 已全部赎回，跳过到期提醒")
            return []
        
        # 获取产品信息
        product_info = self._get_product_info(product_id)
        product_name = product_info.get('name', '未知产品')
        
        # 获取客户信息
        customer_info = self._get_customer_info(customer_id)
        
        # 初始化事件列表
        events = []
        
        # 确保due_date是日期对象
        if isinstance(due_date, str):
            due_date = datetime.datetime.strptime(due_date, '%Y-%m-%d').date()
        if isinstance(due_date, datetime.datetime):
            due_date = due_date.date()
        
        # 1. 提前通知事件（通常在到期前7天、3天和1天发送）
        advance_days = [7, 3, 1]
        
        for days in advance_days:
            # 计算通知日期
            notify_date = due_date - datetime.timedelta(days=days)
            
            # 如果通知日期已经过去，跳过
            today = datetime.date.today()
            if notify_date < today:
                continue
            
            # 生成通知时间（工作时间内的随机时间点）
            hour = random.randint(9, 17)
            minute = random.randint(0, 59)
            notify_time = datetime.datetime.combine(notify_date, datetime.time(hour, minute))
            
            # 生成到期提醒事件
            due_notification_event = {
                'event_id': f"EV{uuid.uuid4().hex[:10]}",
                'base_id': customer_id,
                'event': 'financial_product_due_event',
                'event_time': int(notify_time.timestamp() * 1000),
                'event_property': json.dumps({
                    'product_id': product_id,
                    'product_name': product_name,
                    'investment_id': investment_id,
                    'expire_date': due_date.strftime('%Y-%m-%d'),
                    'days_to_expiry': days,
                    'notification_status': 'sent',
                    'notification_type': self._get_notification_type(customer_info, days),
                    'remaining_amount': hold_amount,
                    'redemption_options': self._get_redemption_options(product_info)
                })
            }
            
            events.append(due_notification_event)
            
            # 2. 通知阅读事件（70%-90%的概率发生，随到期越近概率越高）
            read_probability = 0.7 + (7 - days) * 0.03  # 1天前90%，3天前80%，7天前70%
            
            if random.random() < read_probability:
                # 生成阅读时间（通知后0-12小时内）
                read_delay_hours = random.uniform(0.1, 12)
                read_time = notify_time + datetime.timedelta(hours=read_delay_hours)
                
                notification_read_event = {
                    'event_id': f"EV{uuid.uuid4().hex[:10]}",
                    'base_id': customer_id,
                    'event': 'notification_read_event',
                    'event_time': int(read_time.timestamp() * 1000),
                    'event_property': json.dumps({
                        'notification_id': due_notification_event['event_id'],
                        'product_id': product_id,
                        'notification_type': 'product_due',
                        'read_delay_minutes': int(read_delay_hours * 60),
                        'device_type': random.choice(['mobile', 'pc', 'tablet']),
                        'app_version': f"{random.randint(3, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
                    })
                }
                
                events.append(notification_read_event)
                
                # 3. 到期详情查看事件（阅读通知后60%的概率查看详情）
                if random.random() < 0.6:
                    # 生成查看时间（阅读后0-60分钟内）
                    view_delay_minutes = random.uniform(0.5, 60)
                    view_time = read_time + datetime.timedelta(minutes=view_delay_minutes)
                    
                    detail_view_event = {
                        'event_id': f"EV{uuid.uuid4().hex[:10]}",
                        'base_id': customer_id,
                        'event': 'product_detail_view_event',
                        'event_time': int(view_time.timestamp() * 1000),
                        'event_property': json.dumps({
                            'product_id': product_id,
                            'product_name': product_name,
                            'time_length': random.randint(1, 10),  # 浏览时长(分钟)
                            'review_date': view_time.strftime('%Y-%m-%d'),
                            'page_ip': self._generate_random_ip(),
                            'view_section': 'redemption_info',
                            'from_notification': True,
                            'due_date': due_date.strftime('%Y-%m-%d'),
                            'days_to_expiry': days
                        })
                    }
                    
                    events.append(detail_view_event)
                    
                    # 4. 再投资查询事件（详情查看后30%的概率查询再投资选项）
                    if random.random() < 0.3 and days <= 3:  # 只在临近到期时查询再投资
                        # 生成查询时间（详情查看后0-30分钟内）
                        query_delay_minutes = random.uniform(1, 30)
                        query_time = view_time + datetime.timedelta(minutes=query_delay_minutes)
                        
                        reinvest_query_event = {
                            'event_id': f"EV{uuid.uuid4().hex[:10]}",
                            'base_id': customer_id,
                            'event': 'reinvestment_options_query_event',
                            'event_time': int(query_time.timestamp() * 1000),
                            'event_property': json.dumps({
                                'product_id': product_id,
                                'investment_id': investment_id,
                                'current_amount': hold_amount,
                                'due_date': due_date.strftime('%Y-%m-%d'),
                                'category_filter': random.choice(['same_category', 'same_risk', 'recommended', None]),
                                'sort_by': random.choice(['yield', 'term', 'popularity', None])
                            })
                        }
                        
                        events.append(reinvest_query_event)
        
        # 5. 到期当天特殊提醒事件
        if due_date >= today:
            # 生成到期当天的提醒时间（上午9-10点）
            due_hour = random.randint(9, 10)
            due_minute = random.randint(0, 59)
            due_notify_time = datetime.datetime.combine(due_date, datetime.time(due_hour, due_minute))
            
            due_day_event = {
                'event_id': f"EV{uuid.uuid4().hex[:10]}",
                'base_id': customer_id,
                'event': 'product_maturity_event',
                'event_time': int(due_notify_time.timestamp() * 1000),
                'event_property': json.dumps({
                    'product_id': product_id,
                    'product_name': product_name,
                    'investment_id': investment_id,
                    'maturity_date': due_date.strftime('%Y-%m-%d'),
                    'initial_amount': purchase_amount,
                    'final_amount': hold_amount,
                    'expected_interest': round(hold_amount * product_info.get('expected_yield', 0.04) * 
                                            (investment.get('term', 0) / 365), 2),
                    'redemption_type': 'auto' if product_info.get('redemption_way') == '固定赎回' else 'manual',
                    'fund_arrival_expected': (due_date + datetime.timedelta(days=random.randint(1, 3))).strftime('%Y-%m-%d')
                })
            }
            
            events.append(due_day_event)
        
        # 排序事件，确保时间顺序
        events.sort(key=lambda x: x['event_time'])
        
        self.logger.debug(f"为投资 {investment_id} 的到期日 {due_date} 生成了 {len(events)} 个提醒事件")
        
        return events

    def _get_notification_type(self, customer_info, days_to_expiry):
        """
        根据客户信息和到期天数确定通知类型
        
        Args:
            customer_info (dict): 客户信息
            days_to_expiry (int): 距离到期的天数
            
        Returns:
            str: 通知类型
        """
        import random
        
        # 获取客户是否有APP
        has_app = self._customer_has_app(customer_info.get('base_id', ''))
        
        # 根据到期天数调整通知类型概率
        if days_to_expiry == 1:  # 临近到期，增加SMS通知概率
            if has_app:
                return random.choices(
                    ['app_push', 'sms', 'app_message', 'email', 'sms+app_push'],
                    weights=[0.4, 0.3, 0.1, 0.1, 0.1],
                    k=1
                )[0]
            else:
                return random.choices(
                    ['sms', 'email', 'wechat_message'],
                    weights=[0.6, 0.3, 0.1],
                    k=1
                )[0]
        elif days_to_expiry == 3:  # 中等紧急度
            if has_app:
                return random.choices(
                    ['app_push', 'app_message', 'email', 'sms'],
                    weights=[0.5, 0.2, 0.2, 0.1],
                    k=1
                )[0]
            else:
                return random.choices(
                    ['email', 'sms', 'wechat_message'],
                    weights=[0.5, 0.3, 0.2],
                    k=1
                )[0]
        else:  # 提前较多，主要使用非实时通知
            if has_app:
                return random.choices(
                    ['app_message', 'email', 'app_push'],
                    weights=[0.5, 0.3, 0.2],
                    k=1
                )[0]
            else:
                return random.choices(
                    ['email', 'wechat_message', 'sms'],
                    weights=[0.6, 0.3, 0.1],
                    k=1
                )[0]

    def _customer_has_app(self, customer_id):
        """
        检查客户是否有APP
        
        Args:
            customer_id (str): 客户ID
            
        Returns:
            bool: 是否有APP
        """
        try:
            if not customer_id:
                return False
            
            query = "SELECT COUNT(*) as count FROM cdp_app_user_profile WHERE base_id = %s"
            results = self.db_manager.execute_query(query, (customer_id,))
            
            if results and results[0].get('count', 0) > 0:
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"检查客户APP状态时出错: {str(e)}")
            return random.choice([True, False])  # 出错时随机返回

    def _get_redemption_options(self, product_info):
        """
        获取产品的赎回选项
        
        Args:
            product_info (dict): 产品信息
            
        Returns:
            list: 赎回选项列表
        """
        redemption_way = product_info.get('redemption_way', '随时赎回')
        
        if redemption_way == '固定赎回':
            return ['auto_redeem', 'reinvest']
        else:
            return ['manual_redeem', 'auto_redeem', 'partial_redeem', 'reinvest']
        
    def generate_investment_related_events(self, customer_ids, date_range):
        """
        批量生成理财相关事件
        
        针对指定的客户列表和日期范围，生成完整的理财相关事件链，
        包括浏览、点击、购买、赎回等，保证事件时序性和关联性
        
        Args:
            customer_ids (list): 客户ID列表，如为空则自动选择活跃客户
            date_range (tuple): 日期范围(start_date, end_date)
            
        Returns:
            dict: 包含生成事件统计信息的字典
        """
        import datetime
        import random
        
        self.logger.info("开始批量生成理财相关事件")
        
        # 处理日期范围
        start_date, end_date = date_range
        
        # 转换日期格式
        if isinstance(start_date, str):
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # 检查日期范围有效性
        if start_date > end_date:
            self.logger.error(f"无效的日期范围: {start_date} 至 {end_date}")
            return {'error': '无效的日期范围', 'generated_events': 0}
        
        # 初始化统计信息
        stats = {
            'total_customers': 0,
            'processed_customers': 0,
            'generated_events': 0,
            'purchase_events': 0,
            'click_events': 0,
            'view_events': 0,
            'redemption_events': 0,
            'due_notification_events': 0,
            'errors': []
        }
        
        # 如果未提供客户ID列表，获取活跃客户
        if not customer_ids:
            self.logger.info("未提供客户ID列表，将自动选择活跃客户")
            customer_ids = self._get_active_customer_ids(start_date, end_date, limit=300)
        
        # 更新总客户数
        stats['total_customers'] = len(customer_ids)
        
        if not customer_ids:
            self.logger.warning("没有找到客户，无法生成事件")
            return stats
        
        self.logger.info(f"将为 {len(customer_ids)} 个客户生成理财相关事件，日期范围: {start_date} 至 {end_date}")
        
        # 获取时间范围内的投资记录
        investment_records = self._get_investments_by_date_range(start_date, end_date)
        
        # 按客户分组投资记录
        customer_investments = {}
        for record in investment_records:
            customer_id = record.get('base_id')
            if customer_id in customer_ids:  # 只处理指定的客户
                if customer_id not in customer_investments:
                    customer_investments[customer_id] = []
                customer_investments[customer_id].append(record)
        
        # 获取时间范围内的赎回记录
        redemption_records = self._get_redemptions_by_date_range(start_date, end_date)
        
        # 按客户分组赎回记录
        customer_redemptions = {}
        for record in redemption_records:
            customer_id = record.get('customer_id')
            if customer_id in customer_ids:  # 只处理指定的客户
                if customer_id not in customer_redemptions:
                    customer_redemptions[customer_id] = []
                customer_redemptions[customer_id].append(record)
        
        # 获取时间范围内即将到期的投资记录（为生成到期提醒事件）
        maturing_investments = self._get_maturing_investments(start_date, end_date)
        
        # 按客户分组到期记录
        customer_maturings = {}
        for record in maturing_investments:
            customer_id = record.get('base_id')
            if customer_id in customer_ids:  # 只处理指定的客户
                if customer_id not in customer_maturings:
                    customer_maturings[customer_id] = []
                customer_maturings[customer_id].append(record)
        
        # 处理每个客户
        for idx, customer_id in enumerate(customer_ids):
            try:
                # 更新进度
                stats['processed_customers'] += 1
                if idx % 20 == 0 or idx == len(customer_ids) - 1:
                    self.logger.info(f"处理进度: {idx+1}/{len(customer_ids)} 客户")
                
                # 处理购买相关事件
                if customer_id in customer_investments:
                    for investment in customer_investments[customer_id]:
                        # 生成购买结果事件
                        purchase_event = self.generate_purchase_result_event(investment)
                        if purchase_event:
                            stats['purchase_events'] += 1
                            stats['generated_events'] += 1
                        
                        # 生成购买前点击事件（1-3次点击）
                        click_count = random.randint(1, 3)
                        purchase_date = self._parse_timestamp(investment.get('detail_time'))
                        click_events = self.generate_product_click_events(
                            customer_id, 
                            investment.get('product_id'), 
                            purchase_date, 
                            count=click_count
                        )
                        stats['click_events'] += len(click_events)
                        stats['generated_events'] += len(click_events)
                        
                        # 生成购买前详情页浏览事件（1-2次浏览）
                        view_count = random.randint(1, 2)
                        view_events = self.generate_product_detail_view_events(
                            customer_id, 
                            investment.get('product_id'), 
                            purchase_date, 
                            count=view_count
                        )
                        stats['view_events'] += len(view_events)
                        stats['generated_events'] += len(view_events)
                
                # 处理赎回相关事件
                if customer_id in customer_redemptions:
                    for redemption in customer_redemptions[customer_id]:
                        # 生成赎回相关事件
                        redemption_events = self.generate_redemption_events(redemption)
                        if redemption_events:
                            stats['redemption_events'] += len(redemption_events)
                            stats['generated_events'] += len(redemption_events)
                
                # 处理即将到期的投资提醒事件
                if customer_id in customer_maturings:
                    for maturing in customer_maturings[customer_id]:
                        # 计算到期日期
                        maturity_date = self._parse_date(maturing.get('maturity_date'))
                        if maturity_date:
                            # 生成到期提醒事件
                            due_events = self.generate_due_notification_events(
                                maturing, maturity_date
                            )
                            if due_events:
                                stats['due_notification_events'] += len(due_events)
                                stats['generated_events'] += len(due_events)
                
                # 如果客户没有任何投资记录，生成一些浏览和点击事件
                if (customer_id not in customer_investments and 
                    customer_id not in customer_redemptions and
                    customer_id not in customer_maturings):
                    
                    # 随机选择1-3个产品
                    products = self._get_random_products(limit=random.randint(1, 3))
                    if products:
                        for product in products:
                            # 随机生成浏览日期
                            random_day = random.randint(0, (end_date - start_date).days)
                            browse_date = start_date + datetime.timedelta(days=random_day)
                            
                            # 生成点击事件
                            click_events = self.generate_product_click_events(
                                customer_id, 
                                product.get('base_id'), 
                                browse_date, 
                                count=1
                            )
                            stats['click_events'] += len(click_events)
                            stats['generated_events'] += len(click_events)
                            
                            # 50%概率生成详情页浏览事件
                            if random.random() < 0.5:
                                view_events = self.generate_product_detail_view_events(
                                    customer_id, 
                                    product.get('base_id'), 
                                    browse_date, 
                                    count=1
                                )
                                stats['view_events'] += len(view_events)
                                stats['generated_events'] += len(view_events)
            
            except Exception as e:
                error_msg = f"处理客户 {customer_id} 事件时出错: {str(e)}"
                self.logger.error(error_msg)
                stats['errors'].append(error_msg)
        
        # 记录最终统计信息
        self.logger.info(f"理财相关事件生成完成: 处理了 {stats['processed_customers']} 个客户")
        self.logger.info(f"共生成 {stats['generated_events']} 个事件")
        self.logger.info(f"其中: 购买结果事件 {stats['purchase_events']} 个, 点击事件 {stats['click_events']} 个, "
                        f"浏览事件 {stats['view_events']} 个, 赎回事件 {stats['redemption_events']} 个, "
                        f"到期提醒事件 {stats['due_notification_events']} 个")
        
        if stats['errors']:
            self.logger.warning(f"处理过程中出现 {len(stats['errors'])} 个错误")
        
        return stats

    def _get_active_customer_ids(self, start_date, end_date, limit=300):
        """
        获取时间范围内活跃客户的ID列表
        
        Args:
            start_date (datetime.date): 开始日期
            end_date (datetime.date): 结束日期
            limit (int): 返回客户数量限制
            
        Returns:
            list: 客户ID列表
        """
        try:
            # 转换为时间戳格式
            start_timestamp = int(datetime.datetime.combine(
                start_date, datetime.time(0, 0)).timestamp() * 1000)
            end_timestamp = int(datetime.datetime.combine(
                end_date, datetime.time(23, 59, 59)).timestamp() * 1000)
            
            # 查询活跃客户（有交易或事件记录的客户）
            query = """
            SELECT DISTINCT base_id 
            FROM (
                -- 有资金流水的客户
                SELECT base_id FROM cdp_account_flow
                WHERE detail_time BETWEEN %s AND %s
                UNION
                -- 有理财记录的客户
                SELECT base_id FROM cdp_investment_order
                WHERE detail_time BETWEEN %s AND %s
                UNION
                -- 有事件记录的客户
                SELECT base_id FROM cdp_customer_event
                WHERE event_time BETWEEN %s AND %s
            ) AS active_customers
            LIMIT %s
            """
            
            results = self.db_manager.execute_query(
                query, 
                (start_timestamp, end_timestamp, start_timestamp, end_timestamp, 
                start_timestamp, end_timestamp, limit)
            )
            
            # 提取客户ID
            customer_ids = [row['base_id'] for row in results if 'base_id' in row]
            
            return customer_ids
            
        except Exception as e:
            self.logger.error(f"获取活跃客户时出错: {str(e)}")
            return []

    def _get_investments_by_date_range(self, start_date, end_date):
        """
        获取日期范围内的投资记录
        
        Args:
            start_date (datetime.date): 开始日期
            end_date (datetime.date): 结束日期
            
        Returns:
            list: 投资记录列表
        """
        try:
            # 转换为时间戳格式
            start_timestamp = int(datetime.datetime.combine(
                start_date, datetime.time(0, 0)).timestamp() * 1000)
            end_timestamp = int(datetime.datetime.combine(
                end_date, datetime.time(23, 59, 59)).timestamp() * 1000)
            
            query = """
            SELECT * FROM cdp_investment_order
            WHERE detail_time BETWEEN %s AND %s
            ORDER BY detail_time
            """
            
            results = self.db_manager.execute_query(query, (start_timestamp, end_timestamp))
            return results
            
        except Exception as e:
            self.logger.error(f"获取投资记录时出错: {str(e)}")
            return []

    def _get_redemptions_by_date_range(self, start_date, end_date):
        """
        获取日期范围内的赎回记录
        
        Args:
            start_date (datetime.date): 开始日期
            end_date (datetime.date): 结束日期
            
        Returns:
            list: 赎回记录列表
        """
        try:
            # 转换为时间戳格式
            start_timestamp = int(datetime.datetime.combine(
                start_date, datetime.time(0, 0)).timestamp() * 1000)
            end_timestamp = int(datetime.datetime.combine(
                end_date, datetime.time(23, 59, 59)).timestamp() * 1000)
            
            # 查询状态变更为"完全赎回"或"部分卖出"且赎回时间在范围内的记录
            query = """
            SELECT io.*, io.base_id AS customer_id
            FROM cdp_investment_order io
            WHERE (io.wealth_status IN ('完全赎回', '部分卖出'))
            AND (
                (io.wealth_all_redeem_time BETWEEN %s AND %s) OR
                (io.wealth_status = '部分卖出' AND io.detail_time < %s)
            )
            ORDER BY 
                CASE WHEN io.wealth_all_redeem_time IS NOT NULL THEN io.wealth_all_redeem_time
                ELSE io.detail_time END
            """
            
            results = self.db_manager.execute_query(
                query, (start_timestamp, end_timestamp, end_timestamp)
            )
            return results
            
        except Exception as e:
            self.logger.error(f"获取赎回记录时出错: {str(e)}")
            return []

    def _get_maturing_investments(self, start_date, end_date):
        """
        获取在日期范围内即将到期的投资记录
        
        查找到期日接近指定日期范围的投资，用于生成到期提醒事件
        
        Args:
            start_date (datetime.date): 开始日期
            end_date (datetime.date): 结束日期
            
        Returns:
            list: 即将到期的投资记录列表
        """
        try:
            # 计算提醒范围（到期日+提前提醒天数）
            reminder_start_date = start_date - datetime.timedelta(days=7)  # 到期前7天开始提醒
            reminder_end_date = end_date + datetime.timedelta(days=1)  # 包含结束日期
            
            # 转换为时间戳格式
            reminder_start_timestamp = int(datetime.datetime.combine(
                reminder_start_date, datetime.time(0, 0)).timestamp() * 1000)
            reminder_end_timestamp = int(datetime.datetime.combine(
                reminder_end_date, datetime.time(23, 59, 59)).timestamp() * 1000)
            
            query = """
            SELECT * FROM cdp_investment_order
            WHERE maturity_time BETWEEN %s AND %s
            AND wealth_status IN ('持有', '部分卖出')
            ORDER BY maturity_time
            """
            
            results = self.db_manager.execute_query(
                query, (reminder_start_timestamp, reminder_end_timestamp)
            )
            return results
            
        except Exception as e:
            self.logger.error(f"获取即将到期的投资记录时出错: {str(e)}")
            return []

    def _get_random_products(self, limit=5):
        """
        获取随机产品列表
        
        Args:
            limit (int): 返回产品数量
            
        Returns:
            list: 产品列表
        """
        try:
            query = """
            SELECT * FROM cdp_product_archive
            WHERE marketing_status = '在售'
            ORDER BY RAND()
            LIMIT %s
            """
            
            results = self.db_manager.execute_query(query, (limit,))
            return results
            
        except Exception as e:
            self.logger.error(f"获取随机产品时出错: {str(e)}")
            return []

    def _parse_date(self, date_value):
        """
        解析日期值为标准日期对象
        
        Args:
            date_value: 日期值，可能是字符串、日期或时间戳
            
        Returns:
            datetime.date: 标准日期对象，无法解析则返回None
        """
        if not date_value:
            return None
        
        import datetime
        
        # 如果已经是日期对象
        if isinstance(date_value, datetime.date):
            return date_value
        
        # 如果是datetime对象
        if isinstance(date_value, datetime.datetime):
            return date_value.date()
        
        # 如果是字符串
        if isinstance(date_value, str):
            try:
                return datetime.datetime.strptime(date_value, '%Y-%m-%d').date()
            except ValueError:
                try:
                    return datetime.datetime.strptime(date_value, '%Y/%m/%d').date()
                except ValueError:
                    return None
        
        # 如果是时间戳（整数或浮点数）
        if isinstance(date_value, (int, float)):
            try:
                # 假设是毫秒级时间戳
                if date_value > 1000000000000:  # 13位时间戳
                    date_value /= 1000
                return datetime.datetime.fromtimestamp(date_value).date()
            except:
                return None
        
        # 其他情况无法解析
        return None
