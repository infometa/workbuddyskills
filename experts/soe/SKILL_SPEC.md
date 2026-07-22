# 子能力规范约定 (Sub-Capability Specification)

本文档定义了 `soe` WorkBuddy 专家插件中子能力（sub-capability，即 `references/` 下的各分析能力）的标准化规范，所有新增子能力必须遵循此约定。

> 说明：由于 WorkBuddy 插件的 `skills` 字段只扫描 `skills/` 下的**直接子目录**（不支持多层嵌套自动发现），本项目只注册唯一的顶层 Skill（`skills/soe/`）。因此这里的"子能力"不是 WorkBuddy 意义上独立注册的 Skill，而是 `skills/soe/references/` 下按分类组织、由 `SKILL.md` 入口索引按需渐进式加载的能力模块。

---

## 1. 目录结构规范

每个子能力作为独立目录存在于 `skills/soe/references/<category>/` 下：

```
skills/soe/references/<category>/<capability-name>/
├── SKILL.md              # [必须] 能力定义文件 — 唯一入口
├── scripts/              # [可选] 能力专属工具脚本
│   ├── __init__.py
│   └── *.py
├── references/           # [可选] 参考资料（知识库/映射表/模板/示例输入输出）
│   └── *.md / *.yaml / *.json
└── tools/                 # [可选] MCP 工具定义
    └── *.tool.yaml
```

### 命名规则

| 项目 | 规则 | 示例 |
|------|------|------|
| 分类目录 | 英文小写 + 连字符 | `alert-analysis/` |
| 能力目录 | 英文小写 + 连字符 | `waf-log-analyzer/` |
| 定义文件 | 统一为 `SKILL.md` | `SKILL.md` |
| 脚本文件 | snake_case | `l1_cwp_analyze.py` |

---

## 2. SKILL.md 文件规范（能力定义文件）

### 2.1 Frontmatter（YAML 头部）— 必须

```yaml
---
name: capability-name                # [必须] 能力唯一标识（与目录名一致）
description: "一句话描述..."          # [必须] 功能描述（供入口 SKILL.md 路由表展示）
version: 1.0.0                       # [必须] 语义化版本号
triggers:                            # [必须] 触发关键词列表（入口路由匹配用）
  - 关键词1
  - 关键词2
  - 关键词3
input_formats:                       # [可选] 支持的输入文件格式
  - "*.pcap"
  - "*.xlsx"
dependencies:                        # [可选] 依赖的其他能力
  - soc-alert-pipeline
role: infrastructure                 # [可选] 角色类型（infrastructure=基础设施/独立功能）
---
```

### 2.2 正文结构 — 必须按此顺序

```markdown
# 标题 (capability-name)

## 角色定位
一段话描述该能力的专业身份和核心职责。

## 能力范围
- 列出该能力能做的所有事情（5-10 条）
- 每条用一句话描述

## 工作流程
### Step 1: {步骤名}
- 具体操作说明
- 判断条件和分支

### Step 2: {步骤名}
...

### Step N: 报告输出
- 最终输出物描述

## 输出格式
说明输出的格式（Markdown/HTML/JSONL/结构化报告等）。

## 与其他能力联动（可选）
- **上游**: 哪些能力为本能力提供输入
- **平级**: 可以协同工作的能力
- **下游**: 消费本能力输出的能力
```

---

## 3. 路由注册规范

新增子能力后，必须在入口 `skills/soe/SKILL.md` 的 **意图路由表** 中添加条目：

```markdown
| 分类 | `capability-name` | 触发关键词(逗号分隔) | 数据输入格式 | `references/<分类>/<capability-name>/SKILL.md` |
```

路由匹配规则：
- `triggers` 中的关键词会被入口 SKILL.md 用于意图匹配
- 关键词应覆盖：中文术语 + 英文术语 + 常见缩写 + 产品名
- 避免过于宽泛的关键词（如单独的"分析"、"查询"）

---

## 4. 质量标准

### 4.1 能力定义质量检查清单

- [ ] Frontmatter 包含所有必须字段（name/description/version/triggers）
- [ ] `name` 与目录名一致
- [ ] `triggers` 至少包含 3 个差异化关键词
- [ ] `description` 不超过 200 字符
- [ ] 工作流程至少包含 3 个 Step
- [ ] 每个 Step 有具体可执行的操作描述（非空洞原则）
- [ ] 明确声明输出格式
- [ ] 如有依赖关系，在 `dependencies` 和「联动」章节中双向声明

### 4.2 禁止事项

- ❌ 在 SKILL.md 中包含具体测试数据或示例输入输出（放 `references/` 目录）
- ❌ 在 SKILL.md 中编写具体代码实现（放 `scripts/` 目录）
- ❌ 触发关键词与已有能力严重重叠（会导致路由冲突）
- ❌ 工作流程描述过于抽象模糊（必须可操作）
- ❌ 省略 Frontmatter 或使用非标准字段名
- ❌ 在 `skills/` 下新建独立的顶层能力目录（WorkBuddy 只扫描 `skills/soe/` 这一个 Skill，新能力必须放进 `skills/soe/references/`）

---

## 5. 分类体系

当前支持的分类目录（均位于 `skills/soe/references/` 下）：

| 分类目录 | 含义 | 适用场景 |
|---------|------|---------|
| `vulnerability-analysis/` | 漏洞管理 | 漏扫报告解析、CVE修复验证 |
| `alert-analysis/` | 告警研判 | 安全产品告警研判、L0/L1 分析（含资产关联辅助） |
| `intrusion-analysis/` | 入侵溯源 | 主机入侵排查、攻击链还原 |
| `attack-analysis/` | 攻击分析 | DDoS/流量攻击分析、勒索病毒分析 |
| `asset-management/` | 告警研判辅助 | 告警研判资产关联辅助（IP→主机映射） |
| `general/` | 腾讯云产品日志排查 | 腾讯云产品日志分析 |

新增分类需在此表和 README.md 中同步更新。

---

## 6. 版本管理

- 遵循语义化版本：`MAJOR.MINOR.PATCH`
  - MAJOR: 能力范围/工作流程重大变更（不兼容旧行为）
  - MINOR: 新增能力或优化（向后兼容）
  - PATCH: 描述修正/关键词调整（无功能变化）
- 版本变更时更新 Frontmatter 中的 `version` 字段
- 插件整体版本在 `.codebuddy-plugin/plugin.json` 的 `version` 字段单独维护

---

## 7. 示例：创建新能力

假设要新增一个「勒索病毒分析」能力：

### 7.1 创建目录

```bash
mkdir -p skills/soe/references/attack-analysis/ransomware-analysis
```

### 7.2 编写 SKILL.md

```markdown
---
name: ransomware-analysis
description: "勒索病毒分析：基于勒索信、加密文件扩展名、注册表等特征识别勒索家族，分析入侵路径，评估数据恢复可能性。"
version: 1.0.0
triggers:
  - 勒索病毒
  - 勒索软件
  - ransomware
  - 加密文件
  - 赎金
  - 勒索信
  - 文件被加密
---

# 勒索病毒分析 (ransomware-analysis)

## 角色定位
勒索病毒应急响应专家，能从勒索现场特征快速识别勒索家族、分析入侵路径并评估恢复可能性。

## 能力范围
- 基于勒索信内容识别勒索家族
- 基于加密文件扩展名匹配已知家族
- 分析入侵路径（RDP暴破/漏洞利用/钓鱼邮件）
- 评估数据恢复可能性（是否有已知解密工具）
- 提供应急处置建议

## 工作流程
### Step 1: 样本特征收集
- 收集勒索信内容 / 加密文件扩展名 / 注册表变更
- 提取勒索钱包地址和联系方式

### Step 2: 家族识别
- 匹配已知勒索家族特征库
- 确认勒索家族和变种版本
- 查询该家族已知解密工具

### Step 3: 入侵路径分析
- 分析初始入侵方式
- 还原横向传播路径
- 确定加密范围

### Step 4: 报告输出
- 勒索家族判定
- 入侵路径还原
- 恢复可能性评估
- 应急处置建议（隔离/备份/上报）

## 输出格式
Markdown 勒索分析报告（家族判定 + 入侵路径 + 恢复建议）。
```

> **注**：以上为创建新能力时的最小化示例。实际已落地的 `ransomware-analysis` 能力以 `references/attack-analysis/ransomware-analysis/SKILL.md` 为准，包含零 Key 在线情报查询、4 个免费数据源、独立 IOC 提取工具、SSL 三级回退、缓存策略等完整功能。

### 7.3 注册路由

在入口 `skills/soe/SKILL.md` 的意图路由表中添加：

```markdown
| 攻击分析 | `ransomware-analysis` | 勒索病毒、ransomware、加密文件、赎金、勒索信 | 勒索信/加密样本/系统日志 | `references/attack-analysis/ransomware-analysis/SKILL.md` |
```

---

## 8. 与 tc-sec 模式的对比

| 维度 | tc-sec（参考） | soe（本项目） |
|------|--------------|-------------------|
| 插件清单 | `.codebuddy-plugin/plugin.json` | `.codebuddy-plugin/plugin.json` |
| Agent 行为层 | `agents/tc-sec.md` | `agents/soe.md` |
| 唯一注册 Skill | `skills/tc-sec/SKILL.md` | `skills/soe/SKILL.md` |
| 子能力组织 | `references/workflow/<name>/` + `scripts/` | `references/<分类>/<能力名>/SKILL.md` |
| 路由方式 | workflow trigger 匹配 → run.py 直达 | 意图路由表 triggers 匹配 → 加载对应 `references/.../SKILL.md` |
| 执行方式 | run.py 脚本执行（机械） + agent 灵活编排 | 能力 SKILL.md 指导（智能） + scripts 辅助 |
| 联动机制 | 两段式（脚本阶段 + agent阶段） | 层级依赖（L0→L1→L2） + 资产层横切 |
