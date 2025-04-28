#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库初始化脚本

用于创建数据库和所有必要的表结构。
"""

import os
import sys
import time
import argparse

# 添加项目根目录到系统路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# 导入项目模块
from src.core.database_manager import get_database_manager
from src.logger import get_logger


def init_database(force: bool = False) -> int:
    """
    初始化数据库
    
    Args:
        force: 是否强制重新初始化数据库
        
    Returns:
        退出码(0表示成功)
    """
    logger = get_logger('init_database')
    logger.info("开始初始化数据库...")
    
    try:
        # 获取数据库管理器
        db_manager = get_database_manager()
        
        # 检查连接
        if not db_manager.check_connection_with_retry(max_retries=3, retry_interval=5):
            logger.error("无法连接到数据库，请检查配置和数据库服务")
            return 1
        
        # 初始化数据库
        if not db_manager.init_database():
            logger.error("初始化数据库失败")
            return 1
        
        # 升级数据库架构
        if not db_manager.upgrade_database():
            logger.error("升级数据库结构失败")
            return 1
        
        logger.info("数据库初始化完成")
        return 0
        
    except Exception as e:
        logger.error(f"数据库初始化过程中出错: {str(e)}", exc_info=True)
        return 1
    finally:
        # 关闭连接
        db_manager.close_connection()


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="初始化银行数据模拟系统数据库")
    parser.add_argument("--force", action="store_true", help="强制重新初始化数据库（警告：会删除所有现有数据）")
    args = parser.parse_args()
    
    # 执行数据库初始化
    exit_code = init_database(force=args.force)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
