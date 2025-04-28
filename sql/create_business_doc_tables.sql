-- ========================================================
-- 银行数据模拟系统(CDP版) - 业务单据相关表创建脚本
-- 创建日期: 2025-04-10
-- 说明: 用于创建业务单据范式相关的数据库表
-- ========================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 创建账户交易单据表 (资金账户流水)
DROP TABLE IF EXISTS cdp_account_transaction;
CREATE TABLE cdp_account_transaction (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pt DATE NOT NULL COMMENT '分区字段，数据导入日期',
    base_id VARCHAR(32) NOT NULL COMMENT '客户唯一标识',
    detail_id VARCHAR(32) NOT NULL COMMENT '资金流水编码(15位)',
    detail_time BIGINT NOT NULL COMMENT '交易时间戳(13位)',
    transaction_date DATE COMMENT '资金交易日期',
    
    account_id VARCHAR(32) COMMENT '账户ID',
    transaction_type VARCHAR(32) COMMENT '资金交易类型(转入/转出)',
    amount DECIMAL(15,2) COMMENT '资金交易金额',
    balance DECIMAL(15,2) COMMENT '资金交易余额',
    currency VARCHAR(16) DEFAULT 'CNY' COMMENT '货币类型',
    status VARCHAR(32) COMMENT '资金交易状态(成功/失败)',
    description TEXT COMMENT '交易描述',
    channel VARCHAR(32) COMMENT '交易渠道',
    remark TEXT COMMENT '备注',
    
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_base_id (base_id),
    INDEX idx_detail_id (detail_id),
    INDEX idx_pt (pt),
    INDEX idx_detail_time (detail_time),
    INDEX idx_transaction_date (transaction_date),
    INDEX idx_account_id (account_id),
    INDEX idx_transaction_type (transaction_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='CDP资金账户流水表';

-- 创建借款记录表
DROP TABLE IF EXISTS cdp_loan_record;
CREATE TABLE cdp_loan_record (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pt DATE NOT NULL COMMENT '分区字段，数据导入日期',
    base_id VARCHAR(32) NOT NULL COMMENT '客户唯一标识',
    detail_id VARCHAR(32) NOT NULL COMMENT '借款单ID',
    detail_time BIGINT NOT NULL COMMENT '借款创建时间戳(13位)',
    
    product_id VARCHAR(32) COMMENT '产品ID',
    loan_amount DECIMAL(15,2) COMMENT '借款金额',
    loan_term_days INT COMMENT '借款周期（天）',
    agreed_interest_rate DECIMAL(6,4) COMMENT '约定利率',
    repayment_method VARCHAR(64) COMMENT '还款方式',
    repayment_settlement_time BIGINT COMMENT '还款结清时间戳',
    is_settled BOOLEAN COMMENT '是否结清',
    repayment_status VARCHAR(32) COMMENT '还款状态(正常还款，逾期)',
    overdue_amount DECIMAL(15,2) COMMENT '逾期金额',
    application_channel_source VARCHAR(32) COMMENT '申请渠道来源(助贷，银行，其他)',
    
    account_id VARCHAR(32) COMMENT '账户ID',
    approval_time BIGINT COMMENT '审批时间戳',
    
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_base_id (base_id),
    INDEX idx_detail_id (detail_id),
    INDEX idx_pt (pt),
    INDEX idx_detail_time (detail_time),
    INDEX idx_product_id (product_id),
    INDEX idx_account_id (account_id),
    INDEX idx_repayment_status (repayment_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='CDP借款记录表';

-- 创建理财购买单据表
DROP TABLE IF EXISTS cdp_investment_order;
CREATE TABLE cdp_investment_order (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pt DATE NOT NULL COMMENT '分区字段，数据导入日期',
    base_id VARCHAR(32) NOT NULL COMMENT '客户唯一标识',
    detail_id VARCHAR(32) NOT NULL COMMENT '理财编码(15位)',
    detail_time BIGINT NOT NULL COMMENT '购买时间戳(13位)',
    
    account_id VARCHAR(32) COMMENT '账户ID',
    product_id VARCHAR(32) COMMENT '产品ID',
    purchase_amount DECIMAL(15,2) COMMENT '购买金额',
    hold_amount DECIMAL(15,2) COMMENT '剩余金额',
    term INT COMMENT '期限(天)',
    
    wealth_purchase_time BIGINT COMMENT '买入时间时间戳',
    wealth_all_redeem_time BIGINT COMMENT '完全赎回时间时间戳',
    wealth_date DATE COMMENT '购买日期',
    wealth_status VARCHAR(32) COMMENT '理财状态(持有/部分卖出/完全赎回)',
    
    maturity_time BIGINT COMMENT '到期时间戳(13位)',
    status VARCHAR(32) COMMENT '投资状态',
    channel VARCHAR(32) COMMENT '购买渠道',
    expected_return DECIMAL(6,4) COMMENT '预期收益率',
    remark TEXT COMMENT '备注',
    
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_base_id (base_id),
    INDEX idx_detail_id (detail_id),
    INDEX idx_pt (pt),
    INDEX idx_detail_time (detail_time),
    INDEX idx_product_id (product_id),
    INDEX idx_account_id (account_id),
    INDEX idx_wealth_date (wealth_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='CDP理财购买单据表';

-- 创建客户资金账户分析表
DROP TABLE IF EXISTS cdp_customer_wealth_analysis;
CREATE TABLE cdp_customer_wealth_analysis (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pt DATE NOT NULL COMMENT '分区字段，数据导入日期',
    base_id VARCHAR(32) NOT NULL COMMENT '客户唯一标识',
    detail_id VARCHAR(32) NOT NULL COMMENT '资金分析编号',
    detail_time BIGINT NOT NULL COMMENT '分析时间戳(13位)',
    
    deposit_type VARCHAR(32) COMMENT '存款类型',
    wealth_amount DECIMAL(15,2) COMMENT '理财金额',
    saving_mount DECIMAL(15,2) COMMENT '存款金额',
    loan_amount DECIMAL(15,2) COMMENT '借款金额',
    debit_card_number INT COMMENT '借记卡数量',
    debit_card_status VARCHAR(32) COMMENT '借记卡状态',
    
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_base_id (base_id),
    INDEX idx_detail_id (detail_id),
    INDEX idx_pt (pt),
    INDEX idx_detail_time (detail_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='CDP客户资金账户分析表';

SET FOREIGN_KEY_CHECKS = 1;