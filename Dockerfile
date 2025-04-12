FROM python:3.9-slim

WORKDIR /app

# 复制应用代码
COPY . /app/

# 安装依赖
RUN pip install --no-cache-dir -r redbook_app/requirements.txt

# 创建必要的目录
RUN mkdir -p /app/redbook_app/frontend /app/redbook_app/results /app/redbook_app/templates /app/redbook_app/static

# 复制 index.html 到根目录
COPY index.html /app/

# 暴露端口
EXPOSE 8008 8080

# 启动应用
CMD ["python", "redbook_app/run.py"] 