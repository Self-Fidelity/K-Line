"""策略服务：封装StrategyManager"""

from typing import Optional, Dict, List, Any
import pandas as pd
from pathlib import Path
import sys

# 添加src目录到路径
backend_dir = Path(__file__).parent.parent.parent
src_dir = backend_dir.parent / "src"
sys.path.insert(0, str(src_dir))

from src.strategy.manager import StrategyManager
from src.strategy.statistics import StrategyStatistics


class StrategyService:
    """策略服务类"""
    
    def __init__(self):
        """初始化策略服务"""
        self.strategy_manager = StrategyManager()
        self.statistics = StrategyStatistics()
    
    def list_strategies(self, user_id: Optional[int] = None) -> List[Dict]:
        """
        获取所有可用策略列表
        
        Args:
            user_id: 用户ID（用于过滤用户自定义策略）
        
        Returns:
            策略列表
        """
        strategy_names = self.strategy_manager.list_strategies()
        result = []
        for strategy_name in strategy_names:
            strategy = self.strategy_manager.get_strategy(strategy_name)
            if strategy:
                result.append({
                    "name": strategy.name,
                    "description": strategy.description,
                    "is_system": True,  # 系统策略
                })
        # TODO: 添加用户自定义策略
        return result
    
    def get_strategy_info(self, strategy_name: str) -> Dict:
        """
        获取策略详细信息
        
        Args:
            strategy_name: 策略名称
        
        Returns:
            策略信息
        """
        strategy = self.strategy_manager.get_strategy(strategy_name)
        if not strategy:
            return None
        strategy_info = strategy.get_strategy_info()
        return {
            "name": strategy_info["name"],
            "description": strategy_info["description"],
            "detailed_description": strategy_info.get("detailed_description", ""),
            "parameter_descriptions": strategy_info.get("parameter_descriptions", {}),
            "is_system": True,
        }
    
    def analyze(
        self,
        strategy_name: str,
        stock_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **strategy_kwargs: Any,
    ) -> Dict:
        """
        执行策略分析
        
        Args:
            strategy_name: 策略名称
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            **strategy_kwargs: 策略参数
        
        Returns:
            分析结果
        """
        # 获取数据
        from backend.app.services.data_service import DataService
        data_service = DataService()
        data = data_service.get_kline_data(stock_code, start_date, end_date)
        
        if data.empty:
            raise ValueError(f"股票 {stock_code} 没有数据")
        
        # 执行策略
        result = self.strategy_manager.run_strategy(
            strategy_name=strategy_name,
            data=data,
            **strategy_kwargs,
        )
        
        if result.empty:
            raise ValueError("策略分析结果为空")
        
        # 计算统计信息
        stats = self.statistics.calculate_statistics(
            data=data,
            strategy_result=result,
        )
        
        return {
            "strategy_name": strategy_name,
            "stock_code": stock_code,
            "start_date": start_date,
            "end_date": end_date,
            "result": result.to_dict("records"),
            "statistics": stats,
        }
    
    def compare(
        self,
        strategy_names: List[str],
        stock_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        strategy_params: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Dict:
        """
        策略比较分析
        
        Args:
            strategy_names: 策略名称列表
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            strategy_params: 各策略的参数（key为策略名称，value为该策略的参数字典）
        
        Returns:
            比较结果
        """
        if not strategy_names:
            raise ValueError("至少选择一个策略进行比较")
        
        if len(strategy_names) < 2:
            raise ValueError("策略比较至少需要两个策略")
        
        strategy_params = strategy_params or {}
        results = []
        
        for strategy_name in strategy_names:
            try:
                params = strategy_params.get(strategy_name, {})
                result = self.analyze(
                    strategy_name=strategy_name,
                    stock_code=stock_code,
                    start_date=start_date,
                    end_date=end_date,
                    **params,
                )
                results.append(result)
            except Exception as e:
                results.append({
                    "strategy_name": strategy_name,
                    "stock_code": stock_code,
                    "error": str(e),
                })
        
        return {
            "stock_code": stock_code,
            "start_date": start_date,
            "end_date": end_date,
            "results": results,
        }
