"""
FastAPI 主入口文件

Web 服务入口，配置 CORS 和路由
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models.database import engine, Base
from api.routes import keywords, items, trends, crawler


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    应用生命周期管理

    启动时创建数据库表，关闭时清理连接
    """
    # 启动时：确保数据库表存在
    Base.metadata.create_all(bind=engine)
    yield
    # 关闭时：清理资源（如果需要）


# 创建 FastAPI 应用
app = FastAPI(
    title="商机发现 API",
    description="通过爬取知乎、B站等平台的热门内容，分析用户需求，发现副业/创业机会",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite default
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(keywords.router, prefix="/api/keywords", tags=["关键词"])
app.include_router(items.router, prefix="/api/items", tags=["内容"])
app.include_router(trends.router, prefix="/api/trends", tags=["趋势"])
app.include_router(crawler.router, prefix="/api/crawler", tags=["爬虫"])


@app.get("/")
async def root():
    """根路径 - API 信息"""
    return {
        "name": "商机发现 API",
        "version": "0.1.0",
        "description": "通过爬取知乎、B站等平台的热门内容，分析用户需求，发现副业/创业机会",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok"}


def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = True):
    """
    运行开发服务器

    Args:
        host: 监听地址
        port: 监听端口
        reload: 热重载
    """
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    run_server()
