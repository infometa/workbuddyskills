#!/usr/bin/env python3
"""
find_nodes.py · v6.6

【功能 1】列出某学段+学科的所有候选节点（让 AI 选）
【功能 2】用关键词模糊匹配最佳节点
【功能 3】发现学科树本身缺失，提示是否需要新建

用法：
  # 列某学段+学科的所有节点
  python3 find_nodes.py --stage elementary --subject chinese
  python3 find_nodes.py --stage middle --subject math
  python3 find_nodes.py --stage high --subject info-tech

  # 关键词模糊匹配（推荐 AI 用这个）
  python3 find_nodes.py --stage elementary --subject science --keyword "电路"
  python3 find_nodes.py --stage middle --subject history --keyword "二战"

  # 列所有有树的 (stage, subject) 组合
  python3 find_nodes.py --list-trees

  # 输出 JSON 给 AI 程序解析
  python3 find_nodes.py --stage middle --subject math --keyword "函数" --json

输出：节点 id + 中文名 + 年级 + 所在 domain，按相关性排序
退出码：
  0  找到节点
  1  学科有树但没匹配的节点（建议用 register_node.py 新建）
  2  学段+学科组合无树（标注为 free_mode 或先建树）
  3  参数错误
"""
import json, sys, argparse, re, difflib
from pathlib import Path

CURRICULUM_ALIASES = {
    'cn': 'cn', 'china': 'cn', 'cn-national': 'cn',
    'us': 'us', 'usa': 'us', 'us-ccss': 'us',
    'international': 'international', 'ib': 'international',
}

SUBJECT_ALIASES = {
    'tech': 'info-tech', 'it': 'info-tech', 'computer': 'info-tech',
    'information-technology': 'info-tech',
    '语文': 'chinese', '数学': 'math', '英语': 'english',
    '物理': 'physics', '化学': 'chemistry', '生物': 'biology',
    '历史': 'history', '地理': 'geography', '科学': 'science',
    '信息技术': 'info-tech', '信息': 'info-tech', '编程': 'info-tech',
    '政治': 'politics',
}

STAGE_ALIASES = {
    '小学': 'elementary', 'primary': 'elementary',
    '初中': 'middle', 'junior': 'middle',
    '高中': 'high', 'senior': 'high',
}


def find_repo() -> Path:
    for c in [
        Path.home() / 'CodeBuddy' / '一次函数' / 'teachany-opensource',
        Path.home() / 'teachany-opensource',
        Path.home() / 'CodeBuddy' / 'teachany-opensource',
    ]:
        if (c / 'data' / 'trees').exists():
            return c
    return None


def normalize(s: str, mapping: dict) -> str:
    if not s:
        return ''
    s = s.strip().lower()
    return mapping.get(s, s)


def list_all_trees(repo: Path):
    """返回所有 (curriculum, stage, subject, file)"""
    out = []
    for f in (repo / 'data' / 'trees').rglob('*.json'):
        try:
            t = json.load(open(f, encoding='utf-8'))
            if not isinstance(t, dict) or 'domains' not in t:
                continue
            parts = f.relative_to(repo / 'data' / 'trees').parts
            if len(parts) >= 3:
                curr, stg, name = parts[0], parts[1], parts[-1].replace('.json', '')
                node_count = sum(len(d.get('nodes', [])) for d in t.get('domains', []))
                out.append({
                    'curriculum': curr, 'stage': stg, 'subject': name,
                    'file': str(f.relative_to(repo)), 'nodes': node_count,
                    'subject_zh': t.get('name', name),
                })
        except: pass
    return out


def load_tree(repo: Path, curriculum: str, stage: str, subject: str):
    p = repo / 'data' / 'trees' / curriculum / stage / f'{subject}.json'
    if not p.exists():
        return None, None
    return json.load(open(p, encoding='utf-8')), p


def score_node(node: dict, domain: dict, keyword: str) -> float:
    """对节点和关键词做相似度评分"""
    nid = node.get('id', '').lower()
    name = node.get('name', '').lower()
    name_en = node.get('name_en', '').lower()
    desc = (node.get('description') or '').lower()
    dom_id = (domain.get('id') or '').lower()
    dom_name = (domain.get('name') or '').lower()
    kw = keyword.lower()

    # 直接子串匹配高分
    score = 0
    if kw in nid: score += 100
    if kw in name: score += 80
    if kw in name_en: score += 60
    if kw in desc: score += 30
    if kw in dom_id or kw in dom_name: score += 20

    # difflib 模糊度（兜底）
    score += difflib.SequenceMatcher(None, kw, nid).ratio() * 20
    score += difflib.SequenceMatcher(None, kw, name).ratio() * 15

    return score


def main():
    ap = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                 description=__doc__)
    ap.add_argument('--stage', help='elementary/middle/high 或 小学/初中/高中')
    ap.add_argument('--subject', help='学科 id 或中文（math/chinese/info-tech/...）')
    ap.add_argument('--curriculum', default='cn', help='cn/us/international，默认 cn')
    ap.add_argument('--keyword', help='关键词模糊匹配（推荐！）')
    ap.add_argument('--limit', type=int, default=15, help='返回多少候选（默认 15）')
    ap.add_argument('--list-trees', action='store_true', help='列所有学科树')
    ap.add_argument('--json', action='store_true', help='输出 JSON 供程序解析')
    args = ap.parse_args()

    repo = find_repo()
    if not repo:
        print("❌ 未找到 teachany-opensource 仓库", file=sys.stderr)
        sys.exit(3)

    # --list-trees 模式
    if args.list_trees:
        trees = list_all_trees(repo)
        if args.json:
            print(json.dumps(trees, ensure_ascii=False, indent=2))
        else:
            print(f"📚 全部学科树（{len(trees)} 个）：")
            print()
            cur_stage = ''
            for t in sorted(trees, key=lambda x: (x['curriculum'], x['stage'], x['subject'])):
                stage_key = f"{t['curriculum']}/{t['stage']}"
                if stage_key != cur_stage:
                    print(f"\n── {stage_key} ──")
                    cur_stage = stage_key
                print(f"  {t['subject']:15s} ({t['nodes']:3d} 节点)  {t['subject_zh']}")
        return

    # 正常模式：必须有 stage + subject
    if not args.stage or not args.subject:
        ap.print_help()
        sys.exit(3)

    curriculum = normalize(args.curriculum, CURRICULUM_ALIASES)
    stage = normalize(args.stage, STAGE_ALIASES)
    subject = normalize(args.subject, SUBJECT_ALIASES)

    tree, tree_path = load_tree(repo, curriculum, stage, subject)
    if not tree:
        # 学科树不存在
        result = {
            'status': 'tree_not_found',
            'curriculum': curriculum, 'stage': stage, 'subject': subject,
            'expected_path': f'data/trees/{curriculum}/{stage}/{subject}.json',
            'message': f'{curriculum}/{stage}/{subject} 学科树不存在',
            'suggestion': '此学科可建议用户：(A) 用 free_mode 自由模式（不挂树）  (B) 联系管理员新建树',
            'available_trees': [t['subject'] for t in list_all_trees(repo)
                                if t['curriculum'] == curriculum and t['stage'] == stage],
        }
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"⚠️  {curriculum}/{stage}/{subject} 学科树不存在")
            print(f"   期望路径: {result['expected_path']}")
            print()
            print(f"   该学段已有学科:")
            for s in result['available_trees']:
                print(f"     {s}")
            print()
            print(f"💡 两种处理方式:")
        print(f"   A) 自由模式（推荐）：课件无需挂树，manifest 加 \"free_mode\": true")
        print(f"      v7.9.6 起：free_mode 课件会自动出现在知识树的 ✨「其他知识 Other Knowledge」入口")
        print(f"      同时也出现在 Gallery（按学科分类）")
        print(f"   B) 先建树：联系管理员新建 {result['expected_path']}")
        sys.exit(2)

    # 收集所有节点
    all_nodes = []
    for d in tree.get('domains', []):
        for n in d.get('nodes', []):
            all_nodes.append({'node': n, 'domain': d})

    # 排序：keyword 模式按相似度，否则按 grade
    if args.keyword:
        scored = [(score_node(x['node'], x['domain'], args.keyword), x) for x in all_nodes]
        scored.sort(key=lambda t: -t[0])
        results = [x for s, x in scored if s > 5][:args.limit]
        if not results:
            results = [x for s, x in scored[:args.limit]]
    else:
        all_nodes.sort(key=lambda x: (x['node'].get('grade', 0), x['domain'].get('id', ''), x['node'].get('id', '')))
        results = all_nodes[:args.limit]

    # 输出
    if args.json:
        out = {
            'status': 'ok',
            'curriculum': curriculum, 'stage': stage, 'subject': subject,
            'tree_file': str(tree_path.relative_to(repo)),
            'tree_subject_zh': tree.get('name', subject),
            'total_nodes': len(all_nodes),
            'returned': len(results),
            'keyword': args.keyword or '',
            'candidates': [
                {
                    'node_id': r['node'].get('id'),
                    'name': r['node'].get('name'),
                    'name_en': r['node'].get('name_en', ''),
                    'grade': r['node'].get('grade'),
                    'domain': r['domain'].get('id'),
                    'domain_name': r['domain'].get('name'),
                    'status': r['node'].get('status'),
                    'has_courses': len(r['node'].get('courses', [])) > 0,
                    'description': r['node'].get('description', ''),
                }
                for r in results
            ],
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        tree_zh = tree.get('name', subject)
        print(f"🌳 {tree_zh}（{curriculum}/{stage}/{subject}.json · 共 {len(all_nodes)} 节点）")
        if args.keyword:
            print(f"🔍 关键词: '{args.keyword}'  返回前 {len(results)} 个候选\n")
        else:
            print(f"📋 列出前 {len(results)} 个节点（用 --keyword 精准匹配）\n")
        print(f"  {'node_id':40s} {'grade':5s} {'domain':25s} {'名称'}")
        print(f"  {'-'*40} {'-'*5} {'-'*25} {'-'*30}")
        for r in results:
            n = r['node']
            d = r['domain']
            tag = '✅' if n.get('courses') else ('🆕' if n.get('status') == 'placeholder' else '  ')
            print(f"  {tag} {n.get('id',''):40s} G{n.get('grade','?'):4} {d.get('id',''):25s} {n.get('name','')}")
        print()
        print(f"💡 选好后在课件 HTML 头部加：")
        if results:
            r = results[0]
            print(f'  <meta name="teachany-node" content="{r["node"]["id"]}">')
            print(f'  <meta name="teachany-subject" content="{subject}">')
            print(f'  <meta name="teachany-grade" content="{r["node"].get("grade", 0)}">')
        print()
        print(f"图例: ✅ 已有课件  🆕 placeholder 待课件   (空) 无活跃")
    sys.exit(0)


if __name__ == '__main__':
    main()
