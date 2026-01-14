"""动量策略（Momentum Strategy）"""

import pandas as pd
from typing import Any

from src.strategy.base import BaseStrategy
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MomentumStrategy(BaseStrategy):
    """
    动量策略
    
    策略说明：
    - 动量指标衡量价格变化的速度
    - 当动量指标从负转正时，产生买入信号
    - 当动量指标从正转负时，产生卖出信号
    - 默认周期：10日
    """
    
    def __init__(
        self,
        period: int = 10,
    ):
        """
        初始化动量策略
        
        Args:
            period: 动量计算周期（默认10）
        """
        super().__init__(
            name="Momentum Strategy",
            description="动量策略：基于价格变化速度判断趋势",
            detailed_description="""动量策略是一种基于价格变化速度的技术分析策略。

策略原理：
- 动量指标 = 当前价格 - N日前价格
- 当动量指标从负转正时，表示价格开始上涨，产生买入信号
- 当动量指标从正转负时，表示价格开始下跌，产生卖出信号

适用场景：
- 适用于趋势明显的市场
- 可以捕捉价格变化的早期信号

注意事项：
- 周期设置需要根据股票特性调整
- 周期越小，信号越敏感但可能产生假信号
- 周期越大，信号越滞后但更可靠""",
            parameter_descriptions={
                "period": "动量计算周期：计算动量指标的天数，即当前价格与N日前价格的差值，默认10日",
            }
        )
        self.period = period
    
    def analyze(
        self,
        data: pd.DataFrame,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        执行动量策略分析
        
        Args:
            data: 股票数据 DataFrame，必须包含 date, close 列
            **kwargs: 其他参数（可选：period）
        
        Returns:
            分析结果 DataFrame，包含以下列：
            - date: 日期
            - close: 收盘价
            - momentum: 动量指标（当前价格 - N日前价格）
            - signal: 信号（1=买入，-1=卖出，0=持有）
            - signal_type: 信号类型
        """
        if not self.validate_data(data):
            raise ValueError("数据不满足策略要求")
        
        df = data.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        
        period = int(kwargs.get("period", self.period))
        
        # 计算动量（当前价格 - N日前价格）
        df["momentum"] = df["close"] - df["close"].shift(period)
        
        # 生成信号
        df["signal"] = 0
        for i in range(1, len(df)):
            prev_momentum = df.iloc[i - 1]["momentum"]
            curr_momentum = df.iloc[i]["momentum"]
            
            # 动量从负转正：买入信号
            if pd.notna(prev_momentum) and pd.notna(curr_momentum):
                if prev_momentum <= 0 and curr_momentum > 0:
                    df.iloc[i, df.columns.get_loc("signal")] = 1
                # 动量从正转负：卖出信号
                elif prev_momentum >= 0 and curr_momentum < 0:
                    df.iloc[i, df.columns.get_loc("signal")] = -1
        
        df["signal_type"] = df["signal"].map({1: "买入", -1: "卖出", 0: "持有"})
        
        result_columns = ["date", "close", "momentum", "signal", "signal_type"]
        result = df[result_columns].copy()
        
        signal_count = len(result[result["signal"] != 0])
        logger.info(f"动量策略分析完成，共生成 {signal_count} 个交易信号")
        
        return result
    
    def get_required_columns(self) -> list[str]:
        """获取策略需要的列"""
        return ["date", "close"]
