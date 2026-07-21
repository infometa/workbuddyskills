# 勒索家族技术档案

本文档提供勒索家族的详细技术参考信息，供分析时查阅。

## 目录

1. [LockBit](#lockbit)
2. [BlackCat / ALPHV](#blackcat--alphv)
3. [Phobos](#phobos)
4. [Akira](#akira)
5. [STOP / Djvu](#stop--djvu)
6. [Conti](#conti)
7. [Royal / BlackSuit](#royal--blacksuit)
8. [Play](#play)
9. [BianLian](#bianlian)
10. [Rhysida](#rhysida)

---

## LockBit

### 概述
- **首次出现**: 2019 年 9 月
- **开发者**: LockBit Supp（Russia-linked）
- **运营模式**: RaaS（勒索即服务）
- **当前状态**: 活跃（LockBit 3.0）

### 技术特征
- **加密算法**: AES-256 + RSA-2048
- **加密模式**: 部分文件加密（提高速度）
- **平台**: Windows
- **编程语言**: C/C++

### 攻击链 (MITRE ATT&CK)
1. **初始访问**: T1190 Exploit Public-Facing Application, T1078 Valid Accounts
2. **执行**: T1059 Command and Scripting Interpreter
3. **持久化**: T1547 Boot or Logon Autostart Execution
4. **横向移动**: T1021 Remote Services (SMB/WMI), T1569 System Services (PsExec)
5. **数据窃取**: T1567 Exfiltration Over Web Service
6. **影响**: T1486 Data Encrypted for Impact

### 识别特征
- 扩展名: `.lockbit`, `.lockbit3`, `.abcd`
- 勒索信: `Restore-My-Files.txt`
- 关键词: "LockBit", "lockbitsupp", "unique ID"

### 防御建议
- 禁用 RDP 对公网暴露，启用 NLA
- 部署 EDR 检测横向移动
- 定期备份并离线存储

---

## BlackCat / ALPHV

### 概述
- **首次出现**: 2021 年 11 月
- **运营模式**: RaaS
- **当前状态**: 活跃（2024 年初宣称"关闭"后继续运营）

### 技术特征
- **加密算法**: AES + ChaCha20
- **编程语言**: Rust（跨平台）
- **平台**: Windows, Linux
- **特色**: 支持 Windows/Linux 加密，支持通过命令行参数控制行为

### 攻击链
1. **初始访问**: T1190, T1078
2. **执行**: T1059
3. **凭据访问**: T1003 OS Credential Dumping (Mimikatz)
4. **横向移动**: T1021, T1570 Lateral Tool Transfer
5. **数据窃取**: T1567
6. **影响**: T1486

### 识别特征
- 扩展名: `.blackcat`, `.alphv`, `.alphvv`
- 勒索信: `RECOVER-FILES.txt`
- 关键词: "BlackCat", "ALPHV", "double extortion"

---

## Phobos

### 概述
- **首次出现**: 2019 年 1 月
- **运营模式**: 独立运营（非 RaaS）
- **当前状态**: 活跃（多个变体持续更新）

### 技术特征
- **加密算法**: AES + RSA
- **编程语言**: C/C++
- **平台**: Windows

### 攻击链
1. **初始访问**: T1110 Brute Force (RDP)
2. **执行**: T1059
3. **横向移动**: T1021
4. **影响**: T1486

### 识别特征
- 扩展名变体极多: `.phobos`, `.faust`, `.devicdata`, `.elking`, `.eight`
- 勒索信: `info.txt`, `info.hta`
- 关键词: "Phobos", "write to us"

---

## Akira

### 概述
- **首次出现**: 2023 年 3 月
- **来源**: 前 Conti 成员
- **当前状态**: 活跃

### 技术特征
- **编程语言**: C++（Windows）, Rust（Linux）
- **平台**: Windows, Linux

### 攻击链
1. **初始访问**: T1190（Cisco AnyConnect 漏洞）, T1078（VPN 凭据）
2. **执行**: T1059
3. **横向移动**: T1021, T1570
4. **数据窃取**: T1567
5. **影响**: T1486

### 识别特征
- 扩展名: `.akira`
- 勒索信: `akira_readme.txt`

---

## STOP / Djvu

### 概述
- **首次出现**: 2018 年 2 月
- **运营模式**: 独立运营
- **当前状态**: 活跃（扩展名变体持续增加）

### 技术特征
- **加密算法**: Salsa20 + RSA-2048
- **编程语言**: C/C++
- **平台**: Windows

### 攻击链
1. **初始访问**: 通过软件破解/广告软件分发
2. **执行**: T1059
3. **影响**: T1486

### 识别特征
- 扩展名变体超过 300 个: `.djvu`, `.djvuu`, `.stop` 等
- 勒索信: `_readme.txt`
- 关键词: "STOP", "gorentos@bitmessage.ch"

---

## Conti

### 概述
- **首次出现**: 2020 年 5 月
- **运营者**: Wizard Spider
- **当前状态**: 2022 年解散，源码泄露后衍生多个家族

### 技术特征
- **加密算法**: AES-256 + RSA-4096
- **编程语言**: C/C++
- **平台**: Windows

### 识别特征
- 扩展名: `.conti`
- 勒索信: `CONTI_README.txt`

---

## Royal / BlackSuit

### 概述
- **首次出现**: 2022 年 9 月
- **来源**: 前 Conti 成员
- **当前状态**: 活跃

### 技术特征
- **加密算法**: AES + RSA
- **编程语言**: C++
- **平台**: Windows
- **特色**: 部分加密以加快速度

### 识别特征
- 扩展名: `.royal`, `.blacksuit`
- 勒索信: `Royal_Readme.txt`

---

## Play

### 概述
- **首次出现**: 2022 年 6 月
- **当前状态**: 活跃

### 技术特征
- **编程语言**: C/C++
- **平台**: Windows

### 攻击链
1. **初始访问**: T1190（Exchange ProxyShell/ProxyNotShell）
2. **横向移动**: T1059（PowerShell + Cobalt Strike）
3. **影响**: T1486

### 识别特征
- 扩展名: `.play`
- 勒索信: `Readme.txt`（简洁）

---

## BianLian

### 概述
- **首次出现**: 2022 年 8 月
- **当前状态**: 活跃（逐渐转向纯数据勒索）

### 技术特征
- **编程语言**: Go
- **平台**: Windows

### 攻击链
1. **初始访问**: T1190（SonicWall 漏洞）, T1078
2. **数据窃取**: T1567
3. **影响**: T1486（逐渐减少）

### 识别特征
- 扩展名: `.bianlian`
- 勒索信: `look at this.txt`

---

## Rhysida

### 概述
- **首次出现**: 2023 年 5 月
- **当前状态**: 活跃
- **目标行业**: 教育、医疗、政府

### 技术特征
- **编程语言**: C/C++
- **平台**: Windows

### 攻击链
1. **初始访问**: T1566 Phishing, T1190
2. **横向移动**: T1059（Cobalt Strike）
3. **数据窃取**: T1567
4. **影响**: T1486

### 识别特征
- 扩展名: `.rhysida`, `.locked`
- 勒索信: `CriticalBreachDetected.pdf`

---

## 参考资料

- [MITRE ATT&CK](https://attack.mitre.org/)
- [NoMoreRansom](https://www.nomoreransom.org/)
- [ID Ransomware](https://id-ransomware.malwarehunterteam.com/)
- [CISA Ransomware Guidance](https://www.cisa.gov/stopransomware)
- [VirusTotal](https://www.virustotal.com/)
