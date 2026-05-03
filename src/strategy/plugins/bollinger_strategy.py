"""布林带策略（Bollinger Bands Strategy）"""

import pandas as pd
from typing import Any

from src.strategy.base import BaseStrategy
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BollingerStrategy(BaseStrategy):
    """
    布林带策略
    
    策略说明：
    - 布林带由中轨（移动平均）、上轨（中轨+标准差倍数）、下轨（中轨-标准差倍数）组成
    - 当价格触及下轨时，产生买入信号（超卖）
    - 当价格触及上轨时，产生卖出信号（超买）
    - 默认参数：周期20，标准差倍数2
    """
    
    def __init__(
        self,
        period: int = 20,
        std_dev: float = 2.0,
    ):
        """
        初始化布林带策略
        
        Args:
            period: 移动平均周期（默认20）
            std_dev: 标准差倍数（默认2.0）
        """
        super().__init__(
            name="Bollinger Strategy",
            description="布林带策略：基于价格与布林带上下轨的关系判断超买超卖",
            detailed_description="""布林带（Bollinger Bands）策略是一种基于统计学的技术分析策略。

策略原理：
- 布林带由三条线组成：中轨（移动平均）、上轨（中轨+标准差倍数）、下轨（中轨-标准差倍数）
- 当价格触及或跌破下轨时，表示超卖，可能产生买入信号
- 当价格触及或突破上轨时，表示超买，可能产生卖出信号

适用场景：
- 适用于震荡市场
- 在趋势市场中需要结合其他指标

注意事项：
- 标准差倍数越大，上下轨越宽，信号越少但更可靠
- 标准差倍数越小，上下轨越窄，信号越多但可能产生假信号""",
            parameter_descriptions={
                "period": "移动平均周期：计算中轨（移动平均）的天数，默认20日",
                "std_dev": "标准差倍数：用于计算上下轨的标准差倍数，数值越大布林带越宽，默认2.0",
            }
        )
        self.period = period
        self.std_dev = std_dev
    
    def get_param_bounds(self) -> dict:
        return {
            "period": (10, 50, int),
            "std_dev": (0.5, 3.5, float),
        }

    def analyze(
        self,
        data: pd.DataFrame,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        执行布林带策略分析
        
        Args:
            data: 股票数据 DataFrame，必须包含 date, close 列
            **kwargs: 其他参数（可选：period, std_dev）
        
        Returns:
            分析结果 DataFrame，包含以下列：
            - date: 日期
            - close: 收盘价
            - upper_band: 上轨
            - middle_band: 中轨（移动平均）
            - lower_band: 下轨
            - signal: 信号（1=买入，-1=卖出，0=持有）
            - signal_type: 信号类型
        """
        if not self.validate_data(data):
            raise ValueError("数据不满足策略要求")
        
        df = data.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        
        period = int(kwargs.get("period", self.period))
        std_dev = float(kwargs.get("std_dev", self.std_dev))
        
        # 计算中轨（移动平均）
        df["middle_band"] = df["close"].rolling(window=period).mean()
        
        # 计算标准差
        std = df["close"].rolling(window=period).std()
        
        # 计算上轨和下轨
        df["upper_band"] = df["middle_band"] + (std * std_dev)
        df["lower_band"] = df["middle_band"] - (std * std_dev)
        
        # 生成信号（只在状态变化时产生信号）
        df["signal"] = 0
        for i in range(1, len(df)):
            prev_close = df.iloc[i - 1]["close"]
            curr_close = df.iloc[i]["close"]
            prev_lower = df.iloc[i - 1]["lower_band"]
            curr_lower = df.iloc[i]["lower_band"]
            prev_upper = df.iloc[i - 1]["upper_band"]
            curr_upper = df.iloc[i]["upper_band"]
            
            # 从下轨下方上穿下轨：买入信号
            if prev_close <= prev_lower and curr_close > curr_lower:
                df.iloc[i, df.columns.get_loc("signal")] = 1
            # 从上轨上方下穿上轨：卖出信号
            elif prev_close >= prev_upper and curr_close < curr_upper:
                df.iloc[i, df.columns.get_loc("signal")] = -1
        
        df["signal_type"] = df["signal"].map({1: "买入", -1: "卖出", 0: "持有"})
        
        result_columns = ["date", "close", "upper_band", "middle_band", "lower_band", "signal", "signal_type"]
        result = df[result_columns].copy()
        
        signal_count = len(result[result["signal"] != 0])
        logger.info(f"布林带策略分析完成，共生成 {signal_count} 个交易信号")
        
        return result
    
    def get_required_columns(self) -> list[str]:
        """获取策略需要的列"""
        return ["date", "close"]
