#!/usr/bin/env bash
# ============================================================
# TeachAny Baseline Checker (v6)
# ============================================================
# 检查课件是否满足 7 条基础能力门槛（B-1 ~ B-7）。
# 用法：
#   bash check_baseline.sh <课件目录>
#   例如：bash check_baseline.sh examples/tang-dynasty/
#
# 退出码：
#   0 = 全部 PASS，可交付
#   1 = 有 FAIL，Completeness Gate 不通过
# ============================================================

set -e

COURSE_DIR="${1:-.}"
if [ ! -d "$COURSE_DIR" ]; then
  echo "❌ 课件目录不存在: $COURSE_DIR"
  exit 1
fi

COURSE_DIR="$(cd "$COURSE_DIR" && pwd)"
SKILL_SCRIPTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HTML="$COURSE_DIR/index.html"

if [ ! -f "$HTML" ]; then
  echo "❌ 未找到 $HTML"
  exit 1
fi

echo "================================================"
echo "TeachAny Baseline Checker v6"
echo "================================================"
echo "检查课件: $COURSE_DIR"
echo ""

FAILED=0
PASSED=0
WARNS=0

pass() { echo "  ✅ PASS  $1"; PASSED=$((PASSED+1)); }
fail() { echo "  ❌ FAIL  $1"; FAILED=$((FAILED+1)); }
warn() { echo "  ⚠️  WARN  $1"; WARNS=$((WARNS+1)); }

# ─── B-1 · 单页连续滚动 ────────────────────────
echo "[B-1] 单页连续滚动（No Pagination）"
html_count=$(find "$COURSE_DIR" -maxdepth 2 -name "*.html" | wc -l | tr -d ' ')
if [ "$html_count" -le 2 ]; then
  pass "只有 $html_count 个 HTML 文件（allowed ≤ 2，index + 可选 preview）"
else
  fail "课件目录有 $html_count 个 HTML，疑似多页翻页课件"
fi

# 检查 iframe 嵌套
if grep -q "<iframe" "$HTML"; then
  if grep -qE '<iframe[^>]*src="(video|audio|embed|preview)' "$HTML"; then
    pass "iframe 仅用于视频/音频/嵌入，非页面翻页"
  else
    warn "发现 iframe，请确认不是用来做翻页"
  fi
else
  pass "无 iframe 翻页"
fi

# 检查 "下一页" 按钮
if grep -qE 'class="[^"]*next-page|下一页|next-slide' "$HTML"; then
  fail "发现'下一页'按钮样式，课件应为单页滚动"
else
  pass "无翻页按钮"
fi
echo ""

# ─── B-2 · 自动触发语音 ────────────────────────
echo "[B-2] 自动触发语音讲解"
TTS_DIR="$COURSE_DIR/tts"
if [ -d "$TTS_DIR" ]; then
  mp3_count=$(find "$TTS_DIR" -name "*.mp3" | wc -l | tr -d ' ')
  if [ "$mp3_count" -ge 3 ]; then
    pass "发现 $mp3_count 个 TTS mp3 文件"
  else
    fail "tts/ 下只有 $mp3_count 个 mp3，至少需 3 个（引入/核心/总结）"
  fi
else
  fail "缺失 tts/ 目录（应通过 generate-tts.py 生成）"
fi

# 检查自动播放逻辑
if grep -qE "IntersectionObserver|auto.*play|autoplay" "$HTML"; then
  pass "发现自动播放逻辑（IntersectionObserver / autoplay）"
else
  fail "未发现自动触发语音的逻辑（IntersectionObserver）"
fi

# 严禁 Web Speech API
if grep -qE "speechSynthesis|SpeechSynthesisUtterance" "$HTML"; then
  fail "检测到 window.speechSynthesis（Web Speech API），B-2 严禁使用"
else
  pass "未使用 Web Speech API"
fi

# 全局播放控制
if grep -qE "全局.*(播放|暂停)|audio-global|tts-controller" "$HTML"; then
  pass "发现全局 TTS 控制器"
else
  warn "未见显式的全局 TTS 控制器（B-2 要求）"
fi
echo ""

# ─── B-3 · 多模态能力接入 ──────────────────────
echo "[B-3] 多模态能力（至少 3 种：图像≥3 + TTS + 地图/视频/动画）"
multi_count=0

# B-3a · 图像：至少 3 张，且在 HTML 里真实引用
img_files=$(find "$COURSE_DIR" -maxdepth 4 \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" -o -name "*.webp" \) 2>/dev/null | wc -l | tr -d ' ')
# 用 grep -oE 按匹配次数计数（允许同一行多个 <img>），wc -l 再数总行数
img_refs=$(grep -oE "<img[^>]+src=['\"][^'\"]+['\"]" "$HTML" 2>/dev/null | wc -l | tr -d ' ')
img_refs=${img_refs:-0}
# 确保是整数
[[ "$img_refs" =~ ^[0-9]+$ ]] || img_refs=0
if [ "$img_files" -ge 3 ] && [ "$img_refs" -ge 3 ]; then
  pass "✓ 图像：$img_files 张文件 + HTML 引用 $img_refs 次（≥3 合规）"
  multi_count=$((multi_count+1))
elif [ "$img_files" -ge 3 ]; then
  fail "✗ 图像：$img_files 张文件但 HTML 仅引用 $img_refs 次（需 ≥3）"
elif [ "$img_refs" -ge 3 ]; then
  fail "✗ 图像：HTML 引用 $img_refs 处但只找到 $img_files 个本地文件（需 ≥3 张真图）"
else
  fail "✗ AI 生成图片不足：本地 $img_files 张 / 引用 $img_refs 处（B-3a 要求 ≥3 张真实图片）"
fi

# 是否只有占位符
if [ "$img_files" -lt 3 ] && grep -qE "ai-media-zone|data-suggested-prompt" "$HTML" 2>/dev/null; then
  warn "  发现 AI 多模态互动区占位符，但占位符不算真实图片（B-3a FAIL）"
fi

# B-3a0 · Pillow 生图字体环境预检（v7.12.2）
# 根因修复：禁止 Pillow 静默 fallback 到默认位图字体导致中文/理科符号乱码。
FONT_RESOLVER="$SKILL_SCRIPTS/font_resolver.py"
if command -v python3 &>/dev/null && [ -f "$FONT_RESOLVER" ] && [ "$img_files" -ge 1 ]; then
  if python3 "$FONT_RESOLVER" --check >/tmp/teachany_font_check.log 2>&1; then
    pass "✓ Pillow 中文/理科字体环境可用（font_resolver.py）"
  else
    fail "✗ Pillow 中文/理科字体环境不可用：$(cat /tmp/teachany_font_check.log | head -1)"
  fi
fi

# B-3a+ · PNG 图片文字完整性抽检（检测 .notdef 方框，v6.1 新增）
# 当图片中大量像素集中在极少颜色时，可能是字体不支持导致方框渲染
if command -v python3 &>/dev/null && [ "$img_files" -ge 1 ]; then
  notdef_warn=$(python3 -c "
import sys, os
try:
    from PIL import Image
except ImportError:
    sys.exit(0)  # Pillow 未安装则跳过
course_dir = '$COURSE_DIR'
assets_dir = os.path.join(course_dir, 'assets')
if not os.path.isdir(assets_dir):
    sys.exit(0)
issues = []
for f in os.listdir(assets_dir):
    if not f.lower().endswith(('.png','.jpg','.jpeg','.webp')):
        continue
    fpath = os.path.join(assets_dir, f)
    try:
        img = Image.open(fpath).convert('RGBA')
        # 抽样检测：取中间 1/4 区域的像素
        w, h = img.size
        crop = img.crop((w//4, h//4, 3*w//4, 3*h//4))
        pixels = list(crop.getdata())
        total = len(pixels)
        if total == 0:
            continue
        # 检测是否有大量 .notdef 方框特征：
        # 方框通常是细线条+大面积背景，颜色种类极少（<20）
        unique_colors = len(set(pixels))
        # 检测文本区域是否有方框字符的特征模式
        # 方框在 Pillow 中通常渲染为矩形轮廓，检查是否有大量完全相同的非背景像素
        from collections import Counter
        color_counts = Counter(pixels)
        top2 = color_counts.most_common(2)
        if len(top2) >= 2:
            bg_ratio = top2[0][1] / total
            # 如果 95% 以上都是同一颜色，且文件名暗示应有文字内容
            # 这表明图片可能只有背景没有有效文字渲染
            text_hints = ['hero','reaction','equation','formula','concept','amphoteric','thermite']
            has_text_hint = any(h in f.lower() for h in text_hints)
            if bg_ratio > 0.98 and has_text_hint and unique_colors < 15:
                issues.append(f)
    except Exception:
        continue
if issues:
    print(','.join(issues))
" 2>/dev/null)
  if [ -n "$notdef_warn" ]; then
    warn "  B-3a+ 图片文字完整性疑似问题：$notdef_warn（可能使用了不支持 Unicode 上下标的字体，详见硬规则 #51）"
  fi
fi

# B-3 · TTS
tts_mp3_count=0
if [ -d "$TTS_DIR" ]; then
  tts_mp3_count=$(find "$TTS_DIR" -name "*.mp3" 2>/dev/null | wc -l | tr -d ' ')
fi
if [ "$tts_mp3_count" -ge 3 ]; then
  pass "✓ TTS 音频已生成（$tts_mp3_count 段，≥3）"
  multi_count=$((multi_count+1))
fi

# B-3 · 视频（v7.3：真实 mp4 + HTML 嵌入 + 音频流）
video_files=$(find "$COURSE_DIR" -maxdepth 4 \( -name "*.mp4" -o -name "*.webm" \) 2>/dev/null | wc -l | tr -d ' ')
video_refs=$(grep -oE "<(video|source)[^>]+src=['\"][^'\"]+\.(mp4|webm)['\"]" "$HTML" 2>/dev/null | wc -l | tr -d ' ')
if [ "$video_files" -ge 1 ] && [ "$video_refs" -ge 1 ]; then
  if command -v ffprobe >/dev/null 2>&1; then
    first_video=$(find "$COURSE_DIR" -maxdepth 4 \( -name "*.mp4" -o -name "*.webm" \) 2>/dev/null | head -1)
    if ffprobe -v error -show_entries stream=codec_type -of csv=p=0 "$first_video" 2>/dev/null | grep -qx "audio"; then
      pass "✓ 视频资源 $video_files 个，HTML 引用 $video_refs 处，且含 audio 流"
      multi_count=$((multi_count+1))
    else
      fail "✗ 视频资源存在但未检测到 audio 流（哑片 mp4 不合规）"
    fi
  else
    pass "✓ 视频资源 $video_files 个，HTML 引用 $video_refs 处（未安装 ffprobe，跳过音轨抽检）"
    multi_count=$((multi_count+1))
  fi
elif [ "$video_files" -ge 1 ]; then
  fail "✗ 有视频文件但 HTML 未用 <video>/<source> 嵌入"
elif [ "$video_refs" -ge 1 ]; then
  fail "✗ HTML 引用了视频但未找到本地 mp4/webm 文件"
fi

# B-3 · 地图
if grep -qE "L\.CRS\.EPSG4326|L\.map|leaflet|echarts.*registerMap" "$HTML" 2>/dev/null; then
  pass "✓ 包含地图渲染逻辑"
  multi_count=$((multi_count+1))
fi

# B-3 · 游戏化动画
if grep -qE "requestAnimationFrame|lottie|gsap|d3\.select|<canvas\b|sort-game|drag.*drop" "$HTML" 2>/dev/null; then
  pass "✓ 包含游戏化/动画逻辑"
  multi_count=$((multi_count+1))
fi

# 总量：至少 3 种（图像+TTS+另一项）
if [ "$multi_count" -ge 3 ]; then
  pass "多模态能力总数 $multi_count ≥ 3（合规）"
else
  fail "多模态能力总数 $multi_count（至少 3 种：图像≥3 + TTS + 地图/视频/动画任一）"
fi

# 检查是否误用外部 TTS/图像 API
if grep -qE "api\.openai\.com.*tts|azure.*speech|baidu.*tts|ali.*tts" "$HTML" 2>/dev/null; then
  fail "检测到外部 TTS API，违反 B-3"
fi
if grep -qE "dall-e|openai\.com/.*image|ideogram\.ai/api" "$HTML" 2>/dev/null; then
  fail "检测到外部图像 API，违反 B-3（应用 WorkBuddy image_gen）"
fi
echo ""

# ─── B-4 · 历史/地理课件用本地地图 ─────────────
echo "[B-4] 历史/地理课件强制使用本地地图资源"
# 通过文件名关键字判断是否历史/地理课件
is_geo_course=false
for kw in history geography 历史 地理 dynasty 朝代 map 地图 疆域 文明; do
  if [[ "$COURSE_DIR" == *"$kw"* ]] || grep -qE "$kw" "$HTML"; then
    is_geo_course=true; break
  fi
done

if [ "$is_geo_course" = true ]; then
  # v7.9.4+ 唯一标准路线：声明式 data-teachany-map + teachany-historical-map.js + 本地 assets/maps
  if grep -qE "data-teachany-map=|teachany-historical-map\.js" "$HTML"; then
    pass "历史/地理课件使用标准地图模块 data-teachany-map / teachany-historical-map.js"
  elif grep -qE "L\.map\s*\(" "$HTML"; then
    warn "发现手写 Leaflet 地图；新课件应迁移到标准 data-teachany-map 模块"
  else
    fail "历史/地理课件缺标准地图模块（应使用 data-teachany-map + teachany-historical-map.js）"
  fi

  map_geojson_count=0
  [ -d "$COURSE_DIR/assets/maps" ] && map_geojson_count=$(find "$COURSE_DIR/assets/maps" -name "*.geojson" 2>/dev/null | wc -l | tr -d ' ')
  if [ "$map_geojson_count" -ge 1 ] || grep -qE "assets/maps/[^\"']+\.geojson|\.geojson" "$HTML"; then
    pass "地图使用本地 GeoJSON 资源"
  else
    warn "未检测到本地 GeoJSON 资源；发布前需复制到 assets/maps/"
  fi

  if [ -f "$COURSE_DIR/assets/maps/hillshade.jpg" ] || grep -qE "hillshade\.jpg|hillshade" "$HTML"; then
    pass "地图配置包含本地 hillshade 地形底图"
  else
    warn "未检测到 hillshade.jpg；地理/历史地图建议使用本地地形底图"
  fi

  if grep -qE "L\.tileLayer\s*\(|DataV|datav|amap|map\.baidu|lbs\.qq\.com|tianditu|openstreetmap|cartodb|esri" "$HTML"; then
    fail "检测到在线瓦片或外部地图 API；B-4 要求本地资源和标准模块"
  fi
else
  pass "非历史/地理课件，跳过 B-4"
fi
echo ""

# ─── B-5 · 末尾知识图谱 ────────────────────────
echo "[B-5] 末尾知识图谱"
if grep -qE "id=\"knowledge-map\"|id=\"knowledge-graph\"|knowledge-map-section|知识图谱" "$HTML"; then
  pass "包含知识图谱章节"

  if grep -qE "前置|prerequisite" "$HTML" && grep -qE "后续|next-step" "$HTML"; then
    pass "包含前置节点 + 后续节点"
  else
    fail "知识图谱缺前置或后续节点（B-5 要求两者都有）"
  fi

  if grep -qE "weponusa\.github\.io/teachany/knowledge-graph\.html|knowledge-graph\.html\?node=" "$HTML"; then
    pass "节点可跳转到主站知识图谱"
  else
    warn "知识图谱节点未配置跳转 URL"
  fi
else
  fail "课件末尾缺知识图谱章节"
fi
echo ""

# ─── B-6 · 风格与结构标准 ──────────────────────
echo "[B-6] 风格与结构标准"
required_sections=("hero|开场|欢迎" "学习目标|learning.?objectives" "引入|introduction|intro" "核心概念|core.?concept" "例题|示范|演练" "互动|练习" "小测|测试|quiz" "总结|summary" "知识图谱|knowledge.?map")
sec_hit=0
sec_miss=()
for pat in "${required_sections[@]}"; do
  label="${pat%%|*}"
  if grep -qE "$pat" "$HTML"; then
    sec_hit=$((sec_hit+1))
  else
    sec_miss+=("$label")
  fi
done
if [ "$sec_hit" -ge 7 ]; then
  pass "标准结构 ${sec_hit}/9 段已覆盖"
else
  fail "标准结构仅覆盖 ${sec_hit}/9，缺失: ${sec_miss[*]}"
fi

# 字体
if grep -qE "PingFang|Source Han|system-ui|-apple-system" "$HTML"; then
  pass "包含推荐中文字体栈"
else
  warn "未检测到推荐中文字体栈"
fi

# 长度（html 文件字节数）
size=$(wc -c < "$HTML" | tr -d ' ')
if [ "$size" -gt 15000 ] && [ "$size" -lt 800000 ]; then
  pass "HTML 大小 $((size/1024)) KB 在合理范围（15KB~800KB）"
elif [ "$size" -le 15000 ]; then
  fail "HTML 仅 $((size/1024)) KB，内容过少（需含 9 段标准结构）"
else
  warn "HTML 达 $((size/1024)) KB，疑似过大（考虑拆分外部 js）"
fi
echo ""

# ─── B-7 · UI 布局避让 ────────────────────────
echo "[B-7] AI 学伴 与 音频按钮 不重叠"
has_assistant=false
has_audio_ctl=false

if grep -qE "ai-assistant|ai-companion|AI学伴|AI 学伴|chat-widget|bottom:\s*20px[^}]*right:\s*20px" "$HTML"; then
  has_assistant=true
fi

if grep -qE "tts-controller|audio-control|tts-button|音频.*(按钮|控制)|bottom:\s*90px" "$HTML"; then
  has_audio_ctl=true
fi

if $has_assistant && $has_audio_ctl; then
  has_lr_split=false
  has_vertical=false

  # 逐块 CSS 匹配：取 "#ai-assistant {" 到下一个 "}" 之间的行
  # python 更稳
  ai_has_left=$(python3 -c "
import re, sys
html = open('$HTML', encoding='utf-8').read()
m = re.search(r'#ai-assistant\b[^{]*\{([^}]*)\}', html, re.DOTALL)
if m and re.search(r'left:\s*\d+px', m.group(1)):
    print('yes')
" 2>/dev/null)

  tts_has_right=$(python3 -c "
import re, sys
html = open('$HTML', encoding='utf-8').read()
m = re.search(r'#tts-controller\b[^{]*\{([^}]*)\}', html, re.DOTALL)
if m and re.search(r'right:\s*\d+px', m.group(1)):
    print('yes')
" 2>/dev/null)

  if [ "$ai_has_left" = "yes" ] && [ "$tts_has_right" = "yes" ]; then
    has_lr_split=true
  fi

  if grep -qE "bottom:\s*(90|100|110|120|130)px" "$HTML"; then
    has_vertical=true
  fi

  if $has_lr_split; then
    pass "AI 学伴（左下）与 TTS 控制（右下）左右分离"
  elif $has_vertical; then
    pass "AI 学伴与 TTS 控制按钮纵向错位（bottom ≥ 90px）"
  else
    warn "未明确检测到按钮避让，请确认：AI 学伴（left:20px）+ TTS（right:20px）或 bottom 错位"
  fi
elif $has_assistant; then
  warn "只有 AI 学伴，无全局 TTS 控制（B-2 要求）"
elif $has_audio_ctl; then
  warn "只有 TTS 控制，无 AI 学伴"
else
  warn "未检测到 AI 学伴/TTS 控制按钮"
fi
echo ""

# ─── 汇总 ─────────────────────────────────────
echo "================================================"
echo "检查汇总"
echo "================================================"
printf "  ✅ PASS:  %d\n" "$PASSED"
printf "  ⚠️  WARN:  %d\n" "$WARNS"
printf "  ❌ FAIL:  %d\n" "$FAILED"
echo ""

if [ "$FAILED" -eq 0 ]; then
  echo "✅ 基线全部通过，Completeness Gate 可通过"
  exit 0
else
  echo "❌ 有 $FAILED 项 FAIL，Completeness Gate 不通过"
  echo "   请修复后重跑本脚本"
  exit 1
fi
