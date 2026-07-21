#!/usr/bin/env python3
"""
find-hero.py — TeachAny Hero 图查找工具（CDN 优先版 + v7.9.12 SVG 兜底）

按优先级查找课件可用的 hero 封面图，返回 CDN URL 或本地文件：
  L1: image-registry.json 索引 → CDN URL
  L2: CDN 命名规则探测（{subject}/{keyword}-hero.png）
  L3-a: image_gen 兜底（需会话有此工具）→ 生成后上传图床 → 返回 CDN URL
  L3-b: gen-hero-svg.py SVG 兜底（v7.9.12 新增，永不降级）→ 生成 assets/<id>-hero.svg

v7.9.12 更新：Hero 图永不降级。L1/L2 未命中且会话无 image_gen 工具时，
使用 `--gen-svg` 参数直接调用 gen-hero-svg.py 生成 SVG 知识结构图兜底。

不再复制图片到课件本地 assets/，HTML 直接引用 CDN URL（L1/L2）或本地 SVG（L3-b）。
离线/导出场景由 export-pptx.py 等脚本按需下载。

用法:
  python3 scripts/find-hero.py <课件目录>
  python3 scripts/find-hero.py <课件目录> --subject math --grade 8
  python3 scripts/find-hero.py <课件目录> --gen-svg      # L1/L2 未命中时直接生成 SVG 兜底
  python3 scripts/find-hero.py community/ --batch
  python3 scripts/find-hero.py <课件目录> --cdn         # 默认模式，返回 CDN URL
  python3 scripts/find-hero.py <课件目录> --local        # 兼容模式，下载到本地 assets/

输出: JSON 格式 {level, source, url, action}
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# ─── 常量 ───────────────────────────────────────────────

HERO_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.svg'}
SUBJECT_DIRS = ['biology', 'chinese', 'english', 'history', 'math', 'physics', 'science', 'geography', 'chemistry']

# CDN 配置
CDN_BASE = "https://cdn.jsdelivr.net/gh/weponusa/teachany-images@main"
CDN_FALLBACKS = [
    "https://raw.githubusercontent.com/weponusa/teachany-images/main",
    "https://ghfast.top/https://raw.githubusercontent.com/weponusa/teachany-images/main",
]

# teachany-images 本地路径（用于 --local 模式和 L3 上传）
TEACHANY_IMAGES_DIR = Path(os.environ.get(
    'TEACHANY_IMAGES_DIR',
    str(Path.home() / 'CodeBuddy' / '一次函数' / 'teachany-images')
))

# image-registry.json 路径
SCRIPT_DIR = Path(__file__).resolve().parent
REGISTRY_PATH = SCRIPT_DIR.parent / "skill" / "assets" / "image-registry.json"


# ─── 工具函数 ───────────────────────────────────────────

def load_registry() -> dict:
    """加载 image-registry.json"""
    if REGISTRY_PATH.exists():
        with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"images": [], "cdn_base": CDN_BASE}


# node-index.json 缓存（用于 dir → node_id 反查）
_NODE_INDEX_CACHE: dict | None = None


def load_node_index() -> dict:
    """加载 node-index.json，返回 {dir_name: node_id} 映射"""
    global _NODE_INDEX_CACHE
    if _NODE_INDEX_CACHE is not None:
        return _NODE_INDEX_CACHE

    idx_path = SCRIPT_DIR.parent / "data" / "node-index.json"
    if not idx_path.exists():
        _NODE_INDEX_CACHE = {}
        return _NODE_INDEX_CACHE

    try:
        idx = json.load(open(idx_path, 'r', encoding='utf-8'))
        nodes = idx.get('nodes', {})
        # 构造 dir_name → node_id 映射
        # node-index 中 CN 课标的 key 就是完整 node_id（如 bio-m-biosphere-largest）
        # 需要建立 dir_name（如 bio-biosphere-largest）→ node_id 的映射
        dir_to_node = {}
        for node_id, node_info in nodes.items():
            if node_info.get('curriculum') != 'cn':
                continue
            # courses 字段包含目录名
            courses = node_info.get('courses', [])
            if courses:
                for c in courses:
                    if isinstance(c, str):
                        dir_to_node[c] = node_id
                    elif isinstance(c, dict):
                        cid = c.get('dir', c.get('id', ''))
                        if cid:
                            dir_to_node[cid] = node_id
        _NODE_INDEX_CACHE = dir_to_node
        return _NODE_INDEX_CACHE
    except Exception:
        _NODE_INDEX_CACHE = {}
        return _NODE_INDEX_CACHE


def resolve_node_id(course_dir: Path, text: str) -> str:
    """解析课件的唯一 node_id

    优先级：
    1. HTML <meta name="teachany-node"> 标签（权威来源）
    2. node-index.json 中 courses 反查（目录名 → node_id）
    3. 兜底：目录名作为 course_id（向后兼容）
    """
    # 1. 从 HTML meta 提取
    m = re.search(r'<meta\s+name="teachany-node"\s+content="([^"]+)"', text)
    if not m:
        m = re.search(r'<meta\s+name="course-node"\s+content="([^"]+)"', text)
    if m:
        return m.group(1).strip()

    # 2. 从 node-index.json 反查
    dir_map = load_node_index()
    dir_name = course_dir.name
    if dir_name in dir_map:
        return dir_map[dir_name]

    # 3. 兜底
    return dir_name


def extract_course_meta(course_dir: Path) -> dict:
    """从课件 index.html 提取元信息

    核心字段：
    - node_id: 知识点唯一标识（所有资源匹配基于此）
    - course_id: 目录名（向后兼容，仅用于 L2 关键词提取）
    """
    html_path = course_dir / 'index.html'
    meta = {
        'course_id': course_dir.name,   # 目录名，向后兼容
        'node_id': course_dir.name,     # 默认同目录名，后面会覆盖
        'subject': '',
        'grade': 0,
        'title': '',
    }
    if not html_path.exists():
        return meta

    text = html_path.read_text(encoding='utf-8', errors='ignore')

    # 提取 title
    m = re.search(r'<title>([^<]+)</title>', text)
    if m:
        meta['title'] = m.group(1).strip()

    # 提取 subject
    m = re.search(r'<meta\s+name="teachany-subject"\s+content="([^"]+)"', text)
    if not m:
        m = re.search(r'"subject"\s*:\s*"([^"]+)"', text)
    if m:
        meta['subject'] = m.group(1).strip().lower()

    # 提取 grade
    m = re.search(r'<meta\s+name="teachany-grade"\s+content="(\d+)"', text)
    if not m:
        m = re.search(r'"grade"\s*:\s*(\d+)', text)
    if m:
        meta['grade'] = int(m.group(1))

    # 提取 node_id（核心：所有资源匹配基于此）
    meta['node_id'] = resolve_node_id(course_dir, text)

    return meta


def subject_to_dirname(subject: str) -> str:
    """将学科关键词映射到 CDN 目录名"""
    mapping = {
        'math': 'math', '数学': 'math',
        'physics': 'physics', '物理': 'physics',
        'chemistry': 'chemistry', '化学': 'chemistry',
        'biology': 'biology', '生物': 'biology',
        'chinese': 'chinese', '语文': 'chinese',
        'english': 'english', '英语': 'english',
        'history': 'history', '历史': 'history',
        'geography': 'geography', '地理': 'geography',
        'politics': 'politics', '政治': 'politics',
        'science': 'science', '科学': 'science',
    }
    return mapping.get(subject, subject)


def extract_keywords(course_id: str, title: str) -> list[str]:
    """从 course_id 和 title 提取搜索关键词"""
    keywords = []

    # 从 course_id 提取（如 bio-h-cell-membrane → cell-membrane）
    parts = course_id.split('-')
    skip_prefixes = {'bio', 'bioh', 'h', 'm', 'e', 'chn', 'sci', 'math', 'phys',
                     'hist', 'geo', 'pol', 'eng', 'chem', 'sci', 'info'}
    meaningful = []
    for p in parts:
        if p.lower() not in skip_prefixes:
            meaningful.append(p)
    if meaningful:
        keywords.append('-'.join(meaningful))

    # 从 title 提取中文关键词（2-4 字的词）
    zh_words = re.findall(r'[\u4e00-\u9fff]{2,4}', title)
    keywords.extend(zh_words[:3])

    return keywords


def build_cdn_url(subject: str, keyword: str) -> str:
    """构造 CDN URL"""
    subj_dir = subject_to_dirname(subject)
    return f"{CDN_BASE}/{subj_dir}/{keyword}-hero.png"


# ─── L1：image-registry.json 索引查找 ────────────────────

def find_l1_registry(node_id: str, subject: str, keywords: list[str],
                      course_id: str = '') -> dict | None:
    """L1: 从 image-registry.json 查找匹配的 CDN URL

    匹配优先级：
    1. node_id 精确匹配 match_nodes（权威路径）
    2. course_id 精确匹配 match_nodes（向后兼容，旧注册条目可能用目录名）
    3. 标签模糊匹配
    """
    registry = load_registry()
    images = registry.get("images", [])
    cdn_base = registry.get("cdn_base", CDN_BASE)

    # 1. node_id 精确匹配 match_nodes
    for img in images:
        if img.get("slot") != "hero":
            continue
        match_nodes = img.get("match_nodes", [])
        if node_id in match_nodes:
            url = img.get("url") or f"{cdn_base}/{img.get('file', '')}"
            return {
                'level': 'L1',
                'source': 'image-registry',
                'url': url,
                'file': img.get('file', ''),
                'id': img.get('id', ''),
                'matched_by': 'node_id',
                'action': 'use_cdn_url',
            }

    # 1.5 course_id 精确匹配（向后兼容）
    if course_id and course_id != node_id:
        for img in images:
            if img.get("slot") != "hero":
                continue
            match_nodes = img.get("match_nodes", [])
            if course_id in match_nodes:
                url = img.get("url") or f"{cdn_base}/{img.get('file', '')}"
                return {
                    'level': 'L1',
                    'source': 'image-registry',
                    'url': url,
                    'file': img.get('file', ''),
                    'id': img.get('id', ''),
                    'matched_by': 'course_id_fallback',
                    'action': 'use_cdn_url',
                }

    # 2. 标签匹配
    norm_keywords = [kw.lower().replace(' ', '-') for kw in keywords]
    best_match = None
    best_score = 0

    for img in images:
        if img.get("slot") != "hero":
            continue
        img_subject = img.get("subject", "")
        img_tags = [t.lower() for t in img.get("tags", [])]

        # 学科必须匹配
        if subject and img_subject != subject_to_dirname(subject):
            continue

        score = 0
        for kw in norm_keywords:
            for tag in img_tags:
                if kw == tag:
                    score += 10
                elif kw in tag or tag in kw:
                    score += 5

        if score > best_score:
            best_score = score
            best_match = img

    if best_match and best_score >= 5:
        url = best_match.get("url") or f"{cdn_base}/{best_match.get('file', '')}"
        return {
            'level': 'L1',
            'source': 'image-registry',
            'url': url,
            'file': best_match.get('file', ''),
            'id': best_match.get('id', ''),
            'match_score': best_score,
            'action': 'use_cdn_url',
        }

    return None


# ─── L2：CDN 命名规则探测 ───────────────────────────────

def find_l2_cdn_probe(subject: str, keywords: list[str]) -> dict | None:
    """L2: 按命名规则构造 CDN URL 并探测可用性

    注意：此函数不实际发起 HTTP 请求（避免依赖），
    而是返回最可能的 CDN URL，由调用方验证。
    """
    if not subject or not keywords:
        return None

    subj_dir = subject_to_dirname(subject)

    # 尝试每个关键词
    for kw in keywords:
        kw_slug = kw.lower().replace(' ', '-')
        url = f"{CDN_BASE}/{subj_dir}/{kw_slug}-hero.png"
        file_path = f"{subj_dir}/{kw_slug}-hero.png"

        return {
            'level': 'L2',
            'source': 'cdn_naming_convention',
            'url': url,
            'file': file_path,
            'keyword': kw_slug,
            'action': 'use_cdn_url',
            'note': 'CDN URL 已构造，需验证是否可访问（curl -sI URL）',
        }

    return None


# ─── L3-a：image_gen 兜底（会话有此工具时）──────────────

def generate_l3_hint(course_dir: Path, meta: dict) -> dict:
    """L3-a: 未命中，输出 image_gen 推荐提示 + 上传图床指引"""
    grade = meta.get('grade', 9)
    subject = meta.get('subject', 'general')
    title = meta.get('title', course_dir.name)
    node_id = meta.get('node_id', course_dir.name)
    course_id = meta.get('course_id', course_dir.name)

    # 按学段选 prompt 模板
    if grade <= 6:
        style = 'warm cartoon illustration for elementary school students, bright vivid colors, friendly characters, simple shapes, educational poster style'
    elif grade <= 9:
        style = 'semi-realistic illustration with infographic elements, clear visual hierarchy, educational textbook style for middle school'
    else:
        style = 'academic geometric illustration, professional dark blue palette, conceptual diagram aesthetic, suitable for high school textbook cover'

    prompt = f'{title}, {style}, 16:9 horizontal composition'

    # 构造目标 CDN 路径
    subj_dir = subject_to_dirname(subject)
    keywords = extract_keywords(course_id, title)
    keyword_slug = keywords[0] if keywords else node_id
    target_cdn_file = f"{subj_dir}/{keyword_slug}-hero.png"
    target_cdn_url = f"{CDN_BASE}/{target_cdn_file}"

    return {
        'level': 'L3',
        'source': 'image_gen_required',
        'action': 'generate_and_upload',
        'prompt': prompt,
        'target_cdn_url': target_cdn_url,
        'target_cdn_file': target_cdn_file,
        'subject': subject,
        'grade': grade,
        'steps': [
            f'1. 调用 image_gen 生成 hero 图（prompt: {prompt[:80]}...）',
            f'2. 上传到 teachany-images: git add {target_cdn_file} && git commit && git push',
            f'3. 注册索引: python3 scripts/image_resolver.py register --id {subj_dir}-{keyword_slug}-hero --file {target_cdn_file} --subject {subj_dir} --slot hero --match-nodes {node_id}',
            f'4. HTML 引用: <img src="{target_cdn_url}">',
        ],
        'fallback_note': '若会话无 image_gen 工具，请加 --gen-svg 参数走 L3-b SVG 兜底（v7.9.12 永不降级）',
    }


# ─── L3-b：gen-hero-svg.py SVG 兜底（v7.9.12 新增）──────────

def generate_l3_svg(course_dir: Path, meta: dict) -> dict:
    """L3-b: 调用 gen-hero-svg.py 生成 SVG 知识结构图兜底（永不降级）"""
    course_id = meta.get('course_id', course_dir.name)
    svg_path = course_dir / 'assets' / f'{course_id}-hero.svg'

    script = Path(__file__).resolve().parent / 'gen-hero-svg.py'
    if not script.exists():
        return {
            'level': 'L3-svg',
            'source': 'gen-hero-svg.py missing',
            'action': 'error',
            'error': f'gen-hero-svg.py 不存在: {script}',
        }

    # 调用 gen-hero-svg.py（它会优先读 manifest.json，无参数即可）
    try:
        result = subprocess.run(
            ['python3', str(script), str(course_dir)],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            return {
                'level': 'L3-svg',
                'source': 'gen-hero-svg.py failed',
                'action': 'error',
                'error': result.stderr.strip() or result.stdout.strip(),
            }

        if not svg_path.exists():
            return {
                'level': 'L3-svg',
                'source': 'gen-hero-svg.py produced no file',
                'action': 'error',
                'error': f'脚本退出码 0 但文件未生成: {svg_path}',
            }

        return {
            'level': 'L3-svg',
            'source': 'gen-hero-svg.py',
            'action': 'svg_generated',
            'path': str(svg_path.relative_to(course_dir)),
            'size_kb': round(svg_path.stat().st_size / 1024, 1),
            'url': f'./{svg_path.relative_to(course_dir).as_posix()}',
            'note': 'v7.9.12 L3 SVG 兜底（永不降级），HTML 中 <img src> 直接引用此相对路径',
        }
    except subprocess.TimeoutExpired:
        return {
            'level': 'L3-svg',
            'source': 'gen-hero-svg.py timeout',
            'action': 'error',
            'error': 'gen-hero-svg.py 30 秒超时',
        }
    except Exception as e:
        return {
            'level': 'L3-svg',
            'source': 'gen-hero-svg.py exception',
            'action': 'error',
            'error': str(e),
        }


# ─── 本地兼容模式（--local）─────────────────────────────

def find_local_hero(course_dir: Path) -> dict | None:
    """查找课件本地 assets/ 下已有的 hero 图（兼容旧课件）"""
    assets_dir = course_dir / 'assets'
    if not assets_dir.exists():
        return None

    for f in assets_dir.rglob('*'):
        if f.is_file() and f.suffix.lower() in HERO_EXTENSIONS and 'hero' in f.name.lower():
            return {
                'level': 'L0',
                'source': 'local_assets',
                'path': str(f.relative_to(course_dir)),
                'size_kb': round(f.stat().st_size / 1024, 1),
                'action': 'use_local',
                'note': '本地文件，建议迁移到 CDN 以减小仓库体积',
            }
    return None


def download_cdn_to_local(cdn_url: str, course_dir: Path, course_id: str) -> dict | None:
    """将 CDN 图片下载到课件本地 assets/（--local 模式用）"""
    try:
        import urllib.request
        assets_dir = course_dir / 'assets'
        assets_dir.mkdir(parents=True, exist_ok=True)
        target = assets_dir / f"{course_id}-hero.png"
        urllib.request.urlretrieve(cdn_url, str(target))
        return {
            'action': 'downloaded',
            'local_path': str(target.relative_to(course_dir)),
            'cdn_url': cdn_url,
        }
    except Exception as e:
        return {'action': 'download_failed', 'error': str(e), 'cdn_url': cdn_url}


# ─── 主流程 ─────────────────────────────────────────────

def find_hero_for_course(course_dir: Path, subject_override: str = '',
                          grade_override: int = 0, cdn_mode: bool = True,
                          dry_run: bool = False, gen_svg: bool = False) -> dict:
    """对单个课件执行查找

    参数:
        gen_svg: v7.9.12 新增。L1/L2 未命中时直接调用 gen-hero-svg.py
                 生成 SVG 知识结构图兜底（Hero 永不降级）。
                 False（默认）时仅输出 image_gen 提示（L3-a），需主 agent 决策。
    """

    course_dir = course_dir.resolve()
    if not course_dir.exists():
        return {'error': f'课件目录不存在: {course_dir}'}

    # 提取元信息
    meta = extract_course_meta(course_dir)
    if subject_override:
        meta['subject'] = subject_override.lower()
    if grade_override:
        meta['grade'] = grade_override

    keywords = extract_keywords(meta['course_id'], meta['title'])

    result = {
        'course_id': meta['course_id'],
        'node_id': meta['node_id'],
        'title': meta['title'],
        'subject': meta['subject'],
        'grade': meta['grade'],
        'keywords': keywords,
    }

    # CDN 模式（默认）：L1 → L2 → L3
    if cdn_mode:
        # L1: image-registry.json（用 node_id 匹配）
        l1 = find_l1_registry(meta['node_id'], meta['subject'], keywords,
                              course_id=meta['course_id'])
        if l1:
            result['hero'] = l1
            result['hero']['status'] = 'found'
            return result

        # L2: CDN 命名规则探测
        l2 = find_l2_cdn_probe(meta['subject'], keywords)
        if l2:
            result['hero'] = l2
            result['hero']['status'] = 'found'
            return result

        # L3-b: gen-hero-svg.py SVG 兜底（v7.9.12，--gen-svg 时自动走）
        if gen_svg:
            l3_svg = generate_l3_svg(course_dir, meta)
            result['hero'] = l3_svg
            result['hero']['status'] = 'svg_generated' if l3_svg.get('action') == 'svg_generated' else 'error'
            return result

        # L3-a: image_gen 兜底提示（需主 agent 决策）
        l3 = generate_l3_hint(course_dir, meta)
        result['hero'] = l3
        result['hero']['status'] = 'needs_generation'
        return result

    # 本地兼容模式：先查本地，再查 CDN 并下载
    else:
        local = find_local_hero(course_dir)
        if local:
            result['hero'] = local
            result['hero']['status'] = 'found_local'
            return result

        # 尝试从 CDN 下载到本地
        l1 = find_l1_registry(meta['node_id'], meta['subject'], keywords,
                              course_id=meta['course_id'])
        if l1:
            if not dry_run:
                dl = download_cdn_to_local(l1['url'], course_dir, meta['course_id'])
                result['hero'] = {**l1, 'download': dl, 'status': 'downloaded'}
            else:
                result['hero'] = {**l1, 'status': 'would_download'}
            return result

        l2 = find_l2_cdn_probe(meta['subject'], keywords)
        if l2:
            if not dry_run:
                dl = download_cdn_to_local(l2['url'], course_dir, meta['course_id'])
                result['hero'] = {**l2, 'download': dl, 'status': 'downloaded'}
            else:
                result['hero'] = {**l2, 'status': 'would_download'}
            return result

        # L3-b: SVG 兜底
        if gen_svg:
            l3_svg = generate_l3_svg(course_dir, meta)
            result['hero'] = l3_svg
            result['hero']['status'] = 'svg_generated' if l3_svg.get('action') == 'svg_generated' else 'error'
            return result

        l3 = generate_l3_hint(course_dir, meta)
        result['hero'] = l3
        result['hero']['status'] = 'needs_generation'
        return result


def main():
    parser = argparse.ArgumentParser(description='TeachAny Hero 图查找工具（CDN 优先 + v7.9.12 SVG 兜底）')
    parser.add_argument('path', help='课件目录或 community/ 根目录')
    parser.add_argument('--subject', default='', help='学科覆盖（如 math/physics/history）')
    parser.add_argument('--grade', type=int, default=0, help='年级覆盖')
    parser.add_argument('--batch', action='store_true', help='批量模式')
    parser.add_argument('--dry-run', action='store_true', help='仅查找不下载')
    parser.add_argument('--cdn', action='store_true', default=True, help='CDN 模式（默认）')
    parser.add_argument('--local', action='store_true', help='本地模式：下载 CDN 图片到 assets/')
    parser.add_argument('--gen-svg', action='store_true', help='v7.9.12：L1/L2 未命中时自动调用 gen-hero-svg.py 生 SVG 兜底（永不降级）')
    parser.add_argument('--json', action='store_true', help='输出 JSON 格式')
    args = parser.parse_args()

    cdn_mode = not args.local
    path = Path(args.path)

    if args.batch or (path.is_dir() and (path / 'community').exists() or path.name == 'community'):
        # 批量模式
        community_dir = path if path.name == 'community' else path / 'community'
        if not community_dir.exists():
            print(f'错误: {community_dir} 不存在', file=sys.stderr)
            sys.exit(1)

        results = []
        for d in sorted(community_dir.iterdir()):
            if not d.is_dir():
                continue
            if d.name in ('archive', 'pending', 'node_modules'):
                continue
            if not (d / 'index.html').exists():
                continue
            r = find_hero_for_course(d, args.subject, args.grade, cdn_mode,
                                     args.dry_run, args.gen_svg)
            results.append(r)

        # 统计
        stats = {'L0': 0, 'L1': 0, 'L2': 0, 'L3': 0, 'L3-svg': 0, 'error': 0}
        for r in results:
            if 'error' in r:
                stats['error'] += 1
            else:
                level = r['hero'].get('level', '?')
                stats[level] = stats.get(level, 0) + 1

        if args.json:
            print(json.dumps({'results': results, 'stats': stats}, ensure_ascii=False, indent=2))
        else:
            print(f'\n=== Hero 查找统计（CDN 优先 + v7.9.12 SVG 兜底）===')
            print(f'  L0 本地已有: {stats.get("L0", 0)}')
            print(f'  L1 索引命中: {stats.get("L1", 0)}')
            print(f'  L2 CDN 命名: {stats.get("L2", 0)}')
            print(f'  L3 需生图:   {stats.get("L3", 0)}')
            print(f'  L3-svg 兜底: {stats.get("L3-svg", 0)}')
            print()

            for r in results:
                if 'error' in r:
                    print(f'  ❌ {r["error"]}')
                    continue
                hero = r['hero']
                level = hero.get('level', '?')
                cid = r['course_id']
                if level == 'L0':
                    print(f'  📁 L0 {cid} → {hero["path"]} ({hero["size_kb"]}KB, 本地)')
                elif level == 'L1':
                    url = hero.get('url', '?')
                    print(f'  🌐 L1 {cid} → {url}')
                elif level == 'L2':
                    url = hero.get('url', '?')
                    print(f'  🔗 L2 {cid} → {url} (命名规则)')
                elif level == 'L3':
                    print(f'  🎨 L3 {cid} → 需生成: {hero["prompt"][:60]}...')
                elif level == 'L3-svg':
                    if hero.get('action') == 'svg_generated':
                        print(f'  🎨 L3-svg {cid} → 已生成 {hero["path"]} ({hero["size_kb"]}KB)')
                    else:
                        print(f'  ❌ L3-svg {cid} → 失败: {hero.get("error", "")}')

        # L3 需生图 or L3-svg 生成失败时 exit 1
        l3_error = sum(1 for r in results
                       if r.get('hero', {}).get('level') == 'L3-svg'
                       and r.get('hero', {}).get('action') != 'svg_generated')
        if stats.get('L3', 0) > 0 or l3_error > 0:
            sys.exit(1)
        sys.exit(0)

    else:
        # 单课件模式
        result = find_hero_for_course(path, args.subject, args.grade, cdn_mode,
                                      args.dry_run, args.gen_svg)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            if 'error' in result:
                print(f'❌ {result["error"]}')
                sys.exit(1)
            hero = result['hero']
            level = hero.get('level', '?')
            print(f'\n课件: {result["course_id"]}《{result["title"]}》')
            print(f'学科: {result["subject"]}  年级: G{result["grade"]}')
            print(f'搜索关键词: {result["keywords"]}')
            print()
            if level == 'L0':
                print(f'📁 L0 本地命中: {hero["path"]} ({hero["size_kb"]}KB)')
                print(f'   建议: 迁移到 CDN 以减小仓库体积')
            elif level == 'L1':
                print(f'🌐 L1 索引命中: {hero["url"]}')
                print(f'   ID: {hero.get("id", "?")}  文件: {hero.get("file", "?")}')
                print(f'   动作: HTML 中引用此 CDN URL')
            elif level == 'L2':
                print(f'🔗 L2 CDN 命名命中: {hero["url"]}')
                print(f'   关键词: {hero.get("keyword", "?")}')
                print(f'   动作: 验证 CDN 可访问性后引用此 URL')
            elif level == 'L3':
                print(f'🎨 L1-L2 未命中，需调用 image_gen 生成')
                print(f'   推荐 prompt: {hero["prompt"]}')
                print(f'   目标 CDN: {hero.get("target_cdn_url", "?")}')
                for step in hero.get('steps', []):
                    print(f'   {step}')
                print(f'   💡 若会话无 image_gen 工具，加 --gen-svg 走 L3 SVG 兜底（v7.9.12 永不降级）')
            elif level == 'L3-svg':
                if hero.get('action') == 'svg_generated':
                    print(f'🎨 L3 SVG 兜底已生成: {hero["path"]} ({hero["size_kb"]}KB)')
                    print(f'   动作: HTML 中 <img src="{hero["url"]}"> 即可')
                else:
                    print(f'❌ L3 SVG 兜底失败: {hero.get("error", "")}')
                    sys.exit(1)

        if result.get('hero', {}).get('status') == 'needs_generation':
            sys.exit(1)
        if result.get('hero', {}).get('status') == 'error':
            sys.exit(1)


if __name__ == '__main__':
    main()
