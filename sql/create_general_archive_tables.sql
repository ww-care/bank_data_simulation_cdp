-- ========================================================
-- 银行数据模拟系统(CDP版) - 通用档案相关表创建脚本
-- 创建日期: 2025-04-10
-- 说明: 用于创建通用档案范式相关的数据库表
-- ========================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 创建产品档案表
DROP TABLE IF EXISTS cdp_product_archive;
CREATE TABLE cdp_product_archive (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pt DATE NOT NULL COMMENT '分区字段，数据导入日期',
    base_id VARCHAR(32) NOT NULL COMMENT '产品唯一标识',
    name VARCHAR(128) NOT NULL COMMENT '产品名称',
    bank_name VARCHAR(128) COMMENT '银行名称',
    type VARCHAR(32) COMMENT '产品类型',
    product_type VARCHAR(64) COMMENT '理财产品类型(股票型基金/货币型基金/债券型基金/其他)',
    risk_level VARCHAR(16) COMMENT '风险等级(R1-R5)',
    investment_period INT COMMENT '投资期限(月)',
    expected_yield DECIMAL(6,4) COMMENT '预期收益率',
    minimum_investment DECIMAL(15,2) COMMENT '最低投资金额',
    redemption_way VARCHAR(64) COMMENT '赎回方式(随时赎回/固定赎回)',
    marketing_status VARCHAR(32) COMMENT '营销状态(在售/关闭)',
    
    interest_rate DECIMAL(6,4) COMMENT '利率',
    launch_date DATE COMMENT '产品上线日期',
    
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_base_id (base_id),
    INDEX idx_pt (pt),
    INDEX idx_risk_level (risk_level),
    INDEX idx_product_type (product_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='CDP产品档案表';

-- 创建存款类型档案表
DROP TABLE IF EXISTS cdp_deposit_type_archive;
CREATE TABLE cdp_deposit_type_archive (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pt DATE NOT NULL COMMENT '分区字段，数据导入日期',
    base_id VARCHAR(32) NOT NULL COMMENT '存款类型唯一标识',
    name VARCHAR(128) NOT NULL COMMENT '存款类型名称',
    description TEXT COMMENT '描述',
    base_interest_rate DECIMAL(6,4) COMMENT '基准利率',
    min_term INT COMMENT '最短期限(月)',
    max_term INT COMMENT '最长期限(月)',
    min_amount DECIMAL(15,2) COMMENT '最低金额',
    
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_base_id (base_id),
    INDEX idx_pt (pt)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='CDP存款类型档案表';

-- 创建银行支行档案表
DROP TABLE IF EXISTS cdp_branch_archive;
CREATE TABLE cdp_branch_archive (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pt DATE NOT NULL COMMENT '分区字段，数据导入日期',
    base_id VARCHAR(32) NOT NULL COMMENT '支行唯一标识',
    name VARCHAR(128) NOT NULL COMMENT '支行名称',
    address VARCHAR(256) COMMENT '地址',
    city VARCHAR(64) COMMENT '城市',
    province VARCHAR(64) COMMENT '省份',
    phone VARCHAR(32) COMMENT '联系电话',
    business_hours VARCHAR(128) COMMENT '营业时间',
    manager_id VARCHAR(32) COMMENT '负责人ID',
    status VARCHAR(32) COMMENT '状态',
    
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_base_id (base_id),
    INDEX idx_pt (pt),
    INDEX idx_city (city),
    INDEX idx_province (province)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='CDP银行支行档案表';

-- 创建账户档案表
DROP TABLE IF EXISTS cdp_account_archive;
CREATE TABLE cdp_account_archive (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pt DATE NOT NULL COMMENT '分区字段，数据导入日期',
    base_id VARCHAR(32) NOT NULL COMMENT '账户唯一标识',
    customer_id VARCHAR(32) NOT NULL COMMENT '客户ID',
    account_type VARCHAR(32) COMMENT '账户类型',
    opening_date DATE COMMENT '开户日期',
    balance DECIMAL(15,2) COMMENT '账户余额',
    currency VARCHAR(16) DEFAULT 'CNY' COMMENT '货币类型',
    status VARCHAR(32) COMMENT '账户状态',
    branch_id VARCHAR(32) COMMENT '开户支行ID',
    deposit_type_id VARCHAR(32) COMMENT '存款类型ID',
    interest_rate DECIMAL(6,4) COMMENT '利率',
    term INT COMMENT '期限',
    maturity_date DATE COMMENT '到期日期',
    
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_base_id (base_id),
    INDEX idx_customer_id (customer_id),
    INDEX idx_pt (pt),
    INDEX idx_account_type (account_type),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='CDP账户档案表';

SET FOREIGN_KEY_CHECKS = 1;