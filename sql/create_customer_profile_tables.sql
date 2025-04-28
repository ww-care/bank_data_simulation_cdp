-- ========================================================
-- 银行数据模拟系统(CDP版) - 客户档案相关表创建脚本
-- 创建日期: 2025-04-10
-- 说明: 用于创建客户档案范式相关的数据库表
-- ========================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 创建客户档案表
DROP TABLE IF EXISTS cdp_customer_profile;
CREATE TABLE cdp_customer_profile (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pt DATE NOT NULL COMMENT '分区字段，数据导入日期',
    base_id VARCHAR(32) NOT NULL COMMENT '客户唯一标识(12位)',
    name VARCHAR(128) COMMENT '客户姓名',
    id_type VARCHAR(32) COMMENT '证件类型',
    id_number VARCHAR(32) COMMENT '证件号码',
    phone VARCHAR(32) COMMENT '客户电话',
    address VARCHAR(256) COMMENT '地址',
    email VARCHAR(128) COMMENT '客户电子邮件',
    gender VARCHAR(16) COMMENT '客户性别(F/M/O)',
    birth_date DATE COMMENT '客户生日',
    registration_date DATE COMMENT '注册日期',
    customer_type VARCHAR(32) COMMENT '客户类型（个人/企业）',
    credit_score INT COMMENT '信用评分',
    is_vip BOOLEAN COMMENT 'VIP标识',
    branch_id VARCHAR(32) COMMENT '所属支行ID',
    occupation VARCHAR(64) COMMENT '客户职业',
    annual_income DECIMAL(15,2) COMMENT '年收入（个人客户）',
    business_type VARCHAR(64) COMMENT '行业类型（企业客户）',
    annual_revenue DECIMAL(15,2) COMMENT '年营收（企业客户）',
    establishment_date DATE COMMENT '成立日期（企业客户）',
    
    -- 新增匹配需求的字段
    city VARCHAR(64) COMMENT '城市',
    province VARCHAR(64) COMMENT '省份',
    country VARCHAR(64) DEFAULT 'China' COMMENT '国家',
    salary_category VARCHAR(16) COMMENT '客户工资分类(1-8级)',
    member_id VARCHAR(32) COMMENT '会员编码(12位)',
    member_level VARCHAR(16) COMMENT '会员等级(1-5级)',
    member_last_month_level VARCHAR(16) COMMENT '会员上月等级(1-5级)',
    is_member_level_up BOOLEAN COMMENT '会员等级是否提升',
    risk_level VARCHAR(16) COMMENT '风险偏好等级(R1-R5)',
    customer_churn_tag BOOLEAN COMMENT '当前持仓较上月日均持仓金额流失一半标识',
    is_churn_this_week BOOLEAN COMMENT '本周新增流失客户标识',
    is_high_consumption BOOLEAN COMMENT '是否存在单笔高额消费',
    monthly_average_amount DECIMAL(15,2) COMMENT '客户月均消费',
    
    -- 授信相关字段
    credit_account_id VARCHAR(32) COMMENT '授信账户ID',
    credit_amount DECIMAL(15,2) COMMENT '授信金额',
    is_credit_in_use BOOLEAN COMMENT '授信是否使用中',
    remaining_limit DECIMAL(15,2) COMMENT '剩余额度',
    limit_utilization_rate DECIMAL(6,2) COMMENT '额度使用率(0-100%)',
    
    -- 产品购买行为标识
    clearance_date DATE COMMENT '用户最近一次清仓日期',
    sell_wealth_date DATE COMMENT '用户最近一次理财产品清仓日',
    sell_all_date DATE COMMENT '用户最近一次清仓日',
    first_purchase_type VARCHAR(64) COMMENT '首次产品购买类型',
    have_wealth BOOLEAN COMMENT '曾持有财富产品持有标识',
    no_use_days INT COMMENT '资金未发生支用天数',
    savings_sell_all_date DATE COMMENT '用户最近一次存款产品清仓日',
    wealth_customer_phase VARCHAR(32) COMMENT '财富客户阶段(注册/首投/老客/召回/流失)',
    
    -- 客户经理关联字段
    manager_id VARCHAR(32) COMMENT '关联的客户经理ID',
    
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_base_id (base_id),
    INDEX idx_pt (pt),
    INDEX idx_manager_id (manager_id),
    INDEX idx_risk_level (risk_level),
    INDEX idx_member_level (member_level),
    INDEX idx_customer_type (customer_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='CDP客户档案表';

-- 创建银行经理档案表
DROP TABLE IF EXISTS cdp_manager_profile;
CREATE TABLE cdp_manager_profile (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pt DATE NOT NULL COMMENT '分区字段，数据导入日期',
    base_id VARCHAR(32) NOT NULL COMMENT '经理唯一标识(12位)',
    name VARCHAR(128) COMMENT '经理姓名',
    gender VARCHAR(16) COMMENT '性别(F/M/O)',
    birth_date DATE COMMENT '出生日期',
    hire_date DATE COMMENT '入职日期',
    department VARCHAR(64) COMMENT '所属部门',
    position VARCHAR(64) COMMENT '职位名称(初级客户经理/高级客户经理)',
    phone VARCHAR(32) COMMENT '联系电话',
    email VARCHAR(128) COMMENT '电子邮箱',
    address VARCHAR(256) COMMENT '家庭住址',
    
    -- 业绩相关字段
    annual_performance DECIMAL(15,2) COMMENT '年度业绩',
    monthly_target DECIMAL(15,2) COMMENT '月度目标',
    current_client_count INT COMMENT '当前管理客户数量',
    active_client_count INT COMMENT '活跃客户数量',
    last_performance_review_date DATE COMMENT '上次业绩评估日期',
    notes TEXT COMMENT '备注信息',
    
    -- 支行关联 
    branch_id VARCHAR(32) COMMENT '所属支行ID',
    
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_base_id (base_id),
    INDEX idx_pt (pt),
    INDEX idx_branch_id (branch_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='CDP银行经理档案表';

-- 创建APP用户表
DROP TABLE IF EXISTS cdp_app_user_profile;
CREATE TABLE cdp_app_user_profile (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pt DATE NOT NULL COMMENT '分区字段，数据导入日期',
    base_id VARCHAR(32) NOT NULL COMMENT '客户唯一标识',
    app_user_id VARCHAR(32) NOT NULL COMMENT 'APP用户ID',
    register_date DATE COMMENT 'APP注册日期',
    register_channel VARCHAR(32) COMMENT '注册渠道',
    device_type VARCHAR(32) COMMENT '设备类型',
    device_os VARCHAR(32) COMMENT '操作系统',
    app_version VARCHAR(32) COMMENT 'APP版本',
    last_login_time BIGINT COMMENT '最近登录时间戳',
    login_count INT COMMENT '登录次数',
    is_active BOOLEAN COMMENT '是否活跃',
    preference_settings JSON COMMENT '偏好设置',
    push_notification_enabled BOOLEAN COMMENT '是否开启推送通知',
    
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_base_id (base_id),
    INDEX idx_app_user_id (app_user_id),
    INDEX idx_pt (pt),
    INDEX idx_register_date (register_date),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='CDP APP用户档案表';

SET FOREIGN_KEY_CHECKS = 1;