"""FastAPI应用入口"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import sys

from backend.app.config import settings

# 创建FastAPI应用
app = FastAPI(
    title="K-Line API",
    description="中国股市数据获取和策略分析API",
    version="0.1.0",
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """根路径"""
    return JSONResponse(
        content={
            "message": "K-Line API",
            "version": "0.1.0",
            "docs": "/docs",
        }
    )


@app.get("/health")
async def health_check():
    """健康检查"""
    return JSONResponse(content={"status": "healthy"})


# 导入路由
from backend.app.api import auth, data, strategy, chart, batch_analysis, data_update, custom_strategy, watchlist, strategy_aggregation

app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(data.router, prefix="/api/data", tags=["数据"])
app.include_router(strategy.router, prefix="/api/strategy", tags=["策略"])
app.include_router(chart.router, prefix="/api/chart", tags=["图表"])
app.include_router(batch_analysis.router, prefix="/api/batch-analysis", tags=["批量分析"])
app.include_router(data_update.router, prefix="/api/admin/data-update", tags=["数据更新管理"])
app.include_router(custom_strategy.router, prefix="/api/custom-strategy", tags=["自定义策略"])
app.include_router(watchlist.router, prefix="/api/watchlist", tags=["自选股"])
app.include_router(strategy_aggregation.router, prefix="/api/strategy-aggregation", tags=["策略聚合"])

# 启动数据更新服务
from backend.app.services.data_update_service import DataUpdateService
update_service = DataUpdateService()
update_service.start_scheduler()

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
