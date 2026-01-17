# K-Line 系统部署指南

本指南将帮助您在服务器上快速部署 K-Line 系统。我们推荐使用 **Docker Compose** 进行一键部署。

## 目录
1. [前提条件](#前提条件)
2. [环境配置](#环境配置)
3. [构建与启动](#构建与启动)
4. [常见问题](#常见问题)

## 前提条件

- 这里的服务器需要有 **Docker** 和 **Docker Compose** 环境。
- 确保服务器的 80 (前端) 和 8000 (后端) 端口未被占用。

## 环境配置

1. **获取代码**
   将项目代码上传到服务器。

2. **配置环境变量**
   在项目根目录下复制示例配置：
   ```bash
   cp .env.example .env
   ```
   
   编辑 `.env` 文件，修改以下关键配置：
   - `FRONTEND_PORT`: 前端访问端口（默认 80）。
   - `BACKEND_PORT`: 后端 API 端口（默认 8000）。
   - `SECRET_KEY`: 生成一个随机字符串用于加密。
   - `VITE_API_BASE_URL`: 生产环境通常设为 `/api`（通过 Nginx 代理）。
   - 其他邮件SMTP配置（如果需要）。

3. **前端高级配置 (可选)**
   如果需要将项目部署在子路径下（例如 `http://domain.com/stock/`），请在 `frontend` 目录下新建或修改 `.env` 文件：
   ```bash
   # 设置应用的基础路径 (默认为 /)
   VITE_BASE_PATH=/stock/
   ```
   **注意**：修改此配置后必须重新构建前端镜像 (`docker-compose build frontend`) 才能生效。

## 构建与启动

1. **构建并启动服务**
   在项目根目录运行：
   ```bash
   docker-compose up -d --build
   ```
   该命令会自动：
   - 构建前端（Vue + Vite -> 静态文件 -> Nginx）
   - 构建后端（Python -> Uvicorn）
   - 挂载必要的卷（Database, Logs）

2. **验证部署**
   - 访问 `http://your-server-ip` 查看前端页面。
   - 访问 `http://your-server-ip/api/docs` 查看后端 API 文档。
   - 访问 `http://your-server-ip/api/logs` 查看系统日志。

3. **停止服务**
   ```bash
   docker-compose down
   ```

## 数据持久化

- **数据库**: 数据存储在项目根目录的 `data/database/kline.db`。Docker 会通过卷挂载此文件，因此重启容器不会丢失数据。
- **日志**: 日志存储在 `logs/` 目录。

## 手动部署（不推荐）

如果不使用 Docker，您需要：
1. **后端**: 安装 Python 3.12+，运行 `pip install -r requirements.txt`，然后用 `uvicorn backend.app.main:app --host 0.0.0.0 --port 8000` 启动。
2. **前端**: 安装 Node.js 18+，运行 `npm run build`，然后配置 Nginx 指向 `dist` 目录并反向代理 `/api` 到 8000 端口。

## 维护

- **更新代码**: 拉取新代码后，重新运行 `docker-compose up -d --build`。
- **查看日志**: 
  ```bash
  docker-compose logs -f backend
  docker-compose logs -f frontend
  ```
