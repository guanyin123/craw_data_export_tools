"""
趋势路由

提供趋势分析相关的 API 接口
"""
from typing import Optional
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from models.database import get_db
from models.models import Trend, Keyword
from analyzer.trend_analyzer import TrendAnalyzer
from api.schemas import TrendResponse, RisingKeyword

router = APIRouter()

# 创建趋势分析器实例
trend_analyzer = TrendAnalyzer()


@router.get("/daily/{target_date}", response_model=list[TrendResponse])
async def get_daily_trends(
    target_date: date,
    limit: int = Query(50, ge=1, le=200, description="返回数量"),
    db: Session = Depends(get_db),
):
    """
    获取指定日期的趋势数据

    返回该日期关键词出现次数最多的趋势
    """
    trends = db.query(Trend).filter(
        Trend.date == target_date
    ).order_by(Trend.count.desc()).limit(limit).all()

    return trends


@router.get("/recent")
async def get_recent_trends(
    days: int = Query(7, ge=1, le=30, description="最近天数"),
    db: Session = Depends(get_db),
):
    """
    获取最近几天的趋势数据

    按日期分组返回趋势
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    trends = db.query(Trend).filter(
        Trend.date >= start_date,
        Trend.date <= end_date
    ).order_by(Trend.date, Trend.count.desc()).all()

    # 批量获取所有关键词，避免 N+1 查询
    if trends:
        keyword_ids = list(set(t.keyword_id for t in trends))
        keywords = db.query(Keyword).filter(Keyword.id.in_(keyword_ids)).all()
        keyword_map = {k.id: k for k in keywords}
    else:
        keyword_map = {}

    # 按日期分组
    result = {}
    for trend in trends:
        date_str = str(trend.date)
        if date_str not in result:
            result[date_str] = []

        keyword = keyword_map.get(trend.keyword_id)
        if keyword:
            result[date_str].append({
                "id": trend.id,
                "keyword": keyword.word,
                "keyword_id": trend.keyword_id,
                "count": trend.count,
                "avg_score": trend.avg_score,
            })

    return result


@router.get("/rising", response_model=list[RisingKeyword])
async def get_rising_keywords(
    days: int = Query(7, ge=1, le=30, description="对比天数"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    db: Session = Depends(get_db),
):
    """
    获取上升趋势的关键词

    对比最近两个周期，找出增长最快的关键词
    """
    rising = trend_analyzer.get_rising_keywords(db, days=days, limit=limit)
    return rising


@router.get("/hot")
async def get_hot_keywords(
    days: int = Query(1, ge=1, le=7, description="最近天数"),
    limit: int = Query(50, ge=1, le=200, description="返回数量"),
    db: Session = Depends(get_db),
):
    """
    获取热门关键词

    基于最近几天的内容统计
    """
    keywords = trend_analyzer.get_hot_keywords(db, days=days, limit=limit)

    return [
        {
            "id": kw.id,
            "word": kw.word,
            "count": kw.count,
            "category": kw.category,
        }
        for kw in keywords
    ]


@router.post("/analyze")
async def analyze_trends(
    target_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """
    分析指定日期的趋势

    手动触发趋势分析，更新趋势数据
    """
    try:
        count = trend_analyzer.analyze_daily_trends(db, target_date)
        return {
            "success": True,
            "message": f"趋势分析完成",
            "date": target_date or date.today(),
            "count": count,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.get("/keyword/{keyword_id}")
async def get_keyword_trend(
    keyword_id: int,
    days: int = Query(30, ge=1, le=90, description="查询天数"),
    db: Session = Depends(get_db),
):
    """
    获取指定关键词的趋势历史

    返回该关键词在最近几天的趋势变化
    """
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="关键词不存在")

    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    trends = db.query(Trend).filter(
        Trend.keyword_id == keyword_id,
        Trend.date >= start_date,
        Trend.date <= end_date
    ).order_by(Trend.date).all()

    return {
        "keyword": keyword.word,
        "keyword_id": keyword_id,
        "category": keyword.category,
        "trends": [
            {
                "date": str(trend.date),
                "count": trend.count,
                "avg_score": trend.avg_score,
            }
            for trend in trends
        ],
    }
