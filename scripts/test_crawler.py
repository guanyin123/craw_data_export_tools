#!/usr/bin/env python3
"""
爬虫测试脚本

用法:
    python scripts/test_crawler.py           # 测试知乎爬虫
    python scripts/test_crawler.py --limit 5 # 只抓取5条
    python scripts/test_crawler.py --no-save # 不保存到数据库
"""
import asyncio
import sys
import argparse
from pathlib import Path
from datetime import datetime

# 添加 backend 目录到 Python 路径
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

try:
    from crawler import ZhihuCrawler, default_zhihu_config
    from models.database import SessionLocal
    from models.models import Item
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("请确保在项目根目录运行此脚本，且已安装所有依赖")
    sys.exit(1)


async def test_crawler(limit: int = 10, save: bool = True):
    """
    测试知乎爬虫

    Args:
        limit: 抓取数量
        save: 是否保存到数据库
    """
    print(f"🕷️  开始测试知乎爬虫 (limit={limit}, save={save})...")
    print("=" * 50)

    # 配置爬虫（测试时使用较短延迟）
    config = default_zhihu_config
    config.min_delay = 1.0  # 测试时缩短延迟
    config.max_items_per_run = limit

    try:
        async with ZhihuCrawler(config) as crawler:
            # 抓取数据
            items = await crawler.crawl(limit=limit)

            if not items:
                print("❌ 未获取到任何数据")
                return

            print(f"\n✅ 成功获取 {len(items)} 条数据")
            print("\n📊 数据预览:")
            print("-" * 50)

            # 显示前3条
            for i, item in enumerate(items[:3], 1):
                print(f"\n[{i}] {item.title}")
                print(f"    热度: {item.score:,}")
                print(f"    作者: {item.author or '未知'}")
                print(f"    链接: {item.url}")
                content_preview = (item.content or "")[:100]
                print(f"    内容: {content_preview}...")

            if len(items) > 3:
                print(f"\n... 还有 {len(items) - 3} 条数据")

            # 保存到数据库
            if save:
                print(f"\n💾 保存到数据库...")
                db = SessionLocal()
                try:
                    saved_count = 0
                    for item in items:
                        # 检查是否已存在（根据URL）
                        existing = db.query(Item).filter(Item.url == item.url).first()
                        if existing:
                            logger.debug(f"跳过已存在: {item.title[:30]}...")
                            continue

                        db_item = Item(
                            platform=item.platform,
                            title=item.title,
                            content=item.content,
                            url=item.url,
                            score=item.score,
                            comment_count=item.comment_count,
                            author=item.author,
                            created_at=item.created_at or datetime.now(),
                            crawled_at=datetime.now(),
                        )
                        db.add(db_item)
                        saved_count += 1

                    db.commit()
                    print(f"✅ 保存 {saved_count} 条新数据到数据库")

                    # 显示数据库统计
                    total_count = db.query(Item).filter(Item.platform == "zhihu").count()
                    print(f"📋 数据库中知乎数据总数: {total_count}")

                except Exception as e:
                    db.rollback()
                    print(f"❌ 保存失败: {e}")
                    raise
                finally:
                    db.close()
            else:
                print("\n⚠️  跳过保存 (--no-save)")

            print("\n" + "=" * 50)
            print("✅ 测试完成")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="爬虫测试脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python scripts/test_crawler.py           # 测试知乎爬虫(10条)
  python scripts/test_crawler.py --limit 5 # 只抓取5条
  python scripts/test_crawler.py --no-save # 不保存到数据库
        """
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=10,
        help="抓取数量 (默认: 10)"
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="不保存到数据库"
    )
    args = parser.parse_args()

    # 运行测试
    asyncio.run(test_crawler(limit=args.limit, save=not args.no_save))


if __name__ == "__main__":
    main()
