# Windows 系统日志收集工具

## 概述

这是一个功能强大的Windows系统日志收集工具，专门用于收集和分析Windows系统的各种日志信息，特别适用于安全事件调查、系统故障排查和勒索病毒溯源分析。

**更新时间：** 2026-03-23

## 系统要求

- Windows操作系统
- **管理员权限**（必须）
- **PowerShell 3.0 及以上版本**（必须）
  - 脚本使用了 `[ordered]@{}`、`[PSCustomObject]@{}` 等 PowerShell 3.0+ 语法特性
  - 如需安装或升级 PowerShell，请参考：[安装 PowerShell（Microsoft 官方文档）](https://learn.microsoft.com/en-us/powershell/scripting/install/install-powershell-on-windows?view=powershell-7.5#msi)
  - 可通过 `$PSVersionTable.PSVersion` 命令查看当前版本
- 足够的磁盘空间存储日志文件

## 使用方式

### 1. 运行脚本

1. 以**管理员身份**打开Powershell
2. 导航到脚本所在目录
3. 运行脚本：
   ```powershell
   get_log_all_in_one.ps1
   ```

### 2. 选择执行模式

脚本启动后会显示菜单，您可以选择：

- **0 或 回车** - 执行所有步骤（推荐，默认选项）
- **1-9** - 执行特定步骤

### 3. 菜单选项说明

| 选项 | 功能描述              |
|----|-------------------|
| 0  | 执行所有步骤（默认）        |
| 1  | 收集系统基本信息          |
| 2  | 收集关键安全事件和关键系统事件   |
| 3  | 收集进程信息              |
| 4  | 收集网络配置信息          |
| 5  | 检查并收集IIS日志        |
| 6  | 收集自启动项信息          |
| 7  | 收集USN日志（文件系统变更记录） |
| 8  | 检查常见文件夹二进制数字签名    |
| 9  | 收集 PSReadLine 命令历史 |

## 功能清单

### 核心功能

1. **系统基本信息收集**
   - 系统详细信息
   - 用户账户信息
   - 网络配置
   - 运行进程和服务

2. **Windows事件日志导出**
   - 安全日志（Security）
   - 系统日志（System）
   - 应用程序日志（Application）

3. **关键安全事件分析**
   - 登录成功/失败事件
   - 特权登录事件
   - 账户创建事件
   - 服务安装事件

4. **进程监控**
   - 进程详细信息
   - 服务安装事件（7045）
   - 服务启动类型变更事件（7040）

5. **自启动项全面收集**
   - 注册表启动项
   - 启动文件夹内容
   - WMI启动命令
   - MSConfig已禁用启动项
   - 计划任务启动项
   - 浏览器扩展

6. **文件系统变更追踪**
   - USN日志收集
   - 文件系统变更记录
   - 支持多驱动器

7. **网络和Web服务**
   - 网络连接状态
   - IIS日志收集
   - 防火墙配置

### 高级功能

- **错误处理**：完善的错误处理和权限检查
- **进度显示**：实时显示收集进度

## 输出文件说明

log_COMPUTERNAME_yyyyMMdd_HHmmss.txt : 输出报告本体

### 原始报告结构（输入）

```
log_COMPUTERNAME_yyyyMMdd_HHmmss.txt
├── 采集信息 (_CollectionMeta)      # 运行时参数与机器标识
├── 执行耗时 (_ExecutionTiming)      # 各步骤耗时统计
├── [1] 系统基本信息 (SystemInfo)    # 系统基础信息
├── [2] 关键安全事件 (SystemEvent)   # 系统日志信息
├── [3] 进程信息 (Processes)         # 进程信息
├── [4] 网络配置信息 (Network)       # 网络信息
├── [5] IIS日志 (IISLogs)            # IIS日志（如果存在）
├── [6] 自启动项信息 (Startup)       # 启动项信息
├── [7] USN日志 (USNLogs)            # USN日志
├── [8] 文件数字签名 (CheckSignature)# 常见目录的签名检查信息
└── [9] PSReadLine命令历史           # PSReadLine 命令历史
```

### 日志来源列表

| 日志类型            | 日志来源                                                        | 具体内容            | 输出位置           | 修改时间       |
|-----------------|-------------------------------------------------------------|-----------------|----------------|------------|
| 系统信息            | Cmdlet: Get-CimInstance                                     | 系统详细信息          | SystemInfo     | 2025年9月22日 |
| 用户信息            | whoami.exe                                                  | 当前用户信息          | SystemInfo     | 2025年9月22日 |
| 用户管理            | Cmdlet: Get-LocalUser; net.exe(不兼容Cmdlet时)                  | 系统用户列表          | SystemInfo     | 2025年9月22日 |
| 权限管理            | Cmdlet: Get-LocalGroupMember; net.exe(不兼容Cmdlet时)           | 管理员组成员          | SystemInfo     | 2025年9月22日 |
| 网络共享            | Cmdlet: Get-SmbShare                                        | 网络共享信息          | SystemInfo     | 2025年9月22日 |
| 安全日志(Security)  | Cmdlet: Get-WinEvent                                        | 重要安全事件日志        | SystemEvent    | 2025年9月22日 |
| 系统日志(System)    | Cmdlet: Get-WinEvent                                        | 重要系统事件日志        | SystemEvent    | 2025年9月22日 |
| 进程列表            | Cmdlet: Get-Process                                         | 进程列表            | Processes      | 2025年9月22日 |
| 网络配置            | Cmdlet: Get-NetAdapter                                      | IP配置信息          | Network        | 2025年9月22日 |
| 路由信息            | Cmdlet: Get-NetRoute                                        | 路由表             | Network        | 2025年9月22日 |
| ARP表            | Cmdlet: Get-NetNeighbor                                     | ARP缓存           | Network        | 2025年9月22日 |
| 防火墙配置           | Cmdlet: Get-NetFirewallProfile; Cmdlet: Get-NetFirewallRule | 防火墙设置           | Network        | 2025年9月22日 |
| 网络连接            | Cmdlet: Get-NetTCPConnection; Cmdlet: Get-NetUDPEndpoint    | 网络连接状态          | Network        | 2025年9月22日 |
| Web服务器日志        | Cmdlet: Copy-Item                                           | IIS访问日志         | IISLogs        | 2025年9月22日 |
| 自启动项            | Cmdlet: Get-ChildItem                                       | 启动文件夹内容信息       | Startup        | 2025年9月22日 |
| 自启动项            | Cmdlet: Get-WmiObject                                       | WMI自启动命令        | Startup        | 2025年9月22日 |
| 自启动项            | Cmdlet: Get-WmiObject                                       | WMI自启动服务        | Startup        | 2025年9月22日 |
| 自启动项            | Cmdlet: Get-ItemProperty                                    | 注册表：MSConfig启动项 | Startup        | 2025年9月22日 |
| 自启动项            | Cmdlet: Get-ItemProperty                                    | 注册表：常见启动项内容     | Startup        | 2025年9月22日 |
| 自启动项            | Cmdlet: Get-ItemProperty                                    | 注册表：浏览器扩展启动项    | Startup        | 2025年9月22日 |
| 自启动项            | Cmdlet: Get-ScheduledTask                                   | 计划任务列表          | Startup        | 2025年9月22日 |
| 文件系统变更          | fsutil.exe                                                  | 文件系统变更记录(原始)    | USNLogs        | 2025年9月22日 |
| 文件系统变更          | fsutil.exe                                                  | 文件系统变更记录(解析)    | USNLogs        | 2025年9月22日 |
| 系统常见文件夹中签名验证失败项 | Cmdlet: Get-AuthenticodeSignature; Cmdlet: Get-FileHash     | 签名无效的文件哈希值      | CheckSignature | 2025年9月22日 |

## 使用建议

### 日常使用

1. **完整检查**：运行默认选项（0）获取完整系统状态
2. **定向分析**：根据需要选择特定步骤
3. **定期收集**：建议定期运行以建立基线

### 安全事件调查

1. **登录分析**：重点关注 `SystemEvent/Security/login_failed_4625` 查找暴力破解攻击
2. **服务监控**：检查 `SystemEvent/System/service_install_7045` 查找可疑服务安装
3. **持久化检测**：分析 `Startup` 下的自启动项
4. **文件追踪**：使用USN日志追踪文件系统变更
5. **命令历史**：检查 `PSReadLineHistory` 查找可疑 PowerShell 命令

### 勒索病毒溯源分析

**重点分析文件优先级：**

- **极高优先级**：`USNLogs`（文件加密行为直接证据）
- **高优先级**：`IISLogs`（网站入侵、SQL注入迹象）
- **高优先级**：`Startup`（恶意软件持久化机制）
- **高优先级**：`SystemEvent/System/service_install_7045`（可疑服务安装）

## 注意事项

1. **权限要求**：必须以管理员身份运行
2. **磁盘空间**：确保有足够空间存储日志文件
3. **运行时间**：完整收集可能需要几分钟到十几分钟
4. **系统影响**：收集过程对系统性能影响较小
5. **数据安全**：收集的日志可能包含敏感信息

## 故障排除

### 常见问题（FAQ）

1. **权限不足**：确保以管理员身份运行
2. **USN日志收集失败**：某些驱动器可能未启用USN日志
3. **IIS日志未找到**：系统可能未安装IIS

### 错误处理

脚本内置了完善的错误处理机制：
- 自动检测管理员权限
- 跳过不可用的功能
- 提供详细的错误信息
- 继续执行其他可用步骤

## 技术支持

如遇到问题或需要技术支持，请：
1. 检查是否以管理员权限运行
2. 查看生成的错误日志
3. 确认系统兼容性
4. 联系技术支持团队