<div align="center">

# 📈 K-Line System

<p align="center">
  <em>A股数据分析与策略回测系统</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Vue-3.0+-brightgreen.svg" alt="Vue">
  <img src="https://img.shields.io/badge/FastAPI-Latest-009688.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

<p align="center">
  从数据获取、存储、策略开发、回测分析到可视化展示的<strong>全栈解决方案</strong>
</p>

</div>

---

## ✨ 核心特性

### 📊 数据中心
- 🔄 **自动更新** - 集成 AkShare，自动获取并增量更新 A 股历史行情数据
- 🗂️ **数据管理** - 支持手动触发全量或增量更新，实时查看数据状态
- ⚡ **高效存储** - 生产环境使用 PostgreSQL + 连接池，开发可用 SQLite 回退，支持快速查询

### 🧪 策略实验室
- 📈 **单策略分析** - 针对单只股票运行特定策略，查看买卖信号和详细回测报告
- ⚖️ **策略对比** - 同时对比多个策略在同一只股票上的表现，直观比较优劣
- 🎯 **策略聚合** - 🆕 将多个策略组合使用，通过加权投票机制生成最终交易信号
- 🔧 **参数优化** - 🆕 使用粒子群算法 (PSO) 自动寻找策略的最佳参数组合
- 💻 **自定义策略** - 🆕 通过 Web 界面编写 Python 代码快速创建新策略，即写即测

### 📉 可视化与复盘
- 📊 **专业 K 线图** - 集成 TradingView Lightweight Charts，支持缩放、平移
- 📐 **技术指标** - 内置 MA、MACD、RSI、布林带等多种指标，支持自定义
- 🎲 **筹码分布 (CYQ)** - 🆕 实现的筹码分布指标，帮助分析支撑压力位
- 🎯 **交易信号标记** - 在图表上直观展示策略生成的买卖点

### 🔐 系统管理
- 👥 **用户管理** - 完善的基于角色的权限控制 (RBAC)
- 📝 **系统日志** - 实时记录用户行为和系统状态监控
- ⭐ **自选股** - 用户个性化收藏关注的股票

---

## 🛠️ 技术栈

<table>
  <tr>
    <td><strong>后端</strong></td>
    <td>Python 3.12 • FastAPI • Pandas • NumPy • PostgreSQL • SQLAlchemy • RestrictedPython</td>
  </tr>
  <tr>
    <td><strong>前端</strong></td>
    <td>Vue 3 • TypeScript • Vite • Element Plus • Lightweight Charts</td>
  </tr>
  <tr>
    <td><strong>部署</strong></td>
    <td>Docker • Docker Compose • Nginx • PostgreSQL</td>
  </tr>
</table>

---

## 🚀 快速开始

### 方式一：Docker 一键部署 (推荐)

> 适用于服务器部署或快速体验

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/K-Line.git
cd K-Line

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件配置：
#   - SECRET_KEY: 随机字符串（必须修改！）
#   - POSTGRES_USER / POSTGRES_PASSWORD / POSTGRES_DB: 数据库凭据
#   - FRONTEND_PORT / BACKEND_PORT: 服务端口

# 3. 启动服务
docker-compose up -d --build
```

**访问地址：**
- 🌐 前端: `http://localhost` (或您配置的端口)
- 📚 后端 API 文档: `http://localhost:8000/docs`

> 📖 详细部署指南请参考 [DEPLOY.md](DEPLOY.md)

### 方式二：本地开发

> 适用于开发调试

#### 后端

```bash
# 1. 创建虚拟环境
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. 安装依赖
uv pip install -r requirements.txt

# 3. 初始化数据库（确保 PostgreSQL 已启动，或设置 DATABASE_TYPE=sqlite 使用本地 SQLite）
uv run python scripts/setup.py

# 4. 启动服务
uv run uvicorn backend.app.main:app --reload
```

#### 前端

```bash
cd frontend
npm install
npm run dev
```

---

## 📂 项目结构

```
K-Line/
├── 📁 backend/              # Python 后端
│   ├── app/
│   │   ├── api/             # API 路由
│   │   ├── models/          # 数据模型
│   │   ├── services/        # 业务逻辑
│   │   └── strategy/        # 策略引擎插件
│   └── ...
├── 📁 frontend/             # Vue3 前端
│   ├── src/
│   │   ├── api/             # API 客户端
│   │   ├── views/           # 页面组件
│   │   ├── components/      # 通用组件
│   │   └── plugins/         # 图表插件 (CYQ等)
│   └── ...
├── 📁 data/                 # 数据存储 & 节假日配置
│   ├── china_holidays.json  # A股休市日历
│   └── ...
├── 📁 deploy/               # 部署相关配置
├── 🐳 docker-compose.yml    # Docker 编排文件（含 PostgreSQL）
└── 📋 requirements.txt      # Python 依赖
```

---

## 🧪 策略开发

系统支持插件化策略开发：

- 📝 在 `backend/app/strategy/strategies/` 下添加新的 Python 文件来扩展策略
- 💻 或直接在 Web 界面的"自定义策略"模块中编写

### 内置策略

- 📊 **技术指标策略**: MA、MACD、RSI、布林带、动量策略
- 🕯️ **K线形态策略**: 锤子线、上吊线、十字星、吞没形态等

---

## 📸 预览

> 🎨 _截图待添加_

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## ⚠️ 免责声明

本项目仅用于**学习和研究目的**。

- 数据来源于 AkShare，使用时请遵守相关数据源的使用条款
- 投资有风险，策略分析结果仅供参考，不构成投资建议

---

## 📄 许可证

本项目采用 [MIT](LICENSE) 许可证。

---

<div align="center">

**⭐ 敢承诺100%AI编程，不含任何手工成分！**

Made with ❤️ by HIN

</div>
