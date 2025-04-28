@echo off
:: ======================================================
:: 银行经理与客户分配关系脚本 (Windows版)
:: 作用：对已生成的客户和经理数据执行分配操作
:: ======================================================

setlocal enabledelayedexpansion

:: 设置脚本路径和项目根目录
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

:: 设置日期和时间变量
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YEAR=%dt:~0,4%"
set "MONTH=%dt:~4,2%"
set "DAY=%dt:~6,2%"
set "HOUR=%dt:~8,2%"
set "MINUTE=%dt:~10,2%"
set "SECOND=%dt:~12,2%"
set "TIMESTAMP=%YEAR%%MONTH%%DAY%"

:: 输出日志函数
:log
    echo %YEAR%-%MONTH%-%DAY% %HOUR%:%MINUTE%:%SECOND% - %~1
    goto :eof

:: 默认参数
set "CUSTOMER_FILE=%PROJECT_ROOT%\data\customer_data.json"
set "MANAGER_FILE=%PROJECT_ROOT%\data\manager_data.json"
set "OUTPUT_FORMAT=json"
set "OUTPUT_FILE=%PROJECT_ROOT%\data\assignments.json"
set "LOG_FILE=%PROJECT_ROOT%\logs\assignment_%TIMESTAMP%.log"

:: 解析命令行参数
:parse_args
    if "%~1"=="" goto :end_parse_args
    if "%~1"=="--customer-file" (
        set "CUSTOMER_FILE=%~2"
        shift /1
        shift /1
        goto :parse_args
    )
    if "%~1"=="--manager-file" (
        set "MANAGER_FILE=%~2"
        shift /1
        shift /1
        goto :parse_args
    )
    if "%~1"=="--output" (
        set "OUTPUT_FORMAT=%~2"
        shift /1
        shift /1
        goto :parse_args
    )
    if "%~1"=="--output-file" (
        set "OUTPUT_FILE=%~2"
        shift /1
        shift /1
        goto :parse_args
    )
    if "%~1"=="--log-file" (
        set "LOG_FILE=%~2"
        shift /1
        shift /1
        goto :parse_args
    )
    if "%~1"=="--help" (
        echo 银行经理与客户分配关系工具
        echo 用法: %0 [选项]
        echo 选项:
        echo   --customer-file 文件  客户数据文件路径 (默认: PROJECT_ROOT\data\customer_data.json)
        echo   --manager-file 文件   经理数据文件路径 (默认: PROJECT_ROOT\data\manager_data.json)
        echo   --output 类型         输出格式: json, csv, db (默认: json)
        echo   --output-file 文件    输出文件路径 (默认: PROJECT_ROOT\data\assignments.json)
        echo   --log-file 文件       日志文件路径
        echo   --help                显示帮助信息
        exit /b 0
    )
    echo 未知参数: %~1
    exit /b 1
:end_parse_args

:: 检查文件是否存在
if not exist "%CUSTOMER_FILE%" (
    call :log "错误: 客户数据文件不存在: %CUSTOMER_FILE%"
    exit /b 1
)

if not exist "%MANAGER_FILE%" (
    call :log "错误: 经理数据文件不存在: %MANAGER_FILE%"
    exit /b 1
)

:: 创建需要的目录
for %%F in ("%OUTPUT_FILE%") do if not exist "%%~dpF" mkdir "%%~dpF"
for %%F in ("%LOG_FILE%") do if not exist "%%~dpF" mkdir "%%~dpF"

:: 记录开始消息
call :log "开始执行银行经理与客户分配操作" > "%LOG_FILE%"
call :log "客户数据文件: %CUSTOMER_FILE%" >> "%LOG_FILE%"
call :log "经理数据文件: %MANAGER_FILE%" >> "%LOG_FILE%"
call :log "输出格式: %OUTPUT_FORMAT%" >> "%LOG_FILE%"
call :log "输出文件: %OUTPUT_FILE%" >> "%LOG_FILE%"

:: 创建临时Python脚本
set "TEMP_SCRIPT=%TEMP%\assign_managers_to_customers_%RANDOM%.py"

(
echo import os
echo import sys
echo import json
echo import datetime
echo import pandas as pd
echo.
echo # 将项目根目录添加到系统路径
echo project_root = r"%PROJECT_ROOT%"
echo sys.path.insert(0, project_root^)
echo.
echo from src.config_manager import get_config_manager
echo from src.database_manager import get_database_manager
echo from src.data_generator.relationship_manager import ManagerClientAssignment
echo.
echo def main():
echo     """主函数"""
echo     customer_file = r"%CUSTOMER_FILE%"
echo     manager_file = r"%MANAGER_FILE%"
echo.
echo     # 加载客户数据
echo     print(f"正在加载客户数据: {customer_file}")
echo     try:
echo         with open(customer_file, 'r', encoding='utf-8') as f:
echo             customers = json.load(f)
echo         print(f"已加载 {len(customers)} 个客户，其中 {sum(1 for c in customers if c.get('is_vip', False))} 个VIP客户")
echo     except Exception as e:
echo         print(f"加载客户数据失败: {str(e)}")
echo         return 1
echo.
echo     # 加载经理数据
echo     print(f"正在加载经理数据: {manager_file}")
echo     try:
echo         with open(manager_file, 'r', encoding='utf-8') as f:
echo             managers = json.load(f)
echo         print(f"已加载 {len(managers)} 个经理")
echo     except Exception as e:
echo         print(f"加载经理数据失败: {str(e)}")
echo         return 1
echo.
echo     # 创建分配器并执行分配
echo     print("开始执行客户经理分配...")
echo     assignment = ManagerClientAssignment(managers, customers)
echo     assignments = assignment.assign_clients()
echo.
echo     # 更新经理的客户数量字段
echo     print("更新经理客户数量...")
echo     for manager in managers:
echo         manager_id = manager['base_id']
echo         assigned_clients = assignments.get(manager_id, [])
echo         manager['current_client_count'] = len(assigned_clients)
echo         manager['active_client_count'] = int(len(assigned_clients) * 0.8)  # 假设80%%的客户是活跃的
echo.
echo     # 根据输出格式保存结果
echo     output_format = r"%OUTPUT_FORMAT%"
echo     output_file = r"%OUTPUT_FILE%"
echo.
echo     if output_format == "json":
echo         # 格式化数据用于JSON输出
echo         formatted_assignments = []
echo         for manager_id, customer_ids in assignments.items():
echo             manager_info = next((m for m in managers if m['base_id'] == manager_id), {})
echo             manager_name = manager_info.get('name', '')
echo             position = manager_info.get('position', '')
echo.
echo             formatted_assignments.append({
echo                 'manager_id': manager_id,
echo                 'manager_name': manager_name,
echo                 'position': position,
echo                 'customer_count': len(customer_ids),
echo                 'customer_ids': customer_ids
echo             })
echo.
echo         with open(output_file, 'w', encoding='utf-8') as f:
echo             json.dump(formatted_assignments, f, ensure_ascii=False, indent=2)
echo         print(f"已将分配结果保存为JSON: {output_file}")
echo.
echo     elif output_format == "csv":
echo         # 格式化数据用于CSV输出
echo         rows = []
echo         for manager_id, customer_ids in assignments.items():
echo             manager_info = next((m for m in managers if m['base_id'] == manager_id), {})
echo             manager_name = manager_info.get('name', '')
echo             position = manager_info.get('position', '')
echo.
echo             for customer_id in customer_ids:
echo                 customer_info = next((c for c in customers if c['base_id'] == customer_id), {})
echo                 customer_name = customer_info.get('name', '')
echo                 is_vip = customer_info.get('is_vip', False)
echo.
echo                 rows.append({
echo                     'manager_id': manager_id,
echo                     'manager_name': manager_name,
echo                     'position': position,
echo                     'customer_id': customer_id,
echo                     'customer_name': customer_name,
echo                     'is_vip': is_vip
echo                 })
echo.
echo         df = pd.DataFrame(rows)
echo         df.to_csv(output_file, index=False, encoding='utf-8')
echo         print(f"已将分配结果保存为CSV: {output_file}")
echo.
echo     elif output_format == "db":
echo         # 保存到数据库
echo         result = assignment.save_to_database()
echo         if result:
echo             print("已成功将分配结果保存到数据库")
echo         else:
echo             print("保存分配结果到数据库失败")
echo.
echo     # 保存更新后的经理数据
echo     manager_output_file = os.path.splitext(manager_file)[0] + "_updated.json"
echo     with open(manager_output_file, 'w', encoding='utf-8') as f:
echo         json.dump(managers, f, ensure_ascii=False, indent=2)
echo     print(f"已保存更新后的经理数据: {manager_output_file}")
echo.
echo     # 输出统计信息
echo     print("分配统计信息:")
echo     assigned_count = sum(len(cids) for cids in assignments.values())
echo     total_count = len(customers)
echo     assignment_rate = (assigned_count / total_count) * 100 if total_count > 0 else 0
echo     print(f"客户分配完成率: {assignment_rate:.2f}%% ({assigned_count}/{total_count})")
echo.
echo     # 按职位统计
echo     position_stats = {}
echo     for manager in managers:
echo         position = manager.get('position', '未知')
echo         manager_id = manager['base_id']
echo         client_count = len(assignments.get(manager_id, []))
echo.
echo         if position not in position_stats:
echo             position_stats[position] = {
echo                 'managers': 0,
echo                 'customers': 0
echo             }
echo.
echo         position_stats[position]['managers'] += 1
echo         position_stats[position]['customers'] += client_count
echo.
echo     for position, stats in position_stats.items():
echo         avg_customers = stats['customers'] / stats['managers'] if stats['managers'] > 0 else 0
echo         print(f"{position}: {stats['managers']}人, 平均 {avg_customers:.2f} 客户/人")
echo.
echo     return 0
echo.
echo if __name__ == "__main__":
echo     sys.exit(main())
) > "%TEMP_SCRIPT%"

:: 执行Python脚本
call :log "执行分配操作..." >> "%LOG_FILE%"
python "%TEMP_SCRIPT%" 2>&1 >> "%LOG_FILE%"

:: 检查执行结果
if errorlevel 1 (
    call :log "分配操作失败" >> "%LOG_FILE%"
    exit /b 1
) else (
    call :log "分配操作成功完成" >> "%LOG_FILE%"

    :: 清理临时文件
    del "%TEMP_SCRIPT%" >nul 2>&1
    exit /b 0
)
