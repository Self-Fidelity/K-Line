"""策略参数优化模块"""

import random
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Callable, Tuple, Optional
from concurrent.futures import ProcessPoolExecutor
import logging

from src.strategy.manager import StrategyManager
from src.strategy.statistics import StrategyStatistics

logger = logging.getLogger(__name__)

class Optimizer:
    """参数优化器"""

    def __init__(self, strategy_name: str, stock_data: pd.DataFrame):
        self.strategy_name = strategy_name
        self.stock_data = stock_data
        self.manager = StrategyManager()
        self.strategy_class = self.manager.get_strategy(strategy_name).__class__

    def _evaluate(self, params: Dict[str, Any], target_metric: str = "sharpe_ratio") -> float:
        """
        评估一组参数的表现

        Args:
            params: 策略参数
            target_metric: 优化目标指标 (sharpe_ratio, cumulative_return, sortino_ratio, win_rate)
        """
        try:
            strategy = self.strategy_class(**params)
            result = strategy.analyze(self.stock_data)

            # 计算统计指标
            stats = StrategyStatistics.calculate_statistics(self.stock_data, result)

            # 获取目标指标
            score = stats.get(target_metric)

            # 如果指标为 None (例如无交易)，返回极小值
            if score is None:
                return -1e9

            return float(score)

        except Exception as e:
            # 只有在 debug 模式下才打印详细错误，避免刷屏
            # logger.debug(f"Evaluating params {params} failed: {e}")
            return -1e9

    def optimize_grid(self, param_grid: Dict[str, List[Any]], target_metric: str = "sharpe_ratio") -> Dict[str, Any]:
        """网格搜索优化"""
        import itertools

        keys = param_grid.keys()
        values = param_grid.values()
        combinations = list(itertools.product(*values))

        best_score = -float("inf")
        best_params = {}

        # 简单循环，实际生产中可以使用多进程
        for combo in combinations:
            params = dict(zip(keys, combo))
            score = self._evaluate(params, target_metric)

            if score > best_score:
                best_score = score
                best_params = params

        return {
            "best_params": best_params,
            "best_score": best_score,
            "method": "grid"
        }

    def optimize_pso(
        self,
        param_bounds: Dict[str, Tuple[float, float, type]],
        num_particles: int = 20,
        max_iter: int = 50,
        target_metric: str = "sharpe_ratio"
    ) -> Dict[str, Any]:
        """
        粒子群优化 (PSO)

        Args:
            param_bounds: 参数边界字典，key: (min, max, type)
                type 可以是 int 或 float
            num_particles: 粒子数量
            max_iter: 最大迭代次数
        """

        # 初始化粒子
        particles = []
        velocities = []
        pbest = []
        pbest_scores = []

        gbest = None
        gbest_score = -float("inf")

        dim = len(param_bounds)
        keys = list(param_bounds.keys())

        for _ in range(num_particles):
            pos = {}
            vel = {}
            for key, (min_val, max_val, dtype) in param_bounds.items():
                if dtype is int:
                    pos[key] = random.randint(int(min_val), int(max_val))
                else:
                    pos[key] = random.uniform(min_val, max_val)
                vel[key] = random.uniform(-1, 1) * (max_val - min_val) * 0.1

            particles.append(pos)
            velocities.append(vel)
            pbest.append(pos)
            pbest_scores.append(-float("inf"))

        # PSO 参数
        w = 0.729  # 惯性权重
        c1 = 1.49445 # 个体认知权重
        c2 = 1.49445 # 社会认知权重

        for iter_i in range(max_iter):
            for i in range(num_particles):
                # 评估适应度
                score = self._evaluate(particles[i], target_metric)

                # 更新个体最优
                if score > pbest_scores[i]:
                    pbest_scores[i] = score
                    pbest[i] = particles[i].copy()

                # 更新全局最优
                if score > gbest_score:
                    gbest_score = score
                    gbest = particles[i].copy()

            # 更新速度和位置
            for i in range(num_particles):
                for key in keys:
                    min_val, max_val, dtype = param_bounds[key]

                    r1 = random.random()
                    r2 = random.random()

                    # 速度更新
                    velocities[i][key] = (
                        w * velocities[i][key] +
                        c1 * r1 * (pbest[i][key] - particles[i][key]) +
                        c2 * r2 * (gbest[key] - particles[i][key])
                    )

                    # 位置更新
                    particles[i][key] += velocities[i][key]

                    # 边界处理
                    if dtype is int:
                        particles[i][key] = int(round(particles[i][key]))

                    if particles[i][key] < min_val:
                        particles[i][key] = min_val if dtype is not int else int(min_val)
                        velocities[i][key] *= -0.5 # 碰壁反弹
                    elif particles[i][key] > max_val:
                        particles[i][key] = max_val if dtype is not int else int(max_val)
                        velocities[i][key] *= -0.5

            logger.info(f"PSO Iteration {iter_i+1}/{max_iter}, Best Score: {gbest_score:.4f}")

        return {
            "best_params": gbest,
            "best_score": gbest_score,
            "method": "pso"
        }
