import time
import psutil


class BatchProcessingOptimizer:
    """
    批量处理优化器
    
    用于优化大数据量生成和导入的性能，自动调整批处理大小，
    监控内存使用，实现高效数据处理
    """
    
    def __init__(self, db_manager, logger, initial_batch_size=1000, max_batch_size=10000, min_batch_size=100):
        """
        初始化批量处理优化器
        
        Args:
            db_manager: 数据库管理器
            logger: 日志记录器
            initial_batch_size (int): 初始批处理大小
            max_batch_size (int): 最大批处理大小
            min_batch_size (int): 最小批处理大小
        """
        self.db_manager = db_manager
        self.logger = logger
        self.initial_batch_size = initial_batch_size
        self.max_batch_size = max_batch_size
        self.min_batch_size = min_batch_size
        
        # 当前批处理大小
        self.current_batch_size = initial_batch_size
        
        # 性能指标
        self.last_batch_time = 0
        self.total_processed = 0
        self.total_batches = 0
        self.total_time = 0
        self.peak_memory_usage = 0
        self.batch_times = []
        
        # 内存监控
        self.memory_threshold = 0.8  # 内存使用率阈值，超过此值会减小批量大小
    
    def process_batch(self, data_generator, data_importer, total_count=None, progress_callback=None):
        """
        批量处理数据
        
        使用数据生成器生成数据，并使用数据导入器导入数据库，
        自动调整批处理大小以优化性能
        
        Args:
            data_generator: 数据生成函数，接受batch_size参数
            data_importer: 数据导入函数，接受数据列表参数
            total_count (int, optional): 总数据量，用于进度计算
            progress_callback (function, optional): 进度回调函数
            
        Returns:
            dict: 处理统计信息
        """
        
        
        # 初始化统计信息
        stats = {
            'total_processed': 0,
            'total_batches': 0,
            'total_time': 0,
            'average_batch_time': 0,
            'peak_memory_usage': 0,
            'batch_size_adjustments': 0,
            'final_batch_size': self.current_batch_size,
            'success': True,
            'error': None
        }
        
        # 重置性能指标
        self.total_processed = 0
        self.total_batches = 0
        self.total_time = 0
        self.peak_memory_usage = 0
        self.batch_times = []
        
        try:
            # 开始计时
            start_time = time.time()
            
            # 如果未提供总数量，设置为None
            total_remaining = total_count
            
            # 批量处理循环
            while True:
                # 调整批处理大小（根据剩余数量）
                if total_remaining is not None and total_remaining < self.current_batch_size:
                    batch_size = total_remaining
                else:
                    batch_size = self.current_batch_size
                
                # 生成当前批次数据
                batch_start_time = time.time()
                batch_data = data_generator(batch_size)
                
                # 如果没有数据，结束处理
                if not batch_data or len(batch_data) == 0:
                    break
                
                # 检查内存使用情况
                current_memory_usage = self._get_memory_usage()
                self.peak_memory_usage = max(self.peak_memory_usage, current_memory_usage)
                
                # 导入数据
                data_importer(batch_data)
                
                # 更新计数
                processed_count = len(batch_data)
                self.total_processed += processed_count
                self.total_batches += 1
                
                # 计算批处理时间
                batch_time = time.time() - batch_start_time
                self.batch_times.append(batch_time)
                self.last_batch_time = batch_time
                
                # 调整批处理大小
                self._adjust_batch_size(batch_time, current_memory_usage)
                
                # 更新统计信息
                stats['batch_size_adjustments'] += 1 if self.current_batch_size != batch_size else 0
                
                # 更新剩余数量
                if total_remaining is not None:
                    total_remaining -= processed_count
                    if total_remaining <= 0:
                        break
                
                # 调用进度回调
                if progress_callback and total_count:
                    progress = min(1.0, self.total_processed / total_count)
                    progress_callback(progress, self.total_processed, total_count)
                
                # 定期日志记录
                if self.total_batches % 10 == 0:
                    self.logger.info(
                        f"已处理 {self.total_processed} 条记录, "
                        f"批次 {self.total_batches}, "
                        f"当前批处理大小 {self.current_batch_size}, "
                        f"内存使用率 {current_memory_usage:.2%}"
                    )
            
            # 计算总时间
            self.total_time = time.time() - start_time
            
            # 更新最终统计信息
            stats.update({
                'total_processed': self.total_processed,
                'total_batches': self.total_batches,
                'total_time': self.total_time,
                'average_batch_time': sum(self.batch_times) / len(self.batch_times) if self.batch_times else 0,
                'peak_memory_usage': self.peak_memory_usage,
                'final_batch_size': self.current_batch_size
            })
            
            # 记录最终统计
            self.logger.info(
                f"批处理完成: 总处理 {self.total_processed} 条记录, "
                f"总批次 {self.total_batches}, "
                f"总耗时 {self.total_time:.2f}秒, "
                f"平均批处理时间 {stats['average_batch_time']:.2f}秒, "
                f"峰值内存使用率 {self.peak_memory_usage:.2%}"
            )
            
            return stats
            
        except Exception as e:
            error_msg = f"批处理过程中出错: {str(e)}"
            self.logger.error(error_msg)
            stats.update({
                'success': False,
                'error': error_msg,
                'total_processed': self.total_processed,
                'total_batches': self.total_batches,
                'total_time': time.time() - start_time if 'start_time' in locals() else 0
            })
            return stats
    
    def _adjust_batch_size(self, batch_time, memory_usage):
        """
        调整批处理大小
        
        根据上一批处理的执行时间和内存使用情况，动态调整批处理大小
        
        Args:
            batch_time (float): 上一批处理的执行时间（秒）
            memory_usage (float): 当前内存使用率（0-1）
        """
        # 内存使用过高时，减小批处理大小
        if memory_usage > self.memory_threshold:
            # 内存使用率越高，减小比例越大
            reduction_factor = max(0.5, 1 - (memory_usage - self.memory_threshold) * 2)
            new_batch_size = max(self.min_batch_size, int(self.current_batch_size * reduction_factor))
            
            if new_batch_size < self.current_batch_size:
                self.logger.warning(
                    f"内存使用率过高 ({memory_usage:.2%})，减小批处理大小: "
                    f"{self.current_batch_size} -> {new_batch_size}"
                )
                self.current_batch_size = new_batch_size
                return
        
        # 批处理时间合理区间（秒）
        optimal_time_min = 1.0
        optimal_time_max = 5.0
        
        # 根据处理时间调整批处理大小
        if batch_time < optimal_time_min and self.current_batch_size < self.max_batch_size:
            # 处理太快，增加批处理大小
            increase_factor = min(2.0, optimal_time_min / max(0.1, batch_time))
            new_batch_size = min(self.max_batch_size, int(self.current_batch_size * increase_factor))
            
            if new_batch_size > self.current_batch_size:
                self.logger.debug(
                    f"批处理时间较短 ({batch_time:.2f}秒)，增加批处理大小: "
                    f"{self.current_batch_size} -> {new_batch_size}"
                )
                self.current_batch_size = new_batch_size
                
        elif batch_time > optimal_time_max and self.current_batch_size > self.min_batch_size:
            # 处理太慢，减小批处理大小
            reduction_factor = max(0.5, optimal_time_max / batch_time)
            new_batch_size = max(self.min_batch_size, int(self.current_batch_size * reduction_factor))
            
            if new_batch_size < self.current_batch_size:
                self.logger.debug(
                    f"批处理时间较长 ({batch_time:.2f}秒)，减小批处理大小: "
                    f"{self.current_batch_size} -> {new_batch_size}"
                )
                self.current_batch_size = new_batch_size
    
    def _get_memory_usage(self):
        """
        获取当前内存使用率
        
        Returns:
            float: 内存使用率（0-1）
        """
        try:
            # 获取当前进程
            process = psutil.Process()
            # 获取内存使用情况（百分比）
            memory_info = process.memory_percent()
            return memory_info / 100.0  # 转换为0-1范围
        except ImportError:
            self.logger.warning("未安装psutil库，无法监控内存使用情况")
            return 0.5  # 返回默认值
        except Exception as e:
            self.logger.error(f"获取内存使用率时出错: {str(e)}")
            return 0.5  # 返回默认值
    
    def get_performance_stats(self):
        """
        获取性能统计信息
        
        Returns:
            dict: 性能统计信息
        """
        # 计算平均批处理时间
        avg_batch_time = sum(self.batch_times) / len(self.batch_times) if self.batch_times else 0
        
        return {
            'total_processed': self.total_processed,
            'total_batches': self.total_batches,
            'total_time': self.total_time,
            'peak_memory_usage': self.peak_memory_usage,
            'average_batch_time': avg_batch_time,
            'processing_rate': self.total_processed / self.total_time if self.total_time > 0 else 0,
            'current_batch_size': self.current_batch_size,
            'batch_time_history': self.batch_times
        }
    
    def reset(self):
        """重置批处理优化器状态"""
        self.current_batch_size = self.initial_batch_size
        self.total_processed = 0
        self.total_batches = 0
        self.total_time = 0
        self.peak_memory_usage = 0
        self.batch_times = []