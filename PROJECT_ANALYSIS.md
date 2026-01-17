# K-Line 项目全面分析报告

## 📋 项目概述

**K-Line** 是一个完整的中国A股市场数据获取、存储、分析和可视化系统。项目采用前后端分离架构，提供Web界面进行股票数据管理、策略分析、策略开发与回测。

### 核心功能
- ✅ **股票数据管理**：自动获取/更新每日K线、分时K线（akshare），支持本地SQLite存储与增量更新。
- ✅ **策略分析框架**：插件化策略设计，支持动态加载；内置多种经典策略（MA, RSI, MACD, Bollinger等）。
- ✅ **策略回测与优化**：提供详细的回测统计指标（年化收益、最大回撤、夏普比率等）；支持参数多线程优化（PSO/网格搜索）。
- ✅ **自定义策略**：提供在线代码编辑器，支持用户编写、调试、验证 Python 策略代码。
- ✅ **高级可视化**：基于 Lightweight Charts 的专业K线图，集成筹码分布（CYQ）、多种技术指标叠加。
- ✅ **企业级功能**：完善的用户权限管理（RBAC），审计日志（Audit Log），数据安全保障。
- ✅ **批量分析**：支持全市场扫描与策略筛选。

---

## 🏗️ 技术架构

### 后端技术栈
| 技术 | 版本 | 用途 |
|------|------|------|
| **Python** | 3.12+ | 核心开发语言 |
| **FastAPI** | 0.104+ | 高性能异步 Web 框架 |
| **SQLite** | - | 轻量级关系型数据库 |
| **Pandas/NumPy** | Latest | 金融数据处理与数值计算 |
| **AkShare** | Latest | 开源财经数据接口 |
| **APScheduler** | 3.10+ | 定时任务调度 |

### 前端技术栈
| 技术 | 版本 | 用途 |
|------|------|------|
| **Vue 3** | 3.3+ | 渐进式前端框架 |
| **TypeScript** | 5.2+ | 静态类型系统 |
| **Element Plus** | 2.4+ | 桌面端 UI 组件库 |
| **Lightweight Charts** | 4.1+ | 高性能金融图表库 |
| **Pinia** | 2.1+ | 状态管理 |
| **Vite** | 5.0+ | 极速构建工具 |

---

## 📁 核心项目结构

```
K-Line/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── api/                # RESTful API 路由 (auth, data, strategy, logs...)
│   │   ├── services/           # 业务逻辑层 (DataService, StrategyService, AuditLogService...)
│   │   ├── models/             # Pydantic 数据模型
│   │   └── utils/              # 通用工具
│   ├── scripts/                # 数据库管理脚本
│   └── main.py                 # 应用入口
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── api/                # Axios 请求封装
│   │   ├── components/         # 公共组件 (KlineChart, ChipDistribution...)
│   │   ├── views/              # 页面视图 (Dashboard, StrategyAnalysis, UserManagement...)
│   │   └── plugins/            # 插件扩展 (如自定义图表类型)
├── scripts/                    # 运维脚本 (fetch_data.py, run_strategy.py)
├── data/                       # 数据持久化
│   ├── database/               # kline.db (SQLite)
│   └── strategy_results/       # 回测结果缓存
└── logs/                       # 系统运行日志
```

---

## �️ 数据库设计 (Schema)

系统使用 SQLite 存储，核心表结构如下：

### 1. 市场数据
- **stock_daily_kline**: 日频 K 线数据 (Date, Open, High, Low, Close, Volume...)
- **stock_minute_kline**: 分时 K 线数据 (1m, 5m, 15m, 30m, 60m)

### 2. 用户与权限
- **users**: 用户信息 (Username, PasswordHash, Role, Permissions)
- **user_settings**: 用户偏好设置
- **watchlist**: 用户自选股关联表

### 3. 策略与系统
- **custom_strategies**: 用户自定义策略代码与元数据
- **audit_logs**: 系统审计日志 (Action, User, IP, Timestamp, Details)
- **monitor_alerts**: 策略监控预警规则

---

## � 关键业务流程

### 1. 策略回测与优化
```mermaid
graph LR
A[用户配置参数] --> B(后端接收请求);
B --> C{是否需要优化?};
C -- 是 --> D[启动 Optimizer (PSO/Grid)];
D --> E[多线程并行回测];
E --> F[生成最优参数];
C -- 否 --> G[使用当前参数];
F --> G;
G --> H[执行 Strategy.analyze()];
H --> I[计算 Statistics];
I --> J[返回结果 JSON];
J --> K[前端渲染图表 & 报表];
```

### 2. 筹码分布 (CYQ) 计算
数据服务层基于**换手率衰减算法**计算每日筹码分布：
1. 获取历史 K 线数据。
2. 遍历每一日交易，根据换手率计算当日"新筹码"与"老筹码"的移动。
3. 生成价格-筹码量分布直方图。
4. 前端通过自定义 Canvas 层叠加在 K 线图右侧展示。

---

## 🔒 安全性设计

1.  **认证 (Authentication)**: 基于 OAuth2 + JWT 的无状态认证。
2.  **授权 (Authorization)**: RBAC 模型，严格区分 `admin` 与 `user` 权限（如数据更新接口仅限管理员）。
3.  **审计 (Auditing)**: `AuditLogService` 自动记录关键变更，不可篡改。
4.  **代码沙箱**: 自定义策略执行虽为 Python 代码，但建议在受控容器中运行（当前为本地直接执行，需注意风险）。

---

## 🐛 已知限制与改进计划

1.  **性能瓶颈**: 
    - 随着分时数据量增长，SQLite 单文件可能面临读写压力。计划迁移至 PostgreSQL 或 ClickHouse。
    - 策略优化目前为 CPU 密集型，可考虑 Celery 异步任务队列。
2.  **实时性**:
    - 当前为盘后数据更新模式。接入 WebSocket 实时行情是下一步重点。
3.  **移动端适配**:
    - 当前前端主要针对桌面端优化，移动端布局需重构。

---

**报告生成日期**: 2025-01-17
**版本**: v0.2.0
