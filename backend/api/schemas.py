"""
API 数据模型定义

使用 Pydantic 定义请求和响应的数据结构
"""
from datetime import datetime
from datetime import date as DateType
from typing import Optional

from pydantic import BaseModel, Field


# =============================================================================
# 通用响应模型
# =============================================================================

class ApiResponse(BaseModel):
    """通用 API 响应"""
    code: int = Field(0, description="状态码，0表示成功")
    message: str = Field("", description="响应消息")
    data: Optional[dict] = Field(None, description="响应数据")


class PaginatedResponse(BaseModel):
    """分页响应"""
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    items: list = Field(..., description="数据列表")


# =============================================================================
# 关键词相关
# =============================================================================

class KeywordBase(BaseModel):
    """关键词基础模型"""
    word: str = Field(..., min_length=1, max_length=200, description="关键词")
    category: Optional[str] = Field(None, max_length=20, description="分类")


class KeywordCreate(KeywordBase):
    """创建关键词请求"""
    count: int = Field(..., ge=0, description="出现次数")


class KeywordUpdate(BaseModel):
    """更新关键词请求"""
    category: Optional[str] = Field(None, max_length=20, description="分类")


class KeywordResponse(KeywordBase):
    """关键词响应"""
    id: int = Field(..., description="关键词ID")
    count: int = Field(..., ge=0, description="出现次数")
    first_seen: datetime = Field(..., description="首次出现时间")
    last_seen: datetime = Field(..., description="最后出现时间")

    class Config:
        from_attributes = True


class KeywordWithItems(KeywordResponse):
    """带关联内容的关键词响应"""
    items: list["ItemLite"] = Field(default_factory=list, description="关联的内容")


class KeywordStats(BaseModel):
    """关键词统计"""
    total: int = Field(..., description="关键词总数")
    by_category: dict[str, int] = Field(default_factory=dict, description="按分类统计")


# =============================================================================
# 内容相关
# =============================================================================

class ItemBase(BaseModel):
    """内容基础模型"""
    platform: str = Field(..., max_length=20, description="平台")
    title: str = Field(..., max_length=500, description="标题")
    url: str = Field(..., max_length=1000, description="链接")


class ItemResponse(ItemBase):
    """内容响应"""
    id: int = Field(..., description="内容ID")
    content: Optional[str] = Field(None, description="内容")
    score: int = Field(..., ge=0, description="热度分数")
    comment_count: int = Field(..., ge=0, description="评论数")
    author: Optional[str] = Field(None, max_length=200, description="作者")
    created_at: datetime = Field(..., description="创建时间")
    crawled_at: datetime = Field(..., description="爬取时间")

    class Config:
        from_attributes = True


class ItemLite(BaseModel):
    """内容简要信息（用于关联展示）"""
    id: int
    title: str
    platform: str
    score: int
    url: str

    class Config:
        from_attributes = True


class ItemListResponse(PaginatedResponse):
    """内容列表响应"""
    items: list[ItemResponse]


# =============================================================================
# 趋势相关
# =============================================================================

class TrendBase(BaseModel):
    """趋势基础模型"""
    keyword_id: int = Field(..., description="关键词ID")
    date: DateType = Field(..., description="日期")
    count: int = Field(..., ge=0, description="出现次数")
    avg_score: Optional[float] = Field(None, ge=0, description="平均热度")


class TrendResponse(TrendBase):
    """趋势响应"""
    id: int = Field(..., description="趋势ID")
    keyword: Optional[KeywordBase] = Field(None, description="关键词信息")

    class Config:
        from_attributes = True


class TrendWithKeyword(BaseModel):
    """带关键词信息的趋势"""
    date: DateType = Field(..., description="日期")
    keyword: str = Field(..., description="关键词")
    count: int = Field(..., ge=0, description="出现次数")
    avg_score: Optional[float] = Field(None, description="平均热度")


class RisingKeyword(BaseModel):
    """上升趋势关键词"""
    keyword: str = Field(..., description="关键词")
    current_count: int = Field(..., ge=0, description="当前周期次数")
    previous_count: int = Field(..., ge=0, description="上一周期次数")
    growth_rate: float = Field(..., description="增长率")
    avg_score: float = Field(..., description="平均热度")


# =============================================================================
# 爬虫相关
# =============================================================================

class CrawlerRunRequest(BaseModel):
    """运行爬虫请求"""
    platform: str = Field(..., description="平台: zhihu 或 bilibili")
    limit: int = Field(10, ge=1, le=100, description="抓取数量")


class CrawlerStatus(BaseModel):
    """爬虫状态"""
    is_running: bool = Field(..., description="是否正在运行")
    platform: Optional[str] = Field(None, description="当前运行的平台")
    last_run: Optional[datetime] = Field(None, description="上次运行时间")
    last_count: Optional[int] = Field(None, description="上次抓取数量")


class CrawlerRunResponse(BaseModel):
    """爬虫运行响应"""
    success: bool = Field(..., description="是否成功")
    platform: str = Field(..., description="平台")
    count: int = Field(..., description="抓取数量")
    message: str = Field(..., description="响应消息")


# =============================================================================
# 分析相关
# =============================================================================

class AnalyzeRequest(BaseModel):
    """分析请求"""
    limit: Optional[int] = Field(None, ge=1, le=1000, description="分析数量限制")


class AnalyzeResponse(BaseModel):
    """分析响应"""
    items_analyzed: int = Field(..., description="分析的内容数量")
    keywords_found: int = Field(..., description="发现的关键词数量")
    keywords_updated: int = Field(..., description="更新的关键词数量")
    message: str = Field(..., description="响应消息")


# =============================================================================
# 分类相关
# =============================================================================

class CategoryEnum:
    """分类枚举"""
    TOOL = "TOOL"
    CONTENT = "CONTENT"
    SERVICE = "SERVICE"
    PRODUCT = "PRODUCT"
    LIFESTYLE = "LIFESTYLE"
    CAREER = "CAREER"
    OTHER = "OTHER"

    @classmethod
    def all(cls):
        """所有分类"""
        return [
            cls.TOOL, cls.CONTENT, cls.SERVICE, cls.PRODUCT,
            cls.LIFESTYLE, cls.CAREER, cls.OTHER
        ]


class CategoryStats(BaseModel):
    """分类统计"""
    category: str = Field(..., description="分类")
    count: int = Field(..., description="关键词数量")
    top_keywords: list[str] = Field(..., description="热门关键词")
