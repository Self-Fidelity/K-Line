"""日期工具模块

支持中国股市交易日历，节假日列表从配置文件动态加载。
"""

import calendar
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Set

import pandas as pd


def _load_holidays_from_config() -> Set[str]:
    """从配置文件加载节假日列表

    查找路径（按优先级）：
    1. 环境变量 CHINA_HOLIDAYS_FILE 指定的路径
    2. data/china_holidays.json 项目级配置文件
    3. 内置默认节假日（2024-2026）

    JSON 格式示例:
    {
        "holidays": ["2024-01-01", "2024-02-10", ...],
        "description": "中国股市休市日历"
    }
    """
    # 检查环境变量
    import os
    env_path = os.getenv("CHINA_HOLIDAYS_FILE")
    if env_path and Path(env_path).exists():
        try:
            data = json.loads(Path(env_path).read_text())
            return set(data.get("holidays", []))
        except Exception:
            pass

    # 检查项目配置文件
    config_path = Path(__file__).parent.parent.parent / "data" / "china_holidays.json"
    if config_path.exists():
        try:
            data = json.loads(config_path.read_text())
            holidays = set(data.get("holidays", []))
            if holidays:
                return holidays
        except Exception:
            pass

    # 内置默认节假日（2024-2026，定期更新）
    return _get_builtin_holidays()


def _get_builtin_holidays() -> Set[str]:
    """内置节假日列表（2024-2026 中国A股休市日历）"""
    return {
        # 2024
        "2024-01-01", "2024-02-09", "2024-02-10", "2024-02-11",
        "2024-02-12", "2024-02-13", "2024-02-14", "2024-02-15",
        "2024-02-16", "2024-04-04", "2024-04-05", "2024-05-01",
        "2024-05-02", "2024-05-03", "2024-06-10", "2024-09-16",
        "2024-09-17", "2024-10-01", "2024-10-02", "2024-10-03",
        "2024-10-04", "2024-10-07",
        # 2025
        "2025-01-01", "2025-01-28", "2025-01-29", "2025-01-30",
        "2025-01-31", "2025-02-03", "2025-02-04", "2025-04-04",
        "2025-05-01", "2025-05-02", "2025-06-02", "2025-09-29",
        "2025-09-30", "2025-10-01", "2025-10-02", "2025-10-03",
        "2025-10-06", "2025-10-07",
        # 2026
        "2026-01-01", "2026-02-17", "2026-02-18", "2026-02-19",
        "2026-02-20", "2026-02-23", "2026-04-06", "2026-05-01",
        "2026-05-04", "2026-05-05", "2026-06-22", "2026-09-25",
        "2026-10-01", "2026-10-02", "2026-10-05", "2026-10-06",
        "2026-10-07",
    }


# 模块加载时初始化节假日集合
CHINA_HOLIDAYS: Set[str] = _load_holidays_from_config()


def format_date(date: datetime, fmt: str = "%Y%m%d") -> str:
    """
    格式化日期为字符串（统一格式）

    Args:
        date: 日期对象
        fmt: 日期格式，默认为 '%Y%m%d'

    Returns:
        格式化后的日期字符串
    """
    return date.strftime(fmt)


def parse_date(date_str: str, fmt: str = "%Y%m%d") -> datetime:
    """
    解析日期字符串
    
    Args:
        date_str: 日期字符串
        fmt: 日期格式，默认为 '%Y%m%d'
    
    Returns:
        日期对象
    """
    return datetime.strptime(date_str, fmt)


def is_weekend(date: datetime) -> bool:
    """
    判断是否为周末
    
    Args:
        date: 日期对象
    
    Returns:
        如果是周末返回 True，否则返回 False
    """
    return date.weekday() >= 5  # 5=Saturday, 6=Sunday


def is_holiday(date: datetime) -> bool:
    """
    判断是否为中国股市节假日
    
    Args:
        date: 日期对象
    
    Returns:
        如果是节假日返回 True，否则返回 False
    
    Note:
        这里使用的是硬编码的节假日列表，实际应用中建议从配置文件或API获取
    """
    date_str = format_date(date, "%Y-%m-%d")
    return date_str in CHINA_HOLIDAYS


def is_trading_day(date: Optional[datetime] = None) -> bool:
    """
    判断是否为交易日（非周末且非节假日）
    
    Args:
        date: 日期对象，如果为 None 则使用当前日期
    
    Returns:
        如果是交易日返回 True，否则返回 False
    """
    if date is None:
        date = datetime.now()
    
    # 排除周末
    if is_weekend(date):
        return False
    
    # 排除节假日
    if is_holiday(date):
        return False
    
    return True


def get_last_trading_day(date: Optional[datetime] = None) -> datetime:
    """
    获取上一个交易日
    
    Args:
        date: 基准日期，如果为 None 则使用当前日期
    
    Returns:
        上一个交易日
    """
    if date is None:
        date = datetime.now()
    
    # 向前查找交易日
    prev_date = date - timedelta(days=1)
    while not is_trading_day(prev_date):
        prev_date = prev_date - timedelta(days=1)
    
    return prev_date


def get_trading_days(start_date: str, end_date: str, fmt: str = "%Y%m%d") -> list[str]:
    """
    获取指定日期范围内的所有交易日
    
    Args:
        start_date: 开始日期（字符串）
        end_date: 结束日期（字符串）
        fmt: 日期格式，默认为 '%Y%m%d'
    
    Returns:
        交易日列表（字符串格式）
    """
    start = parse_date(start_date, fmt)
    end = parse_date(end_date, fmt)
    
    trading_days = []
    current = start
    while current <= end:
        if is_trading_day(current):
            trading_days.append(format_date(current, fmt))
        current += timedelta(days=1)
    
    return trading_days


def add_trading_days(date: datetime, days: int) -> datetime:
    """
    在指定日期基础上增加/减少指定数量的交易日
    
    Args:
        date: 基准日期
        days: 交易日数量（可以为负数）
    
    Returns:
        计算后的日期
    """
    if days == 0:
        return date
    
    current = date
    remaining = abs(days)
    direction = 1 if days > 0 else -1
    
    while remaining > 0:
        current += timedelta(days=direction)
        if is_trading_day(current):
            remaining -= 1
    
    return current
