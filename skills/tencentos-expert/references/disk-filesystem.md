---
name: disk-filesystem
description: 文件系统创建、挂载、检查和修复。 包括 /etc/fstab 配置和挂载问题排查。
description_zh: 文件系统创建、挂载、检查和修复
description_en: Filesystem creation, mounting, checking and repair
version: 1.0.0
---

# 文件系统管理

帮助进行文件系统的创建、挂载、检查和修复，以及 /etc/fstab 配置管理。

## 安全原则

> ⚠️ **重要**：AI 只执行诊断命令（查看、分析），**不自动执行任何格式化/写入操作**。
> 
> 涉及数据破坏的操作（如 mkfs 格式化、修改 fstab、fsck 修复等）仅作为参考提供给用户，由用户自行判断和手动执行。

## 适用场景

### 用户可能的问题表述

**格式化相关**：
- "怎么格式化磁盘"、"mkfs 怎么用"
- "用什么文件系统好"、"ext4 还是 xfs"
- "新分区怎么格式化"、"格式化成 xfs"

**挂载相关**：
- "怎么挂载磁盘"、"mount 怎么用"
- "挂载失败"、"mount: wrong fs type"
- "开机自动挂载怎么配"、"fstab 怎么写"
- "磁盘重启后没挂载"、"fstab 配置不生效"
- "UUID 怎么查"、"用 UUID 挂载"

**fstab 问题**：
- "/etc/fstab 配置错误"、"fstab 写错了进不了系统"
- "fstab 格式是什么"、"fstab 各字段含义"
- "挂载选项有哪些"、"noatime 是什么意思"

**文件系统检查**：
- "文件系统损坏"、"fsck 怎么用"
- "只读文件系统"、"Filesystem is read-only"
- "磁盘报错需要 fsck"
- "怎么检查 xfs 文件系统"、"xfs_repair"

**卸载问题**：
- "umount 失败"、"device is busy"
- "哪个进程在用这个磁盘"
- "强制卸载"

## 诊断步骤（AI 可自动执行）

以下命令为只读查看命令，可由 AI 自动执行。

### 步骤 1：查看文件系统信息

```bash
# 查看所有块设备的文件系统类型
lsblk -f

# 查看指定设备的详细信息（UUID、TYPE、LABEL）
blkid /dev/sdb1

# 查看所有设备
blkid

# 查看当前挂载情况
mount | column -t

# 或更简洁的方式
findmnt

# 查看 fstab 配置
cat /etc/fstab

# 查看支持的文件系统类型
cat /proc/filesystems
```

**文件系统对比**：

| 特性 | ext4 | xfs |
|-----|------|-----|
| 最大文件系统 | 1EB | 8EB |
| 最大文件 | 16TB | 8EB |
| 在线扩容 | ✅ | ✅ |
| 在线缩容 | ✅ | ❌ |
| 适用场景 | 通用 | 大文件、高并发 |

### 步骤 2：排查挂载问题

```bash
# 检查是否已挂载
mount | grep sdb1
findmnt /dev/sdb1

# 查看挂载点
lsblk

# 查看谁在使用该挂载点
fuser -mv /data

# 或使用 lsof
lsof +D /data
```

---

## 操作参考（仅供用户手动执行）

> 🛑 **以下命令涉及格式化/挂载/修改配置操作，AI 不会自动执行！**
> 
> 请用户根据实际情况，自行判断和手动执行。

### 创建文件系统（格式化）

```bash
# ext4 文件系统（通用推荐）
# mkfs.ext4 /dev/sdb1

# ext4 带标签
# mkfs.ext4 -L "DATA" /dev/sdb1

# xfs 文件系统（大文件、高性能推荐）
# mkfs.xfs /dev/sdb1

# xfs 带标签
# mkfs.xfs -L "DATA" /dev/sdb1
```

### 挂载文件系统

```bash
# 临时挂载
# mount /dev/sdb1 /data

# 指定文件系统类型
# mount -t ext4 /dev/sdb1 /data

# 只读挂载
# mount -o ro /dev/sdb1 /data

# 使用 UUID 挂载（推荐）
# mount UUID="xxx-xxx-xxx" /data

# 卸载
# umount /data
# 或
# umount /dev/sdb1

# 强制卸载（设备忙时）
# umount -l /data   # lazy 卸载
# umount -f /data   # 强制卸载（NFS）
```

### 配置开机自动挂载（/etc/fstab）

```bash
# 获取 UUID（此命令可查看）
blkid /dev/sdb1

# 编辑 fstab（手动操作）
# vim /etc/fstab
```

**fstab 格式**：
```
# <设备>                                 <挂载点>  <类型>  <选项>        <dump> <fsck>
UUID=xxx-xxx-xxx-xxx                    /data     ext4    defaults      0      2
/dev/sdb1                               /backup   xfs     defaults      0      0
LABEL=DATA                              /mnt/data ext4    defaults      0      2
```

**字段说明**：

| 字段 | 说明 | 常用值 |
|-----|------|-------|
| 设备 | 推荐使用 UUID | UUID=xxx, /dev/sdb1, LABEL=xxx |
| 挂载点 | 挂载目录 | /data, /mnt/disk1 |
| 类型 | 文件系统类型 | ext4, xfs, nfs |
| 选项 | 挂载选项 | defaults, noatime, ro |
| dump | 备份标志 | 0（不备份） |
| fsck | 检查顺序 | 0（不检查）, 1（根分区）, 2（其他） |

**常用挂载选项**：

```
defaults    # 默认：rw,suid,dev,exec,auto,nouser,async
noatime     # 不更新访问时间（提升性能）
nodiratime  # 不更新目录访问时间
noexec      # 禁止执行程序
nosuid      # 忽略 SUID 位
ro          # 只读
nofail      # 设备不存在时不报错（云盘推荐）
```

```bash
# 验证 fstab 配置（不重启测试）
# mount -a

# 如果有错误，会提示；正确则无输出
```

### 文件系统检查与修复

```bash
# ⚠️ 必须先卸载文件系统！

# ext4 检查
# umount /dev/sdb1
# fsck.ext4 /dev/sdb1

# ext4 自动修复
# fsck.ext4 -y /dev/sdb1

# xfs 检查
# umount /dev/sdb1
# xfs_repair /dev/sdb1

# xfs 强制修复（日志损坏时）
# xfs_repair -L /dev/sdb1
```

## 常见问题排查

### 挂载失败：wrong fs type

```bash
# 错误信息
mount: wrong fs type, bad option, bad superblock

# 排查步骤
# 1. 确认文件系统类型（可自动执行）
blkid /dev/sdb1

# 2. 指定正确的类型（手动执行）
# mount -t xfs /dev/sdb1 /data

# 3. 如果是新磁盘，可能未格式化（手动执行）
# mkfs.ext4 /dev/sdb1
```

### 挂载失败：already mounted

```bash
# 检查是否已挂载（可自动执行）
mount | grep sdb1
findmnt /dev/sdb1
lsblk

# 先卸载再重新挂载（手动执行）
# umount /dev/sdb1
# mount /dev/sdb1 /data
```

### 卸载失败：target is busy

```bash
# 查看谁在使用（可自动执行）
fuser -mv /data
lsof +D /data

# 杀掉使用该目录的进程（手动执行，谨慎！）
# fuser -km /data

# 或 lazy 卸载（手动执行）
# umount -l /data
```

### 启动卡住：fstab 配置错误

```bash
# 进入救援模式后（手动操作）
# 1. 重新挂载根分区为读写
# mount -o remount,rw /

# 2. 编辑 fstab 修复错误
# vim /etc/fstab

# 3. 重启
# reboot

# 预防：云盘使用 nofail 选项
# UUID=xxx  /data  ext4  defaults,nofail  0  2
```

## 相关技能

- **disk-space**：磁盘空间分析与清理
- **disk-partition**：磁盘分区管理
- **disk-lvm**：LVM 逻辑卷管理
