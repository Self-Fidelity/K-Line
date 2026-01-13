"""自定义策略服务"""

import json
import sqlite3
import tempfile
import importlib.util
import inspect
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime
import traceback

from backend.app.models.custom_strategy import (
    CustomStrategyCreate,
    CustomStrategyUpdate,
    CustomStrategyInfo,
    CustomStrategyDetail,
    CustomStrategyValidateResponse,
)
from src.strategy.base import BaseStrategy
from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CustomStrategyService:
    """自定义策略服务类"""
    
    def __init__(self):
        """初始化自定义策略服务"""
        self.db_path = settings.get_database_path()
        self.custom_strategy_dir = settings.DATA_DIR / "custom_strategies"
        self.custom_strategy_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _extract_strategy_info(self, code: str) -> Dict[str, Any]:
        """
        从策略代码中提取策略信息（包括parameter_descriptions）
        
        Args:
            code: 策略代码
            
        Returns:
            包含策略信息的字典
        """
        info = {
            'name': None,
            'description': None,
            'detailed_description': None,
            'parameter_descriptions': {}
        }
        
        try:
            # 尝试加载策略类
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                f.write(code)
                temp_file = Path(f.name)
            
            try:
                spec = importlib.util.spec_from_file_location("temp_strategy", temp_file)
                if spec is None or spec.loader is None:
                    return info
                
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # 查找策略类
                strategy_class = None
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (
                        issubclass(obj, BaseStrategy)
                        and obj != BaseStrategy
                        and obj.__module__ == module.__name__
                    ):
                        strategy_class = obj
                        break
                
                if strategy_class:
                    # 实例化策略以获取信息
                    strategy = strategy_class()
                    info['name'] = strategy.name
                    info['description'] = strategy.description
                    info['detailed_description'] = strategy.detailed_description
                    info['parameter_descriptions'] = strategy.parameter_descriptions or {}
            
            finally:
                # 清理临时文件
                try:
                    temp_file.unlink()
                except:
                    pass
        
        except Exception as e:
            logger.warning(f"提取策略信息失败: {e}")
        
        return info
    
    def create_strategy(
        self,
        user_id: int,
        strategy_data: CustomStrategyCreate,
    ) -> CustomStrategyInfo:
        """
        创建自定义策略
        
        Args:
            user_id: 用户ID
            strategy_data: 策略数据
            
        Returns:
            创建的策略信息
        """
        conn = self._get_connection()
        try:
            # 验证策略代码
            validation = self.validate_strategy_code(strategy_data.code)
            if not validation.valid:
                raise ValueError(f"策略代码验证失败: {', '.join(validation.errors)}")
            
            # 从策略代码中提取信息（如果用户没有提供，则使用提取的信息）
            extracted_info = self._extract_strategy_info(strategy_data.code)
            
            # 使用用户提供的信息，如果没有则使用提取的信息
            final_name = strategy_data.name or extracted_info['name'] or '未命名策略'
            final_description = strategy_data.description or extracted_info['description'] or ''
            final_detailed_description = strategy_data.detailed_description or extracted_info['detailed_description'] or ''
            # parameter_descriptions: 优先使用用户提供的，如果没有则使用从代码中提取的
            final_parameter_descriptions = strategy_data.parameter_descriptions or extracted_info['parameter_descriptions']
            
            # 生成策略文件路径
            user_strategy_dir = self.custom_strategy_dir / str(user_id)
            user_strategy_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成安全的文件名（基于策略名称）
            safe_name = "".join(c for c in final_name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '_')
            file_name = f"{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
            file_path = user_strategy_dir / file_name
            
            # 保存策略代码到文件
            file_path.write_text(strategy_data.code, encoding='utf-8')
            
            # 保存到数据库
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO custom_strategies 
                (user_id, name, description, detailed_description, code, parameter_descriptions, file_path, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                final_name,
                final_description,
                final_detailed_description,
                strategy_data.code,
                json.dumps(final_parameter_descriptions, ensure_ascii=False),
                str(file_path),
                now,
            ))
            strategy_id = cursor.lastrowid
            conn.commit()
            
            logger.info(f"用户 {user_id} 创建自定义策略: {final_name} (ID: {strategy_id})")
            
            return self.get_strategy(strategy_id, user_id)
            
        except sqlite3.IntegrityError as e:
            conn.rollback()
            if "UNIQUE constraint" in str(e):
                raise ValueError(f"策略名称 '{strategy_data.name}' 已存在")
            raise
        except Exception as e:
            conn.rollback()
            logger.error(f"创建自定义策略失败: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    
    def update_strategy(
        self,
        strategy_id: int,
        user_id: int,
        strategy_data: CustomStrategyUpdate,
    ) -> CustomStrategyInfo:
        """
        更新自定义策略
        
        Args:
            strategy_id: 策略ID
            user_id: 用户ID
            strategy_data: 更新的策略数据
            
        Returns:
            更新后的策略信息
        """
        conn = self._get_connection()
        try:
            # 检查策略是否存在且属于该用户
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, code, file_path FROM custom_strategies 
                WHERE id = ? AND user_id = ?
            """, (strategy_id, user_id))
            row = cursor.fetchone()
            
            if not row:
                raise ValueError(f"策略不存在或无权限访问")
            
            # 如果更新了代码，需要验证
            if strategy_data.code is not None:
                validation = self.validate_strategy_code(strategy_data.code)
                if not validation.valid:
                    raise ValueError(f"策略代码验证失败: {', '.join(validation.errors)}")
                
                # 更新文件
                file_path = Path(row['file_path'])
                if file_path.exists():
                    file_path.write_text(strategy_data.code, encoding='utf-8')
            
            # 构建更新SQL
            updates = []
            params = []
            
            if strategy_data.name is not None:
                updates.append("name = ?")
                params.append(strategy_data.name)
            
            if strategy_data.description is not None:
                updates.append("description = ?")
                params.append(strategy_data.description)
            
            if strategy_data.detailed_description is not None:
                updates.append("detailed_description = ?")
                params.append(strategy_data.detailed_description)
            
            if strategy_data.code is not None:
                updates.append("code = ?")
                params.append(strategy_data.code)
            
            if strategy_data.parameter_descriptions is not None:
                updates.append("parameter_descriptions = ?")
                params.append(json.dumps(strategy_data.parameter_descriptions, ensure_ascii=False))
            
            if updates:
                updates.append("updated_at = ?")
                params.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                params.append(strategy_id)
                params.append(user_id)
                
                cursor.execute(f"""
                    UPDATE custom_strategies 
                    SET {', '.join(updates)}
                    WHERE id = ? AND user_id = ?
                """, params)
                conn.commit()
                
                logger.info(f"用户 {user_id} 更新自定义策略 ID: {strategy_id}")
            
            return self.get_strategy(strategy_id, user_id)
            
        except Exception as e:
            conn.rollback()
            logger.error(f"更新自定义策略失败: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    
    def delete_strategy(self, strategy_id: int, user_id: int) -> bool:
        """
        删除自定义策略
        
        Args:
            strategy_id: 策略ID
            user_id: 用户ID
            
        Returns:
            是否删除成功
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            # 获取文件路径
            cursor.execute("""
                SELECT file_path FROM custom_strategies 
                WHERE id = ? AND user_id = ?
            """, (strategy_id, user_id))
            row = cursor.fetchone()
            
            if not row:
                raise ValueError(f"策略不存在或无权限访问")
            
            # 删除文件
            file_path = Path(row['file_path']) if row['file_path'] else None
            if file_path and file_path.exists():
                try:
                    file_path.unlink()
                except Exception as e:
                    logger.warning(f"删除策略文件失败: {e}")
            
            # 删除数据库记录
            cursor.execute("""
                DELETE FROM custom_strategies 
                WHERE id = ? AND user_id = ?
            """, (strategy_id, user_id))
            conn.commit()
            
            logger.info(f"用户 {user_id} 删除自定义策略 ID: {strategy_id}")
            return True
            
        except Exception as e:
            conn.rollback()
            logger.error(f"删除自定义策略失败: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    
    def get_strategy(self, strategy_id: int, user_id: int) -> CustomStrategyInfo:
        """
        获取策略信息
        
        Args:
            strategy_id: 策略ID
            user_id: 用户ID
            
        Returns:
            策略信息
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, user_id, name, description, detailed_description, 
                       code, parameter_descriptions, is_public, is_system, 
                       created_at, updated_at
                FROM custom_strategies 
                WHERE id = ? AND user_id = ?
            """, (strategy_id, user_id))
            row = cursor.fetchone()
            
            if not row:
                raise ValueError(f"策略不存在或无权限访问")
            
            # 解析parameter_descriptions
            param_descs = json.loads(row['parameter_descriptions'] or '{}')
            
            # 如果parameter_descriptions为空，尝试从代码中提取
            if not param_descs or len(param_descs) == 0:
                extracted_info = self._extract_strategy_info(row['code'])
                if extracted_info['parameter_descriptions']:
                    param_descs = extracted_info['parameter_descriptions']
                    # 更新数据库中的parameter_descriptions
                    cursor.execute("""
                        UPDATE custom_strategies 
                        SET parameter_descriptions = ?
                        WHERE id = ?
                    """, (json.dumps(param_descs, ensure_ascii=False), strategy_id))
                    conn.commit()
            
            return CustomStrategyInfo(
                id=row['id'],
                user_id=row['user_id'],
                name=row['name'],
                description=row['description'] or '',
                detailed_description=row['detailed_description'] or '',
                parameter_descriptions=param_descs,
                is_public=bool(row['is_public']),
                is_system=bool(row['is_system']),
                created_at=row['created_at'],
                updated_at=row['updated_at'],
            )
        finally:
            conn.close()
    
    def get_strategy_detail(self, strategy_id: int, user_id: int) -> CustomStrategyDetail:
        """
        获取策略详情（包含代码）
        
        Args:
            strategy_id: 策略ID
            user_id: 用户ID
            
        Returns:
            策略详情
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, user_id, name, description, detailed_description, 
                       code, parameter_descriptions, is_public, is_system, 
                       created_at, updated_at
                FROM custom_strategies 
                WHERE id = ? AND user_id = ?
            """, (strategy_id, user_id))
            row = cursor.fetchone()
            
            if not row:
                raise ValueError(f"策略不存在或无权限访问")
            
            # 解析parameter_descriptions
            param_descs = json.loads(row['parameter_descriptions'] or '{}')
            
            # 如果parameter_descriptions为空，尝试从代码中提取
            if not param_descs or len(param_descs) == 0:
                extracted_info = self._extract_strategy_info(row['code'])
                if extracted_info['parameter_descriptions']:
                    param_descs = extracted_info['parameter_descriptions']
                    # 更新数据库中的parameter_descriptions
                    cursor.execute("""
                        UPDATE custom_strategies 
                        SET parameter_descriptions = ?
                        WHERE id = ?
                    """, (json.dumps(param_descs, ensure_ascii=False), strategy_id))
                    conn.commit()
            
            return CustomStrategyDetail(
                id=row['id'],
                user_id=row['user_id'],
                name=row['name'],
                description=row['description'] or '',
                detailed_description=row['detailed_description'] or '',
                code=row['code'],
                parameter_descriptions=param_descs,
                is_public=bool(row['is_public']),
                is_system=bool(row['is_system']),
                created_at=row['created_at'],
                updated_at=row['updated_at'],
            )
        finally:
            conn.close()
    
    def list_strategies(self, user_id: int) -> List[CustomStrategyInfo]:
        """
        获取用户的所有自定义策略
        
        Args:
            user_id: 用户ID
            
        Returns:
            策略列表
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, user_id, name, description, detailed_description, 
                       parameter_descriptions, is_public, is_system, 
                       created_at, updated_at
                FROM custom_strategies 
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
            
            strategies = []
            for row in cursor.fetchall():
                strategies.append(CustomStrategyInfo(
                    id=row['id'],
                    user_id=row['user_id'],
                    name=row['name'],
                    description=row['description'] or '',
                    detailed_description=row['detailed_description'] or '',
                    parameter_descriptions=json.loads(row['parameter_descriptions'] or '{}'),
                    is_public=bool(row['is_public']),
                    is_system=bool(row['is_system']),
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                ))
            
            return strategies
        finally:
            conn.close()
    
    def validate_strategy_code(
        self,
        code: str,
        test_data: bool = False,
    ) -> CustomStrategyValidateResponse:
        """
        验证策略代码
        
        Args:
            code: 策略代码
            test_data: 是否使用测试数据验证
            
        Returns:
            验证结果
        """
        errors = []
        warnings = []
        strategy_name = None
        strategy_description = None
        
        try:
            # 语法检查
            compile(code, '<string>', 'exec')
            
            # 尝试加载策略类
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                f.write(code)
                temp_file = Path(f.name)
            
            try:
                spec = importlib.util.spec_from_file_location("temp_strategy", temp_file)
                if spec is None or spec.loader is None:
                    errors.append("无法加载策略模块")
                    return CustomStrategyValidateResponse(
                        valid=False,
                        errors=errors,
                        warnings=warnings,
                    )
                
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # 查找策略类
                strategy_class = None
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (
                        issubclass(obj, BaseStrategy)
                        and obj != BaseStrategy
                        and obj.__module__ == module.__name__
                    ):
                        strategy_class = obj
                        break
                
                if strategy_class is None:
                    errors.append("未找到继承自 BaseStrategy 的策略类")
                else:
                    # 尝试实例化
                    try:
                        strategy = strategy_class()
                        strategy_name = strategy.name
                        strategy_description = strategy.description
                        
                        # 如果使用测试数据，尝试运行
                        if test_data:
                            import pandas as pd
                            test_df = pd.DataFrame({
                                'date': pd.date_range('2024-01-01', periods=100, freq='D'),
                                'open': [100 + i * 0.1 for i in range(100)],
                                'close': [101 + i * 0.1 for i in range(100)],
                                'high': [102 + i * 0.1 for i in range(100)],
                                'low': [99 + i * 0.1 for i in range(100)],
                                'volume': [1000000] * 100,
                            })
                            
                            try:
                                result = strategy.analyze(test_df)
                                if result is None or not isinstance(result, pd.DataFrame):
                                    warnings.append("analyze 方法返回结果格式可能不正确")
                            except Exception as e:
                                warnings.append(f"测试运行失败: {str(e)}")
                    
                    except Exception as e:
                        errors.append(f"策略实例化失败: {str(e)}")
            
            finally:
                # 清理临时文件
                try:
                    temp_file.unlink()
                except:
                    pass
            
        except SyntaxError as e:
            errors.append(f"语法错误: {str(e)}")
        except Exception as e:
            errors.append(f"验证失败: {str(e)}")
            logger.error(f"策略代码验证失败: {e}", exc_info=True)
        
        return CustomStrategyValidateResponse(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            strategy_name=strategy_name,
            strategy_description=strategy_description,
        )
    
    def load_user_strategy(self, strategy_id: int) -> Optional[BaseStrategy]:
        """
        加载用户自定义策略实例
        
        Args:
            strategy_id: 策略ID
            
        Returns:
            策略实例，如果不存在返回 None
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT code, file_path FROM custom_strategies 
                WHERE id = ?
            """, (strategy_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # 优先使用文件路径，如果文件不存在则使用代码
            file_path = Path(row['file_path']) if row['file_path'] else None
            code = row['code'] or ''
            
            if not code:
                logger.warning(f"策略 ID {strategy_id} 没有代码")
                return None
            
            if file_path and file_path.exists():
                # 从文件加载
                spec = importlib.util.spec_from_file_location(f"custom_strategy_{strategy_id}", file_path)
            else:
                # 从代码加载（使用临时文件）
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                    f.write(code)
                    temp_file = Path(f.name)
                spec = importlib.util.spec_from_file_location(f"custom_strategy_{strategy_id}", temp_file)
            
            if spec is None or spec.loader is None:
                return None
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 查找策略类
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (
                    issubclass(obj, BaseStrategy)
                    and obj != BaseStrategy
                ):
                    return obj()
            
            return None
            
        except Exception as e:
            logger.error(f"加载用户策略失败: {e}", exc_info=True)
            return None
        finally:
            conn.close()
