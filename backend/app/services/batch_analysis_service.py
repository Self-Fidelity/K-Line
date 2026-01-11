"""批量分析服务"""

from typing import List, Dict, Any, Optional
import logging
import pandas as pd

from backend.app.services.strategy_service import StrategyService
from backend.app.services.data_service import DataService

logger = logging.getLogger(__name__)


class BatchAnalysisService:
    """批量分析服务类"""
    
    def __init__(self):
        """初始化批量分析服务"""
        self.strategy_service = StrategyService()
        self.data_service = DataService()
    
    def check_buy_signals(
        self,
        stock_codes: List[str],
        strategy_names: List[str],
        strategy_params: Dict[str, Dict[str, Any]] = {},
    ) -> Dict[str, Any]:
        """
        批量检测股票买点
        
        Args:
            stock_codes: 股票代码列表
            strategy_names: 策略名称列表
            strategy_params: 策略参数（key为策略名称，value为该策略的参数）
        
        Returns:
            批量买点检测结果
        """
        results = []
        recommended_stocks = []
        
        # 批量检测每只股票
        for stock_code in stock_codes:
            try:
                # 获取股票名称
                stock_name = self._get_stock_name(stock_code)
                
                # 获取最新数据（最近30天，用于判断买点）
                data = self.data_service.get_kline_data(stock_code, None, None)
                
                if data.empty:
                    raise ValueError(f"股票 {stock_code} 没有数据")
                
                # 检测各策略的买入信号
                strategy_signals = []
                has_buy_signal = False
                
                for strategy_name in strategy_names:
                    try:
                        # 获取策略参数
                        params = strategy_params.get(strategy_name, {})
                        
                        # 执行策略分析
                        analysis_result = self.strategy_service.analyze(
                            strategy_name=strategy_name,
                            stock_code=stock_code,
                            start_date=None,
                            end_date=None,
                            **params,
                        )
                        
                        # 检查是否有买入信号（信号值为1表示买入）
                        strategy_result = analysis_result.get("result", [])
                        if strategy_result and len(strategy_result) > 0:
                            # 获取最新的信号（按日期排序，取最后一条）
                            latest_result = max(
                                strategy_result,
                                key=lambda x: x.get("date", ""),
                                default=None
                            )
                            
                            if latest_result:
                                signal = latest_result.get("signal", 0)
                                signal_type = latest_result.get("signal_type", "持有")
                                signal_date = latest_result.get("date", None)
                                
                                # 将日期转换为字符串格式
                                signal_date_str = None
                                if signal_date is not None:
                                    if hasattr(signal_date, 'strftime'):
                                        # 如果是日期时间对象，转换为字符串
                                        signal_date_str = signal_date.strftime('%Y-%m-%d')
                                    else:
                                        signal_date_str = str(signal_date)
                                
                                has_signal = signal == 1  # 买入信号（signal == 1 表示买入）
                                
                                if has_signal:
                                    has_buy_signal = True
                                
                                strategy_signals.append({
                                    "strategy_name": strategy_name,
                                    "has_buy_signal": has_signal,
                                    "latest_signal_date": signal_date_str,
                                    "signal_type": signal_type,
                                    "error": None,
                                })
                            else:
                                strategy_signals.append({
                                    "strategy_name": strategy_name,
                                    "has_buy_signal": False,
                                    "latest_signal_date": None,
                                    "signal_type": None,
                                    "error": None,
                                })
                        else:
                            strategy_signals.append({
                                "strategy_name": strategy_name,
                                "has_buy_signal": False,
                                "latest_signal_date": None,
                                "signal_type": None,
                                "error": None,
                            })
                            
                    except Exception as e:
                        logger.warning(f"策略 {strategy_name} 分析股票 {stock_code} 失败: {e}", exc_info=True)
                        strategy_signals.append({
                            "strategy_name": strategy_name,
                            "has_buy_signal": False,
                            "latest_signal_date": None,
                            "signal_type": None,
                            "error": str(e),
                        })
                
                result = {
                    "stock_code": stock_code,
                    "stock_name": stock_name,
                    "success": True,
                    "error": None,
                    "has_buy_signal": has_buy_signal,
                    "strategy_signals": strategy_signals,
                    "recommended": has_buy_signal,
                }
                results.append(result)
                
                if has_buy_signal:
                    recommended_stocks.append(result)
                    
            except Exception as e:
                logger.error(f"分析股票 {stock_code} 失败: {e}", exc_info=True)
                result = {
                    "stock_code": stock_code,
                    "stock_name": None,
                    "success": False,
                    "error": str(e),
                    "has_buy_signal": False,
                    "strategy_signals": [],
                    "recommended": False,
                }
                results.append(result)
        
        # 统计信息
        success_count = sum(1 for r in results if r["success"])
        failed_count = len(results) - success_count
        recommended_count = len(recommended_stocks)
        
        return {
            "total_count": len(stock_codes),
            "success_count": success_count,
            "failed_count": failed_count,
            "recommended_count": recommended_count,
            "results": results,
            "recommended_stocks": recommended_stocks,
        }
    
    def _get_stock_name(self, stock_code: str) -> Optional[str]:
        """获取股票名称"""
        try:
            df = self.data_service.get_stock_list(market="all", refresh=False)
            stock_info = df[df["code"] == stock_code]
            if not stock_info.empty:
                return stock_info.iloc[0]["name"]
            return None
        except Exception as e:
            logger.warning(f"获取股票名称失败 {stock_code}: {e}")
            return None
