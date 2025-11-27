#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kaggle Competition Monitor
定期扫描 Kaggle 最新发布的比赛，根据关键词过滤并发送邮件通知
"""

import os
import re
import json
import time
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from kaggle.api.kaggle_api_extended import KaggleApi
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 配置参数
KAGGLE_USERNAME = os.getenv('KAGGLE_USERNAME')
KAGGLE_KEY = os.getenv('KAGGLE_KEY')
KEYWORDS = os.getenv('KEYWORDS', '').split(',')
CHECK_INTERVAL_HOURS = float(os.getenv('CHECK_INTERVAL_HOURS', 4))
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')
RECEIVER_EMAIL = os.getenv('RECEIVER_EMAIL')
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.qq.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 465))

# 已通知比赛记录文件
DATA_DIR = Path(__file__).parent / 'data'
DATA_DIR.mkdir(exist_ok=True)
NOTIFIED_FILE = DATA_DIR / 'notified_competitions.json'


def setup_kaggle_credentials():
    """设置 Kaggle API 认证"""
    if KAGGLE_USERNAME and KAGGLE_KEY:
        os.environ['KAGGLE_USERNAME'] = KAGGLE_USERNAME
        os.environ['KAGGLE_KEY'] = KAGGLE_KEY
        logger.info("已从环境变量加载 Kaggle 认证信息")
    else:
        kaggle_json = Path.home() / '.kaggle' / 'kaggle.json'
        if kaggle_json.exists():
            logger.info(f"使用 {kaggle_json} 中的认证信息")
        else:
            logger.error("未找到 Kaggle 认证信息，请配置环境变量或 kaggle.json")
            raise ValueError("Kaggle credentials not found")


def load_notified_competitions() -> set:
    """加载已通知的比赛 ID 列表"""
    if NOTIFIED_FILE.exists():
        try:
            with open(NOTIFIED_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(data.get('competitions', []))
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"读取已通知记录失败: {e}")
    return set()


def save_notified_competitions(notified: set):
    """保存已通知的比赛 ID 列表"""
    try:
        with open(NOTIFIED_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'competitions': list(notified),
                'updated_at': datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
    except IOError as e:
        logger.error(f"保存已通知记录失败: {e}")


def match_keywords(text: str, keywords: List[str]) -> List[str]:
    """
    检查文本是否包含关键词（不区分大小写）
    返回匹配到的关键词列表
    """
    if not text or not keywords:
        return []

    text_lower = text.lower()
    matched = []
    for keyword in keywords:
        keyword = keyword.strip()
        if not keyword:
            continue
        if keyword.lower() in text_lower:
            matched.append(keyword)
    return matched


def get_competitions(api: KaggleApi) -> List[Dict]:
    """获取 Kaggle 比赛列表"""
    try:
        competitions = api.competitions_list()
        result = []
        for comp in competitions:
            # comp.ref 可能是完整 URL 或仅比赛名称
            comp_ref = comp.ref
            if comp_ref.startswith('http'):
                url = comp_ref
                comp_id = comp_ref.split('/')[-1]
            else:
                url = f"https://www.kaggle.com/competitions/{comp_ref}"
                comp_id = comp_ref

            result.append({
                'id': comp_id,
                'title': comp.title,
                'description': comp.description or '',
                'url': url,
                'deadline': str(comp.deadline) if comp.deadline else 'N/A',
                'reward': comp.reward or 'N/A',
                'category': comp.category or 'N/A',
                'teams_count': comp.teamCount if hasattr(comp, 'teamCount') else 'N/A',
                'enabled_date': str(comp.enabledDate) if hasattr(comp, 'enabledDate') and comp.enabledDate else 'N/A'
            })
        logger.info(f"获取到 {len(result)} 个比赛")
        return result
    except Exception as e:
        logger.error(f"获取比赛列表失败: {e}")
        return []


def filter_competitions(competitions: List[Dict], keywords: List[str], notified: set) -> List[Dict]:
    """
    过滤比赛：
    1. 排除已通知的比赛
    2. 匹配关键词（标题或描述）
    """
    filtered = []
    for comp in competitions:
        # 跳过已通知的
        if comp['id'] in notified:
            continue

        # 检查标题和描述
        text = f"{comp['title']} {comp['description']}"
        matched_keywords = match_keywords(text, keywords)

        if matched_keywords:
            comp['matched_keywords'] = matched_keywords
            filtered.append(comp)
            logger.info(f"匹配到比赛: {comp['title']} (关键词: {', '.join(matched_keywords)})")

    return filtered


def format_email_content(competitions: List[Dict]) -> str:
    """格式化邮件内容（HTML 格式）"""
    html_header = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .competition {
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 20px;
                background-color: #f9f9f9;
            }
            .title {
                font-size: 18px;
                font-weight: bold;
                color: #20BEFF;
                margin-bottom: 10px;
            }
            .title a { color: #20BEFF; text-decoration: none; }
            .title a:hover { text-decoration: underline; }
            .meta { color: #666; font-size: 14px; margin-bottom: 8px; }
            .keywords {
                display: inline-block;
                background-color: #20BEFF;
                color: white;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 12px;
                margin-right: 5px;
            }
            .description {
                margin-top: 10px;
                padding: 10px;
                background-color: #fff;
                border-radius: 4px;
            }
        </style>
    </head>
    <body>
    """

    html = html_header + f"""
        <h2>Kaggle 新比赛通知</h2>
        <p>检测到 <strong>{len(competitions)}</strong> 个与你关注领域相关的新比赛：</p>
    """

    for comp in competitions:
        keywords_html = ''.join([f'<span class="keywords">{kw}</span>' for kw in comp.get('matched_keywords', [])])

        html += f"""
        <div class="competition">
            <div class="title"><a href="{comp['url']}" target="_blank">{comp['title']}</a></div>
            <div class="meta">
                💰 奖励: {comp['reward']} |
                📁 类别: {comp['category']} |
                ⏰ 截止: {comp['deadline']}
            </div>
            <div class="meta">🔑 匹配关键词: {keywords_html}</div>
            <div class="description">{comp['description'][:500]}{'...' if len(comp['description']) > 500 else ''}</div>
        </div>
        """

    html += f"""
        <hr>
        <p style="color: #999; font-size: 12px;">
            此邮件由 Kaggle Competition Monitor 自动发送<br>
            发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </p>
    </body>
    </html>
    """

    return html


def send_email(competitions: List[Dict]) -> bool:
    """发送邮件通知"""
    if not all([SENDER_EMAIL, SENDER_PASSWORD, RECEIVER_EMAIL]):
        logger.error("邮件配置不完整，请检查 SENDER_EMAIL, SENDER_PASSWORD, RECEIVER_EMAIL")
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'Kaggle 新比赛通知 ({len(competitions)} 个匹配)'
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL

        html_content = format_email_content(competitions)
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))

        logger.info(f"正在发送邮件: {SMTP_SERVER}:{SMTP_PORT}")

        # 根据端口选择连接方式
        if SMTP_PORT == 465:
            # SSL 连接
            import ssl
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        else:
            # TLS 连接 (端口 587 或其他)
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
            server.quit()

        logger.info(f"邮件发送成功，通知 {len(competitions)} 个比赛到 {RECEIVER_EMAIL}")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP 认证失败，请检查邮箱账号和授权码")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"邮件发送失败: {e}")
        return False
    except Exception as e:
        logger.error(f"发送邮件时发生错误: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def check_and_notify():
    """执行一次检查并通知"""
    logger.info("=" * 50)
    logger.info("开始检查 Kaggle 比赛...")

    # 设置 Kaggle 认证
    setup_kaggle_credentials()

    # 初始化 API
    api = KaggleApi()
    api.authenticate()

    # 加载已通知记录
    notified = load_notified_competitions()
    logger.info(f"已记录 {len(notified)} 个已通知的比赛")

    # 获取比赛列表
    competitions = get_competitions(api)
    if not competitions:
        logger.warning("未获取到比赛列表")
        return

    # 清理关键词列表
    keywords = [kw.strip() for kw in KEYWORDS if kw.strip()]
    if not keywords:
        logger.warning("未配置关键词，将不进行过滤")
        return

    logger.info(f"关键词列表: {', '.join(keywords)}")

    # 过滤比赛
    matched = filter_competitions(competitions, keywords, notified)

    if not matched:
        logger.info("没有发现新的匹配比赛")
        return

    logger.info(f"发现 {len(matched)} 个新的匹配比赛")

    # 发送邮件
    if send_email(matched):
        # 更新已通知记录
        for comp in matched:
            notified.add(comp['id'])
        save_notified_competitions(notified)
        logger.info("已更新通知记录")
    else:
        logger.error("邮件发送失败，本次匹配的比赛将在下次检查时重试")


def main():
    """主函数 - 循环运行"""
    logger.info("🏆 Kaggle Competition Monitor 启动")
    logger.info(f"检查间隔: {CHECK_INTERVAL_HOURS} 小时")
    logger.info(f"监控关键词: {', '.join([kw.strip() for kw in KEYWORDS if kw.strip()])}")

    while True:
        try:
            check_and_notify()
        except Exception as e:
            logger.error(f"检查过程中发生错误: {e}")

        # 等待下一次检查
        wait_seconds = CHECK_INTERVAL_HOURS * 3600
        logger.info(f"下次检查时间: {datetime.now().timestamp() + wait_seconds}")
        logger.info(f"等待 {CHECK_INTERVAL_HOURS} 小时后进行下一次检查...")
        time.sleep(wait_seconds)


if __name__ == '__main__':
    main()
