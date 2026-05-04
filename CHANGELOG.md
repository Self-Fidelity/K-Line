# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.1.2] - 2026-05-04

### Fixed

#### Docker 部署
- **backend Dockerfile**: 添加缺失的 `colorama` 依赖，修复容器启动时 `ModuleNotFoundError`
- **nginx 配置**: 删除 `deploy/nginx.conf.template` 中重复的 `/api/` location，解决 `duplicate location` 导致 frontend 容器崩溃
- **健康检查端点**: `deploy/backend.Dockerfile` 与 `docker-compose.yml` 中的 healthcheck 从 `/docs` 更正为 `/health`
- **docker-compose 卷**: 移除未使用的 `data` 和 `logs` 命名卷声明，避免混淆

#### CLI 脚本
- `scripts/fetch_data.py`: 将硬编码的 `SQLiteStorage()` 替换为 `get_storage_instance()`，支持根据 `.env` 中的 `DATABASE_TYPE` 自动选择 PostgreSQL 或 SQLite
- `scripts/setup.py`: 同步支持 PostgreSQL 初始化，不再仅限 SQLite

#### PostgreSQL 存储层 (`src/data_storage/postgres_storage.py`)
- **users 表字段统一**: `password_hash` → `hashed_password`，与 SQLiteStorage 保持一致
- **aggregation_schemes 表重构**: 新增 `stock_code`、`required_strategies` 字段，移除 `weights`，支持按股票关联聚合方案
- **新增方法**: `set_default_param_set()` / `get_default_param_set()`，完善参数集管理
- **数据序列化**: aggregation_schemes 的 JSON 字段自动序列化/反序列化

#### API 模型
- `backend/app/models/auth.py`: `UserResponse.email` 改为 `Optional[str]`，兼容无邮箱场景

### Notes
- 首次使用 Docker Compose 部署时，若遇 Docker Hub 网络问题，可手动从国内镜像站拉取基础镜像后重打标签：
  ```bash
  docker pull docker.m.daocloud.io/library/python:3.12-slim && docker tag docker.m.daocloud.io/library/python:3.12-slim python:3.12-slim
  docker pull docker.m.daocloud.io/library/node:18-alpine && docker tag docker.m.daocloud.io/library/node:18-alpine node:18-alpine
  docker pull docker.m.daocloud.io/library/nginx:alpine && docker tag docker.m.daocloud.io/library/nginx:alpine nginx:alpine
  ```
