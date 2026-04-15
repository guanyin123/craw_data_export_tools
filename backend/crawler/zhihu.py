"""
知乎爬虫模块

使用知乎官方API获取热榜数据（需要Cookie）
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional

from .base import BaseCrawler, CrawlItem
from .config import ZhihuConfig

logger = logging.getLogger(__name__)


class ZhihuCrawler(BaseCrawler):
    """
    知乎爬虫

    使用知乎官方API获取热榜数据
    需要配置Cookie才能正常访问
    """

    def __init__(self, config: Optional[ZhihuConfig] = None):
        super().__init__(config or ZhihuConfig())
        self.config: ZhihuConfig  # type: ignore

    def _build_headers(self) -> dict:
        """构建更完整的请求头"""
        return {
            "User-Agent": self.config.user_agent,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://www.zhihu.com/",
            "Origin": "https://www.zhihu.com",
        }

    async def init_client(self):
        """初始化 HTTP 客户端（覆盖基类以添加自定义headers）"""
        from .base import httpx

        if self._client is None or self._client.is_closed:
            headers = self._build_headers()

            # 添加 Cookie
            if self.config.cookie:
                headers["Cookie"] = self.config.cookie
                logger.info(f"{self.__class__.__name__}: 使用已配置的 Cookie")
            else:
                logger.warning(
                    f"{self.__class__.__name__}: 未配置Cookie，可能无法获取数据"
                )

            proxy = self.config.proxy if self.config.proxy else None

            self._client = httpx.AsyncClient(
                headers=headers,
                proxy=proxy,
                timeout=self.config.timeout,
                follow_redirects=True,
            )
            logger.info(f"{self.__class__.__name__}: HTTP 客户端已初始化")

    async def fetch_hot_list(self) -> list[dict]:
        """
        抓取知乎热榜

        Returns:
            list[dict]: 热榜数据列表
        """
        logger.info("抓取知乎热榜...")

        params = {"limit": self.config.hot_limit}
        response = await self.get(self.config.hot_list_url, params=params)

        data = response.json()
        if data.get("data") is None:
            logger.warning(f"热榜响应格式异常: {data}")
            return []

        hot_list = data["data"]
        logger.info(f"获取热榜 {len(hot_list)} 条")
        return hot_list

    async def fetch_answers(self, question_id: str) -> list[dict]:
        """
        抓取指定问题的回答

        Args:
            question_id: 问题 ID

        Returns:
            list[dict]: 回答列表
        """
        logger.debug(f"抓取问题回答: question_id={question_id}")

        params = {
            "limit": self.config.answer_limit,
            "sort_by": self.config.answer_sort_by,
            "include": "content,excerpt,voteup_count,created_time,author"
        }

        url = self.config.answer_url.format(question_id=question_id)
        response = await self.get(url, params=params)

        data = response.json()
        if data.get("data") is None:
            logger.debug(f"回答响应格式异常: {data}")
            return []

        return data["data"]

    def _parse_hot_item(self, raw_item: dict) -> CrawlItem:
        """
        解析热榜条目

        Args:
            raw_item: 原始热榜数据

        Returns:
            CrawlItem: 解析后的数据项
        """
        target = raw_item.get("target", {})
        question_type = raw_item.get("type", "")

        # 基础信息
        title = target.get("title", "")
        question_id = str(target.get("id", ""))
        url = target.get("url", f"https://www.zhihu.com/question/{question_id}")

        # 热度值 (知乎使用格式化的热度字符串，如 "1.2 万热度")
        hot_value_str = raw_item.get("detail_text", "").replace("热度", "").replace("万", "0000").strip()
        try:
            score = int(float(hot_value_str) if hot_value_str else 0)
        except ValueError:
            score = 0

        # 创建时间
        created_time = target.get("created")
        created_at = None
        if created_time:
            try:
                created_at = datetime.fromtimestamp(created_time)
            except (ValueError, OSError):
                pass

        # 作者
        author = None
        if "author" in target:
            author_info = target.get("author", {})
            if isinstance(author_info, dict):
                author = author_info.get("name", "")

        # 摘要作为内容预览
        content = target.get("excerpt", "")

        return CrawlItem(
            platform="zhihu",
            title=title,
            content=content,
            url=url,
            score=score,
            comment_count=0,
            author=author,
            created_at=created_at or datetime.now(),
            raw_data={"type": question_type, "question_id": question_id, **raw_item},
        )

    async def _enrich_item_content(self, item: CrawlItem) -> CrawlItem:
        """
        为条目补充完整内容（抓取高赞回答）

        Args:
            item: 待补充的数据项

        Returns:
            CrawlItem: 补充后的数据项
        """
        if not item.raw_data:
            return item

        question_id = item.raw_data.get("question_id")
        if not question_id:
            return item

        try:
            answers = await self.fetch_answers(question_id)
            if not answers:
                return item

            # 获取最高赞回答
            top_answer = answers[0]
            content = top_answer.get("content", "")
            # 移除 HTML 标签，保留纯文本
            import re
            content = re.sub(r"<[^>]+>", "", content)
            content = content.strip()

            # 更新内容
            item.content = content

            # 更新点赞数（如果回答的点赞数更高）
            answer_voteup = top_answer.get("voteup_count", 0)
            if answer_voteup > item.score:
                item.score = answer_voteup

            # 更新作者（使用回答作者）
            answer_author = top_answer.get("author", {})
            if isinstance(answer_author, dict):
                item.author = answer_author.get("name", item.author)

            logger.debug(f"补充回答内容: {item.title[:30]}...")
        except Exception as e:
            logger.warning(f"补充内容失败: {e}")

        return item

    async def fetch_items(self, limit: Optional[int] = None) -> list[CrawlItem]:
        """
        抓取知乎热榜数据

        Args:
            limit: 最大抓取数量

        Returns:
            list[CrawlItem]: 抓取的数据列表
        """
        max_items = limit or self.config.max_items_per_run

        # 1. 抓取热榜
        hot_list = await self.fetch_hot_list()

        # 2. 解析热榜条目
        items = []
        for raw_item in hot_list[:max_items]:
            try:
                item = self._parse_hot_item(raw_item)
                items.append(item)
            except Exception as e:
                logger.warning(f"解析热榜条目失败: {e}")
                continue

        # 3. 补充完整内容（异步并发抓取回答）
        if items and self.config.answer_limit > 0:
            logger.info(f"开始补充 {len(items)} 个条目的完整内容...")
            enriched_items = await asyncio.gather(
                *[self._enrich_item_content(item) for item in items],
                return_exceptions=True
            )

            # 过滤异常结果
            items = [
                item for item in enriched_items
                if isinstance(item, CrawlItem) and item.content
            ]

        # 4. 添加爬取时间
        crawled_at = datetime.now()
        for item in items:
            if item.raw_data is None:
                item.raw_data = {}
            item.raw_data["crawled_at"] = crawled_at.isoformat()

        return items
