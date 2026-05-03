# K-Line 系统部署指南

本指南将帮助您在服务器上快速部署 K-Line 系统。我们推荐使用 **Docker Compose** 进行一键部署。

## 目录
1. [前提条件](#前提条件)
2. [环境配置](#环境配置)
3. [构建与启动](#构建与启动)
4. [常见问题](#常见问题)

## 前提条件

- 这里的服务器需要有 **Docker** 和 **Docker Compose** 环境。
- 确保服务器的以下端口未被占用：**80** (前端), **8000** (后端), **5432** (PostgreSQL)。

## 环境配置

1. **获取代码**
   将项目代码上传到服务器。

2. **配置环境变量**
   在项目根目录下复制示例配置：
   ```bash
   cp .env.example .env
   ```
   
   编辑 `.env` 文件，修改以下关键配置：
   | 变量 | 说明 | 示例 |
   |------|------|------|
   | `SECRET_KEY` | **必须修改！** JWT 签名密钥，默认值会导致启动失败 | `openssl rand -hex 32` 生成 |
   | `POSTGRES_USER` | PostgreSQL 用户名 | `kline_user` |
   | `POSTGRES_PASSWORD` | PostgreSQL 密码 | 随机强密码 |
   | `POSTGRES_DB` | PostgreSQL 数据库名 | `kline_db` |
   | `DATABASE_TYPE` | 数据库类型（`postgresql` / `sqlite`） | `postgresql` |
   | `FRONTEND_PORT` | 前端访问端口 | `80` |
   | `BACKEND_PORT` | 后端 API 端口 | `8000` |
   | `VITE_BASE_PATH` | 应用基础路径（子路径部署时设置） | `/` 或 `/stock/` |
   
   其他可选配置：
   - `ACCESS_TOKEN_EXPIRE_MINUTES`: Token 过期时间（默认 1440 分钟 / 24小时）
   - `SMTP_*`: 邮件服务器配置（用于密码重置等）


## 构建与启动

1. **构建并启动服务**
   在项目根目录运行：
   ```bash
   docker-compose up -d --build
   ```
   该命令会自动：
   - 启动 PostgreSQL 16 数据库（含健康检查）
   - 构建前端（Vue + Vite → 静态文件 → Nginx）
   - 构建后端（Python + Uvicorn，等待 PostgreSQL 就绪后启动）
   - 挂载必要的卷（PostgreSQL 数据、日志）

2. **验证部署**
   - 访问 `http://your-server-ip` 查看前端页面。
   - 访问 `http://your-server-ip/api/docs` 查看后端 API 文档。
   - 访问 `http://your-server-ip/api/health` 健康检查端点。
   - 检查 PostgreSQL：`docker exec kline-postgres pg_isready -U kline_user -d kline_db`

3. **停止服务**
   ```bash
   docker-compose down
   ```

## 数据持久化

- **数据库**: PostgreSQL 数据存储在 Docker 卷 `postgres_data` 中。备份命令：
  ```bash
  docker exec kline-postgres pg_dump -U kline_user kline_db > backup.sql
  ```
- **日志**: 日志存储在 `logs/` 目录。
- **图表文件**: 生成的图表文件存储在容器内 `static/` 目录，会定期自动清理。

## 数据库切换

如需使用 SQLite（开发/单机场景），在 `.env` 中设置：
```
DATABASE_TYPE=sqlite
```
此时 Docker Compose 不会启动 PostgreSQL 服务（需手动调整 depends_on）。

## 手动部署（不推荐）

如果不使用 Docker，您需要：
1. **PostgreSQL**: 安装并启动 PostgreSQL 16+，创建数据库和用户
2. **后端**: 安装 Python 3.12+，`pip install -r requirements.txt`，设置环境变量后启动 uvicorn
3. **前端**: 安装 Node.js 18+，`npm run build`，配置 Nginx 指向 `dist` 目录并反向代理 `/api`

## 维护

- **更新代码**: 拉取新代码后，重新运行 `docker-compose up -d --build`。
- **查看日志**: 
  ```bash
  docker-compose logs -f backend
  docker-compose logs -f frontend
  docker-compose logs -f postgres
  ```
- **数据库备份**:
  ```bash
  docker exec kline-postgres pg_dump -U kline_user kline_db > backup_$(date +%Y%m%d).sql
  ```
