"""策略统计分析模块"""

import pandas as pd
from typing import Dict, Any, Optional
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
            initial_capital: 初始资金（默认100000）
        
        Returns:
            统计结果字典，包含：
            - total_signals: 总信号数
            - buy_signals: 买入信号数
            - sell_signals: 卖出信号数
            - total_return: 总收益率
            - cumulative_return: 累计收益率
            - win_rate: 胜率（成功率）
            - max_drawdown: 最大回撤
            - sharpe_ratio: 夏普比率（如果数据足够）
            - trades: 交易记录列表
        """
        # 合并数据
        df = pd.merge(
            data[["date", "close"]],
            strategy_result[["date", "signal", "signal_type"]],
            on="date",
            how="inner",
        ).sort_values("date").reset_index(drop=True)
        
        if df.empty:
            return {
                "total_signals": 0,
                "buy_signals": 0,
                "sell_signals": 0,
                "total_return": 0.0,
                "cumulative_return": 0.0,
                "win_rate": 0.0,
                "max_drawdown": 0.0,
                "trades": [],
            }
        
        # 统计信号数量
        buy_signals = len(df[df["signal"] == 1])
        sell_signals = len(df[df["signal"] == -1])
        total_signals = buy_signals + sell_signals
        
        # 计算交易和收益率
        trades = []
        capital = initial_capital
        position = 0  # 持仓数量
        buy_price = 0.0
        total_profit = 0.0
        profitable_trades = 0
        total_trades = 0
        
        # 记录每日市值
        equity_curve = []
        
        for i in range(len(df)):
            row = df.iloc[i]
            date = row["date"]
            close_price = row["close"]
            signal = row["signal"]
            
            # 更新当前市值
            current_value = capital + position * close_price
            equity_curve.append(current_value)
            
            if signal == 1:  # 买入信号
                if position == 0:  # 没有持仓，买入
                    # 使用全部资金买入（简化处理，不考虑手续费）
                    position = capital / close_price
                    buy_price = close_price
                    capital = 0.0
                    trades.append({
                        "date": date,
                        "type": "buy",
                        "price": close_price,
                        "shares": position,
                    })
            
            elif signal == -1:  # 卖出信号
                if position > 0:  # 有持仓，卖出
                    # 全部卖出
                    capital = position * close_price
                    profit = capital - (position * buy_price)
                    profit_rate = (close_price - buy_price) / buy_price * 100
                    
                    total_profit += profit
                    total_trades += 1
                    if profit > 0:
                        profitable_trades += 1
                    
                    trades.append({
                        "date": date,
                        "type": "sell",
                        "price": close_price,
                        "shares": position,
                        "buy_price": buy_price,
                        "profit": profit,
                        "profit_rate": profit_rate,
                    })
                    
                    position = 0.0
                    buy_price = 0.0
        
        # 如果最后还有持仓，按最后价格计算
        if position > 0 and len(df) > 0:
            final_price = df.iloc[-1]["close"]
            final_capital = capital + position * final_price
            profit = (position * final_price) - (position * buy_price)
            profit_rate = (final_price - buy_price) / buy_price * 100 if buy_price > 0 else 0.0
            
            total_profit += profit
            total_trades += 1
            if profit > 0:
                profitable_trades += 1
            
            equity_curve[-1] = final_capital
        else:
            final_capital = capital
        
        # 计算收益率
        total_return = (final_capital - initial_capital) / initial_capital * 100
        cumulative_return = total_return
        
        # 计算胜率
        win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0.0
        
        # 计算最大回撤
        max_drawdown = 0.0
        if equity_curve:
            peak = equity_curve[0]
            for value in equity_curve:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak * 100
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
        
        return {
            "total_signals": total_signals,
            "buy_signals": buy_signals,
            "sell_signals": sell_signals,
            "total_return": round(total_return, 2),
            "cumulative_return": round(cumulative_return, 2),
            "win_rate": round(win_rate, 2),
            "max_drawdown": round(max_drawdown, 2),
            "total_trades": total_trades,
            "profitable_trades": profitable_trades,
            "final_capital": round(final_capital, 2),
            "total_profit": round(total_profit, 2),
            "trades": trades,
        }
    
    @staticmethod
    def print_statistics(stats: Dict[str, Any]) -> None:
        """
        打印统计结果
        
        Args:
            stats: 统计结果字典
        """
        print("\n" + "=" * 60)
        print("策略统计分析结果")
        print("=" * 60)
        print(f"总信号数: {stats['total_signals']}")
        print(f"  买入信号: {stats['buy_signals']}")
        print(f"  卖出信号: {stats['sell_signals']}")
        print(f"\n交易统计:")
        print(f"  总交易次数: {stats['total_trades']}")
        print(f"  盈利交易: {stats['profitable_trades']}")
        print(f"  胜率（成功率）: {stats['win_rate']:.2f}%")
        print(f"\n收益率:")
        print(f"  累计收益率: {stats['cumulative_return']:.2f}%")
        print(f"  总收益: {stats['total_profit']:.2f}")
        print(f"  最终资金: {stats['final_capital']:.2f}")
        print(f"\n风险指标:")
        print(f"  最大回撤: {stats['max_drawdown']:.2f}%")
        print("=" * 60 + "\n")
