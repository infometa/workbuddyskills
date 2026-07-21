---
name: yujie-analyzer
version: 1.0.0
triggers:
  - 御界
  - NDR
  - NTA
  - C2通信
  - 高级威胁检测
description: |
  腾讯御界 (高级威胁检测 / NDR / NTA) 告警 L1 分析 skill

  消费 L0 适配层 (soc-alert-pipeline) 输出的 parsed 字段,
  基于御界威胁场景知识库 (C2 Beacon / 隧道代理 / 横向移动 / 数据外传), 产出:
    - NAT 还原 (real_attacker_ip / real_victim_ip)
    - 协议识别降级 (app_proto="failed" 时基于端口+特征推断)
    - 威胁判定 (TTP / ATT&CK 映射)
    - 处置建议
    - 标准化案例文档

  适用场景:
  - 单条御界事件的深度分析
  - 流量告警中 NAT 链还原
  - 联调: 御界 ↔ 主机安全 (L2 消费 L1 输出)

  不适用:
  - raw_log 解析 (用 soc-alert-pipeline)
  - 跨产品关联 (用 L2, 暂未实现)
---

# yujie-analyzer (L1 御界)

## 一、定位

L1 产品分析 skill, 在 L0 适配层之上:

```
SOC 导出 xlsx (御界告警)
      ↓
soc-alert-pipeline (L0)  →  parsed dict (含 NAT 还原 / packet 解析)
      ↓
yujie-analyzer (L1, 本 skill)  →  案例文档 + 威胁判定
      ↓
L2 关联 (soc-correlation, 暂未实现)
```

## 二、与 cwp-analyzer 的差异

| 维度 | cwp-analyzer | yujie-analyzer |
|---|---|---|
| 数据视角 | 主机层 (process/cmd/user) | 流量层 (5 元组 / 协议 / 流统计) |
| 核心还原 | (无 NAT) | **NAT 还原 (real_attacker_ip / real_victim_ip)** |
| 协议识别 | (无) | **DPI 降级 (app_proto=failed 时基于端口+特征)** |
| 关键信号 | 进程行为 | 流统计 (bytes/seconds) + 协议特征 |
| 关联对象 | 主机 (host_ip) | 攻击者 IP (real_attacker_ip) |

## 三、当前覆盖的威胁场景

| 场景 | TTP | 关键信号 | detector |
|---|---|---|---|
| C2 Beacon | T1071 / T1095 | bytes_toclient=0 / 固定间隔 / 失败协议 | `ttp_detectors/c2_beacon.py` |
| 隧道/代理 | T1572 / T1090 | WireGuard/IPSec/GRE / 端口 51820 等 | `ttp_detectors/tunnel_detection.py` |
| 横向移动 | T1021 / T1210 | 短时多 dst_port / 漏洞 EXP 特征 | `ttp_detectors/lateral_movement.py` |
| 数据外传 | T1567 / T1041 | 大 bytes / 异常外联 / 已知矿池 | `ttp_detectors/exfiltration.py` |

详见 `references/threat-catalog.md`。

## 四、快速开始

```bash
# 1. L0 跑一遍
python3 ../soc-alert-pipeline/scripts/l0_parse.py \
    <xlsx_path> --out /tmp/yujie_l0.jsonl

# 2. L1 分析
python3 scripts/l1_yujie_analyze.py /tmp/yujie_l0.jsonl --out cases/

# 3. 产出: cases/yujie_*.md
ls cases/ | head
```

## 五、NAT 还原 (L1 关键能力)

`scripts/nat_resolve.py` 提供:

```python
from nat_resolve import resolve_nat_chain

result = resolve_nat_chain(parsed)
# {
#   "real_attacker_ip": "123.103.18.70",  # 公网
#   "real_victim_ip": "172.16.114.119",
#   "ip_discrepancy": True,                # 与 OCSF 透出 IP 不同
#   "nat_chain": ["gre"],                  # 封装链
#   "trust_level": "high",                 # 还原可信度
#   "rationale": "...",
# }
```

NAT 链类型识别:
- 0 跳: 无 NAT (IP 一致)
- 1 跳: 单层 GRE/IPIP
- 2 跳: GRE + 内层 VPN (典型云上 WireGuard)

详见 `references/nat-encapsulation.md`。

## 六、与 L0 / L2 的接口

**L0 → L1 输入** (`parsed` dict):
```python
{
    "src_ip", "dst_ip", "src_port", "dst_port", "protocol",
    "real_attacker_ip", "real_victim_ip", "ip_discrepancy",  # L0 已填
    "encapsulation": {"gre": ...},
    "src_mac", "dst_mac",
    "app_proto", "rule_id", "rule_name", "score",
    "event_timestamp", "event_timestamp_raw",
    "packet_header": {...},  # 解析后的网络包
    "flow_stats": {...},     # 流统计
    "alert": {...},          # Suricata 规则详情
}
```

**L1 → L2 输出**: 案例文档, 含 `correlation_hints` 段:
```yaml
threat:
  correlation_hints:
    pivot_keys: ["real_attacker_ip", "real_victim_ip"]
    time_window_min: 15
```

## 七、待用户确认项 (TODO)

1. **产品代号**:
   - 当前 PRODUCT="yujie" (拼音)
   - 实际 SOC OCSF 透出 logsource_subtype 是 (待你查文档, 我没看到御界的那份数据有 OCSF logsource_subtype 字段? 待确认)
   - 规则名带 "INTA", 可能是英文缩写 InTA

2. **app_proto="failed" 时的降级规则**:
   - 当前 v0.1: 端口 51820 → WireGuard, 80/443 → HTTP/HTTPS
   - 需要 L1 二期接入更多端口签名

3. **GRE 跨 VPC 的处置建议**:
   - 当前 v0.1: 标"跨 VPC 隐蔽通道"提示
   - 实际可能是合法 VPN, 需要业务侧确认

## 八、变更记录

| 日期 | 变更 | 原因 |
|---|---|---|
| 2026-07-06 | 初版 | L0 跑通后建 L1 |
| TODO | 接入更多 DPI 降级规则 | 等用户提供内部端口签名表 |
