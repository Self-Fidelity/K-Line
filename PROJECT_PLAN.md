# K-Line 项目规划文档

## 1. 项目概述

### 1.1 项目目标
构建一个中国股市每日股票数据获取和存储系统，支持自动定时更新，但目前测试阶段由手动触发来进行。会制作等多种策略来评估分析股票走势。结果目前会输出成一个CSV文件供阅览，后续可能还有其它结果输出方式。


### 1.2 核心功能
- ✅ 获取中国A股每日股票数据
- ✅ 数据本地存储（支持增量更新）
- ✅ 定时自动更新数据
- ✅ 数据查询和导出功能
- 多种策略分析股票，各个策略以插件的形式发挥作用，策略分析结果可输出

---

## 2. 技术选型

### 2.1 数据源
**akshare**
- ✅ 免费开源，无需注册
- ✅ 数据源丰富（东方财富、同花顺等）
- ✅ 支持沪深A股、历史数据
- ✅ 社区活跃，维护良好
- ✅ 接口简单易用


### 2.2 技术栈
- **Python**: 3.12.3
- **依赖管理**: uv
- **数据获取**: akshare
- **定时任务**: APScheduler 或 schedule
- **数据存储**: 
  - SQLite
- **日志**: logging
- **配置管理**: configparser 或 python-dotenv

### 2.3 开发工具
- Git 版本控制
- 代码格式化: black
- 代码检查: flake8 或 pylint
- 类型检查: mypy（可选）

---

## 3. 项目结构（建议）

```
K-Line/
├── .cursor/                 # Cursor IDE 配置
│   └── rules/
├── .git/                    # Git 仓库
├── .gitignore              # Git 忽略文件
├── pyproject.toml          # Poetry 配置文件
├── README.md               # 项目说明
├── PROJECT_PLAN.md         # 项目规划文档（本文件）
│
├── src/                    # 源代码目录
│   ├── __init__.py
│   ├── config/             # 配置模块
│   │   ├── __init__.py
│   │   └── settings.py     # 配置管理
│   ├── data_fetcher/       # 数据获取模块
│   │   ├── __init__.py
│   │   ├── fetcher.py      # 核心数据获取类
│   │   └── stock_list.py   # 股票列表管理
│   ├── data_storage/       # 数据存储模块
│   │   ├── __init__.py
│   │   ├── storage.py      # 存储接口
│   │   └── sqlite_storage.py  # SQLite 实现
│   ├── scheduler/          # 定时任务模块
│   │   ├── __init__.py
│   │   └── scheduler.py    # 任务调度
│   └── utils/              # 工具模块
│       ├── __init__.py
│       ├── logger.py       # 日志配置
│       └── date_utils.py   # 日期工具
│
├── data/                   # 数据存储目录（可选，如使用文件存储）
│   ├── csv/               # CSV 数据
│   └── database/          # SQLite 数据库文件
│
├── logs/                   # 日志目录
│
├── scripts/                # 脚本目录
│   ├── fetch_data.py      # 手动执行数据获取
│   └── setup.py           # 初始化脚本
│
└── tests/                  # 测试目录（可选）
    ├── __init__.py
    └── test_fetcher.py
```

---

## 4. 功能模块设计

### 4.1 数据获取模块（data_fetcher）
**功能：**
- 获取股票列表（全部A股或指定股票）
- 获取单只/批量股票的日K线数据
- 支持历史数据获取
- 错误处理和重试机制

**主要接口：**
```python
class StockDataFetcher:
    def get_stock_list(self, market: str = 'all') -> List[Dict]
    def get_daily_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame
    def get_latest_data(self, stock_code: str) -> pd.DataFrame
    def batch_fetch(self, stock_codes: List[str], date: str) -> Dict[str, pd.DataFrame]
```

### 4.2 数据存储模块（data_storage）
**功能：**
- 数据入库（支持增量更新）
- 数据查询
- 数据导出（CSV/JSON）
- 数据完整性检查

**存储字段（日K线数据）：**
- 股票代码 (stock_code)
- 交易日期 (trade_date)
- 开盘价 (open)
- 收盘价 (close)
- 最高价 (high)
- 最低价 (low)
- 成交量 (volume)
- 成交额 (amount)
- 涨跌幅 (pct_chg)
- 更新时间 (update_time)

**主要接口：**
```python
class DataStorage:
    def save_daily_data(self, data: pd.DataFrame, stock_code: str) -> bool
    def get_daily_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame
    def get_latest_date(self, stock_code: str) -> str
    def check_data_exists(self, stock_code: str, trade_date: str) -> bool
```

### 4.3 定时任务模块（scheduler）
TODO

---

## 5. 数据流程

### 5.1 初始数据获取
```
1. 获取股票列表
2. 遍历股票列表
3. 获取每只股票的历史数据（可选）
4. 存储到本地数据库
```

### 5.2 每日自动更新
TODO

---

## 6. 待确认问题

### 6.1 数据范围
- [ ] 获取全部A股数据，还是特定股票？
- 都需要，技能获取全部A股数据来进行分析，也可以获取特定股票来进行分析
- [ ] 是否需要回填历史数据？如果需要，回填多长时间？
 - 第一次数据初始化得时候最好是把所有目前在市的数据都获取到，后续则检测已有数据到哪儿，按需获取新数据
- [ ] 需要哪些市场？（沪深主板、创业板、科创板等）
 - 目前只获取沪深主板，当然后续可能添加其它板块，可以不设置得太死，尽量灵活开发

### 6.2 存储方式
- [ ] SQLite（推荐，轻量级）
- [ ] 是否需要数据压缩或归档？
 - 数据压缩暂时不考虑；需要一个合理的归档方式，你可以考虑下

### 6.3 更新策略
 - 目前开发测试阶段，只需要我手动来更新

### 6.4 数据字段
- [ ] 基础字段：开盘、收盘、最高、最低、成交量、成交额
- [ ] 是否还需要：换手率、涨跌幅、市盈率等扩展字段？
- [ ] 是否需要复权价格？
 - 使用后复权

### 6.5 运行环境
- [ ] 本地运行（Windows）
- [ ] 是否需要部署到服务器？
 现阶段本地运行，后续考虑部署到服务器上运行

### 6.6 其他功能
- [ ] 是否需要数据可视化（K线图）？
 - 需要数据可以化，当然现阶段暂时只需要K线图，后续可能会随着各种分析指标的加入，添加其它的可视化项目
- [ ] 是否需要数据导出功能？
 - 需要数据导出的功能，包括具体的股票数据和各种策略的分析结果
- [ ] 是否需要数据质量检查（异常值检测）？
 - 暂时不需要数据质量检查，以数据源获取到的数据为准
- [ ] 是否需要数据备份机制？
 - 暂时不用数据备份

---

## 7. 开发计划（待确认）

### 阶段一：基础框架搭建
1. 项目结构创建
2. uv 依赖配置
3. 配置管理模块
4. 日志模块

### 阶段二：核心功能开发
1. 数据获取模块
2. 数据存储模块（SQLite）
3. 基础测试

### 阶段三：自动更新功能
1. 定时任务模块
2. 交易日判断
3. 增量更新逻辑

### 阶段四：优化和扩展
1. 错误处理优化
2. 性能优化
3. 文档完善
4. 可选功能（导出、可视化等）

---

## 8. 下一步行动

请确认以上规划，特别是"待确认问题"部分。确认后，我们可以开始：
1. 创建项目结构
2. 配置 Poetry 依赖
3. 搭建基础框架
4. 逐步实现核心功能
