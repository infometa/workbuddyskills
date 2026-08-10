# 审查检查项速查表 + 报告模板

本文件是 `expert-reviewer` 的检查项索引和报告模板，**不是规范定义**。规范定义在 `CODEBUDDY.md` 与 `WorkBuddy专家开发规范.md` 中，由 LLM 在审查时实时读取。本文件每条检查项标注规范出处，便于报告中引用。

---

## 一、检查项总目录（按 CODEBUDDY.md §十七 Checklist 组织）

### A 组：一致性硬性（不通过则不可上架，BLOCKER 级）

适用于所有专家类型，外部提交专家包均需检查。

| 编号 | 检查项 | 规范依据 | 脚本/LLM | 外部提交 适用 |
|------|--------|---------|---------|--------------|
| A01 | plugin.json 文件存在且可解析 | §三 | 脚本 | ✅ |
| A02 | plugin.json `name` 为小写字母+连字符 | §3.1 | 脚本 | ✅ |
| A03 | plugin.json `version` 为合法 semver（仅纯数字） | §3.1 | 脚本 | ✅ |
| A04 | plugin.json `expertType` ∈ {agent, team, plugin} | §3.3 | 脚本 | ✅ |
| A05 | `agentName` = Agent 定义文件 `name` = 文件名（不含 .md） | §十三-1 / §十七 | 脚本 | ✅ |
| A06 | `agentName` 有业务语义（非 `team-lead` 等通用名） | §3.3 / §十三-1 | 脚本（关键词黑名单）+ LLM | ✅ |
| A07 | Team 型：`teamInfo.memberAgents[]` ID = `members[].id` = 定义文件名 | §十三-2 | 脚本 | ✅ |
| A08 | Team 型：`members[]` 必须包含主理人（role=lead） | §3.6 / §十七 | 脚本 | ✅ |
| A09 | Team 型：`members[].role` 必须为字符串 `"lead"` 或 `"member"` | §3.6 | 脚本 | ✅ |
| A10 | Team 型：settings.json `agent` = plugin.json `agentName` | §八 / §十三-4 | 脚本 | ✅ |
| A11 | plugin.json `avatar` 路径指向实际存在的文件 | §十三-3 | 脚本 | ✅ |
| A12 | plugin.json `skills[]` 路径下存在对应 SKILL.md | §十三-5 | 脚本 | ✅ |
| A13 | Agent frontmatter `tools` 字段：要么不加，要么写全（禁止部分指定） | §4.1 / §十三-6 / §十七 | 脚本（启发） + LLM | ✅ |
| A14 | agents/、skills/、avatars/ 在插件根目录（不在 `.codebuddy-plugin/` 里） | §二 / §十七 | 脚本 | ✅ |
| A15 | `agents/` 下只有 agent 定义文件（带 frontmatter 的 .md） | §十七 | 脚本（检测无 frontmatter 的 md） | ✅ |
| A16 | 配置目录下只有 `plugin.json`（无 agents/skills/avatars/hooks/commands/.lsp.json） | §十七 | 脚本 | ✅ |
| A17 | 所有 JSON 文件可正常解析 | §十七 | 脚本 | ✅ |

> **说明**：A14 的「配置目录」允许 `.workbuddy-plugin/` 或 `.codebuddy-plugin/`。两者均通过校验，不列为审查阻断项。

### B 组：Team 型专项（required，主理人/成员 Prompt 完整性）

仅 `expertType=team` 时检查。绝大多数为 LLM 通过读规范判断。

| 编号 | 检查项 | 规范依据 | 严重性 | 外部提交 适用 |
|------|--------|---------|--------|--------------|
| B01 | 主理人 prompt 含「团队协作机制（铁律）」章节 + 4 条正则 | WorkBuddy §5.2.1 / CODEBUDDY §4.4 | BLOCKER | ✅ |
| B02 | 主理人 prompt 含 5 条红线（禁跳 TeamCreate / 禁代写 / 禁跳阶段 / 禁直连 / 禁 spawn 自己） | CODEBUDDY §4.4 | BLOCKER | ✅ |
| B03 | 主理人 prompt 含协作规则（TeamCreate→Agent spawn→SendMessage 回传 流程 + 名称参数） | CODEBUDDY §4.4 | BLOCKER | ✅ |

| B07 | 成员 prompt 含角色定义、擅长领域 3-5 个、分析框架、输出模板 | CODEBUDDY §4.5.3 / WorkBuddy §5.3 | BLOCKER | ✅ |
| B08 | 成员 prompt 明确要求通过 SendMessage 回传给主理人 | CODEBUDDY §4.5.3 第 6 点 | SUGGESTION（强烈建议） | 建议提示，不阻断 |
| B09 | 术语统一：使用「主理人」/「团队成员」，不使用「团长」/「团员」 | §十七 | SUGGESTION | ✅ |


### C 组：展示字段质量（agent/team 上架必填）

| 编号 | 检查项 | 规范依据 | 严重性 | 外部提交 适用 |
|------|--------|---------|--------|--------------|
| C01 | plugin.json `displayName.zh` / `displayName.en` 必填 | §3.5 | BLOCKER | ✅ |
| C02 | plugin.json `displayDescription.zh` 在 40-50 字之间 | §3.5 / WorkBuddy §3.3 | SUGGESTION | ✅ |
| C03 | plugin.json `defaultInitPrompt` 必须与 `quickPrompts[0]` 一致 | §3.5 | SUGGESTION | ✅ |
| C04 | plugin.json `categoryId` ∈ §十一 13 个标准分类 | §十一 | BLOCKER | ✅ |

| C06 | `tags` 数量建议 3-5 个 | §3.5 / WorkBuddy §3.3 | SUGGESTION | ✅（仅判断范围） |
| C07 | Agent MD frontmatter 含 `displayName` 与 `profession` 必填 | §4.1 / WorkBuddy §4.2 | SUGGESTION | ✅ |
| C08 | `displayDescription`、`description`、Agent prompt 不得包含与平台实际运行方式不符的技术承诺（如"本地AI""全程不联网""离线运行""不上云""零数据外传"等），CodeBuddy/WorkBuddy 的模型推理均通过云端进行 | 平台事实 | BLOCKER | ✅ |

### D 组：头像规范

| 编号 | 检查项 | 规范依据 | 严重性 | 外部提交 适用 |
|------|--------|---------|--------|--------------|
| D01 | 头像格式 PNG 或 JPG | §十 | BLOCKER | ✅ |
| D02 | 头像尺寸 512×512 px | §十 | BLOCKER | ✅ |
| D03 | 头像大小 ≤500KB | §十 | BLOCKER | ✅ |
| D04 | Team 型：每个成员都有对应头像文件 | §十 | BLOCKER | ✅ |

### E 组：金融类专项（仅金融类专家团触发）

触发条件：`categoryId=08-FinanceInvestment` 或 plugin 名含金融关键词。

| 编号 | 检查项 | 规范依据 | 严重性 | 外部提交 适用 |
|------|--------|---------|--------|--------------|
| E01 | `defaultInitPrompt` 不含「能不能买/该买吗/推荐」等决策类措辞 | §17.1 / §18 | BLOCKER | ✅ |
| E02 | `displayDescription`、`description` 不暗示投资建议/买卖信号 | §17.1 / §18 | BLOCKER | ✅ |
| E03 | 主理人/成员 prompt 输出末尾要求免责声明（4 要素：AI 生成 + 公开信息 + 不构成投资建议 + 不构成个股推荐） | §17.2 | BLOCKER | ✅ |
| E04 | 数据来源披露要求（引用行情/财务/资金时标注来源） | §17.3 | SUGGESTION | ✅ |



### G 组：安全、依赖引导与通用性（参考 skill-reviewer v3.7）

| 编号 | 检查项 | 规范依据 | 严重性 | 外部提交 适用 |
|------|--------|---------|--------|--------------|
| G01 | 凭据/密钥/token/password 等真实值不得硬编码在专家包文件中 | 安全规则 / §十七 | BLOCKER | ✅ |
| G02 | `scripts/`、`bin/` 中不得存在越权读取、数据外传、危险 shell 命令等高风险行为 | 安全规则 / §十七 | BLOCKER 或 SUGGESTION | ✅ |
| G03 | 内网域名、内网软件源必须有适用范围说明或公网降级方案 | §十七 | SUGGESTION（影响可用性时 BLOCKER） | ✅ |
| G04 | 不应残留开发者个人路径、其他 IDE 平台路径、CDN `@latest` 未锁定版本 | 安全规则 / §十七 | SUGGESTION | ✅ |
| G05 | 有 `bin/`、`scripts/`、环境变量或外部服务依赖时，必须说明安装、版本、配置、验证方式 | §五 / §六 / §十七 | 关键依赖无引导 BLOCKER；部分缺失 SUGGESTION | ✅ |

### Q 组：深度质量评审（建议级，不阻断）

| 维度 | 判断重点 |
|------|----------|
| Q01 AI 可执行性 | 指令是否可被模型稳定执行，是否避免空泛口号 |
| Q02 路由/触发清晰度 | agent/skill 触发场景、职责边界是否清楚 |
| Q03 上下文效率 | Prompt 是否冗余，是否支持渐进加载 |
| Q04 容错降级 | 数据缺失、工具不可用、外部依赖失败时是否有降级 |
| Q05 角色边界 | Team 主理人与成员是否各司其职，不互相代写 |
| Q06 团队编排 | Workflow 是否有 Phase、输入输出依赖、串并行关系 |
| Q07 用户体验 | 输出是否结构化、易读、可行动 |
| Q08 受众适配 | 面向目标用户的术语、粒度和默认假设是否合适 |
| Q09 可移植性 | 是否避免本机路径、内网强依赖、平台锁死 |
| Q10 领域准确性 | 专业框架、边界与合规提示是否可靠 |
| Q11 可维护性 | 文件结构、引用关系、扩展方式是否易维护 |

---

## 二、Markdown 审查报告模板

> **使用说明**：LLM 在第七步生成报告时套用本模板。BLOCKER/SUGGESTION 数量按实际检测结果；每条问题必须标注规范依据与修复方案。

```markdown
# 专家包审查报告 - <plugin-name>

> 审查时间：<YYYY-MM-DD HH:MM>
> 审查人：CodeBuddy expert-reviewer

> 专家类型：<agent | team | plugin>

---

## 一、总体结论

**整体结论：<可上架 | 需修复后方可上架 | 需重大修改后再审>**

| 维度 | 数量 |
|------|------|
| 阻断问题（BLOCKER）| N |
| 建议改进项（SUGGESTION）| M |
| 亮点 | P |

预计修复工作量：约 X 分钟。

---

## 二、阻断问题（BLOCKER）— 必修后方可上架

### B01 ❌ <一句话标题>

- **现状**：
  ```
  <文件路径>:
  <引用文件原文，避免凭空臆断>
  ```
- **规范依据**：CODEBUDDY.md §x.y / WorkBuddy专家开发规范.md §a.b
- **修复方案**：<具体可执行的修复步骤；如可机械修复，标注「AI 可代修」>

### B02 ...

---

## 三、建议改进项（SUGGESTION）— 建议修复但不阻断上架

### S01 ⚠️ <一句话标题>

- **现状**：...
- **规范依据**：...
- **建议修复**：...
- **说明**：<为什么是 SUGGESTION 而非 BLOCKER>

---

## 四、深度质量评审

| 维度 | 评级 | 判断 |
|------|------|------|
| AI 可执行性 | 优/良/待改进 | <一句话判断> |
| 路由/触发清晰度 | 优/良/待改进 | <一句话判断> |
| 上下文效率 | 优/良/待改进 | <一句话判断> |
| 容错降级 | 优/良/待改进 | <一句话判断> |
| 角色边界 | 优/良/待改进 | <一句话判断> |
| 团队编排 | 优/良/待改进 | <一句话判断> |
| 用户体验 | 优/良/待改进 | <一句话判断> |
| 受众适配 | 优/良/待改进 | <一句话判断> |
| 可移植性 | 优/良/待改进 | <一句话判断> |
| 领域准确性 | 优/良/待改进 | <一句话判断> |
| 可维护性 | 优/良/待改进 | <一句话判断> |

**改进建议**（仅列评级为「待改进」的维度）。所有深度质量评审结论均为建议级，不阻断上架。

---

## 五、修复优先级表

| 优先级 | 编号 | 问题 | 工作量 |
|--------|------|------|--------|
| P0 | B01 | <BLOCKER 标题> | <预估时间> |
| P1 | S01 | <SUGGESTION 标题> | <预估时间> |
| ... | ... | ... | ... |

**预计总修复时间**：P0 约 X 分钟，P1 约 Y 分钟，总计约 Z 分钟。

---

## 六、亮点（可选）


- ✅ <突出的设计、合理的架构、优秀的 prompt 等>

---

## 附录：审查依据快照

- CODEBUDDY.md：<本次审查所依据的章节列表>
- WorkBuddy专家开发规范.md：<本次审查所依据的章节列表>
- 脚本输出：`<.review-cache/...>`
```

---

## 三、报告条目质量铁律

每条 BLOCKER / SUGGESTION 必须满足：

1. **现状必须有原文引用**——文件路径 + 行号 + 文件原文片段，不得凭文件名/关键词臆断
2. **规范依据必须精确到章节**——格式 `CODEBUDDY.md §x.y / WorkBuddy专家开发规范.md §a.b`
3. **修复方案必须可执行**——给出具体步骤，可机械修复的标注「AI 可代修」
4. **不要虚构问题**——若未读过文件，宁可标注「未确认」也不报为问题（参见 memory 82844461）
