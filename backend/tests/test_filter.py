"""测试内容过滤器"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from crawler.filter import ContentFilter

def test_filter():
    filter = ContentFilter()

    # 测试娱乐内容 - 应该被过滤
    assert not filter.has_business_value("搞笑段子合集", "哈哈哈哈笑死我了")

    # 测试商业内容 - 应该保留
    assert filter.has_business_value("如何做副业月入过万", "分享几个靠谱的副业方向")

    # 测试技术内容 - 应该保留
    assert filter.has_business_value("Chrome扩展开发教程", "从零开始学习浏览器扩展开发")

    # 测试纯娱乐 - 应该被过滤
    assert not filter.has_business_value("明星八卦", "据爆料某某某又...")

    print("✅ 所有过滤器测试通过")

if __name__ == "__main__":
    test_filter()
