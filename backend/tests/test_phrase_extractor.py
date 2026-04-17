"""测试短语提取器"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer.phrase_extractor import default_phrase_extractor

def test_title_extraction():
    # 测试引号内容提取
    title1 = "有什么好用的《Chrome扩展》可以提高工作效率？"
    phrases1 = default_phrase_extractor.extract_from_title(title1)
    print(f"标题1: {title1}")
    print(f"提取短语: {phrases1}")
    assert any("Chrome扩展" in p or "扩展" in p for p in phrases1), "应该提取Chrome扩展"

    # 测试副业关键词
    title2 = "副业推荐：在家就能做的5个兼职"
    phrases2 = default_phrase_extractor.extract_from_title(title2)
    print(f"标题2: {title2}")
    print(f"提取短语: {phrases2}")
    assert any("副业" in p for p in phrases2), "应该提取副业"

    # 测试问句核心话题
    title3 = "远程工作如何提高团队协作效率？"
    phrases3 = default_phrase_extractor.extract_from_title(title3)
    print(f"标题3: {title3}")
    print(f"提取短语: {phrases3}")
    assert len(phrases3) > 0, "应该提取到短语"
    print("✅ 标题提取测试通过")

def test_content_extraction():
    content = """
    我想开发一个Chrome扩展来自动化我的工作流程。
    这个扩展可以帮助我节省很多时间，提高工作效率。
    Chrome扩展开发使用JavaScript和HTML。
    自动化是未来的趋势，学会自动化可以让你的工作更轻松。
    """
    phrases = default_phrase_extractor.extract_from_content(content)
    print(f"内容短语: {phrases}")
    assert len(phrases) > 0, "应该提取到内容短语"
    # 验证长度在2-4字
    for word, weight in phrases:
        assert 2 <= len(word) <= 4, f"短语长度应在2-4字: {word}"
    print("✅ 内容提取测试通过")

def test_empty_input():
    assert default_phrase_extractor.extract_from_title("") == []
    assert default_phrase_extractor.extract_from_content("") == []
    print("✅ 空输入测试通过")

if __name__ == "__main__":
    test_title_extraction()
    test_content_extraction()
    test_empty_input()
