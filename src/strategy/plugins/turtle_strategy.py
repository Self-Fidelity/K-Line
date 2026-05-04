"""海龟交易策略（简化版）"""

import pandas as pd
from typing import Any

from src.strategy.base import BaseStrategy
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TurtleStrategy(BaseStrategy):
    """
    海龟交易策略（简化版）

    策略说明：
    - 经典的趋势跟踪策略。
    - 买入信号：收盘价突破过去 N 天的最高价（唐奇安通道上轨）。
    - 卖出信号：收盘价跌破过去 M 天的最低价（唐奇安通道下轨）。
    - 默认 N=20, M=10
    """

    def __init__(
        self,
        entry_period: int = 20,
        exit_period: int = 10,
    ):
        super().__init__(
            name="Turtle Strategy",
            description="海龟交易策略：基于唐奇安通道的趋势突破策略",
            detailed_description="""海龟交易策略（简化版）

策略原理：
基于唐奇安通道（Donchian Channel）的突破系统。
- 上轨：过去 N 天的最高价
- 下轨：过去 M 天的最低价

交易信号：
- 买入（开仓）：当价格突破上轨时（Price > Max_High(N)）。
- 卖出（平仓）：当价格跌破下轨时（Price < Min_Low(M)）。

这是一个典型的趋势跟踪策略，旨在捕捉大趋势。在震荡市场中可能会频繁止损。

参数说明：
- entry_period: 入场周期（突破此周期的最高价买入），默认20
- exit_period: 离场周期（跌破此周期的最低价卖出），默认10
""",
            parameter_descriptions={
                "entry_period": "入场突破周期（天），默认20",
                "exit_period": "离场跌破周期（天），默认10",
            }
        )
        self.entry_period = entry_period
        self.exit_period = exit_period

    def analyze(
        self,
        data: pd.DataFrame,
        **kwargs: Any,
    ) -> pd.DataFrame:
        if not self.validate_data(data):
            raise ValueError("数据不满足策略要求")

        df = data.copy()
        df = df.sort_values("date").reset_index(drop=True)

        entry_period = int(kwargs.get("entry_period", self.entry_period))
        exit_period = int(kwargs.get("exit_period", self.exit_period))

        # 计算唐奇安通道（注意：不包含当日，使用 shift(1)）
        df["donchian_high"] = df["high"].rolling(window=entry_period, min_periods=entry_period).max().shift(1)
        df["donchian_low"] = df["low"].rolling(window=exit_period, min_periods=exit_period).min().shift(1)

        df["signal"] = 0

        # 买入：收盘价 > 昨日计算出的donchian_high
        # 卖出：收盘价 < 昨日计算出的donchian_low

        # 记录持仓状态
        position = 0

        for i in range(max(entry_period, exit_period), len(df)):
            close = df.iloc[i]["close"]
            upper = df.iloc[i]["donchian_high"]
            lower = df.iloc[i]["donchian_low"]

            if position == 0:
                if close > upper:
                    df.iloc[i, df.columns.get_loc("signal")] = 1
                    position = 1
            elif position == 1:
                if close < lower:
                    df.iloc[i, df.columns.get_loc("signal")] = -1
                    position = 0

        df["signal_type"] = df["signal"].map({1: "买入", -1: "卖出", 0: "持有"})

        result_columns = ["date", "close", "donchian_high", "donchian_low", "signal", "signal_type"]
        result = df[result_columns].copy()

        logger.info(f"海龟策略分析完成，共生成 {len(result[result['signal'] != 0])} 个交易信号")

        return result

    def get_required_columns(self) -> list[str]:
        return ["date", "close", "high", "low"]
