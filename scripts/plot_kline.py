"""K线图生成示例脚本"""

import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import settings
from src.data_storage import SQLiteStorage
from src.visualization import KLineChart
from src.utils.logger import setup_logger
from src.utils.date_utils import format_date, parse_date

logger = setup_logger()


def plot_kline(
    stock_code: str,
    start_date: str = "",
    end_date: str = "",
    output_path: str = "",
    with_ma: bool = False,
    ma_periods: list = None,
):
    """
    生成K线图（HTML格式）
    
    Args:
        stock_code: 股票代码
        start_date: 开始日期（格式：'20240101'），如果为空则从最早开始
        end_date: 结束日期（格式：'20240101'），如果为空则到最新
        output_path: 输出路径，如果为空则自动生成HTML文件
        with_ma: 是否显示均线
        ma_periods: 均线周期列表，如 [5, 10, 20, 30]
    """
    logger.info(f"开始生成股票 {stock_code} 的K线图...")
    
    # 初始化
    settings.init_directories()
    storage = SQLiteStorage()
    data_source = storage.get_update_config("data_source", "akshare")
    
    # 获取数据
    df = storage.get_daily_data(stock_code, start_date, end_date, data_source=data_source)
    
    if df.empty:
        logger.warning(f"股票 {stock_code} 没有数据可绘制")
        return None
    
    logger.info(f"获取到 {len(df)} 条数据")
    
    # 获取股票信息（用于图表标题）
    stock_name = stock_code
    
    # 生成输出路径
    if not output_path:
        date_suffix = ""
        if start_date or end_date:
            date_suffix = f"_{start_date}_{end_date}" if start_date and end_date else f"_{start_date or end_date}"
        
        output_dir = settings.CHART_DIR
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(output_dir / f"{stock_code}_kline{date_suffix}.html")
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 创建K线图
    chart = KLineChart(width=1200, height=800)
    
    try:
        if with_ma:
            # 带均线的K线图
            ma_periods = ma_periods or [5, 10, 20, 30]
            file_path = chart.plot_with_ma(
                data=df,
                stock_code=stock_code,
                stock_name=stock_name,
                ma_periods=ma_periods,
                save_path=output_path,
            )
        else:
            # 普通K线图
            file_path = chart.plot(
                data=df,
                stock_code=stock_code,
                stock_name=stock_name,
                save_path=output_path,
            )
        
        logger.info(f"K线图已保存到: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"生成K线图失败: {e}", exc_info=True)
        return None


def plot_multiple_stocks(
    stock_codes: list,
    start_date: str = "",
    end_date: str = "",
    output_dir: str = "",
    with_ma: bool = False,
):
    """
    批量生成多只股票的K线图
    
    Args:
        stock_codes: 股票代码列表
        start_date: 开始日期
        end_date: 结束日期
        output_dir: 输出目录
        with_ma: 是否显示均线
    """
    logger.info(f"开始批量生成 {len(stock_codes)} 只股票的K线图...")
    
    settings.init_directories()
    output_dir = Path(output_dir) if output_dir else settings.CHART_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    failed_count = 0
    
    for stock_code in stock_codes:
        try:
            output_path = output_dir / f"{stock_code}_kline.html"
            result = plot_kline(
                stock_code=stock_code,
                start_date=start_date,
                end_date=end_date,
                output_path=str(output_path),
                with_ma=with_ma,
            )
            if result:
                success_count += 1
            else:
                failed_count += 1
        except Exception as e:
            logger.error(f"生成股票 {stock_code} 的K线图失败: {e}", exc_info=True)
            failed_count += 1
            continue
        
        if (success_count + failed_count) % 10 == 0:
            logger.info(f"进度: {success_count + failed_count}/{len(stock_codes)}")
    
    logger.info(f"批量生成完成！成功: {success_count}，失败: {failed_count}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="K线图生成示例脚本")
    parser.add_argument(
        "--stock",
        type=str,
        required=True,
        help="股票代码（如 000001）",
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
        "--output",
        type=str,
        default="",
        help="输出文件路径（可选），如果为空则自动生成HTML文件",
    )
    parser.add_argument(
        "--ma",
        action="store_true",
        help="显示均线",
    )
    parser.add_argument(
        "--ma-periods",
        type=str,
        default="5,10,20,30",
        help="均线周期（用逗号分隔），如 '5,10,20,30'",
    )
    
    args = parser.parse_args()
    
    # 解析均线周期
    ma_periods = None
    if args.ma:
        try:
            ma_periods = [int(p.strip()) for p in args.ma_periods.split(",")]
        except ValueError:
            logger.warning(f"均线周期格式错误，使用默认值: [5, 10, 20, 30]")
            ma_periods = [5, 10, 20, 30]
    
    # 生成K线图
    plot_kline(
        stock_code=args.stock,
        start_date=args.start_date,
        end_date=args.end_date,
        output_path=args.output,
        with_ma=args.ma,
        ma_periods=ma_periods,
    )


if __name__ == "__main__":
    main()
