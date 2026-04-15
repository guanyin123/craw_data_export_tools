# 商机发现 MVP (Opportunity Discovery)

> 通过爬取知乎、B站等平台的热门内容，分析用户需求，发现副业/创业机会

## 项目概述

本项目旨在通过数据驱动的方式发现市场机会，主要功能包括：

- **双模式支持**
  - 机会扫描模式：广泛扫描各平台热门内容，发现可立即执行的副业/创业机会
  - 领域洞察模式：针对关键词/领域深度分析，了解垂直领域用户痛点

- **核心功能**
  - 高频词 Top100 榜单
  - 分类聚合（工具类/内容类/服务类等）
  - 趋势分析（时间维度，显示需求上升/下降趋势）

## 技术栈

| 层级 | 技术选择 |
|-----|---------|
| 前端 | React 18 + TypeScript + Ant Design 5 |
| 后端 | FastAPI + SQLAlchemy |
| 数据库 | SQLite |
| 分词 | jieba |

## 项目结构

```
craw_data_export_tools/
├── backend/           # 后端服务
│   ├── crawler/       # 爬虫模块
│   ├── analyzer/      # 分析模块
│   ├── api/           # API 接口
│   ├── models/        # 数据模型
│   └── data/          # 数据文件
├── frontend/          # 前端应用
│   └── src/
│       ├── pages/     # 页面组件
│       ├── components/# 通用组件
│       ├── store/     # 状态管理
│       └── api/       # API 客户端
└── scripts/           # 工具脚本
```

## 开发进度

详见 [文档目录](../Documents/ObsidianVault/wiki/side-projects/opportunity-discovery-mvp/)

- [架构设计](../Documents/ObsidianVault/wiki/side-projects/opportunity-discovery-mvp/2026-04-14-architecture-design.md)
- [开发进度](../Documents/ObsidianVault/wiki/side-projects/opportunity-discovery-mvp/progress.md)

## 快速开始

> **重要提示**: 所有后端命令都需要在虚拟环境中运行。确保命令行前缀显示 `(venv)`，如果没有请先激活虚拟环境：
>
> ```bash
> # Windows
> venv\Scripts\activate
>
> # Linux/Mac
> source venv/bin/activate
> ```

### 后端

```bash
cd backend
python -m venv venv
# 激活虚拟环境
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac
# 安装依赖
pip install -r requirements.txt
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

## 运行爬虫

> **前提条件**: 确保后端虚拟环境已激活（命令行前缀显示 `(venv)`）

### 方式1：通过 API（推荐）

先启动后端服务：

```bash
cd backend
python -m api.main
```

然后在另一个终端执行爬虫请求：

```powershell
# Windows PowerShell
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/crawler/run?platform=zhihu&limit=10&save=true&analyze=true" -ContentType "application/json" -body '{}'

# 或使用 curl
curl -X POST "http://localhost:8000/api/crawler/run?platform=zhihu&limit=10&save=true&analyze=true" -H "Content-Type: application/json" -d "{}"
```

**API参数说明：**
- `platform`: 平台名称 (`zhihu` 或 `bilibili`)
- `limit`: 抓取数量
- `save`: 是否保存到数据库
- `analyze`: 是否分析关键词

### 方式2：直接运行脚本

```bash
cd backend

# 抓取知乎热榜（默认10条）
python run_crawler.py

# 抓取更多数据
python run_crawler.py --limit 20

# 抓取B站数据
python run_crawler.py --platform bilibili

# 不保存到数据库，仅测试
python run_crawler.py --no-save

# 查看帮助
python run_crawler.py --help
```

## 平台爬虫说明

### B站爬虫

B站爬虫使用第三方热榜API，**不需要配置Cookie**，可以直接运行：

```bash
# 抓取B站热门数据
python run_crawler.py --platform bilibili

# 指定抓取数量
python run_crawler.py --platform bilibili --limit 20
```

**B站爬虫特点：**

| 特性 | 说明 |
|------|------|
| 数据源 | 第三方热榜API（无需登录） |
| API源 | 3个备用API，自动切换 |
| 获取内容 | 热门视频标题、热度、UP主、简介 |
| Cookie | **不需要** |

**平台对比：**

| 对比项 | 知乎 | B站 |
|--------|------|------|
| Cookie | 需要（推荐配置） | 不需要 |
| 数据内容 | 热榜问题 + 高赞回答 | 热门视频信息 |
| 热度指标 | 热度值/点赞数 | 播放量/热度值 |

### 知乎爬虫

知乎爬虫建议配置Cookie以获取更完整的数据：

```bash
# 复制Cookie示例文件
cp backend/data/zhihu_cookie.txt.example backend/data/zhihu_cookie.txt

# 编辑文件，填入你的知乎Cookie
# 然后运行
python run_crawler.py --platform zhihu
```

## 合规性说明

- 仅个人学习使用，不做商业化
- 控制抓取频率，避免对平台造成压力
- 数据仅用于分析发现需求，不公开原始数据
- 遵守 robots.txt

## License

MIT
