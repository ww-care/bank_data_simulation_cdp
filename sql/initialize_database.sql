-- ========================================================
-- 银行数据模拟系统(CDP版) - 数据库初始化脚本
-- 创建日期: 2025-04-10
-- 说明: 用于初始化银行数据模拟系统数据库和执行所有表创建脚本
-- ========================================================

-- 设置字符集
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 创建数据库(如果不存在)
CREATE DATABASE IF NOT EXISTS bank_data_simulation CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE bank_data_simulation;

-- 执行各个表创建脚本
SOURCE create_customer_profile_tables.sql;
SOURCE create_business_doc_tables.sql;
SOURCE create_general_archive_tables.sql;
SOURCE create_event_tables.sql;
SOURCE create_system_tables.sql;

-- 恢复外键检查
SET FOREIGN_KEY_CHECKS = 1;

-- 确认数据库初始化完成
SELECT 'Bank Data Simulation System Database Initialized Successfully!' AS Result;