#!/usr/bin/env python3
"""
TeachAny 课件索引重建工具

原则：以实际存在的课件文件为唯一信源（single source of truth）
1. 扫描 examples/ 和 community/ 下所有课件（v6.1 起同时支持两个通道）
2. 读取每个课件的 manifest.json
3. 根据 manifest 中的 subject + node_id 反查知识树
4. 修复知识树中的 courses 数组和 status
5. 清理重复节点
6. 重建 registry.json

v6.1 变更（2026-04-24）:
- scan_courses() 同时扫 examples/ 和 community/（除 drafts/ 和 pending/）
- registry.path 根据实际位置生成（examples/xxx 或 community/xxx）
- 课件同名冲突时 examples/ 优先（视为官方升级版）

v6.2 变更（2026-04-27）:
- name 字段回退：优先 name → title_zh → title（兼容旧 manifest）
- 新增 detect_images() 自动检测 hero_image / scene_image
- registry entry 增加 hero_image / scene_image 字段

v6.3 变更（2026-04-29）:
- 集成 image_resolver.py 的统一图片发现机制
- detect_images_unified() 先查 image-registry.json（CDN 预制图），再查本地 assets/
- hero_image 字段可能为 CDN URL（以 "cdn:" 前缀标记）或本地相对路径

v7.0 变更（2026-05-09）:
- 多版本课件支持：同 node_id 允许多个课件并列（不同 author）
- 同 author+node_id 覆盖逻辑：保留 version 最高的那个（旧版本不挂载到树）
- manifest.json 新增 variant 字段支持（如 "基础版"、"进阶版"）
- 知识树 courses 数组新增结构化注释（带 author/variant 标识供前端选择器使用）
- registry entry 新增 variant 字段
"""
import json
import re
import subprocess
import sys
from pathlib import Path
from collections import defaultdict
import copy

# 需要扫描的课件目录；每个项是 (目录, 是否 official 候选)
# v6.1: examples/ 仍是官方通道，community/ 加入扫描（skip drafts/ 和 pending/）
COURSE_DIRS = [
    ('examples',  True),   # 官方示例课件
    ('community', False),  # 社区课件（PR 合并后进这里）
]

# community/ 下忽略的子目录（这些不是课件）
COMMUNITY_SKIP = {'drafts', 'pending', 'README.md'}

# v6.2: 图片后缀白名单
IMG_EXTS = {'.png', '.jpg', '.jpeg', '.webp'}

# v6.3: image-registry.json 路径
IMAGE_REGISTRY_PATH = Path(__file__).resolve().parents[1] / "skill" / "assets" / "image-registry.json"


def load_image_registry():
    """加载 image-registry.json 图片索引"""
    if IMAGE_REGISTRY_PATH.exists():
        with open(IMAGE_REGISTRY_PATH, encoding='utf-8') as f:
            return json.load(f)
    return {"images": []}


def resolve_image_from_registry(node_id, slot, subject=None):
    """从 image-registry.json 中查找匹配的图片（轻量版 resolve，无需导入 image_resolver.py）

    与 image_resolver.py 的 resolve_image() 逻辑一致，但只做精确匹配（score ≥ 500）
    返回: (url, local_filename) 或 (None, None)
    """
    registry = load_image_registry()
    for img in registry.get("images", []):
        if node_id in img.get("match_nodes", []) and img.get("slot") == slot:
            return img.get("url", ""), Path(img.get("file", "")).name
    return None, None


def extract_teachany_version_from_html(course_dir: Path):
    """从 index.html 的 <meta name="teachany-version"> 中提取版本号

    v6.3 新增：当 manifest.json 中没有 teachany_version 字段时，
    从课件 HTML 的 meta 标签中解析版本号作为回退。
    """
    index_path = course_dir / 'index.html'
    if not index_path.exists():
        return ''
    try:
        html = index_path.read_text(encoding='utf-8', errors='ignore')
        # 匹配 <meta name="teachany-version" content="6.1">
        m = re.search(r'<meta\s+name=["\']teachany-version["\']\s+content=["\']([\d.]+)["\']', html, re.IGNORECASE)
        if m:
            return m.group(1)
    except Exception:
        pass
    return ''


def detect_images(course_dir: Path):
    """自动检测课件的 hero 和 scene 图片（v6.2 统一命名规范）

    检测优先级：
      1. *-hero.{png,jpg,webp}   后缀匹配（主流模式）
      2. hero-*.{png,jpg,webp}   前缀匹配（兼容旧命名）
      3. hero.{png,jpg,webp}     纯名称匹配
      4. assets/ 下字母序第一张  兜底

    同理检测 *-scene / scene-* / scene。
    返回: (hero_image_rel, scene_image_rel)  相对于 course_dir 的路径字符串
    """
    # 搜索 assets/ 和 images/ 两个可能的目录
    img_dir = None
    for name in ('assets', 'images'):
        candidate = course_dir / name
        if candidate.exists() and candidate.is_dir():
            img_dir = candidate
            break
    if img_dir is None:
        return '', ''

    all_imgs = sorted([
        p for p in img_dir.iterdir()
        if p.is_file() and p.suffix.lower() in IMG_EXTS
    ])
    if not all_imgs:
        return '', ''

    def find_typed(keyword):
        """按优先级查找指定类型的图片"""
        # 1. 后缀匹配：*-keyword.ext（主流模式）
        for p in all_imgs:
            if p.stem.lower().endswith(f'-{keyword}'):
                return p
        # 2. 前缀匹配：keyword-*.ext（兼容旧命名）
        for p in all_imgs:
            if p.stem.lower().startswith(f'{keyword}-'):
                return p
        # 3. 纯名称匹配：keyword.ext
        for p in all_imgs:
            if p.stem.lower() == keyword:
                return p
        return None

    hero = find_typed('hero')
    scene = find_typed('scene')

    def to_rel(p):
        if p is None:
            return ''
        return str(p.relative_to(course_dir))

    # hero 兜底：取第一张图
    if hero is None and all_imgs:
        hero = all_imgs[0]

    return to_rel(hero), to_rel(scene)


def scan_courses():
    """扫描 examples/ 和 community/ 下所有实际存在的课件

    返回: { course_id: (manifest_dict, source_dir) }
    source_dir: 'examples' 或 'community'
    同名冲突时 examples/ 优先
    """
    courses = {}  # course_id -> (manifest, source_dir)
    for base_dir, _is_official in COURSE_DIRS:
        base = Path(base_dir)
        if not base.exists():
            continue
        for d in base.iterdir():
            if not d.is_dir():
                continue
            if d.name.startswith('_') or d.name.startswith('.'):
                continue
            if base_dir == 'community' and d.name in COMMUNITY_SKIP:
                continue
            manifest_path = d / 'manifest.json'
            index_path = d / 'index.html'
            if not (manifest_path.exists() and index_path.exists()):
                continue
            try:
                with open(manifest_path, encoding='utf-8') as f:
                    manifest = json.load(f)
            except json.JSONDecodeError:
                print(f"  ⚠️  {base_dir}/{d.name}: manifest.json 格式错误，跳过")
                continue
            # 冲突处理：如果 examples/ 已有同名，community/ 版本跳过
            if d.name in courses:
                existing_src = courses[d.name][1]
                if existing_src == 'examples':
                    print(f"  ℹ️  {d.name}: community/ 版本被 examples/ 覆盖（正常）")
                    continue
            courses[d.name] = (manifest, base_dir)
    return courses


def load_tree(tree_file):
    """加载知识树"""
    with open(tree_file, encoding='utf-8') as f:
        return json.load(f)


def save_tree(tree_file, tree_data):
    """保存知识树"""
    with open(tree_file, 'w', encoding='utf-8') as f:
        json.dump(tree_data, f, ensure_ascii=False, indent=2)
    f.close()
    # 确保结尾换行
    with open(tree_file, 'a') as f:
        f.write('\n')


def deduplicate_nodes(nodes_list):
    """去重节点列表（按 id 去重，保留最完整的那个）"""
    seen = {}
    for node in nodes_list:
        nid = node.get('id', '')
        if nid not in seen:
            seen[nid] = node
        else:
            # 保留有 courses 的版本
            existing = seen[nid]
            if not existing.get('courses') and node.get('courses'):
                seen[nid] = node
            elif existing.get('courses') and node.get('courses'):
                # 合并 courses
                merged = list(set(existing['courses'] + node['courses']))
                seen[nid]['courses'] = merged
    return list(seen.values())


def subject_to_tree_prefix(subject):
    """从学科名映射到知识树文件前缀"""
    mapping = {
        'math': ['math-elementary', 'math-middle', 'math-high'],
        'physics': ['physics-middle', 'physics-high'],
        'chemistry': ['chemistry-middle', 'chemistry-high'],
        'biology': ['biology-middle', 'biology-high'],
        'chinese': ['chinese-elementary', 'chinese-middle', 'chinese-high'],
        'english': ['english-elementary', 'english-middle', 'english-high'],
        'geography': ['geography-high'],
        'earth_science': ['earth-science-middle'],
        'science': ['science-elementary'],  # v5.34.6 新增：小学科学（2022 版课标）
        'info_tech': ['info-tech-high'],
    }
    return mapping.get(subject, [])


def grade_to_stage(grade):
    """从年级推断学段"""
    if grade <= 6:
        return 'elementary'
    elif grade <= 9:
        return 'middle'
    else:
        return 'high'


def main():
    print('='*70)
    print('TeachAny 课件索引重建工具')
    print('='*70)

    # 用户身份即可重建索引：课件制作完成后直接扫描 community/ 并注册到 Gallery。

    # 0. 规范化社区上传课件（修复中文 subject/grade、缺 node_id、树缺节点等上传断链）
    print('\n🧩 步骤0: 规范化社区上传课件...')
    helper0 = Path('scripts') / 'register-community-uploads.py'
    if helper0.exists():
        result0 = subprocess.run([sys.executable, str(helper0)], text=True, capture_output=True)
        if result0.returncode != 0:
            print('  ❌ register-community-uploads.py 执行失败')
            if result0.stdout.strip(): print(result0.stdout.strip())
            if result0.stderr.strip(): print(result0.stderr.strip())
            raise SystemExit(result0.returncode)
        print('  ' + ((result0.stdout.strip().splitlines() or ['✅ 完成'])[0]))
    else:
        print('  ⚠️  scripts/register-community-uploads.py 不存在，跳过')

    # 1. 扫描课件
    print('\n📦 步骤1: 扫描课件文件...')
    courses = scan_courses()
    print(f'   找到 {len(courses)} 个完整课件')

    # 2. 建立课件→知识节点的映射
    print('\n🔗 步骤2: 建立课件→知识节点映射...')

    # v6.1 先一次性加载旧 registry + 探测 legacy 课件（index.html 存在但无 manifest）
    old_registry = {}
    try:
        with open('registry.json', encoding='utf-8') as f:
            old_data = json.load(f)
            for c in old_data.get('courses', []):
                old_registry[c['id']] = c
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    legacy_preserved = []  # [(course_id, old_entry)]
    for cid, old_entry in old_registry.items():
        if cid in courses:
            continue
        old_path = old_entry.get('path', '')
        if old_path and Path(old_path, 'index.html').exists():
            legacy_preserved.append((cid, old_entry))
    legacy_ids = {cid for cid, _ in legacy_preserved}
    if legacy_ids:
        print(f'   🧰 遗留兼容：{len(legacy_ids)} 个旧课件无 manifest.json 但 index.html 存在，视为存在')

    # 按 (subject, node_id) 分组
    node_courses = defaultdict(list)  # (subject, node_id) -> [course_id]
    for course_id, (manifest, _src) in courses.items():
        subject = manifest.get('subject', '')
        node_id = manifest.get('node_id', '')
        if subject and node_id:
            node_courses[(subject, node_id)].append(course_id)
        else:
            print(f'  ⚠️  {course_id}: 缺少 subject 或 node_id')
    # v6.5: legacy 课件（无 manifest 但 index.html 存在）也反向挂到树节点
    # 用旧 registry 里记录的 subject + node_id
    # ⭐ v7.0: 移到覆盖逻辑之前，确保 legacy 也被同 author 覆盖
    legacy_mounted = 0
    for cid, old_entry in legacy_preserved:
        sub = old_entry.get('subject', '')
        nid = old_entry.get('node_id', '')
        if sub and nid:
            node_courses[(sub, nid)].append(cid)
            legacy_mounted += 1
    if legacy_mounted:
        print(f'   🔗 legacy 课件已通过 old_registry 信息反向挂载: {legacy_mounted}')

    # ⭐ v7.0 多版本课件覆盖逻辑：
    # 同一知识点（node_id）+ 同一作者（author）→ 仅保留版本号最高的那个（覆盖旧版本）
    # 同一知识点 + 不同作者 → 全部保留（并列展示）
    # 版本号比较使用 tuple 化的数字版本（如 "2.1.0" → (2, 1, 0)）
    def _parse_version(v):
        """将版本字符串转为可比较的 tuple"""
        if not v:
            return (0,)
        parts = re.split(r'[.\-]', str(v).strip())
        result = []
        for p in parts:
            try:
                result.append(int(p))
            except ValueError:
                result.append(0)
        return tuple(result) if result else (0,)

    overridden_courses = set()  # 被覆盖的课件 ID，不挂载到树
    for key, cid_list in list(node_courses.items()):
        if len(cid_list) <= 1:
            continue
        # 按 author 分组
        author_groups = defaultdict(list)  # author -> [(course_id, version_tuple, version_str)]
        for cid in cid_list:
            # 从 courses（有 manifest）或 old_registry（legacy）中取元信息
            if cid in courses:
                manifest = courses[cid][0]
                author = manifest.get('author', 'unknown')
                version = manifest.get('version', '1.0')
            elif cid in old_registry:
                author = old_registry[cid].get('author', 'unknown')
                version = old_registry[cid].get('version', '1.0')
            else:
                author = 'unknown'
                version = '0.0'
            author_groups[author].append((cid, _parse_version(version), version))

        # 同一 author 下只保留最高版本
        keep_ids = []
        for author, versions in author_groups.items():
            if len(versions) == 1:
                keep_ids.append(versions[0][0])
            else:
                # 按版本号降序排列；版本相同时按 ID 长度升序（更短/更规范的 ID 优先）
                sorted_v = sorted(versions, key=lambda x: (x[1], -len(x[0])), reverse=True)
                winner = sorted_v[0]
                keep_ids.append(winner[0])
                # 标记被覆盖的课件
                for loser in sorted_v[1:]:
                    overridden_courses.add(loser[0])
                    print(f'  🔄 {key[1]}: 同作者({author})版本覆盖 — '
                          f'保留 {winner[0]}(v{winner[2]}), '
                          f'覆盖 {loser[0]}(v{loser[2]})')

        # 更新 node_courses 为去重后的列表
        node_courses[key] = keep_ids

    if overridden_courses:
        print(f'   📌 多版本覆盖：{len(overridden_courses)} 个旧版本课件不再挂载到知识树')

    print(f'   {len(node_courses)} 个知识节点有课件')

    # 3. 修复知识树
    print('\n🌳 步骤3: 修复知识树...')
    # ⭐ 递归扫描：包含 data/trees/international/*.json 国际课标树
    tree_files = sorted(Path('data/trees').rglob('*.json'))

    for tree_file in tree_files:
        tree_data = load_tree(tree_file)
        tree_subject = tree_data.get('subject', '')
        tree_name = tree_file.stem
        modified = False

        # 递归处理所有 domain 和 node
        def fix_domain(domain):
            nonlocal modified
            if 'nodes' in domain:
                # 去重节点
                original_count = len(domain['nodes'])
                domain['nodes'] = deduplicate_nodes(domain['nodes'])
                if len(domain['nodes']) < original_count:
                    removed = original_count - len(domain['nodes'])
                    print(f'  🔧 {tree_name}/{domain["id"]}: 去除 {removed} 个重复节点')
                    modified = True

                # 修复每个节点的 courses
                for node in domain['nodes']:
                    fix_node(node, tree_subject)

        def fix_node(node, subject):
            nonlocal modified
            node_id = node.get('id', '')

            # 查找该节点应该有的课件
            expected_courses = node_courses.get((subject, node_id), [])

            # 当前节点的 courses
            current_courses = node.get('courses', [])

            # ⭐ 归一化：剥离 "examples/" 前缀（防止污染，参见 v5.34.5 fix）
            normalized_current = []
            for c in current_courses:
                if isinstance(c, str) and c.startswith('examples/'):
                    stripped = c.split('/', 1)[1]
                    print(f'  🧹 {tree_name}/{node_id}: 归一化 "{c}" → "{stripped}"')
                    normalized_current.append(stripped)
                    modified = True
                else:
                    normalized_current.append(c)
            current_courses = normalized_current

            # 过滤掉不存在的课件引用（legacy 也算"存在"）
            valid_current = [c for c in current_courses if c in courses or c in legacy_ids]
            invalid_current = [c for c in current_courses if c not in courses and c not in legacy_ids]

            if invalid_current:
                print(f'  🗑️  {tree_name}/{node_id}: 移除无效引用 {invalid_current}')
                modified = True

            # 合并：保留有效的 + 添加预期的
            all_courses = list(set(valid_current + expected_courses))

            if set(all_courses) != set(current_courses):
                node['courses'] = sorted(all_courses)
                if all_courses:
                    node['status'] = 'active'
                    if not current_courses:
                        print(f'  ✅ {tree_name}/{node_id}: 添加课件 {all_courses}')
                else:
                    node['status'] = 'gap'
                modified = True
            elif all_courses and node.get('status') != 'active':
                node['status'] = 'active'
                modified = True

            # ⭐ v7.0: 多课件节点写入 course_variants 元信息（供前端选择器）
            if len(all_courses) > 1:
                variants_info = []
                for cid in sorted(all_courses):
                    if cid in courses:
                        m = courses[cid][0]
                        variants_info.append({
                            'id': cid,
                            'author': m.get('author', ''),
                            'variant': m.get('variant', ''),
                            'version': m.get('version', '1.0'),
                            'difficulty': m.get('difficulty', 1),
                        })
                    elif cid in old_registry:
                        oe = old_registry[cid]
                        variants_info.append({
                            'id': cid,
                            'author': oe.get('author', ''),
                            'variant': oe.get('variant', ''),
                            'version': oe.get('version', '1.0'),
                            'difficulty': oe.get('difficulty', 1),
                        })
                if variants_info:
                    old_variants = node.get('course_variants', [])
                    if old_variants != variants_info:
                        node['course_variants'] = variants_info
                        modified = True
            else:
                # 单课件节点：清除 course_variants（如果有的话）
                if 'course_variants' in node:
                    del node['course_variants']
                    modified = True

            # 递归处理子节点
            for key in ['children', 'nodes', 'domains']:
                if key in node:
                    for child in node[key]:
                        fix_node(child, subject)

        # 处理所有 domain
        if 'domains' in tree_data:
            for domain in tree_data['domains']:
                fix_domain(domain)

        if modified:
            save_tree(tree_file, tree_data)
            print(f'  💾 保存: {tree_name}.json')
        else:
            print(f'  ✓ {tree_name}.json: 无需修改')

    # 3.5 (v7.9.6 新增，v7.9.7 扩展 ext-* 学习路径推荐课件)
    #     填充"其他知识"虚拟树，收纳 4 类课件：
    #       (a) manifest.free_mode = true
    #       (b) manifest.node_id 不在任何官方课标树中
    #       (c) manifest 缺 node_id
    #       (d) 无 manifest 但属于 ext-* 学习路径推荐课件（从 HTML meta 提取元信息）
    print('\n✨ 步骤3.5: 填充"其他知识"虚拟树（收纳 free_mode / 未挂载 / ext-* 学习路径推荐课件）...')
    virtual_tree_path = Path('data/trees/other/user-generated.json')
    if virtual_tree_path.exists():
        # 收集所有官方树中存在的 node_id
        all_official_node_ids = set()
        for tree_file in tree_files:
            if tree_file == virtual_tree_path:
                continue
            try:
                td = json.loads(tree_file.read_text(encoding='utf-8'))
            except (OSError, json.JSONDecodeError):
                continue

            def _collect_ids(obj):
                if isinstance(obj, dict):
                    if 'id' in obj and 'name' in obj:
                        all_official_node_ids.add(obj['id'])
                    for k in ('domains', 'nodes', 'children'):
                        if k in obj:
                            for child in obj[k]:
                                _collect_ids(child)
                elif isinstance(obj, list):
                    for item in obj:
                        _collect_ids(item)
            _collect_ids(td)

        # 扫描所有有 manifest 的课件，找出应该放进"其他知识"的
        virtual_nodes = []
        # 强制保留在“其他知识”的跨课标/探究课入口：这些内容即使挂了近似官方 node_id，
        # 也需要在“其他知识”里保留一份发现入口，避免 rebuild-index 把该 Tab 清空。
        OTHER_TREE_FORCE_COURSE_IDS = {
            'math-m-linear-function-inquiry-phone-plan',  # 一次函数 PBL 探究课
            'course-classical-poetry',                    # 古典诗词系统课程
            'chn-pingze-grade1',                          # 古诗平仄启蒙
            'ext-539f176d',                                # 民族文化与宗教研究
        }
        orphan_reasons = {'free_mode': 0, 'node_not_found': 0, 'missing_node_id': 0,
                          'forced_other': 0, 'inquiry_project': 0,
                          'ext_passed': 0, 'ext_rejected': 0}

        # v7.9.8 新增：学科前缀映射，用于"简写 node_id"自动探测
        SUBJECT_PREFIX = {
            'math': 'math', 'mathematics': 'math',
            'chinese': 'chn', 'chn': 'chn',
            'english': 'eng', 'eng': 'eng',
            'physics': 'phy', 'phy': 'phy',
            'chemistry': 'chem', 'chem': 'chem',
            'biology': 'bio', 'bio': 'bio',
            'history': 'hist', 'hist': 'hist',
            'geography': 'geo', 'geo': 'geo',
            'science': 'sci', 'sci': 'sci',
            'info-tech': 'it', 'it': 'it',
        }
        def _level_from_grade(g):
            try: g = int(g)
            except (TypeError, ValueError): return None
            if 1 <= g <= 6: return 'e'
            if 7 <= g <= 9: return 'm'
            if 10 <= g <= 12: return 'h'
            return None

        for cid, (manifest, src) in sorted(courses.items()):
            nid = manifest.get('node_id', '').strip()
            is_free = bool(manifest.get('free_mode'))
            subject = manifest.get('subject', 'other')
            name = manifest.get('title') or manifest.get('name') or cid
            grade = manifest.get('grade', 0)

            reason = None
            lesson_type = (manifest.get('lesson_type') or '').strip()
            if cid in OTHER_TREE_FORCE_COURSE_IDS:
                reason = 'forced_other'
            elif is_free:
                reason = 'free_mode'
            elif lesson_type == 'inquiry-project':
                # 探究课可同时挂正式知识树和“其他知识/探究课”入口，便于 PBL 场景发现。
                reason = 'inquiry_project'
            elif not nid:
                reason = 'missing_node_id'
            elif nid not in all_official_node_ids:
                # v7.9.8 智能探测：尝试补全 <subject_prefix>-<level>- 前缀
                sp = SUBJECT_PREFIX.get(subject)
                lv = _level_from_grade(grade)
                candidate = None
                if sp and lv:
                    full = f'{sp}-{lv}-{nid}'
                    if full in all_official_node_ids:
                        candidate = full
                # 也尝试去掉已有前缀（如果 nid 已经是完整格式但拼错）
                if not candidate and sp:
                    for lv2 in ('e', 'm', 'h'):
                        full = f'{sp}-{lv2}-{nid}'
                        if full in all_official_node_ids:
                            candidate = full
                            break

                if candidate:
                    print(f'  ⚠️ 检测到简写 node_id：{cid} "{nid}" 应为 "{candidate}"')
                    print(f'     → 请修正 manifest.node_id 为 "{candidate}"（课件暂挂"其他知识"）')
                reason = 'node_not_found'

            if not reason:
                continue

            orphan_reasons[reason] += 1
            # 强制保留 / 探究课统一使用 other-<course_id>，避免与正式树节点 id 冲突
            if reason in ('forced_other', 'inquiry_project'):
                vid = f'other-{cid}'
            else:
                vid = nid if nid else f'other-{cid}'
            virtual_nodes.append({
                'id': vid,
                'name': name,
                'name_en': manifest.get('title_en', ''),
                'grade': grade if isinstance(grade, int) else 0,
                'subject': subject,
                'prerequisites': [],
                'extends': [],
                'parallel': [],
                'courses': [cid],
                'status': 'active',
                'source': f'user-generated({reason})',
                'curriculum_points': [manifest.get('description_zh', '') or manifest.get('description', '')],
                'excerpt_ids': []
            })

        # v7.9.7 新增：扫描 ext-* 学习路径推荐课件（无 manifest，元信息在 HTML meta 里）
        # 质检门槛：
        #   (a) course-id 以 ext- 开头
        #   (b) HTML ≥ 10 KB（避免空壳占位）
        #   (c) HTML 含 <meta name="course-subject"> 和 <meta name="course-title">
        #   (d) HTML 含 ≥ 5 个 <section>（保证有教学结构）
        META_RE = re.compile(r'<meta\s+name="(course-[^"]+)"\s+content="([^"]*)"', re.I)
        SECTION_RE = re.compile(r'<section[^>]*>', re.I)
        EXT_MIN_SIZE = 10_240      # 10 KB
        EXT_MIN_SECTIONS = 5

        ext_dirs_scanned = 0
        for base_dir in ('examples', 'community'):
            base = Path(base_dir)
            if not base.exists():
                continue
            for d in sorted(base.iterdir()):
                if not d.is_dir() or not d.name.startswith('ext-'):
                    continue
                # 已经被 courses 收录（有 manifest）的跳过（已在上一段处理）
                if d.name in courses:
                    continue
                index_path = d / 'index.html'
                if not index_path.exists():
                    continue
                ext_dirs_scanned += 1
                try:
                    html = index_path.read_text(encoding='utf-8', errors='replace')
                except OSError:
                    continue

                # 质检项 (b)(c)(d)
                size = len(html.encode('utf-8'))
                metas = dict(META_RE.findall(html))
                section_count = len(SECTION_RE.findall(html))

                reasons_reject = []
                if size < EXT_MIN_SIZE:
                    reasons_reject.append(f'size<{EXT_MIN_SIZE}({size})')
                if 'course-subject' not in metas or not metas.get('course-subject'):
                    reasons_reject.append('no course-subject')
                if 'course-title' not in metas or not metas.get('course-title'):
                    reasons_reject.append('no course-title')
                if section_count < EXT_MIN_SECTIONS:
                    reasons_reject.append(f'sections<{EXT_MIN_SECTIONS}({section_count})')

                if reasons_reject:
                    orphan_reasons['ext_rejected'] += 1
                    print(f'  ⚠️ ext 课件未通过质检，跳过: {d.name} ({", ".join(reasons_reject)})')
                    continue

                # 通过质检：纳入虚拟树
                orphan_reasons['ext_passed'] += 1
                ext_subject = metas.get('course-subject', 'other')
                ext_title = metas.get('course-title', d.name)
                ext_node = metas.get('course-node', d.name)
                # 虚拟节点 id：优先用 course-node（无学科前缀），否则用目录名
                ext_vid = ext_node if ext_node and ext_node not in all_official_node_ids else f'other-{d.name}'
                virtual_nodes.append({
                    'id': ext_vid,
                    'name': ext_title,
                    'name_en': '',
                    'grade': 0,
                    'subject': ext_subject,
                    'prerequisites': [],
                    'extends': [],
                    'parallel': [],
                    'courses': [d.name],
                    'status': 'active',
                    'source': 'learning-path-ext',
                    'curriculum_points': [f'学习路径推荐课件（ext-* 前缀，无 manifest.json，元信息来自 HTML meta）'],
                    'excerpt_ids': []
                })
                # 同时把课件加入 courses 集合，供步骤 4 写入 registry
                # 构造一个最小 manifest 供下游消费
                synthetic_manifest = {
                    'id': d.name,
                    'name': ext_title,
                    'title': ext_title,
                    'subject': ext_subject,
                    'node_id': ext_node or '',
                    'grade': 0,
                    'author': 'learning-path',
                    'free_mode': True,  # 标记为 free_mode，让下游一致处理
                    '_synthetic_from_ext_html': True
                }
                courses[d.name] = (synthetic_manifest, base_dir)

        # 按 subject 聚合去重（同一 virtual id 可能对应多个 cid）
        merged = {}
        for n in virtual_nodes:
            if n['id'] in merged:
                merged[n['id']]['courses'].extend(n['courses'])
                merged[n['id']]['courses'] = sorted(set(merged[n['id']]['courses']))
            else:
                merged[n['id']] = n
        virtual_nodes = sorted(merged.values(), key=lambda x: (x.get('subject', ''), x['id']))

        # 回写虚拟树
        virtual_tree = json.loads(virtual_tree_path.read_text(encoding='utf-8'))
        virtual_tree['domains'][0]['nodes'] = virtual_nodes
        virtual_tree_path.write_text(
            json.dumps(virtual_tree, ensure_ascii=False, indent=2) + '\n',
            encoding='utf-8'
        )
        print(f'  ✅ 已填充 {len(virtual_nodes)} 个虚拟节点到 {virtual_tree_path}')
        print(f'     free_mode: {orphan_reasons["free_mode"]}, '
              f'node 未找到: {orphan_reasons["node_not_found"]}, '
              f'缺 node_id: {orphan_reasons["missing_node_id"]}, '
              f'强制保留: {orphan_reasons["forced_other"]}, '
              f'探究课: {orphan_reasons["inquiry_project"]}')
        if ext_dirs_scanned:
            print(f'     ext-* 学习路径课件: 扫描 {ext_dirs_scanned} 个，'
                  f'质检通过 {orphan_reasons["ext_passed"]}，'
                  f'拒绝 {orphan_reasons["ext_rejected"]}')
    else:
        print(f'  ⏭️ {virtual_tree_path} 不存在，跳过（可用 git pull 拉取）')

    # 4. 重建注册表
    print('\n📋 步骤4: 重建注册表...')
    # 注：old_registry 和 legacy_preserved 已在步骤 2 加载，此处复用
    
    registry_courses = []
    official_count = 0
    community_count = 0
    course_count = 0
    for course_id, (manifest, src_dir) in sorted(courses.items()):
        # 保留旧注册表中的 status（official/community/course），默认 community
        # ⭐ v5.34.8 防污染：新增课件（旧 registry 中没有）默认一律为 community，
        #    严禁仅凭位于 examples/ 目录就自动打成 official —— 这是导致用户生成
        #    课件污染官方 Gallery 的历史漏洞。升级为 official 必须管理员手工改
        #    registry.json 并提交 commit。
        old_entry = old_registry.get(course_id, {})
        if old_entry:
            status = old_entry.get('status', 'community')
        else:
            status = 'community'
            print(f'  🆕 {course_id}: 新课件，默认 status=community（升级 official 请手工编辑 registry.json）')
        # 若 manifest 指明 category=course 也视为多章节课程
        if manifest.get('category') == 'course' and status not in ('official',):
            status = 'course'
        
        # v6.2: name 字段回退：优先 name，次选 title_zh / title（兼容旧 manifest）
        course_name = manifest.get('name', '') or manifest.get('title_zh', '') or manifest.get('title', '')
        course_name_en = manifest.get('name_en', '') or manifest.get('title', '')
        # 避免 name_en 和 name 完全相同（发生在旧 manifest 只有 title 字段时）
        if course_name_en == course_name:
            course_name_en = ''
        # v6.2: description_zh 智能回退：如果 description_zh 为空但 description 含中文，则复用
        desc_zh = manifest.get('description_zh', '')
        desc = manifest.get('description', '')
        if not desc_zh and desc and any('\u4e00' <= ch <= '\u9fff' for ch in desc):
            desc_zh = desc
        # v6.3: teachany_version 三级回退：
        #   1. manifest.teachany_version（显式声明）
        #   2. manifest.version（多数 manifest 用这个字段）
        #   3. index.html <meta name="teachany-version">（最后兜底）
        course_path = Path(src_dir) / course_id
        ta_version = (
            manifest.get('teachany_version', '')
            or manifest.get('version', '')
            or extract_teachany_version_from_html(course_path)
        )
        # v6.3: 统一图片发现 — 先查 image-registry.json，再查本地 assets/
        node_id = manifest.get('node_id', '')
        m_subject = manifest.get('subject', '')

        # 1. 查 image-registry.json（CDN 预制图）
        cdn_hero_url, cdn_hero_file = resolve_image_from_registry(node_id, 'hero', m_subject)
        cdn_scene_url, cdn_scene_file = resolve_image_from_registry(node_id, 'scene', m_subject)

        # 2. 查本地 assets/（与 v6.2 兼容）
        local_hero, local_scene = detect_images(course_path)

        # 3. 合并：CDN 优先，本地兜底
        hero_image = local_hero or (f"cdn:{cdn_hero_url}" if cdn_hero_url else '')
        scene_image = local_scene or (f"cdn:{cdn_scene_url}" if cdn_scene_url else '')

        entry = {
            'id': course_id,
            'name': course_name,
            'name_en': course_name_en,
            'subject': manifest.get('subject', ''),
            'grade': manifest.get('grade', 0),
            'node_id': manifest.get('node_id', ''),
            'domain': manifest.get('domain', ''),
            'description': manifest.get('description', ''),
            'description_zh': desc_zh,
            'emoji': manifest.get('emoji', '📚'),
            'tags': manifest.get('tags', []),
            'difficulty': manifest.get('difficulty', 1),
            'duration': manifest.get('duration', ''),
            'lines': manifest.get('lines', ''),
            'created': manifest.get('created', ''),
            'version': manifest.get('version', '1.0'),
            'license': manifest.get('license', 'MIT'),
            'status': status,
            # ⭐ v6.1: path 根据课件实际目录生成（examples/xxx 或 community/xxx）
            'path': f'{src_dir}/{course_id}',
            'has_tts': manifest.get('has_tts', False),
            'has_video': manifest.get('has_video', False),
            'has_en': manifest.get('has_en', False),
            'author': manifest.get('author', ''),
            'teachany_version': ta_version,
            'curriculum': manifest.get('curriculum', 'cn-national'),
            # ⭐ v6.2: 图片资产字段（自动检测）
            'hero_image': hero_image,
            'scene_image': scene_image,
            # ⭐ v7.0: 多版本课件支持
            'variant': manifest.get('variant', ''),  # 版本标识（如"基础版"、"进阶版"）
            'overridden': course_id in overridden_courses,  # 是否被同作者更高版本覆盖
        }
        registry_courses.append(entry)
        if status == 'official':
            official_count += 1
        elif status == 'course':
            course_count += 1
        else:
            community_count += 1

    # v6.1: 把遗留课件（无 manifest 但 index.html 存在）追加进 registry
    legacy_count = 0
    for cid, old_entry in legacy_preserved:
        registry_courses.append(old_entry)
        legacy_count += 1
        st = old_entry.get('status', 'community')
        if st == 'official':
            official_count += 1
        elif st == 'course':
            course_count += 1
        else:
            community_count += 1
    if legacy_count:
        print(f'   ➕ 遗留课件已并入 registry: {legacy_count}')

    registry = {
        'version': '1.0',
        'total': len(registry_courses),
        'updated': '2026-04-17',
        'courses': registry_courses
    }

    with open('registry.json', 'w', encoding='utf-8') as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)

    print(f'   注册表已重建: {len(registry_courses)} 个课件 (官方={official_count}, 社区={community_count}, 课程={course_count})')

    # v7.7: 同步派生索引，解决"社区课件已进 registry 但 Gallery/知识图谱不显示"的断链问题
    # v7.9.9: 新增 build-nodes-selector.py —— 修复 path.html 学习路径选择器的断链
    # v7.9.10: 新增 build-nodes-metadata.py —— 修复 path.html 知识图谱网络加载（TeachAnyLearningPath.initialize 依赖）
    print('\n🔄 步骤4.5: 同步社区索引和标准知识图谱索引...')
    for helper in [
        'sync-community-index.py',
        'build-teachany-kg-manifest.py',
        'build-nodes-selector.py',
        'build-nodes-metadata.py',
    ]:
        helper_path = Path('scripts') / helper
        if not helper_path.exists():
            print(f'  ⚠️  跳过 {helper}: 文件不存在')
            continue
        result = subprocess.run([sys.executable, str(helper_path)], text=True, capture_output=True)
        if result.returncode != 0:
            print(f'  ❌ {helper} 执行失败')
            if result.stdout.strip(): print(result.stdout.strip())
            if result.stderr.strip(): print(result.stderr.strip())
            raise SystemExit(result.returncode)
        first_line = (result.stdout.strip().splitlines() or ['完成'])[0]
        print(f'  ✅ {helper}: {first_line}')

    # 5. 最终验证
    print('\n' + '='*70)
    print('📊 最终验证')
    print('='*70)

    # 重新扫描（递归覆盖 international/ 子目录）
    tree_courses = set()
    for tf in Path('data/trees').rglob('*.json'):
        td = load_tree(tf)
        def collect(n):
            if 'courses' in n and n['courses']:
                tree_courses.update(n['courses'])
            for k in ['children', 'nodes', 'domains']:
                if k in n:
                    for c in n[k]:
                        collect(c)
        collect(td)

    reg_set = set(c['id'] for c in registry_courses)
    # v6.1: "文件存在"含 legacy（有 index.html 但缺 manifest）
    file_set = set(courses.keys()) | legacy_ids

    print(f'\n  文件存在:   {len(file_set)}')
    print(f'  已注册:     {len(reg_set)}')
    print(f'  树引用:     {len(tree_courses)}')

    # 不一致检查
    tree_not_exist = tree_courses - file_set
    if tree_not_exist:
        print(f'\n  ❌ 知识树引用但文件不存在: {len(tree_not_exist)}')
        for x in sorted(tree_not_exist):
            print(f'     - {x}')
    else:
        print(f'\n  ✅ 知识树引用全部有效')

    reg_not_exist = reg_set - file_set
    if reg_not_exist:
        print(f'  ❌ 注册表但文件不存在: {len(reg_not_exist)}')
    else:
        print(f'  ✅ 注册表全部有效')

    file_not_in_tree = file_set - tree_courses
    if file_not_in_tree:
        print(f'  ⚠️  文件存在但知识树未引用: {len(file_not_in_tree)}')
        for x in sorted(file_not_in_tree):
            print(f'     - {x}')
    else:
        print(f'  ✅ 所有课件都被知识树引用')

    print(f'\n  三者完全一致: {len(file_set & reg_set & tree_courses)}')

    # 6. Hero 图基线校验（v7.9：发布流程强制）
    print('\n🖼️ 步骤6: Hero 图基线校验（hero 文件存在 + HTML 真实引用）...')
    check_hero_path = Path('scripts') / 'check-hero.py'
    if check_hero_path.exists():
        # 只校验 official 课件（examples/），社区课件历史遗留太多，单独治理
        examples_dir = Path('examples')
        hero_fail = []
        if examples_dir.exists():
            import sys as _sys
            for d in sorted(examples_dir.iterdir()):
                if not d.is_dir() or not (d / 'index.html').exists():
                    continue
                result = subprocess.run(
                    [_sys.executable, str(check_hero_path), str(d)],
                    text=True, capture_output=True
                )
                if result.returncode != 0:
                    hero_fail.append(d.name)
        if hero_fail:
            print(f'  ❌ {len(hero_fail)} 个官方课件 hero 校验失败:')
            for name in hero_fail[:10]:
                print(f'     - examples/{name}')
            print(f'  → 运行 python3 scripts/check-hero.py examples/<name> 查看详情')
            # 非阻断：只告警不退出，避免小问题阻塞整个索引重建
        else:
            print(f'  ✅ 所有官方课件 hero 校验通过')
    else:
        print('  ⚠️  scripts/check-hero.py 不存在，跳过 hero 校验')

    print('\n✅ 重建完成！')


if __name__ == '__main__':
    main()
