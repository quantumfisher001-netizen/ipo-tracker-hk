# -*- coding: utf-8 -*-
"""
加密货币庄家行为分析模块
接收用户持仓数据，通过 Perplexity Sonar API 进行庄家操控迹象分析
"""

import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import pytz
import requests

sys.path.insert(0, str(Path(__file__).parent))

from perplexity_client import PerplexityClient

logger = logging.getLogger(__name__)

HK_TZ = pytz.timezone("Asia/Hong_Kong")

GITHUB_API_URL = "https://api.github.com"
GITHUB_REPO = os.environ.get("GITHUB_REPOSITORY", "quantumfisher001-netizen/ipo-tracker-hk")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

MM_LABEL = "crypto-mm-analysis"
AUTO_LABEL = "auto-generated"

SYSTEM_PROMPT = (
    "你是一位专注庄家行为分析的加密货币研究员，熟悉 MMT 案例、ALPACA 轧空、"
    "SIREN 控盘等典型手法。请用中文回答，分析结论需有据可查，"
    "并在末尾附上完整免责声明：本分析仅供信息参考，不构成任何投资建议，"
    "加密货币市场风险极高，请自行承担投资风险。"
)


def build_analysis_query(
    token: str,
    cost_price: str,
    current_price: str,
    pnl: str,
    funding_rates: str,
    oi_change: str,
    whale_flow: str,
    kol_frequency: str,
    cex_consolidation: str,
) -> str:
    """构建庄家行为分析查询"""
    return (
        f"我当前持有 {token}，请帮我判断是否存在庄家操控迹象：\n\n"
        f"【当前数据】\n"
        f"- 持仓成本：{cost_price}\n"
        f"- 当前价格：{current_price}\n"
        f"- 持仓盈亏：{pnl}\n"
        f"- 合约资金费率（连续最近 3 期）：{funding_rates}\n"
        f"- OI 变化（过去 24 小时）：{oi_change}\n"
        f"- 链上大户净流向：{whale_flow}\n"
        f"- KOL 近期推文频率：{kol_frequency}\n"
        f"- 近期是否有大量代币向 CEX 归集：{cex_consolidation}\n\n"
        f"请分析：\n"
        f"1. 当前最符合哪种庄家手法？"
        f"（控盘拉盘出货 / 清算猎手 / KOL 轧空 / 资金费率套利 / 无明显操控）\n"
        f"2. 若判断为出货阶段，给出 3 个具体证据\n"
        f"3. 操作建议（继续持有 / 止盈减仓 / 立即离场），附执行价位\n"
        f"4. 危险信号倒计时：若以下哪项发生，我必须在 10 分钟内离场（列出 2-3 个）\n\n"
        f"同时，请搜索 {token} 最新的链上数据、资金费率、大户持仓变化、"
        f"近期 KOL 推文内容作为补充参考。"
    )


def run_analysis(client: PerplexityClient, query: str) -> dict:
    """调用 Perplexity API 执行庄家行为分析"""
    logger.info("=== 开始庄家行为分析 ===")
    result = client.search(
        query,
        system_prompt=SYSTEM_PROMPT,
        max_tokens=2000,
    )
    logger.info("分析完成，成功：%s", result.get("success"))
    return result


def generate_analysis_report(
    token: str,
    query_inputs: dict,
    analysis_result: dict,
    date_str: str,
    time_str: str,
) -> str:
    """生成分析报告（Markdown 格式）"""
    sections = []

    sections.append(f"# 🔍 加密货币庄家行为分析 — {token} — {date_str}\n")
    sections.append(f"> 报告生成时间：{time_str}  |  数据来源：Perplexity Sonar API\n")

    sections.append("## 📋 输入数据摘要\n")
    sections.append(f"| 项目 | 数据 |")
    sections.append(f"|------|------|")
    sections.append(f"| 代币 | {token} |")
    sections.append(f"| 持仓成本 | {query_inputs['cost_price']} |")
    sections.append(f"| 当前价格 | {query_inputs['current_price']} |")
    sections.append(f"| 持仓盈亏 | {query_inputs['pnl']} |")
    sections.append(f"| 资金费率（近 3 期）| {query_inputs['funding_rates']} |")
    sections.append(f"| OI 变化（24h）| {query_inputs['oi_change']} |")
    sections.append(f"| 链上大户净流向 | {query_inputs['whale_flow']} |")
    sections.append(f"| KOL 推文频率 | {query_inputs['kol_frequency']} |")
    sections.append(f"| CEX 归集 | {query_inputs['cex_consolidation']} |")
    sections.append("")

    sections.append("## 🧠 庄家行为分析\n")
    if analysis_result.get("success") and analysis_result.get("content"):
        sections.append(analysis_result["content"])
        if analysis_result.get("citations"):
            sections.append("\n**参考来源：**")
            for url in analysis_result["citations"][:8]:
                sections.append(f"- {url}")
    else:
        err = analysis_result.get("error", "未知错误")
        sections.append(f"> ⚠️ 分析数据获取失败：{err}")
    sections.append("")

    sections.append("## ⚠️ 免责声明\n")
    sections.append(
        "- 本报告由 AI 自动生成，**仅供信息参考，不构成任何投资建议**\n"
        "- 加密货币市场波动极大，存在本金全损风险，请务必独立判断\n"
        "- 庄家行为分析基于公开数据推断，不代表对市场走势的准确预测\n"
        "- 所有操作建议均为参考性意见，实际盈亏由投资者自行承担\n"
    )

    sections.append("---")
    sections.append(
        f"*本报告由 [ipo-tracker-hk](https://github.com/quantumfisher001-netizen/ipo-tracker-hk) "
        f"加密货币庄家分析模块自动生成 | {time_str}*"
    )

    return "\n".join(sections)


def _ensure_labels(headers: dict) -> None:
    """确保 GitHub Issue 标签存在"""
    labels_url = f"{GITHUB_API_URL}/repos/{GITHUB_REPO}/labels"

    for label_name, color, description in [
        (MM_LABEL, "d93f0b", "加密货币庄家行为分析报告"),
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
    """创建 GitHub Issue，返回 True 表示成功"""
    if not GITHUB_TOKEN:
        logger.warning("未设置 GITHUB_TOKEN，跳过创建 Issue")
        return False

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    _ensure_labels(headers)

    try:
        resp = requests.post(
            f"{GITHUB_API_URL}/repos/{GITHUB_REPO}/issues",
            headers=headers,
            json={"title": title, "body": body, "labels": [MM_LABEL, AUTO_LABEL]},
            timeout=30,
        )
        resp.raise_for_status()
        logger.info("GitHub Issue 创建成功：%s", resp.json().get("html_url", ""))
        return True
    except requests.RequestException as e:
        logger.error("创建 GitHub Issue 失败：%s", e)
        return False


def save_report(content: str, reports_dir: str, token: str, date_str: str) -> str:
    """保存分析报告到文件，返回文件路径"""
    os.makedirs(reports_dir, exist_ok=True)
    safe_token = "".join(c if c.isalnum() else "_" for c in token.upper())
    filename = f"crypto-mm-{safe_token}-{date_str}.md"
    filepath = os.path.join(reports_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info("报告已保存到：%s", filepath)
    return filepath


def main():
    """主程序：读取环境变量，执行庄家行为分析，输出 GitHub Issue 和报告文件"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    now_hk = datetime.now(HK_TZ)
    date_str = now_hk.strftime("%Y-%m-%d")
    time_str = now_hk.strftime("%Y-%m-%d %H:%M HKT")

    # ── 读取输入参数（来自 workflow_dispatch 环境变量）─────────────────────────
    token = os.environ.get("INPUT_TOKEN", "").strip()
    cost_price = os.environ.get("INPUT_COST_PRICE", "未知").strip()
    current_price = os.environ.get("INPUT_CURRENT_PRICE", "未知").strip()
    pnl = os.environ.get("INPUT_PNL", "未知").strip()
    funding_rates = os.environ.get("INPUT_FUNDING_RATES", "未知").strip()
    oi_change = os.environ.get("INPUT_OI_CHANGE", "未知").strip()
    whale_flow = os.environ.get("INPUT_WHALE_FLOW", "未知").strip()
    kol_frequency = os.environ.get("INPUT_KOL_FREQUENCY", "正常").strip()
    cex_consolidation = os.environ.get("INPUT_CEX_CONSOLIDATION", "未知").strip()

    if not token:
        logger.error("未提供代币名称（INPUT_TOKEN），请设置环境变量")
        sys.exit(1)

    logger.info("加密货币庄家分析启动 — 代币：%s — %s", token, time_str)

    # ── 初始化客户端 ──────────────────────────────────────────────────────────
    try:
        client = PerplexityClient()
    except ValueError as e:
        logger.error("初始化 Perplexity 客户端失败：%s", e)
        sys.exit(1)

    query_inputs = {
        "cost_price": cost_price,
        "current_price": current_price,
        "pnl": pnl,
        "funding_rates": funding_rates,
        "oi_change": oi_change,
        "whale_flow": whale_flow,
        "kol_frequency": kol_frequency,
        "cex_consolidation": cex_consolidation,
    }

    # ── 执行分析 ──────────────────────────────────────────────────────────────
    query = build_analysis_query(token, **query_inputs)
    analysis_result = run_analysis(client, query)

    # ── 生成报告 ──────────────────────────────────────────────────────────────
    report_content = generate_analysis_report(
        token=token,
        query_inputs=query_inputs,
        analysis_result=analysis_result,
        date_str=date_str,
        time_str=time_str,
    )

    # ── 保存报告文件 ──────────────────────────────────────────────────────────
    repo_root = Path(__file__).parent.parent
    report_path = save_report(report_content, str(repo_root / "reports"), token, date_str)

    # ── 创建 GitHub Issue ─────────────────────────────────────────────────────
    issue_title = f"🔍 庄家行为分析 — {token} — {date_str}"
    filename = Path(report_path).name
    issue_body = (
        report_content
        + f"\n\n---\n📁 完整报告已存档：[{filename}](../blob/main/reports/{filename})"
    )
    issue_created = create_github_issue(issue_title, issue_body)

    logger.info(
        "分析完成！报告路径：%s，Issue 创建：%s",
        report_path,
        "成功" if issue_created else "失败/跳过",
    )


if __name__ == "__main__":
    main()
