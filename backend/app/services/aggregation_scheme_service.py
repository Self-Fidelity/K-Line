from typing import List, Dict, Any, Optional
from backend.app.models.aggregation_scheme import AggregationSchemeCreate
from src.data_storage.sqlite_storage import SQLiteStorage
from src.utils.logger import get_logger

logger = get_logger(__name__)

class AggregationSchemeService:
    """策略聚合方案服务"""
    
    def __init__(self):
        self.storage = SQLiteStorage()
        
    def create_scheme(self, scheme: AggregationSchemeCreate) -> Optional[int]:
        """创建聚合方案"""
        return self.storage.save_aggregation_scheme(
            name=scheme.name,
            strategies=scheme.strategies,
            buy_threshold=scheme.buy_threshold,
            sell_threshold=scheme.sell_threshold,
            required_strategies=scheme.required_strategies,
            description=scheme.description,
            stock_code=scheme.stock_code
        )
        
    def get_schemes(self, stock_code: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取聚合方案列表"""
        return self.storage.get_aggregation_schemes(stock_code)
        
    def delete_scheme(self, scheme_id: int) -> bool:
        """删除聚合方案"""
        return self.storage.delete_aggregation_scheme(scheme_id)
