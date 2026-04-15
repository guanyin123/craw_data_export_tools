"""
B站爬虫模块

使用热榜API获取B站热门视频数据
"""
import logging
from datetime import datetime
from typing import Optional
import re

from .base import BaseCrawler, CrawlItem
from .config import BilibiliConfig

logger = logging.getLogger(__name__)


class BilibiliCrawler(BaseCrawler):
    """
    B站爬虫

    使用第三方热榜API获取热门视频数据
    """

    # 备选API列表
    API_ENDPOINTS = [
        "https://api.vvhan.com/api/hotlist/biliHot",
        "https://hot.api0v.com/list/bilibili",
        "https://hot.go-old.cn/api/bilibili",
    ]

    def __init__(self, config: Optional[BilibiliConfig] = None):
        super().__init__(config or BilibiliConfig())
        self.config: BilibiliConfig  # type: ignore

    async def fetch_hot_data(self) -> list[dict]:
        """
        从备选API抓取B站热门数据

        Returns:
            list[dict]: 热门数据列表
        """
        logger.info("抓取B站热门数据...")

        for i, api_url in enumerate(self.API_ENDPOINTS, 1):
            try:
                logger.debug(f"尝试API源 {i}/{len(self.API_ENDPOINTS)}: {api_url}")
                response = await self.get(api_url)
                data = response.json()

                items = self._parse_api_response(data, api_url)
                if items:
                    logger.info(f"从 API源{i} 获取 {len(items)} 条数据")
                    return items

            except Exception as e:
                logger.debug(f"API源{i} 失败: {e}")
                continue

        logger.error("所有API源均失败")
        return []

    def _parse_api_response(self, data: dict, api_url: str) -> list[dict]:
        """解析API响应"""
        # vvhan API格式
        if "vvhan" in api_url:
            if data.get("success"):
                return data.get("data", [])

        # api0v API格式
        if "api0v" in api_url:
            if data.get("code") == 200:
                return data.get("data", {}).get("data", [])

        # go-old API格式
        if "go-old" in api_url:
            if data.get("code") == 0:
                return data.get("data", [])

        return data.get("data", data.get("list", []))

    def _parse_hot_item(self, raw_item: dict) -> Optional[CrawlItem]:
        """解析热门条目"""
        try:
            title = raw_item.get("title", raw_item.get("name", ""))
            url = raw_item.get("url", raw_item.get("link", raw_item.get("mobileUrl", "")))

            # 热度/播放量
            hot_value = raw_item.get(
                "hot",
                raw_item.get("hotValue", raw_item.get("score", raw_item.get("play", 0)))
            )
            if isinstance(hot_value, str):
                hot_value = hot_value.replace("万", "0000").replace(",", "").strip()
                match = re.search(r"([\d.]+)", hot_value)
                if match:
                    hot_value = int(float(match.group(1)))
                else:
                    hot_value = 0

            # 作者/UP主
            author = raw_item.get("author", raw_item.get("owner", raw_item.get("up", "")))

            # 摘要
            content = raw_item.get("desc", raw_item.get("summary", raw_item.get("description", "")))

            # 排名
            ranking = raw_item.get("rank", raw_item.get("index", 0))

            # 封面
            cover = raw_item.get("cover", raw_item.get("pic", ""))

            return CrawlItem(
                platform="bilibili",
                title=title,
                content=content,
                url=url,
                score=int(hot_value),
                comment_count=0,
                author=author,
                created_at=datetime.now(),
                raw_data={"ranking": ranking, "cover": cover, **raw_item},
            )
        except Exception as e:
            logger.warning(f"解析条目失败: {e}")
            return None

    async def fetch_items(self, limit: Optional[int] = None) -> list[CrawlItem]:
        """抓取B站热门数据"""
        max_items = limit or self.config.max_items_per_run

        hot_list = await self.fetch_hot_data()

        if not hot_list:
            logger.warning("未获取到任何数据")
            return []

        items = []
        for raw_item in hot_list[:max_items]:
            item = self._parse_hot_item(raw_item)
            if item and item.title:
                items.append(item)

        crawled_at = datetime.now()
        for item in items:
            if item.raw_data is None:
                item.raw_data = {}
            item.raw_data["crawled_at"] = crawled_at.isoformat()

        logger.info(f"解析完成，获取 {len(items)} 条有效数据")
        return items
