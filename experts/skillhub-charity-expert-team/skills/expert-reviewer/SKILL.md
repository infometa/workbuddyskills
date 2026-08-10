---
name: expert-reviewer
description: 审查外部提交的 Expert Marketplace 专家包（agent/team/plugin）合规性与质量，输出对外可交付的 Markdown 审查报告。触发场景：审查专家、检查专家包、专家合规审查、专家质量评估、review expert、check expert package。重点覆盖 plugin.json 字段、目录结构、Team 主理人铁律、成员协作回传、安全合规、金融类合规、头像规范等维度。
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Expert Reviewer

审查外部提交的 Expert Marketplace 专家包是否符合上架规范，按「脚本确定性形状检查 + LLM 实时读规范判断」分层执行，输出对外可交付的 Markdown 审查报告。

## 执行原则

> **⚠️ 严格规则**：所有「形状层」的确定性操作（目录骨架、JSON 解析、字段相等、文件存在、版本号格式、头像尺寸等）**必须调用 Python 脚本**，禁止 LLM 手动逐项检查。
>
> **⚠️ 严格规则**：所有「规范层」的语义判断（主理人 prompt 是否含 TeamCreate 铁律、成员是否要求 SendMessage 回传、金融文案是否合规等）**必须由 LLM 实时读取 CODEBUDDY.md 与 WorkBuddy专家开发规范.md** 后再下结论。**禁止凭印象、关键词或文件名臆断**。
>
> **⚠️ 严格规则**：每条 BLOCKER 必须有直接验证依据（读过的文件原文、命令输出、规范文档章节出处）。**未验证不得断言**——这是质量底线（参见 memory 82844461）。
>
> **⚠️ 严禁修改专家包业务内容**：除 frontmatter 字段顺序归一与编码归一外，审查阶段**不修改专家包的任何业务文件**（agents/*.md、SKILL.md body、plugin.json 业务字段、头像等）。所有修改只在审查工作目录内进行，不触碰原始输入目录以外的任何文件。
>
> **⚠️ 报告范围**：报告只输出「开发者需修复（BLOCKER）」和「建议优化（SUGGESTION）」。

---

## 审查流程（严格按顺序）

### 第零步：zip 解压（仅当输入为 .zip 文件时）

当用户提供的审查对象是 `.zip` 文件（如微信/邮件收到的压缩包）时，**必须按以下标准做法解压**，防止旧版文件残留导致审查结果失真：

```powershell
# 1. 确定审查工作目录（放在 zip 同级的 .review-work/ 下）
$zipPath = "<zip文件路径>"
$pluginName = "<plugin-name>"
$workRoot = Join-Path (Split-Path -Parent $zipPath) ".review-work"
$cacheDir = Join-Path $workRoot ("$pluginName-review")

# 2. 如果同名目录已存在，先整体删除（PowerShell Expand-Archive -Force 只覆盖同名文件，不清理 zip 中不存在的旧文件）
if (Test-Path $cacheDir) {
    Remove-Item -Recurse -Force $cacheDir
}

# 3. 解压到干净的目录
Expand-Archive -Path $zipPath -DestinationPath $cacheDir -Force
```

**关键规则**：
- **先删后解压**：`Expand-Archive -Force` 的行为是「覆盖同名文件」，**不会删除**目标目录中 zip 里不存在的文件。如果旧版残留文件混入，会导致审查到已删除的文件或遗漏新增文件
- **审查工作目录命名**：统一使用 `<zip同级目录>/.review-work/<plugin-name>-review/`（plugin-name 从 zip 文件名推断，去掉版本号后缀）
- **解压后验证**：解压完成后列出目录树，确认结构完整且无 `__MACOSX/`、`.DS_Store` 等打包垃圾干扰判断（这些可在报告中列为 SUGGESTION）
- **非 zip 输入跳过**：如果用户直接提供的是专家包目录路径或已解压的目录，无需此步

### 第一步：确定审查对象

**输入**：

1. 专家包路径（审查工作目录或已解压的专家包目录）
2. 可选：用户指定的报告输出路径

**前置动作 — 读取专家包基本信息**：

LLM 必须先读取专家包 `plugin.json`，并向用户展示以下信息：

```
📋 专家包基本信息：
- 包名：<plugin name>
- 作者：<author.name>（<author.email>）
- 类型：<expertType>
```

### 第二步：读取规范文档（关键步骤，不可跳过）

**LLM 必须用 read_file 读取本 skill 包内自带的两份规范副本**：

```
<skill_base_dir>/references/standards/CODEBUDDY.md
<skill_base_dir>/references/standards/WorkBuddy专家开发规范.md
```

**重点章节**：
- CODEBUDDY.md §一 ~ §十一：基础规范（专家类型/目录/plugin.json/Agent MD/Skill/头像/分类）
- CODEBUDDY.md §十三：一致性约束 7 条
- CODEBUDDY.md §十六：**外部提交审查原则**（尊重作者命名与角色设定）
- CODEBUDDY.md §十七：**交付前 Checklist**（最权威的检查项总目录）
- CODEBUDDY.md §十八：金融类专家团合规要求
- WorkBuddy专家开发规范.md §5.2.1：团队协作铁律

### 第三步：调用 normalize.py — 前置规范化

```bash
python <skill_base_dir>/scripts/normalize.py <expert_dir> --output-file <output_path>
```

脚本自动完成：
- BOM 移除、UTF-8 编码归一、CRLF→LF 换行统一
- plugin.json 字段顺序按 §三 规范重排
- Agent MD frontmatter 字段顺序归一

**LLM 职责**：读取 output JSON 的 `changes` 列表，确认所有自动修改符合预期。

### 第四步：调用 review.py — 形状层确定性检查 + ai_actions 输出

```bash
python <skill_base_dir>/scripts/review.py <expert_dir> \
  --output-file <json_path>
```

**脚本输出结构**（顶层字段）：

| 字段 | 说明 |
|------|------|
| `expert_dir` | 审查目录 |
| `plugin_name` | 从 plugin.json 提取 |
| `expert_type` | agent / team / plugin |

| `structure_findings[]` | 脚本确定性检测结果（目录骨架、JSON 解析、字段相等、文件存在、版本格式、头像尺寸） |
| `ai_actions[]` | 让 LLM 读规范判断的项（每项含 `reference_doc` 指向规范出处） |
| `finance_flag` | 是否触发金融类合规检查 |
| `report_skeleton` | Markdown 报告骨架 |

**LLM 职责**：
1. 读取 output JSON
2. 把 `structure_findings` 中 `severity=blocker` 的直接列入报告 BLOCKER 区
3. **逐项执行 ai_actions**（详见下一步）
4. 填充 `report_skeleton` 生成最终 Markdown 报告

### 第五步：执行 ai_actions（核心规范判断）

每个 ai_action 的处理流程：

```
1. 读取 action.reference_doc 指向的规范章节（已在第二步读完，对照即可）
2. 读取 action.target_file 的内容（如 agents/team-lead.md）
3. 按 action.instruction 的指令逐条对照规范判断
4. 输出结论：✅ 通过 / ❌ 不通过（写入 BLOCKER）/ ⚠️ 部分缺失（写入 SUGGESTION）
5. 把规范出处直接标在报告条目里：「规范依据：CODEBUDDY.md §4.4 / WorkBuddy专家开发规范.md §5.2.1」
```

**ai_actions 类型清单**（详见 `references/ai-action-protocol.md`）：

| action_type | 检查内容 | 处理级别 |
|-------------|---------|--------|
| `team-rule-check` | 主理人 prompt 是否含 TeamCreate 铁律、5 条红线、协作规则 | BLOCKER |
| `member-rule-check` | 成员 prompt 是否含擅长领域、分析框架、输出模板；SendMessage 回传要求作为建议项 | BLOCKER / SUGGESTION |
| `prompt-completeness` | Agent MD frontmatter 是否含 displayName/profession 必填 | SUGGESTION |
| `display-text-quality` | displayDescription 字数、defaultInitPrompt 与 quickPrompts[0] 一致、描述不含与平台实际不符的技术承诺 | SUGGESTION |
| `platform-claim-check` | description/displayDescription/agent prompt 不得包含与平台运行方式不符的技术承诺 | BLOCKER |
| `finance-compliance` | §十八：决策类措辞、免责声明、数据来源披露 | BLOCKER / SUGGESTION |
| `security-hygiene-review` | 凭据硬编码、危险命令、内网域名、个人路径、CDN @latest 等安全与通用性复核 | BLOCKER / SUGGESTION |
| `dependency-guide-check` | bin/scripts/环境变量/外部依赖的安装与配置引导完整性 | BLOCKER / SUGGESTION |
| `deep-quality-review` | 专家包 11 维度语义质量评审 | SUGGESTION |


### 第六步：安全/依赖引导/深度质量评审（参考 skill-reviewer v3.7）

`review.py` 会额外输出三类 ai_action，LLM 必须执行后写入报告：

| action_type | 检查内容 | 输出级别 |
|-------------|---------|---------|
| `security-hygiene-review` | 复核凭据硬编码、危险 shell、内网域名、个人路径、平台路径、CDN @latest 等安全与通用性问题 | 真实凭据硬编码 BLOCKER；其余按影响列 SUGGESTION |
| `dependency-guide-check` | 当存在 `bin/`、`scripts/`、环境变量或外部工具依赖时，检查 README/SKILL/Agent 是否提供安装、版本、配置、验证说明 | 关键依赖完全无引导列 BLOCKER；部分缺失列 SUGGESTION |
| `deep-quality-review` | 阅读核心 agents/README/skills，按 11 维度做语义质量评审 | 永远只列 SUGGESTION，不阻断 |

**深度质量评审 11 维度**：AI 可执行性、路由/触发清晰度、上下文效率、容错降级、角色边界、团队编排、用户体验、受众适配、可移植性、领域准确性、可维护性。

> 批量审查 ≥2 个专家包时，`security-hygiene-review`、`dependency-guide-check`、`deep-quality-review` 可使用 `code-explorer` subagent 并行阅读，主 agent 负责合并结论和写报告。单个专家包审查时由主 agent 执行。

### 第七步：金融类专项检查（启发式触发）

`review.py` 自动识别（`finance_flag=true` 时）：
- `categoryId` 为 `08-FinanceInvestment`
- 或 plugin 名含关键词 `stock|trading|finance|fund|invest|equity|portfolio`

触发后追加 `finance-compliance` 类型 ai_action，LLM 读 CODEBUDDY.md §十八 逐项核对：
- defaultInitPrompt 不含「能不能买/该买吗/推荐」等决策类措辞
- displayDescription、description 不暗示投资建议
- 输出末尾是否有 AI 生成 + 公开信息 + 不构成投资建议 + 不构成个股推荐 四要素声明
- 数据来源是否标注

### 第八步：生成审查报告

报告路径：`<expert_dir>/审查报告-<plugin-name>.md` 或用户指定路径。


**报告结构**：

```markdown
# 专家包审查报告 - <plugin-name>

## 一、总体结论
**整体结论：<可上架 | 需修复后方可上架>**

- 阻断问题（BLOCKER）：N 个
- 建议改进项（SUGGESTION）：M 个

## 二、阻断问题（BLOCKER）— 必修

### B01 ❌ <一句话标题>
- **现状**：<引用文件原文>
- **规范依据**：CODEBUDDY.md §x.y / WorkBuddy专家开发规范.md §a.b
- **修复方案**：<具体可执行的修复步骤>

## 三、建议改进项（SUGGESTION）
（同上格式）

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

## 五、修复优先级表
| 优先级 | 编号 | 问题 | 工作量 |

## 六、亮点
（可选，体现专家包的优势）
```

### 第九步：交互式修复循环


- 对可机械修复的项（如 frontmatter 字段顺序、displayDescription 字数）：AI 自决直接修改缓存目录，重跑 review.py 验证
- 对涉及业务内容的项（如主理人补铁律、成员补 SendMessage）：在报告中给出具体修复建议，等用户决定是否由 AI 代修或作者自行修复
- 修复完成后重新运行 review.py，循环直至无 BLOCKER

---

## ai_action 执行协议

**核心原则**：默认 AI 自决，仅在「会改业务内容 + 不可逆 + 选项不唯一」时弹窗。

### 一律 AI 自决（不弹窗）

- 形状层修复：字段顺序、编码归一、frontmatter 占位补全
- 翻译/字数精简：displayDescription 超字数、description 翻译
- 明显的规范违反：成员 SendMessage 缺失（修复方式唯一）

### 必须弹窗（关键岔路）

1. **修改主理人/成员业务 prompt 内容**：模板 1，给具体提案让用户确认
2. **金融合规违反需改外露文案**：模板 1
3. **修复方式跨多个合理选项**：模板 2，多选

### 弹窗模板（统一格式）

```json
{
  "title": "<plugin_name> - <决策点一句话>",
  "questions": [{
    "id": "<field>_<plugin_name>",
    "question": "AI 建议: <提案>\n规范依据: <章节>\n请选择:",
    "options": ["采纳并修复", "修改后采纳（请告诉我改什么）", "我手动处理", "跳过此项（报告标注）"],
    "multiSelect": false
  }]
}
```

---

## 输出位置约定

- normalize.py / review.py 的 JSON 输出：`<expert_dir>/.review-cache/<plugin-name>-<step>.json`
- 最终审查报告：`<expert_dir>/审查报告-<plugin-name>.md`
- zip 解压审查工作目录：`<zip同级目录>/.review-work/<plugin-name>-review/`（**重新审查新版时必须先删除旧目录再解压**，见第零步）

---

## 参考文档

| 文件 | 说明 |
|------|------|
| `references/review-checklist.md` | 检查项速查表（按 CODEBUDDY.md §十七 组织）+ Markdown 报告模板 |
| `references/ai-action-protocol.md` | ai_actions 类型定义 + 弹窗触发条件 |

---

## 自动化脚本

| 脚本 | 路径 | 说明 |
|------|------|------|
| review.py | `scripts/review.py` | 形状层确定性检查 + ai_actions 输出 + 金融类启发式识别 |
| normalize.py | `scripts/normalize.py` | 编码/换行/字段顺序归一 |
| review_utils.py | `scripts/review_utils.py` | 通用工具函数 |

> **脚本路径约定**：`scripts/` 相对于本 skill 包根目录。调用时使用 `python <skill_base_dir>/scripts/xxx.py`。

### 脚本 vs LLM 职责分工

| 操作 | 脚本（确定性） | LLM（规范/语义） |
|------|---------------|--------------------|
| 编码/BOM/CRLF 归一 | ✅ normalize.py | — |
| 字段顺序排序 | ✅ normalize.py | — |
| 目录骨架检查 | ✅ review.py | — |
| JSON 可解析性 | ✅ review.py | — |
| 字段相等关系（agentName=name=文件名） | ✅ review.py | — |
| 头像尺寸/大小（Pillow） | ✅ review.py | — |
| 版本号格式 | ✅ review.py | — |

| 金融类启发式识别 | ✅ review.py | — |
| 主理人 TeamCreate 铁律完整性 | — | ✅ team-rule-check |
| 成员 SendMessage 回传要求 | — | ✅ member-rule-check |
| 金融合规文案 | — | ✅ finance-compliance |
| 安全启发式扫描 | ✅ 凭据/内网域名/路径/CDN/危险命令预提取 | ✅ security-hygiene-review 语义复核 |
| 依赖引导上下文 | ✅ bin/scripts/环境变量/安装命令预提取 | ✅ dependency-guide-check 完整性判断 |
| 深度质量评审上下文 | ✅ 文件统计/Markdown 结构/Agent 概览预提取 | ✅ deep-quality-review 11 维度评审 |
| 规范出处标注 | — | ✅ 报告生成时标注 §n.m |
| 报告生成与渲染 | ✅ 输出骨架 | ✅ 填充内容 |

