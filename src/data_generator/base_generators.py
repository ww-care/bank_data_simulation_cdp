#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
生成器基类模块

为CDP范式数据生成器提供通用功能和基类。
"""

import uuid
import random
import datetime
import json
import re
import faker
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union, Set

from src.time_manager.time_manager import get_time_manager
from src.logger import get_logger


class BaseGenerator:
    """所有数据生成器的基类，提供通用功能"""
    
    def __init__(self, fake_generator: faker.Faker, config_manager):
        """
        初始化生成器基类
        
        Args:
            fake_generator: Faker实例，用于生成随机数据
            config_manager: 配置管理器实例
        """
        self.faker = fake_generator
        self.config_manager = config_manager
        self.time_manager = get_time_manager()
        self.logger = get_logger(self.__class__.__name__)
        
        # 加载验证规则配置
        self.validation_config = self.config_manager.get_entity_config('validation')
    
    def generate_id(self, prefix: str = '') -> str:
        """
        生成唯一ID
        
        Args:
            prefix: ID前缀
            
        Returns:
            生成的ID
        """
        # 生成16位唯一标识符
        id_value = uuid.uuid4().hex[:16].upper()
        if prefix:
            return f"{prefix}{id_value}"
        return id_value
    
    def get_partition_date(self) -> str:
        """
        获取分区日期，用于设置pt字段
        
        Returns:
            分区日期字符串，格式为YYYY-MM-DD
        """
        return datetime.date.today().strftime('%Y-%m-%d')
    
    def random_choice(self, choices: List, weights: Optional[List[float]] = None) -> Any:
        """
        从列表中随机选择一项
        
        Args:
            choices: 候选项列表
            weights: 权重列表，权重和不需要为1
            
        Returns:
            选中的项
        """
        if not choices:
            return None
        return random.choices(choices, weights=weights, k=1)[0]
    
    def random_date(self, start_date: datetime.date, end_date: datetime.date) -> datetime.date:
        """
        生成指定范围内的随机日期
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            随机日期
        """
        days_diff = (end_date - start_date).days
        if days_diff <= 0:
            return start_date
        
        random_days = random.randint(0, days_diff)
        return start_date + datetime.timedelta(days=random_days)
    
    def random_datetime(self, start_date: datetime.date, end_date: datetime.date,
                       business_hours: bool = False) -> datetime.datetime:
        """
        生成指定范围内的随机日期时间
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            business_hours: 是否限制在营业时间内(9:00-17:00)
            
        Returns:
            随机日期时间
        """
        random_date = self.random_date(start_date, end_date)
        
        if business_hours:
            random_hour = random.randint(9, 17)
        else:
            random_hour = random.randint(0, 23)
            
        random_minute = random.randint(0, 59)
        random_second = random.randint(0, 59)
        
        return datetime.datetime.combine(
            random_date, 
            datetime.time(random_hour, random_minute, random_second)
        )
    
    def datetime_to_timestamp(self, dt: datetime.datetime) -> int:
        """
        将datetime转换为13位时间戳
        
        Args:
            dt: datetime对象
            
        Returns:
            13位时间戳
        """
        return self.time_manager.datetime_to_timestamp(dt)
    
    def timestamp_to_datetime(self, ts: int) -> datetime.datetime:
        """
        将13位时间戳转换为datetime
        
        Args:
            ts: 13位时间戳
            
        Returns:
            datetime对象
        """
        return self.time_manager.timestamp_to_datetime(ts)
    
    def validate_email(self, email: str) -> bool:
        """
        验证邮箱格式
        
        Args:
            email: 邮箱地址
            
        Returns:
            是否有效
        """
        pattern = self.validation_config.get('customer_profile', {}).get(
            'email_pattern', '^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
        return bool(re.match(pattern, email))
    
    def validate_phone(self, phone: str) -> bool:
        """
        验证手机号格式
        
        Args:
            phone: 手机号
            
        Returns:
            是否有效
        """
        pattern = self.validation_config.get('customer_profile', {}).get(
            'phone_pattern', '^1[3-9]\d{9}$')
        return bool(re.match(pattern, phone))
    
    def validate_id_number(self, id_number: str) -> bool:
        """
        验证身份证号格式
        
        Args:
            id_number: 身份证号
            
        Returns:
            是否有效
        """
        pattern = self.validation_config.get('customer_profile', {}).get(
            'id_number_pattern', '^\d{17}[\dXx]$')
        return bool(re.match(pattern, id_number))
    
    def create_json_property(self, data: Dict) -> str:
        """
        创建JSON格式的属性字符串
        
        Args:
            data: 属性数据字典
            
        Returns:
            JSON字符串
        """
        return json.dumps(data, ensure_ascii=False)
    
    def check_required_fields(self, data: Dict, model_type: str) -> List[str]:
        """
        检查必需字段是否存在
        
        Args:
            data: 数据字典
            model_type: 模型类型(customer_profile/business_doc/event/general_archive)
            
        Returns:
            缺失的字段列表
        """
        missing_fields = []
        
        # 基础必需字段
        required_fields = ['pt', 'base_id']
        
        # 根据模型类型添加特定字段
        if model_type == 'business_doc':
            required_fields.extend(['detail_id', 'detail_time'])
        elif model_type == 'event':
            required_fields.extend(['event_id', 'event', 'event_time', 'event_property'])
        
        # 也从配置文件获取额外必需字段
        config_required = self.validation_config.get(model_type, {}).get('required_fields', [])
        if config_required:
            required_fields.extend([f for f in config_required if f not in required_fields])
        
        # 检查字段
        for field in required_fields:
            if field not in data or data[field] is None:
                missing_fields.append(field)
        
        return missing_fields
    
    def distribute_by_ratio(self, ratios: Dict[str, float], count: int) -> Dict[str, int]:
        """
        根据比例分配数量
        
        Args:
            ratios: 类别及其比例
            count: 总数量
            
        Returns:
            各类别分配的数量
        """
        result = {}
        remaining = count
        total_ratio = sum(ratios.values())
        
        # 规范化比例
        normalized_ratios = {k: v/total_ratio for k, v in ratios.items()}
        
        # 分配主要数量
        for category, ratio in normalized_ratios.items():
            category_count = int(count * ratio)
            result[category] = category_count
            remaining -= category_count
        
        # 分配剩余数量
        categories = list(ratios.keys())
        for _ in range(remaining):
            # 按比例权重随机选择一个类别增加1
            category = self.random_choice(categories, list(normalized_ratios.values()))
            result[category] += 1
        
        return result
    
    def normal_distribution_value(self, mean: float, std_dev: float, 
                                 min_value: float = None, max_value: float = None) -> float:
        """
        生成符合正态分布的随机值，支持范围限制
        
        Args:
            mean: 均值
            std_dev: 标准差
            min_value: 最小值限制
            max_value: 最大值限制
            
        Returns:
            随机值
        """
        value = np.random.normal(mean, std_dev)
        
        # 应用范围限制
        if min_value is not None:
            value = max(min_value, value)
        if max_value is not None:
            value = min(max_value, value)
            
        return value
    
    def apply_vip_multiplier(self, base_value: float, is_vip: bool, multiplier: float) -> float:
        """
        应用VIP乘数于基础值
        
        Args:
            base_value: 基础值
            is_vip: 是否VIP
            multiplier: VIP乘数
            
        Returns:
            调整后的值
        """
        if is_vip:
            return base_value * multiplier
        return base_value


class BaseProfileGenerator(BaseGenerator):
    """客户档案范式生成器基类"""
    
    def generate(self, *args, **kwargs) -> List[Dict]:
        """
        生成客户档案数据
        
        Returns:
            客户档案数据列表
        """
        self.logger.warning(f"未实现的generate方法: {self.__class__.__name__}")
        return []
    
    def validate_profile(self, profile: Dict) -> bool:
        """
        验证档案数据的有效性
        
        Args:
            profile: 档案数据
            
        Returns:
            是否有效
        """
        # 检查必需字段
        missing_fields = self.check_required_fields(profile, 'customer_profile')
        if missing_fields:
            self.logger.warning(f"档案数据缺少必需字段: {missing_fields}")
            return False
        
        # 返回验证结果
        return True
    
    def prepare_profile_data(self, profile: Dict) -> Dict:
        """
        准备标准格式的档案数据
        
        Args:
            profile: 原始档案数据
            
        Returns:
            标准格式的档案数据
        """
        # 确保有pt字段
        if 'pt' not in profile:
            profile['pt'] = self.get_partition_date()
        
        # 确保有base_id字段
        if 'base_id' not in profile and 'customer_id' in profile:
            profile['base_id'] = profile['customer_id']
        
        return profile
    
    def clean_profiles(self, profiles: List[Dict]) -> List[Dict]:
        """
        清理和验证档案数据列表
        
        Args:
            profiles: 档案数据列表
            
        Returns:
            清理后的档案数据列表
        """
        cleaned_profiles = []
        
        for profile in profiles:
            # 准备数据
            prepared_profile = self.prepare_profile_data(profile)
            
            # 验证数据
            if self.validate_profile(prepared_profile):
                cleaned_profiles.append(prepared_profile)
        
        self.logger.info(f"清理后的档案数据: {len(cleaned_profiles)}/{len(profiles)}")
        return cleaned_profiles


class BaseDocGenerator(BaseGenerator):
    """业务单据范式生成器基类"""
    
    def generate(self, *args, **kwargs) -> List[Dict]:
        """
        生成业务单据数据
        
        Returns:
            业务单据数据列表
        """
        self.logger.warning(f"未实现的generate方法: {self.__class__.__name__}")
        return []
    
    def validate_doc(self, doc: Dict) -> bool:
        """
        验证单据数据的有效性
        
        Args:
            doc: 单据数据
            
        Returns:
            是否有效
        """
        # 检查必需字段
        missing_fields = self.check_required_fields(doc, 'business_doc')
        if missing_fields:
            self.logger.warning(f"单据数据缺少必需字段: {missing_fields}")
            return False
        
        # 验证时间戳格式
        if 'detail_time' in doc:
            timestamp = doc['detail_time']
            if not isinstance(timestamp, int) or len(str(timestamp)) != 13:
                self.logger.warning(f"单据时间戳格式不正确: {timestamp}")
                return False
        
        # 验证金额非负
        if 'amount' in doc and doc['amount'] < 0:
            self.logger.warning(f"单据金额不能为负: {doc['amount']}")
            return False
        
        # 验证状态值在有效范围内
        if 'status' in doc:
            valid_statuses = self.validation_config.get('business_doc', {}).get(
                'transaction_status', ['success', 'pending', 'failed', 'canceled'])
            if doc['status'] not in valid_statuses:
                self.logger.warning(f"单据状态值无效: {doc['status']}")
                return False
        
        # 返回验证结果
        return True
    
    def prepare_doc_data(self, doc: Dict) -> Dict:
        """
        准备标准格式的单据数据
        
        Args:
            doc: 原始单据数据
            
        Returns:
            标准格式的单据数据
        """
        # 确保有pt字段
        if 'pt' not in doc:
            doc['pt'] = self.get_partition_date()
        
        # 确保有base_id字段
        if 'base_id' not in doc and 'customer_id' in doc:
            doc['base_id'] = doc['customer_id']
        
        # 确保detail_time是13位时间戳
        if 'detail_time' in doc and isinstance(doc['detail_time'], datetime.datetime):
            doc['detail_time'] = self.datetime_to_timestamp(doc['detail_time'])
        
        return doc
    
    def clean_docs(self, docs: List[Dict]) -> List[Dict]:
        """
        清理和验证单据数据列表
        
        Args:
            docs: 单据数据列表
            
        Returns:
            清理后的单据数据列表
        """
        cleaned_docs = []
        
        for doc in docs:
            # 准备数据
            prepared_doc = self.prepare_doc_data(doc)
            
            # 验证数据
            if self.validate_doc(prepared_doc):
                cleaned_docs.append(prepared_doc)
        
        self.logger.info(f"清理后的单据数据: {len(cleaned_docs)}/{len(docs)}")
        return cleaned_docs


class BaseEventGenerator(BaseGenerator):
    """行为事件范式生成器基类"""
    
    def generate(self, *args, **kwargs) -> List[Dict]:
        """
        生成行为事件数据
        
        Returns:
            行为事件数据列表
        """
        self.logger.warning(f"未实现的generate方法: {self.__class__.__name__}")
        return []
    
    def validate_event(self, event: Dict) -> bool:
        """
        验证事件数据的有效性
        
        Args:
            event: 事件数据
            
        Returns:
            是否有效
        """
        # 检查必需字段
        missing_fields = self.check_required_fields(event, 'event')
        if missing_fields:
            self.logger.warning(f"事件数据缺少必需字段: {missing_fields}")
            return False
        
        # 验证时间戳格式
        if 'event_time' in event:
            timestamp = event['event_time']
            if not isinstance(timestamp, int) or len(str(timestamp)) != 13:
                self.logger.warning(f"事件时间戳格式不正确: {timestamp}")
                return False
        
        # 验证事件属性是否为有效JSON
        if 'event_property' in event:
            prop = event['event_property']
            if isinstance(prop, str):
                try:
                    json.loads(prop)
                except json.JSONDecodeError:
                    self.logger.warning(f"事件属性不是有效的JSON: {prop}")
                    return False
        
        # 返回验证结果
        return True
    
    def prepare_event_data(self, event: Dict) -> Dict:
        """
        准备标准格式的事件数据
        
        Args:
            event: 原始事件数据
            
        Returns:
            标准格式的事件数据
        """
        # 确保有pt字段
        if 'pt' not in event:
            event['pt'] = self.get_partition_date()
        
        # 确保有base_id字段
        if 'base_id' not in event and 'customer_id' in event:
            event['base_id'] = event['customer_id']
        
        # 确保event_time是13位时间戳
        if 'event_time' in event and isinstance(event['event_time'], datetime.datetime):
            event['event_time'] = self.datetime_to_timestamp(event['event_time'])
        
        # 确保event_property是JSON字符串
        if 'event_property' in event and isinstance(event['event_property'], dict):
            event['event_property'] = self.create_json_property(event['event_property'])
        
        return event
    
    def clean_events(self, events: List[Dict]) -> List[Dict]:
        """
        清理和验证事件数据列表
        
        Args:
            events: 事件数据列表
            
        Returns:
            清理后的事件数据列表
        """
        cleaned_events = []
        
        for event in events:
            # 准备数据
            prepared_event = self.prepare_event_data(event)
            
            # 验证数据
            if self.validate_event(prepared_event):
                cleaned_events.append(prepared_event)
        
        self.logger.info(f"清理后的事件数据: {len(cleaned_events)}/{len(events)}")
        return cleaned_events
    
    def generate_session_id(self) -> str:
        """
        生成会话ID
        
        Returns:
            会话ID
        """
        return f"SES{uuid.uuid4().hex[:12].upper()}"


class BaseArchiveGenerator(BaseGenerator):
    """通用档案范式生成器基类"""
    
    def generate(self, *args, **kwargs) -> List[Dict]:
        """
        生成通用档案数据
        
        Returns:
            通用档案数据列表
        """
        self.logger.warning(f"未实现的generate方法: {self.__class__.__name__}")
        return []
    
    def validate_archive(self, archive: Dict) -> bool:
        """
        验证档案数据的有效性
        
        Args:
            archive: 档案数据
            
        Returns:
            是否有效
        """
        # 检查必需字段
        missing_fields = self.check_required_fields(archive, 'general_archive')
        if missing_fields:
            self.logger.warning(f"档案数据缺少必需字段: {missing_fields}")
            return False
        
        # 返回验证结果
        return True
    
    def prepare_archive_data(self, archive: Dict) -> Dict:
        """
        准备标准格式的档案数据
        
        Args:
            archive: 原始档案数据
            
        Returns:
            标准格式的档案数据
        """
        # 确保有pt字段
        if 'pt' not in archive:
            archive['pt'] = self.get_partition_date()
        
        # 确保有base_id字段
        if 'base_id' not in archive:
            if 'product_id' in archive:
                archive['base_id'] = archive['product_id']
            elif 'branch_id' in archive:
                archive['base_id'] = archive['branch_id']
            elif 'account_id' in archive:
                archive['base_id'] = archive['account_id']
        
        return archive
    
    def clean_archives(self, archives: List[Dict]) -> List[Dict]:
        """
        清理和验证档案数据列表
        
        Args:
            archives: 档案数据列表
            
        Returns:
            清理后的档案数据列表
        """
        cleaned_archives = []
        
        for archive in archives:
            # 准备数据
            prepared_archive = self.prepare_archive_data(archive)
            
            # 验证数据
            if self.validate_archive(prepared_archive):
                cleaned_archives.append(prepared_archive)
        
        self.logger.info(f"清理后的档案数据: {len(cleaned_archives)}/{len(archives)}")
        return cleaned_archives
