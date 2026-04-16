"""
分词器模块

使用 jieba 进行中文分词，支持停用词过滤
"""
import logging
import re
from pathlib import Path
from typing import Set, List

import jieba

logger = logging.getLogger(__name__)

# 数据目录
DATA_DIR = Path(__file__).parent.parent / "data"
# 停用词文件路径
STOP_WORDS_FILE = DATA_DIR / "stop_words.txt"


class Tokenizer:
    """
    中文分词器

    功能:
    - 使用 jieba 进行分词
    - 过滤停用词
    - 过滤单字符和无意义词
    - 提取关键词
    """

    # 默认停用词（当文件不存在时使用）
    DEFAULT_STOP_WORDS = {
        "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
        "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有",
        "看", "好", "自己", "这", "那", "什么", "为", "么", "与", "及", "其",
        "中", "而", "或", "以", "于", "之", "等", "对", "将", "从", "被", "由",
        "可以", "但是", "因为", "所以", "如果", "虽然", "让", "给", "把", "向",
        "吗", "呢", "啊", "吧", "哦", "哈", "呀", "哪", "怎", "如何", "为何",
        "这个", "那个", "这些", "那些", "这样", "那样", "这里", "那里",
        "已经", "正在", "将要", "可能", "应该", "能够", "需要", "想要",
    }

    # 无意义词模式（纯数字、特殊符号等）
    MEANINGLESS_PATTERNS = [
        re.compile(r'^\d+$'),  # 纯数字
        re.compile(r'^[^\w\u4e00-\u9fff]+$'),  # 纯符号
    ]

    def __init__(self, stop_words_file: Path = STOP_WORDS_FILE):
        """
        初始化分词器

        Args:
            stop_words_file: 停用词文件路径
        """
        self.stop_words: Set[str] = self._load_stop_words(stop_words_file)
        logger.info(f"分词器初始化完成，加载 {len(self.stop_words)} 个停用词")

        # 设置 jieba 日志级别
        jieba.setLogLevel(jieba.logging.INFO)

    def _load_stop_words(self, file_path: Path) -> Set[str]:
        """
        加载停用词表

        Args:
            file_path: 停用词文件路径

        Returns:
            Set[str]: 停用词集合
        """
        stop_words = set()

        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        word = line.strip()
                        if word and not word.startswith("#"):
                            stop_words.add(word)
                logger.info(f"从文件加载 {len(stop_words)} 个停用词: {file_path}")
            except Exception as e:
                logger.warning(f"加载停用词文件失败: {e}")

        # 如果没有加载到停用词，使用默认停用词
        if not stop_words:
            stop_words = self.DEFAULT_STOP_WORDS.copy()
            logger.info("使用默认停用词表")

        return stop_words

    def is_meaningful(self, word: str) -> bool:
        """
        判断词是否有意义

        Args:
            word: 词语

        Returns:
            bool: 是否有意义
        """
        # 过滤单字符
        if len(word) <= 1:
            return False

        # 过滤停用词
        if word in self.stop_words:
            return False

        # 过滤无意义模式
        for pattern in self.MEANINGLESS_PATTERNS:
            if pattern.match(word):
                return False

        return True

    def cut(
        self,
        text: str,
        filter_stop: bool = True,
        min_length: int = 2
    ) -> List[str]:
        """
        分词

        Args:
            text: 待分词文本
            filter_stop: 是否过滤停用词
            min_length: 最小词长度

        Returns:
            List[str]: 分词结果列表
        """
        if not text:
            return []

        # 使用 jieba 分词
        words = jieba.cut(text)

        # 过滤
        result = []
        for word in words:
            word = word.strip()

            # 检查长度
            if len(word) < min_length:
                continue

            # 过滤停用词
            if filter_stop and not self.is_meaningful(word):
                continue

            result.append(word)

        return result

    def extract_keywords(
        self,
        text: str,
        top_k: int = 20
    ) -> List[tuple[str, int]]:
        """
        提取关键词（基于词频）

        Args:
            text: 待分析文本
            top_k: 返回前k个关键词

        Returns:
            List[tuple[str, int]]: (关键词, 词频) 列表
        """
        # 分词
        words = self.cut(text)

        # 统计词频
        word_count = {}
        for word in words:
            word_count[word] = word_count.get(word, 0) + 1

        # 按词频排序
        sorted_words = sorted(
            word_count.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_words[:top_k]

    def extract_tags(
        self,
        text: str,
        top_k: int = 10,
        with_weight: bool = True
    ) -> List[tuple[str, float]] | List[str]:
        """
        使用 jieba 的 TF-IDF 算法提取关键词

        Args:
            text: 待分析文本
            top_k: 返回前k个关键词
            with_weight: 是否返回权重

        Returns:
            关键词列表
        """
        import jieba.analyse

        tags = jieba.analyse.extract_tags(
            text,
            topK=top_k,
            withWeight=with_weight,
            allowPOS=('n', 'vn', 'v', 'a')  # 名词、动名词、动词、形容词
        )

        # 过滤停用词
        filtered_tags = []
        for item in tags:
            if with_weight:
                word, weight = item
                if self.is_meaningful(word):
                    filtered_tags.append((word, weight))
            else:
                if self.is_meaningful(item):
                    filtered_tags.append(item)

        return filtered_tags

    def cut_with_pos(
        self,
        text: str,
        allowed_pos: Set[str] | None = None,
        min_length: int = 2
    ) -> List[tuple[str, str]]:
        """
        带词性标注的分词

        Args:
            text: 待分词文本
            allowed_pos: 允许的词性集合，默认为名词、动词、形容词
            min_length: 最小词长度

        Returns:
            list[tuple[str, str]]: (词, 词性) 列表

        词性说明:
            n: 名词, nr: 人名, ns: 地名, nt: 机构名
            v: 动词, vn: 动名词
            a: 形容词, an: 名形词
            m: 数量词
        """
        if not text or not text.strip():
            return []

        # 默认只保留名词、动名词、动词、形容词、英文词
        # Add 'eng' for English words common in tech/business contexts
        if allowed_pos is None:
            allowed_pos = {"n", "nr", "ns", "nt", "vn", "a", "an", "eng"}

        import jieba.posseg as pseg

        words = []
        for word, pos in pseg.cut(text):
            word = word.strip()

            # 检查长度
            if len(word) < min_length:
                continue

            # 检查词性
            if pos not in allowed_pos:
                continue

            # 过滤停用词
            if not self.is_meaningful(word):
                continue

            words.append((word, pos))

        return words

    def extract_meaningful_phrases(
        self,
        text: str,
        max_length: int = 4
    ) -> List[str]:
        """
        提取有意义的短语

        Args:
            text: 待分析文本
            max_length: 短语最大长度

        Returns:
            list[str]: 有意义的短语列表
        """
        if not text or not text.strip():
            return []

        # 使用jieba的TF-IDF提取关键词，这些天然是有意义的短语
        tags = self.extract_tags(text, top_k=20, with_weight=True)

        # 过滤出合适长度的短语
        phrases = []
        for word, weight in tags:
            if 2 <= len(word) <= max_length * 2:  # 允许中文短语
                phrases.append(word)

        # 也使用词性标注提取一些组合
        words_with_pos = self.cut_with_pos(text, allowed_pos={"n", "nr", "ns", "nt", "vn", "eng"})

        # 简单组合：连续的名词/英文词
        current_phrase = ""
        for word, pos in words_with_pos:
            current_phrase += word
            if len(current_phrase) >= 2 and len(current_phrase) <= max_length * 2:
                phrases.append(current_phrase)
            if pos in {"n", "nr", "ns", "nt"}:
                current_phrase = word  # 重置为当前词，可能开始新短语

        return list(set(phrases))  # 去重


# 默认分词器实例
default_tokenizer = Tokenizer()
