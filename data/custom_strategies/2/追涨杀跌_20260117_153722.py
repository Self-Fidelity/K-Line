import pandas as pd
import numpy as np
from typing import Any
from src.strategy.base import BaseStrategy

class FullPositionMomentum(BaseStrategy):
    """
    全仓追涨杀跌策略
    
    逻辑：
    - 未持仓时：当日涨幅 > buy_threshold -> 全仓买入 (1)
    - 持仓中时：当日跌幅 < sell_threshold -> 全仓卖出 (-1)
    - 其他时间：保持现状 (0)
    """
    
    def __init__(self, buy_threshold: float = 0.03, sell_threshold: float = -0.03):
        super().__init__(
            name="Full Position Momentum",
            description="全仓单线程追涨杀跌",
            detailed_description="涨了就全仓进，跌了就全仓出，中间过程不调仓。",
            parameter_descriptions={
                "buy_threshold": "买入触发涨幅（例如0.03表示3%）",
                "sell_threshold": "卖出触发跌幅（例如-0.03表示-3%）",
            }
        )
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
    
    def analyze(self, data: pd.DataFrame, **kwargs: Any) -> pd.DataFrame:
        result = data.copy()
        
        # 1. 计算日涨跌幅
        # 如果 data 已经自带 pct_chg 且单位是百分比（如 3.5 代表 3.5%），
        # 则需要使用：result['pct_chg'] / 100
        change = result['pct_chg'] if 'pct_chg' in result.columns else result['close'].pct_change()
        
        # 2. 定义信号数组
        # 0: 无操作, 1: 买入, -1: 卖出
        signals = np.zeros(len(result))
        
        # 3. 模拟单线程持仓状态
        holding = False  # 初始状态：未持仓
        
        for i in range(len(result)):
            current_change = change.iloc[i]
            
            if not holding:
                # 情况 A：目前没仓位，看是否达到买入标准
                if current_change >= self.buy_threshold:
                    signals[i] = 1
                    holding = True
            else:
                # 情况 B：目前满仓，看是否达到卖出标准
                if current_change <= self.sell_threshold:
                    signals[i] = -1
                    holding = False
        
        result['signal'] = signals
        return result