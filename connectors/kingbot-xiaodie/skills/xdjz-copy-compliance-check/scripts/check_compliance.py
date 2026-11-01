#!/usr/bin/env python3
"""内容社区文案合规检测：确定性违禁词扫描（第一道筛查）。

按 ``assets/lexicon.json`` 词库扫描文案，输出候选命中（原文位置、检查维度、
默认严重等级、是否待语境复核）、等级计数与候选整体风险。最终判定以模型
语境复核为准；本脚本只做可复现的匹配。

仅依赖 Python 3 标准库。

用法::

    python3 scripts/check_compliance.py --title T --body B --tags "a,b" \\
        --goods-title G --goods-desc D [--json]
    python3 scripts/check_compliance.py --input items.json [--json]

可选参数::

    --lexicon <path>   词库路径，默认 <脚本目录>/../assets/lexicon.json
    --json             以 UTF-8 JSON 输出（中文不转义），否则输出中文文本摘要

退出码::

    0  候选整体风险为低风险
    1  候选整体风险为高风险或中风险
    2  参数错误、输入文件不可读或不合法、词库缺失或不合法
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

SEVERITIES: tuple[str, ...] = ("red", "yellow", "blue")
FIELDS: tuple[str, ...] = ("title", "body", "tags", "goods_title", "goods_desc")
DIMENSION_MIN = 1
DIMENSION_MAX = 11

_REQUIRED_STR_FIELDS: tuple[str, ...] = ("word", "category", "basis", "suggestion")
_TOP_LEVEL_STR_FIELDS: tuple[str, ...] = ("schema_version", "lexicon_version", "source")

# 匹配式通配符：{*} = 1–8 个任意归一化字符，{n} = 1 个以上数字
_WILDCARD_RE = re.compile(r"\{\*\}|\{n\}")


# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LexiconEntry:
    word: str
    category: str
    dimension: int
    severity: str
    needs_context: bool
    basis: str
    suggestion: str
    match: tuple[str, ...] = ()  # 空 = 使用 word
    condition: str | None = None


@dataclass(frozen=True)
class Lexicon:
    schema_version: str
    lexicon_version: str
    source: str
    entries: tuple[LexiconEntry, ...]


@dataclass(frozen=True)
class Normalized:
    norm: str
    pos_map: tuple[int, ...]


@dataclass(frozen=True)
class Hit:
    field: str  # title|body|tags|goods_title|goods_desc
    index: int | None  # tags 的标签序号，其余为 None
    start: int  # 原文码点区间 [start, end)
    end: int
    text: str  # 原文片段 = 原文[start:end]
    word: str
    matched_term: str
    entry_id: int
    category: str
    dimension: int
    severity: str
    needs_context: bool
    basis: str
    suggestion: str


@dataclass(frozen=True)
class Counts:
    red: int
    yellow: int
    blue: int
    total: int


@dataclass(frozen=True)
class CheckResult:
    name: str
    hits: tuple[Hit, ...]  # 按字段顺序、start、end、entry_id 排序
    counts: Counts
    overall_risk: str  # high|medium|low
    overall_risk_label: str  # 高风险|中风险|低风险


@dataclass(frozen=True)
class BatchResult:
    items: tuple[CheckResult, ...]
    counts: Counts
    overall_risk: str
    overall_risk_label: str


@dataclass(frozen=True)
class InputItem:
    name: str = ""
    title: str = ""
    body: str = ""
    tags: tuple[str, ...] = ()
    goods_title: str = ""
    goods_desc: str = ""


class LexiconError(Exception):
    """词库加载或校验失败。

    属性：
        path:   词库文件路径
        index:  出错词条序号（从 1 起）；与具体词条无关时为 None
        word:   出错词条的 word（若可读），否则为 None
        reason: 错误原因（中文）
    """

    def __init__(
        self,
        path: str,
        index: int | None,
        reason: str,
        word: str | None = None,
    ) -> None:
        self.path = str(path)
        self.index = index
        self.word = word
        self.reason = reason
        super().__init__(self.__str__())

    def __str__(self) -> str:
        loc = f"词库文件 {self.path}"
        if self.index is not None:
            loc += f" 第 {self.index} 条"
            if self.word is not None:
                loc += f' "{self.word}"'
        return f"{loc}：{self.reason}"


# ---------------------------------------------------------------------------
# 词库
# ---------------------------------------------------------------------------


def _validate_match_item(item: Any) -> str | None:
    """校验 match 中的单个匹配式，合法返回 None，否则返回原因。

    去掉通配符 ``{*}``、``{n}`` 后再归一化，结果不得为空（需求 8.4–8.6）。
    """
    if not isinstance(item, str):
        return "应为字符串"
    if not item:
        return "不能为空字符串"
    if not _term_has_content(item):
        return "归一化后为空"
    return None


def _term_has_content(term: str) -> bool:
    """匹配式去掉通配符后归一化是否非空。"""
    return bool(normalize(_WILDCARD_RE.sub("", term)).norm)


def _parse_entry(raw: Any, i: int, path: str) -> LexiconEntry:
    """校验并转换第 i 条（从 1 起）词条。"""
    if not isinstance(raw, dict):
        raise LexiconError(path, i, "词条应为 JSON 对象")

    word_val = raw.get("word")
    word = word_val if isinstance(word_val, str) and word_val else None

    def fail(reason: str) -> LexiconError:
        return LexiconError(path, i, reason, word)

    for key in ("word", "category", "dimension", "severity",
                "needs_context", "basis", "suggestion"):
        if key not in raw:
            raise fail(f"缺少字段 {key}")

    for key in _REQUIRED_STR_FIELDS:
        val = raw[key]
        if not isinstance(val, str):
            raise fail(f"字段 {key} 应为字符串")
        if not val:
            raise fail(f"字段 {key} 不能为空")

    dimension = raw["dimension"]
    if isinstance(dimension, bool) or not isinstance(dimension, int):
        raise fail("字段 dimension 应为整数")
    if not DIMENSION_MIN <= dimension <= DIMENSION_MAX:
        raise fail(f"字段 dimension 应在 {DIMENSION_MIN}–{DIMENSION_MAX} 之间，实际为 {dimension}")

    severity = raw["severity"]
    if severity not in SEVERITIES:
        raise fail(f"字段 severity 应为 red/yellow/blue 之一，实际为 {severity!r}")

    needs_context = raw["needs_context"]
    if not isinstance(needs_context, bool):
        raise fail("字段 needs_context 应为布尔值")

    match: tuple[str, ...] = ()
    if "match" in raw:
        m = raw["match"]
        if not isinstance(m, list):
            raise fail("字段 match 应为字符串数组")
        if not m:
            raise fail("字段 match 不能为空数组")
        for j, item in enumerate(m, start=1):
            reason = _validate_match_item(item)
            if reason is not None:
                raise fail(f"字段 match 第 {j} 项{reason}")
        match = tuple(m)
    elif not _term_has_content(raw["word"]):
        # 未声明 match 时 word 即匹配式，必须归一化后非空
        raise fail("字段 word 归一化后为空")

    condition: str | None = None
    if "condition" in raw:
        c = raw["condition"]
        if not isinstance(c, str):
            raise fail("字段 condition 应为字符串")
        condition = c

    return LexiconEntry(
        word=raw["word"],
        category=raw["category"],
        dimension=dimension,
        severity=severity,
        needs_context=needs_context,
        basis=raw["basis"],
        suggestion=raw["suggestion"],
        match=match,
        condition=condition,
    )


def parse_lexicon(text: str, path: str) -> Lexicon:
    """把词库 JSON 文本解析为 Lexicon；遇到第一处错误即抛 LexiconError。"""
    path = str(path)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise LexiconError(
            path, None, f"不是合法 JSON（第 {e.lineno} 行第 {e.colno} 列：{e.msg}）"
        ) from e

    if not isinstance(data, dict):
        raise LexiconError(path, None, "顶层应为 JSON 对象")
    for key in _TOP_LEVEL_STR_FIELDS:
        if key not in data:
            raise LexiconError(path, None, f"缺少顶层字段 {key}")
        if not isinstance(data[key], str):
            raise LexiconError(path, None, f"顶层字段 {key} 应为字符串")
    if "entries" not in data:
        raise LexiconError(path, None, "缺少顶层字段 entries")
    raw_entries = data["entries"]
    if not isinstance(raw_entries, list):
        raise LexiconError(path, None, "顶层字段 entries 应为数组")

    entries = tuple(_parse_entry(raw, i, path) for i, raw in enumerate(raw_entries, start=1))
    return Lexicon(
        schema_version=data["schema_version"],
        lexicon_version=data["lexicon_version"],
        source=data["source"],
        entries=entries,
    )


def load_lexicon(path: Path) -> Lexicon:
    """读取 UTF-8 词库文件并解析；I/O 与解码错误转为 LexiconError。"""
    p = str(path)
    try:
        raw = Path(path).read_bytes()
    except OSError as e:
        reason = e.strerror or str(e)
        raise LexiconError(p, None, f"无法读取（{reason}）") from e
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        raise LexiconError(p, None, f"不是 UTF-8 编码（字节位置 {e.start}）") from e
    if text.startswith("\ufeff"):
        text = text[1:]
    return parse_lexicon(text, p)


def _entry_to_dict(e: LexiconEntry) -> dict[str, Any]:
    d: dict[str, Any] = {
        "word": e.word,
        "category": e.category,
        "dimension": e.dimension,
        "severity": e.severity,
        "needs_context": e.needs_context,
        "basis": e.basis,
        "suggestion": e.suggestion,
    }
    if e.condition is not None:
        d["condition"] = e.condition
    if e.match:
        d["match"] = list(e.match)
    return d


def dump_lexicon(lex: Lexicon) -> str:
    """Lexicon_Serializer：把内存词库格式化为 JSON 文本（省略默认值可选字段）。"""
    data = {
        "schema_version": lex.schema_version,
        "lexicon_version": lex.lexicon_version,
        "source": lex.source,
        "entries": [_entry_to_dict(e) for e in lex.entries],
    }
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


# ---------------------------------------------------------------------------
# 归一化（任务 8.1）
# ---------------------------------------------------------------------------


def normalize_char(ch: str) -> str:
    """单个原文字符归一化：NFKC → 小写 → NFKC，仅保留 L*、N* 类别。"""
    t = unicodedata.normalize("NFKC", ch)  # 全角→半角、兼容字符展开
    t = unicodedata.normalize("NFKC", t.lower())  # 英文转小写后再次规范化
    return "".join(c for c in t if unicodedata.category(c)[0] in ("L", "N"))


def normalize(text: str) -> Normalized:
    """逐码点归一化，pos_map[k] 为归一化第 k 个字符对应的原文码点下标。"""
    out: list[str] = []
    pos_map: list[int] = []
    for i, ch in enumerate(text):
        for c in normalize_char(ch):
            out.append(c)
            pos_map.append(i)
    return Normalized(norm="".join(out), pos_map=tuple(pos_map))


# ---------------------------------------------------------------------------
# 匹配（任务 9.x）
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CompiledTerm:
    """单个已编译匹配式。

    字面式：``norm`` 为归一化后的字面串，``pattern`` 为 None。
    通配式：``pattern`` 为编译后的正则（作用于归一化文本），``norm`` 为 None。
    ``term`` 保留词库中的原始匹配式（未归一化），写入 ``Hit.matched_term``。
    """

    entry_id: int  # 词条在 entries 中的下标（从 0 起）
    term_order: int  # 匹配式在该词条 terms 中的序号，用于同区间去重的稳定排序
    term: str
    is_wildcard: bool
    norm: str | None = None
    pattern: "re.Pattern[str] | None" = None


@dataclass(frozen=True)
class CompiledLexicon:
    lexicon: Lexicon
    terms: tuple[CompiledTerm, ...]


# 通配符对应的正则片段（作用于归一化文本）：
# - {*}：1–8 个任意归一化字符，非贪婪 → 每个起点取最短匹配；
# - {n}：1 个以上数字。归一化经 NFKC，全角数字、圈数字（①→1）等已变为 ASCII，
#   因此用 [0-9]；其他文字的数字（如阿拉伯-印度数字）不视为 {n}。
#   采用非贪婪 +?：后接字面段时取最短，位于末尾时只匹配 1 位，同样是最短匹配。
_WILDCARD_REGEX = {"{*}": ".{1,8}?", "{n}": "[0-9]+?"}


def _compile_wildcard(term: str) -> "re.Pattern[str]":
    """把通配匹配式编译为正则：字面段先归一化再转义，通配符替换为对应片段。"""
    parts: list[str] = []
    pos = 0
    for m in _WILDCARD_RE.finditer(term):
        parts.append(re.escape(normalize(term[pos:m.start()]).norm))
        parts.append(_WILDCARD_REGEX[m.group(0)])
        pos = m.end()
    parts.append(re.escape(normalize(term[pos:]).norm))
    # 归一化文本不含换行，DOTALL 仅为稳妥
    return re.compile("".join(parts), re.DOTALL)


def compile_lexicon(lex: Lexicon) -> CompiledLexicon:
    """为每个词条生成匹配式（缺省为 [word]），归一化后区分字面式与通配式。"""
    compiled: list[CompiledTerm] = []
    for entry_id, entry in enumerate(lex.entries):
        terms = entry.match if entry.match else (entry.word,)
        for order, term in enumerate(terms):
            if _WILDCARD_RE.search(term):
                try:
                    pattern = _compile_wildcard(term)
                except re.error as e:
                    raise LexiconError(
                        "<compiled>", entry_id + 1, f"匹配式 {term!r} 无法编译为正则（{e}）",
                        entry.word,
                    ) from e
                compiled.append(CompiledTerm(entry_id, order, term, True, pattern=pattern))
            else:
                norm = normalize(term).norm
                if not norm:  # parse_lexicon 已保证非空；防御直接构造的 Lexicon
                    raise LexiconError(
                        "<compiled>", entry_id + 1, f"匹配式 {term!r} 归一化后为空", entry.word
                    )
                compiled.append(CompiledTerm(entry_id, order, term, False, norm=norm))
    return CompiledLexicon(lexicon=lex, terms=tuple(compiled))


_SEVERITY_RANK = {s: i for i, s in enumerate(SEVERITIES)}  # red=0 < yellow=1 < blue=2


def scan_text(
    text: str, field: str, index: int | None, clex: CompiledLexicon
) -> list[Hit]:
    """扫描单段文本，返回按 (start, end, entry_id) 排序的命中。

    区间对齐说明：通过边界对齐检查的归一化区间 [s, e) 恰好覆盖原文字符
    pos_map[s]..pos_map[e-1] 的全部归一化输出（以及其间归一化为空的字符），因此
    - 原文片段的归一化结果等于 norm[s:e]（属性 3）；
    - 不同的对齐区间映射到不同的原文区间（单射），同区间去重后不会出现原文区间
      完全相同的两条 Hit（属性 6）；
    - 对齐区间之间的包含关系在归一化空间与原文空间中等价，故包含过滤可在
      归一化空间完成。
    """
    nz = normalize(text)
    norm, pos_map = nz.norm, nz.pos_map
    n = len(norm)
    if n == 0:
        return []

    def aligned(s: int, e: int) -> bool:
        return (s == 0 or pos_map[s - 1] != pos_map[s]) and (
            e == n or pos_map[e] != pos_map[e - 1]
        )

    entries = clex.lexicon.entries
    # 归一化区间 → 当前最优候选（同区间去重）
    best: dict[tuple[int, int], CompiledTerm] = {}

    def rank(ct: CompiledTerm) -> tuple[int, bool, int, int]:
        e = entries[ct.entry_id]
        return (_SEVERITY_RANK[e.severity], e.needs_context, ct.entry_id, ct.term_order)

    def offer(s: int, e: int, ct: CompiledTerm) -> None:
        if e <= s or not aligned(s, e):
            return
        key = (s, e)
        cur = best.get(key)
        if cur is None or rank(ct) < rank(cur):
            best[key] = ct

    for ct in clex.terms:
        if ct.is_wildcard:
            assert ct.pattern is not None
            for p in range(n):
                m = ct.pattern.match(norm, p)
                if m is not None:
                    offer(m.start(), m.end(), ct)
        else:
            assert ct.norm is not None
            L = len(ct.norm)
            p = norm.find(ct.norm)
            while p != -1:
                offer(p, p + L, ct)
                p = norm.find(ct.norm, p + 1)

    # 严格包含过滤：按 (s 升序, e 降序) 扫描，若此前区间的最大 e ≥ 当前 e，
    # 则存在 y.s ≤ x.s 且 x.e ≤ y.e；由于区间已去重，y 必然更长，删除 x。
    kept: list[tuple[int, int]] = []
    max_e = -1
    for s, e in sorted(best, key=lambda k: (k[0], -k[1])):
        if e <= max_e:
            continue
        kept.append((s, e))
        max_e = e

    hits: list[Hit] = []
    for s, e in kept:
        ct = best[(s, e)]
        entry = entries[ct.entry_id]
        start = pos_map[s]
        end = pos_map[e - 1] + 1
        hits.append(
            Hit(
                field=field,
                index=index,
                start=start,
                end=end,
                text=text[start:end],
                word=entry.word,
                matched_term=ct.term,
                entry_id=ct.entry_id,
                category=entry.category,
                dimension=entry.dimension,
                severity=entry.severity,
                needs_context=entry.needs_context,
                basis=entry.basis,
                suggestion=entry.suggestion,
            )
        )
    hits.sort(key=lambda h: (h.start, h.end, h.entry_id))
    return hits


# ---------------------------------------------------------------------------
# 汇总（任务 10.1）
# ---------------------------------------------------------------------------


RISK_LABELS: dict[str, str] = {"high": "高风险", "medium": "中风险", "low": "低风险"}


def check_item(item: InputItem, clex: "CompiledLexicon") -> CheckResult:
    """按字段固定顺序独立扫描单条输入。

    每个字段（及每个标签）内的命中已按 (start, end, entry_id) 排序，按
    title → body → tags（按标签序号）→ goods_title → goods_desc 顺序拼接，
    即得到「字段顺序、start、end、entry_id」排序。空字段不产生 Hit。
    """
    hits: list[Hit] = []
    hits += scan_text(item.title, "title", None, clex)
    hits += scan_text(item.body, "body", None, clex)
    for k, tag in enumerate(item.tags):
        hits += scan_text(tag, "tags", k, clex)
    hits += scan_text(item.goods_title, "goods_title", None, clex)
    hits += scan_text(item.goods_desc, "goods_desc", None, clex)
    counts, risk = aggregate(hits)
    return CheckResult(
        name=item.name,
        hits=tuple(hits),
        counts=counts,
        overall_risk=risk,
        overall_risk_label=RISK_LABELS[risk],
    )


def check_batch(items: Sequence[InputItem], clex: "CompiledLexicon") -> BatchResult:
    """批量检测：各 item 独立汇总；总计数求和，整体风险对全部 Hit 重新聚合。"""
    results = tuple(check_item(it, clex) for it in items)
    return _make_batch(results)


def _make_batch(results: tuple[CheckResult, ...]) -> BatchResult:
    all_hits = [h for r in results for h in r.hits]
    _, risk = aggregate(all_hits)
    counts = Counts(
        red=sum(r.counts.red for r in results),
        yellow=sum(r.counts.yellow for r in results),
        blue=sum(r.counts.blue for r in results),
        total=sum(r.counts.total for r in results),
    )
    return BatchResult(
        items=results, counts=counts, overall_risk=risk, overall_risk_label=RISK_LABELS[risk]
    )


def aggregate(hits: Sequence[Hit]) -> tuple[Counts, str]:
    """按 severity 计数；有 red → high，否则有 yellow → medium，否则 low。"""
    red = sum(1 for h in hits if h.severity == "red")
    yellow = sum(1 for h in hits if h.severity == "yellow")
    blue = sum(1 for h in hits if h.severity == "blue")
    counts = Counts(red=red, yellow=yellow, blue=blue, total=len(hits))
    risk = "high" if red else "medium" if yellow else "low"
    return counts, risk


def exit_code_for(risk: str) -> int:
    """高风险 / 中风险 → 1，低风险 → 0。"""
    return 1 if risk in ("high", "medium") else 0


# ---------------------------------------------------------------------------
# 输出（任务 10.3）
# ---------------------------------------------------------------------------

_HIT_KEYS: tuple[str, ...] = (
    "field", "index", "start", "end", "text", "word", "matched_term", "entry_id",
    "category", "dimension", "severity", "needs_context", "basis", "suggestion",
)


def hit_to_dict(h: Hit) -> dict[str, Any]:
    return {k: getattr(h, k) for k in _HIT_KEYS}  # index 为 None → JSON null


def hit_from_dict(d: dict[str, Any]) -> Hit:
    return Hit(**{k: d[k] for k in _HIT_KEYS})


def counts_to_dict(c: Counts) -> dict[str, Any]:
    return {"red": c.red, "yellow": c.yellow, "blue": c.blue, "total": c.total}


def counts_from_dict(d: dict[str, Any]) -> Counts:
    return Counts(red=d["red"], yellow=d["yellow"], blue=d["blue"], total=d["total"])


def check_result_to_dict(r: CheckResult) -> dict[str, Any]:
    return {
        "name": r.name,
        "hits": [hit_to_dict(h) for h in r.hits],
        "counts": counts_to_dict(r.counts),
        "overall_risk": r.overall_risk,
        "overall_risk_label": r.overall_risk_label,
    }


def check_result_from_dict(d: dict[str, Any]) -> CheckResult:
    return CheckResult(
        name=d["name"],
        hits=tuple(hit_from_dict(h) for h in d["hits"]),
        counts=counts_from_dict(d["counts"]),
        overall_risk=d["overall_risk"],
        overall_risk_label=d["overall_risk_label"],
    )


def batch_result_to_dict(b: BatchResult) -> dict[str, Any]:
    return {
        "items": [check_result_to_dict(r) for r in b.items],
        "counts": counts_to_dict(b.counts),
        "overall_risk": b.overall_risk,
        "overall_risk_label": b.overall_risk_label,
    }


def batch_result_from_dict(d: dict[str, Any]) -> BatchResult:
    return BatchResult(
        items=tuple(check_result_from_dict(r) for r in d["items"]),
        counts=counts_from_dict(d["counts"]),
        overall_risk=d["overall_risk"],
        overall_risk_label=d["overall_risk_label"],
    )


def result_to_dict(obj: CheckResult | BatchResult) -> dict[str, Any]:
    if isinstance(obj, BatchResult):
        return batch_result_to_dict(obj)
    return check_result_to_dict(obj)


def result_from_dict(d: dict[str, Any]) -> CheckResult | BatchResult:
    """顶层含 ``items`` 为批量结果，否则为单条结果。"""
    if "items" in d:
        return batch_result_from_dict(d)
    return check_result_from_dict(d)


def result_to_json(obj: CheckResult | BatchResult) -> str:
    """UTF-8 JSON（中文不转义，缩进 2）。"""
    return json.dumps(result_to_dict(obj), ensure_ascii=False, indent=2)


def result_from_json(text: str) -> CheckResult | BatchResult:
    return result_from_dict(json.loads(text))


_SEVERITY_TAGS = {"red": "[🔴 严重]", "yellow": "[🟡 警告]", "blue": "[🔵 建议]"}
_FIELD_LABELS = {
    "title": "标题",
    "body": "正文",
    "tags": "标签",
    "goods_title": "商品标题",
    "goods_desc": "商品描述",
}
_FIELD_RANK = {f: i for i, f in enumerate(FIELDS)}
NEEDS_CONTEXT_MARK = "【待语境复核】"

# 摘要按行组织：原文片段等字段中的换行、回车、制表符转写为可见的 \n、\r、\t，
# 保证每条 Hit 恰好占一行（待语境复核标注始终位于该行行尾）。
_LINE_ESCAPES = str.maketrans({"\n": "\\n", "\r": "\\r", "\t": "\\t"})


def _one_line(s: str) -> str:
    return s.translate(_LINE_ESCAPES)


def _render_hit(h: Hit) -> str:
    line = (
        f"  {_SEVERITY_TAGS[h.severity]} 「{_one_line(h.text)}」→ {_one_line(h.word)}"
        f"（维度{h.dimension}·{_one_line(h.category)}）"
        f"依据：{_one_line(h.basis)} 建议：{_one_line(h.suggestion)}"
    )
    if h.needs_context:
        line += " " + NEEDS_CONTEXT_MARK
    return line


def _group_label(field: str, index: int | None) -> str:
    label = _FIELD_LABELS.get(field, field)
    if field == "tags" and index is not None:
        label += f" #{index + 1}"  # 面向用户的标签序号从 1 起
    return label


def _counts_line(prefix: str, counts: Counts, risk_label: str) -> str:
    return (
        f"{prefix}：🔴 严重 {counts.red} · 🟡 警告 {counts.yellow} · 🔵 建议 {counts.blue}"
        f"（共 {counts.total} 条），候选整体风险：{risk_label}"
    )


def _render_hits(hits: Sequence[Hit]) -> list[str]:
    if not hits:
        return ["未发现候选命中。"]
    # 分组键：字段固定顺序、标签序号；组内按 red → yellow → blue，同级保持原顺序
    groups: dict[tuple[int, int, str, int | None], list[Hit]] = {}
    for h in hits:
        key = (_FIELD_RANK.get(h.field, len(FIELDS)), -1 if h.index is None else h.index,
               h.field, h.index)
        groups.setdefault(key, []).append(h)
    lines: list[str] = []
    for key in sorted(groups, key=lambda k: (k[0], k[1], k[2])):
        _, _, field, index = key
        lines.append(f"▌{_group_label(field, index)}")
        for h in sorted(groups[key], key=lambda h: _SEVERITY_RANK.get(h.severity, 99)):
            lines.append(_render_hit(h))
    return lines


def render_text(obj: CheckResult | BatchResult) -> str:
    """中文文本摘要：按字段分组，字段内 red → yellow → blue；末行为计数与候选整体风险。"""
    lines: list[str] = []
    if isinstance(obj, BatchResult):
        for i, r in enumerate(obj.items, start=1):
            name = _one_line(r.name) if r.name else f"第 {i} 条"
            lines.append(f"===== {name} =====")
            lines += _render_hits(r.hits)
            lines.append(_counts_line("小计", r.counts, r.overall_risk_label))
            lines.append("")
        lines.append(_counts_line("合计", obj.counts, obj.overall_risk_label))
    else:
        lines += _render_hits(obj.hits)
        lines.append(_counts_line("合计", obj.counts, obj.overall_risk_label))
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# CLI（任务 11.1）
# ---------------------------------------------------------------------------


DEFAULT_LEXICON_PATH = Path(__file__).resolve().parent.parent / "assets" / "lexicon.json"

# 单字段参数：(argparse dest, InputItem 字段名)
_FIELD_ARGS: tuple[str, ...] = ("title", "body", "tags", "goods_title", "goods_desc")
_ITEM_STR_KEYS: tuple[str, ...] = ("name", "title", "body", "goods_title", "goods_desc")
_TAG_SPLIT_RE = re.compile(r"[,，]")


class InputError(Exception):
    """输入文件不可读或不合法；str 即完整的中文错误信息（不含「错误：」前缀）。"""


def split_tags(raw: str) -> tuple[str, ...]:
    """按半角/全角逗号切分标签，去掉首尾空白并丢弃空项。"""
    return tuple(t for t in (p.strip() for p in _TAG_SPLIT_RE.split(raw)) if t)


def _item_from_obj(obj: Any, where: str) -> InputItem:
    """把 JSON 对象转换为 InputItem；未知键忽略，类型不符抛 ValueError。"""
    if not isinstance(obj, dict):
        raise ValueError(f"{where}应为 JSON 对象")
    kwargs: dict[str, Any] = {}
    for key in _ITEM_STR_KEYS:
        if key in obj:
            val = obj[key]
            if not isinstance(val, str):
                raise ValueError(f"{where}字段 {key} 应为字符串")
            kwargs[key] = val
    if "tags" in obj:
        tags = obj["tags"]
        if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
            raise ValueError(f"{where}字段 tags 应为字符串数组")
        kwargs["tags"] = tuple(tags)
    return InputItem(**kwargs)


def load_input(path: str | Path) -> tuple[list[InputItem], bool]:
    """读取 --input 文件，返回 (items, is_batch)。

    顶层含 ``items`` 为批量（is_batch=True），否则顶层对象视为单条。
    文件不可读抛 InputError「无法读取输入文件 …」，其余问题抛「输入文件 … 格式不合法」。
    """
    p = str(path)
    try:
        raw = Path(path).read_bytes()
    except OSError as e:
        raise InputError(f"无法读取输入文件 {p}：{e.strerror or e}") from e

    def bad(reason: str) -> InputError:
        return InputError(f"输入文件 {p} 格式不合法：{reason}")

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        raise bad(f"不是 UTF-8 编码（字节位置 {e.start}）") from e
    if text.startswith("\ufeff"):
        text = text[1:]
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise bad(f"不是合法 JSON（第 {e.lineno} 行第 {e.colno} 列：{e.msg}）") from e
    except RecursionError as e:
        raise bad("JSON 嵌套过深") from e

    if not isinstance(data, dict):
        raise bad("顶层应为 JSON 对象")
    try:
        if "items" in data:
            raw_items = data["items"]
            if not isinstance(raw_items, list):
                raise bad("字段 items 应为数组")
            items = [
                _item_from_obj(obj, f"items 第 {i} 项")
                for i, obj in enumerate(raw_items, start=1)
            ]
            return items, True
        return [_item_from_obj(data, "")], False
    except ValueError as e:
        raise bad(str(e)) from e


def _build_parser() -> "argparse.ArgumentParser":
    import argparse

    parser = argparse.ArgumentParser(
        prog="check_compliance.py",
        description="内容社区文案合规检测：按词库确定性扫描违禁词（候选命中，需语境复核）。",
    )
    parser.add_argument("--title", help="笔记标题")
    parser.add_argument("--body", help="笔记正文")
    parser.add_argument("--tags", help="话题标签，半角/全角逗号分隔")
    parser.add_argument("--goods-title", dest="goods_title", help="商品标题")
    parser.add_argument("--goods-desc", dest="goods_desc", help="商品描述")
    parser.add_argument("--input", help="批量/单条输入 JSON 文件（UTF-8）")
    parser.add_argument("--json", action="store_true", help="以 UTF-8 JSON 输出")
    parser.add_argument(
        "--lexicon", default=str(DEFAULT_LEXICON_PATH),
        help="词库路径，默认 <脚本目录>/../assets/lexicon.json",
    )
    return parser


def _reconfigure_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8")
        except Exception:  # 测试捕获对象等可能不支持
            pass


def _error(msg: str) -> int:
    sys.stderr.write(f"错误：{msg}\n")
    return 2


def main(argv: list[str] | None = None) -> int:
    _reconfigure_utf8()
    try:
        parser = _build_parser()
        try:
            args = parser.parse_args(argv)
        except SystemExit as e:  # argparse 参数错误为 2，--help 为 0
            code = e.code
            return code if isinstance(code, int) else (0 if code is None else 2)

        given = [f for f in _FIELD_ARGS if getattr(args, f) is not None]
        if args.input is not None and given:
            return _error("--input 不能与单字段参数同时使用")
        if args.input is None and not given:
            rc = _error(
                "请至少提供 --title/--body/--tags/--goods-title/--goods-desc 之一，或使用 --input"
            )
            sys.stderr.write(parser.format_usage())
            return rc

        if args.input is not None:
            try:
                items, is_batch = load_input(args.input)
            except InputError as e:
                return _error(str(e))
        else:
            items = [InputItem(
                title=args.title or "",
                body=args.body or "",
                tags=split_tags(args.tags) if args.tags is not None else (),
                goods_title=args.goods_title or "",
                goods_desc=args.goods_desc or "",
            )]
            is_batch = False

        try:
            clex = compile_lexicon(load_lexicon(Path(args.lexicon)))
        except LexiconError as e:
            return _error(str(e))

        result: CheckResult | BatchResult
        result = check_batch(items, clex) if is_batch else check_item(items[0], clex)
        out = result_to_json(result) + "\n" if args.json else render_text(result)
        sys.stdout.write(out)
        sys.stdout.flush()
        return exit_code_for(result.overall_risk)
    except Exception as e:  # 未捕获异常默认退出码 1 会与「有风险」混淆
        return _error(f"内部错误：{type(e).__name__}: {e}")


if __name__ == "__main__":
    sys.exit(main())
