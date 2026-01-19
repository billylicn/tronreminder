FROM python:3.10-slim

# 安装 cron
RUN apt-get update && \
    apt-get install -y --no-install-recommends cron && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# 安装 Python 依赖
RUN pip install --no-cache-dir requests beautifulsoup4 lxml

# 设置时区和禁用 Python 缓冲
ENV TZ=Asia/Shanghai \
    PYTHONUNBUFFERED=1
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 赋予脚本执行权限
RUN chmod +x ./entrypoint.sh

# 默认每天早上 8 点运行（可通过环境变量覆盖）
ENV CRON_SCHEDULE="0 8 * * *"

CMD ["cron", "-f", "./entrypoint.sh"]