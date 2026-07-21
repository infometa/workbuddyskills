#!/usr/bin/env bash
# ============================================================
# TeachAny Map Resources Installer (v6)
# ============================================================
# 一键下载并安装历史/地理课件所需的全套地图资源：
#   1. Natural Earth 地形底图（hillshade, 9 张 JPG）
#   2. historical-basemaps 世界历代格局（21 个时间切片 GeoJSON）
#   3. CHGIS V6 中国历代疆域（17 个朝代，由 shapefile 切片生成）
#   4. Natural Earth 河流/湖泊/海岸线
#   5. 建立 data/geography 和 data/history 的 symlink（指向 _legacy/resources）
#
# 使用：
#   cd teachany-opensource
#   bash scripts/install_map_resources.sh
#
# 前置依赖：
#   - curl
#   - node + npx（用于 mapshaper）
#   - python3（仅执行切片脚本时需要）
# ============================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="$PROJECT_ROOT/data"
LEGACY_ROOT="$DATA_DIR/_legacy/resources"
GEO_DIR="$LEGACY_ROOT/geography"
HIST_DIR="$LEGACY_ROOT/history"

echo "================================================"
echo "TeachAny Map Resources Installer v6"
echo "================================================"
echo "项目根目录: $PROJECT_ROOT"
echo ""

# ─── 基础目录 ─────────────────────────────────
mkdir -p "$GEO_DIR/hillshade"
mkdir -p "$GEO_DIR/historical-china"
mkdir -p "$GEO_DIR/historical-world"
mkdir -p "$GEO_DIR/modern-china"
mkdir -p "$GEO_DIR/world"
mkdir -p "$GEO_DIR/rivers"
mkdir -p "$GEO_DIR/lakes"
mkdir -p "$GEO_DIR/coastline"
mkdir -p "$HIST_DIR/timelines"
mkdir -p "$HIST_DIR/figures"

# ─── 1. 建立符号链接 ──────────────────────────
echo "[1/5] 建立 symlink: data/geography → _legacy/resources/geography"
cd "$DATA_DIR"
[ -L geography ] && rm -f geography
[ -L history ]   && rm -f history
ln -sfn _legacy/resources/geography geography
ln -sfn _legacy/resources/history history
cd - > /dev/null
echo "  ✅ symlink 已建立"
echo ""

# ─── 2. Natural Earth hillshade ───────────────
echo "[2/5] 下载 Natural Earth 地形底图（JPG）"
HILLSHADE_BASE="https://raw.githubusercontent.com/weponusa/teachany-map-assets/main/hillshade"
for f in global-color-hillshade-4k.jpg global-color-hillshade-2k.jpg \
         global-hillshade-4k.jpg global-color-relief-4k.jpg; do
  out="$GEO_DIR/hillshade/$f"
  if [ -f "$out" ] && [ "$(wc -c < "$out" | tr -d ' ')" -gt 50000 ]; then
    echo "  ✔ 已存在: $f"
    continue
  fi
  echo "  ⬇ 下载 $f ..."
  curl -fsSL -o "$out" "$HILLSHADE_BASE/$f" 2>/dev/null || {
    echo "  ⚠️  从 teachany-map-assets 下载失败，改从 Natural Earth 源站"
    echo "     请手动下载："
    echo "     https://www.naturalearthdata.com/downloads/10m-raster-data/"
    echo "     推荐：Cross-blended Hypsometric Tints (HYP_HR) × Shaded Relief (SR_HR)"
    echo "     用 gdal 合成后降采样：gdal_translate -outsize 4096 2048 ..."
  }
done
echo ""

# ─── 3. historical-basemaps（世界） ────────────
echo "[3/5] 下载 historical-basemaps 世界历代数据（21 个切片）"
WORLD_BASE="https://raw.githubusercontent.com/aourednik/historical-basemaps/master/geojson"
WORLD_OUT="$GEO_DIR/historical-world"

# bce-xxxx 前缀 + 纯年份前缀两套
declare -a WORLD_FILES=(
  "bce-3000:world_bc3000"
  "bce-1500:world_bc1500"
  "bce-1000:world_bc1000"
  "bce-500:world_bc500"
  "bce-323-alexander:world_bc323"
  "bce-200:world_bc200"
  "bce-1:world_bc1"
  "ce-200:world_200"
  "ce-500:world_500"
  "ce-800-caliphate-carolingian:world_800"
  "ce-1000:world_1000"
  "ce-1200-mongol-rise:world_1200"
  "ce-1300-mongol-peak:world_1300"
  "ce-1492-age-of-discovery:world_1492"
  "ce-1600:world_1600"
  "ce-1700:world_1700"
  "ce-1815-vienna:world_1815"
  "ce-1880:world_1880"
  "ce-1914-wwi:world_1914"
  "ce-1945-wwii:world_1945"
  "ce-2000:world_2000"
)

for entry in "${WORLD_FILES[@]}"; do
  IFS=':' read -r outname srcname <<< "$entry"
  out="$WORLD_OUT/${outname}.geojson"
  if [ -f "$out" ] && [ "$(wc -c < "$out" | tr -d ' ')" -gt 100000 ]; then
    echo "  ✔ 已存在: ${outname}.geojson"
    continue
  fi
  echo "  ⬇ 下载 ${outname}.geojson ..."
  curl -fsSL -o "$out" "$WORLD_BASE/${srcname}.geojson" 2>/dev/null || echo "  ⚠️ 失败"
done

# 简化大文件
if command -v npx &> /dev/null; then
  echo "  ⚙️  用 mapshaper 简化 > 1.2 MB 的文件（保留 40% 顶点）..."
  for f in "$WORLD_OUT"/*.geojson; do
    size=$(wc -c < "$f" | tr -d ' ')
    if [ "$size" -gt 1200000 ]; then
      tmp="${f}.tmp"
      npx --yes mapshaper@0.6 "$f" -simplify 40% keep-shapes -o precision=0.001 "$tmp" 2>/dev/null > /dev/null && mv "$tmp" "$f"
    fi
  done
fi
echo ""

# ─── 4. CHGIS V6（中国） ───────────────────────
echo "[4/5] 下载 CHGIS V6 中国历代数据（prefecture polygon）"
CHGIS_ZIP="/tmp/chgis_v6.zip"
CHGIS_DIR="/tmp/chgis_v6"
CHGIS_URL="https://dataverse.harvard.edu/api/access/datafile/:persistentId/?persistentId=doi:10.7910/DVN/I0Q7SM/2VUO2N"

if [ ! -f "$CHGIS_DIR/v6_time_pref_pgn_utf_wgs84.shp" ]; then
  if [ ! -f "$CHGIS_ZIP" ] || [ "$(wc -c < "$CHGIS_ZIP" | tr -d ' ')" -lt 10000000 ]; then
    echo "  ⬇ 下载 CHGIS V6 zip (30MB)..."
    curl -fsSL --max-time 300 -o "$CHGIS_ZIP" "$CHGIS_URL" || {
      echo "  ⚠️  CHGIS 下载失败（Harvard Dataverse 偶尔需要重试）"
      echo "     手动下载: $CHGIS_URL"
      exit 1
    }
  fi
  mkdir -p "$CHGIS_DIR"
  cd "$CHGIS_DIR"
  unzip -oq "$CHGIS_ZIP"
  cd - > /dev/null
  echo "  ✅ 解压完成"
fi

# 执行切片脚本（若已存在则跳过）
CN_OUT="$GEO_DIR/historical-china"
if [ -f "$CN_OUT/tang-dynasty.geojson" ] && [ "$(wc -c < "$CN_OUT/tang-dynasty.geojson" | tr -d ' ')" -gt 500000 ]; then
  echo "  ✔ 朝代 GeoJSON 已存在，跳过切片"
else
  if [ -f "$PROJECT_ROOT/scripts/build_chgis_dynasty_maps_v2.sh" ]; then
    echo "  ⚙️  执行 CHGIS 朝代切片脚本..."
    bash "$PROJECT_ROOT/scripts/build_chgis_dynasty_maps_v2.sh"
    python3 "$PROJECT_ROOT/scripts/annotate_dynasty_powers.py" 2>/dev/null || true
    python3 "$PROJECT_ROOT/scripts/build_song_era_maps.py" 2>/dev/null || true
    python3 "$PROJECT_ROOT/scripts/rebuild_china_maps.py" 2>/dev/null || true
  else
    echo "  ⚠️  切片脚本不存在，跳过（请手动运行）"
  fi
fi
echo ""

# ─── 5. 现代中国行政 + 世界当代 ────────────────
echo "[5/5] 下载现代行政边界和物理地理（若缺失）"
MC_OUT="$GEO_DIR/modern-china"
[ ! -f "$MC_OUT/provinces.geojson" ] && {
  echo "  ⬇ 下载 provinces.geojson ..."
  curl -fsSL -o "$MC_OUT/provinces.geojson" \
    "https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json" || echo "  ⚠️ 失败"
}

[ ! -f "$GEO_DIR/world/countries.geojson" ] && {
  echo "  ⬇ 下载 world/countries.geojson ..."
  curl -fsSL -o "$GEO_DIR/world/countries.geojson" \
    "https://raw.githubusercontent.com/martynafford/natural-earth-geojson/master/10m/cultural/ne_10m_admin_0_countries.json" \
    || echo "  ⚠️ 失败"
}
echo ""

# ─── 验证 ─────────────────────────────────────
echo "================================================"
echo "验证安装结果"
echo "================================================"
cd "$GEO_DIR"
hs=$(ls hillshade/*.jpg 2>/dev/null | wc -l | tr -d ' ')
hc=$(ls historical-china/*.geojson 2>/dev/null | wc -l | tr -d ' ')
hw=$(ls historical-world/*.geojson 2>/dev/null | wc -l | tr -d ' ')
mc=$(ls modern-china/*.geojson 2>/dev/null | wc -l | tr -d ' ')

printf "  hillshade:         %d 个 JPG  (应: 3-9)\n" "$hs"
printf "  historical-china:  %d 个 GeoJSON  (应: 17)\n" "$hc"
printf "  historical-world:  %d 个 GeoJSON  (应: 21)\n" "$hw"
printf "  modern-china:      %d 个 GeoJSON  (应: ≥1)\n" "$mc"
echo ""

if [ "$hc" -ge 10 ] && [ "$hw" -ge 15 ] && [ "$hs" -ge 1 ]; then
  echo "✅ 安装完成！下一步："
  echo "   1. 启动本地服务器：python3 -m http.server 8080"
  echo "   2. 打开预览页：http://localhost:8080/data/map-inventory-preview.html"
  echo "   3. 参考技能文档：~/.codebuddy/skills/teachany/historical-maps.md"
else
  echo "⚠️  部分资源缺失，请检查网络后重试"
  echo "   或手动下载：见 ~/.codebuddy/skills/teachany/historical-maps.md §1"
  exit 1
fi
