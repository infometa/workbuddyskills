# -*- coding: utf-8 -*-
"""
语义检索升级 v1.0（可选 / 可选依赖）
Semantic Search Upgrade for Vietnam Finance & Tax Corpus

在原有 TF-IDF 检索(search_corpus.py) 基础上，提供基于句向量的语义检索：
  - 若环境已安装 sentence-transformers，则用多语言嵌入模型做语义匹配（长尾法规、同义表述更强）；
  - 若未安装，则自动回退到原有 TF-IDF 检索，保证专家包“零依赖、可移植”不破防。

安装（可选，会引入模型下载，非必需）：
  pip install sentence-transformers
  # 首次运行会下载 multilingual-e5-small 或 paraphrase-multilingual-MiniLM

用法：
  python search_corpus_semantic.py "越南建厂选址 综合成本" --top-k 10
"""

import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(os.path.dirname(HERE), "corpus", "vietnam-finance-tax-corpus")
META = os.path.join(CORPUS, "chunks_metadata.json")
TFIDF = os.path.join(CORPUS, "search_corpus.py")
MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def _fallback_tfidf(query, top_k):
    print("[info] 未检测到 sentence-transformers，回退至 TF-IDF 检索。\n", file=sys.stderr)
    subprocess.run([sys.executable, TFIDF, query, "--top-k", str(top_k)])


def _semantic(query, top_k):
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
    except Exception as e:  # noqa: BLE001
        print(f"[warn] 无法加载语义模型依赖：{e}", file=sys.stderr)
        _fallback_tfidf(query, top_k)
        return

    print(f"[info] 使用语义模型 {MODEL} 检索（首次可能下载模型）...", file=sys.stderr)
    with open(META, "r", encoding="utf-8") as f:
        meta = json.load(f)
    texts = [m.get("text", "") for m in meta]
    model = SentenceTransformer(MODEL)
    q_emb = model.encode([query], normalize_embeddings=True)
    c_emb = model.encode(texts, normalize_embeddings=True, batch_size=64)
    sims = (c_emb @ q_emb[0])
    idx = np.argsort(-sims)[:top_k]
    print(f"\n语义检索 top-{top_k} 结果：")
    for i in idx:
        m = meta[i]
        print(f"  [{sims[i]:.3f}] {m.get('source_file','?')} | {m.get('text','')[:120]}")


def main():
    p = argparse.ArgumentParser(description="越南财税语料语义检索（可选升级）")
    p.add_argument("query", type=str, help="查询文本")
    p.add_argument("--top-k", type=int, default=10)
    p.add_argument("--force-tfidf", action="store_true", help="强制使用原 TF-IDF")
    args = p.parse_args()

    if args.force_tfidf:
        _fallback_tfidf(args.query, args.top_k)
    else:
        _semantic(args.query, args.top_k)


if __name__ == "__main__":
    main()
