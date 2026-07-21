# Intrusion Analysis Skill

🔒 入侵检测排查分析 Skill — 支持 **Windows** 和 **Linux**，从标准化日志报告中自动执行 AI 安全分析与入侵溯源。

## 概述

本项目是一个 **AI Agent 流程编排 Skill**，用于自动化入侵检测排查分析。在目标服务器上运行轻量级日志采集脚本，生成标准化纯文本日志报告（`.txt`），AI 系统性地执行安全分析管线，生成结构化的入侵检测排查分析报告。

### 工作流程

**Windows：**
```
PS1 采集 → preanalyze.py 预分析 → AI 深度分析 → 按需回查 → 分析报告
```

**Linux：**
```
Bash 采集 → preanalyze.py 预分析 → AI 深度分析 → 按需回查 → 分析报告
```

### 分析维度

| Windows（9 维度） | Linux（9 维度） |
|-------------------|-----------------|
| 系统画像（OS/用户/管理员组/安全配置） | 系统画像（OS/用户/sudoers/SELinux/AppArmor） |
| 登录活动（4624/4625/4672/4720） | SSH 认证（暴力破解/成功登录/密钥/sudo/用户管理） |
| 进程与服务（7045/7040/4688） | 进程分析（CPU/Mem Top15/PPID=1/反弹Shell） |
| 网络（防火墙/端口/连接交叉验证） | 网络分析（监听端口/连接/路由/iptables） |
| 文件变更（USN 勒索特征扫描） | Shell 命令历史（bash/zsh 敏感命令，按用户分组） |
| PowerShell 脚本块（4104/4103） | 持久化机制（crontab/systemd/init.d/profiles/sudoers） |
| RDP 远程桌面（四证据交叉验证） | SSH 安全配置（sshd/authorized_keys/PAM） |
| 持久化（注册表/启动项/计划任务） | 环境信息（LD_PRELOAD/内核模块/NTP） |
| 签名校验 + 命令历史（数字签名/PSReadLine） | 文件完整性校验（包校验/SUID/SGID/关键二进制） |

## 项目结构

```
intrusion-analysis-skill/
├── SKILL.md                              ← 统一 Skill 定义
├── README.md
├── scripts/
│   ├── analysis/
│   │   ├── preanalyze.py                 ← 预分析统一入口
│   │   ├── _common/                      ← 公共模块（平台无关）
│   │   │   ├── __init__.py
│   │   │   ├── constants.py              ← 共享常量（日志格式正则/云元数据 IP）
│   │   │   ├── models.py                 ← 数据模型（SectionIndex）
│   │   │   └── parsers.py                ← 日志结构解析器 + IP 分类
│   │   ├── windows/                      ← Windows 预分析器
│   │   │   ├── preanalyze_windows.py     ← 入口 + can_handle/run 接口
│   │   │   └── _pa_windows/              ← 内部模块包
│   │   │       ├── analyzers.py          ← 5 项交叉分析 + 威胁评分
│   │   │       ├── constants.py          ← 常量与特征库
│   │   │       ├── extractors.py         ← 15 项数据精简提取 + 质量校验
│   │   │       ├── models.py             ← 数据模型
│   │   │       ├── parsers.py            ← 日志章节解析器
│   │   │       └── renderer.py           ← Markdown 输出渲染器
│   │   └── linux/                        ← Linux 预分析器
│   │       ├── preanalyze_linux.py       ← 入口 + can_handle/run 接口
│   │       └── _pa_linux/                ← 内部模块包
│   │           ├── condenser.py          ← 章节精简压缩
│   │           ├── constants.py          ← 常量与特征库
│   │           ├── handlers.py           ← 各章节处理器
│   │           └── ssh_analysis.py       ← SSH 交叉验证分析
│   ├── windows/
│   │   ├── get_log_all_in_one.ps1        ← Windows 日志采集工具
│   │   └── README.md                     ← Windows 采集脚本文档
│   └── linux/
│       ├── get_log_all_in_one.sh         ← Linux 日志采集工具
│       └── README.md                     ← Linux 采集脚本文档
└── templates/
    └── analysis_report_template.md       ← 统一分析报告模板（攻击链驱动，平台无关）
```

## 快速开始

### Windows

1. 在目标服务器上以管理员权限运行 PowerShell 脚本：

```powershell
powershell -ExecutionPolicy Bypass -File get_log_all_in_one.ps1
```

2. 将生成的 `log_<hostname>_<timestamp>.txt` 提供给 AI Agent，说"入侵分析"。

### Linux

1. 在目标服务器上以 root 权限运行 Bash 脚本：

```bash
sudo bash get_log_all_in_one.sh
```

2. 将生成的 `log_<IP>_<hostname>_<user>_<timestamp>.txt` 提供给 AI Agent，说"Linux 入侵分析"。

### 触发词

- "入侵分析" / "日志分析" / "安全排查" / "intrusion analysis"（Windows）
- "Linux 入侵分析" / "Linux 日志分析" / "Linux 安全排查"（Linux）

## 技术栈

| 技术 | 用途 |
|------|------|
| PowerShell | Windows 日志采集脚本（纯文本 .txt 输出） |
| Bash | Linux 日志采集脚本（纯文本 .txt 输出） |
| Python ≥ 3.10 | 预分析脚本（Windows: 5 项交叉分析 + 15 项数据精简提取 + 威胁评分；Linux: SSH 交叉验证 + 各章节精简 + 威胁评分）。需要 3.10+ 以支持 PEP 604 联合类型语法（`X \| Y`）和 PEP 585 泛型（`list[str]`） |
| SKILL.md | AI Agent 分析流程编排定义 |

## License

MIT
