"""手动数据获取脚本"""

import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import settings
from src.data_fetcher import StockListManager, StockDataFetcher
from src.data_storage import get_storage_instance
from src.utils.logger import setup_logger
from src.utils.date_utils import format_date

logger = setup_logger()


def fetch_all_stocks(
    market: str = "main",
    start_date: str = "",
    end_date: str = "",
):
    """
    获取所有股票的数据
    
    Args:
        market: 市场类型
        start_date: 开始日期（格式：'20240101'），如果为空则获取历史所有数据
        end_date: 结束日期（格式：'20240101'），如果为空则获取到最新
    """
    logger.info("开始获取股票数据...")
    
    # 初始化
    settings.init_directories()
    storage = get_storage_instance()
    stock_manager = StockListManager()
    fetcher = StockDataFetcher()
    
    # 获取股票列表
    stock_list = stock_manager.get_stock_list(market=market)
    stock_codes = stock_list["code"].tolist()
    
    logger.info(f"共需要获取 {len(stock_codes)} 只股票的数据")
    
    success_count = 0
    fail_count = 0
    
    data_source = fetcher._get_provider().name
    
    for i, stock_code in enumerate(stock_codes, 1):
        try:
            # 检查是否已有数据
            latest_date = storage.get_latest_date(stock_code, data_source=data_source)
            
            # 如果已有数据且未指定开始日期，则从最新日期之后开始获取
            fetch_start_date = start_date
            if not fetch_start_date and latest_date:
                # 从最新日期的下一天开始
                from src.utils.date_utils import parse_date, add_trading_days
                latest = parse_date(latest_date)
                next_date = add_trading_days(latest, 1)
                fetch_start_date = format_date(next_date)
                logger.debug(f"股票 {stock_code} 已有数据到 {latest_date}，将从 {fetch_start_date} 开始获取")
            
            # 获取数据
            df = fetcher.get_daily_data(
                stock_code=stock_code,
                start_date=fetch_start_date,
                end_date=end_date,
                adjust="hfq",  # 后复权
            )
            
            if not df.empty:
                # 保存数据
                storage.save_daily_data(df, stock_code, data_source=data_source)
                success_count += 1
            else:
                logger.warning(f"股票 {stock_code} 未获取到数据")
                fail_count += 1
            
            # 进度日志
            if i % 100 == 0:
                logger.info(f"进度: {i}/{len(stock_codes)}，成功: {success_count}，失败: {fail_count}")
                
        except Exception as e:
            logger.error(f"处理股票 {stock_code} 失败: {e}", exc_info=True)
            fail_count += 1
            continue
    
    logger.info(f"数据获取完成！成功: {success_count}，失败: {fail_count}")


def fetch_single_stock(stock_code: str, start_date: str = "", end_date: str = ""):
    """
    获取单只股票的数据
    
    Args:
        stock_code: 股票代码
        start_date: 开始日期
        end_date: 结束日期
    """
    logger.info(f"开始获取股票 {stock_code} 的数据...")
    
    settings.init_directories()
    storage = get_storage_instance()
    fetcher = StockDataFetcher()
    
    data_source = fetcher._get_provider().name
    
    # 检查是否已有数据
    latest_date = storage.get_latest_date(stock_code, data_source=data_source)
    fetch_start_date = start_date
    if not fetch_start_date and latest_date:
        from src.utils.date_utils import parse_date, add_trading_days
        latest = parse_date(latest_date)
        next_date = add_trading_days(latest, 1)
        fetch_start_date = format_date(next_date)
        logger.info(f"股票 {stock_code} 已有数据到 {latest_date}，将从 {fetch_start_date} 开始获取")
    
    # 获取数据
    df = fetcher.get_daily_data(
        stock_code=stock_code,
        start_date=fetch_start_date,
        end_date=end_date,
        adjust="hfq",
    )
    
    if not df.empty:
        storage.save_daily_data(df, stock_code, data_source=data_source)
        logger.info(f"股票 {stock_code} 数据获取完成，共 {len(df)} 条")
    else:
        logger.warning(f"股票 {stock_code} 未获取到数据")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="手动获取股票数据")
    parser.add_argument(
        "--market",
        type=str,
        default="main",
        help="市场类型（main/sse/szse/all），默认为 main",
    )
    parser.add_argument(
        "--stock",
        type=str,
        help="股票代码（如 000001），如果指定则只获取该股票的数据",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default="",
        help="开始日期（格式：20240101），如果为空则获取历史所有数据",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default="",
        help="结束日期（格式：20240101），如果为空则获取到最新",
    )
    
    args = parser.parse_args()
    
    if args.stock:
        # 获取单只股票
        fetch_single_stock(args.stock, args.start_date, args.end_date)
    else:
        # 获取所有股票
        fetch_all_stocks(args.market, args.start_date, args.end_date)


if __name__ == "__main__":
    main()
