#!/usr/bin/env python3
"""
register_node.py · v6.5

在指定学科树里新增一个 placeholder 节点。
新节点 status=placeholder，一旦有课件（node_id 匹配）上传就会被反向挂载并 status→active。

用法：
  python3 register_node.py --node-id <id> --subject <学科> --stage <学段> \
      [--domain <领域>] [--name <名>] [--grade <年级>]
"""
import json, argparse, sys
from pathlib import Path

def find_repo():
    for c in [
        Path.home() / 'CodeBuddy' / '一次函数' / 'teachany-opensource',
        Path.home() / 'teachany-opensource',
        Path.home() / 'CodeBuddy' / 'teachany-opensource',
    ]:
        if (c / 'data' / 'trees').exists():
            return c
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--node-id', required=True)
    ap.add_argument('--subject', required=True, help='math/chinese/english/physics/history/...')
    ap.add_argument('--stage', required=True, choices=['elementary','middle','high'])
    ap.add_argument('--domain', default='general', help='domain id, default "general"')
    ap.add_argument('--name', default='', help='节点中文名（留空则用 node-id）')
    ap.add_argument('--grade', type=int, default=0, help='年级 1-12（留空则根据学段推定）')
    ap.add_argument('--curriculum', default='cn', choices=['cn','international','international-alt'])
    args = ap.parse_args()

    repo = find_repo()
    if not repo:
        print("❌ 未找到 teachany-opensource", file=sys.stderr)
        sys.exit(2)

    tree_file = repo / 'data' / 'trees' / args.curriculum / args.stage / f'{args.subject}.json'
    if not tree_file.exists():
        print(f"❌ 树文件不存在: {tree_file}", file=sys.stderr)
        print(f"   （可用的学科：{sorted(set(f.stem for f in (repo/'data/trees'/args.curriculum/args.stage).glob('*.json')))}）", file=sys.stderr)
        sys.exit(2)

    with open(tree_file, encoding='utf-8') as f:
        tree = json.load(f)

    # 检查是否已存在
    for d in tree.get('domains', []):
        for n in d.get('nodes', []):
            if n.get('id') == args.node_id:
                print(f"ℹ️  node_id '{args.node_id}' 已在 {d.get('id')} 下存在，无需重复注册")
                sys.exit(0)

    # 推定 grade
    if not args.grade:
        args.grade = {'elementary':3, 'middle':8, 'high':11}[args.stage]

    # 找或建 domain
    domain = next((d for d in tree['domains'] if d.get('id') == args.domain), None)
    if not domain:
        domain = {
            'id': args.domain,
            'name': args.domain.replace('-', ' ').title(),
            'description': f'{args.domain} domain (auto-created)',
            'nodes': []
        }
        tree['domains'].append(domain)
        print(f"✅ 新建 domain: {args.domain}")

    # 新节点
    new_node = {
        'id': args.node_id,
        'name': args.name or args.node_id,
        'grade': args.grade,
        'status': 'placeholder',
        'courses': [],
        'description': f'{args.name or args.node_id}（placeholder，待课件反向挂载）',
    }
    domain['nodes'].append(new_node)

    with open(tree_file, 'w', encoding='utf-8') as f:
        json.dump(tree, f, ensure_ascii=False, indent=2)

    rel = tree_file.relative_to(repo)
    print(f"✅ 节点已注册 → {rel}")
    print(f"   {args.node_id}  [{args.domain}]  {args.name or args.node_id}  G{args.grade}")
    print(f"   status: placeholder（有课件上传后自动 active）")
    print()
    print("🔖 下一步：")
    print("   1. cd", repo)
    print("   2. git add -A && git commit -m 'feat(tree): 注册节点", args.node_id + "'")
    print("   3. git push origin main")
    print("   4. 上传 node_id 匹配的课件，前端自动挂载显示")

if __name__ == '__main__':
    main()
