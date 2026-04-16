"""测试短语提取器"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer.phrase_extractor import default_phrase_extractor

def test_phrase_extraction():
    # 测试标题提取
    title1 = "有什么好用的Chrome扩展可以提高工作效率？"
    phrases1 = default_phrase_extractor.extract_from_title(title1)
    print(f"标题1: {title1}")
    print(f"提取短语: {phrases1}")
    assert "Chrome扩展" in phrases1 or any("扩展" in p for p in phrases1)

    title2 = "副业推荐：在家就能做的5个兼职"
    phrases2 = default_phrase_extractor.extract_from_title(title2)
    print(f"标题2: {title2}")
    print(f"提取短语: {phrases2}")
    assert any("副业" in p for p in phrases2)

    # 测试内容提取
    content = """
    我想开发一个Chrome扩展来自动化我的工作流程。
    这个扩展可以帮助我节省很多时间，提高工作效率。
    Chrome扩展开发使用JavaScript和HTML。
    """
    phrases3 = default_phrase_extractor.extract_from_content(content)
    print(f"内容短语: {phrases3}")
    assert len(phrases3) > 0

    print("✅ 短语提取器测试通过")

if __name__ == "__main__":
    test_phrase_extraction()
