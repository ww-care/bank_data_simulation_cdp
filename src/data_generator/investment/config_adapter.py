"""
理财购买生成器配置适配器
负责从系统配置文件中提取和转换理财相关配置
"""

import yaml
import os
import logging


class InvestmentConfigAdapter:
    """
    理财配置适配器类
    用于从主配置文件中提取理财相关配置，并转换为理财生成器可使用的结构
    """
    
    def __init__(self, config_manager=None, config_path=None):
        """
        初始化配置适配器
        
        Args:
            config_manager: 配置管理器实例
            config_path: 配置文件路径，当config_manager不可用时使用
        """
        self.config_manager = config_manager
        self.config_path = config_path
        self.config = None
        self.investment_config = None
        self.logger = logging.getLogger(__name__)
    
    def load_config(self):
        """
        加载配置文件
        优先使用config_manager，如不可用则直接读取配置文件
        
        Returns:
            dict: 加载的配置字典
        """
        try:
            if self.config_manager:
                self.logger.info("Loading config from config manager")
                self.config = self.config_manager.get_config()
            elif self.config_path and os.path.exists(self.config_path):
                self.logger.info(f"Loading config from specified path: {self.config_path}")
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f)
            else:
                # 尝试默认路径
                default_paths = [
                    os.path.join('config', 'bank_data_simulation_config.yaml'),
                    os.path.join(os.getcwd(), 'config', 'bank_data_simulation_config.yaml')
                ]
                
                for path in default_paths:
                    if os.path.exists(path):
                        self.logger.info(f"Loading config from default path: {path}")
                        with open(path, 'r', encoding='utf-8') as f:
                            self.config = yaml.safe_load(f)
                        break
                else:
                    raise FileNotFoundError("No valid config file found")
                    
            self.logger.debug("Config loaded successfully")
            return self.config
        
        except Exception as e:
            self.logger.error(f"Failed to load config: {str(e)}")
            raise
    
    def extract_investment_config(self):
        """
        从主配置中提取理财相关配置
        
        Returns:
            dict: 提取的理财配置字典
        """
        if not self.config:
            self.logger.info("Config not loaded yet, loading now")
            self.load_config()
        
        # 如果加载配置失败，返回空字典
        if not self.config:
            self.logger.warning("Failed to load config, returning empty investment config")
            return {}
        
        # 提取理财配置
        self.investment_config = self.config.get('investment', {})
        if not self.investment_config:
            self.logger.warning("No 'investment' section found in config")
        else:
            self.logger.debug(f"Found investment config with {len(self.investment_config)} keys")
        
        # 提取客户配置（用于风险偏好映射）
        customer_config = self.config.get('customer', {})
        if not customer_config:
            self.logger.warning("No 'customer' section found in config")
        
        # 提取验证规则配置
        validation_config = self.config.get('validation', {})
        if not validation_config:
            self.logger.debug("No 'validation' section found in config")
        
        # 提取时间分布配置
        time_config = self.config.get('transaction', {}).get('time_distribution', {})
        if not time_config:
            self.logger.debug("No 'time_distribution' section found in config")
        
        # 储存相关配置以供其他方法使用
        self._customer_config = customer_config
        self._validation_config = validation_config
        self._time_config = time_config
        
        return self.investment_config
    
    def get_risk_level_mapping(self):
        """
        获取客户风险等级与产品风险等级的映射关系
        
        Returns:
            dict: 风险等级映射关系
        """
        if not self.investment_config:
            self.logger.debug("Investment config not extracted yet, extracting now")
            self.extract_investment_config()
        
        # 尝试从配置中获取风险等级分布
        risk_level_distribution = self.investment_config.get('risk_level_distribution', {})
        
        # 构建风险等级映射
        risk_mapping = {
            "R1": {"acceptable_risk": ["low"], "weight": 1.0},
            "R2": {"acceptable_risk": ["low"], "weight": 0.9},
            "R3": {"acceptable_risk": ["low", "medium"], "weight": 0.8},
            "R4": {"acceptable_risk": ["low", "medium", "high"], "weight": 0.7},
            "R5": {"acceptable_risk": ["low", "medium", "high"], "weight": 0.6}
        }
        
        # 从配置中获取自定义风险映射（如果存在）
        custom_mapping = self.investment_config.get('risk_level_mapping', {})
        if custom_mapping:
            self.logger.info("Using custom risk level mapping from config")
            risk_mapping.update(custom_mapping)
        
        # 补充逻辑：根据风险等级分布信息优化映射
        if risk_level_distribution:
            # 例如：如果配置中low风险产品占比很高，可以适当调整映射权重
            low_risk_ratio = risk_level_distribution.get('low', 0)
            if low_risk_ratio > 0.6:  # 如果低风险产品占比超过60%
                # 提高低风险产品的权重
                for risk_level, mapping in risk_mapping.items():
                    if "low" in mapping["acceptable_risk"]:
                        mapping["weight"] = min(1.0, mapping["weight"] * 1.2)
        
        self.logger.debug(f"Risk level mapping constructed with {len(risk_mapping)} levels")
        return risk_mapping
    
    def get_investment_amount_config(self):
        """
        获取理财金额相关配置
        
        Returns:
            dict: 理财金额配置，包含个人/企业客户金额范围和VIP乘数
        """
        if not self.investment_config:
            self.logger.debug("Investment config not extracted yet, extracting now")
            self.extract_investment_config()
        
        # 获取金额配置
        amount_config = self.investment_config.get('amount', {})
        
        # 获取VIP乘数，默认为1.5
        vip_multiplier = self.investment_config.get('vip_multiplier', 1.5)
        
        # 如果配置缺失，提供默认值
        if not amount_config:
            self.logger.warning("No investment amount config found, using defaults")
            amount_config = {
                'personal': {
                    'min': 10000,
                    'max': 200000,
                    'mean': 50000,
                    'std_dev': 30000
                },
                'corporate': {
                    'min': 100000,
                    'max': 2000000,
                    'mean': 500000,
                    'std_dev': 300000
                }
            }
        else:
            # 确保个人客户配置存在
            if 'personal' not in amount_config:
                self.logger.warning("No personal amount config found, using defaults")
                amount_config['personal'] = {
                    'min': 10000,
                    'max': 200000,
                    'mean': 50000,
                    'std_dev': 30000
                }
            
            # 确保企业客户配置存在
            if 'corporate' not in amount_config:
                self.logger.warning("No corporate amount config found, using defaults")
                amount_config['corporate'] = {
                    'min': 100000,
                    'max': 2000000,
                    'mean': 500000,
                    'std_dev': 300000
                }
        
        # 构建最终配置
        final_config = {
            'personal': amount_config.get('personal', {}),
            'corporate': amount_config.get('corporate', {}),
            'vip_multiplier': vip_multiplier
        }
        
        self.logger.debug(f"Investment amount config: {final_config}")
        return final_config
    
    def get_term_distribution(self):
        """
        获取理财期限分布配置
        
        Returns:
            dict: 理财期限分布配置，包含短中长期的比例和天数分布
        """
        if not self.investment_config:
            self.logger.debug("Investment config not extracted yet, extracting now")
            self.extract_investment_config()
        
        # 从配置中获取期限分布
        term_distribution = self.investment_config.get('term_distribution', {})
        
        # 如果配置缺失，提供默认值
        if not term_distribution:
            self.logger.warning("No term distribution config found, using defaults")
            term_distribution = {
                'short_term': {  # 短期(1-3个月)
                    'ratio': 0.35,
                    'days': [30, 60, 90]
                },
                'medium_term': {  # 中期(3-12个月)
                    'ratio': 0.45,
                    'days': [120, 180, 270, 365]
                },
                'long_term': {  # 长期(12个月以上)
                    'ratio': 0.20,
                    'days': [540, 730, 1095]
                }
            }
        else:
            # 检查并补全各期限类型配置
            for term_type in ['short_term', 'medium_term', 'long_term']:
                if term_type not in term_distribution:
                    self.logger.warning(f"No {term_type} config found, using defaults")
                    
                    if term_type == 'short_term':
                        term_distribution[term_type] = {
                            'ratio': 0.35,
                            'days': [30, 60, 90]
                        }
                    elif term_type == 'medium_term':
                        term_distribution[term_type] = {
                            'ratio': 0.45,
                            'days': [120, 180, 270, 365]
                        }
                    else:  # long_term
                        term_distribution[term_type] = {
                            'ratio': 0.20,
                            'days': [540, 730, 1095]
                        }
        
        # 验证比例总和是否接近1.0
        total_ratio = sum(term['ratio'] for term in term_distribution.values())
        if not 0.99 <= total_ratio <= 1.01:
            self.logger.warning(f"Term distribution ratios sum to {total_ratio}, normalizing")
            # 归一化比例
            for term_type in term_distribution:
                term_distribution[term_type]['ratio'] /= total_ratio
        
        self.logger.debug(f"Term distribution config processed with {len(term_distribution)} term types")
        return term_distribution
    
    def get_expected_return_config(self):
        """
        获取预期收益率配置
        
        Returns:
            dict: 预期收益率配置，包含不同风险等级的收益率范围和期限调整系数
        """
        if not self.investment_config:
            self.logger.debug("Investment config not extracted yet, extracting now")
            self.extract_investment_config()
        
        # 从配置中获取预期收益率配置
        expected_return = self.investment_config.get('expected_return', {})
        
        # 如果配置缺失，提供默认值
        if not expected_return:
            self.logger.warning("No expected return config found, using defaults")
            expected_return = {
                'low_risk': {
                    'min': 0.030,
                    'max': 0.045
                },
                'medium_risk': {
                    'min': 0.045,
                    'max': 0.070
                },
                'high_risk': {
                    'min': 0.070,
                    'max': 0.120
                },
                'term_adjustment': {
                    'medium': 0.010,  # 中期产品收益率加成
                    'long': 0.015     # 长期产品收益率加成
                }
            }
        else:
            # 检查各风险级别配置是否完整
            for risk_level in ['low_risk', 'medium_risk', 'high_risk']:
                if risk_level not in expected_return:
                    self.logger.warning(f"No {risk_level} return config found, using defaults")
                    
                    if risk_level == 'low_risk':
                        expected_return[risk_level] = {'min': 0.030, 'max': 0.045}
                    elif risk_level == 'medium_risk':
                        expected_return[risk_level] = {'min': 0.045, 'max': 0.070}
                    else:  # high_risk
                        expected_return[risk_level] = {'min': 0.070, 'max': 0.120}
            
            # 确保期限调整配置存在
            if 'term_adjustment' not in expected_return:
                self.logger.warning("No term adjustment config found, using defaults")
                expected_return['term_adjustment'] = {
                    'medium': 0.010,
                    'long': 0.015
                }
        
        # 验证各风险级别的收益率范围合理性
        for risk_level, rates in expected_return.items():
            if risk_level != 'term_adjustment':
                min_rate = rates.get('min', 0)
                max_rate = rates.get('max', 0)
                
                if min_rate >= max_rate:
                    self.logger.warning(f"Invalid rate range for {risk_level}: min({min_rate}) >= max({max_rate})")
                    # 设置一个合理的默认范围
                    if risk_level == 'low_risk':
                        rates['min'] = 0.030
                        rates['max'] = 0.045
                    elif risk_level == 'medium_risk':
                        rates['min'] = 0.045
                        rates['max'] = 0.070
                    else:  # high_risk
                        rates['min'] = 0.070
                        rates['max'] = 0.120
        
        self.logger.debug(f"Expected return config processed with {len(expected_return)-1} risk levels")
        return expected_return
    
    def get_risk_level_distribution(self):
        """
        获取风险等级分布配置
        
        Returns:
            dict: 风险等级分布配置，包含各风险等级的分布比例
        """
        if not self.investment_config:
            self.logger.debug("Investment config not extracted yet, extracting now")
            self.extract_investment_config()
        
        # 从配置中获取风险等级分布
        risk_level_distribution = self.investment_config.get('risk_level_distribution', {})
        
        # 如果配置缺失，提供默认值
        if not risk_level_distribution or len(risk_level_distribution) == 0:
            self.logger.warning("No risk level distribution config found, using defaults")
            risk_level_distribution = {
                'low': 0.45,     # 低风险产品占比
                'medium': 0.35,  # 中风险产品占比
                'high': 0.20     # 高风险产品占比
            }
        
        # 检查是否包含所有风险级别
        risk_levels = ['low', 'medium', 'high']
        for level in risk_levels:
            if level not in risk_level_distribution:
                self.logger.warning(f"No {level} risk level distribution found, using defaults")
                if level == 'low':
                    risk_level_distribution[level] = 0.45
                elif level == 'medium':
                    risk_level_distribution[level] = 0.35
                else:  # high
                    risk_level_distribution[level] = 0.20
        
        # 验证分布比例总和是否接近1.0
        total_ratio = sum(ratio for level, ratio in risk_level_distribution.items() 
                        if level in risk_levels)
        
        if not 0.99 <= total_ratio <= 1.01:
            self.logger.warning(f"Risk level distribution ratios sum to {total_ratio}, normalizing")
            # 归一化比例
            for level in risk_levels:
                if level in risk_level_distribution:
                    risk_level_distribution[level] /= total_ratio
        
        # 添加一些额外的统计信息到返回结果
        result = {
            'distribution': risk_level_distribution,
            'summary': {
                'low_ratio': risk_level_distribution.get('low', 0),
                'medium_ratio': risk_level_distribution.get('medium', 0),
                'high_ratio': risk_level_distribution.get('high', 0),
                'total_ratio': total_ratio
            }
        }
        
        self.logger.debug(f"Risk level distribution config processed for {len(risk_levels)} risk levels")
        return result
    
    def get_redemption_config(self):
        """
        获取赎回行为配置
        
        Returns:
            dict: 赎回行为配置，包含提前赎回概率、部分赎回比例等参数
        """
        if not self.investment_config:
            self.logger.debug("Investment config not extracted yet, extracting now")
            self.extract_investment_config()
        
        # 默认赎回行为配置
        default_redemption_config = {
            "early_redemption_base_prob": 0.02,  # 每日提前赎回基础概率
            "partial_redemption_prob": 0.4,      # 部分赎回概率
            "partial_redemption_range": [0.2, 0.7],  # 部分赎回金额比例范围
            "market_volatility_impact": 0.5,     # 市场波动对赎回的影响系数
            "min_redemption_amount": 100,        # 最小赎回金额
            "product_type_factors": {            # 不同产品类型的赎回因子
                "monetary_fund": 2.0,            # 货币基金赎回因子(较容易赎回)
                "bond_fund": 1.2,                # 债券基金赎回因子
                "stock_fund": 0.8,               # 股票基金赎回因子(较难赎回)
                "mixed_fund": 1.0,               # 混合基金赎回因子
                "structured_deposit": 0.5        # 结构性存款赎回因子(很难赎回)
            },
            "vip_customer_factor": 0.8,          # VIP客户赎回因子(更理性)
            "time_factors": {                    # 持有时间的影响因子
                "early_stage": 0.3,              # 初期赎回系数(较低)
                "mid_stage": 1.0,                # 中期赎回系数
                "late_stage": 1.5                # 后期赎回系数(较高)
            }
        }
        
        # 尝试从配置中获取自定义赎回配置
        custom_redemption = self.investment_config.get('redemption_config', {})
        
        # 合并默认配置和自定义配置
        redemption_config = default_redemption_config.copy()
        if custom_redemption:
            self.logger.info("Found custom redemption config, merging with defaults")
            
            # 递归合并嵌套字典
            for key, value in custom_redemption.items():
                if isinstance(value, dict) and key in redemption_config and isinstance(redemption_config[key], dict):
                    # 对于嵌套字典，递归合并
                    redemption_config[key].update(value)
                else:
                    # 对于普通值或新键，直接覆盖/添加
                    redemption_config[key] = value
        
        # 验证部分赎回比例范围
        partial_range = redemption_config.get('partial_redemption_range', [0, 0])
        if len(partial_range) != 2 or partial_range[0] >= partial_range[1] or partial_range[0] < 0 or partial_range[1] > 1:
            self.logger.warning(f"Invalid partial redemption range: {partial_range}, using default [0.2, 0.7]")
            redemption_config['partial_redemption_range'] = [0.2, 0.7]
        
        # 验证基础概率值范围
        for prob_key in ['early_redemption_base_prob', 'partial_redemption_prob']:
            prob_value = redemption_config.get(prob_key, -1)
            if prob_value < 0 or prob_value > 1:
                self.logger.warning(f"Invalid probability value for {prob_key}: {prob_value}, using default")
                if prob_key == 'early_redemption_base_prob':
                    redemption_config[prob_key] = 0.02
                else:  # partial_redemption_prob
                    redemption_config[prob_key] = 0.4
        
        self.logger.debug(f"Redemption config processed with {len(redemption_config)} parameters")
        return redemption_config
    
    def build_investment_generator_config(self):
        """
        构建理财生成器需要的完整配置
        
        Returns:
            dict: 完整的理财生成器配置
        """
        self.logger.info("Building complete investment generator configuration")
        
        if not self.investment_config:
            self.logger.debug("Investment config not extracted yet, extracting now")
            self.extract_investment_config()
        
        # 构建完整配置
        complete_config = {
            'risk_level_mapping': self.get_risk_level_mapping(),
            'amount_config': self.get_investment_amount_config(),
            'term_distribution': self.get_term_distribution(),
            'expected_return': self.get_expected_return_config(),
            'risk_level_distribution': self.get_risk_level_distribution(),
            'redemption_config': self.get_redemption_config(),
        }
        
        # 添加时间分布配置
        time_distribution = self.config.get('transaction', {}).get('time_distribution', {})
        if time_distribution:
            complete_config['time_distribution'] = time_distribution
        else:
            self.logger.warning("No time distribution config found, using defaults")
            complete_config['time_distribution'] = {
                'workday_ratio': 0.80,          # 工作日交易占比
                'workday': {
                    'morning': {'ratio': 0.35, 'peak_time': '10:30'},  # 9:00-12:00
                    'lunch': {'ratio': 0.15, 'peak_time': '13:00'},    # 12:00-14:00
                    'afternoon': {'ratio': 0.30, 'peak_time': '15:30'}, # 14:00-17:00
                    'evening': {'ratio': 0.15, 'peak_time': '19:00'},  # 17:00-22:00
                    'night': {'ratio': 0.05, 'peak_time': '23:00'}     # 22:00-次日9:00
                },
                'weekend': {
                    'morning': {'ratio': 0.25, 'peak_time': '11:00'},  # 9:00-12:00
                    'afternoon': {'ratio': 0.45, 'peak_time': '14:00'}, # 12:00-16:00
                    'evening': {'ratio': 0.25, 'peak_time': '19:30'},  # 16:00-22:00
                    'night': {'ratio': 0.05, 'peak_time': '22:30'}     # 22:00-次日9:00
                }
            }
        
        # 添加季节性和周期性配置
        seasonal_cycle = self.config.get('seasonal_cycle', {})
        if seasonal_cycle:
            complete_config['seasonal_cycle'] = seasonal_cycle
        
        # 添加一些通用参数
        if 'system' in self.config:
            system_config = self.config['system']
            complete_config['system'] = {
                'random_seed': system_config.get('random_seed', 42),
                'locale': system_config.get('locale', 'zh_CN'),
                'batch_size': system_config.get('batch_size', 1000)
            }
        
        # 添加配置版本和生成时间
        complete_config['_metadata'] = {
            'version': '1.0',
            'generated_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'config_source': 'file' if self.config_path else 'config_manager'
        }
        
        self.logger.info(f"Complete investment config built with {len(complete_config)} sections")
        return complete_config
