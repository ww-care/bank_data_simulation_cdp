#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
日志管理脚本

用于管理系统日志，包括归档、清理和分析功能。
"""

import os
import sys
import time
import datetime
import argparse
import json
import re
from collections import Counter, defaultdict

# 添加项目根目录到系统路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# 导入项目模块
from src.logger import get_logger, archive_logs, cleanup_old_logs


def list_logs(verbose: bool = False) -> int:
    """
    列出系统日志文件
    
    Args:
        verbose: 是否显示详细信息
        
    Returns:
        退出码(0表示成功)
    """
    logger = get_logger('manage_logs')
    logger.info("列出系统日志文件...")
    
    try:
        # 日志目录
        log_dir = os.path.join(project_root, 'logs')
        
        if not os.path.exists(log_dir):
            print("日志目录不存在")
            return 1
        
        print("\n===== 系统日志文件 =====")
        
        # 主日志目录
        print("\n主日志目录:")
        main_logs = [f for f in os.listdir(log_dir) if os.path.isfile(os.path.join(log_dir, f))]
        
        if not main_logs:
            print("  没有找到日志文件")
        else:
            for log_file in main_logs:
                file_path = os.path.join(log_dir, log_file)
                file_size = os.path.getsize(file_path) / 1024  # KB
                file_mtime = os.path.getmtime(file_path)
                mtime_str = datetime.datetime.fromtimestamp(file_mtime).strftime('%Y-%m-%d %H:%M:%S')
                
                if verbose:
                    line_count = sum(1 for _ in open(file_path, 'r', encoding='utf-8'))
                    print(f"  {log_file} ({file_size:.2f} KB, {line_count} 行, 最后修改: {mtime_str})")
                else:
                    print(f"  {log_file} ({file_size:.2f} KB, 最后修改: {mtime_str})")
        
        # 归档目录
        archive_dir = os.path.join(log_dir, 'archive')
        if os.path.exists(archive_dir):
            print("\n归档目录:")
            archives = os.listdir(archive_dir)
            
            if not archives:
                print("  没有找到归档")
            else:
                for archive in archives:
                    archive_path = os.path.join(archive_dir, archive)
                    if os.path.isdir(archive_path):
                        # 统计归档中的文件数和总大小
                        file_count = 0
                        total_size = 0
                        for root, dirs, files in os.walk(archive_path):
                            file_count += len(files)
                            total_size += sum(os.path.getsize(os.path.join(root, f)) for f in files)
                        
                        # 获取归档创建时间
                        archive_mtime = os.path.getmtime(archive_path)
                        mtime_str = datetime.datetime.fromtimestamp(archive_mtime).strftime('%Y-%m-%d %H:%M:%S')
                        
                        print(f"  {archive} ({file_count} 个文件, {total_size/1024:.2f} KB, 创建于: {mtime_str})")
        
        return 0
        
    except Exception as e:
        logger.error(f"列出日志文件时出错: {str(e)}", exc_info=True)
        return 1


def archive_system_logs(name: str = None) -> int:
    """
    归档系统日志
    
    Args:
        name: 归档名称，默认为当前时间戳
        
    Returns:
        退出码(0表示成功)
    """
    logger = get_logger('manage_logs')
    logger.info("开始归档系统日志...")
    
    try:
        archive_dir = archive_logs(name)
        
        if archive_dir:
            print(f"日志已成功归档到: {archive_dir}")
            return 0
        else:
            print("归档日志失败")
            return 1
        
    except Exception as e:
        logger.error(f"归档系统日志时出错: {str(e)}", exc_info=True)
        return 1


def cleanup_system_logs(days: int = 30) -> int:
    """
    清理系统旧日志
    
    Args:
        days: 保留的天数
        
    Returns:
        退出码(0表示成功)
    """
    logger = get_logger('manage_logs')
    logger.info(f"开始清理 {days} 天前的系统日志...")
    
    try:
        cleanup_old_logs(days)
        print(f"已清理 {days} 天前的旧日志")
        return 0
        
    except Exception as e:
        logger.error(f"清理系统日志时出错: {str(e)}", exc_info=True)
        return 1


def analyze_logs(log_file: str = None, error_only: bool = False, 
                task_id: str = None, start_time: str = None, 
                end_time: str = None) -> int:
    """
    分析日志文件
    
    Args:
        log_file: 日志文件路径，默认为主日志文件
        error_only: 是否只分析错误
        task_id: 筛选特定任务ID
        start_time: 开始时间筛选
        end_time: 结束时间筛选
        
    Returns:
        退出码(0表示成功)
    """
    logger = get_logger('manage_logs')
    logger.info(f"开始分析日志文件: {log_file}")
    
    try:
        # 确定日志文件
        log_dir = os.path.join(project_root, 'logs')
        
        if not log_file:
            log_file = os.path.join(log_dir, 'bank_data_simulation.log')
        elif not os.path.isabs(log_file):
            log_file = os.path.join(log_dir, log_file)
        
        if not os.path.exists(log_file):
            print(f"日志文件不存在: {log_file}")
            return 1
        
        # 解析时间筛选条件
        start_timestamp = None
        if start_time:
            try:
                start_timestamp = time.mktime(datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S').timetuple())
            except ValueError:
                try:
                    start_timestamp = time.mktime(datetime.datetime.strptime(start_time, '%Y-%m-%d').timetuple())
                except ValueError:
                    print(f"无效的开始时间格式: {start_time}，应为 'YYYY-MM-DD' 或 'YYYY-MM-DD HH:MM:SS'")
                    return 1
        
        end_timestamp = None
        if end_time:
            try:
                end_timestamp = time.mktime(datetime.datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S').timetuple())
            except ValueError:
                try:
                    # 设置为当天结束时间
                    dt = datetime.datetime.strptime(end_time, '%Y-%m-%d')
                    dt = dt.replace(hour=23, minute=59, second=59)
                    end_timestamp = time.mktime(dt.timetuple())
                except ValueError:
                    print(f"无效的结束时间格式: {end_time}，应为 'YYYY-MM-DD' 或 'YYYY-MM-DD HH:MM:SS'")
                    return 1
        
        # 分析变量
        log_count = 0
        error_count = 0
        warning_count = 0
        module_stats = Counter()
        task_stats = defaultdict(int)
        error_messages = []
        
        # 日志格式正则表达式
        log_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (\w+) - (\w+) - (.+)'
        
        # 分析日志
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                match = re.match(log_pattern, line)
                if match:
                    timestamp_str, module, level, message = match.groups()
                    
                    # 解析时间戳
                    try:
                        timestamp = time.mktime(datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f').timetuple())
                    except ValueError:
                        # 跳过无法解析的时间
                        continue
                    
                    # 时间筛选
                    if start_timestamp and timestamp < start_timestamp:
                        continue
                    if end_timestamp and timestamp > end_timestamp:
                        continue
                    
                    # 任务ID筛选
                    if task_id:
                        if f"task_id={task_id}" not in message and f"任务 {task_id}" not in message:
                            continue
                    
                    # 错误筛选
                    if error_only and level.lower() not in ['error', 'critical', 'fatal']:
                        continue
                    
                    # 统计
                    log_count += 1
                    module_stats[module] += 1
                    
                    if level.lower() in ['error', 'critical', 'fatal']:
                        error_count += 1
                        error_messages.append((timestamp_str, module, message))
                    elif level.lower() == 'warning':
                        warning_count += 1
                    
                    # 提取任务ID
                    task_match = re.search(r'task_id=(\w+)', message) or re.search(r'任务 (\w+)', message)
                    if task_match:
                        task_id_found = task_match.group(1)
                        task_stats[task_id_found] += 1
        
        # 输出分析结果
        print("\n===== 日志分析结果 =====")
        print(f"日志文件: {log_file}")
        
        if start_time or end_time:
            time_range = []
            if start_time:
                time_range.append(f"从 {start_time}")
            if end_time:
                time_range.append(f"到 {end_time}")
            print(f"时间范围: {' '.join(time_range)}")
        
        if task_id:
            print(f"筛选任务ID: {task_id}")
        
        print(f"\n总日志条数: {log_count}")
        print(f"错误数: {error_count}")
        print(f"警告数: {warning_count}")
        
        if module_stats:
            print("\n模块统计:")
            for module, count in module_stats.most_common(10):
                print(f"  {module}: {count} 条")
        
        if task_stats:
            print("\n任务统计:")
            for task_id, count in sorted(task_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {task_id}: {count} 条")
        
        if error_messages:
            print("\n错误消息:")
            for i, (timestamp, module, message) in enumerate(error_messages[:20]):
                print(f"  {i+1}. [{timestamp}] {module}: {message[:150]}{'...' if len(message) > 150 else ''}")
            
            if len(error_messages) > 20:
                print(f"  ... 以及其他 {len(error_messages) - 20} 条错误")
        
        return 0
        
    except Exception as e:
        logger.error(f"分析日志文件时出错: {str(e)}", exc_info=True)
        return 1


def analyze_json_logs(log_file: str, task_id: str = None, event: str = None) -> int:
    """
    分析JSON格式日志文件
    
    Args:
        log_file: 日志文件路径
        task_id: 筛选特定任务ID
        event: 筛选特定事件类型
        
    Returns:
        退出码(0表示成功)
    """
    logger = get_logger('manage_logs')
    logger.info(f"开始分析JSON日志文件: {log_file}")
    
    try:
        log_dir = os.path.join(project_root, 'logs')
        
        if not os.path.isabs(log_file):
            log_file = os.path.join(log_dir, log_file)
        
        if not os.path.exists(log_file):
            print(f"日志文件不存在: {log_file}")
            return 1
        
        # 分析变量
        log_count = 0
        level_stats = Counter()
        event_stats = Counter()
        module_stats = Counter()
        task_stats = defaultdict(int)
        
        # 分析日志
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    log_data = json.loads(line.strip())
                    
                    # 筛选
                    if task_id and log_data.get('task_id') != task_id:
                        continue
                    
                    if event and log_data.get('event') != event:
                        continue
                    
                    # 统计
                    log_count += 1
                    level_stats[log_data.get('level', 'UNKNOWN')] += 1
                    
                    if 'name' in log_data:
                        module_stats[log_data['name']] += 1
                    
                    if 'event' in log_data:
                        event_stats[log_data['event']] += 1
                    
                    if 'task_id' in log_data:
                        task_stats[log_data['task_id']] += 1
                    
                except json.JSONDecodeError:
                    continue
        
        # 输出分析结果
        print("\n===== JSON日志分析结果 =====")
        print(f"日志文件: {log_file}")
        
        if task_id:
            print(f"筛选任务ID: {task_id}")
        
        if event:
            print(f"筛选事件类型: {event}")
        
        print(f"\n总日志条数: {log_count}")
        
        if level_stats:
            print("\n级别统计:")
            for level, count in level_stats.most_common():
                print(f"  {level}: {count} 条")
        
        if module_stats:
            print("\n模块统计:")
            for module, count in module_stats.most_common(10):
                print(f"  {module}: {count} 条")
        
        if event_stats:
            print("\n事件类型统计:")
            for event, count in event_stats.most_common(10):
                print(f"  {event}: {count} 条")
        
        if task_stats:
            print("\n任务统计:")
            for task_id, count in sorted(task_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {task_id}: {count} 条")
        
        return 0
        
    except Exception as e:
        logger.error(f"分析JSON日志文件时出错: {str(e)}", exc_info=True)
        return 1


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="管理银行数据模拟系统日志")
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # 列出日志命令
    list_parser = subparsers.add_parser('list', help='列出系统日志文件')
    list_parser.add_argument('-v', '--verbose', action='store_true', help='显示详细信息')
    
    # 归档日志命令
    archive_parser = subparsers.add_parser('archive', help='归档系统日志')
    archive_parser.add_argument('-n', '--name', help='归档名称，默认为当前时间戳')
    
    # 清理日志命令
    cleanup_parser = subparsers.add_parser('cleanup', help='清理系统旧日志')
    cleanup_parser.add_argument('-d', '--days', type=int, default=30, help='保留的天数，默认30天')
    
    # 分析日志命令
    analyze_parser = subparsers.add_parser('analyze', help='分析日志文件')
    analyze_parser.add_argument('-f', '--file', help='日志文件路径，默认为主日志文件')
    analyze_parser.add_argument('-e', '--error-only', action='store_true', help='只分析错误')
    analyze_parser.add_argument('-t', '--task-id', help='筛选特定任务ID')
    analyze_parser.add_argument('-s', '--start-time', help='开始时间筛选，格式为YYYY-MM-DD或YYYY-MM-DD HH:MM:SS')
    analyze_parser.add_argument('-end', '--end-time', help='结束时间筛选，格式为YYYY-MM-DD或YYYY-MM-DD HH:MM:SS')
    
    # 分析JSON日志命令
    json_parser = subparsers.add_parser('analyze-json', help='分析JSON格式日志文件')
    json_parser.add_argument('-f', '--file', required=True, help='JSON日志文件路径')
    json_parser.add_argument('-t', '--task-id', help='筛选特定任务ID')
    json_parser.add_argument('-e', '--event', help='筛选特定事件类型')
    
    args = parser.parse_args()
    
    # 执行相应的命令
    if args.command == 'list':
        return list_logs(verbose=args.verbose)
    elif args.command == 'archive':
        return archive_system_logs(name=args.name)
    elif args.command == 'cleanup':
        return cleanup_system_logs(days=args.days)
    elif args.command == 'analyze':
        return analyze_logs(
            log_file=args.file,
            error_only=args.error_only,
            task_id=args.task_id,
            start_time=args.start_time,
            end_time=args.end_time
        )
    elif args.command == 'analyze-json':
        return analyze_json_logs(
            log_file=args.file,
            task_id=args.task_id,
            event=args.event
        )
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
