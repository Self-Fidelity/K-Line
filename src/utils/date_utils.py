"""日期工具模块"""

import calendar
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd


# 中国股市节假日列表（需要定期更新）
# 这里只包含一些主要的节假日，实际使用时需要更完整的列表
CHINA_HOLIDAYS = {
    # 2024年节假日（示例）
    "2024-01-01",  # 元旦
    "2024-02-10",  # 春节
    "2024-02-11",
    "2024-02-12",
    "2024-02-13",
    "2024-02-14",
    "2024-02-15",
    "2024-02-16",
    "2024-02-17",
    "2024-04-04",  # 清明节
    "2024-04-05",
    "2024-04-06",
    "2024-05-01",  # 劳动节
    "2024-05-02",
    "2024-05-03",
    "2024-05-04",
    "2024-05-05",
    "2024-06-10",  # 端午节
    "2024-09-15",  # 中秋节
    "2024-09-16",
    "2024-09-17",
    "2024-10-01",  # 国庆节
    "2024-10-02",
    "2024-10-03",
    "2024-10-04",
    "2024-10-05",
    "2024-10-06",
    "2024-10-07",
}


def format_date(date: datetime, fmt: str = "%Y%m%d") -> str:
    """
    格式化日期为字符串
    
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
