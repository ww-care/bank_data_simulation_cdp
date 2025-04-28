"""
理财记录数据模型
表示一条理财购买记录的所有相关信息
"""


class InvestmentRecord:
    """理财记录数据模型"""
    
    def __init__(self):
        self.investment_id = None          # 理财编码
        self.customer_id = None            # 客户编码
        self.product_id = None             # 产品编号
        self.purchase_time = None          # 买入时间
        self.purchase_date = None          # 购买日期
        self.full_redeem_time = None       # 完全赎回时间
        self.purchase_amount = None        # 购买金额
        self.hold_amount = None            # 剩余金额
        self.status = None                 # 理财状态(持有/部分卖出/完全赎回)
        self.maturity_date = None          # 到期日期
        self.expected_return = None        # 预期收益
        
    def to_dict(self):
        """转换为字典"""
        # TODO: 实现转字典逻辑
        pass
        
    @classmethod
    def from_dict(cls, data):
        """从字典创建对象"""
        # TODO: 实现从字典创建对象逻辑
        pass
