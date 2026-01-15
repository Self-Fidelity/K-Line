"""优化进度管理器"""

import time
from typing import Dict, Optional
from threading import Lock


class OptimizationProgressManager:
    """优化进度管理器 - 单例模式"""
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._progress_store = {}
                    cls._instance._store_lock = Lock()
        return cls._instance
    
    def start_optimization(self, task_id: str, total_iterations: int):
        """开始优化任务"""
        with self._store_lock:
            self._progress_store[task_id] = {
                'current_iteration': 0,
                'total_iterations': total_iterations,
                'best_score': None,
                'start_time': time.time(),
                'status': 'running',
                'estimated_time_remaining': None
            }
    
    def update_progress(
        self, 
        task_id: str, 
        current_iteration: int, 
        best_score: float
    ):
        """更新进度"""
        with self._store_lock:
            if task_id not in self._progress_store:
                return
            
            progress = self._progress_store[task_id]
            progress['current_iteration'] = current_iteration
            progress['best_score'] = best_score
            
            # 估算剩余时间
            elapsed_time = time.time() - progress['start_time']
            if current_iteration > 0:
                time_per_iteration = elapsed_time / current_iteration
                remaining_iterations = progress['total_iterations'] - current_iteration
                progress['estimated_time_remaining'] = time_per_iteration * remaining_iterations
    
    def finish_optimization(self, task_id: str, best_params: dict, best_score: float):
        """完成优化"""
        with self._store_lock:
            if task_id not in self._progress_store:
                return
            
            progress = self._progress_store[task_id]
            progress['status'] = 'completed'
            progress['best_params'] = best_params
            progress['best_score'] = best_score
            progress['total_time'] = time.time() - progress['start_time']
    
    def fail_optimization(self, task_id: str, error: str):
        """优化失败"""
        with self._store_lock:
            if task_id not in self._progress_store:
                return
            
            progress = self._progress_store[task_id]
            progress['status'] = 'failed'
            progress['error'] = error
    
    def get_progress(self, task_id: str) -> Optional[Dict]:
        """获取进度"""
        with self._store_lock:
            return self._progress_store.get(task_id)
    
    def clear_progress(self, task_id: str):
        """清除进度"""
        with self._store_lock:
            if task_id in self._progress_store:
                del self._progress_store[task_id]


# 全局单例
progress_manager = OptimizationProgressManager()
