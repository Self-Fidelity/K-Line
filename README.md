# K-Line 项目

中国股市每日股票数据获取和存储系统，支持策略分析和可视化。

## 项目概述

K-Line 是一个用于获取、存储和分析中国A股市场数据的Python项目。主要功能包括：

- ✅ 获取中国A股每日股票数据（使用 akshare）
- ✅ 数据本地存储（SQLite，支持增量更新）
- ✅ 手动触发数据更新（测试阶段）
- ✅ 策略分析插件框架
- ✅ 数据导出功能（CSV）
- ✅ K线图可视化（Bokeh，HTML格式）

## 技术栈

- **Python**: 3.12.3
- **依赖管理**: uv
- **数据获取**: akshare
- **数据存储**: SQLite
- **可视化**: Bokeh（HTML交互式图表）
- **数据处理**: pandas, numpy

## 项目结构

## 项目结构

```
K-Line/
├── backend/                # 后端代码 (FastAPI)
│   ├── app/                # 应用源码
│   ├── scripts/            # 数据库维护脚本
│   └── requirements.txt    # 后端依赖
├── frontend/               # 前端代码 (Vue 3 + TS)
│   ├── src/                # 前端源码
│   └── package.json        # 前端依赖
├── src/                    # 核心业务逻辑 (策略/数据处理)
│   ├── strategy/           # 策略引擎 & 插件
│   └── data_fetcher/       # 数据获取核心
├── scripts/                # 命令行工具脚本 (数据获取/策略运行)
├── data/                   # 数据存储
│   ├── database/           # SQLite 数据库
│   └── strategy_results/   # 策略结果
└── logs/                   # 系统日志
```

## 🚀 新增功能 (v0.2.0)

- **📊 筹码分布 (CYQ)**: 可视化筹码分布图，支持成本区间、获利比例分析。
- **📝 审计日志**: 记录用户关键操作（登录、策略创建等），增强系统安全性。
- **👥 用户管理**: 完善的 RBAC 权限系统，支持管理员管理用户角色。
- **⚡ 策略优化**: 支持多线程参数优化，实时显示优化进度。
- **🧩 策略聚合**: 支持策略参数方案的保存与加载，方便批量管理。

## 安装说明

### 前置要求

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) - 快速的 Python 包管理工具

安装 uv：
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# 或者使用 pip: pip install uv
```

### 1. 创建虚拟环境并安装依赖

```bash
# 使用 uv 创建虚拟环境并安装依赖
uv venv
uv pip install -r requirements.txt -r backend/requirements.txt
```

### 2. 激活虚拟环境

```bash
# Linux/Mac
source .venv/bin/activate

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Windows CMD
.venv\Scripts\activate.bat
```

### 3. （可选）使用 uv 直接运行命令

无需激活虚拟环境，uv 可以直接运行：
```bash
# 运行脚本
uv run python scripts/setup.py
uv run python scripts/fetch_data.py --stock 000001
```

## 使用方法

### 1. 初始化数据库

```bash
# 使用 uv run（推荐，无需激活虚拟环境）
uv run python scripts/setup.py

# 或激活虚拟环境后运行
source .venv/bin/activate  # Linux/Mac
python scripts/setup.py
```

### 2. 获取股票数据

#### 获取所有股票数据

```bash
# 获取所有沪深主板股票的历史数据
python scripts/fetch_data.py --market main

# 获取指定日期范围的数据
python scripts/fetch_data.py --market main --start-date 20240101 --end-date 20241231
```

#### 获取单只股票数据

```bash
# 获取单只股票的数据
python scripts/fetch_data.py --stock 000001
```

### 3. 策略分析

#### 列出所有可用策略

```bash
# 列出所有已注册的策略
python scripts/run_strategy.py --list
```

#### 运行指定策略

```bash
# 运行指定策略
python scripts/run_strategy.py --strategy "MA策略" --stock 000001

# 运行策略并指定日期范围
python scripts/run_strategy.py --strategy "MA策略" --stock 000001 --start-date 20240101 --end-date 20241231

# 运行策略并传递自定义参数（MA策略示例）
python scripts/run_strategy.py --strategy "MA策略" --stock 000001 --strategy-args '{"short_period": 10, "long_period": 30}'
```

#### 运行所有策略

```bash
# 运行所有已注册的策略
python scripts/run_strategy.py --all --stock 000001
```

**当前可用的策略：**
- **MA Strategy**：移动平均策略，基于短期和长期移动平均线的交叉点生成买卖信号

### 策略分析和统计

分析策略表现并计算统计指标（成功率、累计收益率等）：

```bash
# 分析策略并显示统计结果
python scripts/analyze_strategy.py --strategy "MA Strategy" --stock 000001 --start-date 20240101 --end-date 20241231

# 分析策略并生成带信号的K线图
python scripts/analyze_strategy.py --strategy "MA Strategy" --stock 000001 --plot

# 指定初始资金
python scripts/analyze_strategy.py --strategy "MA Strategy" --stock 000001 --initial-capital 200000
```

**统计指标包括：**
- 总信号数（买入/卖出）
- 交易统计（总交易次数、盈利交易、胜率）
- 收益率（累计收益率、总收益、最终资金）
- 风险指标（最大回撤）

策略结果会导出为CSV文件，保存在 `data/strategy_results/{策略名称}/` 目录下，每种策略的结果单独存放。

### 4. 数据导出

导出股票数据为CSV文件：

```bash
# 导出单只股票的数据
python scripts/export_data.py --stock 000001

# 导出指定日期范围的数据
python scripts/export_data.py --stock 000001 --start-date 20240101 --end-date 20241231

# 导出所有股票的数据
python scripts/export_data.py --all
```

### 5. K线图可视化

生成交互式K线图（HTML格式）：

```bash
# 生成K线图（HTML文件）
python scripts/plot_kline.py --stock 000001 --start-date 20240101 --end-date 20241231

# 生成带均线的K线图
python scripts/plot_kline.py --stock 000001 --ma --ma-periods "5,10,20,30"

# 指定输出路径
python scripts/plot_kline.py --stock 000001 --output data/images/custom_kline.html
```

**注意**：生成的HTML文件可以使用浏览器打开，支持交互式缩放、平移等操作。

### 6. 策略框架演示

查看策略框架使用示例：

```bash
# 演示策略框架
python scripts/demo_strategy.py

# 查看示例策略代码
python scripts/demo_strategy.py --create-example
```

## 示例脚本说明

项目提供了以下示例脚本，展示如何使用各个功能模块：

- **scripts/export_data.py** - 数据导出示例
  - 支持单只股票或所有股票的数据导出
  - 支持指定日期范围导出
  
- **scripts/plot_kline.py** - K线图生成示例
  - 使用Bokeh生成交互式HTML图表
  - 支持均线叠加
  - 图表保存在 `data/images/` 目录
  
- **scripts/demo_strategy.py** - 策略框架使用示例
  - 演示如何加载和使用策略插件
  - 展示策略插件代码结构

## 配置说明

项目配置位于 `src/config/settings.py`，主要配置项包括：

- 数据库路径
- 日志配置
- 数据源配置（akshare）
- 策略插件路径
- 数据导出目录
- 图表输出目录（`data/images/`）

可以通过环境变量或修改配置文件来调整设置。

## 开发计划

详细开发计划请参考 [PROJECT_PLAN.md](PROJECT_PLAN.md)。

## 许可证

本项目采用 MIT 许可证。

## 贡献指南

欢迎提交 Issue 和 Pull Request。

## 注意事项

- 本项目仅用于学习和研究目的
- 数据来源于 akshare，使用时请遵守相关数据源的使用条款
- 投资有风险，策略分析结果仅供参考，不构成投资建议
- **建议在虚拟环境中运行项目**，避免污染系统Python环境
