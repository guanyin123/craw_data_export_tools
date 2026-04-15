"""
内容分类器模块

根据关键词和内容特征，将内容分类到不同的类别
"""
import logging
from enum import Enum
from typing import Optional, Set

from models.models import Keyword

logger = logging.getLogger(__name__)


class Category(str, Enum):
    """内容分类枚举"""
    TOOL = "TOOL"           # 工具类（软件、APP、SaaS等）
    CONTENT = "CONTENT"     # 内容类（自媒体、博客、视频等）
    SERVICE = "SERVICE"     # 服务类（咨询、教育、代运营等）
    PRODUCT = "PRODUCT"     # 实物类（电商产品、周边等）
    LIFESTYLE = "LIFESTYLE" # 生活类（健康、美食、旅游等）
    CAREER = "CAREER"       # 职业类（求职、创业、技能提升等）
    OTHER = "OTHER"         # 其他


# 分类关键词规则
CATEGORY_KEYWORDS = {
    Category.TOOL: {
        # 软件工具类
        "软件", "app", "应用", "工具", "平台", "系统", "插件", "扩展",
        "ai", "人工智能", "chatgpt", "gpt", "自动化", "脚本", "代码",
        "编辑器", "ide", "框架", "库", "api", "sdk", "开发",
        # SaaS类
        "saas", "订阅", "会员", "账户", "云端", "在线",
        # 效率工具
        "效率", "管理", "协作", "办公", "笔记", "日历", "待办",
    },
    Category.CONTENT: {
        # 内容创作
        "写作", "创作", "文案", "文章", "视频", "音频", "播客",
        "自媒体", "公众号", "小红书", "抖音", "b站", "知乎",
        "博主", "up主", "up", "粉丝", "流量", "变现",
        # 内容类型
        "教程", "指南", "评测", "推荐", "盘点", "合集",
    },
    Category.SERVICE: {
        # 服务类
        "咨询", "顾问", "服务", "外包", "代运营", "代理",
        "教育", "培训", "课程", "教学", "学习", "辅导",
        "设计", "制作", "开发", "定制", "外包",
        # 专业服务
        "法律", "财务", "税务", "审计", "翻译",
    },
    Category.PRODUCT: {
        # 实物产品
        "产品", "商品", "店铺", "电商", "淘宝", "京东", "拼多多",
        "货源", "供应链", "库存", "发货", "物流",
        # 制造
        "生产", "加工", "制造", "工厂", "定制",
        # 实物类别
        "服装", "食品", "数码", "家居", "美妆", "母婴",
    },
    Category.LIFESTYLE: {
        # 生活类
        "健康", "养生", "运动", "健身", "减肥", "饮食",
        "美食", "菜谱", "烹饪", "餐厅", "探店",
        "旅游", "旅行", "景点", "攻略", "民宿",
        # 娱乐
        "游戏", "电影", "音乐", "书籍", "阅读",
    },
    Category.CAREER: {
        # 职业类
        "求职", "招聘", "面试", "简历", "工作", "职业",
        "创业", "副业", "兼职", "自由职业", "远程",
        "薪资", "收入", "赚钱", "理财", "投资",
        # 技能
        "技能", "能力", "提升", "学习", "培训", "证书",
        "转行", "跳槽", "升职", "加薪", "裸辞",
    },
}


class Classifier:
    """
    内容分类器

    基于关键词规则进行分类
    """

    def __init__(self):
        """初始化分类器，预计算小写关键词集合以提升性能"""
        # 预计算小写关键词集合，将 O(n*m) 降低为 O(1) 查找
        self.category_keywords: dict[Category, set[str]] = {
            category: {k.lower() for k in keywords}
            for category, keywords in CATEGORY_KEYWORDS.items()
        }

    def classify_by_keyword(
        self,
        keyword: str,
        default: Category = Category.OTHER
    ) -> Category:
        """
        根据关键词分类

        Args:
            keyword: 关键词
            default: 默认分类

        Returns:
            Category: 分类结果
        """
        keyword_lower = keyword.lower()

        # O(1) 集合查找（已预计算小写集合）
        for category, keywords in self.category_keywords.items():
            if keyword_lower in keywords:
                return category

        return default

    def classify_by_text(
        self,
        text: str,
        default: Category = Category.OTHER
    ) -> Category:
        """
        根据文本内容分类

        Args:
            text: 文本内容
            default: 默认分类

        Returns:
            Category: 分类结果
        """
        if not text:
            return default

        text_lower = text.lower()

        # 统计每个分类的匹配分数
        scores = {}
        for category, keywords in self.category_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    score += 1
            if score > 0:
                scores[category] = score

        # 返回分数最高的分类
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]

        return default

    def batch_classify_keywords(
        self,
        keywords: list[Keyword],
        db_session,
        default: Category = Category.OTHER
    ) -> dict[Category, int]:
        """
        批量分类关键词

        Args:
            keywords: 关键词列表
            db_session: 数据库会话
            default: 默认分类

        Returns:
            dict[Category, int]: 各分类的数量
        """
        counts = {c: 0 for c in Category}

        for keyword in keywords:
            # 如果已有分类，跳过
            if keyword.category:
                counts[Category(keyword.category)] += 1
                continue

            # 分类
            category = self.classify_by_keyword(keyword.word, default)

            # 更新数据库
            keyword.category = category.value

            counts[category] += 1

        try:
            db_session.commit()
            logger.info(f"批量分类完成: {dict(counts)}")
        except Exception as e:
            db_session.rollback()
            logger.error(f"批量分类失败: {e}")
            raise

        return counts

    def get_category_suggestions(
        self,
        keyword: str,
        top_k: int = 3
    ) -> list[tuple[Category, float]]:
        """
        获取分类建议（带相似度分数）

        Args:
            keyword: 关键词
            top_k: 返回前k个建议

        Returns:
            list[tuple[Category, float]]: (分类, 分数) 列表
        """
        scores = []
        keyword_lower = keyword.lower()

        for category, keywords in self.category_keywords.items():
            # 计算相似度分数
            score = 0
            for kw in keywords:
                if kw.lower() in keyword_lower or keyword_lower in kw.lower():
                    score += 1

            if score > 0:
                scores.append((category, score))

        # 按分数排序
        scores.sort(key=lambda x: x[1], reverse=True)

        return scores[:top_k]


# 默认分类器实例
default_classifier = Classifier()
