"""成交量加权移动平均策略 (VWMA)"""

import pandas as pd
from typing import Any

from src.strategy.base import BaseStrategy
from src.utils.logger import get_logger

logger = get_logger(__name__)


class VWMAStrategy(BaseStrategy):
    """
    成交量加权移动平均策略 (VWMA)

    策略说明：
    - VWMA (Volume Weighted Moving Average) 相比普通 MA 更重视成交量大的价格。
    - 策略原理类似于 MA 交叉，但使用 VWMA 替代 SMA。
    - 买入信号：短期 VWMA 上穿长期 VWMA。
    - 卖出信号：短期 VWMA 下穿长期 VWMA。
    """

    def __init__(
        self,
        short_period: int = 5,
        long_period: int = 20,
    ):
        super().__init__(
            name="VWMA Strategy",
            description="VWMA策略：基于成交量加权移动平均的交叉策略",
            detailed_description="""成交量加权移动平均 (VWMA)

策略原理：
VWMA = Sum(Price * Volume) / Sum(Volume)
VWMA 赋予成交量大的价格更高的权重，因此比简单移动平均 (SMA) 更能反映市场真实成本和趋势力度。

交易信号：
- 买入：短期 VWMA 上穿长期 VWMA（金叉）。
- 卖出：短期 VWMA 下穿长期 VWMA（死叉）。

VWMA 能够过滤掉无量上涨或下跌带来的虚假信号。

参数说明：
- short_period: 短期周期，默认5
- long_period: 长期周期，默认20
""",
            parameter_descriptions={
                "short_period": "短期周期，默认5",
                "long_period": "长期周期，默认20",
            }
        )
        self.short_period = short_period
        self.long_period = long_period

    def analyze(
        self,
        data: pd.DataFrame,
        **kwargs: Any,
    ) -> pd.DataFrame:
        if not self.validate_data(data):
            raise ValueError("数据不满足策略要求")

        df = data.copy()
        df = df.sort_values("date").reset_index(drop=True)

        short_period = int(kwargs.get("short_period", self.short_period))
        long_period = int(kwargs.get("long_period", self.long_period))

        # 计算 PV = Price * Volume
        df["pv"] = df["close"] * df["volume"]

        # 计算 VWMA
        # VWMA = RollingSum(PV) / RollingSum(Volume)

        df["vwma_short"] = df["pv"].rolling(window=short_period).sum() / df["volume"].rolling(window=short_period).sum()
        df["vwma_long"] = df["pv"].rolling(window=long_period).sum() / df["volume"].rolling(window=long_period).sum()

        df["signal"] = 0

        # 交叉判断
        for i in range(1, len(df)):
            prev_s = df.iloc[i-1]["vwma_short"]
            prev_l = df.iloc[i-1]["vwma_long"]
            curr_s = df.iloc[i]["vwma_short"]
            curr_l = df.iloc[i]["vwma_long"]

            if pd.isna(prev_s) or pd.isna(prev_l) or pd.isna(curr_s) or pd.isna(curr_l):
                continue

            if prev_s <= prev_l and curr_s > curr_l:
                df.iloc[i, df.columns.get_loc("signal")] = 1
            elif prev_s >= prev_l and curr_s < curr_l:
                df.iloc[i, df.columns.get_loc("signal")] = -1

        df["signal_type"] = df["signal"].map({1: "买入", -1: "卖出", 0: "持有"})

        result_columns = ["date", "close", "vwma_short", "vwma_long", "signal", "signal_type"]
        result = df[result_columns].copy()

        logger.info(f"VWMA策略分析完成，共生成 {len(result[result['signal'] != 0])} 个交易信号")

        return result

    def get_required_columns(self) -> list[str]:
        return ["date", "close", "volume"]
