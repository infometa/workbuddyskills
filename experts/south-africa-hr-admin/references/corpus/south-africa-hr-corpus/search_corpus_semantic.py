# -*- coding: utf-8 -*-
"""
语义检索升级 v1.0（可选 / 可选依赖）
Semantic Search Upgrade for South Africa HR & Admin Corpus

在原有 TF-IDF 检索(search_corpus.py)基础上，提供基于句向量的语义检索：
  - 若环境已安装 sentence-transformers，则用多语言嵌入模型做语义匹配
    （长尾法规、同义表述、中→英跨语言查询更强）；
  - 若未安装，则自动回退到原有 TF-IDF 检索，保证专家包“零依赖、可移植”不破防。

安装（可选，会引入模型下载，非必需）：
  pip install sentence-transformers
  # 首次运行会下载 paraphrase-multilingual-MiniLM-L12-v2

用法：
  python search_corpus_semantic.py "南非外派员工带薪育儿假怎么算" --top-k 10
  python search_corpus_semantic.py "BCEA overtime Sunday pay" --top-k 5 --force-tfidf
"""

import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
META = os.path.join(HERE, "chunks_metadata.json")
TFIDF = os.path.join(HERE, "search_corpus.py")
EMB_PATH = os.path.join(HERE, "semantic_embeddings.npz")
IDS_PATH = os.path.join(HERE, "semantic_ids.json")
# 多语言模型：英文法规 + 中文提问均可编码，首次下载约 470MB
MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def _fallback_tfidf(query, top_k, reason="未检测到 sentence-transformers"):
    """回退至 TF-IDF。必须把子进程退出码透传出去——否则 TF-IDF 侧的
    '检索后端不可用' 会被本脚本吞成 exit 0，重新变成静默失败。"""
    print(f"[info] {reason}，回退至 TF-IDF 检索。\n", file=sys.stderr)
    proc = subprocess.run([sys.executable, TFIDF, query, "--top-k", str(top_k)])
    if proc.returncode != 0:
        sys.exit(proc.returncode)


def _try_load_prebuilt(meta):
    """若 build_semantic_index.py 已生成索引且 chunk 顺序一致，则直接加载。"""
    if not (os.path.exists(EMB_PATH) and os.path.exists(IDS_PATH)):
        return None
    try:
        import numpy as np
        with open(IDS_PATH, "r", encoding="utf-8") as f:
            saved_ids = json.load(f)
        if saved_ids != [m.get("id", "") for m in meta]:
            return None  # metadata 已变化，须重建索引
        data = np.load(EMB_PATH)
        return data["embeddings"]
    except Exception:
        return None


def _semantic(query, top_k):
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
    except Exception as e:  # noqa: BLE001
        print(f"[warn] 无法加载语义模型依赖：{e}", file=sys.stderr)
        _fallback_tfidf(query, top_k)
        return

    if not os.path.exists(META):
        print("[error] 元数据 chunks_metadata.json 不存在，请先运行 build_index.py --force", file=sys.stderr)
        sys.exit(2)

    with open(META, "r", encoding="utf-8") as f:
        meta = json.load(f)
    # 优先用完整块文本 text；缺失时回退 preview
    texts = [m.get("text") or m.get("preview", "") for m in meta]

    # 优先加载预构建语义索引（免去对全语料重新编码）
    c_emb = _try_load_prebuilt(meta)

    # 加载模型：若本机未缓存模型且无网络（换电脑的常见情形），
    # 这里会失败——必须回退 TF-IDF，绝不能让专家包整体不可用。
    try:
        model = SentenceTransformer(MODEL)
    except Exception as e:  # noqa: BLE001
        print(
            f"[warn] 语义模型不可用（多为未缓存模型且无法联网下载）：{str(e)[:150]}",
            file=sys.stderr,
        )
        _fallback_tfidf(query, top_k, reason="语义模型加载失败（离线且无本地模型缓存）")
        return

    try:
        if c_emb is not None:
            print("[info] 已加载预构建语义索引 semantic_embeddings.npz，直接检索。", file=sys.stderr)
        else:
            print(f"[info] 现场编码语料（模型 {MODEL}，首次可能下载）...", file=sys.stderr)
            c_emb = model.encode(texts, normalize_embeddings=True, batch_size=32)
        q_emb = model.encode([query], normalize_embeddings=True)
    except Exception as e:  # noqa: BLE001
        print(f"[warn] 语义编码失败：{str(e)[:150]}", file=sys.stderr)
        _fallback_tfidf(query, top_k, reason="语义编码过程失败")
        return

    sims = (c_emb @ q_emb[0])
    idx = np.argsort(-sims)[:top_k]

    print(f"\n语义检索 top-{top_k} 结果：")
    for i in idx:
        m = meta[i]
        snippet = (m.get("text") or m.get("preview", ""))[:120].replace("\n", " ")
        src = m.get("source_file", "?")
        lbl = m.get("source_label", "")
        cat = m.get("category", "")
        print(f"  [{sims[i]:.3f}] {lbl} — {src}")
        if cat:
            print(f"          板块: {cat}")
        print(f"          {snippet}...")


def main():
    p = argparse.ArgumentParser(description="南非人力行政语料语义检索（可选升级）")
    p.add_argument("query", type=str, help="查询文本（支持中文/英文）")
    p.add_argument("--top-k", type=int, default=10)
    p.add_argument("--force-tfidf", action="store_true", help="强制使用原 TF-IDF")
    args = p.parse_args()

    if args.force_tfidf:
        _fallback_tfidf(args.query, args.top_k)
    else:
        _semantic(args.query, args.top_k)


if __name__ == "__main__":
    main()
