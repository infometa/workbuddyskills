---
name: security-baseline
description: "基于 GB/T 22239-2019《信息安全技术 网络安全等级保护基本要求》三级标准，对 TencentOS Server（兼容 CentOS/RHEL 系）进行安全基线检查和自动加固。覆盖身份鉴别、访问控制、安全审计、入侵防范、恶意代码防范和资源控制六大安全域，共 37 检查项。支持检查模式（只看不动）和加固模式（自动修复）两种模式。触发关键词包括：等保、等保三级、安全加固、安全基线、安全检查、security baseline、security hardening、compliance check、等保2.0、GB/T 22239。"
description_zh: 系统安全基线检查与加固
description_en: System security baseline check and hardening based on GB/T 22239-2019
version: 1.0.0
---

# TencentOS 等保三级安全加固

> 依据：GB/T 22239-2019《信息安全技术 网络安全等级保护基本要求》第三级
> 配套规范：《TencentOS Server 操作系统安全规范》V2.0
> 适用系统： TencentOS Server 3 / TencentOS Server 4

## Purpose

对 TencentOS Server 进行等保三级合规的安全基线检查和自动加固，覆盖操作系统层面的六大安全域：

1. **身份鉴别** — 密码复杂度、密码有效期、密码历史、加密算法、登录失败锁定、会话超时
2. **访问控制** — SSH 安全配置、Banner、密钥权限、su 限制、umask、用户目录权限、关键文件权限
3. **安全审计** — auditd 服务与规则、审计日志存储、rsyslog 配置
4. **入侵防范** — 禁用不必要文件系统、网络参数加固、关闭不必要服务/端口
5. **恶意代码防范** — 卸载不安全软件包、GPG 签名验证
6. **资源控制** — 时间同步、cron 权限、GRUB 权限、Banner 文件权限、UID/GID 唯一性、空密码账户、SUID/SGID 审计等

支持两种运行模式：
- **检查模式（check）**：只读扫描，输出合规结果（PASS/FAIL/SKIP），不修改系统
- **加固模式（harden）**：自动执行加固操作，操作前备份原始配置

### 风险分级体系

| 等级 | 含义 | 说明 |
|------|------|------|
| **R1** | 高风险（必须执行） | 直接影响系统安全的核心配置，如密码策略、登录控制、审计日志 |
| **R2** | 中风险（建议执行） | 提升安全防护能力的加固项，如文件权限、服务关闭、软件清理 |
| **R3** | 低风险（可选执行） | 进一步完善安全防护的可选项，如 Banner、sticky bit |

## When to Use

- 用户要求对 TencentOS / CentOS / RHEL 进行等保合规检查
- 用户提到关键词：等保、等保三级、安全加固、安全基线、合规检查、security hardening
- 用户需要在服务器上线前进行安全基线加固
- 用户需要生成等保合规检查报告
- 用户提到 GB/T 22239、等保 2.0

## Prerequisites

### 目标服务器要求

- **OS**：TencentOS Server 3 或 TencentOS Server 4（兼容 CentOS 8/RHEL 8+）
- **权限**：需要 root 权限
- **连接方式**：SSH（使用密钥认证或密码）

### 适配说明

TencentOS Server 3 和 4 共享以下安全特性：
- 使用 `pam_pwquality` 管理密码复杂度（替代 pam_cracklib）
- 使用 `pam_faillock` 管理登录失败锁定（替代 pam_tally2）
- 使用 `chrony` 进行时间同步（替代 ntp）
- 使用 `systemd` 管理所有服务
- 使用 `dnf` 包管理器（兼容 yum 命令）

## 检查项总览（37 项）

### 1. 身份鉴别（6 项）

| 编号 | 检查项 | 风险等级 | 配置文件/模块 |
|------|--------|---------|--------------|
| 1.1 | 密码复杂度策略（pam_pwquality） | R1 | `/etc/security/pwquality.conf` |
| 1.2 | 密码有效期策略（login.defs） | R1 | `/etc/login.defs` |
| 1.3 | 密码历史记录（pam_pwhistory） | R1 | `/etc/pam.d/system-auth` |
| 1.4 | 密码加密算法（SHA-512） | R1 | `/etc/login.defs` + PAM |
| 1.5 | 登录失败锁定策略（pam_faillock） | R1 | `/etc/security/faillock.conf` |
| 1.6 | 会话超时锁定（TMOUT） | R1 | `/etc/profile` |

### 2. 访问控制（8 项）

| 编号 | 检查项 | 风险等级 | 配置文件/模块 |
|------|--------|---------|--------------|
| 2.1 | SSH 远程访问安全配置 | R1 | `/etc/ssh/sshd_config` |
| 2.2 | SSH 登录 Banner 配置 | R3 | `/etc/ssh/sshd_config` + `/etc/issue.net` |
| 2.3 | SSH 密钥文件权限 | R2 | `/etc/ssh/ssh_host_*_key` |
| 2.4 | 限制 su 命令访问（pam_wheel） | R1 | `/etc/pam.d/su` |
| 2.5 | 默认 umask 配置 | R2 | `/etc/profile` |
| 2.6 | 用户目录权限（<=750） | R2 | `/home/*/` |
| 2.7 | 关键系统文件权限 | R2 | `/etc/passwd` `/etc/shadow` 等 |
| 2.8 | 禁止 root 远程 SSH 登录 ⚠️ | R1 | `/etc/ssh/sshd_config` |

### 3. 安全审计（4 项）

| 编号 | 检查项 | 风险等级 | 配置文件/模块 |
|------|--------|---------|--------------|
| 3.1 | 审计服务状态（auditd） | R1 | `systemctl` |
| 3.2 | 审计规则配置（14 类完整规则） | R1 | `/etc/audit/rules.d/audit.rules` |
| 3.3 | 审计日志存储配置 | R2 | `/etc/audit/auditd.conf` |
| 3.4 | rsyslog 日志服务配置 | R1 | `/etc/rsyslog.conf` |

### 4. 入侵防范（6 项）

| 编号 | 检查项 | 风险等级 | 配置文件/模块 |
|------|--------|---------|--------------|
| 4.1 | 禁用不必要的文件系统 | R2 | `/etc/modprobe.d/` |
| 4.2 | 网络参数加固（16 项 sysctl） | R1 | `/etc/sysctl.conf` |
| 4.3 | 关闭不必要的服务（16 项） | R2 | `systemctl` |
| 4.4 | 关闭高危端口（21/23/25/111/427/631） | R2 | `ss -tuln` |
| 4.5 | 防火墙状态 ⚠️ | R1 | `firewalld` / `iptables` |
| 4.6 | SELinux 状态 ⚠️ | R1 | `/etc/selinux/config` |

### 5. 恶意代码防范（2 项）

| 编号 | 检查项 | 风险等级 | 配置文件/模块 |
|------|--------|---------|--------------|
| 5.1 | 卸载不安全/不必要软件包 | R2 | `rpm -q` |
| 5.2 | 软件包 GPG 签名验证 | R2 | `/etc/dnf/dnf.conf` |

### 6. 资源控制（8 项）

| 编号 | 检查项 | 风险等级 | 配置文件/模块 |
|------|--------|---------|--------------|
| 6.1 | 时间同步服务（chrony） | R1 | `systemctl` |
| 6.2 | cron 计划任务权限 | R2 | `/etc/crontab` `/etc/cron.allow` |
| 6.3 | GRUB 引导配置权限 | R2 | `/boot/grub2/grub.cfg` |
| 6.4 | Banner 文件权限 | R3 | `/etc/motd` `/etc/issue` |
| 6.5 | 禁用自动播放（autofs） | R3 | `systemctl` |
| 6.6 | 世界可写目录 sticky bit | R3 | 文件系统 |
| 6.7 | 审计进程早启动（GRUB audit=1） | R2 | `/etc/default/grub` |
| 6.8 | UID/GID 唯一性检查 | R2 | `/etc/passwd` `/etc/group` |
| 6.9 | 空密码账户检查 | R1 | `/etc/shadow` |
| 6.10 | 无用系统账户清理 | R2 | `/etc/passwd` |
| 6.11 | SUID/SGID 文件审计 | R3 | 文件系统 |

## Workflow

### Phase 1: 连接目标服务器

```bash
# 密钥连接
ssh -i /path/to/key -o StrictHostKeyChecking=no root@$HOST "uname -a && cat /etc/os-release"

# 密码连接
sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no root@$HOST "uname -a && cat /etc/os-release"
```

确认目标系统为 TencentOS Server 3 或 4。

### Phase 2: 安全检查（只检测，不修改）

将脚本上传到目标服务器并执行：

```bash
# 上传脚本
scp ${SKILL_DIR}/scripts/tos_security_harden.sh root@$HOST:/tmp/

# 执行检查（只读模式）
ssh root@$HOST "bash /tmp/tos_security_harden.sh check"

# 按风险等级检查
ssh root@$HOST "bash /tmp/tos_security_harden.sh check -l R1"

# 检查指定项
ssh root@$HOST "bash /tmp/tos_security_harden.sh check -i 1.1,1.2,2.1"
```

### Phase 3: 生成检查报告

将检查结果整理为结构化报告，向用户展示各项的 PASS/FAIL 状态、风险等级和具体不合规细节。

### Phase 4: 安全加固（需用户确认）

**加固操作会修改系统配置，必须先获得用户明确确认。**

```bash
# 加固所有项
ssh root@$HOST "bash /tmp/tos_security_harden.sh harden"

# 按风险等级加固
ssh root@$HOST "bash /tmp/tos_security_harden.sh harden -l R1"

# 加固指定项
ssh root@$HOST "bash /tmp/tos_security_harden.sh harden -i 1.1,1.2,2.1"

# 静默模式
ssh root@$HOST "bash /tmp/tos_security_harden.sh harden -l R2 -q"
```

### Phase 5: 验证加固结果

```bash
ssh root@$HOST "bash /tmp/tos_security_harden.sh check"
```

对比加固前后的 PASS/FAIL 变化。

## ⚠️ 高风险项 — 需责任人确认

**以下三个加固项可能导致严重后果，harden 模式执行前必须由责任人明确确认：**

### 1. 禁止 root 远程登录

**影响**：如果没有其他可用管理账户，将导致无法远程登录服务器。

**执行前必须确认**：
- [ ] 已创建非 root 管理账户
- [ ] 该账户已加入 sudoers
- [ ] 已测试该账户可正常 SSH 登录
- [ ] 已测试该账户可正常 sudo

**确认方式**：脚本会在加固前暂停，打印以上检查清单，要求输入 `YES` 才继续。

### 2. 启用防火墙

**影响**：可能拦截业务端口，导致服务不可用。

**执行前必须确认**：
- [ ] 已梳理当前监听端口清单
- [ ] SSH 端口已确认在白名单中
- [ ] 业务端口已确认在白名单中
- [ ] 有备用登录方式（如 VNC / 控制台）

**确认方式**：脚本会在加固前列出当前所有监听端口，要求输入 `YES` 才继续。

### 3. SELinux

**影响**：可能导致应用无法正常运行、服务启动失败。

**执行前必须确认**：
- [ ] 了解 SELinux 对当前业务的影响
- [ ] 已评估是否有自定义策略需求
- [ ] 建议先设为 permissive 模式观察

**确认方式**：脚本会在加固前说明风险，要求输入 `YES` 才继续。如选择启用，默认设为 permissive 而非 enforcing。

> **注意**：当脚本以非交互方式运行（如通过 Ansible/自动化平台批量下发），高风险项默认跳过并记录 SKIP 状态，必须由管理员手动执行。

## Command Execution Policy

- **检查模式（check）**：所有命令 `requires_approval: false`，只读不修改
- **加固模式（harden）**：所有命令 `requires_approval: true`，必须用户确认
- 高风险项（禁 root 登录、防火墙、SELinux）在脚本内部有额外确认机制

## TencentOS 版本适配

| 配置项 | TencentOS Server 3 | TencentOS Server 4 |
|--------|--------------------|--------------------|
| 内核 | 5.4 系列 | 6.6 LTS |
| PAM 密码复杂度 | `pam_pwquality` | `pam_pwquality` |
| PAM 登录锁定 | `pam_faillock` | `pam_faillock` |
| 时间同步 | `chrony` | `chrony` |
| 包管理器 | `dnf`（兼容 yum） | `dnf`（兼容 yum） |
| GRUB 路径 | `/boot/grub2/grub.cfg` | 自动检测 EFI/Legacy |

脚本通过 `/etc/os-release` 的 `VERSION_ID` 自动检测版本并适配。

## Error Handling

| 错误场景 | 处理方式 |
|----------|---------|
| SSH 连接失败 | 检查 IP/端口/密码，提示用户确认 |
| 非 root 用户执行 | 提示需要 root 权限 |
| 非 TencentOS 系统 | 输出警告，继续执行（部分项可能不适用） |
| sshd 配置变更后验证失败 | 自动回滚备份的 sshd_config |
| 高风险项未确认 | SKIP 并记录日志 |

## File References

| 文件 | 说明 |
|------|------|
| `scripts/tos_security_harden.sh` | 安全检查+加固脚本（check/harden 双模式，含高风险项确认） |
| `references/checklist.md` | 等保三级 31 项检查清单速查表（含风险等级和条款映射） |
