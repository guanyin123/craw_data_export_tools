"""
爬虫基类模块
"""
import asyncio
import logging
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
import httpx
from .config import CrawlerConfig

logger = logging.getLogger(__name__)


@dataclass
class CrawlItem:
    """
    爬取的数据项
    """
    platform: str  # 'zhihu' | 'bilibili'
    title: str
    content: Optional[str]  # 回答内容/评论内容
    url: str
    score: int  # 点赞数/热度
    comment_count: int = 0
    author: Optional[str] = None
    created_at: Optional[datetime] = None
    raw_data: Optional[dict[str, Any]] = None  # 原始数据，用于调试

    def __repr__(self) -> str:
        return f"<CrawlItem(platform={self.platform}, title={self.title[:30]}..., score={self.score})>"


class BaseCrawler(ABC):
    """
    爬虫基类

    子类需要实现:
    - fetch_items(): 抓取数据
    """

    def __init__(self, config: CrawlerConfig):
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
        self._last_request_time: float = 0

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.init_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close_client()

    async def init_client(self):
        """初始化 HTTP 客户端"""
        if self._client is None or self._client.is_closed:
            headers = {
                "User-Agent": self.config.user_agent,
                "Accept": "application/json",
            }

            # 添加 Cookie
            cookies = None
            if self.config.cookie:
                headers["Cookie"] = self.config.cookie
                logger.info(f"{self.__class__.__name__}: 使用已配置的 Cookie")

            # httpx 使用 proxy 参数 (单数形式)
            proxy = self.config.proxy if self.config.proxy else None

            self._client = httpx.AsyncClient(
                headers=headers,
                proxy=proxy,
                timeout=self.config.timeout,
                follow_redirects=True,
            )
            logger.info(f"{self.__class__.__name__}: HTTP 客户端已初始化")

    async def close_client(self):
        """关闭 HTTP 客户端"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            logger.info(f"{self.__class__.__name__}: HTTP 客户端已关闭")

    async def request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> httpx.Response:
        """
        发送 HTTP 请求，带重试和延迟

        Args:
            method: HTTP 方法
            url: 请求 URL
            **kwargs: httpx.request 参数

        Returns:
            httpx.Response: 响应对象

        Raises:
            httpx.HTTPError: 请求失败
        """
        if self._client is None:
            await self.init_client()

        # 限流：计算延迟
        await self._rate_limit()

        # 重试逻辑
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                response = await self._client.request(method, url, **kwargs)
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as e:
                last_error = e
                logger.warning(
                    f"{self.__class__.__name__}: 请求失败 (状态码={e.response.status_code}, "
                    f"尝试 {attempt + 1}/{self.config.max_retries}): {url}"
                )
                if e.response.status_code < 500:
                    # 4xx 错误不重试
                    raise
            except httpx.RequestError as e:
                last_error = e
                logger.warning(
                    f"{self.__class__.__name__}: 请求异常 "
                    f"(尝试 {attempt + 1}/{self.config.max_retries}): {e}"
                )

            # 最后一次不等待
            if attempt < self.config.max_retries - 1:
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))

        raise last_error  # type: ignore

    async def get(self, url: str, **kwargs) -> httpx.Response:
        """GET 请求"""
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs) -> httpx.Response:
        """POST 请求"""
        return await self.request("POST", url, **kwargs)

    async def _rate_limit(self):
        """
        限流：确保请求间隔不低于配置的最小延迟
        """
        current_time = asyncio.get_event_loop().time()
        elapsed = current_time - self._last_request_time

        if elapsed < self.config.min_delay:
            wait_time = self.config.min_delay - elapsed
            logger.debug(f"{self.__class__.__name__}: 限流等待 {wait_time:.2f} 秒")
            await asyncio.sleep(wait_time)

        # 添加随机延迟，避免模式识别
        random_delay = random.uniform(0, self.config.max_delay - self.config.min_delay)
        await asyncio.sleep(random_delay)

        self._last_request_time = asyncio.get_event_loop().time()

    @abstractmethod
    async def fetch_items(self, limit: Optional[int] = None) -> list[CrawlItem]:
        """
        抓取数据

        Args:
            limit: 最大抓取数量，None 使用配置默认值

        Returns:
            list[CrawlItem]: 抓取的数据列表
        """
        pass

    async def crawl(self, limit: Optional[int] = None) -> list[CrawlItem]:
        """
        执行爬取任务

        Args:
            limit: 最大抓取数量

        Returns:
            list[CrawlItem]: 抓取的数据列表
        """
        logger.info(f"{self.__class__.__name__}: 开始爬取, limit={limit or self.config.max_items_per_run}")

        try:
            items = await self.fetch_items(limit)
            logger.info(f"{self.__class__.__name__}: 爬取完成, 获取 {len(items)} 条数据")
            return items
        except Exception as e:
            logger.error(f"{self.__class__.__name__}: 爬取失败: {e}")
            raise
