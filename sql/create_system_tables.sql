-- ========================================================
-- 银行数据模拟系统(CDP版) - 系统管理相关表创建脚本
-- 创建日期: 2025-04-10
-- 说明: 用于创建系统管理相关的数据库表
-- ========================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 任务状态表
DROP TABLE IF EXISTS task_state;
CREATE TABLE task_state (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id VARCHAR(32) NOT NULL UNIQUE COMMENT '任务ID',
    task_type VARCHAR(32) NOT NULL COMMENT '任务类型',
    status VARCHAR(16) NOT NULL COMMENT '任务状态',
    start_time DATETIME NOT NULL COMMENT '开始时间',
    end_time DATETIME COMMENT '结束时间',
    current_stage VARCHAR(64) COMMENT '当前阶段',
    progress JSON COMMENT '进度信息',
    parameters JSON COMMENT '任务参数',
    last_error TEXT COMMENT '最近错误信息',
    
    -- 新增调度相关字段
    schedule_type VARCHAR(32) COMMENT '调度类型(13点/1点/手动)',
    next_scheduled_time DATETIME COMMENT '下次计划执行时间',
    last_successful_time DATETIME COMMENT '上次成功执行时间',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_task_id (task_id),
    INDEX idx_status (status),
    INDEX idx_task_type (task_type),
    INDEX idx_next_scheduled_time (next_scheduled_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='任务状态表';

-- 任务检查点表
DROP TABLE IF EXISTS task_checkpoint;
CREATE TABLE task_checkpoint (
    id INT AUTO_INCREMENT PRIMARY KEY,
    checkpoint_id VARCHAR(32) NOT NULL UNIQUE COMMENT '检查点ID',
    task_id VARCHAR(32) NOT NULL COMMENT '关联任务ID',
    checkpoint_time DATETIME NOT NULL COMMENT '检查点创建时间',
    checkpoint_data JSON NOT NULL COMMENT '检查点数据',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_task_id (task_id),
    INDEX idx_checkpoint_id (checkpoint_id),
    FOREIGN KEY (task_id) REFERENCES task_state(task_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='任务检查点表';

-- 性能指标表
DROP TABLE IF EXISTS performance_metrics;
CREATE TABLE performance_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id VARCHAR(32) NOT NULL COMMENT '关联任务ID',
    metric_time DATETIME NOT NULL COMMENT '指标时间',
    cpu_usage FLOAT COMMENT 'CPU使用率(%)',
    memory_usage FLOAT COMMENT '内存使用(MB)',
    generation_rate FLOAT COMMENT '生成速率(记录/秒)',
    entity_type VARCHAR(32) COMMENT '实体类型',
    batch_size INT COMMENT '批处理大小',
    duration_ms INT COMMENT '执行时长(毫秒)',
    records_count INT COMMENT '记录数量',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_task_id (task_id),
    INDEX idx_metric_time (metric_time),
    FOREIGN KEY (task_id) REFERENCES task_state(task_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='性能指标表';

-- 系统配置表
DROP TABLE IF EXISTS system_config;
CREATE TABLE system_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(64) NOT NULL UNIQUE COMMENT '配置键',
    config_value TEXT COMMENT '配置值',
    description VARCHAR(255) COMMENT '描述',
    category VARCHAR(32) COMMENT '分类',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_config_key (config_key),
    INDEX idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统配置表';

-- 系统日志表
DROP TABLE IF EXISTS system_log;
CREATE TABLE system_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    log_time DATETIME NOT NULL COMMENT '日志时间',
    log_level VARCHAR(16) NOT NULL COMMENT '日志级别',
    task_id VARCHAR(32) COMMENT '关联任务ID',
    component VARCHAR(64) COMMENT '组件名称',
    message TEXT NOT NULL COMMENT '日志消息',
    exception TEXT COMMENT '异常信息',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_log_time (log_time),
    INDEX idx_log_level (log_level),
    INDEX idx_task_id (task_id),
    INDEX idx_component (component)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统日志表';

-- 数据生成统计表
DROP TABLE IF EXISTS generation_statistics;
CREATE TABLE generation_statistics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id VARCHAR(32) NOT NULL COMMENT '关联任务ID',
    entity_type VARCHAR(32) NOT NULL COMMENT '实体类型',
    count INT NOT NULL COMMENT '生成数量',
    start_time DATETIME COMMENT '开始时间',
    end_time DATETIME COMMENT '结束时间',
    duration_seconds INT COMMENT '持续时间(秒)',
    average_rate FLOAT COMMENT '平均速率(记录/秒)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_task_id (task_id),
    INDEX idx_entity_type (entity_type),
    FOREIGN KEY (task_id) REFERENCES task_state(task_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数据生成统计表';

-- 数据验证结果表
DROP TABLE IF EXISTS validation_result;
CREATE TABLE validation_result (
    id INT AUTO_INCREMENT PRIMARY KEY,
    validation_id VARCHAR(32) NOT NULL COMMENT '验证ID',
    task_id VARCHAR(32) COMMENT '关联任务ID',
    entity_type VARCHAR(32) NOT NULL COMMENT '实体类型',
    validation_time DATETIME NOT NULL COMMENT '验证时间',
    validation_type VARCHAR(32) NOT NULL COMMENT '验证类型',
    status VARCHAR(16) NOT NULL COMMENT '验证状态',
    total_records INT NOT NULL COMMENT '验证记录总数',
    passed_records INT NOT NULL COMMENT '验证通过记录数',
    failed_records INT NOT NULL COMMENT '验证失败记录数',
    validation_details JSON COMMENT '验证详情',
    error_samples JSON COMMENT '错误样本',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_validation_id (validation_id),
    INDEX idx_task_id (task_id),
    INDEX idx_entity_type (entity_type),
    INDEX idx_validation_time (validation_time),
    INDEX idx_status (status),
    FOREIGN KEY (task_id) REFERENCES task_state(task_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数据验证结果表';

SET FOREIGN_KEY_CHECKS = 1;