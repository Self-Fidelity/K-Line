"""图表服务：封装KLineChart，支持Bokeh Server"""

import uuid
from typing import Optional, Dict, Any
from pathlib import Path
import sys
import pandas as pd

# 添加src目录到路径
backend_dir = Path(__file__).parent.parent.parent
src_dir = backend_dir.parent / "src"
sys.path.insert(0, str(src_dir))

from src.visualization.kline import KLineChart
from backend.app.utils.bokeh_server import bokeh_server_manager
from bokeh.document import Document
from bokeh.io import curdoc

# 启动Bokeh Server（如果尚未启动）
try:
    bokeh_server_manager.start_server()
except Exception:
    pass  # 如果已经启动，忽略错误


class ChartService:
    """图表服务类"""
    
    def __init__(self):
        """初始化图表服务"""
        self.chart = KLineChart()
        self.server_manager = bokeh_server_manager
    
    def generate_chart(
        self,
        data: pd.DataFrame,
        stock_code: str,
        stock_name: Optional[str] = None,
        strategy_result: Optional[pd.DataFrame] = None,
        statistics: Optional[Dict[str, Any]] = None,
        chart_type: str = "kline",  # 'kline' or 'kline_with_ma'
        ma_periods: Optional[list] = None,
    ) -> str:
        """
        生成图表（返回chart_id）
        
        Args:
            data: K线数据
            stock_code: 股票代码
            stock_name: 股票名称
            strategy_result: 策略结果
            statistics: 统计信息
            chart_type: 图表类型
            ma_periods: 均线周期列表（如果chart_type为'kline_with_ma'）
        
        Returns:
            图表ID
        """
        chart_id = str(uuid.uuid4())
        
        # 创建Bokeh文档
        doc = self.server_manager.create_chart_document(chart_id)
        
        # 生成图表（使用Bokeh Server模式）
        # 注意：这里我们需要修改KLineChart以支持Bokeh Server
        # 目前先返回chart_id，实际的图表生成将在chart_api中处理
        return chart_id
    
    def generate_chart_html(
        self,
        data: pd.DataFrame,
        stock_code: str,
        stock_name: Optional[str] = None,
        strategy_result: Optional[pd.DataFrame] = None,
        statistics: Optional[Dict[str, Any]] = None,
        chart_type: str = "kline",
        ma_periods: Optional[list] = None,
        save_path: Optional[Path] = None,
    ) -> str:
        """
        生成图表HTML文件（返回文件路径）
        
        Args:
            data: K线数据
            stock_code: 股票代码
            stock_name: 股票名称
            strategy_result: 策略结果
            statistics: 统计信息
            chart_type: 图表类型
            ma_periods: 均线周期列表
            save_path: 保存路径
        
        Returns:
            HTML文件路径
        """
        # 导入settings
        from backend.app.config import settings as backend_settings
        from src.config import settings
        
        if save_path is None:
            save_path = settings.IMAGES_DIR / f"{stock_code}_chart_{uuid.uuid4().hex[:8]}.html"
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 使用现有的KLineChart生成HTML
        if chart_type == "kline_with_ma" and ma_periods:
            file_path = self.chart.plot_with_ma(
                data=data,
                stock_code=stock_code,
                stock_name=stock_name,
                save_path=save_path,
                strategy_result=strategy_result,
                statistics=statistics,
                ma_periods=ma_periods,
            )
        else:
            file_path = self.chart.plot(
                data=data,
                stock_code=stock_code,
                stock_name=stock_name,
                save_path=save_path,
                strategy_result=strategy_result,
                statistics=statistics,
            )
        
        return str(file_path)
    
    def get_chart_url(self, chart_id: str) -> str:
        """
        获取图表URL
        
        Args:
            chart_id: 图表ID
        
        Returns:
            图表URL
        """
        return self.server_manager.get_chart_url(chart_id)
    
    def delete_chart(self, chart_id: str) -> bool:
        """
        删除图表
        
        Args:
            chart_id: 图表ID
        
        Returns:
            是否删除成功
        """
        return self.server_manager.delete_chart(chart_id)
