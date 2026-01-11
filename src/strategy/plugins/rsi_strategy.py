"""RSI策略（Relative Strength Index Strategy）"""

import pandas as pd
from typing import Any
import numpy as np

from src.strategy.base import BaseStrategy
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RSIStrategy(BaseStrategy):
    """
    RSI策略（相对强弱指标策略）
    
    策略说明：
    - RSI是衡量股价超买超卖的指标，范围0-100
    - 当RSI < 超卖阈值时，产生买入信号
    - 当RSI > 超买阈值时，产生卖出信号
    - 默认周期：14日，超卖阈值：30，超买阈值：70
    """
    
    def __init__(
        self,
        period: int = 14,
        oversold: float = 30.0,
        overbought: float = 70.0,
    ):
        """
        初始化RSI策略
        
        Args:
            period: RSI计算周期（默认14）
            oversold: 超卖阈值（默认30）
            overbought: 超买阈值（默认70）
        """
        super().__init__(
            name="RSI Strategy",
            description=f"RSI Strategy (period: {period}, oversold: {oversold}, overbought: {overbought})"
        )
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
    
    def _calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """
        计算RSI指标
        
        Args:
            prices: 价格序列
            period: 计算周期
        
        Returns:
            RSI序列
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)  # 初始值填充为50（中性）
    
    def analyze(
        self,
        data: pd.DataFrame,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        执行RSI策略分析
        
        Args:
            data: 股票数据 DataFrame，必须包含 date, close 列
            **kwargs: 其他参数（可选：period, oversold, overbought）
        
        Returns:
            分析结果 DataFrame，包含以下列：
            - date: 日期
            - close: 收盘价
            - rsi: RSI指标值
            - signal: 信号（1=买入，-1=卖出，0=持有）
            - signal_type: 信号类型
        """
        if not self.validate_data(data):
            raise ValueError("数据不满足策略要求")
        
        df = data.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        
        period = kwargs.get("period", self.period)
        oversold = kwargs.get("oversold", self.oversold)
        overbought = kwargs.get("overbought", self.overbought)
        
        # 计算RSI
        df["rsi"] = self._calculate_rsi(df["close"], period)
        
        # 生成信号（只在状态变化时产生信号）
        df["signal"] = 0
        for i in range(1, len(df)):
            prev_rsi = df.iloc[i - 1]["rsi"]
            curr_rsi = df.iloc[i]["rsi"]
            
            # 从超卖区域上穿超卖阈值：买入信号
            if prev_rsi <= oversold and curr_rsi > oversold:
                df.iloc[i, df.columns.get_loc("signal")] = 1
            # 从超买区域下穿超买阈值：卖出信号
            elif prev_rsi >= overbought and curr_rsi < overbought:
                df.iloc[i, df.columns.get_loc("signal")] = -1
        
        df["signal_type"] = df["signal"].map({1: "买入", -1: "卖出", 0: "持有"})
        
        result_columns = ["date", "close", "rsi", "signal", "signal_type"]
        result = df[result_columns].copy()
        
        signal_count = len(result[result["signal"] != 0])
        logger.info(f"RSI策略分析完成，共生成 {signal_count} 个交易信号")
        
        return result
    
    def get_required_columns(self) -> list[str]:
        """获取策略需要的列"""
        return ["date", "close"]
