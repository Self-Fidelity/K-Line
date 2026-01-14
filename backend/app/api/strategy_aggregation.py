"""
Strategy Aggregation Router

Combines signals from multiple strategies using weighted voting logic.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd
import numpy as np

from ..services.strategy_service import StrategyService
from ..services.data_service import DataService
from ..api.auth import get_current_user_id

router = APIRouter()


class StrategyWithWeight(BaseModel):
    """Strategy configuration with weight"""
    name: str
    params: Dict[str, float] = Field(default_factory=dict)
    weight: float = Field(default=1.0, ge=0.1, le=10.0)  # Weight range: 0.1-10.0


class AggregationSettings(BaseModel):
    """Aggregation settings for weighted voting"""
    buy_threshold: float = Field(ge=0.0)  # Minimum buy weight to trigger buy
    sell_threshold: float = Field(ge=0.0)  # Minimum sell weight to trigger sell
    required_strategies: List[str] = Field(default_factory=list)  # Must be present (veto power)


class AggregationRequest(BaseModel):
    """Request for strategy aggregation analysis"""
    stock_code: str = Field(min_length=6, max_length=6)
    start_date: str
    end_date: str
    strategies: List[StrategyWithWeight]
    settings: AggregationSettings


class SignalDetail(BaseModel):
    """Individual strategy signal detail"""
    strategy_name: str
    signal: int  # 1=buy, -1=sell, 0=hold
    weight: float


class AggregatedSignal(BaseModel):
    """Aggregated signal for a specific date"""
    date: str
    final_signal: int  # 1=buy, -1=sell, 0=hold
    buy_weight: float
    sell_weight: float
    strategy_details: List[SignalDetail]


class AggregationResponse(BaseModel):
    """Response from aggregation analysis"""
    stock_code: str
    stock_name: Optional[str]
    start_date: str
    end_date: str
    aggregated_signals: List[AggregatedSignal]
    trade_records: List[Dict]
    statistics: Dict
    total_weight: float  # Sum of all strategy weights


def aggregate_signals_by_date(
    strategy_results: Dict[str, pd.DataFrame],
    weights: Dict[str, float],
    settings: AggregationSettings
) -> List[AggregatedSignal]:
    """
    Aggregate signals from multiple strategies using weighted voting.
    
    Logic:
    1. For each date, calculate buy_weight and sell_weight
    2. Check if required strategies are present
    3. Apply thresholds to generate final signal
    """
    # Ensure dates are strings to avoid type mismatch
    for name in strategy_results:
        if 'date' in strategy_results[name].columns:
             strategy_results[name]['date'] = strategy_results[name]['date'].astype(str)

    # Get all unique dates from all strategies
    all_dates = set()
    for df in strategy_results.values():
        if 'signal' in df.columns:
            all_dates.update(df['date'].tolist())
    
    all_dates = sorted(list(all_dates))
    aggregated_signals = []
    
    for date in all_dates:
        # ...
        buy_weight = 0.0
        sell_weight = 0.0
        strategy_details = []
        
        # Collect signals from all strategies for this date
        for strategy_name, df in strategy_results.items():
            date_data = df[df['date'] == date]
            if not date_data.empty and 'signal' in df.columns:
                signal = int(date_data.iloc[0]['signal'])
                weight = weights[strategy_name]
                
                strategy_details.append(SignalDetail(
                    strategy_name=strategy_name,
                    signal=signal,
                    weight=weight
                ))
                
                if signal == 1:  # Buy signal
                    buy_weight += weight
                elif signal == -1:  # Sell signal
                    sell_weight += weight
        
        # Check required strategies
        if settings.required_strategies:
            present_strategies = {detail.strategy_name for detail in strategy_details}
            required_present = all(req in present_strategies for req in settings.required_strategies)
            
            # If required strategies missing, no signal
            if not required_present:
                aggregated_signals.append(AggregatedSignal(
                    date=date,
                    final_signal=0,
                    buy_weight=buy_weight,
                    sell_weight=sell_weight,
                    strategy_details=strategy_details
                ))
                continue
        
        # Apply weighted voting logic
        final_signal = 0
        
        if buy_weight >= settings.buy_threshold and sell_weight < settings.sell_threshold:
            final_signal = 1  # BUY
        elif sell_weight >= settings.sell_threshold and buy_weight < settings.buy_threshold:
            final_signal = -1  # SELL
        elif buy_weight >= settings.buy_threshold and sell_weight >= settings.sell_threshold:
            # Conflict: higher weight wins
            final_signal = 1 if buy_weight > sell_weight else -1
        # else: final_signal = 0 (HOLD)
        
        aggregated_signals.append(AggregatedSignal(
            date=date,
            final_signal=final_signal,
            buy_weight=buy_weight,
            sell_weight=sell_weight,
            strategy_details=strategy_details
        ))
    
    return aggregated_signals


def calculate_trade_records(signals: List[AggregatedSignal], kline_data: pd.DataFrame) -> List[Dict]:
    """Calculate trade records based on aggregated signals"""
    trades = []
    position = None  # None, or {'entry_date': date, 'entry_price': price, 'signal': 1/-1}
    
    # Create a mapping from date to price
    price_map = dict(zip(kline_data['date'], kline_data['close']))
    
    for signal_record in signals:
        date = signal_record.date
        signal = signal_record.final_signal
        
        if date not in price_map:
            continue
            
        price = price_map[date]
        
        if signal == 1 and position is None:  # Buy signal, no position
            position = {
                'entry_date': date,
                'entry_price': price,
                'signal': 1
            }
        elif signal == -1 and position is not None and position['signal'] == 1:  # Sell signal, have long position
            # Close position
            profit = price - position['entry_price']
            profit_pct = (profit / position['entry_price']) * 100
            
            trades.append({
                'entry_date': position['entry_date'],
                'entry_price': position['entry_price'],
                'exit_date': date,
                'exit_price': price,
                'profit': profit,
                'profit_pct': profit_pct,
                'type': 'long'
            })
            position = None
    
    return trades


@router.post("/analyze", response_model=AggregationResponse)
async def analyze_aggregation(
    request: AggregationRequest,
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Analyze stock using multiple strategies with weighted voting aggregation
    """
    strategy_service = StrategyService()
    data_service = DataService()
    
    # Validate weights
    total_weight = sum(s.weight for s in request.strategies)
    if total_weight == 0:
        raise HTTPException(status_code=400, detail="Total strategy weight cannot be zero")
    
    # Validate thresholds
    if request.settings.buy_threshold > total_weight:
        raise HTTPException(
            status_code=400,
            detail=f"Buy threshold ({request.settings.buy_threshold}) exceeds total weight ({total_weight})"
        )
    if request.settings.sell_threshold > total_weight:
        raise HTTPException(
            status_code=400,
            detail=f"Sell threshold ({request.settings.sell_threshold}) exceeds total weight ({total_weight})"
        )
    
    # Get stock data
    try:
        kline_data = data_service.get_kline_data(
            stock_code=request.stock_code,
            start_date=request.start_date,
            end_date=request.end_date
        )
        if kline_data.empty:
            raise HTTPException(status_code=404, detail=f"No data found for stock {request.stock_code}")
            
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Failed to get stock data: {str(e)}")
    
    # Run each strategy
    strategy_results = {}
    weights = {}
    
    for strategy_config in request.strategies:
        try:
            # Note: analyze is synchronous in StrategyService
            result = strategy_service.analyze(
                strategy_name=strategy_config.name,
                stock_code=request.stock_code,
                start_date=request.start_date,
                end_date=request.end_date,
                user_id=current_user_id,
                **strategy_config.params
            )
            
            # result['result'] is a list of dicts, convert to DataFrame
            result_df = pd.DataFrame(result['result'])
            strategy_results[strategy_config.name] = result_df
            weights[strategy_config.name] = strategy_config.weight
            
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Strategy '{strategy_config.name}' failed: {str(e)}"
            )

    
    # Aggregate signals
    aggregated_signals = aggregate_signals_by_date(
        strategy_results,
        weights,
        request.settings
    )
    
    # Ensure kline dates are strings for matching
    if not kline_data.empty and 'date' in kline_data.columns:
        kline_data['date'] = kline_data['date'].astype(str)

    # Calculate trade records
    trade_records = calculate_trade_records(aggregated_signals, kline_data)
    
    # Calculate statistics
    # Calculate statistics
    statistics = {
        'total_trades': 0,
        'winning_trades': 0,
        'losing_trades': 0,
        'win_rate': 0.0,
        'total_return': 0.0,
        'annualized_return': 0.0,
        'average_return': 0.0,
        'max_drawdown': 0.0,
        'sharpe_ratio': 0.0,
        'sortino_ratio': 0.0,
        'pl_ratio': 0.0,
        'benchmark_return': 0.0,  # Placeholder
        'benchmark_drawdown': 0.0 # Placeholder
    }

    try:
        if trade_records:
            total_trades = len(trade_records)
            winning_trades = sum(1 for t in trade_records if t['profit'] > 0)
            losing_trades = total_trades - winning_trades
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            total_profit_pct = sum(t['profit_pct'] for t in trade_records)
            avg_return = total_profit_pct / total_trades if total_trades > 0 else 0

            # Calculate P/L Ratio
            avg_win = sum(t['profit_pct'] for t in trade_records if t['profit'] > 0) / winning_trades if winning_trades > 0 else 0
            avg_loss = abs(sum(t['profit_pct'] for t in trade_records if t['profit'] <= 0)) / losing_trades if losing_trades > 0 else 0
            pl_ratio = avg_win / avg_loss if avg_loss > 0 else (999.0 if avg_win > 0 else 0.0)
            
            # Calculate Max Drawdown based on trade sequence (approximation)
            current_equity = 1.0
            max_equity = 1.0
            max_dd = 0.0
            
            for trade in trade_records:
                current_equity *= (1 + trade['profit_pct'] / 100)
                if current_equity > max_equity:
                    max_equity = current_equity
                
                dd = (max_equity - current_equity) / max_equity
                if dd > max_dd:
                    max_dd = dd

            statistics['total_trades'] = total_trades
            statistics['winning_trades'] = winning_trades
            statistics['losing_trades'] = losing_trades
            statistics['win_rate'] = round(win_rate, 2)
            statistics['total_return'] = round(total_profit_pct, 2) # Simple Sum
            statistics['average_return'] = round(avg_return, 2)
            statistics['pl_ratio'] = round(pl_ratio, 2)
            statistics['max_drawdown'] = round(max_dd * 100, 2) # Convert to %
            
            # Simple Sharple/Sortino estimation
            if len(trade_records) > 1:
                # Calculate returns sequence
                returns_seq = [t['profit_pct'] for t in trade_records]
                returns_np = np.array(returns_seq)
                mean_ret = np.mean(returns_np)
                std_ret = np.std(returns_np, ddof=1)
                
                statistics['sharpe_ratio'] = round(mean_ret / std_ret if std_ret > 0 else 0.0, 2)
                
                # Sortino
                negative_returns = returns_np[returns_np < 0]
                downside_std = np.std(negative_returns, ddof=1) if len(negative_returns) > 1 else (np.std(negative_returns) if len(negative_returns) > 0 else 1.0)
                statistics['sortino_ratio'] = round(mean_ret / downside_std if downside_std > 0 else 0.0, 2)
            
            # Calculate annualized return (approximate)
            if len(aggregated_signals) > 0:
                # Ensure dates are datetime objects for subtraction
                last_date = pd.to_datetime(aggregated_signals[-1].date)
                first_date = pd.to_datetime(aggregated_signals[0].date)
                days = (last_date - first_date).days
                if days > 0:
                    statistics['annualized_return'] = round((total_profit_pct / days) * 365, 2)
    except Exception as e:
        print(f"Error calculating statistics: {e}")
        # Keep default 0 values in statistics

    # Calculate Benchmark (Buy & Hold) Stats
    try:
        if not kline_data.empty and 'close' in kline_data.columns:
            closes = kline_data['close'].values
            if len(closes) > 0:
                # Return
                first_close = float(closes[0])
                last_close = float(closes[-1])
                benchmark_return = ((last_close - first_close) / first_close * 100) if first_close != 0 else 0.0
                statistics['benchmark_return'] = round(benchmark_return, 2)
                
                # Drawdown
                # Use numpy for efficiency
                running_max = np.maximum.accumulate(closes)
                # Avoid division by zero
                drawdown = np.where(running_max > 0, (running_max - closes) / running_max, 0.0)
                max_dd_bench = np.max(drawdown) * 100
                statistics['benchmark_drawdown'] = round(max_dd_bench, 2)
    except Exception as e:
        print(f"Error calculating benchmark stats: {e}")


    
    return AggregationResponse(
        stock_code=request.stock_code,
        stock_name=None,  # TODO: Get from stock info
        start_date=request.start_date,
        end_date=request.end_date,
        aggregated_signals=aggregated_signals,
        trade_records=trade_records,
        statistics=statistics,
        total_weight=total_weight
    )
