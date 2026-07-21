#!/usr/bin/env python3
"""L2 跨产品关联 - 把 L1 案例聚合成攻击链

输入:
  - L1 案例目录 (cases/*.md): 含威胁判定 + IOC + correlation_hints
  - L0 JSONL (含资产关联): 用于补充资产信息

输出:
  - 攻击链 (attack_chains/*.md): 每个关联组一条

关联键 (v1 简单版, 无时间窗拆分):
  - 主: real_attacker_ip (同一攻击者的所有事件 → 攻击者视角)
  - 次: victim_ip (同一受害资产的所有事件 → 受害者视角)

关联意义:
  - 攻击者视角: 一个攻击者攻击了多个目标 (横向移动 / 扫描)
  - 受害者视角: 一个资产被多个攻击者攻击 (高价值目标 / 已失陷)

用法:
  python3 l2_correlate.py \
      --cases l0_output/yujie_cases l0_output/cwp_cases \
      --l0 l0_output/yujie_l0_v3.jsonl l0_output/cwp_l0_v3.jsonl \
      --out l0_output/attack_chains

  # 只看攻击者视角 (跨产品关联)
  python3 l2_correlate.py --cases ... --l0 ... --out ... --pivot attacker

  # 只看受害者视角 (资产被攻击)
  python3 l2_correlate.py --cases ... --l0 ... --out ... --pivot victim

  # 最低事件数阈值 (默认 2)
  python3 l2_correlate.py --cases ... --l0 ... --out ... --min-events 3
"""
from __future__ import annotations
import argparse
import json
import re
import sys
import uuid
from collections import defaultdict
from datetime import datetime
from html import escape
from pathlib import Path

# SCRIPT_DIR = skills/soe/references/alert-analysis/soc-alert-pipeline/scripts/
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))


# ==================== Kill Chain 阶段排序 ====================

KILL_CHAIN_ORDER = {
    "Initial Access": 1,
    "Execution": 2,
    "Persistence": 3,
    "Privilege Escalation": 4,
    "Defense Evasion": 5,
    "Credential Access": 6,
    "Discovery": 7,
    "Lateral Movement": 8,
    "Collection": 9,
    "Command and Control": 10,
    "Exfiltration": 11,
    "Impact": 12,
}


def kill_chain_rank(phase: str | None) -> int:
    """返回 Kill Chain 阶段的排序值 (越小越早)"""
    if not phase:
        return 99
    return KILL_CHAIN_ORDER.get(phase.strip(), 99)


# ==================== 案例加载 (复用 gen_report 的解析逻辑) ====================

def load_cases(case_dirs: list[Path]) -> list[dict]:
    """加载 L1 案例 .md, 解析出结构化字段"""
    cases = []
    for d in case_dirs:
        if not d.exists():
            continue
        for md_path in sorted(d.glob("*.md")):
            try:
                content = md_path.read_text(encoding="utf-8")
            except Exception:
                continue
            case = parse_case_md(content, md_path.stem)
            cases.append(case)
    return cases


def parse_case_md(content: str, case_id: str) -> dict:
    """从 .md 文件解析关键字段"""
    case = {
        "id": case_id,
        "content": content,
        "product": (
            "yujie" if case_id.startswith("yujie")
            else "cwp" if case_id.startswith("cwp")
            else "tianmu" if case_id.startswith("tianmu")
            else "waf" if case_id.startswith("waf")
            else "cfw" if case_id.startswith("cfw")
            else "unknown"
        ),
        "threat_type": None,
        "ttp": None,
        "confidence": 0.0,
        "kill_chain_phase": None,
        "rule_name": None,
        "src_ip": None,
        "dst_ip": None,
        "real_attacker_ip": None,
        "real_victim_ip": None,
        "host_ip": None,
        "hostname": None,
        "user": None,
        "event_time": None,
        "row": _extract_row_from_id(case_id),
    }

    m = re.search(r"\*\*威胁类型\*\*:\s*(.+)", content)
    if m: case["threat_type"] = m.group(1).strip()

    m = re.search(r"\*\*TTP\*\*:\s*(\S+)", content)
    if m: case["ttp"] = m.group(1).strip()

    m = re.search(r"\*\*置信度\*\*:\s*([\d.]+)", content)
    if m:
        try: case["confidence"] = float(m.group(1))
        except ValueError: pass

    m = re.search(r"\*\*Kill Chain 阶段\*\*:\s*(.+)", content)
    if m: case["kill_chain_phase"] = m.group(1).strip()

    m = re.search(r"\| 源 IP \| ([^|]+) \|", content)
    if m:
        ip = m.group(1).strip()
        if ip and ip != "-": case["src_ip"] = ip

    m = re.search(r"\| 目的 IP:端口 \| ([^:]+):", content)
    if m:
        ip = m.group(1).strip()
        if ip and ip != "-": case["dst_ip"] = ip

    m = re.search(r"\| 主机 \| ([^|]+) \|", content)
    if m:
        ip = m.group(1).strip()
        if ip and ip != "?" and ip != "-": case["host_ip"] = ip

    # 御界: 真实 (NAT 还原)
    m = re.search(r"\*\*真实 \(NAT 还原\)\*\* \| ([^:]+):", content)
    if m:
        parts = m.group(1).strip().split()
        if parts: case["real_attacker_ip"] = parts[0]

    # 御界: 从 NAT 链分析里提取 real_victim_ip
    m = re.search(r"真实:.*?→\s*([^\s;]+)", content)
    if m:
        victim = m.group(1).strip().rstrip(";")
        if victim and victim != "-": case["real_victim_ip"] = victim

    m = re.search(r"\| 用户 \| ([^|]+) \|", content)
    if m:
        u = m.group(1).strip()
        if u and u != "-": case["user"] = u

    m = re.search(r"\| 事件时间 \| ([^|]+) \|", content)
    if m: case["event_time"] = m.group(1).strip()

    m = re.search(r"\| 告警名称 \| ([^|]+) \|", content)
    if not m:
        m = re.search(r"\| 规则 \| ([^(]+)", content)
    if m: case["rule_name"] = m.group(1).strip()

    # 主机安全: 从 _raw_kv 里没有, 但从 case md 的附录里可以提取 appid
    m = re.search(r'"appid":\s*"([^"]+)"', content)
    if m: case["appid"] = m.group(1)

    # 御界: vpcid
    m = re.search(r'"vpcid":\s*(\d+)', content)
    if m: case["vpcid"] = int(m.group(1))

    return case


def _extract_row_from_id(case_id: str) -> int:
    """从 case ID 提取 row 号: yujie_r00000_xxx → 0"""
    m = re.match(r"\w+_r(\d+)_", case_id)
    if m:
        return int(m.group(1))
    return -1


# ==================== L0 加载 (资产信息) ====================

def load_l0_assets(l0_paths: list[Path]) -> dict[int, dict]:
    """加载 L0 JSONL, 按 (source_file, row) 索引资产信息

    Returns:
        {(source_file, row): asset_dict}
    """
    assets = {}
    for p in l0_paths:
        if not p.exists():
            continue
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                key = (rec.get("source_file", ""), rec.get("row", -1))
                assets[key] = rec.get("asset", {}) or {}
    return assets


def enrich_cases_with_assets(cases: list[dict], assets: dict) -> None:
    """把 L0 的资产信息合并到 cases 里 (in-place 修改)"""
    for case in cases:
        # 从 case 的 source_file + row 找资产
        # case 里没有 source_file, 用 product + row 模糊匹配
        row = case.get("row", -1)
        if row < 0:
            continue

        # 尝试匹配: 御界 case 找 yujie 的 L0, 主机安全 case 找 cwp 的 L0
        for (source_file, rec_row), asset in assets.items():
            if rec_row != row:
                continue
            product = case.get("product", "")
            if product == "yujie" and "yujie" not in source_file.lower() and "45614" not in source_file:
                continue
            if product == "cwp" and "144610" not in source_file and "cwp" not in source_file.lower():
                continue
            case["asset"] = asset
            break


# ==================== 关联算法 ====================

def correlate_by_attacker(cases: list[dict], min_events: int = 2) -> list[dict]:
    """按攻击者 IP 分组关联

    Returns:
        [{pivot_type: "attacker", pivot_key: "1.2.3.4", cases: [...], ...}, ...]
    """
    groups = defaultdict(list)
    for case in cases:
        attacker = case.get("real_attacker_ip") or case.get("src_ip")
        if attacker and attacker != "-":
            groups[attacker].append(case)

    chains = []
    for attacker, group_cases in groups.items():
        if len(group_cases) < min_events:
            continue
        chains.append(_build_chain(attacker, group_cases, "attacker"))
    return chains


def correlate_by_victim(cases: list[dict], min_events: int = 2) -> list[dict]:
    """按受害资产 IP 分组关联"""
    groups = defaultdict(list)
    for case in cases:
        victim = case.get("real_victim_ip") or case.get("host_ip") or case.get("dst_ip")
        if victim and victim != "-":
            groups[victim].append(case)

    chains = []
    for victim, group_cases in groups.items():
        if len(group_cases) < min_events:
            continue
        chains.append(_build_chain(victim, group_cases, "victim"))
    return chains


def _build_chain(pivot_key: str, cases: list[dict], pivot_type: str) -> dict:
    """构建单个攻击链"""
    # 按 kill chain 阶段 + 时间排序
    sorted_cases = sorted(
        cases,
        key=lambda c: (kill_chain_rank(c.get("kill_chain_phase")), c.get("event_time") or ""),
    )

    # 统计
    products = defaultdict(int)
    threat_types = defaultdict(int)
    ttps = set()
    kill_chain_phases = set()
    times = []

    for c in sorted_cases:
        products[c["product"]] += 1
        if c["threat_type"]:
            threat_types[c["threat_type"]] += 1
        if c["ttp"]:
            ttps.add(c["ttp"])
        if c["kill_chain_phase"]:
            kill_chain_phases.add(c["kill_chain_phase"])
        if c["event_time"]:
            times.append(c["event_time"])

    # 资产信息 (从第一个有 asset 的 case 取)
    victim_asset = None
    for c in sorted_cases:
        a = c.get("asset", {})
        if isinstance(a, dict) and a.get("victim_asset"):
            victim_asset = a["victim_asset"]
            break

    return {
        "chain_id": f"chain_{pivot_type}_{pivot_key.replace('.', '_')}_{uuid.uuid4().hex[:6]}",
        "pivot_type": pivot_type,         # "attacker" / "victim"
        "pivot_key": pivot_key,
        "cases": sorted_cases,
        "case_count": len(sorted_cases),
        "products": dict(products),
        "threat_types": dict(threat_types),
        "ttps": sorted(ttps),
        "kill_chain_phases": sorted(kill_chain_phases, key=kill_chain_rank),
        "time_range": (min(times), max(times)) if times else (None, None),
        "victim_asset": victim_asset,
        "is_cross_product": len(products) >= 2,
    }


# ==================== 攻击链渲染 ====================

def render_chain_md(chain: dict) -> str:
    """渲染单个攻击链为 Markdown"""
    lines = []
    pivot_type = chain["pivot_type"]
    pivot_key = chain["pivot_key"]
    chain_id = chain["chain_id"]

    # 标题
    if pivot_type == "attacker":
        title = f"攻击链 (攻击者视角) - {pivot_key}"
    else:
        title = f"攻击链 (受害者视角) - {pivot_key}"

    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"> chain_id: {chain_id}")
    lines.append(f"> 生成时间: {datetime.now().isoformat()}")
    lines.append("")

    # 1. 概要
    lines.append("## 1. 概要")
    lines.append("")
    lines.append("| 字段 | 值 |")
    lines.append("|---|---|")
    lines.append(f"| 关联类型 | {'攻击者视角 (同一攻击者)' if pivot_type == 'attacker' else '受害者视角 (同一受害资产)'} |")
    lines.append(f"| 关联键 | `{pivot_key}` |")
    lines.append(f"| 事件数 | {chain['case_count']} |")
    t_min, t_max = chain["time_range"]
    if t_min and t_max:
        lines.append(f"| 时间范围 | {t_min} ~ {t_max} |")
    else:
        lines.append("| 时间范围 | (无时间数据) |")

    # 涉及产品
    products_str = ", ".join(f"{p} ({n})" for p, n in chain["products"].items())
    lines.append(f"| 涉及产品 | {products_str} |")
    lines.append(f"| **跨产品关联** | {'✅ 是 (跨产品攻击链)' if chain['is_cross_product'] else '❌ 否 (单产品)'} |")

    # 威胁类型
    threats_str = ", ".join(f"{t} ({n})" for t, n in chain["threat_types"].items())
    lines.append(f"| 威胁类型 | {threats_str or '(无)'} |")

    # TTP
    ttps_str = ", ".join(chain["ttps"]) if chain["ttps"] else "(无)"
    lines.append(f"| ATT&CK TTP | {ttps_str} |")

    # Kill Chain 阶段
    phases_str = " → ".join(chain["kill_chain_phases"]) if chain["kill_chain_phases"] else "(无)"
    lines.append(f"| Kill Chain 阶段 | {phases_str} |")

    # 受害资产
    if chain["victim_asset"]:
        va = chain["victim_asset"]
        lines.append(f"| 受害资产 | `{va.get('ip', '?')}` - {va.get('hostname', '?')} ({va.get('asset_type', '?')}, {va.get('importance', '?')}) |")
    else:
        lines.append("| 受害资产 | (未匹配资产库) |")
    lines.append("")

    # 2. 时间线
    lines.append("## 2. 时间线 (按 Kill Chain 阶段排序)")
    lines.append("")
    lines.append("| # | 时间 | 产品 | 威胁类型 | TTP | 置信度 | Kill Chain | 攻击者 | 受害者 | 案例 ID |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for i, c in enumerate(chain["cases"], 1):
        attacker = c.get("real_attacker_ip") or c.get("src_ip") or "-"
        victim = c.get("real_victim_ip") or c.get("host_ip") or c.get("dst_ip") or "-"
        lines.append(
            f"| {i} | {c.get('event_time', '-')[:30]} | {c['product']} | "
            f"{c.get('threat_type', '-') or '-'} | `{c.get('ttp', '-') or '-'}` | "
            f"{c.get('confidence', 0):.2f} | {c.get('kill_chain_phase', '-') or '-'} | "
            f"`{attacker}` | `{victim}` | `{c['id']}` |"
        )
    lines.append("")

    # 3. Kill Chain 还原
    lines.append("## 3. Kill Chain 还原")
    lines.append("")
    if pivot_type == "attacker":
        lines.append(f"攻击者 `{pivot_key}` 的攻击行为按 Kill Chain 阶段还原:")
    else:
        lines.append(f"受害资产 `{pivot_key}` 被攻击的行为按 Kill Chain 阶段还原:")
    lines.append("")

    # 按 Kill Chain 阶段分组
    by_phase = defaultdict(list)
    for c in chain["cases"]:
        phase = c.get("kill_chain_phase") or "Unknown"
        by_phase[phase].append(c)

    for phase in sorted(by_phase.keys(), key=kill_chain_rank):
        phase_cases = by_phase[phase]
        rank = kill_chain_rank(phase)
        lines.append(f"### 阶段 {rank}: {phase} ({len(phase_cases)} 个事件)")
        lines.append("")
        for c in phase_cases:
            attacker = c.get("real_attacker_ip") or c.get("src_ip") or "?"
            victim = c.get("real_victim_ip") or c.get("host_ip") or c.get("dst_ip") or "?"
            threat = c.get("threat_type") or "?"
            ttp = c.get("ttp") or "?"
            conf = c.get("confidence", 0)
            product = c["product"]
            lines.append(f"- [{product}] `{attacker}` → `{victim}`: {threat} (TTP: {ttp}, conf={conf:.2f})")
        lines.append("")

    # 4. 跨产品关联分析
    lines.append("## 4. 跨产品关联分析")
    lines.append("")
    if chain["is_cross_product"]:
        lines.append("**此攻击链跨越多个产品**, 说明攻击行为在不同安全产品中都留下了痕迹:")
        lines.append("")
        for product, count in chain["products"].items():
            product_name = (
                "御界 (高级威胁检测)" if product == "yujie"
                else "主机安全 (CWP)" if product == "cwp"
                else "天幕 (安全治理/阻断)" if product == "tianmu"
                else product
            )
            lines.append(f"- **{product_name}**: {count} 个事件")
        lines.append("")

        # 分析跨产品关联的意义
        products_set = set(chain["products"].keys())
        if "tianmu" in products_set and "yujie" in products_set:
            lines.append("**天幕 ↔ 御界 关联**:")
            lines.append("- 天幕 (网络治理层) 阻断了攻击者的网络请求 (已拦截)")
            lines.append("- 御界 (流量层) 检测到攻击者的网络行为 (C2 / 隧道 / 扫描)")
            lines.append("- 关联意义: 天幕阻断了什么 ↔ 御界检测到什么, 可确认攻击是否被有效拦截")
            lines.append("")
        if "tianmu" in products_set and "cwp" in products_set:
            lines.append("**天幕 ↔ 主机安全 关联**:")
            lines.append("- 天幕 (网络治理层) 阻断了攻击者的网络请求 (已拦截)")
            lines.append("- 主机安全 (主机层) 检测到受害主机的进程行为 (入侵/持久化)")
            lines.append("- 关联意义: 天幕阻断了但主机安全仍有告警 → 攻击可能已突破边界")
            lines.append("")
        if "yujie" in products_set and "cwp" in products_set:
            lines.append("**御界 ↔ 主机安全 关联**:")
            lines.append("- 御界 (流量层) 检测到攻击者的网络行为 (C2 / 隧道 / 横向)")
            lines.append("- 主机安全 (主机层) 检测到受害主机的进程行为 (暴力破解 / 反弹 shell)")
            lines.append("- 两者结合可以还原完整的攻击链: 网络入侵 → 主机失陷 → 横向扩散")
            lines.append("")
    else:
        products = list(chain["products"].keys())
        product = products[0] if products else "?"
        product_name = (
            "御界" if product == "yujie"
            else "主机安全" if product == "cwp"
            else "天幕" if product == "tianmu"
            else product
        )
        lines.append(f"此攻击链仅涉及 **{product_name}** (单产品), 暂无跨产品关联.")
        lines.append("")
        lines.append("**建议**:")
        if product == "yujie":
            lines.append("- 拉取受害 IP 在主机安全 (cwp) 的告警, 看是否有主机层异常")
            lines.append("- 拉取攻击者 IP 在 WAF / CFW / 天幕 的告警, 看是否有应用层 / 网络层阻断")
        elif product == "cwp":
            lines.append("- 拉取受害主机 IP 在御界 (yujie) 的告警, 看是否有流量层异常")
            lines.append("- 拉取攻击者 IP 在御界 / 天幕 / CFW 的告警, 看是否有网络层阻断")
        elif product == "tianmu":
            lines.append("- 拉取天幕阻断的源IP 在御界 (yujie) 的告警, 看是否有流量层检测")
            lines.append("- 拉取天幕阻断的源IP 在主机安全 (cwp) 的告警, 看是否已突破边界")
        lines.append("")

    # 5. 处置建议
    lines.append("## 5. 处置建议")
    lines.append("")
    if pivot_type == "attacker":
        lines.append(f"### 针对攻击者 `{pivot_key}`")
        lines.append("")
        lines.append(f"- [ ] **阻断攻击者 IP**: 安全组 / CFW / WAF 阻断 `{pivot_key}` 的所有入站和出站流量")
        lines.append(f"- [ ] **拉取历史**: 在 SOC / 御界 / 主机安全 / WAF 中搜索 `{pivot_key}` 的全部历史告警")
        lines.append(f"- [ ] **威胁情报查询**: 查 `{pivot_key}` 是否在已知 IOC 库 (微步 / ThreatBook / VirusTotal)")
        if chain["is_cross_product"]:
            lines.append("- [ ] **攻击链溯源**: 按 Kill Chain 时间线还原攻击者从初始入侵到最终目标的完整路径")
        lines.append("")

        lines.append("### 针对受害资产")
        lines.append("")
        if chain["victim_asset"]:
            va = chain["victim_asset"]
            lines.append(f"- [ ] **隔离受害主机**: `{va.get('ip')}` ({va.get('hostname')})")
            lines.append(f"- [ ] **取证**: 拉取 `{va.get('ip')}` 的进程列表 / 网络连接 / 文件系统变更")
            lines.append(f"- [ ] **加固**: 检查 `{va.get('hostname')}` 的弱口令 / 未授权服务 / 补丁状态")
        else:
            lines.append("- [ ] **识别受害主机**: 当前受害 IP 未匹配资产库, 需先确认资产归属")
            lines.append("- [ ] **隔离**: 确认后立即隔离")
        lines.append("")
    else:
        lines.append(f"### 针对受害资产 `{pivot_key}`")
        lines.append("")
        lines.append(f"- [ ] **立即隔离**: `{pivot_key}` 已被多个攻击者攻击, 可能已失陷")
        lines.append(f"- [ ] **取证**: 拉取 `{pivot_key}` 的完整主机取证 (进程 / 网络 / 文件 / 内存)")
        lines.append(f"- [ ] **溯源**: 分析所有攻击 `{pivot_key}` 的攻击者 IP, 看是否同一团伙")
        lines.append(f"- [ ] **加固**: 修复 `{pivot_key}` 的漏洞 / 弱口令 / 配置问题")
        lines.append("")

    # 6. 附录: 原始案例列表
    lines.append("## 6. 附录: 涉及的案例列表")
    lines.append("")
    for c in chain["cases"]:
        lines.append(f"- `{c['id']}`: {c.get('threat_type', '?')} (conf={c.get('confidence', 0):.2f})")
    lines.append("")

    return "\n".join(lines)


# ==================== CLI ====================

def main():
    ap = argparse.ArgumentParser(
        description="L2 跨产品关联 - 攻击链还原",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--cases", nargs="+", type=Path, required=True,
                    help="L1 案例目录 (可多个)")
    ap.add_argument("--l0", nargs="+", type=Path, default=None,
                    help="L0 JSONL 文件 (含资产关联, 可选)")
    ap.add_argument("--out", type=Path, default=Path("attack_chains"),
                    help="输出目录 (默认 ./attack_chains)")
    ap.add_argument("--pivot", choices=["attacker", "victim", "both"], default="both",
                    help="关联视角: attacker (攻击者) / victim (受害者) / both (默认)")
    ap.add_argument("--min-events", type=int, default=2,
                    help="最低事件数阈值 (默认 2)")
    ap.add_argument("--cross-product-only", action="store_true",
                    help="只输出跨产品关联的攻击链 (≥2 个产品)")
    args = ap.parse_args()

    # 1. 加载案例
    print("[INFO] 加载 L1 案例...", file=sys.stderr)
    cases = load_cases(args.cases)
    print(f"[INFO] 案例数: {len(cases)}", file=sys.stderr)

    # 2. 加载 L0 资产信息 (可选)
    if args.l0:
        print("[INFO] 加载 L0 资产信息...", file=sys.stderr)
        assets = load_l0_assets(args.l0)
        print(f"[INFO] L0 资产记录: {len(assets)}", file=sys.stderr)
        enrich_cases_with_assets(cases, assets)
        matched = sum(1 for c in cases if c.get("asset"))
        print(f"[INFO] 案例匹配资产: {matched}/{len(cases)}", file=sys.stderr)

    # 3. 关联
    chains = []
    if args.pivot in ("attacker", "both"):
        print("[INFO] 按攻击者 IP 关联...", file=sys.stderr)
        attacker_chains = correlate_by_attacker(cases, args.min_events)
        chains.extend(attacker_chains)
        print(f"[INFO] 攻击者视角攻击链: {len(attacker_chains)}", file=sys.stderr)

    if args.pivot in ("victim", "both"):
        print("[INFO] 按受害资产 IP 关联...", file=sys.stderr)
        victim_chains = correlate_by_victim(cases, args.min_events)
        chains.extend(victim_chains)
        print(f"[INFO] 受害者视角攻击链: {len(victim_chains)}", file=sys.stderr)

    # 4. 过滤: 只看跨产品
    if args.cross_product_only:
        before = len(chains)
        chains = [c for c in chains if c["is_cross_product"]]
        print(f"[INFO] 跨产品过滤: {before} → {len(chains)}", file=sys.stderr)

    # 5. 排序: 按事件数降序
    chains.sort(key=lambda c: c["case_count"], reverse=True)

    # 6. 输出
    args.out.mkdir(parents=True, exist_ok=True)
    print(f"[INFO] 输出目录: {args.out}", file=sys.stderr)

    # 汇总文件
    summary_lines = [
        "# L2 攻击链汇总",
        "",
        f"> 生成时间: {datetime.now().isoformat()}",
        f"> 案例总数: {len(cases)}",
        f"> 攻击链总数: {len(chains)}",
        f"> 跨产品攻击链: {sum(1 for c in chains if c['is_cross_product'])}",
        "",
        "## 攻击链列表 (按事件数降序)",
        "",
        "| # | chain_id | 视角 | 关联键 | 事件数 | 跨产品 | 涉及产品 | Kill Chain |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for i, chain in enumerate(chains, 1):
        pivot = "攻击者" if chain["pivot_type"] == "attacker" else "受害者"
        cross = "✅" if chain["is_cross_product"] else "❌"
        products = ", ".join(f"{p}({n})" for p, n in chain["products"].items())
        phases = " → ".join(chain["kill_chain_phases"][:3]) if chain["kill_chain_phases"] else "-"
        summary_lines.append(
            f"| {i} | `{chain['chain_id']}` | {pivot} | `{chain['pivot_key']}` | "
            f"{chain['case_count']} | {cross} | {products} | {phases} |"
        )

    summary_lines.append("")
    summary_lines.append("## 详细攻击链")
    summary_lines.append("")

    # 同时输出结构化 JSONL (供 gen_report.py 消费)
    jsonl_path = args.out / "attack_chains.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as jsonl_f:
        for chain in chains:
            md = render_chain_md(chain)
            out_path = args.out / f"{chain['chain_id']}.md"
            out_path.write_text(md, encoding="utf-8")
            summary_lines.append(
                f"- [{chain['chain_id']}](./{chain['chain_id']}.md): "
                f"{chain['pivot_type']} `{chain['pivot_key']}` ({chain['case_count']} 事件)"
            )

            # JSONL 记录 (只含报告需要的关键字段, 不含完整 cases 列表)
            top_cases = [
                {
                    "case_id": c["id"],
                    "product": c["product"],
                    "threat_type": c.get("threat_type"),
                    "ttp": c.get("ttp"),
                    "confidence": c.get("confidence", 0),
                    "kill_chain_phase": c.get("kill_chain_phase"),
                    "event_time": c.get("event_time"),
                    "real_attacker_ip": c.get("real_attacker_ip"),
                    "real_victim_ip": c.get("real_victim_ip"),
                    "src_ip": c.get("src_ip"),
                    "dst_ip": c.get("dst_ip"),
                    "host_ip": c.get("host_ip"),
                    "user": c.get("user"),
                }
                for c in chain["cases"][:20]  # 只取前 20 个, 避免报告过大
            ]
            jsonl_record = {
                "chain_id": chain["chain_id"],
                "pivot_type": chain["pivot_type"],
                "pivot_key": chain["pivot_key"],
                "case_count": chain["case_count"],
                "is_cross_product": chain["is_cross_product"],
                "products": chain["products"],
                "threat_types": chain["threat_types"],
                "ttps": chain["ttps"],
                "kill_chain_phases": chain["kill_chain_phases"],
                "time_range": list(chain["time_range"]),
                "victim_asset": chain["victim_asset"],
                "top_cases": top_cases,
                "md_file": f"{chain['chain_id']}.md",
            }
            jsonl_f.write(json.dumps(jsonl_record, ensure_ascii=False) + "\n")

    (args.out / "SUMMARY.md").write_text("\n".join(summary_lines), encoding="utf-8")

    print(f"[OK] 生成 {len(chains)} 个攻击链 + 1 个汇总 + 1 个 JSONL", file=sys.stderr)
    print(f"[OK] 汇总: {args.out / 'SUMMARY.md'}", file=sys.stderr)
    print(f"[OK] JSONL: {jsonl_path} (供 gen_report.py 消费)", file=sys.stderr)
    print(f"[OK] 跨产品攻击链: {sum(1 for c in chains if c['is_cross_product'])}", file=sys.stderr)


if __name__ == "__main__":
    main()
