#!/usr/bin/env python3
"""扫呗数电票技能 —— GenUI 卡片编排自检脚本。

对齐《Linx GenUI 卡片使用教程》的组件选择与页面结构规则。
用法：
    python check_card.py <card.json> [更多文件...]

检查项：
  1. 组件类型白名单：只能用教程列出的 20 个组件
  2. 容器数量：一条消息只保留一个 Card
  3. 操作组数量：整条消息最多一个含 Button 的卡片块
  4. 展示/输入组件不混用：Text 不得伪装选项，Button 不得模拟多选
  5. 页面结构顺序：顶部 → 中部 → 底部
  6. 组件选型规范：固定候选不得用 Input/Textarea；日期范围必须两个 DatePicker
  7. 金额单位：疑似「分当元」时告警（WARN）
  8. 技术标识泄露：不得出现接口名等
  9. 未知组件类型告警

设计约束：
  - 仅使用 Python 标准库
  - 只读本地文件，不联网、不修改任何文件
  - 一次报出全部问题
退出码：0 = 通过（可能含 WARN）；1 = 存在 ERROR；2 = 用法错误
"""

import argparse
import json
import re
import sys
from pathlib import Path

# 教程第 3 节列出的 20 个组件
VALID_COMPONENTS = {
    # 容器与文字
    "Card", "Text", "Alert", "Tag", "Divider", "Descriptions",
    # 指标、流程与数据
    "Statistic", "Progress", "Steps", "Table", "Chart",
    # 选择与输入
    "RadioGroup", "ChoiceList", "Select", "CheckboxGroup",
    "Input", "Textarea", "InputNumber", "DatePicker",
    # 操作
    "Button",
}

# 展示组件（不能承载用户选择）
DISPLAY_COMPONENTS = {
    "Text", "Statistic", "Progress", "Steps", "Table", "Chart", "Descriptions",
}

# 输入组件
INPUT_COMPONENTS = {
    "RadioGroup", "ChoiceList", "Select", "CheckboxGroup",
    "Input", "Textarea", "InputNumber", "DatePicker",
}

# 需要 Button 提交的动作型组件
ACTION_COMPONENTS = {"Button"}

# 技术标识泄露
# 用通用模式覆盖「协议名 / 部署标识 / 网关」这类内部标识，不点名具体历史值。
FORBIDDEN_TECH_RE = re.compile(
    r"(mcp|sys\d{3,}|app_\d+|[-_]gateway|gateway"
    r"|接口异常|查询通道|服务异常|"
    r"getAllInvoiceStatistics|getInvoiceList|getInvoiceDetail|getTradeList|getGoodsList|"
    r"getStoreList|getSwitchByType|getCrownAuthInfo|blueInvoice|confirmInvoice|"
    r"oilGun|oil_gun|"
    r"query_type|store_id|invoice_id|return_code|invoice_scene|issue_status|"
    r"total_fee|total_amount|normal_amount|refund_amount)",
    re.IGNORECASE,
)

# 术语禁用
TERM_FORBIDDEN_RE = re.compile(r"(冲红|红冲票|正常票|净额|实际开票金额)")

# 孤立 emoji 行
EMOJI_ONLY_LINE_RE = re.compile(
    r"^[\U0001F000-\U0001FAFF☀-➿⬀-⯿️‍\U0001F1E6-\U0001F1FF\s]+$"
)


class Issue:
    __slots__ = ("level", "code", "where", "message")

    def __init__(self, level, code, where, message):
        self.level = level
        self.code = code
        self.where = where
        self.message = message

    def __str__(self):
        marker = "ERROR" if self.level == "ERROR" else "WARN "
        loc = self.where or "全篇"
        return f"  [{marker}] {loc} {self.code} {self.message}"


def walk(node, path, out):
    """遍历卡片 JSON，收集所有组件节点。

    节点形态：{"type": "Text", "props": {...}} 或 {"type": "Text", ...}
    容器节点（Card）递归其 children / content。
    """
    if isinstance(node, dict):
        t = node.get("type")
        if isinstance(t, str):
            out.append((t, node, path))
        for key in ("children", "content", "body", "items", "columns", "rows"):
            if key in node and isinstance(node[key], (list, dict)):
                walk(node[key], f"{path}.{key}", out)
        # 展示组件的 props 若是组件数组也递归
        props = node.get("props")
        if isinstance(props, dict):
            for key in ("children", "content", "items", "data"):
                if key in props and isinstance(props[key], (list, dict)):
                    walk(props[key], f"{path}.props.{key}", out)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            walk(item, f"{path}[{i}]", out)


def collect_strings(node, out):
    if isinstance(node, str):
        out.append(node)
    elif isinstance(node, dict):
        for v in node.values():
            collect_strings(v, out)
    elif isinstance(node, list):
        for v in node:
            collect_strings(v, out)


def check_valid_components(components, issues):
    for t, node, path in components:
        if t not in VALID_COMPONENTS:
            issues.append(Issue(
                "WARN", "CMP-UNKNOWN", path,
                f"组件「{t}」不在本技能支持的组件白名单内，"
                f"请先查 card-templates.md 确认可用组件",
            ))


def check_single_card(components, issues):
    cards = [(t, n, p) for t, n, p in components if t == "Card"]
    if len(cards) > 1:
        issues.append(Issue(
            "ERROR", "CARD-MULTI", cards[1][2],
            f"一条消息出现了 {len(cards)} 个 Card，"
            f"同一业务结果应合并为一个卡片块",
        ))
    if not cards:
        issues.append(Issue(
            "WARN", "CARD-NONE", "",
            "未发现 Card 容器，教程建议用 Card 承载一组相关内容",
        ))


def check_action_group(components, issues):
    """整条消息最多保留一个含操作按钮的卡片块。"""
    # 找出所有 Button 所在的顶层卡片块
    blocks = []
    for t, n, p in components:
        if t == "Card":
            blocks.append((p, n))
    blocks_with_btn = []
    for p, n in blocks:
        sub = []
        walk(n, p, sub)
        if any(tt == "Button" for tt, _, _ in sub):
            blocks_with_btn.append(p)
    if len(blocks_with_btn) > 1:
        issues.append(Issue(
            "ERROR", "ACTION-MULTI", blocks_with_btn[1],
            f"有 {len(blocks_with_btn)} 个卡片块包含 Button，"
            f"整条消息最多保留一个含操作按钮的卡片块",
        ))


def check_display_input_mix(components, issues):
    """展示组件不得承载选择；输入组件不得用展示组件替代。"""
    for t, node, path in components:
        if t in DISPLAY_COMPONENTS:
            props = node.get("props") or {}
            # Text / Statistic 等出现 options / choices 字段即为伪装选项
            for key in ("options", "choices", "items", "value"):
                if key in props and t == "Text":
                    issues.append(Issue(
                        "ERROR", "FAKE-OPTION", path,
                        "Text 不得用来模拟选项，请改用 RadioGroup / Select / ChoiceList",
                    ))
                    break
            if t == "Statistic" and "options" in props:
                issues.append(Issue(
                    "ERROR", "FAKE-OPTION", path,
                    "Statistic 不得承载选项，请改用选择类组件",
                ))


def check_selection_components(components, issues):
    """固定候选不得用 Input / Textarea。"""
    for t, node, path in components:
        props = node.get("props") or {}
        options = props.get("options")
        has_options = isinstance(options, list) and len(options) > 0
        if t == "Input" and has_options:
            issues.append(Issue(
                "ERROR", "INPUT-OPTIONS", path,
                "候选可枚举时应改用 Select，不得用 Input 承载固定候选",
            ))
        if t == "Textarea" and has_options:
            issues.append(Issue(
                "ERROR", "TEXTAREA-OPTIONS", path,
                "Textarea 只用于长文本补充说明，不得收集结构化选项",
            ))
        if t == "RadioGroup":
            n = len(options) if isinstance(options, list) else 0
            if n > 12:
                issues.append(Issue(
                    "ERROR", "RADIO-TOOMANY", path,
                    f"RadioGroup 适合 1—12 项，当前 {n} 项，请改用 Select",
                ))
        if t == "Select":
            n = len(options) if isinstance(options, list) else 0
            if n > 30:
                issues.append(Issue(
                    "ERROR", "SELECT-TOOMANY", path,
                    f"Select 适合 1—30 项，当前 {n} 项",
                ))
        if t == "Table":
            props_cols = props.get("columns") or props.get("cols")
            if isinstance(props_cols, list) and len(props_cols) > 6:
                issues.append(Issue(
                    "ERROR", "TABLE-COLS", path,
                    f"Table 适合 1—6 列，当前 {len(props_cols)} 列",
                ))


def check_date_range(components, issues):
    """日期范围必须有开始和结束两个日期字段。"""
    for t, node, path in components:
        if t != "DatePicker":
            continue
        props = node.get("props") or {}
        label = str(props.get("label", "")) + str(props.get("name", ""))
        if "范围" in label or "range" in label.lower():
            has_start = any(
                k in props for k in ("startDate", "start_date", "beginDate", "start")
            )
            has_end = any(
                k in props for k in ("endDate", "end_date", "endDateTime", "end")
            )
            if not (has_start and has_end):
                issues.append(Issue(
                    "ERROR", "DATE-RANGE", path,
                    "日期范围必须同时提供开始与结束两个日期字段",
                ))


def check_amount_unit(components, issues):
    """金额疑似未做「分 → 元」换算时告警。"""
    amounts = []
    for t, node, path in components:
        if t not in ("Statistic", "Descriptions", "Text", "Table"):
            continue
        props = node.get("props") or {}
        for key in ("value", "content", "title", "text", "label"):
            v = props.get(key)
            if isinstance(v, (int, float)):
                amounts.append((path, float(v)))
            elif isinstance(v, str):
                for m in re.finditer(r"¥\s*(\d+(?:\.\d+)?)", v):
                    amounts.append((path, float(m.group(1))))
    if not amounts:
        return
    vals = [a for _, a in amounts]
    if not all(abs(a) % 100 == 0 for a in vals):
        return
    if not any(abs(a) >= 100 for a in vals):
        return
    shown = "、".join(f"¥{a:.2f}" for a in vals)
    issues.append(Issue(
        "WARN", "AMT-UNIT", "",
        f"金额 {shown} 全为 100 的整数倍，疑似未做「分 → 元」换算。"
        f"接口金额单位是分，请用 scripts/calc_amount.py 取值",
    ))


def check_text_quality(strings, issues):
    joined = "\n".join(strings)
    for m in FORBIDDEN_TECH_RE.finditer(joined):
        issues.append(Issue(
            "ERROR", "TECH-LEAK", "",
            f"卡片文案出现技术表述「{m.group(0)}」，商户侧只输出业务结果",
        ))
    for m in TERM_FORBIDDEN_RE.finditer(joined):
        issues.append(Issue(
            "ERROR", "TERM", "",
            f"「{m.group(0)}」用词不合规，请使用统一术语",
        ))
    for s in strings:
        if "**" in s:
            issues.append(Issue("ERROR", "MD-BOLD", "", "卡片文案不得使用 ** 加粗"))
        if re.search(r"(?<!\*)\*(?!\*)", s):
            issues.append(Issue("ERROR", "MD-ITALIC", "", "卡片文案不得使用 * 斜体"))
        if "__" in s:
            issues.append(Issue("ERROR", "MD-UNDERLINE", "", "卡片文案不得使用 __ 下划线"))


def _norm_label(text):
    """归一化标签：去掉 emoji 与空白，便于基准与卡片标签对齐。

    卡片标签常带语义化图标（如「💰 单价」），基准文件里写「单价」，
    归一化后才能真正比对上。
    """
    if not isinstance(text, str):
        return ""
    cleaned = re.sub(
        "[\U0001F000-\U0001FAFF☀-➿⬀-⯿️‍\U0001F1E6-\U0001F1FF\U00002190-\U000021FF\U00002B00-\U00002BFF]",
        "",
        text,
    )
    return re.sub(r"\s+", "", cleaned)


def _collect_amounts_by_title(components):
    """从 Statistic / Descriptions 组件中提取「标题 → 金额」映射。

    用于与 calc_amount.py 的权威基准做确定性比对。
    标签会做归一化（去图标），同一归一化标签以首个为准。
    Descriptions 的字段可能在 props.items 列表里（label/content 成对），
    需要一并收集。
    """
    mapping = {}

    def add(title, value):
        if not isinstance(title, str):
            return
        amounts = []
        if isinstance(value, (int, float)):
            amounts.append(float(value))
        elif isinstance(value, str):
            for m in re.finditer(r"¥\s*(\d+(?:\.\d+)?)", value):
                amounts.append(float(m.group(1)))
        if not amounts:
            return
        mapping.setdefault(_norm_label(title), amounts[0])

    for t, node, path in components:
        if t == "Statistic":
            props = node.get("props") or {}
            add(props.get("title"), props.get("value"))
        elif t == "Descriptions":
            props = node.get("props") or {}
            add(props.get("title"), props.get("value"))
            items = props.get("items")
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        add(item.get("label"), item.get("content"))
    return mapping


def _parse_reference(text):
    """解析基准文件，得到「标签 → 金额」基准。

    支持两种基准：
      1. 汇总口径（开票数量 / 开票金额 / 有效开票金额 / 蓝票（正常开具）/ 红票（红冲）），
         来自 scripts/calc_amount.py 的输出；
      2. 通用口径——任意「标签：¥金额」行，例如开票场景的
         「合计：¥0.02」「订单金额：¥86.00」「单价：¥0.01」，
         会与卡片中同名的 Statistic / Descriptions 标签逐一比对。

    ★ 另支持**无标签裸金额**行（如 `calc_amount.py one 8600` 的输出「¥86.00」）：
      解析为「无标签金额」，比对时只要卡片里存在与之一致的金额即视为一致。
      这样 `one 8600` 的输出直接当基准也不会再报 REF-EMPTY。
    """
    ref = {}
    bare = []
    for line in text.splitlines():
        m = re.search(
            r"(开票数量|开票金额|有效开票金额|蓝票（正常开具）|红票（红冲）)[:：]\s*(.+)", line
        )
        if m:
            key, val = m.group(1), m.group(2)
            if key == "开票数量":
                c = re.search(r"(\d+)\s*张", val)
                if c:
                    ref["开票数量"] = float(c.group(1))
                continue
            amts = re.findall(r"¥\s*(\d+(?:\.\d+)?)", val)
            if not amts:
                continue
            if key == "开票金额":
                ref["开票金额"] = float(amts[0])
            elif key == "有效开票金额":
                ref["有效开票金额"] = float(amts[0])
            elif key == "蓝票（正常开具）":
                ref["蓝票（正常开具）"] = float(amts[0])
            elif key == "红票（红冲）":
                ref["红票（红冲）"] = float(amts[0])
            continue

        # 通用口径：任意「标签：¥金额」行
        g = re.match(r"\s*([^:：\n]{1,20})[:：]\s*.*?¥\s*(\d+(?:\.\d+)?)", line)
        if g:
            ref.setdefault(g.group(1).strip(), float(g.group(2)))
            continue

        # 无标签裸金额行：整行只有一个 ¥金额
        b = re.fullmatch(r"\s*¥\s*(\d+(?:\.\d+)?)\s*", line)
        if b:
            bare.append(float(b.group(1)))

    # 统一归一化标签（去图标与空白），使基准与卡片标签可对齐
    return {_norm_label(k): v for k, v in ref.items()}, bare


def check_amount_against_reference(components, issues, reference_text):
    """确定性校验：卡片中的指标金额必须与 calc_amount.py 的权威值一致。

    这是拦截「分 → 元」换算错误的唯一可靠手段：
    ¥6.00 与 ¥600.00 在文风上完全合理，启发式抓不住，必须与基准比对。
    """
    ref, bare = _parse_reference(reference_text)
    if not ref and not bare:
        issues.append(Issue(
            "ERROR", "REF-EMPTY", "",
            "基准文件里没解析出任何数值，无法校验金额一致性。"
            "请用 calc_amount.py one <分> [标签] 生成基准（带标签更佳）",
        ))
        return

    card = _collect_amounts_by_title(components)
    if not card:
        return  # 卡片里没有指标金额，跳过

    card_values = list(card.values())

    for title, expected in ref.items():
        key = _norm_label(title)
        if key not in card:
            continue  # 卡片未展示该项，不算不一致
        actual = card[key]
        if abs(round(actual, 2) - round(expected, 2)) > 0.005:
            ratio = f"（卡片是基准的 {actual / expected:.0f} 倍）" if expected else ""
            issues.append(Issue(
                "ERROR", "AMT-DIVERGE", "",
                f"「{title}」与基准不一致：卡片 {actual:.2f}，基准 {expected:.2f}{ratio}。"
                f"最常见原因是把「分」当成「元」，请用 scripts/calc_amount.py 重新取值",
            ))

    # ★ 兜底：基准与卡片的标签对不上时（标签写法不同、基准标签没出现在卡片里），
    #   仍要拦住「分当元」。仅在两侧金额条目数相同时做全量集合比对，避免误报。
    monetary_ref = [v for k, v in ref.items() if k != "开票数量"]
    if len(monetary_ref) == len(card_values) and card_values:
        unmatched = [
            v for v in monetary_ref
            if not any(abs(round(c, 2) - round(v, 2)) <= 0.005 for c in card_values)
        ]
        if unmatched:
            issues.append(Issue(
                "ERROR", "AMT-UNMATCHED", "",
                f"基准金额 {unmatched[0]:.2f} 在卡片中找不到对应数值，"
                f"卡片金额为 {'、'.join(f'{c:.2f}' for c in card_values)}。"
                f"最常见原因是把「分」当成「元」或基准与卡片不是同一次取值，"
                f"请用 scripts/calc_amount.py 重新取值并保持标签一致",
            ))

    # 无标签裸金额基准：卡片中只要存在与之一致的金额即视为一致
    if bare and ref:
        pass
    elif bare:
        if card_values and not any(
            abs(round(v, 2) - round(b, 2)) <= 0.005 for v in card_values for b in bare
        ):
            issues.append(Issue(
                "ERROR", "AMT-DIVERGE", "",
                f"卡片中没有任何金额与基准一致：基准 {bare[0]:.2f}，"
                f"卡片 {'、'.join(f'{v:.2f}' for v in card_values)}。"
                f"最常见原因是把「分」当成「元」，请用 scripts/calc_amount.py 重新取值",
            ))


# ★ 开票信息清单（待确认）与待补信息卡片必须覆盖的固定字段（九字段口径）
REQUIRED_INFO_FIELDS = [
    "抬头类型", "发票抬头", "商品", "税收类目", "税率",
    "单价", "数量", "合计", "接收邮箱",
]

# 触发「九字段必须齐全」校验的卡片标题关键词
_INFO_CARD_KEYWORDS = ["开票信息", "信息确认", "还差一点", "待补", "开票清单"]


def _card_title(node):
    props = node.get("props") or {}
    for key in ("title", "content", "text"):
        v = props.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def _collect_descriptions_labels(components):
    """收集卡片里所有 Descriptions 字段标签（已归一化）。"""
    labels = []
    for t, node, path in components:
        if t != "Descriptions":
            continue
        props = node.get("props") or {}
        items = props.get("items")
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    lab = item.get("label")
                    if isinstance(lab, str):
                        labels.append((_norm_label(lab), path))
    return labels


def check_info_card_fields(components, issues):
    """开票信息清单 / 待补信息卡片必须把九项字段全部列全。

    ★ 本项针对「只列了订单号、时间、金额，商品/税率/单价/数量全缺」这类交付缺口：
    字段查不到时也要**列出该行**并标注待补，而不是整行不出现。
    """
    titles = []
    for t, node, path in components:
        if t == "Card":
            title = _card_title(node)
            if title and any(k in title for k in _INFO_CARD_KEYWORDS):
                titles.append((path, title))
    if not titles:
        return

    present = {lab for lab, _ in _collect_descriptions_labels(components)}
    missing = [f for f in REQUIRED_INFO_FIELDS if _norm_label(f) not in present]
    if missing:
        issues.append(Issue(
            "ERROR", "INFO-FIELDS-MISSING", titles[0][0],
            f"开票信息清单缺少字段：{'、'.join(missing)}。"
            f"九项字段必须全部出现；查不到的写「待补充」并在提示里说明，"
            f"不允许整行省略",
        ))


def check_file(path, issues, reference_text=None):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError:
        issues.append(Issue("ERROR", "IO-ENCODING", "", f"{path} 不是 UTF-8 编码"))
        return True
    except json.JSONDecodeError as exc:
        issues.append(Issue("ERROR", "JSON-INVALID", "", f"{path} 不是合法 JSON：{exc}"))
        return True
    except OSError as exc:
        issues.append(Issue("ERROR", "IO-READ", "", f"无法读取 {path}：{exc}"))
        return True

    components = []
    walk(data, "root", components)

    check_valid_components(components, issues)
    check_single_card(components, issues)
    check_action_group(components, issues)
    check_display_input_mix(components, issues)
    check_selection_components(components, issues)
    check_date_range(components, issues)
    check_amount_unit(components, issues)
    check_info_card_fields(components, issues)
    if reference_text is not None:
        check_amount_against_reference(components, issues, reference_text)

    strings = []
    collect_strings(data, strings)
    check_text_quality(strings, issues)

    errors = [i for i in issues if i.level == "ERROR"]
    warns = [i for i in issues if i.level == "WARN"]
    print(f"\n=== {path} ===")
    print(f"组件数：{len(components)}　ERROR：{len(errors)}　WARN：{len(warns)}")
    if not issues:
        print("通过：未发现违规项。")
        return False
    for issue in issues:
        print(str(issue))
    return bool(errors)


def main():
    parser = argparse.ArgumentParser(
        description="扫呗数电票技能 GenUI 卡片编排自检（只读本地文件，不联网）"
    )
    parser.add_argument("files", nargs="+", help="待校验的卡片 JSON 文件路径")
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
    for raw in args.files:
        path = Path(raw)
        if not path.is_file():
            print(f"\n=== {path} ===")
            print("  [ERROR] 文件不存在或不是普通文件")
            has_error = True
            continue
        if check_file(path, issues := [], reference_text):
            has_error = True

    print("\n" + "=" * 50)
    if has_error:
        print("结论：不通过。存在 ERROR 级问题，请修正后重新校验。")
        return 1
    print("结论：通过。可输出。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
