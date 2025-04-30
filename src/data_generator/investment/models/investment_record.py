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
        """
        将理财记录对象转换为字典格式
        
        处理日期/时间字段的格式化，方便数据库存储和API交互
        
        Returns:
            dict: 包含理财记录所有属性的字典
        """
        import datetime
        
        # 处理时间戳字段函数
        def format_timestamp(timestamp):
            """将各种时间格式转换为13位毫秒时间戳"""
            if timestamp is None:
                return None
            
            # 如果已经是数字时间戳
            if isinstance(timestamp, (int, float)):
                # 确保是13位毫秒级
                if timestamp > 1000000000000:  # 已经是13位
                    return int(timestamp)
                else:  # 转换为13位
                    return int(timestamp * 1000)
            
            # 如果是datetime对象
            if isinstance(timestamp, datetime.datetime):
                return int(timestamp.timestamp() * 1000)
            
            # 如果是字符串，尝试解析
            if isinstance(timestamp, str):
                try:
                    # 尝试解析ISO格式
                    dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    return int(dt.timestamp() * 1000)
                except ValueError:
                    try:
                        # 尝试解析常见日期时间格式
                        dt = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                        return int(dt.timestamp() * 1000)
                    except ValueError:
                        pass
            
            # 无法处理的格式返回None
            return None
        
        # 处理日期字段函数
        def format_date(date_obj):
            """将各种日期格式转换为标准字符串"""
            if date_obj is None:
                return None
            
            # 如果已经是字符串
            if isinstance(date_obj, str):
                return date_obj
            
            # 如果是date对象
            if isinstance(date_obj, datetime.date):
                return date_obj.strftime('%Y-%m-%d')
            
            # 如果是datetime对象
            if isinstance(date_obj, datetime.datetime):
                return date_obj.strftime('%Y-%m-%d')
            
            # 无法处理的格式返回None
            return None
        
        # 构建基础字典
        result = {
            'investment_id': self.investment_id,
            'customer_id': self.customer_id,
            'product_id': self.product_id,
            'purchase_time': format_timestamp(self.purchase_time),
            'purchase_date': format_date(self.purchase_date),
            'full_redeem_time': format_timestamp(self.full_redeem_time),
            'purchase_amount': self.purchase_amount,
            'hold_amount': self.hold_amount,
            'status': self.status,
            'maturity_date': format_date(self.maturity_date),
            'expected_return': self.expected_return
        }
        
        # 生成时间字段（兼容CDP格式）
        if self.purchase_time:
            result['detail_id'] = self.investment_id
            result['base_id'] = self.customer_id
            result['detail_time'] = format_timestamp(self.purchase_time)
            result['wealth_purchase_time'] = format_timestamp(self.purchase_time)
            result['wealth_all_redeem_time'] = format_timestamp(self.full_redeem_time)
            result['wealth_date'] = format_date(self.purchase_date)
            result['wealth_status'] = self.status
        
        # 移除None值字段
        # result = {k: v for k, v in result.items() if v is not None}
        
        return result

    @classmethod
    def from_dict(cls, data):
        """
        从字典创建理财记录对象
        
        处理不同数据源的字段映射，支持标准格式和CDP格式
        
        Args:
            data (dict): 包含理财记录数据的字典
            
        Returns:
            InvestmentRecord: 创建的理财记录对象
        """
        import datetime
        
        # 处理时间戳字段函数
        def parse_timestamp(timestamp):
            """将数字时间戳转换为datetime对象"""
            if timestamp is None:
                return None
            
            # 如果是数字
            if isinstance(timestamp, (int, float)):
                # 判断是秒级还是毫秒级时间戳
                if timestamp > 1000000000000:  # 13位毫秒级时间戳
                    return datetime.datetime.fromtimestamp(timestamp / 1000)
                else:  # 10位秒级时间戳
                    return datetime.datetime.fromtimestamp(timestamp)
            
            # 如果是字符串，尝试转换为数字
            if isinstance(timestamp, str):
                try:
                    timestamp = float(timestamp)
                    # 递归调用处理数字情况
                    return parse_timestamp(timestamp)
                except (ValueError, TypeError):
                    # 尝试解析日期时间字符串
                    try:
                        # 尝试ISO格式
                        return datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    except ValueError:
                        try:
                            # 尝试常见格式
                            return datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            try:
                                # 尝试日期格式
                                return datetime.datetime.strptime(timestamp, '%Y-%m-%d')
                            except ValueError:
                                pass
            
            # 如果已经是datetime对象
            if isinstance(timestamp, datetime.datetime):
                return timestamp
            
            # 无法处理的格式返回None
            return None
        
        # 处理日期字段函数
        def parse_date(date_str):
            """将字符串转换为date对象"""
            if date_str is None:
                return None
            
            # 如果已经是日期对象
            if isinstance(date_str, datetime.date):
                return date_str
            
            # 如果是datetime对象
            if isinstance(date_str, datetime.datetime):
                return date_str.date()
            
            # 如果是字符串
            if isinstance(date_str, str):
                try:
                    return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    try:
                        return datetime.datetime.strptime(date_str, '%Y/%m/%d').date()
                    except ValueError:
                        pass
            
            # 无法处理的格式返回None
            return None
        
        # 创建对象
        investment = cls()
        
        # 处理标准字段
        investment.investment_id = data.get('investment_id') or data.get('detail_id')
        investment.customer_id = data.get('customer_id') or data.get('base_id')
        investment.product_id = data.get('product_id')
        
        # 处理时间和日期字段
        investment.purchase_time = parse_timestamp(data.get('purchase_time') or data.get('wealth_purchase_time') or data.get('detail_time'))
        investment.purchase_date = parse_date(data.get('purchase_date') or data.get('wealth_date'))
        investment.full_redeem_time = parse_timestamp(data.get('full_redeem_time') or data.get('wealth_all_redeem_time'))
        investment.maturity_date = parse_date(data.get('maturity_date'))
        
        # 处理金额字段
        investment.purchase_amount = data.get('purchase_amount')
        investment.hold_amount = data.get('hold_amount')
        
        # 处理状态字段
        investment.status = data.get('status') or data.get('wealth_status')
        
        # 处理预期收益字段
        investment.expected_return = data.get('expected_return')
        
        return investment
