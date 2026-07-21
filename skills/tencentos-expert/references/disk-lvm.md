---
name: disk-lvm
description: LVM（逻辑卷管理）的创建、扩容、快照等操作。 包括 PV、VG、LV 的完整生命周期管理。
description_zh: LVM 逻辑卷管理（创建、扩容、快照）
description_en: LVM logical volume management including creation, expansion and snapshots
version: 1.0.0
---

# LVM 逻辑卷管理

帮助进行 LVM（逻辑卷管理）的创建、扩容、快照等操作，实现灵活的磁盘空间管理。

## 安全原则

> ⚠️ **重要**：AI 只执行诊断命令（查看、分析），**不自动执行任何创建/删除/格式化操作**。
> 
> 涉及数据的操作（如 pvcreate、vgcreate、lvcreate、lvremove、mkfs 等）仅作为参考提供给用户，由用户自行判断和手动执行。

## 适用场景

### 用户可能的问题表述

**LVM 查看**：
- "查看 LVM 信息"、"pvs/vgs/lvs"
- "逻辑卷有多大"、"VG 剩余空间"
- "LVM 结构是什么样的"

**扩容需求**（最常见）：
- "磁盘怎么扩容"、"在线扩容"
- "LV 怎么扩展"、"lvextend 怎么用"
- "加了新盘怎么扩容"、"把新磁盘加到 LVM"
- "云盘扩容后怎么让系统识别"
- "扩容后空间没生效"、"resize2fs / xfs_growfs"

**创建 LVM**：
- "怎么创建 LVM"、"LVM 怎么配置"
- "pvcreate / vgcreate / lvcreate 怎么用"
- "把两块盘合成一个"、"跨盘存储"

**快照相关**：
- "LVM 快照怎么创建"、"lvcreate -s"
- "从快照恢复"、"快照回滚"
- "快照占用空间"

**缩容/删除**：
- "LV 怎么缩小"、"lvreduce"（⚠️ 危险）
- "删除逻辑卷"、"lvremove"
- "移除物理卷"、"pvmove / vgreduce"

**问题排查**：
- "LVM 报错"、"VG 无法激活"
- "PV 丢失"、"vgchange"
- "LVM 元数据损坏"

## LVM 基础概念

```
┌──────────────────────────────────────────────────────┐
│                    文件系统                           │
│                   /dev/vg01/lv01                      │
├──────────────────────────────────────────────────────┤
│                   逻辑卷 (LV)                         │
│                    lv01 (100G)                        │
├──────────────────────────────────────────────────────┤
│                    卷组 (VG)                          │
│                    vg01 (200G)                        │
├────────────────────┬─────────────────────────────────┤
│   物理卷 (PV)       │        物理卷 (PV)              │
│  /dev/sdb1 (100G)   │      /dev/sdc1 (100G)          │
├────────────────────┴─────────────────────────────────┤
│                  物理磁盘                             │
│              /dev/sdb    /dev/sdc                     │
└──────────────────────────────────────────────────────┘
```

**术语说明**：
- **PV (Physical Volume)**：物理卷，可以是整个磁盘或分区
- **VG (Volume Group)**：卷组，由一个或多个 PV 组成
- **LV (Logical Volume)**：逻辑卷，从 VG 中划分，可格式化使用

## 诊断步骤（AI 可自动执行）

以下命令为只读查看命令，可由 AI 自动执行。

### 查看 LVM 信息

```bash
# 查看物理卷
pvs
pvdisplay

# 查看卷组
vgs
vgdisplay

# 查看逻辑卷
lvs
lvdisplay

# 查看所有 LVM 信息
lsblk
```

---

## 操作参考（仅供用户手动执行）

> 🛑 **以下命令涉及创建/删除/格式化操作，AI 不会自动执行！**
> 
> 请用户根据实际情况，自行判断和手动执行。

### 创建 LVM（完整流程）

```bash
# 假设使用 /dev/sdb 和 /dev/sdc 两块新磁盘

# 1. 创建物理卷
# pvcreate /dev/sdb /dev/sdc

# 验证（可自动执行）
pvs

# 2. 创建卷组
# vgcreate vg_data /dev/sdb /dev/sdc

# 验证（可自动执行）
vgs

# 3. 创建逻辑卷
# 指定大小
# lvcreate -L 100G -n lv_data vg_data

# 或使用所有剩余空间
# lvcreate -l 100%FREE -n lv_data vg_data

# 或使用百分比
# lvcreate -l 80%VG -n lv_data vg_data

# 验证（可自动执行）
lvs

# 4. 格式化
# mkfs.ext4 /dev/vg_data/lv_data
# 或
# mkfs.xfs /dev/vg_data/lv_data

# 5. 挂载
# mkdir -p /data
# mount /dev/vg_data/lv_data /data

# 6. 配置开机自动挂载
# echo "/dev/vg_data/lv_data /data ext4 defaults 0 2" >> /etc/fstab
```

### 扩展逻辑卷（在线扩容）

这是 LVM 最常用的功能！

#### 场景 A：VG 有剩余空间

```bash
# 1. 查看 VG 剩余空间（可自动执行）
vgs

# 2. 扩展 LV（手动执行）
# 增加 50G
# lvextend -L +50G /dev/vg_data/lv_data

# 或扩展到 200G
# lvextend -L 200G /dev/vg_data/lv_data

# 或使用所有剩余空间
# lvextend -l +100%FREE /dev/vg_data/lv_data

# 3. 扩展文件系统（手动执行）
# ext4:
# resize2fs /dev/vg_data/lv_data

# xfs:
# xfs_growfs /data

# 一步完成（推荐）
# lvextend -L +50G /dev/vg_data/lv_data --resizefs
```

#### 场景 B：需要添加新磁盘

```bash
# 1. 添加新磁盘为物理卷（手动执行）
# pvcreate /dev/sdd

# 2. 扩展卷组（手动执行）
# vgextend vg_data /dev/sdd

# 3. 扩展逻辑卷（手动执行）
# lvextend -l +100%FREE /dev/vg_data/lv_data --resizefs

# 验证（可自动执行）
df -h /data
```

### 创建快照

LVM 快照用于备份或测试。

```bash
# 创建快照（需要 VG 有剩余空间，手动执行）
# lvcreate -L 10G -s -n lv_data_snap /dev/vg_data/lv_data

# 查看快照（可自动执行）
lvs

# 挂载快照（只读，手动执行）
# mkdir -p /mnt/snap
# mount -o ro /dev/vg_data/lv_data_snap /mnt/snap

# 从快照恢复（⚠️ 危险操作，会覆盖原数据，手动执行）
# umount /data
# lvconvert --merge /dev/vg_data/lv_data_snap

# 删除快照（手动执行）
# lvremove /dev/vg_data/lv_data_snap
```

### 缩小逻辑卷

> ⚠️ 警告：缩小操作有风险！必须先备份！XFS 不支持缩小！

```bash
# 仅 ext4 支持！以下命令需手动执行

# 1. 卸载
# umount /data

# 2. 检查文件系统
# e2fsck -f /dev/vg_data/lv_data

# 3. 缩小文件系统到 50G
# resize2fs /dev/vg_data/lv_data 50G

# 4. 缩小 LV 到 50G
# lvreduce -L 50G /dev/vg_data/lv_data

# 5. 重新挂载
# mount /dev/vg_data/lv_data /data
```

## 常见问题排查

### 扩容后空间未生效

```bash
# 确认 LV 已扩展（可自动执行）
lvs

# 确认文件系统已扩展（可自动执行）
df -h

# 如果文件系统未扩展，手动执行：
# ext4:
# resize2fs /dev/vg_data/lv_data

# xfs:
# xfs_growfs /data
```

### PV 无法删除

```bash
# 查看 PV 使用情况（可自动执行）
pvdisplay /dev/sdb

# 如果有数据，先迁移（手动执行）
# pvmove /dev/sdb

# 然后从 VG 移除（手动执行）
# vgreduce vg_data /dev/sdb

# 最后删除 PV（手动执行）
# pvremove /dev/sdb
```

### LV 删除

```bash
# 以下命令需手动执行

# 1. 卸载
# umount /data

# 2. 删除 LV
# lvremove /dev/vg_data/lv_data

# 3. 如果要删除 VG
# vgremove vg_data

# 4. 如果要删除 PV
# pvremove /dev/sdb /dev/sdc
```

## 云服务器扩容实战

腾讯云/阿里云等云服务器扩容数据盘：

```bash
# 以下命令需手动执行

# 1. 控制台扩容磁盘后，刷新磁盘信息
# SCSI 磁盘：
# echo 1 > /sys/block/sdb/device/rescan

# virtio 磁盘：
# 可能需要重启或使用 qemu-guest-agent

# 2. 扩展物理卷
# pvresize /dev/sdb

# 3. 扩展逻辑卷
# lvextend -l +100%FREE /dev/vg_data/lv_data --resizefs

# 4. 验证（可自动执行）
df -h
```

## 相关技能

- **disk-space**：磁盘空间分析与清理
- **disk-partition**：磁盘分区管理
- **disk-filesystem**：文件系统管理
