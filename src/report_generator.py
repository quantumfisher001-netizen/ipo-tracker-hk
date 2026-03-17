# -*- coding: utf-8 -*-
"""
报告生成模块
将监控结果生成结构化 Markdown 报告
"""

import json
import logging
import os
from datetime import datetime

import pytz

logger = logging.getLogger(__name__)

HK_TZ = pytz.timezone("Asia/Hong_Kong")


def _hk_now() -> datetime:
    """返回当前香港时间"""
    return datetime.now(HK_TZ)


def generate_daily_report(
    market_overview: dict,
    company_updates: list,
    listed_performance: list,
    date_str: str = None,
    new_listings: list = None,  # 保留参数但不再使用，避免旧调用报错
) -> str:
    """
    生成每日IPO报告（Markdown格式）

    Args:
        market_overview: 市场概览数据，格式为 {"market": {...}, "new_filings_analysis": {...}}
        company_updates: 各公司进展更新列表（只包含 has_update=True 的公司）
        listed_performance: 已上市股票表现
        date_str: 报告日期字符串，默认使用今天香港时间
        new_listings: 已废弃参数，保留以兼容旧调用

    Returns:
        Markdown 格式报告字符串
    """
    now = _hk_now()
    if date_str is None:
        date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%Y-%m-%d %H:%M HKT")

    sections = []

    # ─── 标题 ─────────────────────────────────────────────────────────────────
    sections.append(f"# 🇭🇰 香港IPO日报 - {date_str}\n")
    sections.append(f"> 报告生成时间：{time_str}  |  数据来源：Perplexity Sonar API\n")

    # ─── 市场概览 ─────────────────────────────────────────────────────────────
    sections.append("## 📊 市场概览\n")
    market_data = market_overview.get("market", {})
    if market_data.get("success") and market_data.get("content"):
        sections.append(market_data["content"])
        if market_data.get("citations"):
            sections.append("\n**参考来源：**")
            for url in market_data["citations"][:5]:
                sections.append(f"- {url}")
    else:
        err = market_data.get("error", "未知错误")
        sections.append(f"> ⚠️ 市场概览数据获取失败：{err}")
    sections.append("")

    # ─── 今日新递表公司分析 ───────────────────────────────────────────────────
    sections.append("## 🆕 今日新递表公司分析\n")
    filings_data = market_overview.get("new_filings_analysis", {})
    if filings_data.get("success") and filings_data.get("content"):
        sections.append(filings_data["content"])
        if filings_data.get("citations"):
            sections.append("\n**参考来源：**")
            for url in filings_data["citations"][:5]:
                sections.append(f"- {url}")
    else:
        err = filings_data.get("error", "未知错误")
        sections.append(f"> ⚠️ 新递表公司分析数据获取失败：{err}")
    sections.append("")

    # ─── 监控清单重要进展 ─────────────────────────────────────────────────────
    sections.append("## 🔥 监控清单重要进展\n")
    if company_updates:
        for update in company_updates:
            sections.append(f"### 🆕 {update['company']}（{update['sector']}）")
            sections.append(update.get("content", "无详细信息"))
            sections.append("")
    else:
        sections.append("> 今日监控清单内暂无新进展\n")

    # ─── 已上市股票表现 ───────────────────────────────────────────────────────
    sections.append("## 📈 已上市股票表现\n")
    if listed_performance:
        for perf in listed_performance:
            sections.append(f"### {perf['company']}（{perf.get('ticker', 'N/A')}）")
            if perf.get("success") and perf.get("content"):
                sections.append(perf["content"])
            elif perf.get("error"):
                sections.append(f"> ⚠️ 数据获取失败：{perf['error']}")
            sections.append("")
    else:
        sections.append("> 暂无已上市股票数据\n")

    # ─── 风险提示 ─────────────────────────────────────────────────────────────
    sections.append("## ⚠️ 风险提示\n")
    sections.append(
        "- 本报告由 AI 自动生成，仅供参考，不构成任何投资建议\n"
        "- IPO 市场存在较高风险，请在投资前做好充分研究\n"
        "- 所有信息基于公开来源，请以港交所官方公告为准\n"
        "- 新股认购存在中签率不确定性，认购前请了解相关风险\n"
    )

    # ─── 页脚 ─────────────────────────────────────────────────────────────────
    sections.append("---")
    sections.append(
        f"*本报告由 [ipo-tracker-hk](https://github.com/quantumfisher001-netizen/ipo-tracker-hk) "
        f"自动生成 | {time_str}*"
    )

    return "\n".join(sections)


def save_report(report_content: str, reports_dir: str, date_str: str = None) -> str:
    """
    保存报告到文件

    Args:
        report_content: 报告内容
        reports_dir: 保存目录
        date_str: 日期字符串

    Returns:
        保存的文件路径
    """
    if date_str is None:
        date_str = _hk_now().strftime("%Y-%m-%d")

    os.makedirs(reports_dir, exist_ok=True)
    filename = f"ipo-report-{date_str}.md"
    filepath = os.path.join(reports_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report_content)

    logger.info("报告已保存到：%s", filepath)
    return filepath


def save_data_snapshot(data: dict, data_dir: str, date_str: str = None) -> str:
    """
    保存原始数据快照（JSON格式）

    Args:
        data: 数据字典
        data_dir: 保存目录
        date_str: 日期字符串

    Returns:
        保存的文件路径
    """
    if date_str is None:
        date_str = _hk_now().strftime("%Y-%m-%d")

    os.makedirs(data_dir, exist_ok=True)
    filename = f"snapshot-{date_str}.json"
    filepath = os.path.join(data_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info("数据快照已保存到：%s", filepath)
    return filepath


def format_issue_body(report_content: str, report_path: str = None) -> str:
    """
    格式化 GitHub Issue 正文

    Args:
        report_content: 报告内容
        report_path: 报告文件路径（可选，用于添加链接）

    Returns:
        GitHub Issue 正文字符串
    """
    body = report_content
    if report_path:
        filename = os.path.basename(report_path)
        body += (
            f"\n\n---\n📁 完整报告已存档：[{filename}]"
            f"(../blob/main/reports/{filename})"
        )
    return body
