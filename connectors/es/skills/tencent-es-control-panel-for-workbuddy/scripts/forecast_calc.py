# /// script
# dependencies = []
# ///
"""
容量预测计算脚本（tencent-es-control-panel MCP 版）

⚠️ 本脚本【零云 API 调用】，不读取任何腾讯云凭证，不做任何签名，不发起任何网络请求。
   它只做一件事：把 GetMonitorData MCP tool 的返回结果做确定性数值计算。

为什么需要这个脚本：
  容量预测涉及线性回归（Σxy / Σx²）、百分位数排序、阈值外推等数值计算，
  输入规模是上百个数据点（7 天 × Period=3600 ≈ 168 点）。
  这类计算交给 LLM「照规则表心算」不可靠 —— 且算错不会报错，
  只会安静地给出看似合理的错误结论，比脚本报错危险得多。

  与之相对，健康打分那类「阈值比较」（磁盘 ≥ 95% → 一票否决）LLM 可以可靠执行，
  因此 tencent-es-diagnose 用纯规则表是合适的。两者性质不同，不可类比。

数据流：
  GetMonitorData(MCP tool) 取数 → 本脚本计算 → Agent 拿确定性数字写报告

用法：
  # 单指标
  python3 mcpcall GetMonitorData ... | python3 forecast_calc.py --node-num 3 --disk-size 300 --disk-type CLOUD_SSD

  # 多指标（把多个 GetMonitorData 响应放进一个 JSON 数组）
  cat metrics.json | python3 forecast_calc.py --node-num 3 --disk-size 300 --disk-type CLOUD_SSD --node-type ES.S1.LARGE16

输入格式（stdin，三种都支持）：
  1. 单个 GetMonitorData 响应：      {"Response": {"MetricName": "...", "DataPoints": [...]}}
  2. 多个响应组成的数组：            [{"Response": {...}}, {"Response": {...}}]
  3. 已剥掉 Response 外层的对象：    {"MetricName": "...", "DataPoints": [...]}
"""

import argparse
import json
import math
import sys

# ============================================================
# 阈值表（与 references/capacity-forecast-rules.md 严格一致）
# ============================================================

METRIC_THRESHOLDS = {
    "DiskUsageMax":         {"warn": 65,   "critical": 80,  "unit": "%",    "label": "磁盘使用率（最大）"},
    "CpuUsageMax":          {"warn": 70,   "critical": 85,  "unit": "%",    "label": "CPU 使用率（最大）"},
    "JvmMemUsageMax":       {"warn": 75,   "critical": 85,  "unit": "%",    "label": "JVM 内存使用率（最大）"},
    "IndexSpeed":           {"warn": None, "critical": None, "unit": "次/s", "label": "写入 QPS"},
    "SearchCompletedSpeed": {"warn": None, "critical": None, "unit": "次/s", "label": "查询 QPS"},
    "SearchLatencyAvg":     {"warn": 200,  "critical": 500, "unit": "ms",   "label": "查询平均延迟"},
}

# 磁盘类型
LOCAL_DISK_TYPES = {"LOCAL_SSD"}
CLOUD_DISK_TYPES = {"CLOUD_PREMIUM", "CLOUD_SSD", "CLOUD_HSSD"}

DISK_TYPE_LABELS = {
    "LOCAL_SSD":      "本地 SSD 盘（不可扩磁盘，只能加节点）",
    "CLOUD_PREMIUM":  "高性能云硬盘（可原地扩容）",
    "CLOUD_SSD":      "SSD 云硬盘（可原地扩容）",
    "CLOUD_HSSD":     "增强型 SSD 云硬盘（可原地扩容）",
}

# 节点数量允许区间（与 UpdateInstanceNodeNum 服务端约束一致）
NODE_NUM_RANGES = {
    "dedicatedMaster":       (3, 5),
    "dedicatedMl":           (3, 5),
    "hotData":               (2, 50),
    "warmData":              (2, 50),
    "dedicatedCoordinating": (2, 50),
}

# 升配推荐表（规格升配暂无 MCP tool，仅用于只读推荐）
CPU_UPGRADE_MAP = {
    "ES.S1.SMALL2": "ES.S1.MEDIUM4", "ES.S1.MEDIUM4": "ES.S1.LARGE8",
    "ES.S1.MEDIUM8": "ES.S1.LARGE16", "ES.S1.LARGE8": "ES.S1.2XLARGE16",
    "ES.S1.LARGE16": "ES.S1.2XLARGE16", "ES.S1.2XLARGE16": "ES.S1.4XLARGE32",
    "ES.S1.2XLARGE32": "ES.S1.4XLARGE32", "ES.S1.4XLARGE32": "ES.S1.4XLARGE64",
}
MEM_UPGRADE_MAP = {
    "ES.S1.MEDIUM4": "ES.S1.MEDIUM8", "ES.S1.MEDIUM8": "ES.S1.LARGE16",
    "ES.S1.LARGE8": "ES.S1.LARGE16", "ES.S1.LARGE16": "ES.S1.2XLARGE32",
    "ES.S1.2XLARGE16": "ES.S1.2XLARGE32", "ES.S1.2XLARGE32": "ES.S1.4XLARGE64",
    "ES.S1.4XLARGE32": "ES.S1.4XLARGE64",
}


def error_exit(msg: str):
    sys.stderr.write(json.dumps({"error": msg}, ensure_ascii=False) + "\n")
    sys.exit(1)


# ============================================================
# 输入解析
# ============================================================

def _iter_responses(payload):
    """把三种输入形态统一成 response dict 的迭代器"""
    if isinstance(payload, list):
        items = payload
    else:
        items = [payload]
    for item in items:
        if not isinstance(item, dict):
            continue
        # 兼容 {"Response": {...}} 与已剥外层的 {...}
        resp = item.get("Response", item)
        if isinstance(resp, dict) and "DataPoints" in resp:
            yield resp


def parse_metrics(payload, instance_id: str = "") -> dict:
    """
    解析 GetMonitorData 响应，返回 {metric_name: [(ts, value), ...]}
    ⚠️ 此处执行哨兵值剔除：丢弃所有 value < 0 的点（云监控探针失败返回 -2/-1）
    """
    result = {}
    for resp in _iter_responses(payload):
        metric = resp.get("MetricName", "")
        if not metric:
            continue
        for dp in resp.get("DataPoints", []):
            # 多实例场景：按 instance_id 过滤
            if instance_id:
                dims = {d.get("Name"): d.get("Value") for d in dp.get("Dimensions", [])}
                dim_iid = dims.get("uInstanceId") or dims.get("InstanceId") or ""
                if dim_iid and dim_iid != instance_id:
                    continue

            timestamps = dp.get("Timestamps") or []
            values = dp.get("Values") or []
            points = []
            sentinel = 0
            for ts, val in zip(timestamps, values):
                if val is None:
                    continue
                try:
                    fval = float(val)
                except (TypeError, ValueError):
                    continue
                # 哨兵值剔除（探针采集失败返回 -2，偶见 -1）
                if fval < 0:
                    sentinel += 1
                    continue
                points.append((float(ts), fval))

            points.sort(key=lambda p: p[0])
            prev = result.get(metric)
            if prev:
                prev["points"].extend(points)
                prev["sentinel_dropped"] += sentinel
                prev["raw_total"] += len(timestamps)
            else:
                result[metric] = {
                    "points": points,
                    "sentinel_dropped": sentinel,
                    "raw_total": len(timestamps),
                }
    return result


# ============================================================
# 数值计算
# ============================================================

def linear_regression(points: list) -> tuple:
    """最小二乘线性回归，返回 (slope, intercept)。points: [(x, y), ...]"""
    n = len(points)
    if n < 2:
        return 0.0, (points[0][1] if n == 1 else 0.0)

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x_mean = sum(xs) / n
    y_mean = sum(ys) / n

    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    denominator = sum((x - x_mean) ** 2 for x in xs)
    if denominator == 0:
        return 0.0, y_mean

    slope = numerator / denominator
    return slope, y_mean - slope * x_mean


def percentile(values: list, pct: float) -> float:
    """线性插值百分位数（pct: 0~100）"""
    if not values:
        return 0.0
    s = sorted(values)
    if len(s) == 1:
        return s[0]
    idx = (len(s) - 1) * pct / 100.0
    lo = int(math.floor(idx))
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (idx - lo)


def days_to_threshold(points: list, slope: float, intercept: float,
                      base_ts: float, threshold) -> dict:
    """
    预测多少天后达到 threshold。
    base_ts 用【最后一个有效数据点的时间】而非 now()，
    避免分析历史区间时 now 落在数据范围外导致外推失真。
    """
    if threshold is None:
        return {"days": None, "note": "该指标无阈值，不做外推"}
    if len(points) < 2:
        return {"days": None, "note": "有效数据点不足 2 个，无法外推"}

    current_fit = slope * base_ts + intercept
    if current_fit >= threshold:
        return {"days": 0, "note": "拟合值已达到或超过阈值"}
    if slope <= 0:
        return {"days": None, "note": "趋势平稳或下降（slope<=0），不外推"}

    target_ts = (threshold - intercept) / slope
    days = (target_ts - base_ts) / 86400.0
    if days < 0:
        return {"days": 0, "note": "拟合值已超过阈值"}
    if days > 3650:
        return {"days": None, "note": f"外推超过 10 年（{days:.0f} 天），增长极缓，视为无需关注"}
    return {"days": round(days, 1), "note": ""}


def monthly_growth_rate(points: list, slope: float, intercept: float,
                        base_ts: float) -> float:
    """
    月增长率（%）：基于回归线，比较 base_ts 与 base_ts+30d 的拟合值。
    ⚠️ 修复 v3 capacity_forecast.py 的 NameError BUG
       （原代码在无 threshold 参数的函数体内引用了未定义的 threshold 变量）。
    """
    if len(points) < 2:
        return 0.0
    current_fit = slope * base_ts + intercept
    future_fit = slope * (base_ts + 30 * 86400) + intercept
    if current_fit == 0:
        return 0.0
    return (future_fit - current_fit) / abs(current_fit) * 100.0


def analyze_metric(metric: str, bundle: dict) -> dict:
    """对单个指标做完整统计"""
    points = bundle["points"]
    th = METRIC_THRESHOLDS.get(metric, {"warn": None, "critical": None, "unit": "", "label": metric})
    values = [v for _, v in points]

    out = {
        "metric": metric,
        "label": th["label"],
        "unit": th["unit"],
        "warn": th["warn"],
        "critical": th["critical"],
        "valid_points": len(points),
        "raw_points": bundle["raw_total"],
        "sentinel_dropped": bundle["sentinel_dropped"],
    }

    if not points:
        out.update({
            "status": "no_data",
            "note": "无有效数据（可能探针失联或该指标不适用）",
        })
        return out

    base_ts = points[-1][0]
    slope, intercept = linear_regression(points)

    out.update({
        "current": round(values[-1], 3),
        "min": round(min(values), 3),
        "max": round(max(values), 3),
        "avg": round(sum(values) / len(values), 3),
        "p50": round(percentile(values, 50), 3),
        "p95": round(percentile(values, 95), 3),
        "slope_per_day": round(slope * 86400, 6),
        "trend": "上升" if slope * 86400 > 0.01 else ("下降" if slope * 86400 < -0.01 else "平稳"),
        "monthly_growth_rate_pct": round(monthly_growth_rate(points, slope, intercept, base_ts), 2),
        "days_to_warn": days_to_threshold(points, slope, intercept, base_ts, th["warn"]),
        "days_to_critical": days_to_threshold(points, slope, intercept, base_ts, th["critical"]),
    })

    # 数据完整性提示
    if out["raw_points"] > 0 and out["valid_points"] < out["raw_points"] * 0.5:
        out["confidence"] = "low"
        out["confidence_note"] = (
            f"监控数据缺失较多（有效 {out['valid_points']}/{out['raw_points']} 点），预测置信度低"
        )
    elif out["valid_points"] < 10:
        out["confidence"] = "low"
        out["confidence_note"] = f"有效数据点仅 {out['valid_points']} 个，线性回归不稳定，结果为粗略估算"
    else:
        out["confidence"] = "normal"
        out["confidence_note"] = ""

    # 水位状态
    cur = out["current"]
    if th["critical"] is not None and cur >= th["critical"]:
        out["status"] = "critical"
    elif th["warn"] is not None and cur >= th["warn"]:
        out["status"] = "warn"
    else:
        out["status"] = "normal"

    # CPU 偶发 vs 持续判定（口径与规则表一致）
    if metric == "CpuUsageMax":
        if out["p50"] > 70:
            out["pattern"] = "sustained"
            out["pattern_note"] = f"持续高负载（P50={out['p50']}% > 70%）→ 升配有效"
        elif out["p95"] > 85:
            out["pattern"] = "spike"
            out["pattern_note"] = (
                f"偶发打高（P95={out['p95']}% > 85% 但 P50={out['p50']}% < 60%）"
                f"→ ⚠️ 不推荐扩容，转 tencent-es-diagnose 分析尖刺"
            )
        else:
            out["pattern"] = "normal"
            out["pattern_note"] = "无持续压力"

    return out


# ============================================================
# 扩容建议（输出目标值，直接对应 MCP tool 入参）
# ============================================================

def build_recommendations(metrics: dict, node_num: int, disk_size: int,
                          disk_type: str, node_type: str, node_role: str) -> list:
    recs = []
    is_local = disk_type in LOCAL_DISK_TYPES
    disk_label = DISK_TYPE_LABELS.get(disk_type, f"未知磁盘类型（{disk_type}）")

    # ---------- 1. 磁盘 ----------
    disk = metrics.get("DiskUsageMax")
    if disk and disk.get("status") != "no_data":
        cur = disk["current"]
        d80 = disk["days_to_critical"].get("days")
        trigger = cur >= 65 or (d80 is not None and d80 <= 30)
        if trigger:
            urgency = "🔴 紧急" if cur >= 80 else ("🟠 建议" if cur >= 65 else "🟡 预警")
            if cur >= 80:
                timeline = "磁盘已超过 80%，ES 即将触发只读保护，需立即处理"
            elif d80 is not None:
                timeline = f"按当前趋势，预计 {d80:.0f} 天后达到 80%"
            else:
                timeline = f"当前 {cur}%，月增长 {disk['monthly_growth_rate_pct']}%"

            if is_local or disk_size <= 0:
                # 本地盘：只能加节点，目标使用率 ≤ 50%
                if node_num > 0:
                    target_nodes = math.ceil(node_num * cur / 50.0)
                    target_nodes = max(target_nodes, node_num + 1)
                    lo, hi = NODE_NUM_RANGES.get(node_role, (2, 50))
                    capped = min(target_nodes, hi)
                    recs.append({
                        "priority": 1,
                        "type": "scale_out_nodes",
                        "urgency": urgency,
                        "reason": f"磁盘使用率 {cur}%（{disk_label}）。{timeline}",
                        "analysis": "本地盘容量与机型绑定，无法单独扩磁盘，只能通过增加节点扩展存储。",
                        "tool": "UpdateInstanceNodeNum",
                        "tool_args": {"Type": node_role, "NodeNum": capped},
                        "action": f"节点数 {node_num} → {capped}（目标磁盘使用率 ≤50%）",
                        "capped": capped != target_nodes,
                        "capped_note": (
                            f"理论需 {target_nodes} 节点，受上限 {hi} 约束后取 {capped}"
                            if capped != target_nodes else ""
                        ),
                    })
            else:
                # 云盘：优先原地扩容，目标使用率 ≤ 60%
                raw_target = disk_size * cur / 60.0
                target_disk = int(math.ceil(raw_target / 100.0) * 100)
                target_disk = max(target_disk, disk_size + 100)
                projected = round(cur * disk_size / target_disk, 1)
                recs.append({
                    "priority": 1,
                    "type": "expand_disk",
                    "urgency": urgency,
                    "reason": f"磁盘使用率 {cur}%（{disk_label}）。{timeline}",
                    "analysis": "云硬盘支持原地扩容，无数据搬迁，影响最小，优先选择。",
                    "tool": "UpdateInstanceDiskSize",
                    "tool_args": {"Type": node_role, "DiskSize": target_disk},
                    "action": (
                        f"单节点磁盘 {disk_size}GB → {target_disk}GB"
                        f"（集群总容量 {disk_size * node_num}GB → {target_disk * node_num}GB，"
                        f"扩容后预计使用率 ~{projected}%）"
                    ),
                    "calc": f"{disk_size} × {cur}% / 0.6 = {raw_target:.1f} → 向上取整百位 → {target_disk}",
                    "must_verify": "调用前用 DescribeClusterDiskRange 确认落在 Min/Max 区间",
                    "alternative": "若已达磁盘上限，改用 UpdateInstanceNodeNum 加节点",
                })

    # ---------- 2. CPU ----------
    cpu = metrics.get("CpuUsageMax")
    if cpu and cpu.get("status") != "no_data" and cpu["current"] >= 70:
        pattern = cpu.get("pattern", "normal")
        if pattern == "spike":
            recs.append({
                "priority": 99,
                "type": "monitor_only",
                "urgency": "🟡 趋势观察",
                "reason": f"CPU 当前 {cpu['current']}%，P50={cpu['p50']}%、P95={cpu['p95']}%，呈偶发打高模式",
                "analysis": "偶发打高扩容无效（扩容解决不了查询/写入模式问题）。",
                "tool": None,
                "action": "转 tencent-es-diagnose 分析尖刺时段的大查询/批量写入/merge/snapshot",
            })
        elif pattern == "sustained":
            target = CPU_UPGRADE_MAP.get(node_type, "")
            if target:
                recs.append({
                    "priority": 2,
                    "type": "upgrade_spec_unsupported",
                    "urgency": "🔴 紧急" if cpu["p50"] >= 85 else "🟠 建议",
                    "reason": f"CPU 持续高负载：P50={cpu['p50']}%、P95={cpu['p95']}%",
                    "analysis": "持续高 CPU 影响查询响应与写入吞吐，建议纵向升配增加核数。",
                    "tool": None,
                    "unsupported": True,
                    "action": f"推荐规格 {node_type} → {target}",
                    "console_hint": "⛔ 规格升配暂无 MCP tool，请在控制台执行：节点配置 → 调整配置",
                })
            else:
                lo, hi = NODE_NUM_RANGES.get(node_role, (2, 50))
                recs.append({
                    "priority": 3,
                    "type": "scale_out_nodes",
                    "urgency": "🟠 建议",
                    "reason": f"CPU 持续高负载：P50={cpu['p50']}%，当前规格 {node_type} 无更高 CPU 档位",
                    "analysis": "无法纵向升配，需横向扩容分散 CPU 压力。",
                    "tool": "UpdateInstanceNodeNum",
                    "tool_args": {"Type": node_role, "NodeNum": min(node_num + 2, hi)},
                    "action": f"节点数 {node_num} → {min(node_num + 2, hi)}",
                })
        else:
            # pattern == normal 但当前值已越线（如刚开始打高、或末点恰为尖刺）。
            # ⚠️ 修复 v3 缺陷：此分支原本什么都不加，导致 status=critical
            #    却输出「✅ 健康」的自相矛盾结论。
            recs.append({
                "priority": 97,
                "type": "monitor_only",
                "urgency": "🟠 需关注" if cpu["status"] == "critical" else "🟡 趋势观察",
                "reason": (
                    f"CPU 当前 {cpu['current']}% 已越线，"
                    f"但 P50={cpu['p50']}%、P95={cpu['p95']}% 尚未构成持续或明显偶发模式"
                ),
                "analysis": "可能是刚开始出现压力，或分析窗口末端恰为尖刺。"
                            "样本尚不足以支撑扩容决策。",
                "tool": None,
                "action": "建议缩短统计粒度（Period=60）或延长分析周期复查；"
                          "若持续越线则转 tencent-es-diagnose 排查",
            })

    # ---------- 3. JVM ----------
    jvm = metrics.get("JvmMemUsageMax")
    if jvm and jvm.get("status") != "no_data" and jvm["current"] >= 75:
        target = MEM_UPGRADE_MAP.get(node_type, "")
        cur = jvm["current"]
        urgency = "🔴 紧急" if cur >= 95 else ("🟠 危险" if cur >= 85 else "🟡 预警")
        rec = {
            "priority": 2,
            "type": "upgrade_spec_unsupported",
            "urgency": urgency,
            "reason": f"JVM 内存 {cur}%（P50={jvm['p50']}%），存在 GC 压力"
                      + ("和熔断/OOM 风险" if cur >= 85 else ""),
            "analysis": "先排查 fielddata/聚合/segment（转 tencent-es-diagnose）；"
                        "确认是规模增长则升配增加内存（堆内存 = 节点内存 50%，升配后自动增大）。",
            "tool": None,
            "unsupported": True,
            "console_hint": "⛔ 规格升配暂无 MCP tool，请在控制台执行：节点配置 → 调整配置",
        }
        if target:
            rec["action"] = f"推荐规格 {node_type} → {target}"
        else:
            lo, hi = NODE_NUM_RANGES.get(node_role, (2, 50))
            rec.update({
                "priority": 3,
                "type": "scale_out_nodes",
                "tool": "UpdateInstanceNodeNum",
                "tool_args": {"Type": node_role, "NodeNum": min(node_num + 2, hi)},
                "unsupported": False,
                "action": f"当前规格 {node_type} 已是最高内存档位，改为横向扩容 {node_num} → {min(node_num + 2, hi)}",
                "console_hint": "",
            })
        recs.append(rec)

    # ---------- 4. QPS 增长 ----------
    for m, label in (("IndexSpeed", "写入"), ("SearchCompletedSpeed", "查询")):
        q = metrics.get(m)
        if q and q.get("status") != "no_data":
            g = q["monthly_growth_rate_pct"]
            if g > 30:
                lo, hi = NODE_NUM_RANGES.get(node_role, (2, 50))
                recs.append({
                    "priority": 4,
                    "type": "scale_out_nodes",
                    "urgency": "🟡 趋势预警",
                    "reason": f"{label} QPS 月增长 {g}%（当前 {q['current']} {q['unit']}）",
                    "analysis": f"{label} QPS 持续增长会带来磁盘与 CPU 压力，建议提前规划横向扩容预留容量。",
                    "tool": "UpdateInstanceNodeNum",
                    "tool_args": {"Type": node_role, "NodeNum": min(node_num + 2, hi)},
                    "action": f"建议提前扩容：节点数 {node_num} → {min(node_num + 2, hi)}",
                })

    # ---------- 5. 查询延迟（仅参考） ----------
    lat = metrics.get("SearchLatencyAvg")
    if lat and lat.get("status") != "no_data" and lat["current"] >= 200:
        recs.append({
            "priority": 98,
            "type": "monitor_only",
            "urgency": "🔴 紧急" if lat["current"] >= 500 else "🟡 趋势观察",
            "reason": f"查询平均延迟 {lat['current']}ms 超过预警阈值 200ms",
            "analysis": "延迟根因（wildcard/深度分页/text 聚合等）属 tencent-es-diagnose 职责，"
                        "本流程不据此单独推荐扩容。",
            "tool": None,
            "action": "若 CPU/JVM 同时高，参考上方建议；否则转 tencent-es-diagnose 排查查询写法",
        })

    if not recs:
        # ⚠️ 修复 v3 缺陷：不能仅因「没生成建议」就断言健康。
        #    必须交叉核对各指标 status，避免掩盖 warn/critical 状态。
        breached = [
            f"{m['label']}={m['current']}{m['unit']}（{m['status']}）"
            for m in metrics.values()
            if m.get("status") in ("warn", "critical")
        ]
        if breached:
            recs.append({
                "priority": 96,
                "type": "monitor_only",
                "urgency": "🟡 需关注",
                "reason": "存在越线指标但未达本流程的扩容触发条件：" + "；".join(breached),
                "analysis": "扩容触发需同时满足水位与趋势/模式条件，当前样本不足以支撑扩容决策。",
                "tool": None,
                "action": "建议延长分析周期复查；若为 CPU/JVM/延迟类问题，"
                          "转 tencent-es-diagnose 做根因分析",
            })
        else:
            recs.append({
                "priority": 100,
                "type": "healthy",
                "urgency": "✅ 健康",
                "reason": "各项资源使用率均在正常范围",
                "analysis": "",
                "tool": None,
                "action": "建议继续监控，30 天后重新评估",
            })

    recs.sort(key=lambda r: r["priority"])

    # 单次单一变更提醒
    actionable = [r for r in recs if r.get("tool")]
    if len(actionable) > 1:
        for i, r in enumerate(actionable):
            if i > 0:
                r["serial_note"] = (
                    "⚠️ 腾讯云不允许同时变更多种类型，"
                    f"需等前一项（{actionable[0]['tool']}）完成后再执行"
                )
    return recs


def main():
    parser = argparse.ArgumentParser(
        description="ES 容量预测计算（零云 API 调用，输入为 GetMonitorData 返回的 JSON）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
输入：stdin 接收 GetMonitorData MCP tool 的返回 JSON
      支持单个响应、多个响应组成的数组、或已剥掉 Response 外层的对象

示例：
  # 单指标
  cat disk.json | python3 scripts/forecast_calc.py --node-num 3 --disk-size 300 --disk-type CLOUD_SSD

  # 多指标 + 完整集群上下文
  cat metrics.json | python3 scripts/forecast_calc.py \\
      --node-num 3 --disk-size 300 --disk-type CLOUD_SSD \\
      --node-type ES.S1.LARGE16 --node-role hotData

说明：
  - 本脚本不调用任何腾讯云 API，不读取凭证，不发起网络请求
  - 自动剔除云监控 -2 / -1 哨兵值
  - 输出的 tool_args 是【目标值】，可直接用于 MCP tool 入参
        """,
    )
    parser.add_argument("--node-num", type=int, default=0,
                        help="目标节点类型的当前节点数（来自 DescribeInstances 的 NodeInfoList）")
    parser.add_argument("--disk-size", type=int, default=0,
                        help="目标节点类型的当前单节点磁盘 GB（来自 NodeInfoList）")
    parser.add_argument("--disk-type", default="",
                        help="磁盘类型：LOCAL_SSD / CLOUD_PREMIUM / CLOUD_SSD / CLOUD_HSSD")
    parser.add_argument("--node-type", default="",
                        help="当前节点规格，如 ES.S1.LARGE16（用于升配推荐）")
    parser.add_argument("--node-role", default="hotData",
                        choices=["hotData", "warmData", "dedicatedMaster",
                                 "dedicatedCoordinating", "dedicatedMl"],
                        help="目标节点类型，默认 hotData")
    parser.add_argument("--instance-id", default="",
                        help="多实例批量返回时，只分析该实例")
    parser.add_argument("--output", choices=["json", "text"], default="json")

    args = parser.parse_args()

    raw = sys.stdin.read().strip()
    if not raw:
        error_exit("stdin 无输入。请将 GetMonitorData 的返回 JSON 通过管道传入。")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        error_exit(f"stdin 不是合法 JSON：{e}")

    bundles = parse_metrics(payload, args.instance_id)
    if not bundles:
        error_exit(
            "未能从输入中解析出任何指标数据。"
            "请确认传入的是 GetMonitorData 的返回（应含 MetricName 与 DataPoints 字段）。"
        )

    metrics = {m: analyze_metric(m, b) for m, b in bundles.items()}
    recs = build_recommendations(
        metrics, args.node_num, args.disk_size,
        args.disk_type, args.node_type, args.node_role,
    )

    result = {
        "cluster_context": {
            "node_role": args.node_role,
            "node_num": args.node_num,
            "disk_size_per_node_gb": args.disk_size,
            "total_storage_gb": args.disk_size * args.node_num if args.node_num else 0,
            "disk_type": args.disk_type,
            "disk_type_label": DISK_TYPE_LABELS.get(args.disk_type, args.disk_type or "未提供"),
            "can_expand_disk": args.disk_type in CLOUD_DISK_TYPES,
            "node_type": args.node_type,
        },
        "metrics": metrics,
        "recommendations": recs,
        "notes": [
            "本脚本零云 API 调用，仅做确定性数值计算",
            "已剔除云监控 -2 / -1 哨兵值",
            "外推基准为最后一个有效数据点时间（非当前时间），避免历史区间外推失真",
            "recommendations[].tool_args 中的值均为【目标值】，可直接用于 MCP tool 入参",
            "变更仍需向用户展示详情并获得明确确认后才可执行",
        ],
    }

    if args.output == "text":
        ctx = result["cluster_context"]
        print(f"集群上下文：{ctx['node_role']} × {ctx['node_num']} 节点，"
              f"单节点磁盘 {ctx['disk_size_per_node_gb']}GB，{ctx['disk_type_label']}")
        print("\n── 指标统计 ──")
        for m in metrics.values():
            if m.get("status") == "no_data":
                print(f"{m['label']}: 无有效数据")
                continue
            dw = m["days_to_critical"].get("days")
            print(f"{m['label']}: 当前={m['current']}{m['unit']} "
                  f"P50={m['p50']} P95={m['p95']} 趋势={m['trend']} "
                  f"达危险线={'%.0f 天' % dw if dw else m['days_to_critical']['note']} "
                  f"[有效 {m['valid_points']}/{m['raw_points']} 点]")
        print("\n── 建议 ──")
        for r in recs:
            print(f"{r['urgency']} {r['reason']}")
            print(f"  → {r['action']}")
            if r.get("tool"):
                print(f"  Tool: {r['tool']}({json.dumps(r['tool_args'], ensure_ascii=False)})")
            if r.get("console_hint"):
                print(f"  {r['console_hint']}")
            if r.get("serial_note"):
                print(f"  {r['serial_note']}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
