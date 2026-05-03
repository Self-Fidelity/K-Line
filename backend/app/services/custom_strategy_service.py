"""自定义策略服务

使用 RestrictedPython 沙箱安全执行用户上传的策略代码。
所有用户代码在受限环境中运行，防止代码注入攻击。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime

from backend.app.models.custom_strategy import (
    CustomStrategyCreate,
    CustomStrategyUpdate,
    CustomStrategyInfo,
    CustomStrategyDetail,
    CustomStrategyValidateResponse,
)
from backend.app.dependencies import get_storage
from backend.app.utils.strategy_sandbox import get_sandbox, StrategySandbox
from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CustomStrategyService:
    """自定义策略服务类（沙箱安全执行）"""

    def __init__(self):
        """初始化自定义策略服务"""
        self.storage = get_storage()
        self.sandbox = get_sandbox()
        self.custom_strategy_dir = settings.DATA_DIR / "custom_strategies"
        self.custom_strategy_dir.mkdir(parents=True, exist_ok=True)

    def _extract_strategy_info(self, code: str) -> Dict[str, Any]:
        """
        使用沙箱从策略代码中安全提取策略信息

        Args:
            code: 策略代码

        Returns:
            包含策略信息的字典
        """
        result = self.sandbox.execute(code)
        if result.success and result.extracted_info:
            return result.extracted_info

        logger.warning(f"沙箱提取策略信息失败: {result.errors}")
        return {
            'name': None,
            'description': None,
            'detailed_description': None,
            'parameter_descriptions': {},
        }
    
    def create_strategy(
        self,
        user_id: int,
        strategy_data: CustomStrategyCreate,
    ) -> CustomStrategyInfo:
        """
        创建自定义策略（沙箱验证 + PostgreSQL 存储）

        Args:
            user_id: 用户ID
            strategy_data: 策略数据

        Returns:
            创建的策略信息
        """
        # 使用沙箱验证策略代码
        validation = self.validate_strategy_code(strategy_data.code)
        if not validation.valid:
            raise ValueError(f"策略代码验证失败: {', '.join(validation.errors)}")

        # 从策略代码中提取信息
        extracted_info = self._extract_strategy_info(strategy_data.code)

        # 合并用户提供的信息和提取的信息
        final_name = strategy_data.name or extracted_info.get('name') or '未命名策略'
        final_description = strategy_data.description or extracted_info.get('description') or ''
        final_detailed_description = strategy_data.detailed_description or extracted_info.get('detailed_description') or ''
        final_parameter_descriptions = strategy_data.parameter_descriptions or extracted_info.get('parameter_descriptions') or {}

        # 保存策略代码到文件
        user_strategy_dir = self.custom_strategy_dir / str(user_id)
        user_strategy_dir.mkdir(parents=True, exist_ok=True)

        safe_name = "".join(c for c in final_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')
        file_name = f"{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        file_path = user_strategy_dir / file_name
        file_path.write_text(strategy_data.code, encoding='utf-8')

        # 保存到数据库
        strategy_id = self.storage.create_custom_strategy(
            user_id=user_id,
            name=final_name,
            code=strategy_data.code,
            description=final_description,
            detailed_description=final_detailed_description,
            parameter_descriptions=final_parameter_descriptions,
            file_path=str(file_path),
        )

        logger.info(f"用户 {user_id} 创建自定义策略: {final_name} (ID: {strategy_id})")
        return self.get_strategy(strategy_id, user_id)

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
        # 检查策略是否存在且属于该用户
        existing = self.storage.get_custom_strategy_by_user(strategy_id, user_id)
        if not existing:
            raise ValueError("策略不存在或无权限访问")

        updates: Dict[str, Any] = {}

        # 如果更新了代码，需要沙箱验证
        if strategy_data.code is not None:
            validation = self.validate_strategy_code(strategy_data.code)
            if not validation.valid:
                raise ValueError(f"策略代码验证失败: {', '.join(validation.errors)}")
            updates['code'] = strategy_data.code

            # 更新文件
            file_path = Path(existing.get('file_path', ''))
            if file_path.exists():
                file_path.write_text(strategy_data.code, encoding='utf-8')

        if strategy_data.name is not None:
            updates['name'] = strategy_data.name
        if strategy_data.description is not None:
            updates['description'] = strategy_data.description
        if strategy_data.detailed_description is not None:
            updates['detailed_description'] = strategy_data.detailed_description
        if strategy_data.parameter_descriptions is not None:
            updates['parameter_descriptions'] = json.dumps(
                strategy_data.parameter_descriptions, ensure_ascii=False
            )

        if updates:
            self.storage.update_custom_strategy(strategy_id, **updates)
            logger.info(f"用户 {user_id} 更新自定义策略 ID: {strategy_id}")

        return self.get_strategy(strategy_id, user_id)

    def delete_strategy(self, strategy_id: int, user_id: int, is_admin: bool = False) -> bool:
        """
        删除自定义策略

        Args:
            strategy_id: 策略ID
            user_id: 当前用户ID
            is_admin: 是否为管理员

        Returns:
            是否删除成功
        """
        existing = self.storage.get_custom_strategy(strategy_id)
        if not existing:
            raise ValueError("策略不存在")

        if existing['user_id'] != user_id and not is_admin:
            raise ValueError("无权删除该策略")

        # 删除文件
        file_path = Path(existing.get('file_path', ''))
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                logger.warning(f"删除策略文件失败: {e}")

        self.storage.delete_custom_strategy(strategy_id)
        logger.info(f"用户 {user_id} (Admin: {is_admin}) 删除自定义策略 ID: {strategy_id}")
        return True

    def get_strategy(self, strategy_id: int, user_id: int) -> CustomStrategyInfo:
        """
        获取策略信息（不含代码）

        Args:
            strategy_id: 策略ID
            user_id: 用户ID

        Returns:
            策略信息
        """
        row = self.storage.get_custom_strategy_by_user(strategy_id, user_id)
        if not row:
            raise ValueError("策略不存在或无权限访问")

        param_descs = row.get('parameter_descriptions', {})
        if not param_descs:
            extracted = self._extract_strategy_info(row.get('code', ''))
            param_descs = extracted.get('parameter_descriptions', {})
            if param_descs:
                self.storage.update_custom_strategy(
                    strategy_id,
                    parameter_descriptions=json.dumps(param_descs, ensure_ascii=False),
                )

        return CustomStrategyInfo(
            id=row['id'],
            user_id=row['user_id'],
            name=row['name'],
            description=row.get('description') or '',
            detailed_description=row.get('detailed_description') or '',
            parameter_descriptions=param_descs,
            is_public=bool(row.get('is_public')),
            is_system=bool(row.get('is_system')),
            created_at=row.get('created_at', ''),
            updated_at=row.get('updated_at', ''),
        )

    def get_strategy_detail(self, strategy_id: int, user_id: int) -> CustomStrategyDetail:
        """
        获取策略详情（包含代码）

        Args:
            strategy_id: 策略ID
            user_id: 用户ID

        Returns:
            策略详情
        """
        row = self.storage.get_custom_strategy_by_user(strategy_id, user_id)
        if not row:
            raise ValueError("策略不存在或无权限访问")

        param_descs = row.get('parameter_descriptions', {})
        if not param_descs:
            extracted = self._extract_strategy_info(row.get('code', ''))
            param_descs = extracted.get('parameter_descriptions', {})
            if param_descs:
                self.storage.update_custom_strategy(
                    strategy_id,
                    parameter_descriptions=json.dumps(param_descs, ensure_ascii=False),
                )

        return CustomStrategyDetail(
            id=row['id'],
            user_id=row['user_id'],
            name=row['name'],
            description=row.get('description') or '',
            detailed_description=row.get('detailed_description') or '',
            code=row.get('code', ''),
            parameter_descriptions=param_descs,
            is_public=bool(row.get('is_public')),
            is_system=bool(row.get('is_system')),
            created_at=row.get('created_at', ''),
            updated_at=row.get('updated_at', ''),
        )

    def list_strategies(self, user_id: int = None) -> List[CustomStrategyInfo]:
        """
        获取所有自定义策略（包含创建者信息）

        Args:
            user_id: 可选的用户ID过滤

        Returns:
            策略列表
        """
        rows = self.storage.list_custom_strategies(user_id=user_id)

        return [
            CustomStrategyInfo(
                id=row['id'],
                user_id=row['user_id'],
                username=row.get('username') or 'Unknown',
                name=row['name'],
                description=row.get('description') or '',
                detailed_description=row.get('detailed_description') or '',
                parameter_descriptions=row.get('parameter_descriptions', {}),
                is_public=bool(row.get('is_public')),
                is_system=bool(row.get('is_system')),
                created_at=row.get('created_at', ''),
                updated_at=row.get('updated_at', ''),
            )
            for row in rows
        ]

    def validate_strategy_code(
        self,
        code: str,
        test_data: bool = False,
    ) -> CustomStrategyValidateResponse:
        """
        使用沙箱安全验证策略代码

        Args:
            code: 策略代码
            test_data: 是否使用测试数据验证

        Returns:
            验证结果
        """
        # 静态安全检查
        validation = self.sandbox.validate(code)

        # 沙箱执行检查
        if validation.success:
            result = self.sandbox.execute(code)
            if not result.success:
                validation.errors.extend(result.errors)
                validation.warnings.extend(result.warnings)
            else:
                validation.extracted_info = result.extracted_info
                if test_data and result.strategy_instance:
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
                        analysis = result.strategy_instance.analyze(test_df)
                        if analysis is None:
                            validation.warnings.append("analyze 返回 None")
                    except Exception as e:
                        validation.warnings.append(f"测试运行告警: {str(e)}")

        return CustomStrategyValidateResponse(
            valid=len(validation.errors) == 0,
            errors=validation.errors,
            warnings=validation.warnings,
            strategy_name=validation.extracted_info.get('name'),
            strategy_description=validation.extracted_info.get('description'),
        )

    def load_user_strategy(self, strategy_id: int) -> Optional[Any]:
        """
        使用沙箱安全加载用户自定义策略实例

        Args:
            strategy_id: 策略ID

        Returns:
            策略实例，如果不存在返回 None
        """
        row = self.storage.get_custom_strategy(strategy_id)
        if not row or not row.get('code'):
            logger.warning(f"策略 ID {strategy_id} 不存在或无代码")
            return None

        result = self.sandbox.execute(row['code'])
        if result.success and result.strategy_instance:
            return result.strategy_instance

        logger.warning(f"沙箱加载策略 ID {strategy_id} 失败: {result.errors}")
        return None
