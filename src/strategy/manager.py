"""策略管理器"""

import importlib
import importlib.util
import inspect
from pathlib import Path
from typing import Dict, List, Optional, Type, Any
import pandas as pd

from src.strategy.base import BaseStrategy
from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class StrategyManager:
    """策略管理器，负责策略的发现、加载和调用"""
    
    def __init__(self, strategy_dir: Optional[Path] = None):
        """
        初始化策略管理器
        
        Args:
            strategy_dir: 策略插件目录，如果为 None 则使用配置中的目录
        """
        self.strategy_dir = strategy_dir or settings.STRATEGY_PLUGIN_DIR
        self.strategies: Dict[str, BaseStrategy] = {}
        self._load_strategies()
    
    def _load_strategies(self) -> None:
        """加载所有策略插件"""
        if not self.strategy_dir.exists():
            logger.warning(f"策略目录不存在: {self.strategy_dir}")
            return
        
        # 查找所有 Python 文件
        for strategy_file in self.strategy_dir.glob("*.py"):
            if strategy_file.name == "__init__.py":
                continue
            
            try:
                self._load_strategy_from_file(strategy_file)
            except Exception as e:
                logger.error(f"加载策略文件 {strategy_file} 失败: {e}", exc_info=True)
    
    def _load_strategy_from_file(self, file_path: Path) -> None:
        """
        从文件加载策略
        
        Args:
            file_path: 策略文件路径
        """
        module_name = f"src.strategy.plugins.{file_path.stem}"
        
        try:
            # 动态导入模块
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                logger.warning(f"无法加载策略模块: {file_path}")
                return
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 查找策略类（继承自 BaseStrategy 的类）
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (
                    issubclass(obj, BaseStrategy)
                    and obj != BaseStrategy
                    and obj.__module__ == module_name
                ):
                    # 实例化策略
                    try:
                        strategy = obj()
                        self.register_strategy(strategy)
                        logger.info(f"加载策略: {strategy.name}")
                    except Exception as e:
                        logger.error(f"实例化策略 {name} 失败: {e}", exc_info=True)
            
        except Exception as e:
            logger.error(f"加载策略文件 {file_path} 失败: {e}", exc_info=True)
    
    def register_strategy(self, strategy: BaseStrategy) -> None:
        """
        注册策略
        
        Args:
            strategy: 策略实例
        """
        if strategy.name in self.strategies:
            logger.warning(f"策略 {strategy.name} 已存在，将被覆盖")
        
        self.strategies[strategy.name] = strategy
        logger.debug(f"注册策略: {strategy.name}")
    
    def get_strategy(self, name: str) -> Optional[BaseStrategy]:
        """
        获取策略实例
        
        Args:
            name: 策略名称
        
        Returns:
            策略实例，如果不存在返回 None
        """
        return self.strategies.get(name)
    
    def list_strategies(self) -> List[str]:
        """
        列出所有已注册的策略名称
        
        Returns:
            策略名称列表
        """
        return list(self.strategies.keys())
    
    def run_strategy(
        self,
        strategy_name: str,
        data: pd.DataFrame,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        运行指定策略
        
        Args:
            strategy_name: 策略名称
            data: 股票数据 DataFrame
            **kwargs: 传递给策略的参数
        
        Returns:
            策略分析结果 DataFrame
        """
        strategy = self.get_strategy(strategy_name)
        if strategy is None:
            raise ValueError(f"策略 {strategy_name} 不存在")
        
        if not strategy.validate_data(data):
            raise ValueError(f"数据不满足策略 {strategy_name} 的要求")
        
        logger.info(f"执行策略: {strategy_name}")
        return strategy.analyze(data, **kwargs)
    
    def run_all_strategies(
        self,
        data: pd.DataFrame,
        **kwargs: Any,
    ) -> Dict[str, pd.DataFrame]:
        """
        运行所有已注册的策略
        
        Args:
            data: 股票数据 DataFrame
            **kwargs: 传递给策略的参数
        
        Returns:
            字典，key 为策略名称，value 为策略分析结果
        """
        results = {}
        for strategy_name in self.list_strategies():
            try:
                result = self.run_strategy(strategy_name, data, **kwargs)
                results[strategy_name] = result
            except Exception as e:
                logger.error(f"执行策略 {strategy_name} 失败: {e}", exc_info=True)
                continue
        
        return results
