# K-Line 项目快速开始指南

## 使用 uv 管理依赖（推荐）

### 1. 安装 uv

```bash
# 使用官方安装脚本（推荐）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 pip 安装
pip install uv

# 或使用 conda 安装
conda install -c conda-forge uv
```

### 2. 创建虚拟环境并安装依赖

```bash
# 创建虚拟环境
uv venv

# 安装依赖
uv pip install -r requirements.txt -r backend/requirements.txt
```

### 3. 初始化数据库

```bash
# 本地开发可用 SQLite（无需 PostgreSQL）
export DATABASE_TYPE=sqlite

# 初始化数据库表和目录
uv run python scripts/setup.py
```

### 4. 运行后端服务

```bash
# 使用 uv run
uv run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

后端将在 http://localhost:8000 运行
API 文档：http://localhost:8000/docs

### 5. 运行前端服务

```bash
cd frontend
npm install
npm run dev
```

前端将在 http://localhost:5173 运行

### 6. 运行脚本

```bash
# 获取股票数据
uv run python scripts/fetch_data.py --stock 000001

# 运行策略
uv run python scripts/run_strategy.py --list

# 其他脚本也类似
uv run python scripts/<script_name>.py <args>
```

## uv 的优势

- ⚡ **极快的安装速度**：比 pip 快 10-100 倍
- 🔒 **可靠的依赖解析**：使用现代依赖解析器
- 📦 **统一工具**：替代 pip、venv、pip-tools 等多个工具
- 🎯 **简单易用**：`uv run` 无需激活虚拟环境即可运行

## 常用 uv 命令

```bash
# 创建虚拟环境
uv venv

# 安装依赖
uv pip install -r requirements.txt

# 运行 Python 脚本（无需激活虚拟环境）
uv run python script.py

# 运行命令（在虚拟环境中）
uv run uvicorn backend.app.main:app --reload

# 查看已安装的包
uv pip list

# 添加新依赖
uv pip install package-name

# 导出依赖
uv pip freeze > requirements.txt
```

## 注意事项

1. 使用 `uv run` 时无需激活虚拟环境
2. `uv venv` 默认创建 `.venv` 目录
3. 如果遇到网络问题，可以配置 pip 镜像源
4. 依赖已经在 `pyproject.toml` 中定义，也可以使用 `uv sync`（需要修复构建配置）
