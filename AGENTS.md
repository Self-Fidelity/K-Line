# K-Line 项目 — AI Agent 指南

> 本文档面向 AI 编程助手。阅读前默认你对本项目一无所知。所有信息均基于实际代码与配置文件，请勿臆测。

---

## 项目概述

K-Line 是一个**A股数据分析与策略回测全栈系统**，涵盖数据获取、存储、技术指标计算、策略开发、回测分析、可视化展示与用户管理。

- **数据端**：通过 [AkShare](https://www.akshare.xyz/) 自动/手动获取 A 股历史行情（日 K、分钟 K），支持增量更新与批量更新。
- **策略端**：内置 8+ 种策略（MA、MACD、RSI、KDJ、布林带、动量、蜡烛图形态、海龟、VWMA 等），支持策略对比、加权聚合、参数优化（PSO 粒子群算法），以及通过 Web 界面编写自定义策略（沙箱执行）。
- **可视化端**：前端使用 TradingView Lightweight Charts 绘制专业 K 线图，叠加指标、买卖点标记、筹码分布（CYQ）等；后端同时支持 Bokeh 生成独立 HTML 图表。
- **管理端**：基于角色的用户权限（RBAC）、自选股、系统日志、数据更新定时任务调度。

**项目口号**：敢承诺 100% AI 编程，不含任何手工成分。

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.12+ • FastAPI • Pydantic v2 • SQLAlchemy（连接池）• Uvicorn |
| 前端 | Vue 3 • TypeScript • Vite 5 • Element Plus • Pinia • Lightweight Charts v5 • CodeMirror 6 |
| 数据 | Pandas • NumPy • AkShare • Bokeh（图表生成）|
| 数据库 | PostgreSQL 16（生产）/ SQLite（开发回退）|
| 优化 | mealpy（PSO 粒子群优化）|
| 沙箱 | RestrictedPython（用户自定义策略安全执行）|
| 部署 | Docker • Docker Compose • Nginx • PostgreSQL |
| 任务调度 | APScheduler（后端自动数据更新）|

---

## 项目结构

```
K-Line/
├── backend/                    # FastAPI 后端服务
│   ├── app/
│   │   ├── api/               # 13 个 API 路由模块（auth, data, strategy, chart...）
│   │   ├── models/            # Pydantic v2 请求/响应模型
│   │   ├── services/          # 业务逻辑层（直接调用 src/ 核心引擎）
│   │   ├── utils/             # security.py（JWT/密码）, bokeh_server.py, strategy_sandbox.py
│   │   ├── config.py          # 后端专属配置（JWT、CORS、SMTP、Bokeh）
│   │   ├── dependencies.py    # get_storage() 工厂、get_db() 依赖注入
│   │   └── main.py            # FastAPI 入口：路由注册、CORS、限流、静态文件挂载
│   └── scripts/
│       ├── entrypoint.sh      # Docker 容器入口（初始化数据库 + 启动 uvicorn）
│       └── init_db.py         # 数据库初始化辅助脚本
├── frontend/                   # Vue3 前端
│   ├── src/
│   │   ├── api/               # Axios 封装 + 各模块 API 接口（含请求去重、错误统一处理）
│   │   ├── components/        # KlineChart.vue, CodeEditor.vue, layout/
│   │   ├── views/             # 页面组件（11 个主要视图）
│   │   ├── stores/            # Pinia：auth.ts, stockData.ts
│   │   ├── router/            # Vue Router（懒加载、路由守卫）
│   │   ├── plugins/           # ChipDistributionSeries.ts（筹码分布自定义图元）
│   │   ├── utils/             # indicators.ts（技术指标纯 TS 实现）, statistics.ts
│   │   └── styles/            # SCSS 全局变量与主题（强制深色模式）
│   ├── vite.config.ts         # Vite 配置：base 路径、@/ 别名、/api 代理到 localhost:8000
│   └── package.json           # 依赖：vue, element-plus, lightweight-charts, pinia, axios, codemirror...
├── src/                        # ⭐ 核心共享引擎（被 backend 和 scripts 共同导入）
│   ├── config/                # Settings 类：路径、数据库、akshare 超时、日志配置
│   ├── data_fetcher/          # StockDataFetcher（akshare 封装）, StockListManager
│   ├── data_storage/          # DataStorage(ABC), SQLiteStorage, PostgresStorage, DataExporter
│   ├── strategy/              # BaseStrategy, StrategyManager, StrategyStatistics, Optimizer, ProgressManager
│   │   └── plugins/           # 内置策略插件（8+ 种）
│   ├── visualization/         # KLineChart（Bokeh 生成 HTML 图表）
│   └── utils/                 # Logger（轮转日志）, date_utils（A股交易日历）, akshare_config
├── scripts/                    # CLI 脚本（直接调用 src/ 引擎）
│   ├── setup.py               # 初始化目录结构与数据库表
│   ├── fetch_data.py          # 获取股票数据
│   ├── run_strategy.py        # 运行策略
│   ├── analyze_strategy.py    # 策略回测分析（可生成 Bokeh 图表）
│   ├── export_data.py         # 导出 CSV
│   ├── plot_kline.py          # 绘制 K 线 HTML
│   └── demo_strategy.py       # 策略开发示例
├── tests/                      # Python 单元测试
│   ├── test_new_strategies.py # 策略正确性测试（KDJ/Turtle/VWMA）
│   ├── test_optimization.py   # PSO 优化测试
│   └── test_storage_params.py # SQLite 参数持久化测试
├── deploy/                     # 部署配置
│   ├── backend.Dockerfile     # Python 3.12 multi-stage，非 root 用户运行
│   ├── frontend.Dockerfile    # Node 18 构建 + Nginx Alpine  serving
│   └── nginx.conf.template    # 动态 base path + /api 反向代理
├── data/                       # 数据目录
│   ├── csv/                   # CSV 导出
│   ├── custom_strategies/     # 用户自定义策略文件（按 user_id 分目录）
│   ├── database/              # SQLite 文件（kline.db）
│   ├── images/                # Bokeh 生成的 HTML 图表
│   └── china_holidays.json    # A股休市日历（2024-2026）
├── docs/
│   └── STRATEGY_TEMPLATE.md   # 策略开发完整指南（中文）
├── docker-compose.yml          # 三服务编排：postgres + backend + frontend
├── requirements.txt            # Python 主依赖（akshare, pandas, fastapi, sqlalchemy...）
├── backend/requirements.txt    # 后端额外依赖（与主文件有重叠）
├── .env.example                # 环境变量模板（数据库、JWT、SMTP、前端 base path）
├── start.bat                   # Windows 本地一键启动（SQLite 模式）
├── stop.bat                    # Windows 强制停止所有 python/node 进程
├── QUICKSTART.md               # uv 快速开始指南
├── DEPLOY.md                   # Docker Compose 部署指南
└── README.md                   # 项目总览（中文）
```

**关键架构关系**：`src/` 是核心引擎，不依赖 `backend/` 或 `frontend/`；`backend/app/services/` 直接导入 `src/` 的类；`scripts/` 是 `src/` 的 CLI 包装器。修改 `src/` 会同时影响后端 API 和 CLI 工具。

---

## 环境配置

项目使用 `.env` 文件管理配置。复制 `.env.example` 为 `.env` 后按需修改。

**必须修改的生产环境变量**：
- `SECRET_KEY`：JWT 签名密钥，**绝对不能使用默认值**。生成方式：`openssl rand -hex 32`

**数据库切换**：
- `DATABASE_TYPE=postgresql`（生产，Docker Compose 默认）
- `DATABASE_TYPE=sqlite`（本地开发，零配置）

**前端相关**：
- `VITE_BASE_PATH=/`：子路径部署时修改（如 `/stock/`）
- `VITE_API_BASE_URL=/`：API 基础路径

---

## 构建与运行命令

### 方式一：Docker Compose（生产/服务器部署）

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env：修改 SECRET_KEY、Postgres 密码

# 2. 构建并启动（三服务：postgres + backend + frontend）
docker-compose up -d --build

# 3. 验证
# 前端：http://localhost
# 后端 API 文档：http://localhost:8000/docs
# 健康检查：http://localhost:8000/health

# 4. 查看日志
docker-compose logs -f backend
docker-compose logs -f postgres

# 5. 停止
docker-compose down
```

> Docker Compose 中 PostgreSQL 数据卷为 `postgres_data`，备份命令：
> `docker exec kline-postgres pg_dump -U kline_user kline_db > backup.sql`

### 方式二：本地开发（推荐 uv）

```bash
# 安装 uv（如未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建虚拟环境并安装依赖
uv venv
uv pip install -r requirements.txt -r backend/requirements.txt

# 使用 SQLite 开发（无需 PostgreSQL）
$env:DATABASE_TYPE="sqlite"        # Windows PowerShell
export DATABASE_TYPE=sqlite         # Linux/macOS

# 初始化数据库与目录
uv run python scripts/setup.py

# 启动后端
uv run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# 启动前端（新终端）
cd frontend
npm install
npm run dev
```

**开发环境访问地址**：
- 前端：`http://localhost:5173`
- 后端 API：`http://localhost:8000`
- API 文档：`http://localhost:8000/docs`

### Windows 一键脚本

```bash
start.bat   # 启动后端 + 前端 + 自动打开浏览器（使用 SQLite）
stop.bat    # 强制结束所有 python.exe 和 node.exe（注意：会杀掉全局进程）
```

### 常用 CLI 脚本（uv run 无需激活虚拟环境）

```bash
# 获取单只股票数据
uv run python scripts/fetch_data.py --stock 000001

# 运行策略并查看结果
uv run python scripts/run_strategy.py --strategy "MA策略" --stock 000001 --start-date 20240101

# 策略回测分析 + 生成 Bokeh 图表
uv run python scripts/analyze_strategy.py --strategy "MA策略" --stock 000001 --plot

# 导出数据到 CSV
uv run python scripts/export_data.py --stock 000001
```

---

## 代码组织与模块规范

### 后端（backend/app/）

采用 **分层架构**：

```
API Router → Pydantic Models → Service → src/ Engine → Storage/DataFetcher
```

- `api/`：纯 HTTP 层，只做参数校验、调用 Service、返回响应。禁止在此处写业务逻辑。
- `services/`：业务逻辑层。所有对 `src/` 的调用应封装在 Service 中，供 API 复用。
- `models/`：Pydantic v2 Schema。请求模型以 `*Request`/`*Create`/`*Update` 结尾，响应模型以 `*Response`/`*Info` 结尾。
- `utils/`：横向工具。`strategy_sandbox.py` 使用 RestrictedPython 执行用户代码，**白名单机制**：允许 `math`, `statistics`, `datetime`, `pandas`, `numpy`, `abc`, `typing`；禁止 `os`, `sys`, `subprocess`, `socket`, `urllib`, `requests`, `open`, `eval`, `exec`, `compile`。

### 核心引擎（src/）

- `src/data_fetcher/`：所有 akshare 调用集中于此，含重试逻辑与批量处理。
- `src/data_storage/`：
  - `DataStorage` 是抽象基类，定义市场数据（K线）与业务数据（用户、审计日志、自选股、股票列表、配置表）的统一接口。
  - `SQLiteStorage`：单文件，开发便利。
  - `PostgresStorage`：使用 SQLAlchemy 连接池，生产环境。
  - **所有业务数据（auth、audit logs、watchlist、stock_list、data_update_config）均已通过 `DataStorage` 统一**。backend 与 data_fetcher 不再直接调用 `sqlite3.connect()`。
- `src/strategy/`：
  - `BaseStrategy`：所有策略必须继承。必须实现 `analyze(data: pd.DataFrame, **kwargs) -> pd.DataFrame`。
  - 输出 DataFrame **必须包含** `date`, `signal`（1=买入, -1=卖出, 0=持有）, `signal_type`（"买入"/"卖出"/"持有"）。
  - `StrategyManager` 自动扫描 `src/strategy/plugins/*.py` 加载策略类。
  - 策略类必须能在无参情况下实例化（所有参数有默认值）。
  - 命名规范：类名 CamelCase + `Strategy` 后缀（如 `MAStrategy`），文件名 snake_case + `_strategy.py`（如 `ma_strategy.py`），策略名称 `name` 使用英文且全局唯一。
- `src/visualization/`：`KLineChart` 使用 Bokeh 生成 HTML，包含 K线、买卖点标记、MA  overlay、成交量子图、统计面板。

### 前端（frontend/src/）

- **Composition API**：所有组件使用 `<script setup lang="ts">`。
- **API 层**（`api/`）：每个模块一个文件，导出类型化的请求/响应接口。`client.ts` 统一处理 JWT 注入、请求去重（GET 级）、错误归一化（401 跳转登录、全局 Toast）。
- **状态管理**（`stores/`）：仅两个 Pinia Store——`auth.ts`（登录态）和 `stockData.ts`（股票列表缓存，5 分钟 TTL）。
- **视图**（`views/`）：11 个页面，全部懒加载。路由守卫：`requiresAuth` 跳登录，`requiresAdmin` 检查 `role === 'admin'`。
- **样式**：SCSS + CSS 变量。强制深色模式（`useDark().value = true`）。引入 Element Plus 中文语言包。
- **路径别名**：`@/` 映射到 `./src/`。

---

## 代码风格指南

### Python

- Python 3.12+，使用类型注解（`list[str]`, `pd.DataFrame` 等）。
- 字符串使用双引号为主，中文注释和文档字符串正常书写。
- 日志：使用 `src/utils/logger.py` 的 `get_logger(__name__)`，而非裸 `print()`。
- 导入顺序：标准库 → 第三方 → 本项目模块。本项目模块以 `from src.xxx` 或 `from backend.app.xxx` 开头。
- `Path` 优先于字符串拼接路径。
- 数据库操作：优先使用 `get_storage()` 工厂获取存储实例；避免在 API 层直接写 SQL。

### TypeScript / Vue

- 严格模式开启（`tsconfig.json` 中 `noUnusedLocals`, `noUnusedParameters` 为 `true`）。
- 组件样式使用 `<style scoped lang="scss">`。
- SCSS 变量通过 `@use '@/styles/variables' as v` 引入。
- API 调用统一走 `api/` 层，禁止在组件中直接 `axios.get()`。
- 图标使用 `@element-plus/icons-vue`，在 `main.ts` 中全局自动注册。

---

## 测试说明

- **框架**：标准库 `unittest`（非 pytest）。
- **运行方式**：
  ```bash
  python -m unittest discover -s tests -v
  # 或单文件
  python -m unittest tests.test_new_strategies
  ```
- **测试策略**：纯单元测试，**使用合成 DataFrame**（100-200 行确定性数据），不连接真实数据库或网络。
- **覆盖范围**：
  - `test_new_strategies.py`：验证 KDJ、Turtle、VWMA 策略输出包含预期列。
  - `test_optimization.py`：验证 PSO 优化器返回的参数在合法边界内。
  - `test_storage_params.py`：验证 SQLite 中策略参数的增删改查（临时数据库，tearDown 清理）。
- **注意**：前端目录中**没有测试**。需要前端测试时需自行引入 Vitest / Cypress 等框架。

---

## 安全注意事项

1. **SECRET_KEY**：`.env` 中的默认值必须修改，否则后端启动会抛出 `ValueError`。生产环境使用 `openssl rand -hex 32` 生成强密钥。
2. **JWT Token**：`ACCESS_TOKEN_EXPIRE_MINUTES` 默认 1440 分钟（24 小时）。生产环境可按需缩短。
3. **自定义策略沙箱**：用户上传的 Python 代码通过 `RestrictedPython` 编译后执行。白名单外的一切模块/函数均被禁止。即便如此，**仍需定期审计 `strategy_sandbox.py` 的允许列表**。
4. **CORS**：生产环境应在 `backend/app/config.py` 中将 `CORS_ORIGINS` 限制为实际前端域名，不要保留 `*` 或 localhost。
5. **数据库**：PostgreSQL 密码在 `.env` 中明文存储，请确保 `.env` 文件权限为 `600`，且已加入 `.gitignore`。
6. **stop.bat**：Windows 开发脚本使用 `taskkill /F /IM python.exe` 和 `node.exe`，会**杀死本机所有 Python 和 Node 进程**，不要在共享开发机上使用。
7. **静态文件**：`backend/app/main.py` 挂载了 `/static` 和 `/charts` 目录。确保这些目录的写入权限受控，防止路径遍历攻击。

---

## 策略开发快速参考

新增内置策略的步骤：

1. 在 `src/strategy/plugins/` 下创建新文件（如 `my_strategy.py`）。
2. 继承 `BaseStrategy`，实现 `analyze()`。
3. 确保返回 DataFrame 含 `date`, `signal`, `signal_type`。
4. 类支持无参实例化，策略名称唯一。
5. 用 `python scripts/analyze_strategy.py --strategy "Your Name" --stock 000001 --plot` 测试。

详细规范参考 `docs/STRATEGY_TEMPLATE.md`。

用户通过 Web 界面提交的自定义策略：
- 代码存储在 `data/custom_strategies/{user_id}/`。
- 文件名格式：`{name}_{timestamp}.py`。
- 由 `backend/app/utils/strategy_sandbox.py` 沙箱编译执行。

---

## 部署架构

```
┌─────────────┐
│   Nginx     │  <-- frontend 容器 (port 80)
│  (Vue dist) │      动态 base path (envsubst)
└──────┬──────┘
       │ /api/*  → proxy_pass
       ▼
┌─────────────┐
│   FastAPI   │  <-- backend 容器 (port 8000)
│  (Uvicorn)  │      非 root 用户 (kline:kline)
└──────┬──────┘
       │ PostgreSQL / SQLite
       ▼
┌─────────────┐
│ PostgreSQL  │  <-- postgres 容器 (port 5432)
│   16 Alpine │      健康检查 + 资源限制 (1 CPU / 512M)
└─────────────┘
```

- Docker Compose 中所有服务时区为 `Asia/Shanghai`。
- 日志使用 `json-file` driver 并设置大小轮转。
- 后端健康检查：`curl -f http://localhost:8000/docs`。
- 前端健康检查：`wget --spider http://localhost:80/`。

---

## 常见陷阱与注意事项

- **`src/` 不是遗留代码**：它是活跃维护的核心引擎。修改策略、存储或数据获取逻辑时，优先考虑在 `src/` 中修改，而非在 `backend/` 中写重复逻辑。
- **数据库兼容性陷阱（已修复）**：~~部分模块曾硬编码使用 `sqlite3` 连接~~。经过两次重构（`da18cfe`、`de41a60`），所有 backend API、service、data_fetcher 均已通过 `DataStorage` 抽象层访问数据库。新增持久化功能时，只需在 `DataStorage` 基类中定义抽象方法，并在 `SQLiteStorage` 和 `PostgresStorage` 中分别实现即可。
- **前端端口**：`vite.config.ts` 中 dev server 端口为 5173，但 `start.bat` 里打开浏览器用的是 5174（笔误），本地开发以实际 `npm run dev` 输出端口为准。
- **Bokeh 图表与 Lightweight Charts**：Bokeh 用于后端生成可下载的 HTML 图表；Lightweight Charts 用于前端交互式图表。两者独立，不要混用。
- **静态文件挂载顺序**：`main.py` 中 `/static` 和 `/charts` 的 `StaticFiles` 挂载在路由注册之后。`sys.path.insert(0, str(src_dir))` 用于运行时让 `src_settings` 可被导入，不要删除。
- **用户策略自动发现**：`StrategyManager` 使用文件系统扫描加载策略。新增/修改 `src/strategy/plugins/` 下的文件后，**重启后端进程**才能生效（没有热重载）。
- **`save_stock_list` 事务安全**：`SQLiteStorage` 和 `PostgresStorage` 的 `save_stock_list()` 采用"先清空表再全量插入"策略，且已添加事务保护（异常时 rollback）。但在开发测试时，**切勿传入不完整的 DataFrame** 进行测试，否则会导致生产环境中的股票列表表被意外清空。测试应使用独立临时数据库。
