"""数据存储接口定义"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import pandas as pd


class DataStorage(ABC):
    """数据存储抽象基类"""
    
    @abstractmethod
    def save_daily_data(
        self,
        data: pd.DataFrame,
        stock_code: str,
        data_source: str = "akshare",
        adjust: str = "qfq",
    ) -> bool:
        """
        保存日K线数据
        
        Args:
            data: 日K线数据 DataFrame
            stock_code: 股票代码
            data_source: 数据来源，'akshare' 或 'tushare'
            adjust: 复权方式，'qfq'（前复权）、'hfq'（后复权）、'none'（不复权）
        
        Returns:
            是否保存成功
        """
        pass
    
    @abstractmethod
    def get_daily_data(
        self,
        stock_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        data_source: Optional[str] = None,
        adjust: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        获取日K线数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期（格式：'20240101'）
            end_date: 结束日期（格式：'20240101'）
            data_source: 数据来源过滤，None 则返回所有来源
            adjust: 复权方式过滤，None 则返回所有复权方式
        
        Returns:
            日K线数据 DataFrame
        """
        pass
    
    @abstractmethod
    def get_latest_date(self, stock_code: str, data_source: Optional[str] = None, adjust: Optional[str] = None) -> Optional[str]:
        """
        获取指定股票的最新数据日期
        
        Args:
            stock_code: 股票代码
            data_source: 数据来源过滤，None 则查询所有来源
            adjust: 复权方式过滤，None 则查询所有复权方式
        
        Returns:
            最新日期字符串（格式：'20240101'），如果没有数据返回 None
        """
        pass
    
    @abstractmethod
    def check_data_exists(
        self,
        stock_code: str,
        trade_date: str,
        data_source: Optional[str] = None,
        adjust: Optional[str] = None,
    ) -> bool:
        """
        检查指定日期的数据是否存在
        
        Args:
            stock_code: 股票代码
            trade_date: 交易日期（格式：'20240101'）
            data_source: 数据来源过滤，None 则查询所有来源
            adjust: 复权方式过滤，None 则查询所有复权方式
        
        Returns:
            如果数据存在返回 True，否则返回 False
        """
        pass
    
    @abstractmethod
    def get_all_stocks(self, data_source: Optional[str] = None, adjust: Optional[str] = None) -> list[str]:
        """
        获取数据库中所有股票代码列表
        
        Args:
            data_source: 数据来源过滤，None 则返回所有来源
            adjust: 复权方式过滤，None 则返回所有复权方式
        
        Returns:
            股票代码列表
        """
        pass
    
    @abstractmethod
    def clear_data_by_source(self, data_source: str) -> int:
        """
        清空指定数据来源的所有日K线数据
        
        Args:
            data_source: 数据来源，'akshare' 或 'tushare'
        
        Returns:
            删除的行数
        """
        pass

    # ───────────────────── 审计日志 ─────────────────────

    @abstractmethod
    def create_audit_log(
        self,
        username: str,
        action: str,
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> int:
        """创建审计日志"""
        pass

    @abstractmethod
    def list_audit_logs(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """列出审计日志"""
        pass

    # ───────────────────── 自选股 ─────────────────────

    @abstractmethod
    def add_to_watchlist(
        self, user_id: int, stock_code: str, stock_name: Optional[str] = None
    ) -> int:
        """添加到自选股"""
        pass

    @abstractmethod
    def remove_from_watchlist(self, user_id: int, stock_code: str) -> bool:
        """从自选股删除"""
        pass

    @abstractmethod
    def get_watchlist(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户自选股列表"""
        pass

    @abstractmethod
    def is_in_watchlist(self, user_id: int, stock_code: str) -> bool:
        """检查是否在自选股中"""
        pass

    # ───────────────────── 股票列表 ─────────────────────

    @abstractmethod
    def init_stock_list_table(self) -> None:
        """初始化股票列表表"""
        pass

    @abstractmethod
    def load_stock_list(self) -> Optional[pd.DataFrame]:
        """从数据库加载股票列表"""
        pass

    @abstractmethod
    def save_stock_list(self, df: pd.DataFrame) -> None:
        """保存股票列表到数据库"""
        pass

    # ───────────────────── 用户管理 ─────────────────────

    @abstractmethod
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """根据用户名获取用户"""
        pass

    @abstractmethod
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取用户"""
        pass

    @abstractmethod
    def create_user(
        self,
        username: str,
        password_hash: str,
        email: Optional[str] = None,
        role: str = "user",
        max_watchlist_count: Optional[int] = None,
        is_active: bool = True,
    ) -> int:
        """创建用户，返回ID"""
        pass

    @abstractmethod
    def check_email_exists(self, email: str) -> bool:
        """检查邮箱是否已存在"""
        pass

    @abstractmethod
    def list_users(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """列出所有用户"""
        pass

    @abstractmethod
    def update_user(self, user_id: int, **fields: Any) -> bool:
        """更新用户字段"""
        pass

    @abstractmethod
    def delete_user(self, user_id: int) -> bool:
        """删除用户"""
        pass

    # ───────────────────── 数据更新配置 ─────────────────────

    @abstractmethod
    def init_update_config_table(self) -> None:
        """初始化数据更新配置表"""
        pass

    @abstractmethod
    def get_update_config(self, key: str, default: str) -> str:
        """获取更新配置值"""
        pass

    @abstractmethod
    def set_update_config(self, key: str, value: str) -> None:
        """设置更新配置值"""
        pass

    # ───────────────────── 策略参数 ─────────────────────

    @abstractmethod
    def save_strategy_params(self, stock_code: str, strategy_name: str, params: str) -> bool:
        """保存策略参数"""
        pass

    @abstractmethod
    def get_strategy_params(self, stock_code: str, strategy_name: str) -> Optional[str]:
        """获取策略参数"""
        pass

    # ───────────────────── 参数集管理 ─────────────────────

    @abstractmethod
    def save_param_set(
        self,
        stock_code: str,
        strategy_name: str,
        name: str,
        params: Dict[str, Any],
        description: str = "",
        param_ranges: Optional[Dict[str, List[float]]] = None,
        target_metric: Optional[str] = None,
        best_score: Optional[float] = None,
        optimization_method: Optional[str] = None,
        num_particles: Optional[int] = None,
        max_iter: Optional[int] = None,
        date_range: Optional[str] = None,
        is_default: bool = False,
    ) -> Optional[int]:
        """保存参数集"""
        pass

    @abstractmethod
    def get_param_sets(self, stock_code: str, strategy_name: str) -> List[Dict[str, Any]]:
        """获取参数集列表"""
        pass

    @abstractmethod
    def get_param_set_by_id(self, param_set_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取参数集"""
        pass

    @abstractmethod
    def delete_param_set(self, param_set_id: int) -> bool:
        """删除参数集"""
        pass

    @abstractmethod
    def set_default_param_set(self, param_set_id: int, stock_code: str, strategy_name: str) -> bool:
        """设置默认参数集"""
        pass

    @abstractmethod
    def get_default_param_set(self, stock_code: str, strategy_name: str) -> Optional[Dict[str, Any]]:
        """获取默认参数集"""
        pass

    # ───────────────────── 策略聚合方案 ─────────────────────

    @abstractmethod
    def save_aggregation_scheme(
        self,
        name: str,
        strategies: List[Dict[str, Any]],
        buy_threshold: float,
        sell_threshold: float,
        required_strategies: List[str],
        description: str = "",
        stock_code: Optional[str] = None,
    ) -> Optional[int]:
        """保存策略聚合方案"""
        pass

    @abstractmethod
    def get_aggregation_schemes(self, stock_code: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取策略聚合方案列表"""
        pass

    @abstractmethod
    def get_aggregation_scheme_by_id(self, scheme_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取聚合方案"""
        pass

    @abstractmethod
    def delete_aggregation_scheme(self, scheme_id: int) -> bool:
        """删除策略聚合方案"""
        pass

    # ───────────────────── 自定义策略 ─────────────────────

    @abstractmethod
    def create_custom_strategy(
        self,
        user_id: int,
        name: str,
        code: str,
        description: str = "",
        detailed_description: str = "",
        parameter_descriptions: Optional[Dict[str, str]] = None,
        file_path: Optional[str] = None,
        is_public: bool = False,
    ) -> int:
        """创建自定义策略，返回策略ID"""
        pass

    @abstractmethod
    def get_custom_strategy(self, strategy_id: int) -> Optional[Dict[str, Any]]:
        """获取单个自定义策略"""
        pass

    @abstractmethod
    def get_custom_strategy_by_user(self, strategy_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """获取用户拥有的策略"""
        pass

    @abstractmethod
    def update_custom_strategy(self, strategy_id: int, **fields: Any) -> bool:
        """更新自定义策略字段"""
        pass

    @abstractmethod
    def delete_custom_strategy(self, strategy_id: int) -> bool:
        """删除自定义策略"""
        pass

    @abstractmethod
    def list_custom_strategies(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出所有自定义策略"""
        pass

    # ───────────────────── 工具方法 ─────────────────────

    @abstractmethod
    def get_all_latest_dates(self, data_source: Optional[str] = None) -> Dict[str, Optional[str]]:
        """批量获取所有股票的最新数据日期"""
        pass

    @abstractmethod
    def close(self) -> None:
        """关闭存储连接"""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """健康检查"""
        pass
