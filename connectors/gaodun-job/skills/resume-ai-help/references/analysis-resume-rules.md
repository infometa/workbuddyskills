# 简历解析规则（analysisResume 1:1）

> **来源**：服务端简历解析逻辑（文本解析、起止时间解析、字段取值、技能清洗、教育经历清洗、模块集合装配）。
>
> 本文件定义"用户简历原文 → `XjPersonalResumeModule` + `XjPersonalResumeData` 记录集"的转换规则。诊断（diagnoseReport）与评分（doComputeScore）的输入 `getShowFields` 直接依赖这里产出的 `moduleStatus` / `dataFieldStatus`，必须严格对齐。
>
> ⚠️ **本文档的全部确定性规则已由 `scripts/resume_parse.py`（finalize 子命令）代码实现并强制执行**——本文件是脚本行为的规则说明与排查依据，不要求模型手工执行。模型在 Phase 1 的唯一职责是按模板逐字段填值（见 §10）。

## 1. 总体流程

```
analysisResume(resumeType, content):
  1. resumeDTO = analyzeResumeService.process(content)   # LLM 解析为 ResumeDTOV2（模块→记录数组）
  2. setAvatarUrl(resumeDTO)                             # idPhoto = 头像URL
  3. clearProfessionalSkills(resumeDTO)                  # professionalSkills 多条合并为 1 条
  4. clearProfessionalSkills4SinglePage(resumeDTO)       # professionalSkillsNonOnline 多条合并为 1 条
  5. cleanEducationExperience(resumeDTO)                 # 教育经历前缀清洗
  6. 遍历 moduleConfig[resumeTypeCode]（JSON 数组顺序）逐模块落库：
     - 模块无解析内容 → 走"空模块分支"（见 §3）
     - 模块有解析内容 → 走"有内容分支"（见 §4）
  7. 模块排序：showModuleList 在前 + hiddenModuleList 在后，sort 重新编号 1..N
```

## 2. 数据清洗规则（落库前）

| 清洗 | 规则 |
|---|---|
| `clearProfessionalSkills`（professionalSkills，网申版） | 多条记录合并为 **1 条**：`languageClassify` / `certificateName` / `softwareName` 用 `、` 拼接并去掉 `\n`；`languageDesc` / `certificateDesc` / `softwareDesc` 用 `\n` 拼接 |
| `clearProfessionalSkills4SinglePage`（professionalSkillsNonOnline） | 多条合并为 **1 条**：`languageSkill` / `softwareOperation` 用 `、` 拼接去 `\n`；`qualificationCertificate` 用 `\n` 拼接 |
| `cleanEducationExperience` | `educationExperienceDesc` 和 `classRank` 用正则 `专业课程:|专业课程：|成绩排名:|成绩排名：|专业课程|成绩排名` 做 `replaceFirst` 去前缀 |
| `setAvatarUrl` | `baseInformation.idPhoto` = 上传头像 URL |

> 影响：专业技能两个模块永远只有 **1 条** dataId 记录；`classRank` 入库值已被去前缀。

### 2.1 枚举值归一化（解析侧必须执行）

Java 侧 `analyzeResumeService` 的 LLM parser 会把学历等枚举字段输出为**标准选项值**，落库的 `qualification` 是「大学本科」这类枚举原文，而不是简历里写的「本科」。skill 解析自由文本时必须做同样的归一化，否则评分精确匹配必然落空（"本科" ≠ "大学本科" → 学习能力恒 0）：

| 简历原文（自由文本） | 入库标准值 |
|---|---|
| 本科 / 大学本科 / 学士 | `大学本科` |
| 硕士 / 研究生 / 硕士研究生 | `硕士研究生` |
| 博士 / 博士研究生 | `博士研究生` |
| MBA / 工商管理硕士 | `MBA` |
| 大专 / 专科 / 大学专科 | `大学专科` |
| 高中 / 中专 | `高中` |
| 初中 | `初中` |
| 小学 | `小学` |

> 同理，其他有固定选项的字段（证件类型、政治面貌、婚姻状况、健康状况、最高学历培养方式等）解析时也应输出规范选项值；这些字段不参与评分，但影响 NO_FILL 判定的"有值/空白"结论。

### 2.2 idPhoto（证件照）特殊规则

真实系统中 `idPhoto` 不来自简历文本，而是 `setAvatarUrl` 塞入的**用户头像 URL**——只要用户在 App 里传过头像，`idPhoto` 就有值，不会进 NO_FILL。skill 落地规则：

1. 上传的简历附件（PDF/DOC/DOCX）中**含有照片/头像** → `idPhoto` 记非空占位值（如 `<已上传证件照>`）；
2. 纯文本粘贴、无法判断是否含照片 → **记为空**（会正常进入 NO_FILL，与真实系统"未传头像"行为一致）；
3. 用户明确说明"已上传头像" → 记非空。

## 3. 空模块分支（该模块解析内容为空）

对该模块 `dataFieldList` 每个字段，生成 **1 条**空值记录（所有字段共享同一个新 dataId，sort=1）：

1. **平台过滤**：来源平台 ≠ `APPLET_PONYCAREER`（小马生涯）时，`showOnPage != true` 的字段**直接跳过，不生成记录**；小马生涯平台保留所有字段。
2. **字段状态**：`dataFieldStatus = SHOW(1)` 当且仅当 `canHidden == false`；`canHidden == true` → `HIDDEN(0)`。
3. **模块状态**：`hidden == true` 或 `所有字段 canHidden == true` → HIDDEN；否则 → SHOW。

> ⚠️ **最常踩的坑（必须执行）**：只要模块配置 `hidden == false` 且非全字段 canHidden，**即使简历里完全没有该模块的内容，也必须生成空白记录**。这些空白 SHOW 记录会进入完整度分母并被记 NO_FILL。
>
> 案例（havingInternshipExperience 的 `workExperience`，hidden=false、6 个字段全部 canHidden=false）：应届生简历通常没有工作经历，但真实接口照样输出 6 条 NO_FILL（【开始时间】【结束时间】【公司名称】【部门名称】【岗位名称】【工作职责】）。**禁止"没内容就跳过该模块"的做法。**

## 4. 有内容分支（模块解析出 1..N 条记录）

对每条解析记录（每条生成新 `dataId`，`dataSort` 从 **1** 开始递增）：

1. 先算 `时间解析结果 = 起止时间解析(记录)`（见 §5）。
2. 对 `dataFieldList` **每个字段**（**不过滤 showOnPage**）生成记录：
   - `fieldValue = 字段取值规则(dataFieldCode, 记录, 时间解析结果)`（见 §6）；
   - **`dataFieldStatus = SHOW` 当且仅当 `值非空 || canHidden == false`**（canHidden=true 且值为空 → HIDDEN）。
3. **模块状态**（`visibleModuleMap` 见 §7）：
   - 模块不在 `visibleModuleMap[resumeType]` → **HIDDEN**（C 端不展示的模块，解析出内容也隐藏）；
   - 否则若 `任一字段有值 || (!hidden && 不是所有字段 canHidden)` → **SHOW**；
   - 否则 → HIDDEN。

> ⚠️ **`hidden==true` 的配置不等于永远隐藏**：只要解析出内容（任一字段有值）且在 `visibleModuleMap` 内，模块就是 SHOW，全部字段记录照常生成、照常进诊断/评分。
>
> 案例（havingInternshipExperience）：`campusActivities` 与 `rewardRecords` 配置 `hidden=true`，但简历解析出校内活动/获奖记录时，真实接口会输出它们的 NO_FILL（如【开始时间】【活动名称】【角色】【奖励级别】）和 DESCRIPTION_SUGGEST。**禁止按"hidden=true 就跳过解析"处理。**

## 5. 起止时间解析（getStartEndTime）

每段记录的原始 JSON 中，找 **key 包含 `StartEndTime`** 的第一个键值对（如 `internshipStartEndTime`），值按 `-`（DATE_SEPARATE_TAG）切分：

| 情况 | startTime | endTime |
|---|---|---|
| 无 StartEndTime key 或值为空 | `""` | `""` |
| `start-end` 两段 | `start` 归一化为 `yyyy-MM` | 见下 |
| 只有一段 | 归一化为 `yyyy-MM` | `""` |

endTime 细分：

- `至今` → **当前时间**（`yyyy-MM`，按解析当时的系统时间）；
- 长度 ≤ 2（如 `6`）→ 拼接 startTime 的年份：`start年-6` 再归一化；
- 其他 → 直接归一化为 `yyyy-MM`。

## 6. 字段值提取（getFieldValue）

| dataFieldCode 特征 | 取值 |
|---|---|
| 包含 `StartTime` | `时间解析结果.startTime` |
| 包含 `EndTime` | `时间解析结果.endTime` |
| 包含 `birthDate` | 日期穷举格式归一化 |
| 包含 `Time`（其他时间字段） | 日期穷举格式归一化 |
| 其余 | 原始值 `toString()`；空 → `""` |

> `handleClassRank`（成绩排名选项校验）在代码中**无调用方，是死代码**——`classRank` 原样入库（仅经 §2 前缀清洗）。与"学习能力评分不取 classRank"一致。

## 7. visibleModuleMap（C 端可见模块集）

配置于 `references/resume-module-config.json` 顶层 `visibleModuleMap`（与 `moduleConfig` 并列）：

| resumeType | 可见模块数 | 不可见（解析出内容也会 HIDDEN） |
|---|---|---|
| `noInternshipExperience` | 16 | `familyMember` / `language` / `certificate` / `softwareOperate` / `paper` / `creation` |
| `havingInternshipExperience` | 16 | 同上 6 个 |
| `havingWorkExperience` | 16 | 同上 6 个 |
| `onlineApplication` | 22 | `paper` / `creation` |

> 这就是非网申简历里"语言/证书/软件操作"三个子模块不参与诊断/评分的原因——它们的字段记录因模块 HIDDEN 而被 `getShowFields` 过滤，专业能力三项命中在非网申类型下实际只可能来自 `professionalSkillsNonOnline` 的 `languageSkill` / `qualificationCertificate` / `softwareOperation`。

## 8. 模块 sort（报告顺序依据）

- `analysisResume`：showModuleList（按 `moduleConfig` JSON **数组顺序**）在前，hiddenModuleList（同序）在后，统一重新编号 sort=1..N。**不使用配置中的 `sort` 字段**。
- （对比：`defaultCreateResume` 默认简历路径用的是配置 `sort` 字段排序。两条路径不同；诊断报告跟随解析路径。）
- `fillReportDetail` 按 DB sort 升序遍历模块 → 报告里**显示模块按配置数组序排前，隐藏模块排后**（隐藏模块若有诊断明细也会输出，见 diagnosis-categories.md 的 NO_DATA 空流 quirk）。

## 9. 对本 skill Phase 1 的落地要求

解析用户简历时，产出记录必须带齐：

| 字段 | 规则 |
|---|---|
| `moduleCode` / `dataFieldCode` | 按 `resume-module-config.json` |
| `dataFieldValue` | 经 §2 清洗、§2.1 枚举归一化、§5/§6 时间归一化（`yyyy-MM`） |
| `dataId` | 同一段经历的字段共享（职场能力月数按 dataId 配对） |
| `sort`（dataSort） | 段内从 1 递增（DESCRIPTION_SUGGEST 编号依据） |
| `dataFieldStatus` | `值非空 || canHidden==false` → SHOW，否则 HIDDEN |
| `moduleStatus` | 按 §4.3 / §3.3 判定 |

## 10. 解析自检清单（模型填值时必须逐项核对）

> 第 2、3 条（空模块分支、hidden 模块可见性）**已由脚本保证**，无需手工处理；模型在填 filled.json 时重点保证第 1、4、5、6 条——即"值不丢、条数不少"。

1. **逐字段填值（强制）**：模板已列出**每个模块 × dataFieldList 每个字段**（含 showOnPage=false 字段），逐格给值，空就留 `""`；禁止跳过字段、禁止删字段。`address`（现居住地）等字段空白时由脚本正确记 NO_FILL。
2. ~~空模块也生成记录~~ → 脚本 finalize 自动完成。
3. ~~hidden=true 但有内容的模块照常 SHOW~~ → 脚本 finalize 自动完成；**但前提是模型把内容填进了模板**——原文有校内活动/获奖内容时，必须填进 `campusActivities`/`rewardRecords` 的记录，留空脚本只能当无内容处理。
4. **高频漏解析字段**（逐一对照原文确认有/无值）：
   - 基本信息：`workCity`（期望城市）、`position`（应聘岗位）、`address`（现居住地）、`idPhoto`（证件照，见 §2.2）；
   - 实习/工作经历：`xxxPostName`（岗位名称）、`xxxDepartmentName`（部门名称）——原文出现即填，宁多勿空；
   - 实践经历：`practicalStartTime` / `practicalEndTime` / `practicalExperienceDesc`（实践职责正文，常因排版被漏掉）；
   - `hobbySpecialityDesc`（爱好特长正文，"书法、音乐、Python"这类短文本也是有值）；
   - 奖励记录：`rewardLevel`（奖励级别，国家级/省级/校级，原文通常没有 → 保持空白让它正确记 NO_FILL，不要编造）。
5. **qualification 归一化**：最高学历必须映射到 §2.1 的标准枚举（"本科"→"大学本科"），否则学习能力评分恒 0。
6. **每条经历记录完整**：N 段经历 = N 个 dataId，每段 6 个字段记录齐全（时间字段经 §5 拆分归一化），缺值字段保持空白由 NO_FILL 捕获，**不允许整段丢弃**。

## 附录 A：真实回归案例（2026-08-15，havingInternshipExperience）

同一份简历，真实接口 vs 修复前 skill 的差异及根因，作为回归基准：

| 现象 | 真实接口 | 修复前 skill | 根因 |
|---|---|---|---|
| 总分 | 71（beatPercent 80%） | 61（70%） | qualification "本科"未归一化为"大学本科" → 学习能力 0 vs 10 |
| `workExperience` | 6 条 NO_FILL | 模块缺失 | 空模块分支未生成空白记录 |
| `campusActivities` | 4 NO_FILL + 8 描述建议 | 模块缺失 | 误用"hidden=true 即隐藏"，且漏解析 8 条校内活动记录 |
| `rewardRecords` | 【奖励级别】NO_FILL | 模块缺失/漏字段 | 同上；rewardLevel 原文无值应保持空白 |
| `practicalExperience` | 3 NO_FILL + 4 描述建议 | 2 NO_FILL（无建议） | 漏解析 practicalStartTime 空白与 4 条实践职责正文 |
| `hobbySpeciality` | 1 条描述建议 | 误报 NO_FILL | 漏解析爱好特长正文 |
| `internshipExperience` | 1 NO_FILL（部门名称）+ 1 描述建议 | 2 NO_FILL（误报岗位名称、漏建议） | 漏解析岗位名称原文值 |
| `baseInformation` | 16 条 NO_FILL | 18 条（多 证件照/期望城市/应聘岗位，少 现居住地） | 误过滤 showOnPage=false 的 address；漏提取 workCity/position 原文值；idPhoto 未按 §2.2 处理 |
