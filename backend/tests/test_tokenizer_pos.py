"""测试词性标注分词"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer.tokenizer import default_tokenizer

def test_pos_tagging():
    text = "我想做一个Chrome扩展来提高工作效率"
    words_pos = default_tokenizer.cut_with_pos(text)
    print("词性标注结果:", words_pos)
    # 应该有输出
    assert len(words_pos) > 0, "词性标注应该有结果"
    # 不应该包含代词（"我"）和助词（"的"）
    words_only = [w for w, _ in words_pos]
    assert "我" not in words_only, "不应该包含代词"
    print("✅ 词性标注测试通过")

def test_phrase_extraction():
    text = "如何开发一个Chrome浏览器扩展来提高办公效率"
    phrases = default_tokenizer.extract_meaningful_phrases(text)
    print("提取的短语:", phrases)
    assert len(phrases) > 0, "应该提取出短语"
    print("✅ 短语提取测试通过")

if __name__ == "__main__":
    test_pos_tagging()
    test_phrase_extraction()
