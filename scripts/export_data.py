"""数据导出示例脚本"""

import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import settings
from src.data_storage import SQLiteStorage, DataExporter
from src.utils.logger import setup_logger
from src.utils.date_utils import format_date, parse_date

logger = setup_logger()


def export_stock_data(
    stock_code: str,
    start_date: str = "",
    end_date: str = "",
    output_dir: str = "",
):
    """
    导出股票数据到CSV
    
    Args:
        stock_code: 股票代码
        start_date: 开始日期（格式：'20240101'），如果为空则从最早开始
        end_date: 结束日期（格式：'20240101'），如果为空则到最新
        output_dir: 输出目录，如果为空则使用配置中的导出目录
    """
    logger.info(f"开始导出股票 {stock_code} 的数据...")
    
    # 初始化
    settings.init_directories()
    storage = SQLiteStorage()
    data_source = storage.get_update_config("data_source", "akshare")
    
    # 获取数据
    df = storage.get_daily_data(stock_code, start_date, end_date, data_source=data_source)
    
    if df.empty:
        logger.warning(f"股票 {stock_code} 没有数据可导出")
        return None
    
    logger.info(f"获取到 {len(df)} 条数据")
    
    # 导出数据
    exporter = DataExporter(export_dir=Path(output_dir) if output_dir else None)
    
    # 生成文件名
    date_suffix = ""
    if start_date or end_date:
        date_suffix = f"_{start_date}_{end_date}" if start_date and end_date else f"_{start_date or end_date}"
    
    filename = f"{stock_code}_data{date_suffix}.csv"
    file_path = exporter.export_to_csv(df, filename)
    
    logger.info(f"数据已导出到: {file_path}")
    return file_path


def export_all_stocks(output_dir: str = ""):
    """
    导出所有股票的数据到CSV
    
    Args:
        output_dir: 输出目录，如果为空则使用配置中的导出目录
    """
    logger.info("开始导出所有股票的数据...")
    
    settings.init_directories()
    storage = SQLiteStorage()
    data_source = storage.get_update_config("data_source", "akshare")
    exporter = DataExporter(output_dir=Path(output_dir) if output_dir else None)
    
    # 获取所有股票代码
    stock_codes = storage.get_all_stocks()
    logger.info(f"找到 {len(stock_codes)} 只股票")
    
    exported_count = 0
    failed_count = 0
    
    for stock_code in stock_codes:
        try:
            df = storage.get_daily_data(stock_code, data_source=data_source)
            if not df.empty:
                filename = f"{stock_code}_data.csv"
                exporter.export_to_csv(df, filename)
                exported_count += 1
                
                if exported_count % 100 == 0:
                    logger.info(f"已导出 {exported_count}/{len(stock_codes)} 只股票")
            else:
                failed_count += 1
        except Exception as e:
            logger.error(f"导出股票 {stock_code} 失败: {e}", exc_info=True)
            failed_count += 1
            continue
    
    logger.info(f"导出完成！成功: {exported_count}，失败: {failed_count}")


def export_with_date_range(
    stock_code: str,
    start_date: str,
    end_date: str,
    output_dir: str = "",
):
    """
    按日期范围导出数据
    
    Args:
        stock_code: 股票代码
        start_date: 开始日期（格式：'20240101'）
        end_date: 结束日期（格式：'20240101'）
        output_dir: 输出目录
    """
    logger.info(f"按日期范围导出股票 {stock_code} 的数据: {start_date} ~ {end_date}")
    
    settings.init_directories()
    storage = SQLiteStorage()
    data_source = storage.get_update_config("data_source", "akshare")
    
    # 获取数据
    df = storage.get_daily_data(stock_code, start_date, end_date, data_source=data_source)
    
    if df.empty:
        logger.warning(f"股票 {stock_code} 在指定日期范围内没有数据")
        return None
    
    logger.info(f"获取到 {len(df)} 条数据")
    
    # 导出数据
    exporter = DataExporter(export_dir=Path(output_dir) if output_dir else None)
    filename = f"{stock_code}_data_{start_date}_{end_date}.csv"
    file_path = exporter.export_to_csv(df, filename)
    
    logger.info(f"数据已导出到: {file_path}")
    return file_path


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="数据导出示例脚本")
    parser.add_argument(
        "--stock",
        type=str,
        help="股票代码（如 000001），如果指定则只导出该股票的数据",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default="",
        help="开始日期（格式：20240101）",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default="",
        help="结束日期（格式：20240101）",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="",
        help="输出目录（可选），如果为空则使用配置中的导出目录",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="导出所有股票的数据",
    )
    
    args = parser.parse_args()
    
    if args.all:
        # 导出所有股票
        export_all_stocks(args.output_dir)
    elif args.stock:
        # 导出单只股票
        if args.start_date and args.end_date:
            # 按日期范围导出
            export_with_date_range(args.stock, args.start_date, args.end_date, args.output_dir)
        else:
            # 导出所有数据
            export_stock_data(args.stock, args.start_date, args.end_date, args.output_dir)
    else:
        parser.print_help()
        logger.error("请指定股票代码（--stock）或使用 --all 导出所有股票")


if __name__ == "__main__":
    main()
