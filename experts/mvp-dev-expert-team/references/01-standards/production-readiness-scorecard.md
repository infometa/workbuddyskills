---<!-- Adapted from UmaDev knowledge base (MIT License). Original: knowledge/agentic-delivery/01-standards/production-readiness-scorecard.md -->

id: production-readiness-scorecard
title: 分级生产就绪记分卡（Bronze/Silver/Gold：从可演示到商业级的可审计刻度，商业级必读）
domain: agentic-delivery
category: 01-standards
difficulty: advanced
tags: [readiness-scorecard, bronze-silver-gold, graduated, maturity, demo-vs-commercial, tests-regression, contract, security, a11y, performance, observability, release-safety, 记分卡, 分级, 生产就绪, 可演示, 商业级, 可审计刻度]
quality_score: 95
last_updated: 2026-06-29
---
# 分级生产就绪记分卡（商业级必读）

> "能跑的演示"和"敢卖的商业级产品"之间隔着一条线，而这条线长期是**说不清、争不出**的——每个人心里的"够好了"都不一样。这份记分卡把它变成**可审计的刻度**：跨 测试+回归、契约、安全、无障碍、性能、可观测、发布安全 七个维度，给出 **Bronze（最低可上线）→ Silver（生产稳健）→ Gold（加固）** 三档，**持续打分**，让"现在到底是 demo 还是商业级"一眼可判、可签字、可追责。
> 它不是又一份逐条勾选清单，也不替代上线前的 go/no-go 决策——那是 `operations/01-standards/production-readiness-review`（PRR）。记分卡是**贯穿交付过程的连续分级**：PRR 在终点做一次放行判定，记分卡告诉你**此刻处在哪一档、离下一档还差什么**。各维度的权威标准在文内逐一指向，本规范回答的是"用什么刻度把 demo 和商业级区分开"。

## 1. 三档的含义

| 档位 | 定位 | 一句话判据 |
|---|---|---|
| **Bronze** | 最低可上线（minimum-shippable） | 核心流跑得通、错误不致命、能看见出没出事、能回退 |
| **Silver** | 生产稳健 | 回归有兜底、契约对齐、关键安全/无障碍/性能达标、可观测齐全 |
| **Gold** | 加固（hardened） | 高风险路径 pass^k 可靠、容量/容灾验证、发布安全闭环、审计完备 |

原则：**档位取各维度的最低档**——任何一维只到 Bronze，整体就只是 Bronze。商业级交付的最低线是 **Silver**；Gold 留给关键系统与高风险路径。

## 2. 七维 × 三档评分矩阵

| 维度 | Bronze（最低可上线） | Silver（生产稳健） | Gold（加固） |
|---|---|---|---|
| 测试 + 回归 | 核心流有测试、构建/lint 绿 | 影响图定向覆盖、回归率为零、回归集进门禁 | 关键路径 pass^k、变异加固、独立测试作者 |
| 契约 | 主要接口有定义 | 契约先行、前后端对照、错误模型统一 | 契约破坏在 CI 即红、版本与弃用策略闭环 |
| 安全 | 鉴权到位、无明显高危、密钥不入库 | 授权(RBAC)/限额/输入校验齐、依赖存在性核验 | 供应链加固、SAST/扫描门、威胁面复核 |
| 无障碍 | 核心流可键盘完成 | 对比度/焦点/语义达 AA、自动扫描 0 阻断 | 屏读端到端走查 + 回归断言 |
| 性能 | 无明显 N+1/全量加载、关键页可用 | 热点路径达标、分页/索引/超时到位 | 容量/压测验证、预算守恒、退化阻断 |
| 可观测 | 有日志、出错看得见 | 结构化日志 + 关键指标 + SLI/SLO | 告警/追踪/错误预算闭环、可定位根因 |
| 发布安全 | 能回退 | 渐进发布 + 回滚预案演练 | 自动回滚触发、特性开关、变更可审计 |

各维度权威标准：测试见 `agentic-delivery/01-standards/test-discipline-for-generated-code` 与 `testing/01-standards/ci-test-gates-and-coverage`；回归集见 `agentic-delivery/01-standards/self-improving-memory-and-regression-sets`；契约见 `experts/architect/contract-first-api-design`、`testing/01-standards/contract-testing-and-api-contracts`；安全/供应链见 `security/01-standards/supply-chain-security`；无障碍见 `frontend/01-standards/accessibility-acceptance-gate`；可观测见 `observability/01-standards/observability-and-slo-operations`；发布安全见 `release-engineering/01-standards/progressive-delivery-and-release`；pass^k 见 `agentic-delivery/01-standards/eval-driven-delivery`。

## 3. 持续打分，而非一次性盖章

- **贯穿交付**：记分卡随交付过程持续更新，不是临上线才算一次。每次关键改动后重算受影响维度的档位。
- **看板可见**：当前总档 + 各维度档位 + "离下一档差哪几项"明确列出，让"还差什么"可执行而非空谈。
- **最低档决定总档**：短板维度直接拉低整体定位，逼着补齐而非用强项掩盖弱项。
- **与 PRR 衔接**：上线前 PRR 做 go/no-go 时，记分卡是其输入证据之一——未达目标档即为 no-go 或有条件放行的依据。

## 4. demo 与商业级的可审计分界

- **demo = Bronze 以下或仅 Bronze**：能演示、不可托付生产。
- **商业级 = Silver 起步**：有回归兜底、契约对齐、关键安全/无障碍/性能达标、可观测齐全、可回退。
- **关键/高风险系统 = Gold**：pass^k 可靠、容量容灾验证、发布安全闭环。
- 每次评级**留痕可审计**：档位、证据（哪条达标/未达标）、责任人、目标档与期限随交付归档。

## 5. 接入交付流程

- **立基线**：交付开始即声明目标档（一般 Silver，关键系统 Gold）。
- **持续评**：每个关键步骤后重算受影响维度，更新看板与短板项。
- **补短板**：以"离目标档差哪几项"驱动后续工作，最低档维度优先。
- **放行**：达目标档 + PRR 放行才上线；未达即有条件放行（带遗留项/期限）或不放行。

## 6. 反模式（出现即不合格）

1. **用"差不多能跑"代替刻度**：没有可判定档位，demo 与商业级之争永远扯不清。
2. **强项掩盖短板**：某维很亮就宣称商业级，无视有维度还在 Bronze。
3. **临上线才评一次**：过程中不打分，问题堆到最后无法补。
4. **记分卡不可审计**：只给个"已就绪"结论，无证据、无责任人、无期限。
5. **把记分卡当 PRR 替代品**：用连续分级冒充上线放行决策，或反之。
6. **目标档不声明**：不说要做到哪档，验收时各执一词。
7. **达不到 Silver 就上商业生产**：无回归兜底/契约对齐/可观测/可回退强行交付。

## 7. 最低交付 checklist

- [ ] 交付开始声明目标档（商业级最低 Silver，关键系统 Gold）。
- [ ] 七维（测试+回归/契约/安全/无障碍/性能/可观测/发布安全）各自评出档位。
- [ ] 总档取各维最低档，短板维度优先补齐，不用强项掩盖弱项。
- [ ] 记分卡持续更新、看板可见，明确列出"离目标档差哪几项"。
- [ ] 每次评级留痕：档位 + 证据 + 责任人 + 目标档 + 期限，可审计。
- [ ] 与 PRR 衔接：记分卡作为 go/no-go 的输入证据，未达目标档即拦或有条件放行。
- [ ] 达不到 Silver 不交付商业生产；高风险路径要求 Gold。
