"""
内容过滤器

过滤掉没有商业价值的娱乐类内容
"""
import logging
import re
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# 数据目录
DATA_DIR = Path(__file__).parent.parent / "data"


class ContentFilter:
    """
    内容过滤器

    判断内容是否具有商业分析价值
    """

    def __init__(
        self,
        noise_file: Path = DATA_DIR / "noise_keywords.txt",
        business_file: Path = DATA_DIR / "business_keywords.txt"
    ):
        """
        初始化过滤器

        Args:
            noise_file: 噪音关键词文件
            business_file: 商业关键词文件
        """
        self.noise_keywords = self._load_keywords(noise_file)
        self.business_keywords = self._load_keywords(business_file)
        logger.info(
            f"内容过滤器初始化完成: "
            f"{len(self.noise_keywords)}个噪音词, "
            f"{len(self.business_keywords)}个商业词"
        )

    def _load_keywords(self, file_path: Path) -> set[str]:
        """加载关键词文件"""
        keywords = set()
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    word = line.strip()
                    if word and not word.startswith("#"):
                        keywords.add(word)
        return keywords

    def has_business_value(self, title: str, content: str = "") -> bool:
        """
        判断内容是否具有商业价值

        Args:
            title: 标题
            content: 内容

        Returns:
            bool: 是否有商业价值
        """
        text = f"{title} {content}".lower()

        # 检查是否包含商业关键词
        business_matches = sum(1 for kw in self.business_keywords if kw in text)
        noise_matches = sum(1 for kw in self.noise_keywords if kw in text)

        # 有商业关键词且噪音词较少
        if business_matches > 0:
            return business_matches >= noise_matches

        # 没有商业关键词，检查是否纯噪音
        if noise_matches >= 2:
            return False

        # 默认保留（让后续分析决定）
        return True

    def get_business_keywords(self, text: str) -> List[str]:
        """
        从文本中提取商业相关关键词

        Args:
            text: 文本内容

        Returns:
            List[str]: 找到的商业关键词
        """
        text_lower = text.lower()
        found = []
        for keyword in self.business_keywords:
            if keyword in text_lower:
                found.append(keyword)
        return found


# 默认过滤器实例
default_filter = ContentFilter()
