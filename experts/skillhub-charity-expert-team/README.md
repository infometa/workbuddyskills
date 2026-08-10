# 技术公益专家团

> WorkBuddy 专家市场上架包 · 符合《WorkBuddy 专家开发规范 v2.0》
>
> 🎖️ **Team 型专家团**：6 位专家协作，覆盖 Skill 或 Agent 型专家创作全生命周期（需求 → 编写 → 测试/审查 → 评审 → 图标/头像 → 版权 → 交付）

## 一、专家团概览

| 项 | 值 |
|---|---|
| **技术名称** | `skillhub-charity-expert-team` |
| **展示名称** | 技术公益专家团 / Tech for Good Expert Team |
| **职业** | 公益行业智能方案支持与质量保障团队 |
| **类型** | **Team 型（多专家协作）** |
| **行业分类** | `12-IndustryConsultant`（行业顾问） |
| **版本** | 1.0.0 |
| **支持产出物** | Skill（技能）/ Agent 型专家（从零设计 / Skill 转换） |

## 二、团队阵容

| 角色 | 中文名 | 标识 | 核心能力 | 依赖工具/技能 |
|------|------|------|---------|---------|
| 🎯 **主理人** | 星星 | skillhub-manager | 流程调度、质量审核、用户交互、结论核验、产出物类型判断 | AskUserQuestion |
| 🎨 **解决方案专家** | 帅帅 | skillhub-solution-architect | 需求分析、技能或 Agent 型专家设计编写 | **skill-creator**（Skill）/ **expert-creator**（Agent 专家） |
| 🛡️ **安全测试专家** | 胖虎 | skillhub-security-tester | 全维度测试、安全审计 / 合规审查 | **skill-tester v2.6.0**（Skill）/ **expert-reviewer**（Agent 专家） |
| 🌈 **社会价值评审专家** | 露露 | skillhub-social-value-evaluator | 四维公益价值评审（契合度/受助者保护/价值导向/合规边界），Skill 与 Agent 专家均适用 | 独立 rubric |
| 🖼️ **图标设计专家** | 明月 | skillhub-icon-designer | 生成 3 稿候选 → 用户选定 → 定稿处理为 512x512 落盘（图标 或 头像） | **image_gen** + `scripts/finalize_icon.py` |
| ⚖️ **活动运营专家** | 芋头 | skillhub-operation-expert | 软著权声明、信息采集 | AskUserQuestion |
| 📦 **运维专家** | J | skillhub-ops-expert | 打包（Skill 或 Agent 专家包）、信息汇总、MCP/问卷/本地三级降级交付 | Bash / MCP / **wenjuan-fallback-submit** |

## 三、核心工作流（产出物类型判断 →(Phase 0 可选)→1→2→(2.5+3 两线并行)→3.5→4→5）

```
用户描述需求 / 或询问"腾讯技术公益有哪些任务可以领取" / 或要求创建 Agent 专家 / 或要求把 Skill 转换为专家
      │
      ▼
[产出物类型判断]（新增，优先于任务类型判断）：Skill（默认）/ Agent 专家（从零设计）/ Agent 专家（Skill 转换，需先过「转换资格门」）
      │
      ▼
[Phase 0]（可选分支，仅 Skill 线）主理人：委托运维专家 list_requirements 查询建设中需求 → 弹卡供用户选择 → 汇入 Phase 1
      │
      ▼
[Phase 1] 主理人：需求确认（AskUserQuestion 交互；若源自 Phase 0 则基于选定需求做设计构思细化访谈；若为 Skill 转换则围绕源 Skill 内容细化）
      │
      ▼
[Phase 2] 解决方案专家：≥3 设计思路选型 → 目标是 Skill 用 skill-creator 编写；目标是 Agent 专家用 expert-creator 编写（转换模式先反向提炼源 Skill 定位）
      │
      ▼
[Phase 2.5 + 3]（两线并行，互不依赖）
      ├─ 安全测试专家：目标是 Skill 用 skill-tester 全维度测试 → A+（≥4.75）才通过；目标是 Agent 专家用 expert-reviewer 审查 → 0 BLOCKER 才通过
      └─ 社会价值评审专家：四维 rubric（Skill/Agent 专家通用）→ 总分≥80 且无单项<60 才通过
      │   任一不通过 → 委托解决方案专家整改 → 聚焦复测（迭代上限 3 轮，图标/头像线不受影响）
      ▼
[Phase 3.5]: 图标设计专家：生成 3 稿候选（image_gen 直出）→ 主理人逐张展示图片 + 弹卡选择 → finalize_icon.py 统一处理为 512x512 → 定稿落盘 icons/icon.png（Skill）或 avatars/expert.png（Agent 专家）
      ├─ 用户不满意可反复重新设计，不构成"违规中断"
      ├─ 用户确认定稿并完成图片落盘后 → 进入 Phase 4
      ▼
[Phase 4] 活动运营专家：软著权声明确认 → 采集用户信息（待双门禁通过 + 视觉资产定稿后启动）
      │  （标注：仅用于后期激励核对身份）
      ▼
[Phase 5] 运维专家：确认视觉资产齐备 → zip 打包（pack_and_hash.sh 自动识别 Skill/Agent 目录结构，计算 MD5 + 大小校验）
      │  → MCP 直传（首选，Skill 与 Agent 专家共用同一套 request_upload 通道）→ 腾讯问卷自动提交（次选）→ 本地导出（最终兜底）
      │  → 回报前必须拿到可验证凭证（submission_id + get_submission_status 复核 / 问卷截图 / 本地文件路径）才算完成
      ▼
提交成功（≠ 已上架，进入平台人工审核流程）
```

## 四、目录结构

```
skillhub-charity-expert-team/
├── .workbuddy-plugin/
│   └── plugin.json                          # ★ 配置文件（Team 型，7 agents）
├── .mcp.json                                # ★ MCP 连接器声明（ssvSkillHub，固定 Token 鉴权）
├── avatars/
│   ├── team.png                             # ★ 团队头像
│   ├── team-lead.png                        #   主理人头像
│   ├── member-solution.png                  #   方案专家头像
│   ├── member-icon-designer.png             #   图标设计专家头像
│   ├── member-tester.png                    #   安全测试专家头像
│   ├── member-evaluator.png                 #   社会价值评审专家头像
│   ├── member-legal.png                     #   活动运营专家头像
│   └── member-ops.png                       #   运维专家头像
├── agents/
│   ├── skillhub-manager.md                  # ★ 主理人 — 团队协作机制 + 产出物类型判断 + 结论核验铁律
│   ├── skillhub-solution-architect.md       # ★ 解决方案专家 — 使用 skill-creator（Skill）/ expert-creator（Agent 专家）
│   ├── skillhub-icon-designer.md            # ★ 图标设计专家 — image_gen 生成候选图 + finalize_icon.py 定稿处理（图标/头像）
│   ├── skillhub-security-tester.md          # ★ 安全测试专家 — 使用 skill-tester（Skill）/ expert-reviewer（Agent 专家）
│   ├── skillhub-social-value-evaluator.md   # ★ 社会价值评审专家 — 四维 rubric（Skill/Agent 专家通用）
│   ├── skillhub-operation-expert.md         # ★ 活动运营专家 — 版权确认 + 信息采集
│   ├── skillhub-ops-expert.md               # ★ 运维专家 — 需求查询 + 打包（自动识别类型）+ 三级降级交付
│   └── references/
│       ├── skillhub-ops-expert-mcp-protocol.md          #   MCP 协议唯一权威参考（list_requirements/request_upload/get_submission_status，含固定 Token 鉴权与 429 限频重试）
│       ├── skillhub-ops-expert-packaging-templates.md   #   metadata.md 生成模板 + 材料重命名规则 + 回报模板
│       ├── skillhub-solution-architect-agent-mode.md    #   帅帅的 Agent 型专家模式差异对照与协作细节
│       ├── skillhub-cross-platform-paths.md             #   团队级共用铁律：~/.workbuddy/... 家目录路径的跨平台（macOS/Linux/Windows/WSL）处理规则
│       └── skillhub-incident-log.md                     #   团队真实事故档案（按角色分组，全体成员文档统一指针引用，避免事故叙述多处重复维护）
├── scripts/
│   ├── pack_and_hash.sh                      #   打包 + MD5 计算 + 视觉资产齐备校验 + 大小硬性校验，自动识别 Skill/Agent 目录结构并剔除过程文件
│   ├── finalize_icon.py                      #   图标/头像定稿处理：Pillow 统一缩放 512x512 + 可选 pngquant 压缩（跨平台一致）
│   └── requirements.txt                      #   finalize_icon.py 的 Python 依赖（Pillow）
├── skills/                                  # ★ 共享技能（按规范植入专家团）
│   ├── skill-creator/                       #   技能编写工具
│   ├── skill-tester/                        #   全维度测试工具（TRACE 对齐 v2.6.0）
│   ├── wenjuan-fallback-submit/             #   MCP 失败后的腾讯问卷自动提交兜底
│   ├── expert-creator/                      #   Agent 型专家生成工具（帅帅使用）
│   └── expert-reviewer/                     #   Agent 型专家合规审查工具（胖虎使用）
├── settings.json                            # ★ 主理人设置（agent 指向主理人 ID）
└── README.md                                # 本文件
```

## 五、设计理念

### 严格流水线，仅一组三线并行

- **Phase 2.5（图标/头像）、3（测试/审查）、3.5（评审）是唯一允许并行的一组**（三者维度正交、互不依赖，定稿后同时委托）
- 其余阶段一律串行，且**必须一气呵成连续推进**，不可在中途停手交差

### 两条产出物线，共用协作范式与提交通道

- **Skill 线**：需求→帅帅用 skill-creator 编写→胖虎用 skill-tester 测试（A+门禁）→明月出图标→J 打包提交
- **Agent 专家线**：需求（或转换资格门核验通过的源 Skill）→帅帅用 expert-creator 编写→胖虎用 expert-reviewer 审查（0 BLOCKER 门禁）→明月出头像→J 打包提交
- 两条线共用：露露的社会价值评审 rubric、J 的 MCP 提交通道（`request_upload`/上传/`get_submission_status`）、图标设计专家的生图与定稿处理工具链，仅打包环节由 `pack_and_hash.sh` 自动识别目录结构分流

### 专家分工而不越界

- ✅ 解决方案专家**只写内容**，不测试、不设计视觉资产
- ✅ 图标设计专家**只做视觉**，不评价内容质量
- ✅ 安全测试专家**只测不修**，不能改内容文件
- ✅ 社会价值评审专家**只评审公益价值**，不评价技术架构
- ✅ 活动运营专家**只确认版权和采集信息**，不干预内容
- ✅ 运维专家**只打包交付**，不评审质量
- ✅ 主理人**只调度与核验**，不亲自写、测、审、发

### 迭代而不妥协，结论必须可验证

- Phase 2.5+3 的「方案 ↔ 测试/评审」循环是质量闸门：双门禁不通过不进入 Phase 3.5，迭代上限 3 轮
- **Phase 5 的"完成"判定必须基于可验证凭证**（MCP：submission_id + `get_submission_status` 复核到的真实状态；问卷：脚本返回的status+截图；本地兜底：文件路径），不能仅凭成员语气播报完成（详见 `skillhub-manager.md` 团队协作机制「结论核验」；相关事故见 `agents/references/skillhub-incident-log.md` INC-02）

## 六、安全与隐私

| 原则 | 实践 |
|------|------|
| **数据最小化** | 只采集机构名称、姓名、手机号 3 项 |
| **用途明示** | 采集时明确告知「仅用于后期激励核对身份」 |
| **不强制提供** | 手机号可选，缺失不阻塞流程 |
| **不打包个人信息** | 用户信息独立于主包 zip，不泄漏到市场 |
| **不用于商业目的** | 采集的信息不用于营销、售卖或第三方共享 |
| **确定性优先于模型判断** | MD5、日期、图标/头像像素尺寸等可机械确定的值，一律用脚本/系统命令取得，禁止 AI 口算或凭空生成 |
| **MCP 鉴权** | 固定 `MCP_AUTH_TOKEN` 已写入 `.mcp.json`，禁止在对话中提及或引导用户填写 |

## 七、安装与上架

### 环境前置要求

- **操作系统**：macOS / Linux / Windows（Windows 需 WSL 或 Git Bash，因 `pack_and_hash.sh` 依赖 `zip` 命令；`finalize_icon.py` 为纯 Python 脚本，Windows 原生终端/PowerShell 即可运行，无需 WSL）
- **Python**：3.9+（用于 wenjuan-fallback-submit 脚本、图标/头像定稿处理 `finalize_icon.py`、`expert-reviewer` 的 `normalize.py`/`review.py`）
- **Bash 工具链**：`zip`、`md5sum`（macOS 用 `md5`，脚本已自动适配）
- **Python 依赖**：
  - `pip install -r skills/wenjuan-fallback-submit/requirements.txt`（即 playwright ≥ 1.45）
  - `pip install -r scripts/requirements.txt`（即 Pillow ≥ 10.0，供 `finalize_icon.py` 缩放图标/头像用）
- **浏览器内核**：`python3 -m playwright install chromium`（Windows 上 Python 启动器通常只注册 `python`，无 `3` 后缀，命令不可用时改用 `python -m playwright install chromium`；首次使用约 100MB 下载）
- **图标压缩工具（可选）**：`pngquant`，macOS/Linux/Windows 均有官方版本（如 `brew install pngquant` / `apt install pngquant` / `choco install pngquant`）；未安装时 `finalize_icon.py` 自动降级为交付未压缩的 512x512 PNG，不阻断流程
- **网络**：可访问 `wj.qq.com`（问卷提交通道）

### 本地测试

```text
# 测试 Prompt
我想创建一个志愿者工时管理的技能
帮我做一个公益项目申报自动化的技能
帮我创建一个公益领域的智能顾问专家
帮我把这个技能包装成一个专家
```

## 八、上架前自检清单

### 文件结构 ✅
- [x] `.workbuddy-plugin/plugin.json` 存在且格式正确（Team 型，含 teamInfo + members）
- [x] `agents/` 目录下有 7 个 Agent MD 文件（含 frontmatter displayName + profession）
- [x] `avatars/` 目录下有 `team.png` + 7 个成员头像
- [x] `skills/` 目录已植入 skill-creator、skill-tester、wenjuan-fallback-submit、expert-creator、expert-reviewer
- [x] `scripts/` 目录含 `pack_and_hash.sh`、`finalize_icon.py`、`requirements.txt`
- [x] 打包产物 zip 内不含 `icons/candidates/`/`avatars/candidates/`（候选草稿）、`reports/`、`.review-cache/`/`.review-work/`（审查过程缓存）等过程文件——由 `pack_and_hash.sh` 的 EXCLUDES 自动剔除，无需人工介入
- [x] 不包含 `hooks/`、`commands/`、`.lsp.json`
- [x] README.md 存在

### plugin.json ✅
- [x] `name`: `skillhub-charity-expert-team`
- [x] `expertType`: `team`
- [x] `agentName`: `skillhub-manager`（与主理人 MD 文件名/name 一致）
- [x] `teamInfo`: 含 `leadAgent` + `memberAgents`（6 成员）
- [x] `members`: 7 成员对象，含 id / name / profession / avatar / role
- [x] `profession` 与 `displayName` 一致（Team 型规范）
- [x] `displayDescription.zh` 在 40-50 字符范围内
- [x] `tags`: 固定 3 个
- [x] `quickPrompts`: 固定 3 个（第一条与 defaultInitPrompt 一致）
- [x] `skills`: 指向 `./skills/skill-creator`、`./skills/skill-tester`、`./skills/wenjuan-fallback-submit`、`./skills/expert-creator`、`./skills/expert-reviewer`

### Agent MD 文件 ✅
- [x] 7 个 Agent 均有 frontmatter `name`、`description`、`displayName`、`profession`
- [x] frontmatter **不**包含 `tools` 字段（规范禁止）
- [x] 主理人 MD 包含「团队协作机制（铁律）」章节 + 「产出物类型判断」+ 「转换资格门」，含成员结论核验红线
- [x] 方案专家明确使用 skill-creator（Skill，规范 3.4）/ expert-creator（Agent 专家）
- [x] 图标设计专家使用 `image_gen` 生成候选图，用户定稿后调用 `scripts/finalize_icon.py` 统一处理为 512x512（跨平台一致，不手写 sips/convert/magick），按产出物类型落盘到 `icons/icon.png` 或 `avatars/expert.png`
- [x] 测试专家明确使用 skill-tester（Skill，规范 3.5）/ expert-reviewer（Agent 专家）
- [x] 活动运营专家正确标注信息用途
- [x] 运维专家定义了 MCP → 问卷 → 本地导出三级降级方案，且打包脚本自动识别产出物类型

### 头像 ✅
- [x] 格式：PNG，7 个成员均有独立头像（非占位符）

## 九、版本约定

- **当前版本**：`1.0.0`
- 本地特性迭代过程中保持版本不变，变更累积到 `charity/skillhub.md` 设计文档
- 正式发版时修改 `plugin.json` 的 `version` + git push

## 十、关联资源

- **skill-creator**：[`../../skill-creator/SKILL.md`](../../skill-creator/SKILL.md) — 技能编写工具
- **skill-tester v2.6.0**：[`../../skill-tester/SKILL.md`](../../skill-tester/SKILL.md) — TRACE 对齐测试工具
- **expert-creator**：[`../../expert-creator/SKILL.md`](../../expert-creator/SKILL.md) — Agent 型专家生成工具
- **expert-reviewer**：[`../../expert-reviewer/SKILL.md`](../../expert-reviewer/SKILL.md) — Agent 型专家合规审查工具
- **wenjuan-fallback-submit**：[`./skills/wenjuan-fallback-submit/SKILL.md`](./skills/wenjuan-fallback-submit/SKILL.md) — MCP 失败兜底通道
- **开发规范**：《WorkBuddy Skill 生态合作介绍》PDF、《WorkBuddy-Expert-Standard》PDF（Agent 型专家规范）
- **MCP 使用文档**：《WorkBuddy 专家团 MCP Server》PDF（含固定 Token 鉴权、429 限频重试机制）
- **skillhub 设计文档与真实事故记录**：[`../../skillhub.md`](../../skillhub.md)

---

> 本专家团按 WorkBuddy 专家开发规范 v2.0 设计，符合团队协作型（Team）专家的上架审核标准。

