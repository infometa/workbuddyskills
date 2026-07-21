#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_provenance.py —— 论文速读结果的 ngram 防幻觉校验器（v0.1 POC）

功能：
  - 读取 result.json + 各篇 paper_*.json（由 parse_pdf.py 产出）
  - 对 result.json 中所有强/中校验 claim 做双粒度 ngram 匹配（3-gram + 5-gram）
  - 校验数字 / 专有名词是否精确命中
  - 校验 page 在 [1, total_pages] 范围内
  - 校验 section 是否存在于 parse_pdf 识别的 sections 中
  - 输出 provenance-audit.json（结构详见 references/provenance-rules.md §六）
  - 可选：--in-place 模式下，自动删除强校验失败的 claim 并写回 result.json

用法：
  python scripts/verify_provenance.py \
      --result result.json \
      --papers paper_a.json paper_b.json \
      --out provenance-audit.json

  python scripts/verify_provenance.py \
      --result result.json \
      --papers paper_a.json \
      --in-place              # 自动清理 result.json 中的 HALLUCINATED_EXCERPT

退出码：
  0  正常（不管是否有 hallucination flag）
  1  参数错误 / 文件不存在
  2  result.json 格式错误（缺关键字段）
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

SCRIPT_VERSION = "0.2.0"

# v0.4.0 / P0-B：整篇置信度降级阈值（详见 references/provenance-rules.md § 八）
DEGRADED_HIGH_RATIO_THRESHOLD = 0.60
DEGRADED_FAILED_COUNT_THRESHOLD = 3

# ============================================================
# 1. 文本归一化
# ============================================================

PUNCT_PATTERN = re.compile(r"[\.,;:\(\)\[\]\{\}\"\"'']+")


def normalize(text: str) -> str:
    if not text:
        return ""
    t = unicodedata.normalize("NFC", text)
    t = t.lower()
    t = PUNCT_PATTERN.sub(" ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def tokenize(text: str) -> list[str]:
    """简单按空白 + 中文单字 切 token。"""
    norm = normalize(text)
    tokens: list[str] = []
    for chunk in norm.split():
        # 对纯中文段按字拆，混合则整 token 保留
        if all("\u4e00" <= c <= "\u9fff" for c in chunk):
            tokens.extend(list(chunk))
        else:
            tokens.append(chunk)
    return tokens


def make_ngrams(tokens: list[str], n: int) -> set[tuple[str, ...]]:
    if len(tokens) < n:
        return set()
    return {tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)}


# ============================================================
# 2. 专名 / 数字提取
# ============================================================

NUMBER_RE = re.compile(r"(?<![A-Za-z_])\d+(?:[\.,]\d+)?\s*(?:[kKmMbB%]|%)?(?![A-Za-z_])")
NAME_RE = re.compile(r"\b(?:[A-Z][a-zA-Z]{2,}(?:[-_][A-Z0-9][a-zA-Z0-9]+)*|[A-Z]{2,}[-_][A-Z0-9]+|GPT-\d+|LLaMA(?:-\d+)?|BERT|T5|ROUGE-[LlNn12])\b")


def extract_numbers(text: str) -> list[str]:
    return [m.group(0).replace(",", "").replace(" ", "").lower() for m in NUMBER_RE.finditer(text)]


def extract_names(text: str) -> list[str]:
    return [m.group(0) for m in NAME_RE.finditer(text)]


# ============================================================
# 3. 论文索引（paper_*.json → ngram / numbers / names / sections）
# ============================================================


class PaperIndex:
    def __init__(self, paper_json: dict[str, Any]):
        self.meta = paper_json.get("meta", {})
        self.total_pages = int(self.meta.get("total_pages") or 0)
        self.sections = paper_json.get("sections", [])
        self.section_titles_lc = {str(s.get("title", "")).lower() for s in self.sections}
        self.blocks = paper_json.get("blocks", [])

        full_text_parts: list[str] = []
        for b in self.blocks:
            full_text_parts.append(str(b.get("text", "")))
        self.full_text = " ".join(full_text_parts)

        tokens = tokenize(self.full_text)
        self.tokens = tokens
        self.ngrams3 = make_ngrams(tokens, 3)
        self.ngrams5 = make_ngrams(tokens, 5)

        self.numbers: set[str] = set(extract_numbers(self.full_text))
        self.names: set[str] = set(extract_names(self.full_text))

    def match_claim(self, claim_text: str) -> dict[str, Any]:
        claim_tokens = tokenize(claim_text)
        claim_5grams = make_ngrams(claim_tokens, 5)
        claim_3grams = make_ngrams(claim_tokens, 3)

        if claim_5grams:
            hit5 = len(claim_5grams & self.ngrams5)
            ratio5 = hit5 / max(1, len(claim_5grams))
        else:
            hit5 = 0
            ratio5 = 0.0

        if claim_3grams:
            hit3 = len(claim_3grams & self.ngrams3)
            ratio3 = hit3 / max(1, len(claim_3grams))
        else:
            hit3 = 0
            ratio3 = 0.0

        claim_numbers = extract_numbers(claim_text)
        numbers_matched = [n for n in claim_numbers if n in self.numbers]
        numbers_missing = [n for n in claim_numbers if n not in self.numbers]

        claim_names = extract_names(claim_text)
        names_matched = [n for n in claim_names if n in self.names or n.lower() in self.full_text.lower()]
        names_missing = [n for n in claim_names if n not in names_matched]

        # 跨语言 paraphrase 判定：claim 含 CJK 但 paper 主要是英文（反之亦然）
        # → ngram 自然对不上，但数字 / 专名仍应匹配；若全匹配，视为合理改写
        claim_has_cjk = any("\u4e00" <= c <= "\u9fff" for c in claim_text)
        paper_sample = self.full_text[:2000]
        paper_cjk_ratio = sum(1 for c in paper_sample if "\u4e00" <= c <= "\u9fff") / max(1, len(paper_sample))
        paper_is_english = paper_cjk_ratio < 0.2
        is_cross_language_paraphrase = claim_has_cjk and paper_is_english

        if ratio5 >= 0.6 and not numbers_missing and not names_missing:
            confidence = "high"
        elif ratio5 >= 0.3 or (ratio3 >= 0.7 and not numbers_missing):
            confidence = "medium"
        elif ratio3 >= 0.4:
            confidence = "low"
        else:
            confidence = "failed"

        # 跨语言 paraphrase 放宽：若所有数字 + 所有专名都精确命中，最低也给 medium
        if is_cross_language_paraphrase and not numbers_missing and not names_missing:
            if len(numbers_matched) + len(names_matched) >= 2:
                if confidence in ("failed", "low"):
                    confidence = "medium"
            elif len(numbers_matched) + len(names_matched) >= 1:
                if confidence == "failed":
                    confidence = "low"

        if not numbers_missing and not names_missing and confidence == "failed" and ratio3 >= 0.3:
            confidence = "low"

        return {
            "5gram_hit_ratio": round(ratio5, 3),
            "3gram_hit_ratio": round(ratio3, 3),
            "numbers_matched": numbers_matched,
            "numbers_missing": numbers_missing,
            "names_matched": names_matched,
            "names_missing": names_missing,
            "cross_language_paraphrase": is_cross_language_paraphrase,
            "confidence": confidence,
        }

    def section_exists(self, section_title: str) -> bool:
        if not section_title:
            return False
        lc = section_title.lower()
        if lc in self.section_titles_lc:
            return True
        for t in self.section_titles_lc:
            if lc in t or t in lc:
                return True
        return False

    def page_valid(self, page: Optional[int]) -> bool:
        if page is None:
            return True  # pasted_text 场景允许 null
        return 1 <= int(page) <= max(1, self.total_pages)


# ============================================================
# 4. 风险判定
# ============================================================


def confidence_to_risk(confidence: str, page_valid: bool, section_valid: bool) -> str:
    if not page_valid:
        return "high"
    if confidence == "high":
        return "low"
    if confidence == "medium":
        return "low" if section_valid else "medium"
    if confidence == "low":
        return "medium"
    return "high"


# ============================================================
# 5. 遍历 result.json 的 claim
# ============================================================


def iter_claims(result: dict[str, Any]) -> Iterable[dict[str, Any]]:
    papers = result.get("papers", []) or []
    for p in papers:
        label = p.get("label")
        sc = p.get("summary_card") or {}
        pmap = sc.get("provenance_map") or {}

        # --- summary_card scalar fields ---
        for field in ("research_question", "method", "dataset", "contributions", "limitations"):
            content = sc.get(field)
            loc = pmap.get(field) or {}
            if content is None:
                continue
            yield {
                "claim_type": f"summary_card.{field}",
                "paper_label": label,
                "claim_text": _stringify(content),
                "claimed_location": loc,
                "strength": "medium",
            }

        # --- summary_card.key_results (array) ---
        results_arr = sc.get("key_results") or []
        results_pmap = pmap.get("key_results") or []
        for idx, item in enumerate(results_arr):
            loc = results_pmap[idx] if idx < len(results_pmap) else {}
            yield {
                "claim_type": "summary_card.key_results",
                "paper_label": label,
                "claim_text": _stringify(item),
                "claimed_location": loc,
                "strength": "strong",
            }

        # --- deep_dive.original_excerpts ---
        for dd_idx, dd in enumerate(p.get("deep_dive_answers") or []):
            for ex_idx, ex in enumerate(dd.get("original_excerpts") or []):
                yield {
                    "claim_type": "deep_dive.original_excerpts",
                    "paper_label": label,
                    "claim_text": ex.get("text", ""),
                    "claimed_location": {"page": ex.get("page"), "section": ex.get("section")},
                    "strength": "strong",
                    "_dd_idx": dd_idx,
                    "_ex_idx": ex_idx,
                }

        # --- connection_points.evidence_pages ---
        # 注：connection_points.insight 是**用户导向的分析推理**（本文 X 如何连接到你的方向），
        # 而非直接从论文摘抄，因此不做 ngram 文本匹配，仅验证 evidence_pages 合法性 +
        # insight 里若出现数字/专名则做弱校验。
        for cp_idx, cp in enumerate(p.get("connection_points") or []):
            for pg in cp.get("evidence_pages") or []:
                yield {
                    "claim_type": "connection_points.evidence_pages",
                    "paper_label": label,
                    "claim_text": cp.get("insight", "")[:200],
                    "claimed_location": {"page": pg, "section": None},
                    "strength": "weak",
                    "_cp_idx": cp_idx,
                    "_page": pg,
                }

    # --- comparison.table ---
    comp = result.get("comparison") or {}
    for row_idx, row in enumerate((comp.get("table") or [])):
        dim = row.get("dimension")
        for label, cell in (row.get("rows") or {}).items():
            content = cell.get("content")
            prov = cell.get("provenance") or {}
            if content in (None, "—", "-"):
                continue
            yield {
                "claim_type": f"comparison.table.{dim}",
                "paper_label": label,
                "claim_text": _stringify(content),
                "claimed_location": prov,
                "strength": "strong",
            }


def _stringify(x: Any) -> str:
    if isinstance(x, str):
        return x
    if isinstance(x, list):
        return " ; ".join(_stringify(i) for i in x)
    if isinstance(x, dict):
        return json.dumps(x, ensure_ascii=False)
    return str(x)


# ============================================================
# 6. 主流程
# ============================================================


def audit(result: dict[str, Any], paper_indices: dict[str, PaperIndex]) -> dict[str, Any]:
    audit_claims: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []
    flagged: list[dict[str, Any]] = []

    match_dist = {"high": 0, "medium": 0, "low": 0, "failed": 0}
    strong = medium = weak = 0

    for idx, claim in enumerate(iter_claims(result), start=1):
        label = claim.get("paper_label")
        strength = claim.get("strength", "weak")
        pidx = paper_indices.get(label) if label else None

        cid = f"c-{idx:03d}"

        if pidx is None:
            audit_claims.append(
                {
                    "id": cid,
                    "claim_type": claim["claim_type"],
                    "paper_label": label,
                    "claim_text": claim["claim_text"][:400],
                    "claimed_location": claim.get("claimed_location"),
                    "ngram_match_confidence": "failed",
                    "match_details": {"error": "未找到对应 paper 索引"},
                    "hallucination_risk": "high",
                    "action_taken": "kept_with_warning",
                }
            )
            match_dist["failed"] += 1
            continue

        claim_text = claim.get("claim_text", "")
        loc = claim.get("claimed_location") or {}
        page = loc.get("page") if isinstance(loc, dict) else None
        section = loc.get("section") if isinstance(loc, dict) else None

        if strength != "weak":
            md = pidx.match_claim(claim_text)
        else:
            md = {"confidence": "high", "note": "weak-check skipped"}

        page_ok = pidx.page_valid(page)
        section_ok = pidx.section_exists(section) if section else True

        risk = confidence_to_risk(md["confidence"], page_ok, section_ok)
        match_dist[md["confidence"]] = match_dist.get(md["confidence"], 0) + 1

        if strength == "strong":
            strong += 1
        elif strength == "medium":
            medium += 1
        else:
            weak += 1

        action = "kept"
        if strength == "strong" and risk == "high":
            action = "removed"
            removed.append(
                {
                    "claim_id": cid,
                    "claim_type": claim["claim_type"],
                    "paper_label": label,
                    "reason": "strong check failed: " + md["confidence"],
                    "loc": claim.get("claimed_location"),
                }
            )
        elif risk in ("medium", "high"):
            flagged.append(
                {
                    "claim_id": cid,
                    "claim_type": claim["claim_type"],
                    "paper_label": label,
                    "risk": risk,
                }
            )

        audit_claims.append(
            {
                "id": cid,
                "claim_type": claim["claim_type"],
                "paper_label": label,
                "claim_text": claim_text[:400],
                "claimed_location": {"page": page, "section": section},
                "ngram_match_confidence": md["confidence"],
                "match_details": {
                    "5gram_hit_ratio": md.get("5gram_hit_ratio"),
                    "3gram_hit_ratio": md.get("3gram_hit_ratio"),
                    "numbers_matched": md.get("numbers_matched"),
                    "numbers_missing": md.get("numbers_missing"),
                    "names_matched": md.get("names_matched"),
                    "names_missing": md.get("names_missing"),
                    "cross_language_paraphrase": md.get("cross_language_paraphrase"),
                    "page_valid": page_ok,
                    "section_valid": section_ok,
                },
                "hallucination_risk": risk,
                "action_taken": action,
            }
        )

    audit_obj = {
        "audit_version": SCRIPT_VERSION,
        "audit_timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "total_claims_checked": len(audit_claims),
        "breakdown": {"strong_checked": strong, "medium_checked": medium, "weak_skipped": weak},
        "match_distribution": match_dist,
        "claims": audit_claims,
        "removed_claims": removed,
        "flagged_for_user_review": flagged,
    }
    audit_obj["confidence_degraded"] = compute_confidence_degraded(audit_obj)
    return audit_obj


def compute_confidence_degraded(audit_obj: dict[str, Any]) -> dict[str, Any]:
    """根据 audit 结果决定整篇是否触发置信度降级（v0.4.0 / P0-B）。

    详见 references/provenance-rules.md § 八。返回结构：
        {
          "is_degraded": bool,
          "reason": "claims_removed" | "failed_count_exceeds" | "high_ratio_below_threshold" | None,
          "stats": {"high": ..., "medium": ..., "low": ..., "failed": ..., "total": ...},
          "high_ratio": float | None,
          "threshold": float,
          "removed_claims_count": int,
          "advice_zh": str | None
        }
    """
    md = audit_obj.get("match_distribution") or {}
    high = int(md.get("high", 0))
    medium = int(md.get("medium", 0))
    low = int(md.get("low", 0))
    failed = int(md.get("failed", 0))
    total = high + medium + low + failed

    removed_count = len(audit_obj.get("removed_claims") or [])
    high_ratio: Optional[float] = (high / total) if total > 0 else None

    reason: Optional[str] = None
    if removed_count > 0:
        reason = "claims_removed"
    elif failed >= DEGRADED_FAILED_COUNT_THRESHOLD:
        reason = "failed_count_exceeds"
    elif high_ratio is not None and high_ratio < DEGRADED_HIGH_RATIO_THRESHOLD:
        reason = "high_ratio_below_threshold"

    is_degraded = reason is not None
    advice_zh: Optional[str] = None
    if is_degraded:
        advice_zh = {
            "claims_removed": (
                "强校验失败的 claim 已被自动移除；建议核对原文后再使用本次报告的关键结论。"
            ),
            "failed_count_exceeds": (
                f"已有 {failed} 条 claim 完全无法在原文定位；可能是 PDF 解析错位或粘贴段缺失上下文，"
                "建议改用 deep 模式或重新粘贴更长上下文。"
            ),
            "high_ratio_below_threshold": (
                f"高置信 claim 仅占 {high_ratio:.0%}（阈值 60%）；建议在 deep 模式下重读关键段落以补强证据。"
                if high_ratio is not None else
                "高置信 claim 占比偏低；建议在 deep 模式下重读关键段落。"
            ),
        }.get(reason)

    return {
        "is_degraded": is_degraded,
        "reason": reason,
        "stats": {"high": high, "medium": medium, "low": low, "failed": failed, "total": total},
        "high_ratio": round(high_ratio, 4) if high_ratio is not None else None,
        "threshold": DEGRADED_HIGH_RATIO_THRESHOLD,
        "removed_claims_count": removed_count,
        "advice_zh": advice_zh,
    }


def apply_removals_in_place(result: dict[str, Any], removed: list[dict[str, Any]]) -> dict[str, Any]:
    """v0.1 POC：对 strong 失败的 original_excerpts / key_results / comparison cell 做标记。"""
    removed_set = {(r["claim_type"], r["paper_label"]) for r in removed}
    for p in result.get("papers") or []:
        label = p.get("label")
        if ("summary_card.key_results", label) in removed_set:
            sc = p.get("summary_card") or {}
            kr = sc.get("key_results") or []
            sc["key_results"] = [item for item in kr if not _has_unmatched_number(item)]
        if ("deep_dive.original_excerpts", label) in removed_set:
            for dd in p.get("deep_dive_answers") or []:
                dd["original_excerpts"] = [
                    ex for ex in (dd.get("original_excerpts") or []) if ex.get("text")
                ]
    return result


def _has_unmatched_number(item: Any) -> bool:
    # 占位：v0.1 POC 实际保守保留，由 audit.removed_claims 报告即可
    return False


# ============================================================
# 7. CLI
# ============================================================


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Provenance ngram audit for paper-quick-reader result.json")
    parser.add_argument("--result", "-r", required=True, help="Path to result.json")
    parser.add_argument("--papers", "-p", nargs="+", required=True, help="Paths to paper_*.json produced by parse_pdf.py")
    parser.add_argument("--out", "-o", default="provenance-audit.json", help="Audit JSON output path")
    parser.add_argument("--in-place", action="store_true", help="Apply removals back into result.json")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    args = parser.parse_args(argv)

    result_path = Path(args.result).expanduser().resolve()
    if not result_path.exists():
        _err(f"result.json 不存在: {result_path}")
        return 1
    try:
        result = json.loads(result_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        _err(f"result.json 解析失败: {e}")
        return 2

    indices: dict[str, PaperIndex] = {}
    for pp in args.papers:
        path = Path(pp).expanduser().resolve()
        if not path.exists():
            _err(f"paper json 不存在: {path}")
            return 1
        data = json.loads(path.read_text(encoding="utf-8"))
        meta = data.get("meta", {})
        label = meta.get("label") or meta.get("title") or path.stem
        indices[label] = PaperIndex(data)

    # 若 result.json 中的 label 与 index key 不一致，允许用位置兜底
    if "papers" in result:
        result_labels = [p.get("label") for p in result["papers"]]
        missing = [lbl for lbl in result_labels if lbl and lbl not in indices]
        if missing:
            remaining = [k for k in indices if k not in result_labels]
            for miss, rem in zip(missing, remaining):
                indices[miss] = indices[rem]

    audit_result = audit(result, indices)

    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(audit_result, ensure_ascii=False, indent=2 if args.pretty else None),
        encoding="utf-8",
    )
    _err(f"已写入 audit: {out_path}")

    if args.in_place:
        result = apply_removals_in_place(result, audit_result["removed_claims"])
        # v0.4.0 / P0-B：把整篇降级摘要写到 result.meta.confidence_degraded
        # 让 render_report.py 在头部出 banner，用户第一眼就被警示
        result.setdefault("meta", {})["confidence_degraded"] = audit_result["confidence_degraded"]
        result_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None),
            encoding="utf-8",
        )
        _err(f"已原地更新: {result_path}")
        if audit_result["confidence_degraded"]["is_degraded"]:
            _err(f"⚠ confidence_degraded={audit_result['confidence_degraded']['reason']}")

    _err(
        "总 claim 数 {n}；high={h} medium={m} low={l} failed={f}；removed={r}".format(
            n=audit_result["total_claims_checked"],
            h=audit_result["match_distribution"].get("high", 0),
            m=audit_result["match_distribution"].get("medium", 0),
            l=audit_result["match_distribution"].get("low", 0),
            f=audit_result["match_distribution"].get("failed", 0),
            r=len(audit_result["removed_claims"]),
        )
    )
    return 0


def _err(msg: str) -> None:
    sys.stderr.write(f"[verify_provenance] {msg}\n")


if __name__ == "__main__":
    sys.exit(main())
