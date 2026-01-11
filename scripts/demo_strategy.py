"""策略框架使用示例脚本"""

import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import settings
from src.data_storage import SQLiteStorage, DataExporter
from src.strategy import StrategyManager, BaseStrategy
from src.utils.logger import setup_logger
import pandas as pd

logger = setup_logger()


def demo_strategy_framework():
    """
    演示策略框架的使用
    """
    logger.info("=== 策略框架使用示例 ===")
    
    # 初始化
    settings.init_directories()
    storage = SQLiteStorage()
    strategy_manager = StrategyManager()
    
    # 列出所有已注册的策略
    strategies = strategy_manager.list_strategies()
    logger.info(f"已注册的策略数量: {len(strategies)}")
    
    if strategies:
        logger.info(f"策略列表: {strategies}")
    else:
        logger.info("当前没有已注册的策略插件")
        logger.info("您可以创建策略插件并放在 src/strategy/plugins/ 目录下")
    
    # 演示如何获取股票数据并运行策略（如果有策略的话）
    stock_code = "000001"
    
    # 获取股票数据
    logger.info(f"\n获取股票 {stock_code} 的数据...")
    df = storage.get_daily_data(stock_code, start_date="20240101", end_date="20241231")
    
    if df.empty:
        logger.warning(f"股票 {stock_code} 没有数据")
        return
    
    logger.info(f"获取到 {len(df)} 条数据")
    
    # 如果策略管理器中有策略，运行它们
    if strategies:
        logger.info(f"\n运行 {len(strategies)} 个策略...")
        results = strategy_manager.run_all_strategies(df)
        
        logger.info(f"策略执行完成，结果数量: {len(results)}")
        
        # 导出策略结果
        exporter = DataExporter()
        for strategy_name, result_df in results.items():
            if not result_df.empty:
                logger.info(f"策略 {strategy_name} 返回 {len(result_df)} 条结果")
                file_path = exporter.export_strategy_result(result_df, strategy_name, stock_code)
                logger.info(f"结果已导出到: {file_path}")
    else:
        logger.info("\n当前没有可运行的策略插件")
        logger.info("策略框架已就绪，可以创建自定义策略插件")


def create_example_strategy():
    """
    创建一个示例策略（用于演示）
    注意：这个策略不会被自动加载，仅作为示例代码
    """
    
    class ExampleStrategy(BaseStrategy):
        """
        示例策略：简单的移动平均策略
        这是一个演示策略，展示如何创建自定义策略
        """
        
        def __init__(self):
            super().__init__(
                name="example_ma",
                description="示例移动平均策略"
            )
        
        def analyze(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
            """
            执行策略分析
            
            Args:
                data: 股票数据 DataFrame
                **kwargs: 其他参数
            
            Returns:
                分析结果 DataFrame
            """
            # 复制数据
            result = data.copy()
            
            # 计算移动平均
            ma5 = result["close"].rolling(window=5).mean()
            ma10 = result["close"].rolling(window=10).mean()
            ma20 = result["close"].rolling(window=20).mean()
            
            # 添加到结果中
            result["ma5"] = ma5
            result["ma10"] = ma10
            result["ma20"] = ma20
            
            # 计算信号（简单示例：当ma5上穿ma10时买入）
            result["signal"] = 0
            result.loc[ma5 > ma10, "signal"] = 1
            result.loc[ma5 < ma10, "signal"] = -1
            
            return result
        
        def get_required_columns(self) -> list[str]:
            """返回策略需要的列"""
            return ["date", "close"]
    
    logger.info("=== 示例策略代码 ===")
    logger.info("这是一个示例策略的代码结构")
    logger.info("要使用策略插件，请：")
    logger.info("1. 在 src/strategy/plugins/ 目录下创建Python文件")
    logger.info("2. 定义继承自 BaseStrategy 的策略类")
    logger.info("3. 实现 analyze 方法")
    logger.info("4. 策略管理器会自动发现并加载策略")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="策略框架使用示例脚本")
    parser.add_argument(
        "--create-example",
        action="store_true",
        help="显示示例策略代码",
    )
    
    args = parser.parse_args()
    
    if args.create_example:
        create_example_strategy()
    else:
        demo_strategy_framework()


if __name__ == "__main__":
    main()
