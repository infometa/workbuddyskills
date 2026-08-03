# -*- coding: utf-8 -*-
"""
语义向量索引构建脚本（可选 / 可选依赖）
Semantic Embedding Index Builder for South Africa HR & Admin Corpus

目的：
  对语料库生成句向量索引 semantic_embeddings.npz，使 search_corpus_semantic.py
  在已生成索引时直接加载，免去每次查询重新编码（快几十倍）。

关键设计 —— 与 TF-IDF 层 chunk 对齐：
  - 默认直接读取 build_index.py 产出的 chunks_metadata.json 中的「完整块文本 text」，
    逐块编码。因为 TF-IDF 层与语义层用的是同一份 chunk 记录，检索结果天然对齐。
  - 若 chunks_metadata.json 缺失，则复用 build_index.py 的同一套扫描+切分函数
    （chunk_text / extract_text_* / SKIP_DIRS）重建完全相同的 chunk 序列，再编码。

依赖：
  pip install sentence-transformers numpy
  首次运行会下载多语言模型（约 120–470MB，取决于所选模型）。

用法：
  python build_semantic_index.py
  python build_semantic_index.py --model sentence-transformers/paraphrase-multilingual-mpnet-base-v2
  python build_semantic_index.py --force   # 即便已存在索引也重建
"""

import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
META = os.path.join(HERE, "chunks_metadata.json")
EMB_PATH = os.path.join(HERE, "semantic_embeddings.npz")
IDS_PATH = os.path.join(HERE, "semantic_ids.json")

# 与 search_corpus_semantic.py 保持一致，确保语义检索/索引用同一模型
DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def _load_chunks_via_metadata():
    """优先：直接读取 TF-IDF 层产出的同一份 chunk 记录（保证对齐）。"""
    if not os.path.exists(META):
        return None
    with open(META, "r", encoding="utf-8") as f:
        meta = json.load(f)
    chunks = []
    for m in meta:
        text = m.get("text") or m.get("preview", "")
        if not text or len(text) < 20:
            continue
        chunks.append({
            "id": m.get("id", ""),
            "text": text,
            "source_file": m.get("source_file", ""),
            "source_path": m.get("source_path", ""),
        })
    return chunks


def _load_chunks_via_build_index():
    """回退：复用 build_index.py 的同一套切分逻辑重建 chunk 序列。"""
    sys.path.insert(0, HERE)
    import build_index as bi  # noqa: E402

    all_chunks = []
    for filepath in sorted(bi.CORPUS_DIR.rglob("*")):
        if not filepath.is_file():
            continue
        if filepath.name in bi.SKIP_NAMES:
            continue
        rel_parts = filepath.relative_to(bi.CORPUS_DIR).parts
        if any(part in bi.SKIP_DIRS for part in rel_parts):
            continue
        ext = filepath.suffix.lower()
        if ext == ".md":
            text = bi.extract_text_from_md(filepath)
        elif ext == ".txt":
            text = bi.extract_text_from_txt(filepath)
        elif ext == ".html":
            text = bi.extract_text_from_html(filepath)
        else:
            continue
        if not text or len(text) < 50:
            continue
        category = bi.get_category_from_path(filepath)
        for i, chunk in enumerate(bi.chunk_text(text)):
            all_chunks.append({
                "id": f"{filepath.stem}_{i:04d}",
                "text": chunk,
                "source_file": filepath.name,
                "source_path": str(filepath.relative_to(bi.CORPUS_DIR)),
                "category": category,
                "chunk_index": i,
            })
    return all_chunks


def main():
    p = argparse.ArgumentParser(description="构建南非人力行政语料语义向量索引")
    p.add_argument("--model", type=str, default=DEFAULT_MODEL, help="句向量模型名")
    p.add_argument("--force", action="store_true", help="即便已存在索引也重建")
    args = p.parse_args()

    if os.path.exists(EMB_PATH) and not args.force:
        print("[SKIP] semantic_embeddings.npz 已存在，如需重建请加 --force")
        return

    try:
        import numpy as np
        from sentence_transformers import SentenceTransformer
    except Exception as e:  # noqa: BLE001
        print(f"[ERROR] 无法加载依赖（sentence-transformers / numpy）：{e}", file=sys.stderr)
        print("        请先安装： pip install sentence-transformers numpy", file=sys.stderr)
        sys.exit(1)

    print("=" * 60)
    print("  南非人力行政语料 — 语义向量索引构建")
    print("=" * 60)

    print("[1/3] 载入 chunk（与 TF-IDF 层对齐）...")
    t0 = time.time()
    chunks = _load_chunks_via_metadata()
    if not chunks:
        print("      chunks_metadata.json 缺失，回退至 build_index.py 重建切分...")
        chunks = _load_chunks_via_build_index()
    if not chunks:
        print("[ERROR] 没有可用 chunk，请先运行 build_index.py --force", file=sys.stderr)
        sys.exit(1)
    print(f"      载入 {len(chunks)} 个 chunk（{time.time() - t0:.1f}s）")

    print(f"[2/3] 用模型 {args.model} 编码（首次可能下载模型）...")
    t0 = time.time()
    model = SentenceTransformer(args.model)
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        batch_size=32,
        show_progress_bar=True,
    )
    embeddings = np.asarray(embeddings, dtype="float32")
    print(f"      编码完成：矩阵 {embeddings.shape}（{time.time() - t0:.1f}s）")

    print("[3/3] 保存索引...")
    np.savez_compressed(EMB_PATH, embeddings=embeddings)
    ids = [c["id"] for c in chunks]
    with open(IDS_PATH, "w", encoding="utf-8") as f:
        json.dump(ids, f, ensure_ascii=False)
    size_mb = os.path.getsize(EMB_PATH) / 1024 / 1024
    print(f"      索引: {EMB_PATH} ({size_mb:.2f} MB)")
    print(f"      ID : {IDS_PATH} ({len(ids)} 条)")
    print()
    print("=" * 60)
    print("  语义向量索引构建完成！")
    print("  现在运行 search_corpus_semantic.py 将自动加载本索引（无需每次重编码）。")
    print("=" * 60)


if __name__ == "__main__":
    main()
