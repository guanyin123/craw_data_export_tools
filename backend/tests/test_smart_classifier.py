"""测试智能分类器"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer.classifier import default_classifier, Category

def test_exact_match():
    assert default_classifier.classify("Chrome扩展") == Category.TOOL
    assert default_classifier.classify("AI工具") == Category.TOOL
    assert default_classifier.classify("副业") == Category.CAREER
    assert default_classifier.classify("远程工作") == Category.CAREER
    assert default_classifier.classify("自媒体") == Category.CONTENT
    assert default_classifier.classify("在线课程") == Category.SERVICE
    print("✅ 精确匹配测试通过")

def test_partial_match():
    # 部分匹配测试
    assert default_classifier.classify("自动化") == Category.TOOL
    assert default_classifier.classify("电商") == Category.PRODUCT
    assert default_classifier.classify("健身") == Category.LIFESTYLE
    print("✅ 部分匹配测试通过")

def test_context_classification():
    # 上下文辅助分类
    context = "我想开发一个Chrome扩展来自动化工作"
    result = default_classifier.classify("扩展", context)
    assert result == Category.TOOL, f"期望TOOL但得到{result}"
    print("✅ 上下文分类测试通过")

def test_suggestions():
    suggestions = default_classifier.get_category_suggestions("开发")
    assert len(suggestions) > 0, "应该有分类建议"
    print(f"'开发'的建议: {suggestions}")
    print("✅ 分类建议测试通过")

def test_unknown_keyword():
    result = default_classifier.classify("复刻")
    assert result == Category.OTHER, f"未知词应归为OTHER但得到{result}"
    print("✅ 未知词测试通过")

if __name__ == "__main__":
    test_exact_match()
    test_partial_match()
    test_context_classification()
    test_suggestions()
    test_unknown_keyword()
