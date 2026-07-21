# 主机安全威胁 → ATT&CK 映射表

| 威胁场景 | 主 TTP | 副 TTP | 阶段 |
|---|---|---|---|
| 暴力破解 (SSH/RDP) | T1110 Brute Force | T1078 Valid Accounts | Initial Access |
| 反弹 Shell (bash) | T1059.004 Unix Shell | T1071.001 Web Protocols | Execution |
| 反弹 Shell (python) | T1059.006 Python | T1071.001 Web Protocols | Execution |
| 反弹 Shell (nc) | T1059.004 Unix Shell | T1095 Non-App Protocol | Execution |
| Crontab 植入 | T1053.003 Cron | T1543 System Service | Persistence |
| SSH authorized_keys | T1098.004 SSH Authorized Keys | T1078 Valid Accounts | Persistence |
| Systemd 服务植入 | T1543.002 Systemd Service | T1574 Hijack Execution Flow | Persistence |
| SUID 提权 | T1548.001 Setuid and Setgid | T1068 Exploitation for Privilege Escalation | Privilege Escalation |
| SSH 横向 | T1021.004 SSH | T1570 Lateral Tool Transfer | Lateral Movement |
| SMB 横向 | T1021.002 SMB | T1570 Lateral Tool Transfer | Lateral Movement |
| Mimikatz / 凭据窃取 | T1003 OS Credential Dumping | T1555 Credentials from Password Stores | Credential Access |
| 挖矿 | T1496 Resource Hijacking | T1059 Command and Scripting Interpreter | Impact |
| Webshell | T1505.003 Web Shell | T1059 Command and Scripting Interpreter | Persistence |
| 数据外传 | T1567 Exfiltration Over Web Service | T1041 Exfiltration Over C2 | Exfiltration |

## 引用

- ATT&CK v14: https://attack.mitre.org/
- 子技术 ID (T1059.004 等) 参考 https://attack.mitre.org/techniques/
