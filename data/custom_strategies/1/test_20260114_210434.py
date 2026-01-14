"""自定义策略模板"""

import pandas as pd
from typing import Any
from src.strategy.base import BaseStrategy

class MyCustomStrategy(BaseStrategy):
    """
    自定义策略
    
    策略说明：
    - 在这里描述你的策略逻辑
    """
    
    def __init__(self, param1: int = 10, param2: float = 0.5):
        """
        初始化策略
        
        Args:
            param1: 参数1说明
            param2: 参数2说明
        """
        super().__init__(
            name="My Custom Strategy",
            description="自定义策略描述",
            detailed_description="策略详细说明",
            parameter_descriptions={
                "param1": "参数1说明",
                "param2": "参数2说明",
            }
        )
        self.param1 = param1
        self.param2 = param2
    
    def analyze(
        self,
        data: pd.DataFrame,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        执行策略分析
        
        Args:
            data: 股票数据 DataFrame，包含 date, open, close, high, low, volume 等列
            **kwargs: 其他参数
        
        Returns:
            分析结果 DataFrame，必须包含 date 列，建议包含 signal 列（1=买入，-1=卖出，0=持有）
        """
        result = data.copy()
        
        # 在这里实现你的策略逻辑
        # 示例：简单的移动平均策略
        result['ma'] = result['close'].rolling(window=self.param1).mean()
        result['signal'] = 0
        
        # 当收盘价上穿均线时买入
        result.loc[result['close'] > result['ma'], 'signal'] = 1
        # 当收盘价下穿均线时卖出
        result.loc[result['close'] < result['ma'], 'signal'] = -1
        
        return result
