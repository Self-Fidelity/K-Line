"""KDJ指标策略"""

import pandas as pd
from typing import Any

from src.strategy.base import BaseStrategy
from src.utils.logger import get_logger

logger = get_logger(__name__)


class KDJStrategy(BaseStrategy):
    """
    KDJ随机指标策略

    策略说明：
    - KDJ指标是一种相当新颖、实用的技术分析指标，它起先用于期货市场的分析，后被广泛用于股市的中短期趋势分析，是期货和股票市场上最常用的技术分析工具。
    - 买入信号：K线上穿D线（金叉），且K < 50 (低位金叉更有效)
    - 卖出信号：K线下穿D线（死叉），且K > 50 (高位死叉更有效)
    """

    def __init__(
        self,
        period: int = 9,
        k_period: int = 3,
        d_period: int = 3,
    ):
        super().__init__(
            name="KDJ Strategy",
            description="KDJ策略：基于随机指标的超买超卖和交叉信号",
            detailed_description="""KDJ指标（随机指标）

策略原理：
1. 计算RSV（未成熟随机值）：(今日收盘价 - N日内最低价) / (N日内最高价 - N日内最低价) * 100
2. 计算K值：2/3 * 前一日K值 + 1/3 * 当日RSV
3. 计算D值：2/3 * 前一日D值 + 1/3 * 当日K值
4. 计算J值：3 * K值 - 2 * D值

交易信号：
- 买入：K线向上突破D线（金叉），通常要求金叉发生在50以下，越低越好。
- 卖出：K线向下跌破D线（死叉），通常要求死叉发生在50以上，越高越好。
- J线可以作为辅助，J > 100 为超买，J < 0 为超卖。

参数说明：
- period: 计算RSV的周期，默认9日
- k_period: K值平滑周期，默认3
- d_period: D值平滑周期，默认3
""",
            parameter_descriptions={
                "period": "计算RSV的周期，默认9",
                "k_period": "K值平滑周期，默认3",
                "d_period": "D值平滑周期，默认3",
            }
        )
        self.period = period
        self.k_period = k_period
        self.d_period = d_period

    def analyze(
        self,
        data: pd.DataFrame,
        **kwargs: Any,
    ) -> pd.DataFrame:
        if not self.validate_data(data):
            raise ValueError("数据不满足策略要求")

        df = data.copy()
        df = df.sort_values("date").reset_index(drop=True)

        period = kwargs.get("period", self.period)

        # 计算RSV
        low_min = df["low"].rolling(window=period, min_periods=1).min()
        high_max = df["high"].rolling(window=period, min_periods=1).max()

        # 避免除以零
        denom = high_max - low_min
        denom = denom.replace(0, 1)  # 防止除0

        df["rsv"] = (df["close"] - low_min) / denom * 100

        # 计算K, D, J
        # K = 2/3 * PrevK + 1/3 * RSV
        # D = 2/3 * PrevD + 1/3 * K
        # 初始化
        k_values = [50.0] * len(df)
        d_values = [50.0] * len(df)

        # 转换为列表加速计算
        rsv_list = df["rsv"].fillna(50).tolist()

        for i in range(1, len(df)):
            k_values[i] = (2/3) * k_values[i-1] + (1/3) * rsv_list[i]
            d_values[i] = (2/3) * d_values[i-1] + (1/3) * k_values[i]

        df["k"] = k_values
        df["d"] = d_values
        df["j"] = 3 * df["k"] - 2 * df["d"]

        # 计算信号
        df["signal"] = 0

        # 向量化计算交叉
        # 金叉：K从下往上穿过D
        buy_condition = (df["k"].shift(1) < df["d"].shift(1)) & (df["k"] > df["d"]) & (df["k"] < 50)
        # 死叉：K从上往下穿过D
        sell_condition = (df["k"].shift(1) > df["d"].shift(1)) & (df["k"] < df["d"]) & (df["k"] > 50)

        df.loc[buy_condition, "signal"] = 1
        df.loc[sell_condition, "signal"] = -1

        df["signal_type"] = df["signal"].map({1: "买入", -1: "卖出", 0: "持有"})

        result_columns = ["date", "close", "k", "d", "j", "signal", "signal_type"]
        result = df[result_columns].copy()

        logger.info(f"KDJ策略分析完成，共生成 {len(result[result['signal'] != 0])} 个交易信号")

        return result

    def get_required_columns(self) -> list[str]:
        return ["date", "close", "high", "low"]
