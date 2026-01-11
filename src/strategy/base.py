"""策略基类定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd


class BaseStrategy(ABC):
    """策略基类"""
    
    def __init__(self, name: str, description: str = ""):
        """
        初始化策略
        
        Args:
            name: 策略名称
            description: 策略描述
        """
        self.name = name
        self.description = description
    
    @abstractmethod
    def analyze(
        self,
        data: pd.DataFrame,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        执行策略分析
        
        Args:
            data: 股票数据 DataFrame，必须包含 date, open, close, high, low, volume 等列
            **kwargs: 其他参数
        
        Returns:
            分析结果 DataFrame，应该包含 date 列和策略相关的指标列
        """
        pass
    
    def get_required_columns(self) -> list[str]:
        """
        获取策略需要的列
        
        Returns:
            必需的列名列表
        """
        return ["date", "open", "close", "high", "low", "volume"]
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        验证数据是否满足策略要求
        
        Args:
            data: 股票数据 DataFrame
        
        Returns:
            如果数据有效返回 True，否则返回 False
        """
        required_columns = self.get_required_columns()
        return all(col in data.columns for col in required_columns)
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        获取策略信息
        
        Returns:
            策略信息字典
        """
        return {
            "name": self.name,
            "description": self.description,
            "required_columns": self.get_required_columns(),
        }
