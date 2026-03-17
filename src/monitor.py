# -*- coding: utf-8 -*-
"""
香港IPO自动监控主程序
执行三大任务：
  1. 已有项目进展追踪
  2. 市场新动态搜索
  3. 新递表项目分析
结果创建 GitHub Issue 并存档到 reports/ 目录
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import pytz
import requests

# 确保 src 目录在 Python 路径中
sys.path.insert(0, str(Path(__file__).parent))

from ipo_watchlist import (
    WATCHLIST,
    get_listed_companies,
    get_pre_ipo_companies,
)
from perplexity_client import PerplexityClient
from report_generator import (
    format_issue_body,
    generate_daily_report,
    save_data_snapshot,
    save_report,
)

# ─── 日志配置 ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

HK_TZ = pytz.timezone("Asia/Hong_Kong")

# ─── 路径配置 ──────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).parent.parent
REPORTS_DIR = REPO_ROOT / "reports"
DATA_DIR = REPO_ROOT / "data"

# ─── GitHub API ────────────────────────────────────────────────────────────────
GITHUB_API_URL = "https://api.github.com"
GITHUB_REPO = os.environ.get("GITHUB_REPOSITORY", "quantumfisher001-netizen/ipo-tracker-hk")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
IPO_LABEL = "ipo-daily-report"
AUTO_LABEL = "auto-generated"


# ─── 任务一：已有项目进展追踪 ─────────────────────────────────────────────────

def track_company_progress(client: PerplexityClient) -> list:
    """
    任务一：针对每个监控项目搜索最新进展
    为减少 API 调用，将多个公司合并查询
    """
    logger.info("=== 任务一：追踪已有项目进展 ===")

    pre_ipo = get_pre_ipo_companies()
    results = []

    # 将公司分批，每批最多 5 家，合并查询以控制成本
    batch_size = 5
    for i in range(0, len(pre_ipo), batch_size):
        batch = pre_ipo[i : i + batch_size]
        company_names = "、".join(c["name"] for c in batch)

        query = (
            f"请搜索以下香港IPO项目的最新进展（2025-2026年）：{company_names}。\n"
            "对于每个公司，请提供：\n"
            "1. 最新IPO状态（聆讯结果/招股日期/定价/上市日期）\n"
            "2. 近期重要公告\n"
            "3. 是否有重大变化\n"
            "请简明扼要，每家公司不超过100字。"
        )

        logger.info("查询批次 %d/%d：%s", i // batch_size + 1, (len(pre_ipo) + batch_size - 1) // batch_size, company_names)
        result = client.search(query, max_tokens=1500)
        time.sleep(2)  # 控制请求频率

        # 为批次中的每家公司创建结果记录
        for company in batch:
            # 检查内容中是否提到了该公司（作为"有更新"的简单判断）
            has_update = False
            if result.get("success") and result.get("content"):
                content_lower = result["content"]
                has_update = company["name"] in content_lower and any(
                    kw in content_lower
                    for kw in ["聆讯", "招股", "上市", "通过", "失效", "撤回", "定价"]
                )

            results.append(
                {
                    "company": company["name"],
                    "sector": company["sector"],
                    "status": company["status"],
                    "category_name": _get_category_name(company["name"]),
                    "has_update": has_update,
                    "success": result.get("success", False),
                    "content": result.get("content", ""),
                    "error": result.get("error"),
                    "citations": result.get("citations", []),
                }
            )

    logger.info("任务一完成，共追踪 %d 家公司", len(results))
    return results


def _get_category_name(company_name: str) -> str:
    """根据公司名称返回类别名称"""
    for category, data in WATCHLIST.items():
        for company in data["companies"]:
            if company["name"] == company_name:
                return data["name"]
    return ""


# ─── 任务二：市场新动态 ──────────────────────────────────────────────────────

def search_market_news(client: PerplexityClient) -> dict:
    """
    任务二：搜索过去24小时香港IPO市场新消息
    合并多个查询为一次请求，控制成本
    """
    logger.info("=== 任务二：搜索市场新动态 ===")

    query = (
        "请搜索最近24小时香港IPO市场的最新动态（截至今天），包括：\n"
        "1. 新递表公司（向港交所递交上市申请）\n"
        "2. 新通过聆讯的公司\n"
        "3. 即将开始招股的新股\n"
        "4. 近期上市首日表现\n"
        "5. 港交所最新IPO政策或市场趋势\n"
        "请用中文回答，条理清晰，重点突出。"
    )

    result = client.search(query, max_tokens=1500)
    logger.info("任务二完成，成功：%s", result.get("success"))
    return result


# ─── 任务三：新递表项目深度分析 ──────────────────────────────────────────────

def analyze_new_filings(client: PerplexityClient) -> list:
    """
    任务三：分析热门赛道的新递表项目
    """
    logger.info("=== 任务三：分析新递表项目 ===")

    query = (
        "请搜索2025-2026年香港IPO市场中，以下热门赛道的新递表项目：\n"
        "半导体、人工智能（AI）、生物医药、机器人、新能源、消费品\n\n"
        "对于发现的新递表项目，请提供：\n"
        "1. 公司名称和主营业务\n"
        "2. 所属赛道\n"
        "3. 递表时间\n"
        "4. 估值或融资情况（如有）\n"
        "5. 主要投资亮点和风险\n\n"
        "请重点关注最近1-3个月内的新递表项目。"
    )

    result = client.search(query, max_tokens=2000)
    logger.info("任务三完成，成功：%s", result.get("success"))
    return [result]


# ─── 已上市股票表现 ──────────────────────────────────────────────────────────

def track_listed_performance(client: PerplexityClient) -> list:
    """追踪已上市股票的最新表现"""
    logger.info("=== 追踪已上市股票表现 ===")

    listed = get_listed_companies()
    results = []

    for company in listed:
        ticker_info = f"（代码：{company['ticker']}）" if company.get("ticker") else ""
        query = (
            f"请搜索香港上市股票 {company['name']}{ticker_info} 的最新表现：\n"
            "1. 最新股价和涨跌幅\n"
            "2. 近期重要公告或新闻\n"
            "3. 分析师评级（如有）\n"
            "请简明扼要，不超过150字。"
        )

        result = client.search(query, max_tokens=512)
        results.append(
            {
                "company": company["name"],
                "ticker": company.get("ticker"),
                "sector": company["sector"],
                "success": result.get("success", False),
                "content": result.get("content", ""),
                "error": result.get("error"),
                "citations": result.get("citations", []),
            }
        )
        time.sleep(1)

    logger.info("已上市股票追踪完成，共 %d 支", len(results))
    return results


# ─── GitHub Issue 创建 ────────────────────────────────────────────────────────

def _ensure_labels(headers: dict) -> None:
    """确保 GitHub Issue 标签存在"""
    labels_url = f"{GITHUB_API_URL}/repos/{GITHUB_REPO}/labels"

    for label_name, color, description in [
        (IPO_LABEL, "0075ca", "每日IPO自动监控报告"),
        (AUTO_LABEL, "e4e669", "由 GitHub Actions 自动生成"),
    ]:
        try:
            resp = requests.get(f"{labels_url}/{label_name}", headers=headers, timeout=10)
            if resp.status_code == 404:
                requests.post(
                    labels_url,
                    headers=headers,
                    json={"name": label_name, "color": color, "description": description},
                    timeout=10,
                )
                logger.info("已创建标签：%s", label_name)
        except requests.RequestException as e:
            logger.warning("创建标签失败 %s：%s", label_name, e)


def create_github_issue(title: str, body: str) -> bool:
    """
    创建 GitHub Issue

    Returns:
        True 表示成功，False 表示失败
    """
    if not GITHUB_TOKEN:
        logger.warning("未设置 GITHUB_TOKEN，跳过创建 Issue")
        return False

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    _ensure_labels(headers)

    issue_data = {
        "title": title,
        "body": body,
        "labels": [IPO_LABEL, AUTO_LABEL],
    }

    try:
        resp = requests.post(
            f"{GITHUB_API_URL}/repos/{GITHUB_REPO}/issues",
            headers=headers,
            json=issue_data,
            timeout=30,
        )
        resp.raise_for_status()
        issue_url = resp.json().get("html_url", "")
        logger.info("GitHub Issue 创建成功：%s", issue_url)
        return True
    except requests.RequestException as e:
        logger.error("创建 GitHub Issue 失败：%s", e)
        return False


# ─── 主程序 ───────────────────────────────────────────────────────────────────

def main():
    """主程序入口"""
    now_hk = datetime.now(HK_TZ)
    date_str = now_hk.strftime("%Y-%m-%d")
    logger.info("香港IPO监控系统启动 - %s", now_hk.strftime("%Y-%m-%d %H:%M HKT"))

    # 初始化 API 客户端
    try:
        client = PerplexityClient()
    except ValueError as e:
        logger.error("初始化 Perplexity 客户端失败：%s", e)
        sys.exit(1)

    # ── 执行三大任务 ───────────────────────────────────────────────────────────
    company_updates = track_company_progress(client)
    market_overview = search_market_news(client)
    new_listings = analyze_new_filings(client)
    listed_performance = track_listed_performance(client)

    # ── 生成报告 ───────────────────────────────────────────────────────────────
    logger.info("正在生成报告...")
    report_content = generate_daily_report(
        market_overview=market_overview,
        company_updates=company_updates,
        new_listings=new_listings,
        listed_performance=listed_performance,
        date_str=date_str,
    )

    # ── 保存报告文件 ───────────────────────────────────────────────────────────
    report_path = save_report(report_content, str(REPORTS_DIR), date_str)

    # ── 保存数据快照 ───────────────────────────────────────────────────────────
    snapshot = {
        "date": date_str,
        "generated_at": now_hk.isoformat(),
        "market_overview": market_overview,
        "company_updates": company_updates,
        "new_listings": new_listings,
        "listed_performance": listed_performance,
    }
    save_data_snapshot(snapshot, str(DATA_DIR), date_str)

    # ── 创建 GitHub Issue ─────────────────────────────────────────────────────
    issue_title = f"🇭🇰 香港IPO日报 - {date_str}"
    issue_body = format_issue_body(report_content, report_path)
    issue_created = create_github_issue(issue_title, issue_body)

    # ── 完成 ──────────────────────────────────────────────────────────────────
    logger.info("监控任务完成！报告路径：%s，Issue 创建：%s", report_path, "成功" if issue_created else "失败/跳过")


if __name__ == "__main__":
    main()
