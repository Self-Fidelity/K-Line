# 数据获取策略详细设计文档

本文档详细说明数据获取的策略和实现方案。

## 1. 数据获取策略概述

系统采用两种不同的数据获取策略，分别针对非自选股票和用户自选股票：

### 1.1 非用户自选股票数据（日K线）

- **获取频率**: 每日一次
- **获取时间**: 交易日结束后（建议15:30）
- **数据范围**: 仅获取新一天的数据（增量更新）
- **数据存储**: `stock_daily_kline` 表
- **用途**: 系统级数据分析、策略回测

### 1.2 用户自选股票数据（分时K线）

- **获取频率**: 交易时间内实时获取（根据分时周期）
- **分时周期**: 1, 5, 15, 30, 60分钟（用户可设置）
- **数据范围**: 获取最新分时K线数据（增量更新）
- **数据存储**: `stock_minute_kline` 表
- **用途**: 实时监控、短期交易分析

## 2. 数据库设计

### 2.1 日K线数据表（已有）

```sql
CREATE TABLE stock_daily_kline (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_code TEXT NOT NULL,
    trade_date TEXT NOT NULL,
    open REAL NOT NULL,
    close REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    volume REAL NOT NULL,
    amount REAL,
    pct_chg REAL,
    change REAL,
    turnover REAL,
    update_time TEXT NOT NULL,
    UNIQUE(stock_code, trade_date)
);
```

### 2.2 分时K线数据表（新增）

```sql
CREATE TABLE stock_minute_kline (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_code TEXT NOT NULL,
    trade_datetime TEXT NOT NULL,  -- 交易日期时间，格式：'20240101 0930'
    period TEXT NOT NULL,  -- 周期：'1', '5', '15', '30', '60'
    open REAL NOT NULL,
    close REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    volume REAL NOT NULL,
    amount REAL,
    update_time TEXT NOT NULL,
    UNIQUE(stock_code, trade_datetime, period)
);

CREATE INDEX idx_minute_stock_code ON stock_minute_kline(stock_code);
CREATE INDEX idx_minute_datetime ON stock_minute_kline(trade_datetime);
CREATE INDEX idx_minute_period ON stock_minute_kline(period);
CREATE INDEX idx_minute_stock_datetime ON stock_minute_kline(stock_code, trade_datetime, period);
```

### 2.3 自选股票表（更新）

```sql
CREATE TABLE watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    stock_code TEXT NOT NULL,
    period TEXT NOT NULL DEFAULT '1',  -- 分时周期：'1', '5', '15', '30', '60'
    created_at TEXT NOT NULL,
    updated_at TEXT,
    UNIQUE(user_id, stock_code),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

## 3. 数据获取实现

### 3.1 日K线数据获取（非自选股票）

#### 实现方法

使用现有的 `StockDataFetcher.get_daily_data()` 方法，通过定时任务每日执行。

#### 定时任务配置

```python
# 每日一次，交易日结束后（15:30）
scheduler.add_job(
    fetch_daily_data_all_stocks,
    'cron',
    day_of_week='mon-fri',
    hour=15,
    minute=30,
    timezone='Asia/Shanghai'
)
```

#### 实现逻辑

```python
async def fetch_daily_data_all_stocks():
    """获取所有非自选股票的日K线数据（仅获取新一天的数据）"""
    # 1. 获取所有股票列表
    stock_list = await get_all_stocks()
    
    # 2. 获取所有自选股票代码（排除）
    watchlist_stocks = await get_all_watchlist_stocks()
    watchlist_codes = {stock['stock_code'] for stock in watchlist_stocks}
    
    # 3. 获取非自选股票列表
    non_watchlist_stocks = [s for s in stock_list if s['code'] not in watchlist_codes]
    
    # 4. 对每个股票获取最新数据日期
    # 5. 仅获取新一天的数据（增量更新）
    for stock in non_watchlist_stocks:
        stock_code = stock['code']
        latest_date = await storage.get_latest_date(stock_code)
        
        # 计算需要获取的日期范围（从最新日期+1到今天）
        start_date = (latest_date + timedelta(days=1)).strftime('%Y%m%d') if latest_date else None
        end_date = datetime.now().strftime('%Y%m%d')
        
        # 获取数据
        data = fetcher.get_daily_data(stock_code, start_date=start_date, end_date=end_date)
        
        # 保存数据（自动去重）
        if not data.empty:
            storage.save_daily_data(data, stock_code)
```

### 3.2 分时K线数据获取（自选股票）

#### akshare API使用

akshare提供分钟K线数据接口：`ak.stock_zh_a_hist_min_em()` 或 `ak.stock_zh_a_hist_min_em(symbol, period)`

```python
import akshare as ak

# 获取1分钟K线数据
df = ak.stock_zh_a_hist_min_em(symbol="000001", period="1")

# period可选值：'1', '5', '15', '30', '60'
# 返回字段：时间, 开盘, 收盘, 最高, 最低, 成交量, 成交额
```

#### 扩展StockDataFetcher

```python
class StockDataFetcher:
    """股票数据获取器（扩展支持分时数据）"""
    
    def get_minute_data(
        self,
        stock_code: str,
        period: str = "1",  # '1', '5', '15', '30', '60'
        start_datetime: str = None,  # 格式：'20240101 0930'
        end_datetime: str = None,
    ) -> pd.DataFrame:
        """
        获取单只股票的分时K线数据
        
        Args:
            stock_code: 股票代码（如 '000001'）
            period: 分时周期，'1', '5', '15', '30', '60'
            start_datetime: 开始日期时间（格式：'20240101 0930'）
            end_datetime: 结束日期时间（格式：'20240101 1500'）
        
        Returns:
            分时K线数据 DataFrame
        """
        # 使用akshare获取分时数据
        # 数据标准化
        # 返回DataFrame
        pass
```

#### 定时任务配置（按周期分组）

```python
# 1分钟周期
scheduler.add_job(
    fetch_watchlist_minute_data,
    'cron',
    day_of_week='mon-fri',
    hour='9-15',
    minute='*',  # 每分钟
    kwargs={'period': '1'},
    timezone='Asia/Shanghai'
)

# 5分钟周期
scheduler.add_job(
    fetch_watchlist_minute_data,
    'cron',
    day_of_week='mon-fri',
    hour='9-15',
    minute='*/5',
    kwargs={'period': '5'},
    timezone='Asia/Shanghai'
)

# 15分钟周期
scheduler.add_job(
    fetch_watchlist_minute_data,
    'cron',
    day_of_week='mon-fri',
    hour='9-15',
    minute='*/15',
    kwargs={'period': '15'},
    timezone='Asia/Shanghai'
)

# 30分钟周期
scheduler.add_job(
    fetch_watchlist_minute_data,
    'cron',
    day_of_week='mon-fri',
    hour='9-15',
    minute='*/30',
    kwargs={'period': '30'},
    timezone='Asia/Shanghai'
)

# 60分钟周期
scheduler.add_job(
    fetch_watchlist_minute_data,
    'cron',
    day_of_week='mon-fri',
    hour='9-15',
    minute='0',  # 每小时
    kwargs={'period': '60'},
    timezone='Asia/Shanghai'
)
```

#### 实现逻辑

```python
async def fetch_watchlist_minute_data(period: str):
    """获取自选股票的分时K线数据（按周期）"""
    # 1. 获取所有设置该周期的自选股票
    watchlist_items = await get_watchlist_by_period(period)
    
    # 2. 对每个股票获取最新数据时间
    # 3. 仅获取新的分时数据（增量更新）
    for item in watchlist_items:
        stock_code = item['stock_code']
        latest_datetime = await storage.get_latest_minute_datetime(stock_code, period)
        
        # 计算需要获取的时间范围
        # 获取数据
        data = fetcher.get_minute_data(stock_code, period=period, ...)
        
        # 保存数据（自动去重）
        if not data.empty:
            storage.save_minute_kline(data, stock_code, period)
```

## 4. 数据存储实现

### 4.1 扩展SQLiteStorage

```python
class SQLiteStorage(DataStorage):
    """SQLite存储（扩展支持分时数据）"""
    
    # 现有的日K线方法
    def save_daily_data(self, data: pd.DataFrame, stock_code: str) -> bool
    def get_daily_data(self, stock_code: str, start_date: str = None, end_date: str = None) -> pd.DataFrame
    
    # 新增分时K线方法
    def save_minute_kline(self, data: pd.DataFrame, stock_code: str, period: str) -> bool
    def get_minute_kline(self, stock_code: str, period: str, start_datetime: str = None, end_datetime: str = None) -> pd.DataFrame
    def get_latest_minute_datetime(self, stock_code: str, period: str) -> Optional[str]
```

### 4.2 数据去重和增量更新

- 使用 `UNIQUE(stock_code, trade_datetime, period)` 约束确保数据不重复
- 使用 `INSERT OR IGNORE` 或 `INSERT OR REPLACE` 实现增量更新
- 获取数据前先查询最新时间，仅获取新数据

## 5. API设计

### 5.1 日K线数据API

```python
GET /api/data/stocks/{stock_code}/kline
Query Parameters:
    - start_date: 开始日期（可选）
    - end_date: 结束日期（可选）

POST /api/data/fetch
Body: {
    "stock_code": "000001"  # 可选，不传则获取所有非自选股票
}
```

### 5.2 分时K线数据API

```python
GET /api/data/stocks/{stock_code}/minute-kline
Query Parameters:
    - period: 分时周期（必需）：'1', '5', '15', '30', '60'
    - start_datetime: 开始日期时间（可选，格式：'20240101 0930'）
    - end_datetime: 结束日期时间（可选，格式：'20240101 1500'）

GET /api/watchlist/{stock_code}/minute-kline
Query Parameters:
    - period: 分时周期（可选，默认使用用户设置）
    - start_datetime: 开始日期时间（可选）
    - end_datetime: 结束日期时间（可选）
```

### 5.3 自选股票API（更新）

```python
POST /api/watchlist
Body: {
    "stock_code": "000001",
    "period": "5"  # 分时周期：'1', '5', '15', '30', '60'
}

PUT /api/watchlist/{stock_code}
Body: {
    "period": "15"  # 更新分时周期
}
```

## 6. 前端展示

### 6.1 自选股票列表

- 显示股票代码、名称、分时周期
- 显示最新价格、涨跌幅（从分时数据获取）

### 6.2 分时K线图表

- 支持按周期切换（1, 5, 15, 30, 60分钟）
- 使用Bokeh绘制分时K线图
- 支持时间范围选择

## 7. 注意事项

1. **数据量控制**: 分时数据量较大，需要合理的数据清理策略（如保留最近N天的数据）
2. **API调用频率**: 注意akshare API的调用频率限制
3. **交易时间判断**: 只在交易时间获取分时数据
4. **数据一致性**: 确保同一股票的多个周期数据一致
5. **性能优化**: 分时数据查询需要考虑索引优化
6. **错误处理**: 网络错误、API错误需要重试机制

## 8. 数据清理策略（可选）

为控制数据库大小，可以考虑：

```python
# 定期清理过期的分时数据（保留最近30天）
async def cleanup_old_minute_data(days: int = 30):
    """清理指定天数前的分时数据"""
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
    # 删除指定日期之前的数据
```
