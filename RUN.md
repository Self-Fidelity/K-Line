# 运行项目

## 使用 uv（推荐）

### 后端
```bash
uv run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端
```bash
cd frontend
npm install
npm run dev
```

## 使用 conda（当前环境）

### 后端
```bash
conda activate k-line
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端
```bash
cd frontend
npm install
npm run dev
```
