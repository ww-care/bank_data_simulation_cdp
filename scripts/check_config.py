#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
配置检查脚本

用于验证配置文件的正确性并显示当前的配置值。
"""

import os
import sys
import json
import argparse

# 添加项目根目录到系统路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# 导入项目模块
from src.core.config_manager import get_config_manager
from src.logger import get_logger


def check_config(show_all: bool = False) -> int:
    """
    检查配置并展示配置信息
    
    Args:
        show_all: 是否显示所有配置信息
        
    Returns:
        退出码(0表示成功)
    """
    logger = get_logger('check_config')
    logger.info("开始检查配置...")
    
    try:
        # 获取配置管理器
        config_manager = get_config_manager()
        
        # 检查系统配置
        system_config = config_manager.get_system_config()
        if not system_config:
            logger.error("系统配置为空或无效")
            return 1
        
        # 检查数据库配置
        db_config = config_manager.get_db_config()
        if not db_config or not all(key in db_config for key in ['host', 'port', 'user', 'database']):
            logger.error("数据库配置不完整")
            return 1
        
        # 检查日志配置
        log_config = config_manager.get_log_config()
        if not log_config:
            logger.error("日志配置为空或无效")
            return 1
        
        # 显示配置信息
        print("\n===== 配置检查结果 =====")
        print("\n--- 系统配置 ---")
        
        if show_all:
            print(json.dumps(system_config, indent=2, ensure_ascii=False))
        else:
            print(f"- 随机种子: {config_manager.get_config_value('system.random_seed')}")
            print(f"- 地区设置: {config_manager.get_config_value('system.locale')}")
            print(f"- 历史数据开始日期: {config_manager.get_config_value('system.historical_start_date')}")
            print(f"- 历史数据结束日期: {config_manager.get_config_value('system.historical_end_date')}")
            print(f"- 批处理大小: {config_manager.get_config_value('system.batch_size')}")
        
        print("\n--- 数据库配置 ---")
        # 隐藏密码
        safe_db_config = db_config.copy()
        if 'password' in safe_db_config:
            safe_db_config['password'] = '********'
        
        for key, value in safe_db_config.items():
            print(f"- {key}: {value}")
        
        print("\n--- 日志配置 ---")
        print(f"- 根日志级别: {log_config.get('loggers', {}).get('', {}).get('level', 'INFO')}")
        print(f"- 日志处理器: {', '.join(log_config.get('loggers', {}).get('', {}).get('handlers', []))}")
        
        print("\n--- 环境变量覆盖 ---")
        env_vars = [var for var in os.environ if var.startswith("BANK_SIM_")]
        if env_vars:
            for var in env_vars:
                value = os.environ[var]
                if 'password' in var.lower():
                    value = '********'
                print(f"- {var}: {value}")
        else:
            print("- 无环境变量覆盖")
        
        print("\n配置验证通过！")
        return 0
        
    except Exception as e:
        logger.error(f"配置检查过程中出错: {str(e)}", exc_info=True)
        return 1


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="检查银行数据模拟系统配置")
    parser.add_argument("--all", action="store_true", help="显示所有配置信息")
    args = parser.parse_args()
    
    # 执行配置检查
    exit_code = check_config(show_all=args.all)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
