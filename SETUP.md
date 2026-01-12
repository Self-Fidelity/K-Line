# K-Line 项目环境设置指南

## 前置要求

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) - 快速的 Python 包管理工具
- Node.js 和 npm（用于前端开发）

## 安装 uv

```bash
# 使用官方安装脚本（推荐）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 pip 安装
pip install uv

# 或使用 conda 安装
conda install -c conda-forge uv
```

## 环境设置步骤

### 1. 创建虚拟环境

```bash
cd /home/ubuntu/K-Line
uv venv
```

### 2. 激活虚拟环境（可选）

使用 `uv run` 时无需激活虚拟环境。如需激活：

```bash
source .venv/bin/activate
```

### 3. 安装 Python 依赖

```bash
# 使用 uv 安装所有依赖（推荐）
uv pip install -r requirements.txt -r backend/requirements.txt

# 或使用 uv run（无需激活虚拟环境）
uv run pip install -r requirements.txt -r backend/requirements.txt
```

### 4. 初始化数据库

```bash
# 使用 uv run（推荐，无需激活虚拟环境）
uv run python backend/scripts/init_db.py
uv run python scripts/setup.py

# 或激活虚拟环境后运行
source .venv/bin/activate
python backend/scripts/init_db.py
python scripts/setup.py
```

### 5. 安装前端依赖

```bash
cd frontend
npm install
cd ..
```

### 6. 运行项目

#### 运行后端（FastAPI）

```bash
# 使用 uv run（推荐）
uv run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# 或激活虚拟环境后运行
source .venv/bin/activate
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

后端将在 http://localhost:8000 运行
API 文档：http://localhost:8000/docs

#### 运行前端（Vue）

```bash
cd frontend
npm run dev
```

前端将在 http://localhost:5173 运行

## 验证安装

### 检查 Python 包

```bash
# 使用 uv
uv pip list | grep -E "fastapi|akshare|pandas|bokeh"

# 或激活虚拟环境后
source .venv/bin/activate
pip list | grep -E "fastapi|akshare|pandas|bokeh"
```

### 检查 Node.js 包

```bash
cd frontend
npm list --depth=0
```

### 检查数据库

```bash
ls -la data/database/
```

## 常见问题

### 1. pip 安装失败

如果 pip 安装失败，可以尝试：
```bash
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py --user
```

### 2. npm 版本过旧

如果 npm 版本过旧，可以更新：
```bash
sudo npm install -g npm@latest
```

### 3. 端口被占用

如果 8000 或 5173 端口被占用：
- 后端：修改 uvicorn 命令中的 `--port` 参数
- 前端：修改 `frontend/vite.config.ts` 中的端口配置

## 下一步

完成环境设置后，可以：
1. 获取股票数据：`python scripts/fetch_data.py --stock 000001`
2. 运行策略分析：`python scripts/run_strategy.py --list`
3. 访问 Web 界面：http://localhost:5173
