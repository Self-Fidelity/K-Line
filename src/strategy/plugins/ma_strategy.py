"""移动平均策略（MA Strategy）"""

import pandas as pd
from typing import Any, Optional

from src.strategy.base import BaseStrategy
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MAStrategy(BaseStrategy):
    """
    移动平均策略
    
    策略说明：
    - 计算短期移动平均线（SMA）和长期移动平均线（LMA）
    - 当短期均线上穿长期均线时，产生买入信号
    - 当短期均线下穿长期均线时，产生卖出信号
    - 默认短期周期：5日，长期周期：20日
    """
    
    def __init__(
        self,
        short_period: int = 5,
        long_period: int = 20,
    ):
        """
        初始化移动平均策略
        
        Args:
            short_period: 短期移动平均周期（默认5）
            long_period: 长期移动平均周期（默认20）
        """
        super().__init__(
            name="MA Strategy",
            description="移动平均策略：基于短期和长期移动平均线的交叉信号",
            detailed_description="""移动平均（MA）策略是一种经典的技术分析策略。

策略原理：
- 计算短期移动平均线（SMA）和长期移动平均线（LMA）
- 当短期均线上穿长期均线时，形成"金叉"，产生买入信号
- 当短期均线下穿长期均线时，形成"死叉"，产生卖出信号

适用场景：
- 适用于趋势明显的市场
- 在震荡市场中可能产生较多假信号

注意事项：
- 参数设置需要根据股票特性调整
- 短期周期越小，信号越敏感但假信号越多
- 长期周期越大，信号越滞后但更可靠""",
            parameter_descriptions={
                "short_period": "短期移动平均周期：计算短期均线的天数，数值越小对价格变化越敏感，默认5日",
                "long_period": "长期移动平均周期：计算长期均线的天数，数值越大趋势判断越稳定，默认20日",
            }
        )
        self.short_period = short_period
        self.long_period = long_period
    
    def analyze(
        self,
        data: pd.DataFrame,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        执行移动平均策略分析
        
        Args:
            data: 股票数据 DataFrame，必须包含 date, close 列
            **kwargs: 其他参数（可选：short_period, long_period）
        
        Returns:
            分析结果 DataFrame，包含以下列：
            - date: 日期
            - close: 收盘价
            - ma_short: 短期移动平均
            - ma_long: 长期移动平均
            - signal: 信号（1=买入，-1=卖出，0=持有）
            - signal_type: 信号类型（买入/卖出/持有）
        """
        # 验证数据
        if not self.validate_data(data):
            raise ValueError("数据不满足策略要求")
        
        # 复制数据
        df = data.copy()
        df = df.sort_values("date").reset_index(drop=True)
        
        # 使用传入的参数覆盖默认值（如果提供）
        short_period = kwargs.get("short_period", self.short_period)
        long_period = kwargs.get("long_period", self.long_period)
        
        # 计算移动平均线
        df["ma_short"] = df["close"].rolling(window=short_period, min_periods=1).mean()
        df["ma_long"] = df["close"].rolling(window=long_period, min_periods=1).mean()
        
        # 计算信号
        # 短期均线上穿长期均线：买入信号（1）
        # 短期均线下穿长期均线：卖出信号（-1）
        # 其他情况：持有（0）
        df["signal"] = 0
        
        # 判断交叉点
        for i in range(1, len(df)):
            prev_ma_short = df.iloc[i - 1]["ma_short"]
            prev_ma_long = df.iloc[i - 1]["ma_long"]
            curr_ma_short = df.iloc[i]["ma_short"]
            curr_ma_long = df.iloc[i]["ma_long"]
            
            # 金叉：短期均线从下方穿越长期均线
            if prev_ma_short <= prev_ma_long and curr_ma_short > curr_ma_long:
                df.iloc[i, df.columns.get_loc("signal")] = 1
            # 死叉：短期均线从上方穿越长期均线
            elif prev_ma_short >= prev_ma_long and curr_ma_short < curr_ma_long:
                df.iloc[i, df.columns.get_loc("signal")] = -1
        
        # 添加信号类型描述
        df["signal_type"] = df["signal"].map({1: "买入", -1: "卖出", 0: "持有"})
        
        # 选择需要返回的列
        result_columns = ["date", "close", "ma_short", "ma_long", "signal", "signal_type"]
        result = df[result_columns].copy()
        
        logger.info(f"MA策略分析完成，共生成 {len(result[result['signal'] != 0])} 个交易信号")
        
        return result
    
    def get_required_columns(self) -> list[str]:
        """获取策略需要的列"""
        return ["date", "close"]
