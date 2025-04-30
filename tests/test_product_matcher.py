import unittest
import mock
import datetime
from src.data_generator.investment.product_matcher import ProductMatcher

class TestProductMatcher(unittest.TestCase):
    """测试产品匹配器"""
    
    def setUp(self):
        """测试准备"""
        # 创建模拟对象
        self.db_manager = mock.MagicMock()
        self.logger = mock.MagicMock()
        
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
            }
        }
        
        # 创建测试对象
        self.product_matcher = ProductMatcher(self.db_manager, mock_config, self.logger)
    
    def test_calculate_risk_match_score(self):
        """测试风险等级匹配分数计算"""
        # 测试完全匹配情况
        score = self.product_matcher._calculate_risk_match_score('R3', 'R3')
        self.assertAlmostEqual(score, 1.0, places=1)
        
        # 测试相近匹配情况
        score = self.product_matcher._calculate_risk_match_score('R3', 'R2')
        self.assertGreater(score, 0.7)
        
        # 测试差距较大的情况
        score = self.product_matcher._calculate_risk_match_score('R1', 'R5')
        self.assertLess(score, 0.4)
        
        # 测试保守客户与高风险产品
        score = self.product_matcher._calculate_risk_match_score('R1', 'R4')
        self.assertLess(score, 0.3)
        
        # 测试进取型客户与低风险产品
        score = self.product_matcher._calculate_risk_match_score('R5', 'R1')
        self.assertLess(score, 0.7)

    def test_calculate_investment_capacity(self):
        """测试客户投资能力计算"""
        # 测试普通个人客户
        customer = {
            'customer_type': 'personal',
            'is_vip': False,
            'risk_level': 'R3',
            'salarycategory': '4级'
        }
        
        capacity = self.product_matcher.calculate_investment_capacity(customer)
        self.assertIn('min_amount', capacity)
        self.assertIn('max_amount', capacity)
        self.assertIn('suggested_amount', capacity)
        self.assertLessEqual(capacity['min_amount'], capacity['suggested_amount'])
        self.assertLessEqual(capacity['suggested_amount'], capacity['max_amount'])
        
        # 测试VIP客户投资能力
        vip_customer = dict(customer)
        vip_customer['is_vip'] = True
        
        vip_capacity = self.product_matcher.calculate_investment_capacity(vip_customer)
        self.assertGreater(vip_capacity['max_amount'], capacity['max_amount'])
        
        # 测试企业客户投资能力
        corporate_customer = dict(customer)
        corporate_customer['customer_type'] = 'corporate'
        
        corp_capacity = self.product_matcher.calculate_investment_capacity(corporate_customer)
        self.assertGreater(corp_capacity['min_amount'], capacity['min_amount'])

    def test_find_matching_products(self):
        """测试产品匹配功能"""
        # 准备测试数据
        customer = {
            'base_id': 'CUST123',
            'customer_type': 'personal',
            'is_vip': False,
            'risk_level': 'R3',
            'firstpurchasetype': '债券型基金'
        }
        
        products = [
            {
                'base_id': 'PROD1',
                'product_type': '债券型基金',
                'risk_level': 'R2',
                'expected_yield': 0.04,
                'investment_period': 6,
                'minimum_investment': 10000,
                'redemption_way': '随时赎回',
                'marketing_status': '在售'
            },
            {
                'base_id': 'PROD2',
                'product_type': '货币型基金',
                'risk_level': 'R1',
                'expected_yield': 0.02,
                'investment_period': 3,
                'minimum_investment': 5000,
                'redemption_way': '随时赎回',
                'marketing_status': '在售'
            },
            {
                'base_id': 'PROD3',
                'product_type': '股票型基金',
                'risk_level': 'R4',
                'expected_yield': 0.08,
                'investment_period': 12,
                'minimum_investment': 20000,
                'redemption_way': '固定赎回',
                'marketing_status': '在售'
            }
        ]
        
        # 模拟方法
        self.product_matcher._get_available_products = mock.MagicMock(return_value=products)
        
        # 测试匹配功能
        matched_products = self.product_matcher.find_matching_products(customer)
        
        # 验证结果
        self.assertGreater(len(matched_products), 0)
        
        # 检查每个结果是否包含必要的信息
        for item in matched_products:
            self.assertIn('product', item)
            self.assertIn('match_score', item)
            self.assertIn('risk_match', item)
            self.assertIn('feature_match', item)
            self.assertIn('return_match', item)
        
        # 验证排序是否正确
        self.assertGreaterEqual(
            matched_products[0]['match_score'],
            matched_products[-1]['match_score']
        )

if __name__ == '__main__':
    unittest.main()