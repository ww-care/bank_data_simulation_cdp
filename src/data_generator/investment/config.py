"""
理财购买生成器配置文件
包含理财购买生成器的各种配置参数
"""


class InvestmentGeneratorConfig:
    """理财购买生成器配置"""
    
    # 风险等级配置
    RISK_LEVEL_MAPPING = {
        "R1": {"acceptable_risk": ["R1"], "weight": 1.0},
        "R2": {"acceptable_risk": ["R1", "R2"], "weight": 0.9},
        "R3": {"acceptable_risk": ["R1", "R2", "R3"], "weight": 0.8},
        "R4": {"acceptable_risk": ["R1", "R2", "R3", "R4"], "weight": 0.7},
        "R5": {"acceptable_risk": ["R1", "R2", "R3", "R4", "R5"], "weight": 0.6}
    }
    
    # 购买金额范围配置
    PURCHASE_AMOUNT_CONFIG = {
        "min_percentage": 0.01,  # 最小投资额占客户资产比例
        "max_percentage": 0.7,   # 最大投资额占客户资产比例
        "vip_boost": 1.2         # VIP客户投资额提升系数
    }
    
    # 赎回行为配置
    REDEMPTION_CONFIG = {
        "early_redemption_base_prob": 0.02,  # 每日提前赎回基础概率
        "partial_redemption_prob": 0.4,      # 部分赎回概率
        "partial_redemption_range": [0.2, 0.7],  # 部分赎回金额比例范围
        "market_volatility_impact": 0.5      # 市场波动对赎回的影响系数
    }
    
    # 时间分布配置
    TIME_DISTRIBUTION = {
        "peak_hours": [10, 11, 14, 15],  # 高峰时间
        "weekend_weight": 0.6,           # 周末权重
        "month_end_boost": 1.3           # 月末交易提升系数
    }
