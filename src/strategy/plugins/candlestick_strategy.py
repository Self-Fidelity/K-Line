"""蜡烛图形态策略（Candlestick Pattern Strategy）"""

import pandas as pd
from typing import Any
import numpy as np

from src.strategy.base import BaseStrategy
from src.utils.logger import get_logger

logger = get_logger(__name__)


# 辅助函数（模块级别）
def _get_body_size(row: pd.Series) -> float:
    """获取实体大小（绝对值）"""
    return abs(row["close"] - row["open"])

def _get_upper_shadow(row: pd.Series) -> float:
    """获取上影线长度"""
    return row["high"] - max(row["open"], row["close"])

def _get_lower_shadow(row: pd.Series) -> float:
    """获取下影线长度"""
    return min(row["open"], row["close"]) - row["low"]

def _is_bullish(row: pd.Series) -> bool:
    """判断是否为阳线（收盘价 > 开盘价）"""
    return row["close"] > row["open"]

def _is_bearish(row: pd.Series) -> bool:
    """判断是否为阴线（收盘价 < 开盘价）"""
    return row["close"] < row["open"]

def _is_doji(row: pd.Series, threshold: float = 0.1) -> bool:
    """判断是否为十字星（实体很小）"""
    body_size = _get_body_size(row)
    total_range = row["high"] - row["low"]
    if total_range == 0:
        return False
    return body_size / total_range < threshold


class BullishEngulfingStrategy(BaseStrategy):
    """
    看涨吞没策略（Bullish Engulfing）
    
    策略说明：
    - 第一根K线为阴线，第二根K线为阳线
    - 第二根K线完全吞没第一根K线的实体
    - 第二根K线的开盘价低于第一根K线的收盘价
    - 第二根K线的收盘价高于第一根K线的开盘价
    - 产生买入信号
    """
    
    def __init__(self):
        super().__init__(
            name="Bullish Engulfing",
            description="看涨吞没形态：看涨反转信号",
            detailed_description="""看涨吞没（Bullish Engulfing）是一种看涨反转的蜡烛图形态。

形态特征：
- 第一根K线为阴线（下跌）
- 第二根K线为阳线（上涨）
- 第二根K线完全吞没第一根K线的实体
- 第二根K线的开盘价低于第一根K线的收盘价
- 第二根K线的收盘价高于第一根K线的开盘价

交易信号：
- 产生买入信号

适用场景：
- 出现在下跌趋势中，可能预示反转
- 需要结合其他技术指标确认""",
            parameter_descriptions={}
        )
    
    def analyze(
        self,
        data: pd.DataFrame,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """执行看涨吞没策略分析"""
        if not self.validate_data(data):
            raise ValueError("数据不满足策略要求")
        
        df = data.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        
        df["signal"] = 0
        
        for i in range(1, len(df)):
            prev = df.iloc[i - 1]
            curr = df.iloc[i]
            
            # 前一根为阴线，当前为阳线
            if _is_bearish(prev) and _is_bullish(curr):
                # 当前开盘价 < 前一根收盘价，当前收盘价 > 前一根开盘价
                if curr["open"] < prev["close"] and curr["close"] > prev["open"]:
                    df.iloc[i, df.columns.get_loc("signal")] = 1
        
        df["signal_type"] = df["signal"].map({1: "买入", -1: "卖出", 0: "持有"})
        
        result_columns = ["date", "open", "high", "low", "close", "signal", "signal_type"]
        result = df[result_columns].copy()
        
        signal_count = len(result[result["signal"] != 0])
        logger.info(f"看涨吞没策略分析完成，共生成 {signal_count} 个交易信号")
        
        return result


class BearishEngulfingStrategy(BaseStrategy):
    """
    看跌吞没策略（Bearish Engulfing）
    
    策略说明：
    - 第一根K线为阳线，第二根K线为阴线
    - 第二根K线完全吞没第一根K线的实体
    - 第二根K线的开盘价高于第一根K线的收盘价
    - 第二根K线的收盘价低于第一根K线的开盘价
    - 产生卖出信号
    """
    
    def __init__(self):
        super().__init__(
            name="Bearish Engulfing",
            description="看跌吞没形态：看跌反转信号",
            detailed_description="""看跌吞没（Bearish Engulfing）是一种看跌反转的蜡烛图形态。

形态特征：
- 第一根K线为阳线（上涨）
- 第二根K线为阴线（下跌）
- 第二根K线完全吞没第一根K线的实体
- 第二根K线的开盘价高于第一根K线的收盘价
- 第二根K线的收盘价低于第一根K线的开盘价

交易信号：
- 产生卖出信号

适用场景：
- 出现在上涨趋势中，可能预示反转
- 需要结合其他技术指标确认""",
            parameter_descriptions={}
        )
    
    def analyze(
        self,
        data: pd.DataFrame,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """执行看跌吞没策略分析"""
        if not self.validate_data(data):
            raise ValueError("数据不满足策略要求")
        
        df = data.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        
        df["signal"] = 0
        
        for i in range(1, len(df)):
            prev = df.iloc[i - 1]
            curr = df.iloc[i]
            
            # 前一根为阳线，当前为阴线
            if _is_bullish(prev) and _is_bearish(curr):
                # 当前开盘价 > 前一根收盘价，当前收盘价 < 前一根开盘价
                if curr["open"] > prev["close"] and curr["close"] < prev["open"]:
                    df.iloc[i, df.columns.get_loc("signal")] = -1
        
        df["signal_type"] = df["signal"].map({1: "买入", -1: "卖出", 0: "持有"})
        
        result_columns = ["date", "open", "high", "low", "close", "signal", "signal_type"]
        result = df[result_columns].copy()
        
        signal_count = len(result[result["signal"] != 0])
        logger.info(f"看跌吞没策略分析完成，共生成 {signal_count} 个交易信号")
        
        return result


class HammerStrategy(BaseStrategy):
    """
    锤子线策略（Hammer）
    
    策略说明：
    - 实体小，位于K线上部
    - 下影线长度至少是实体的2倍
    - 上影线很短或没有
    - 可能出现在下跌趋势中，为看涨信号
    - 产生买入信号
    """
    
    def __init__(self, shadow_ratio: float = 2.0):
        """
        初始化锤子线策略
        
        Args:
            shadow_ratio: 下影线与实体的最小比例（默认2.0）
        """
        super().__init__(
            name="Hammer",
            description="锤子线形态：看涨反转信号",
            detailed_description="""锤子线（Hammer）是一种看涨反转的蜡烛图形态。

            形态特征：
            - 实体小，位于K线上部
            - 下影线长度至少是实体的2倍
            - 上影线很短或没有
            - 可能出现在下跌趋势中

            交易信号：
            - 产生买入信号

            适用场景：
            - 出现在下跌趋势底部，可能预示反转
            - 需要结合其他技术指标确认""",
            parameter_descriptions={
                "shadow_ratio": "影线比例：下影线长度与实体长度的最小比例，默认2.0",
            }
        )
        self.shadow_ratio = shadow_ratio

    def get_param_bounds(self) -> dict:
        return {"shadow_ratio": (1.0, 3.5, float)}

    def analyze(
        self,
        data: pd.DataFrame,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """执行锤子线策略分析"""
        if not self.validate_data(data):
            raise ValueError("数据不满足策略要求")
        
        df = data.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        
        shadow_ratio = float(kwargs.get("shadow_ratio", self.shadow_ratio))
        
        df["signal"] = 0
        
        for i in range(len(df)):
            row = df.iloc[i]
            body_size = _get_body_size(row)
            lower_shadow = _get_lower_shadow(row)
            upper_shadow = _get_upper_shadow(row)
            
            if body_size > 0 and lower_shadow > 0:
                # 下影线长度至少是实体的2倍，上影线很短
                if lower_shadow >= body_size * shadow_ratio and upper_shadow <= body_size * 0.5:
                    df.iloc[i, df.columns.get_loc("signal")] = 1
        
        df["signal_type"] = df["signal"].map({1: "买入", -1: "卖出", 0: "持有"})
        
        result_columns = ["date", "open", "high", "low", "close", "signal", "signal_type"]
        result = df[result_columns].copy()
        
        signal_count = len(result[result["signal"] != 0])
        logger.info(f"锤子线策略分析完成，共生成 {signal_count} 个交易信号")
        
        return result


class HangingManStrategy(BaseStrategy):
    """
    上吊线策略（Hanging Man）
    
    策略说明：
    - 实体小，位于K线上部
    - 下影线长度至少是实体的2倍
    - 上影线很短或没有
    - 可能出现在上涨趋势中，为看跌信号
    - 产生卖出信号
    """
    
    def __init__(self, shadow_ratio: float = 2.0):
        """
        初始化上吊线策略
        
        Args:
            shadow_ratio: 下影线与实体的最小比例（默认2.0）
        """
        super().__init__(
            name="Hanging Man",
            description="上吊线形态：看跌反转信号",
            detailed_description="""上吊线（Hanging Man）是一种看跌反转的蜡烛图形态。

形态特征：
- 实体小，位于K线上部
- 下影线长度至少是实体的2倍
- 上影线很短或没有
- 可能出现在上涨趋势中

交易信号：
- 产生卖出信号

适用场景：
- 出现在上涨趋势顶部，可能预示反转
- 需要结合其他技术指标确认""",
            parameter_descriptions={
                "shadow_ratio": "影线比例：下影线长度与实体长度的最小比例，默认2.0",
            }
        )
        self.shadow_ratio = shadow_ratio

    def get_param_bounds(self) -> dict:
        return {"shadow_ratio": (1.0, 3.5, float)}

    def analyze(
        self,
        data: pd.DataFrame,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """执行上吊线策略分析"""
        if not self.validate_data(data):
            raise ValueError("数据不满足策略要求")
        
        df = data.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        
        shadow_ratio = float(kwargs.get("shadow_ratio", self.shadow_ratio))
        
        df["signal"] = 0
        
        for i in range(len(df)):
            row = df.iloc[i]
            body_size = _get_body_size(row)
            lower_shadow = _get_lower_shadow(row)
            upper_shadow = _get_upper_shadow(row)
            
            if body_size > 0 and lower_shadow > 0:
                # 下影线长度至少是实体的2倍，上影线很短
                if lower_shadow >= body_size * shadow_ratio and upper_shadow <= body_size * 0.5:
                    df.iloc[i, df.columns.get_loc("signal")] = -1
        
        df["signal_type"] = df["signal"].map({1: "买入", -1: "卖出", 0: "持有"})
        
        result_columns = ["date", "open", "high", "low", "close", "signal", "signal_type"]
        result = df[result_columns].copy()
        
        signal_count = len(result[result["signal"] != 0])
        logger.info(f"上吊线策略分析完成，共生成 {signal_count} 个交易信号")
        
        return result


class DojiStrategy(BaseStrategy):
    """
    十字星策略（Doji）
    
    策略说明：
    - 开盘价和收盘价非常接近（实体很小）
    - 表示市场犹豫不决
    - 需要结合趋势方向判断（上升趋势中的十字星可能是看跌信号，下降趋势中的十字星可能是看涨信号）
    - 这里简化为：如果出现在下跌后，为买入信号；如果出现在上涨后，为卖出信号
    """
    
    def __init__(self, lookback: int = 5, doji_threshold: float = 0.1):
        """
        初始化十字星策略
        
        Args:
            lookback: 回看周期（用于判断趋势，默认5）
            doji_threshold: 十字星阈值（实体/总范围 < 阈值，默认0.1）
        """
        super().__init__(
            name="Doji",
            description="十字星形态：市场犹豫信号",
            detailed_description="""十字星（Doji）是一种表示市场犹豫不决的蜡烛图形态。

形态特征：
- 开盘价和收盘价非常接近（实体很小）
- 表示买卖双方力量均衡

交易信号：
- 如果出现在下跌后，为买入信号
- 如果出现在上涨后，为卖出信号

适用场景：
- 需要结合趋势方向判断
- 上升趋势中的十字星可能是看跌信号
- 下降趋势中的十字星可能是看涨信号""",
            parameter_descriptions={
                "lookback": "回看周期：用于判断趋势方向的天数，默认5日",
                "doji_threshold": "十字星阈值：实体大小与总波动范围的比例，小于此值认为是十字星，默认0.1",
            }
        )
        self.lookback = lookback
        self.doji_threshold = doji_threshold

    def get_param_bounds(self) -> dict:
        return {
            "lookback": (3, 20, int),
            "doji_threshold": (0.05, 0.25, float),
        }

    def analyze(
        self,
        data: pd.DataFrame,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """执行十字星策略分析"""
        if not self.validate_data(data):
            raise ValueError("数据不满足策略要求")
        
        df = data.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        
        lookback = int(kwargs.get("lookback", self.lookback))
        doji_threshold = float(kwargs.get("doji_threshold", self.doji_threshold))
        
        df["signal"] = 0
        
        for i in range(lookback, len(df)):
            row = df.iloc[i]
            
            # 判断是否为十字星
            if not _is_doji(row, doji_threshold):
                continue
            
            # 计算前N日的价格变化
            prev_price = df.iloc[i - lookback]["close"]
            curr_price = row["close"]
            price_change = (curr_price - prev_price) / prev_price
            
            # 如果之前是下跌趋势（跌幅>2%），十字星可能预示反转，买入信号
            if price_change < -0.02:
                df.iloc[i, df.columns.get_loc("signal")] = 1
            # 如果之前是上涨趋势（涨幅>2%），十字星可能预示反转，卖出信号
            elif price_change > 0.02:
                df.iloc[i, df.columns.get_loc("signal")] = -1
        
        df["signal_type"] = df["signal"].map({1: "买入", -1: "卖出", 0: "持有"})
        
        result_columns = ["date", "open", "high", "low", "close", "signal", "signal_type"]
        result = df[result_columns].copy()
        
        signal_count = len(result[result["signal"] != 0])
        logger.info(f"十字星策略分析完成，共生成 {signal_count} 个交易信号")
        
        return result


class MorningStarStrategy(BaseStrategy):
    """
    早晨之星策略（Morning Star）
    
    策略说明：
    - 三根K线组合：第一根为阴线，第二根为小实体（或十字星），第三根为阳线
    - 第三根阳线的收盘价深入第一根阴线的实体内部
    - 出现在下跌趋势中，为看涨反转信号
    - 产生买入信号
    """
    
    def __init__(self):
        super().__init__(
            name="Morning Star",
            description="早晨之星形态：看涨反转信号",
            detailed_description="""早晨之星（Morning Star）是一种看涨反转的三根K线组合形态。

形态特征：
- 第一根K线为阴线（下跌）
- 第二根K线为小实体（或十字星）
- 第三根K线为阳线（上涨）
- 第三根阳线的收盘价深入第一根阴线的实体内部

交易信号：
- 产生买入信号

适用场景：
- 出现在下跌趋势中，为看涨反转信号
- 需要结合其他技术指标确认""",
            parameter_descriptions={}
        )
    
    def analyze(
        self,
        data: pd.DataFrame,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """执行早晨之星策略分析"""
        if not self.validate_data(data):
            raise ValueError("数据不满足策略要求")
        
        df = data.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        
        df["signal"] = 0
        
        for i in range(2, len(df)):
            first = df.iloc[i - 2]  # 第一根：阴线
            second = df.iloc[i - 1]  # 第二根：小实体或十字星
            third = df.iloc[i]  # 第三根：阳线
            
            # 第一根为阴线
            if not _is_bearish(first):
                continue
            
            # 第二根为小实体（实体小于第一根实体的50%）
            first_body = _get_body_size(first)
            second_body = _get_body_size(second)
            if first_body == 0 or second_body / first_body > 0.5:
                continue
            
            # 第三根为阳线，收盘价深入第一根实体内部（至少50%）
            if not _is_bullish(third):
                continue
            
            first_mid = (first["open"] + first["close"]) / 2
            if third["close"] > first_mid:
                df.iloc[i, df.columns.get_loc("signal")] = 1
        
        df["signal_type"] = df["signal"].map({1: "买入", -1: "卖出", 0: "持有"})
        
        result_columns = ["date", "open", "high", "low", "close", "signal", "signal_type"]
        result = df[result_columns].copy()
        
        signal_count = len(result[result["signal"] != 0])
        logger.info(f"早晨之星策略分析完成，共生成 {signal_count} 个交易信号")
        
        return result


class EveningStarStrategy(BaseStrategy):
    """
    黄昏之星策略（Evening Star）
    
    策略说明：
    - 三根K线组合：第一根为阳线，第二根为小实体（或十字星），第三根为阴线
    - 第三根阴线的收盘价深入第一根阳线的实体内部
    - 出现在上涨趋势中，为看跌反转信号
    - 产生卖出信号
    """
    
    def __init__(self):
        super().__init__(
            name="Evening Star",
            description="黄昏之星形态：看跌反转信号",
            detailed_description="""黄昏之星（Evening Star）是一种看跌反转的三根K线组合形态。

形态特征：
- 第一根K线为阳线（上涨）
- 第二根K线为小实体（或十字星）
- 第三根K线为阴线（下跌）
- 第三根阴线的收盘价深入第一根阳线的实体内部

交易信号：
- 产生卖出信号

适用场景：
- 出现在上涨趋势中，为看跌反转信号
- 需要结合其他技术指标确认""",
            parameter_descriptions={}
        )
    
    def analyze(
        self,
        data: pd.DataFrame,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """执行黄昏之星策略分析"""
        if not self.validate_data(data):
            raise ValueError("数据不满足策略要求")
        
        df = data.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        
        df["signal"] = 0
        
        for i in range(2, len(df)):
            first = df.iloc[i - 2]  # 第一根：阳线
            second = df.iloc[i - 1]  # 第二根：小实体或十字星
            third = df.iloc[i]  # 第三根：阴线
            
            # 第一根为阳线
            if not _is_bullish(first):
                continue
            
            # 第二根为小实体（实体小于第一根实体的50%）
            first_body = _get_body_size(first)
            second_body = _get_body_size(second)
            if first_body == 0 or second_body / first_body > 0.5:
                continue
            
            # 第三根为阴线，收盘价深入第一根实体内部（至少50%）
            if not _is_bearish(third):
                continue
            
            first_mid = (first["open"] + first["close"]) / 2
            if third["close"] < first_mid:
                df.iloc[i, df.columns.get_loc("signal")] = -1
        
        df["signal_type"] = df["signal"].map({1: "买入", -1: "卖出", 0: "持有"})
        
        result_columns = ["date", "open", "high", "low", "close", "signal", "signal_type"]
        result = df[result_columns].copy()
        
        signal_count = len(result[result["signal"] != 0])
        logger.info(f"黄昏之星策略分析完成，共生成 {signal_count} 个交易信号")
        
        return result


class HaramiStrategy(BaseStrategy):
    """
    孕线策略（Harami）
    
    策略说明：
    - 两根K线组合：第一根为大实体，第二根为小实体
    - 第二根K线的实体完全包含在第一根K线的实体内
    - 看涨孕线：第一根为阴线，第二根为阳线（买入信号）
    - 看跌孕线：第一根为阳线，第二根为阴线（卖出信号）
    """
    
    def __init__(self):
        super().__init__(
            name="Harami",
            description="孕线形态：反转信号",
            detailed_description="""孕线（Harami）是一种反转的蜡烛图形态。

形态特征：
- 两根K线组合：第一根为大实体，第二根为小实体
- 第二根K线的实体完全包含在第一根K线的实体内

交易信号：
- 看涨孕线：第一根为阴线，第二根为阳线（买入信号）
- 看跌孕线：第一根为阳线，第二根为阴线（卖出信号）

适用场景：
- 可能出现在趋势转折点
- 需要结合其他技术指标确认""",
            parameter_descriptions={}
        )
    
    def analyze(
        self,
        data: pd.DataFrame,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """执行孕线策略分析"""
        if not self.validate_data(data):
            raise ValueError("数据不满足策略要求")
        
        df = data.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        
        df["signal"] = 0
        
        for i in range(1, len(df)):
            prev = df.iloc[i - 1]
            curr = df.iloc[i]
            
            prev_body = _get_body_size(prev)
            curr_body = _get_body_size(curr)
            
            # 第一根实体必须明显大于第二根（至少2倍）
            if prev_body == 0 or curr_body / prev_body > 0.5:
                continue
            
            # 第二根实体完全包含在第一根实体内
            prev_open = prev["open"]
            prev_close = prev["close"]
            curr_open = curr["open"]
            curr_close = curr["close"]
            
            prev_min = min(prev_open, prev_close)
            prev_max = max(prev_open, prev_close)
            curr_min = min(curr_open, curr_close)
            curr_max = max(curr_open, curr_close)
            
            if curr_min >= prev_min and curr_max <= prev_max:
                # 看涨孕线：第一根为阴线，第二根为阳线
                if _is_bearish(prev) and _is_bullish(curr):
                    df.iloc[i, df.columns.get_loc("signal")] = 1
                # 看跌孕线：第一根为阳线，第二根为阴线
                elif _is_bullish(prev) and _is_bearish(curr):
                    df.iloc[i, df.columns.get_loc("signal")] = -1
        
        df["signal_type"] = df["signal"].map({1: "买入", -1: "卖出", 0: "持有"})
        
        result_columns = ["date", "open", "high", "low", "close", "signal", "signal_type"]
        result = df[result_columns].copy()
        
        signal_count = len(result[result["signal"] != 0])
        logger.info(f"孕线策略分析完成，共生成 {signal_count} 个交易信号")
        
        return result
