"""
简单的爬虫运行脚本

直接运行爬虫抓取数据，无需启动API服务
"""
import asyncio
import sys
from pathlib import Path

# 添加backend目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from crawler.zhihu import ZhihuCrawler
from crawler.bilibili import BilibiliCrawler
from crawler.config import default_zhihu_config, default_bilibili_config
from analyzer.keyword_counter import KeywordCounter
from models.database import SessionLocal
from models.models import Item
from datetime import datetime


async def run_crawler(platform: str = "zhihu", limit: int = 10, save: bool = True, analyze: bool = True):
    """
    运行爬虫

    Args:
        platform: 平台名称 (zhihu/bilibili)
        limit: 抓取数量
        save: 是否保存到数据库
        analyze: 是否分析关键词
    """
    print(f"开始抓取 {platform} 数据，数量: {limit}")

    try:
        if platform == "zhihu":
            config = default_zhihu_config
            config.max_items_per_run = limit
            async with ZhihuCrawler(config) as crawler:
                items = await crawler.crawl(limit=limit)
        else:  # bilibili
            config = default_bilibili_config
            config.max_items_per_run = limit
            async with BilibiliCrawler(config) as crawler:
                items = await crawler.crawl(limit=limit)

        print(f"成功抓取 {len(items)} 条数据")

        # 保存到数据库
        if save and items:
            with SessionLocal() as db:
                try:
                    for item in items:
                        existing = db.query(Item).filter(Item.url == item.url).first()
                        if not existing:
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
                    db.commit()
                    print(f"保存了 {len(items)} 条新数据到数据库")
                except Exception as e:
                    db.rollback()
                    print(f"保存失败: {e}")
                    raise

            # 分析关键词
            if analyze:
                print("开始分析关键词...")
                counter = KeywordCounter()
                with SessionLocal() as db:
                    try:
                        counter.analyze_new_items(db, limit=len(items))
                        print("关键词分析完成")

                        # 显示关键词统计
                        from models.models import Keyword
                        keyword_count = db.query(Keyword).count()
                        print(f"当前数据库共有 {keyword_count} 个关键词")
                    except Exception as e:
                        db.rollback()
                        print(f"分析失败: {e}")
                        raise

        # 显示部分结果
        print("\n=== 抓取结果预览 ===")
        for i, item in enumerate(items[:5], 1):
            print(f"\n{i}. {item.title}")
            print(f"   热度: {item.score} | 作者: {item.author}")
            print(f"   内容: {item.content[:100]}...")

    except Exception as e:
        print(f"爬虫运行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="运行爬虫抓取数据")
    parser.add_argument(
        "--platform", "-p",
        choices=["zhihu", "bilibili"],
        default="zhihu",
        help="平台名称 (默认: zhihu)"
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
    parser.add_argument(
        "--no-analyze",
        action="store_true",
        help="不分析关键词"
    )

    args = parser.parse_args()

    asyncio.run(run_crawler(
        platform=args.platform,
        limit=args.limit,
        save=not args.no_save,
        analyze=not args.no_analyze,
    ))
