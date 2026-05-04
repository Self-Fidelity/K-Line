# K-Line 项目发展路线图

> 本文档记录已确认但尚未实现的功能规划。按 Phase 分期，每期内按优先级排序。
> 当前数据层架构已预留接口，未来迭代时参照本文档执行。

---

## Phase 1：多数据源支持（已完成）

**状态**：已完成 ✅  
**目标**：支持 AkShare + Tushare 双数据源切换，数据物理隔离（同表不同 source 标记）。

### 已完成
- [x] Provider 抽象层（BaseDataProvider / AkShareProvider / TushareProvider）
- [x] Tushare token Web 配置与数据库安全存储
- [x] 前端数据源切换面板
- [x] 数据源连接测试 API

### 本次待完成
- [x] `stock_daily_kline` 表增加 `data_source` 字段，UNIQUE 改为 `(stock_code, trade_date, data_source)`
- [x] `save_daily_data` / `get_daily_data` 接口增加 `data_source` 参数透传
- [x] SQLite + PostgreSQL 双存储引擎适配
- [x] 管理员可选"清空旧数据源历史数据"（`clear_data_by_source` API 已实现）

---

## Phase 2：扩展指标系统（全市场计算 + 持久化检验）

**状态**：规划中  
**触发条件**：用户需要自定义 RSR 等市场面指标，且要求可回溯检验  
**预计工作量**：2-3 天

### 核心需求
1. 每晚定时任务计算全市场 5000+ 只股票的扩展指标（10~20 个）
2. 每只股票的每个指标值都要落库，方便人工 SQL 检验
3. 指标用于选股筛选（后台计算 → 输出入选名单）

### 新增数据库表

```sql
CREATE TABLE stock_daily_indicators (
    stock_code TEXT NOT NULL,
    trade_date TEXT NOT NULL,
    data_source TEXT NOT NULL DEFAULT 'akshare',
    
    -- 市场面/统计面指标（预留 20 列，现用 10，余 10 备用）
    rsr REAL,                           -- 相对强弱排名 (Relative Strength Rank)
    relative_strength REAL,             -- 相对强弱值
    momentum_score REAL,                -- 动量得分
    volatility_20d REAL,                -- 20 日波动率
    volume_ratio REAL,                  -- 量比
    ma_bias REAL,                       -- 均线偏离度
    rsi_14 REAL,                        -- RSI14（与策略实时计算的独立存档）
    macd_signal REAL,                   -- MACD 信号线（独立存档）
    boll_position REAL,                 -- 布林带位置 (0~1)
    trend_strength REAL,                -- 趋势强度
    custom_1 REAL,                      -- 预留扩展位
    custom_2 REAL,
    custom_3 REAL,
    custom_4 REAL,
    custom_5 REAL,
    custom_6 REAL,
    custom_7 REAL,
    custom_8 REAL,
    custom_9 REAL,
    custom_10 REAL,
    
    update_time TEXT,
    PRIMARY KEY (stock_code, trade_date, data_source)
);

-- 查询索引
CREATE INDEX idx_indicators_by_stock 
ON stock_daily_indicators(stock_code, data_source, trade_date);

CREATE INDEX idx_indicators_by_date 
ON stock_daily_indicators(trade_date, data_source, rsr);
```

### 与现有实时指标（MACD/KDJ/RSI）的关系

| 维度 | 现有策略指标（MACD/KDJ/RSI） | 扩展指标（RSR 等） |
|------|----------------------------|-------------------|
| 计算时机 | 策略 `analyze()` **运行时实时算** | 每晚定时任务**后台预计算** |
| 输入数据 | 单只股票的 OHLCV | 全市场横截面数据（需排名、分位） |
| 存储位置 | **不存储**，内存计算后立即使用 | **`stock_daily_indicators` 表持久化** |
| 用途 | 策略信号判断（买入/卖出/持有） | 选股筛选 + 人工检验 + 策略输入 |
| 冲突 | **无冲突**，两者互补 | — |

**结论**：扩展指标是 K 线数据的**衍生层**，策略可以读取扩展指标作为额外输入，两者完全独立。

### 定时任务流程

```
每晚 19:30 定时任务启动
  ↓
1. 下载日K线 → stock_daily_kline
  ↓
2. 读取全市场 K 线（5000 只）到内存 DataFrame
  ↓
3. Python 计算扩展指标（10~20 个）
   - RSR：按涨幅排序计算分位
   - 动量：N 日收益率
   - 波动率：标准差
   - ...
  ↓
4. 批量写入 stock_daily_indicators（5000 条/天）
  ↓
5. 基于指标筛选股票（SQL WHERE 条件）
   例：SELECT stock_code FROM stock_daily_indicators 
       WHERE trade_date = '20240101' 
         AND rsr > 0.8 
         AND momentum_score > 1.5
  ↓
6. 筛选结果写入 daily_screening 表（可选）
```

### 人工检验方式

```sql
-- 查某只股票历史指标走势
SELECT trade_date, rsr, momentum_score, volatility_20d
FROM stock_daily_indicators
WHERE stock_code = '000001' AND data_source = 'akshare'
ORDER BY trade_date;

-- 查某天全市场 RSR 排名
SELECT stock_code, rsr
FROM stock_daily_indicators
WHERE trade_date = '20240101' AND data_source = 'akshare'
ORDER BY rsr DESC
LIMIT 100;
```

---

## Phase 3：逐笔成交数据存储（Tick Data）

**状态**：规划中  
**触发条件**：用户上传全市场逐笔成交 ZIP 文件  
**预计工作量**：3-4 天

### 核心需求
1. 用户每天收盘后上传一个 ZIP（内含全市场所有个股的逐笔 CSV）
2. 系统解压、按股票分目录保存
3. 从逐笔数据预计算统计特征（2sigma 边界、VWAP、Delta 等），结果写入 PostgreSQL
4. 原始逐笔 CSV 保留在文件系统，方便人工打开检验

### 存储架构

```
data/
├── database/                    ← PostgreSQL（业务数据 + K线 + 统计特征）
│
├── tick/
│   ├── upload/                  ← 用户上传的 ZIP 临时存放
│   │   └── 20240101_all_tick.zip
│   │
│   ├── raw/                     ← 解压后按股票分 CSV
│   │   ├── 000001/
│   │   │   ├── 20240101.csv     ← 平安银行 2024-01-01 逐笔
│   │   │   └── 20240102.csv
│   │   └── 600000/
│   │       ├── 20240101.csv     ← 浦发银行 2024-01-01 逐笔
│   │       └── 20240102.csv
│   │
│   └── derived/                 ← 从 CSV 预计算的中间结果（JSON）
│       └── 000001/
│           └── 20240101_stats.json
│
└── orderflow/                   ← 订单流预计算结果（Phase 4 使用，现在空着）
    └── 000001/
        ├── 20240101_footprint.json
        └── 20240101_profile.json
```

### 后端 API 接口（预留）

```python
# POST /api/admin/tick/upload
# 接收：multipart/form-data，ZIP 文件
# 处理：解压 → 校验 CSV 格式 → 移动到 data/tick/raw/{stock_code}/
# 返回：{uploaded_stocks: 5128, total_rows: 25000000, status: 'success'}

# GET /api/tick/{stock_code}/{trade_date}
# 返回：该股票该日的 2sigma / VWAP / Delta 统计摘要
# 数据源：PostgreSQL tick_summary 表
```

### 逐笔统计特征表（PostgreSQL）

```sql
CREATE TABLE tick_summary (
    stock_code TEXT NOT NULL,
    trade_date TEXT NOT NULL,
    data_source TEXT NOT NULL DEFAULT 'akshare',
    
    -- 价格统计
    price_mean REAL,              -- 均价
    price_std REAL,               -- 标准差
    sigma_upper REAL,             -- mean + 2*std
    sigma_lower REAL,             -- mean - 2*std
    vwap REAL,                    -- 成交量加权均价
    
    -- 订单流统计
    total_volume INTEGER,         -- 总成交量（股）
    buy_volume INTEGER,           -- 主动买量
    sell_volume INTEGER,          -- 主动卖量
    delta INTEGER,                -- 买 - 卖
    
    -- 时间分布
    morning_volume INTEGER,       -- 09:30-11:30 成交量
    afternoon_volume INTEGER,     -- 13:00-15:00 成交量
    
    update_time TEXT,
    PRIMARY KEY (stock_code, trade_date, data_source)
);
```

### 处理流程

```
用户上传 20240101_all_tick.zip
  ↓
后端接收 → 保存到 data/tick/upload/
  ↓
定时任务检测到新 ZIP
  ↓
解压到 data/tick/temp/20240101/
  ↓
遍历 ZIP 内 CSV 文件
  000001.csv → data/tick/raw/000001/20240101.csv
  600000.csv → data/tick/raw/600000/20240101.csv
  ...
  ↓
删除临时文件和 ZIP（或保留 ZIP 作为备份）
  ↓
读取每个 CSV → 计算统计特征
  ↓
写入 tick_summary（PostgreSQL）
```

### 人工检验方式

| 想查什么 | 方式 |
|---------|------|
| 平安银行 2024-01-01 逐笔原数据 | 直接打开 `data/tick/raw/000001/20240101.csv` |
| 平安银行当天的 2sigma 边界 | SQL `SELECT * FROM tick_summary WHERE stock_code='000001'` |
| 系统 VWAP 算得对不对 | SQL 查 `tick_summary`，或自己对 CSV 用 pandas 算一遍对比 |

---

## Phase 4：订单流界面（Order Flow）

**状态**：远期规划  
**触发条件**：Phase 3 稳定运行，用户需要可视化分析  
**预计工作量**：5-7 天（前端为主）

### 核心功能

| 功能 | 说明 | 数据源 |
|------|------|--------|
| Footprint 图表 | 每个价格档位的主动买/卖量矩阵 | 预计算 JSON |
| Volume Profile | 成交量按价格分布（POC、VAH、VAL） | 预计算 JSON |
| Delta 曲线 | 累计买单 - 卖单 | 预计算 JSON |
| 2sigma 边界线 | 正态分布上下轨 | tick_summary 表 |

### 预计算策略

> 订单流数据量大，**不能实时算**，必须每晚预计算。

```python
# 每晚定时任务（Phase 3 之后扩展）
for stock_code in all_stocks:
    df = read_tick_csv(stock_code, date)      # 读原始逐笔
    
    footprint = calc_footprint(df)             # 计算 footprint 矩阵
    save_json(footprint, f"data/orderflow/{stock_code}/{date}_footprint.json")
    
    profile = calc_volume_profile(df)          # 计算 volume profile
    save_json(profile, f"data/orderflow/{stock_code}/{date}_profile.json")
```

### 前端展示

- TradingView Lightweight Charts 自定义系列
- 或独立 React/Vue 订单流组件
- 盘中不看，只展示已收盘日期的预计算结果

---

## 附录：技术选型不变更项

以下决策已在讨论中确认，未来迭代时**不重新讨论**：

| 决策 | 内容 |
|------|------|
| 数据库（生产） | PostgreSQL（Docker 部署） |
| 数据库（开发） | SQLite（本地 `start.bat`） |
| K 线存储 | PostgreSQL `stock_daily_kline` 表 |
| 指标存储 | PostgreSQL `stock_daily_indicators` 表（Phase 2） |
| 逐笔原始数据 | 文件系统 CSV（`data/tick/raw/`） |
| 逐笔统计特征 | PostgreSQL `tick_summary` 表（Phase 3） |
| 订单流聚合数据 | 文件系统 JSON（`data/orderflow/`）（Phase 4） |
| 数据源标记 | 所有市场数据表均含 `data_source` 字段（akshare/tushare） |

---

*文档版本: v1.0*  
*创建日期: 2026-05-04*  
*最后更新: 2026-05-04*
