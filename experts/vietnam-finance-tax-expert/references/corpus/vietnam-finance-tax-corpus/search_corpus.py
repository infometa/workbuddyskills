#!/usr/bin/env python3
"""
越南财税语料库 TF-IDF 语义检索脚本
====================================
接受查询文本，返回 top-K 最相关的语料块及其元数据。

用法：
    python search_corpus.py "越南企业所得税税率" --top-k 10 [--json]
"""

import json
import pickle
import sys
import time
from pathlib import Path

import numpy as np
from scipy.sparse import load_npz
from sklearn.metrics.pairwise import cosine_similarity

CORPUS_DIR = Path(__file__).resolve().parent
VECTORIZER_PATH = CORPUS_DIR / "tfidf_vectorizer.pkl"
MATRIX_PATH = CORPUS_DIR / "tfidf_matrix.npz"
META_PATH = CORPUS_DIR / "chunks_metadata.json"


def load_index():
    with open(VECTORIZER_PATH, "rb") as f:
        vectorizer = pickle.load(f)
    tfidf_matrix = load_npz(str(MATRIX_PATH))
    with open(META_PATH, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    return vectorizer, tfidf_matrix, metadata


def search(query: str, vectorizer, tfidf_matrix, metadata, top_k: int = 10):
    """执行 TF-IDF 语义检索"""
    query_vec = vectorizer.transform([query])
    similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()
    top_indices = np.argsort(similarities)[::-1][:top_k]

    results = []
    seen_files = set()
    file_limit = 3  # 每个源文件最多返回条数

    for idx in top_indices:
        if similarities[idx] < 0.01:  # 过滤掉完全不相关的
            continue
        source_file = metadata[idx]["source_file"]
        if source_file in seen_files:
            if sum(1 for r in results if r["source_file"] == source_file) >= file_limit:
                continue
        seen_files.add(source_file)

        results.append({
            "rank": len(results) + 1,
            "score": round(float(similarities[idx]), 4),
            "chunk_id": metadata[idx]["id"],
            "source_file": source_file,
            "source_label": metadata[idx]["source_label"],
            "preview": metadata[idx]["preview"],
            "char_count": metadata[idx]["char_count"],
        })
        if len(results) >= top_k:
            break

    return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description="越南财税语料库语义检索")
    parser.add_argument("query", help="搜索查询文本")
    parser.add_argument("--top-k", type=int, default=10, help="返回结果数")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出")
    parser.add_argument("--files-only", action="store_true", help="仅输出源文件名列表")
    args = parser.parse_args()

    if not VECTORIZER_PATH.exists():
        print("[ERROR] 索引不存在，请先运行 build_index.py", file=sys.stderr)
        sys.exit(1)

    t0 = time.time()
    vectorizer, tfidf_matrix, metadata = load_index()
    load_time = time.time() - t0

    t0 = time.time()
    results = search(args.query, vectorizer, tfidf_matrix, metadata, args.top_k)
    search_time = time.time() - t0

    if args.files_only:
        for r in results:
            print(r["source_file"])
        return

    if args.json:
        output = {
            "query": args.query,
            "total_chunks": len(metadata),
            "results": results,
            "timing": {"load_ms": round(load_time * 1000), "search_ms": round(search_time * 1000)},
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return

    # 人类可读输出
    print(f"\n查询: \"{args.query}\"")
    print(f"语料库总量: {len(metadata)} 个分块")
    print(f"索引加载: {load_time*1000:.0f}ms | 检索耗时: {search_time*1000:.0f}ms")
    print("-" * 60)

    if not results:
        print("未找到相关结果。")
        return

    for r in results:
        print(f"\n[{r['rank']}] 相似度: {r['score']:.4f} | {r['source_label']} — {r['source_file']}")
        print(f"    {r['preview'][:150]}...")
        print(f"    全文长度: {r['char_count']} 字符")

    print(f"\n共 {len(results)} 条结果")


if __name__ == "__main__":
    main()
