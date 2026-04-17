"""
有意义短语提取器

从文本中提取具有商业价值的短语（2-4字）
"""
import logging
import re
from typing import List, Tuple

from .tokenizer import default_tokenizer

logger = logging.getLogger(__name__)


class PhraseExtractor:
    """提取2-4字的有意义短语，过滤无意义的单字词"""

    def __init__(self):
        self.tokenizer = default_tokenizer

    def extract_from_title(self, title: str) -> List[str]:
        """
        从标题中提取有价值短语

        策略:
        1. 使用词性标注提取
        2. 提取引号/书名号内容
        3. 提取问句中的核心话题词
        """
        if not title:
            return []

        phrases = []

        # 方法1: 使用 tokenizer 的短语提取
        pos_phrases = self.tokenizer.extract_meaningful_phrases(title)
        phrases.extend(pos_phrases)

        # 方法2: 提取引号/书名号内容（通常包含关键词）
        quoted = re.findall(r'["「《](.+?)["」》]', title)
        phrases.extend(quoted)

        # 方法3: 提取问句核心话题（"xxx怎么/如何/推荐"）
        question_match = re.search(r"(.*?)(?:怎么|如何|有什么|有没有|推荐)", title)
        if question_match:
            topic = question_match.group(1).strip()
            if len(topic) >= 2:
                phrases.append(topic)

        # 去重并过滤
        unique_phrases = []
        seen = set()
        for phrase in phrases:
            phrase = phrase.strip()
            if 2 <= len(phrase) <= 6 and phrase not in seen:
                if not phrase.replace(" ", "").isdigit() and (
                    any('\u4e00' <= c <= '\u9fff' for c in phrase) or
                    (phrase.isascii() and any(c.isalnum() for c in phrase))
                ):
                    unique_phrases.append(phrase)
                    seen.add(phrase)

        return unique_phrases

    def extract_from_content(
        self,
        content: str,
        top_k: int = 20
    ) -> List[Tuple[str, int]]:
        """
        从内容中提取高频短语

        Args:
            content: 内容文本
            top_k: 返回前k个

        Returns:
            List[Tuple[str, int]]: (短语, 权重) 列表
        """
        if not content:
            return []

        # 使用 TF-IDF 提取关键词
        tags = self.tokenizer.extract_tags(
            content,
            top_k=top_k * 2,
            with_weight=True
        )

        # 过滤出有商业价值的短语（2-4字）
        valuable = []
        for word, weight in tags:
            if 2 <= len(word) <= 4:
                valuable.append((word, int(weight * 100)))

        return valuable[:top_k]


# 默认实例
default_phrase_extractor = PhraseExtractor()
