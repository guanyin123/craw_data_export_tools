"""
内容过滤器

过滤掉没有商业价值的娱乐类内容
"""
import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"


class ContentFilter:
    """判断内容是否具有商业分析价值"""

    def __init__(
        self,
        noise_file: Path = DATA_DIR / "noise_keywords.txt",
        business_file: Path = DATA_DIR / "business_keywords.txt"
    ):
        self.noise_keywords = self._load_keywords(noise_file)
        self.business_keywords = self._load_keywords(business_file)
        logger.info(
            f"内容过滤器初始化完成: "
            f"{len(self.noise_keywords)}个噪音词, "
            f"{len(self.business_keywords)}个商业词"
        )

    def _load_keywords(self, file_path: Path) -> set[str]:
        keywords = set()
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    word = line.strip()
                    if word and not word.startswith("#"):
                        keywords.add(word.lower())
        return keywords

    def has_business_value(self, title: str, content: str = "") -> bool:
        """判断内容是否具有商业价值"""
        text = f"{title} {content}".lower()
        business_matches = sum(1 for kw in self.business_keywords if kw in text)
        noise_matches = sum(1 for kw in self.noise_keywords if kw in text)
        if business_matches > 0:
            return business_matches >= noise_matches
        if noise_matches >= 2:
            return False
        return True

    def get_business_keywords(self, text: str) -> List[str]:
        """从文本中提取商业相关关键词"""
        text_lower = text.lower()
        return [kw for kw in self.business_keywords if kw in text_lower]


default_filter = ContentFilter()
