---
name: disk-space
description: 分析磁盘空间使用情况，定位占用空间大的文件和目录， 提供清理建议。
description_zh: 磁盘空间分析与清理建议
description_en: Disk space analysis and cleanup recommendations
version: 1.0.0
---

# 磁盘空间排查

帮助分析磁盘空间使用情况，定位空间占用大的文件和目录，提供清理建议。

## 安全原则

> ⚠️ **重要**：AI 只执行诊断命令（查看、分析），**不自动执行任何删除操作**。
> 
> 清理命令仅作为参考提供给用户，由用户自行判断和手动执行。

## 适用场景

### 用户可能的问题表述

**空间不足类**：
- "磁盘空间不足"、"磁盘满了"、"No space left on device"
- "磁盘空间为什么这么少了"、"磁盘怎么突然满了"
- "根目录空间不足"、"/ 分区满了"
- "/var 目录占用太大"、"/home 空间不够了"
- "写文件失败，提示空间不足"

**空间查看类**：
- "查看磁盘空间"、"看下磁盘使用情况"
- "df -h"、"磁盘占用多少了"
- "哪个目录占用空间最大"、"什么东西占了这么多空间"
- "大文件在哪里"、"找一下大于 1G 的文件"

**日志/缓存类**：
- "日志文件太大了"、"/var/log 占用很大"
- "journal 日志怎么清理"、"journalctl 占了多少空间"
- "yum/dnf 缓存怎么清理"、"软件包缓存太大"
- "清理系统垃圾"、"释放磁盘空间"

**inode 相关**：
- "inode 用完了"、"inode 不足"
- "明明还有空间但是写不了文件"
- "小文件太多导致空间不足"

**删除未释放**：
- "删了文件但空间没释放"、"rm 之后空间还是满的"
- "哪个进程占着已删除的文件"
- "lsof 查看已删除文件"

## 诊断步骤

以下命令可由 AI 自动执行，用于分析磁盘使用情况。

### 步骤 1：查看整体磁盘使用情况

```bash
# 查看所有挂载点的磁盘使用情况
df -h

# 查看 inode 使用情况（小文件过多也会导致"空间不足"）
df -i
```

**关注点**：
- `Use%` 超过 80% 的分区需要关注
- `Use%` 超过 95% 需要立即处理
- inode 使用率高说明小文件过多

### 步骤 2：定位大目录

```bash
# 查看根目录下各目录大小（排序显示前 20）
du -sh /* 2>/dev/null | sort -hr | head -20

# 如果 /var 占用大，继续深入
du -sh /var/* 2>/dev/null | sort -hr | head -10

# 如果 /home 占用大
du -sh /home/* 2>/dev/null | sort -hr | head -10
```

### 步骤 3：查找大文件

```bash
# 查找大于 100MB 的文件
find / -type f -size +100M -exec ls -lh {} \; 2>/dev/null | sort -k5 -hr | head -20

# 查找大于 1GB 的文件
find / -type f -size +1G -exec ls -lh {} \; 2>/dev/null

# 查找最近 7 天内修改的大文件（可能是日志增长）
find / -type f -size +100M -mtime -7 -exec ls -lh {} \; 2>/dev/null
```

### 步骤 4：检查常见占用大户

```bash
# 检查日志目录
du -sh /var/log/*  2>/dev/null | sort -hr | head -10

# 检查 journal 日志大小
journalctl --disk-usage

# 检查软件包缓存
du -sh /var/cache/yum 2>/dev/null
du -sh /var/cache/dnf 2>/dev/null

# 检查临时文件
du -sh /tmp /var/tmp 2>/dev/null

# 检查已删除但未释放的文件（进程仍持有）
lsof +L1 2>/dev/null | head -20
```

---

## 清理参考（仅供用户手动执行）

> 🛑 **以下命令涉及删除操作，AI 不会自动执行！**
> 
> 请用户根据诊断结果，自行判断是否需要执行以下清理操作。

### 1. 清理 journal 日志

```bash
# 清理 journal 日志，只保留最近 7 天
journalctl --vacuum-time=7d

# 或只保留 500MB
journalctl --vacuum-size=500M
```

### 2. 清理旧日志文件

```bash
# 查看可清理的旧日志（先预览，不删除）
find /var/log -name "*.gz" -mtime +30 -ls
find /var/log -name "*.old" -mtime +30 -ls

# 确认后手动删除（谨慎操作）
# find /var/log -name "*.gz" -mtime +30 -delete
# find /var/log -name "*.old" -mtime +30 -delete
```

### 3. 清理软件包缓存

```bash
# TencentOS 2（yum 管理）
yum clean all

# TencentOS 3/4（dnf 管理）
dnf clean all

# 清理旧内核（保留当前和一个备用）
package-cleanup --oldkernels --count=2
```

### 4. 清理临时文件

```bash
# 查看可清理的临时文件（先预览，不删除）
find /tmp -type f -mtime +7 -ls
find /var/tmp -type f -mtime +7 -ls

# 确认后手动删除
# find /tmp -type f -mtime +7 -delete
# find /var/tmp -type f -mtime +7 -delete
```

### 5. 处理已删除但未释放的文件

```bash
# 查看哪些进程持有已删除的文件
lsof +L1

# 重启对应服务释放空间（以 rsyslog 为例）
# systemctl restart rsyslog
```

## 相关技能

- **disk-partition**：分区管理（fdisk、parted、lsblk）
- **disk-filesystem**：文件系统管理（fstab、挂载、fsck）
- **disk-health**：磁盘健康检测（SMART、坏块）
- **disk-lvm**：LVM 逻辑卷管理（扩容、快照）
