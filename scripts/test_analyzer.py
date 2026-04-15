#!/usr/bin/env python3
"""
数据分析测试脚本

用法:
    python scripts/test_analyzer.py           # 分析所有未分析的内容
    python scripts/test_analyzer.py --limit 5 # 只分析5条
    python scripts/test_analyzer.py --trends  # 分析趋势
"""
import sys
import argparse
from pathlib import Path

# 添加 backend 目录到 Python 路径
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

try:
    from analyzer import (
        default_tokenizer,
        default_keyword_counter,
        default_classifier,
        default_trend_analyzer,
    )
    from models.database import SessionLocal
    from models.models import Item, Keyword, KeywordItem
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("请确保在项目根目录运行此脚本，且已安装所有依赖")
    sys.exit(1)


def test_tokenizer():
    """测试分词器"""
    print("\n" + "=" * 50)
    print("🧪 测试分词器")
    print("=" * 50)

    test_text = """
    如何看待同济大学王教授的百万经费 Nature 论文被指数据造假？
    这篇文章在pubpeer都被锤烂了，nature生物论文出这种问题也不是一天两天了。
    """

    keywords = default_tokenizer.extract_tags(test_text, top_k=10)

    print(f"\n原文: {test_text.strip()[:50]}...")
    print(f"\n提取关键词:")
    for i, (word, weight) in enumerate(keywords, 1):
        print(f"  {i}. {word} ({weight:.2f})")


def test_keyword_counter(limit: int = 5):
    """测试关键词统计"""
    print("\n" + "=" * 50)
    print("🔢 测试关键词统计")
    print("=" * 50)

    db = SessionLocal()
    try:
        # 获取未分析的内容
        from sqlalchemy import select
        subquery = select(KeywordItem.item_id)
        unanalyzed = db.query(Item).filter(
            ~Item.id.in_(subquery)
        ).limit(limit).all()

        if not unanalyzed:
            print("没有未分析的内容")
            return

        print(f"\n分析 {len(unanalyzed)} 条内容...")

        # 统计关键词
        word_count = default_keyword_counter.count_from_items(unanalyzed, db)

        print(f"\n✅ 提取 {len(word_count)} 个关键词")
        print("\n🔥 热门关键词 (Top 10):")
        for i, (word, count) in enumerate(sorted(word_count.items(), key=lambda x: x[1], reverse=True)[:10], 1):
            print(f"  {i}. {word} (出现次数: {count})")

    finally:
        db.close()


def test_classifier():
    """测试分类器"""
    print("\n" + "=" * 50)
    print("🏷️  测试分类器")
    print("=" * 50)

    test_keywords = ["软件", "创业", "美食", "视频", "编程", "投资", "健康"]

    print("\n关键词分类结果:")
    for word in test_keywords:
        category = default_classifier.classify_by_keyword(word)
        suggestions = default_classifier.get_category_suggestions(word)
        suggestion_str = ", ".join([f"{c.value}({s})" for c, s in suggestions])
        print(f"  {word:8s} -> {category.value:10s} (建议: {suggestion_str})")


def classify_keywords():
    """批量分类数据库中的关键词"""
    print("\n" + "=" * 50)
    print("🏷️  批量分类关键词")
    print("=" * 50)

    db = SessionLocal()
    try:
        # 获取未分类的关键词
        keywords = db.query(Keyword).filter(Keyword.category == None).limit(50).all()

        if not keywords:
            print("没有未分类的关键词")
            return

        print(f"\n分类 {len(keywords)} 个关键词...")

        counts = default_classifier.batch_classify_keywords(keywords, db)

        print("\n分类结果:")
        for category, count in counts.items():
            if count > 0:
                print(f"  {category.value}: {count}")

    finally:
        db.close()


def test_trends():
    """测试趋势分析"""
    print("\n" + "=" * 50)
    print("📈 测试趋势分析")
    print("=" * 50)

    db = SessionLocal()
    try:
        # 分析最近趋势
        count = default_trend_analyzer.analyze_daily_trends(db)
        print(f"\n✅ 创建/更新 {count} 条趋势记录")

        # 获取热门关键词
        hot_keywords = default_trend_analyzer.get_hot_keywords(db, days=1, limit=10)
        print(f"\n🔥 今日热门关键词:")
        for i, kw in enumerate(hot_keywords, 1):
            print(f"  {i}. {kw.word} (总次数: {kw.count})")

        # 获取上升趋势关键词
        rising = default_trend_analyzer.get_rising_keywords(db, days=7, limit=10)
        if rising:
            print(f"\n📈 上升趋势关键词 (Top 10):")
            for i, item in enumerate(rising, 1):
                growth = item["growth_rate"]
                if growth == float('inf'):
                    growth_str = "NEW"
                else:
                    growth_str = f"+{growth * 100:.0f}%"
                print(f"  {i}. {item['keyword']} ({growth_str}, {item['current_count']}次)")

    finally:
        db.close()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="数据分析测试脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python scripts/test_analyzer.py           # 完整测试流程
  python scripts/test_analyzer.py --limit 5 # 只分析5条
  python scripts/test_analyzer.py --trends  # 只分析趋势
  python scripts/test_analyzer.py --classify # 只分类关键词
        """
    )
    parser.add_argument("--limit", "-l", type=int, default=5, help="分析数量")
    parser.add_argument("--trends", "-t", action="store_true", help="只分析趋势")
    parser.add_argument("--classify", "-c", action="store_true", help="只分类关键词")
    args = parser.parse_args()

    print("📊 数据分析测试")
    print("=" * 50)

    if args.classify:
        test_classifier()
        classify_keywords()
    elif args.trends:
        test_trends()
    else:
        # 完整测试
        test_tokenizer()
        test_keyword_counter(args.limit)
        test_classifier()
        classify_keywords()
        test_trends()

    print("\n" + "=" * 50)
    print("✅ 测试完成")


if __name__ == "__main__":
    main()
