# 故障排除

## Error Code -102

### 问题描述
访问 http://localhost:5173/ 时出现 Error Code -102（连接被拒绝）

### 原因
端口5173被其他进程占用，Vite开发服务器无法在该端口启动，自动切换到了其他端口（如5174）

### 解决方案

#### 方案1：访问实际运行的端口（推荐）
1. 查看运行 `npm run dev` 的终端输出
2. 找到 "Local: http://localhost:XXXX/" 这一行
3. 访问该URL（通常是 http://localhost:5174/）

#### 方案2：释放5173端口
1. 查找占用5173端口的进程：
   ```powershell
   netstat -ano | findstr ":5173"
   ```

2. 停止该进程（替换PID为实际进程ID）：
   ```powershell
   taskkill /PID <PID> /F
   ```

3. 重新运行：
   ```powershell
   npm run dev
   ```

#### 方案3：修改配置使用其他端口
编辑 `vite.config.ts`，修改 `server.port` 为其他端口（如5175）
