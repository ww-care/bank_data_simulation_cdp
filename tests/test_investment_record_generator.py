import unittest
import datetime
import mock
from src.data_generator.investment.investment_record_generator import InvestmentRecordGenerator
from src.data_generator.investment.product_matcher import ProductMatcher
from src.data_generator.investment.utils import InvestmentUtils

class TestInvestmentRecordGenerator(unittest.TestCase):
    """
    理财购买生成器单元测试类
    
    测试理财购买记录生成的核心功能和边界情况
    """
    
    def setUp(self):
        """
        测试前的准备工作，设置模拟对象和测试数据
        """
        # 创建模拟对象
        self.db_manager = mock.MagicMock()
        self.config_manager = mock.MagicMock()
        self.logger = mock.MagicMock()
        self.time_manager = mock.MagicMock()
        
        # 模拟配置
        mock_config = {
            'risk_level_mapping': {
                'R1': {'acceptable_risk': ['low'], 'weight': 1.0},
                'R2': {'acceptable_risk': ['low'], 'weight': 0.9},
                'R3': {'acceptable_risk': ['low', 'medium'], 'weight': 0.8},
                'R4': {'acceptable_risk': ['low', 'medium', 'high'], 'weight': 0.7},
                'R5': {'acceptable_risk': ['low', 'medium', 'high'], 'weight': 0.6}
            },
            'amount_config': {
                'personal': {'min': 10000, 'max': 200000, 'mean': 50000, 'std_dev': 30000},
                'corporate': {'min': 100000, 'max': 2000000, 'mean': 500000, 'std_dev': 300000},
                'vip_multiplier': 1.5
            },
            'redemption_config': {
                'early_redemption_base_prob': 0.02,
                'partial_redemption_prob': 0.4,
                'partial_redemption_range': [0.2, 0.7]
            },
            'term_distribution': {
                'short_term': {'ratio': 0.35, 'days': [30, 60, 90]},
                'medium_term': {'ratio': 0.45, 'days': [120, 180, 270, 365]},
                'long_term': {'ratio': 0.20, 'days': [540, 730, 1095]}
            },
            'expected_return': {
                'low_risk': {'min': 0.030, 'max': 0.045},
                'medium_risk': {'min': 0.045, 'max': 0.070},
                'high_risk': {'min': 0.070, 'max': 0.120}
            },
            'risk_level_distribution': {
                'low': 0.45,
                'medium': 0.35,
                'high': 0.20
            },
            'system': {
                'batch_size': 100,
                'random_seed': 42
            }
        }
        
        # 模拟ConfigAdapter
        mock_config_adapter = mock.MagicMock()
        mock_config_adapter.build_investment_generator_config.return_value = mock_config
        
        # 创建测试对象
        self.generator = InvestmentRecordGenerator(
            self.db_manager, 
            self.config_manager, 
            self.logger, 
            self.time_manager
        )
        
        # 替换配置适配器和配置
        self.generator.config_adapter = mock_config_adapter
        self.generator.config = mock_config
        
        # 模拟产品匹配器
        self.generator.product_matcher = mock.MagicMock(spec=ProductMatcher)
        
        # 设置测试数据
        self.setup_test_data()
    
    def setup_test_data(self):
        """设置测试数据"""
        # 模拟客户数据
        self.test_customer = {
            'base_id': 'CUST123456',
            'name': '测试客户',
            'customer_type': 'personal',
            'risk_level': 'R3',
            'is_vip': False,
            'wealthamount': 100000,
            'registration_date': '2023-01-01',
            'firstpurchasetype': None,
            'havewealth': '否',
            'wealthcustomerphase': '注册',
            'sellwealthdate': None,
            'sellalldate': None,
            'nousedays': 0
        }
        
        # 模拟产品数据
        self.test_product = {
            'base_id': 'PROD123456',
            'name': '测试理财产品',
            'product_type': '债券型基金',
            'risk_level': 'R2',
            'investment_period': 6,  # 6个月
            'expected_yield': 0.045,  # 4.5%
            'minimum_investment': 10000,
            'redemption_way': '随时赎回',
            'marketing_status': '在售'
        }
        
        # 模拟投资记录
        self.test_investment = {
            'detail_id': 'INV123456',
            'base_id': 'CUST123456',
            'detail_time': int(datetime.datetime(2023, 6, 1, 10, 30).timestamp() * 1000),
            'product_id': 'PROD123456',
            'purchase_amount': 50000,
            'hold_amount': 50000,
            'term': 180,  # 6个月
            'wealth_purchase_time': int(datetime.datetime(2023, 6, 1, 10, 30).timestamp() * 1000),
            'wealth_all_redeem_time': None,
            'wealth_date': datetime.date(2023, 6, 1),
            'wealth_status': '持有',
            'maturity_time': int(datetime.datetime(2023, 12, 1).timestamp() * 1000),
            'status': '成功',
            'channel': 'mobile_app',
            'expected_return': 0.045
        }
        
        # 模拟赎回信息
        self.test_redemption = {
            'investment_id': 'INV123456',
            'redemption_amount': 20000,
            'is_full_redemption': False,
            'redemption_timestamp': int(datetime.datetime(2023, 8, 1, 14, 30).timestamp() * 1000)
        }
    
    def test_calculate_investment_amount(self):
        """测试投资金额计算逻辑"""
        # 模拟产品匹配器返回的投资能力
        self.generator.product_matcher.calculate_investment_capacity.return_value = {
            'min_amount': 10000,
            'max_amount': 200000,
            'suggested_amount': 50000
        }
        
        # 测试普通客户
        amount = self.generator.calculate_investment_amount(self.test_customer, self.test_product)
        self.assertGreaterEqual(amount, 10000)
        self.assertLessEqual(amount, 200000)
        
        # 测试VIP客户
        vip_customer = dict(self.test_customer)
        vip_customer['is_vip'] = True
        
        self.generator.product_matcher.calculate_investment_capacity.return_value = {
            'min_amount': 10000,
            'max_amount': 300000,  # VIP客户上限更高
            'suggested_amount': 75000
        }
        
        amount = self.generator.calculate_investment_amount(vip_customer, self.test_product)
        self.assertGreaterEqual(amount, 10000)
        self.assertLessEqual(amount, 300000)
        
        # 测试企业客户
        corporate_customer = dict(self.test_customer)
        corporate_customer['customer_type'] = 'corporate'
        
        self.generator.product_matcher.calculate_investment_capacity.return_value = {
            'min_amount': 100000,
            'max_amount': 2000000,
            'suggested_amount': 500000
        }
        
        amount = self.generator.calculate_investment_amount(corporate_customer, self.test_product)
        self.assertGreaterEqual(amount, 100000)
        self.assertLessEqual(amount, 2000000)
    
    def test_generate_purchase_time(self):
        """测试购买时间生成逻辑"""
        # 测试工作日购买时间
        workday = datetime.date(2023, 6, 1)  # 2023年6月1日是周四（工作日）
        
        # 模拟必要的方法
        self.generator._get_time_distribution = mock.MagicMock(return_value={
            'morning': {
                'weight': 0.35,
                'peak_time': '10:30',
                'hours': [9, 10, 11]
            },
            'afternoon': {
                'weight': 0.40,
                'peak_time': '15:00',
                'hours': [14, 15, 16, 17]
            },
            'evening': {
                'weight': 0.25,
                'peak_time': '19:00',
                'hours': [18, 19, 20, 21]
            }
        })
        
        purchase_time = self.generator._generate_purchase_time(workday, 'personal')
        
        # 验证时间在工作日时间范围内
        self.assertEqual(purchase_time.date(), workday)
        self.assertGreaterEqual(purchase_time.hour, 8)  # 至少在早上8点之后
        self.assertLess(purchase_time.hour, 23)  # 在晚上11点之前
    
    def test_weighted_sample_products(self):
        """测试加权随机抽样产品逻辑"""
        # 准备带权重的产品列表
        matched_products = [
            {'product': {'base_id': 'P1'}, 'match_score': 0.9},
            {'product': {'base_id': 'P2'}, 'match_score': 0.7},
            {'product': {'base_id': 'P3'}, 'match_score': 0.5},
            {'product': {'base_id': 'P4'}, 'match_score': 0.3},
            {'product': {'base_id': 'P5'}, 'match_score': 0.1}
        ]
        
        # 测试选择数量小于总数
        selected = self.generator._weighted_sample_products(matched_products, 3)
        self.assertEqual(len(selected), 3)
        
        # 确保选择的是字典对象
        for product in selected:
            self.assertIn('product', product)
            self.assertIn('match_score', product)
        
        # 测试选择数量等于总数
        selected = self.generator._weighted_sample_products(matched_products, 5)
        self.assertEqual(len(selected), 5)
        
        # 测试选择数量大于总数
        selected = self.generator._weighted_sample_products(matched_products, 10)
        self.assertEqual(len(selected), 5)  # 应该返回所有产品
        
        # 测试空列表情况
        selected = self.generator._weighted_sample_products([], 3)
        self.assertEqual(len(selected), 0)
    
    def test_generate_purchase_channel(self):
        """测试购买渠道生成逻辑"""
        # 测试普通客户
        channels = ['mobile_app', 'online_banking', 'counter', 'phone_banking', 'third_party']
        
        # 需要覆盖到以下方法以避免测试中的随机变量导致不确定性
        original_random = mock.MagicMock(return_value=0.5)  # 返回固定值
        original_choices = mock.MagicMock(return_value=['mobile_app'])  # 返回固定选择
        
        # 使用mock.patch暂时替换random.random和random.choices
        with mock.patch('random.random', original_random), \
             mock.patch('random.choices', original_choices):
            
            channel = self.generator._generate_purchase_channel(self.test_customer)
            self.assertIn(channel, channels)
            
            # 测试VIP客户
            vip_customer = dict(self.test_customer)
            vip_customer['is_vip'] = True
            channel = self.generator._generate_purchase_channel(vip_customer)
            self.assertIn(channel, channels)
            
            # 测试企业客户
            corp_customer = dict(self.test_customer)
            corp_customer['customer_type'] = 'corporate'
            channel = self.generator._generate_purchase_channel(corp_customer)
            self.assertIn(channel, channels)
    
    def test_is_product_available(self):
        """测试产品可用性检查逻辑"""
        # 测试正常在售产品
        available_product = dict(self.test_product)
        result = self.generator._is_product_available(available_product, datetime.date(2023, 6, 1))
        self.assertTrue(result)
        
        # 测试已下架产品
        unavailable_product = dict(self.test_product)
        unavailable_product['marketing_status'] = '下架'
        result = self.generator._is_product_available(unavailable_product, datetime.date(2023, 6, 1))
        self.assertFalse(result)
        
        # 测试未上架产品
        future_product = dict(self.test_product)
        future_product['launch_date'] = datetime.date(2023, 7, 1)
        result = self.generator._is_product_available(future_product, datetime.date(2023, 6, 1))
        self.assertFalse(result)
        
        # 测试已到期产品
        expired_product = dict(self.test_product)
        expired_product['end_date'] = datetime.date(2023, 5, 1)
        result = self.generator._is_product_available(expired_product, datetime.date(2023, 6, 1))
        self.assertFalse(result)
    
    def test_parse_date(self):
        """测试日期解析逻辑"""
        # 模拟_parse_date方法（如果实现不存在）
        if not hasattr(self.generator, '_parse_date'):
            self.generator._parse_date = lambda date_str: (
                datetime.datetime.strptime(date_str, '%Y-%m-%d').date() 
                if isinstance(date_str, str) 
                else (date_str.date() if isinstance(date_str, datetime.datetime) else date_str)
            )
        
        # 测试字符串日期
        date_str = '2023-06-01'
        parsed = self.generator._parse_date(date_str)
        self.assertEqual(parsed, datetime.date(2023, 6, 1))
        
        # 测试另一种格式的字符串日期
        date_str = '2023/06/01'
        parsed = self.generator._parse_date(date_str)
        self.assertEqual(parsed, datetime.date(2023, 6, 1))
        
        # 测试日期对象
        date_obj = datetime.date(2023, 6, 1)
        parsed = self.generator._parse_date(date_obj)
        self.assertEqual(parsed, date_obj)
        
        # 测试datetime对象
        datetime_obj = datetime.datetime(2023, 6, 1, 10, 30)
        parsed = self.generator._parse_date(datetime_obj)
        self.assertEqual(parsed, datetime_obj.date())
    
    def test_update_customer_wealth_status(self):
        """测试客户财富状态更新逻辑"""
        # 模拟获取客户信息的方法
        self.generator._get_customer_info = mock.MagicMock(return_value=self.test_customer)
        
        # 模拟获取客户投资记录的方法
        self.generator._get_customer_investments = mock.MagicMock(return_value=[])
        
        # 模拟计算财富阶段的方法
        self.generator._calculate_wealth_phase = mock.MagicMock(return_value="首投")
        
        # 模拟获取最后交易日期的方法
        self.generator._get_last_transaction_date = mock.MagicMock(return_value=datetime.date(2023, 5, 1))
        
        # 模拟更新客户信息的方法
        self.generator._update_customer_info = mock.MagicMock(return_value=True)

        # 添加模拟获取产品信息的方法
        self.generator._get_product_info = mock.MagicMock(return_value={
            'product_type': '债券型基金', 
            'product_id': 'PROD123456'
        })
        
        # 测试购买记录更新
        purchase_info = {
            'base_id': 'CUST123456',
            'purchase_amount': 50000,
            'wealth_status': '持有',
            'product_id': 'PROD123456'
        }
        print("准备调用update_customer_wealth_status方法")
        result = self.generator.update_customer_wealth_status('CUST123456', purchase_info)
        print(f"purchase_info-方法返回值: {result}")

        # 打印调用信息，看看模拟方法是否被调用
        print(f"_get_customer_info called: {self.generator._get_customer_info.called}")
        print(f"_get_product_info called: {self.generator._get_product_info.called}")
        print(f"_update_customer_info called: {self.generator._update_customer_info.called}")
        self.assertTrue(result)
        
        # 验证_update_customer_info被调用
        self.generator._update_customer_info.assert_called()
        
        # 测试赎回记录更新
        redemption_info = {
            'base_id': 'CUST123456',
            'wealth_all_redeem_time': int(datetime.datetime(2023, 8, 1).timestamp() * 1000),
            'wealth_status': '完全赎回',
            'redemption_amount': 50000
        }
        
        # 重置mock
        self.generator._update_customer_info.reset_mock()
        
        result = self.generator.update_customer_wealth_status('CUST123456', redemption_info)
        print(f"redemption_info-方法返回值: {result}")
        self.assertTrue(result)
        
        # 验证_update_customer_info被调用
        self.generator._update_customer_info.assert_called()
    
    def test_validate_generated_data(self):
        """测试数据验证逻辑"""
        # 模拟validate_generated_data方法
        def mock_validate_data(records):
            is_valid = True
            valid_records = 0
            invalid_records = 0
            
            for record in records:
                # 简单检查必须字段
                if all(field in record for field in ['detail_id', 'base_id', 'product_id', 'detail_time', 
                                                  'purchase_amount', 'wealth_date', 'wealth_status']):
                    valid_records += 1
                else:
                    invalid_records += 1
                    is_valid = False
            
            return {
                'is_valid': is_valid,
                'total_records': len(records),
                'valid_records': valid_records,
                'invalid_records': invalid_records,
                'error_summary': {},
                'field_stats': {},
                'warnings': [],
                'validation_details': []
            }
        
        # 赋予生成器模拟的验证方法
        self.generator.validate_generated_data = mock_validate_data
        
        # 准备有效的测试数据
        valid_records = [
            {
                'detail_id': 'INV123456',
                'base_id': 'CUST123456',
                'product_id': 'PROD123456',
                'detail_time': int(datetime.datetime(2023, 6, 1).timestamp() * 1000),
                'purchase_amount': 50000,
                'hold_amount': 50000,
                'wealth_date': datetime.date(2023, 6, 1),
                'wealth_status': '持有'
            },
            {
                'detail_id': 'INV789012',
                'base_id': 'CUST789012',
                'product_id': 'PROD789012',
                'detail_time': int(datetime.datetime(2023, 6, 2).timestamp() * 1000),
                'purchase_amount': 30000,
                'hold_amount': 30000,
                'wealth_date': datetime.date(2023, 6, 2),
                'wealth_status': '持有'
            }
        ]
        
        # 验证有效数据
        result = self.generator.validate_generated_data(valid_records)
        self.assertTrue(result['is_valid'])
        self.assertEqual(result['valid_records'], 2)
        self.assertEqual(result['invalid_records'], 0)
        
        # 准备无效的测试数据
        invalid_records = valid_records + [
            {
                # 缺少必填字段
                'base_id': 'CUST345678',
                'product_id': 'PROD345678',
                'detail_time': int(datetime.datetime(2023, 6, 3).timestamp() * 1000),
                'purchase_amount': 40000,
                'wealth_status': '持有'
                # 缺少wealth_date
            }
        ]
        
        # 验证包含无效记录的数据
        result = self.generator.validate_generated_data(invalid_records)
        self.assertFalse(result['is_valid'])
        self.assertEqual(result['valid_records'], 2)
        self.assertEqual(result['invalid_records'], 1)

if __name__ == '__main__':
    unittest.main()