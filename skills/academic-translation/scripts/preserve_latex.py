#!/usr/bin/env python3
"""
preserve_latex.py — 公式 / 引用 / 数字零损伤护城河

核心三个动作：
  1. mask    : 把待保留的 LaTeX 命令 / 公式 / 引用 替换为 <KIND_n> 占位符，发给翻译模型
  2. restore : 翻译完成后还原占位符为原始 token
  3. verify  : 校验译文中所有占位符已还原 + 数字 / 专有名词没被翻译

用法：
  python preserve_latex.py mask    --in source.txt --out masked.json
  python preserve_latex.py restore --in translated.json --out final.txt
  python preserve_latex.py verify  --original source.txt --translated final.txt
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

LATEX_PRESERVE_PATTERNS: List[Tuple[str, str, int]] = [
    (r'\\begin\{equation\*?\}.*?\\end\{equation\*?\}', 'EQUATION', re.DOTALL),
    (r'\\begin\{align\*?\}.*?\\end\{align\*?\}', 'ALIGN', re.DOTALL),
    (r'\\begin\{algorithm\*?\}.*?\\end\{algorithm\*?\}', 'ALGORITHM', re.DOTALL),
    (r'\\begin\{table\*?\}.*?\\end\{table\*?\}', 'TABLE', re.DOTALL),
    (r'\\begin\{figure\*?\}.*?\\end\{figure\*?\}', 'FIGURE', re.DOTALL),
    (r'\$\$[^$]+\$\$', 'DISPLAY_MATH', 0),
    (r'\$[^$\n]+\$', 'INLINE_MATH', 0),
    (r'\\cite[tp]?\{[^}]+\}', 'CITE', 0),
    (r'\\eqref\{[^}]+\}', 'EQREF', 0),
    (r'\\autoref\{[^}]+\}', 'AUTOREF', 0),
    (r'\\ref\{[^}]+\}', 'REF', 0),
    (r'\\label\{[^}]+\}', 'LABEL', 0),
    (r'```[\s\S]*?```', 'CODEBLOCK', 0),
    (r'https?://\S+', 'URL', 0),
]

KNOWN_PROPER_NOUNS = {
    "ImageNet", "COCO", "CIFAR-10", "CIFAR-100", "GLUE", "SuperGLUE",
    "BERT", "GPT", "T5", "BART", "ELMo", "RoBERTa", "XLNet", "LLaMA", "Qwen",
    "Transformer", "RNN", "LSTM", "GRU", "CNN", "ViT", "ResNet", "VGG",
    "Adam", "SGD", "AdamW", "RMSprop",
    "ReLU", "GELU", "Softmax", "Swish",
    "MS-MARCO", "TREC", "BEIR",
    "WordNet", "FrameNet",
    "PageRank", "BM25", "TF-IDF",
    "Spark", "Hadoop", "Flink", "Kafka",
}


def mask_text(text: str) -> Tuple[str, Dict[str, str]]:
    counters: Dict[str, int] = {}
    preserved: Dict[str, str] = {}
    masked = text
    for pattern, kind, flags in LATEX_PRESERVE_PATTERNS:
        def repl(m: re.Match) -> str:
            counters[kind] = counters.get(kind, 0) + 1
            tag = f"<{kind}_{counters[kind]}>"
            preserved[tag] = m.group(0)
            return tag
        masked = re.sub(pattern, repl, masked, flags=flags)
    return masked, preserved


def restore_text(masked_or_translated: str, preserved: Dict[str, str]) -> str:
    out = masked_or_translated
    for tag, original in sorted(preserved.items(), key=lambda kv: -len(kv[0])):
        out = out.replace(tag, original)
    return out


def verify(original: str, translated: str) -> Dict[str, list]:
    issues: Dict[str, list] = {"errors": [], "warnings": []}

    leftover = re.findall(r"<\w+_\d+>", translated)
    if leftover:
        issues["errors"].append(f"占位符未还原: {sorted(set(leftover))[:10]}")

    orig_nums = sorted(set(re.findall(r"\b\d+\.?\d*%?\b", original)))
    trans_nums = sorted(set(re.findall(r"\b\d+\.?\d*%?\b", translated)))
    if orig_nums != trans_nums:
        diff = sorted(set(orig_nums) ^ set(trans_nums))
        issues["warnings"].append(f"数字差异: {diff[:20]}")

    for word in KNOWN_PROPER_NOUNS:
        pattern = r"\b" + re.escape(word) + r"\b"
        orig_count = len(re.findall(pattern, original))
        trans_count = len(re.findall(pattern, translated))
        if orig_count > 0 and trans_count < orig_count:
            issues["warnings"].append(
                f"专有名词「{word}」可能被翻译: 原文 {orig_count} 次 → 译文 {trans_count} 次"
            )

    if "$" in original:
        orig_dollars = original.count("$")
        trans_dollars = translated.count("$")
        if orig_dollars != trans_dollars:
            issues["errors"].append(
                f"行内 $ 数量不一致: 原文 {orig_dollars}, 译文 {trans_dollars}（公式可能被破坏）"
            )

    return issues


def cmd_mask(args: argparse.Namespace) -> int:
    src = Path(args.input).read_text(encoding="utf-8")
    masked, preserved = mask_text(src)
    payload = {"masked": masked, "preserved": preserved, "kinds": {}}
    for tag in preserved:
        kind = tag.strip("<>").rsplit("_", 1)[0]
        payload["kinds"][kind] = payload["kinds"].get(kind, 0) + 1
    Path(args.output).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ Masked → {args.output}")
    print(f"   保留 token 计数: {payload['kinds']}")
    return 0


def cmd_restore(args: argparse.Namespace) -> int:
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    translated = payload.get("translated", payload.get("masked", ""))
    preserved = payload["preserved"]
    restored = restore_text(translated, preserved)
    Path(args.output).write_text(restored, encoding="utf-8")
    print(f"✅ Restored → {args.output}")
    leftover = re.findall(r"<\w+_\d+>", restored)
    if leftover:
        print(f"⚠️  仍有 {len(leftover)} 个占位符未还原: {sorted(set(leftover))[:5]}")
        return 2
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    original = Path(args.original).read_text(encoding="utf-8")
    translated = Path(args.translated).read_text(encoding="utf-8")
    issues = verify(original, translated)
    if not issues["errors"] and not issues["warnings"]:
        print("✅ 公式 / 引用 / 数字保留校验通过")
        return 0
    if issues["errors"]:
        print("🚨 ERRORS:")
        for e in issues["errors"]:
            print(f"   - {e}")
    if issues["warnings"]:
        print("⚠️  WARNINGS:")
        for w in issues["warnings"]:
            print(f"   - {w}")
    return 1 if issues["errors"] else 0


def cmd_check_input(args: argparse.Namespace) -> int:
    """快速检查输入是否为可处理的 PDF / LaTeX / 文本（用于 Preflight P1）."""
    path = Path(args.input)
    if not path.exists():
        print(f"❌ 文件不存在: {path}")
        return 1
    if path.suffix.lower() == ".pdf":
        try:
            import pdfplumber
        except ImportError:
            print("⚠️  pdfplumber 未安装；请先 `pip install pdfplumber`")
            return 2
        with pdfplumber.open(path) as pdf:
            text = (pdf.pages[0].extract_text() or "").strip()
            if len(text) < 100:
                print(f"⚠️  PDF 第一页文本过短（{len(text)} 字符），可能是扫描件，建议先 OCR")
                return 3
            print(f"✅ PDF 可解析（共 {len(pdf.pages)} 页，第一页 {len(text)} 字符）")
            return 0
    elif path.suffix.lower() == ".tex":
        text = path.read_text(encoding="utf-8", errors="ignore")
        if r"\documentclass" not in text and r"\begin{document}" not in text:
            print("⚠️  LaTeX 文件缺少 \\documentclass 或 \\begin{document}，可能是片段")
        print(f"✅ LaTeX 可解析（{len(text)} 字符）")
        return 0
    else:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if len(text.strip()) < 50:
            print(f"⚠️  文本过短（{len(text)} 字符）")
            return 3
        print(f"✅ 文本可解析（{len(text)} 字符）")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="academic-translation 公式 / 引用零损伤工具")
    sub = parser.add_subparsers(dest="cmd", required=True)

    pm = sub.add_parser("mask", help="掩码原文中的 LaTeX 命令和公式")
    pm.add_argument("--in", dest="input", required=True)
    pm.add_argument("--out", dest="output", required=True)
    pm.set_defaults(func=cmd_mask)

    pr = sub.add_parser("restore", help="还原占位符为原始 token")
    pr.add_argument("--in", dest="input", required=True, help="JSON 文件含 translated + preserved")
    pr.add_argument("--out", dest="output", required=True)
    pr.set_defaults(func=cmd_restore)

    pv = sub.add_parser("verify", help="校验译文中所有占位符已还原 + 数字保留")
    pv.add_argument("--original", required=True)
    pv.add_argument("--translated", required=True)
    pv.set_defaults(func=cmd_verify)

    pc = sub.add_parser("check-input", help="快速检查 PDF / LaTeX / 文本输入可解析性（Preflight P1）")
    pc.add_argument("--in", dest="input", required=True)
    pc.set_defaults(func=cmd_check_input)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
