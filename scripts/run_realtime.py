#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
实时数据生成脚本

运行此脚本以生成实时数据（按调度规则生成增量数据）
"""

import os
import sys
import time
import schedule
import datetime
import signal

# 添加项目根目录到系统路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# 导入项目模块
from src.data_generator.data_generator import get_data_generator
from src.time_manager.time_manager import get_time_manager
from src.logger import get_logger

# 全局变量
running = True
logger = get_logger('realtime_generation')

def signal_handler(signum, frame):
    """
    信号处理函数，用于优雅地停止调度
    """
    global running
    logger.info(f"收到信号 {signum}，准备停止调度...")
    running = False

def generate_morning_data():
    """
    生成当天0-12点的数据
    """
    logger.info("开始生成当天0-12点数据...")
    
    try:
        # 获取数据生成器
        generator = get_data_generator()
        
        # 获取时间管理器
        time_manager = get_time_manager()
        
        # 计算当天0-12点的时间范围
        now = datetime.datetime.now()
        start_time = datetime.datetime.combine(now.date(), datetime.time(0, 0, 0))
        end_time = datetime.datetime.combine(now.date(), datetime.time(12, 0, 0))
        
        logger.info(f"当天0-12点时间范围: {start_time} 至 {end_time}")
        
        # 生成实时数据
        stats = generator.generate_data_for_timeperiod(start_time, end_time, mode='realtime')
        
        logger.info(f"当天0-12点数据生成完成，生成记录数: {sum(stats.values()) if stats else 0}")
        for entity, count in (stats or {}).items():
            logger.info(f"  - {entity}: {count} 条记录")
    
    except Exception as e:
        logger.error(f"当天0-12点数据生成失败: {str(e)}", exc_info=True)

def generate_evening_data():
    """
    生成前一天13-23点的数据
    """
    logger.info("开始生成前一天13-23点数据...")
    
    try:
        # 获取数据生成器
        generator = get_data_generator()
        
        # 获取时间管理器
        time_manager = get_time_manager()
        
        # 计算前一天13-23点的时间范围
        now = datetime.datetime.now()
        yesterday = now.date() - datetime.timedelta(days=1)
        start_time = datetime.datetime.combine(yesterday, datetime.time(13, 0, 0))
        end_time = datetime.datetime.combine(yesterday, datetime.time(23, 59, 59))
        
        logger.info(f"前一天13-23点时间范围: {start_time} 至 {end_time}")
        
        # 生成实时数据
        stats = generator.generate_data_for_timeperiod(start_time, end_time, mode='realtime')
        
        logger.info(f"前一天13-23点数据生成完成，生成记录数: {sum(stats.values()) if stats else 0}")
        for entity, count in (stats or {}).items():
            logger.info(f"  - {entity}: {count} 条记录")
    
    except Exception as e:
        logger.error(f"前一天13-23点数据生成失败: {str(e)}", exc_info=True)

def main():
    """
    设置调度并启动实时数据生成
    """
    logger.info("启动实时数据生成调度...")
    
    # 注册信号处理函数
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 设置调度
    schedule.every().day.at("13:00").do(generate_morning_data)
    schedule.every().day.at("01:00").do(generate_evening_data)
    
    logger.info("实时数据生成调度已设置：")
    logger.info("  - 每天 13:00 生成当天 0-12 点数据")
    logger.info("  - 每天 01:00 生成前一天 13-23 点数据")
    
    # 运行调度循环
    global running
    while running:
        schedule.run_pending()
        time.sleep(10)
    
    logger.info("实时数据生成调度已停止")
    return 0

if __name__ == "__main__":
    sys.exit(main())
