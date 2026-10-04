# 腾讯云安全运营专家 (soe) — WorkBuddy 专家插件

## 项目定位

`soe` 是一个 **WorkBuddy / CodeBuddy 专家插件**（"腾讯云安全运营专家"）。它是一个 agent 型专家，覆盖漏洞管理、多产品告警研判（WAF/CWP云镜/御界NDR/天幕/CFW云防火墙/SOC）、入侵溯源、DDoS流量分析、勒索病毒分析、腾讯云产品日志排查、腾讯 iOA 零信任排障等安全运营场景（资产关联作为告警研判的辅助能力），参考 `tc-sec` 插件的架构模式实现。

## 架构

插件由 `.codebuddy-plugin/plugin.json` 声明两类组件，分别承担不同职责：

1. **Agent**（`agents/soe.md`）— 专家的系统提示词 / 人格。定义角色定位、核心能力概览、工作原则、交互规范。这是"行为规则"层。
2. **Skill**（`skills/soe/SKILL.md`）— 可操作知识，**渐进式加载**。`SKILL.md` 是入口索引（意图路由表 + 路由决策流程），按需引用 `references/` 下按安全领域分类的具体能力说明。这是"操作手册"层。

```
┌─────────────────────────────────────────────────────────┐
│              用户输入（安全运营相关需求）                   │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│   Agent 层: agents/soe.md — 角色人设 / 工作原则 / 交互规范  │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│   Skill 层: skills/soe/SKILL.md — 意图路由表 / 决策流程    │
│                                                          │
│  意图识别 → 能力匹配 → 渐进式加载 references/<能力>/SKILL.md │
└────────────────────────────┬────────────────────────────┘
                             │ 渐进式加载
         ┌─────────┬──────────────┬────────┬─────────┬────────────────┬─────────┐
         ▼         ▼              ▼        ▼         ▼                ▼
┌─────────┐┌──────────────┐┌───────┐┌───────┐┌────────────────┐┌─────────────┐
│漏洞管理  ││告警研判       ││入侵溯源││攻击分析││腾讯云产品日志排查││iOA排障      │
│(3能力)  ││(5能力+资产关联)││(1)    ││(2)    ││(1)             ││(8子能力+公共)│
└─────────┘└──────────────┘└───────┘└───────┘└────────────────┘└─────────────┘
```

## 目录结构

```
soe_skill/
├── .codebuddy-plugin/
│   └── plugin.json                          # 插件清单（名称/头像/分类/快捷Prompt等）
├── agents/
│   └── soe.md                               # Agent 行为层 — 角色人设与工作原则
├── avatars/
│   └── expert.png                           # 专家头像（九尾狐科技守护者形象）
├── skills/
│   └── soe/                                 # 唯一注册的 Skill（WorkBuddy 扁平加载要求）
│       ├── SKILL.md                         # Skill 入口索引 — 意图路由表
│       └── references/                      # 按安全领域分类的完整能力集（渐进式加载）
│           ├── vulnerability-analysis/       # 漏洞管理
│           │   ├── vul-analyse/
│           │   ├── host-cve-validator/
│           │   └── container-cve-fix-validator/
│           ├── alert-analysis/               # 告警研判
│           │   ├── waf-log-analyzer/
│           │   ├── cwp-analyzer/
│           │   ├── yujie-analyzer/
│           │   ├── tianmu-analyzer/
│           │   ├── cfw-analyzer/
│           │   └── soc-alert-pipeline/
│           ├── intrusion-analysis/           # 入侵溯源
│           │   └── host-intrusion-analysis/
│           ├── attack-analysis/              # 攻击分析
│           │   ├── ddos-analysis/
│           │   └── ransomware-analysis/
│           ├── asset-management/             # 资产管理
│           │   └── asset-manager/
│           ├── general/                      # 通用排查
│           │   └── log-analysis-troubleshooting/
│           └── ioa-troubleshooting/          # iOA 排障（领域入口 + 9 个子目录）
│               ├── SKILL.md                  # iOA 领域入口（8 个子能力路由）
│               ├── common/                   # 公共响应与安全规范
│               ├── trusted-access/           # 可信接入
│               ├── endpoint-management/      # 终端资产
│               ├── policy-management/        # 策略管控
│               ├── security-protection/      # 安全检测
│               ├── platform-operations/      # 平台运维
│               ├── consulting/               # 咨询判断
│               ├── ioa-openapi-invoke/       # iOA 开放接口调用
│               └── ioa-sql-query-generator/  # 只读 SQL 查询生成
├── SKILL_SPEC.md                             # 新增能力的规范约定
└── README.md                                 # 本文件
```

> **为什么是"单 Skill + references 渐进式加载"而不是"多 Skill 扁平注册"**：WorkBuddy 的 `plugin.json` `skills` 字段按约定扫描 `skills/` 下的**直接子目录**（每个子目录需含 `SKILL.md`），不支持多层嵌套分类自动发现。为保留按安全领域分类管理 14 个能力的组织方式，参照 `tc-sec` 的做法——只注册一个 Skill（`skills/soe/`），其 `SKILL.md` 作为入口索引，具体能力全部收纳进 `references/` 按需渐进式加载。

## 能力清单

| 分类 | 能力 | 说明 |
|------|------|------|
| 漏洞管理 | `vul-analyse` | 漏扫报告解析（15+厂商格式） |
| 漏洞管理 | `host-cve-validator` | 主机CVE修复验证引擎 |
| 漏洞管理 | `container-cve-fix-validator` | 容器CVE修复验证引擎 |
| 告警研判 | `waf-log-analyzer` | WAF攻击日志分析 |
| 告警研判 | `cwp-analyzer` | CWP/云镜告警 L1 分析 |
| 告警研判 | `yujie-analyzer` | 御界 NDR 告警 L1 分析 |
| 告警研判 | `tianmu-analyzer` | 天幕阻断日志 L1 分析 |
| 告警研判 | `cfw-analyzer` | CFW 云防火墙告警日志分析 |
| 告警研判 | `soc-alert-pipeline` | SOC 告警流水线 L0 适配层 |
| 告警研判 | `asset-manager` | 告警研判资产关联辅助（IP→主机映射） |
| 入侵溯源 | `host-intrusion-analysis` | 主机入侵检测排查 |
| 攻击分析 | `ddos-analysis` | DDoS 攻击流量分析 |
| 攻击分析 | `ransomware-analysis` | 勒索病毒家族识别、入侵路径分析、数据恢复评估 |
| 腾讯云产品日志排查 | `log-analysis-troubleshooting` | 腾讯云产品日志分析 |
| iOA排障 | `ioa-troubleshoot-expert` | 腾讯 iOA 零信任终端安全排障领域入口（内部 8 个子能力：可信接入/终端资产/策略管控/安全检测/平台运维/咨询判断/接口调用/只读查询） |

## 环境准备

### Python 版本

Python 3.8+（推荐 3.10+），所有脚本以 `python3` 调用。

### 依赖安装

各能力相互独立，按需安装对应依赖：

| 能力 | 依赖清单 | 关键依赖 |
|------|---------|---------|
| DDoS 流量分析 | `skills/soe/references/attack-analysis/ddos-analysis/scripts/requirements.txt` | scapy / dpkt / numpy / loguru / mcp |
| 主机 CVE 修复验证 | `skills/soe/references/vulnerability-analysis/host-cve-validator/requirements.txt` | openpyxl / paramiko / python-docx / pywinrm / httpx / PyYAML |
| 容器 CVE 修复验证 | `skills/soe/references/vulnerability-analysis/container-cve-fix-validator/requirements.txt` | pandas / openpyxl / paramiko / python-docx |
| iOA 开放接口调用 | `skills/soe/references/ioa-troubleshooting/ioa-openapi-invoke/requirements.txt` | requests / cryptography |
| 漏扫报告解析（vul-analyse） | 无独立清单 | httpx / PyYAML / beautifulsoup4（`pip install httpx pyyaml beautifulsoup4`） |
| 其余能力 | 无第三方依赖 | Python 标准库 |

> 未安装依赖时脚本有明确报错提示，不会静默失败。

### 可选环境变量

| 变量 | 用途 | 说明 |
|------|------|------|
| `NVD_API_KEY` | NVD 查询提速 | 免费申请：https://nvd.nist.gov/developers/request-an-api-key 。配置后 NVD 限速从 5 提升到 50 req/30s，大批量 CVE 分析建议配置；凭据通过环境变量注入 |

## 层级依赖关系

```
L0 适配层:    soc-alert-pipeline（统一 raw_log 解析）
                   ↓ parsed 字段
L1 产品分析:  cwp-analyzer | yujie-analyzer | tianmu-analyzer | cfw-analyzer | waf-log-analyzer
                   ↓ 结构化事件
L2 跨产品关联（关联多产品 L1 输出）

资产数据层:   asset-manager（告警研判资产关联辅助，提供 IP→主机映射）
独立能力:     vul-analyse | host-cve-validator | container-cve-fix-validator
              host-intrusion-analysis | ddos-analysis
              ransomware-analysis | log-analysis-troubleshooting

iOA 排障域:   ioa-troubleshoot-expert（领域入口，二级路由到 8 个子能力：
              6 个知识型子能力 + ioa-openapi-invoke 接口调用 + ioa-sql-query-generator 只读查询）
```

## 与 tc-sec 的架构对比

| 维度 | tc-sec（参考） | soe（本项目） |
|------|--------------|-------------------|
| 插件清单 | `.codebuddy-plugin/plugin.json` | `.codebuddy-plugin/plugin.json` |
| Agent 行为层 | `agents/tc-sec.md` | `agents/soe.md` |
| Skill 知识层 | `skills/tc-sec/SKILL.md` + `references/` | `skills/soe/SKILL.md` + `references/` |
| 子能力组织 | `references/workflow/<name>/` + `scripts/`（工作流为主） | `references/<分类>/<能力名>/SKILL.md`（意图路由为主） |
| 加载方式 | workflow trigger 匹配 → run.py 直达执行 | 意图路由表匹配 → 加载对应 `references/.../SKILL.md` 按其内部流程执行 |
| 执行方式 | run.py 脚本执行（机械） + agent 灵活编排 | 各能力目录下 scripts/ 工具 + agent 按 SKILL.md 指导编排 |

## 新增能力

参见 [SKILL_SPEC.md](./SKILL_SPEC.md) 了解新增能力（子 Skill）的规范约定，新增能力需放入 `skills/soe/references/<分类>/<能力名>/`，并在 `skills/soe/SKILL.md` 的意图路由表中注册。


