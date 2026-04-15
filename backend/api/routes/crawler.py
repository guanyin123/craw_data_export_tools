"""
爬虫控制路由

提供爬虫控制相关的 API 接口
"""
import asyncio
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from models.database import get_db
from models.models import Item
from crawler.zhihu import ZhihuCrawler
from crawler.bilibili import BilibiliCrawler
from crawler.config import default_zhihu_config, default_bilibili_config
from analyzer.keyword_counter import KeywordCounter
from api.schemas import CrawlerRunRequest, CrawlerStatus, CrawlerRunResponse

router = APIRouter()

# 爬虫状态
crawler_state = {
    "is_running": False,
    "platform": None,
    "last_run": None,
    "last_count": 0,
}

# 使用锁保护状态修改，防止竞态条件
crawler_lock = asyncio.Lock()


@router.get("/status", response_model=CrawlerStatus)
async def get_crawler_status():
    """
    获取爬虫运行状态
    """
    return CrawlerStatus(
        is_running=crawler_state["is_running"],
        platform=crawler_state["platform"],
        last_run=crawler_state["last_run"],
        last_count=crawler_state["last_count"],
    )


@router.post("/run", response_model=CrawlerRunResponse)
async def run_crawler(
    request: CrawlerRunRequest,
    background_tasks: BackgroundTasks,
    save: bool = Query(True, description="是否保存到数据库"),
    analyze: bool = Query(True, description="是否分析关键词"),
):
    """
    运行爬虫

    支持同步和异步运行
    """
    # 使用锁保护状态检查和修改
    async with crawler_lock:
        if crawler_state["is_running"]:
            raise HTTPException(status_code=409, detail="爬虫正在运行")

        platform = request.platform.lower()
        if platform not in ["zhihu", "bilibili"]:
            raise HTTPException(status_code=400, detail="不支持的平台")

        # 标记为运行中
        crawler_state["is_running"] = True
        crawler_state["platform"] = platform

    # 同步运行（小数据量）
    if request.limit <= 20:
        try:
            result = await _run_crawler_sync(platform, request.limit, save, analyze)
            return result
        finally:
            async with crawler_lock:
                crawler_state["is_running"] = False
                crawler_state["platform"] = None
    else:
        # 后台运行（大数据量）
        background_tasks.add_task(
            _run_crawler_background,
            platform,
            request.limit,
            save,
            analyze,
        )
        return CrawlerRunResponse(
            success=True,
            platform=platform,
            count=0,
            message=f"爬虫已在后台启动，预计抓取 {request.limit} 条数据",
        )


async def _run_crawler_sync(
    platform: str,
    limit: int,
    save: bool,
    analyze: bool,
) -> CrawlerRunResponse:
    """
    同步运行爬虫

    注意：状态管理由调用者 run_crawler 负责
    """
    try:
        if platform == "zhihu":
            config = default_zhihu_config
            config.max_items_per_run = limit
            async with ZhihuCrawler(config) as crawler:
                items = await crawler.crawl(limit=limit)
        else:  # bilibili
            config = default_bilibili_config
            config.max_items_per_run = limit
            async with BilibiliCrawler(config) as crawler:
                items = await crawler.crawl(limit=limit)

        count = len(items)

        # 保存到数据库（使用上下文管理器确保连接关闭）
        if save and items:
            from models.database import SessionLocal
            with SessionLocal() as db:
                try:
                    for item in items:
                        existing = db.query(Item).filter(Item.url == item.url).first()
                        if not existing:
                            db_item = Item(
                                platform=item.platform,
                                title=item.title,
                                content=item.content,
                                url=item.url,
                                score=item.score,
                                comment_count=item.comment_count,
                                author=item.author,
                                created_at=item.created_at or datetime.now(),
                                crawled_at=datetime.now(),
                            )
                            db.add(db_item)
                    db.commit()
                except Exception:
                    db.rollback()
                    raise

            # 分析关键词（使用上下文管理器确保连接关闭）
            if analyze:
                counter = KeywordCounter()
                with SessionLocal() as db:
                    try:
                        counter.analyze_new_items(db, limit=count)
                    except Exception:
                        db.rollback()
                        raise

        # 更新状态
        async with crawler_lock:
            crawler_state["last_run"] = datetime.now()
            crawler_state["last_count"] = count

        return CrawlerRunResponse(
            success=True,
            platform=platform,
            count=count,
            message=f"成功抓取 {count} 条数据",
        )

    except Exception as e:
        # 更新状态
        async with crawler_lock:
            crawler_state["is_running"] = False
            crawler_state["platform"] = None
        raise HTTPException(status_code=500, detail=f"爬虫运行失败: {str(e)}")


def _run_crawler_background(
    platform: str,
    limit: int,
    save: bool,
    analyze: bool,
):
    """
    后台运行爬虫

    注意：状态管理由调用者 run_crawler 负责
    """
    import logging

    try:
        if platform == "zhihu":
            config = default_zhihu_config
            config.max_items_per_run = limit
            # 在新的事件循环中运行
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                with ZhihuCrawler(config) as crawler:
                    items = loop.run_until_complete(crawler.crawl(limit=limit))
            finally:
                loop.close()
        else:  # bilibili
            config = default_bilibili_config
            config.max_items_per_run = limit
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                with BilibiliCrawler(config) as crawler:
                    items = loop.run_until_complete(crawler.crawl(limit=limit))
            finally:
                loop.close()

        count = len(items)

        # 保存到数据库（使用上下文管理器确保连接关闭）
        if save and items:
            from models.database import SessionLocal
            with SessionLocal() as db:
                try:
                    for item in items:
                        existing = db.query(Item).filter(Item.url == item.url).first()
                        if not existing:
                            db_item = Item(
                                platform=item.platform,
                                title=item.title,
                                content=item.content,
                                url=item.url,
                                score=item.score,
                                comment_count=item.comment_count,
                                author=item.author,
                                created_at=item.created_at or datetime.now(),
                                crawled_at=datetime.now(),
                            )
                            db.add(db_item)
                    db.commit()
                except Exception:
                    db.rollback()
                    raise

            # 分析关键词（使用上下文管理器确保连接关闭）
            if analyze:
                counter = KeywordCounter()
                with SessionLocal() as db:
                    try:
                        counter.analyze_new_items(db, limit=count)
                    except Exception:
                        db.rollback()
                        raise

        # 更新状态
        crawler_state["last_run"] = datetime.now()
        crawler_state["last_count"] = count

    except Exception as e:
        # 更新状态
        crawler_state["is_running"] = False
        crawler_state["platform"] = None
        logging.error(f"爬虫后台运行失败: {e}")
    finally:
        # 确保状态被重置
        crawler_state["is_running"] = False
        crawler_state["platform"] = None


@router.post("/analyze")
async def analyze_existing_data(
    limit: Optional[int] = Query(None, ge=1, le=1000, description="分析数量限制"),
    db: Session = Depends(get_db),
):
    """
    分析现有数据

    对数据库中未分析的内容进行关键词提取
    """
    try:
        counter = KeywordCounter()
        count = counter.analyze_new_items(db, limit=limit)

        # 获取关键词总数
        from models.models import Keyword
        keyword_count = db.query(Keyword).count()

        return {
            "success": True,
            "items_analyzed": count,
            "total_keywords": keyword_count,
            "message": f"成功分析 {count} 条内容",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.get("/platforms")
async def get_supported_platforms():
    """
    获取支持的爬虫平台列表
    """
    return {
        "platforms": [
            {
                "name": "zhihu",
                "display_name": "知乎",
                "description": "知乎热榜和高赞回答",
                "enabled": True,
            },
            {
                "name": "bilibili",
                "display_name": "B站",
                "description": "B站热门视频",
                "enabled": True,
            },
        ]
    }
