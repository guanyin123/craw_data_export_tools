"""测试词性标注分词"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer.tokenizer import default_tokenizer

def test_pos_tagging():
    text = "我想做一个Chrome扩展来提高工作效率"

    # 带词性分词（默认只保留名词、动名词、动词、形容词）
    words_pos = default_tokenizer.cut_with_pos(text)
    print("词性标注结果:", words_pos)

    # 应该包含名词
    assert any(pos in {"n", "nr", "ns", "nt"} for _, pos in words_pos)

    # 测试包含英文词性
    words_pos_with_eng = default_tokenizer.cut_with_pos(
        text,
        allowed_pos={"n", "nr", "ns", "nt", "vn", "a", "an", "v", "eng"}
    )
    print("包含英文的词性标注结果:", words_pos_with_eng)
    assert any("Chrome" in w for w, _ in words_pos_with_eng)

    # 测试短语提取（使用包含更多词性的文本）
    phrase_text = "数据分析工具帮助用户快速处理大量数据"
    phrases = default_tokenizer.extract_meaningful_phrases(phrase_text)
    print("提取的短语:", phrases)
    assert len(phrases) > 0

    print("词性标注测试通过")

if __name__ == "__main__":
    test_pos_tagging()
