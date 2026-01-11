# WebUI 高级功能设计文档

本文档详细说明用户角色、策略固化、自选股票和实时监控等高级功能的实现设计。

## 1. 用户角色系统

### 角色定义

- **普通用户 (user)**: 默认角色
  - 可以使用系统策略进行分析
  - 可以创建和管理自己的自定义策略
  - 可以管理自选股票（受数量限制）
  - 可以设置监控警报
  
- **超级管理员 (admin)**: 系统管理角色
  - 所有普通用户权限
  - 用户管理（创建、编辑、删除用户）
  - 修改用户角色
  - 设置用户自选股数量限制
  - 策略固化（将用户策略变为系统策略）
  - 系统配置管理

### 数据库设计

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',  -- 'user' 或 'admin'
    max_watchlist_count INTEGER DEFAULT 20,  -- 自选股数量限制
    is_active BOOLEAN DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT
);

CREATE TABLE user_settings (
    user_id INTEGER PRIMARY KEY,
    notification_email TEXT,  -- 通知邮箱
    notification_enabled BOOLEAN DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 权限控制实现

- JWT token中包含用户ID和角色信息
- API路由使用依赖注入进行权限检查
- 前端路由守卫根据角色限制访问
- 前端UI根据角色显示/隐藏功能

## 2. 策略固化功能

### 功能描述

管理员可以将用户开发的策略固化为系统策略，使所有用户都可以使用该策略。

### 实现流程

1. 用户创建并测试自定义策略
2. 管理员查看待固化的策略列表
3. 管理员审核策略（查看源码、测试功能）
4. 确认固化后：
   - 将策略文件从 `data/custom_strategies/{user_id}/` 复制到 `src/strategy/plugins/`
   - 更新数据库标记策略为系统策略
   - 原用户策略文件保留作为备份
   - 策略对所有用户可见可用

### 数据库设计

```sql
ALTER TABLE custom_strategies ADD COLUMN promoted_at TEXT;
ALTER TABLE custom_strategies ADD COLUMN promoted_by INTEGER;  -- 管理员ID
ALTER TABLE custom_strategies ADD COLUMN is_system BOOLEAN DEFAULT 0;
```

### API设计

- `GET /api/strategy/pending-promotion` - 获取待固化策略列表（仅管理员）
- `POST /api/strategy/custom/{strategy_id}/promote` - 固化策略（仅管理员）

## 3. 自选股票功能

### 功能描述

用户可以选择关注的股票，系统实时获取这些股票的分时K线数据。

### 数据库设计

```sql
CREATE TABLE watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    stock_code TEXT NOT NULL,
    period TEXT NOT NULL DEFAULT '1',  -- 分时周期：'1', '5', '15', '30', '60'（分钟）
    created_at TEXT NOT NULL,
    UNIQUE(user_id, stock_code),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 分时K线数据表（用于用户自选股票）
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

### 数量限制

- 管理员可以为每个用户设置自选股数量限制
- 默认限制：20只
- 超级管理员可以设置更高的限制（如100只）
- 添加自选股票时检查数量限制

### 数据获取策略

#### 非用户自选股票数据（日K线）
- **获取频率**: 每日一次（交易日结束后，如15:30）
- **数据范围**: 仅获取新一天的数据（增量更新）
- **数据存储**: 存储到 `stock_daily_kline` 表
- **获取方式**: 使用现有的 `StockDataFetcher.get_daily_data()` 方法

#### 用户自选股票数据（分时K线）
- **获取频率**: 交易时间内实时获取（根据分时周期设定）
  - 1分钟周期：每分钟获取
  - 5分钟周期：每5分钟获取
  - 15分钟周期：每15分钟获取
  - 30分钟周期：每30分钟获取
  - 60分钟周期：每60分钟获取
- **数据范围**: 获取最新分时K线数据（增量更新）
- **数据存储**: 存储到 `stock_minute_kline` 表
- **分时周期**: 用户可设置（1, 5, 15, 30, 60分钟），支持修改
- **获取方式**: 使用新的 `StockDataFetcher.get_minute_data()` 方法（akshare的分钟K线API）

### API设计

- `GET /api/watchlist` - 获取用户自选股票列表
- `POST /api/watchlist` - 添加自选股票（包含period参数：1, 5, 15, 30, 60）
- `PUT /api/watchlist/{stock_code}` - 更新自选股票（可修改period）
- `DELETE /api/watchlist/{stock_code}` - 删除自选股票
- `GET /api/watchlist/{stock_code}/minute-kline` - 获取自选股票分时K线数据
- `GET /api/watchlist/limit` - 获取用户自选股数量限制

## 4. 实时监控和邮件提醒

### 功能描述

用户可以设置监控条件，当自选股票的特定策略满足条件时，发送邮件提醒用户。

### 数据库设计

```sql
CREATE TABLE monitor_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    stock_code TEXT NOT NULL,
    strategy_name TEXT NOT NULL,
    strategy_params TEXT,  -- JSON字符串，策略参数
    alert_condition TEXT NOT NULL,  -- 'buy_signal', 'sell_signal', 'price_above', 'price_below', 'return_above' 等
    alert_value REAL,  -- 触发值（如价格阈值）
    is_active BOOLEAN DEFAULT 1,
    last_triggered_at TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE alert_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id INTEGER NOT NULL,
    triggered_at TEXT NOT NULL,
    message TEXT,
    FOREIGN KEY (alert_id) REFERENCES monitor_alerts(id)
);
```

### 监控条件类型

- **buy_signal**: 策略生成买入信号时触发
- **sell_signal**: 策略生成卖出信号时触发
- **price_above**: 当前价格高于设定值时触发
- **price_below**: 当前价格低于设定值时触发
- **return_above**: 策略累计收益率达到设定值时触发

### 监控服务设计

```python
class MonitorService:
    """实时监控服务"""
    
    def __init__(self):
        self.scheduler = APScheduler()
        self.notification_service = NotificationService()
        self.data_service = DataService()
        self.strategy_service = StrategyService()
    
    async def check_alerts(self):
        """检查所有活跃的监控警报"""
        # 1. 获取所有活跃的警报
        alerts = await self.get_active_alerts()
        
        # 2. 按股票代码分组
        stocks_by_code = {}
        for alert in alerts:
            if alert.stock_code not in stocks_by_code:
                stocks_by_code[alert.stock_code] = []
            stocks_by_code[alert.stock_code].append(alert)
        
        # 3. 对每个股票获取最新数据并检查警报
        for stock_code, alerts_list in stocks_by_code.items():
            # 获取最新数据
            latest_data = await self.data_service.get_latest_data(stock_code)
            
            # 对每个警报运行策略分析
            for alert in alerts_list:
                # 运行策略
                strategy_result = await self.strategy_service.analyze(
                    alert.strategy_name,
                    stock_code,
                    **json.loads(alert.strategy_params or '{}')
                )
                
                # 检查是否满足触发条件
                if await self.check_alert_condition(alert, latest_data, strategy_result):
                    # 发送邮件通知
                    await self.notification_service.send_alert_email(
                        user_id=alert.user_id,
                        stock_code=stock_code,
                        strategy_name=alert.strategy_name,
                        alert=alert,
                        latest_data=latest_data,
                        strategy_result=strategy_result
                    )
                    
                    # 更新警报触发时间
                    await self.update_alert_triggered(alert.id)
    
    def start_monitoring(self):
        """启动监控服务"""
        # 在交易时间每隔N分钟执行check_alerts
        self.scheduler.add_job(
            self.check_alerts,
            'cron',
            day_of_week='mon-fri',
            hour='9-15',
            minute='*/1',  # 每分钟检查一次
            timezone='Asia/Shanghai'
        )
        self.scheduler.start()
```

### 邮件通知服务

```python
class NotificationService:
    """邮件通知服务"""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
    
    async def send_alert_email(
        self,
        user_id: int,
        stock_code: str,
        strategy_name: str,
        alert: MonitorAlert,
        latest_data: pd.DataFrame,
        strategy_result: pd.DataFrame
    ):
        """发送警报邮件"""
        # 获取用户邮箱
        user_email = await self.get_user_email(user_id)
        if not user_email:
            return
        
        # 构建邮件内容
        subject = f"股票监控警报: {stock_code} - {strategy_name}"
        body = self._build_email_body(
            stock_code=stock_code,
            strategy_name=strategy_name,
            alert=alert,
            latest_data=latest_data,
            strategy_result=strategy_result
        )
        
        # 发送邮件
        await self._send_email(user_email, subject, body)
    
    def _build_email_body(self, ...) -> str:
        """构建邮件内容（HTML格式）"""
        # 使用Jinja2模板引擎
        # 包含股票代码、策略名称、触发条件、当前数据、建议操作等信息
        pass
```

### 邮件模板设计

邮件内容包含：
- 股票代码和名称
- 策略名称
- 触发条件说明
- 最新价格和涨跌幅
- 策略信号（买入/卖出）
- 建议操作
- 查看详细分析链接

## 5. 定时任务调度

### 使用APScheduler

- 配置交易日判断（排除周末和节假日）
- 自选股票数据获取任务（交易时间执行）
- 监控警报检查任务（交易时间执行）
- 支持任务暂停、恢复、手动触发

### 任务配置

```python
# 自选股票数据获取任务
scheduler.add_job(
    fetch_watchlist_data,
    'cron',
    day_of_week='mon-fri',
    hour='9-15',  # 交易时间
    minute='*/5',  # 每5分钟
    timezone='Asia/Shanghai'
)

# 监控警报检查任务
scheduler.add_job(
    check_monitor_alerts,
    'cron',
    day_of_week='mon-fri',
    hour='9-15',
    minute='*/1',  # 每分钟
    timezone='Asia/Shanghai'
)
```

### 交易日判断

- 使用交易日历API或静态列表
- 排除周末（周六、周日）
- 排除法定节假日
- 仅在工作日的交易时间执行任务

## 6. 管理员面板功能

### 用户管理

- 用户列表（搜索、筛选、分页）
- 创建用户（用户名、邮箱、密码、角色）
- 编辑用户信息
- 删除用户
- 修改用户角色（user/admin）
- 设置用户自选股数量限制
- 启用/禁用用户账户

### 策略固化管理

- 查看待固化的策略列表（用户自定义策略）
- 预览策略源码（只读）
- 测试策略功能
- 确认固化策略
- 查看固化历史记录
- 撤销固化（将系统策略恢复为用户策略）

### 系统配置

- 全局自选股数量限制（默认值）
- 数据获取频率配置（分钟）
- 监控检查频率配置（分钟）
- SMTP邮件服务器配置
- 系统日志查看

## 7. 前端页面设计

### 自选股票管理页面 (`WatchlistManagement.vue`)

- 自选股票列表（卡片或表格展示）
- 显示股票代码、名称、最新价格、涨跌幅
- 添加自选股票（搜索选择，显示当前数量/限制）
- 删除自选股票
- 实时数据刷新
- 快速跳转到股票分析

### 监控警报管理页面 (`MonitorAlerts.vue`)

- 监控警报列表
- 创建监控警报表单：
  - 选择股票（从自选股票中选择）
  - 选择策略
  - 配置策略参数
  - 选择触发条件
  - 设置触发值（如果需要）
- 编辑/删除监控警报
- 启用/禁用监控警报
- 警报触发历史记录
- 邮箱配置（接收通知的邮箱地址）

### 管理员面板 (`AdminPanel.vue`)

- 标签页切换：
  - **用户管理**: 用户列表、创建/编辑/删除用户、角色管理
  - **策略固化**: 待固化策略列表、审核、固化操作
  - **系统配置**: 全局配置、邮件服务器配置、系统日志
- 权限控制（仅管理员可见）

## 8. 服务层设计

### 自选股票服务 (`WatchlistService`)

```python
class WatchlistService:
    """自选股票服务"""
    
    async def get_watchlist(self, user_id: int) -> List[Dict]
    async def add_stock(self, user_id: int, stock_code: str) -> bool
    async def remove_stock(self, user_id: int, stock_code: str) -> bool
    async def get_realtime_data(self, user_id: int, stock_code: str) -> Dict
    async def check_limit(self, user_id: int) -> Tuple[int, int]  # (当前数量, 限制数量)
```

### 监控服务 (`MonitorService`)

```python
class MonitorService:
    """实时监控服务"""
    
    async def get_alerts(self, user_id: int) -> List[Dict]
    async def create_alert(self, user_id: int, alert_data: Dict) -> Dict
    async def update_alert(self, alert_id: int, user_id: int, alert_data: Dict) -> Dict
    async def delete_alert(self, alert_id: int, user_id: int) -> bool
    async def check_alerts(self) -> None  # 定时任务调用
    async def check_alert_condition(self, alert, data, strategy_result) -> bool
```

### 邮件通知服务 (`NotificationService`)

```python
class NotificationService:
    """邮件通知服务"""
    
    async def send_alert_email(self, user_id: int, ...) -> bool
    async def test_email(self, user_id: int, email: str) -> bool
    def _build_email_body(self, ...) -> str  # 使用Jinja2模板
```

## 9. 配置项

### 后端配置 (`backend/app/config.py`)

```python
# SMTP邮件服务器配置
SMTP_HOST: str = "smtp.example.com"
SMTP_PORT: int = 587
SMTP_USER: str = ""
SMTP_PASSWORD: str = ""
SMTP_USE_TLS: bool = True

# 默认自选股数量限制
DEFAULT_WATCHLIST_LIMIT: int = 20

# 数据获取频率（分钟）
DATA_FETCH_INTERVAL: int = 5

# 监控检查频率（分钟）
MONITOR_CHECK_INTERVAL: int = 1

# 交易时间
TRADING_HOURS_START: int = 9  # 9:30
TRADING_HOURS_END: int = 15  # 15:00
```

## 10. 安全考虑

1. **密码安全**: 使用bcrypt加密存储密码
2. **权限控制**: 严格的角色权限检查
3. **代码安全**: 用户策略代码的验证和安全执行
4. **数据隔离**: 用户数据相互隔离
5. **邮件安全**: SMTP使用TLS加密
6. **频率限制**: 防止API滥用（如邮件发送频率限制）
