"""策略服务：封装StrategyManager"""

from typing import Optional, Dict, List, Any
import pandas as pd
from pathlib import Path
import sys

# 添加src目录到路径
backend_dir = Path(__file__).parent.parent.parent
src_dir = backend_dir.parent / "src"
sys.path.insert(0, str(src_dir))

from src.strategy.manager import StrategyManager
from src.strategy.statistics import StrategyStatistics
from src.utils.logger import get_logger
from backend.app.services.custom_strategy_service import CustomStrategyService

logger = get_logger(__name__)


class StrategyService:
    """策略服务类"""
    
    def __init__(self):
        """初始化策略服务"""
        self.strategy_manager = StrategyManager()
        self.statistics = StrategyStatistics()
        self.custom_strategy_service = CustomStrategyService()
    
    def list_strategies(self, user_id: Optional[int] = None) -> List[Dict]:
        """
        获取所有可用策略列表
        
        Args:
            user_id: 用户ID（用于过滤用户自定义策略）
        
        Returns:
            策略列表
        """
        strategy_names = self.strategy_manager.list_strategies()
        result = []
        for strategy_name in strategy_names:
            strategy = self.strategy_manager.get_strategy(strategy_name)
            if strategy:
                result.append({
                    "name": strategy.name,
                    "description": strategy.description,
                    "detailed_description": strategy.detailed_description,
                    "parameter_descriptions": strategy.parameter_descriptions,
                    "is_system": True,  # 系统策略
                })
        
        # 添加用户自定义策略
        if user_id:
            try:
                custom_strategies = self.custom_strategy_service.list_strategies(user_id)
                for cs in custom_strategies:
                    result.append({
                        "name": cs.name,
                        "description": cs.description,
                        "detailed_description": cs.detailed_description,
                        "parameter_descriptions": cs.parameter_descriptions,
                        "is_system": False,  # 用户自定义策略
                    })
            except Exception as e:
                logger.warning(f"加载用户自定义策略失败: {e}")
        
        return result
    
    def get_strategy_info(self, strategy_name: str, user_id: Optional[int] = None) -> Dict:
        """
        获取策略详细信息
        
        Args:
            strategy_name: 策略名称
            user_id: 用户ID（用于查找用户自定义策略）
        
        Returns:
            策略信息
        """
        strategy = self.strategy_manager.get_strategy(strategy_name)
        if strategy:
            strategy_info = strategy.get_strategy_info()
            return {
                "name": strategy_info["name"],
                "description": strategy_info["description"],
                "detailed_description": strategy_info.get("detailed_description", ""),
                "parameter_descriptions": strategy_info.get("parameter_descriptions", {}),
                "is_system": True,
            }
        
        # 如果系统策略中找不到，尝试从用户自定义策略中查找
        if user_id:
            try:
                custom_strategies = self.custom_strategy_service.list_strategies(user_id)
                for cs in custom_strategies:
                    if cs.name == strategy_name:
                        return {
                            "name": cs.name,
                            "description": cs.description,
                            "detailed_description": cs.detailed_description,
                            "parameter_descriptions": cs.parameter_descriptions,
                            "is_system": False,
                        }
            except Exception as e:
                logger.warning(f"查找用户自定义策略失败: {e}")
        
        return None
    
    def get_strategy_code(self, strategy_name: str) -> Optional[str]:
        """
        获取系统策略的代码
        
        Args:
            strategy_name: 策略名称
        
        Returns:
            策略代码，如果不存在返回 None
        """
        strategy = self.strategy_manager.get_strategy(strategy_name)
        if not strategy:
            logger.warning(f"策略 {strategy_name} 不存在")
            return None
        
        # 获取策略文件路径
        # 通过策略类的模块信息找到文件路径
        import inspect
        try:
            # 方法1: 通过 inspect.getfile 获取文件路径
            try:
                strategy_file = inspect.getfile(strategy.__class__)
                logger.debug(f"inspect.getfile 返回: {strategy_file}")
                
                # 如果是 .pyc 文件，转换为 .py 文件
                if strategy_file.endswith('.pyc'):
                    strategy_file = strategy_file[:-1]  # 移除 'c'
                
                file_path = Path(strategy_file)
                # 如果是 __pycache__ 目录中的文件，需要找到对应的 .py 文件
                if '__pycache__' in str(file_path):
                    # 从 __pycache__ 目录中找到对应的 .py 文件
                    cache_dir = file_path.parent
                    if cache_dir.name == '__pycache__':
                        parent_dir = cache_dir.parent
                        # 获取文件名（不含扩展名）
                        file_stem = file_path.stem
                        # 移除可能的 .cpython-xxx 后缀
                        if '.' in file_stem:
                            file_stem = file_stem.split('.')[0]
                        py_file = parent_dir / f"{file_stem}.py"
                        if py_file.exists():
                            file_path = py_file
                
                if file_path.exists() and file_path.suffix == '.py':
                    logger.debug(f"找到策略文件: {file_path}")
                    return file_path.read_text(encoding='utf-8')
                else:
                    logger.debug(f"文件不存在或不是 .py 文件: {file_path}")
            except (TypeError, OSError) as e:
                # inspect.getfile 可能失败，尝试方法2
                logger.debug(f"inspect.getfile 失败: {e}")
                pass
            
            # 方法2: 通过模块路径找到文件
            module = strategy.__class__.__module__
            if module:
                # 模块名格式: src.strategy.plugins.xxx
                module_parts = module.split('.')
                if len(module_parts) >= 3 and module_parts[0] == 'src' and module_parts[1] == 'strategy':
                    # 构建文件路径
                    from src.config import settings
                    plugin_dir = settings.STRATEGY_PLUGIN_DIR
                    if len(module_parts) == 4 and module_parts[2] == 'plugins':
                        # 模块名是 src.strategy.plugins.xxx
                        file_name = f"{module_parts[3]}.py"
                        file_path = plugin_dir / file_name
                        if file_path.exists():
                            return file_path.read_text(encoding='utf-8')
            
            # 方法3: 遍历策略目录，查找包含该策略的文件
            from src.config import settings
            plugin_dir = settings.STRATEGY_PLUGIN_DIR
            if plugin_dir.exists():
                for py_file in plugin_dir.glob("*.py"):
                    if py_file.name == "__init__.py":
                        continue
                    try:
                        # 读取文件内容，检查是否包含策略类
                        content = py_file.read_text(encoding='utf-8')
                        # 检查是否包含策略名称（支持多种格式）
                        name_patterns = [
                            f'name="{strategy_name}"',
                            f"name='{strategy_name}'",
                            f'name = "{strategy_name}"',
                            f"name = '{strategy_name}'",
                        ]
                        if any(pattern in content for pattern in name_patterns):
                            logger.debug(f"在文件 {py_file} 中找到策略 {strategy_name}")
                            return content
                    except Exception as e:
                        logger.debug(f"读取文件 {py_file} 失败: {e}")
                        continue
            
            logger.warning(f"无法找到策略 {strategy_name} 的源代码文件")
        except Exception as e:
            logger.error(f"无法获取策略 {strategy_name} 的文件路径: {e}", exc_info=True)
        
        return None
    
    def analyze(
        self,
        strategy_name: str,
        stock_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        user_id: Optional[int] = None,
        **strategy_kwargs: Any,
    ) -> Dict:
        """
        执行策略分析
        
        Args:
            strategy_name: 策略名称
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            user_id: 用户ID（用于加载用户自定义策略）
            **strategy_kwargs: 策略参数
        
        Returns:
            分析结果
        """
        # 获取数据
        from backend.app.services.data_service import DataService
        data_service = DataService()
        data = data_service.get_kline_data(stock_code, start_date, end_date)
        
        if data.empty:
            raise ValueError(f"股票 {stock_code} 没有数据")
        
        # 尝试从系统策略管理器获取策略
        strategy = self.strategy_manager.get_strategy(strategy_name)
        
        # 如果系统策略中找不到，尝试从用户自定义策略中加载
        if not strategy and user_id:
            try:
                custom_strategies = self.custom_strategy_service.list_strategies(user_id)
                for cs in custom_strategies:
                    if cs.name == strategy_name:
                        # 加载用户自定义策略
                        strategy = self.custom_strategy_service.load_user_strategy(cs.id)
                        if strategy:
                            break
            except Exception as e:
                logger.warning(f"加载用户自定义策略失败: {e}")
        
        if not strategy:
            raise ValueError(f"策略 {strategy_name} 不存在")
        
        # 验证数据
        if not strategy.validate_data(data):
            raise ValueError(f"数据不满足策略 {strategy_name} 的要求")
        
        # 执行策略
        try:
            result = strategy.analyze(data, **strategy_kwargs)
        except Exception as e:
            logger.error(f"执行策略 {strategy_name} 失败: {e}", exc_info=True)
            raise ValueError(f"执行策略失败: {str(e)}")
        
        if result.empty:
            raise ValueError("策略分析结果为空")
        
        # 计算统计信息
        stats = self.statistics.calculate_statistics(
            data=data,
            strategy_result=result,
        )
        
        # 转换结果数据，确保日期格式为字符串
        result_records = result.to_dict("records")
        for record in result_records:
            # 将 date 字段转换为字符串格式 YYYY-MM-DD
            if "date" in record and record["date"]:
                if hasattr(record["date"], "strftime"):
                    record["date"] = record["date"].strftime("%Y-%m-%d")
                elif isinstance(record["date"], str) and "T" in record["date"]:
                    record["date"] = record["date"].split("T")[0]
        
        return {
            "strategy_name": strategy_name,
            "stock_code": stock_code,
            "start_date": start_date,
            "end_date": end_date,
            "result": result_records,
            "statistics": stats,
        }
    
    def compare(
        self,
        strategy_names: List[str],
        stock_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        strategy_params: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Dict:
        """
        策略比较分析
        
        Args:
            strategy_names: 策略名称列表
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            strategy_params: 各策略的参数（key为策略名称，value为该策略的参数字典）
        
        Returns:
            比较结果
        """
        if not strategy_names:
            raise ValueError("至少选择一个策略进行比较")
        
        if len(strategy_names) < 2:
            raise ValueError("策略比较至少需要两个策略")
        
        strategy_params = strategy_params or {}
        results = []
        
        for strategy_name in strategy_names:
            try:
                params = strategy_params.get(strategy_name, {})
                result = self.analyze(
                    strategy_name=strategy_name,
                    stock_code=stock_code,
                    start_date=start_date,
                    end_date=end_date,
                    **params,
                )
                results.append(result)
            except Exception as e:
                results.append({
                    "strategy_name": strategy_name,
                    "stock_code": stock_code,
                    "error": str(e),
                })
        
        return {
            "stock_code": stock_code,
            "start_date": start_date,
            "end_date": end_date,
            "results": results,
        }
