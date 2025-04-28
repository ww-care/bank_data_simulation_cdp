#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
交易描述生成器模块

负责生成符合交易类型的描述文本。
"""

import random
import faker
from typing import Dict, List, Tuple, Optional, Any, Union


class TransactionDescriptionGenerator:
    """交易描述生成器，生成符合交易类型的描述文本"""
    
    def __init__(self, fake_generator: faker.Faker, config: Dict):
        """
        初始化交易描述生成器
        
        Args:
            fake_generator: Faker实例，用于生成随机数据
            config: 配置字典，包含交易描述规则
        """
        self.faker = fake_generator
        self.config = config
        
        # 常用收款方/付款方名称
        self.common_merchants = [
            "京东商城", "天猫超市", "苏宁易购", "唯品会", "美团外卖", 
            "饿了么", "滴滴出行", "哔哩哔哩", "腾讯视频", "爱奇艺",
            "中国移动", "中国电信", "中国联通", "国家电网", "中国石油", 
            "中国石化", "沃尔玛", "家乐福", "麦当劳", "肯德基"
        ]
        
        # 常用公司名称
        self.common_companies = [
            "XX科技有限公司", "XX商贸有限公司", "XX服务有限公司", "XX文化传媒", 
            "XX金融集团", "XX健康管理", "XX教育咨询", "XX建筑工程", 
            "XX信息技术", "XX物流有限公司"
        ]
        
        # 常用工资描述
        self.salary_descriptions = [
            "{}月工资", "{}月薪资", "{}工资发放", "{}月收入", "{}薪酬"
        ]
        
        # 购物类描述
        self.shopping_descriptions = [
            "{}购物消费", "{}商品购买", "{}日用品消费", "{}商城购物", 
            "{}电器消费", "{}服装消费", "{}超市购物"
        ]
        
        # 交通类描述
        self.transportation_descriptions = [
            "{}打车费用", "{}公共交通", "{}高铁票", "{}飞机票", 
            "{}出行服务", "{}交通消费"
        ]
        
        # 餐饮类描述
        self.food_descriptions = [
            "{}餐饮消费", "{}外卖订单", "{}餐厅消费", "{}美食消费",
            "{}咖啡消费", "{}甜品消费"
        ]
        
        # 娱乐类描述
        self.entertainment_descriptions = [
            "{}影院消费", "{}游戏充值", "{}演出票", "{}会员续费",
            "{}娱乐消费", "{}休闲活动"
        ]
        
        # 转账类描述
        self.transfer_descriptions = [
            "转账-{}(尾号{})", "向{}(尾号{})转账", "{}(尾号{})转入", 
            "转入{}(尾号{})", "转出至{}(尾号{})", "{}(尾号{})转账",
            "汇款给{}(尾号{})"
        ]
        
        # 公共事业缴费描述
        self.utility_descriptions = [
            "{}水费缴纳", "{}电费缴纳", "{}燃气费", "{}宽带费用",
            "{}物业费", "{}手机话费", "{}有线电视费"
        ]
    
    def generate_description(self, transaction_type: str, amount: float, 
                           channel: str, frozen: bool = False) -> str:
        """
        根据交易类型和金额生成描述
        
        Args:
            transaction_type: 交易类型
            amount: 交易金额
            channel: 交易渠道
            frozen: 是否是frozen: 是否是冻结账户
            
        Returns:
            交易描述
        """
        # 冻结账户特殊处理
        if frozen:
            if transaction_type == 'inquiry':
                return "账户状态查询-账户已冻结"
            else:
                return "账户已冻结，交易受限"
        
        # 根据交易类型生成描述
        if transaction_type == 'deposit':
            return self._generate_deposit_description(amount, channel)
        elif transaction_type == 'withdrawal':
            return self._generate_withdrawal_description(amount, channel)
        elif transaction_type == 'transfer_in':
            return self._generate_transfer_in_description(amount, channel)
        elif transaction_type == 'transfer_out':
            return self._generate_transfer_out_description(amount, channel)
        elif transaction_type == 'consumption':
            return self._generate_consumption_description(amount, channel)
        elif transaction_type == 'inquiry':
            return self._generate_inquiry_description(channel)
        else:  # other
            return self._generate_other_description(amount, channel)
    
    def _generate_deposit_description(self, amount: float, channel: str) -> str:
        """
        生成存款交易描述
        
        Args:
            amount: 存款金额
            channel: 交易渠道
            
        Returns:
            存款描述
        """
        # 工资类存款（大额存款有一定概率是工资）
        if amount > 5000 and random.random() < 0.3:
            month = random.randint(1, 12)
            salary_template = random.choice(self.salary_descriptions)
            return salary_template.format(f"{month}月")
        
        # 渠道相关描述
        if channel == 'counter':
            return "柜台存款"
        elif channel == 'atm':
            return "ATM存款"
        elif channel == 'online_banking':
            return "网银转账存入"
        elif channel == 'mobile_app':
            return "手机银行存入"
        else:
            return "存款"
    
    def _generate_withdrawal_description(self, amount: float, channel: str) -> str:
        """
        生成取款交易描述
        
        Args:
            amount: 取款金额
            channel: 交易渠道
            
        Returns:
            取款描述
        """
        # 渠道相关描述
        if channel == 'counter':
            return "柜台取款"
        elif channel == 'atm':
            return "ATM取款"
        elif channel == 'online_banking':
            return "网银取款"
        elif channel == 'mobile_app':
            return "手机银行取款"
        else:
            return "取款"
    
    def _generate_transfer_in_description(self, amount: float, channel: str) -> str:
        """
        生成转入交易描述
        
        Args:
            amount: 转入金额
            channel: 交易渠道
            
        Returns:
            转入描述
        """
        # 生成转账来源
        if random.random() < 0.7:  # 70%是个人转账
            name = self.faker.name()
            last_digits = self.faker.numerify('####')
        else:  # 30%是公司转账
            name = random.choice(self.common_companies)
            last_digits = self.faker.numerify('####')
        
        # 使用转账模板
        template = random.choice(self.transfer_descriptions)
        
        if "转入" in template or "收到" in template:
            return template.format(name, last_digits)
        else:
            return template.format(name, last_digits) + "-收款"
    
    def _generate_transfer_out_description(self, amount: float, channel: str) -> str:
        """
        生成转出交易描述
        
        Args:
            amount: 转出金额
            channel: 交易渠道
            
        Returns:
            转出描述
        """
        # 生成转账目标
        if random.random() < 0.7:  # 70%是个人转账
            name = self.faker.name()
            last_digits = self.faker.numerify('####')
        else:  # 30%是公司转账
            name = random.choice(self.common_companies)
            last_digits = self.faker.numerify('####')
        
        # 使用转账模板
        template = random.choice(self.transfer_descriptions)
        
        if "转出" in template or "汇款" in template:
            return template.format(name, last_digits)
        else:
            return template.format(name, last_digits) + "-付款"
    
    def _generate_consumption_description(self, amount: float, channel: str) -> str:
        """
        生成消费交易描述
        
        Args:
            amount: 消费金额
            channel: 交易渠道
            
        Returns:
            消费描述
        """
        # 根据金额范围选择不同类型的消费
        merchant = random.choice(self.common_merchants)
        
        if amount < 100:
            # 小额消费，多为餐饮、交通
            if random.random() < 0.6:
                template = random.choice(self.food_descriptions)
                return template.format(merchant)
            else:
                template = random.choice(self.transportation_descriptions)
                return template.format(merchant)
        elif amount < 500:
            # 中等消费，多为购物、娱乐
            if random.random() < 0.6:
                template = random.choice(self.shopping_descriptions)
                return template.format(merchant)
            else:
                template = random.choice(self.entertainment_descriptions)
                return template.format(merchant)
        else:
            # 大额消费，多为购物、公共事业缴费
            if random.random() < 0.7:
                template = random.choice(self.shopping_descriptions)
                return template.format(merchant)
            else:
                template = random.choice(self.utility_descriptions)
                return template.format(merchant)
    
    def _generate_inquiry_description(self, channel: str) -> str:
        """
        生成查询交易描述
        
        Args:
            channel: 交易渠道
            
        Returns:
            查询描述
        """
        # 渠道相关描述
        if channel == 'counter':
            return "柜台账户查询"
        elif channel == 'atm':
            return "ATM余额查询"
        elif channel == 'online_banking':
            return "网银账户查询"
        elif channel == 'mobile_app':
            return "手机银行查询"
        else:
            return "账户查询"
    
    def _generate_other_description(self, amount: float, channel: str) -> str:
        """
        生成其他类型交易描述
        
        Args:
            amount: 交易金额
            channel: 交易渠道
            
        Returns:
            其他类型交易描述
        """
        # 其他类型交易
        other_descriptions = [
            "账户服务费", "年费", "理财产品申购", "理财产品赎回",
            "结息", "利息收入", "利息支出", "流水打印费用",
            "挂失手续费", "SMS短信服务费", "跨行服务费"
        ]
        
        return random.choice(other_descriptions)