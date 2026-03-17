# -*- coding: utf-8 -*-
"""
香港IPO自动监控主程序
执行三大任务：
  1. 已有项目进展追踪（一次性查询，只显示有动态的公司）
  2. 市场概览 + 今日新递表公司五维度投资分析
  3. 已上市股票表现追踪
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

# API 请求间隔（秒），避免触发速率限制
API_RATE_LIMIT_DELAY = 2

# 判断"无新消息"的关键词列表
NO_NEWS_KEYWORDS = ["没有新消息", "无新消息", "暂无", "未发现", "无相关", "不确定"]


# ─── 任务一：已有项目进展追踪 ─────────────────────────────────────────────────

def track_company_progress(client: PerplexityClient) -> list:
    """
    任务一：一次性查询所有监控项目，解析出有动态的公司
    节省 token：整个清单只用 1 次 API 调用
    """
    logger.info("=== 任务一：追踪已有项目进展 ===")

    pre_ipo = get_pre_ipo_companies()

    # 构建公司名单字符串
    company_list = "\n".join(
        f"- {c['name']}（{c['sector']}，状态：{c['status']}）"
        for c in pre_ipo
    )

    today = datetime.now(HK_TZ).strftime("%Y年%m月%d日")

    query = (
        f"今天是{today}。以下是一份香港IPO监控清单，请搜索今天或最近几天这些公司的最新动态：\n\n"
        f"{company_list}\n\n"
        "请注意：\n"
        "1. 只需要报告**有实质性新消息**的公司（例如：通过聆讯、招股公告、上市日期、专利诉讼、递表失效、撤回申请等）\n"
        "2. 没有新消息的公司**完全不需要提及**\n"
        "3. 对每个有动态的公司，格式如下：\n"
        "【公司名称】\n"
        "动态：[具体内容，不超过100字]\n"
        "风险：[如有风险因素]\n"
        "关联：[如有同赛道关联公司动向]\n\n"
        "如果以上所有公司今天都没有新消息，请直接回复：「今日监控清单内暂无新进展」"
    )

    result = client.search(query, max_tokens=2000)

    results = []
    content = result.get("content", "") if result.get("success") else ""

    for company in pre_ipo:
        # 判断该公司是否在返回内容中被提及
        has_update = False
        company_content = ""

        if content and company["name"] in content:
            # 提取该公司相关的段落
            lines = content.split("\n")
            capturing = False
            company_lines = []
            for line in lines:
                if company["name"] in line:
                    capturing = True
                    company_lines.append(line)
                elif capturing:
                    # 遇到下一个【公司名称】则停止
                    if line.startswith("【") and company["name"] not in line:
                        break
                    company_lines.append(line)

            company_content = "\n".join(company_lines).strip()

            # 判断是否有实质性更新（不是"无消息"类回复）
            has_update = bool(company_content) and not any(kw in company_content for kw in NO_NEWS_KEYWORDS)

        # 只有 has_update=True 的公司才加入结果列表
        if has_update:
            results.append({
                "company": company["name"],
                "sector": company["sector"],
                "status": company["status"],
                "category_name": _get_category_name(company["name"]),
                "has_update": True,
                "success": True,
                "content": company_content,
                "error": None,
                "citations": result.get("citations", []),
            })

    logger.info("任务一完成，共发现 %d 家公司有更新（总监控 %d 家）", len(results), len(pre_ipo))
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
    任务二：市场概览 + 今日新递表公司五维度投资分析
    返回 {"market": {...}, "new_filings_analysis": {...}}
    """
    logger.info("=== 任务二：搜索市场新动态 ===")

    today = datetime.now(HK_TZ).strftime("%Y年%m月%d日")

    # 查询1：市场概览
    market_query = (
        f"请搜索今天（{today}）香港IPO市场的最新动态，包括：\n"
        "1. 今天新递表的公司（向港交所递交上市申请）\n"
        "2. 最近通过聆讯的公司\n"
        "3. 即将招股的新股（招股日期、价格区间、上市日期）\n"
        "4. 近期上市首日表现\n"
        "5. 港交所最新IPO政策或市场趋势\n"
        "请用中文回答，条理清晰。"
    )
    market_result = client.search(market_query, max_tokens=1200)
    time.sleep(API_RATE_LIMIT_DELAY)

    # 查询2：今日新递表公司五维度分析
    analysis_query = (
        f"请搜索今天（{today}）向港交所递交IPO申请的公司名单。\n"
        "对于今天新递表的每家公司，请逐一提供以下五个维度的简要分析：\n\n"
        "【公司名称】（赛道）\n"
        "📌 基本情况：主营业务、保荐人、预计集资规模\n"
        "💡 是否参与IPO认购：建议/不建议/观望，一句话理由\n"
        "📈 短期持有（首周）：预期表现判断\n"
        "🏦 长期持有：核心竞争力或主要风险\n"
        "🔗 港股通可能性：高/中/低，判断依据\n"
        "💰 现金流状况：盈利/亏损/烧钱速度简述\n\n"
        f"如今天（{today}）无新递表公司，请明确说明「今日无新递表公司」。"
    )
    analysis_result = client.search(analysis_query, max_tokens=1500)

    logger.info("任务二完成，市场概览：%s，新递表分析：%s",
                market_result.get("success"), analysis_result.get("success"))

    return {
        "market": market_result,
        "new_filings_analysis": analysis_result,
    }


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

    # ── 执行任务 ───────────────────────────────────────────────────────────────
    company_updates = track_company_progress(client)
    market_overview = search_market_news(client)        # 返回 {"market":..., "new_filings_analysis":...}
    listed_performance = track_listed_performance(client)

    # ── 生成报告 ───────────────────────────────────────────────────────────────
    logger.info("正在生成报告...")
    report_content = generate_daily_report(
        market_overview=market_overview,
        company_updates=company_updates,
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
