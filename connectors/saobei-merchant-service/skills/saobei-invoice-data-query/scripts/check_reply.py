#!/usr/bin/env python3
"""扫呗数电票数据查询助手 —— 商户侧回复草稿自检脚本。

用法:
    python3 check_reply.py <reply.txt> [更多文件...]

读取本地文本文件（对话回复草稿），按本技能的输出规则做静态校验：
  1. Markdown 符号禁令（禁止 ** 加粗、* 斜体、__ 下划线标记）
  2. 负数金额禁令（接口红票金额为负，展示时须取绝对值）
  3. 术语硬约束（蓝票/红票/红冲/有效开票金额统一用词）
  4. 金额数值一致性（有效开票金额 = |蓝票| − |红票|）
  5. 发票号码完整性（禁止省略形式、样例号码）
  6. 下载入口格式（图标与文字同行、无重复文案）
  7. 展示顺序（开票数量 -> 开票金额 -> 有效开票金额 -> 蓝票 -> 红票）
  8. 分页去重（相同发票号码重复出现）
  9. 概念混淆（开票状态/开票来源/发票类型三者不可混用）
  10. 孤立emoji 行
  11. 样例占位符残留
  12. 技术过程泄露（接口名、参数名、内部字段名等技术标识）
  13. **降级交付校验**：声明取不到数据时，不得同时出现金额/笔数，
      也不得出现"没有开票"或"未开通数电票"的断言；
      引导授权时必须点名连接器展示名「扫呗商户服务」
  14. **输出风格校验**：拦截主观解读、猜测性归因与结尾主动引导问句，
      只保留数据与结论（2026-10-21 用户反馈）

设计约束:
  - 仅使用 Python 标准库（argparse / re / sys / pathlib）
  - 只读本地文本，不发起任何网络请求
  - 不写入、不修改、不删除任何文件
  - 不依赖任何第三方包，不执行任何外部命令
  - 一次报出全部问题（不做遇错即停），便于一次性修完

退出码:
  0 = 全部通过（可能含 WARN）
  1 = 存在 ERROR 级问题
  2 = 用法错误 / 文件不可读
"""

import argparse
import re
import sys
from pathlib import Path

# 样例发票号码前缀（真实发票号码长度通常为 20 位，样例统一使用易识别的连续序号）
SAMPLE_TICKET_PREFIX = "2642720000000000"

# 金额解析：匹配 ¥12.00 / 12.00元 / ¥12 / 12 元 等常见形态
AMOUNT_RE = re.compile(r"(?:¥\s*(\d+(?:\.\d+)?)|(\d+(?:\.\d+)?)\s*元)")

# 发票号码：15-24 位纯数字，允许被省略号截断
TICKET_FULL_RE = re.compile(r"(?<!\d)(\d{15,24})(?!\d)")
TICKET_TRUNCATED_RE = re.compile(r"(?:…{2,}|\.{3,}|。{3,})\s*\d{3,}|\d{3,}\s*(?:…{2,}|\.{3,})")

# 孤立 emoji 行：整行去除空白后，仅由 emoji / 符号 / 变体选择符组成
EMOJI_CHARS = (
    "\\U0001F000-\\U0001FAFF"  # 各类 emoji 与符号
    "☀-➿"          # 常用符号区
    "⬀-⯿"          # 补充符号区
    "️‍"    # 变体选择符与零宽连接符
    "\\U0001F1E6-\\U0001F1FF"  # 国旗区域指示符
    r"\s"
)
EMOJI_ONLY_LINE_RE = re.compile("^[" + EMOJI_CHARS + "]+$")

# 占位符残留
PLACEHOLDER_RE = re.compile(
    r"(TODO|TBD|FIXME|XXX|待补充|占位符|merchant@example\.com)",
    re.IGNORECASE,
)

# 不允许出现在商户侧回复中的技术表述
# 用通用模式覆盖「协议名 / 部署标识 / 网关」这类内部标识，不点名具体历史值。
FORBIDDEN_TECH_RE = re.compile(
    r"(mcp|sys\d{3,}|app_\d+|[-_]gateway|gateway"
    r"|接口异常|查询通道|服务异常|系统(没有|未)返回|调用失败|"
    r"getAllInvoiceStatistics|getInvoiceList|getInvoiceDetail|"
    r"getStoreList|getSwitchByType|getCrownAuthInfo|blueInvoice|confirmInvoice|"
    r"query_type|store_id|invoice_id|return_code|invoice_scene|issue_status|"
    r"total_fee|total_amount|normal_amount|refund_amount)",
    re.IGNORECASE,
)

# 主观解读 / 归因 / 主动引导句（2026-10-21 用户反馈：这类"废话"一律不要）
SUBJECTIVE_RE = re.compile(
    r"(几点观察|值得注意|可以看出|能够看出|说明这|说明本|整体呈现|"
    r"值得注意的是|从数据(来看|上看)|属于正常|看起来像|像是同一批|"
    r"集中操作|可能是|大概是|推测|疑似|"
    r"需要我(帮|来)|要不要我|需要的话我|可以继续帮|跟我说一声|"
    r"随时可以|为你服务|如果还需要|如有需要)",
)

# 收尾式主动引导（以问号结尾且含邀请语气）
PROACTIVE_INVITE_RE = re.compile(
    r"(需要|要不要|是否需要|需不需要)[^。！？\n]{0,20}[?？]|"
    r"(告诉我|告我|说一声|喊我)[^。！？\n]{0,20}[?？]",
)

# 术语禁用词 -> 建议用词
TERM_RULES = [
    (r"冲红", "应使用「红冲」"),
    (r"红冲票", "应使用「红票（红冲）」"),
    (r"正常票", "应使用「蓝票（正常开具）」"),
    (r"(?<!红票冲减后的)(?<!税后)净额", "应使用「有效开票金额」"),
    (r"实际开票金额", "应使用「开票金额」或「有效开票金额」"),
    (r"暂无符合条件的开票记录", "应使用「XX 没有开票哦～」的自然表达"),
    (r"查询不到数据", "应直接说明该时间范围内没有开票"),
    (r"暂无数据", "应使用「XX 没有开票哦～」的自然表达"),
]

# 降级交付标志：出现这些表述说明本次未取到真实数据
DEGRADED_MARKERS_RE = re.compile(
    r"(暂时(取不到|拿不到|无法)|无法(查询|获取|取到)|"
    r"需要先完成.{0,20}授权|未授权|未启用|授权完成后|暂时查不到)"
)

# 声明取不到数据时，禁止出现的"事实断言"与数字
DEGRADED_FORBIDDEN_RE = re.compile(
    r"(没有开票|未开通数电票|没有开通数电票|开票数量[:：]|开票金额[:：])"
)

# 降级时必须给出的确定性信息
DEGRADED_REQUIRED_RE = re.compile(r"(查询时间[:：]|查询范围[:：])")

# 降级话术中引导用户授权时，必须点名「扫呗商户服务」（面板展示名）
DEGRADED_NEED_AUTH_HINT_RE = re.compile(r"(授权|连接器)")
DEGRADED_AUTH_NAME_RE = re.compile(r"扫呗商户服务")


class Issue:
    __slots__ = ("level", "code", "line", "message")

    def __init__(self, level, code, line, message):
        self.level = level
        self.code = code
        self.line = line
        self.message = message


def parse_amounts(line):
    """从一行文本中解析出所有金额，返回 float 列表。"""
    out = []
    for m in AMOUNT_RE.finditer(line):
        raw = m.group(1) or m.group(2)
        try:
            out.append(float(raw))
        except ValueError:
            continue
    return out


def check_markdown(lines, issues):
    for idx, line in enumerate(lines, 1):
        if "**" in line:
            issues.append(Issue("ERROR", "MD-BOLD", idx, "使用了 ** 加粗，商户端渲染会异常"))
        if re.search(r"(?<!\*)\*(?!\*)", line):
            issues.append(Issue("ERROR", "MD-ITALIC", idx, "使用了 * 斜体，商户端渲染会异常"))
        if "__" in line:
            issues.append(Issue("ERROR", "MD-UNDERLINE", idx, "使用了 __ 下划线标记，商户端渲染会异常"))


def check_negative_amount(lines, issues):
    """禁止负数金额直接展示给商户。

    接口中已红冲记录的金额为负数（如 total_fee = -1），
    展示时必须取绝对值，否则会出现「¥-6.00」这种商户看不懂的写法。
    """
    neg_re = re.compile(r"¥\s*-\s*\d")
    for idx, line in enumerate(lines, 1):
        for m in neg_re.finditer(line):
            issues.append(
                Issue(
                    "ERROR",
                    "NEG-AMOUNT",
                    idx,
                    f"金额为负数「{m.group(0)}」，展示时应取绝对值",
                )
            )


def check_terms(lines, issues):
    for idx, line in enumerate(lines, 1):
        for pattern, advice in TERM_RULES:
            for m in re.finditer(pattern, line):
                issues.append(
                    Issue("ERROR", "TERM", idx, f"「{m.group(0)}」用词不合规：{advice}")
                )


def check_amount_unit(lines, issues):
    """启发式检查：金额疑似未做「分 → 元」换算。

    接口所有金额字段单位是分，展示前必须 ÷100。历史上出现过把
    total_fee=600 直接显示成「¥600.00」（实际应为 ¥6.00）的事故。

    判定启发式：汇总里所有金额都是 100 的整数倍（形如 ¥600.00、¥1200.00），
    且存在 ≥100 的取值时，疑似把分当成了元。

    这是 WARN 而非 ERROR：确实存在真实金额恰为整百元的合法场景，
    确认无误后可忽略，但必须显式核对。

    注意：本启发式无法覆盖全部换算错误（例如把 601 分显示成 ¥601.00），
    确定性保障依赖 check_amount_against_reference()。
    """
    summary_amounts = []
    for line in lines:
        if any(k in line for k in ("开票金额", "有效开票金额", "蓝票", "红票")):
            summary_amounts.extend(parse_amounts(line))

    if not summary_amounts:
        return

    # 全部金额都必须是 100 的整数倍才触发，避免误伤含角分的正常金额
    if not all(abs(a) % 100 == 0 for a in summary_amounts):
        return

    if not any(abs(a) >= 100 for a in summary_amounts):
        return

    shown = "、".join(f"¥{a:.2f}" for a in summary_amounts)
    issues.append(
        Issue(
            "WARN",
            "AMT-UNIT",
            0,
            f"金额 {shown} 全为 100 的整数倍，疑似未做「分 → 元」换算。"
            f"接口金额单位是分，展示前必须 ÷100。"
            f"请用 scripts/calc_amount.py 复核（确认确实为元则可忽略）",
        )
    )


def _parse_reference(text):
    """从 calc_amount.py 的输出或草稿中解析出标准的汇总数值。

    返回 dict，键为：开票数量 / 开票金额 / 有效开票金额 / 蓝票金额 / 红票金额
    """
    ref = {}
    for line in text.splitlines():
        m = re.search(r"(开票数量|开票金额|有效开票金额|蓝票（正常开具）|红票（红冲）)"
                      r"[:：]\s*(.+)", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2)
        amts = parse_amounts(val)
        if key == "开票数量":
            c = re.search(r"(\d+)\s*张", val)
            if c:
                ref["开票数量"] = float(c.group(1))
        elif key == "开票金额" and "有效" not in key:
            if amts:
                ref["开票金额"] = amts[0]
        elif key == "有效开票金额":
            if amts:
                ref["有效开票金额"] = amts[0]
        elif key == "蓝票（正常开具）":
            if amts:
                ref["蓝票金额"] = amts[0]
            c = re.search(r"(\d+)\s*张", val)
            if c:
                ref["蓝票数量"] = float(c.group(1))
        elif key == "红票（红冲）":
            if amts:
                ref["红票金额"] = amts[0]
            c = re.search(r"(\d+)\s*张", val)
            if c:
                ref["红票数量"] = float(c.group(1))
    return ref


def check_amount_against_reference(lines, issues, reference_text):
    """确定性校验：草稿中的汇总数值必须与 calc_amount.py 算出的权威值一致。

    这条检查专门拦截「分 → 元」换算错误：换算错时金额会整体差 100 倍，
    任何单看草稿都发现不了，只有拿权威基准比对才能抓住。

    reference_text 为 calc_amount.py 的输出内容。
    """
    ref = _parse_reference(reference_text)
    if not ref:
        issues.append(
            Issue(
                "ERROR",
                "REF-EMPTY",
                0,
                "基准文件里没解析出任何汇总数值，无法校验金额一致性",
            )
        )
        return

    draft = _parse_reference("\n".join(lines))
    if not draft:
        return  # 草稿不是汇总类型，跳过

    for field, label in (
        ("开票数量", "开票数量"),
        ("开票金额", "开票金额"),
        ("有效开票金额", "有效开票金额"),
        ("蓝票金额", "蓝票金额"),
        ("红票金额", "红票金额"),
    ):
        if field not in ref:
            continue
        if field not in draft:
            issues.append(
                Issue(
                    "ERROR",
                    "REF-MISSING",
                    0,
                    f"草稿缺少「{label}」，无法与基准比对",
                )
            )
            continue
        if abs(round(draft[field], 2) - round(ref[field], 2)) > 0.005:
            ratio = ""
            if ref[field]:
                ratio = f"（草稿是基准的 {draft[field] / ref[field]:.0f} 倍）"
            issues.append(
                Issue(
                    "ERROR",
                    "AMT-DIVERGE",
                    0,
                    f"「{label}」与基准不一致：草稿 {draft[field]:.2f}，"
                    f"基准 {ref[field]:.2f}{ratio}。"
                    f"最常见原因是把「分」当成「元」，请用 scripts/calc_amount.py 重新取值",
                )
            )


def check_amount_consistency(lines, issues):
    """校验数值一致性。

    口径：
      有效开票金额 = |蓝票金额| − |红票金额|

    注意：笔数用「N张」解析，金额用 ¥/元 解析，两者独立。
    """
    normal = refund = effective = total = None
    for idx, line in enumerate(lines, 1):
        amounts = parse_amounts(line)
        if not amounts:
            continue
        value = amounts[0]

        # 「蓝票」需先于「红票」判断
        if "蓝票" in line:
            normal = (idx, value)
        elif "红票" in line:
            refund = (idx, value)
        elif "有效开票金额" in line:
            effective = (idx, value)
        elif "开票金额" in line:
            total = (idx, value)

    looks_like_summary = any(v is not None for v in (normal, refund, effective, total))
    if not looks_like_summary:
        return

    missing = [
        name
        for name, v in (
            ("蓝票金额", normal),
            ("红票金额", refund),
            ("有效开票金额", effective),
            ("开票金额", total),
        )
        if v is None
    ]
    if missing:
        issues.append(
            Issue(
                "WARN",
                "AMT-INCOMPLETE",
                0,
                "汇总输出缺少：" + "、".join(missing) + "，未能校验数值一致性",
            )
        )
        return

    # 有效开票金额 = |蓝票| − |红票|（红票可能返回负数，故取绝对值）
    expected_effective = round(abs(normal[1]) - abs(refund[1]), 2)
    if abs(round(effective[1], 2) - expected_effective) > 0.005:
        issues.append(
            Issue(
                "ERROR",
                "AMT-MISMATCH",
                effective[0],
                f"有效开票金额数值不一致：|{normal[1]:.2f}| − |{refund[1]:.2f}| "
                f"= {expected_effective:.2f}，但写的是 {effective[1]:.2f}。"
                f"红票金额取绝对值后再相减",
            )
        )

    # 开票金额 = |蓝票| + |红票|（WARN，因接口 total_amount 口径需确认）
    expected_total = round(abs(normal[1]) + abs(refund[1]), 2)
    if abs(round(total[1], 2) - expected_total) > 0.005:
        issues.append(
            Issue(
                "WARN",
                "AMT-TOTAL",
                total[0],
                f"开票金额 {total[1]:.2f} 与 |{normal[1]:.2f}| + |{refund[1]:.2f}| "
                f"= {expected_total:.2f} 不一致，请确认接口 total_amount 口径",
            )
        )


def check_display_order(lines, issues):
    """校验固定展示顺序：开票数量 -> 开票金额 -> 有效开票金额 -> 蓝票 -> 红票。"""
    order = ["开票数量", "开票金额", "有效开票金额", "蓝票", "红票"]
    positions = {}

    for idx, line in enumerate(lines, 1):
        for name in order:
            if name in line and name not in positions:
                positions[name] = idx

    # 只有出现「开票数量：N张」这类汇总意图时才校验顺序；
    # 纯明细、单张反查、降级交付本就没有汇总字段，不应误报
    has_summary_intent = any(
        re.search(r"开票数量[:：]\s*\d+\s*张", line) for line in lines
    )
    if not has_summary_intent:
        return

    missing = [n for n in order if n not in positions]
    if missing:
        issues.append(
            Issue("WARN", "ORD-MISSING", 0, "汇总输出缺少字段：" + "、".join(missing))
        )
        return

    # 「开票数量」与其它字段无包含关系，按首次出现行号排序即可
    seq = [(positions[n], n) for n in order]
    seq_sorted = sorted(seq)
    if [n for _, n in seq_sorted] != order:
        actual = " → ".join(n for _, n in seq_sorted)
        issues.append(
            Issue(
                "ERROR",
                "ORD-WRONG",
                seq_sorted[0][0],
                f"展示顺序不符，应为「开票数量 → 开票金额 → 开票成功 → 开票中 → 开票失败」，"
                f"实际为「{actual}」",
            )
        )


def check_degraded_delivery(lines, issues):
    """降级交付校验。

    当回复声明"数据取不到"（连接器不可用 / 未授权）时：
      - 禁止同时给出金额/笔数（会构成编造）
      - 禁止断言"没有开票"或"未开通数电票"（无数据时下不了这个结论）
      - 必须给出查询时间与查询范围（这两项不依赖联网）

    注意：「某字段查不到」这类如实澄清不属于降级交付，不强制要求时间范围。
    """
    full_text = "\n".join(lines)
    if not DEGRADED_MARKERS_RE.search(full_text):
        return

    # 仅在真正涉及"取不到开票数据"时才要求范围信息。
    # 「门店这块查不到」属于字段不支持的澄清，不在此列。
    is_data_unavailable = re.search(
        r"(暂时(取不到|拿不到|无法)|无法(查询|获取|取到)|"
        r"需要先完成.{0,20}授权|未授权|未启用|授权完成后)",
        full_text,
    )
    if not is_data_unavailable:
        return

    for idx, line in enumerate(lines, 1):
        for m in DEGRADED_FORBIDDEN_RE.finditer(line):
            issues.append(
                Issue(
                    "ERROR",
                    "DEGRADED-FABRICATE",
                    idx,
                    f"已声明取不到数据，却又出现事实断言或数字「{m.group(0)}」，"
                    f"这会构成编造。无数据时不得断言开票结果",
                )
            )

        # 降级时任何带 ¥ 的金额都可疑
        if "¥" in line and not DEGRADED_REQUIRED_RE.search(line):
            for m in AMOUNT_RE.finditer(line):
                issues.append(
                    Issue(
                        "ERROR",
                        "DEGRADED-AMOUNT",
                        idx,
                        f"已声明取不到数据，却出现金额「{m.group(0)}」",
                    )
                )

    if not DEGRADED_REQUIRED_RE.search(full_text):
        issues.append(
            Issue(
                "ERROR",
                "DEGRADED-NO-SCOPE",
                0,
                "降级交付缺少「查询时间」或「查询范围」，"
                "这两项不依赖联网，必须照常给出",
            )
        )

    # 引导授权时必须点名「扫呗商户服务」，否则商户在面板里找不到
    if DEGRADED_NEED_AUTH_HINT_RE.search(full_text) and not DEGRADED_AUTH_NAME_RE.search(
        full_text
    ):
        issues.append(
            Issue(
                "ERROR",
                "DEGRADED-NO-CONNECTOR-NAME",
                0,
                "引导授权时必须写明连接器展示名「扫呗商户服务」，"
                "商户在连接器面板中按此名称查找",
            )
        )


def check_ticket_numbers(lines, issues):
    seen = {}

    for idx, line in enumerate(lines, 1):
        for m in TICKET_TRUNCATED_RE.finditer(line):
            issues.append(
                Issue(
                    "ERROR",
                    "TICKET-TRUNC",
                    idx,
                    f"发票号码被省略：「{m.group(0)}」，必须完整展示",
                )
            )
        for m in TICKET_FULL_RE.finditer(line):
            number = m.group(1)
            if number.startswith(SAMPLE_TICKET_PREFIX):
                issues.append(
                    Issue(
                        "WARN",
                        "TICKET-SAMPLE",
                        idx,
                        f"发票号码 {number} 为样例值，输出前需替换为接口实际返回值",
                    )
                )
            seen.setdefault(number, []).append(idx)

    for number, positions in seen.items():
        if len(positions) > 1:
            issues.append(
                Issue(
                    "ERROR",
                    "TICKET-DUP",
                    positions[1],
                    f"发票号码 {number} 在第 {positions} 行重复出现，"
                    f"分页展示需按 invoice_id 去重",
                )
            )


def check_concept_confusion(lines, issues):
    """防止概念混淆。

    接口中三个维度相互独立，商户侧不可混用：
      issue_status   开票状态（开票成功/中/失败/已冲红/冲红中/冲红失败）
      invoice_scene  开票来源（自定义/订单/物料码/扫码）
      invoice_type   发票类型（蓝票/红票）
    典型错误是把「开票状态：已冲红」当成「发票类型：红票」来表述，
    或把「订单开票」写成票种。
    """
    # 「发票类型」行里出现开票状态枚举 → 混淆
    type_patterns = [
        (r"发票类型[:：].*(开票成功|开票中|开票失败)", "发票类型只应是蓝票（正常开具）/ 红票（红冲），不要写开票状态"),
        (r"发票类型[:：].*(自定义开票|订单开票|物料码开票|扫码开票)", "发票类型只应是蓝票/红票，不要写开票来源"),
        (r"开票来源[:：].*(蓝票|红票)", "开票来源只应是自定义/订单/物料码/扫码，不要写票种"),
        (r"开票来源[:：].*(开票成功|开票中|开票失败|已冲红)", "开票来源只应是自定义/订单/物料码/扫码，不要写开票状态"),
        (r"开票状态[:：].*(蓝票|红票)", "开票状态是开具进度，不是票种"),
    ]
    for idx, line in enumerate(lines, 1):
        for pattern, advice in type_patterns:
            for m in re.finditer(pattern, line):
                issues.append(
                    Issue("ERROR", "CONFUSE", idx, f"「{m.group(0)}」：{advice}")
                )


def check_download_entry(lines, issues):
    """校验下载入口格式。

    invoice_url 可能为空字符串，此时不得展示下载入口。
    """
    has_download = False

    for idx, line in enumerate(lines, 1):
        if "📥" not in line:
            continue
        has_download = True
        stripped = line.strip()
        if stripped == "📥" or re.match(r"^📥\s*[\U0001F000-\U0001FAFF\s]*$", stripped):
            issues.append(
                Issue(
                    "ERROR",
                    "DL-ALONE",
                    idx,
                    "下载图标单独成行，必须与文字同行（如「📥 下载发票 PDF」）",
                )
            )
        elif not re.search(r"📥\s*\S", stripped):
            issues.append(
                Issue("ERROR", "DL-FORMAT", idx, "下载入口格式应为「📥 下载发票 PDF」")
            )

    if has_download:
        full_text = "\n".join(lines)
        if re.search(r"PDF\s*下载发票|PDF下载发票|下载发票\s*PDF\s*下载", full_text):
            for idx, line in enumerate(lines, 1):
                if re.search(r"PDF\s*下载发票|PDF下载发票|下载发票\s*PDF\s*下载", line):
                    issues.append(
                        Issue("ERROR", "DL-DUP", idx, "下载文案重复，统一使用「📥 下载发票 PDF」")
                    )


def check_emoji_only_lines(lines, issues):
    for idx, line in enumerate(lines, 1):
        if not line.strip():
            continue
        if EMOJI_ONLY_LINE_RE.match(line.strip()):
            issues.append(Issue("WARN", "EMOJI-LONE", idx, "孤立 emoji 行，emoji 应与文字同行"))


def check_placeholders(lines, issues):
    for idx, line in enumerate(lines, 1):
        for m in PLACEHOLDER_RE.finditer(line):
            issues.append(
                Issue("ERROR", "PLACEHOLDER", idx, f"残留占位符：「{m.group(0)}」，需替换为真实内容")
            )


def check_tech_exposure(lines, issues):
    for idx, line in enumerate(lines, 1):
        for m in FORBIDDEN_TECH_RE.finditer(line):
            issues.append(
                Issue(
                    "ERROR",
                    "TECH-LEAK",
                    idx,
                    f"回复中出现技术表述「{m.group(0)}」，商户侧只输出业务结果",
                )
            )


def check_style_tone(lines, issues):
    """2026-10-21 用户反馈：只给数据和结论，不写解读、归因与主动引导句。"""
    for idx, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped:
            continue
        for m in SUBJECTIVE_RE.finditer(stripped):
            issues.append(
                Issue(
                    "WARN",
                    "STYLE-SUBJECTIVE",
                    idx,
                    f"疑似主观解读或主动引导「{m.group(0)}」，"
                    f"只保留数据与结论，删除这类句子",
                )
            )
        if PROACTIVE_INVITE_RE.search(stripped):
            issues.append(
                Issue(
                    "WARN",
                    "STYLE-INVITE",
                    idx,
                    "结尾出现主动扩展引导问句，除非用户主动提出后续需求，否则删除",
                )
            )


def check_file(path, issues, reference_text=None):
    """读取并校验单个文件，追加结果到 issues。返回是否存在 ERROR。"""
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        issues.append(Issue("ERROR", "IO-ENCODING", 0, f"{path} 不是 UTF-8 编码"))
        return True
    except OSError as exc:
        issues.append(Issue("ERROR", "IO-READ", 0, f"无法读取 {path}：{exc}"))
        return True

    lines = text.splitlines()

    check_markdown(lines, issues)
    check_negative_amount(lines, issues)
    check_terms(lines, issues)
    check_amount_consistency(lines, issues)
    check_amount_unit(lines, issues)
    if reference_text is not None:
        check_amount_against_reference(lines, issues, reference_text)
    check_display_order(lines, issues)
    check_ticket_numbers(lines, issues)
    check_concept_confusion(lines, issues)
    check_download_entry(lines, issues)
    check_emoji_only_lines(lines, issues)
    check_placeholders(lines, issues)
    check_tech_exposure(lines, issues)
    check_style_tone(lines, issues)
    check_degraded_delivery(lines, issues)

    if not text.strip():
        issues.append(Issue("WARN", "EMPTY", 0, "文件内容为空"))

    errors = [i for i in issues if i.level == "ERROR"]
    print(f"\n=== {path} ===")
    print(f"行数：{len(lines)}　ERROR：{len(errors)}　"
          f"WARN：{len([i for i in issues if i.level == 'WARN'])}")

    if not issues:
        print("通过：未发现违规项。")
        return False

    has_error = False
    for issue in issues:
        marker = "ERROR" if issue.level == "ERROR" else "WARN "
        location = f"L{issue.line}" if issue.line else "全篇"
        if issue.level == "ERROR":
            has_error = True
        print(f"  [{marker}] {location} {issue.code} {issue.message}")

    return has_error


def main():
    parser = argparse.ArgumentParser(
        description="扫呗数电票数据查询助手回复草稿自检（只读本地文件，不联网）"
    )
    parser.add_argument("files", nargs="+", help="待校验的回复草稿文本文件路径")
    parser.add_argument(
        "--reference",
        help="基准文件：calc_amount.py 的输出。提供后会做确定性的金额一致性比对，"
             "可拦截「分→元」换算错误",
    )
    args = parser.parse_args()

    reference_text = None
    if args.reference:
        ref_path = Path(args.reference)
        if not ref_path.is_file():
            print(f"[ERROR] 基准文件不存在或不是普通文件：{ref_path}")
            return 2
        try:
            reference_text = ref_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            print(f"[ERROR] 无法读取基准文件 {ref_path}：{exc}")
            return 2

    has_error = False
    for raw_path in args.files:
        path = Path(raw_path)
        if not path.is_file():
            print(f"\n=== {path} ===")
            print(f"  [ERROR] 文件不存在或不是普通文件")
            has_error = True
            continue
        if check_file(path, issues := [], reference_text):
            has_error = True

    print("\n" + "=" * 50)
    if has_error:
        print("结论：不通过。存在 ERROR 级问题，请修正后重新校验。")
        return 1
    print("结论：通过。可输出给商户。")
    return 0


if __name__ == "__main__":
    sys.exit(main())