# 御界威胁 → ATT&CK 映射表

| 威胁场景 | 主 TTP | 副 TTP | 阶段 |
|---|---|---|---|
| C2 Beacon (HTTP) | T1071.001 Web Protocols | T1095 Non-App Protocol | Command and Control |
| C2 Beacon (DNS) | T1071.004 DNS | T1572 Protocol Tunneling | Command and Control |
| C2 Beacon (单向流) | T1095 Non-App Protocol | T1071 Application Layer Protocol | Command and Control |
| WireGuard 隧道 | T1572 Protocol Tunneling | T1090.004 Domain Fronting | Command and Control |
| OpenVPN / IPsec 隧道 | T1572 Protocol Tunneling | T1573 Encrypted Channel | Command and Control |
| GRE / IPIP 跨 VPC 封装 | T1572 Protocol Tunneling | T1090.002 External Proxy | Command and Control |
| SOCKS 代理 | T1090.001 Internal Proxy | T1572 Protocol Tunneling | Command and Control |
| HTTP 代理 | T1090.001 Internal Proxy | T1090.002 External Proxy | Command and Control |
| SMB 横向 | T1021.002 SMB | T1210 Exploitation of Remote Services | Lateral Movement |
| RDP 横向 | T1021.001 RDP | T1021 Remote Services | Lateral Movement |
| SSH 横向 | T1021.004 SSH | T1570 Lateral Tool Transfer | Lateral Movement |
| SMB 漏洞利用 (MS17-010) | T1210 Exploitation of Remote Services | T1021.002 SMB | Lateral Movement |
| Web 服务漏洞 (Log4j) | T1190 Exploit Public-Facing Application | T1059 Command and Scripting Interpreter | Initial Access |
| 端口扫描 | T1046 Network Service Discovery | T1018 Remote System Discovery | Discovery |
| 数据外传 (HTTP) | T1567 Exfiltration Over Web Service | T1041 Exfiltration Over C2 | Exfiltration |
| 数据外传 (云存储) | T1567.002 Exfiltration to Cloud Storage | T1567 Exfiltration Over Web Service | Exfiltration |
| 跨境异常外联 | T1071 Application Layer Protocol | T1567 Exfiltration | Command and Control |
| 挖矿池连接 | T1496 Resource Hijacking | T1071.001 Web Protocols | Impact |

## 引用

- ATT&CK v14: https://attack.mitre.org/
- 子技术 ID 参考 https://attack.mitre.org/techniques/
