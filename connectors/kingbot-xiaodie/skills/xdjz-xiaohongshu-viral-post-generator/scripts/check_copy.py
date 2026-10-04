#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书笔记文案合规检查。

检查项：
  1. 标题字数是否 <= 20
  2. 极限词 / 违禁词扫描（广告法 + 小红书社区规范）
  3. 站外导流词检测
  4. 话题标签数量

用法：
  python3 check_copy.py --title "标题" --body "正文"
  python3 check_copy.py --input notes.json
  python3 check_copy.py --input notes.json --json

notes.json 结构：
  {
    "plans": [
      {"name": "方案1 痛点共鸣", "title": "...", "body": "...", "tags": ["#a", "#b"]},
      {"name": "方案2 效果反差", "title": "...", "body": "...", "tags": ["#a"]}
    ]
  }

退出码：0 = 全部通过；1 = 存在高风险或中风险命中；2 = 参数错误
"""

import argparse
import json
import os
import sys
import re

TITLE_LIMIT = 20
TAG_MIN, TAG_MAX = 5, 8

# ---------- 词库 ----------
# high: 直接违反广告法 / 明确限流风险
# mid : 高风险表达，需改写或提供证据
# low : 弱营销感，建议优化

WORDS = {
    "极限词（广告法禁用）": {
        "level": "high",
        "items": [
            "最好", "最佳", "最强", "最优", "最便宜", "最贵", "最低价", "最高级", "销量第一",
            "第一名", "唯一", "独一无二", "绝无仅有", "前所未有", "史无前例",
            "顶级", "顶尖", "极致", "终极", "无敌", "完美无缺", "万能", "全效",
            "之王", "王牌", "王者", "冠军之选", "天花板", "封神",
            "百分百", "100%", "零风险", "绝对",
        ],
        "tip": "改成『更适合』『我个人偏爱』『在我用过的里面…』等相对表述",
    },
    "虚假权威 / 无法举证": {
        "level": "high",
        "items": [
            "国家级", "国家免检", "驰名商标", "权威认证", "官方指定", "人民大会堂",
            "特供", "专供", "军工品质", "专家推荐", "医院同款", "医美级",
        ],
        "tip": "删掉，或确认有实体证书后写成具体证件名称；没有就标待确认",
    },
    "医疗功效断言": {
        "level": "high",
        "items": [
            "治疗", "治愈", "疗效", "根治", "痊愈", "攻克",
            "抗癌", "抗炎", "消炎", "杀菌", "灭菌", "抑菌",
            "祛斑", "淡斑", "美白针", "溶脂", "减肥", "瘦身", "燃脂",
            "排毒", "抗衰老", "抗氧化", "生发", "丰胸",
        ],
        "tip": "改为个人使用感受：『我个人观察到…』『看起来…』，避免客观功效承诺",
    },
    "站外导流": {
        "level": "high",
        "items": [
            "加微信", "加v", "加vx", "加qq", "私聊", "私我", "私信我",
            "微信号", "vx号", "wx号", "qq群", "手机号联系",
            "淘宝搜", "某宝搜", "拼多多搜", "复制打开", "点击链接",
        ],
        "tip": "正文禁止出现联系方式与站外引导，一律删除",
    },
    "促销诱导 / 夸大": {
        "level": "mid",
        "items": [
            "全网最低", "全网首发", "史低价", "历史最低", "抄底价",
            "秒杀", "疯抢", "抢疯了", "亏本清仓", "老板跑路",
            "最后一天", "仅此一天", "错过再等一年", "错过拍大腿",
            "闭眼入", "闭眼买", "必买", "必入", "不买后悔", "人手必备",
            "黑科技", "逆天", "惊了", "炸了", "绝了配方",
        ],
        "tip": "换成事实陈述：『到手价 ¥XX』『这个价位我个人能接受』",
    },
    "自嗨 / 空话（建议替换）": {
        "level": "low",
        "items": [
            "我们精心打造", "倾力巨献", "匠心之作", "品质之选", "良心推荐",
            "值得信赖", "质量保证", "严格把控", "倾情奉献", "致力于",
        ],
        "tip": "换成具体事实：材质、参数、使用时长、具体场景",
    },
}

LEVEL_WEIGHT = {"high": 3, "mid": 2, "low": 1}
LEVEL_LABEL = {"high": "高风险", "mid": "中风险", "low": "低风险"}


def scan_text(text):
    """返回 [(level, category, word, count)]"""
    hits = []
    for category, conf in WORDS.items():
        for w in conf["items"]:
            kw = w.strip()
            if not kw:
                continue
            cnt = text.count(kw)
            if cnt:
                hits.append((conf["level"], category, kw, cnt))
    # 长词优先（避免『ingleton』式子串误判，这里主要是把更具体的词排前）
    hits.sort(key=lambda x: (-len(x[2]), x[0]))
    # 去除被更长词包含的重复项
    filtered = []
    for h in hits:
        w = h[2]
        if any(w != o[2] and w in o[2] for o in hits if LEVEL_WEIGHT[o[0]] >= LEVEL_WEIGHT[h[0]]):
            continue
        filtered.append(h)
    return filtered


def check_title(title):
    issues = []
    n = len(title)
    if n == 0:
        issues.append(("high", "标题为空"))
    elif n > TITLE_LIMIT:
        issues.append(("high", "标题 %d 字，超出 %d 字上限 %d 字" % (n, TITLE_LIMIT, n - TITLE_LIMIT)))
    return n, issues


def check_tags(tags):
    issues = []
    n = len(tags) if tags else 0
    if n == 0:
        issues.append(("mid", "未设置话题标签"))
    elif n < TAG_MIN:
        issues.append(("low", "话题标签 %d 个，建议 %d-%d 个" % (n, TAG_MIN, TAG_MAX)))
    elif n > TAG_MAX:
        issues.append(("low", "话题标签 %d 个，超过建议上限 %d 个" % (n, TAG_MAX)))
    return n, issues


def check_plan(plan):
    name = plan.get("name", "未命名方案")
    title = plan.get("title", "") or ""
    body = plan.get("body", "") or ""
    tags = plan.get("tags") or []

    tlen, t_issues = check_title(title)
    ntags, g_issues = check_tags(tags)

    full = title + "\n" + body
    # 标签不参与违禁词扫描（话题标签与正文规则不同）
    hits = scan_text(body)

    return {
        "name": name,
        "title": title,
        "title_len": tlen,
        "tag_count": ntags,
        "structural": t_issues + g_issues,
        "hits": [{"level": lv, "category": cat, "word": w, "count": c,
                  "tip": WORDS[cat]["tip"]} for lv, cat, w, c in hits],
    }


def render_text(results):
    lines = []
    worst = 0
    for r in results:
        lines.append("")
        lines.append("── %s ──" % r["name"])
        if r["structural"]:
            for lv, msg in r["structural"]:
                lines.append("  [%s] %s" % (LEVEL_LABEL.get(lv, lv), msg))
                worst = max(worst, LEVEL_WEIGHT.get(lv, 0))
        else:
            lines.append("  [通过] 标题 %d 字 / 标签 %d 个" % (r["title_len"], r["tag_count"]))

        if not r["hits"]:
            lines.append("  [通过] 未命中违禁词")
        else:
            seen_cat = set()
            for h in r["hits"]:
                lines.append("  [%s] 「%s」×%d  →  %s" %
                             (LEVEL_LABEL[h["level"]], h["word"], h["count"], h["category"]))
                worst = max(worst, LEVEL_WEIGHT[h["level"]])
                if h["category"] not in seen_cat:
                    seen_cat.add(h["category"])
                    lines.append("        建议：%s" % h["tip"])

    lines.append("")
    if worst >= 3:
        verdict = "发现高风险项，必须改写后重新发布"
    elif worst == 2:
        verdict = "发现中风险项，建议改写"
    elif worst == 1:
        verdict = "仅有低风险提示，可优化也可保留"
    else:
        verdict = "全部通过"
    lines.append("结论：%s" % verdict)
    return "\n".join(lines), worst


def main():
    ap = argparse.ArgumentParser(description="小红书笔记文案合规检查")
    ap.add_argument("--title", help="单条标题")
    ap.add_argument("--body", help="单条正文")
    ap.add_argument("--tags", help="逗号分隔的话题标签")
    ap.add_argument("--input", help="notes.json 路径（多方案批量）")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出")
    args = ap.parse_args()

    if args.input:
        if not os.path.isfile(args.input):
            print("错误：找不到文件 %s" % args.input, file=sys.stderr)
            return 2
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
        plans = data.get("plans", [])
        if not plans:
            print("错误：JSON 中没有 plans 字段", file=sys.stderr)
            return 2
        plans = [{"name": p.get("name", "方案%d" % (i + 1)),
                  "title": p.get("title", ""),
                  "body": p.get("body", ""),
                  "tags": p.get("tags", [])}
                 for i, p in enumerate(plans)]
        results = [check_plan(p) for p in plans]
    elif args.title or args.body:
        results = [check_plan({
            "name": "方案1",
            "title": args.title or "",
            "body": args.body or "",
            "tags": [t for t in (args.tags or "").split(",") if t.strip()],
        })]
    else:
        ap.print_help()
        return 2

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        text, worst = render_text(results)
        print(text)

    return 1 if worst >= 2 else 0


if __name__ == "__main__":
    sys.exit(main())
