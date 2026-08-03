#!/usr/bin/env python3
"""
南非人力行政语料库 TF-IDF 索引构建脚本
======================================
递归扫描子目录，处理 .md/.txt/.html 语料，分块后生成 TF-IDF 向量并保存。
支持双模式：sklearn 可用时用 sklearn，不可用时回退纯 Python TF-IDF。

用法：
    python build_index.py [--force]
"""

import json
import math
import os
import pickle
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

# ============================================================
# 配置
# ============================================================
CORPUS_DIR = Path(__file__).resolve().parent
VECTORIZER_PATH = CORPUS_DIR / "tfidf_vectorizer.pkl"
MATRIX_PATH = CORPUS_DIR / "tfidf_matrix.npz"
META_PATH = CORPUS_DIR / "chunks_metadata.json"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

SKIP_NAMES = {
    "build_index.py", "search_corpus.py", "search_corpus_semantic.py",
    "chunks_metadata.json",
    "tfidf_vectorizer.pkl", "tfidf_matrix.npz", "MANIFEST.json",
    "tfidf_index.json",  # 纯 Python 模式的索引文件
}

# 整目录跳过：核心法源(primary-sources/)是供逐字引用的官方法案原文/清单，
# 不应被切块当成普通语料索引，否则会污染检索结果。
SKIP_DIRS = {
    "primary-sources",
}


def extract_text_from_md(filepath: Path) -> str:
    """从 Markdown 文件提取纯文本"""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        # 去除 YAML frontmatter
        text = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.DOTALL)
        # 去除代码块
        text = re.sub(r"```[\s\S]*?```", "", text)
        # 去除 HTML 标签
        text = re.sub(r"<[^>]+>", "", text)
        # 去除 Markdown 链接，保留文本
        text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
        # 去除图片
        text = re.sub(r"!\[([^\]]*)\]\([^\)]+\)", "", text)
        # 去除标题标记
        text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
        # 去除粗体/斜体
        text = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", text)
        # 去除引用
        text = re.sub(r"^>\s+", "", text, flags=re.MULTILINE)
        # 去除列表标记
        text = re.sub(r"^[\-\*\+]\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"^\d+\.\s+", "", text, flags=re.MULTILINE)
        # 去除水平线
        text = re.sub(r"^---+$", "", text, flags=re.MULTILINE)
        # 压缩多余空行
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
    except Exception as e:
        print(f"  [WARN] MD 解析失败 {filepath.name}: {e}")
        return ""


def extract_text_from_txt(filepath: Path) -> str:
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return f.read().strip()
    except Exception as e:
        print(f"  [WARN] TXT 读取失败 {filepath.name}: {e}")
        return ""


def extract_text_from_html(filepath: Path) -> str:
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        # 简易 HTML 文本提取（不依赖 bs4）
        for tag in ["script", "style", "nav", "footer", "header"]:
            text = re.sub(rf"<{tag}[^>]*>[\s\S]*?</{tag}>", "", text, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"&nbsp;", " ", text)
        text = re.sub(r"&amp;", "&", text)
        text = re.sub(r"&lt;", "<", text)
        text = re.sub(r"&gt;", ">", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
    except Exception as e:
        print(f"  [WARN] HTML 解析失败 {filepath.name}: {e}")
        return ""


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list:
    if not text:
        return []

    # 按段落分割
    paragraphs = re.split(r"\n\s*\n|(?<=\n)#{1,3} |(?<=\n)第[一二三四五六七八九十百千]+[章节条]|(?<=\n)## ", text)
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
                # 按句子分割超长段落
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

    # 添加重叠
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


def get_category_from_path(filepath: Path) -> str:
    """从文件路径提取板块分类"""
    try:
        rel = filepath.relative_to(CORPUS_DIR)
        parts = rel.parts
        if len(parts) > 1:
            return parts[0]
    except ValueError:
        pass
    return "root"


def get_file_label(filename: str, category: str) -> str:
    """生成人类可读的来源标签"""
    category_labels = {
        "01-labour-law": "劳动法",
        "02-payroll-social-security": "薪酬社保",
        "03-visa-immigration": "签证移民",
        "04-bbbee-employment-equity": "B-BBEE与就业公平",
        "05-company-registration-admin": "公司注册与行政",
        "06-ccma-dispute-resolution": "CCMA争议解决",
        "07-office-facilities": "办公场地",
        "08-occupational-health-safety": "职业安全",
        "09-chinese-practice": "中资实务",
    }
    return category_labels.get(category, category)


# ============================================================
# 纯 Python TF-IDF（无外部依赖）
# ============================================================

def tokenize(text: str) -> list:
    """简易分词：中英文混合"""
    # 英文：按非字母数字分割
    # 中文：按字分割（bigram）
    tokens = []
    # 英文词
    en_words = re.findall(r"[a-zA-Z]{2,}", text.lower())
    tokens.extend(en_words)
    # 中文 bigram
    cn_chars = re.findall(r"[\u4e00-\u9fff]", text)
    for i in range(len(cn_chars) - 1):
        tokens.append(cn_chars[i] + cn_chars[i + 1])
    # 中文单字（作为补充）
    tokens.extend(cn_chars)
    return tokens


def build_pure_python_tfidf(all_chunks: list):
    """构建纯 Python TF-IDF 索引"""
    print("  [纯Python模式] 构建 TF-IDF 索引...")
    t0 = time.time()

    # 分词
    docs_tokens = [tokenize(chunk["text"]) for chunk in all_chunks]
    N = len(docs_tokens)

    # 计算 DF
    df = defaultdict(int)
    for tokens in docs_tokens:
        for term in set(tokens):
            df[term] += 1

    # 计算 IDF
    idf = {}
    for term, df_val in df.items():
        idf[term] = math.log((N + 1) / (df_val + 1)) + 1

    # 计算 TF-IDF 向量
    tfidf_vectors = []
    for tokens in docs_tokens:
        tf = Counter(tokens)
        total = len(tokens) if tokens else 1
        vec = {}
        for term, count in tf.items():
            tf_val = count / total
            vec[term] = tf_val * idf.get(term, 0)
        tfidf_vectors.append(vec)

    # 保存为 JSON 格式
    index_data = {
        "idf": idf,
        "vectors": tfidf_vectors,
        "mode": "pure_python",
    }
    index_path = CORPUS_DIR / "tfidf_index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False)
    print(f"  [纯Python模式] 索引保存至: {index_path}")
    print(f"  [纯Python模式] 词汇量: {len(idf)}, 向量数: {len(tfidf_vectors)}, 耗时: {time.time() - t0:.1f}s")
    return index_data


# ============================================================
# sklearn TF-IDF（有外部依赖时使用）
# ============================================================

def build_sklearn_tfidf(all_chunks: list):
    """使用 sklearn 构建 TF-IDF 索引"""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from scipy.sparse import save_npz

    print("  [sklearn模式] 构建 TF-IDF 索引...")
    t0 = time.time()

    vectorizer = TfidfVectorizer(
        ngram_range=(1, 3),
        max_features=50000,
        sublinear_tf=True,
        analyzer="char_wb",
        strip_accents="unicode",
        max_df=0.85,
        min_df=2,
    )
    texts = [c["text"] for c in all_chunks]
    tfidf_matrix = vectorizer.fit_transform(texts)

    with open(VECTORIZER_PATH, "wb") as f:
        pickle.dump(vectorizer, f)
    save_npz(str(MATRIX_PATH), tfidf_matrix)

    print(f"  [sklearn模式] 词汇量: {len(vectorizer.vocabulary_)}, 矩阵: {tfidf_matrix.shape}, 耗时: {time.time() - t0:.1f}s")
    return {"mode": "sklearn"}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="构建南非人力行政策料 TF-IDF 索引")
    parser.add_argument("--force", action="store_true", help="强制重建")
    args = parser.parse_args()

    # 检查是否需要重建
    has_sklearn_index = VECTORIZER_PATH.exists() and MATRIX_PATH.exists() and META_PATH.exists()
    has_pure_index = (CORPUS_DIR / "tfidf_index.json").exists()
    if (has_sklearn_index or has_pure_index) and not args.force:
        print("[SKIP] 索引已存在，如需重建请加 --force")
        return

    print("=" * 60)
    print("  南非人力行政语料库 — TF-IDF 索引构建")
    print("=" * 60)
    print(f"  语料库目录: {CORPUS_DIR}")
    print()

    # ---- 第一步：递归扫描文件、分块 ----
    print("[1/3] 递归扫描语料文件并分块...")
    t0 = time.time()

    all_chunks = []
    file_count = 0

    for filepath in sorted(CORPUS_DIR.rglob("*")):
        if not filepath.is_file():
            continue
        if filepath.name in SKIP_NAMES:
            continue
        # 跳过整目录（如 primary-sources 核心法源）
        rel_parts = filepath.relative_to(CORPUS_DIR).parts
        if any(part in SKIP_DIRS for part in rel_parts):
            continue

        ext = filepath.suffix.lower()
        if ext == ".md":
            text = extract_text_from_md(filepath)
        elif ext == ".txt":
            text = extract_text_from_txt(filepath)
        elif ext == ".html":
            text = extract_text_from_html(filepath)
        else:
            continue

        if not text or len(text) < 50:
            continue

        file_count += 1
        category = get_category_from_path(filepath)
        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "id": f"{filepath.stem}_{i:04d}",
                "text": chunk,
                "source_file": filepath.name,
                "source_path": str(filepath.relative_to(CORPUS_DIR)),
                "source_label": get_file_label(filepath.name, category),
                "category": category,
                "chunk_index": i,
                "file_type": ext.lstrip("."),
                "char_count": len(chunk),
            })

    print(f"      处理 {file_count} 个文件，产生 {len(all_chunks)} 个文本块 ({time.time() - t0:.1f}s)")

    if not all_chunks:
        print("[ERROR] 没有有效文本，退出。")
        sys.exit(1)

    # ---- 第二步：训练 TF-IDF ----
    print("[2/3] 训练 TF-IDF 向量化器...")
    try:
        import sklearn
        has_sklearn = True
    except ImportError:
        has_sklearn = False

    if has_sklearn:
        try:
            result = build_sklearn_tfidf(all_chunks)
            mode = "sklearn"
            # 注意：本机装了 sklearn，因此只产出 pkl + npz，不落盘 tfidf_index.json。
            # 目标机若没装 sklearn，search_corpus.py 会从 chunks_metadata.json 的完整
            # 正文实时构建纯 Python 索引（约 130ms），故无需为可移植性额外落盘 ~7.9MB 索引。
            print("  [INFO] 未落盘 tfidf_index.json：目标机缺少 sklearn 时，"
                  "search_corpus.py 将按需实时构建纯 Python 索引。")
        except Exception as e:
            print(f"  [WARN] sklearn 构建失败: {e}，回退纯 Python 模式")
            result = build_pure_python_tfidf(all_chunks)
            mode = "pure_python"
    else:
        print("  [INFO] 未安装 sklearn，使用纯 Python TF-IDF")
        result = build_pure_python_tfidf(all_chunks)
        mode = "pure_python"

    # ---- 第三步：保存元数据 ----
    print("[3/3] 保存元数据...")
    t0 = time.time()

    meta_records = []
    for c in all_chunks:
        meta_records.append({
            "id": c["id"],
            # 完整块文本：供 search_corpus_semantic.py 做句向量 embedding 使用
            "text": c["text"],
            "preview": c["text"][:200],
            "source_file": c["source_file"],
            "source_path": c["source_path"],
            "source_label": c["source_label"],
            "category": c["category"],
            "chunk_index": c["chunk_index"],
            "file_type": c["file_type"],
            "char_count": c["char_count"],
        })
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(meta_records, f, ensure_ascii=False, indent=2)

    print(f"      metadata: {META_PATH} ({len(meta_records)} 条)")
    print()
    print("=" * 60)
    print(f"  TF-IDF 索引构建完成！")
    print(f"     文件数: {file_count}")
    print(f"     分块数: {len(all_chunks)}")
    print(f"     模式: {mode}")
    print(f"     耗时: {time.time() - t0:.1f}s")
    print("=" * 60)


if __name__ == "__main__":
    main()
