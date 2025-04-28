#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库管理模块

负责数据库连接、表创建、数据导入和查询等操作。
"""

import os
import mysql.connector
import pandas as pd
import numpy as np
import json
import datetime
from typing import Dict, List, Tuple, Any, Optional, Union

from src.config_manager import get_config_manager
from src.logger import get_logger


class DatabaseManager:
    """数据库管理器类，处理与MySQL数据库的交互"""
    
    def __init__(self):
        """初始化数据库管理器"""
        self.logger = get_logger('database_manager')
        self.config_manager = get_config_manager()
        self.db_config = self.config_manager.get_db_config()
        self.connection = None
        self.cursor = None
        
        # SQL 文件目录
        self.sql_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'sql')
    
    def connect(self) -> bool:
        """
        连接到MySQL数据库
        
        Returns:
            连接是否成功
        """
        try:
            self.connection = mysql.connector.connect(
                host=self.db_config.get('host', 'localhost'),
                port=int(self.db_config.get('port', 3306)),
                user=self.db_config.get('user', 'root'),
                password=self.db_config.get('password', ''),
                database=self.db_config.get('database', 'bank_data_simulation_cdp'),
                charset=self.db_config.get('charset', 'utf8mb4'),
                connection_timeout=int(self.db_config.get('timeout', 10))
            )
            self.cursor = self.connection.cursor(dictionary=True)
            self.logger.info("成功连接到MySQL数据库")
            return True
        except Exception as e:
            self.logger.error(f"连接数据库失败: {str(e)}")
            return False
    
    def close_connection(self):
        """关闭数据库连接"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            self.logger.info("数据库连接已关闭")
        except Exception as e:
            self.logger.error(f"关闭数据库连接时出错: {str(e)}")
    
    def create_tables(self):
        """创建CDP模型相关的数据库表"""
        try:
            if not self.connection or not self.cursor:
                if not self.connect():
                    return False
            
            # 创建客户档案表
            self._create_customer_profile_tables()
            
            # 创建业务单据表
            self._create_business_doc_tables()
            
            # 创建行为事件表
            self._create_event_tables()
            
            # 创建通用档案表
            self._create_general_archive_tables()
            
            self.logger.info("所有表创建完成")
            return True
        except Exception as e:
            self.logger.error(f"创建表时出错: {str(e)}")
            return False
    
    def _execute_sql_file(self, file_name: str):
        """
        执行SQL文件中的建表语句
        
        Args:
            file_name: SQL文件名
        """
        sql_file_path = os.path.join(self.sql_dir, file_name)
        
        try:
            with open(sql_file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
                
            # 分割SQL语句
            sql_statements = sql_content.split(';')
            
            for statement in sql_statements:
                # 跳过空语句
                if statement.strip():
                    self.cursor.execute(statement.strip())
                    
            self.connection.commit()
            self.logger.info(f"执行SQL文件成功: {file_name}")
            
        except Exception as e:
            self.logger.error(f"执行SQL文件失败: {file_name}, 错误: {str(e)}")
            raise
    
    def _create_customer_profile_tables(self):
        """创建客户档案相关表"""
        self._execute_sql_file('create_customer_profile_tables.sql')
        self.logger.info("客户档案相关表创建完成")
    
    def _create_business_doc_tables(self):
        """创建业务单据相关表"""
        self._execute_sql_file('create_business_doc_tables.sql')
        self.logger.info("业务单据相关表创建完成")
    
    def _create_event_tables(self):
        """创建行为事件相关表"""
        self._execute_sql_file('create_event_tables.sql')
        self.logger.info("行为事件相关表创建完成")
    
    def _create_general_archive_tables(self):
        """创建通用档案相关表"""
        self._execute_sql_file('create_general_archive_tables.sql')
        self.logger.info("通用档案相关表创建完成")
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """
        执行SQL查询
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            查询结果列表
        """
        try:
            if not self.connection or not self.cursor:
                if not self.connect():
                    return []
            
            self.cursor.execute(query, params or ())
            result = self.cursor.fetchall()
            return result
        except Exception as e:
            self.logger.error(f"执行查询失败: {str(e)}, SQL: {query}")
            return []
    
    def execute_update(self, query: str, params: Optional[tuple] = None) -> int:
        """
        执行SQL更新语句
        
        Args:
            query: SQL更新语句
            params: 更新参数
            
        Returns:
            影响的行数
        """
        try:
            if not self.connection or not self.cursor:
                if not self.connect():
                    return 0
            
            self.cursor.execute(query, params or ())
            self.connection.commit()
            return self.cursor.rowcount
        except Exception as e:
            self.logger.error(f"执行更新失败: {str(e)}, SQL: {query}")
            if self.connection:
                self.connection.rollback()
            return 0
    
    def import_dataframe(self, table_name: str, df: pd.DataFrame, batch_size: int = 1000) -> int:
        """
        将DataFrame数据导入数据库表
        
        Args:
            table_name: 表名
            df: DataFrame数据
            batch_size: 批处理大小
            
        Returns:
            导入的记录数
        """
        if df.empty:
            self.logger.warning(f"导入到表{table_name}的DataFrame为空")
            return 0
        
        try:
            if not self.connection or not self.cursor:
                if not self.connect():
                    return 0
            
            # 获取列名
            columns = df.columns.tolist()
            
            # 构建INSERT语句
            placeholders = ", ".join(["%s"] * len(columns))
            column_names = ", ".join([f"`{col}`" for col in columns])
            insert_query = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
            
            # 批量导入数据
            total_imported = 0
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i+batch_size]
                values = [tuple(row) for row in batch.values]
                
                self.cursor.executemany(insert_query, values)
                self.connection.commit()
                
                batch_imported = len(batch)
                total_imported += batch_imported
                self.logger.debug(f"已导入 {batch_imported} 条记录到表 {table_name}，累计 {total_imported}/{len(df)}")
            
            self.logger.info(f"成功导入 {total_imported} 条记录到表 {table_name}")
            return total_imported
            
        except Exception as e:
            self.logger.error(f"导入数据到表 {table_name} 失败: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return 0
    
    def check_last_timestamp(self, table_name: str, timestamp_field: str) -> Optional[int]:
        """
        获取表中最后的时间戳
        
        Args:
            table_name: 表名
            timestamp_field: 时间戳字段名
            
        Returns:
            最后的时间戳，如果没有则返回None
        """
        try:
            query = f"SELECT MAX({timestamp_field}) as last_timestamp FROM {table_name}"
            result = self.execute_query(query)
            
            if result and result[0]['last_timestamp'] is not None:
                return result[0]['last_timestamp']
            return None
            
        except Exception as e:
            self.logger.error(f"获取表 {table_name} 最后时间戳失败: {str(e)}")
            return None
    
    def get_active_accounts(self) -> List[Dict]:
        """
        获取所有活跃状态的账户数据
        
        Returns:
            活跃账户数据列表
        """
        try:
            if not self.connection or not self.cursor:
                if not self.connect():
                    return []
            
            # 查询活跃账户
            # 这里假设cdp_account_archive表存在，且status字段表示账户状态
            query = "SELECT * FROM cdp_account_archive WHERE status = 'active'"
            accounts = self.execute_query(query)
            
            # 为每个账户获取关联的客户信息
            if accounts:
                for account in accounts:
                    customer_id = account.get('customer_id')
                    if customer_id:
                        customer_query = f"SELECT * FROM cdp_customer_profile WHERE base_id = %s"
                        customers = self.execute_query(customer_query, (customer_id,))
                        if customers:
                            # 合并客户信息到账户数据中
                            for key, value in customers[0].items():
                                if key not in account and key != 'base_id':
                                    account[key] = value
            
            self.logger.info(f"成功获取 {len(accounts)} 个活跃账户")
            return accounts
            
        except Exception as e:
            self.logger.error(f"获取活跃账户失败: {str(e)}")
            return []
    
    def import_data(self, table_name: str, data_list: List[Dict]) -> int:
        """
        将生成的数据导入数据库表
        
        Args:
            table_name: 表名
            data_list: 数据列表
            
        Returns:
            导入的记录数
        """
        if not data_list:
            self.logger.warning(f"导入到表{table_name}的数据列表为空")
            return 0
        
        try:
            if not self.connection or not self.cursor:
                if not self.connect():
                    return 0
            
            # 转换为DataFrame以便批量导入
            df = pd.DataFrame(data_list)
            
            # 处理特殊类型的数据
            for col in df.columns:
                # 处理日期时间类型
                if df[col].dtype == 'object':
                    # 检查是否有datetime对象
                    if any(isinstance(val, (datetime.datetime, datetime.date)) for val in df[col] if val is not None):
                        # 转换datetime对象为字符串
                        df[col] = df[col].apply(lambda x: x.isoformat() if isinstance(x, (datetime.datetime, datetime.date)) else x)
                
                # 处理JSON类型数据
                if df[col].dtype == 'object':
                    # 检查是否有字典或列表对象
                    if any(isinstance(val, (dict, list)) for val in df[col] if val is not None):
                        # 转换为JSON字符串
                        df[col] = df[col].apply(lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, (dict, list)) else x)
            
            # 使用DataFrame导入函数
            return self.import_dataframe(table_name, df)
            
        except Exception as e:
            self.logger.error(f"导入数据到表 {table_name} 失败: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return 0


# 单例模式
_instance = None

def get_database_manager() -> DatabaseManager:
    """
    获取DatabaseManager的单例实例
    
    Returns:
        DatabaseManager实例
    """
    global _instance
    if _instance is None:
        _instance = DatabaseManager()
    return _instance


if __name__ == "__main__":
    # 简单测试
    db_manager = get_database_manager()
    if db_manager.connect():
        db_manager.create_tables()
        db_manager.close_connection()
