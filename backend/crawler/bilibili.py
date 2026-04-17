"""
B站爬虫模块

使用B站官方API获取热门视频数据
"""
import logging
from datetime import datetime
from typing import Optional
import re

from .base import BaseCrawler, CrawlItem
from .config import BilibiliConfig
from .filter import default_filter as content_filter

logger = logging.getLogger(__name__)


class BilibiliCrawler(BaseCrawler):
    """
    B站爬虫

    使用B站官方API获取热门视频数据
    """

    def __init__(self, config: Optional[BilibiliConfig] = None):
        super().__init__(config or BilibiliConfig())
        self.config: BilibiliConfig  # type: ignore

    async def init_client(self):
        """初始化 HTTP 客户端（覆盖基类以添加自定义headers）"""
        from .base import httpx

        if self._client is None or self._client.is_closed:
            headers = {
                "User-Agent": self.config.user_agent,
                "Accept": "application/json",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Referer": "https://www.bilibili.com/",
                "Origin": "https://www.bilibili.com",
            }

            # 添加 Cookie（可选）
            if self.config.cookie:
                headers["Cookie"] = self.config.cookie
                logger.info(f"{self.__class__.__name__}: 使用已配置的 Cookie")
            else:
                logger.info(f"{self.__class__.__name__}: 未配置Cookie，使用官方API")

            proxy = self.config.proxy if self.config.proxy else None

            self._client = httpx.AsyncClient(
                headers=headers,
                proxy=proxy,
                timeout=self.config.timeout,
                follow_redirects=True,
            )
            logger.info(f"{self.__class__.__name__}: HTTP 客户端已初始化")

    async def fetch_hot_data(self) -> list[dict]:
        """
        从B站官方API抓取热门数据

        Returns:
            list[dict]: 热门数据列表
        """
        logger.info("抓取B站热门数据...")

        try:
            params = {"ps": self.config.trending_ps}
            response = await self.get(self.config.trending_url, params=params)
            data = response.json()

            if data.get("code") == 0:
                items = data.get("data", {}).get("list", [])
                logger.info(f"获取B站热门 {len(items)} 条")
                return items
            else:
                logger.warning(f"B站API返回错误: {data.get('message', 'Unknown error')}")
                return []

        except Exception as e:
            logger.error(f"抓取B站数据失败: {e}")
            return []

    def _parse_hot_item(self, raw_item: dict) -> Optional[CrawlItem]:
        """解析热门条目"""
        try:
            title = raw_item.get("title", "")

            # 过滤无商业价值的内容
            if not content_filter.has_business_value(title, ""):
                logger.debug(f"过滤无价值内容: {title}")
                return None

            # 构建视频URL
            bvid = raw_item.get("bvid", "")
            url = f"https://www.bilibili.com/video/{bvid}" if bvid else raw_item.get("uri", "")

            # 播放量/热度
            stat = raw_item.get("stat", {})
            # 使用观看人数或播放数作为热度
            hot_value = stat.get("view", stat.get("played", 0))

            # 作者/UP主
            owner = raw_item.get("owner", {})
            author = owner.get("name", "") if isinstance(owner, dict) else ""

            # 简介
            content = raw_item.get("desc", "")

            # 封面
            cover = raw_item.get("pic", "")

            return CrawlItem(
                platform="bilibili",
                title=title,
                content=content,
                url=url,
                score=int(hot_value),
                comment_count=stat.get("review", 0),
                author=author,
                created_at=datetime.now(),
                raw_data={"bvid": bvid, "cover": cover, "stat": stat, **raw_item},
            )
        except Exception as e:
            logger.warning(f"解析条目失败: {e}")
            return None

    async def fetch_comments(self, bvid: str, limit: int = 10) -> list[dict]:
        """
        抓取指定视频的评论

        Args:
            bvid: 视频BV号
            limit: 最多抓取评论数

        Returns:
            list[dict]: 评论列表
        """
        logger.debug(f"抓取视频评论: bvid={bvid}")

        # 先获取视频的 cid（用作 oid）
        oid_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
        comment_url = "https://api.bilibili.com/x/v2/reply"

        try:
            resp = await self.get(oid_url)
            data = resp.json()

            if data.get("code") != 0:
                logger.debug(f"获取视频信息失败: {data}")
                return []

            oid = data["data"]["cid"]

            params = {
                "type": 1,
                "oid": oid,
                "pn": 1,
                "ps": limit,
                "sort": 2  # 按点赞排序
            }

            response = await self.get(comment_url, params=params)
            comment_data = response.json()

            if comment_data.get("code") == 0:
                replies = comment_data.get("data", {}).get("replies", [])
                logger.debug(f"获取 {len(replies)} 条评论")
                return replies
            else:
                logger.debug(f"评论API错误: {comment_data}")
                return []
        except Exception as e:
            logger.warning(f"抓取评论失败: {e}")
            return []

    def _build_comment_summary(self, comments: list[dict], max_length: int = 500) -> str:
        """
        构建评论摘要

        Args:
            comments: 评论列表
            max_length: 摘要最大长度

        Returns:
            str: 评论摘要
        """
        if not comments:
            return ""

        summary_parts = []
        total_length = 0

        for comment in comments:
            member = comment.get("member", {})
            content = comment.get("content", {}).get("message", "")
            if content:
                author = member.get("uname", "网友")
                summary_parts.append(f"{author}: {content}")
                total_length += len(content)
                if total_length >= max_length:
                    break

        return " | ".join(summary_parts)

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
                # 抓取评论
                bvid = raw_item.get("bvid", "")
                if bvid:
                    try:
                        comments = await self.fetch_comments(bvid, limit=10)
                        if comments:
                            comment_summary = self._build_comment_summary(comments)
                            if comment_summary:
                                if item.content:
                                    item.content = f"{item.content}\n\n[评论摘要] {comment_summary}"
                                else:
                                    item.content = f"[评论摘要] {comment_summary}"
                                top_score = max(
                                    (c.get("like", 0) for c in comments),
                                    default=0
                                )
                                if item.raw_data is None:
                                    item.raw_data = {}
                                item.raw_data["top_comment_score"] = top_score
                    except Exception as e:
                        logger.warning(f"抓取评论失败: {e}")

                items.append(item)

        crawled_at = datetime.now()
        for item in items:
            if item.raw_data is None:
                item.raw_data = {}
            item.raw_data["crawled_at"] = crawled_at.isoformat()

        logger.info(f"解析完成，获取 {len(items)} 条有效数据")
        return items
