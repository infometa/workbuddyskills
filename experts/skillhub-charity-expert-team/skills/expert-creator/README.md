# Expert Creator — WorkBuddy 专家包生成器

> 通过交互式问答，按《WorkBuddy 专家开发规范 v2.0》一键生成可直接 git push 上架的 AI 专家包。

## 一、这是什么

`expert-creator` 是一个 **WorkBuddy 平台内置工具型 Skill**，用于辅助第三方开发者**快速创建符合官方规范的 AI 专家包**。

调用它，你不需要：
- ❌ 手写 `.workbuddy-plugin/plugin.json`
- ❌ 自己组织 14+ 个必填字段
- ❌ 担心三处一致性约束（agentName ≡ 文件名 ≡ frontmatter name）
- ❌ 反复查阅 PDF 标准

它会：
- ✅ 6 阶段交互式采集所有必要信息
- ✅ 自动生成完整目录结构（`.workbuddy-plugin/` + `agents/` + `avatars/` + 可选 `skills/`）
- ✅ 自动注入默认安全基线
- ✅ 输出可直接 `zip` 提交审核的产物
- ✅ 中文优先填充所有面向用户的字段

## 二、什么时候调用

**触发关键词**：创建专家、生成专家、做一个专家、专家市场上架、new expert、create expert

**典型场景**：
- 想为某个垂直领域（公益、金融、医疗等）打造一个 AI 专家
- 已有一个 Skill，想包装成专家上架（专家可以调度 Skill）
- 旧版专家文件需要按 v2.0 规范重构
- 想快速验证某个专家创意，先生成 MVP 测试

**不该调用**：
- 你只想创建一个 Skill（请用 [`skill-creator`](../skill-creator/)）
- 你想测试一个已有 Skill（请用 [`skill-tester`](../skill-tester/)）

## 三、最小工作流（6 阶段）

调用本 Skill 后，会按以下流程引导你：

```
Phase 0  介绍流程 + 询问输出目录                  （1 分钟）
   ↓
Phase 1  基础元数据                                 （2 分钟）
         name / displayName / profession /
         displayDescription / categoryId / author
   ↓
Phase 2  核心使命 + 触发关键词 + tags             （1-2 分钟）
   ↓
Phase 3  规则与安全防护                             （1-2 分钟）
         默认基线 5 项核心 + 输出安全
   ↓
Phase 4  交付物 + 工作流 + Skill 联动              （2-3 分钟）
         quickPrompts / defaultInitPrompt
   ↓
Phase 5  进阶能力 + 沟通风格 + 知识库              （1-2 分钟）
   ↓
Phase 6  汇总确认 + 生成专家包目录                 （30 秒）
         三处一致性自动校验
```

**预计总耗时**：8-12 分钟

## 四、产出物

调用结束后，你会得到一个完整的目录结构：

```
{your-expert-name}/
├── .workbuddy-plugin/
│   └── plugin.json              # ★ 14 个必填字段全部就绪
├── avatars/
│   └── expert.png               # ★ 512×512 头像（含 SVG 占位模板）
├── agents/
│   └── {your-expert-name}.md    # ★ Agent 定义（含安全防护章节）
├── skills/                      #   可选：附带技能
│   └── {skill-name}/
└── README.md                    #   推荐：上架说明
```

## 五、如何在 WorkBuddy 中使用

### 方式 A：对话中触发（推荐）

```text
帮我创建一个公益慈善领域的 AI 专家
```

或者

```text
@skill://expert-creator
```

WorkBuddy 会自动激活本 Skill 并开始引导。

### 方式 B：作为 IDE/CLI 插件调用

参考 WorkBuddy 文档的 Skill 加载方式。

## 六、关键约束

调用 `expert-creator` 期间，请注意：

1. **频繁的交互问答**：本 Skill 大量使用 `AskUserQuestion`，请耐心回答（也可在任何阶段说"用默认值"快速跳过）
2. **三处一致性**：`name`、`agentName`、Agent MD 文件名必须完全一致——这是 PDF 规范铁律，本 Skill 会自动保证
3. **categoryId 必填**：从 12 个分类（PDF v2.0 §8）中选一个；如果实在拿不准，选 `12-IndustryConsultant`
4. **头像建议提前准备**：512×512 PNG/JPG，≤500KB；如果没有可以让本 Skill 生成 SVG 占位图
5. **Skill 嵌入策略**：如果专家需要调用 Skill，强烈建议把 Skill **拷贝到专家包内**（`skills/{name}/`），不要用符号链接

## 七、参考样板

本 Skill 内置以下 4 个生产可用样板，会在 Phase 6 询问是否复用其结构：

| 样板路径 | 类型 | 适合参考的场景 |
|---|---|---|
| `charity/experts/小益/` | Agent 型 + 内嵌 Skill | 标准单专家 + 带 Skill 联动 |
| `charity/experts/公益机构智能文书和财会助手/` | Agent 型 + 多 Skill | 复合型专家（多 Skill 编排） |

## 八、上架与发版

> ⚠️ **WorkBuddy 已支持 git 自动同步上架**：仓库在官方登记 git 路径后，**修改 plugin.json 的 `version` 字段并 push 即触发上架**，无需打包提交。

### 推荐流程（B 方案：日常迭代不改 version）

```bash
# 阶段 1：日常迭代（不改 version，CHANGELOG 累积）
# - 修改 agents/ / plugin.json 的非 version 字段 / skills/...
git commit -m "feat: 描述变更" && git push

# 阶段 2：想正式发版上架时
# - 直接修改 plugin.json 的 version（如 1.0.0 → 1.1.0）
git commit -am "release: v1.1.0" && git push
# → WorkBuddy 自动拉取登记的 git 路径，更新到新版本
```

### 离线分发（可选）

如需离线分享给同事测试或本地回归：

```bash
# 在 charity/experts/ 目录下打包（pack.sh 会自动同步上游 Skill 内容）
./pack.sh experts/{your-expert-name}
```

> 📌 离线打包**不是上架步骤**，仅用于本地分发。上架以 git push plugin.json（含新 version）为准。

## 九、与其他工具的关系

| 工具 | 产物 | 何时使用 |
|---|---|---|
| **`expert-creator`**（本工具） | 专家包 | 想做"AI 专家"上架专家市场 |
| [`skill-creator`](../skill-creator/) | Skill 包 | 想做单一能力的工具型 Skill |
| [`skill-tester`](../skill-tester/) | 测试报告 | 测试现有专家/Skill 的质量 |

**完整工作流**：
```
有创意 → expert-creator/skill-creator 创建
       → skill-tester 测试质量
       → 修改 version + git push 上架
       → 提交上架
```

## 十、常见问题

**Q1: 我已经有一个旧版专家文件，能用 expert-creator 重构吗？**
A: 可以。在 Phase 0 告诉它"我有现成专家想升级到 v2.0"，它会引导你逐字段对比并生成新版结构。

**Q2: 生成的 Agent MD 中能加 `tools` 字段吗？**
A: ❌ 不能。PDF v2.0 §11 明确：`tools` 字段会导致审核不通过，工具权限由系统统一分配。

**Q3: displayName.zh 必须是中文吗？**
A: 是的。本 Skill 面向中文用户场景，所有 `.zh` 字段必须有完整中文。`.en` 是辅助。

**Q4: 我要创建一个团队（Team 型）专家怎么办？**
A: 当前 v1.0 仅支持 Agent 型（单专家）。Team 型计划在 v2.0 支持，目前请参考 PDF v2.0 §5 手动创建。

## 十一、版本与维护

- **当前版本**：v1.0.0
- **遵循标准**：WorkBuddy 专家开发规范 v2.0（2026-04-15）
- **作者**：Tencent_SSV_Tech4Good
- **依赖**：`AskUserQuestion`、`write_to_file`、`read_file`

详细技术规范请参考 [`SKILL.md`](./SKILL.md) 与 [`references/expert-template.md`](./references/expert-template.md)。
