# 🤖 评论AI — 短视频评论智能识别与自动转化

> AI 驱动的多平台评论监控 → 意图识别 → 情感分析 → 智能回复 → 私域引流一体化工具

## 核心能力

| 能力 | 说明 |
|------|------|
| 🧠 意图识别 | LLM 分析 + 增强关键词引擎（同义词、否定词检测） |
| ❤️ 情感分析 | 正面/负面/中性/混合，支持置信度 |
| 💬 智能回复 | LLM 生成 + 模板降级，按潜客分层策略 |
| 📊 数据持久化 | SQLite 三表存储，数据不丢 |
| ⚡ 性能优化 | LRU 缓存、批量处理、命中率统计 |
| 🎨 控制台 | 暗色主题 Web UI，一键演示 |

## 快速开始

```bash
# 安装依赖
pip install fastapi uvicorn httpx pydantic pydantic-settings python-dotenv openai

# 启动
cd comment-ai-tool
python -m src.main

# 访问控制台
open http://localhost:8000
```

或使用启动脚本：
```bash
chmod +x start.sh
./start.sh
```

## 技术架构

```
评论采集 → 意图分析 → 情感分析 → 潜客评分 → 智能回复 → 私域建档
  (多平台)   (LLM+关键词)  (词典)    (0-1分)    (LLM+模板)  (SQLite)
```

## API 文档

启动后访问 http://localhost:8000/docs

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/demo/run` | POST | 演示模式，跑完整流程 |
| `/api/v1/analyze` | POST | 分析单条评论 |
| `/api/v1/leads` | GET | 获取潜客列表 |
| `/api/v1/leads/export` | GET | 导出CSV |
| `/api/v1/stats` | GET | 统计数据 |

## 测试

```bash
# 运行全部测试 (95项)
python test_api.py        # 33项 API 集成测试
python test_edge.py       # 15项 边界测试
python test_keyword.py    # 30项 关键词引擎测试
python test_sentiment.py  # 17项 情感分析测试
```

## 当前状态

**v0.2.4** — 95 项测试全通过

✅ 已完成:
- 评论数据模型 (Comment, LeadScore, Lead)
- 增强关键词引擎 (同义词组、否定词检测、情感分析)
- AI 意图分析 (LLM + 关键词降级)
- 智能回复生成 (LLM + 模板降级)
- 抖音评论监控器 (模拟数据)
- SQLite 持久化 (leads, scores, analysis_log)
- LRU 缓存 (意图分析、情感分析)
- FastAPI RESTful API
- 暗色控制台 Web UI
- 潜客管理 (建档/状态更新/CSV导出)
- 结构化日志
- 95 项自动化测试

🔲 待开发:
- 抖音开放平台 API 对接
- 小红书评论监控
- 定时任务调度
- 私域引流链路

## 项目结构

```
comment-ai-tool/
├── config/settings.py          # 配置管理
├── src/
│   ├── analyzers/
│   │   ├── intent_analyzer.py  # 意图分析 (LLM+关键词)
│   │   ├── keyword_engine.py   # 增强关键词引擎
│   │   └── sentiment.py        # 情感分析
│   ├── api/routes.py           # FastAPI 路由
│   ├── core/
│   │   ├── cache.py            # LRU 缓存
│   │   ├── database.py         # SQLite 持久化
│   │   └── logger.py           # 日志配置
│   ├── models/comment.py       # 数据模型
│   ├── monitors/               # 平台监控器
│   ├── repliers/reply_generator.py  # 回复生成
│   └── main.py                 # 入口
├── static/index.html           # 控制台 UI
├── test_*.py                   # 测试文件
├── Makefile                    # 便捷命令
├── pyproject.toml              # 打包配置
└── README.md
```

## 许可

MIT
