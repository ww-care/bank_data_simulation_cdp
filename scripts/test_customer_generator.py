#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
客户档案生成器测试脚本

用于测试客户档案生成器的基本功能
"""

import os
import sys
import json
import pandas as pd
import faker
from pathlib import Path

# 添加项目根目录到系统路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# 导入项目模块
from src.config_manager import get_config_manager
from src.data_generator.profile_generators import CustomerProfileGenerator
from src.logger import get_logger

def main():
    """测试客户档案生成器"""
    logger = get_logger('test_customer_generator')
    
    try:
        # 获取配置管理器
        config_manager = get_config_manager()
        
        # 加载系统配置
        system_config = config_manager.get_system_config()
        
        # 创建Faker实例，配置区域设置
        locale = system_config.get('system', {}).get('locale', 'zh_CN')
        fake = faker.Faker(locale)
        
        # 创建客户档案生成器
        logger.info("初始化客户档案生成器")
        customer_generator = CustomerProfileGenerator(fake, config_manager)
        
        # 生成测试数据
        test_count = 100  # 生成100条测试数据
        logger.info(f"生成 {test_count} 条测试客户数据")
        customers = customer_generator.generate(test_count)
        
        # 检查生成的数据
        logger.info(f"成功生成 {len(customers)} 条客户数据")
        
        # 打印前5条数据
        for i, customer in enumerate(customers[:5]):
            logger.info(f"客户 {i+1}:\n{json.dumps(customer, ensure_ascii=False, default=str, indent=2)}")
        
        # 将数据保存为CSV文件
        output_dir = project_root / "output"
        output_dir.mkdir(exist_ok=True)
        
        # 将数据转换为DataFrame
        df = pd.DataFrame(customers)
        
        # 保存到CSV
        output_file = output_dir / "test_customers.csv"
        df.to_csv(output_file, index=False, encoding='utf-8')
        logger.info(f"数据已保存至: {output_file}")
        
        # 打印数据统计
        logger.info("数据统计:")
        logger.info(f"- 总客户数: {len(customers)}")
        logger.info(f"- 男性客户数: {sum(1 for c in customers if c.get('gender') == 'M')}")
        logger.info(f"- 女性客户数: {sum(1 for c in customers if c.get('gender') == 'F')}")
        logger.info(f"- VIP客户数: {sum(1 for c in customers if c.get('is_vip'))}")
        logger.info(f"- 身份证客户数: {sum(1 for c in customers if c.get('id_type') == '身份证')}")
        
        # 风险等级统计
        risk_levels = {}
        for c in customers:
            risk_level = c.get('risk_level')
            if risk_level:
                risk_levels[risk_level] = risk_levels.get(risk_level, 0) + 1
        
        logger.info("风险等级分布:")
        for level, count in sorted(risk_levels.items()):
            logger.info(f"- {level}: {count} ({count/len(customers)*100:.2f}%)")
        
        return 0
    
    except Exception as e:
        logger.error(f"测试失败: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
