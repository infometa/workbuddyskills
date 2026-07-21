#!/bin/bash
# bundle_map_assets.sh · v7.0 (CDN-first)
# 作用：把课件 index.html 里引用的地图 GeoJSON + hillshade 拷到 ./assets/maps/
#       让课件完全自包含，不依赖仓库 data/ 或线上 fallback URL。
# 原则：所有依赖要跟成果始终一起。
#
# 资源来源优先级（v5.37 重构）：
#   1. skill 本地缓存 / 仓库 data/_legacy/ ← 秒级 cp
#   2. jsDelivr CDN ← cdn.jsdelivr.net/gh/weponusa/teachany-images@main/
#   3. GitHub raw ← raw.githubusercontent.com fallback
#
# 用法：
#   bash bundle_map_assets.sh <课件目录>

set -e

COURSE_DIR="${1:-}"
if [ -z "$COURSE_DIR" ] || [ ! -d "$COURSE_DIR" ]; then
  echo "用法: $0 <课件目录>"
  echo "例: $0 community/history-ww2"
  exit 1
fi

HTML="$COURSE_DIR/index.html"
if [ ! -f "$HTML" ]; then
  echo "❌ 找不到 $HTML"
  exit 1
fi

echo "═════════════════════════════════════"
echo "  Bundle Map Assets · v7.0 (CDN-first)"
echo "═════════════════════════════════════"
echo "课件目录: $COURSE_DIR"
echo

# CDN 基础 URL（v5.37: 地图资源统一存储在 teachany-images 仓库）
CDN_BASE="https://cdn.jsdelivr.net/gh/weponusa/teachany-images@main"
CDN_FALLBACK="https://raw.githubusercontent.com/weponusa/teachany-images/main"

# 1. 资源源优先级（本地目录列表）
# v7.10: 新地图库路径 ~/.codebuddy/skills/teachany/assets/maps/{physical,chrono-cn,chrono-world,political}
SKILL_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SKILL_MAPS="$SKILL_ROOT/assets/maps"
SKILL_ASSETS="$(cd "$(dirname "$0")/.." && pwd)/assets"
# 定位 teachany-opensource 仓库（用于 _legacy 资源）
REPO=""
for c in "$HOME/CodeBuddy/一次函数/teachany-opensource" "$HOME/teachany-opensource" "$HOME/CodeBuddy/teachany-opensource"; do
  [ -d "$c/data/_legacy/resources/geography" ] && { REPO="$c"; break; }
done
if [ -z "$REPO" ] && [ -d "$COURSE_DIR/../.." ]; then
  candidate=$(cd "$COURSE_DIR/../.." && pwd)
  [ -d "$candidate/data/_legacy/resources/geography" ] && REPO="$candidate"
fi

# v7.10 新库路径（优先）+ 旧路径（兼容）
SOURCES=(
  # ★ 新地图库（v7.10+）
  "$SKILL_MAPS/chrono-cn"
  "$SKILL_MAPS/chrono-world"
  "$SKILL_MAPS/physical/hillshade"
  "$SKILL_MAPS/political/world"
  "$SKILL_MAPS/political/china-modern"
  "$SKILL_MAPS/political/admin-boundaries"
  # 旧路径（兼容，可能不存在）
  "$SKILL_ASSETS/historical-china"
  "$SKILL_ASSETS/historical-world"
  "$SKILL_ASSETS/hillshade"
)
if [ -n "$REPO" ]; then
  SOURCES+=(
    "$REPO/data/_legacy/resources/geography/historical-china"
    "$REPO/data/_legacy/resources/geography/historical-world"
    "$REPO/data/_legacy/resources/geography/hillshade"
  )
fi

# 工具函数：从 CDN 下载（带 fallback）
download_from_cdn() {
  local rel_path="$1"
  local dst="$2"
  # 尝试 jsDelivr CDN
  if curl -fsSL --max-time 30 -o "$dst" "$CDN_BASE/$rel_path" 2>/dev/null; then
    return 0
  fi
  # 尝试 GitHub raw fallback
  if curl -fsSL --max-time 30 -o "$dst" "$CDN_FALLBACK/$rel_path" 2>/dev/null; then
    return 0
  fi
  return 1
}

echo "[1/3] 资源源目录:"
for s in "${SOURCES[@]}"; do
  if [ -d "$s" ]; then
    count=$(find "$s" -maxdepth 1 -type f | wc -l | tr -d ' ')
    echo "  ✓ $s ($count 文件)"
  fi
done
echo "  ☁️  CDN: $CDN_BASE"
echo

# 2. 扫描 HTML 提取所有 .geojson 文件名（去掉路径）
echo "[2/3] 扫描 index.html 提取地图引用..."
# 策略 A：直接匹配 *.geojson 文件名
GEOJSONS_A=$(grep -oE "['\"\`][^'\"\`]*\.geojson" "$HTML" 2>/dev/null | \
  sed -E "s|.*/([^/'\"\`]+\.geojson)|\1|" | \
  grep -oE "[a-z0-9_-]+\.geojson" | sort -u)
# 策略 B：匹配 data-map="xxx" 属性（ww2 类课件用按钮切换）
GEOJSONS_B=$(grep -oE 'data-map="[a-z0-9_-]+"' "$HTML" 2>/dev/null | \
  sed -E 's|data-map="([^"]+)"|\1.geojson|' | sort -u)
# 策略 C：匹配 loadXxxMap(this, 'xxx', ...) 的第二个参数
GEOJSONS_C=$(grep -oE "load[A-Za-z]+Map\s*\(\s*this\s*,\s*['\"][a-z0-9_-]+['\"]" "$HTML" 2>/dev/null | \
  sed -E "s|.*,\s*['\"]([^'\"]+)['\"].*|\1.geojson|" | sort -u)

GEOJSONS=$(echo -e "$GEOJSONS_A\n$GEOJSONS_B\n$GEOJSONS_C" | grep -v "^$" | sort -u)

if [ -z "$GEOJSONS" ]; then
  echo "  ℹ️  课件没有 .geojson 引用，只检查 hillshade..."
fi

# 输出引用列表
count_refs=0
for f in $GEOJSONS; do
  count_refs=$((count_refs + 1))
  echo "  📍 $f"
done
[ "$count_refs" -gt 0 ] && echo "     （共 $count_refs 个 geojson 引用）"
echo

# 3. 拷贝
mkdir -p "$COURSE_DIR/assets/maps"
DST="$COURSE_DIR/assets/maps"

echo "[3/3] 拷贝资源到 $DST ..."
copied=0
missing=0
for f in $GEOJSONS; do
  if [ -f "$DST/$f" ]; then
    echo "  ⏭️  $f (已存在, skip)"
    continue
  fi
  found=""
  # 第一轮：精确匹配
  for src in "${SOURCES[@]}"; do
    if [ -f "$src/$f" ]; then
      cp "$src/$f" "$DST/$f"
      size=$(du -h "$DST/$f" | awk '{print $1}')
      echo "  ✅ $f ($size) ← $(basename "$src")"
      found=1
      copied=$((copied + 1))
      break
    fi
  done
  # 第二轮：模糊匹配（新库的 NNN-xxx.geojson ↔ 旧引用 xxx.geojson）
  if [ -z "$found" ]; then
    for src in "${SOURCES[@]}"; do
      [ -d "$src" ] || continue
      match=$(find "$src" -maxdepth 1 -type f -name "*$f" 2>/dev/null | head -1)
      if [ -n "$match" ] && [ -f "$match" ]; then
        cp "$match" "$DST/$f"
        size=$(du -h "$DST/$f" | awk '{print $1}')
        echo "  ✅ $f ($size) ← $(basename "$src")/$(basename "$match")"
        found=1
        copied=$((copied + 1))
        break
      fi
    done
  fi
  if [ -z "$found" ]; then
    echo "  ⚠️  $f 未找到"
    missing=$((missing + 1))
  fi
done

# hillshade
if grep -qE "hillshade|basemap" "$HTML"; then
  if [ ! -f "$DST/hillshade.jpg" ]; then
    hill_found=""
    for src in "${SOURCES[@]}"; do
      for name in "global-hillshade-4k.jpg" "global-color-hillshade-4k.jpg"; do
        if [ -f "$src/$name" ]; then
          cp "$src/$name" "$DST/hillshade.jpg"
          size=$(du -h "$DST/hillshade.jpg" | awk '{print $1}')
          echo "  ✅ hillshade.jpg ($size) ← $name"
          hill_found=1
          copied=$((copied + 1))
          break 2
        fi
      done
    done
    if [ -z "$hill_found" ]; then
      echo "  ℹ️  没找到 hillshade，课件若需要底图请手工加"
    fi
  else
    echo "  ⏭️  hillshade.jpg (已存在)"
  fi
fi

echo
echo "═════════════════════════════════════"
echo "  总结: 拷贝 $copied 个 · 缺失 $missing 个"
total_size=$(du -sh "$DST" 2>/dev/null | awk '{print $1}')
echo "  $DST 总大小: $total_size"
echo "═════════════════════════════════════"

if [ "$missing" -gt 0 ]; then
  echo
  echo "⚠️  有 $missing 个资源未找到，请检查 skill 或仓库的地图资源是否齐全"
  exit 1
fi

echo
echo "✅ 课件已完全自包含，所有依赖位于 ./assets/maps/"
echo "   可安全发布，无论仓库 data/ 是否部署都能工作"
