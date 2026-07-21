# 行业知识库索引

> 本目录为专家团提供行业级设计规范、架构模式、平台规范、成本模型和**工程纪律标准**参考。
> 每个成员在对应工作阶段**必须**使用 Read 工具读取相关文件，作为联网调研的补充基线。

## 目录结构

```
references/
├── README.md                    # 本索引文件
├── 01-standards/                # 工程纪律标准（UmaDev 融合 — 11 篇商业级必读）
│   ├── spec-as-contract.md             # 规格即契约 8 要素
│   ├── eval-driven-delivery.md         # 评测驱动交付
│   ├── verifier-critic-pattern.md      # 验证者/评审者模式
│   ├── test-discipline.md              # 生成式代码测试纪律
│   ├── test-integrity-anti-gaming.md   # 测试完整性反作弊
│   ├── generated-code-failure-modes.md # 生成式代码失效模式（6 类）
│   ├── production-readiness-scorecard.md # 生产就绪记分卡（7×3 矩阵）
│   ├── self-improving-memory.md        # 自学习记忆与回归集
│   ├── open-decisions-register.md      # 悬而未决登记册
│   ├── context-engineering.md          # 上下文工程
│   └── code-organization.md            # 代码组织规范（分层·分包·不堆单文件）
├── industries/                  # 行业设计规范
│   ├── saas-b2b.md             # SaaS / B2B 工具
│   ├── ecommerce.md            # 电商 / 消费
│   ├── content-platform.md     # 内容 / 社区平台
│   ├── ai-native.md            # AI 原生产品
│   └── enterprise.md           # 企业管理 / ERP
├── platforms/                   # 平台开发规范
│   ├── wechat-miniprogram.md   # 微信小程序
│   └── harmonyos.md            # 鸿蒙 HarmonyOS NEXT
├── architecture/                # 架构模式参考
│   ├── mvp-stack.md            # MVP 技术选型矩阵
│   ├── rag-knowledge-base.md   # RAG / 企业知识库
│   ├── multi-tenant-saas.md    # 多租户 SaaS
│   └── ai-agent-patterns.md    # AI Agent 工程化模式
├── cost-models/                 # 成本模型
│   └── development-costs.md    # 开发成本参考
└── design-systems/              # 设计系统参考（7 篇商业级）
    ├── token-standard.md            # 四层 Token + DESIGN.md 9节 + Master+Overrides
    ├── design-commands.md           # 设计动作命令库（23 命令 + 寄存器 + 平台轴 + denylist）
    ├── ui-styles-library.md         # UI 风格库（40 套 + 决策树）
    ├── industry-design-systems.md   # 行业推荐（30 行业推理规则）
    ├── color-palettes.md            # 配色库（30 套 × 17 语义色 + Tailwind）
    ├── typography-pairings.md       # 字体配对（25 套 + Google Fonts）
    └── landing-patterns.md          # 落地页模式（24 种 + section 顺序）
```

## 引用机制（谁在什么时候读什么）

| 成员 | 读取文件 | 时机 | Agent prompt 中的引用章节 |
|------|----------|------|--------------------------|
| **PM** | `industries/{对应行业}.md` | Phase 1 竞品调研前 | pm.md → 「行业知识库引用（必读）」 |
| **架构师** | `01-standards/spec-as-contract.md` + `01-standards/context-engineering.md` + `01-standards/generated-code-failure-modes.md` + `01-standards/code-organization.md` + `architecture/*.md` + `cost-models/development-costs.md` | Phase 1 技术选型前 | architect.md → 「知识库引用（必读）」 |
| **设计师** | `design-systems/design-commands.md` + `ui-styles-library.md` + `industry-design-systems.md` + `color-palettes.md` + `typography-pairings.md` + `landing-patterns.md` + `token-standard.md` + `industries/{对应行业}.md` | Phase 2 设计系统生成前（Step 2 全量并行读取） | designer.md → 「设计系统知识库引用（必读）」 |
| **前端** | `01-standards/generated-code-failure-modes.md` + `01-standards/context-engineering.md` + `platforms/{对应平台}.md` | Phase 3 开发前 | frontend.md → 「平台知识库引用（必读）」 |
| **QA** | `01-standards/test-discipline.md` + `01-standards/test-integrity-anti-gaming.md` + `01-standards/verifier-critic-pattern.md` + `01-standards/generated-code-failure-modes.md` + `01-standards/production-readiness-scorecard.md` | Phase 2 写测试 + Phase 4 评级前 | qa.md → 「知识库引用（必读）」 |
| **后端** | `01-standards/code-organization.md` + `01-standards/generated-code-failure-modes.md` + `01-standards/test-discipline.md` + `01-standards/eval-driven-delivery.md` | 项目搭建前 + 自检前 | backend.md → 「项目目录结构与代码组织」+「失效模式自检清单」 |
| **运维** | `01-standards/production-readiness-scorecard.md` + `architecture/mvp-stack.md` + `cost-models/development-costs.md` | Phase 4 部署前 | devops.md → 「知识库引用（必读）」 |
| **项目总监** | 全部（门禁时参照） | 每个 Phase 门禁检查时 | team-lead.md → 「知识库调度规则」 |

## 使用方式

1. **主理人（大湾区靓仔）** 在 spawn 成员时，通过指令告知成员读取对应的 `references/` 文件路径
2. **各成员** 在工作流程的对应步骤中，使用 Read 工具读取文件，将内容作为调研基线
3. **门禁检查**：主理人在每个 Phase 结束时，检查成员产出是否参照了对应知识库内容

> 知识库内容作为基线参考，联网搜索用于补充最新数据和版本兼容性信息。两者互补，不替代。

## 01-standards/ 文件来源

`01-standards/` 下 11 篇文档中，10 篇改编自 [UmaDev](https://github.com/umacloud/umadev) 知识库（MIT License，原文件位于 `knowledge/agentic-delivery/01-standards/`，每篇顶部有来源标注），`code-organization.md` 为本专家团自有的代码组织规范（分层·分包·单文件≤300行·单一职责）。
