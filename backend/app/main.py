"""FastAPI 主应用"""

import logging
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.app.config import settings

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 速率限制器
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

# 创建FastAPI应用
app = FastAPI(
    title="K-Line API",
    description="K线数据和策略分析API",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# 注册速率限制器
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 配置CORS - 生产环境限制来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


# 请求日志和计时中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有API请求及其响应时间"""
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    # 跳过静态文件和文档请求
    if not request.url.path.startswith(("/static/", "/docs", "/redoc", "/openapi.json")):
        logger.info(
            "request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round(duration * 1000, 2),
                "client": request.client.host if request.client else "unknown",
            },
        )

    return response


@app.get("/")
async def root():
    """根路径"""
    return JSONResponse(
        content={
            "message": "K-Line API",
            "version": "1.0.0",
            "docs": "/docs",
        }
    )


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return JSONResponse(content={"status": "healthy"})


# 导入路由
from backend.app.api import (
    auth,
    data,
    strategy,
    chart,
    batch_analysis,
    data_update,
    custom_strategy,
    watchlist,
    strategy_aggregation,
    param_sets,
    aggregation_schemes,
    users,
    logs
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(users.router, prefix="/api/admin/users", tags=["用户管理"])
app.include_router(data.router, prefix="/api/data", tags=["数据"])
app.include_router(strategy.router, prefix="/api/strategy", tags=["策略"])
app.include_router(chart.router, prefix="/api/chart", tags=["图表"])
app.include_router(batch_analysis.router, prefix="/api/batch-analysis", tags=["批量分析"])
app.include_router(data_update.router, prefix="/api/admin/data-update", tags=["数据更新管理"])
app.include_router(custom_strategy.router, prefix="/api/custom-strategy", tags=["自定义策略"])
app.include_router(watchlist.router, prefix="/api/watchlist", tags=["自选股"])
app.include_router(strategy_aggregation.router, prefix="/api/strategy-aggregation", tags=["策略聚合"])
app.include_router(param_sets.router, prefix="/api/strategy", tags=["参数集管理"])
app.include_router(aggregation_schemes.router, prefix="/api/strategy/aggregation-schemes", tags=["聚合策略方案"])
app.include_router(logs.router, prefix="/api/logs", tags=["系统日志"])



# 挂载静态文件目录（用于图表HTML文件）
# 添加src目录到路径以获取IMAGES_DIR
backend_dir = Path(__file__).parent.parent
src_dir = backend_dir.parent / "src"
sys.path.insert(0, str(src_dir))
from src.config import settings as src_settings

# 确保目录存在
src_settings.IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# 挂载静态文件目录
try:
    app.mount("/charts", StaticFiles(directory=str(src_settings.IMAGES_DIR)), name="charts")
except ValueError:
    # 如果已经挂载，忽略错误
    pass
