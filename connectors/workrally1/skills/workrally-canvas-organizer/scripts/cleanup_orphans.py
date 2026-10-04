#!/usr/bin/env python3
"""
WorkRally 画布散落节点清理工具（MCP 版 · 纯本地计算）
------------------------------------------------------

用途：整理画布后，清理那些"散落在外、未归类到任何画板"的旧媒资节点（image/video 孤儿）。

🛡️ 核心铁律：
    - text / freehand 节点**绝不删除**（硬编码排除，不可通过任何参数绕过）
    - artboard / generator 节点**绝不删除**
    - 只删除 type ∈ {image, video} 且 parentId 为空的孤儿节点

本脚本**不发起任何网络请求**、**不需要 workrally CLI / API Key**。
它只做本地计算：解析 draft_v1 → 筛孤儿 → 输出待删 ID 清单与 build_draft 参数。

与 MCP 工具的分工：
    Agent 侧（MCP）                                本脚本（本地）
    ──────────────────────────────────────        ────────────────────────────────
    1. canvas_manage(action="get",
                      canvas_id=<id>) ──────────► 落盘 canvas_snapshot.json
    2.                                            cleanup_orphans.py --canvas canvas_snapshot.json
                                                  [--emit-delete-args del_args.json]
    3. canvas_manage(action="build_draft",
                     canvas_id=<id>,
                     delete_node_ids=<清单>, mode="merge")

用法:
    # Dry-run：列出待删清单 + 输出 build_draft 参数（不删除任何东西）
    cleanup_orphans.py --canvas canvas_snapshot.json

    # 同时输出可直接喂给 MCP 的参数文件
    cleanup_orphans.py --canvas canvas_snapshot.json --emit-delete-args /tmp/workrally/del_args.json

工作原理：
    1. 读 Agent 用 MCP `canvas_manage(action="get")` 落盘的返回（含 draft_v1 base64）
    2. 解析 draft_v1（Y.js update 二进制）扫描所有节点的 id / type / parentId
    3. 筛选 type ∈ {image, video} 且 parentId 为空的节点
    4. 分批（每批 ≤ 80）输出 delete_node_ids，交给 MCP `build_draft` 删除

实战经验：
    - draft_v1 是 Y.js update 格式（非 gzip/msgpack/cbor）
    - 字段编码模式：<name_len><name>\\x01w<varint_len><value>
    - 新整理产生的子节点 id 形如 node_<uuid> 且 parentId=board_*
    - 原散落节点 id 是 UUID (36 字符) 且 parentId 为空
"""
import argparse
import base64
import json
import re
import sys
from pathlib import Path

# ========= 硬编码安全白名单（绝不删除的类型）=========
PROTECTED_TYPES = {'text', 'freehand', 'artboard', 'generator'}
# 只允许删除的类型
DELETABLE_TYPES = {'image', 'video'}


# -------- Y.js draft_v1 字段解码 --------
def read_varint(s: str, pos: int):
    """读取 Y.js/Protobuf 风格的 varint，返回 (value, new_pos)"""
    v, sh = 0, 0
    while True:
        b = ord(s[pos])
        pos += 1
        v |= (b & 0x7f) << sh
        if b < 0x80:
            break
        sh += 7
    return v, pos


def read_field_value(s: str, pos: int):
    """字段值跟在 \\x01w<varint_len> 之后。返回 (value_str, new_pos) 或 (None, pos)。"""
    if pos + 1 >= len(s) or s[pos] != '\x01' or s[pos + 1] != 'w':
        return None, pos
    L, np = read_varint(s, pos + 2)
    if np + L > len(s):
        return None, pos
    return s[np:np + L], np + L


def find_all_fields(s: str, name: str):
    """扫描出所有 `<len><name>\\x01w<len><value>` 模式，返回 [(offset, value), ...]"""
    key_prefix = chr(len(name)) + name
    results = []
    pos = 0
    while True:
        idx = s.find(key_prefix, pos)
        if idx < 0:
            break
        val, new_pos = read_field_value(s, idx + len(key_prefix))
        if val is not None:
            results.append((idx, val))
            pos = new_pos
        else:
            pos = idx + 1
    return results


def parse_draft_v1(draft_v1_b64: str) -> list:
    """
    解析 draft_v1，返回节点列表 [{id, type, parentId}, ...]

    策略：
        1. 分别扫描所有 id / type / parentId 字段出现位置
        2. 按 offset 排序
        3. 以每个 id 字段为"节点起点"，向后聚类最近的 type（和可能的 parentId）
    """
    try:
        raw = base64.b64decode(draft_v1_b64)
    except Exception:
        return []
    # 用 latin-1 按字节读，避免 unicode 解码错误
    s = raw.decode('latin-1')

    id_events = [(off, 'id', v) for off, v in find_all_fields(s, 'id')]
    type_events = [(off, 'type', v) for off, v in find_all_fields(s, 'type')]
    # parentId 字段名实际可能是 parentId 或 parent_id，两种都试
    parent_events = []
    for name in ('parentId', 'parent_id'):
        parent_events += [(off, 'parentId', v) for off, v in find_all_fields(s, name)]

    # 合并按 offset 排序
    events = sorted(id_events + type_events + parent_events, key=lambda x: x[0])

    # 聚类：一个节点 = 从某个 id event 开始，直到遇到下一个 id event 之间的所有字段
    nodes = []
    current = None
    for off, kind, val in events:
        if kind == 'id':
            if current and current.get('id'):
                nodes.append(current)
            current = {'id': val, 'type': None, 'parentId': None}
        elif current is not None:
            if kind == 'type' and current['type'] is None:
                current['type'] = val
            elif kind == 'parentId' and current['parentId'] is None:
                current['parentId'] = val
    if current and current.get('id'):
        nodes.append(current)

    # 去重（同 id 可能被多次记录，保留首次出现的 type/parentId）
    seen = {}
    for n in nodes:
        if n['id'] not in seen:
            seen[n['id']] = n
        else:
            # 合并：保留非空值
            existing = seen[n['id']]
            if not existing['type'] and n['type']:
                existing['type'] = n['type']
            if not existing['parentId'] and n['parentId']:
                existing['parentId'] = n['parentId']
    return list(seen.values())


# -------- 读取 MCP 落盘的画布快照 --------
def load_canvas(path: str) -> dict:
    """读 Agent 用 MCP canvas_manage(action='get') 落盘的返回。"""
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def find_draft_v1(obj):
    """在任意嵌套结构里递归找 draft_v1 字符串字段。"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == 'draft_v1' and isinstance(v, str):
                return v
            got = find_draft_v1(v)
            if got:
                return got
    elif isinstance(obj, list):
        for v in obj:
            got = find_draft_v1(v)
            if got:
                return got
    return None


# -------- 主流程 --------
def parse_canvas_id(arg: str) -> str:
    m = re.search(r'/canvas/([a-z0-9]+)', arg)
    return m.group(1) if m else arg.strip()


def main():
    ap = argparse.ArgumentParser(
        description='WorkRally 画布散落节点清理工具（MCP 版，文字节点强制保留）',
        epilog='🛡️ 核心铁律：text/freehand/artboard/generator 节点永远不会被删除。',
    )
    ap.add_argument('--canvas', required=True,
                    help='Agent 用 MCP canvas_manage(action="get") 落盘的快照 JSON 路径')
    ap.add_argument('--canvas-id',
                    help='画布 ID（用于生成 MCP 调用参数；不给则从快照里尽力推断）')
    ap.add_argument('--batch-size', type=int, default=80, help='每批删除节点数上限（默认 80）')
    ap.add_argument('--output-dir', default='/tmp/workrally',
                    help='中间文件输出目录')
    ap.add_argument('--emit-delete-args', dest='emit_delete_args',
                    help='输出可直接喂给 canvas_manage(build_draft) 的参数 JSON')
    args = ap.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    canvas_id = parse_canvas_id(args.canvas_id) if args.canvas_id else None
    print(f'[1/5] canvas_id = {canvas_id or "(未提供)"}')

    print(f'[2/5] 读取画布快照: {args.canvas}')
    canvas = load_canvas(args.canvas)

    if not canvas_id:
        # 尽力从快照里取
        for k in ('canvas_id', 'id', 'project_id'):
            v = canvas.get(k) if isinstance(canvas, dict) else None
            if isinstance(v, str) and v:
                canvas_id = v
                break
        print(f'      → 推断 canvas_id = {canvas_id or "(失败)"}')

    draft_v1 = find_draft_v1(canvas)
    if not draft_v1:
        print('❌ 快照里未找到 draft_v1 字段，无法解析节点。')
        print('   请确认 Agent 调用的是：canvas_manage(action="get", canvas_id="<id>")，')
        print('   并把完整返回（不经裁剪）原样落盘。')
        sys.exit(1)

    print('[3/5] 解析 draft_v1 ...')
    nodes = parse_draft_v1(draft_v1)
    (out_dir / 'all_nodes.json').write_text(
        json.dumps(nodes, ensure_ascii=False, indent=2), encoding='utf-8'
    )

    # 统计
    type_count = {}
    for n in nodes:
        t = n.get('type') or 'unknown'
        type_count[t] = type_count.get(t, 0) + 1
    print(f'      共解析 {len(nodes)} 个节点')
    print(f'      类型分布: {type_count}')

    # ======== 筛选待删节点（严格白名单）========
    to_delete = []
    protected_count = 0
    for n in nodes:
        nid = n.get('id')
        ntype = n.get('type')
        parent = n.get('parentId')
        if not nid or not ntype:
            continue
        # 🛡️ 硬编码保护：任何受保护类型都跳过
        if ntype in PROTECTED_TYPES:
            protected_count += 1
            continue
        # 只允许删除 image/video
        if ntype not in DELETABLE_TYPES:
            continue
        # 只删孤儿（无 parent 或 parent 为空字符串）
        if parent and parent.strip():
            continue
        to_delete.append(n)

    print('[4/5] 筛选结果：')
    print(f'      🛡️ 受保护节点（text/freehand/artboard/generator）: {protected_count}')
    print(f'      🗑️  散落待删节点（image/video 孤儿）: {len(to_delete)}')

    # 进一步按类型拆分展示
    del_by_type = {}
    for n in to_delete:
        del_by_type[n['type']] = del_by_type.get(n['type'], 0) + 1
    for t, c in sorted(del_by_type.items()):
        print(f'         - {t}: {c}')

    # 保存待删清单
    delete_ids = [n['id'] for n in to_delete]
    (out_dir / 'delete_ids.json').write_text(
        json.dumps(delete_ids, ensure_ascii=False, indent=2), encoding='utf-8'
    )
    print(f'      待删清单已写入 {out_dir}/delete_ids.json')

    if not to_delete:
        print('[5/5] ✅ 没有需要清理的散落节点。')
        return

    # ======== 最终安全检查（防御性编程）========
    for nid in delete_ids:
        matched = next((n for n in nodes if n['id'] == nid), None)
        if matched and matched.get('type') in PROTECTED_TYPES:
            print(f'❌ 致命错误：待删列表里混入了受保护类型 {matched["type"]}，中止！')
            sys.exit(2)

    # ======== 分批输出 MCP 参数 ========
    bs = max(1, args.batch_size)
    batches = [delete_ids[i:i + bs] for i in range(0, len(delete_ids), bs)]
    print(f'[5/5] 待删 {len(delete_ids)} 个节点，分 {len(batches)} 批（每批 ≤ {bs}）。')

    if args.emit_delete_args:
        payload = {
            'canvas_id': canvas_id,
            'mode': 'merge',
            'batches': [
                {'delete_node_ids': b} for b in batches
            ],
        }
        Path(args.emit_delete_args).parent.mkdir(parents=True, exist_ok=True)
        with open(args.emit_delete_args, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f'      MCP 调用参数 → {args.emit_delete_args}')

    print()
    print('下一步（由 Agent 通过 MCP 执行，无需 CLI）：')
    for i, b in enumerate(batches, 1):
        print(f'  canvas_manage(action="build_draft", canvas_id="{canvas_id}",')
        print(f'                delete_node_ids=<第 {i} 批 {len(b)} 个>, mode="merge")')
    print()
    print(f'🛡️ 重申：即使执行删除，text/freehand/artboard/generator 节点也绝不会被删除。')
    print(f'✅ 完成。画布: https://workrally.qq.com/toolbox/canvas/{canvas_id}')


if __name__ == '__main__':
    main()
