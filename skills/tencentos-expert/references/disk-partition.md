---
name: disk-partition
description: 磁盘分区查看、创建、删除和调整。 支持 MBR 和 GPT 分区表管理。
description_zh: 磁盘分区管理（MBR/GPT）
description_en: Disk partition management supporting MBR and GPT partition tables
version: 1.0.0
---

# 磁盘分区管理

帮助查看、创建、删除和调整磁盘分区，支持 MBR 和 GPT 分区表。

## 安全原则

> ⚠️ **重要**：AI 只执行诊断命令（查看、分析），**不自动执行任何分区/格式化操作**。
> 
> 涉及数据破坏的操作（如 fdisk 写入、parted 创建、mkfs 格式化等）仅作为参考提供给用户，由用户自行判断和手动执行。

## 适用场景

### 用户可能的问题表述

**查看分区信息**：
- "查看磁盘分区"、"看下分区情况"
- "lsblk"、"fdisk -l"、"有几块磁盘"
- "磁盘是 GPT 还是 MBR"、"分区表类型是什么"
- "这块盘有多大"、"磁盘容量多少"

**新磁盘处理**：
- "新加了一块磁盘怎么用"、"新磁盘怎么分区"
- "云盘挂载上来了怎么用"、"数据盘怎么初始化"
- "/dev/sdb 是新加的盘，怎么分区"
- "磁盘分区规划建议"

**分区操作**：
- "怎么用 fdisk 分区"、"parted 怎么用"
- "创建一个 100G 的分区"、"把磁盘分成两个区"
- "删除分区"、"调整分区大小"
- "MBR 转 GPT"、"分区表转换"

**分区问题排查**：
- "分区识别不到"、"磁盘不显示"
- "分区丢失"、"分区表损坏"
- "超过 2TB 的盘怎么分区"（需要 GPT）

## 诊断步骤（AI 可自动执行）

以下命令为只读查看命令，可由 AI 自动执行。

### 步骤 1：查看磁盘和分区信息

```bash
# 查看所有块设备（推荐，直观的树形结构）
lsblk

# 查看详细信息（包含文件系统类型、UUID、挂载点）
lsblk -f

# 查看磁盘大小和分区
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT

# 查看所有磁盘（包括未分区的）
fdisk -l

# 查看指定磁盘
fdisk -l /dev/sdb
```

### 步骤 2：识别分区表类型

```bash
# 查看分区表类型（MBR/GPT）
fdisk -l /dev/sda | grep "Disklabel type"

# 或使用 parted
parted /dev/sda print | grep "Partition Table"

# 或使用 blkid
blkid -o value -s PTTYPE /dev/sda
```

**分区表对比**：

| 特性 | MBR | GPT |
|-----|-----|-----|
| 最大磁盘容量 | 2TB | 无限制 |
| 最大分区数 | 4 主分区 | 128 分区 |
| UEFI 支持 | 不支持 | 支持 |
| 推荐场景 | 旧系统兼容 | 新系统、大磁盘 |

---

## 操作参考（仅供用户手动执行）

> 🛑 **以下命令涉及分区/格式化操作，AI 不会自动执行！**
> 
> 请用户根据实际情况，自行判断和手动执行。

### 创建分区（MBR 分区表）

```bash
# 交互式创建分区
fdisk /dev/sdb

# fdisk 常用命令：
# p - 打印分区表
# n - 新建分区
# d - 删除分区
# t - 更改分区类型
# w - 写入并退出
# q - 不保存退出

# 非交互式创建分区（脚本化）
# echo -e "n\np\n1\n\n\nw" | fdisk /dev/sdb
```

### 创建分区（GPT 分区表）

```bash
# 使用 parted（推荐用于 GPT）
parted /dev/sdb

# parted 常用命令：
# print - 显示分区信息
# mklabel gpt - 创建 GPT 分区表
# mkpart primary ext4 0% 100% - 创建分区
# rm 1 - 删除分区 1
# quit - 退出

# 非交互式创建 GPT 分区
# parted -s /dev/sdb mklabel gpt
# parted -s /dev/sdb mkpart primary ext4 0% 100%

# 或使用 gdisk（GPT fdisk）
# gdisk /dev/sdb
```

### 分区后续操作

```bash
# 通知内核重新读取分区表
partprobe /dev/sdb

# 或
blockdev --rereadpt /dev/sdb

# 验证分区已创建
lsblk /dev/sdb
```

### 新磁盘完整分区流程

```bash
# 1. 确认磁盘（假设新磁盘是 /dev/sdb）
lsblk
fdisk -l /dev/sdb

# 2. 创建 GPT 分区表（大于 2TB 或新系统推荐）
# parted -s /dev/sdb mklabel gpt

# 3. 创建一个占满整个磁盘的分区
# parted -s /dev/sdb mkpart primary ext4 0% 100%

# 4. 验证分区
lsblk /dev/sdb

# 5. 格式化（见 disk-filesystem 技能）
# mkfs.ext4 /dev/sdb1

# 6. 挂载使用（见 disk-filesystem 技能）
# mount /dev/sdb1 /data
```

### 扩展分区（非 LVM）

> ⚠️ 警告：扩展分区有数据丢失风险，请先备份！

```bash
# 使用 growpart 扩展分区（云服务器常用）
# growpart /dev/vda 1

# 扩展文件系统
# ext4:
# resize2fs /dev/vda1

# xfs:
# xfs_growfs /dev/vda1
```

## 注意事项

1. **备份重要数据**：分区操作有风险，务必提前备份
2. **不要操作系统盘**：除非你知道自己在做什么
3. **GPT 优先**：新系统、大磁盘优先使用 GPT
4. **分区对齐**：使用 parted 的百分比方式可自动对齐

## 相关技能

- **disk-space**：磁盘空间分析与清理
- **disk-filesystem**：文件系统创建与挂载
- **disk-lvm**：LVM 逻辑卷管理
