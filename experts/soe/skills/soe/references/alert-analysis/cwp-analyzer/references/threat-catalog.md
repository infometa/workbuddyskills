# 主机安全威胁场景知识库 (CWP / 云镜)

> 基于 ATT&CK + 实际数据观察整理. 每条威胁给出: 触发信号 / ATT&CK 映射 / 判定规则 / 处置建议.
>
> TODO (等用户接入腾讯云镜官方文档):
> - `status` 字段值映射 (1=成功? 0=失败?)
> - `type` 字段值映射 (jdbc_login / ssh_login / ... 的官方含义)
> - 内部事件 ID (如 202628000009612) 编码规则

## 一、暴力破解 (T1110)

### 1.1 触发信号

| 字段 | 期望模式 | 备注 |
|---|---|---|
| `rule_name` | 含 "登录失败" / "暴力破解" / "brute" | |
| `status` | "0" 或 "1" (失败码, 待确认) | |
| `dst_port` | 22 (SSH) / 3389 (RDP) / 3306 (MySQL) | |
| `count` (在 _raw_kv) | > 1 通常意味着多次尝试 | **关键信号** |
| 时间分布 | 同 src_ip 短时间内多次失败 | L1 二期加: 需要历史聚合 |

### 1.2 ATT&CK 映射

- 主: T1110 Brute Force
- 关联: T1078 Valid Accounts (成功后)
- 关联: T1021 Remote Services (成功后)

### 1.3 判定规则 (L1 v0.1)

```python
def is_brute_force(parsed, raw_kv):
    if "失败" in parsed.get("rule_name", "") or "brute" in parsed.get("rule_name", "").lower():
        count = int(raw_kv.get("count", 1) or 1)
        if count >= 2:
            return True, "high", count
    return False, None, 0
```

### 1.4 处置建议

- [ ] 阻断 src_ip (CWP / 安全组 / WAF)
- [ ] 检查 dst_ip 的 sshd 登录日志 (`lastb` / `/var/log/secure`)
- [ ] 强制目标账号改密
- [ ] 启用 fail2ban / 腾讯云镜自带防护
- [ ] 同 src_ip 历史告警聚合 (L1 二期 / L2 消费)

## 二、反弹 Shell (T1059.004)

### 2.1 触发信号

| 字段 | 期望模式 |
|---|---|
| `cmd` | 含 `/dev/tcp/` / `bash -i` / `nc -e` / `python -c 'import socket'` |
| `process` | bash / sh / python / perl / nc |
| `user` | 非 root (常见) / 任何用户都可能 |

### 2.2 ATT&CK 映射

- 主: T1059.004 Unix Shell
- 关联: T1071.001 Application Layer Protocol: Web
- 关联: T1095 Non-Application Layer Protocol

### 2.3 判定规则 (L1 v0.1)

```python
import re
REVERSE_SHELL_PATTERNS = [
    r"bash\s+-i\s+>&\s*/dev/tcp/",       # bash 内置反弹
    r"/dev/tcp/[^\s]+",                   # bash /dev/tcp
    r"nc\s+-e\s+/bin/(ba)?sh",            # netcat -e
    r"python[23]?\s+-c\s+['\"].*socket.*connect",  # python
    r"perl\s+-e\s+['\"].*socket",         # perl
    r"curl\s+[^\s]+\s*\|\s*bash",         # curl | bash
    r"wget\s+[^\s]+\s*\|\s*bash",         # wget | bash
    r"php\s+-r\s+['\"].*fsockopen",       # php
    r"ruby\s+-rsocket",                   # ruby
    r"exec\s+\d+<>.*tcp",                 # bash 高级
]

def is_reverse_shell(parsed, raw_kv):
    cmd = parsed.get("cmd", "") or raw_kv.get("cmd", "")
    if not cmd:
        return False
    for pat in REVERSE_SHELL_PATTERNS:
        if re.search(pat, cmd, re.IGNORECASE):
            return True, pat
    return False, None
```

### 2.4 处置建议

- [ ] **立即隔离主机** (CWP 隔离网络)
- [ ] 杀掉进程: `ps aux | grep -E "bash|nc|python"` → kill
- [ ] 拉取 shell 历史: `cat ~/.bash_history`
- [ ] 检查外联 IP (CWP 告警的 dst_ip): 拉取 `ss -tnp` / `netstat -tnp` 历史
- [ ] 检查 cron / systemd 持久化
- [ ] 关联 L2: 拉取此 dst_ip 在御界的告警, 看是否有 C2 / 数据外传

## 三、持久化 (T1543 / T1546)

### 3.1 触发信号

| 子场景 | 字段 | 模式 |
|---|---|---|
| crontab 植入 | `cmd` | `crontab -e` / `*/1 * * * *` 异常条目 / `/etc/cron.d/` 写入 |
| ssh 后门 | `process_path` | `authorized_keys` 修改 |
| systemd 服务 | `process_path` | `/etc/systemd/system/` 写入 |
| 启动项 | `process` | 异常开机启动项 |
| suid 提权 | `process_path` | `chmod +s` / 异常 suid |

### 3.2 ATT&CK 映射

- T1543 Create or Modify System Process: System Service
- T1546 Event Triggered Execution
- T1053.003 Cron

### 3.3 处置建议

- [ ] 拉取 `crontab -l` / `/etc/cron.*` 历史
- [ ] 拉取 `/etc/systemd/system/` 变更
- [ ] 检查 `~/.ssh/authorized_keys` 异常公钥
- [ ] 拉取 `find / -perm -4000` 异常 suid

## 四、横向移动 (T1021 / T1570)

### 4.1 触发信号

| 子场景 | 字段 | 模式 |
|---|---|---|
| ssh 横向 | `dst_ip` | 多个内网 IP, 同 user, 短时间内 |
| smb/rpc 横向 | `process` | `psexec` / `wmic` / `smbclient` |
| 端口扫描 | `dst_port` | 短时间内多 dst_port, 同 src_ip |
| 凭据窃取 | `cmd` | `mimikatz` / `lsass` / `/etc/shadow` 读取 |

### 4.2 ATT&CK 映射

- T1021 Remote Services
- T1570 Lateral Tool Transfer
- T1003 OS Credential Dumping

### 4.3 处置建议

- [ ] 拉取此 src_ip 的 CWP 横向历史
- [ ] 拉取内网流量 (御界 / 云防火墙)
- [ ] 隔离受感染主机
- [ ] 全网改密

## 五、其他场景 (待补充)

| 场景 | 优先级 | 说明 |
|---|---|---|
| 挖矿 (T1496) | 中 | 进程名 (xmrig/minerd) + CPU 异常 |
| Webshell | 高 | 写入文件 + cmd 评估 |
| 内核漏洞利用 | 低 | 罕见 |
| 数据外传 (T1567) | 高 | 关联御界更合适 |
| 容器逃逸 (T1611) | 中 | 容器内异常 |

## 六、变更记录

| 日期 | 变更 | 原因 |
|---|---|---|
| 2026-07-06 | 初版 (4 个核心场景) | 基于实际数据观察 |
