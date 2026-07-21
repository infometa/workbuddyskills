#!/usr/bin/env bash
# ============================================================
# TeachAny Course Publisher (v6.8 · 全自动端到端验证 + Pages 自救)
# ============================================================
# 按双仓库规范提交课件到 teachany-courseware，并自动验证上线。
#
# 流程（全自动，失败直接退非零码）：
#   [1/5]   基线检查（check_baseline.sh，22 PASS 要求）
#   [1.2/5] node_id 预校验（check_node_id.py，防挂空）
#   [1.5/5] 内联地图资源（bundle_map_assets.sh，自包含）
#   [2/5]   定位 / 自动 clone teachany-opensource 仓库
#   [3/5]   从 HTML teachany-* meta 生成 manifest.json
#           + 校正 title → 《X》 · 学科 Gx · TeachAny v6
#           + 补齐 8 条 teachany-* meta
#   [4/5]   拷贝到 community/drafts/<id>/
#   [5/5]   submit-to-community.py 打包 + POST Pages Functions → 建 PR
#   [6/6]   自动 poll 课件 URL 直到 HTTP 200（最多 10 分钟）
#
# 成功条件：最终 curl 到 200 才算成功，否则退出 11。
#
# v6.6 修复：
# - 修 manifest 抓错 meta 的 bug（meta 命名 teachany-xxx 连字符被错匹配）
# - 顺序：先读 HTML meta → 生成 manifest → 覆盖 HTML meta（可重入幂等）
# - 新增 [6/6] 自动验证，防止"声称成功但线上 404"
# - Gallery URL 修为 index.html（而不是 gallery.html）
#
# 用法：
#   bash publish_course.sh <源课件目录> [course-id] [--author 姓名]
#
# 环境变量：
#   TEACHANY_REPO           指定仓库路径
#   TEACHANY_WORKER_URL     自建 Worker URL
#   TEACHANY_DIRECT_TOKEN   直连 GitHub token
# ============================================================

set -e

SRC_DIR="${1:-}"
COURSE_ID="${2:-}"
AUTHOR=""

# 解析 --author
shift 2>/dev/null || true
shift 2>/dev/null || true
while [ $# -gt 0 ]; do
  case "$1" in
    --author) AUTHOR="$2"; shift 2 ;;
    *) shift ;;
  esac
done

if [ -z "$SRC_DIR" ] || [ ! -d "$SRC_DIR" ]; then
  echo "❌ 用法: bash publish_course.sh <源课件目录> [course-id] [--author 姓名]"
  exit 1
fi

SRC_DIR="$(cd "$SRC_DIR" && pwd)"
[ -z "$COURSE_ID" ] && COURSE_ID="$(basename "$SRC_DIR")"

echo "================================================"
echo "TeachAny Course Publisher v6.8 · 全自动端到端 + Pages 自救"
echo "================================================"
echo "源课件: $SRC_DIR"
echo "Course ID: $COURSE_ID"
echo ""

SKILL_SCRIPTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ─── 1. 基线检查 ──────────────────────────────
if [ -f "$SKILL_SCRIPTS/check_baseline.sh" ]; then
  echo "[1/5] 基线检查"
  if ! bash "$SKILL_SCRIPTS/check_baseline.sh" "$SRC_DIR" > /tmp/baseline.log 2>&1; then
    echo "  ❌ 基线检查 FAIL，不能发布"
    tail -25 /tmp/baseline.log
    exit 1
  fi
  pass_count=$(grep -c "✅ PASS" /tmp/baseline.log 2>/dev/null | head -1 || echo 0)
  echo "  ✅ 基线通过（$pass_count PASS）"
fi

# ─── 1.1. v7.3 反空壳教学质量闸门 ─────────────────
QUALITY_GATE="$SKILL_SCRIPTS/../../scripts/validate-teaching-quality.py"
if [ -f "$QUALITY_GATE" ]; then
  echo ""
  echo "[1.1/5] v7.3 教学质量闸门"
  if ! python3 "$QUALITY_GATE" "$SRC_DIR" > /tmp/teaching_quality.log 2>&1; then
    echo "  ❌ 教学质量闸门 FAIL，不能发布"
    tail -30 /tmp/teaching_quality.log
    exit 1
  fi
  echo "  ✅ 教学质量闸门通过"
fi

# ─── 1.2. node_id 预校验（v6.5 新增 / v6.6 支持 free_mode）─────
# 确保 node_id 在知识树里存在，否则前端无法显示
# free_mode：课件写 <meta name="teachany-free-mode" content="true"> 跳过校验
if [ -f "$SKILL_SCRIPTS/check_node_id.py" ] && [ -f "$SRC_DIR/index.html" ]; then
  echo ""
  echo "[1.2/5] 校验 node_id 存在于知识树"
  # 检查 free_mode
  if grep -qE 'name="teachany-free-mode"[^>]*content="true"' "$SRC_DIR/index.html" 2>/dev/null; then
    echo "  🎯 检测到 teachany-free-mode=true → 跳过 node_id 校验（自由知识点模式）"
    echo "     课件将出现在 Gallery 学科分类，但不挂任何知识图谱节点"
  elif ! python3 "$SKILL_SCRIPTS/check_node_id.py" "$SRC_DIR" > /tmp/node_check.log 2>&1; then
    echo "  ❌ node_id 不在知识树里（课件即使上传也无法在 Gallery/知识图谱显示）"
    cat /tmp/node_check.log | head -20
    echo ""
    echo "  💡 三种处理方式："
    echo "     A) 修正 node_id 为已有节点（推荐）："
    echo "        python3 ~/.codebuddy/skills/teachany/scripts/find_nodes.py \\"
    echo "          --stage <小学|初中|高中> --subject <学科> --keyword <关键词>"
    echo ""
    echo "     B) 注册新节点到知识树（管理员场景）："
    echo "        python3 ~/.codebuddy/skills/teachany/scripts/register_node.py ..."
    echo ""
    echo "     C) 自由模式（课件不挂树，只进 Gallery）："
    echo "        在 HTML <head> 加：<meta name=\"teachany-free-mode\" content=\"true\">"
    exit 1
  else
    grep -E "✅|节点名" /tmp/node_check.log | head -3
  fi
fi

# ─── 1.5. 地图资源自包含（v6.4 新增）──────────
# 原则：所有依赖要跟成果始终一起
if [ -f "$SKILL_SCRIPTS/bundle_map_assets.sh" ]; then
  # 只在 HTML 含地图引用时才跑
  if grep -qE "\.geojson|data-map=|hillshade|TEACHANY_MAP_BASE" "$SRC_DIR/index.html" 2>/dev/null; then
    echo ""
    echo "[1.5/5] 内联地图资源（让课件自包含）"
    bash "$SKILL_SCRIPTS/bundle_map_assets.sh" "$SRC_DIR" > /tmp/bundle_maps.log 2>&1 || true
    copied=$(grep -c "✅" /tmp/bundle_maps.log 2>/dev/null | head -1 || echo 0)
    skipped=$(grep -c "⏭️" /tmp/bundle_maps.log 2>/dev/null | head -1 || echo 0)
    missing=$(grep -c "⚠️.*未找到" /tmp/bundle_maps.log 2>/dev/null | head -1 || echo 0)
    echo "  ✅ 地图资源：新拷贝 $copied 个 · 已存在 $skipped 个 · 缺失 $missing 个"
    if [ "$missing" -gt 0 ]; then
      echo "  ⚠️  有资源缺失，课件可能依赖 fallback URL 加载"
      grep "⚠️" /tmp/bundle_maps.log | head -5
    fi
  fi
fi

# ─── 2. 定位仓库 ──────────────────────────────
echo ""
echo "[2/5] 定位 teachany-opensource"

locate_repo() {
  [ -n "$TEACHANY_REPO" ] && [ -f "$TEACHANY_REPO/scripts/submit-to-community.py" ] && { echo "$TEACHANY_REPO"; return; }
  local candidates=(
    "$HOME/CodeBuddy/一次函数/teachany-opensource"
    "$HOME/CodeBuddy/teachany-opensource"
    "$HOME/teachany-opensource"
    "$HOME/WorkBuddy/teachany-opensource"
  )
  for c in "${candidates[@]}"; do
    [ -f "$c/scripts/submit-to-community.py" ] && { echo "$c"; return; }
  done
  # ⭐ find 可能因参数不存在返回非零，暂关 set -e
  set +e
  local search_roots=()
  [ -d "$HOME/CodeBuddy" ] && search_roots+=("$HOME/CodeBuddy")
  [ -d "$HOME/WorkBuddy" ] && search_roots+=("$HOME/WorkBuddy")
  search_roots+=("$HOME")
  local found=""
  if [ "${#search_roots[@]}" -gt 0 ]; then
    found=$(find "${search_roots[@]}" -maxdepth 5 -name "submit-to-community.py" 2>/dev/null | head -1)
  fi
  set -e
  [ -n "$found" ] && echo "$(dirname "$(dirname "$found")")"
}

REPO="$(locate_repo)"
if [ -z "$REPO" ]; then
  # ⭐ v7.9.9: 使用 sparse checkout 只拉取发布所需目录，排除既有课件 (~600MB)
  DEFAULT_CLONE="$HOME/teachany-opensource"
  echo "  ℹ️  未找到 teachany-opensource 仓库"
  echo "  🔄 自动克隆到: $DEFAULT_CLONE（sparse 模式，排除既有课件）"
  echo ""
  if git clone --depth 1 --filter=blob:none --sparse https://github.com/weponusa/teachany.git "$DEFAULT_CLONE" 2>&1 | tail -5; then
    cd "$DEFAULT_CLONE"
    git sparse-checkout init --cone
    # 发布流程只需要 scripts + data + skill + community/drafts(投稿目录)
    git sparse-checkout set scripts/ data/ skill/ community/drafts/ .sparse-checkout-presets/
    cd - >/dev/null
    REPO="$DEFAULT_CLONE"
    echo "  ✅ 仓库已克隆（sparse，约 40MB）: $REPO"
  else
    echo ""
    echo "  ❌ 自动克隆失败。请手动执行："
    echo "     git clone --filter=blob:none --sparse https://github.com/weponusa/teachany.git $HOME/teachany-opensource"
    echo "     cd $HOME/teachany-opensource && git sparse-checkout set scripts/ data/ skill/"
    echo "  或设置环境变量：export TEACHANY_REPO=/path/to/teachany-opensource"
    exit 1
  fi
fi
echo "  ✅ 仓库: $REPO"

# ─── 3. 生成/补全 manifest.json + 校正 HTML title/meta ─────────
# v6.6 修复：用 Python 一站式处理（兼容多种 meta 命名 / 顺序正确）
echo ""
echo "[3/5] 生成 manifest.json + 校正 HTML"

MANIFEST="$SRC_DIR/manifest.json"
AUTHOR_FINAL="${AUTHOR:-TeachAny 用户}"

python3 - "$SRC_DIR/index.html" "$MANIFEST" "$COURSE_ID" "$AUTHOR_FINAL" <<'PYEOF'
import json, re, sys
from pathlib import Path

html_path = Path(sys.argv[1])
manifest_path = Path(sys.argv[2])
course_id = sys.argv[3]
author = sys.argv[4]

html = html_path.read_text(encoding="utf-8")

# ⭐ 兼容三种 meta 命名：teachany-xxx (官方 v6) / teachany:xxx / course-xxx
def get_meta(html, *keys):
    """从 HTML 抓 meta，按 keys 顺序找到第一个非空值"""
    for key in keys:
        m = re.search(
            rf'<meta\s+[^>]*name=["\']({re.escape(key)})["\'][^>]*content=["\']([^"\']+)["\']',
            html, re.IGNORECASE
        )
        if m and m.group(2).strip():
            return m.group(2).strip()
        # 顺序反过来再试
        m = re.search(
            rf'<meta\s+[^>]*content=["\']([^"\']+)["\'][^>]*name=["\']({re.escape(key)})["\']',
            html, re.IGNORECASE
        )
        if m and m.group(1).strip():
            return m.group(1).strip()
    return ""

# 抓 title（去掉 · 后的部分）
title_m = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
title_raw = title_m.group(1).strip() if title_m else course_id
title = re.sub(r"\s*[·\|・].*$", "", title_raw).strip()
# 去掉《》括号
title = re.sub(r"^[《<]|[》>]$", "", title).strip()
if not title:
    title = course_id

# 关键 meta
node_id = get_meta(html, "teachany-node", "teachany:node_id", "course-node")
subject = get_meta(html, "teachany-subject", "teachany:subject", "course-subject")
grade_str = get_meta(html, "teachany-grade", "teachany:grade", "course-grade")
stage = get_meta(html, "teachany-stage", "teachany:stage", "course-stage")
free_mode_str = get_meta(html, "teachany-free-mode")
free_mode = free_mode_str.lower() in ("true", "1", "yes")
description = get_meta(html, "description") or f"TeachAny v6 合规课件：{title}"

# 从 grade 数字推 stage
try:
    grade = int(grade_str) if grade_str else 0
except:
    grade = 0

if not grade and stage:
    grade = {"elementary": 4, "primary": 4, "middle": 8, "junior": 8, "lsec": 8,
             "high": 11, "senior": 11}.get(stage.lower(), 9)

# free_mode：强制清空 node_id（自由模式不挂任何节点）
if free_mode:
    if node_id:
        print(f"  🎯 free_mode=true，丢弃 HTML 残留的 node_id='{node_id}'")
    node_id = ""

# 兜底
if not free_mode and not node_id:
    print(f"  ⚠️  HTML 缺 teachany-node meta 且非 free_mode，用 course_id 兜底", file=sys.stderr)
    node_id = course_id
if not subject:
    print(f"  ⚠️  HTML 缺 teachany-subject meta，用 'general' 兜底", file=sys.stderr)
    subject = "general"
if not grade:
    grade = 9

print(f"  📖 从 HTML 解析:")
print(f"     title={title}")
print(f"     node_id={node_id}")
print(f"     subject={subject}")
print(f"     grade={grade}")

# 1. 写/覆盖 manifest.json（不再 fallback 用旧错的）
manifest = {
    "id": course_id,
    "name": title,
    "node_id": node_id,
    "subject": subject,
    "grade": grade,
    "author": author,
    "description": description,
    "version": "1.0.0",
    "teachany_version": "v7.9",
    "curriculum": "cn-national",
    "free_mode": free_mode,  # v6.6: 自由知识点模式（不挂树）
}
# 如果旧 manifest 存在且完整就保留它（避免覆盖管理员手填的字段）
if manifest_path.exists():
    try:
        old = json.load(open(manifest_path, encoding="utf-8"))
        # 仅当旧的有 node_id 且与 HTML meta 一致时才保留
        if old.get("node_id") == node_id and old.get("subject") == subject:
            manifest.update({k: v for k, v in old.items() if k not in manifest or not manifest[k]})
            print(f"  ✅ 复用已有 manifest.json（一致）")
        else:
            print(f"  🔄 重写 manifest.json（旧值与 HTML meta 不一致）")
    except: pass

manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"  ✅ manifest.json: id={course_id} node_id={node_id} subject={subject}")

# 2. 校正 HTML title + 8 条 teachany-* meta
subject_map = {
    "math":"数学","chinese":"语文","english":"英语","physics":"物理",
    "chemistry":"化学","biology":"生物","history":"历史","geography":"地理",
    "politics":"政治","science":"科学","tech":"信息技术","it":"信息技术",
    "info-tech":"信息技术","information-technology":"信息技术","general":"通识",
}
subject_cn = subject_map.get(subject, subject)
if grade <= 6:    stage_cn = f"小学 G{grade}"
elif grade <= 9:  stage_cn = f"初中 G{grade}"
elif grade <= 12: stage_cn = f"高中 G{grade}"
else:             stage_cn = f"G{grade}"

new_title = f"《{title}》 · {subject_cn} {stage_cn} · TeachAny v7.9"
title_re = re.compile(r"<title[^>]*>[^<]*</title>", re.IGNORECASE)
if title_re.search(html):
    html = title_re.sub(f"<title>{new_title}</title>", html, count=1)
else:
    html = re.sub(r"(<head[^>]*>)", r"\1\n  <title>" + new_title + "</title>", html, count=1, flags=re.IGNORECASE)
print(f"  ✅ <title> → {new_title}")

# 3. 删旧 teachany-* meta + 重新插入完整 8 条
required = {
    "teachany-id": course_id,
    "teachany-name": title,
    "teachany-node": node_id,
    "teachany-subject": subject,
    "teachany-grade": str(grade),
    "teachany-version": "v6",
    "teachany-author": author,
    "teachany-curriculum": "cn-national",
}
html = re.sub(r'\s*<meta\s+[^>]*name=["\']teachany-[^"\']+["\'][^>]*>\s*', "\n  ", html, flags=re.IGNORECASE)
new_metas = "\n  " + "\n  ".join(f'<meta name="{k}" content="{v}">' for k, v in required.items())
if "</head>" in html:
    html = html.replace("</head>", new_metas + "\n</head>", 1)
elif re.search(r"<head[^>]*>", html, re.IGNORECASE):
    html = re.sub(r"(<head[^>]*>)", r"\1" + new_metas, html, count=1, flags=re.IGNORECASE)
print(f"  ✅ teachany-* meta: 8 条已就位")

# 4. 统一当前双仓架构路径：logo 用 courseware 最新资源；标准运行时用 courseware 根级 assets/scripts。
#    这样即便课件来自旧模板，也不会继续引用已失效的 /teachany/assets 或顶层 /scripts。
path_rewrites = {
    "https://weponusa.github.io/teachany/assets/teachany-logo.png": "https://weponusa.github.io/teachany-courseware/assets/teachany-logo.png",
    "https://weponusa.github.io/teachany-courseware/scripts/": "../../assets/scripts/",
    "https://weponusa.github.io/teachany/scripts/": "../../assets/scripts/",
    "../../scripts/": "../../assets/scripts/",
}
for old, new in path_rewrites.items():
    html = html.replace(old, new)
print("  ✅ 双仓路径修正：logo + 标准运行时路径已统一")

html_path.write_text(html, encoding="utf-8")
PYEOF

if [ ! -f "$MANIFEST" ]; then
  echo "  ❌ manifest.json 生成失败"
  exit 1
fi

# ─── 4. 拷贝到 community/drafts/ ───────────────

# ─── 4. 拷贝到 community/drafts/ ───────────────
echo ""
echo "[4/5] 拷贝到 community/drafts/$COURSE_ID"
DRAFT_DIR="$REPO/community/drafts/$COURSE_ID"
mkdir -p "$REPO/community/drafts"
if [ -d "$DRAFT_DIR" ]; then
  echo "  ⚠️  已存在，覆盖"
  rm -rf "$DRAFT_DIR"
fi
cp -R "$SRC_DIR" "$DRAFT_DIR"
SIZE=$(du -sh "$DRAFT_DIR" | awk '{print $1}')
echo "  ✅ 已拷入 community/drafts/$COURSE_ID ($SIZE)"

# ─── 5. 调用官方 submit 脚本 ─────────────────
echo ""
echo "[5/5] 提交到 TeachAny Community"
cd "$REPO"

# 5.0 预检：Worker 是否可达（curl 可能返回非零，禁 set -e）
WORKER_URL="${TEACHANY_WORKER_URL:-https://teachany-community.pages.dev/api/submit}"
echo "  🔍 预检 Worker 可达性: $WORKER_URL"
set +e
WORKER_STATUS=$(curl -sI --max-time 6 -o /dev/null -w "%{http_code}" "$WORKER_URL" 2>/dev/null)
curl_exit=$?
set -e
echo "     HTTP $WORKER_STATUS (curl exit: $curl_exit)"

USE_MODE="worker"
if [ "$WORKER_STATUS" = "000" ] || [ -z "$WORKER_STATUS" ]; then
  echo "  ⚠️  Worker 不可达"
  if [ -n "$TEACHANY_DIRECT_TOKEN" ]; then
    echo "  🔑 使用 TEACHANY_DIRECT_TOKEN 直连 GitHub"
    USE_MODE="direct"
  else
    # v6.7: 移除 manual 管理员直推模式（绕过质检，违反硬规则 #18.4）
    # 只保留 drafts-only，用户等 Worker 恢复再重跑
    echo "  💤 Worker 不可达且无 TEACHANY_DIRECT_TOKEN → 仅保留到 drafts/"
    echo "     等 Worker 恢复后重跑：$0 $SRC_DIR $COURSE_ID"
    USE_MODE="drafts-only"
  fi
fi

SUBMIT_ARGS=("$COURSE_ID" "--from" "drafts")
[ -n "$AUTHOR" ] && SUBMIT_ARGS+=("--author" "$AUTHOR")

STATUS=0

case "$USE_MODE" in
  worker|direct)
    if python3 scripts/submit-to-community.py "${SUBMIT_ARGS[@]}" 2>&1 | tee /tmp/submit.log; then
      if grep -q "⛔\|❌" /tmp/submit.log; then
        STATUS=1
      fi
    else
      STATUS=$?
    fi
    ;;
  drafts-only)
    echo "  ℹ️  课件已暂存到 drafts/，可稍后重试"
    STATUS=10
    ;;
esac

# Worker SSL 失败的特征检测
if [ $STATUS -ne 0 ] && [ -f /tmp/submit.log ] && grep -qE "SSL|unexpected eof|无法连接|urlopen|timed out" /tmp/submit.log 2>/dev/null; then
  STATUS=10  # 标记为"已暂存但 Worker 不通"
fi

echo ""
echo "================================================"
if [ $STATUS -eq 0 ]; then
  echo "✅ 提交成功！"
  PR_URL=$(grep -oE 'https://github.com/[^ ]+/pull/[0-9]+' /tmp/submit.log 2>/dev/null | head -1)
  [ -n "$PR_URL" ] && echo "" && echo "PR 地址: $PR_URL"

  COURSE_URL="https://weponusa.github.io/teachany-courseware/community/$COURSE_ID/"

  # ─── 6/6 自动验证（v6.8：修复 Pages 部署不触发问题）─────
  echo ""
  echo "[6/6] 自动验证课件 URL 可访问"
  # v7.14：真实课件统一发布到 teachany-courseware。
  # courseware 的 community-publish.yml 会解包、rebuild-index 并部署 gh-pages。
  echo "  ⏳ 等 PR 合并 + 解包 + Pages 部署（最多 10 分钟，每 30s 检查一次）..."
  PAGES_KICKED=0  # 是否已主动触发过 Pages
  for attempt in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
    sleep 30
    code=$(curl -sI --max-time 10 "${COURSE_URL}?_=$(date +%s)" 2>/dev/null | head -1 | grep -oE "[0-9]{3}")
    if [ "$code" = "200" ]; then
      echo "  ✅ 第 ${attempt} 次检查 (${attempt}*30s)：HTTP 200，课件已上线"
      break
    fi
    echo "  ⏳ 第 ${attempt} 次检查 (${attempt}*30s)：HTTP $code，继续等..."

    # v6.8: 第 6 次（3 分钟）还 404 且 main 里已有课件目录 → 主动触发 Pages
    if [ "$attempt" = "6" ] && [ "$PAGES_KICKED" = "0" ] && [ "$code" != "200" ]; then
      echo ""
      echo "  🔧 已等 3 分钟 URL 仍 404，检查是否为 Pages 未触发问题..."
      REPO_DIR="${TEACHANY_COURSEWARE_REPO:-$HOME/CodeBuddy/一次函数/teachany-courseware}"
      if [ -d "$REPO_DIR/.git" ]; then
        pushd "$REPO_DIR" > /dev/null
        git fetch origin main --quiet 2>&1
        # 检查 courseware main 里有没有这个课件目录
        if git ls-tree -r origin/main --name-only 2>/dev/null | grep -q "community/$COURSE_ID/index.html"; then
          echo "  ✅ courseware/main 里已有 community/$COURSE_ID/index.html"
          echo "  ⚠️  但 Pages 404 → 确认是 GITHUB_TOKEN commit 不触发 Deploy workflow 的已知问题"
          echo "  🚀 push 一个 empty commit 触发 Deploy to GitHub Pages..."
          git checkout main --quiet 2>&1
          git pull origin main --quiet 2>&1
          git commit --allow-empty -m "chore: trigger pages redeploy for $COURSE_ID" 2>&1 | tail -3
          if git push origin main 2>&1 | tail -3; then
            PAGES_KICKED=1
            echo "  ✅ 已 push empty commit，Deploy workflow 应该已启动（~1 分钟跑完）"
          else
            echo "  ❌ push 失败，可能需要手动处理"
          fi
        else
          echo "  ⚠️  courseware/main 里还没有 community/$COURSE_ID/ 目录，PR 可能还在合并/解包中，继续等..."
        fi
        popd > /dev/null
      else
        echo "  ⚠️  未找到本地 teachany-courseware 仓库，无法主动触发 Pages；继续等..."
      fi
    fi
  done

  # 最终一锤验证
  FINAL_CODE=$(curl -sI --max-time 10 "${COURSE_URL}?_=$(date +%s)" 2>/dev/null | head -1 | grep -oE "[0-9]{3}")
  echo ""
  echo "================================================"
  if [ "$FINAL_CODE" = "200" ]; then
    echo "🎉 课件已真上线（HTTP 200）"
    echo ""
    echo "  📚 课件地址: $COURSE_URL"
    NODE_ID_FINAL=$(python3 -c "import json; print(json.load(open('$MANIFEST')).get('node_id',''))" 2>/dev/null || true)
    echo "  🗺️  知识图谱: https://weponusa.github.io/teachany/path.html?node=$NODE_ID_FINAL"
    echo "  📋 Gallery:  https://weponusa.github.io/teachany/index.html"
    [ -n "$PR_URL" ] && echo "  🔀 PR:       $PR_URL"
    exit 0
  else
    echo "⚠️  PR 已成功提交，但 10 分钟内课件 URL 仍未 200（HTTP $FINAL_CODE）"
    echo ""
    echo "  📚 期望 URL: $COURSE_URL"
    [ -n "$PR_URL" ] && echo "  🔀 PR:       $PR_URL（去这里看是否合并 + workflow 状态）"
    echo ""
    echo "  可能原因："
    echo "    - PR 还在等审核 / 自动合并 workflow 未完成"
    echo "    - GitHub Pages 部署慢（偶尔 15+ 分钟）"
    echo "    - validate.yml 检测到课件不合规拒绝合并"
    echo ""
    echo "  自检命令："
    echo "    curl -I '$COURSE_URL'    # 等几分钟再试"
    echo "    gh pr view <PR号> --repo weponusa/teachany-courseware"
    exit 11
  fi
elif [ $STATUS -eq 10 ]; then
  echo "🟡 已就绪但未联网提交"
  echo ""
  echo "课件完全合规（基线 PASS + manifest 生成 + 已暂存 drafts），"
  echo "只因 Worker 当前不可达未完成最后一步网络提交。"
  echo ""
  echo "三种恢复方式（按难度从低到高）："
  echo ""
  echo "  🅰️  等 Worker 恢复后重跑："
  echo "      $0 $SRC_DIR $COURSE_ID"
  echo ""
  echo "  🅱️  用 GitHub Fine-grained token 直连（绕过 Worker，仍走 PR 质检）："
  echo "      TEACHANY_DIRECT_TOKEN=ghp_xxx $0 $SRC_DIR $COURSE_ID"
  echo ""
  echo "  ⛔ 管理员直推模式已废弃（v6.7 起移除）：任何发布都必须走 PR + 质检"
  echo ""
  echo "  📁 课件当前位置: $REPO/community/drafts/$COURSE_ID"
  exit 10
else
  echo "❌ 提交失败（退出码 $STATUS）"
  echo "详情见 /tmp/submit.log"
  echo ""
  echo "常见原因与对策："
  case $STATUS in
    2) echo "  - 课件校验未通过：manifest.json 缺字段或 index.html 元信息不全" ;;
    3) echo "  - Worker 拒绝：限频或权限问题，等 1 分钟重试" ;;
    4) echo "  - 网络错误：检查网络连接后重跑本脚本" ;;
    *) echo "  - 查看完整日志：cat /tmp/submit.log" ;;
  esac
  exit $STATUS
fi
