"""策略统计分析模块"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List
from src.utils.logger import get_logger

logger = get_logger(__name__)


class StrategyStatistics:
    """策略统计分析类"""
    
    @staticmethod
    def calculate_statistics(
        data: pd.DataFrame,
        strategy_result: pd.DataFrame,
        initial_capital: float = 100000.0,
    ) -> Dict[str, Any]:
        """
        计算策略统计指标
        
        Args:
            data: 原始股票数据（包含 date, close 等列）
            strategy_result: 策略分析结果（包含 date, signal, signal_type 等列）
            initial_capital: 初始资金，默认10万
        
        Returns:
            统计结果字典
        """
        try:
            # 1. 数据预处理
            if data.empty or strategy_result.empty:
                logger.warning("输入数据为空")
                return StrategyStatistics._get_empty_stats()
            
            # 确保日期列为 datetime 类型以便合并
            data = data.copy()
            if "date" not in data.columns:
                # 尝试从 trade_date 转换
                if "trade_date" in data.columns:
                     data["date"] = pd.to_datetime(data["trade_date"], format="%Y%m%d", errors="coerce")
                else:
                    logger.error("数据缺少 date 列")
                    return StrategyStatistics._get_empty_stats()
            else:
                data["date"] = pd.to_datetime(data["date"])
                
            strategy_result = strategy_result.copy()
            strategy_result["date"] = pd.to_datetime(strategy_result["date"])
            
            # 检查必要列
            required_data_cols = ["date", "close"]
            for col in required_data_cols:
                if col not in data.columns:
                    logger.error(f"数据缺少必要列: {col}")
                    return StrategyStatistics._get_empty_stats()
            
            # 补充可选列，如果不存在则填充0或NaN
            for col in ["open", "high", "low", "volume"]:
                if col not in data.columns:
                    data[col] = 0.0

            # 合并数据
            # 使用 merge_asof 或者 inner merge
            # 这里假设 strategy_result 的日期是 data 的子集或完全匹配
            df = pd.merge(
                data[["date", "close", "open", "high", "low", "volume"]],
                strategy_result[["date", "signal"]], # 只取需要的列
                on="date",
                how="inner",
            ).sort_values("date").reset_index(drop=True)
            
            if df.empty:
                logger.warning("合并后的数据为空")
                return StrategyStatistics._get_empty_stats()
            
            # 2. 计算策略权益曲线
            # position: 1=持有, 0=空仓
            df['position'] = 0
            current_pos = 0
            
            # 优化：使用 numpy 向量化操作或 fillna 替代循环 (如果逻辑允许)
            # 但为了保持"信号出现后持仓变化"的逻辑清晰，先保留循环或使用 shift
            # 逻辑：signal=1 -> pos=1 (假设当日收盘成交，持仓从当日开始算? 
            # 通常回测是：Signal T -> Trade T+1 Open. 
            # 现有逻辑简化为：Signal T -> Position T (End of Day) -> Return T+1 depends on Position T.
            
            # 使用循环填充持仓状态 (支持多空，目前仅做多)
            positions = []
            curr = 0
            for sig in df['signal']:
                if sig == 1:
                    curr = 1
                elif sig == -1:
                    curr = 0
                positions.append(curr)
            df['position'] = positions
                
            df['pct_change'] = df['close'].pct_change().fillna(0)
            
            # 策略收益：持有昨天的仓位，享受今天的涨跌
            # shift(1) 是因为今天的收益取决于昨天的持仓
            df['strategy_ret'] = df['position'].shift(1).fillna(0) * df['pct_change']
            
            # 3. 计算权益曲线 (Equity Curve)
            df['equity_curve'] = (1 + df['strategy_ret']).cumprod() * initial_capital
            df['benchmark_curve'] = (1 + df['pct_change']).cumprod() * initial_capital
            
            # 4. 统计交易详情
            trades = StrategyStatistics._calculate_trades(df)
            
            # 5. 计算核心指标
            total_signals = len(df[df["signal"] != 0])
            buy_signals = len(df[df["signal"] == 1])
            sell_signals = len(df[df["signal"] == -1])
            
            # 策略表现
            final_equity = df.iloc[-1]['equity_curve']
            total_return = (final_equity - initial_capital) / initial_capital * 100
            strategy_max_dd = StrategyStatistics._calculate_max_drawdown(df['equity_curve'])
            
            # 基准表现 (买入持有)
            final_benchmark = df.iloc[-1]['benchmark_curve']
            benchmark_return = (final_benchmark - initial_capital) / initial_capital * 100
            benchmark_max_dd = StrategyStatistics._calculate_max_drawdown(df['benchmark_curve'])
            
            # 胜率计算
            profitable_trades = len([t for t in trades if t['profit_rate'] > 0])
            total_trades = len(trades)
            win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0.0

            return {
                "total_signals": total_signals,
                "buy_signals": buy_signals,
                "sell_signals": sell_signals,
                "total_trades": total_trades,
                "profitable_trades": profitable_trades,
                "win_rate": round(win_rate, 2),
                # 策略表现
                "cumulative_return": round(total_return, 2),
                "max_drawdown": round(strategy_max_dd, 2),
                "equity_curve": df['equity_curve'].tolist(),
                # 基准表现
                "benchmark_return": round(benchmark_return, 2),
                "benchmark_max_drawdown": round(benchmark_max_dd, 2),
                "benchmark_curve": df['benchmark_curve'].tolist(),
                # 原始数据(用于图表)
                "dates": df['date'].dt.strftime('%Y-%m-%d').tolist(),
                "close_prices": df['close'].tolist(),
                "trades": trades,
                # 每日收益率数据 (可选)
                "daily_returns": df['strategy_ret'].tolist()
            }
            
        except Exception as e:
            logger.error(f"计算统计指标时发生错误: {e}", exc_info=True)
            # 返回空结果而不是抛出异常，防止API 500
            return StrategyStatistics._get_empty_stats()

    @staticmethod
    def _calculate_trades(df: pd.DataFrame) -> List[Dict]:
        """计算具体交易记录"""
        trades = []
        position = 0
        buy_price = 0.0
        buy_date = None
        
        # 确保数据已排序
        # 迭代查找
        for idx, row in df.iterrows():
            signal = row["signal"]
            price = row["close"]
            date_str = row["date"].strftime('%Y-%m-%d')
            
            if signal == 1 and position == 0:
                # 买入
                position = 1
                buy_price = price
                buy_date = date_str
                trades.append({
                    "date": date_str,
                    "type": "buy",
                    "price": price,
                    "action": "Open Long"
                })
                
            elif signal == -1 and position == 1:
                # 卖出
                position = 0
                profit_rate = (price - buy_price) / buy_price * 100 if buy_price > 0 else 0.0
                trades.append({
                    "date": date_str,
                    "type": "sell",
                    "price": price,
                    "buy_price": buy_price,
                    "buy_date": buy_date,
                    "profit_rate": profit_rate,
                    "action": "Close Long"
                })
                
        return trades

    @staticmethod
    def _calculate_max_drawdown(equity_curve: pd.Series) -> float:
        """计算最大回撤"""
        if len(equity_curve) == 0:
            return 0.0
        
        # 计算累计最大值
        rolling_max = equity_curve.cummax()
        # 计算回撤
        drawdown = (equity_curve - rolling_max) / rolling_max * 100
        # 最小的值即为最大回撤 (负数), 取绝对值
        return abs(drawdown.min())

    @staticmethod
    def _get_empty_stats() -> Dict[str, Any]:
        return {
            "total_signals": 0,
            "buy_signals": 0,
            "sell_signals": 0,
            "total_trades": 0,
            "profitable_trades": 0,
            "win_rate": 0.0,
            "cumulative_return": 0.0,
            "max_drawdown": 0.0,
            "benchmark_return": 0.0,
            "benchmark_max_drawdown": 0.0,
            "equity_curve": [],
            "benchmark_curve": [],
            "dates": [],
            "close_prices": [],
            "trades": [],
            "daily_returns": []
        }

    @staticmethod
    def print_statistics(stats: Dict[str, Any]) -> None:
        """打印统计结果"""
        print("\n" + "=" * 60)
        print("策略统计分析结果")
        print("=" * 60)
        print(f"交易统计:")
        print(f"  总交易次数: {stats.get('total_trades', 0)}")
        print(f"  盈利交易: {stats.get('profitable_trades', 0)}")
        print(f"  胜率: {stats.get('win_rate', 0):.2f}%")
        print(f"\n策略表现:")
        print(f"  累计收益率: {stats.get('cumulative_return', 0):.2f}%")
        print(f"  最大回撤: {stats.get('max_drawdown', 0):.2f}%")
        print(f"\n基准表现 (买入持有):")
        print(f"  累计收益率: {stats.get('benchmark_return', 0):.2f}%")
        print(f"  最大回撤: {stats.get('benchmark_max_drawdown', 0):.2f}%")
        print("=" * 60 + "\n")
