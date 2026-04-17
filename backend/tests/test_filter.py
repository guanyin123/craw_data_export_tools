"""测试内容过滤器"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from crawler.filter import ContentFilter

def test_filter():
    f = ContentFilter()
    # 娱乐内容应该被过滤
    assert not f.has_business_value("搞笑段子合集", "哈哈哈哈笑死我了"), "娱乐内容应该被过滤"
    # 商业内容应该保留
    assert f.has_business_value("如何做副业月入过万", "分享几个靠谱的副业方向"), "商业内容应该保留"
    # 技术内容应该保留
    assert f.has_business_value("Chrome扩展开发教程", "从零开始学习浏览器扩展开发"), "技术内容应该保留"
    # 纯娱乐应该被过滤
    assert not f.has_business_value("明星八卦", "据爆料某某某又..."), "纯娱乐应该被过滤"
    # 中性内容默认保留
    assert f.has_business_value("如何提高工作效率", ""), "中性内容默认保留"
    print("✅ 所有过滤器测试通过")

if __name__ == "__main__":
    test_filter()
