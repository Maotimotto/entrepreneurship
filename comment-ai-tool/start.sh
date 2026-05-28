#!/usr/bin/env bash
# 评论AI 快速启动脚本
set -e

cd "$(dirname "$0")"

echo "🤖 评论AI — 启动中..."
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 需要 Python 3.10+"
    exit 1
fi

# 检查依赖
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "📦 安装依赖..."
    pip install -r requirements.txt
fi

# 检查 .env
if [ ! -f .env ]; then
    echo "⚙️  未检测到 .env，使用降级模式（关键词匹配）"
    echo "   配置 .env 可启用 AI 分析，参考 .env.example"
    echo ""
fi

echo "🚀 启动服务: http://localhost:8000"
echo "📊 控制台:   http://localhost:8000"
echo "📖 API文档:  http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止"
echo ""

python3 -m src.main
