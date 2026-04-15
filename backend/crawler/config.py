"""
爬虫配置管理模块
"""
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class CrawlerConfig:
    """
    爬虫基础配置
    """
    # 请求配置
    timeout: int = 30  # 请求超时时间(秒)
    max_retries: int = 3  # 最大重试次数
    retry_delay: float = 2.0  # 重试延迟(秒)

    # 限流配置
    min_delay: float = 5.0  # 最小请求间隔(秒)
    max_delay: float = 15.0  # 最大请求间隔(秒)

    # 数据配置
    max_items_per_run: int = 50  # 单次抓取最大条目数
    user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    # 认证配置
    cookie: Optional[str] = None  # Cookie字符串
    cookie_file: Optional[str] = None  # Cookie文件路径

    # 代理配置(可选)
    proxy: Optional[str] = None

    # 数据目录
    data_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "data")

    def __post_init__(self):
        """确保数据目录存在，并加载Cookie"""
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 如果指定了cookie_file，从文件加载
        if self.cookie_file and not self.cookie:
            self.cookie = self._load_cookie_from_file(self.cookie_file)

    def _load_cookie_from_file(self, file_path: str) -> Optional[str]:
        """
        从文件加载Cookie

        Args:
            file_path: Cookie文件路径

        Returns:
            Optional[str]: Cookie字符串，失败返回None
        """
        path = Path(file_path)

        # 支持相对路径（相对于data_dir）
        if not path.is_absolute():
            path = self.data_dir / file_path

        if not path.exists():
            return None

        try:
            lines = path.read_text(encoding="utf-8").strip().split("\n")
            # 过滤注释行和空行
            cookie_lines = [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]
            content = "; ".join(cookie_lines) if cookie_lines else ""
            if content:
                return content
        except Exception as e:
            import logging
            logging.warning(f"加载Cookie文件失败 {path}: {e}")

        return None


@dataclass
class ZhihuConfig(CrawlerConfig):
    """
    知乎爬虫配置
    """
    # 知乎API端点
    hot_list_url: str = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total"
    answer_url: str = "https://www.zhihu.com/api/v4/questions/{question_id}/answers"

    # 请求参数
    hot_limit: int = 50  # 热榜获取数量
    answer_limit: int = 5  # 每个问题获取回答数量
    answer_sort_by: str = "default"  # 回答排序: default, voting


@dataclass
class BilibiliConfig(CrawlerConfig):
    """
    B站爬虫配置
    """
    # B站API端点
    trending_url: str = "https://api.bilibili.com/x/web-interface/popular"
    video_info_url: str = "https://api.bilibili.com/x/web-interface/view"
    comment_url: str = "https://api.bilibili.com/x/v2/reply"

    # 请求参数
    trending_ps: int = 50  # 热门获取数量
    comment_limit: int = 20  # 每个视频获取评论数量
    comment_order: str = "hot"  # 评论排序: hot, time


# 默认配置实例
default_zhihu_config = ZhihuConfig(
    cookie_file="zhihu_cookie.txt"  # 尝试从文件加载
)
default_bilibili_config = BilibiliConfig(
    cookie_file="bilibili_cookie.txt"  # 尝试从文件加载
)
