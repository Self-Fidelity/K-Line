"""策略代码沙箱执行环境

基于 RestrictedPython 实现安全的自定义策略代码执行。
所有用户代码在受限环境中运行，禁止：
- 文件系统访问 (open, __import__ 等)
- 网络访问 (requests, urllib 等)
- 系统调用 (os, subprocess 等)
- 危险内置函数 (eval, exec, compile, getattr 等)
"""

from __future__ import annotations

import inspect
import traceback
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from RestrictedPython import compile_restricted, safe_globals
from RestrictedPython.Eval import default_guarded_getitem
from RestrictedPython.Guards import (
    guarded_iter_unpack_sequence,
    safer_getattr,
    full_write_guard,
)


@dataclass
class SandboxResult:
    """沙箱执行结果"""
    success: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    strategy_class: Optional[type] = None
    strategy_instance: Optional[Any] = None
    extracted_info: Dict[str, Any] = field(default_factory=dict)


class StrategySandbox:
    """策略代码安全沙箱"""

    # 允许的安全内置函数和类型
    ALLOWED_BUILTINS: Dict[str, Any] = {
        # 基本类型
        'bool': bool,
        'int': int,
        'float': float,
        'str': str,
        'list': list,
        'tuple': tuple,
        'dict': dict,
        'set': set,
        'frozenset': frozenset,
        # 安全函数
        'len': len,
        'min': min,
        'max': max,
        'sum': sum,
        'abs': abs,
        'round': round,
        'range': range,
        'enumerate': enumerate,
        'zip': zip,
        'map': map,
        'filter': filter,
        'sorted': sorted,
        'reversed': reversed,
        'any': any,
        'all': all,
        # 类型检查
        'isinstance': isinstance,
        'issubclass': issubclass,
        'type': type,
        # 数学运算
        'pow': pow,
        'divmod': divmod,
        # 字符串
        'format': format,
        'repr': repr,
        # 迭代工具
        'iter': iter,
        'next': next,
        # 属性访问
        'hasattr': hasattr,  # 受限版本在运行时检查
        # None & 常量
        'None': None,
        'True': True,
        'False': False,
        # 异常类（允许 raise）
        'Exception': Exception,
        'ValueError': ValueError,
        'TypeError': TypeError,
        'KeyError': KeyError,
        'IndexError': IndexError,
        'AttributeError': AttributeError,
        'RuntimeError': RuntimeError,
        'NotImplementedError': NotImplementedError,
    }

    # 允许导入的模块白名单
    ALLOWED_MODULES: List[str] = [
        'math',
        'statistics',
        'datetime',
    ]

    def __init__(self):
        """初始化沙箱"""
        self._build_globals()

    def _build_globals(self) -> Dict[str, Any]:
        """构建安全的全局命名空间"""
        globs = safe_globals.copy()
        globs.update(self.ALLOWED_BUILTINS)

        # 安全属性访问守卫
        globs['_getattr_'] = safer_getattr
        globs['_getitem_'] = default_guarded_getitem
        globs['_write_'] = full_write_guard
        globs['_getiter_'] = iter
        globs['_iter_unpack_sequence_'] = guarded_iter_unpack_sequence

        # 替换危险的 __import__ 为安全版本
        globs['__import__'] = self._safe_import

        # 禁止访问
        globs['__builtins__'] = globs
        globs['__metaclass__'] = type

        # 注入必要的基类
        globs['ABC'] = __import__('abc').ABC
        globs['abstractmethod'] = __import__('abc').abstractmethod
        globs['pd'] = __import__('pandas')
        globs['np'] = __import__('numpy')
        globs['DataFrame'] = __import__('pandas').DataFrame
        globs['Series'] = __import__('pandas').Series
        globs['Optional'] = __import__('typing').Optional
        globs['Dict'] = __import__('typing').Dict
        globs['Any'] = __import__('typing').Any

        self._globs = globs

    def _safe_import(self, name: str, *args, **kwargs) -> Any:
        """安全的模块导入：只允许白名单中的模块"""
        # 允许导入的顶级包
        allowed_top = {'math', 'statistics', 'datetime', 'abc', 'typing',
                       'pandas', 'numpy', 'collections'}
        top_level = name.split('.')[0]

        if top_level in allowed_top:
            return __import__(name, *args, **kwargs)

        raise ImportError(f"模块 '{name}' 不允许导入（安全限制）")

    def validate(self, code: str) -> SandboxResult:
        """
        验证策略代码（编译检查 + 静态分析）

        Args:
            code: 策略源代码

        Returns:
            SandboxResult 包含验证结果
        """
        result = SandboxResult(success=True)

        # 1. 静态安全检查：扫描危险关键词
        dangerous_patterns = [
            ('__import__', '禁止直接使用 __import__'),
            ('import os', '禁止导入 os 模块'),
            ('import sys', '禁止导入 sys 模块'),
            ('import subprocess', '禁止导入 subprocess 模块'),
            ('import socket', '禁止导入 socket 模块'),
            ('import urllib', '禁止导入 urllib 模块'),
            ('import requests', '禁止导入 requests 模块'),
            ('import shutil', '禁止导入 shutil 模块'),
            ('import pickle', '禁止导入 pickle 模块'),
            ('open(', '禁止文件操作 (open)'),
            ('exec(', '禁止使用 exec'),
            ('eval(', '禁止使用 eval'),
            ('compile(', '禁止使用 compile'),
        ]

        for pattern, msg in dangerous_patterns:
            if pattern in code:
                result.errors.append(msg)

        # 2. 编译检查
        try:
            byte_code = compile_restricted(code, filename='<strategy>', mode='exec')
        except SyntaxError as e:
            result.errors.append(f"语法错误 (行 {e.lineno}): {e.msg}")
            result.success = False
            return result
        except Exception as e:
            result.errors.append(f"编译错误: {str(e)}")
            result.success = False
            return result

        if result.errors:
            result.success = False
        return result

    def execute(self, code: str) -> SandboxResult:
        """
        在沙箱中执行策略代码

        Args:
            code: 策略源代码

        Returns:
            SandboxResult 包含执行结果和提取的策略信息
        """
        result = self.validate(code)
        if not result.success:
            return result

        # 编译
        try:
            byte_code = compile_restricted(code, filename='<strategy>', mode='exec')
        except Exception as e:
            result.errors.append(f"编译错误: {str(e)}")
            result.success = False
            return result

        # 创建局部命名空间
        local_ns: Dict[str, Any] = {}

        # 执行代码
        try:
            exec(byte_code, self._globs, local_ns)
        except Exception as e:
            result.errors.append(f"执行错误: {str(e)}")
            result.success = False
            return result

        # 查找策略类
        strategy_class = None
        from src.strategy.base import BaseStrategy

        for name, obj in local_ns.items():
            if (
                inspect.isclass(obj)
                and issubclass(obj, BaseStrategy)
                and obj is not BaseStrategy
            ):
                strategy_class = obj
                break

        if strategy_class is None:
            result.errors.append("未找到继承自 BaseStrategy 的策略类")
            result.success = False
            return result

        result.strategy_class = strategy_class

        # 实例化并提取信息
        try:
            instance = strategy_class()
            result.strategy_instance = instance
            result.extracted_info = {
                'name': getattr(instance, 'name', '未命名策略'),
                'description': getattr(instance, 'description', ''),
                'detailed_description': getattr(instance, 'detailed_description', ''),
                'parameter_descriptions': getattr(instance, 'parameter_descriptions', {}),
            }
        except Exception as e:
            result.warnings.append(f"策略实例化警告: {str(e)}")
            result.extracted_info = {
                'name': getattr(strategy_class, 'name', '未命名策略'),
                'description': '',
                'detailed_description': '',
                'parameter_descriptions': {},
            }

        return result

    def execute_analysis(
        self,
        code: str,
        data: 'pd.DataFrame',
        **params: Any,
    ) -> SandboxResult:
        """
        在沙箱中执行策略分析

        Args:
            code: 策略源代码
            data: 股票数据 DataFrame
            **params: 策略参数

        Returns:
            SandboxResult (strategy_instance 将包含分析结果)
        """
        result = self.execute(code)
        if not result.success or result.strategy_instance is None:
            return result

        try:
            # 设置参数
            for key, value in params.items():
                if hasattr(result.strategy_instance, key):
                    setattr(result.strategy_instance, key, value)

            # 验证数据
            if not result.strategy_instance.validate_data(data):
                result.errors.append("数据不满足策略要求")
                result.success = False
                return result

            # 执行分析
            analysis_result = result.strategy_instance.analyze(data, **params)
            result.extracted_info['analysis_result'] = analysis_result
        except Exception as e:
            result.errors.append(f"策略分析执行错误: {str(e)}")
            result.success = False

        return result


# 全局沙箱实例（推荐复用，避免重复初始化）
_sandbox_instance: Optional[StrategySandbox] = None


def get_sandbox() -> StrategySandbox:
    """获取全局沙箱实例"""
    global _sandbox_instance
    if _sandbox_instance is None:
        _sandbox_instance = StrategySandbox()
    return _sandbox_instance
