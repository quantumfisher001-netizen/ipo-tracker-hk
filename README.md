# 🇭🇰 ipo-tracker-hk

**香港IPO实时追踪系统** — 自动监控香港IPO市场动态，每日生成智能分析报告。

[![IPO Monitor](https://github.com/quantumfisher001-netizen/ipo-tracker-hk/actions/workflows/ipo-monitor.yml/badge.svg)](https://github.com/quantumfisher001-netizen/ipo-tracker-hk/actions/workflows/ipo-monitor.yml)

---

## 📋 项目说明

本系统使用 **Perplexity Sonar API** 进行实时联网搜索，通过 **GitHub Actions** 每天定时自动运行，将香港IPO市场最新动态整理成结构化日报，输出到 **GitHub Issues** 并存档为 Markdown 文件。

---

## ✨ 功能介绍

| 功能 | 说明 |
|------|------|
| 📊 **市场概览** | 每日香港IPO市场整体动态 |
| 🔥 **重要进展** | 监控项目的聆讯结果、招股日期、上市公告 |
| 📋 **项目状态更新** | 32+ 个监控项目的逐一状态追踪 |
| 🆕 **新递表项目** | 热门赛道（半导体/AI/生物医药/机器人等）新递表公司分析 |
| 📈 **已上市表现** | 精锋医疗、天数智芯等已上市股票股价及新闻 |
| ⚠️ **风险提示** | 自动附加投资风险声明 |
| 🔍 **加密货币庄家行为分析** | 手动触发，输入持仓数据，AI 判断庄家操控手法并给出操作建议 |

---

## 🏗️ 技术架构

```
Perplexity Sonar API（实时联网搜索）
        ↓
GitHub Actions（每天 9:00 / 16:00 HKT 自动运行 / 手动触发庄家分析）
        ↓
Python 3.11（monitor.py / crypto_mm_analyzer.py）
        ↓
报告输出
├── GitHub Issues（每日日报 / 庄家分析报告）
└── reports/ 目录（Markdown 存档）
        +
data/ 目录（JSON 数据快照）
```

---

## 🔧 如何设置

### 1. Fork 或克隆本仓库

### 2. 配置 GitHub Secrets

前往仓库 **Settings → Secrets and variables → Actions**，添加以下 Secret：

| Secret 名称 | 说明 | 是否必须 |
|------------|------|---------|
| `PPLX_API_KEY` | Perplexity API Key（前往 [perplexity.ai/settings/api](https://www.perplexity.ai/settings/api) 获取） | ✅ 必须 |

> `GITHUB_TOKEN` 由 GitHub Actions 自动提供，无需手动配置。

### 3. 启用 GitHub Actions

确保仓库的 Actions 功能已开启（Settings → Actions → General → Allow all actions）。

### 4. 手动触发测试

前往 **Actions → 香港IPO自动监控 → Run workflow** 可手动触发一次运行。

---

## 📅 运行时间表

| 时间（香港时间 HKT） | UTC | 说明 |
|---------------------|-----|------|
| 每天 09:00 | 01:00 | 早间开市前汇总 |
| 每天 16:00 | 08:00 | 港股收市后汇总 |

---

## 📊 监控项目清单

### A类 - 已通过聆讯/接近上市
- 易控智驾（自动驾驶）

### B类 - 递表中（近期有进展）
- 琻捷电子（半导体）、乐动机器人（机器人）、海马云（云计算）
- 先为达生物（生物医药/GLP-1）、护家科技HBN（消费护肤）、优地机器人（机器人）

### B类 - 递表中（等待聆讯）
- 武汉聚芯微、硅基智能、创智芯联、魔视智能、伯希和、好医生云医疗
- 铂生生物、瑞为信息、优艾智合、滨会生物、森亿医疗、时迈药业
- 欢创科技、新荷花中药、米多多、铂生卓越

### C类 - 招股书失效（关注是否再次递表）
- 暖哇科技（保险AI）、因明生物（创新药）、成都国星宇航（商业航天）

### D类 - 已上市（监控二级市场表现）
- 精锋医疗 02675.HK、天数智芯、海致科技

### E类 - 未递表/早期
- 普渡科技（服务机器人）、康爱生物（细胞免疫）、小视科技（视觉AI）

---

## 📁 文件结构

```
ipo-tracker-hk/
├── .github/
│   └── workflows/
│       ├── ipo-monitor.yml            # GitHub Actions 定时任务（IPO 日报）
│       └── crypto-mm-analysis.yml     # GitHub Actions 手动触发（庄家分析）
├── src/
│   ├── monitor.py                     # IPO 监控主程序
│   ├── crypto_mm_analyzer.py          # 加密货币庄家行为分析模块
│   ├── perplexity_client.py           # Perplexity API 封装
│   ├── report_generator.py            # 报告生成
│   └── ipo_watchlist.py               # 监控清单
├── data/                              # JSON 数据快照存档
├── reports/                           # Markdown 报告存档
├── requirements.txt
└── README.md
```

---

## 📰 报告示例

每日报告格式：

```markdown
# 🇭🇰 香港IPO日报 - 2026-03-17

## 📊 市场概览
## 🔥 重要进展
## 📋 项目状态更新
## 🆕 新递表项目
## 📈 已上市股票表现
## ⚠️ 风险提示
```

日报将自动发布到 [Issues](../../issues?q=label%3Aipo-daily-report) 页面。

---

## 💰 成本估算

使用 Perplexity Sonar 模型（$1/1M tokens），每月运行约 60 次（每天 2 次），预计月费用 **< $5**，在 Perplexity Pro 会员包含的 API Credits 范围内。

---

## 🔍 加密货币庄家行为分析

通过 **Actions → 加密货币庄家行为分析 → Run workflow** 手动触发，填写以下输入参数：

> **前提条件**：需在仓库 **Settings → Secrets and variables → Actions** 中配置 `PPLX_API_KEY`（与 IPO 监控共用同一个密钥）。

| 参数 | 说明 | 示例 |
|------|------|------|
| `token` | 代币名称 | BTC |
| `cost_price` | 持仓成本价格 | $42,000 |
| `current_price` | 当前价格 | $45,000 |
| `pnl` | 持仓盈亏 | +7.1% |
| `funding_rates` | 合约资金费率（近 3 期） | +0.01%, +0.02%, +0.03% |
| `oi_change` | OI 变化（24h） | 增加 / 减少 / 稳定 |
| `whale_flow` | 链上大户净流向 | 流入交易所 / 流出交易所 / 未知 |
| `kol_frequency` | KOL 近期推文频率 | 正常 / 异常密集 |
| `cex_consolidation` | 近期代币是否向 CEX 归集 | 是 / 否 / 未知 |

分析结果将自动发布到 [Issues](../../issues?q=label%3Acrypto-mm-analysis) 页面（标签：`crypto-mm-analysis`），并存档到 `reports/` 目录。

**分析内容包括：**
1. 当前最符合哪种庄家手法（控盘拉盘出货 / 清算猎手 / KOL 轧空 / 资金费率套利 / 无明显操控）
2. 出货阶段的 3 个具体证据（如适用）
3. 操作建议（继续持有 / 止盈减仓 / 立即离场），附执行价位参考
4. 危险信号倒计时（2-3 个必须在 10 分钟内离场的信号）

---

## ⚠️ 免责声明

本系统由 AI 自动生成报告，**仅供信息参考，不构成任何投资建议**。所有数据基于公开来源，请以港交所官方公告为准。

加密货币庄家行为分析同样**仅供参考，不构成投资建议**。加密货币市场波动极大，存在本金全损风险，请自行承担投资风险。
