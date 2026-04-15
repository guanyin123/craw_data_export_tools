"""
内容路由

提供内容（items）相关的 API 接口
"""
from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from models.database import get_db
from models.models import Item, KeywordItem
from api.schemas import ItemResponse, ItemListResponse

router = APIRouter()


@router.get("", response_model=ItemListResponse)
async def list_items(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    platform: Optional[str] = Query(None, description="平台筛选: zhihu, bilibili"),
    min_score: int = Query(0, ge=0, description="最小热度"),
    keyword_id: Optional[int] = Query(None, description="关键词ID，获取关联内容"),
    db: Session = Depends(get_db),
):
    """
    获取内容列表

    支持分页、平台筛选、热度筛选、关键词筛选
    """
    query = db.query(Item)

    # 平台筛选
    if platform:
        query = query.filter(Item.platform == platform)

    # 热度筛选
    if min_score > 0:
        query = query.filter(Item.score >= min_score)

    # 关键词筛选
    if keyword_id:
        item_ids_subq = db.query(KeywordItem.item_id).filter(
            KeywordItem.keyword_id == keyword_id
        )
        query = query.filter(Item.id.in_(item_ids_subq))

    # 总数
    total = query.count()

    # 分页
    offset = (page - 1) * page_size
    items = query.order_by(Item.score.desc()).offset(offset).limit(page_size).all()

    return ItemListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items,
    )


@router.get("/recent")
async def get_recent_items(
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    platform: Optional[str] = Query(None, description="平台筛选"),
    hours: int = Query(24, ge=1, le=168, description="最近几小时"),
    db: Session = Depends(get_db),
):
    """
    获取最近的内容

    默认返回最近24小时的内容
    """
    start_time = datetime.now() - timedelta(hours=hours)

    query = db.query(Item).filter(Item.crawled_at >= start_time)

    if platform:
        query = query.filter(Item.platform == platform)

    items = query.order_by(Item.score.desc()).limit(limit).all()

    return items


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: int,
    db: Session = Depends(get_db),
):
    """
    获取内容详情

    包含完整内容和关联关键词
    """
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="内容不存在")

    return item


@router.get("/{item_id}/keywords")
async def get_item_keywords(
    item_id: int,
    db: Session = Depends(get_db),
):
    """
    获取内容关联的关键词

    返回该内容中提取的所有关键词
    """
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="内容不存在")

    keyword_items = db.query(KeywordItem).filter(
        KeywordItem.item_id == item_id
    ).all()

    from models.models import Keyword
    keyword_ids = [ki.keyword_id for ki in keyword_items]
    keywords = db.query(Keyword).filter(Keyword.id.in_(keyword_ids)).all()

    # 构建 keyword_id 到 KeywordItem 的映射，避免嵌套循环
    keyword_item_map = {ki.keyword_id: ki for ki in keyword_items}

    return [
        {
            "id": kw.id,
            "word": kw.word,
            "count": kw.count,
            "category": kw.category,
            "score": keyword_item_map.get(kw.id).score if kw.id in keyword_item_map else None,
        }
        for kw in keywords
    ]
