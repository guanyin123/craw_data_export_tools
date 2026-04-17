"""
智能分类器模块

基于语义相似度和上下文进行分类
"""
import logging
from enum import Enum
from pathlib import Path
from typing import Optional, List, Tuple

from models.models import Keyword

logger = logging.getLogger(__name__)


class Category(str, Enum):
    """内容分类枚举"""
    TOOL = "TOOL"
    CONTENT = "CONTENT"
    SERVICE = "SERVICE"
    PRODUCT = "PRODUCT"
    LIFESTYLE = "LIFESTYLE"
    CAREER = "CAREER"
    OTHER = "OTHER"


class SmartClassifier:
    """
    智能分类器

    使用多种策略进行分类:
    1. 关键词精确匹配
    2. 同义词包含匹配
    3. 上下文语义分析
    4. 字特征推断
    """

    DATA_DIR = Path(__file__).parent.parent / "data"

    def __init__(self, synonyms_file: Path = DATA_DIR / "category_synonyms.txt"):
        self.synonyms_map = self._load_synonyms(synonyms_file)
        total_rules = sum(len(v) for v in self.synonyms_map.values())
        logger.info(f"智能分类器初始化完成，加载 {total_rules} 个分类规则")

    def _load_synonyms(self, file_path: Path) -> dict[Category, list[str]]:
        """加载同义词映射文件"""
        synonyms = {c: [] for c in Category}
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if ":" in line:
                        category_str, words_str = line.split(":", 1)
                        try:
                            category = Category(category_str.strip())
                            words = [w.strip().lower() for w in words_str.split("|")]
                            synonyms[category].extend(words)
                        except ValueError:
                            logger.warning(f"无效的分类: {category_str}")
        return synonyms

    def classify(
        self,
        keyword: str,
        context: str = "",
        default: Category = Category.OTHER
    ) -> Category:
        """智能分类关键词"""
        keyword_lower = keyword.lower()

        # 策略1: 精确匹配同义词库
        for category, synonyms in self.synonyms_map.items():
            if keyword_lower in synonyms:
                return category

        # 策略2: 部分匹配（包含关系 + 上下文）
        scores = {}
        for category, synonyms in self.synonyms_map.items():
            score = 0
            for synonym in synonyms:
                if synonym in keyword_lower or keyword_lower in synonym:
                    score += 1
                if context and synonym in context.lower():
                    score += 0.5
            if score > 0:
                scores[category] = score

        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]

        # 策略3: 基于字特征推断
        if any(c in keyword for c in ["软", "app", "工具", "系统", "插件"]):
            return Category.TOOL
        if any(c in keyword for c in ["课", "教", "学", "训", "培"]):
            return Category.SERVICE
        if any(c in keyword for c in ["业", "职", "薪", "赚"]):
            return Category.CAREER

        return default

    def batch_classify_keywords(
        self,
        keywords: list[Keyword],
        db_session,
        default: Category = Category.OTHER
    ) -> dict[Category, int]:
        """批量分类关键词（保持向后兼容的方法名）"""
        counts = {c: 0 for c in Category}
        for keyword in keywords:
            if keyword.category:
                counts[Category(keyword.category)] += 1
                continue

            # 获取上下文
            context = ""
            if keyword.keyword_items:
                latest_ki = keyword.keyword_items[0]
                if latest_ki and latest_ki.item:
                    context = f"{latest_ki.item.title} {latest_ki.item.content or ''}"

            category = self.classify(keyword.word, context, default)
            keyword.category = None if category == Category.OTHER else category.value
            counts[category] += 1

        try:
            db_session.commit()
            logger.info(f"批量分类完成: {dict(counts)}")
        except Exception as e:
            db_session.rollback()
            logger.error(f"批量分类失败: {e}")
            raise
        return counts

    def get_category_suggestions(
        self,
        keyword: str,
        top_k: int = 3
    ) -> list[tuple[Category, float]]:
        """获取分类建议（保持向后兼容的方法名）"""
        keyword_lower = keyword.lower()
        scores = []
        for category, synonyms in self.synonyms_map.items():
            score = 0
            for synonym in synonyms:
                if synonym in keyword_lower:
                    score += 1
                if keyword_lower in synonym:
                    score += 0.5
            if score > 0:
                scores.append((category, score))
        if scores:
            max_score = max(s for _, s in scores)
            scores = [(c, s / max_score) for c, s in scores]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


default_classifier = SmartClassifier()
