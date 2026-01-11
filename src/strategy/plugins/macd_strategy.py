"""MACD策略（Moving Average Convergence Divergence Strategy）"""

import pandas as pd
from typing import Any

from src.strategy.base import BaseStrategy
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MACDStrategy(BaseStrategy):
    """
    MACD策略（移动平均收敛散度策略）
    
    策略说明：
    - MACD由快线（EMA12）、慢线（EMA26）和信号线（MACD的9日EMA）组成
    - 当MACD线上穿信号线时，产生买入信号（金叉）
    - 当MACD线下穿信号线时，产生卖出信号（死叉）
    - 默认参数：快线周期12，慢线周期26，信号线周期9
    """
    
    def __init__(
        self,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ):
        """
        初始化MACD策略
        
        Args:
            fast_period: 快线EMA周期（默认12）
            slow_period: 慢线EMA周期（默认26）
            signal_period: 信号线EMA周期（默认9）
        """
        super().__init__(
            name="MACD Strategy",
            description="MACD策略：基于移动平均收敛散度指标判断趋势",
            detailed_description="""MACD（移动平均收敛散度）策略是一种趋势跟踪策略。

策略原理：
- MACD由快线（EMA12）、慢线（EMA26）和信号线（MACD的9日EMA）组成
- MACD线 = 快线 - 慢线
- 当MACD线上穿信号线时，形成"金叉"，产生买入信号
- 当MACD线下穿信号线时，形成"死叉"，产生卖出信号

适用场景：
- 适用于趋势明显的市场
- 在震荡市场中可能产生较多假信号

注意事项：
- 快线周期越小，对价格变化越敏感
- 慢线周期越大，趋势判断越稳定
- 信号线周期影响信号的滞后性""",
            parameter_descriptions={
                "fast_period": "快线EMA周期：计算快线指数移动平均的天数，数值越小越敏感，默认12日",
                "slow_period": "慢线EMA周期：计算慢线指数移动平均的天数，数值越大越稳定，默认26日",
                "signal_period": "信号线周期：计算信号线（MACD的EMA）的天数，影响信号滞后性，默认9日",
            }
        )
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
    
    def _calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """计算指数移动平均"""
        return prices.ewm(span=period, adjust=False).mean()
    
    def analyze(
        self,
        data: pd.DataFrame,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        执行MACD策略分析
        
        Args:
            data: 股票数据 DataFrame，必须包含 date, close 列
            **kwargs: 其他参数（可选：fast_period, slow_period, signal_period）
        
        Returns:
            分析结果 DataFrame，包含以下列：
            - date: 日期
            - close: 收盘价
            - macd: MACD线
            - signal: 信号线
            - histogram: MACD柱状图（MACD - Signal）
            - signal: 信号（1=买入，-1=卖出，0=持有）
            - signal_type: 信号类型
        """
        if not self.validate_data(data):
            raise ValueError("数据不满足策略要求")
        
        df = data.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        
        fast_period = kwargs.get("fast_period", self.fast_period)
        slow_period = kwargs.get("slow_period", self.slow_period)
        signal_period = kwargs.get("signal_period", self.signal_period)
        
        # 计算快线和慢线
        ema_fast = self._calculate_ema(df["close"], fast_period)
        ema_slow = self._calculate_ema(df["close"], slow_period)
        
        # 计算MACD线
        df["macd"] = ema_fast - ema_slow
        
        # 计算信号线（MACD的EMA）
        df["signal"] = self._calculate_ema(df["macd"], signal_period)
        
        # 计算MACD柱状图
        df["histogram"] = df["macd"] - df["signal"]
        
        # 生成交易信号
        df["trade_signal"] = 0
        for i in range(1, len(df)):
            prev_macd = df.iloc[i - 1]["macd"]
            prev_signal = df.iloc[i - 1]["signal"]
            curr_macd = df.iloc[i]["macd"]
            curr_signal = df.iloc[i]["signal"]
            
            # 金叉：MACD从下方穿越信号线
            if prev_macd <= prev_signal and curr_macd > curr_signal:
                df.iloc[i, df.columns.get_loc("trade_signal")] = 1
            # 死叉：MACD从上方穿越信号线
            elif prev_macd >= prev_signal and curr_macd < curr_signal:
                df.iloc[i, df.columns.get_loc("trade_signal")] = -1
        
        # 重命名列以避免冲突
        df = df.rename(columns={"signal": "signal_line"})
        df = df.rename(columns={"trade_signal": "signal"})
        
        df["signal_type"] = df["signal"].map({1: "买入", -1: "卖出", 0: "持有"})
        
        result_columns = ["date", "close", "macd", "signal_line", "histogram", "signal", "signal_type"]
        result = df[result_columns].copy()
        
        signal_count = len(result[result["signal"] != 0])
        logger.info(f"MACD策略分析完成，共生成 {signal_count} 个交易信号")
        
        return result
