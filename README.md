# 🤖 TronReminder - TronClass 课程作业智能提醒机器人

[![Python Version](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub Stars](https://img.shields.io/github/stars/YourUsername/TronReminder?style=social)](https://github.com/billylicn/tronreminder)
[![GitHub Forks](https://img.shields.io/github/forks/YourUsername/TronReminder?style=social)](https://github.com/billylicn/tronreminder)

> 还在担心忘记提交 TronClass 上的课程作业？让 TronReminder 成为你的智能助手！🚀
> 这是一个基于 Python 构建的自动化机器人，能够定时抓取你的 TronClass 课程作业信息，并在截止日期临近时，通过邮件向你发送个性化提醒。支持 Docker 部署，让你轻松管理学习任务！

## ✨ 项目亮点

*   **智能识别**：自动登录 TronClass，获取所有课程的未提交作业。
*   **多时区支持**：将截止时间统一转换为北京时间，确保提醒准确无误。
*   **灵活配置**：可自定义提醒天数、关注学期等。
*   **邮件通知**：通过 QQ 邮箱等 SMTP 服务发送详细作业提醒。
*   **Docker 部署**：提供 Dockerfile 和 Docker Compose 配置，一键部署，开箱即用。
*   **轻量高效**：基于 `requests` 和 `BeautifulSoup`，避免完整的浏览器自动化，资源占用低。

## 🛠️ 快速部署

TronReminder 推荐使用 Docker 进行部署，方便快捷。

### 1. 环境变量配置

在部署前，您需要准备以下环境变量。推荐创建一个 `.env` 文件，或直接在 Docker Compose 文件中设置。

| 变量名                | 描述                                                               | 示例                  |
| :-------------------- | :----------------------------------------------------------------- | :-------------------- |
| `TRON_USERNAME`       | 您的 TronClass 账号（通常是学号）                                | `U1234567`            |
| `TRON_PASSWORD`       | 您的 TronClass 密码                                                | `YourSecurePassword`  |
| `EMAIL_FROM`          | 发送提醒邮件的邮箱地址                                             | `your_email@qq.com`   |
| `EMAIL_PASSWORD`      | 发送邮件的授权码（非邮箱登录密码，请查阅邮箱服务提供商的文档）   | `YourEmailAuthCode`   |
| `EMAIL_TO`            | 接收提醒邮件的邮箱地址（可以和 `EMAIL_FROM` 相同）                 | `your_email@qq.com`   |
| `REMINDER_DAYS_AHEAD` | 提前多少天开始提醒（包含截止当天，即 `0` 天代表当天截止）           | `7` (默认 `14`)       |
| `CURRENT_SEMESTERS`   | 关注的学期列表，多个学期用逗号分隔（例如：`2025-2,2026-1`）        | `2025-2` (默认 `2025-2`) |

**关于 `EMAIL_PASSWORD`（授权码）：**
*   **QQ 邮箱**：登录网页版 QQ 邮箱 -> 设置 -> 账户 -> 开启 SMTP 服务，获取授权码。
*   **其他邮箱**：待支持


### 1. 镜像构建



### 2. Docker Compose 部署

请创建一个 `docker-compose.yml` 文件：

```yaml
version: '3.8'

services:
  tronreminder:
    image: python:3.9-slim-buster # 或使用您的自定义镜像，如果已构建
    container_name: tronreminder
    restart: on-failure
    working_dir: /app
    volumes:
      - .:/app # 将当前项目目录挂载到容器的 /app
    environment:
      - TRON_USERNAME=${TRON_USERNAME}
      - TRON_PASSWORD=${TRON_PASSWORD}
      - EMAIL_FROM=${EMAIL_FROM}
      - EMAIL_PASSWORD=${EMAIL_PASSWORD}
      - EMAIL_TO=${EMAIL_TO}
      - REMINDER_DAYS_AHEAD=${REMINDER_DAYS_AHEAD:-14} # 默认14天
      - CURRENT_SEMESTERS=${CURRENT_SEMESTERS:-2025-2} # 默认2025-2
    command: ["python", "main.py"] # 假设您的主程序文件名为 main.py
    # 如果您需要定时运行，可以使用 cron 或者 Docker Compose 的 healthcheck
    # 例如，使用外部 cron 调度：
    # docker exec tronreminder python main.py
