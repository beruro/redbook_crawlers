FROM python:3.9-slim

WORKDIR /app

# 复制应用代码
COPY redbook_app /app/
COPY requirements.txt /app/

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 创建必要的目录
RUN mkdir -p /app/frontend /app/results /app/templates /app/static

# 暴露端口
EXPOSE 8008 8080

# 启动应用
CMD ["python", "run.py"] 