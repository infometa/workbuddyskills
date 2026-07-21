# NAT 还原与封装链识别 (L1 御界核心能力)

## 一、为什么需要 NAT 还原

OCSF 透出的 `src_ip / dst_ip` 是网络层的"观测 IP", 但实际攻击者和受害者可能隐藏在 NAT / 代理 / 隧道之后.

实际样本 (esSearch_20260706145614.xlsx):
- OCSF 透出: `src=10.0.0.4:51820 → dst=172.16.114.118:51820` (内网 IP, 看起来像内部 VPN)
- raw_log 真实: `attacker=123.103.18.70 (公网), victim=172.16.114.119` (受害主机)
- 性质从"内网违规 VPN" 升级为"**公网攻击者穿越云上 NAT 入侵**"

## 二、NAT 还原算法

L0 已经在 `parsed.real_attacker_ip / real_victim_ip` 填了真实 IP, L1 主要做**校验和增强**:

```python
def resolve_nat_chain(parsed):
    src_ip = parsed.get("src_ip")
    dst_ip = parsed.get("dst_ip")
    real_attacker = parsed.get("real_attacker_ip") or src_ip
    real_victim = parsed.get("real_victim_ip") or dst_ip

    # 1. 一致性
    discrepancy = real_attacker != src_ip or real_victim != dst_ip

    # 2. 封装链
    nat_chain = []
    if parsed.get("encapsulation", {}).get("gre"):
        nat_chain.append("gre")
    if parsed.get("packet_header", {}).get("inner"):
        nat_chain.append("nested_ip")

    # 3. 可信度
    if discrepancy and nat_chain:
        trust = "high"  # 有原始 ext 字段, 可信度高
    elif discrepancy and not nat_chain:
        trust = "medium"  # IP 不一致但没看到封装, 可能是源端 NAT
    else:
        trust = "high"  # 一致, 没 NAT

    return {
        "real_attacker_ip": real_attacker,
        "real_victim_ip": real_victim,
        "ocsf_src_ip": src_ip,
        "ocsf_dst_ip": dst_ip,
        "ip_discrepancy": discrepancy,
        "nat_chain": nat_chain,
        "trust_level": trust,
        "rationale": build_rationale(discrepancy, nat_chain),
    }
```

## 三、典型 NAT 链模式

### 3.1 0 跳: 无 NAT (IP 一致)

```
OCSF:  8.8.8.8 → 1.1.1.1
raw:   8.8.8.8 → 1.1.1.1
判定:  无 NAT, 可能是正常外联或攻击直连
```

### 3.2 1 跳: 云 NAT 网关

```
OCSF:  10.0.0.4 (云内) → 172.16.114.118 (云内)
raw:   123.103.18.70 (公网, 真实攻击者) → 172.16.114.119
判定:  src 端 1 跳 NAT, 攻击者从公网
```

### 3.3 2 跳: GRE 跨 VPC + 内层 VPN

```
OCSF:  10.0.0.4 → 172.16.114.118
packet:  [MAC][外层 IP 10.16.39.43 → 10.16.1.168][GRE][内层 IP 10.0.0.4 → 10.16.39.43][UDP/51820][WireGuard]
raw:    attacker 123.103.18.70 → victim 172.16.114.119
判定:  跨 VPC 隐蔽隧道, 2 跳封装
```

## 四、IP 性质识别

```python
import ipaddress

def classify_ip(ip: str) -> str:
    """识别 IP 性质"""
    if not ip:
        return "unknown"
    try:
        ip_obj = ipaddress.ip_address(ip)
        if ip_obj.is_private:
            return "private"          # 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
        elif ip_obj.is_loopback:
            return "loopback"         # 127.0.0.0/8
        elif ip_obj.is_multicast:
            return "multicast"
        elif ip_obj.is_reserved:
            return "reserved"
        elif ip_obj.is_global:
            return "public"           # 公网 IP
        else:
            return "other"
    except ValueError:
        return "invalid"

def is_internal_ip(ip: str) -> bool:
    return classify_ip(ip) == "private"

def is_external_ip(ip: str) -> bool:
    return classify_ip(ip) == "public"
```

## 五、判定规则: 异常 NAT 模式

| 模式 | 描述 | 威胁评分 |
|---|---|---|
| 公网 IP → 私网 IP (real) | 公网攻击者直连内网 | 高 (+0.3) |
| 私网 IP → 私网 IP 但 dst 是公网 NAT 后 | 内部主机被控外联 | 中 (+0.1) |
| GRE 跨 VPC + 私网 src/dst | 跨 VPC 隐蔽隧道 | 高 (+0.4) |
| 真实 IP 是 RFC1918 但 OCSF 显示是云网关 IP | 云上 NAT, 攻击者在外 | 中 (+0.2) |
| IP 一致且都是私网, 端口合法 | 正常业务流量 | 低 (0) |

## 六、变更记录

| 日期 | 变更 | 原因 |
|---|---|---|
| 2026-07-06 | 初版 | 基于 esSearch_20260706145614.xlsx 御界样本 |
