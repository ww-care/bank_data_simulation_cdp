#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简单测试客户档案生成器
"""

import os
import sys
import json
import faker
from pathlib import Path

# 添加项目根目录到系统路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# 导入项目模块
from src.config_manager import get_config_manager
from src.data_generator.profile_generators import CustomerProfileGenerator

def main():
    """简单测试客户档案生成器"""
    print("开始测试客户档案生成器...")
    
    try:
        # 获取配置管理器
        config_manager = get_config_manager()
        
        # 加载系统配置
        system_config = config_manager.get_system_config()
        
        # 创建Faker实例，配置区域设置
        locale = system_config.get('system', {}).get('locale', 'zh_CN')
        fake = faker.Faker(locale)
        
        # 创建客户档案生成器
        print("初始化客户档案生成器")
        customer_generator = CustomerProfileGenerator(fake, config_manager)
        
        # 生成测试数据
        test_count = 10  # 生成10条测试数据
        print(f"生成 {test_count} 条测试客户数据")
        customers = customer_generator.generate(test_count)
        
        # 检查生成的数据
        print(f"成功生成 {len(customers)} 条客户数据")
        
        # 打印生成的数据
        for i, customer in enumerate(customers):
            print(f"\n客户 {i+1}:")
            for key, value in customer.items():
                print(f"  {key}: {value}")
        
        return 0
    
    except Exception as e:
        print(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
