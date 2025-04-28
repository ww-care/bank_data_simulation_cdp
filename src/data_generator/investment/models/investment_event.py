"""
理财相关事件数据模型
表示与理财相关的各种行为事件
"""

import json


class InvestmentEvent:
    """理财相关事件数据模型"""
    
    def __init__(self):
        self.event_id = None           # 事件ID
        self.base_id = None            # 客户ID
        self.event = None              # 事件类型
        self.event_time = None         # 事件时间
        self.event_property = {}       # 事件属性(JSON)
        
    def to_dict(self):
        """
        将投资记录对象转换为字典
        
        Returns:
            dict: 包含所有字段的字典表示
        """
        return {
            'investment_id': self.investment_id,
            'customer_id': self.customer_id,
            'product_id': self.product_id,
            'purchase_time': self.purchase_time,
            'purchase_date': self.purchase_date,
            'full_redeem_time': self.full_redeem_time,
            'purchase_amount': self.purchase_amount,
            'hold_amount': self.hold_amount,
            'status': self.status,
            'maturity_date': self.maturity_date,
            'expected_return': self.expected_return
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        从字典创建投资记录对象
        
        Args:
            data (dict): 包含投资记录字段的字典
        
        Returns:
            InvestmentRecord: 创建的投资记录对象
        """
        record = cls()
        record.investment_id = data.get('investment_id')
        record.customer_id = data.get('customer_id')
        record.product_id = data.get('product_id')
        record.purchase_time = data.get('purchase_time')
        record.purchase_date = data.get('purchase_date')
        record.full_redeem_time = data.get('full_redeem_time')
        record.purchase_amount = data.get('purchase_amount')
        record.hold_amount = data.get('hold_amount')
        record.status = data.get('status')
        record.maturity_date = data.get('maturity_date')
        record.expected_return = data.get('expected_return')
        return record
