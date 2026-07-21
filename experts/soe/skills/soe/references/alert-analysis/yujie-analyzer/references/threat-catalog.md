# 御界威胁场景知识库 (NTA / NDR / 御界)

> 基于 ATT&CK + 实际数据观察整理 (主要参考 esSearch_20260706145614.xlsx 御界样本).

## 一、C2 Beacon (T1071 / T1095 / T1572)

### 1.1 触发信号

| 字段 | 期望模式 | 备注 |
|---|---|---|
| `flow_stats.bytes_toclient` | == 0 (单向流) | **强信号**: 客户端不发包, 典型 Beacon |
| `flow_stats.bytes_toserver` | 小 (几十~几百字节) | 周期性心跳 |
| `app_proto` | "failed" 或 "http"/"https" 但 payload 异常 | |
| `protocol` / `dst_port` | 任意 | C2 协议多样 |
| 间隔规律 | (L1 二期) | 需要历史聚合 |

### 1.2 ATT&CK 映射

- T1071 Application Layer Protocol
- T1071.001 Web Protocols (HTTP/HTTPS)
- T1071.004 DNS
- T1095 Non-Application Layer Protocol
- T1572 Protocol Tunneling

### 1.3 判定规则 (L1 v0.1)

```python
def is_c2_beacon(parsed, flow_stats):
    if not flow_stats:
        return False
    bytes_to_server = flow_stats.get("bytes_toserver", 0)
    bytes_to_client = flow_stats.get("bytes_toclient", 0)
    pkts_to_server = flow_stats.get("pkts_toserver", 0)
    pkts_to_client = flow_stats.get("pkts_toclient", 0)

    # 强信号: 单向流 + 多次请求
    if bytes_to_client == 0 and pkts_to_client == 0 and bytes_to_server > 0:
        return True, "单向流 (bytes_toclient=0), 符合 Beacon 特征"
    return False, None
```

### 1.4 处置建议

- [ ] 拉取此 real_attacker_ip / real_victim_ip 在御界的历史告警
- [ ] 关联主机安全 (cwp-analyzer): 受害 IP 在 cwp 是否有反弹 shell / 异常进程
- [ ] 隔离受害主机
- [ ] 阻断到 real_attacker_ip 的所有流量

## 二、隧道 / 代理 (T1572 / T1090)

### 2.1 触发信号

| 子场景 | 字段 | 模式 |
|---|---|---|
| WireGuard | `dst_port` | 51820 (默认端口) |
| OpenVPN | `dst_port` | 1194 (默认) / 443 (伪装) |
| IPsec/IKE | `dst_port` | 500 / 4500 |
| GRE 隧道 | `packet_header.outer.protocol` | 47 (GRE) |
| IPIP 隧道 | `packet_header.outer.protocol` | 4 (IP-in-IP) |
| 跨 VPC 封装 | `encapsulation.gre.vpcid` | 不同 vpcid (跨 VPC) |
| SOCKS 代理 | `dst_port` | 1080 |
| HTTP 代理 | `dst_port` | 8080 / 3128 |

### 2.2 ATT&CK 映射

- T1572 Protocol Tunneling
- T1090 Proxy
- T1090.001 Internal Proxy
- T1090.002 External Proxy
- T1090.004 Domain Fronting

### 2.3 判定规则

```python
TUNNEL_PORTS = {
    51820: ("WireGuard", "T1572"),
    1194: ("OpenVPN", "T1572"),
    1723: ("PPTP", "T1572"),
    500: ("IPsec IKE", "T1572"),
    4500: ("IPsec NAT-T", "T1572"),
    1080: ("SOCKS", "T1090.001"),
    3128: ("HTTP Proxy", "T1090.001"),
    8080: ("HTTP Proxy (alt)", "T1090.001"),
}
```

### 2.4 处置建议

- [ ] 确认业务是否合法使用该端口 (很多公司用 WireGuard 远程办公)
- [ ] 非法: 阻断端口 + 隔离主机
- [ ] 拉历史: 受害 IP 是否有其他隧道 / 代理告警
- [ ] 关联主机安全: 受害 IP 的进程 / 命令 (可能有 WireGuard 客户端进程)

## 三、横向移动 (T1021 / T1210)

### 3.1 触发信号

| 字段 | 模式 | 备注 |
|---|---|---|
| `dst_port` | 445 (SMB) / 3389 (RDP) / 22 (SSH) / 23 (Telnet) | **需多个 dst_port, 单事件无法判定** |
| `src_ip` / `real_attacker_ip` | 内部 IP | 内网横向 |
| 漏洞 EXP 特征 | Suricata signature 命中 MS17-010 / Log4j / etc | 已在 `parsed.alert.signature` |

### 3.2 ATT&CK 映射

- T1021 Remote Services
- T1021.001 RDP
- T1021.002 SMB
- T1021.004 SSH
- T1210 Exploitation of Remote Services

### 3.3 判定规则 (L1 v0.1 弱信号)

```python
LATERAL_PORTS = {22, 23, 135, 139, 445, 3389, 5900}

def is_lateral_movement_weak(parsed):
    dst_port = parsed.get("dst_port")
    src_ip = parsed.get("src_ip") or ""
    real_attacker = parsed.get("real_attacker_ip") or src_ip
    if dst_port in LATERAL_PORTS and is_internal_ip(real_attacker):
        return True, "内网横向移动弱信号"
    return False, None
```

### 3.4 处置建议

- [ ] L2 聚合: 同一 real_attacker_ip 短时间多 dst_port → 端口扫描
- [ ] 隔离源主机
- [ ] 关联主机安全: 源主机的进程 / 命令

## 四、数据外传 (T1567 / T1041)

### 4.1 触发信号

| 字段 | 模式 |
|---|---|
| `flow_stats.bytes_toserver` | 大 (>1MB) |
| `dst_ip` / `real_attacker_ip` | 跨境 IP |
| `app_proto` | http/https/ftp/dns-tunnel |

### 4.2 ATT&CK 映射

- T1567 Exfiltration Over Web Service
- T1567.002 Exfiltration to Cloud Storage
- T1041 Exfiltration Over C2 Channel
- T1048 Exfiltration Over Alternative Protocol

### 4.3 处置建议

- [ ] 阻断外联 IP
- [ ] 隔离主机
- [ ] 拉主机层 (cwp) 的对应事件

## 五、变更记录

| 日期 | 变更 | 原因 |
|---|---|---|
| 2026-07-06 | 初版 (4 个核心场景) | 基于 esSearch_20260706145614.xlsx 实际数据 |
