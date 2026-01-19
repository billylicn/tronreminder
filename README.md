# 🤖 TronReminder - 澳门城市大学 TronClass 课程作业智能提醒机器人

[![Python Version](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub Stars](https://img.shields.io/github/stars/YourUsername/TronReminder?style=social)](https://github.com/billylicn/tronreminder)
[![GitHub Forks](https://img.shields.io/github/forks/YourUsername/TronReminder?style=social)](https://github.com/billylicn/tronreminder)

> 还在担心忘记提交 TronClass 上的课程作业？让 TronReminder 成为你的智能助手！🚀
> 这是一个基于 Python 构建的自动化机器人，能够定时抓取你的 TronClass 课程作业信息，并在截止日期临近时，通过邮件向你发送个性化提醒。支持 Docker 部署，让你轻松管理学习任务！

## ✨ 项目亮点

*   **智能识别**：自动登录 TronClass，获取所有课程的未提交作业。
*   **灵活配置**：可自定义提醒天数、关注学期等。
*   **邮件通知**：通过 QQ 邮箱等 SMTP 服务发送详细作业提醒。





### 1. 镜像构建

1. ```git clone```本项目

2. 在项目根目录（`Dockerfile` 所在的目录）下执行以下命令来构建 Docker 镜像：
```docker build -t tronreminder:latest ```

### 2. Docker Compose 部署

3.创建一个 `docker-compose.yml` 文件：

```yaml
version: '3.8'

services:
  tronreminder:
    image: tronreminder:latest # 使用我们刚刚构建的镜像
    container_name: tronreminder
    restart: on-failure # 容器异常退出时自动重启
    environment:
      - TRON_USERNAME=按实际填写
      - TRON_PASSWORD=按实际填写
      - EMAIL_FROM=按实际填写
      - EMAIL_PASSWORD=按实际填写
      - EMAIL_TO=按实际填写
      - REMINDER_DAYS_AHEAD=按实际填写
      - CURRENT_SEMESTERS=按实际填写
```

### 环境变量说明

| 变量名                | 描述                                                               | 示例                  |
| :-------------------- | :----------------------------------------------------------------- | :-------------------- |
| `TRON_USERNAME`       | 您的 TronClass 账号（学号+@cityu.edu.mo）                                | `U1234567@cityu.edu.mo`            |
| `TRON_PASSWORD`       | 您的 TronClass 密码                                                | `YourSecurePassword`  |
| `EMAIL_FROM`          | 发送提醒邮件的邮箱地址 (smtp协议｜**目前仅支持qq邮箱**)                                            | `your_email@qq.com`   |
| `EMAIL_PASSWORD`      | 发送邮件的授权码（非邮箱登录密码，请查阅邮箱服务提供商的文档）(smtp协议)    | `YourEmailAuthCode`   |
| `EMAIL_TO`            | 接收提醒邮件的邮箱地址（可以和 `EMAIL_FROM` 相同）                 | `your_email@qq.com`   |
| `REMINDER_DAYS_AHEAD` | 提前多少天开始提醒（包含截止当天，即 `0` 天代表当天截止）           | `7` (默认 `14`)       |
| `CURRENT_SEMESTERS`   | 关注的学期列表，多个学期用逗号分隔（目前为 2025-2）        | `2025-2` (默认 `2025-2`) |

**关于 `EMAIL_PASSWORD`（授权码）：**
*   **QQ 邮箱**：登录网页版 QQ 邮箱 -> 设置 -> 账户 -> 开启 SMTP 服务，获取授权码。
*   **其他邮箱**：待支持
