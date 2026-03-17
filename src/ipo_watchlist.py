# -*- coding: utf-8 -*-
"""
香港IPO监控清单
包含所有需要监控的IPO项目，按类别分组
"""

# 监控项目列表
WATCHLIST = {
    "A": {
        "name": "A类 - 已通过聆讯/接近上市",
        "companies": [
            {
                "name": "易控智驾",
                "sector": "自动驾驶",
                "status": "已通过聆讯",
                "ticker": None,
            },
        ],
    },
    "B_active": {
        "name": "B类 - 递表中（近期有进展）",
        "companies": [
            {"name": "琻捷电子", "sector": "半导体", "status": "递表中", "ticker": None},
            {"name": "乐动机器人", "sector": "机器人", "status": "递表中", "ticker": None},
            {"name": "海马云", "sector": "云计算", "status": "递表中", "ticker": None},
            {
                "name": "先为达生物",
                "sector": "生物医药/GLP-1",
                "status": "递表中",
                "ticker": None,
            },
            {
                "name": "护家科技HBN",
                "sector": "消费护肤",
                "status": "递表中",
                "ticker": None,
            },
            {
                "name": "优地机器人",
                "sector": "机器人",
                "status": "递表中，预计2026Q1-Q2上市",
                "ticker": None,
            },
        ],
    },
    "B_pending": {
        "name": "B类 - 递表中（等待聆讯）",
        "companies": [
            {"name": "武汉聚芯微", "sector": "半导体", "status": "等待聆讯", "ticker": None},
            {
                "name": "硅基智能",
                "sector": "AI数字人",
                "status": "等待聆讯",
                "ticker": None,
            },
            {
                "name": "创智芯联",
                "sector": "半导体",
                "status": "等待聆讯",
                "ticker": None,
            },
            {
                "name": "魔视智能",
                "sector": "自动驾驶",
                "status": "等待聆讯",
                "ticker": None,
            },
            {
                "name": "伯希和",
                "sector": "户外消费",
                "status": "等待聆讯",
                "ticker": None,
            },
            {
                "name": "好医生云医疗",
                "sector": "医疗",
                "status": "等待聆讯",
                "ticker": None,
            },
            {
                "name": "铂生生物",
                "sector": "干细胞",
                "status": "等待聆讯",
                "ticker": None,
            },
            {
                "name": "瑞为信息",
                "sector": "AI民航",
                "status": "等待聆讯",
                "ticker": None,
            },
            {
                "name": "优艾智合",
                "sector": "工业机器人",
                "status": "等待聆讯",
                "ticker": None,
            },
            {
                "name": "滨会生物",
                "sector": "溶瘤病毒",
                "status": "等待聆讯",
                "ticker": None,
            },
            {
                "name": "森亿医疗",
                "sector": "医疗AI",
                "status": "等待聆讯",
                "ticker": None,
            },
            {
                "name": "时迈药业",
                "sector": "肿瘤免疫",
                "status": "等待聆讯",
                "ticker": None,
            },
            {
                "name": "欢创科技",
                "sector": "机器人/激光雷达",
                "status": "等待聆讯",
                "ticker": None,
            },
            {
                "name": "新荷花中药",
                "sector": "中药",
                "status": "等待聆讯",
                "ticker": None,
            },
            {"name": "米多多", "sector": "消费", "status": "等待聆讯", "ticker": None},
            {
                "name": "铂生卓越",
                "sector": "干细胞",
                "status": "等待聆讯",
                "ticker": None,
            },
        ],
    },
    "C": {
        "name": "C类 - 招股书失效（关注是否再次递表）",
        "companies": [
            {
                "name": "暖哇科技",
                "sector": "保险AI",
                "status": "招股书失效",
                "ticker": None,
            },
            {
                "name": "因明生物",
                "sector": "创新药",
                "status": "招股书失效",
                "ticker": None,
            },
            {
                "name": "成都国星宇航",
                "sector": "商业航天",
                "status": "招股书失效",
                "ticker": None,
            },
        ],
    },
    "D": {
        "name": "D类 - 已上市（监控二级市场表现）",
        "companies": [
            {
                "name": "精锋医疗",
                "sector": "医疗器械",
                "status": "已上市",
                "ticker": "02675.HK",
            },
            {
                "name": "天数智芯",
                "sector": "AI芯片",
                "status": "已上市",
                "ticker": None,
            },
            {
                "name": "海致科技",
                "sector": "科技",
                "status": "已上市",
                "ticker": None,
            },
        ],
    },
    "E": {
        "name": "E类 - 未递表/早期",
        "companies": [
            {
                "name": "普渡科技",
                "sector": "服务机器人",
                "status": "未递表",
                "ticker": None,
            },
            {
                "name": "康爱生物",
                "sector": "细胞免疫",
                "status": "未递表",
                "ticker": None,
            },
            {
                "name": "小视科技",
                "sector": "视觉AI",
                "status": "未递表",
                "ticker": None,
            },
        ],
    },
}

# 热门赛道关键词（用于识别新递表项目）
HOT_SECTORS = [
    "半导体",
    "AI",
    "人工智能",
    "生物医药",
    "机器人",
    "新能源",
    "消费",
    "芯片",
    "医疗",
    "科技",
]


def get_all_companies():
    """返回所有监控公司的扁平列表"""
    companies = []
    for category, data in WATCHLIST.items():
        for company in data["companies"]:
            companies.append({**company, "category": category})
    return companies


def get_companies_by_category(category):
    """按类别返回公司列表"""
    return WATCHLIST.get(category, {}).get("companies", [])


def get_listed_companies():
    """返回已上市公司列表"""
    return get_companies_by_category("D")


def get_pre_ipo_companies():
    """返回IPO前的公司列表（A、B类）"""
    companies = []
    for category in ["A", "B_active", "B_pending"]:
        companies.extend(get_companies_by_category(category))
    return companies
