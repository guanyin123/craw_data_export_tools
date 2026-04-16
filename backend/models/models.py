"""
数据模型定义
"""
from datetime import datetime, date
from sqlalchemy import (
    String, Integer, Text, DateTime, Date, Float, ForeignKey, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Item(Base):
    """
    原始数据表 - 存储爬取的内容
    """
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    platform: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # 'zhihu' | 'bilibili'
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)  # 回答内容/评论内容
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)  # 点赞数
    comment_count: Mapped[int] = mapped_column(Integer, default=0)
    comment_summary: Mapped[str | None] = mapped_column(Text, nullable=True)  # 评论摘要（汇总前10条高赞评论）
    top_comment_score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 最高赞评论点赞数
    author: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    crawled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)

    # 关联关系
    keyword_items: Mapped[list["KeywordItem"]] = relationship(
        back_populates="item", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_platform_crawled", "platform", "crawled_at"),
        Index("idx_score_created", "score", "created_at"),  # 按热度排序查询
        Index("idx_platform_score", "platform", "score"),    # 平台内热门内容
        CheckConstraint("score >= 0", name="check_score_non_negative"),
        CheckConstraint("comment_count >= 0", name="check_comment_count_non_negative"),
    )

    def __repr__(self) -> str:
        return f"<Item(id={self.id}, platform={self.platform}, title={self.title[:20]}...)>"


class Keyword(Base):
    """
    关键词统计表
    """
    __tablename__ = "keywords"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    word: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)  # 增加长度支持短语
    count: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # 出现次数
    category: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # TOOL/CONTENT/SERVICE/PRODUCT/LIFESTYLE/CAREER/OTHER
    first_seen: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_seen: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # 关联关系
    keyword_items: Mapped[list["KeywordItem"]] = relationship(
        back_populates="keyword", cascade="all, delete-orphan"
    )
    trends: Mapped[list["Trend"]] = relationship(
        back_populates="keyword", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_count", "count"),
        Index("idx_category_count", "category", "count"),  # 分类筛选+排序优化
        CheckConstraint("count >= 0", name="check_count_non_negative"),
    )

    def __repr__(self) -> str:
        return f"<Keyword(id={self.id}, word={self.word}, count={self.count}, category={self.category})>"


class Trend(Base):
    """
    趋势数据表
    """
    __tablename__ = "trends"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    keyword_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("keywords.id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False)  # 当天出现次数
    avg_score: Mapped[float | None] = mapped_column(Float, nullable=True)  # 平均热度

    # 关联关系
    keyword: Mapped["Keyword"] = relationship(back_populates="trends")

    __table_args__ = (
        Index("idx_keyword_date", "keyword_id", "date"),
        UniqueConstraint("keyword_id", "date", name="uq_keyword_date"),
        CheckConstraint("count >= 0", name="check_trend_count_non_negative"),
    )

    def __repr__(self) -> str:
        return f"<Trend(id={self.id}, keyword_id={self.keyword_id}, date={self.date}, count={self.count})>"


class KeywordItem(Base):
    """
    关键词-内容关联表
    """
    __tablename__ = "keyword_items"

    keyword_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("keywords.id", ondelete="CASCADE"), primary_key=True
    )
    item_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("items.id", ondelete="CASCADE"), primary_key=True
    )
    score: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # 该关键词在此item中的权重

    # 关联关系
    keyword: Mapped["Keyword"] = relationship(back_populates="keyword_items")
    item: Mapped["Item"] = relationship(back_populates="keyword_items")

    __table_args__ = (
        Index("idx_keyword_item_keyword", "keyword_id"),
        Index("idx_keyword_item_item", "item_id"),
        CheckConstraint("score IS NULL OR score >= 0", name="check_keyword_item_score_non_negative"),
    )

    def __repr__(self) -> str:
        return f"<KeywordItem(keyword_id={self.keyword_id}, item_id={self.item_id}, score={self.score})>"
