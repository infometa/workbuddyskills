#!/usr/bin/env python3
"""
WorkRally 画布整理工具（MCP 版 · 纯本地计算）
------------------------------------------------

本脚本**不发起任何网络请求**、**不需要 workrally CLI / API Key**。
它只做本地计算：读素材 JSON → 分类 → 生成画板/网格节点 JSON。

与 MCP 工具的分工：
    Agent 侧（MCP）                        本脚本（本地）
    ─────────────────────────────────      ─────────────────────────────
    1. asset_search(canvas_project_id=[<id>], channel=["toolbox_canvas"],
                    page_size=100, page=<n>) ──► 落盘 assets.json
    2.                                     organize_canvas.py --assets assets.json
                                           --rules rules.json --emit-args build_args.json
    3. canvas_manage(action="build_draft", canvas_id=<id>,
                      nodes=<build_args.json 里的 nodes>, mode="merge")

用法:
    organize_canvas.py --canvas-id <id> --assets assets.json
                       [--rules rules.json] [--captions]
                       [--output canvas_nodes.json]
                       [--emit-args build_args.json]

⚠️ 加 --emit-args 会额外输出一份「可直接喂给 canvas_manage(build_draft) 的完整参数」：
   {"canvas_id": "<id>", "mode": "merge", "nodes": [...]}
   Agent 读它、把 nodes 原样传给 MCP 即可。**永远用 mode="merge"**（不删除任何现有节点）。

规则文件格式（JSON）:
    {
      "groups": [
        {
          "id": "board_roles",
          "title": "🎭 人物资产",
          "cols": 4,
          "match": { "type": "title_keywords", "keywords": ["韩团风", "清凉造型"] }
        },
        {
          "id": "board_deakins",
          "title": "🎬 迪金斯风格",
          "cols": 5,
          "match": { "type": "title_prefix", "prefix": "迪金斯" }
        },
        {
          "id": "board_videos",
          "title": "🎥 视频库",
          "cols": 3,
          "match": { "type": "asset_type", "value": "video" }
        },
        {
          "id": "board_misc",
          "title": "📦 杂项",
          "cols": 6,
          "match": { "type": "fallback" }
        }
      ],
      "layout": {
        "cell_w": 280, "cell_h": 280,
        "gap": 20, "pad": 40, "title_h": 60,
        "board_gap": 200
      }
    }
"""
import argparse
import json
import re
from pathlib import Path


# -------- 规则匹配 --------
def match_asset(asset: dict, rule: dict) -> bool:
    """判断 asset 是否匹配某条规则"""
    title = asset.get('title') or ''
    atype = asset.get('type') or ''
    m = rule.get('match', {})
    mtype = m.get('type')

    if mtype == 'fallback':
        return True  # 兜底规则，应放在最后
    if mtype == 'asset_type':
        return atype == m.get('value')
    if mtype == 'title_prefix':
        prefixes = m.get('prefix') if isinstance(m.get('prefix'), list) else [m.get('prefix')]
        return any(title.startswith(p) for p in prefixes if p)
    if mtype == 'title_keywords':
        kws = m.get('keywords') or []
        return any(k in title for k in kws)
    if mtype == 'title_regex':
        return bool(re.search(m.get('regex', ''), title))
    if mtype == 'and':
        return all(match_asset(asset, {'match': sub}) for sub in m.get('conditions', []))
    if mtype == 'or':
        return any(match_asset(asset, {'match': sub}) for sub in m.get('conditions', []))
    return False


def classify(assets: list, groups: list) -> dict:
    """按 groups 顺序将 assets 分组。每个 asset 只归入第一个匹配的组。"""
    buckets = {g['id']: [] for g in groups}
    for a in assets:
        for g in groups:
            if match_asset(a, g):
                buckets[g['id']].append(a)
                break
    return buckets


# -------- 素材字段归一 --------
def normalize_asset(a: dict) -> dict:
    """把 MCP asset_search 返回的一条素材归一成脚本内部结构。

    MCP（与 CLI 同源）返回的关键字段：id / type / title。
    为兼容不同版本，额外接受 asset_id / asset_type / name。
    """
    return {
        'id': str(a.get('id') or a.get('asset_id') or a.get('source_id') or ''),
        'type': a.get('type') or a.get('asset_type') or 'image',
        'title': a.get('title') or a.get('name') or '',
    }


def load_assets(path: str) -> list:
    """读 Agent 落盘的 asset_search 返回（支持数组或 {assets|data|list: [...]}）。"""
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, list):
        raw = data
    else:
        raw = data.get('assets') or data.get('data') or data.get('list') or []
    out = []
    for a in raw:
        n = normalize_asset(a)
        if n['id']:
            out.append(n)
    return out


# -------- 布局生成 --------
def build_nodes(groups: list, buckets: dict, layout: dict,
                show_captions: bool = False) -> list:
    """生成画板 + 网格布局节点列表。

    当 show_captions=True（或组级别 show_captions=True）时，会为每个素材
    额外生成一个 caption text 节点显示素材标题。

    ⚠️ text 节点不能作为 artboard 子节点，caption 使用绝对坐标放置。
    """
    cw = layout.get('cell_w', 280)
    ch = layout.get('cell_h', 280)
    gap = layout.get('gap', 20)
    pad = layout.get('pad', 40)
    title_h = layout.get('title_h', 60)
    board_gap = layout.get('board_gap', 200)
    # caption 相关参数
    caption_h = layout.get('caption_h', 28)
    caption_font_size = layout.get('caption_font_size', 14)
    caption_color = layout.get('caption_color', '#cccccc')
    caption_max_len = layout.get('caption_max_len', 20)

    all_nodes = []
    x_cur = 0
    for g in groups:
        items = buckets.get(g['id'], [])
        if not items:
            continue  # 空组跳过

        # 每个组可以单独控制 caption 显示
        group_captions = g.get('show_captions', show_captions)
        eff_caption_h = caption_h if group_captions else 0

        cols = max(1, g.get('cols', 5))
        rows = (len(items) + cols - 1) // cols
        row_h = ch + eff_caption_h  # 单行高度 = 素材高度 + caption 区域
        board_w = pad * 2 + cols * cw + (cols - 1) * gap
        board_h = pad * 2 + title_h + rows * row_h + (rows - 1) * gap

        # 画板
        all_nodes.append({
            'id': g['id'],
            'type': 'artboard',
            'position': {'x': x_cur, 'y': 0},
            'data': {},
            'style': {'width': board_w, 'height': board_h},
        })
        # 画板标题（独立 text 节点，放在画板外部上方）
        all_nodes.append({
            'id': f"{g['id']}_title",
            'type': 'text',
            'position': {'x': x_cur + pad, 'y': -80},
            'data': {
                'text': {
                    'content': g.get('title', g['id']),
                    'fontSize': g.get('title_size', 40),
                    'fontWeight': g.get('title_weight', 700),
                    'color': g.get('title_color', '#ffffff'),
                }
            },
            'style': {'width': 600},
        })
        # 子节点 + caption
        for i, a in enumerate(items):
            row_idx, col_idx = divmod(i, cols)
            # 相对画板的坐标（子节点有 parentId）
            rel_x = pad + col_idx * (cw + gap)
            rel_y = pad + title_h + row_idx * (row_h + gap)
            all_nodes.append({
                'id': f"node_{a['id']}",
                'type': a['type'],
                'position': {'x': rel_x, 'y': rel_y},
                'data': {'asset': {'id': a['id']}},
                'style': {'width': cw, 'height': ch},
                'parentId': g['id'],
            })
            # caption 文字节点（绝对坐标，不是 artboard 子节点）
            if group_captions:
                raw_title = (a.get('title') or '').strip()
                if raw_title:
                    # 截断过长标题
                    if len(raw_title) > caption_max_len:
                        caption_text = raw_title[:caption_max_len - 1] + '\u2026'
                    else:
                        caption_text = raw_title
                    # 绝对坐标 = 画板坐标 + 相对坐标 + 偏移
                    abs_x = x_cur + rel_x
                    abs_y = 0 + rel_y + ch + 2  # 素材下方 2px
                    all_nodes.append({
                        'id': f"cap_{a['id']}",
                        'type': 'text',
                        'position': {'x': abs_x, 'y': abs_y},
                        'data': {
                            'text': {
                                'content': caption_text,
                                'fontSize': caption_font_size,
                                'fontWeight': 400,
                                'color': caption_color,
                            }
                        },
                        'style': {'width': cw},
                    })
        x_cur += board_w + board_gap
    return all_nodes


# -------- 主流程 --------
def parse_canvas_id(arg: str) -> str:
    """支持直接 ID 或完整 URL。"""
    m = re.search(r'/canvas/([a-z0-9]+)', arg)
    return m.group(1) if m else arg.strip()


DEFAULT_RULES = {
    "groups": [
        {"id": "board_videos", "title": "🎥 视频库", "cols": 3,
         "match": {"type": "asset_type", "value": "video"}},
        {"id": "board_misc", "title": "📦 杂项 / 散图", "cols": 6,
         "match": {"type": "fallback"}},
    ],
    "layout": {
        "cell_w": 280, "cell_h": 280, "gap": 20,
        "pad": 40, "title_h": 60, "board_gap": 200,
    },
}


def main():
    ap = argparse.ArgumentParser(description='WorkRally 画布整理工具（MCP 版）')
    ap.add_argument('--canvas-id', required=True,
                    help='画布 ID 或画布 URL（/toolbox/canvas/<id>）')
    ap.add_argument('--assets', required=True,
                    help='Agent 用 MCP asset_search 拉取并落盘的素材 JSON 路径')
    ap.add_argument('--rules', help='规则 JSON 文件路径（不给则使用默认：按视频/其他二分）')
    ap.add_argument('--output', default='/tmp/workrally/canvas_nodes.json',
                    help='生成的节点 JSON 输出路径')
    ap.add_argument('--emit-args', dest='emit_args',
                    help='额外输出一份 canvas_manage(build_draft) 的完整参数 JSON')
    ap.add_argument('--captions', action='store_true',
                    help='为每个素材生成标题文字节点（caption）')
    args = ap.parse_args()

    canvas_id = parse_canvas_id(args.canvas_id)
    print(f'[1/4] canvas_id = {canvas_id}')

    # 加载规则
    if args.rules:
        with open(args.rules, encoding='utf-8') as f:
            cfg = json.load(f)
    else:
        cfg = DEFAULT_RULES
    groups = cfg['groups']
    layout = cfg.get('layout', DEFAULT_RULES['layout'])

    # 读素材（由 Agent 的 MCP asset_search 落盘）
    print(f'[2/4] 读取素材: {args.assets}')
    assets = load_assets(args.assets)
    print(f'      共 {len(assets)} 个 asset')
    if not assets:
        print('      ⚠️ 素材为空。请先确认 Agent 已调用：')
        print('         asset_search(canvas_project_id=["%s"], channel=["toolbox_canvas"], page_size=100)' % canvas_id)
        print('         并把返回原样写入该文件。')
        return

    # 分类
    buckets = classify(assets, groups)
    print('[3/4] 分类结果:')
    for g in groups:
        print(f"      - {g.get('title', g['id']):20s} ({g['id']}): {len(buckets[g['id']])}")

    # 全局 caption 开关：命令行 --captions 或 rules.json 中 show_captions
    global_captions = args.captions or cfg.get('show_captions', False)

    # 生成节点
    nodes = build_nodes(groups, buckets, layout, show_captions=global_captions)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(nodes, f, ensure_ascii=False, indent=2)
    print(f'      共生成 {len(nodes)} 个节点 → {args.output}')

    if args.emit_args:
        payload = {
            'canvas_id': canvas_id,
            'mode': 'merge',
            'nodes': nodes,
        }
        Path(args.emit_args).parent.mkdir(parents=True, exist_ok=True)
        with open(args.emit_args, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f'      build_draft 参数 → {args.emit_args}')

    print()
    print('[4/4] 下一步（由 Agent 通过 MCP 执行，无需 CLI）：')
    print('      canvas_manage(action="build_draft", canvas_id="%s",' % canvas_id)
    print('                    nodes=<上面生成的 nodes 数组>, mode="merge")')
    print('      🛡️ 安全模式：merge 只新增/更新，不会删除任何已有节点（文字/画笔/素材均保留）')
    print('      ✅ 完成。画布: https://workrally.qq.com/toolbox/canvas/%s' % canvas_id)


if __name__ == '__main__':
    main()
