#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
状态管理器

用于管理数据生成任务的状态和断点续传功能。
"""

import json
import uuid
import datetime
from typing import Dict, List, Optional, Any, Union

from src.logger import get_logger
from src.core.database_manager import get_database_manager


class TaskState:
    """任务状态数据类"""
    
    def __init__(self, 
                task_id: str = None,
                task_type: str = None,
                status: str = 'pending',
                parameters: Dict = None,
                start_time: datetime.datetime = None,
                end_time: Optional[datetime.datetime] = None,
                current_stage: str = None,
                progress: Dict[str, int] = None,
                checkpoints: List[Dict] = None,
                last_error: Optional[str] = None):
        """
        初始化任务状态
        
        Args:
            task_id: 任务ID
            task_type: 任务类型
            status: 任务状态
            parameters: 任务参数
            start_time: 开始时间
            end_time: 结束时间
            current_stage: 当前阶段
            progress: 进度信息
            checkpoints: 检查点列表
            last_error: 最近错误信息
        """
        self.task_id = task_id or f"TASK{uuid.uuid4().hex[:12].upper()}"
        self.task_type = task_type
        self.status = status
        self.parameters = parameters or {}
        self.start_time = start_time or datetime.datetime.now()
        self.end_time = end_time
        self.current_stage = current_stage
        self.progress = progress or {}
        self.checkpoints = checkpoints or []
        self.last_error = last_error
    
    def to_dict(self) -> Dict:
        """
        转换为字典表示
        
        Returns:
            字典表示
        """
        return {
            'task_id': self.task_id,
            'task_type': self.task_type,
            'status': self.status,
            'parameters': self.parameters,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'current_stage': self.current_stage,
            'progress': self.progress,
            'checkpoints': self.checkpoints,
            'last_error': self.last_error
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TaskState':
        """
        从字典创建实例
        
        Args:
            data: 字典数据
            
        Returns:
            TaskState实例
        """
        # 处理日期时间字段
        start_time = None
        if data.get('start_time'):
            try:
                start_time = datetime.datetime.fromisoformat(data['start_time'])
            except ValueError:
                start_time = datetime.datetime.now()
        
        end_time = None
        if data.get('end_time'):
            try:
                end_time = datetime.datetime.fromisoformat(data['end_time'])
            except ValueError:
                end_time = None
        
        return cls(
            task_id=data.get('task_id'),
            task_type=data.get('task_type'),
            status=data.get('status', 'pending'),
            parameters=data.get('parameters', {}),
            start_time=start_time,
            end_time=end_time,
            current_stage=data.get('current_stage'),
            progress=data.get('progress', {}),
            checkpoints=data.get('checkpoints', []),
            last_error=data.get('last_error')
        )


class StateManager:
    """状态管理器，处理任务状态存储和恢复"""
    
    def __init__(self):
        """初始化状态管理器"""
        self.logger = get_logger('state_manager')
        self.db_manager = get_database_manager()
    
    def save_task_state(self, task_state: TaskState) -> bool:
        """
        保存任务状态
        
        Args:
            task_state: 任务状态对象
            
        Returns:
            是否成功
        """
        try:
            task_dict = task_state.to_dict()
            
            # 检查任务是否已存在
            existing_task = self.load_task_state(task_state.task_id)
            
            if existing_task:
                # 更新现有任务
                query = """
                UPDATE task_state 
                SET task_type = %s, status = %s, current_stage = %s,
                    progress = %s, parameters = %s, last_error = %s,
                    end_time = %s
                WHERE task_id = %s
                """
                
                params = (
                    task_dict['task_type'],
                    task_dict['status'],
                    task_dict['current_stage'],
                    json.dumps(task_dict['progress']),
                    json.dumps(task_dict['parameters']),
                    task_dict['last_error'],
                    task_dict['end_time'],
                    task_dict['task_id']
                )
                
                self.db_manager.execute_update(query, params)
                self.logger.debug(f"更新任务状态: {task_state.task_id}")
            else:
                # 创建新任务
                query = """
                INSERT INTO task_state 
                (task_id, task_type, status, start_time, end_time, 
                current_stage, progress, parameters, last_error)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                params = (
                    task_dict['task_id'],
                    task_dict['task_type'],
                    task_dict['status'],
                    task_dict['start_time'],
                    task_dict['end_time'],
                    task_dict['current_stage'],
                    json.dumps(task_dict['progress']),
                    json.dumps(task_dict['parameters']),
                    task_dict['last_error']
                )
                
                self.db_manager.execute_update(query, params)
                self.logger.info(f"创建任务状态: {task_state.task_id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"保存任务状态失败: {str(e)}")
            return False
    
    def load_task_state(self, task_id: str) -> Optional[TaskState]:
        """
        加载任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态对象，如果不存在则返回None
        """
        try:
            query = "SELECT * FROM task_state WHERE task_id = %s"
            result = self.db_manager.execute_query(query, (task_id,))
            
            if not result:
                return None
            
            task_data = result[0]
            
            # 处理JSON字段
            progress = json.loads(task_data.get('progress', '{}')) if task_data.get('progress') else {}
            parameters = json.loads(task_data.get('parameters', '{}')) if task_data.get('parameters') else {}
            
            # 构建任务状态对象
            task_dict = {
                'task_id': task_data['task_id'],
                'task_type': task_data['task_type'],
                'status': task_data['status'],
                'start_time': task_data['start_time'].isoformat() if task_data.get('start_time') else None,
                'end_time': task_data['end_time'].isoformat() if task_data.get('end_time') else None,
                'current_stage': task_data['current_stage'],
                'progress': progress,
                'parameters': parameters,
                'last_error': task_data['last_error'],
                'checkpoints': self._load_checkpoints(task_id)
            }
            
            self.logger.debug(f"加载任务状态: {task_id}")
            
            return TaskState.from_dict(task_dict)
            
        except Exception as e:
            self.logger.error(f"加载任务状态失败: {str(e)}")
            return None
    
    def update_progress(self, task_id: str, entity: str, count: int) -> bool:
        """
        更新任务进度
        
        Args:
            task_id: 任务ID
            entity: 实体类型
            count: 新增数量
            
        Returns:
            是否成功
        """
        try:
            # 加载当前任务状态
            task_state = self.load_task_state(task_id)
            if not task_state:
                self.logger.warning(f"任务不存在: {task_id}")
                return False
            
            # 更新进度
            if entity not in task_state.progress:
                task_state.progress[entity] = 0
            
            task_state.progress[entity] += count
            
            # 保存更新后的状态
            return self.save_task_state(task_state)
            
        except Exception as e:
            self.logger.error(f"更新任务进度失败: {str(e)}")
            return False
    
    def create_checkpoint(self, task_id: str) -> Optional[str]:
        """
        创建任务检查点
        
        Args:
            task_id: 任务ID
            
        Returns:
            检查点ID，如果失败则返回None
        """
        try:
            # 加载当前任务状态
            task_state = self.load_task_state(task_id)
            if not task_state:
                self.logger.warning(f"任务不存在: {task_id}")
                return None
            
            # 创建检查点ID
            checkpoint_id = f"CP{uuid.uuid4().hex[:12].upper()}"
            checkpoint_time = datetime.datetime.now()
            
            # 准备检查点数据
            checkpoint_data = {
                'checkpoint_id': checkpoint_id,
                'checkpoint_time': checkpoint_time.isoformat(),
                'progress': task_state.progress,
                'current_stage': task_state.current_stage
            }
            
            # 保存检查点到数据库
            query = """
            INSERT INTO task_checkpoint 
            (checkpoint_id, task_id, checkpoint_time, checkpoint_data)
            VALUES (%s, %s, %s, %s)
            """
            
            params = (
                checkpoint_id,
                task_id,
                checkpoint_time,
                json.dumps(checkpoint_data)
            )
            
            self.db_manager.execute_update(query, params)
            
            # 更新任务状态中的检查点列表
            task_state.checkpoints.append(checkpoint_data)
            self.save_task_state(task_state)
            
            self.logger.info(f"创建任务检查点: {checkpoint_id} (任务 {task_id})")
            
            return checkpoint_id
            
        except Exception as e:
            self.logger.error(f"创建任务检查点失败: {str(e)}")
            return None
    
    def resume_from_checkpoint(self, task_id: str, checkpoint_id: str) -> Optional[TaskState]:
        """
        从检查点恢复任务状态
        
        Args:
            task_id: 任务ID
            checkpoint_id: 检查点ID
            
        Returns:
            恢复后的任务状态，如果失败则返回None
        """
        try:
            # 查询检查点数据
            query = """
            SELECT checkpoint_data 
            FROM task_checkpoint 
            WHERE task_id = %s AND checkpoint_id = %s
            """
            
            result = self.db_manager.execute_query(query, (task_id, checkpoint_id))
            
            if not result:
                self.logger.warning(f"检查点不存在: {checkpoint_id} (任务 {task_id})")
                return None
            
            # 解析检查点数据
            checkpoint_data = json.loads(result[0]['checkpoint_data'])
            
            # 加载当前任务状态
            task_state = self.load_task_state(task_id)
            if not task_state:
                self.logger.warning(f"任务不存在: {task_id}")
                return None
            
            # 从检查点恢复状态
            task_state.progress = checkpoint_data.get('progress', {})
            task_state.current_stage = checkpoint_data.get('current_stage')
            task_state.status = 'running'
            task_state.last_error = None
            
            # 保存恢复后的状态
            self.save_task_state(task_state)
            
            self.logger.info(f"从检查点 {checkpoint_id} 恢复任务 {task_id}")
            
            return task_state
            
        except Exception as e:
            self.logger.error(f"从检查点恢复失败: {str(e)}")
            return None
    
    def _load_checkpoints(self, task_id: str) -> List[Dict]:
        """
        加载任务的所有检查点
        
        Args:
            task_id: 任务ID
            
        Returns:
            检查点列表
        """
        try:
            query = """
            SELECT checkpoint_id, checkpoint_time, checkpoint_data 
            FROM task_checkpoint 
            WHERE task_id = %s 
            ORDER BY checkpoint_time DESC
            """
            
            result = self.db_manager.execute_query(query, (task_id,))
            
            checkpoints = []
            for row in result:
                checkpoint_data = json.loads(row['checkpoint_data'])
                checkpoints.append(checkpoint_data)
            
            return checkpoints
            
        except Exception as e:
            self.logger.error(f"加载检查点失败: {str(e)}")
            return []
    
    def list_tasks(self, status: Optional[str] = None) -> List[TaskState]:
        """
        列出所有任务(可按状态过滤)
        
        Args:
            status: 任务状态过滤条件
            
        Returns:
            任务状态对象列表
        """
        try:
            if status:
                query = "SELECT task_id FROM task_state WHERE status = %s ORDER BY start_time DESC"
                result = self.db_manager.execute_query(query, (status,))
            else:
                query = "SELECT task_id FROM task_state ORDER BY start_time DESC"
                result = self.db_manager.execute_query(query)
            
            tasks = []
            for row in result:
                task_state = self.load_task_state(row['task_id'])
                if task_state:
                    tasks.append(task_state)
            
            return tasks
            
        except Exception as e:
            self.logger.error(f"列出任务失败: {str(e)}")
            return []
    
    def mark_task_completed(self, task_id: str) -> bool:
        """
        标记任务为已完成
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功
        """
        try:
            task_state = self.load_task_state(task_id)
            if not task_state:
                self.logger.warning(f"任务不存在: {task_id}")
                return False
            
            task_state.status = 'completed'
            task_state.end_time = datetime.datetime.now()
            
            return self.save_task_state(task_state)
            
        except Exception as e:
            self.logger.error(f"标记任务完成失败: {str(e)}")
            return False
    
    def mark_task_failed(self, task_id: str, error: str) -> bool:
        """
        标记任务为失败
        
        Args:
            task_id: 任务ID
            error: 错误信息
            
        Returns:
            是否成功
        """
        try:
            task_state = self.load_task_state(task_id)
            if not task_state:
                self.logger.warning(f"任务不存在: {task_id}")
                return False
            
            task_state.status = 'failed'
            task_state.end_time = datetime.datetime.now()
            task_state.last_error = error
            
            return self.save_task_state(task_state)
            
        except Exception as e:
            self.logger.error(f"标记任务失败状态失败: {str(e)}")
            return False


# 单例模式
_instance = None

def get_state_manager() -> StateManager:
    """
    获取StateManager的单例实例
    
    Returns:
        StateManager实例
    """
    global _instance
    if _instance is None:
        _instance = StateManager()
    return _instance
