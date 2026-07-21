#!/usr/bin/env bash
#
# arxiv_fetch.sh — 下载 arXiv 论文 LaTeX 源码并定位 main.tex
#
# 用法:
#   bash arxiv_fetch.sh <arxiv_id> [output_dir]
#
# 例:
#   bash arxiv_fetch.sh 2206.04655
#   bash arxiv_fetch.sh 2206.04655 /tmp/arxiv-work

set -euo pipefail

ARXIV_ID="${1:?用法: bash arxiv_fetch.sh <arxiv_id> [output_dir]}"
OUTPUT_DIR="${2:-arxiv-${ARXIV_ID}}"

if ! [[ "${ARXIV_ID}" =~ ^[0-9]{4}\.[0-9]{4,5}(v[0-9]+)?$ ]] && \
   ! [[ "${ARXIV_ID}" =~ ^[a-z\-]+/[0-9]{7}(v[0-9]+)?$ ]]; then
  echo "❌ arxiv_id 格式不合法: ${ARXIV_ID}"
  echo "   合法格式: 2206.04655 / 2401.12345v2 / cs.LG/0001001"
  exit 1
fi

mkdir -p "${OUTPUT_DIR}"
cd "${OUTPUT_DIR}"

echo "==> 下载 arXiv 源码..."
SRC_URL="https://arxiv.org/e-print/${ARXIV_ID}"
if ! wget -q --tries=2 --timeout=30 "${SRC_URL}" -O "source.tar.gz"; then
  echo "❌ 下载失败: ${SRC_URL}"
  echo "   可能原因: 网络问题 / arxiv ID 不存在 / 该论文未提供源码"
  echo "   降级方案: 改用 PDF 路径："
  echo "     curl -O https://arxiv.org/pdf/${ARXIV_ID}.pdf"
  exit 2
fi

if [ ! -s "source.tar.gz" ]; then
  echo "❌ 下载的源码文件为空"
  exit 2
fi

echo "==> 解压..."
mkdir -p source
if ! tar -xzf source.tar.gz -C source 2>/dev/null; then
  if file source.tar.gz | grep -q "PDF"; then
    echo "ℹ️  arXiv 仅提供了 PDF 而非 LaTeX 源（部分论文如此）"
    mv source.tar.gz source.pdf
    rm -rf source
    echo "✅ 已保存 PDF 到: ${OUTPUT_DIR}/source.pdf"
    echo "   建议改用 scripts/extract_pdf.py 路径"
    exit 0
  else
    gunzip -c source.tar.gz > source/main_unknown.tex 2>/dev/null || true
    if [ -s source/main_unknown.tex ] && grep -q "\\\\documentclass" source/main_unknown.tex 2>/dev/null; then
      echo "ℹ️  源码是单 .tex 文件（非 tar.gz），已保存"
      MAIN_TEX="source/main_unknown.tex"
    else
      echo "❌ 解压失败，文件类型未识别"
      file source.tar.gz
      exit 2
    fi
  fi
fi

echo "==> 定位 main.tex..."
MAIN_TEX="${MAIN_TEX:-}"
if [ -z "${MAIN_TEX}" ]; then
  MAIN_TEX=$(grep -lE '\\documentclass' source/*.tex 2>/dev/null | head -1)
fi
if [ -z "${MAIN_TEX}" ]; then
  MAIN_TEX=$(find source -name "*.tex" -exec grep -lE '\\documentclass' {} \; 2>/dev/null | head -1)
fi

if [ -z "${MAIN_TEX}" ]; then
  echo "⚠️  未找到含 \\documentclass 的 tex 文件，列出所有 .tex："
  find source -name "*.tex" | head -10
  exit 3
fi

echo ""
echo "✅ arXiv 源码已就绪"
echo "   工作目录: ${OUTPUT_DIR}/"
echo "   main.tex: ${MAIN_TEX}"
echo "   首行内容:"
head -3 "${MAIN_TEX}" | sed 's/^/     /'

cat > arxiv-meta.json <<EOF
{
  "arxiv_id": "${ARXIV_ID}",
  "main_tex": "${MAIN_TEX}",
  "source_dir": "source",
  "fetched_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

echo ""
echo "📋 元数据已写入 ${OUTPUT_DIR}/arxiv-meta.json"
