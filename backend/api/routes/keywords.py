"""
关键词路由

提供关键词相关的 API 接口
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.database import get_db
from models.models import Keyword, Item, KeywordItem
from api.schemas import (
    KeywordResponse,
    KeywordUpdate,
    KeywordWithItems,
    KeywordStats,
    ItemLite,
)

router = APIRouter()


@router.get("", response_model=list[KeywordResponse])
async def list_keywords(
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    category: Optional[str] = Query(None, description="分类筛选"),
    min_count: int = Query(0, ge=0, description="最小出现次数"),
    db: Session = Depends(get_db),
):
    """
    获取关键词榜单

    按出现次数降序排列
    """
    query = db.query(Keyword)

    if category:
        query = query.filter(Keyword.category == category)
    if min_count > 0:
        query = query.filter(Keyword.count >= min_count)

    keywords = query.order_by(Keyword.count.desc()).limit(limit).all()
    return keywords


@router.get("/stats", response_model=KeywordStats)
async def get_keyword_stats(
    db: Session = Depends(get_db),
):
    """
    获取关键词统计信息

    返回总数和按分类统计
    """
    total = db.query(Keyword).count()

    # 按分类统计
    category_stats = db.query(
        Keyword.category,
        func.count(Keyword.id)
    ).group_by(Keyword.category).all()

    by_category = {cat or "OTHER": count for cat, count in category_stats}

    return KeywordStats(total=total, by_category=by_category)


@router.get("/{keyword_id}", response_model=KeywordWithItems)
async def get_keyword(
    keyword_id: int,
    limit: int = Query(20, ge=1, le=100, description="关联内容数量"),
    db: Session = Depends(get_db),
):
    """
    获取关键词详情

    包含关联的内容列表
    """
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="关键词不存在")

    # 获取关联内容（按热度排序）
    keyword_items = db.query(KeywordItem).filter(
        KeywordItem.keyword_id == keyword_id
    ).order_by(KeywordItem.score.desc()).limit(limit).all()

    item_ids = [ki.item_id for ki in keyword_items]
    items = db.query(Item).filter(Item.id.in_(item_ids)).all()
    item_map = {item.id: item for item in items}

    # 按 KeywordItem 的顺序组装内容
    item_list = []
    for ki in keyword_items:
        item = item_map.get(ki.item_id)
        if item:
            item_list.append(ItemLite(
                id=item.id,
                title=item.title,
                platform=item.platform,
                score=item.score,
                url=item.url,
            ))

    return KeywordWithItems(
        id=keyword.id,
        word=keyword.word,
        count=keyword.count,
        category=keyword.category,
        first_seen=keyword.first_seen,
        last_seen=keyword.last_seen,
        items=item_list,
    )


@router.patch("/{keyword_id}", response_model=KeywordResponse)
async def update_keyword(
    keyword_id: int,
    update: KeywordUpdate,
    db: Session = Depends(get_db),
):
    """
    更新关键词分类

    支持手动修改关键词的分类
    """
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="关键词不存在")

    if update.category is not None:
        keyword.category = update.category

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"数据库错误: {str(e)}")

    db.refresh(keyword)

    return keyword


@router.delete("/{keyword_id}")
async def delete_keyword(
    keyword_id: int,
    db: Session = Depends(get_db),
):
    """
    删除关键词

    会级联删除关联的趋势和内容关联
    """
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="关键词不存在")

    try:
        db.delete(keyword)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"数据库错误: {str(e)}")

    return {"message": "关键词已删除"}
