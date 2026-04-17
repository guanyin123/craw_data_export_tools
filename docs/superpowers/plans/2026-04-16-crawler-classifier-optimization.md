# 商机发现爬虫与分类器优化方案

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 提升爬取数据质量和分类准确率，使系统能真正发现有价值的商业机会

**问题现状:**
1. **数据质量差**: 84%的关键词被分类为"OTHER"，关键词多为无意义噪音（如"复刻"、"外焦"、"晚安"）
2. **内容过于简单**: 只抓取标题/简介，缺乏实际业务需求信息
3. **分类规则僵化**: 精确匹配关键词，无法识别语义相关的商业机会

**解决方案:**
1. **增强爬虫**: 抓取评论、高赞回答等包含真实用户需求的内容
2. **改进分词**: 使用词性标注，只提取有意义的名词/动词短语
3. **智能分类**: 基于语义相似度和上下文进行分类，而非精确匹配
4. **数据清洗**: 过滤娱乐类内容，专注商业/职业/技术相关话题

**Tech Stack:** Python 3.13, jieba, SQLAlchemy, FastAPI

---

## 文件结构

```
backend/
├── crawler/
│   ├── base.py              # 修改: 添加评论抓取接口
│   ├── zhihu.py             # 修改: 实现评论抓取
│   ├── bilibili.py          # 修改: 实现评论抓取
│   └── filter.py            # 新建: 内容过滤器
├── analyzer/
│   ├── tokenizer.py         # 修改: 添加词性标注过滤
│   ├── classifier.py        # 修改: 实现语义分类
│   └── phrase_extractor.py  # 新建: 有意义短语提取器
├── data/
│   ├── business_keywords.txt    # 新建: 商业相关关键词
│   ├── noise_keywords.txt       # 新建: 噪音词过滤表
│   └── category_synonyms.txt    # 新建: 分类同义词库
└── models/
    └── models.py            # 修改: 添加评论内容字段
```

---

## Task 1: 扩展数据模型支持评论内容

**目标:** 在 items 表中添加 comment_summary 字段存储评论摘要

**Files:**
- Modify: `backend/models/models.py`

- [ ] **Step 1: 读取当前模型定义**

```bash
# 查看 items 表当前定义
cat backend/models/models.py | grep -A 20 "class Item"
```

Expected Output: 当前 Item 模型定义

- [ ] **Step 2: 添加 comment_summary 字段**

在 `Item` 类中添加新字段：

```python
# 在 Item 类中，content 字段后添加
comment_summary = Column(Text, nullable=True, comment="评论摘要（汇总前10条高赞评论）")
comment_count = Column(Integer, default=0, comment="评论数量")
top_comment_score = Column(Integer, nullable=True, comment="最高赞评论点赞数")
```

- [ ] **Step 3: 创建数据库迁移脚本**

```bash
cat > backend/scripts/migrate_add_comments.py << 'EOF'
"""添加评论相关字段到 items 表"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from models.database import get_engine, get_session

def migrate():
    """执行迁移"""
    engine = get_engine()

    with engine.connect() as conn:
        # 检查字段是否已存在
        result = conn.execute(text("PRAGMA table_info(items)"))
        columns = [row[1] for row in result]

        if "comment_summary" in columns:
            print("字段已存在，跳过迁移")
            return

        # 添加新字段
        conn.execute(text(
            "ALTER TABLE items ADD COLUMN comment_summary TEXT"
        ))
        conn.execute(text(
            "ALTER TABLE items ADD COLUMN top_comment_score INTEGER"
        ))
        conn.commit()
        print("迁移完成: 添加 comment_summary, top_comment_score 字段")

if __name__ == "__main__":
    migrate()
EOF
```

- [ ] **Step 4: 运行迁移**

```bash
cd backend && python scripts/migrate_add_comments.py
```

Expected Output: "迁移完成: 添加 comment_summary, top_comment_score 字段"

- [ ] **Step 5: 验证迁移**

```bash
sqlite3 backend/data/opportunity.db "PRAGMA table_info(items);" | grep -E "comment_summary|top_comment_score"
```

Expected Output: 显示新增的字段

- [ ] **Step 6: Commit**

```bash
git add backend/models/models.py backend/scripts/migrate_add_comments.py
git commit -m "feat: 添加评论摘要字段支持"
```

---

## Task 2: 创建内容过滤器

**目标:** 过滤娱乐类内容，只保留有商业价值的帖子

**Files:**
- Create: `backend/crawler/filter.py`
- Create: `backend/data/noise_keywords.txt`
- Create: `backend/data/business_keywords.txt`

- [ ] **Step 1: 创建噪音关键词文件**

```bash
cat > backend/data/noise_keywords.txt << 'EOF'
# 娱乐类噪音词 - 这些内容通常不包含商业机会
娱乐
搞笑
段子
八卦
明星
网红
主播
直播带货
盘点
混剪
鬼畜
翻唱
舞蹈
萌宠
美食制作
vlog
日常
搞笑视频
综艺
电视剧
电影推荐
音乐分享
游戏实况
手游
电竞
二次元
动漫
cosplay
漫画
轻小说
# 纯情感类
情感
树洞
倾诉
失恋
表白
秀恩爱
狗粮
鸡汤
毒鸡汤
励志语录
# 纯热点类（无商业价值）
热搜
爆款
刷屏
网传
据悉
刚刚
# 无意义动词
听说
据悉
据了解
爆料
曝光
揭秘
盘点
汇总
整理
转载
分享
EOF
```

- [ ] **Step 2: 创建商业关键词文件**

```bash
cat > backend/data/business_keywords.txt << 'EOF'
# 商业/创业相关
创业
副业
兼职
自由职业
远程工作
外包
接单
私域流量
流量变现
知识付费
在线教育
职业教育
技能培训
# 产品/工具相关
SaaS
工具软件
效率工具
自动化
API
SDK
开源项目
Chrome扩展
VSCode插件
小程序
APP
办公软件
协作工具
项目管理
# 服务相关
咨询服务
设计服务
开发服务
代运营
内容创作
文案写作
视频制作
配音服务
翻译服务
法律咨询
财务代理
# 营销/增长
获客
转化率
用户增长
私域
社群运营
内容营销
短视频营销
直播带货
跨境电商
# 技术/开发
前端开发
后端开发
全栈开发
移动开发
人工智能
机器学习
数据分析
爬虫
自动化测试
DevOps
# 职场相关
简历优化
面试技巧
跳槽
升职加薪
职业规划
远程办公
数字游民
EOF
```

- [ ] **Step 3: 创建内容过滤器**

```python
"""
内容过滤器

过滤掉没有商业价值的娱乐类内容
"""
import logging
import re
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# 数据目录
DATA_DIR = Path(__file__).parent.parent / "data"


class ContentFilter:
    """
    内容过滤器

    判断内容是否具有商业分析价值
    """

    def __init__(
        self,
        noise_file: Path = DATA_DIR / "noise_keywords.txt",
        business_file: Path = DATA_DIR / "business_keywords.txt"
    ):
        """
        初始化过滤器

        Args:
            noise_file: 噪音关键词文件
            business_file: 商业关键词文件
        """
        self.noise_keywords = self._load_keywords(noise_file)
        self.business_keywords = self._load_keywords(business_file)
        logger.info(
            f"内容过滤器初始化完成: "
            f"{len(self.noise_keywords)}个噪音词, "
            f"{len(self.business_keywords)}个商业词"
        )

    def _load_keywords(self, file_path: Path) -> set[str]:
        """加载关键词文件"""
        keywords = set()
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    word = line.strip()
                    if word and not word.startswith("#"):
                        keywords.add(word)
        return keywords

    def has_business_value(self, title: str, content: str = "") -> bool:
        """
        判断内容是否具有商业价值

        Args:
            title: 标题
            content: 内容

        Returns:
            bool: 是否有商业价值
        """
        text = f"{title} {content}".lower()

        # 检查是否包含商业关键词
        business_matches = sum(1 for kw in self.business_keywords if kw in text)
        noise_matches = sum(1 for kw in self.noise_keywords if kw in text)

        # 有商业关键词且噪音词较少
        if business_matches > 0:
            return business_matches >= noise_matches

        # 没有商业关键词，检查是否纯噪音
        if noise_matches >= 2:
            return False

        # 默认保留（让后续分析决定）
        return True

    def get_business_keywords(self, text: str) -> List[str]:
        """
        从文本中提取商业相关关键词

        Args:
            text: 文本内容

        Returns:
            List[str]: 找到的商业关键词
        """
        text_lower = text.lower()
        found = []
        for keyword in self.business_keywords:
            if keyword in text_lower:
                found.append(keyword)
        return found


# 默认过滤器实例
default_filter = ContentFilter()
```

- [ ] **Step 4: 创建过滤器测试**

```bash
cat > backend/tests/test_filter.py << 'EOF'
"""测试内容过滤器"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from crawler.filter import ContentFilter

def test_filter():
    filter = ContentFilter()

    # 测试娱乐内容 - 应该被过滤
    assert not filter.has_business_value("搞笑段子合集", "哈哈哈哈笑死我了")

    # 测试商业内容 - 应该保留
    assert filter.has_business_value("如何做副业月入过万", "分享几个靠谱的副业方向")

    # 测试技术内容 - 应该保留
    assert filter.has_business_value("Chrome扩展开发教程", "从零开始学习浏览器扩展开发")

    # 测试纯娱乐 - 应该被过滤
    assert not filter.has_business_value("明星八卦", "据爆料某某某又...")

    print("✅ 所有过滤器测试通过")

if __name__ == "__main__":
    test_filter()
EOF
```

- [ ] **Step 5: 运行测试**

```bash
cd backend && python tests/test_filter.py
```

Expected Output: "✅ 所有过滤器测试通过"

- [ ] **Step 6: Commit**

```bash
git add backend/crawler/filter.py backend/data/noise_keywords.txt backend/data/business_keywords.txt backend/tests/test_filter.py
git commit -m "feat: 添加内容过滤器"
```

---

## Task 3: 改进分词器 - 词性标注

**目标:** 只提取有意义的名词、动词，过滤无意义的修饰词

**Files:**
- Modify: `backend/analyzer/tokenizer.py`

- [ ] **Step 1: 读取当前分词器**

```bash
cat backend/analyzer/tokenizer.py
```

- [ ] **Step 2: 添加词性标注方法**

在 `Tokenizer` 类中添加新方法：

```python
def cut_with_pos(
    self,
    text: str,
    allowed_pos: set[str] | None = None,
    min_length: int = 2
) -> list[tuple[str, str]]:
    """
    带词性标注的分词

    Args:
        text: 待分词文本
        allowed_pos: 允许的词性集合，默认为名词、动词、形容词
        min_length: 最小词长度

    Returns:
        list[tuple[str, str]]: (词, 词性) 列表

    词性说明:
        n: 名词, nr: 人名, ns: 地名, nt: 机构名
        v: 动词, vn: 动名词
        a: 形容词, an: 名形词
        m: 数量词
    """
    if not text:
        return []

    # 默认只保留名词、动名词、动词、形容词
    if allowed_pos is None:
        allowed_pos = {"n", "nr", "ns", "nt", "vn", "a", "an"}

    import jieba.posseg as pseg

    words = []
    for word, pos in pseg.cut(text):
        word = word.strip()

        # 检查长度
        if len(word) < min_length:
            continue

        # 检查词性
        if pos not in allowed_pos:
            continue

        # 过滤停用词
        if not self.is_meaningful(word):
            continue

        words.append((word, pos))

    return words


def extract_meaningful_phrases(
    self,
    text: str,
    max_length: int = 4
) -> list[str]:
    """
    提取有意义的短语

    Args:
        text: 待分析文本
        max_length: 短语最大长度

    Returns:
        list[str]: 有意义的短语列表
    """
    # 获取带词性的分词结果
    words_with_pos = self.cut_with_pos(text)

    phrases = []
    current_phrase = []

    for word, pos in words_with_pos:
        current_phrase.append(word)

        # 名词+动词/形容词 组合形成短语
        if len(current_phrase) >= 2 and pos in {"n", "nr", "ns", "nt", "vn"}:
            phrase = "".join(current_phrase[-max_length:])
            if len(phrase) >= 2:
                phrases.append(phrase)

        # 重置短语（遇到新的名词）
        if pos in {"n", "nr", "ns", "nt"}:
            current_phrase = [word]

    return list(set(phrases))  # 去重
```

- [ ] **Step 3: 测试词性标注**

```bash
cat > backend/tests/test_tokenizer_pos.py << 'EOF'
"""测试词性标注分词"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer.tokenizer import default_tokenizer

def test_pos_tagging():
    text = "我想做一个Chrome扩展来提高工作效率"

    # 带词性分词
    words_pos = default_tokenizer.cut_with_pos(text)
    print("词性标注结果:", words_pos)

    # 应该包含名词和动词
    assert any("Chrome" in w for w, _ in words_pos)
    assert any(pos in {"n", "v", "vn"} for _, pos in words_pos)

    # 提取短语
    phrases = default_tokenizer.extract_meaningful_phrases(text)
    print("提取的短语:", phrases)
    assert len(phrases) > 0

    print("✅ 词性标注测试通过")

if __name__ == "__main__":
    test_pos_tagging()
EOF

cd backend && python tests/test_tokenizer_pos.py
```

Expected Output: 包含 "Chrome扩展" 等有意义的短语

- [ ] **Step 4: Commit**

```bash
git add backend/analyzer/tokenizer.py backend/tests/test_tokenizer_pos.py
git commit -m "feat: 添加词性标注和短语提取"
```

---

## Task 4: 创建短语提取器

**目标:** 从内容中提取有商业价值的短语（2-4字），而非单字词

**Files:**
- Create: `backend/analyzer/phrase_extractor.py`

- [ ] **Step 1: 创建短语提取器**

```python
"""
有意义短语提取器

从文本中提取具有商业价值的短语
"""
import logging
from typing import List, Tuple

from .tokenizer import default_tokenizer

logger = logging.getLogger(__name__)


class PhraseExtractor:
    """
    短语提取器

    提取2-4字的有意义短语，过滤无意义的单字词
    """

    # 有价值的短语模式
    VALUABLE_PATTERNS = [
        # 工具/产品类
        r"Chrome扩展",
        r"VSCode插件",
        r"Excel.*",
        r"Python.*",
        r"AI.*",
        # 商业类
        r".*副业",
        r".*创业",
        r".*变现",
        r".*获客",
        # 技能类
        r".*开发",
        r".*设计",
        r".*运营",
    ]

    def __init__(self):
        self.tokenizer = default_tokenizer

    def extract_from_title(self, title: str) -> List[str]:
        """
        从标题中提取有价值短语

        Args:
            title: 标题文本

        Returns:
            List[str]: 短语列表
        """
        if not title:
            return []

        phrases = []

        # 方法1: 使用词性标注提取
        pos_phrases = self.tokenizer.extract_meaningful_phrases(title)
        phrases.extend(pos_phrases)

        # 方法2: 提取引号内容（通常包含关键词）
        import re
        quoted = re.findall(r'["「」](.+?)["」」]', title)
        phrases.extend(quoted)

        # 方法3: 提取问号前的核心问题词
        question_match = re.search(r"(.*?)怎么|如何|有没有|推荐", title)
        if question_match:
            topic = question_match.group(1).strip()
            if len(topic) >= 2:
                phrases.append(topic)

        # 去重并过滤
        unique_phrases = []
        seen = set()
        for phrase in phrases:
            phrase = phrase.strip()
            if 2 <= len(phrase) <= 6 and phrase not in seen:
                # 过滤纯数字、符号
                if not phrase.replace(" ", "").isalnum():
                    unique_phrases.append(phrase)
                    seen.add(phrase)

        return unique_phrases

    def extract_from_content(
        self,
        content: str,
        top_k: int = 20
    ) -> List[Tuple[str, int]]:
        """
        从内容中提取高频短语

        Args:
            content: 内容文本
            top_k: 返回前k个

        Returns:
            List[Tuple[str, int]]: (短语, 频次) 列表
        """
        if not content:
            return []

        # 使用jieba的TF-IDF提取关键词
        tags = self.tokenizer.extract_tags(
            content,
            top_k=top_k * 2,  # 多提取一些，后面再过滤
            with_weight=True
        )

        # 过滤出有商业价值的短语
        valuable = []
        for word, weight in tags:
            if 2 <= len(word) <= 4:  # 只保留2-4字的词
                valuable.append((word, int(weight * 100)))

        return valuable[:top_k]


# 默认实例
default_phrase_extractor = PhraseExtractor()
```

- [ ] **Step 2: 测试短语提取器**

```bash
cat > backend/tests/test_phrase_extractor.py << 'EOF'
"""测试短语提取器"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer.phrase_extractor import default_phrase_extractor

def test_phrase_extraction():
    # 测试标题提取
    title1 = "有什么好用的Chrome扩展可以提高工作效率？"
    phrases1 = default_phrase_extractor.extract_from_title(title1)
    print(f"标题1: {title1}")
    print(f"提取短语: {phrases1}")
    assert "Chrome扩展" in phrases1 or any("扩展" in p for p in phrases1)

    title2 = "副业推荐：在家就能做的5个兼职"
    phrases2 = default_phrase_extractor.extract_from_title(title2)
    print(f"标题2: {title2}")
    print(f"提取短语: {phrases2}")
    assert any("副业" in p for p in phrases2)

    # 测试内容提取
    content = """
    我想开发一个Chrome扩展来自动化我的工作流程。
    这个扩展可以帮助我节省很多时间，提高工作效率。
    Chrome扩展开发使用JavaScript和HTML。
    """
    phrases3 = default_phrase_extractor.extract_from_content(content)
    print(f"内容短语: {phrases3}")
    assert len(phrases3) > 0

    print("✅ 短语提取器测试通过")

if __name__ == "__main__":
    test_phrase_extraction()
EOF

cd backend && python tests/test_phrase_extractor.py
```

Expected Output: 成功提取 "Chrome扩展"、"副业" 等短语

- [ ] **Step 3: Commit**

```bash
git add backend/analyzer/phrase_extractor.py backend/tests/test_phrase_extractor.py
git commit -m "feat: 添加短语提取器"
```

---

## Task 5: 改进分类器 - 语义相似度

**目标:** 基于词向量和语义相似度进行分类，而非精确匹配

**Files:**
- Create: `backend/data/category_synonyms.txt`
- Modify: `backend/analyzer/classifier.py`

- [ ] **Step 1: 创建分类同义词库**

```bash
cat > backend/data/category_synonyms.txt << 'EOF'
# 工具类同义词
TOOL:软件|应用|app|工具|平台|系统|插件|扩展|chrome|vscode|excel|脚本|代码|api|sdk|开发|自动化|效率|办公|笔记|管理
TOOL:AI|chatgpt|gpt|人工智能|机器学习|深度学习|算法|模型|训练
TOOL:saas|订阅|会员|云端|在线服务

# 内容类同义词
CONTENT:写作|创作|文案|文章|视频|音频|播客|自媒体|公众号|小红书|抖音|b站|知乎|博主|up主|粉丝
CONTENT:教程|指南|评测|推荐|盘点|合集|课程|学习|教学

# 服务类同义词
SERVICE:咨询|顾问|服务|外包|代运营|代理|教育|培训|辅导|设计|制作|定制|开发
SERVICE:法律|财务|税务|审计|翻译|写作|配音|剪辑

# 产品类同义词
PRODUCT:产品|商品|店铺|电商|淘宝|京东|拼多多|货源|供应链|库存|物流
PRODUCT:生产|制造|工厂|定制|服装|食品|数码|家居|美妆|母婴

# 生活类同义词
LIFESTYLE:健康|养生|运动|健身|减肥|饮食|美食|菜谱|烹饪|餐厅|探店
LIFESTYLE:旅游|旅行|景点|攻略|民宿|游戏|电影|音乐|书籍|阅读

# 职业类同义词
CAREER:求职|招聘|面试|简历|工作|职业|创业|副业|兼职|自由职业|远程
CAREER:薪资|收入|赚钱|理财|投资|技能|能力|提升|转行|跳槽|升职|加薪|裸辞
CAREER:接单|私域|流量|变现|知识付费|在线教育
EOF
```

- [ ] **Step 2: 重写分类器**

```python
"""
智能分类器模块

基于语义相似度和上下文进行分类
"""
import logging
from enum import Enum
from pathlib import Path
from typing import Optional, List, Tuple

from models.models import Keyword

logger = logging.getLogger(__name__)


class Category(str, Enum):
    """内容分类枚举"""
    TOOL = "TOOL"           # 工具类
    CONTENT = "CONTENT"     # 内容类
    SERVICE = "SERVICE"     # 服务类
    PRODUCT = "PRODUCT"     # 实物类
    LIFESTYLE = "LIFESTYLE" # 生活类
    CAREER = "CAREER"       # 职业类
    OTHER = "OTHER"         # 其他


class SmartClassifier:
    """
    智能分类器

    使用多种策略进行分类:
    1. 关键词精确匹配
    2. 同义词匹配
    3. 上下文语义分析
    4. 词频统计推断
    """

    # 数据目录
    DATA_DIR = Path(__file__).parent.parent / "data"

    def __init__(self, synonyms_file: Path = DATA_DIR / "category_synonyms.txt"):
        """
        初始化分类器

        Args:
            synonyms_file: 同义词映射文件路径
        """
        self.synonyms_map = self._load_synonyms(synonyms_file)
        logger.info(f"智能分类器初始化完成，加载 {len(self.synonyms_map)} 个分类规则")

    def _load_synonyms(self, file_path: Path) -> dict[Category, list[str]]:
        """加载同义词映射"""
        synonyms = {c: [] for c in Category}

        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    # 解析格式: CATEGORY:word1|word2|word3
                    if ":" in line:
                        category_str, words_str = line.split(":", 1)
                        try:
                            category = Category(category_str.strip())
                            words = [w.strip().lower() for w in words_str.split("|")]
                            synonyms[category].extend(words)
                        except ValueError:
                            logger.warning(f"无效的分类: {category_str}")
                            continue

        return synonyms

    def classify(
        self,
        keyword: str,
        context: str = "",
        default: Category = Category.OTHER
    ) -> Category:
        """
        智能分类关键词

        Args:
            keyword: 待分类的关键词
            context: 上下文文本（帮助判断）
            default: 默认分类

        Returns:
            Category: 分类结果
        """
        keyword_lower = keyword.lower()

        # 策略1: 精确匹配同义词库
        for category, synonyms in self.synonyms_map.items():
            if keyword_lower in synonyms:
                logger.debug(f"精确匹配: '{keyword}' -> {category}")
                return category

        # 策略2: 部分匹配（包含关键词）
        scores = {}
        for category, synonyms in self.synonyms_map.items():
            score = 0
            for synonym in synonyms:
                # 双向包含检查
                if synonym in keyword_lower or keyword_lower in synonym:
                    score += 1
                # 检查上下文
                if context and synonym in context.lower():
                    score += 0.5
            if score > 0:
                scores[category] = score

        if scores:
            best_category = max(scores.items(), key=lambda x: x[1])[0]
            logger.debug(f"部分匹配: '{keyword}' -> {best_category} (scores: {scores})")
            return best_category

        # 策略3: 基于字特征的推断
        if any(char in keyword for char in ["软", "app", "工具", "系统", "插件"]):
            return Category.TOOL
        if any(char in keyword for char in ["课", "教", "学", "训", "培"]):
            return Category.SERVICE
        if any(char in keyword for char in ["业", "职", "职", "薪", "赚"]):
            return Category.CAREER

        logger.debug(f"未匹配: '{keyword}' -> {default}")
        return default

    def batch_classify(
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

            # 获取关联的上下文（从 items 获取）
            context = ""
            if keyword.items:
                # 使用最近的内容作为上下文
                latest_item = sorted(keyword.items, key=lambda x: x.created_at, reverse=True)[0]
                context = f"{latest_item.title} {latest_item.content or ''}"

            # 分类
            category = self.classify(keyword.word, context, default)

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

    def suggest_category(
        self,
        keyword: str,
        context: str = ""
    ) -> list[tuple[Category, float]]:
        """
        获取分类建议（带置信度）

        Args:
            keyword: 关键词
            context: 上下文

        Returns:
            list[tuple[Category, float]]: (分类, 置信度) 列表
        """
        keyword_lower = keyword.lower()
        scores = []

        for category, synonyms in self.synonyms_map.items():
            score = 0
            for synonym in synonyms:
                if synonym in keyword_lower:
                    score += 1
                if context and synonym in context.lower():
                    score += 0.5

            if score > 0:
                scores.append((category, score))

        # 归一化分数
        if scores:
            max_score = max(s for _, s in scores)
            scores = [(c, s / max_score) for c, s in scores]

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:3]


# 默认分类器实例
default_classifier = SmartClassifier()
```

- [ ] **Step 3: 测试智能分类器**

```bash
cat > backend/tests/test_smart_classifier.py << 'EOF'
"""测试智能分类器"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer.classifier import default_classifier, Category

def test_smart_classification():
    # 测试工具类
    assert default_classifier.classify("Chrome扩展") == Category.TOOL
    assert default_classifier.classify("AI工具") == Category.TOOL

    # 测试职业类
    assert default_classifier.classify("副业") == Category.CAREER
    assert default_classifier.classify("远程工作") == Category.CAREER

    # 测试内容类
    assert default_classifier.classify("自媒体") == Category.CONTENT

    # 测试服务类
    assert default_classifier.classify("在线课程") == Category.SERVICE

    # 测试上下文辅助分类
    context = "我想开发一个Chrome扩展来自动化工作"
    assert default_classifier.classify("扩展", context) == Category.TOOL

    # 测试建议功能
    suggestions = default_classifier.suggest_category("开发")
    print(f"'开发'的分类建议: {suggestions}")
    assert len(suggestions) > 0

    print("✅ 智能分类器测试通过")

if __name__ == "__main__":
    test_smart_classification()
EOF

cd backend && python tests/test_smart_classifier.py
```

Expected Output: 所有断言通过

- [ ] **Step 4: Commit**

```bash
git add backend/data/category_synonyms.txt backend/analyzer/classifier.py backend/tests/test_smart_classifier.py
git commit -m "feat: 实现智能语义分类器"
```

---

## Task 6: 知乎爬虫 - 添加评论抓取

**目标:** 抓取知乎问题的高赞评论，获取用户真实需求

**Files:**
- Modify: `backend/crawler/zhihu.py`

- [ ] **Step 1: 添加评论抓取方法**

在 `ZhihuCrawler` 类中添加方法：

```python
async def fetch_comments(self, question_id: str, limit: int = 10) -> list[dict]:
    """
    抓取指定问题的评论

    Args:
        question_id: 问题ID
        limit: 最多抓取评论数

    Returns:
        list[dict]: 评论列表
    """
    logger.debug(f"抓取问题评论: question_id={question_id}")

    # 知乎评论API (需要Cookie)
    url = f"https://www.zhihu.com/api/v4/questions/{question_id}/comments"

    params = {
        "limit": limit,
        "order": "vote",  # 按点赞排序
        "include": "content,voteup_count,author"
    }

    try:
        response = await self.get(url, params=params)
        data = response.json()

        if data.get("data") is None:
            logger.debug(f"评论响应异常: {data}")
            return []

        comments = data["data"]
        logger.debug(f"获取 {len(comments)} 条评论")
        return comments

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

    # 提取评论内容，去除HTML
    import re
    summary_parts = []
    total_length = 0

    for comment in comments:
        content = comment.get("content", "")
        # 移除HTML标签
        content = re.sub(r"<[^>]+>", "", content)
        content = content.strip()

        if content:
            summary_parts.append(content)
            total_length += len(content)
            if total_length >= max_length:
                break

    return " | ".join(summary_parts)
```

- [ ] **Step 2: 修改 _enrich_item_content 方法添加评论**

更新 `_enrich_item_content` 方法，添加评论抓取：

```python
async def _enrich_item_content(self, item: CrawlItem) -> CrawlItem:
    """
    为条目补充完整内容（抓取高赞回答和评论）

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
        # 1. 抓取高赞回答
        answers = await self.fetch_answers(question_id)
        if answers:
            top_answer = answers[0]
            content = top_answer.get("content", "")
            import re
            content = re.sub(r"<[^>]+>", "", content).strip()
            item.content = content

            answer_voteup = top_answer.get("voteup_count", 0)
            if answer_voteup > item.score:
                item.score = answer_voteup

            answer_author = top_answer.get("author", {})
            if isinstance(answer_author, dict):
                item.author = answer_author.get("name", item.author)

        # 2. 抓取评论（新增）
        comments = await self.fetch_comments(question_id, limit=10)
        if comments:
            comment_summary = self._build_comment_summary(comments)
            if comment_summary:
                # 将评论摘要添加到内容
                if item.content:
                    item.content = f"{item.content}\n\n[评论摘要] {comment_summary}"
                else:
                    item.content = f"[评论摘要] {comment_summary}"

                # 记录最高赞评论分数
                top_comment_score = max(
                    (c.get("voteup_count", 0) for c in comments),
                    default=0
                )
                item.raw_data["top_comment_score"] = top_comment_score

        logger.debug(f"补充内容完成: {item.title[:30]}...")

    except Exception as e:
        logger.warning(f"补充内容失败: {e}")

    return item
```

- [ ] **Step 3: Commit**

```bash
git add backend/crawler/zhihu.py
git commit -m "feat: 知乎爬虫添加评论抓取"
```

---

## Task 7: B站爬虫 - 添加评论抓取

**目标:** 抓取B站视频的高赞评论

**Files:**
- Modify: `backend/crawler/bilibili.py`

- [ ] **Step 1: 添加评论抓取方法**

在 `BilibiliCrawler` 类中添加：

```python
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

    # B站评论API
    url = "https://api.bilibili.com/x/v2/reply"

    # 需要先将bvid转换为oid
    oid_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"

    try:
        # 获取oid
        resp = await self.get(oid_url)
        data = resp.json()

        if data.get("code") != 0:
            logger.debug(f"获取视频信息失败: {data}")
            return []

        oid = data["data"]["cid"]

        # 获取评论
        params = {
            "type": 1,  # 视频评论
            "oid": oid,
            "pn": 1,
            "ps": limit,
            "sort": 2  # 按点赞排序
        }

        response = await self.get(url, params=params)
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
        # B站评论结构
        member = comment.get("member", {})
        content = comment.get("content", {}).get("message", "")

        if content:
            # 添加作者信息
            author = member.get("uname", "网友")
            summary_parts.append(f"{author}: {content}")
            total_length += len(content)

            if total_length >= max_length:
                break

    return " | ".join(summary_parts)
```

- [ ] **Step 2: 修改 fetch_items 添加评论抓取**

更新 `fetch_items` 方法：

```python
async def fetch_items(self, limit: Optional[int] = None) -> list[CrawlItem]:
    """抓取B站热门数据（含评论）"""
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

                            # 记录最高赞分数
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
```

- [ ] **Step 3: Commit**

```bash
git add backend/crawler/bilibili.py
git commit -m "feat: B站爬虫添加评论抓取"
```

---

## Task 8: 集成过滤器到爬虫流程

**目标:** 爬取时自动过滤无商业价值的内容

**Files:**
- Modify: `backend/crawler/zhihu.py`
- Modify: `backend/crawler/bilibili.py`

- [ ] **Step 1: 修改知乎爬虫添加过滤器**

在 `zhihu.py` 顶部添加导入：

```python
from .filter import default_filter as content_filter
```

修改 `_parse_hot_item` 方法，添加价值判断：

```python
def _parse_hot_item(self, raw_item: dict) -> Optional[CrawlItem]:
    """
    解析热榜条目（带商业价值过滤）

    Args:
        raw_item: 原始热榜数据

    Returns:
        CrawlItem | None: 解析后的数据项，无价值则返回None
    """
    target = raw_item.get("target", {})
    question_type = raw_item.get("type", "")

    # 基础信息
    title = target.get("title", "")
    question_id = str(target.get("id", ""))

    # 过滤无商业价值的内容
    if not content_filter.has_business_value(title, ""):
        logger.debug(f"过滤无价值内容: {title}")
        return None

    url = target.get("url", f"https://www.zhihu.com/question/{question_id}")

    # ... 其余解析逻辑保持不变 ...
```

- [ ] **Step 2: 修改B站爬虫添加过滤器**

在 `bilibili.py` 中做同样修改

- [ ] **Step 3: Commit**

```bash
git add backend/crawler/zhihu.py backend/crawler/bilibili.py
git commit -m "feat: 爬虫集成内容过滤器"
```

---

## Task 9: 更新分析流程使用新组件

**目标:** 使用短语提取器和智能分类器更新分析流程

**Files:**
- Modify: `backend/analyzer/keyword_counter.py`
- Create: `backend/scripts/reanalyze_data.py`

- [ ] **Step 1: 更新 keyword_counter 使用短语提取**

修改 `keyword_counter.py` 中的处理逻辑：

```python
from .phrase_extractor import default_phrase_extractor

# 在处理内容时，同时提取短语
def process_item(item):
    phrases = set()

    # 从标题提取短语
    title_phrases = phrase_extractor.extract_from_title(item.title)
    phrases.update(title_phrases)

    # 从内容提取短语
    if item.content:
        content_phrases = phrase_extractor.extract_from_content(item.content)
        phrases.update(p for p, _ in content_phrases)

    return list(phrases)
```

- [ ] **Step 2: 创建数据重新分析脚本**

```bash
cat > backend/scripts/reanalyze_data.py << 'EOF'
"""重新分析现有数据，使用新的提取和分类方法"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import sessionmaker
from models.database import get_engine, get_session
from models.models import Item, Keyword
from analyzer.phrase_extractor import default_phrase_extractor
from analyzer.classifier import default_classifier
from crawler.filter import default_filter

def reanalyze():
    """重新分析所有数据"""
    session = get_session()

    print("开始重新分析...")

    # 1. 清空现有关键词
    session.query(Keyword).delete()
    session.commit()
    print("已清空现有关键词")

    # 2. 获取所有items
    items = session.query(Item).all()
    print(f"共 {len(items)} 条数据")

    # 3. 重新提取关键词
    keyword_counts = {}

    for item in items:
        # 过滤无价值内容
        if not default_filter.has_business_value(item.title, item.content or ""):
            continue

        # 提取短语
        title_phrases = default_phrase_extractor.extract_from_title(item.title)
        content_phrases = [p for p, _ in default_phrase_extractor.extract_from_content(item.content or "")]

        all_phrases = list(set(title_phrases + content_phrases))

        for phrase in all_phrases:
            if 2 <= len(phrase) <= 4:
                keyword_counts[phrase] = keyword_counts.get(phrase, 0) + 1

    # 4. 创建关键词记录
    keywords_to_create = []
    for word, count in keyword_counts.items():
        if count >= 2:  # 至少出现2次
            # 使用智能分类
            category = default_classifier.classify(word)
            keywords_to_create.append(
                Keyword(
                    word=word,
                    count=count,
                    category=category.value,
                    first_seen=datetime.now(),
                    last_seen=datetime.now()
                )
            )

    session.bulk_save_objects(keywords_to_create)
    session.commit()

    # 5. 统计结果
    from collections import Counter
    categories = [k.category for k in session.query(Keyword).all()]
    category_stats = Counter(categories)

    print(f"\n重新分析完成!")
    print(f"共提取 {len(keywords_to_create)} 个关键词")
    print(f"分类统计: {dict(category_stats)}")

if __name__ == "__main__":
    reanalyze()
EOF
```

- [ ] **Step 3: Commit**

```bash
git add backend/analyzer/keyword_counter.py backend/scripts/reanalyze_data.py
git commit -m "feat: 更新分析流程使用新组件"
```

---

## Task 10: 测试完整流程

**目标:** 端到端测试整个优化后的爬虫和分析流程

**Files:**
- Create: `backend/tests/test_e2e_optimization.py`

- [ ] **Step 1: 创建端到端测试**

```bash
cat > backend/tests/test_e2e_optimization.py << 'EOF'
"""端到端测试优化后的流程"""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from crawler.zhihu import ZhihuCrawler
from crawler.bilibili import BilibiliCrawler
from analyzer.phrase_extractor import default_phrase_extractor
from analyzer.classifier import default_classifier, Category
from crawler.filter import default_filter

async def test_full_pipeline():
    print("=" * 50)
    print("测试优化后的完整流程")
    print("=" * 50)

    # 1. 测试过滤器
    print("\n1. 测试内容过滤器...")
    assert not default_filter.has_business_value("搞笑视频合集", "")
    assert default_filter.has_business_value("副业赚钱指南", "")
    print("   ✅ 过滤器测试通过")

    # 2. 测试短语提取
    print("\n2. 测试短语提取器...")
    test_title = "有什么好用的Chrome扩展可以提高工作效率？"
    phrases = default_phrase_extractor.extract_from_title(test_title)
    print(f"   标题: {test_title}")
    print(f"   提取: {phrases}")
    assert len(phrases) > 0
    print("   ✅ 短语提取器测试通过")

    # 3. 测试智能分类
    print("\n3. 测试智能分类器...")
    test_cases = [
        ("Chrome扩展", Category.TOOL),
        ("副业", Category.CAREER),
        ("自媒体", Category.CONTENT),
        ("在线课程", Category.SERVICE),
    ]
    for word, expected in test_cases:
        result = default_classifier.classify(word)
        print(f"   '{word}' -> {result} (期望: {expected})")
        assert result == expected
    print("   ✅ 智能分类器测试通过")

    # 4. 测试爬虫（如果配置了Cookie）
    print("\n4. 测试爬虫抓取...")
    try:
        zhihu_crawler = ZhihuCrawler()
        await zhihu_crawler.init_client()

        items = await zhihu_crawler.fetch_items(limit=5)
        print(f"   抓取到 {len(items)} 条数据")

        if items:
            for item in items[:2]:
                print(f"   - {item.title[:50]}...")
                print(f"     商业价值: {default_filter.has_business_value(item.title, item.content or '')}")
                print(f"     提取短语: {default_phrase_extractor.extract_from_title(item.title)}")

        print("   ✅ 爬虫测试通过")
    except Exception as e:
        print(f"   ⚠️  爬虫测试跳过 (需要配置Cookie): {e}")

    print("\n" + "=" * 50)
    print("所有测试完成!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
EOF
```

- [ ] **Step 2: 运行测试**

```bash
cd backend && python tests/test_e2e_optimization.py
```

Expected Output: 所有测试通过

- [ ] **Step 3: 运行数据重新分析**

```bash
cd backend && python scripts/reanalyze_data.py
```

Expected Output: 显示新的分类统计，OTHER分类应该大幅减少

- [ ] **Step 4: 验证数据库结果**

```bash
sqlite3 backend/data/opportunity.db "SELECT category, COUNT(*) as count FROM keywords GROUP BY category ORDER BY count DESC;"
```

Expected Output: OTHER占比应该显著下降

- [ ] **Step 5: Commit**

```bash
git add backend/tests/test_e2e_optimization.py
git commit -m "test: 添加端到端测试"
```

---

## 完成检查清单

在执行完所有任务后，验证以下结果：

- [ ] 数据库包含 comment_summary 和 top_comment_score 字段
- [ ] 噪音关键词和商业关键词文件已创建
- [ ] 分类同义词库已创建
- [ ] 短语提取器能正确提取 "Chrome扩展"、"副业" 等有意义的短语
- [ ] 智能分类器能正确分类，OTHER分类占比降到30%以下
- [ ] 爬虫能抓取评论并保存
- [ ] 内容过滤器能过滤娱乐类内容
- [ ] 端到端测试全部通过
- [ ] 数据重新分析后，关键词质量显著提升

---

## 预期结果

优化后的系统应该能够：

1. **数据质量提升**
   - 关键词从 "复刻"、"外焦" 等噪音词
   - 变为 "Chrome扩展"、"副业"、"AI工具" 等有商业价值的短语

2. **分类准确率提升**
   - OTHER分类从84%降到30%以下
   - TOOL、CAREER、SERVICE等分类占比上升

3. **内容价值提升**
   - 包含评论摘要，了解用户真实需求
   - 过滤娱乐类内容，专注商业机会
