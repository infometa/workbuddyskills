#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""腾讯校招求职诈骗轻量检测脚本。

用法：
    python scripts/fraud_checker.py "帖子或聊天文本"
    python scripts/fraud_checker.py "帖子或聊天文本" --account "账号名"

输出 JSON：risk_level / risk_type / decision_step / matched_signals / suggested_response。
"""
import argparse
import json
import re
import sys
from typing import Dict, List, Tuple


def configure_output_encoding() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


configure_output_encoding()

KEYWORDS = {
    "price": [
        "12500", "399", "299", "499", "599", "699", "799", "899", "999", "1280", "1980", "2980",
        "课程包", "报名费", "服务费", "押金", "定金", "退费", "退款", "不过退款", "学费", "辅导费", "培训费", "内推费", "打点费", "简历包装费",
    ],
    "promise": [
        "保offer", "保过", "保留用", "保转正", "保实习", "保上岸", "保进", "包过", "包内推", "包offer", "包录用", "100%", "百分百", "稳进", "稳过", "稳offer",
    ],
    "green_channel": [
        "内部名额", "内部资源", "内部通道", "免笔试", "免HR面", "免简历筛选", "绿色通道", "VIP通道",
    ],
    "referral": [
        "内部推荐", "内推码", "推荐码", "员工内推", "伯乐码",
    ],
    "training": [
        "1v1", "1对1", "陪跑", "训练营", "集训营", "实战营", "课程包", "上岸率", "在职导师辅导", "导师带", "课程辅导",
    ],
    "impersonation": [
        "前腾讯", "前HR", "在职导师", "鹅厂HR", "鹅厂内推", "员工内推", "导师推荐", "学姐带", "学长带",
    ],
    "redirect": [
        "私信", "加微信", "加vx", "加v", "+v", "vx", "VX", "wx", "WX", "微信号", "扫码", "二维码", "进群", "主页", "公众号回复", "评论1", "评论领", "领取", "扣扣", "QQ群",
    ],
    "brand": [
        "腾讯", "鹅厂", "CSIG", "CIG", "IEG", "WXG", "PCG", "TEG", "TME", "CDG", "腾讯音乐", "QQ音乐", "腾讯视频", "腾讯云", "微信",
    ],
    "intern_shape": [
        "远程实习", "线上实习", "日常实习", "暑期实习", "可转正", "100%转正", "免费实习", "0元实习", "0元", "免费",
    ],
    "audience": [
        "留学生", "海归", "海外", "研究生", "硕士", "本科生", "应届", "在读", "985", "211",
    ],
    "fake_warning": [
        "避雷", "踩坑", "被骗", "维权", "退费", "千万别", "退款", "套路", "曝光", "黑名单", "骗子",
    ],
}

ACCOUNT_KEYWORDS = ["实习", "求职", "招聘", "Hub", "Career", "留学", "海外", "接offer", "拿offer", "上岸", "避雷", "曝光", "反诈", "扒一扒"]

RESPONSES = {
    "paid": "这条信息可按求职诈骗处理。关键风险：涉及付费实习/内推/课程/服务费。腾讯校招和实习招聘全流程 0 收费，任何内推费、课程费、服务费、押金、退费、辅导费都不是官方流程。建议不要付款、不要继续添加私人微信/QQ群；如果已经付款，请保留聊天记录、转账记录，尽快通过对应平台举报。求职请只通过官方渠道：https://join.qq.com",
    "fake_warning": "这条信息高度疑似“骗子打骗子”的诈骗变体。它表面是在避雷、吐槽或分享被骗经历，但如果文末/评论区继续引导你私信、加微信、进群或领取资料，本质仍是在把你导向另一个付费机构。请记住：所有付费实习、付费内推、付费保过都不是腾讯官方流程。求职请回到官方渠道：https://join.qq.com",
    "promise_channel_training": "这条信息高度疑似求职诈骗。识别到保 offer、内部名额、绿色通道、免笔试、1v1 陪跑或训练营等风险信号。腾讯校招没有内部名额、保过、免笔试免面试机制，所有候选人都需要通过官方流程评估。正常官方内推/伯乐码不收费，也不能承诺跳过流程或保证结果。建议不要加私人联系方式、不要付费，先到 https://join.qq.com 核实岗位和流程。",
    "high": "这条信息存在较明显的求职诈骗特征。建议：1）不要添加私人微信/QQ/群聊；2）不要支付任何费用，即便对方说很便宜、可退或不过退款；3）到 https://join.qq.com 核对岗位是否真实存在；4）收到 offer 或 HR 联系时，以官方平台和官方邮箱为准。",
    "medium": "这条信息建议谨慎判断。目前没有足够证据直接判定为诈骗，但出现了引流、账号模板化或非官方渠道等风险信号。建议先通过 https://join.qq.com 或腾讯招聘官方账号核实，不要先交钱或提交敏感个人信息。",
    "low": "暂未发现明显诈骗特征，但仍建议遵守三条原则：腾讯校招/实习全流程 0 收费；投递与流程查询走 https://join.qq.com；不向陌生个人账号提供身份证、银行卡、验证码等敏感信息。",
}


def _find_keywords(text: str, category: str) -> List[str]:
    return [kw for kw in KEYWORDS[category] if kw and kw.lower() in text.lower()]


def _money_patterns(text: str) -> List[str]:
    patterns = [r"\b\d{2,5}\s*(?:元|块|rmb|RMB|¥)", r"¥\s*\d{2,5}"]
    found: List[str] = []
    for pat in patterns:
        found.extend(re.findall(pat, text, flags=re.IGNORECASE))
    return found


def _account_signals(account: str) -> List[str]:
    if not account:
        return []
    signals = [f"账号名含机构/引流词：{kw}" for kw in ACCOUNT_KEYWORDS if kw.lower() in account.lower()]
    if re.search(r"\((接offer版|实习版|留学版|求职版)\)", account, flags=re.IGNORECASE):
        signals.append("账号名命中括号模板")
    if re.search(r"^[A-Za-z]{3,8}在(澳洲|纽约|美国|香港|英国|加拿大|新加坡|日本|欧洲|韩国)[a-z]{0,4}$", account):
        signals.append("账号名疑似英文名+地点+随机后缀")
    return signals


def _signals(text: str) -> Dict[str, List[str]]:
    result = {name: _find_keywords(text, name) for name in KEYWORDS}
    money = _money_patterns(text)
    if money:
        result["price"] = list(dict.fromkeys(result["price"] + money))
    return result


def _signal_categories(signals: Dict[str, List[str]]) -> List[str]:
    return [k for k, v in signals.items() if v]


def check_fraud(text: str, account: str = "") -> Dict[str, object]:
    text = text or ""
    account = account or ""
    signals = _signals(text)
    account_hits = _account_signals(account)
    categories = set(_signal_categories(signals))

    matched = []
    for category, words in signals.items():
        if words:
            matched.append({"category": category, "keywords": words})
    for hit in account_hits:
        matched.append({"category": "account", "keywords": [hit]})

    if signals["price"]:
        return _result("red", "paid", "Step 0", matched, RESPONSES["paid"])

    if signals["fake_warning"] and signals["redirect"]:
        return _result("red", "fake_warning_redirect", "Step 3", matched, RESPONSES["fake_warning"])

    if signals["promise"] or signals["green_channel"] or signals["training"]:
        return _result("red", "promise_green_channel_training", "Step 2", matched, RESPONSES["promise_channel_training"])

    high_combo = {"impersonation", "redirect", "intern_shape", "audience", "brand"}
    combo_count = len(categories.intersection(high_combo))
    if combo_count >= 2 or account_hits:
        return _result("orange", "high_risk_combo", "Step 4/5", matched, RESPONSES["high"])

    if signals["redirect"] or signals["fake_warning"] or signals["intern_shape"]:
        return _result("yellow", "medium_risk_signal", "Step 4", matched, RESPONSES["medium"])

    return _result("green", "low_or_normal", "Step 6", matched, RESPONSES["low"])


def _result(level: str, risk_type: str, step: str, matched: List[Dict[str, List[str]]], response: str) -> Dict[str, object]:
    level_name = {
        "red": "🔴 极高风险",
        "orange": "🟠 高风险",
        "yellow": "🟡 中风险",
        "green": "🟢 低风险/暂未发现明显风险",
    }[level]
    return {
        "success": True,
        "risk_level": level_name,
        "risk_type": risk_type,
        "decision_step": step,
        "matched_signals": matched,
        "official_channel": "https://join.qq.com",
        "suggested_response": response,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="求职诈骗风险检测")
    parser.add_argument("text", help="待检测的帖子、聊天或账号描述文本")
    parser.add_argument("--account", default="", help="可选：账号名/昵称")
    parser.add_argument("--compact", action="store_true", help="输出紧凑 JSON")
    args = parser.parse_args()
    print(json.dumps(check_fraud(args.text, account=args.account), ensure_ascii=False, indent=None if args.compact else 2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
