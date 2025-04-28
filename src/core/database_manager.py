#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库管理模块

负责数据库连接、表创建、数据导入和查询等操作，并提供数据库版本管理功能。
"""

import os
import mysql.connector
import pandas as pd
import json
import datetime
import time
from typing import Dict, List, Tuple, Any, Optional, Union

from src.logger import get_logger


class DatabaseManager:
    """数据库管理器类，处理与MySQL数据库的交互"""
    
    def __init__(self):
        """初始化数据库管理器"""
        self.logger = get_logger('database_manager')
        self.connection = None
        self.cursor = None
        
        # 从配置管理器获取数据库配置
        try:
            from src.core.config_manager import get_config_manager
            self.config_manager = get_config_manager()
            self.db_config = self.config_manager.get_db_config()
        except ImportError:
            self.logger.warning("配置管理器导入失败，使用默认数据库配置")
            self.db_config = {
                'host': 'localhost',
                'port': 3306,
                'user': 'bank_user',
                'password': 'bank_password',
                'database': 'bank_data_simulation_cdp',
                'charset': 'utf8mb4',
                'timeout': 10
            }
        
        # SQL 文件目录
        self.sql_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'sql')
        
        # 数据库版本管理
        self.current_version = None
        self.target_version = 1  # 目标数据库版本
    
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
                charset=self.db_config.get('charset', 'utf8mb4'),
                connection_timeout=int(self.db_config.get('timeout', 10))
            )
            self.cursor = self.connection.cursor(dictionary=True)
            self.logger.info("成功连接到MySQL服务器")
            return True
        except Exception as e:
            self.logger.error(f"连接数据库服务器失败: {str(e)}")
            return False
    
    def init_database(self) -> bool:
        """
        初始化数据库，如果不存在则创建
        
        Returns:
            是否成功
        """
        database_name = self.db_config.get('database', 'bank_data_simulation_cdp')
        
        try:
            if not self.connection or not self.cursor:
                if not self.connect():
                    return False
            
            # 检查数据库是否存在
            self.cursor.execute("SHOW DATABASES LIKE %s", (database_name,))
            result = self.cursor.fetchall()
            
            if not result:
                # 创建数据库
                self.cursor.execute(f"CREATE DATABASE {database_name} DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                self.logger.info(f"数据库 {database_name} 创建成功")
            
            # 切换到指定数据库
            self.cursor.execute(f"USE {database_name}")
            self.logger.info(f"已切换到数据库 {database_name}")
            
            # 初始化版本表
            self._init_version_table()
            
            return True
        except Exception as e:
            self.logger.error(f"初始化数据库失败: {str(e)}")
            return False
    
    def _init_version_table(self) -> bool:
        """
        初始化数据库版本表
        
        Returns:
            是否成功
        """
        try:
            # 创建版本表（如果不存在）
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS db_version (
                id INT AUTO_INCREMENT PRIMARY KEY,
                version INT NOT NULL COMMENT '数据库版本号',
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '应用时间',
                description VARCHAR(255) COMMENT '版本描述'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数据库版本表';
            """)
            self.connection.commit()
            
            # 检查是否有版本记录
            self.cursor.execute("SELECT MAX(version) as current_version FROM db_version")
            result = self.cursor.fetchone()
            
            if result and result['current_version'] is not None:
                self.current_version = result['current_version']
                self.logger.info(f"当前数据库版本: {self.current_version}")
            else:
                # 插入初始版本
                self.cursor.execute(
                    "INSERT INTO db_version (version, description) VALUES (0, '初始版本')")
                self.connection.commit()
                self.current_version = 0
                self.logger.info("已初始化数据库版本为0")
            
            return True
        except Exception as e:
            self.logger.error(f"初始化版本表失败: {str(e)}")
            return False
    
    def upgrade_database(self) -> bool:
        """
        升级数据库到最新版本
        
        Returns:
            是否成功
        """
        try:
            if not self.connection or not self.cursor:
                if not self.init_database():
                    return False
            
            # 如果当前版本未知，先获取版本
            if self.current_version is None:
                self.cursor.execute("SELECT MAX(version) as current_version FROM db_version")
                result = self.cursor.fetchone()
                self.current_version = result['current_version'] if result and result['current_version'] is not None else 0
            
            # 如果已经是最新版本，无需升级
            if self.current_version >= self.target_version:
                self.logger.info(f"数据库已经是最新版本 {self.current_version}")
                return True
            
            self.logger.info(f"开始升级数据库，当前版本 {self.current_version}，目标版本 {self.target_version}")
            
            # 逐一应用版本更新
            for version in range(self.current_version + 1, self.target_version + 1):
                self.logger.info(f"应用版本 {version} 更新")
                
                # 应用版本更新
                if version == 1:
                    success = self._apply_version_1()
                # 添加更多版本的更新逻辑...
                # elif version == 2:
                #     success = self._apply_version_2()
                else:
                    self.logger.warning(f"未知的版本 {version}")
                    success = False
                
                if not success:
                    self.logger.error(f"应用版本 {version} 更新失败")
                    return False
                
                # 更新版本记录
                self.cursor.execute(
                    "INSERT INTO db_version (version, description) VALUES (%s, %s)",
                    (version, f"升级到版本 {version}"))
                self.connection.commit()
                self.current_version = version
                
                self.logger.info(f"成功升级到版本 {version}")
            
            self.logger.info(f"数据库升级完成，当前版本 {self.current_version}")
            return True
            
        except Exception as e:
            self.logger.error(f"升级数据库失败: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def _apply_version_1(self) -> bool:
        """
        应用版本1的更新：创建基本表结构
        
        Returns:
            是否成功
        """
        try:
            # 创建系统表
            self._execute_sql_file('create_system_tables.sql')
            
            # 创建CDP表结构
            self._execute_sql_file('create_customer_profile_tables.sql')
            self._execute_sql_file('create_business_doc_tables.sql')
            self._execute_sql_file('create_event_tables.sql')
            self._execute_sql_file('create_general_archive_tables.sql')
            
            return True
        except Exception as e:
            self.logger.error(f"应用版本1更新失败: {str(e)}")
            if self.connection:
                self.connection.rollback()
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
                
            # 分割SQL语句（考虑到SQL语句可能跨多行）
            sql_statements = []
            current_statement = []
            
            for line in sql_content.splitlines():
                line = line.strip()
                
                # 跳过注释行
                if line.startswith('--') or line == '':
                    continue
                
                current_statement.append(line)
                
                if line.endswith(';'):
                    sql_statements.append(' '.join(current_statement))
                    current_statement = []
            
            # 执行SQL语句
            for statement in sql_statements:
                if statement.strip():
                    self.cursor.execute(statement)
                    
            self.connection.commit()
            self.logger.info(f"执行SQL文件成功: {file_name}")
            
        except FileNotFoundError:
            self.logger.error(f"SQL文件不存在: {sql_file_path}")
            raise
        except Exception as e:
            self.logger.error(f"执行SQL文件失败: {file_name}, 错误: {str(e)}")
            raise
    
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
    
    def execute_transaction(self, queries: List[Tuple[str, Optional[tuple]]]) -> bool:
        """
        执行事务（多个SQL语句）
        
        Args:
            queries: SQL语句和参数的列表，每项为 (query, params) 元组
            
        Returns:
            事务是否成功
        """
        try:
            if not self.connection or not self.cursor:
                if not self.connect():
                    return False
            
            # 关闭自动提交
            self.connection.autocommit = False
            
            # 执行所有查询
            for query, params in queries:
                self.cursor.execute(query, params or ())
            
            # 提交事务
            self.connection.commit()
            
            # 恢复自动提交
            self.connection.autocommit = True
            
            return True
        except Exception as e:
            self.logger.error(f"执行事务失败: {str(e)}")
            if self.connection:
                self.connection.rollback()
                self.connection.autocommit = True
            return False
    
    def table_exists(self, table_name: str) -> bool:
        """
        检查表是否存在
        
        Args:
            table_name: 表名
            
        Returns:
            表是否存在
        """
        try:
            if not self.connection or not self.cursor:
                if not self.connect():
                    return False
            
            database = self.db_config.get('database', 'bank_data_simulation_cdp')
            self.cursor.execute(
                "SELECT COUNT(*) AS count FROM information_schema.tables "
                "WHERE table_schema = %s AND table_name = %s",
                (database, table_name)
            )
            result = self.cursor.fetchone()
            return result['count'] > 0
        except Exception as e:
            self.logger.error(f"检查表 {table_name} 是否存在失败: {str(e)}")
            return False
    
    def get_db_version(self) -> Optional[int]:
        """
        获取当前数据库版本
        
        Returns:
            数据库版本，如果未知则返回None
        """
        try:
            if not self.table_exists('db_version'):
                return None
                
            self.cursor.execute("SELECT MAX(version) as current_version FROM db_version")
            result = self.cursor.fetchone()
            
            if result and result['current_version'] is not None:
                self.current_version = result['current_version']
                return self.current_version
            else:
                return None
        except Exception as e:
            self.logger.error(f"获取数据库版本失败: {str(e)}")
            return None
    
    def check_connection_with_retry(self, max_retries: int = 3, retry_interval: int = 5) -> bool:
        """
        检查数据库连接，如果失败则重试
        
        Args:
            max_retries: 最大重试次数
            retry_interval: 重试间隔(秒)
            
        Returns:
            连接是否成功
        """
        retries = 0
        while retries < max_retries:
            try:
                if self.connection and self.connection.is_connected():
                    return True
                
                # 尝试连接
                if self.connect():
                    return True
                
                # 连接失败，重试
                retries += 1
                if retries < max_retries:
                    self.logger.warning(f"数据库连接失败，{retry_interval}秒后重试 ({retries}/{max_retries})")
                    time.sleep(retry_interval)
                
            except Exception as e:
                self.logger.error(f"检查数据库连接失败: {str(e)}")
                retries += 1
                if retries < max_retries:
                    self.logger.warning(f"将在 {retry_interval} 秒后重试 ({retries}/{max_retries})")
                    time.sleep(retry_interval)
        
        self.logger.error(f"数据库连接失败，已达到最大重试次数 {max_retries}")
        return False


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
        print("数据库连接成功")
        db_manager.init_database()
        db_manager.upgrade_database()
        db_manager.close_connection()
    else:
        print("数据库连接失败")
