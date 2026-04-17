"""端到端测试优化后的完整流程"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer.phrase_extractor import default_phrase_extractor
from analyzer.classifier import default_classifier, Category
from analyzer.tokenizer import default_tokenizer
from crawler.filter import default_filter


def test_filter():
    """测试内容过滤器"""
    # 单个噪音词不会过滤，需要 >= 2 个噪音词才过滤
    assert not default_filter.has_business_value("搞笑段子合集", "")  # 搞笑+段子 >= 2
    assert not default_filter.has_business_value("明星八卦盘点", "据报道...")  # 明星+八卦+盘点+据报道 >= 2
    assert default_filter.has_business_value("副业赚钱指南", "分享靠谱副业")
    assert default_filter.has_business_value("Chrome扩展开发教程", "")
    assert default_filter.has_business_value("如何提高工作效率", "")
    print("✅ 内容过滤器测试通过")


def test_tokenizer():
    """测试词性标注分词"""
    words_pos = default_tokenizer.cut_with_pos("我想做一个Chrome扩展来提高工作效率")
    assert len(words_pos) > 0
    words_only = [w for w, _ in words_pos]
    assert "我" not in words_only  # 代词应被过滤
    print("✅ 词性标注测试通过")


def test_phrase_extractor():
    """测试短语提取"""
    title = "有什么好用的Chrome扩展可以提高工作效率？"
    phrases = default_phrase_extractor.extract_from_title(title)
    assert len(phrases) > 0
    print(f"   提取短语: {phrases}")

    title2 = "副业推荐：在家就能做的5个兼职"
    phrases2 = default_phrase_extractor.extract_from_title(title2)
    assert any("副业" in p for p in phrases2)

    content = "Chrome扩展开发使用JavaScript。自动化工具可以提高效率。"
    content_phrases = default_phrase_extractor.extract_from_content(content)
    assert len(content_phrases) > 0
    print("✅ 短语提取器测试通过")


def test_classifier():
    """测试智能分类器"""
    test_cases = [
        ("Chrome扩展", Category.TOOL),
        ("AI工具", Category.TOOL),
        ("副业", Category.CAREER),
        ("远程工作", Category.CAREER),
        ("自媒体", Category.CONTENT),
        ("在线课程", Category.SERVICE),
        ("电商", Category.PRODUCT),
        ("健身", Category.LIFESTYLE),
    ]
    for word, expected in test_cases:
        result = default_classifier.classify(word)
        assert result == expected, f"'{word}': 期望 {expected}, 得到 {result}"
        print(f"   '{word}' -> {result}")

    # 上下文辅助
    result = default_classifier.classify("扩展", "Chrome扩展开发教程")
    assert result == Category.TOOL
    print("✅ 智能分类器测试通过")


def test_integration():
    """集成测试：过滤器 + 提取器 + 分类器"""
    # 模拟真实数据
    test_items = [
        {"title": "有什么好用的Chrome扩展推荐？", "content": "提高工作效率的浏览器工具"},
        {"title": "搞笑段子合集2024", "content": "哈哈哈笑死我了"},
        {"title": "远程工作如何提高效率", "content": "在家办公的技巧和方法"},
        {"title": "副业月入过万的5个方法", "content": "分享几个靠谱的副业方向"},
    ]

    keywords = []
    for item in test_items:
        if not default_filter.has_business_value(item["title"], item["content"]):
            print(f"   过滤: {item['title']}")
            continue

        phrases = default_phrase_extractor.extract_from_title(item["title"])
        for phrase in phrases:
            category = default_classifier.classify(phrase, item["content"])
            keywords.append((phrase, category))

    print(f"\n   有效关键词: {keywords}")
    # 过滤掉搞笑内容
    assert not any("搞笑" in str(k) for k in keywords)
    # 应该有分类结果
    categories = [c for _, c in keywords]
    assert Category.OTHER not in categories or categories.count(Category.OTHER) < len(categories) * 0.3
    print("✅ 集成测试通过")


if __name__ == "__main__":
    print("=" * 50)
    print("端到端测试 - 商机发现系统优化")
    print("=" * 50)

    test_filter()
    test_tokenizer()
    test_phrase_extractor()
    test_classifier()
    test_integration()

    print("\n" + "=" * 50)
    print("所有测试通过!")
    print("=" * 50)
