FROM python:3.12-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 创建数据目录
RUN mkdir -p /data

# 环境变量
ENV COMMENT_AI_DB=/data/comment_ai.db
ENV SERVER_HOST=0.0.0.0
ENV SERVER_PORT=8000

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import httpx; r=httpx.get('http://localhost:8000/api/v1/health'); assert r.json()['status']=='ok'"

# 启动
CMD ["python", "-m", "src.main"]
