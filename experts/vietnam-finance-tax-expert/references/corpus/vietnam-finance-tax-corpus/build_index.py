#!/usr/bin/env python3
"""
越南财税语料库 TF-IDF 索引构建脚本
====================================
处理655个语料文件（.txt + .html），分块后生成 TF-IDF 向量并保存。
零外部模型下载依赖，秒建索引。

用法：
    python build_index.py [--ngram-min 1] [--ngram-max 3] [--force]
"""

import json
import os
import pickle
import re
import sys
import time
from pathlib import Path

from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer

# ============================================================
# 配置
# ============================================================
CORPUS_DIR = Path(__file__).resolve().parent
VECTORIZER_PATH = CORPUS_DIR / "tfidf_vectorizer.pkl"
MATRIX_PATH = CORPUS_DIR / "tfidf_matrix.npz"
META_PATH = CORPUS_DIR / "chunks_metadata.json"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def extract_text_from_html(filepath: Path) -> str:
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n")
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
    except Exception as e:
        print(f"  [WARN] HTML 解析失败 {filepath.name}: {e}")
        return ""


def extract_text_from_txt(filepath: Path) -> str:
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return f.read().strip()
    except Exception as e:
        print(f"  [WARN] TXT 读取失败 {filepath.name}: {e}")
        return ""


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list:
    if not text:
        return []

    paragraphs = re.split(r"\n\s*\n|(?<=\n)#{1,3} |(?<=\n)第[一二三四五六七八九十百千]+[章节条]", text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    chunks = []
    current_chunk = ""
    char_limit = chunk_size * 1.5

    for para in paragraphs:
        if len(current_chunk) + len(para) <= char_limit:
            current_chunk += ("\n\n" if current_chunk else "") + para
        else:
            if current_chunk:
                chunks.append(current_chunk)
            if len(para) > char_limit:
                sentences = re.split(r"(?<=[。！？\.\!\?])\s*", para)
                sub_chunk = ""
                for sent in sentences:
                    if len(sub_chunk) + len(sent) <= char_limit:
                        sub_chunk += sent
                    else:
                        if sub_chunk:
                            chunks.append(sub_chunk)
                        sub_chunk = sent
                current_chunk = sub_chunk if sub_chunk else ""
            else:
                current_chunk = para

    if current_chunk:
        chunks.append(current_chunk)

    if overlap > 0 and len(chunks) > 1:
        overlapped = []
        for i, chunk in enumerate(chunks):
            if i < len(chunks) - 1:
                next_start = chunks[i + 1][: int(overlap * 1.5)]
                overlapped.append(chunk + "\n" + next_start)
            else:
                overlapped.append(chunk)
        return overlapped

    return chunks


def get_file_label(filename: str) -> str:
    name = Path(filename).stem
    sources = {
        "chinatax": "中国国家税务总局",
        "pwc": "PwC", "kpmg": "KPMG", "ey_": "EY", "mazars": "Mazars",
        "ecovis": "Ecovis", "delco": "Delco", "vcci": "VCCI",
        "aseanbriefing": "ASEAN Briefing", "indochinalink": "Indochina Link",
        "lawma": "Lawma", "luatvietnam": "LuatVietnam", "dazpro": "Dazpro",
        "sbv": "越南国家银行 SBV", "jetro": "JETRO",
        "global_law": "Global Law Experts", "ctils": "CTILS",
        "duane_morris": "Duane Morris", "apluslaw": "A+ Law",
        "alitium": "Alitium", "dg_": "DFDL/DG",
    }
    for prefix, label in sources.items():
        if name.startswith(prefix):
            return label
    return name.split("_")[0] if "_" in name else name


def main():
    import argparse
    parser = argparse.ArgumentParser(description="构建越南财税语料 TF-IDF 索引")
    parser.add_argument("--ngram-min", type=int, default=1, help="n-gram 最小长度")
    parser.add_argument("--ngram-max", type=int, default=3, help="n-gram 最大长度")
    parser.add_argument("--force", action="store_true", help="强制重建")
    args = parser.parse_args()

    if VECTORIZER_PATH.exists() and MATRIX_PATH.exists() and META_PATH.exists() and not args.force:
        print(f"[SKIP] 索引已存在")
        print(f"  vectorizer: {VECTORIZER_PATH}")
        print(f"  matrix: {MATRIX_PATH}")
        print(f"  metadata: {META_PATH}")
        print(f"  如需重建请加 --force")
        return

    print("=" * 60)
    print("  越南财税语料库 — TF-IDF 索引构建")
    print("=" * 60)
    print(f"  语料库目录: {CORPUS_DIR}")
    print(f"  n-gram: ({args.ngram_min}, {args.ngram_max})")
    print()

    # ---- 第一步：扫描文件、分块 ----
    print("[1/3] 扫描语料文件并分块...")
    t0 = time.time()
    txt_files = sorted(CORPUS_DIR.glob("*.txt"))
    html_files = sorted(CORPUS_DIR.glob("*.html"))
    skip_names = {"faiss_index.bin", "chunks_metadata.json", "build_index.py",
                  "MANIFEST.json", "tfidf_vectorizer.pkl", "tfidf_matrix.npz",
                  "search_corpus.py"}

    all_chunks = []
    file_count = 0
    for filepath in txt_files + html_files:
        if filepath.name in skip_names:
            continue
        raw_name = filepath.name.lower()
        if raw_name.endswith("_short.txt"):
            continue

        if filepath.suffix == ".txt":
            text = extract_text_from_txt(filepath)
        else:
            text = extract_text_from_html(filepath)

        if not text:
            continue

        file_count += 1
        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "id": f"{filepath.stem}_{i:04d}",
                "text": chunk,
                "source_file": filepath.name,
                "source_label": get_file_label(filepath.name),
                "chunk_index": i,
                "file_type": filepath.suffix.lstrip("."),
                "char_count": len(chunk),
            })

    print(f"      处理 {file_count} 个文件，产生 {len(all_chunks)} 个文本块 ({time.time() - t0:.1f}s)")

    if not all_chunks:
        print("[ERROR] 没有有效文本，退出。")
        sys.exit(1)

    # ---- 第二步：训练 TF-IDF 向量化器 ----
    print("[2/3] 训练 TF-IDF 向量化器...")
    t0 = time.time()

    vectorizer = TfidfVectorizer(
        ngram_range=(args.ngram_min, args.ngram_max),
        max_features=50000,
        sublinear_tf=True,
        analyzer="char_wb",
        strip_accents="unicode",
        max_df=0.85,
        min_df=2,
    )
    texts = [c["text"] for c in all_chunks]
    tfidf_matrix = vectorizer.fit_transform(texts)

    print(f"      训练完成 ({time.time() - t0:.1f}s)")
    print(f"      词汇量: {len(vectorizer.vocabulary_)}")
    print(f"      矩阵形状: {tfidf_matrix.shape}")
    print(f"      稀疏度: {tfidf_matrix.nnz / (tfidf_matrix.shape[0] * tfidf_matrix.shape[1]) * 100:.2f}%")

    # ---- 第三步：保存 ----
    print("[3/3] 保存索引和元数据...")
    t0 = time.time()

    with open(VECTORIZER_PATH, "wb") as f:
        pickle.dump(vectorizer, f)
    print(f"      vectorizer: {VECTORIZER_PATH}")

    from scipy.sparse import save_npz
    save_npz(str(MATRIX_PATH), tfidf_matrix)
    print(f"      matrix: {MATRIX_PATH}")

    meta_records = []
    for c in all_chunks:
        meta_records.append({
            "id": c["id"],
            "preview": c["text"][:200],
            "source_file": c["source_file"],
            "source_label": c["source_label"],
            "chunk_index": c["chunk_index"],
            "file_type": c["file_type"],
            "char_count": c["char_count"],
        })
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(meta_records, f, ensure_ascii=False, indent=2)
    print(f"      metadata: {META_PATH} ({len(meta_records)} 条)")

    print()
    print("=" * 60)
    print(f"  ✅ TF-IDF 索引构建完成！")
    print(f"     文件数: {file_count}")
    print(f"     分块数: {len(all_chunks)}")
    print(f"     词汇量: {len(vectorizer.vocabulary_)}")
    print(f"     耗时: {time.time() - t0 + 0:.1f}s")
    print("=" * 60)


if __name__ == "__main__":
    main()
