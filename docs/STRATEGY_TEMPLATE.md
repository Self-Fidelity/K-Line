# 策略开发模板指南

本文档说明如何为 K-Line 项目添加自定义策略。

## 目录结构

策略文件应放置在 `src/strategy/plugins/` 目录下。每个策略文件应包含一个继承自 `BaseStrategy` 的策略类。

```
src/strategy/plugins/
├── ma_strategy.py          # 移动平均策略（示例）
├── rsi_strategy.py         # RSI策略
├── macd_strategy.py        # MACD策略
├── bollinger_strategy.py   # 布林带策略
├── momentum_strategy.py    # 动量策略
├── candlestick_strategy.py # 蜡烛图形态策略
└── your_strategy.py        # 你的自定义策略
```

## 策略类基本结构

每个策略类必须：

1. 继承自 `BaseStrategy`
2. 实现 `analyze()` 方法
3. 返回包含 `date`、`signal`、`signal_type` 列的 DataFrame
4. 策略名称使用英文

### 基本模板

```python
"""你的策略名称（Your Strategy Name）"""

import pandas as pd
from typing import Any

from src.strategy.base import BaseStrategy
from src.utils.logger import get_logger

logger = get_logger(__name__)


class YourStrategy(BaseStrategy):
    """
    你的策略说明
    
    策略说明：
    - 策略的逻辑说明
    - 参数说明
    - 信号生成规则
    """
    
    def __init__(
        self,
        param1: type = default_value,
        param2: type = default_value,
    ):
        """
        初始化策略
        
        Args:
            param1: 参数1说明
            param2: 参数2说明
        """
        super().__init__(
            name="Your Strategy Name",  # 策略名称（英文）
            description=f"Your Strategy Description (param1: {param1}, param2: {param2})"
        )
        self.param1 = param1
        self.param2 = param2
    
    def analyze(
        self,
        data: pd.DataFrame,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        执行策略分析
        
        Args:
            data: 股票数据 DataFrame，必须包含 date 和策略所需的列
            **kwargs: 其他参数（可选，用于覆盖初始化时的参数）
        
        Returns:
            分析结果 DataFrame，必须包含以下列：
            - date: 日期
            - signal: 信号（1=买入，-1=卖出，0=持有）
            - signal_type: 信号类型（"买入"/"卖出"/"持有"）
            - 其他策略相关的指标列（可选）
        """
        # 1. 验证数据
        if not self.validate_data(data):
            raise ValueError("数据不满足策略要求")
        
        # 2. 复制和准备数据
        df = data.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        
        # 3. 获取参数（支持通过 kwargs 覆盖）
        param1 = kwargs.get("param1", self.param1)
        param2 = kwargs.get("param2", self.param2)
        
        # 4. 计算指标（根据策略逻辑）
        # df["indicator"] = your_calculation(df, param1, param2)
        
        # 5. 生成信号
        df["signal"] = 0  # 初始化为0（持有）
        
        # 根据策略逻辑设置信号
        # df.loc[condition, "signal"] = 1  # 买入信号
        # df.loc[condition, "signal"] = -1  # 卖出信号
        
        # 6. 添加信号类型描述
        df["signal_type"] = df["signal"].map({1: "买入", -1: "卖出", 0: "持有"})
        
        # 7. 选择返回的列
        result_columns = ["date", "close", "signal", "signal_type"]  # 根据需要添加其他列
        result = df[result_columns].copy()
        
        # 8. 记录日志
        signal_count = len(result[result["signal"] != 0])
        logger.info(f"策略分析完成，共生成 {signal_count} 个交易信号")
        
        return result
    
    def get_required_columns(self) -> list[str]:
        """
        获取策略需要的列
        
        Returns:
            必需的列名列表
        """
        # 默认返回所有基础列
        return ["date", "open", "close", "high", "low", "volume"]
        # 如果策略只需要部分列，可以覆盖此方法
        # return ["date", "close"]  # 例如：只需要日期和收盘价
```

## 数据格式说明

### 输入数据（data DataFrame）

策略接收的 DataFrame 通常包含以下列：

- `date`: 日期（datetime 或可转换为 datetime 的格式）
- `open`: 开盘价
- `close`: 收盘价
- `high`: 最高价
- `low`: 最低价
- `volume`: 成交量

### 输出数据（返回值）

策略的 `analyze()` 方法必须返回一个 DataFrame，至少包含以下列：

- `date`: 日期
- `signal`: 信号值
  - `1`: 买入信号
  - `-1`: 卖出信号
  - `0`: 持有（无信号）
- `signal_type`: 信号类型（字符串）
  - `"买入"`: 买入信号
  - `"卖出"`: 卖出信号
  - `"持有"`: 持有

可以包含额外的列，例如策略计算的指标值（如 RSI、MACD 等）。

## 策略类型示例

### 1. 技术指标策略

技术指标策略通常基于价格或成交量计算指标，然后根据指标值生成信号。

**示例：RSI 策略**

```python
class RSIStrategy(BaseStrategy):
    def __init__(self, period: int = 14, oversold: float = 30.0, overbought: float = 70.0):
        super().__init__(name="RSI Strategy", description="...")
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
    
    def analyze(self, data: pd.DataFrame, **kwargs: Any) -> pd.DataFrame:
        # 计算 RSI 指标
        # 根据 RSI 值生成信号
        # 返回结果
        pass
```

### 2. 蜡烛图形态策略

蜡烛图形态策略基于 K 线的形态模式（如看涨吞没、锤子线等）生成信号。

**示例：看涨吞没策略**

```python
class BullishEngulfingStrategy(BaseStrategy):
    def analyze(self, data: pd.DataFrame, **kwargs: Any) -> pd.DataFrame:
        # 检测看涨吞没形态
        # 生成买入信号
        # 返回结果
        pass
```

### 3. 组合策略

组合策略可以结合多个指标或多个形态，生成更复杂的信号。

## 信号生成最佳实践

### 1. 避免连续信号

如果策略可能产生连续的同方向信号，建议只在状态变化时产生信号：

```python
# 方法1：只在状态变化时产生信号
df["signal"] = 0
for i in range(1, len(df)):
    prev_value = df.iloc[i - 1]["indicator"]
    curr_value = df.iloc[i]["indicator"]
    
    if prev_value <= threshold and curr_value > threshold:
        df.iloc[i, df.columns.get_loc("signal")] = 1
    elif prev_value >= threshold and curr_value < threshold:
        df.iloc[i, df.columns.get_loc("signal")] = -1
```

### 2. 使用交叉信号

对于均线交叉等策略，应该在交叉点产生信号：

```python
for i in range(1, len(df)):
    prev_short = df.iloc[i - 1]["ma_short"]
    prev_long = df.iloc[i - 1]["ma_long"]
    curr_short = df.iloc[i]["ma_short"]
    curr_long = df.iloc[i]["ma_long"]
    
    # 金叉：短期均线从下方穿越长期均线
    if prev_short <= prev_long and curr_short > curr_long:
        df.iloc[i, df.columns.get_loc("signal")] = 1
```

### 3. 参数化

策略应该支持参数化，允许用户调整参数：

```python
def __init__(self, period: int = 14):
    self.period = period

def analyze(self, data: pd.DataFrame, **kwargs: Any) -> pd.DataFrame:
    period = kwargs.get("period", self.period)  # 支持通过 kwargs 覆盖
```

## 测试策略

### 1. 使用 analyze_strategy.py 脚本

```bash
# 运行策略分析
python scripts/analyze_strategy.py \
    --strategy "Your Strategy Name" \
    --stock 000001 \
    --start-date 20240101 \
    --end-date 20241231 \
    --plot
```

### 2. 使用 Python 代码

```python
from src.strategy import StrategyManager
from src.data_storage import SQLiteStorage

# 初始化
storage = SQLiteStorage()
strategy_manager = StrategyManager()

# 获取数据
df = storage.get_daily_data("000001", "20240101", "20241231")

# 运行策略
result = strategy_manager.run_strategy("Your Strategy Name", df)

# 查看结果
print(result.head())
```

## 策略管理器自动加载

策略管理器（`StrategyManager`）会自动扫描 `src/strategy/plugins/` 目录下的所有 `.py` 文件，并加载其中继承自 `BaseStrategy` 的类。

**注意事项：**

1. 策略类必须直接继承自 `BaseStrategy`
2. 策略类必须在文件的顶层定义（不能嵌套在其他类中）
3. 策略类必须能够无参数实例化（`Strategy()`），或者在 `__init__` 中提供所有参数的默认值
4. 策略名称（`name`）必须唯一

## 策略命名规范

1. **策略名称（name）**：使用英文，简洁明了
   - 示例：`"MA Strategy"`、`"RSI Strategy"`、`"Bullish Engulfing"`

2. **策略类名**：使用驼峰命名法，以 `Strategy` 结尾
   - 示例：`MAStrategy`、`RSIStrategy`、`BullishEngulfingStrategy`

3. **文件名**：使用下划线命名法，以 `_strategy.py` 结尾
   - 示例：`ma_strategy.py`、`rsi_strategy.py`、`bullish_engulfing_strategy.py`

## 完整示例

参考以下文件了解完整的策略实现：

- **技术指标策略**：`src/strategy/plugins/ma_strategy.py`（移动平均策略）
- **技术指标策略**：`src/strategy/plugins/rsi_strategy.py`（RSI策略）
- **蜡烛图形态策略**：`src/strategy/plugins/candlestick_strategy.py`（多种蜡烛图形态）

## 常见问题

### Q1: 策略没有被加载？

**A:** 检查以下几点：
1. 文件是否在 `src/strategy/plugins/` 目录下
2. 类是否继承自 `BaseStrategy`
3. 类名是否符合规范
4. 查看日志文件 `logs/kline.log` 中的错误信息

### Q2: 如何让策略支持参数？

**A:** 在 `__init__` 方法中定义参数，并在 `analyze` 方法中使用 `kwargs.get()` 来获取参数：

```python
def __init__(self, period: int = 14):
    self.period = period

def analyze(self, data: pd.DataFrame, **kwargs: Any) -> pd.DataFrame:
    period = kwargs.get("period", self.period)
    # 使用 period 进行计算
```

### Q3: 策略只需要部分数据列怎么办？

**A:** 覆盖 `get_required_columns()` 方法：

```python
def get_required_columns(self) -> list[str]:
    return ["date", "close"]  # 只返回需要的列
```

### Q4: 如何调试策略？

**A:** 
1. 使用 `logger.info()` 或 `logger.debug()` 记录中间值
2. 在策略中添加 `print()` 语句查看数据
3. 使用 `analyze_strategy.py` 脚本测试，添加 `--plot` 参数查看可视化结果

## 更多资源

- 策略基类定义：`src/strategy/base.py`
- 策略管理器：`src/strategy/manager.py`
- 现有策略示例：`src/strategy/plugins/` 目录

---

**提示**：在创建新策略前，建议先参考现有策略的实现，特别是与你想要实现的策略类型相似的策略。
