# K-Line Frontend

Vue 3 + TypeScript 前端应用

## 安装依赖

```bash
npm install
```

## 开发

```bash
npm run dev
```

前端开发服务器将运行在 http://localhost:5173

如果端口被占用，Vite会自动使用下一个可用端口（如 5174）

## 构建

```bash
npm run build
```

## 预览构建结果

```bash
npm run preview
```

## 常见问题

### 端口被占用

如果端口5173被占用，可以：

1. 停止占用进程：
   ```powershell
   # 查找占用端口的进程
   netstat -ano | findstr ":5173"
   
   # 停止进程（替换PID为实际进程ID）
   taskkill /PID <PID> /F
   ```

2. 或者访问Vite自动切换的端口（通常是5174）

3. 或者修改 `vite.config.ts` 中的端口号

### Error Code -102

这表示连接被拒绝，通常是因为：
- 前端开发服务器没有运行
- 访问的端口不对（应该访问Vite输出的实际端口）
- 端口被其他进程占用

确保：
1. 运行了 `npm run dev`
2. 访问Vite输出的实际URL（查看终端输出）
