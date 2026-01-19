#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import json
import re
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
import smtplib
import requests
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
from requests.exceptions import Timeout

import os

# ========================
# 🔑 从环境变量读取配置
# ========================
TRON_USERNAME = os.getenv("TRON_USERNAME")
TRON_PASSWORD = os.getenv("TRON_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_TO = os.getenv("EMAIL_TO")

REMINDER_DAYS_AHEAD = int(os.getenv("REMINDER_DAYS_AHEAD", "14"))
CURRENT_SEMESTERS = set(os.getenv("CURRENT_SEMESTERS", "2025-2").split(","))

# 校验必填环境变量
required_vars = {
    "TRON_USERNAME": TRON_USERNAME,
    "TRON_PASSWORD": TRON_PASSWORD,
    "EMAIL_FROM": EMAIL_FROM,
    "EMAIL_PASSWORD": EMAIL_PASSWORD,
    "EMAIL_TO": EMAIL_TO,
}
missing = [name for name, value in required_vars.items() if not value]
if missing:
    raise EnvironmentError(f"❌ 缺少必要环境变量: {', '.join(missing)}")

# 定义北京时间 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))
    
# ========================
# 以下为程序逻辑
# ========================

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Course:
    def __init__(self):
        self.course_id: str = ""
        self.name: str = ""
        self.course_code: str = ""
        self.semester: str = ""
        self.department: str = ""
        self.grade: str = ""
        self.klass: str = ""
        self.start_date: str = ""
        self.end_date: str = ""
        self.teaching_class: str = ""
        self.compulsory: str = ""
        self.credit: str = ""
        self.cover_url: str = ""
        self.course_url: str = ""
        self.instructors: List[str] = []

class Homework:
    def __init__(self):
        self.homework_id: int = 0
        self.title: str = ""
        self.type: str = ""
        self.module_id: int = 0
        self.teaching_unit_id: int = 0
        self.syllabus_id: int = 0
        self.created_at: str = ""
        self.updated_at: str = ""
        self.deadline: str = ""
        self.start_time: Optional[str] = None
        self.end_time: str = ""
        self.published: bool = False
        self.is_closed: bool = False
        self.submitted: bool = False
        self.user_submit_count: int = 0
        self.can_make_up_homework: bool = False
        self.need_make_up: bool = False
        self.score_percentage: str = "0.0"
        self.score_published: bool = False
        self.description_html: str = ""
        self.completion_criterion: str = ""
        self.uploads: List[Dict[str, Any]] = []
        self.course_id: str = ""
        self.course_name: str = ""

def get_remaining_days(deadline_str: str) -> Optional[int]:
    """
    假设截止时间字符串（如 "2026-01-21T07:30:00Z"）中的时间值本身就是北京时间。
    函数将字符串解析为北京时间后，与当前北京时间比较，返回剩余完整日历天数。
    """
    if not deadline_str:
        logger.debug("截止时间为空")
        return None
    try:
        # Step 1: 解析原始字符串
        # 如果字符串有 'Z' 且用户确认其数值是北京时间，那么 'Z' 是多余的，直接移除。
        # 如果原始字符串可能包含类似 '+08:00' 这样的时区信息，fromisoformat 会自动处理。
        dt_str_clean = deadline_str.replace("Z", "")
        deadline_dt_naive_or_aware = datetime.fromisoformat(dt_str_clean)

        # Step 2: 确保截止时间是北京时区
        # 如果解析后没有时区信息 (naive datetime)，则直接赋予北京时区。
        # 如果解析后已有例如 '+08:00' 的时区信息，则将其转换为我们定义的 BEIJING_TZ 对象，
        # 确保时区对象一致性。
        if deadline_dt_naive_or_aware.tzinfo is None:
            deadline_beijing = deadline_dt_naive_or_aware.replace(tzinfo=BEIJING_TZ)
        else:
            # 如果字符串本身就带有 +08:00 或其他时区信息，
            # 确保最终使用我们定义的 BEIJING_TZ 时区对象进行计算
            deadline_beijing = deadline_dt_naive_or_aware.astimezone(BEIJING_TZ)
        
        # Step 3: 获取当前北京时间（带时区）
        now_beijing = datetime.now(BEIJING_TZ)
        
        # Step 4: 提取日期部分进行比较
        deadline_date = deadline_beijing.date()
        now_date = now_beijing.date()
        
        # Step 5: 计算日期的差值
        time_difference = deadline_date - now_date
        remaining_days = time_difference.days

        logger.debug(
            f"原始截止时间: {deadline_str} | "
            f"清理后解析字符串: {dt_str_clean} | "
            f"解析后的datetime (可能带时区): {deadline_dt_naive_or_aware} | "
            f"最终北京时间: {deadline_beijing.strftime('%Y-%m-%d %H:%M:%S%z')} | " # %z 显示时区偏移
            f"当前北京时间: {now_beijing.strftime('%Y-%m-%d %H:%M:%S%z')} | "
            f"截止日期: {deadline_date} | "
            f"当前日期: {now_date} | "
            f"剩余天数: {remaining_days}"
        )
        return remaining_days
    except Exception as e:
        logger.warning(f"解析截止时间失败: {deadline_str} | 错误: {e}")
        return None

    """
    将截止时间视为 UTC 时间（因 TronClass 返回的是 Z 结尾），
    转换为北京时间后，与当前北京时间比较，返回剩余完整天数。
    """
    if not deadline_str:
        logger.debug("截止时间为空")
        return None

    try:
        # Step 1: 解析原始字符串（如 "2026-01-21T07:30:00Z"）
        dt_str = deadline_str.replace("Z", "+00:00")
        deadline_utc = datetime.fromisoformat(dt_str)

        # 如果解析后无时区，默认为 UTC
        if deadline_utc.tzinfo is None:
            deadline_utc = deadline_utc.replace(tzinfo=timezone.utc)

        # Step 2: 转换为北京时间
        deadline_beijing = deadline_utc.astimezone(BEIJING_TZ)

        # Step 3: 获取当前北京时间（带时区）
        now_beijing = datetime.now(BEIJING_TZ)

        # Step 4: 计算差值（秒）
        diff_seconds = (deadline_beijing - now_beijing).total_seconds()
        remaining_days = int(diff_seconds // 86400)  # 向下取整

        logger.debug(
            f"原始截止时间: {deadline_str} | "
            f"北京时间: {deadline_beijing.strftime('%Y-%m-%d %H:%M:%S')} | "
            f"当前北京时间: {now_beijing.strftime('%Y-%m-%d %H:%M:%S')} | "
            f"剩余天数: {remaining_days}"
        )

        return remaining_days

    except Exception as e:
        logger.warning(f"解析截止时间失败: {deadline_str} | 错误: {e}")
        return None

class SessionManager:
    def __init__(self):
        self.session = requests.Session()
        self.is_logged_in = False
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

    def login(self, username: str, password: str) -> bool:
        tron_login_url = "https://tronclass.cityu.edu.mo/login"
        try:
            logger.info("正在获取 CAS 登录入口...")
            resp = self.session.get(tron_login_url, timeout=10)
            cas_login_url = resp.url
            if "login.cityu.edu.mo" not in cas_login_url:
                logger.error("未检测到 CAS 跳转。")
                return False

            soup = BeautifulSoup(resp.text, "html.parser")
            payload = {}
            for inp in soup.find_all("input", {"type": "hidden"}):
                name = inp.get("name")
                value = inp.get("value", "")
                if name:
                    payload[name] = value

            payload['username'] = username
            payload['password'] = password

            cas_headers = {
                'Referer': cas_login_url,
                'Origin': 'https://login.cityu.edu.mo',
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            login_resp = self.session.post(cas_login_url, data=payload, headers=cas_headers, timeout=10, allow_redirects=True)

            if "login.cityu.edu.mo" in login_resp.url and "login" in login_resp.url:
                logger.error("登录失败：停留在 CAS 登录页。")
                return False

            verify_resp = self.session.get("https://tronclass.cityu.edu.mo/user/settings#/", timeout=10)
            if verify_resp.status_code == 200 and "login" not in verify_resp.url:
                logger.info("✅ 登录成功！")
                self.is_logged_in = True
                return True
            else:
                logger.error(f"❌ 会话验证失败。最终 URL: {verify_resp.url}")
                return False

        except Timeout:
            logger.error("请求超时")
            return False
        except Exception as e:
            logger.error(f"登录异常: {e}", exc_info=True)
            return False

    def get_session(self):
        return self.session

class CourseAPI:
    def __init__(self, session: requests.Session):
        self.session = session
        self.base_url = "https://tronclass.cityu.edu.mo"
        self.CURRENT_SEMESTERS = CURRENT_SEMESTERS  # 使用顶部定义的学期白名单

    def get_courses(self, page_index: int = 1) -> List[Course]:
        courses = self._get_courses_from_api(page_index)
        if courses:
            return courses
        return self._get_courses_from_html(page_index)

    def _get_courses_from_api(self, page_index: int) -> List[Course]:
        api_endpoints = [
            f"{self.base_url}/api/my-courses",
            f"{self.base_url}/api/users/courses",
            f"{self.base_url}/api/user/courses",
            f"{self.base_url}/api/course/list",
            f"{self.base_url}/api/courses",
        ]
        params = {"pageIndex": page_index, "pageSize": 20}
        headers = {
            'Referer': 'https://tronclass.cityu.edu.mo/user/courses',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'X-Requested-With': 'XMLHttpRequest'
        }
        for api_url in api_endpoints:
            try:
                resp = self.session.get(api_url, params=params, headers=headers, timeout=10)
                if resp.status_code == 200 and 'application/json' in resp.headers.get('Content-Type', '').lower():
                    data = resp.json()
                    courses = self._try_parse_json_courses(data)
                    if courses:
                        return courses
            except Exception:
                continue
        return []

    def _try_parse_json_courses(self, data) -> List[Course]:
        possible_paths = [
            ['data', 'courses'], ['data', 'list'], ['result', 'courses'],
            ['result', 'list'], ['courses'], ['list'], ['data']
        ]
        for path in possible_paths:
            try:
                current = data
                for key in path:
                    if isinstance(current, dict) and key in current:
                        current = current[key]
                    else:
                        break
                else:
                    if isinstance(current, list) and current and isinstance(current[0], dict) and ('name' in current[0] or 'display_name' in current[0]):
                        return self._parse_courses_json_list(current)
            except Exception:
                continue
        return []

    def _parse_courses_json_list(self, courses_list) -> List[Course]:
        courses = []
        for item in courses_list:
            semester = item.get('semester', '')
            if isinstance(semester, dict):
                semester_code = semester.get('code') or semester.get('name') or semester.get('real_name', '')
            else:
                semester_code = str(semester)

            if semester_code not in self.CURRENT_SEMESTERS:
                continue

            course = Course()
            course.course_id = str(item.get('id', ''))
            course.name = item.get('display_name') or item.get('name', '')
            course.course_code = item.get('course_code', '')
            course.semester = semester_code
            course.department = item.get('department', {}).get('name', '') if isinstance(item.get('department'), dict) else ''
            course.grade = item.get('grade', {}).get('name', '') if isinstance(item.get('grade'), dict) else ''
            course.klass = item.get('klass', {}).get('name', '') if isinstance(item.get('klass'), dict) else ''
            course.start_date = item.get('start_date', '')
            course.end_date = item.get('end_date', '')
            course.teaching_class = item.get('course_attributes', {}).get('teaching_class_name', '') if isinstance(item.get('course_attributes'), dict) else ''
            course.compulsory = "必修" if item.get('compulsory') is True else ("選修" if item.get('compulsory') is False else "")
            course.credit = str(item.get('credit', ''))
            course.cover_url = item.get('cover_url') or item.get('cover', '')
            course.course_url = item.get('course_url') or f"/course/{course.course_id}/content"
            instructors = item.get('instructors', [])
            if isinstance(instructors, list):
                course.instructors = [inst.get('name') or inst.get('display_name', '') for inst in instructors if isinstance(inst, dict)]
            courses.append(course)
        return courses

    def _get_courses_from_html(self, page_index: int) -> List[Course]:
        # 简化版 HTML 解析（保留核心逻辑）
        url = f"{self.base_url}/user/courses"
        try:
            resp = self.session.get(url, params={"pageIndex": page_index}, timeout=10)
            if resp.status_code != 200:
                return []
            html_text = resp.text
            if 'ng-repeat="course in' in html_text:
                # 尝试从 script 中提取 JSON
                for pattern in [r'var\s+courses\s*=\s*(\[.*?\]);', r'window\.courses\s*=\s*(\[.*?\]);']:
                    matches = re.findall(pattern, html_text, re.DOTALL)
                    for match in matches:
                        try:
                            data = json.loads(match)
                            if isinstance(data, list):
                                return self._parse_courses_json_list(data)
                        except:
                            continue
            return []
        except Exception:
            return []

class HomeworkAPI:
    def __init__(self, session: requests.Session):
        self.session = session
        self.base_url = "https://tronclass.cityu.edu.mo"

    def get_pending_homeworks_for_course(self, course_id: str) -> List[Homework]:
        url = f"{self.base_url}/api/courses/{course_id}/homework-activities"
        headers = {
            'Referer': f'https://tronclass.cityu.edu.mo/course/{course_id}/content',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'X-Requested-With': 'XMLHttpRequest'
        }
        try:
            resp = self.session.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return self._parse_homeworks(data, course_id)
        except Exception as e:
            logger.error(f"获取作业失败 ({course_id}): {e}")
        return []

    def _parse_homeworks(self, json_data: dict, course_id: str) -> List[Homework]:
        pending = []
        for hw in json_data.get("homework_activities", []):
            if not hw.get("published") or hw.get("submitted"):
                continue
            h = Homework()
            h.homework_id = hw.get("id", 0)
            h.title = hw.get("title", "")
            h.deadline = hw.get("deadline", "")
            h.can_make_up_homework = hw.get("can_make_up_homework", False)
            h.score_percentage = str(hw.get("score_percentage", "0.0"))
            h.description_html = hw.get("data", {}).get("description", "")
            h.course_id = course_id
            pending.append(h)
        return pending

def send_email(subject: str, body: str) -> bool:
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = EMAIL_FROM
        msg["To"] = EMAIL_TO

        server = smtplib.SMTP_SSL("smtp.qq.com", 465)
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        server.quit()
        logger.info("✅ 邮件发送成功！")
        return True
    except Exception as e:
        logger.error(f"❌ 邮件发送失败: {e}")
        return False

def run_and_notify():
    # 登录
    sm = SessionManager()
    if not sm.login(TRON_USERNAME, TRON_PASSWORD):
        logger.error("登录失败")
        return

    # 获取课程
    course_api = CourseAPI(sm.get_session())
    courses = course_api.get_courses()
    if not courses:
        logger.info("未获取到课程")
        return

    # 构建课程 ID 到名称的映射
    course_map = {c.course_id: c.name for c in courses}

    # 获取所有未提交作业
    homework_api = HomeworkAPI(sm.get_session())
    all_homeworks = []
    for course in courses:
        hws = homework_api.get_pending_homeworks_for_course(course.course_id)
        for hw in hws:
            hw.course_name = course_map.get(hw.course_id, "未知课程")
            hw.remaining_days = get_remaining_days(hw.deadline)
        all_homeworks.extend(hws)

    # 筛选即将截止的作业
    urgent = [
        hw for hw in all_homeworks
        if hw.remaining_days is not None and 0 <= hw.remaining_days <= REMINDER_DAYS_AHEAD
    ]

    if not urgent:
        logger.info("🎉 无即将截止的作业")
        return

    urgent.sort(key=lambda x: x.remaining_days)
    min_days = min(hw.remaining_days for hw in urgent)

    subject = f"⚠️ 作业提醒：最近一项作业将在 {min_days} 天内截止！"
    body = f"🔔 你有 {len(urgent)} 项作业将在未来 {REMINDER_DAYS_AHEAD} 天内截止：\n\n"

    for hw in urgent:
        clean_desc = BeautifulSoup(hw.description_html, "html.parser").get_text()
        clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()[:150]
        body += f"【课程】{hw.course_name}\n"
        body += f"【作业】{hw.title}\n"
        body += f"【截止】{hw.deadline}（剩余 {hw.remaining_days} 天）\n"
        body += f"【补交】{'允许' if hw.can_make_up_homework else '不允许'}\n"
        body += f"【占比】{hw.score_percentage}%\n"
        body += f"【摘要】{clean_desc}...\n"
        body += "-" * 50 + "\n\n"

    body += "请及时登录 TronClass 提交！\n\n—— 你的作业提醒机器人"

    send_email(subject, body)

if __name__ == "__main__":
    run_and_notify()
