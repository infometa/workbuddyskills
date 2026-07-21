# 统一事件 Schema (草案 v0.1)

> ⚠️ 这是 L0 输出 + L1 输入的共同 schema, **v0.1 草案**, 字段会随 L1 迭代调整。
> 维护原则: L1 输出必须能填满"必填字段", 可选字段尽量填, 缺值时用 `null` 而不是省略。

## 一、顶层结构

```yaml
event:
  # === 元数据 (必填) ===
  id: string                          # 事件唯一 ID, L1 生成 (格式: {product}_{time}_{hash})
  product: enum                       # 产品大类 (必填)
  vendor_product: string              # 厂商产品代号 (必填, 取自 base.py PRODUCT)
  schema_version: "0.1"               # schema 版本
  
  # === 时间 (必填) ===
  source_event_time: ISO8601|null     # 事件原始时间 (L0 从 raw_log 解析, 失败为 null)
  ingested_at: ISO8601                # L0 处理时间 (L0 自己填)
  
  # === 网络 (网络事件必填, 主机事件部分填) ===
  network: object|null                # 见 § 二
  
  # === 主机/资产 (主机事件必填) ===
  asset: object|null                  # 见 § 三
  
  # === 检测 (必填) ===
  detection: object                   # 见 § 四
  
  # === 威胁评估 (L1 输出, L0 不填) ===
  threat: object|null                 # 见 § 五
  
  # === 原始数据 (必填, 用于追溯) ===
  raw: object                         # 见 § 六
```

## 二、network 字段

```yaml
network:
  # OCSF 透出 (必填, NAT 前)
  src_ip: string
  src_port: int|null
  dst_ip: string
  dst_port: int|null
  protocol: enum                      # tcp / udp / icmp / gre / ipip / ...
  
  # NAT 还原 (御界等流量类必填, 主机类可填 null)
  real_attacker_ip: string|null       # 真实攻击源
  real_victim_ip: string|null         # 真实受害 IP
  ip_discrepancy: bool                # 真实 IP ≠ OCSF IP 时为 true
  
  # 封装链
  encapsulation:
    gre: object|null                  # {src, dst, vpcid, ...}
    vxlan: object|null
    other: object|null
  
  # MAC (御界已能解析, 主机类为 null)
  src_mac: string|null
  dst_mac: string|null
  
  # 协议识别
  app_proto: string|null              # http / dns / wireguard / failed / ...
  
  # 网络包解析结果 (御界有 packet hex 时填)
  packet_header: object|null          # {outer, inner, transport, payload_meta}
  
  # 流统计 (御界单包流)
  flow_stats: object|null             # {bytes_toserver, bytes_toclient, pkts_*, start, end}
```

## 三、asset 字段

```yaml
asset:
  # 资产身份
  asset_id: string|null               # CMDB 资产 ID (当前没接入 CMDB, 填 null)
  host_ip: string|null                # 主机 IP (御界/主机类都有)
  hostname: string|null               # 主机名 (主机类从 OCSF 透出)
  
  # 资产属性 (L1 接入 CMDB 后填, 当前为 null)
  asset_type: enum|null               # server / workstation / container / vm / ...
  business_system: string|null        # 所属业务系统
  owner: string|null                  # 责任人
  importance: enum|null               # critical / high / medium / low
```

## 四、detection 字段

```yaml
detection:
  rule_id: string                     # 告警规则 ID
  rule_name: string                   # 告警规则名
  severity: enum                      # critical / high / medium / low / informational
  confidence: int|null                # 0-100, 产品原始置信度
  category: string                    # 例: Tunneling / Lateral Movement / ...
  subcategory: string|null
  
  # OCSF 透出的产品分类 (保留供 L2 聚合)
  ocsf:
    logsource_subtype: string         # yujie / cwp / ...
    data_type: string                 # 例: Network Connection
    data_subtype: string
```

## 五、threat 字段 (L1 输出)

```yaml
threat:
  # 威胁判定
  threat_type: string|null            # 例: "C2 Beacon" / "反弹 Shell" / ...
  confidence: float|null              # L1 计算的 0-1 置信度
  
  # ATT&CK 映射
  kill_chain_phase: string|null       # reconnaissance / weaponization / delivery / ...
  mitre_attack: list[string]          # ATT&CK Technique ID, 例: ["T1572", "T1090"]
  
  # IOC 列表
  iocs:
    ips: list[string]
    domains: list[string]
    file_hashes: list[string]
    process: list[string]
    
  # 关联建议 (L1 产出, L2 消费)
  correlation_hints:
    pivot_keys: list[string]          # 建议 L2 用这些键做关联, 例: ["real_attacker_ip", "host_ip"]
    time_window_min: int              # 建议的时间窗 (分钟)
```

## 六、raw 字段

```yaml
raw:
  # OCSF 透出字段 (除上面已结构化外的其他列)
  ocsf_extra: object
  
  # 原始日志 (用于追溯, 大字符串可换文件路径)
  raw_log: string
  
  # L0 解析状态
  parse_status: enum                  # ok / partial / failed
  parse_errors: list[string]          # 字段级错误, 不阻断
  parser_version: string              # 解析器版本
```

## 七、字段填充责任分工

| 字段 | L0 填 | L1 填 | L2 填 |
|---|---|---|---|
| `event.id` | | ✓ | |
| `event.source_event_time` | ✓ | 校正 | |
| `event.network.src/dst_ip` | ✓ | | |
| `event.network.real_attacker/victim_ip` | ✓ | 校正 | |
| `event.detection.*` | ✓ (透出) | 增强 | |
| `event.threat.*` | | ✓ | 增强 |
| `event.threat.mitre_attack` | | ✓ | |
| `event.threat.iocs` | 部分 (IP) | ✓ (完善) | |
| `event.threat.correlation_hints` | | ✓ | 消费 |
| `event.raw.raw_log` | ✓ | | |
| `asset.*` (CMDB 相关) | | | 后续接入 CMDB 填 |

## 八、最小示例

### 御界事件 (最小有效事件)

```json
{
  "event": {
    "id": "yujie_20260706T143022_a3f9",
    "product": "NTA",
    "vendor_product": "yujie",
    "schema_version": "0.1",
    "source_event_time": "2026-07-06T14:30:22+08:00",
    "ingested_at": "2026-07-06T15:00:00+08:00",
    "network": {
      "src_ip": "10.0.0.4",
      "src_port": 51820,
      "dst_ip": "172.16.114.118",
      "dst_port": 51820,
      "protocol": "udp",
      "real_attacker_ip": "123.103.18.70",
      "real_victim_ip": "172.16.114.119",
      "ip_discrepancy": true,
      "encapsulation": {
        "gre": {"src": "192.168.233.1", "dst": "192.168.233.2", "vpcid": 66700}
      },
      "src_mac": "00:0a:f7:12:34:56",
      "dst_mac": "00:0a:f7:65:43:21",
      "app_proto": "failed",
      "packet_header": {
        "outer": {"version": 4, "src_ip": "10.16.39.43", "dst_ip": "10.16.1.168", "protocol": 47},
        "inner": {"version": 4, "src_ip": "10.0.0.4", "dst_ip": "10.16.39.43", "protocol": 17},
        "transport": {"sport": 51820, "dport": 51820, "length": 96}
      },
      "flow_stats": {
        "bytes_toserver": 192, "bytes_toclient": 0,
        "pkts_toserver": 1, "pkts_toclient": 0,
        "start": "2026-07-06T14:30:22", "end": "2026-07-06T14:30:22"
      }
    },
    "asset": {
      "host_ip": "172.16.114.119"
    },
    "detection": {
      "rule_id": "2017001",
      "rule_name": "WireGuard隧道通信",
      "severity": "high",
      "confidence": 85,
      "category": "Tunneling",
      "ocsf": {
        "logsource_subtype": "yujie",
        "data_type": "Network Connection",
        "data_subtype": "VPN"
      }
    },
    "threat": null,
    "raw": {
      "raw_log": "{...}",
      "parse_status": "ok",
      "parse_errors": [],
      "parser_version": "0.1.0"
    }
  }
}
```

### 主机安全事件 (最小有效事件)

```json
{
  "event": {
    "id": "cwp_20260705T153022_b8c1",
    "product": "HOST_SECURITY",
    "vendor_product": "cwp",
    "schema_version": "0.1",
    "source_event_time": "2026-07-05T15:30:22+08:00",
    "ingested_at": "2026-07-06T15:00:00+08:00",
    "network": {
      "src_ip": "203.0.113.45",
      "src_port": 51234,
      "dst_ip": "10.10.1.100",
      "dst_port": 22,
      "protocol": "tcp"
    },
    "asset": {
      "host_ip": "10.10.1.100",
      "hostname": "web-prod-01"
    },
    "detection": {
      "rule_id": "ssh_bruteforce_001",
      "rule_name": "SSH暴力破解",
      "severity": "high",
      "confidence": 90,
      "category": "Credential Access",
      "ocsf": {
        "logsource_subtype": "cwp",
        "data_type": "Authentication",
        "data_subtype": "SSH Login"
      }
    },
    "threat": null,
    "raw": {
      "raw_log": "src_ip=203.0.113.45&src_port=51234&...",
      "parse_status": "ok",
      "parse_errors": [],
      "parser_version": "0.1.0"
    }
  }
}
```

## 九、变更记录

| 版本 | 变更 | 原因 |
|---|---|---|
| 0.1 | 初版 | 基于御界 + 主机安全两份实际数据 |
