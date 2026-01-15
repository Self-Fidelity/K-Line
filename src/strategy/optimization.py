"""策略参数优化模块 - 使用mealpy库实现"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
import logging

from mealpy import FloatVar, IntegerVar, PSO

from src.strategy.manager import StrategyManager
from src.strategy.statistics import StrategyStatistics

logger = logging.getLogger(__name__)


class Optimizer:
    """参数优化器 - 使用mealpy实现"""

    def __init__(self, strategy_name: str, stock_data: pd.DataFrame):
        """
        初始化优化器
        
        Args:
            strategy_name: 策略名称
            stock_data: 股票数据
        """
        self.strategy_name = strategy_name
        self.stock_data = stock_data
        self.manager = StrategyManager()
        
        # 获取策略实例
        strategy = self.manager.get_strategy(strategy_name)
        if strategy is None:
            raise ValueError(f"策略 {strategy_name} 不存在")
        
        self.strategy_class = strategy.__class__
        logger.info(f"优化器初始化成功: 策略={strategy_name}, 数据行数={len(stock_data)}")

    def _evaluate(self, params: Dict[str, Any], target_metric: str = "sharpe_ratio") -> float:
        """
        评估一组参数的表现
        
        Args:
            params: 策略参数
            target_metric: 优化目标指标
            
        Returns:
            得分（越高越好）
        """
        try:
            # 创建策略实例
            strategy = self.strategy_class(**params)
            
            # 运行策略
            result = strategy.analyze(self.stock_data)
            
            if result.empty:
                return -1e9
            
            # 计算统计指标
            stats = StrategyStatistics.calculate_statistics(self.stock_data, result)
            
            # 获取目标指标
            score = stats.get(target_metric)
            
            if score is None or np.isnan(score) or np.isinf(score):
                return -1e9
            
            return float(score)
            
        except Exception as e:
            logger.debug(f"评估参数 {params} 失败: {e}")
            return -1e9

    def optimize_pso(
        self,
        param_bounds: Dict[str, Tuple[float, float, type]],
        num_particles: int = 20,
        max_iter: int = 50,
        target_metric: str = "sharpe_ratio",
        task_id: Optional[str] = None,  # 新增：任务ID用于进度追踪
    ) -> Dict[str, Any]:
        """
        使用粒子群优化算法优化参数
        
        Args:
            param_bounds: 参数边界 {param_name: (min, max, type)}
            num_particles: 粒子数量（种群大小）
            max_iter: 最大迭代次数
            target_metric: 优化目标指标
            task_id: 任务ID（可选）
            
        Returns:
            优化结果字典
        """
        from src.strategy.progress_manager import progress_manager
        
        logger.info(f"开始PSO优化: 粒子数={num_particles}, 迭代={max_iter}, 目标={target_metric}")
        logger.info(f"参数范围: {param_bounds}")
        
        # 初始化进度
        if task_id:
            progress_manager.start_optimization(task_id, max_iter)
        
        # 准备mealpy的变量定义
        bounds = []
        param_names = []
        
        for param_name, (min_val, max_val, param_type) in param_bounds.items():
            param_names.append(param_name)
            
            if param_type is int:
                bounds.append(IntegerVar(lb=int(min_val), ub=int(max_val), name=param_name))
            else:
                bounds.append(FloatVar(lb=float(min_val), ub=float(max_val), name=param_name))
        
        # 当前最佳得分（用于进度更新）
        current_best_score = -1e9
        iteration_count = [0]  # 使用列表以便在闭包中修改
        
        # 定义目标函数（mealpy需要最小化，所以我们返回负值）
        def objective_function(solution):
            """目标函数 - 返回负的得分（因为mealpy是最小化）"""
            params = {}
            for i, param_name in enumerate(param_names):
                _, _, param_type = param_bounds[param_name]
                if param_type is int:
                    params[param_name] = int(round(solution[i]))
                else:
                    params[param_name] = float(solution[i])
            
            score = self._evaluate(params, target_metric)
            
            # 更新最佳得分和进度
            nonlocal current_best_score
            if score > current_best_score:
                current_best_score = score
            
            # 返回负值用于最小化
            return -score
        
        # 定义问题
        problem = {
            "obj_func": objective_function,
            "bounds": bounds,
            "minmax": "min",  # 最小化问题
        }
        
        # 创建PSO优化器
        # 使用标准PSO算法
        model = PSO.OriginalPSO(epoch=max_iter, pop_size=num_particles)
        
        # 记录收敛历史和日志
        convergence_history = []
        optimization_logs = []  # 新增：记录优化日志
        
        # 自定义日志处理器以捕获mealpy日志
        import io
        import sys
        from contextlib import redirect_stdout, redirect_stderr
        
        # 重写模型的evolve方法以添加进度回调
        original_evolve = model.evolve
        
        def evolve_with_progress(epoch):
            result = original_evolve(epoch)
            
            # 更新进度
            iteration_count[0] = epoch + 1
            if task_id and hasattr(model, 'history') and hasattr(model.history, 'list_global_best_fit'):
                current_score = -model.history.list_global_best_fit[-1] if model.history.list_global_best_fit else current_best_score
                progress_manager.update_progress(task_id, epoch + 1, current_score)
                
                # 添加日志
                log_msg = f"Epoch {epoch + 1}/{max_iter}, Best Score: {current_score:.4f}"
                optimization_logs.append(log_msg)
                logger.info(log_msg)
            
            return result
        
        model.evolve = evolve_with_progress
        
        try:
            # 运行优化
            logger.info("开始运行PSO算法...")
            optimization_logs.append("开始PSO优化...")
            
            # solve() 返回的是 best_agent 对象
            best_agent = model.solve(problem)
            
            # 从历史记录中获取收敛数据
            # mealpy会保存历史最佳适应度
            if hasattr(model, 'history') and hasattr(model.history, 'list_global_best_fit'):
                # 转换为正值（因为我们优化时取了负值）
                convergence_history = [-fit for fit in model.history.list_global_best_fit]
            
            # 从 Agent 对象中提取解
            best_position = best_agent.solution
            best_fitness = best_agent.target.fitness
            
            logger.info(f"PSO算法运行完成")
            optimization_logs.append("PSO算法运行完成")
            
            # 提取最佳参数
            best_params = {}
            for i, param_name in enumerate(param_names):
                _, _, param_type = param_bounds[param_name]
                if param_type is int:
                    best_params[param_name] = int(round(best_position[i]))
                else:
                    best_params[param_name] = float(best_position[i])
            
            # 最佳得分（转回正值）
            best_score = -best_fitness
            
            logger.info(f"优化完成: 最佳得分={best_score:.4f}, 最佳参数={best_params}")
            optimization_logs.append(f"最佳得分: {best_score:.4f}")
            
            # 完成进度
            if task_id:
                progress_manager.finish_optimization(task_id, best_params, best_score)
            
            return {
                "best_params": best_params,
                "best_score": float(best_score),
                "method": "pso",
                "convergence_curve": [float(x) for x in convergence_history],  # 转换numpy为float
                "iterations": len(convergence_history),     # 实际迭代次数
                "optimization_logs": optimization_logs      # 优化日志
            }
            
        except Exception as e:
            logger.error(f"PSO优化失败: {e}", exc_info=True)
            optimization_logs.append(f"优化失败: {str(e)}")
            if task_id:
                progress_manager.fail_optimization(task_id, str(e))
            raise
    
    def optimize_grid(
        self,
        param_grid: Dict[str, List[Any]],
        target_metric: str = "sharpe_ratio"
    ) -> Dict[str, Any]:
        """
        网格搜索优化
        
        Args:
            param_grid: 参数网格 {param_name: [value1, value2, ...]}
            target_metric: 优化目标指标
            
        Returns:
            优化结果字典
        """
        import itertools
        
        logger.info(f"开始网格搜索优化: 目标={target_metric}")
        logger.info(f"参数网格: {param_grid}")
        
        keys = list(param_grid.keys())
        values = list(param_grid.values())
        combinations = list(itertools.product(*values))
        
        logger.info(f"总共 {len(combinations)} 种参数组合")
        
        best_score = -float("inf")
        best_params = {}
        
        for i, combo in enumerate(combinations):
            params = dict(zip(keys, combo))
            score = self._evaluate(params, target_metric)
            
            if score > best_score:
                best_score = score
                best_params = params
            
            if (i + 1) % 10 == 0:
                logger.info(f"进度: {i + 1}/{len(combinations)}, 当前最佳得分: {best_score:.4f}")
        
        logger.info(f"网格搜索完成: 最佳得分={best_score:.4f}, 最佳参数={best_params}")
        
        return {
            "best_params": best_params,
            "best_score": float(best_score),
            "method": "grid"
        }
