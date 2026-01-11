"""策略分析和统计脚本"""

import sys
from pathlib import Path
from typing import Optional
import argparse

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import settings
from src.data_storage import SQLiteStorage
from src.strategy import StrategyManager
from src.strategy.statistics import StrategyStatistics
from src.visualization import KLineChart
from src.utils.logger import setup_logger

logger = setup_logger()


def analyze_strategy(
    strategy_name: str,
    stock_code: str,
    start_date: str = "",
    end_date: str = "",
    plot_chart: bool = False,
    output_dir: Optional[str] = None,
) -> dict:
    """
    分析策略并计算统计指标
    
    Args:
        strategy_name: 策略名称
        stock_code: 股票代码
        start_date: 开始日期（格式：20240101）
        end_date: 结束日期（格式：20240101）
        plot_chart: 是否生成带信号的K线图
        output_dir: 输出目录（可选）
    
    Returns:
        统计结果字典
    """
    logger.info(f"分析策略: {strategy_name}，股票代码: {stock_code}")
    
    # 初始化
    settings.init_directories()
    storage = SQLiteStorage()
    strategy_manager = StrategyManager()
    
    # 检查策略是否存在
    available_strategies = strategy_manager.list_strategies()
    matched_strategy = None
    
    if strategy_name in available_strategies:
        matched_strategy = strategy_name
    else:
        for avail_strategy in available_strategies:
            if strategy_name in avail_strategy or avail_strategy in strategy_name:
                matched_strategy = avail_strategy
                break
    
    if not matched_strategy:
        raise ValueError(
            f"策略 '{strategy_name}' 不存在。可用策略: {available_strategies if available_strategies else '无'}"
        )
    
    strategy_name = matched_strategy
    
    # 获取股票数据
    logger.info(f"获取股票 {stock_code} 的数据...")
    df = storage.get_daily_data(stock_code, start_date, end_date)
    
    if df.empty:
        raise ValueError(f"股票 {stock_code} 没有数据")
    
    logger.info(f"获取到 {len(df)} 条数据")
    
    # 运行策略
    logger.info(f"执行策略分析...")
    strategy_result = strategy_manager.run_strategy(strategy_name, df)
    
    if strategy_result.empty:
        raise ValueError("策略分析结果为空")
    
    logger.info(f"策略分析完成，生成 {len(strategy_result)} 条结果")
    
    # 计算统计指标
    logger.info(f"计算策略统计指标...")
    stats = StrategyStatistics.calculate_statistics(
        df,
        strategy_result,
    )
    
    # 打印统计结果
    StrategyStatistics.print_statistics(stats)
    
    # 如果需要，生成带信号的K线图
    if plot_chart:
        logger.info(f"生成带策略信号的K线图...")
        chart = KLineChart(width=1200, height=800)
        
        date_suffix = ""
        if start_date or end_date:
            date_suffix = f"_{start_date}_{end_date}" if start_date and end_date else f"_{start_date or end_date}"
        
        output_dir_path = Path(output_dir) if output_dir else settings.CHART_DIR
        output_dir_path.mkdir(parents=True, exist_ok=True)
        chart_path = output_dir_path / f"{stock_code}_{strategy_name}_signals{date_suffix}.html"
        
        chart.plot(
            data=df,
            stock_code=stock_code,
            save_path=chart_path,
            strategy_result=strategy_result,
            statistics=stats,
        )
        
        logger.info(f"K线图已保存到: {chart_path}")
        stats["chart_path"] = str(chart_path)
    
    return stats


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="策略分析和统计脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 分析策略并显示统计结果
  python scripts/analyze_strategy.py --strategy "MA Strategy" --stock 000001 --start-date 20240101 --end-date 20241231
  
  # 分析策略并生成带信号的K线图
  python scripts/analyze_strategy.py --strategy "MA Strategy" --stock 000001 --plot
        """,
    )
    
    parser.add_argument(
        "--strategy",
        type=str,
        required=True,
        help="策略名称",
    )
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
        "--plot",
        action="store_true",
        help="生成带策略信号的K线图",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="",
        help="输出目录（可选）",
    )
    
    args = parser.parse_args()
    
    try:
        stats = analyze_strategy(
            strategy_name=args.strategy,
            stock_code=args.stock,
            start_date=args.start_date,
            end_date=args.end_date,
            plot_chart=args.plot,
            output_dir=args.output_dir if args.output_dir else None,
        )
        
        if "chart_path" in stats:
            print(f"\nK线图已保存到: {stats['chart_path']}")
    
    except Exception as e:
        logger.error(f"分析策略失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
