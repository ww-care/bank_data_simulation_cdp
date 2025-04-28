#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
进度追踪器

用于跟踪数据生成任务的进度和性能指标。
"""

import time
import datetime
from typing import Dict, List, Any, Optional

from src.logger import get_logger


class ProgressTracker:
    """进度追踪器，用于记录和报告任务进度"""
    
    def __init__(self, task_id: str = None):
        """
        初始化进度追踪器
        
        Args:
            task_id: 关联的任务ID
        """
        self.logger = get_logger('progress_tracker')
        self.task_id = task_id
        self.start_time = None
        self.last_update_time = None
        self.total_entities = {}  # {entity_name: total_count}
        self.current_progress = {}  # {entity_name: current_count}
        self.generation_rates = {}  # {entity_name: records_per_second}
        self.checkpoint_times = []
    
    def start_tracking(self, task_id: str, total_entities: Dict[str, int]):
        """
        开始追踪任务进度
        
        Args:
            task_id: 任务ID
            total_entities: 各实体类型的总数量
        """
        self.task_id = task_id
        self.start_time = time.time()
        self.last_update_time = self.start_time
        self.total_entities = total_entities
        self.current_progress = {entity: 0 for entity in total_entities}
        
        self.logger.info(f"开始追踪任务 {task_id} 的进度")
        self.logger.info(f"计划生成实体数量: {total_entities}")
    
    def update_progress(self, entity: str, count: int):
        """
        更新特定实体的进度
        
        Args:
            entity: 实体类型
            count: 新增数量
        """
        if entity not in self.current_progress:
            self.current_progress[entity] = 0
            
        if entity not in self.total_entities:
            self.logger.warning(f"实体类型 {entity} 不在计划中")
            self.total_entities[entity] = -1  # 未知总数
        
        # 更新进度
        previous_count = self.current_progress[entity]
        self.current_progress[entity] += count
        
        # 计算生成速率
        current_time = time.time()
        time_diff = current_time - self.last_update_time
        
        if time_diff > 0:
            rate = count / time_diff
            if entity not in self.generation_rates:
                self.generation_rates[entity] = rate
            else:
                # 平滑更新速率 (70% 旧值, 30% 新值)
                self.generation_rates[entity] = 0.7 * self.generation_rates[entity] + 0.3 * rate
        
        self.last_update_time = current_time
        
        # 记录进度日志
        total = self.total_entities[entity]
        current = self.current_progress[entity]
        percentage = (current / total * 100) if total > 0 else "未知"
        
        self.logger.info(f"实体 {entity} 进度更新: +{count} 条记录，"
                        f"当前 {current}/{total if total > 0 else '未知'} ({percentage}%)")
    
    def get_progress(self) -> Dict[str, Any]:
        """
        获取当前进度信息
        
        Returns:
            进度信息字典
        """
        current_time = time.time()
        elapsed_time = current_time - self.start_time
        
        # 计算总体完成百分比
        total_records = sum(self.total_entities.values())
        total_completed = sum(self.current_progress.values())
        
        if total_records <= 0:
            completion_percentage = 0
        else:
            completion_percentage = total_completed / total_records * 100
        
        # 估计剩余时间
        if completion_percentage > 0:
            estimated_total_time = elapsed_time / (completion_percentage / 100)
            estimated_remaining_time = estimated_total_time - elapsed_time
        else:
            estimated_remaining_time = None
        
        # 格式化剩余时间
        if estimated_remaining_time is not None:
            remaining_time_str = str(datetime.timedelta(seconds=int(estimated_remaining_time)))
        else:
            remaining_time_str = "未知"
        
        # 构建进度信息
        progress_info = {
            "task_id": self.task_id,
            "start_time": datetime.datetime.fromtimestamp(self.start_time).strftime('%Y-%m-%d %H:%M:%S'),
            "elapsed_time": str(datetime.timedelta(seconds=int(elapsed_time))),
            "completion_percentage": round(completion_percentage, 2),
            "estimated_remaining_time": remaining_time_str,
            "entity_progress": {
                entity: {
                    "completed": self.current_progress.get(entity, 0),
                    "total": self.total_entities.get(entity, 0),
                    "percentage": round(self.current_progress.get(entity, 0) / self.total_entities.get(entity, 1) * 100, 2) 
                        if self.total_entities.get(entity, 0) > 0 else 0,
                    "generation_rate": round(self.generation_rates.get(entity, 0), 2)
                } 
                for entity in self.total_entities
            },
            "overall_rate": round(sum(self.generation_rates.values()), 2)
        }
        
        return progress_info
    
    def get_completion_percentage(self) -> float:
        """
        获取总体完成百分比
        
        Returns:
            完成百分比(0-100)
        """
        total_records = sum(self.total_entities.values())
        total_completed = sum(self.current_progress.values())
        
        if total_records <= 0:
            return 0.0
            
        return total_completed / total_records * 100
    
    def get_estimated_time_remaining(self) -> Optional[float]:
        """
        获取估计剩余时间(秒)
        
        Returns:
            估计剩余时间，或None表示无法估计
        """
        completion_percentage = self.get_completion_percentage()
        
        if completion_percentage <= 0:
            return None
            
        elapsed_time = time.time() - self.start_time
        estimated_total_time = elapsed_time / (completion_percentage / 100)
        
        return estimated_total_time - elapsed_time
    
    def log_performance_metrics(self):
        """
        记录性能指标日志
        """
        progress_info = self.get_progress()
        
        self.logger.info(f"任务 {self.task_id} 性能指标:")
        self.logger.info(f"  - 总体进度: {progress_info['completion_percentage']}%")
        self.logger.info(f"  - 已用时间: {progress_info['elapsed_time']}")
        self.logger.info(f"  - 估计剩余时间: {progress_info['estimated_remaining_time']}")
        self.logger.info(f"  - 总体生成速率: {progress_info['overall_rate']} 记录/秒")
        
        for entity, info in progress_info['entity_progress'].items():
            self.logger.info(f"  - {entity}: {info['completed']}/{info['total']} "
                           f"({info['percentage']}%), 速率: {info['generation_rate']} 记录/秒")
    
    def get_generation_rate(self, entity: str) -> float:
        """
        获取特定实体的生成速率
        
        Args:
            entity: 实体类型
            
        Returns:
            每秒生成记录数
        """
        return self.generation_rates.get(entity, 0.0)
    
    def create_checkpoint(self):
        """
        创建检查点，记录当前时间点
        """
        checkpoint_time = time.time()
        self.checkpoint_times.append(checkpoint_time)
        
        # 格式化时间
        checkpoint_time_str = datetime.datetime.fromtimestamp(checkpoint_time).strftime('%Y-%m-%d %H:%M:%S')
        
        self.logger.info(f"创建进度检查点: {checkpoint_time_str}")
        
        # 记录当前进度
        progress_info = self.get_progress()
        self.logger.info(f"检查点进度: {progress_info['completion_percentage']}% 完成")
        
        return checkpoint_time


# 单例模式
_instance = None

def get_progress_tracker() -> ProgressTracker:
    """
    获取ProgressTracker的单例实例
    
    Returns:
        ProgressTracker实例
    """
    global _instance
    if _instance is None:
        _instance = ProgressTracker()
    return _instance
