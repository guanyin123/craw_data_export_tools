"""
关键词统计模块

对爬取的内容进行分词、词频统计，并更新数据库
"""
import logging
from collections import Counter
from datetime import datetime, date
from typing import List, Dict, Optional

from sqlalchemy.orm import Session

from .tokenizer import Tokenizer, default_tokenizer
from .phrase_extractor import default_phrase_extractor
from models.models import Item, Keyword, KeywordItem

logger = logging.getLogger(__name__)


class KeywordCounter:
    """
    关键词统计器

    功能:
    - 统计词频
    - 更新关键词表
    - 建立关键词-内容关联
    """

    def __init__(self, tokenizer: Optional[Tokenizer] = None):
        """
        初始化关键词统计器

        Args:
            tokenizer: 分词器，默认使用 default_tokenizer
        """
        self.tokenizer = tokenizer or default_tokenizer
        self.phrase_extractor = default_phrase_extractor

    def extract_keywords_from_item(
        self,
        item: Item,
        min_length: int = 2,
        top_k: int = 10
    ) -> List[tuple[str, int]]:
        """
        从单条内容中提取关键词

        Args:
            item: 内容对象
            min_length: 最小词长度
            top_k: 返回前k个关键词

        Returns:
            List[tuple[str, int]]: (关键词, 权重) 列表
        """
        if not item.title and not item.content:
            return []

        result = []

        # 方法1: 从标题提取短语
        title_phrases = default_phrase_extractor.extract_from_title(item.title or "")
        for phrase in title_phrases:
            if len(phrase) >= min_length:
                result.append((phrase, 5))  # 标题短语权重较高

        # 方法2: 从内容提取短语
        if item.content:
            content_phrases = default_phrase_extractor.extract_from_content(item.content, top_k=top_k)
            for phrase, weight in content_phrases:
                if len(phrase) >= min_length:
                    result.append((phrase, weight))

        # 方法3: 传统 TF-IDF 提取（补充）
        text = f"{item.title or ''} {item.content or ''}"
        if text.strip():
            keywords = self.tokenizer.extract_tags(text, top_k=top_k, with_weight=True)
            for word, weight in keywords:
                if len(word) >= min_length:
                    score = int(weight * 10)
                    result.append((word, score))

        # 去重，保留最高权重
        seen = {}
        for word, score in result:
            if word not in seen or score > seen[word]:
                seen[word] = score

        # 按权重排序
        sorted_results = sorted(seen.items(), key=lambda x: x[1], reverse=True)
        return sorted_results[:top_k]

    def count_from_items(
        self,
        items: List[Item],
        db: Session
    ) -> Dict[str, int]:
        """
        统计多个内容的词频

        Args:
            items: 内容列表
            db: 数据库会话

        Returns:
            Dict[str, int]: 词频字典
        """
        word_count = Counter()
        item_keywords: Dict[int, List[tuple[str, int]]] = {}

        for item in items:
            keywords = self.extract_keywords_from_item(item)
            item_keywords[item.id] = keywords

            for word, score in keywords:
                word_count[word] += score

        # 更新数据库
        self._update_keywords(word_count, item_keywords, db)

        return dict(word_count)

    def _classify_keyword(self, word: str) -> str | None:
        """使用智能分类器分类关键词"""
        from .classifier import default_classifier
        category = default_classifier.classify(word)
        return category.value if category.value != "OTHER" else None

    def _update_keywords(
        self,
        word_count: Counter,
        item_keywords: Dict[int, List[tuple[str, int]]],
        db: Session
    ):
        """
        更新关键词表和关联表

        Args:
            word_count: 词频统计
            item_keywords: 每个内容的关键词
            db: 数据库会话
        """
        now = datetime.now()

        # 1. 更新或创建关键词
        keyword_ids: Dict[str, int] = {}

        for word, count in word_count.items():
            # 查找或创建关键词
            keyword = db.query(Keyword).filter(Keyword.word == word).first()

            if keyword:
                # 更新已有关键词
                keyword.count += count
                keyword.last_seen = now
            else:
                # 创建新关键词
                keyword = Keyword(
                    word=word,
                    count=count,
                    category=self._classify_keyword(word),
                    first_seen=now,
                    last_seen=now
                )
                db.add(keyword)
                db.flush()  # 获取ID

            keyword_ids[word] = keyword.id

        # 2. 更新关键词-内容关联
        for item_id, keywords in item_keywords.items():
            for word, score in keywords:
                if word not in keyword_ids:
                    continue

                keyword_id = keyword_ids[word]

                # 检查关联是否已存在
                existing = db.query(KeywordItem).filter(
                    KeywordItem.keyword_id == keyword_id,
                    KeywordItem.item_id == item_id
                ).first()

                if not existing:
                    # 创建关联
                    keyword_item = KeywordItem(
                        keyword_id=keyword_id,
                        item_id=item_id,
                        score=score
                    )
                    db.add(keyword_item)

        try:
            db.commit()
            logger.info(f"更新关键词完成: {len(keyword_ids)} 个关键词")
        except Exception as e:
            db.rollback()
            logger.error(f"更新关键词失败: {e}")
            raise

    def analyze_new_items(
        self,
        db: Session,
        limit: Optional[int] = None
    ) -> int:
        """
        分析数据库中新增的、未分析的内容

        Args:
            db: 数据库会话
            limit: 最大处理数量

        Returns:
            int: 处理的内容数量
        """
        # 获取未分析的内容（没有关键词关联的）
        # 使用 LEFT JOIN 代替 NOT IN 子查询，性能更好
        unanalyzed_items = db.query(Item).outerjoin(
            KeywordItem, Item.id == KeywordItem.item_id
        ).filter(
            KeywordItem.item_id.is_(None)
        ).order_by(Item.score.desc()).limit(limit).all()

        if not unanalyzed_items:
            logger.info("没有需要分析的新内容")
            return 0

        logger.info(f"开始分析 {len(unanalyzed_items)} 条新内容...")

        # 统计关键词
        word_count = self.count_from_items(unanalyzed_items, db)

        logger.info(f"分析完成: 提取 {len(word_count)} 个关键词")

        return len(unanalyzed_items)

    def get_top_keywords(
        self,
        db: Session,
        limit: int = 100,
        category: Optional[str] = None
    ) -> List[Keyword]:
        """
        获取热门关键词

        Args:
            db: 数据库会话
            limit: 返回数量
            category: 分类筛选

        Returns:
            List[Keyword]: 关键词列表
        """
        query = db.query(Keyword)

        if category:
            query = query.filter(Keyword.category == category)

        return query.order_by(Keyword.count.desc()).limit(limit).all()


# 默认关键词统计器实例
default_keyword_counter = KeywordCounter()
