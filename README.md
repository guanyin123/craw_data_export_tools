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

### 后端

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

## 合规性说明

- 仅个人学习使用，不做商业化
- 控制抓取频率，避免对平台造成压力
- 数据仅用于分析发现需求，不公开原始数据
- 遵守 robots.txt

## License

MIT
