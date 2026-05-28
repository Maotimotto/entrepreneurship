# 🤖 评论AI — 短视频评论智能识别与自动转化

> AI 驱动的多平台评论监控 → 潜客识别 → 智能回复 → 私域引流一体化工具

## 它能做什么

```
用户评论: "这个怎么做的？想学！有教程吗"
     ↓ AI 分析
潜客评分: 0.85 / 意图: potential_lead / 紧急度: high
     ↓ 智能回复
自动生成: "感谢关注！想了解更多可以私信我~"
     ↓ 私域建档
自动归档为潜客，等待跟进
```

## 快速开始

```bash
# 1. 安装依赖
pip install fastapi uvicorn httpx pydantic pydantic-settings python-dotenv openai

# 2. 启动服务
cd comment-ai-tool
python -m src.main

# 3. 打开控制台
# 浏览器访问 http://localhost:8000
# 点击「运行演示」查看效果
```

## 控制台预览

暗色主题控制台，一键运行演示：
- 📊 实时统计：评论数、潜客数、回复数、转化率
- 🎯 意图识别：高/中/低意向自动分类
- 💬 智能回复：AI 自动生成个性化回复
- 🏷️ 关键词标签：自动提取触发词

## 技术架构

```
┌──────────────┐    ┌───────────────┐    ┌──────────────┐    ┌────────────┐
│  评论监控     │ →  │  AI 意图分析   │ →  │  智能回复     │ →  │  私域引流   │
│  (多平台)     │    │  (LLM+降级)   │    │  (个性化)     │    │  (潜客库)   │
└──────────────┘    └───────────────┘    └──────────────┘    └────────────┘
```

| 模块 | 文件 | 说明 |
|------|------|------|
| 数据模型 | `src/models/comment.py` | Comment, LeadScore, Lead |
| 意图分析 | `src/analyzers/intent_analyzer.py` | LLM分析 + 关键词降级 |
| 智能回复 | `src/repliers/reply_generator.py` | LLM生成 + 模板降级 |
| 评论监控 | `src/monitors/` | 各平台评论采集器 |
| API接口 | `src/api/routes.py` | FastAPI RESTful |
| 控制台 | `static/index.html` | 暗色主题 Web UI |

## API 文档

启动后访问 http://localhost:8000/docs 查看 Swagger 文档。

核心接口：
- `POST /api/v1/demo/run` — 演示模式，跑完整流程
- `POST /api/v1/analyze` — 分析单条评论
- `GET  /api/v1/leads` — 获取潜客列表
- `PUT  /api/v1/leads/{id}/status` — 更新潜客状态

## 配置

复制 `.env.example` 为 `.env`，配置 AI API Key 启用 LLM 分析：

```bash
cp .env.example .env
# 编辑 .env，填入 API Key
```

无 API Key 时自动使用关键词匹配（降级模式，开箱即用）。

## 测试

```bash
python test_smoke.py   # 模型基础测试
python test_api.py     # API 集成测试 (29项)
```

## 当前状态

**v0.1.2** — MVP 阶段

已完成：
- ✅ 评论数据模型
- ✅ AI 意图分析（LLM + 关键词降级）
- ✅ 智能回复生成（LLM + 模板降级）
- ✅ 抖音评论监控器（模拟数据）
- ✅ FastAPI RESTful API
- ✅ 暗色控制台 Web UI
- ✅ 潜客管理（建档/状态更新）
- ✅ 集成测试（29项全通过）

待开发：
- 🔲 抖音开放平台 API 对接
- 🔲 小红书评论监控
- 🔲 数据持久化（SQLite → PostgreSQL）
- 🔲 定时任务调度
- 🔲 私域引流链路（企微/微信）
- 🔲 数据统计与报表

## 许可

MIT
