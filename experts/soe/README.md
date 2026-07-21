# 腾讯云安全运营专家 (soe) — WorkBuddy 专家插件

## 项目定位

`soe` 是一个 **WorkBuddy / CodeBuddy 专家插件**（"腾讯云安全运营专家"）。它是一个 agent 型专家，覆盖漏洞管理、多产品告警研判（WAF/CWP云镜/御界NDR/天幕/SOC）、入侵溯源、DDoS流量分析、勒索病毒分析、资产管理等安全运营场景，参考 `tc-sec` 插件的架构模式实现。

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
         ┌─────────┬────────┼────────┬─────────┬──────┐
         ▼         ▼        ▼        ▼         ▼      ▼
┌─────────┐┌────────┐┌───────┐┌───────┐┌───────┐┌──────┐
│漏洞管理  ││告警研判 ││入侵溯源 ││攻击分析 ││资产管理 ││通用排查│
│(3能力)  ││(5能力)  ││(1)    ││(2)    ││(1)    ││(1)   │
└─────────┘└────────┘└───────┘└───────┘└───────┘└──────┘
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
│           │   └── soc-alert-pipeline/
│           ├── intrusion-analysis/           # 入侵溯源（分类与能力同名，扁平化）
│           ├── attack-analysis/              # 攻击分析
│           │   ├── ddos-analysis/
│           │   └── ransomware-analysis/
│           ├── asset-management/             # 资产管理
│           │   └── asset-manager/
│           └── general/                      # 通用排查
│               └── log-analysis-troubleshooting/
├── SKILL_SPEC.md                             # 新增能力的规范约定
└── README.md                                 # 本文件
```

> **为什么是"单 Skill + references 渐进式加载"而不是"多 Skill 扁平注册"**：WorkBuddy 的 `plugin.json` `skills` 字段按约定扫描 `skills/` 下的**直接子目录**（每个子目录需含 `SKILL.md`），不支持多层嵌套分类自动发现。为保留按安全领域分类管理 13 个能力的组织方式，参照 `tc-sec` 的做法——只注册一个 Skill（`skills/soe/`），其 `SKILL.md` 作为入口索引，具体能力全部收纳进 `references/` 按需渐进式加载。

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
| 告警研判 | `soc-alert-pipeline` | SOC 告警流水线 L0 适配层 |
| 入侵溯源 | `intrusion-analysis` | 主机入侵检测排查 |
| 攻击分析 | `ddos-analysis` | DDoS 攻击流量分析 |
| 攻击分析 | `ransomware-analysis` | 勒索病毒家族识别、入侵路径分析、数据恢复评估 |
| 资产管理 | `asset-manager` | 主机资产纳管（基础设施，供其他能力调用） |
| 通用排查 | `log-analysis-troubleshooting` | 通用应用日志分析 |

## 层级依赖关系

```
L0 适配层:    soc-alert-pipeline（统一 raw_log 解析）
                   ↓ parsed 字段
L1 产品分析:  cwp-analyzer | yujie-analyzer | tianmu-analyzer
                   ↓ 结构化事件
L2 跨产品关联（关联多产品 L1 输出）

资产数据层:   asset-manager（为所有能力提供 IP→主机映射）
独立能力:     vul-analyse | host-cve-validator | container-cve-fix-validator
              waf-log-analyzer | ddos-analysis | intrusion-analysis
              ransomware-analysis | log-analysis-troubleshooting
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


