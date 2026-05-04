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
    ) -> bool:
        """
        保存日K线数据
        
        Args:
            data: 日K线数据 DataFrame
            stock_code: 股票代码
        
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
    ) -> pd.DataFrame:
        """
        获取日K线数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期（格式：'20240101'）
            end_date: 结束日期（格式：'20240101'）
        
        Returns:
            日K线数据 DataFrame
        """
        pass
    
    @abstractmethod
    def get_latest_date(self, stock_code: str) -> Optional[str]:
        """
        获取指定股票的最新数据日期
        
        Args:
            stock_code: 股票代码
        
        Returns:
            最新日期字符串（格式：'20240101'），如果没有数据返回 None
        """
        pass
    
    @abstractmethod
    def check_data_exists(
        self,
        stock_code: str,
        trade_date: str,
    ) -> bool:
        """
        检查指定日期的数据是否存在
        
        Args:
            stock_code: 股票代码
            trade_date: 交易日期（格式：'20240101'）
        
        Returns:
            如果数据存在返回 True，否则返回 False
        """
        pass
    
    @abstractmethod
    def get_all_stocks(self) -> list[str]:
        """
        获取数据库中所有股票代码列表
        
        Returns:
            股票代码列表
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
