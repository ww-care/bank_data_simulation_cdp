-- ========================================================
-- 银行数据模拟系统(CDP版) - 事件相关表创建脚本
-- 创建日期: 2025-04-10
-- 说明: 用于创建事件范式相关的数据库表
-- ========================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 创建客户行为事件表
DROP TABLE IF EXISTS cdp_customer_event;
CREATE TABLE cdp_customer_event (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pt DATE NOT NULL COMMENT '分区字段，数据导入日期',
    base_id VARCHAR(32) NOT NULL COMMENT '客户唯一标识',
    event_id VARCHAR(32) NOT NULL COMMENT '事件唯一标识',
    event VARCHAR(64) NOT NULL COMMENT '事件代码',
    event_time BIGINT NOT NULL COMMENT '事件发生时间戳(13位)',
    event_property JSON COMMENT '事件属性JSON，包含除基本字段外的所有事件信息',
    
    -- 系统字段
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_base_id (base_id),
    INDEX idx_event_id (event_id),
    INDEX idx_pt (pt),
    INDEX idx_event_time (event_time),
    INDEX idx_event (event)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='CDP客户行为事件表';

-- 创建APP行为事件表
DROP TABLE IF EXISTS cdp_app_event;
CREATE TABLE cdp_app_event (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pt DATE NOT NULL COMMENT '分区字段，数据导入日期',
    base_id VARCHAR(32) NOT NULL COMMENT '客户唯一标识',
    event_id VARCHAR(32) NOT NULL COMMENT '事件唯一标识',
    event VARCHAR(64) NOT NULL COMMENT '事件代码',
    event_time BIGINT NOT NULL COMMENT '事件发生时间戳(13位)',
    event_property JSON COMMENT '事件属性JSON，包含除基本字段外的所有事件信息',
    
    -- 系统字段
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_base_id (base_id),
    INDEX idx_event_id (event_id),
    INDEX idx_pt (pt),
    INDEX idx_event_time (event_time),
    INDEX idx_event (event)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='CDP APP行为事件表';

-- 创建网银行为事件表
DROP TABLE IF EXISTS cdp_web_event;
CREATE TABLE cdp_web_event (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pt DATE NOT NULL COMMENT '分区字段，数据导入日期',
    base_id VARCHAR(32) NOT NULL COMMENT '客户唯一标识',
    event_id VARCHAR(32) NOT NULL COMMENT '事件唯一标识',
    event VARCHAR(64) NOT NULL COMMENT '事件代码',
    event_time BIGINT NOT NULL COMMENT '事件发生时间戳(13位)',
    event_property JSON COMMENT '事件属性JSON，包含除基本字段外的所有事件信息',
    
    -- 系统字段
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_base_id (base_id),
    INDEX idx_event_id (event_id),
    INDEX idx_pt (pt),
    INDEX idx_event_time (event_time),
    INDEX idx_event (event)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='CDP网银行为事件表';

SET FOREIGN_KEY_CHECKS = 1;