# 使用 Python 3.9 slim 镜像作为基础
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY monitor.py .

# 创建非 root 用户运行应用
RUN useradd -m -u 1000 monitor && \
    chown -R monitor:monitor /app

USER monitor

# 运行监控脚本
CMD ["python", "monitor.py"]
