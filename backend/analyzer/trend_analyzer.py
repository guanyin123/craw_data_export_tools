"""
趋势分析模块

分析关键词的时间趋势变化
"""
import logging
from collections import defaultdict
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.models import Item, Keyword, Trend, KeywordItem

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """
    趋势分析器

    功能:
    - 按日期统计关键词出现次数
    - 计算热度趋势
    - 识别上升趋势的关键词
    """

    def __init__(self):
        """初始化趋势分析器"""
        pass

    def analyze_daily_trends(
        self,
        db: Session,
        target_date: Optional[date] = None
    ) -> int:
        """
        分析指定日期的关键词趋势

        Args:
            db: 数据库会话
            target_date: 目标日期，默认为昨天

        Returns:
            int: 创建的趋势记录数
        """
        if target_date is None:
            target_date = (datetime.now() - timedelta(days=1)).date()

        logger.info(f"开始分析 {target_date} 的趋势...")

        # 获取指定日期的所有内容
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = datetime.combine(target_date, datetime.max.time())

        items = db.query(Item).filter(
            Item.crawled_at >= start_datetime,
            Item.crawled_at <= end_datetime
        ).all()

        if not items:
            logger.info(f"日期 {target_date} 没有数据")
            return 0

        # 统计每个关键词的出现次数和平均热度
        # 使用批量查询避免 N+1 问题
        item_ids = [item.id for item in items]

        # 一次性获取所有关键词关联
        all_keyword_items = db.query(KeywordItem).filter(
            KeywordItem.item_id.in_(item_ids)
        ).all()

        # 构建item_id到KeywordItem的映射
        item_to_keywords: Dict[int, List[KeywordItem]] = defaultdict(list)
        for ki in all_keyword_items:
            item_to_keywords[ki.item_id].append(ki)

        # 创建item快速查找表
        item_map = {item.id: item for item in items}

        keyword_stats = defaultdict(lambda: {"count": 0, "total_score": 0})

        for ki in all_keyword_items:
            item = item_map.get(ki.item_id)
            if item:
                keyword_stats[ki.keyword_id]["count"] += 1
                keyword_stats[ki.keyword_id]["total_score"] += item.score

        # 创建或更新趋势记录
        count = 0
        for keyword_id, stats in keyword_stats.items():
            avg_score = stats["total_score"] / stats["count"] if stats["count"] > 0 else 0

            # 检查是否已存在
            existing = db.query(Trend).filter(
                Trend.keyword_id == keyword_id,
                Trend.date == target_date
            ).first()

            if not existing:
                trend = Trend(
                    keyword_id=keyword_id,
                    date=target_date,
                    count=stats["count"],
                    avg_score=avg_score
                )
                db.add(trend)
                count += 1
            else:
                # 更新已存在的记录
                existing.count = stats["count"]
                existing.avg_score = avg_score

        try:
            db.commit()
            logger.info(f"趋势分析完成: 创建/更新 {count} 条记录")
        except Exception as e:
            db.rollback()
            logger.error(f"趋势分析失败: {e}")
            raise

        return count

    def analyze_recent_trends(
        self,
        db: Session,
        days: int = 7
    ) -> Dict[str, List[Dict]]:
        """
        分析最近几天的趋势

        Args:
            db: 数据库会话
            days: 分析天数

        Returns:
            Dict[str, List[Dict]]: 关键词趋势数据
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        # 获取趋势数据
        trends = db.query(Trend).filter(
            Trend.date >= start_date,
            Trend.date <= end_date
        ).order_by(Trend.date, Trend.count.desc()).all()

        # 按日期分组
        result = defaultdict(list)
        for trend in trends:
            keyword = db.query(Keyword).filter(Keyword.id == trend.keyword_id).first()
            if keyword:
                result[str(trend.date)].append({
                    "keyword": keyword.word,
                    "count": trend.count,
                    "avg_score": trend.avg_score,
                })

        return dict(result)

    def get_rising_keywords(
        self,
        db: Session,
        days: int = 7,
        limit: int = 20
    ) -> List[Dict]:
        """
        获取上升趋势的关键词

        Args:
            db: 数据库会话
            days: 对比天数
            limit: 返回数量

        Returns:
            List[Dict]: 上升趋势的关键词列表
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        prev_start_date = start_date - timedelta(days=days)

        # 当前周期的关键词统计
        current_stats = self._get_period_stats(db, start_date, end_date)

        # 之前周期的关键词统计
        previous_stats = self._get_period_stats(db, prev_start_date, start_date)

        # 批量获取所有关键词详情，避免 N+1 查询
        all_keyword_ids = list(current_stats.keys())
        keywords = db.query(Keyword).filter(Keyword.id.in_(all_keyword_ids)).all()
        keyword_map = {k.id: k for k in keywords}

        # 计算增长率
        rising_keywords = []
        for keyword_id, current_data in current_stats.items():
            previous_data = previous_stats.get(keyword_id, {"count": 0, "avg_score": 0})

            current_count = current_data["count"]
            previous_count = previous_data["count"]

            if previous_count == 0:
                # 使用一个大的有限值代替无穷大，便于 JSON 序列化
                growth_rate = 999.0 if current_count > 0 else 0
            else:
                growth_rate = (current_count - previous_count) / previous_count

            # 只包含增长的关键词
            if growth_rate > 0 and current_count >= 2:
                keyword = keyword_map.get(keyword_id)
                if keyword:
                    rising_keywords.append({
                        "keyword": keyword.word,
                        "current_count": current_count,
                        "previous_count": previous_count,
                        "growth_rate": growth_rate,
                        "avg_score": current_data["avg_score"],
                    })

        # 按增长率排序
        rising_keywords.sort(key=lambda x: x["growth_rate"], reverse=True)

        return rising_keywords[:limit]

    def _get_period_stats(
        self,
        db: Session,
        start_date: date,
        end_date: date
    ) -> Dict[int, Dict]:
        """
        获取指定时间段的统计

        Args:
            db: 数据库会话
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            Dict[int, Dict]: {keyword_id: {count, avg_score}}
        """
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())

        # 获取该时段的内容
        items = db.query(Item).filter(
            Item.crawled_at >= start_datetime,
            Item.crawled_at <= end_datetime
        ).all()

        # 统计关键词 - 使用批量查询避免 N+1 问题
        item_ids = [item.id for item in items]

        # 一次性获取所有关键词关联
        all_keyword_items = db.query(KeywordItem).filter(
            KeywordItem.item_id.in_(item_ids)
        ).all()

        # 创建item快速查找表
        item_map = {item.id: item for item in items}

        stats = defaultdict(lambda: {"count": 0, "total_score": 0})

        for ki in all_keyword_items:
            item = item_map.get(ki.item_id)
            if item:
                stats[ki.keyword_id]["count"] += 1
                stats[ki.keyword_id]["total_score"] += item.score

        # 计算平均分
        result = {}
        for keyword_id, data in stats.items():
            result[keyword_id] = {
                "count": data["count"],
                "avg_score": data["total_score"] / data["count"] if data["count"] > 0 else 0
            }

        return result

    def get_hot_keywords(
        self,
        db: Session,
        days: int = 1,
        limit: int = 50
    ) -> List[Keyword]:
        """
        获取热门关键词

        Args:
            db: 数据库会话
            days: 最近天数
            limit: 返回数量

        Returns:
            List[Keyword]: 热门关键词列表
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())

        # 获取该时段的内容ID
        item_ids = db.query(Item.id).filter(
            Item.crawled_at >= start_datetime,
            Item.crawled_at <= end_datetime
        ).all()

        if not item_ids:
            return []

        item_ids = [id for id, in item_ids]

        # 统计关键词出现次数
        keyword_counts = db.query(
            KeywordItem.keyword_id,
            func.count(KeywordItem.item_id).label('count')
        ).filter(
            KeywordItem.item_id.in_(item_ids)
        ).group_by(KeywordItem.keyword_id).order_by(
            func.count(KeywordItem.item_id).desc()
        ).limit(limit).all()

        if not keyword_counts:
            return []

        # 批量获取所有关键词详情，避免 N+1 查询
        keyword_ids = [kid for kid, _ in keyword_counts]
        keywords = db.query(Keyword).filter(Keyword.id.in_(keyword_ids)).all()
        keyword_map = {k.id: k for k in keywords}

        # 按统计顺序返回结果
        result = []
        for keyword_id, count in keyword_counts:
            keyword = keyword_map.get(keyword_id)
            if keyword:
                result.append(keyword)

        return result


# 默认趋势分析器实例
default_trend_analyzer = TrendAnalyzer()
