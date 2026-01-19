#!/bin/bash
set -e

echo "🚀 首次运行：立即检查作业..."
/usr/local/bin/python3 /app/main.py

crontab -r 2>/dev/null || true

# 构建包含环境变量的 crontab 内容
{
  echo "TRON_USERNAME=$TRON_USERNAME"
  echo "TRON_PASSWORD=$TRON_PASSWORD"
  echo "EMAIL_FROM=$EMAIL_FROM"
  echo "EMAIL_PASSWORD=$EMAIL_PASSWORD"
  echo "EMAIL_TO=$EMAIL_TO"
  echo "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
  echo ""
  echo "$CRON_SCHEDULE /usr/local/bin/python3 /app/main.py >> /proc/1/fd/1 2>> /proc/1/fd/2"
} | crontab -

echo "📅 已设置定时任务: $CRON_SCHEDULE"
crontab -l

exec cron -f