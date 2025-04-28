#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
历史数据生成脚本

运行此脚本以生成历史数据（从一年前到昨天的完整历史数据）
"""

import os
import sys
import time
import datetime

# 添加项目根目录到系统路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# 导入项目模块
from src.data_generator.data_generator import get_data_generator
from src.time_manager.time_manager import get_time_manager
from src.logger import get_logger

def main():
    """
    执行历史数据生成
    """
    logger = get_logger('historical_generation')
    logger.info("开始生成历史数据...")
    
    start_time = time.time()
    
    try:
        # 获取数据生成器
        generator = get_data_generator()
        
        # 获取时间管理器
        time_manager = get_time_manager()
        
        # 计算历史数据的时间范围
        start_date, end_date = time_manager.calculate_historical_period()
        
        logger.info(f"历史数据时间范围: {start_date} 至 {end_date}")
        
        # 生成历史数据
        stats = generator.generate_data(start_date, end_date, mode='historical')
        
        logger.info(f"历史数据生成完成，生成记录数: {sum(stats.values()) if stats else 0}")
        for entity, count in (stats or {}).items():
            logger.info(f"  - {entity}: {count} 条记录")
    
    except Exception as e:
        logger.error(f"历史数据生成失败: {str(e)}", exc_info=True)
        return 1
    
    # 记录执行时间
    elapsed_time = time.time() - start_time
    logger.info(f"历史数据生成耗时: {elapsed_time:.2f} 秒")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
