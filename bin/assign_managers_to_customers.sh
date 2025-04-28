#!/bin/bash
# ======================================================
# 银行经理与客户分配关系脚本
# 作用：对已生成的客户和经理数据执行分配操作
# ======================================================

# 设置脚本路径和项目根目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 输出日志函数
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    log "错误: 未找到python3命令，请确保已安装Python 3"
    exit 1
fi

# 默认参数
CUSTOMER_FILE="$PROJECT_ROOT/data/customer_data.json"
MANAGER_FILE="$PROJECT_ROOT/data/manager_data.json"
OUTPUT_FORMAT="json"  # 可选: json, csv, db
OUTPUT_FILE="$PROJECT_ROOT/data/assignments.json"
LOG_FILE="$PROJECT_ROOT/logs/assignment_$(date '+%Y%m%d').log"

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --customer-file)
            CUSTOMER_FILE="$2"
            shift 2
            ;;
        --manager-file)
            MANAGER_FILE="$2"
            shift 2
            ;;
        --output)
            OUTPUT_FORMAT="$2"
            shift 2
            ;;
        --output-file)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --log-file)
            LOG_FILE="$2"
            shift 2
            ;;
        --help)
            echo "银行经理与客户分配关系工具"
            echo "用法: $0 [选项]"
            echo "选项:"
            echo "  --customer-file 文件  客户数据文件路径 (默认: PROJECT_ROOT/data/customer_data.json)"
            echo "  --manager-file 文件   经理数据文件路径 (默认: PROJECT_ROOT/data/manager_data.json)"
            echo "  --output 类型         输出格式: json, csv, db (默认: json)"
            echo "  --output-file 文件    输出文件路径 (默认: PROJECT_ROOT/data/assignments.json)"
            echo "  --log-file 文件       日志文件路径"
            echo "  --help                显示帮助信息"
            exit 0
            ;;
        *)
            log "未知参数: $1"
            exit 1
            ;;
    esac
done

# 检查文件是否存在
if [ ! -f "$CUSTOMER_FILE" ]; then
    log "错误: 客户数据文件不存在: $CUSTOMER_FILE"
    exit 1
fi

if [ ! -f "$MANAGER_FILE" ]; then
    log "错误: 经理数据文件不存在: $MANAGER_FILE"
    exit 1
fi

# 创建需要的目录
mkdir -p "$(dirname "$OUTPUT_FILE")"
mkdir -p "$(dirname "$LOG_FILE")"

# 记录开始消息
log "开始执行银行经理与客户分配操作" | tee -a "$LOG_FILE"
log "客户数据文件: $CUSTOMER_FILE" | tee -a "$LOG_FILE"
log "经理数据文件: $MANAGER_FILE" | tee -a "$LOG_FILE"
log "输出格式: $OUTPUT_FORMAT" | tee -a "$LOG_FILE"
log "输出文件: $OUTPUT_FILE" | tee -a "$LOG_FILE"

# 创建并执行Python脚本
PYTHON_SCRIPT=$(cat << EOF
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
银行经理与客户分配操作脚本
"""

import os
import sys
import json
import datetime
import pandas as pd

# 将项目根目录添加到系统路径
project_root = "$PROJECT_ROOT"
sys.path.insert(0, project_root)

from src.config_manager import get_config_manager
from src.database_manager import get_database_manager
from src.data_generator.relationship_manager import ManagerClientAssignment

def main():
    """主函数"""
    customer_file = "$CUSTOMER_FILE"
    manager_file = "$MANAGER_FILE"
    
    # 加载客户数据
    print(f"正在加载客户数据: {customer_file}")
    try:
        with open(customer_file, 'r', encoding='utf-8') as f:
            customers = json.load(f)
        print(f"已加载 {len(customers)} 个客户，其中 {sum(1 for c in customers if c.get('is_vip', False))} 个VIP客户")
    except Exception as e:
        print(f"加载客户数据失败: {str(e)}")
        return 1
    
    # 加载经理数据
    print(f"正在加载经理数据: {manager_file}")
    try:
        with open(manager_file, 'r', encoding='utf-8') as f:
            managers = json.load(f)
        print(f"已加载 {len(managers)} 个经理")
    except Exception as e:
        print(f"加载经理数据失败: {str(e)}")
        return 1
    
    # 创建分配器并执行分配
    print("开始执行客户经理分配...")
    assignment = ManagerClientAssignment(managers, customers)
    assignments = assignment.assign_clients()
    
    # 更新经理的客户数量字段
    print("更新经理客户数量...")
    for manager in managers:
        manager_id = manager['base_id']
        assigned_clients = assignments.get(manager_id, [])
        manager['current_client_count'] = len(assigned_clients)
        manager['active_client_count'] = int(len(assigned_clients) * 0.8)  # 假设80%的客户是活跃的
    
    # 根据输出格式保存结果
    output_format = "$OUTPUT_FORMAT"
    output_file = "$OUTPUT_FILE"
    
    if output_format == "json":
        # 格式化数据用于JSON输出
        formatted_assignments = []
        for manager_id, customer_ids in assignments.items():
            manager_info = next((m for m in managers if m['base_id'] == manager_id), {})
            manager_name = manager_info.get('name', '')
            position = manager_info.get('position', '')
            
            formatted_assignments.append({
                'manager_id': manager_id,
                'manager_name': manager_name,
                'position': position,
                'customer_count': len(customer_ids),
                'customer_ids': customer_ids
            })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(formatted_assignments, f, ensure_ascii=False, indent=2)
        print(f"已将分配结果保存为JSON: {output_file}")
    
    elif output_format == "csv":
        # 格式化数据用于CSV输出
        rows = []
        for manager_id, customer_ids in assignments.items():
            manager_info = next((m for m in managers if m['base_id'] == manager_id), {})
            manager_name = manager_info.get('name', '')
            position = manager_info.get('position', '')
            
            for customer_id in customer_ids:
                customer_info = next((c for c in customers if c['base_id'] == customer_id), {})
                customer_name = customer_info.get('name', '')
                is_vip = customer_info.get('is_vip', False)
                
                rows.append({
                    'manager_id': manager_id,
                    'manager_name': manager_name,
                    'position': position,
                    'customer_id': customer_id,
                    'customer_name': customer_name,
                    'is_vip': is_vip
                })
        
        df = pd.DataFrame(rows)
        df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"已将分配结果保存为CSV: {output_file}")
    
    elif output_format == "db":
        # 保存到数据库
        result = assignment.save_to_database()
        if result:
            print("已成功将分配结果保存到数据库")
        else:
            print("保存分配结果到数据库失败")
    
    # 保存更新后的经理数据
    manager_output_file = os.path.splitext(manager_file)[0] + "_updated.json"
    with open(manager_output_file, 'w', encoding='utf-8') as f:
        json.dump(managers, f, ensure_ascii=False, indent=2)
    print(f"已保存更新后的经理数据: {manager_output_file}")
    
    # 输出统计信息
    print("分配统计信息:")
    assigned_count = sum(len(cids) for cids in assignments.values())
    total_count = len(customers)
    assignment_rate = (assigned_count / total_count) * 100 if total_count > 0 else 0
    print(f"客户分配完成率: {assignment_rate:.2f}% ({assigned_count}/{total_count})")
    
    # 按职位统计
    position_stats = {}
    for manager in managers:
        position = manager.get('position', '未知')
        manager_id = manager['base_id']
        client_count = len(assignments.get(manager_id, []))
        
        if position not in position_stats:
            position_stats[position] = {
                'managers': 0,
                'customers': 0
            }
        
        position_stats[position]['managers'] += 1
        position_stats[position]['customers'] += client_count
    
    for position, stats in position_stats.items():
        avg_customers = stats['customers'] / stats['managers'] if stats['managers'] > 0 else 0
        print(f"{position}: {stats['managers']}人, 平均 {avg_customers:.2f} 客户/人")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
EOF
)

# 执行Python脚本
log "执行分配操作..." | tee -a "$LOG_FILE"
python3 -c "$PYTHON_SCRIPT" 2>&1 | tee -a "$LOG_FILE"

# 检查执行结果
if [ $? -eq 0 ]; then
    log "分配操作成功完成" | tee -a "$LOG_FILE"
    exit 0
else
    log "分配操作失败" | tee -a "$LOG_FILE"
    exit 1
fi
