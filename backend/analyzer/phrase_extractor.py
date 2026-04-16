"""
有意义短语提取器

从文本中提取具有商业价值的短语
"""
import logging
import re

from .tokenizer import default_tokenizer

logger = logging.getLogger(__name__)


class PhraseExtractor:
    """
    短语提取器

    提取2-4字的有意义短语，过滤无意义的单字词
    """

    def __init__(self):
        self.tokenizer = default_tokenizer

    def extract_from_title(self, title: str) -> list[str]:
        """
        从标题中提取有价值短语

        Args:
            title: 标题文本

        Returns:
            List[str]: 短语列表
        """
        if not title:
            return []

        phrases = []

        # 方法1: 使用词性标注提取
        pos_phrases = self.tokenizer.extract_meaningful_phrases(title)
        phrases.extend(pos_phrases)

        # 方法2: 提取引号内容（通常包含关键词）
        quoted = re.findall(r'["「」『』](.+?)["」』"]', title)
        phrases.extend(quoted)

        # 方法3: 提取问号前的核心问题词
        question_match = re.search(r"(.*?)(?:怎么|如何|有没有|推荐)", title)
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
                # Allow Chinese OR English/Alphanumeric phrases
                if (any('\u4e00' <= c <= '\u9fff' for c in phrase) or
                    (phrase.isascii() and phrase.isalnum())):
                    unique_phrases.append(phrase)
                    seen.add(phrase)

        return unique_phrases

    def extract_from_content(
        self,
        content: str,
        top_k: int = 20
    ) -> list[tuple[str, int]]:
        """
        从内容中提取高频短语

        Args:
            content: 内容文本
            top_k: 返回前k个

        Returns:
            List[Tuple[str, int]]: (短语, 频次) 列表
        """
        if not content:
            return []

        # 使用jieba的TF-IDF提取关键词
        tags = self.tokenizer.extract_tags(
            content,
            top_k=top_k * 2,  # 多提取一些，后面再过滤
            with_weight=True
        )

        # 过滤出有商业价值的短语
        valuable = []
        for word, weight in tags:
            if 2 <= len(word) <= 4:  # 只保留2-4字的词
                valuable.append((word, int(weight * 100)))

        return valuable[:top_k]


# 默认实例
default_phrase_extractor = PhraseExtractor()
