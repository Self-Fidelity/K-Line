"""策略运行脚本"""

import sys
from pathlib import Path
from typing import Optional
import argparse

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import settings
from src.data_storage import SQLiteStorage
from src.data_storage.strategy_export import StrategyResultExporter
from src.strategy import StrategyManager
from src.utils.logger import setup_logger
from src.utils.date_utils import format_date

logger = setup_logger()


def run_strategy(
    strategy_name: str,
    stock_code: str,
    start_date: str = "",
    end_date: str = "",
    output_dir: Optional[str] = None,
    **strategy_kwargs,
) -> Path:
    """
    运行指定策略
    
    Args:
        strategy_name: 策略名称
        stock_code: 股票代码
        start_date: 开始日期（格式：20240101）
        end_date: 结束日期（格式：20240101）
        output_dir: 输出目录（可选）
        **strategy_kwargs: 传递给策略的参数
    
    Returns:
        输出文件路径
    """
    logger.info(f"开始运行策略: {strategy_name}，股票代码: {stock_code}")
    
    # 初始化
    settings.init_directories()
    storage = SQLiteStorage()
    strategy_manager = StrategyManager()
    exporter = StrategyResultExporter(base_dir=Path(output_dir) if output_dir else None)
    
    # 检查策略是否存在（使用策略名称匹配，支持部分匹配）
    available_strategies = strategy_manager.list_strategies()
    matched_strategy = None
    
    # 精确匹配
    if strategy_name in available_strategies:
        matched_strategy = strategy_name
    else:
        # 部分匹配（支持中英文策略名称）
        for avail_strategy in available_strategies:
            if strategy_name in avail_strategy or avail_strategy in strategy_name:
                matched_strategy = avail_strategy
                break
    
    if not matched_strategy:
        raise ValueError(
            f"策略 '{strategy_name}' 不存在。可用策略: {available_strategies if available_strategies else '无'}"
        )
    
    # 使用匹配到的策略名称
    strategy_name = matched_strategy
    
    # 获取股票数据
    logger.info(f"获取股票 {stock_code} 的数据...")
    df = storage.get_daily_data(stock_code, start_date, end_date)
    
    if df.empty:
        raise ValueError(f"股票 {stock_code} 没有数据")
    
    logger.info(f"获取到 {len(df)} 条数据")
    
    # 运行策略
    logger.info(f"执行策略分析...")
    result = strategy_manager.run_strategy(strategy_name, df, **strategy_kwargs)
    
    if result.empty:
        logger.warning("策略分析结果为空")
        return None
    
    logger.info(f"策略分析完成，生成 {len(result)} 条结果")
    
    # 导出结果
    date_suffix = ""
    if start_date or end_date:
        date_suffix = f"_{start_date}_{end_date}" if start_date and end_date else f"_{start_date or end_date}"
    
    # 生成文件名
    filename = f"{stock_code}{date_suffix}.csv"
    file_path = exporter.export_result(result, strategy_name, stock_code, filename)
    
    logger.info(f"策略结果已导出到: {file_path}")
    
    return file_path


def run_all_strategies(
    stock_code: str,
    start_date: str = "",
    end_date: str = "",
    output_dir: Optional[str] = None,
) -> dict:
    """
    运行所有已注册的策略
    
    Args:
        stock_code: 股票代码
        start_date: 开始日期（格式：20240101）
        end_date: 结束日期（格式：20240101）
        output_dir: 输出目录（可选）
    
    Returns:
        结果字典，key为策略名称，value为输出文件路径
    """
    logger.info(f"运行所有策略，股票代码: {stock_code}")
    
    # 初始化
    settings.init_directories()
    storage = SQLiteStorage()
    strategy_manager = StrategyManager()
    
    # 获取可用策略
    strategies = strategy_manager.list_strategies()
    if not strategies:
        logger.warning("当前没有可用的策略")
        return {}
    
    logger.info(f"找到 {len(strategies)} 个策略: {strategies}")
    
    # 获取股票数据
    logger.info(f"获取股票 {stock_code} 的数据...")
    df = storage.get_daily_data(stock_code, start_date, end_date)
    
    if df.empty:
        raise ValueError(f"股票 {stock_code} 没有数据")
    
    logger.info(f"获取到 {len(df)} 条数据")
    
    # 运行所有策略
    results = {}
    exporter = StrategyResultExporter(base_dir=Path(output_dir) if output_dir else None)
    
    date_suffix = ""
    if start_date or end_date:
        date_suffix = f"_{start_date}_{end_date}" if start_date and end_date else f"_{start_date or end_date}"
    
    for strategy_name in strategies:
        try:
            logger.info(f"\n执行策略: {strategy_name}")
            result = strategy_manager.run_strategy(strategy_name, df)
            
            if result.empty:
                logger.warning(f"策略 {strategy_name} 结果为空")
                continue
            
            # 导出结果
            filename = f"{stock_code}{date_suffix}.csv"
            file_path = exporter.export_result(result, strategy_name, stock_code, filename)
            
            results[strategy_name] = file_path
            logger.info(f"策略 {strategy_name} 结果已导出到: {file_path}")
            
        except Exception as e:
            logger.error(f"执行策略 {strategy_name} 失败: {e}", exc_info=True)
            continue
    
    logger.info(f"\n所有策略执行完成，共成功 {len(results)} 个策略")
    
    return results


def list_strategies():
    """列出所有可用的策略"""
    settings.init_directories()
    strategy_manager = StrategyManager()
    
    strategies = strategy_manager.list_strategies()
    
    if not strategies:
        print("当前没有可用的策略插件")
        print(f"请将策略插件放在 {settings.STRATEGY_PLUGIN_DIR} 目录下")
        return
    
    print(f"\n可用的策略列表（共 {len(strategies)} 个）：")
    print("-" * 50)
    
    for strategy_name in strategies:
        strategy = strategy_manager.get_strategy(strategy_name)
        if strategy:
            info = strategy.get_strategy_info()
            print(f"\n策略名称: {info['name']}")
            print(f"  描述: {info['description']}")
            print(f"  需要的列: {', '.join(info['required_columns'])}")
    
    print("-" * 50)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="策略运行脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 列出所有可用策略
  python scripts/run_strategy.py --list
  
  # 运行指定策略
  python scripts/run_strategy.py --strategy "MA策略" --stock 000001
  
  # 运行策略并指定日期范围
  python scripts/run_strategy.py --strategy "MA策略" --stock 000001 --start-date 20240101 --end-date 20241231
  
  # 运行所有策略
  python scripts/run_strategy.py --all --stock 000001
  
  # 运行策略并传递参数（MA策略的自定义参数）
  python scripts/run_strategy.py --strategy "MA策略" --stock 000001 --strategy-args '{"short_period": 10, "long_period": 30}'
        """,
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="列出所有可用的策略",
    )
    parser.add_argument(
        "--strategy",
        type=str,
        help="要运行的策略名称",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="运行所有已注册的策略",
    )
    parser.add_argument(
        "--stock",
        type=str,
        required=False,
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
        "--output-dir",
        type=str,
        default="",
        help="输出目录（可选），如果为空则使用默认目录",
    )
    parser.add_argument(
        "--strategy-args",
        type=str,
        default="",
        help="传递给策略的参数（JSON格式字符串），例如: '{\"short_period\": 10, \"long_period\": 30}'",
    )
    
    args = parser.parse_args()
    
    # 列出策略
    if args.list:
        list_strategies()
        return
    
    # 验证参数
    if not args.all and not args.strategy:
        parser.error("必须指定 --strategy 或 --all")
    
    if not args.stock:
        parser.error("必须指定 --stock 参数")
    
    # 解析策略参数
    strategy_kwargs = {}
    if args.strategy_args:
        import json
        try:
            strategy_kwargs = json.loads(args.strategy_args)
        except json.JSONDecodeError as e:
            logger.error(f"解析策略参数失败: {e}")
            return
    
    # 运行策略
    try:
        if args.all:
            results = run_all_strategies(
                stock_code=args.stock,
                start_date=args.start_date,
                end_date=args.end_date,
                output_dir=args.output_dir if args.output_dir else None,
            )
            
            if results:
                print(f"\n成功运行 {len(results)} 个策略，结果文件:")
                for strategy_name, file_path in results.items():
                    print(f"  {strategy_name}: {file_path}")
        else:
            file_path = run_strategy(
                strategy_name=args.strategy,
                stock_code=args.stock,
                start_date=args.start_date,
                end_date=args.end_date,
                output_dir=args.output_dir if args.output_dir else None,
                **strategy_kwargs,
            )
            
            if file_path:
                print(f"\n策略结果已导出到: {file_path}")
    
    except Exception as e:
        logger.error(f"运行策略失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
