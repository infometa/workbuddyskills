#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sensitive_filter.py
career-qa 进外部问询服务之前的硬规则过滤器。

规则源：references/sensitive-patterns.md
原则：纯关键词匹配，不依赖 LLM，避免 prompt 注入绕过。

调用：
    from sensitive_filter import filter_query
    refusal = filter_query("现在有多少人在活水流程中？")
    if refusal:
        # 拒答，不发外部问询服务
        return refusal
    else:
        # 继续走路由后的外部问询服务
        ...
"""
from typing import Optional

LABOR_PREGNANCY_BOUNDARY_REPLY = """这件事听起来让你很有压力，先别急着把责任都放到自己身上。

我不能替你做法律判断、流程建议，也不评价具体角色或团队责任。如果你只是想了解资料，可以看公开制度或法律法规原文；我这里不做适用判断。

职业发展这部分，我可以陪你先把能控制的事拆开：身体和精力、沟通边界、节奏安排、后续选择。你现在最担心的是哪一块？"""

# 10 类敏感规则（与 skills/career-qa/references/sensitive-patterns.md 同步）
SENSITIVE_RULES = [
    {
        "name": "类别B0 薪酬零讨论",
        "single_match": ["工资", "薪资", "薪酬", "月薪", "年薪", "奖金", "年终", "年终奖",
                          "调薪", "加薪", "涨薪", "涨幅", "薪资涨", "薪酬涨", "package",
                          "offer 金额", "offer金额", "股票", "RSU", "给钱", "收入", "回报"],
        "and_of": [],
        "reply": "我不太方便回答这类问题。",
    },
    {
        "name": "类别A 人员统计",
        "any_of": ["多少人", "几个人", "几人", "占比", "比例", "总数", "人数",
                   "名单", "谁在", "哪些人", "列表", "都有谁"],
        "and_of": ["活水", "转岗", "离职", "招聘", "校招", "社招",
                   "入职", "岗位", "部门", "HR", "匿名池"],
        "reply": "我不太方便回答这类问题。",
    },
    {
        "name": "类别B 个人薪酬",
        "any_of": ["多少", "范围", "标准", "怎么算", "区间", "多高", "多低"],
        "and_of": ["工资", "薪资", "薪酬", "月薪", "年薪", "奖金",
                   "调薪", "package", "offer 金额", "offer金额",
                   "年终奖", "加薪", "涨薪"],
        "reply": "我不太方便回答这类问题。",
    },
    {
        "name": "类别C 他人隐私",
        "any_of": ["他", "她", "TA", "ta", "某人", "某某",
                   "@", "其他人", "别人"],
        "and_of": ["工资", "薪资", "职级", "评估", "自评",
                   "简历", "OKR", "KR"],
        "reply": "我不太方便回答这类问题。",
    },
    {
        "name": "类别E HR 决策",
        "any_of": ["该不该", "能不能", "要不要", "值不值", "适不适合",
                   "好不好", "接不接", "走不走", "去不去"],
        "and_of": ["转", "走", "接", "offer", "跳槽",
                   "离职", "调岗", "转岗", "活水", "申请"],
        "reply": "我不太方便回答这类问题。",
    },
    {
        "name": "类别F 评级 / 打分预测",
        "single_match": ["能落几", "能评几", "落几级", "落几档",
                          "能拿几分", "评几分", "能给几分",
                          "我大概是几", "我能拿到几"],
        "and_of": [],
        "reply": "我不太方便回答这类问题。",
    },
    {
        "name": "类别G 员工梯队 / 排名 / 同事对比",
        "any_of": ["排名", "排第", "梯队", "头部", "中部", "尾部",
                   "同期", "同 level", "同level", "同职级",
                   "比我", "对比", "横比", "赛马",
                   "明星员工", "末位", "淘汰", "TOP", "top 几",
                   "高潜", "梯队池"],
        "and_of": ["我", "你", "ta", "TA", "他", "她", "同事",
                   "员工", "RTX", "部门", "BG", "组里", "团队"],
        "reply": "我不太方便回答这类问题。",
    },
    {
        "name": "类别H 薪酬延伸（公司/岗位/BG 层面）",
        "any_of": ["职级", "level", "T7", "T8", "T9", "T10", "T11", "T12",
                   "BG", "业务群", "部门", "岗位", "团队",
                   "CSIG", "TEG", "IEG", "PCG", "WXG", "CDG", "FiT", "S1", "S2",
                   "腾讯", "司内", "公司", "外面", "业内",
                   "这条线", "这个方向"],
        "and_of": ["薪资", "薪酬", "工资", "年薪", "月薪", "package",
                   "年终", "年终奖", "奖金", "股票", "RSU",
                   "给钱", "给得", "给的", "大方", "抠门", "涨薪", "调薪", "涨幅",
                   "钱", "收入", "回报", "几个月"],
        "reply": "我不太方便回答这类问题。",
    },
    {
        "name": "类别I 劳动/孕产/合规争议",
        "single_match": ["劳动法", "仲裁", "起诉", "取证", "维权", "违法", "合法吗", "合不合法",
                          "投诉", "举报", "赔偿", "裁员赔偿", "强制加班", "加班费",
                          "怀孕", "孕期", "产检", "哺乳期", "怀孕歧视"],
        "and_of": [],
        "reply": LABOR_PREGNANCY_BOUNDARY_REPLY,
    },
    {
        "name": "类别I-2 产假争议语境",
        "any_of": ["产假"],
        "and_of": ["不给", "怎么办", "不敢", "leader", "领导", "歧视", "辞退", "调岗", "降薪", "必须", "强制"],
        "reply": LABOR_PREGNANCY_BOUNDARY_REPLY,
    },
]


def filter_query(query: str) -> Optional[str]:
    """
    返回 None = 通过，可继续调路由后的外部问询服务
    返回 str = 命中规则后的拒答话术，应直接返回给用户
    """
    if not query or not query.strip():
        return None
    for rule in SENSITIVE_RULES:
        # 两种匹配模式：
        # 1) any_of + and_of：必须同时命中两类
        # 2) single_match：任一关键词命中即拦（用于成句的固定表达）
        if rule.get("single_match"):
            if any(k in query for k in rule["single_match"]):
                return rule["reply"]
        else:
            hit_any = any(k in query for k in rule["any_of"])
            hit_and = any(k in query for k in rule["and_of"])
            if hit_any and hit_and:
                return rule["reply"]
    return None


# 自测
if __name__ == "__main__":
    cases = [
        ("现在有多少人在活水流程中？", True),  # A 拦
        ("校招招了几个人？",            True),  # A 拦
        ("我们部门有谁在转岗？",         True),  # A 拦
        ("T7 工资范围是多少？",         True),  # B 拦
        ("活水可以涨薪吗？",             True),  # B0 拦：薪酬零讨论
        ("活水后会调薪吗，能调多少？",   True),  # B0/B 拦
        ("张三的工资是多少？",          True),  # B 拦
        ("他的简历能给我看看吗？",       True),  # C 拦
        ("我现在该不该走活水？",        True),  # E 拦
        ("这个 offer 我接不接？",      True),  # E 拦
        ("我这个表现大概能落几？",      True),  # F 拦
        ("我在我们部门排名第几？",      True),  # G 拦（排名）
        ("跟我同期的人都升到 T9 了吗？", True),  # G 拦（同期对比）
        ("我这画像在司内属于头部吗？",   True),  # G 拦（梯队）
        ("CSIG 给钱大方吗？",          True),  # H 拦（BG 薪酬）
        ("T8 在腾讯一般年终奖几个月？",  True),  # H 拦（职级薪酬）
        ("我怀孕了不敢告诉Leader，你说我该怎么办？", True),  # I 拦
        ("加班消息不回违法吗？",        True),  # I 拦
        ("能不能仲裁？",                True),  # I 拦
        ("产假多少天？",                False),  # 纯规则问题可通过
        ("产假不给怎么办？",            True),  # I-2 拦
        ("活水有试用期吗？",           False),  # 通过
        ("什么是活水？",               False),  # 通过
        ("活水流程怎么走？",            False),  # 通过
        ("怎么申请活水？",              False),  # 通过
    ]
    for q, should_block in cases:
        result = filter_query(q)
        actually_blocked = result is not None
        marker = "✅" if actually_blocked == should_block else "❌"
        status = "拦截" if actually_blocked else "通过"
        print(f"{marker} [{status}] {q}")
        if actually_blocked:
            print(f"   → {result}")
