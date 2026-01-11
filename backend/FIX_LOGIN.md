# 登录问题修复说明

## 问题描述
使用 admin/admin 登录时提示"登录失败，请检查用户名和密码"

## 问题原因
`get_user_by_username` 函数在数据库连接没有设置 `row_factory` 时，返回的是 tuple，不能直接用 `dict(row)` 转换。

## 修复方案
已更新 `backend/app/api/auth.py` 中的 `get_user_by_username` 函数，使其同时支持 Row 对象和 tuple。

## 使用方法
1. **重启后端服务器**（如果正在运行）
2. 使用以下凭据登录：
   - 用户名：`admin`
   - 密码：`admin`

## 验证步骤
1. 确保数据库已初始化：`python backend/scripts/init_db.py`
2. 确保后端服务正在运行：`uvicorn backend.app.main:app --reload`
3. 访问前端登录页面：http://localhost:5173/login
4. 使用 admin/admin 登录
