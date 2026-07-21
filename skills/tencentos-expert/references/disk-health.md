---
name: disk-health
description: 磁盘健康状态检测，包括 SMART 信息查看、 坏块检测和磁盘故障预警。
description_zh: 磁盘健康状态检测与故障预警
description_en: Disk health monitoring with SMART analysis and failure prediction
version: 1.0.0
---

# 磁盘健康检测

帮助检测磁盘健康状态，通过 SMART 信息分析磁盘寿命和潜在故障风险。

## 安全原则

> ⚠️ **重要**：AI 只执行诊断命令（查看、分析），**不自动执行任何破坏性操作**。
> 
> 涉及数据破坏的操作（如 badblocks 写入测试）仅作为参考提供给用户，由用户自行判断和手动执行。

## 适用场景

### 用户可能的问题表述

**磁盘健康检查**：
- "磁盘健康状态"、"磁盘有没有问题"
- "SMART 信息怎么看"、"smartctl 怎么用"
- "磁盘寿命还有多久"、"SSD 写入量查询"
- "磁盘会不会坏"、"需要换盘吗"

**故障预警**：
- "磁盘报警了"、"SMART 告警"
- "Reallocated Sector 是什么意思"、"重映射扇区数"
- "Pending Sector"、"等待重映射扇区"
- "磁盘温度过高"

**坏块检测**：
- "磁盘有坏块吗"、"怎么检测坏块"
- "badblocks 怎么用"
- "磁盘读写报错"、"I/O error"

**NVMe 磁盘**：
- "NVMe 健康状态"、"nvme smart-log"
- "NVMe 磁盘寿命"、"percentage_used"
- "nvme-cli 怎么用"

**性能测试**：
- "磁盘速度怎么样"、"磁盘性能测试"
- "hdparm 测速"、"fio 测试"
- "磁盘 IO 慢"、"磁盘性能下降"

## 前置准备

```bash
# 安装 smartmontools
yum install -y smartmontools

# 启动 smartd 服务（可选，用于持续监控）
systemctl enable --now smartd
```

## 诊断步骤

### 步骤 1：查看磁盘基本信息

```bash
# 列出所有磁盘
lsblk -d -o NAME,SIZE,MODEL,SERIAL

# 查看磁盘详细信息
smartctl -i /dev/sda

# 检查磁盘是否支持 SMART
smartctl -a /dev/sda | grep "SMART support"
```

### 步骤 2：查看 SMART 健康状态

```bash
# 快速健康检查
smartctl -H /dev/sda

# 输出示例：
# SMART overall-health self-assessment test result: PASSED
# 如果显示 FAILED，磁盘可能即将故障！

# 查看完整 SMART 信息
smartctl -a /dev/sda

# 只看关键属性
smartctl -A /dev/sda
```

### 步骤 3：解读关键 SMART 属性

```bash
smartctl -A /dev/sda
```

**关键指标解读**：

| ID | 属性名 | 说明 | 警戒值 |
|----|-------|------|--------|
| 5 | Reallocated_Sector_Ct | 重映射扇区数 | > 0 需关注 |
| 187 | Reported_Uncorrect | 无法修正的错误 | > 0 需关注 |
| 188 | Command_Timeout | 命令超时次数 | 持续增长需关注 |
| 197 | Current_Pending_Sector | 待重映射扇区 | > 0 需关注 |
| 198 | Offline_Uncorrectable | 离线无法修正扇区 | > 0 需关注 |
| 199 | UDMA_CRC_Error_Count | CRC 校验错误 | 持续增长检查线缆 |

**RAW_VALUE 列**是实际数值，**VALUE** 列是归一化值（越低越差）。

### 步骤 4：运行 SMART 自检

```bash
# 短时自检（约 2 分钟）
smartctl -t short /dev/sda

# 长时自检（可能需要数小时）
smartctl -t long /dev/sda

# 查看自检进度
smartctl -c /dev/sda

# 查看自检结果
smartctl -l selftest /dev/sda
```

### 步骤 5：坏块检测

```bash
# ⚠️ 警告：以下操作耗时长，对磁盘有一定压力

# 只读检测（不破坏数据）
badblocks -sv /dev/sdb

# 只读检测，输出到文件
badblocks -sv -o /tmp/badblocks.txt /dev/sdb

# 读写检测（⚠️ 会破坏数据！仅用于新磁盘，手动执行）
# badblocks -wsv /dev/sdb
```

### 步骤 6：NVMe 磁盘检测

```bash
# NVMe 磁盘使用不同的命令
# 安装 nvme-cli
yum install -y nvme-cli

# 查看 NVMe 设备
nvme list

# 查看 SMART 信息
nvme smart-log /dev/nvme0n1

# 关键指标：
# - percentage_used: 磨损百分比（超过 100% 需更换）
# - available_spare: 可用备用块百分比
# - media_errors: 介质错误数
```

## 健康状态判断

### 🟢 健康

- SMART overall-health: PASSED
- Reallocated_Sector_Ct = 0
- Current_Pending_Sector = 0
- 无自检错误

### 🟡 需关注

- Reallocated_Sector_Ct > 0 但稳定
- UDMA_CRC_Error_Count 有增长（可能是线缆问题）
- 温度偏高（> 50°C）

### 🔴 建议更换

- SMART overall-health: FAILED
- Reallocated_Sector_Ct 持续增长
- Current_Pending_Sector > 0
- 自检失败
- NVMe percentage_used > 100%

## 持续监控配置

```bash
# 配置 smartd 进行持续监控
vim /etc/smartd.conf

# 添加监控规则（每天检测一次，发现问题发邮件）
/dev/sda -a -o on -S on -s (S/../.././02|L/../../6/03) -m admin@example.com

# 重启服务
systemctl restart smartd

# 查看日志
journalctl -u smartd
```

## 磁盘性能测试

```bash
# 使用 hdparm 测试读取速度
hdparm -tT /dev/sda

# 使用 dd 测试写入速度（谨慎！会创建大文件）
dd if=/dev/zero of=/tmp/testfile bs=1G count=1 oflag=dsync

# 使用 fio 进行专业测试（需安装）
# TencentOS 2: yum install -y fio
# TencentOS 3/4: dnf install -y fio
fio --name=randread --ioengine=libaio --rw=randread --bs=4k --numjobs=4 \
    --size=1G --runtime=60 --time_based --filename=/dev/sdb
```

## 相关技能

- **disk-space**：磁盘空间分析与清理
- **disk-partition**：磁盘分区管理
- **disk-filesystem**：文件系统管理
