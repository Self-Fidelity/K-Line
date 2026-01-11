"""Bokeh Server管理器"""

import uuid
from typing import Dict, Optional
from pathlib import Path
import sys

# 添加src目录到路径
backend_dir = Path(__file__).parent.parent.parent
src_dir = backend_dir.parent / "src"
sys.path.insert(0, str(src_dir))

from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.application.handlers.function import FunctionHandler
from bokeh.document import Document

from backend.app.config import settings


class BokehServerManager:
    """Bokeh Server管理器"""
    
    def __init__(self):
        """初始化Bokeh Server管理器"""
        self.server: Optional[Server] = None
        self.charts: Dict[str, Document] = {}  # chart_id -> Document映射
        self.server_url = f"http://{settings.BOKEH_SERVER_HOST}:{settings.BOKEH_SERVER_PORT}"
    
    def start_server(self):
        """启动Bokeh Server"""
        if self.server is not None:
            return
        
        # 创建Bokeh应用
        apps = {"/": self._make_app()}
        
        # 启动服务器
        self.server = Server(apps, port=settings.BOKEH_SERVER_PORT, allow_websocket_origin=["*"])
        self.server.start()
    
    def stop_server(self):
        """停止Bokeh Server"""
        if self.server is not None:
            self.server.stop()
            self.server = None
    
    def _make_app(self):
        """创建Bokeh应用"""
        def modify_doc(doc: Document):
            # 从文档的session context获取chart_id
            # 如果没有，创建一个新的
            if hasattr(doc, 'chart_id'):
                chart_id = doc.chart_id
            else:
                chart_id = str(uuid.uuid4())
                doc.chart_id = chart_id
            
            # 存储文档
            self.charts[chart_id] = doc
        
        handler = FunctionHandler(modify_doc)
        return Application(handler)
    
    def get_chart_url(self, chart_id: str) -> str:
        """
        获取图表URL
        
        Args:
            chart_id: 图表ID
        
        Returns:
            图表URL
        """
        if chart_id not in self.charts:
            raise ValueError(f"图表 {chart_id} 不存在")
        
        return f"{self.server_url}/?chart_id={chart_id}"
    
    def create_chart_document(self, chart_id: str) -> Document:
        """
        创建图表文档
        
        Args:
            chart_id: 图表ID
        
        Returns:
            Bokeh文档对象
        """
        doc = Document()
        doc.chart_id = chart_id
        self.charts[chart_id] = doc
        return doc
    
    def get_chart_document(self, chart_id: str) -> Optional[Document]:
        """
        获取图表文档
        
        Args:
            chart_id: 图表ID
        
        Returns:
            Bokeh文档对象，如果不存在返回None
        """
        return self.charts.get(chart_id)
    
    def delete_chart(self, chart_id: str) -> bool:
        """
        删除图表
        
        Args:
            chart_id: 图表ID
        
        Returns:
            是否删除成功
        """
        if chart_id in self.charts:
            del self.charts[chart_id]
            return True
        return False


# 全局Bokeh Server管理器实例
bokeh_server_manager = BokehServerManager()
