"""参数集服务层"""

from typing import Optional, List, Dict, Any
from backend.app.models.param_sets import ParamSetCreate
from backend.app.dependencies import get_storage
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ParamSetsService:
    """参数集服务类"""

    def __init__(self):
        self.storage = get_storage()
    
    def create_param_set(self, param_set: ParamSetCreate) -> Optional[int]:
        """创建参数集"""
        return self.storage.save_param_set(
            stock_code=param_set.stock_code,
            strategy_name=param_set.strategy_name,
            name=param_set.name,
            params=param_set.params,
            description=param_set.description,
            param_ranges=param_set.param_ranges,
            target_metric=param_set.target_metric,
            best_score=param_set.best_score,
            optimization_method=param_set.optimization_method,
            num_particles=param_set.num_particles,
            max_iter=param_set.max_iter,
            date_range=param_set.date_range,
            is_default=param_set.is_default
        )
    
    def get_param_sets(self, stock_code: str, strategy_name: str) -> List[Dict[str, Any]]:
        """获取参数集列表"""
        return self.storage.get_param_sets(stock_code, strategy_name)
    
    def get_param_set_by_id(self, param_set_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取参数集"""
        return self.storage.get_param_set_by_id(param_set_id)
    
    def delete_param_set(self, param_set_id: int) -> bool:
        """删除参数集"""
        return self.storage.delete_param_set(param_set_id)
    
    def set_default_param_set(
        self,
        param_set_id: int,
        stock_code: str,
        strategy_name: str
    ) -> bool:
        """设置默认参数集"""
        return self.storage.set_default_param_set(param_set_id, stock_code, strategy_name)
    
    def get_default_param_set(
        self,
        stock_code: str,
        strategy_name: str
    ) -> Optional[Dict[str, Any]]:
        """获取默认参数集"""
        return self.storage.get_default_param_set(stock_code, strategy_name)
