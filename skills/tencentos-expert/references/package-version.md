---
name: package-version
description: 帮助查询软件包版本信息，检查安全更新，分析依赖关系，提供升级建议。 支持版本查询、CVE 漏洞修复检查、仓库版本对比、依赖分析等功能。
description_zh: 软件包版本查询与安全更新检查
description_en: Package version query and security update checking
version: 1.0.0
---

# 软件包版本查询

帮助查询软件包版本信息，检查安全更新，分析依赖关系，提供升级建议。

## 安全原则

> ⚠️ **重要**：AI 只执行查询命令（查看、分析），**不自动执行安装、升级、卸载操作**。
> 
> 软件包变更命令仅作为参考提供给用户，由用户自行判断和手动执行。

## 适用场景

### 用户可能的问题表述

**版本查询类**：
- "nginx 是什么版本"、"查看 openssl 版本"
- "python 版本是多少"、"gcc 版本太低了"
- "这个包是什么版本的"、"rpm -qa 查软件版本"
- "系统装了哪些软件包"、"有没有装 xxx"

**安全漏洞类**：
- "有没有安全漏洞"、"系统需要打补丁吗"
- "CVE-2024-xxxx 修复了吗"、"这个漏洞影响我吗"
- "nginx 有安全更新吗"、"openssl 有漏洞吗"
- "哪些包需要安全更新"、"怎么检查安全补丁"
- "升级后能修复什么漏洞"

**版本对比类**：
- "yum 源上最新版本是什么"、"有没有新版本"
- "我这个版本是不是最新的"、"为什么版本这么旧"
- "能升级到什么版本"、"最新版本号是多少"
- "为什么装不上新版本"、"仓库里有哪些版本"

**升级回退类**：
- "怎么升级这个软件包"、"升级到最新版本"
- "升级后有问题怎么回退"、"怎么降级软件包"
- "历史版本有哪些"、"怎么安装指定版本"
- "升级会不会有兼容性问题"

**依赖问题类**：
- "安装失败，依赖冲突"、"依赖关系错误"
- "这个包依赖什么"、"需要先装什么"
- "哪些包依赖这个软件"、"删了会影响什么"
- "为什么装不上，缺少依赖"

**来源追溯类**：
- "这个包是从哪个源安装的"、"包的来源是什么"
- "这是官方的包还是第三方的"、"包是不是被篡改了"
- "包的详细信息是什么"、"rpm 包信息"
- "查看包的文件列表"、"这个文件属于哪个包"

## 诊断步骤

以下命令可由 AI 自动执行，用于查询软件包信息。

### 步骤 1：查询已安装软件包版本

```bash
# 查询指定软件包版本（以 nginx 为例）
rpm -q nginx

# 查询详细信息（版本、发布日期、来源等）
rpm -qi nginx

# 查询软件包并显示版本号
rpm -qa | grep -i nginx

# 查询多个相关包
rpm -qa | grep -iE "nginx|openssl|curl"
```

**常用软件版本查询**：

```bash
# 内核版本
uname -r
rpm -q kernel

# 系统发行版
cat /etc/os-release

# 常用软件
rpm -q glibc openssl openssh-server curl wget python3 gcc
```

### 步骤 2：检查可用更新

```bash
# 检查指定包是否有更新（TencentOS 3/4）
dnf check-update nginx

# 检查所有可用更新
dnf check-update

# 只看安全更新
dnf check-update --security

# TencentOS 2 使用 yum
yum check-update nginx
yum check-update --security
```

### 步骤 3：查看仓库中可用版本

```bash
# 查看仓库中所有可用版本
dnf list nginx --showduplicates

# 查看包的详细信息（含仓库来源）
dnf info nginx

# 查看所有可用版本（包括已安装）
dnf list --all nginx

# 查看哪些仓库提供这个包
dnf repoquery --whatprovides nginx
```

### 步骤 4：检查安全漏洞修复信息

```bash
# 查看软件包的更新日志（包含 CVE 修复信息）
rpm -q --changelog nginx | head -100

# 搜索特定 CVE 是否已修复
rpm -q --changelog openssl | grep -i "CVE-2024"

# 查看安全更新公告
dnf updateinfo list security

# 查看指定包的安全公告
dnf updateinfo info --security nginx

# 检查系统已安装包中哪些有安全更新
dnf updateinfo list security installed
```

### 步骤 5：分析依赖关系

```bash
# 查看包的依赖（安装时需要什么）
dnf deplist nginx

# 查看包依赖的库文件
rpm -qR nginx

# 查看哪些包依赖此包（反向依赖）
dnf repoquery --whatrequires nginx

# 检查是否有依赖问题
rpm -Va --nofiles --nodigest 2>/dev/null | head -20
```

### 步骤 6：追溯包的来源

```bash
# 查看包是从哪个仓库安装的
dnf info nginx | grep -E "Repository|From repo"

# 验证包的完整性（GPG 签名）
rpm -K nginx-*.rpm

# 验证已安装包的文件是否被修改
rpm -V nginx

# 查看包安装的文件列表
rpm -ql nginx

# 查看某个文件属于哪个包
rpm -qf /usr/sbin/nginx
```

### 步骤 7：查看升级/安装历史

```bash
# 查看 dnf 操作历史
dnf history

# 查看最近 10 次操作详情
dnf history list --reverse | head -12

# 查看某次操作的详情（ID 从 history 获取）
dnf history info 1

# 查看包的安装/升级时间
rpm -qi nginx | grep -E "Install Date|Build Date"
```

---

## 常见问题解答

### Q1: 如何判断包是否需要升级？

```bash
# 检查指定包
dnf check-update nginx

# 输出解读：
# - 有输出 → 有新版本可用
# - 无输出 → 已是最新版本
```

### Q2: 如何查看某个 CVE 是否影响我的系统？

```bash
# 方法 1: 检查 changelog
rpm -q --changelog openssl | grep -i "CVE-2024-0567"

# 方法 2: 检查安全公告
dnf updateinfo info CVE-2024-0567

# 方法 3: 查看当前版本是否在受影响范围
rpm -q openssl
# 然后对照 CVE 公告中的受影响版本
```

### Q3: 为什么 yum/dnf 找不到某个版本？

可能原因：
1. **仓库未启用**：`dnf repolist` 查看启用的仓库
2. **版本太旧已移除**：官方仓库通常只保留最近几个版本
3. **需要额外仓库**：如 EPEL、SCL 等
4. **架构不匹配**：检查 `uname -m` 是否匹配

```bash
# 查看启用的仓库
dnf repolist

# 查看所有仓库（含禁用）
dnf repolist all

# 搜索所有仓库中的包
dnf search nginx --enablerepo=*
```

### Q4: 如何比较两个版本号的大小？

```bash
# 使用 rpmdev-vercmp（需安装 rpmdevtools）
rpmdev-vercmp 1.20.1 1.21.0

# 或使用 rpm 的版本比较
rpm -E '%{lua:print(rpm.vercmp("1.20.1", "1.21.0"))}'
# 输出: -1 表示前者小于后者, 0 相等, 1 前者大于后者
```

---

## 操作参考（仅供用户手动执行）

> 🛑 **以下命令涉及软件包变更，AI 不会自动执行！**
> 
> 请用户根据查询结果，自行判断是否需要执行以下操作。

### 1. 升级软件包

```bash
# 升级指定包到最新版本
dnf upgrade nginx

# 只应用安全更新
dnf upgrade --security

# 升级所有包
dnf upgrade

# 预览升级（不实际执行）
dnf upgrade nginx --assumeno
```

### 2. 安装指定版本

```bash
# 查看可用版本
dnf list nginx --showduplicates

# 安装指定版本
dnf install nginx-1.20.1-1.el8

# 降级到旧版本
dnf downgrade nginx-1.20.0-1.el8
```

### 3. 回退升级

```bash
# 查看历史记录
dnf history

# 回退到上一次操作前的状态（ID 从 history 获取）
dnf history undo 15

# 回退某个包到之前版本
dnf downgrade nginx
```

### 4. 锁定版本（防止自动升级）

```bash
# 安装 versionlock 插件
dnf install dnf-plugin-versionlock

# 锁定当前版本
dnf versionlock add nginx

# 查看已锁定的包
dnf versionlock list

# 解除锁定
dnf versionlock delete nginx
```

### 5. 修复依赖问题

```bash
# 自动修复依赖
dnf install -y --allowerasing nginx

# 清理并重建缓存
dnf clean all
dnf makecache

# 检查并修复 RPM 数据库
rpm --rebuilddb
```

---

## 命令速查表

| 场景 | 命令 |
|------|------|
| 查看已安装版本 | `rpm -q nginx` |
| 查看详细信息 | `rpm -qi nginx` 或 `dnf info nginx` |
| 检查是否有更新 | `dnf check-update nginx` |
| 查看所有可用版本 | `dnf list nginx --showduplicates` |
| 查看安全更新 | `dnf check-update --security` |
| 查看 CVE 修复记录 | `rpm -q --changelog nginx \| grep CVE` |
| 查看依赖 | `dnf deplist nginx` |
| 查看反向依赖 | `dnf repoquery --whatrequires nginx` |
| 查看包的文件 | `rpm -ql nginx` |
| 查看文件属于哪个包 | `rpm -qf /usr/sbin/nginx` |
| 验证包完整性 | `rpm -V nginx` |
| 查看操作历史 | `dnf history` |

---

## TencentOS 版本差异

| 功能 | TencentOS 2 | TencentOS 3/4 |
|------|-------------|---------------|
| 包管理器 | yum | dnf |
| 安全更新检查 | `yum check-update --security` | `dnf check-update --security` |
| 版本列表 | `yum list --showduplicates` | `dnf list --showduplicates` |
| 历史回退 | `yum history undo` | `dnf history undo` |
| 版本锁定 | `yum-plugin-versionlock` | `dnf-plugin-versionlock` |

> **注意**：TencentOS 3/4 的 `yum` 命令实际是 `dnf` 的软链接，两者可以互换使用。

## 相关技能

- **cve-check**：CVE 漏洞检查与分析
- **security-baseline**：系统安全基线检查
- **yum-repo**：Yum/DNF 仓库管理
