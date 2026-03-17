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

---

## 🏗️ 技术架构

```
Perplexity Sonar API（实时联网搜索）
        ↓
GitHub Actions（每天 9:00 / 16:00 HKT 自动运行）
        ↓
Python 3.11（monitor.py 执行三大任务）
        ↓
报告输出
├── GitHub Issues（每日日报，带标签 ipo-daily-report）
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
│       └── ipo-monitor.yml        # GitHub Actions 定时任务
├── src/
│   ├── monitor.py                 # 主程序
│   ├── perplexity_client.py       # Perplexity API 封装
│   ├── report_generator.py        # 报告生成
│   └── ipo_watchlist.py           # 监控清单
├── data/                          # JSON 数据快照存档
├── reports/                       # Markdown 报告存档
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

## ⚠️ 免责声明

本系统由 AI 自动生成报告，**仅供信息参考，不构成任何投资建议**。所有数据基于公开来源，请以港交所官方公告为准。
