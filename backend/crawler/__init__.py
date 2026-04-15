"""
爬虫模块
"""
from .base import BaseCrawler, CrawlItem
from .config import CrawlerConfig, ZhihuConfig, BilibiliConfig, default_zhihu_config, default_bilibili_config
from .zhihu import ZhihuCrawler
from .bilibili import BilibiliCrawler

__all__ = [
    "BaseCrawler",
    "CrawlItem",
    "CrawlerConfig",
    "ZhihuConfig",
    "BilibiliConfig",
    "ZhihuCrawler",
    "BilibiliCrawler",
    "default_zhihu_config",
    "default_bilibili_config",
]
