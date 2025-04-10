FROM python:3.11-slim

WORKDIR /app

# 复制依赖文件并安装
COPY ../../requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 复制服务代码
COPY ./services/article-service /app


# 暴露端口
EXPOSE 8002

# 启动服务
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"]