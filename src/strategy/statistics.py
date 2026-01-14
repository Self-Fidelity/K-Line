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
        risk_free_rate: float = 0.02, # 无风险利率，默认2%
    ) -> Dict[str, Any]:
        """
        计算策略统计指标
        
        Args:
            data: 原始股票数据（包含 date, close 等列）
            strategy_result: 策略分析结果（包含 date, signal, signal_type 等列）
            initial_capital: 初始资金，默认10万
            risk_free_rate: 年化无风险利率，默认0.02
        
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
            df = pd.merge(
                data[["date", "close", "open", "high", "low", "volume"]],
                strategy_result[["date", "signal"]],
                on="date",
                how="inner",
            ).sort_values("date").reset_index(drop=True)
            
            if df.empty:
                logger.warning("合并后的数据为空")
                return StrategyStatistics._get_empty_stats()
            
            # 2. 计算策略权益曲线
            # position: 1=持有, 0=空仓
            # 简单逻辑：信号 1 -> 买入(持有), -1 -> 卖出(空仓), 0 -> 保持
            df['position'] = 0
            current_pos = 0
            
            positions = []
            for sig in df['signal']:
                if sig == 1:
                    current_pos = 1
                elif sig == -1:
                    current_pos = 0
                positions.append(current_pos)
            
            # 信号在收盘产生，实际交易通常在次日开盘或当日收盘
            # 这里简化为：信号当日收盘成交，持仓从次日生效（或者当日收盘价计算收益需看具体逻辑）
            # 通常：持仓状态在 T 日确定，T+1 日的收益取决于 T 日的持仓
            # df['position'] 代表 T 日收盘后的持仓
            df['position'] = positions
            
            # 计算日收益率：(Today Close - Prev Close) / Prev Close
            df['market_ret'] = df['close'].pct_change().fillna(0.0)
            
            # 策略日收益率 = 昨日持仓 * 今日市场收益率
            # shift(1) 是为了取昨日持仓
            df['strategy_ret'] = df['position'].shift(1).fillna(0.0) * df['market_ret']
            
            # 扣除交易成本（简化）
            # 假设双边万分之三
            commission_rate = 0.0003
            # 交易发生点：position 变化
            df['trade_occurred'] = df['position'].diff().abs().fillna(0.0)
            df['commission'] = df['trade_occurred'] * commission_rate
            
            df['strategy_ret_net'] = df['strategy_ret'] - df['commission']
            
            # 计算净值曲线
            df['equity_curve'] = initial_capital * (1 + df['strategy_ret_net']).cumprod()
            
            # 3. 计算基准权益曲线 (Buy & Hold)
            df['benchmark_curve'] = initial_capital * (1 + df['market_ret']).cumprod()
            
            # 4. 计算统计指标
            
            # 最终权益
            final_equity = df['equity_curve'].iloc[-1]
            final_benchmark = df['benchmark_curve'].iloc[-1]
            
            # 累计收益率
            total_return = (final_equity - initial_capital) / initial_capital * 100
            benchmark_return = (final_benchmark - initial_capital) / initial_capital * 100
            
            # 年化收益率 (假设252个交易日)
            days = len(df)
            annual_return = 0.0
            if days > 0:
                annual_return = ((final_equity / initial_capital) ** (252 / days) - 1) * 100
            
            # 最大回撤
            strategy_max_dd = StrategyStatistics._calculate_max_drawdown(df['equity_curve'])
            benchmark_max_dd = StrategyStatistics._calculate_max_drawdown(df['benchmark_curve'])
            
            # 夏普比率 (Sharpe Ratio)
            # Sharpe = (Rp - Rf) / sigma_p
            # 使用日收益率计算，需年化
            strategy_std = df['strategy_ret_net'].std()
            sharpe_ratio = 0.0
            if strategy_std > 0:
                # 年化超额收益
                excess_daily_ret = df['strategy_ret_net'].mean() - (risk_free_rate / 252)
                sharpe_ratio = (excess_daily_ret / strategy_std) * np.sqrt(252)
                
            # 索提诺比率 (Sortino Ratio)
            # 只考虑下行波动
            downside_returns = df.loc[df['strategy_ret_net'] < 0, 'strategy_ret_net']
            downside_std = downside_returns.std()
            sortino_ratio = 0.0
            if downside_std > 0:
                excess_daily_ret = df['strategy_ret_net'].mean() - (risk_free_rate / 252)
                sortino_ratio = (excess_daily_ret / downside_std) * np.sqrt(252)
            
            # 胜率 (Win Rate)
            # 统计所有产生收益的交易
            trades = StrategyStatistics._calculate_trades(df)
            winning_trades = [t for t in trades if t.get('profit_rate', 0) > 0]
            total_closed_trades = len([t for t in trades if t.get('type') == 'sell'])
            win_rate = (len(winning_trades) / total_closed_trades * 100) if total_closed_trades > 0 else 0.0
            
            # 盈亏比 (Profit/Loss Ratio)
            avg_win = np.mean([t['profit_rate'] for t in winning_trades]) if winning_trades else 0
            losing_trades = [t for t in trades if t.get('profit_rate', 0) <= 0 and t.get('type') == 'sell']
            avg_loss = np.mean([t['profit_rate'] for t in losing_trades]) if losing_trades else 0
            pl_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else (999.0 if avg_win > 0 else 0.0)
            
            # 统计信号数量
            total_signals = len(df[df['signal'] != 0])
            buy_signals = len(df[df['signal'] == 1])
            sell_signals = len(df[df['signal'] == -1])

            return {
                "initial_capital": initial_capital,
                "final_equity": round(final_equity, 2),
                "cumulative_return": round(total_return, 2),
                "annual_return": round(annual_return, 2),
                "max_drawdown": round(strategy_max_dd, 2),
                "sharpe_ratio": round(sharpe_ratio, 3),
                "sortino_ratio": round(sortino_ratio, 3),
                "win_rate": round(win_rate, 2),
                "pl_ratio": round(pl_ratio, 2),
                "total_trades": total_closed_trades,
                "profitable_trades": len(winning_trades),
                
                # 信号统计
                "total_signals": total_signals,
                "buy_signals": buy_signals,
                "sell_signals": sell_signals,
                
                "benchmark_return": round(benchmark_return, 2),
                "benchmark_max_drawdown": round(benchmark_max_dd, 2),
                
                # 曲线数据 (用于前端绘图)
                "equity_curve": df['equity_curve'].tolist(),
                "benchmark_curve": df['benchmark_curve'].tolist(),
                
                # 原始数据
                "dates": df['date'].dt.strftime('%Y-%m-%d').tolist(),
                "close_prices": df['close'].tolist(),
                "trades": trades,
                
                # 每日收益率数据 (用于热力图)
                "daily_returns": df['strategy_ret_net'].tolist()
            }
            
        except Exception as e:
            logger.error(f"计算统计指标时发生错误: {e}", exc_info=True)
            return StrategyStatistics._get_empty_stats()

    @staticmethod
    def _calculate_max_drawdown(equity_curve: pd.Series) -> float:
        """计算最大回撤"""
        if equity_curve.empty:
            return 0.0
            
        # 计算累计最大值
        rolling_max = equity_curve.cummax()
        # 计算回撤
        drawdown = (equity_curve - rolling_max) / rolling_max * 100
        # 取最小回撤（绝对值最大的负数）
        return abs(drawdown.min())

    @staticmethod
    def _calculate_trades(df: pd.DataFrame) -> List[Dict]:
        """计算具体交易记录"""
        trades = []
        position = 0
        buy_price = 0.0
        buy_date = None
        
        # 迭代查找
        for idx, row in df.iterrows():
            signal = row["signal"]
            price = row["close"]
            date_str = row["date"].strftime('%Y-%m-%d')
            
            # 信号产生后，次日（或当日收盘）执行，这里简化为信号即成交
            
            if signal == 1 and position == 0:
                # 开仓买入
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
                # 平仓卖出
                position = 0
                profit = (price - buy_price)
                profit_rate = profit / buy_price * 100 if buy_price > 0 else 0.0
                
                trades.append({
                    "date": date_str,
                    "type": "sell",
                    "price": price,
                    "buy_price": buy_price,
                    "buy_date": buy_date,
                    "profit": profit,
                    "profit_rate": profit_rate,
                    "action": "Close Long"
                })
                
        return trades

    @staticmethod
    def _get_empty_stats() -> Dict[str, Any]:
        """获取空统计结果"""
        return {
            "initial_capital": 0.0,
            "final_equity": 0.0,
            "cumulative_return": 0.0,
            "annual_return": 0.0,
            "max_drawdown": 0.0,
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0,
            "win_rate": 0.0,
            "pl_ratio": 0.0,
            "total_trades": 0,
            "profitable_trades": 0,
            "total_signals": 0,
            "buy_signals": 0,
            "sell_signals": 0,
            "benchmark_return": 0.0,
            "benchmark_max_drawdown": 0.0,
            "equity_curve": [],
            "benchmark_curve": [],
            "dates": [],
            "close_prices": [],
            "trades": [],
            "daily_returns": []
        }
