"""
FastAPI主应用入口
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uuid
import uvicorn

from app.core.config import settings
from app.db.database import init_db
from app.api import users_router, detection_router, tasks_router, call_records_router

from app.core.logger import setup_logging, logger, request_id_ctx

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 1. 初始化日志系统
    setup_logging(level="INFO" if not settings.DEBUG else "DEBUG")
    
    logger.info("🚀 应用正在启动...")
    try:
        await init_db()
        logger.info("✅ 数据库初始化完成")
    except Exception as e:
        logger.error(f"❌ 数据库连接失败: {e}")
    
    yield
    
    logger.info("🛑 应用正在关闭...")


# 创建FastAPI应用实例
app = FastAPI(
    title=settings.APP_NAME,  
    version=settings.APP_VERSION,
    description="AI伪造检测与诈骗预警系统后端API",
    lifespan=lifespan
)


# =========================================================
# [关键修改] 中间件：注入 Request ID
# =========================================================
@app.middleware("http")
async def logger_middleware(request: Request, call_next):
    # 1. 生成 8位 唯一请求ID
    req_id = str(uuid.uuid4())[:8]
    
    # 2. 设置到 ContextVar (这一步很关键，后续所有日志都会带上这个ID)
    token = request_id_ctx.set(req_id)
    
    logger.info(f"➡️ 请求开始: {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        logger.info(f"⬅️ 请求结束: status={response.status_code}")
        return response
    except Exception as e:
        logger.exception(f"❌ 请求处理异常: {e}")
        raise
    finally:
        # 3. 重置上下文
        request_id_ctx.reset(token)


# CORS中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(users_router)
app.include_router(detection_router)
app.include_router(tasks_router)
app.include_router(call_records_router)


@app.get("/")
async def root():
    """根路径"""
    logger.info("访问了根路径") # 测试日志
    return {
        "message": "AI Anti-Fraud Detection System API",
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)