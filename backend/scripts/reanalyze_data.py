"""重新分析现有数据，使用新的提取和分类方法"""
import sys
from pathlib import Path
from datetime import datetime
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.database import SessionLocal
from models.models import Item, Keyword, KeywordItem
from analyzer.keyword_counter import default_keyword_counter
from analyzer.classifier import default_classifier, Category
from crawler.filter import default_filter


def reanalyze():
    """重新分析所有数据"""
    session = SessionLocal()

    print("开始重新分析...")

    # 1. 清空现有关键词和关联
    session.query(KeywordItem).delete()
    session.query(Keyword).delete()
    session.commit()
    print("已清空现有关键词")

    # 2. 获取所有 items
    items = session.query(Item).all()
    print(f"共 {len(items)} 条数据")

    # 3. 过滤 + 使用完整 keyword_counter 流程提取关键词
    filtered_items = []
    for item in items:
        if default_filter.has_business_value(item.title, item.content or ""):
            filtered_items.append(item)
        else:
            print(f"  过滤: {item.title[:40]}...")

    print(f"保留 {len(filtered_items)} 条有价值数据")

    # 4. 使用 keyword_counter 统计关键词（TF-IDF + 短语提取 + 自动分类）
    word_count = default_keyword_counter.count_from_items(filtered_items, session)

    print(f"提取到 {len(word_count)} 个关键词")

    # 5. 对未分类的关键词补充分类（批量查询避免N+1）
    unclassified = session.query(Keyword).outerjoin(
        KeywordItem, Keyword.id == KeywordItem.keyword_id
    ).outerjoin(
        Item, KeywordItem.item_id == Item.id
    ).filter(
        (Keyword.category.is_(None)) | (Keyword.category == "")
    ).all()

    print(f"其中 {len(unclassified)} 个未分类，进行智能分类...")

    for keyword in unclassified:
        context = ""
        # keyword 已通过 join 加载了关联
        for ki in keyword.keyword_items:
            if ki.item:
                context = f"{ki.item.title} {ki.item.content or ''}"
                break

        category = default_classifier.classify(keyword.word, context)
        keyword.category = category.value

    session.commit()

    # 6. 统计结果
    all_keywords = session.query(Keyword).all()
    categories = [kw.category for kw in all_keywords]
    category_stats = Counter(categories)

    print(f"\n{'='*40}")
    print(f"重新分析完成!")
    print(f"总关键词: {len(all_keywords)}")
    print(f"分类统计:")
    for cat, count in category_stats.most_common():
        pct = count / len(all_keywords) * 100 if all_keywords else 0
        print(f"  {cat or 'NULL':12s}: {count:4d} ({pct:.1f}%)")

    other_count = category_stats.get("OTHER", 0) + category_stats.get(None, 0) + category_stats.get("", 0)
    classified_count = len(all_keywords) - other_count
    if all_keywords:
        print(f"\n已分类率: {classified_count}/{len(all_keywords)} ({classified_count/len(all_keywords)*100:.1f}%)")
    print(f"{'='*40}")

    session.close()


if __name__ == "__main__":
    reanalyze()
