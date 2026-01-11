"""策略分析结果导出模块"""

from pathlib import Path
from typing import Optional
import pandas as pd

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class StrategyResultExporter:
    """策略分析结果导出器"""
    
    def __init__(self, base_dir: Optional[Path] = None):
        """
        初始化策略结果导出器
        
        Args:
            base_dir: 基础目录，如果为None则使用配置中的目录
        """
        self.base_dir = base_dir or settings.STRATEGY_RESULTS_DIR
    
    def get_strategy_dir(self, strategy_name: str) -> Path:
        """
        获取策略结果目录
        
        Args:
            strategy_name: 策略名称
        
        Returns:
            策略结果目录路径
        """
        # 清理策略名称，移除不合法字符
        clean_name = strategy_name.replace("/", "_").replace("\\", "_").replace(":", "_")
        strategy_dir = self.base_dir / clean_name
        strategy_dir.mkdir(parents=True, exist_ok=True)
        return strategy_dir
    
    def export_result(
        self,
        result: pd.DataFrame,
        strategy_name: str,
        stock_code: str,
        filename: Optional[str] = None,
    ) -> str:
        """
        导出策略分析结果到CSV
        
        Args:
            result: 策略分析结果 DataFrame
            strategy_name: 策略名称
            stock_code: 股票代码
            filename: 文件名（可选），如果为空则自动生成
        
        Returns:
            导出文件的完整路径
        """
        # 获取策略目录
        strategy_dir = self.get_strategy_dir(strategy_name)
        
        # 生成文件名
        if not filename:
            filename = f"{stock_code}_result.csv"
        
        file_path = strategy_dir / filename
        
        # 导出CSV
        result.to_csv(file_path, index=False, encoding="utf-8-sig")
        logger.info(f"策略结果已导出到: {file_path}")
        
        return str(file_path)
