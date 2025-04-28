# 银行数据模拟系统 (CDP版)

基于CDP数据范式的银行业务数据模拟系统，用于生成用于开发测试、系统演示和数据分析的模拟数据。

## 项目概述

本系统基于CDP（客户数据平台）数据范式设计，模拟生成银行业务环境中的各类数据，包括客户信息、账户数据、交易记录、贷款信息、理财产品等核心业务数据。

系统支持历史数据和实时数据双模式生成：
- 历史模式：一次性生成从一年前到昨天的完整历史数据
- 实时模式：定时生成增量数据，支持13点和次日1点的调度规则

## 数据范式说明

本系统基于CDP数据范式设计，包含四种基本数据类型：

1. **客户档案（Customer Profile）**
   - 描述：主体的profile信息
   - 基础字段：pt(分区字段)、base_id(主体唯一标识)
   - 典型实体：客户、银行经理

2. **业务单据（Business Documents）**
   - 描述：订单、流水等业务单据
   - 基础字段：pt、base_id、detail_id(单据ID)、detail_time(13位时间戳)
   - 典型实体：账户交易、贷款申请、理财购买

3. **行为事件（Behavioral Events）**
   - 描述：主体在各渠道发生的行为
   - 基础字段：pt、base_id、event_id、event(事件代码)、event_time(13位时间戳)、event_property(JSON)
   - 典型实体：APP点击、网银登录、产品浏览

4. **通用档案（General Archives）**
   - 描述：维度表，补充主体信息的维度
   - 基础字段：pt、base_id
   - 典型实体：产品、存款类型、支行、账户

## 项目结构

```
bank_data_simulation_cdp/
├── config/                     # 配置文件目录
│   ├── database.ini            # 数据库连接配置
│   └── bank_data_simulation_config.yaml  # 系统配置文件
├── src/                        # 源代码目录
│   ├── config_manager.py       # 配置管理模块
│   ├── database_manager.py     # 数据库管理模块
│   ├── logger.py               # 日志管理模块
│   ├── time_manager/           # 时间管理模块
│   │   └── time_manager.py     # 时间管理器
│   ├── data_generator/         # 数据生成模块
│   │   ├── data_generator.py   # 数据生成器主控类
│   │   ├── profile_generators.py  # 客户档案生成器
│   │   ├── doc_generators.py      # 业务单据生成器
│   │   ├── event_generators.py    # 行为事件生成器
│   │   └── archive_generators.py  # 通用档案生成器
│   └── validator/              # 数据验证模块
│       └── data_validator.py   # 数据验证器
├── scripts/                    # 脚本目录
│   ├── run_historical.py       # 运行历史数据生成
│   └── run_realtime.py         # 运行实时数据生成
├── logs/                       # 日志目录
└── tests/                      # 测试目录
```

## 使用方法

### 环境准备
1. Python 3.8+
2. MySQL 8.0+
3. 安装依赖: `pip install -r requirements.txt`

### 生成历史数据
```bash
python scripts/run_historical.py
```

### 生成实时数据
```bash
python scripts/run_realtime.py
```

## 配置说明

系统配置文件位于 `config/bank_data_simulation_config.yaml`，支持详细配置各类数据生成参数。
