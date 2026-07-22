# 技术公益专家团

> WorkBuddy 专家市场上架包 · 符合《WorkBuddy 专家开发规范 v2.0》
>
> 🎖️ **Team 型专家团**：6 位专家协作，覆盖技能创作全生命周期（需求 → 编写 → 测试 → 评审 → 图标 → 版权 → 交付）

## 一、专家团概览

| 项 | 值 |
|---|---|
| **技术名称** | `skillhub-charity-expert-team` |
| **展示名称** | 技术公益专家团 / Tech for Good Expert Team |
| **职业** | 公益行业智能方案支持与质量保障团队 |
| **类型** | **Team 型（多专家协作）** |
| **行业分类** | `12-IndustryConsultant`（行业顾问） |
| **版本** | 1.0.0 |

## 二、团队阵容

| 角色 | 中文名 | 标识 | 核心能力 | 依赖工具/技能 |
|------|------|------|---------|---------|
| 🎯 **主理人** | 星星 | skillhub-manager | 流程调度、质量审核、用户交互、结论核验 | AskUserQuestion |
| 🎨 **解决方案专家** | 帅帅 | skillhub-solution-architect | 需求分析、技能设计编写 | **skill-creator** |
| 🛡️ **安全测试专家** | 胖虎 | skillhub-security-tester | 全维度测试、安全审计 | **skill-tester v2.6.0** |
| 🌈 **社会价值评审专家** | 露露 | skillhub-social-value-evaluator | 四维公益价值评审（契合度/受助者保护/价值导向/合规边界） | 独立 rubric |
| 🖼️ **图标设计专家** | 明月 | skillhub-icon-designer | 生成 3 稿图标候选 → 用户选定 → 定稿处理为 512x512 落盘 | **image_gen** + `scripts/finalize_icon.py` |
| ⚖️ **活动运营专家** | 芋头 | skillhub-operation-expert | 软著权声明、信息采集 | AskUserQuestion |
| 📦 **运维专家** | J | skillhub-ops-expert | 打包、信息汇总、MCP/问卷/本地三级降级交付 | Bash / MCP / **wenjuan-fallback-submit** |

## 三、核心工作流（Phase 1→2→(2.5+3 两线并行)→3.5→4→5）

```
用户描述需求
      │
      ▼
[Phase 1] 主理人：需求确认（AskUserQuestion 交互）
      │
      ▼
[Phase 2] 解决方案专家：≥3 设计思路选型 → 用 skill-creator 编写技能
      │
      ▼
[Phase 2.5 + 3]（两线并行，互不依赖）
      ├─ 安全测试专家：skill-tester 全维度测试 → A+（≥4.75）才通过
      └─ 社会价值评审专家：四维 rubric → 总分≥80 且无单项<60 才通过
      │   测试/评审任一不通过 → 委托解决方案专家整改 → 聚焦复测（迭代上限 3 轮，图标线不受影响）
      ▼
[Phase 3.5]: 图标设计专家：生成 3 稿图标（image_gen 直出）→ 主理人逐张展示图片 + 弹卡选择 → 调用 finalize_icon.py 统一处理为 512x512 → 定稿落盘 icons/icon.png
      ├─ 用户不满意可反复重新设计，不构成"违规中断"
      ├─ 用户确认定稿并完成图片落盘后 → 进入 Phase 4
      ▼
[Phase 4] 活动运营专家：软著权声明确认 → 采集用户信息（待双门禁通过 + 图标定稿后启动）
      │  （标注：仅用于后期激励核对身份）
      ▼
[Phase 5] 运维专家：确认图标齐备 → zip 打包（pack_and_hash.sh 计算 MD5）
      │  → MCP 直传（首选）→ 腾讯问卷自动提交（次选兜底）→ 本地导出（最终兜底）
      │  → 回报前必须拿到可验证凭证（submission_id / 问卷截图 / 本地文件路径）才算完成
      ▼
提交成功（≠ 已上架，进入平台人工审核流程）
```

## 四、目录结构

```
skillhub-charity-expert-team/
├── .workbuddy-plugin/
│   └── plugin.json                          # ★ 配置文件（Team 型，7 agents）
├── .mcp.json                                #   MCP 连接器声明（ssvSkillHub）—— 该文件将在MCP恢复后添加
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
│   ├── skillhub-manager.md                  # ★ 主理人 — 团队协作机制 + 结论核验铁律
│   ├── skillhub-solution-architect.md       # ★ 解决方案专家 — 使用 skill-creator
│   ├── skillhub-icon-designer.md            # ★ 图标设计专家 — 直接用 image_gen 生成图标
│   ├── skillhub-security-tester.md          # ★ 安全测试专家 — 使用 skill-tester
│   ├── skillhub-social-value-evaluator.md   # ★ 社会价值评审专家 — 四维 rubric
│   ├── skillhub-operation-expert.md         # ★ 活动运营专家 — 版权确认 + 信息采集
│   └── skillhub-ops-expert.md               # ★ 运维专家 — 打包 + 三级降级交付
├── scripts/
│   ├── pack_and_hash.sh                      #   打包 + MD5 计算 + 图标齐备校验
│   ├── finalize_icon.py                      #   图标定稿处理：Pillow 统一缩放 512x512 + 可选 pngquant 压缩（跨平台一致）
│   └── requirements.txt                      #   finalize_icon.py 的 Python 依赖（Pillow）
├── skills/                                  # ★ 共享技能（按规范植入专家团）
│   ├── skill-creator/                       #   技能编写工具
│   ├── skill-tester/                        #   全维度测试工具（TRACE 对齐 v2.6.0）
│   └── wenjuan-fallback-submit/             #   MCP 失败后的腾讯问卷自动提交兜底
├── settings.json                            # ★ 主理人设置（agent 指向主理人 ID）
└── README.md                                # 本文件
```

## 五、设计理念

### 严格流水线，仅一组三线并行

- **Phase 2.5（图标）、3（测试）、3.5（评审）是唯一允许并行的一组**（三者维度正交、互不依赖，技能定稿后同时委托）
- 其余阶段一律串行，且**必须一气呵成连续推进**，不可在中途停手交差

### 专家分工而不越界

- ✅ 解决方案专家**只写技能**，不测试、不设计图标
- ✅ 图标设计专家**只做视觉**，不评价技能内容质量
- ✅ 安全测试专家**只测不修**，不能改技能文件
- ✅ 社会价值评审专家**只评审公益价值**，不评价技术架构
- ✅ 活动运营专家**只确认版权和采集信息**，不干预技能内容
- ✅ 运维专家**只打包交付**，不评审质量
- ✅ 主理人**只调度与核验**，不亲自写、测、审、发

### 迭代而不妥协，结论必须可验证

- Phase 2.5+3 的「方案 ↔ 测试/评审」循环是质量闸门：双门禁不通过不进入 Phase 3.5，迭代上限 3 轮
- **Phase 5 的"完成"判定必须基于可验证凭证**（submission_id/market_url、问卷脚本返回的 status+截图、或本地兜底文件路径），不能仅凭成员语气播报完成（详见 `skillhub-manager.md` 团队协作机制 #6 的真实事故记录）

## 六、安全与隐私

| 原则 | 实践 |
|------|------|
| **数据最小化** | 只采集机构名称、姓名、手机号 3 项 |
| **用途明示** | 采集时明确告知「仅用于后期激励核对身份」 |
| **不强制提供** | 手机号可选，缺失不阻塞流程 |
| **不打包个人信息** | 用户信息独立于技能包 zip，不泄漏到技能市场 |
| **不用于商业目的** | 采集的信息不用于营销、售卖或第三方共享 |
| **确定性优先于模型判断** | MD5、日期、图标像素尺寸等可机械确定的值，一律用脚本/系统命令取得，禁止 AI 口算或凭空生成 |

## 七、安装与上架

### 环境前置要求

- **操作系统**：macOS / Linux / Windows（Windows 需 WSL 或 Git Bash，因 `pack_and_hash.sh` 依赖 `zip` 命令；`finalize_icon.py` 为纯 Python 脚本，Windows 原生终端/PowerShell 即可运行，无需 WSL）
- **Python**：3.9+（用于 wenjuan-fallback-submit 脚本、图标定稿处理 `finalize_icon.py`）
- **Bash 工具链**：`zip`、`md5sum`（macOS 用 `md5`，脚本已自动适配）
- **Python 依赖**：
  - `pip install -r skills/wenjuan-fallback-submit/requirements.txt`（即 playwright ≥ 1.45）
  - `pip install -r scripts/requirements.txt`（即 Pillow ≥ 10.0，供 `finalize_icon.py` 缩放图标用）
- **浏览器内核**：`python3 -m playwright install chromium`（Windows 上 Python 启动器通常只注册 `python`，无 `3` 后缀，命令不可用时改用 `python -m playwright install chromium`；首次使用约 100MB 下载）
- **图标压缩工具（可选）**：`pngquant`，macOS/Linux/Windows 均有官方版本（如 `brew install pngquant` / `apt install pngquant` / `choco install pngquant`）；未安装时 `finalize_icon.py` 自动降级为交付未压缩的 512x512 PNG，不阻断流程
- **网络**：可访问 `wj.qq.com`（问卷提交通道）

### 本地测试

```text
# 测试 Prompt
我想创建一个志愿者工时管理的技能
帮我做一个公益项目申报自动化的技能
```

## 八、上架前自检清单

### 文件结构 ✅
- [x] `.workbuddy-plugin/plugin.json` 存在且格式正确（Team 型，含 teamInfo + members）
- [x] `agents/` 目录下有 7 个 Agent MD 文件（含 frontmatter displayName + profession）
- [x] `avatars/` 目录下有 `team.png` + 7 个成员头像
- [x] `skills/` 目录已植入 skill-creator、skill-tester、wenjuan-fallback-submit
- [x] `scripts/` 目录含 `pack_and_hash.sh`、`finalize_icon.py`、`requirements.txt`
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
- [x] `skills`: 指向 `./skills/skill-creator`、`./skills/skill-tester`、`./skills/wenjuan-fallback-submit`

### Agent MD 文件 ✅
- [x] 7 个 Agent 均有 frontmatter `name`、`description`、`displayName`、`profession`
- [x] frontmatter **不**包含 `tools` 字段（规范禁止）
- [x] 主理人 MD 包含「团队协作机制（铁律）」章节，含成员结论核验红线
- [x] 方案专家明确使用 skill-creator（规范 3.4）
- [x] 图标设计专家使用 `image_gen` 生成候选图，用户定稿后调用 `scripts/finalize_icon.py` 统一处理为 512x512（跨平台一致，不手写 sips/convert/magick）
- [x] 测试专家明确使用 skill-tester（规范 3.5）
- [x] 活动运营专家正确标注信息用途
- [x] 运维专家定义了 MCP → 问卷 → 本地导出三级降级方案

### 头像 ✅
- [x] 格式：PNG，7 个成员均有独立头像（非占位符）

## 九、版本约定

- **当前版本**：`1.0.0`
- 本地特性迭代过程中保持版本不变，变更累积到 `charity/skillhub.md` 设计文档
- 正式发版时修改 `plugin.json` 的 `version` + git push

## 十、关联资源

- **skill-creator**：[`../../skill-creator/SKILL.md`](../../skill-creator/SKILL.md) — 技能编写工具
- **skill-tester v2.6.0**：[`../../skill-tester/SKILL.md`](../../skill-tester/SKILL.md) — TRACE 对齐测试工具
- **wenjuan-fallback-submit**：[`./skills/wenjuan-fallback-submit/SKILL.md`](./skills/wenjuan-fallback-submit/SKILL.md) — MCP 失败兜底通道
- **开发规范**：《WorkBuddy Skill 生态合作介绍》PDF（§4.3 提及官方图标尺寸参考为 32x32；本团队图标设计专家用 `image_gen` 生成候选图，用户定稿后调用 `scripts/finalize_icon.py` 统一处理为 512x512 PNG 并尝试 pngquant 压缩）
- **skillhub 设计文档与真实事故记录**：[`../../skillhub.md`](../../skillhub.md)

---

> 本专家团按 WorkBuddy 专家开发规范 v2.0 设计，符合团队协作型（Team）专家的上架审核标准。
