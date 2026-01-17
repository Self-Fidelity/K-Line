# K-Line System

K-Line 是一个现代化的中国股市数据分析与策略回测系统。它提供了从数据获取、存储、策略开发、回测分析到可视化展示的全栈解决方案。

## 🌟 主要功能

### 1. 数据中心
- **每日数据自动更新**: 集成 AkShare，自动获取并增量更新 A 股历史行情数据。
- **数据管理**: 支持手动触发全量或增量更新，查看数据状态。
- **高效存储**: 使用 SQLite 进行本地存储，支持快速查询。

### 2. 策略实验室
- **单策略分析**: 针对单只股票运行特定策略，查看买卖信号和详细回测报告（收益率、最大回撤、夏普比率等）。
- **策略对比**: 同时对比多个策略在同一只股票上的表现，直观比较优劣。
- **策略聚合**: **(新特性)** 支持将多个策略组合使用，通过加权投票机制生成最终交易信号。
- **参数优化**: **(新特性)** 使用通过粒子群算法 (PSO) 自动寻找策略的最佳参数组合，并支持保存优化结果。
- **自定义策略**: **(新特性)** 支持通过 Web 界面编写 Python 代码快速创建新策略，即写即测。

### 3. 可视化与复盘
- **专业 K 线图**: 集成 TradingView Lightweight Charts，支持缩放、平移。
- **技术指标**: 内置 MA, Pyramiding 等指标，支持自定义指标叠加。
- **筹码分布 (CYQ)**: **(新特性)** 独家实现的筹码分布指标，帮助分析支撑压力位。
- **交易信号标记**: 在图表上直观展示策略生成的买卖点。

### 4. 系统管理
- **用户管理**: 完善的基于角色的权限控制 (RBAC)，支持管理员管理用户。
- **系统日志**: 实时记录用户行为（登录、策略创建等）和系统状态监控。
- **自选股**: 用户个性化收藏关注的股票。

## 🛠 技术栈

- **后端**: Python 3.12, FastAPI, Pandas, NumPy, SQLite, SQLAlchemy
- **前端**: Vue 3, TypeScript, Vite, Element Plus, Lightweight Charts
- **部署**: Docker, Docker Compose, Nginx

## 🚀 快速开始

### 方式一：Docker 一键部署（推荐）

适用于服务器部署或快速体验。

1.  **克隆项目**
2.  **配置环境**
    ```bash
    cp .env.example .env
    # 编辑 .env 文件配置端口和密钥
    ```
3.  **启动服务**
    ```bash
    docker-compose up -d --build
    ```
4.  **访问**
    - 前端: `http://localhost` (或您配置的端口)
    - 后端 API 文档: `http://localhost:8000/docs`

详细部署指南请参考 [DEPLOY.md](DEPLOY.md)。

### 方式二：本地开发

适用于开发调试。

**后端**
```bash
# 1. 创建虚拟环境
uv venv
source .venv/bin/activate  # 或 Windows: .venv\Scripts\activate

# 2. 安装依赖
uv pip install -r requirements.txt

# 3. 初始化数据库
uv run python backend/app/init_db.py

# 4. 启动服务
uv run uvicorn backend.app.main:app --reload
```

**前端**
```bash
cd frontend
npm install
npm run dev
```

## 📂 项目结构

```
K-Line/
├── backend/                # Python后端
│   ├── app/
│   │   ├── api/            # API 路由
│   │   ├── models/         # 数据模型
│   │   ├── services/       # 业务逻辑
│   │   └── strategy/       # 策略引擎插件
│   └── ...
├── frontend/               # Vue3前端
│   ├── src/
│   │   ├── api/            # API 客户端
│   │   ├── views/          # 页面组件
│   │   ├── components/     # 通用组件
│   │   └── plugins/        # 图表插件 (CYQ等)
│   └── ...
├── data/                   # 数据存储 (SQLite DB)
├── deploy/                 # 部署相关配置
├── docker-compose.yml      # Docker 编排文件
└── requirements.txt        # 后端依赖
```

## 🧪 策略开发

系统支持插件化策略开发。您可以在 `backend/app/strategy/strategies/` 下添加新的 Python 文件来扩展策略，或直接在 Web 界面的"自定义策略"模块中编写。

## 📄 许可证

本项目采用 MIT 许可证。
