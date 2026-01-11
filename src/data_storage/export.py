"""数据导出模块"""

from pathlib import Path
from typing import Optional, List
import pandas as pd

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataExporter:
    """数据导出器"""
    
    def __init__(self, export_dir: Optional[Path] = None):
        """
        初始化数据导出器
        
        Args:
            export_dir: 导出目录，如果为 None 则使用配置中的目录
        """
        self.export_dir = export_dir or settings.EXPORT_DIR
        self.export_dir.mkdir(parents=True, exist_ok=True)
    
    def export_to_csv(
        self,
        data: pd.DataFrame,
        filename: str,
        index: bool = False,
    ) -> str:
        """
        导出数据到 CSV 文件
        
        Args:
            data: 要导出的 DataFrame
            filename: 文件名（不含路径）
            index: 是否包含索引
        
        Returns:
            导出文件的完整路径
        """
        file_path = self.export_dir / filename
        
        try:
            data.to_csv(file_path, index=index, encoding="utf-8-sig")
            logger.info(f"数据已导出到: {file_path}")
            return str(file_path)
        except Exception as e:
            logger.error(f"导出数据失败: {e}", exc_info=True)
            raise
    
    def export_stock_data(
        self,
        data: pd.DataFrame,
        stock_code: str,
        suffix: Optional[str] = None,
    ) -> str:
        """
        导出股票数据到 CSV
        
        Args:
            data: 股票数据 DataFrame
            stock_code: 股票代码
            suffix: 文件名后缀（可选）
        
        Returns:
            导出文件的完整路径
        """
        filename = f"{stock_code}_data.csv"
        if suffix:
            filename = f"{stock_code}_{suffix}.csv"
        
        return self.export_to_csv(data, filename)
    
    def export_strategy_result(
        self,
        result: pd.DataFrame,
        strategy_name: str,
        stock_code: Optional[str] = None,
    ) -> str:
        """
        导出策略分析结果到 CSV
        
        Args:
            result: 策略分析结果 DataFrame
            strategy_name: 策略名称
            stock_code: 股票代码（可选）
        
        Returns:
            导出文件的完整路径
        """
        if stock_code:
            filename = f"{stock_code}_{strategy_name}_result.csv"
        else:
            filename = f"{strategy_name}_result.csv"
        
        return self.export_to_csv(result, filename)
    
    def export_multiple_strategies(
        self,
        results: dict[str, pd.DataFrame],
        stock_code: Optional[str] = None,
    ) -> List[str]:
        """
        导出多个策略的分析结果
        
        Args:
            results: 字典，key 为策略名称，value 为策略分析结果 DataFrame
            stock_code: 股票代码（可选）
        
        Returns:
            导出文件路径列表
        """
        exported_files = []
        
        for strategy_name, result in results.items():
            try:
                file_path = self.export_strategy_result(result, strategy_name, stock_code)
                exported_files.append(file_path)
            except Exception as e:
                logger.error(f"导出策略 {strategy_name} 结果失败: {e}", exc_info=True)
                continue
        
        return exported_files
    
    def export_with_date_range(
        self,
        data: pd.DataFrame,
        filename: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> str:
        """
        按日期范围导出数据
        
        Args:
            data: 数据 DataFrame，必须包含 date 列
            filename: 文件名
            start_date: 开始日期（格式：'20240101'）
            end_date: 结束日期（格式：'20240101'）
        
        Returns:
            导出文件的完整路径
        """
        if "date" not in data.columns:
            raise ValueError("数据必须包含 'date' 列")
        
        # 过滤日期范围
        filtered_data = data.copy()
        filtered_data["date_str"] = pd.to_datetime(filtered_data["date"]).dt.strftime("%Y%m%d")
        
        if start_date:
            filtered_data = filtered_data[filtered_data["date_str"] >= start_date]
        
        if end_date:
            filtered_data = filtered_data[filtered_data["date_str"] <= end_date]
        
        filtered_data = filtered_data.drop(columns=["date_str"])
        
        return self.export_to_csv(filtered_data, filename)
