#!/usr/bin/env python3
"""
南非人力行政语料库 TF-IDF 语义检索脚本
======================================
接受查询文本，返回 top-K 最相关的语料块及其元数据。
支持双模式：sklearn 可用时用 sklearn，不可用时用纯 Python TF-IDF。

用法：
    python search_corpus.py "南非最低工资标准" --top-k 10 [--json] [--files-only]
"""

import json
import math
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

CORPUS_DIR = Path(__file__).resolve().parent
VECTORIZER_PATH = CORPUS_DIR / "tfidf_vectorizer.pkl"
MATRIX_PATH = CORPUS_DIR / "tfidf_matrix.npz"
META_PATH = CORPUS_DIR / "chunks_metadata.json"
PURE_INDEX_PATH = CORPUS_DIR / "tfidf_index.json"


def tokenize(text: str) -> list:
    """简易分词：中英文混合"""
    tokens = []
    en_words = re.findall(r"[a-zA-Z]{2,}", text.lower())
    tokens.extend(en_words)
    cn_chars = re.findall(r"[\u4e00-\u9fff]", text)
    for i in range(len(cn_chars) - 1):
        tokens.append(cn_chars[i] + cn_chars[i + 1])
    tokens.extend(cn_chars)
    return tokens


def build_pure_index_from_meta(metadata: list):
    """从 chunks_metadata.json 的完整正文实时构建纯 Python TF-IDF 索引。

    为什么需要它：build_index.py 是"二选一"逻辑——打包机装了 sklearn 就只产出
    tfidf_vectorizer.pkl + tfidf_matrix.npz，永远不会生成 tfidf_index.json。
    于是在没装 sklearn 的目标机上，回退链会断裂并静默返回空结果。
    这里改为按需实时构建（583 块实测约 130ms），使回退链在任何机器上都闭合，
    且无需把 7.9MB 的落盘索引塞进包里。
    """
    texts = [(m.get("text") or m.get("preview") or "") for m in metadata]
    if not any(texts):
        raise RuntimeError(
            "chunks_metadata.json 中既无 text 也无 preview，无法构建检索索引"
        )

    docs_tokens = [tokenize(t) for t in texts]
    n_docs = len(docs_tokens)

    df = defaultdict(int)
    for tokens in docs_tokens:
        for term in set(tokens):
            df[term] += 1

    idf = {term: math.log((n_docs + 1) / (df_val + 1)) + 1 for term, df_val in df.items()}

    vectors = []
    for tokens in docs_tokens:
        tf = Counter(tokens)
        total = len(tokens) or 1
        vectors.append({term: (count / total) * idf.get(term, 0)
                        for term, count in tf.items()})

    return {"idf": idf, "vectors": vectors, "mode": "pure_python_runtime"}


def load_pure_index(metadata: list):
    """优先用预构建的 tfidf_index.json；缺失或与语料不匹配时实时构建。"""
    if PURE_INDEX_PATH.exists():
        try:
            with open(PURE_INDEX_PATH, "r", encoding="utf-8") as f:
                index_data = json.load(f)
            if len(index_data.get("vectors", [])) == len(metadata):
                return index_data
            print(f"  [WARN] {PURE_INDEX_PATH.name} 与当前语料块数不一致，改为实时构建索引",
                  file=sys.stderr)
        except Exception as e:
            print(f"  [WARN] 读取 {PURE_INDEX_PATH.name} 失败({e})，改为实时构建索引",
                  file=sys.stderr)

    t0 = time.time()
    index_data = build_pure_index_from_meta(metadata)
    print(f"  [INFO] 已实时构建纯 Python TF-IDF 索引（{len(metadata)} 块，"
          f"{(time.time() - t0) * 1000:.0f}ms，无需第三方库）", file=sys.stderr)
    return index_data


def search_pure_python(query: str, metadata: list, top_k: int = 10):
    """纯 Python TF-IDF 检索（零第三方依赖）"""
    index_data = load_pure_index(metadata)

    idf = index_data["idf"]
    vectors = index_data["vectors"]

    # 计算查询向量
    query_tokens = tokenize(query)
    query_tf = Counter(query_tokens)
    total = len(query_tokens) if query_tokens else 1
    query_vec = {}
    for term, count in query_tf.items():
        tf_val = count / total
        query_vec[term] = tf_val * idf.get(term, 0)

    # 计算余弦相似度
    query_norm = math.sqrt(sum(v * v for v in query_vec.values())) or 1
    similarities = []

    for i, doc_vec in enumerate(vectors):
        # 点积
        dot = sum(query_vec.get(term, 0) * weight for term, weight in doc_vec.items())
        doc_norm = math.sqrt(sum(v * v for v in doc_vec.values())) or 1
        sim = dot / (query_norm * doc_norm)
        similarities.append((i, sim))

    # 排序
    similarities.sort(key=lambda x: x[1], reverse=True)

    results = []
    seen_files = set()
    file_limit = 3

    for idx, sim in similarities:
        if sim < 0.001:
            continue
        source_file = metadata[idx]["source_file"]
        if source_file in seen_files:
            if sum(1 for r in results if r["source_file"] == source_file) >= file_limit:
                continue
        seen_files.add(source_file)

        results.append({
            "rank": len(results) + 1,
            "score": round(float(sim), 4),
            "chunk_id": metadata[idx]["id"],
            "source_file": source_file,
            "source_path": metadata[idx].get("source_path", ""),
            "source_label": metadata[idx]["source_label"],
            "category": metadata[idx].get("category", ""),
            "preview": metadata[idx]["preview"],
            "char_count": metadata[idx]["char_count"],
        })
        if len(results) >= top_k:
            break

    return results


def search_sklearn(query: str, metadata: list, top_k: int = 10):
    """sklearn TF-IDF 检索"""
    import pickle
    import numpy as np
    from scipy.sparse import load_npz
    from sklearn.metrics.pairwise import cosine_similarity

    with open(VECTORIZER_PATH, "rb") as f:
        vectorizer = pickle.load(f)
    tfidf_matrix = load_npz(str(MATRIX_PATH))

    query_vec = vectorizer.transform([query])
    similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()
    top_indices = np.argsort(similarities)[::-1][:top_k * 3]  # 多取一些用于去重

    results = []
    seen_files = set()
    file_limit = 3

    for idx in top_indices:
        if similarities[idx] < 0.01:
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
            "source_path": metadata[idx].get("source_path", ""),
            "source_label": metadata[idx]["source_label"],
            "category": metadata[idx].get("category", ""),
            "preview": metadata[idx]["preview"],
            "char_count": metadata[idx]["char_count"],
        })
        if len(results) >= top_k:
            break

    return results


class BackendUnavailable(RuntimeError):
    """所有检索后端均不可用——必须显式报错，绝不能伪装成'没有匹配结果'。"""


def search(query: str, metadata: list, top_k: int = 10):
    """自动选择检索模式：sklearn 优先，纯 Python 兜底。

    注意：'检索成功但无匹配' 与 '检索后端不可用' 是两种截然不同的状态。
    后者若被静默处理成空列表，调用方（含 LLM 专家）会误判为'语料中没有该内容'
    而转向凭记忆作答——这比直接报错危险得多。故此处失败即抛异常。
    """
    failures = []

    if VECTORIZER_PATH.exists() and MATRIX_PATH.exists():
        try:
            return search_sklearn(query, metadata, top_k)
        except Exception as e:
            failures.append(f"sklearn 后端: {e}")
            print(f"  [WARN] sklearn 检索不可用({e})，回退纯 Python 模式", file=sys.stderr)

    try:
        return search_pure_python(query, metadata, top_k)
    except Exception as e:
        failures.append(f"纯 Python 后端: {e}")

    raise BackendUnavailable(
        "所有检索后端均不可用，语料未被检索（这不等于语料中没有相关内容）：\n    - "
        + "\n    - ".join(failures)
    )


def main():
    import argparse
    parser = argparse.ArgumentParser(description="南非人力行政语料库语义检索")
    parser.add_argument("query", help="搜索查询文本")
    parser.add_argument("--top-k", type=int, default=10, help="返回结果数")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出")
    parser.add_argument("--files-only", action="store_true", help="仅输出源文件名列表")
    args = parser.parse_args()

    if not META_PATH.exists():
        print("[ERROR] 元数据不存在，请先运行 build_index.py", file=sys.stderr)
        sys.exit(1)

    t0 = time.time()
    with open(META_PATH, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    load_time = time.time() - t0

    t0 = time.time()
    try:
        results = search(args.query, metadata, args.top_k)
    except BackendUnavailable as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        print("[ERROR] 请勿据此认定语料缺少相关内容；可改用 Read/Grep 直接读取语料文件。",
              file=sys.stderr)
        sys.exit(2)
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
    print(f"加载: {load_time*1000:.0f}ms | 检索: {search_time*1000:.0f}ms")
    print("-" * 60)

    if not results:
        print("未找到相关结果。")
        return

    for r in results:
        print(f"\n[{r['rank']}] 相似度: {r['score']:.4f} | {r['source_label']} — {r['source_file']}")
        if r.get("category"):
            print(f"    板块: {r['category']}")
        print(f"    {r['preview'][:150]}...")
        print(f"    全文长度: {r['char_count']} 字符")

    print(f"\n共 {len(results)} 条结果")


if __name__ == "__main__":
    main()
