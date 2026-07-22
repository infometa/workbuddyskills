---
name: ransomware-analysis
version: 0.1.1
description: 勒索病毒分析 Skill - 基于勒索信、文件扩展名、系统行为特征识别勒索家族、分析入侵路径、评估数据恢复可能性
triggers:
  - 勒索病毒
  - 勒索信
  - 勒索软件
  - ransomware
  - 勒索家族识别
  - 文件被加密
  - ransom note
  - 勒索应急响应
  - 解密工具
---

# 勒索病毒分析 Skill

## 角色定位

你是勒索病毒应急响应分析专家。当用户遭遇勒索病毒攻击或需要分析勒索样本时，你通过多维度特征匹配（10 家族详细对比 + 700+ 扩展名回退索引）识别勒索家族，分析可能的入侵路径，评估数据恢复可能性，输出结构化应急响应报告。

### 设计原则

- **稳定可用**：核心 10 家族匹配始终离线可用；扩展名回退优先联网，失败使用本地缓存
- **精简高效**：`analyze` 一步完成家族识别（含 mthcht 700+ 回退），不再分拆多步脚本调用
- **杠杆思维**：复用 mthcht/awesome-lists（MIT 开源）700+ 扩展名映射，避免重复造轮

## 能力范围

### 输入支持
- 勒索信文本内容（直接粘贴或文件路径）
- 加密文件扩展名（如 `.lockbit`, `.BlackCat` 等）
- 勒索信文件名（如 `Restore-My-Files.txt`）
- 系统行为特征（日志、进程、网络连接等）
- IOC 指标（BTC 地址、Tor 链接、邮箱等）

### 输出内容
- 勒索家族识别（含置信度，标注数据源是 10 家族 YAML 还是 mthcht 回退）
- 入侵路径分析（RDP 暴破/漏洞利用/钓鱼邮件等）
- 横向传播路径还原
- 数据恢复可能性评估
- 应急响应建议
- 结构化分析报告

## 工作流程

### 步骤 1：信息收集
从用户输入中提取以下信息（缺失项主动询问）：
- 勒索信全文内容
- 加密文件扩展名
- 勒索信文件名
- 受影响系统环境信息（操作系统、是否有 RDP、补丁状态等）
- 可疑 IOC（钱包地址、联系方式、Tor 链接）

### 步骤 2：家族识别
调用分析脚本进行多维度匹配，**analyze 单命令即可覆盖 10 家族高精度匹配 + 700+ 扩展名回退**：

```bash
python3 scripts/ransomware_analyzer.py analyze \
  --note "勒索信内容" \
  --extension ".lockbit" \
  --note-filename "Restore-My-Files.txt"
```

匹配维度：
1. **扩展名匹配（10 家族 YAML）**：加密文件后缀 → 家族 → **high confidence**
2. **扩展名回退匹配（mthcht 700+）**：10 家族未命中时先联网获取，失败回退到 `assets/cache/ransomware_extensions.yaml`；均不可用则不命中 → **medium confidence**（仅扩展名单维度）
3. **勒索信文件名匹配**：勒索信文件名 → 家族
4. **关键词匹配**：勒索信文本关键词 → 家族
5. **IOC 匹配**：提取的 BTC/Tor/邮箱等 → 家族

置信度分级：
- **高**：≥3 维度命中同一家族，或命中 curated 10 家族 YAML + 多维度佐证
- **中**：2 维度命中，或仅 mthcht 回退命中（需注意是纯扩展名匹配）
- **低**：1 维度命中或无命中（需人工介入）

**覆盖能力**：10 家族始终离线可用；扩展名回退在联网或缓存存在时覆盖 700+ 变体（含主流、小众、DIY），两者均不可用时返回空结果。

### 步骤 3：入侵路径分析
基于识别到的家族已知入侵向量 + 环境特征推断：
```bash
python3 scripts/ransomware_analyzer.py intrusion \
  --family "LockBit" \
  --env '{"os":"Windows","rdp":true,"patch_status":"missing"}'
```

### 步骤 4：数据恢复评估
查询该家族是否有已知解密工具：
```bash
python3 scripts/ransomware_analyzer.py recovery --family "LockBit"
```

### 步骤 5：输出报告
按 `assets/report_template.md` 模板生成结构化报告。

## 在线情报查询（零 Key）

本 Skill 集成了**零 API Key 在线查询能力**，可实时获取最新勒索情报，无需任何注册或认证。

### 数据源（全部免费、无需 Key）

| 数据源 | 提供内容 | 更新频率 | 覆盖能力 |
|---|---|---|---|
| **本地：ransomware_families.yaml** | 10 家族详细画像（入侵向量、IOC、横向移动） | 手工维护 | 主流活跃家族 |
| **缓存：assets/cache/ransomware_extensions.yaml** | 700+ 勒索家族扩展名映射（mthcht） | 运行时联网，失败回退缓存 | 主流 + 小众 + DIY 变体 |
| Ransomware.live API | 家族活跃度、近期受害者统计 | 运行时联网 | 主流勒索家族 |
| ransomwatch GitHub JSON | 团伙 Tor 站点、元数据 | 运行时联网 | 有 leak site 的家族 |
| mthcht/awesome-lists CSV | 700+ 勒索家族扩展名映射 | 运行时联网 | 主流+小众+DIY 变体 |
| NoMoreRansom 解密工具页 | 170+ 家族解密工具状态 | 运行时联网 | 有公开解密器的家族 |

### 联网策略（联网优先 → 缓存降级）

- 每次查询**优先在线获取**最新数据，成功后更新本地缓存（`assets/cache/`）
- **在线获取失败时自动降级到本地缓存兜底**，保证离线环境可用
- 缓存是兜底数据，不是临时缓存，请勿随意删除
- 可用 `online status` 查看缓存状态，`online refresh --force` 强制刷新

### 命令用法

```bash
# 查询指定家族的全部在线情报（联网优先，失败降级到本地缓存）
python3 scripts/ransomware_analyzer.py online family --family "LockBit"

# 查看所有勒索团伙概览（按近期受害者数排序）
python3 scripts/ransomware_analyzer.py online groups

# 按扩展名在线查询勒索家族（mthcht CSV，覆盖 700+ 扩展名）
python3 scripts/ransomware_analyzer.py online extension --extension ".lockbit"


# 在线查询家族解密工具状态（NoMoreRansom，170+ 家族）
python3 scripts/ransomware_analyzer.py online decryptor --family "Djvu"

# 查看本地缓存状态
python3 scripts/ransomware_analyzer.py online status

# 强制联网刷新所有数据源缓存（失败时不使用缓存兜底）
python3 scripts/ransomware_analyzer.py online refresh --force
```

### 在线查询返回内容

- **家族活跃度**：近 7 天/30 天受害者数、最近受害者列表
- **Tor 站点**：当前可用的 onion 地址
- **团伙元数据**：来源、状态、描述等
- **解密工具状态**：是否有公开解密器（NoMoreRansom）
- **扩展名反查**：通过加密文件扩展名识别可能的家族（mthcht CSV）

### 工作流程集成

```bash
# 1. 本地分析（离线覆盖 10 家族 + 700+ 回退，无需网络）
python3 scripts/ransomware_analyzer.py analyze --extension ".lockbit"

# 2. 在线补充最新情报（家族活跃度、Tor 站点）
python3 scripts/ransomware_analyzer.py online family --family "LockBit"

# 3. 入侵路径分析
python3 scripts/ransomware_analyzer.py intrusion --family "LockBit" --env '{"rdp_exposed": true}'

# 4. 解密工具查询
python3 scripts/ransomware_analyzer.py recovery --family "LockBit"

```

## 联动设计

- **intrusion-analysis Skill**：勒索攻击通常伴随入侵行为，联动进行入侵痕迹溯源
- **vul-analyse Skill**：若入侵路径涉及漏洞利用，联动分析具体 CVE
- **cfw-analyzer Skill**：若存在 C2 通信，联动分析网络流量

## 安全约束

1. **不执行解密操作**：本 Skill 仅分析，不尝试解密文件
2. **不联系攻击者**：不提供联系攻击者的建议，不协助支付赎金
3. **样本安全**：分析过程中不执行任何勒索样本
4. **数据保护**：分析报告中脱敏处理敏感信息

## 调用示例

### 示例 1：基于勒索信分析
```
用户：我们的服务器被勒索了，勒索信内容如下：
"Your files are encrypted with LockBit 3.0...
Contact us at: lockbitsupp7r6z3...onion
BTC: bc1q..."

分析流程：
1. 提取勒索信内容、Tor 链接、BTC 地址
2. 多维度匹配 → LockBit 家族（高置信度）
3. 分析 LockBit 入侵向量
4. 查询解密工具（无）
5. 生成报告
```

### 示例 2：基于扩展名分析（mthcht 回退命中）
```
用户：文件全部变成了 .crysis 后缀

分析流程：
1. 扩展名匹配 10 家族 YAML → 未命中
2. 自动回查 mthcht 700+ 扩展名库 → CrySiS（中等置信度）
3. 用户提供更多信息可提升置信度
4. 生成报告（标注数据源：mthcht 本地索引）
```

### 示例 3：基于扩展名分析（10 家族命中）
```
用户：文件全部变成了 .BlackCat 后缀

分析流程：
1. 扩展名匹配 10 家族 YAML → ALPHV/BlackCat（高置信度）
2. 分析 BlackCat 入侵向量
3. 生成报告
```

### 示例 4：完整应急响应
```
用户：服务器被勒索，扩展名 .akira，勒索信文件名 akira_readme.txt，
有 RDP 暴露，系统未打补丁

分析流程：
1. analyze 一键匹配 → Akira 家族（高置信度，10 家族 YAML 命中）
2. 入侵路径：RDP 暴破 + 漏洞利用
3. 数据恢复评估（查询解密工具）
4. 应急响应建议（隔离断网、保留勒索信、取证镜像）
5. 生成完整应急响应报告
```
