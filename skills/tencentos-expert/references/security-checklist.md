# TencentOS Server 等保三级安全加固检查清单

> 依据：GB/T 22239-2019《信息安全技术 网络安全等级保护基本要求》第三级
> 配套规范：《TencentOS Server 操作系统安全规范》V2.0
> 适用系统：TencentOS Server 3 / TencentOS Server 4

## 风险分级

| 等级 | 含义 | 说明 |
|------|------|------|
| **R1** | 高风险（必须执行） | 直接影响系统安全的核心配置 |
| **R2** | 中风险（建议执行） | 提升安全防护能力的加固项 |
| **R3** | 低风险（可选执行） | 进一步完善安全防护的可选项 |

---

## 1. 身份鉴别

### 1.1 密码复杂度策略 [R1]

| 属性 | 内容 |
|------|------|
| 配置文件 | `/etc/security/pwquality.conf` |
| 要求 | minlen=8, dcredit=-1, ucredit=-1, lcredit=-1, ocredit=-1, retry=3 |
| PAM 引用 | `/etc/pam.d/system-auth` 中需有 `password requisite pam_pwquality.so` |
| 检查命令 | `grep -E "^(minlen|dcredit|ucredit|lcredit|ocredit)" /etc/security/pwquality.conf` |

### 1.2 密码有效期策略 [R1]

| 属性 | 内容 |
|------|------|
| 配置文件 | `/etc/login.defs` |
| 要求 | PASS_MAX_DAYS=90, PASS_MIN_DAYS=3, PASS_MIN_LEN=8, PASS_WARN_AGE=7 |
| 检查命令 | `grep -E "^PASS_(MAX_DAYS|MIN_DAYS|MIN_LEN|WARN_AGE)" /etc/login.defs` |

### 1.3 密码历史记录 [R1]

| 属性 | 内容 |
|------|------|
| 配置文件 | `/etc/pam.d/system-auth` |
| 要求 | `password required pam_pwhistory.so remember=3 enforce_for_root` |
| 位置 | 必须在 `pam_unix.so` 之前 |
| 检查命令 | `grep pam_pwhistory /etc/pam.d/system-auth` |

### 1.4 密码加密算法 [R1]

| 属性 | 内容 |
|------|------|
| 配置文件 | `/etc/login.defs` + `/etc/pam.d/system-auth` |
| 要求 | ENCRYPT_METHOD=SHA512，PAM 中 pam_unix.so 需含 sha512 |
| 检查命令 | `grep "^ENCRYPT_METHOD" /etc/login.defs` |

### 1.5 登录失败锁定策略 [R1]

| 属性 | 内容 |
|------|------|
| 配置文件 | `/etc/security/faillock.conf` + `/etc/pam.d/system-auth` |
| 要求 | deny=3, fail_interval=900, unlock_time=600, even_deny_root, root_unlock_time=300 |
| PAM 配置 | preauth + authfail 双阶段 |
| 检查命令 | `grep -E "^(deny|unlock_time)" /etc/security/faillock.conf` |

### 1.6 会话超时锁定 [R1]

| 属性 | 内容 |
|------|------|
| 配置文件 | `/etc/profile` |
| 要求 | TMOUT=300, readonly TMOUT, export TMOUT |
| 检查命令 | `grep "TMOUT" /etc/profile` |

---

## 2. 访问控制

### 2.1 SSH 远程访问安全配置 [R1]

| 参数 | 期望值 | 说明 |
|------|--------|------|
| Protocol | 2 | 仅使用 SSHv2 |
| PermitEmptyPasswords | no | 禁止空密码登录 |
| MaxAuthTries | 4 | 最大认证尝试(允许<=4) |
| ClientAliveInterval | 300 | 客户端存活检测间隔(允许>0且<=300) |
| ClientAliveCountMax | 3 | 最大存活检测次数 |
| HostbasedAuthentication | no | 禁用主机认证 |
| IgnoreRhosts | yes | 忽略 rhosts 文件 |
| PermitUserEnvironment | no | 禁止用户环境变量 |
| LogLevel | INFO | 日志级别 |
| SyslogFacility | AUTHPRIV | 日志设施 |
| LoginGraceTime | 60 | 登录宽限时间(允许>0且<=60) |
| Ciphers | aes256-ctr,aes192-ctr,aes128-ctr | 加密算法白名单 |

### 2.2 SSH 登录 Banner 配置 [R3]

| 属性 | 内容 |
|------|------|
| 配置文件 | `/etc/ssh/sshd_config` + `/etc/issue.net` |
| 要求 | Banner /etc/issue.net |
| Banner 内容 | "Authorized uses only. All activity may be monitored and reported." |

### 2.3 SSH 密钥文件权限 [R2]

| 文件 | 期望权限 |
|------|---------|
| `/etc/ssh/sshd_config` | 600, root:root |
| `/etc/ssh/ssh_host_*_key` (私钥) | 400, root:root |
| `/etc/ssh/ssh_host_*_key.pub` (公钥) | 644, root:root |

### 2.4 限制 su 命令访问 [R1]

| 属性 | 内容 |
|------|------|
| 配置文件 | `/etc/pam.d/su` + `/etc/login.defs` |
| 要求 | `auth required pam_wheel.so use_uid` + `SU_WHEEL_ONLY yes` |
| 检查命令 | `grep pam_wheel /etc/pam.d/su` |

### 2.5 默认 umask 配置 [R2]

| 属性 | 内容 |
|------|------|
| 配置文件 | `/etc/profile` |
| 要求 | umask 0027（或更严格 077） |
| 检查命令 | `grep "umask" /etc/profile` |

### 2.6 用户目录权限 [R2]

| 属性 | 内容 |
|------|------|
| 检查范围 | `/home/*/` |
| 要求 | 权限 <= 750 |
| 检查命令 | `stat -c "%a %n" /home/*/` |

### 2.7 关键系统文件权限 [R2]

| 文件 | 期望权限 | 所有者 |
|------|---------|--------|
| `/etc/passwd` | 644 | root:root |
| `/etc/shadow` | 000/600/640 | root:root |
| `/etc/group` | 644 | root:root |
| `/etc/gshadow` | 000/600/640 | root:root |
| `/etc/passwd-` | <=644 | root:root |
| `/etc/shadow-` | 600 | root:root |
| `/etc/group-` | <=644 | root:root |
| `/etc/gshadow-` | 600 | root:root |

### 2.8 禁止 root 远程 SSH 登录 [R1] ⚠️ 高风险

| 属性 | 内容 |
|------|------|
| 配置文件 | `/etc/ssh/sshd_config` |
| 要求 | PermitRootLogin no |
| **前置条件** | 已创建非 root 管理账户、已加入 sudoers、已测试 SSH 登录和 sudo |
| **风险** | 无其他管理账户时将导致无法远程登录 |
| **确认方式** | harden 模式下需输入 YES 确认 |

---

## 3. 安全审计

### 3.1 审计服务状态 [R1]

| 属性 | 内容 |
|------|------|
| 要求 | audit 已安装、auditd 已启动且开机自启 |
| 检查命令 | `systemctl is-active auditd && systemctl is-enabled auditd` |

### 3.2 审计规则配置 [R1]

| 审计类别 | 监控项 |
|---------|--------|
| sudoers | `/etc/sudoers`, `/etc/sudoers.d`, `/var/log/sudo.log` |
| identity | `/etc/group`, `/etc/passwd`, `/etc/shadow`, `/etc/gshadow`, `/etc/security/opasswd` |
| user_group_modify | useradd/userdel/usermod/groupadd/groupdel/groupmod |
| time-change | adjtimex/settimeofday/clock_settime, `/etc/localtime`, `/etc/chrony.conf` |
| system-locale | sethostname/setdomainname, `/etc/issue*`, `/etc/hosts`, `/etc/hostname` |
| session | `/var/run/utmp`, `/var/log/wtmp`, `/var/log/btmp` |
| logins | `/var/run/faillock/`, `/var/log/lastlog` |
| perm_mod | chmod/fchmod/chown/fchown/setxattr/removexattr |
| access | 未授权文件访问 (EACCES/EPERM) |
| mounts | mount 操作 |
| delete | unlink/unlinkat/rename/renameat |
| MAC-policy | `/etc/selinux/` |
| modules | insmod/rmmod/modprobe, init_module/delete_module |

### 3.3 审计日志存储配置 [R2]

| 属性 | 内容 |
|------|------|
| 配置文件 | `/etc/audit/auditd.conf` |
| 要求 | max_log_file >= 6, max_log_file_action = ROTATE |

### 3.4 rsyslog 日志服务配置 [R1]

| 属性 | 内容 |
|------|------|
| 要求 | rsyslog 运行中，$FileCreateMode 0640 |
| 检查命令 | `systemctl is-active rsyslog` |

---

## 4. 入侵防范

### 4.1 禁用不必要的文件系统 [R2]

| 属性 | 内容 |
|------|------|
| 禁用列表 | cramfs, squashfs, udf, dccp, sctp |
| 方法 | `/etc/modprobe.d/CIS.conf` 中 `install <fs> /bin/true` |

### 4.2 网络参数加固 [R1]

| 参数 | 期望值 | 说明 |
|------|--------|------|
| net.ipv4.ip_forward | 0 | 禁止 IP 转发 (Docker/K8s 节点需改为 1) |
| net.ipv4.conf.all.send_redirects | 0 | 禁止发送重定向 |
| net.ipv4.conf.default.send_redirects | 0 | 同上(默认) |
| net.ipv4.conf.all.accept_source_route | 0 | 禁止源路由 |
| net.ipv4.conf.default.accept_source_route | 0 | 同上(默认) |
| net.ipv4.conf.all.accept_redirects | 0 | 禁止接受重定向 |
| net.ipv4.conf.default.accept_redirects | 0 | 同上(默认) |
| net.ipv4.conf.all.secure_redirects | 0 | 禁止安全重定向 |
| net.ipv4.conf.default.secure_redirects | 0 | 同上(默认) |
| net.ipv4.conf.all.log_martians | 1 | 记录可疑数据包 |
| net.ipv4.conf.default.log_martians | 1 | 同上(默认) |
| net.ipv4.icmp_echo_ignore_broadcasts | 1 | 忽略广播 ICMP |
| net.ipv4.icmp_ignore_bogus_error_responses | 1 | 忽略伪造错误响应 |
| net.ipv4.conf.all.rp_filter | 1 | 启用反向路径过滤 |
| net.ipv4.conf.default.rp_filter | 1 | 同上(默认) |
| net.ipv4.tcp_syncookies | 1 | 启用 SYN Cookie |

### 4.3 关闭不必要的服务 [R2]

| 服务列表 |
|---------|
| xinetd, avahi-daemon, cups, dhcpd, named, vsftpd, dovecot, smb, squid, snmpd, ypserv, rsyncd, nfs, rpcbind, telnet.socket, tftp.socket |

### 4.4 关闭高危端口 [R2]

| 端口 | 服务 |
|------|------|
| 21 | FTP |
| 23 | Telnet |
| 25 | SMTP |
| 111 | RPC |
| 427 | SLP |
| 631 | CUPS |

### 4.5 防火墙状态 [R1] ⚠️ 高风险

| 属性 | 内容 |
|------|------|
| 要求 | firewalld 或 iptables 已启用 |
| **前置条件** | 已梳理业务端口、SSH 端口在白名单、有备用登录方式 |
| **风险** | 启用防火墙可能拦截业务端口，导致服务不可用 |
| **确认方式** | harden 模式下列出当前监听端口，需输入 YES 确认 |

### 4.6 SELinux 状态 [R1] ⚠️ 高风险

| 属性 | 内容 |
|------|------|
| 配置文件 | `/etc/selinux/config` |
| 要求 | SELINUX=enforcing 或 permissive |
| **风险** | 可能导致应用无法正常运行、服务启动失败 |
| **确认方式** | harden 模式下默认设为 permissive（观察模式），需输入 YES 确认 |

---

## 5. 恶意代码防范

### 5.1 卸载不安全/不必要软件包 [R2]

| 软件包列表 |
|-----------|
| telnet-server, telnet, ypbind, ypserv, rsh, talk, openldap-clients, openslp, openslp-server, prelink |

### 5.2 软件包 GPG 签名验证 [R2]

| 属性 | 内容 |
|------|------|
| 配置文件 | `/etc/dnf/dnf.conf` 或 `/etc/yum.conf` |
| 要求 | gpgcheck=1 |

---

## 6. 资源控制

### 6.1 时间同步服务 [R1]

| 属性 | 内容 |
|------|------|
| 要求 | chrony 已安装且 chronyd 运行中 |

### 6.2 cron 计划任务权限 [R2]

| 属性 | 内容 |
|------|------|
| 要求 | cron 目录权限正确(root:root, go-rwx)，使用 cron.allow/at.allow 白名单 |
| 删除 | cron.deny, at.deny |

### 6.3 GRUB 引导配置权限 [R2]

| 属性 | 内容 |
|------|------|
| 要求 | grub.cfg 权限 <= 600, root:root |
| 路径 | 自动检测 EFI 或 Legacy |

### 6.4 Banner 文件权限 [R3]

| 文件 | 期望 |
|------|------|
| `/etc/motd` | 644, root:root |
| `/etc/issue` | 644, root:root |
| `/etc/issue.net` | 644, root:root |

### 6.5 禁用自动播放 [R3]

| 属性 | 内容 |
|------|------|
| 要求 | autofs 服务已停止且禁用 |

### 6.6 世界可写目录 sticky bit [R3]

| 属性 | 内容 |
|------|------|
| 要求 | 所有世界可写目录(0002)都有 sticky bit(1000) |

### 6.7 审计进程早启动 [R2]

| 属性 | 内容 |
|------|------|
| 配置文件 | `/etc/default/grub` |
| 要求 | GRUB_CMDLINE_LINUX 包含 audit=1 |
| 备注 | 修改后需执行 grub2-mkconfig 并重启生效 |

### 6.8 UID/GID 唯一性 [R2]

| 属性 | 内容 |
|------|------|
| 要求 | 无重复 UID、无重复 GID、无重复用户名 |
| 备注 | 如发现重复需人工处理 |

### 6.9 空密码账户检查 [R1]

| 属性 | 内容 |
|------|------|
| 要求 | 无密码字段为空的账户（!! 和 ! 表示已锁定，不算空密码） |
| 加固 | 锁定空密码账户 `passwd -l <user>` |

### 6.10 无用系统账户清理 [R2]

| 属性 | 内容 |
|------|------|
| 清理列表 | shutdown, halt, games, ftp |
| 备注 | 删除前确认无业务依赖 |

### 6.11 SUID/SGID 文件审计 [R3]

| 属性 | 内容 |
|------|------|
| 要求 | 定期审计，人工确认无异常特权文件 |
| 合法文件 | /usr/bin/su, /usr/bin/passwd, /usr/bin/sudo 等 |

---

## 脚本使用方法

```bash
# 检查全部项
sudo bash tos_security_harden.sh check

# 仅检查高风险项
sudo bash tos_security_harden.sh check -l R1

# 加固高风险项
sudo bash tos_security_harden.sh harden -l R1

# 检查指定项
sudo bash tos_security_harden.sh check -i 1.1,1.2,2.1

# 静默模式加固中风险项
sudo bash tos_security_harden.sh harden -l R2 -q
```

## 高风险项汇总

| 编号 | 检查项 | 风险 | 确认方式 |
|------|--------|------|---------|
| 2.8 | 禁止 root 远程登录 | 无管理账户时锁死服务器 | 需输入 YES |
| 4.5 | 启用防火墙 | 可能拦截业务端口 | 列出端口后需输入 YES |
| 4.6 | 启用 SELinux | 可能导致应用故障 | 默认设 permissive，需输入 YES |

> **非交互模式**（管道/脚本/Ansible 调用）下，三个高风险项自动跳过并记录 SKIP 状态。
