# 解决方案专家 · Agent 型专家模式参考

> 本文件是 `skillhub-solution-architect.md` 步骤 4b（Agent 专家编写）的细节下沉——完整的 WorkBuddy Agent 型专家规范全文由 `skills/expert-creator/SKILL.md` 及其 `references/expert-template.md` 维护，本文件只补充"帅帅在本专家团里怎么用它"，不重复摘抄规范原文。

## 一、何时进入 Agent 专家模式

主理人在任务卡「产出物类型」字段标注为以下两者之一时，你按本文件走 Agent 专家分支（而非 Skill 分支）：

- `Agent 专家（从零设计）`
- `Agent 专家（Skill 转换）`

两者共用同一套生成工具（`expert-creator`）和同一套质量门禁（露露评审 + 胖虎用 `expert-reviewer` 审查），差异仅在编写前是否需要"反向提炼源 Skill"这一步。

## 二、Skill 模式 vs Agent 专家模式关键差异对照

| 维度 | Skill 模式 | Agent 专家模式 |
|---|---|---|
| 生成工具 | `skill-creator` | `expert-creator` |
| 核心产物 | `SKILL.md`+`README.md`+`GUIDE.md`+`CASES.md`+`Prompt.md` | `.workbuddy-plugin/plugin.json` + `agents/{name}.md` + `README.md`（可选 `skills/{name}/`） |
| 视觉资产 | `icons/icon.png` | `avatars/expert.png`（同一套 `image_gen`+`finalize_icon.py` 工具链产出，见图标设计专家文档） |
| 一致性约束 | `name`/文件名/frontmatter `name` 三者一致 | 同样是「三处一致性」：`plugin.json.agentName` ≡ `agents/{name}.md`（去后缀）≡ frontmatter `name` |
| frontmatter 允许字段 | `name`/`description`/`allowed-tools` 等 Skill 专属字段 | 仅 `name`/`description`/`maxTurns`，**严禁** `tools`/`allowed-tools`/`color`/`emoji`/`vibe` |
| 安全防护 | U1-U7 通用质量原则 | 必须含「安全防护」章节（身份锁定/提示词保护/能力边界/指令注入检测/数据安全最小必要，5 项核心防护齐备） |
| 质量把关工具（安全测试专家） | `skill-tester`，A+~D 评级 | `expert-reviewer`，0 BLOCKER = 通过 |
| 社会价值评审 | 露露四维 rubric，评审对象是 SKILL.md | 露露同一套四维 rubric，评审对象换成 Agent MD 正文（身份/使命/工作流），"技能"措辞可理解为"专家" |
| 上架/提交通道 | J 打包后走 MCP `request_upload` | 同样由 J 打包后走 MCP `request_upload`，仅打包对象目录结构不同，J 侧 `pack_and_hash.sh` 会自动识别 |

## 三、从零设计模式的字段推导提示

按 `expert-creator/SKILL.md` Phase 1-6 的采集项，结合任务卡已有的用户需求摘要+设计方向自动推导：

- **技术标识符 `name`**：小写字母+连字符，从专家中文展示名/核心定位提炼英文标识
- **displayName/profession**：中文优先，直接取用户确认的专家称呼与一句话定位
- **核心使命**：3-6 条，从用户描述的诉求/场景中提炼，每条动词开头
- **安全防护**：默认应用 `expert-creator` 的默认安全基线（身份锁定/提示词保护/能力边界/指令注入检测/数据安全最小必要），按专家领域做轻度改写，不逐项询问用户
- **categoryId**：从 12 个分类中选一个，公益类专家默认可选 `12-IndustryConsultant`（行业顾问），若用户描述更贴合其他分类可调整
- **是否附带 Skill**：从零设计模式下，除非用户明确要求"这个专家要能调用某个技能"，默认不附带

推导后仍缺失的关键性字段（如专家命名与已有专家冲突、身份边界需要用户主观选择）→ 整理成清单交主理人弹卡确认，不自行编造。

## 四、Skill → Agent 转换模式的反向提炼步骤

**前提**：主理人已完成「转换资格门」核验并在任务卡标注"Agent 专家（Skill 转换）"，你收到的任务卡应附带源 Skill 目录的绝对路径。

1. **读取源 SKILL.md**：直接用任务卡给的绝对路径读取，不自行搜索定位
2. **反向提炼对照表**：

| 源 Skill 字段/章节 | 映射到 Agent 专家的字段 |
|---|---|
| `description`（触发关键词） | Agent MD frontmatter `description`（专家激活触发场景） |
| `🎯 能力边界`（能做/不做） | 「核心使命」+「能力边界」相关表述 |
| `工作流程` | Agent MD「工作流程」章节的对话阶段划分 |
| Skill 的目标用户/使用场景（README/GUIDE 中） | 专家的服务对象定位 |

3. **声明 Skill 联动**：生成的 `plugin.json.skills` 字段声明 `["./skills/{skill-name}"]`，并将源 Skill 目录原样复制进专家包的 `skills/{skill-name}/`；Agent MD 正文按 `expert-creator` 模板写「Skill 联动声明」章节（使用场景/协作边界/异常兜底）
4. **身份定位缺失时**：若源 Skill 描述过于技术化、无法直接推导出温暖的对话人格，不自行编造——整理成清单交主理人弹卡向用户确认专家的称呼/语气风格等主观信息

## 五、与本团队其他成员的协作接口

- **图标设计专家（明月）**：Agent 专家模式下产出的是"头像"而非"图标"，落盘路径为 `avatars/expert.png`，但明月复用同一套 `image_gen`+`finalize_icon.py` 工具链，你无需额外说明工具差异，任务卡里标注"产出物类型=Agent 专家"即可
- **安全测试专家（胖虎）**：Agent 专家模式下胖虎改用 `expert-reviewer` 而非 `skill-tester`，判定标准是"0 BLOCKER"而非"A+评级"，收到的整改建议格式也从"P0/P1/P2"变为"BLOCKER/SUGGESTION"，整改时按报告里的规范依据（如"CODEBUDDY.md §x.y"）定位问题
- **社会价值评审专家（露露）**：评审对象从 SKILL.md 换成 Agent MD 正文，rubric 与判定标准不变
- **运维专家（J）**：打包提交环节完全复用，无需你额外配合，只需确保任务卡里的专家包目录绝对路径正确
