# Changelog

## [2.1.0] - 2026-07-19

### Added — UmaDev 工程纪律融合（17 项增强）

**P0 核心升级**：
- **10 篇标准文档搬入**：从 UmaDev 知识库 `knowledge/agentic-delivery/01-standards/` 搬入 `references/01-standards/`（spec-as-contract / eval-driven-delivery / verifier-critic-pattern / test-discipline / test-integrity-anti-gaming / generated-code-failure-modes / production-readiness-scorecard / self-improving-memory / open-decisions-register / context-engineering）
- **QA 反作弊门**：5 类测试作弊检测（删测试/弱化断言/skip新增/硬编码断言/框架篡改），杜绝「删测试换绿」
- **QA 先写测试**：Phase 2 同步 spawn QA 写测试用例，Phase 3 前端/后端按测试实现（AgentCoder 实验 +5% pass@1）
- **QA 回归率一等指标**：解决率达标但回归率非零 = 不算完成
- **Spec 规格即契约**：4 要素升级（out-of-scope 独立章节 + 版本锚定 + 内嵌已知坑 + 端到端验证步骤），13 章节模板
- **悬而未决登记册**：第三记忆通道（OPEN/RESOLVED 状态机 + 7 字段 + 三类 slug + 开工复现）
- **踩坑自学习闭环**：识别→记录→触发→验证四阶段（技术栈指纹精准触发，不靠文字匹配）

**P1 产出物升级**：
- **机器可读 sidecar**：架构师必须产出 `openapi.yaml`（OpenAPI 3.0），设计师必须产出 `design-tokens.json` + `design-tokens.css`
- **RoleVerdict 结构化裁决**：成员回传从自由文本升级为 4 字段结构（verdict/blocking/advisory/evidence）
- **生产就绪记分卡**：7 维 × 3 档（Bronze/Silver/Gold），未达 Silver 不交付商业生产
- **改动影响分析**：QA 每次测试前先算「改了什么→波及哪些旧行为→风险面优先级」
- **回归集产物**：每个 P0 缺陷沉淀为持久回归用例 `tests/regression/`

**P2 工程纪律**：
- **失效模式自检**：前端/后端交付前逐项核对 6 类 AI 生成代码失效（沉默逻辑错误/同义测试/happy-path 偏差/幻觉依赖/缺失上下文/性能盲区）
- **上下文工程纪律**：spawn 指令恰当高度 + JIT 检索 + 压实保真 + 子代理隔离
- **增量增删反坍缩**：记忆文件禁止整篇重写，只追加/修正具体条目
- **ADR 产物**：架构师每条选型产出 MADR 格式决策记录

**P3 治理增强**：
- **反剧场铁律**：无产物不设席位，交接=产物≠旁白，写代码≠判代码
- **过度设计护栏**：评审只标正确性/需求/契约硬伤，不标风格偏好
- **Bounded 打回**：最多 3 轮，连续无进展即升级

### Changed
- QA 工作流从「事后测试」改为「Phase 2 先写测试 → Phase 4 跑测试」
- 质量报告新增：回归率/解决率/反作弊结果/失效模式核对/生产就绪评级 5 个维度
- Spec 模板从 10 章节升级为 13 章节（+out-of-scope/已知坑/端到端验证）
- 记忆系统从单通道升级为三通道（经验沉淀+悬而未决登记册+踩坑自学习）
- 所有成员通信规则统一为 RoleVerdict 结构化裁决格式

## [2.0.1] - 2026-07-18

### Fixed — 知识库引用机制修复（腾讯技术反馈）
- **问题**：references/ 14 篇知识库文档存在但无任何 agent 引用，被腾讯技术质疑为"弃用内容"
- **根因**：README 只写了"应读取"但无 agent prompt 真正引用路径，references/ 成为死代码
- **修复**：在 5 个核心 agent prompt 中嵌入明确的「知识库引用（必读）」章节：
  - **PM**：Phase 1 调研前 Read `references/industries/{对应行业}.md`（5 个行业文件）
  - **架构师**：技术选型前 Read `references/architecture/*.md`（4 个架构文件）+ `references/cost-models/development-costs.md`
  - **设计师**：设计 Token 前 Read `references/design-systems/token-standard.md` + 对应行业文件
  - **前端**：方案 D 开发前 Read `references/platforms/wechat-miniprogram.md`，鸿蒙原生 Read `references/platforms/harmonyos.md`
  - **Team Lead**：新增「知识库调度规则」，spawn 成员时下发对应 references 路径，门禁时检查是否引用
- **结果**：13 篇知识库文档全部被至少 1 个 agent 引用，QA/后端/运维不引用（职责不需要）
- **更新**：references/README.md 重写引用机制说明表

## [2.0.0] - 2026-06-17

### Added — Excellent 蒸馏 & 行业知识库 & 审查整改
- **Excellent 人物画像注入**：从12篇优码云AI公众号文章蒸馏韦优人物画像，Team Lead 化身"大湾区靓仔"
  - 15年全栈、9年OPC独立开发、优码云创始人、SuperDev作者、WorkBuddy Nova大使
  - 核心方法论融入：五层工程化体系、Harness六层洋葱、EvoMaster四层进化、SPAR闭环、五源对齐法、DDAD
  - 实战数据：828API企业ERP、1012API跨境电商、年100+项目、95%代码可用率
- **行业知识库**（references/industries/）：SaaS B2B、跨境电商、企业ERP、AI原生应用、内容平台
- **架构知识库**（references/architecture/）：MVP技术栈选型、AI Agent模式、RAG知识库、多租户SaaS
- **设计系统知识库**（references/design-systems/）：四层Token标准
- **平台知识库**（references/platforms/）：微信小程序、HarmonyOS
- **6个完整 Playbook 案例**：团队协作/SaaS任务管理/内容平台/电商小程序/个人理财/腾讯生态

### Fixed — 官方审查整改（2026-07-06 审查报告）
- **B01 (BLOCKER)**：team-lead.md 新增「成员调度规则」章节，明确 Agent 工具 name/subagent_type 参数须传 Agent ID（非中文名）
- **S01 (P4)**：playbook-cases 中 21 处 mock 凭据替换为占位符（`<YOUR_TEST_PASSWORD>` / `<MOCK_JWT_TOKEN>` / `<YOUR_DB_PASSWORD>`），消除安全扫描误报
- **S02 (P2)**：displayDescription 统一为"8位专家"（原为"7位专家"），与 description 和 members 数组一致
- **S03 (P2)**：members[] 字段名 `name` → `displayName`，与 plugin-json-spec.md 模板一致
- **S04 (P3)**：members[] 中 lead 的 profession 已为"项目总监"（与顶层 displayName "MVP开发专家团" 差异化）；顶层 profession=displayName 为 plugin-json-spec.md 强制要求（"Team 型须与 displayName 一致"）
- **S05 (P3)**：connector 依赖声明同时使用 `connectorIds`（顶层，匹配 WorkBuddy 运行时约定）和 `dependencies.connectors`（结构化声明），双写覆盖两种可能的规范（plugin-json-spec.md 未定义 connector 字段，仓库无先例）
- **S06 (P3)**：README 安装路径 `.workbuddy` → `.codebuddy`

### Changed
- 所有成员角色定义升级，融入 Excellent 方法论和实战经验
- IMA 知识库连接器声明从 `connectorIds` 改为 `dependencies.connectors` + `connectorIds` 双写
- 6个 Playbook HTML 案例移动端适配修复（防溢出三件套）

## [1.3.0] - 2026-06-17

### Added — 设计系统融合
- **四层 Token 体系**：从三层升级为 A1-identity/A1-structure/A2/B-slot/C-extension 五级分层，对齐行业设计系统标准
- **DESIGN.md 9 节输出格式**：设计师交付物新增标准化的设计规范文档（Visual Theme → Color → Typography → Components → Layout → Depth → Do's & Don'ts → Responsive → Agent Guide）
- **色彩精规**：调色板四层结构（中性70-90%/强调5-10%/语义0-5%/效果<1%），每屏≤2处强调色
- **排版精规**：ALL CAPS必须≥0.06em字距、标题负字距、三级字重系统(400/510/590)
- **状态覆盖规范**：5态强制覆盖（Loading/Empty/Error/Populated/Edge）
- **布局词汇表**：12/8/4列栅格、节区节奏80/48/32px、Hero 40-60vh
- **动效精规**：150ms跨系统收敛值、5级时长场景、prefers-reduced-motion
- **设计系统选择策略**：按产品类型推荐对应设计系统参考
- **前端19项视觉检查清单**：从14项扩展到19项，融入工程级设计规范

### Changed
- 设计师 Token 体系从三层升级为四层（+B-slot 层）
- 反模式7大罪对齐反AI模板规范（新增：默认靛蓝色强调、圆角卡片+彩色左边框、虚构指标、填充式文案）
- 前端 CSS 技巧更新：阴影用 var(--elev-raised)、圆角用 var(--radius-sm/md/lg/pill)、新增字距规则
- 前端交付检查从14项扩展到19项

## [1.2.1] - 2026-06-17

### Added
- **IMA 知识库增强**：专家团可通过 IMA MCP 连接器（`mcp__ima-mcp`）检索用户私有知识库
  - Team Lead 新增「IMA 知识库增强」章节，定义 Phase 0.5 判断流程
  - PM 新增 IMA 知识库使用指引（搜索竞品资料、业务背景文档）
  - 架构师新增 IMA 知识库使用指引（技术规范、基础设施文档）
  - plugin.json 新增 `connectorIds: ["ima-mcp"]`
- **记忆系统增强**：Team Lead 新增「记忆系统增强」章节，定义各阶段知识沉淀规则

### Changed
- IMA 是增强不是替代：无 IMA 知识库时正常工作，不影响现有流程

## [1.2.0] - 2026-06-17

### ⛔ P0 绝对规则强化（本次核心变更）

**问题**：v1.1.0 中 emoji 禁令仅写在设计师和前端两人的文件中，其他 5 位专家无认知；Team Lead 门禁检查不够强制；缺少可执行的检测手段。导致用户使用后仍出现 emoji 图标和丑陋设计。

**解决方案**：全面升级 P0 规则的执行力度，从"文字约束"升级为"多层级强制门禁"。

### Added
- **团队级 P0 绝对规则**：在 team-lead.md 顶部新增独立章节，emoji 禁令 + 紫粉渐变禁令 + AI 模板味禁令三条 P0 规则凌驾于一切之上
- **emoji 检测正则**：`[\x{1F300}-\x{1F9FF}\x{2600}-\x{26FF}\x{2700}-\x{27BF}]` — 所有阶段门禁都用此正则扫描
- **emoji 替换对照表**：🚀→Rocket, ✨→Sparkles, 📊→BarChart3, 🎯→Target 等 18 个常见 emoji→Lucide 映射
- **Phase 1 下发指令嵌入 P0**：给 PM/架构师/设计师的指令模板中全部包含 P0 规则提醒
- **Phase 2 Emoji 扫描步骤**：设计师输出后必须执行 emoji 正则扫描，零容忍
- **Phase 3 Emoji 代码扫描**：前端代码完成后必须执行 emoji 正则扫描，零容忍
- **Phase 4 最终 P0 全量扫描**：QA 阶段加入 emoji/紫粉渐变/AI模板味 三项扫描
- **QA 缺陷分级更新**：emoji 作为 UI 功能图标 = P0 致命缺陷
- **QA 视觉合规测试章节**：新增 emoji 扫描、紫粉渐变扫描、AI 模板味扫描三组 bash 命令
- **所有 8 位专家 P0 认知**：PM/架构师/QA/运维/后端全部添加 P0 绝对规则认知章节
- **启动标识更新**：版本号 v1.2.0，增加 P0 规则一行提示
- **自查清单升级**：设计师从 13 项→16 项（P0 三项前置），前端从 11 项→14 项（P0 三项前置）
- **设计质量前置门禁**：设计提示词必须包含 Lucide 图标系统锁定

### Changed
- Team Lead 门禁汇总表：从 10 行增至 15 行，每个 Phase 都有 P0 检测
- Plugin.json description：强化 P0 规则声明
- 前端规则编号：规则 1/2/3 → P0-1/P0-2/P0-3，与团队级规则对齐
- 设计师八条红线中 emoji 规则：引用 P0-1 详细定义，避免重复描述
- 前端工作流程：新增第 6 步 emoji 扫描

## [1.1.0] - 2026-06-10

### Added
- Multi-framework frontend support: React, Vue 3, Next.js, Taro 3, Nuxt 3
- CloudBase cloud function development guide for backend
- Real-time communication: WebSocket, SSE, CloudBase real-time listener
- File upload and object storage: COS, S3
- WeChat login and payment integration
- Mobile/responsive design spec with breakpoints and touch targets
- Design deliverable format definition
- Security testing (OWASP Top 6) for QA
- API contract (OpenAPI 3.0) requirement for architect
- Non-functional requirements in PRD template
- Lightweight project fast path
- Phase failure/timeout handling mechanism
- Pause/resume mechanism
- Progress reporting in Phase 2/3
- Quantified Spec change criteria
- Monitoring and logging for DevOps
- Vercel + Railway deployment for DevOps
- Docker multi-stage build for DevOps
- Vector database (pgvector) for AI products
- Error monitoring: Sentry integration templates for Express backend + React frontend
- Data analytics: PM埋点方案（5类必埋事件）+ 前端 analytics 封装
- Feature Flag: 轻量级灰度发布方案（DB-based, 4阶段灰度策略）
- Redis cache strategy: 缓存中间件、键格式、失效策略
- CORS configuration: Express/FastAPI/CloudBase 三方案 + 安全注意事项
- Database backup: pg_dump cron脚本、各平台备份方案、月度验证
- Search design pattern: ILIKE/tsvector/Meilisearch/pgvector 按数据量选型
- Email & notification: Resend/SendGrid/SES + 站内通知（WebSocket 推送）
- SEO guide: Next.js sitemap/robots/structured data, Nuxt useHead, SPA prerender
- i18n: react-i18next / vue-i18n / Next.js i18n 路由 + 文案规范
- API versioning: 所有端点 `/api/v1/` 前缀 + 版本管理规则
- `.gitignore` template in `templates/` directory
- `promptFileSnapshot` field in plugin.json for version tracking

### Fixed
- Agent ID global collision: all IDs now have plugin prefix
- Shared memory pool replaced with send_message flow
- Phase 0/1 boundary clarified
- "One confirmation" over-promise corrected
- CloudBase deploy command updated (tcb deploy)
- Light theme Token completed (shadow/radius/duration/easing)
- Designer description data source clarified
- Empty/Error component states elevated to required
- Designer color table vs anti-purple rule contradiction: clarified Indigo/Slate Blue as solid colors are allowed; only Indigo→Pink gradient + glow + frosted-glass combo is forbidden
- README/README_EN "唯一交互点" over-promise: updated to match team-lead "确认后自动推进"
- Frontend visual checklist anti-purple description aligned with designer's clarified rule

## [1.0.0] - 2026-06-09

### Added
- Initial release with 7-expert team
- 6-phase SOP workflow
- Shared memory pool (deprecated in 1.1.0)
- Three-document confirmation mechanism
- Auto lint-test-fix loops
- Anti-AI-slop design enforcement
