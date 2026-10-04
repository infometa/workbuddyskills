# 简历模块配置（Schema 参考）

> **来源（1:1）**：服务端简历模块配置原件
> **本 skill 内的权威文件**：`references/resume-module-config.json`（原样复制，禁止手改）。
>
> 本 md 只是**阅读辅助**；凡与本文件不一致，一律以 `resume-module-config.json` 为准。

## 1. 数据结构

`resume-module-config.json` 顶层为 `moduleConfig`，按 4 种 `resumeType` code 各挂一份模块数组：

| Key（resumeType code） | value | 含义 |
|---|---|---|
| `noInternshipExperience` | 0 | 零实习经验 |
| `havingInternshipExperience` | 1 | 应届生求职（实习人群） |
| `onlineApplication` | 2 | 在线申请求职（网申人群） |
| `havingWorkExperience` | 3 | 职场人士求职（工作人群） |

每个模块：

```json
{
  "moduleCode": "baseInformation",
  "moduleName": "基本信息",
  "hidden": false,          // 该 resumeType 下模块是否隐藏 → 对应 Java 模块 moduleStatus
  "sort": 1,                // 报告输出的模块排序依据
  "dataFieldList": [
    {
      "dataFieldCode": "personalName",
      "dataFieldName": "姓名",     // NO_FILL 话术【{dataFieldName}】的来源
      "showOnPage": true,          // 对应 Java 字段 dataFieldStatus（SHOW/HIDDEN）
      "canHidden": false
    }
  ]
}
```

> `dataFieldList` 的**数组顺序**即 NO_FILL 诊断在模块内的排序依据（`indexOf(fieldConfig)`）。

## 2. 诊断/评分使用的"可见字段"（getShowFields 还原）

`moduleStatus` / `dataFieldStatus` 由解析阶段 `analysisResume` 赋值，完整规则见 `references/analysis-resume-rules.md`。要点：

- **字段可见**：`值非空 || canHidden == false` → SHOW（即 canHidden=true 的空白字段不可见，不进完整度分母、不记 NO_FILL）；
- **模块可见**：必须在 `visibleModuleMap[resumeType]` 内（配置顶层 `visibleModuleMap`），且（任一字段有值 或 配置 `hidden==false` 且非全字段 canHidden）；
- **模块 sort**：显示模块在前（按 JSON 数组序）+ 隐藏模块在后，重新编号 1..N，**不用配置的 sort 字段**。

## 3. visibleModuleMap（C 端可见模块集）

| resumeType | 可见模块数 | 不可见模块（解析出内容也 HIDDEN） |
|---|---|---|
| `noInternshipExperience` / `havingInternshipExperience` / `havingWorkExperience` | 16 | `familyMember` / `language` / `certificate` / `softwareOperate` / `paper` / `creation` |
| `onlineApplication` | 22 | `paper` / `creation` |

> 非网申类型下 `language` / `certificate` / `softwareOperate` 三个子模块不可见 → 专业能力评分只可能命中 `professionalSkillsNonOnline` 的 3 个综合字段；网申类型下两套字段都可能命中（`professionalSkills` 模块 + 三个子模块）。

## 4. 评分/诊断引用的关键 moduleCode / fieldCode

源项目常量（`PersonalResumeConstants.java`）：

```
模块：
baseInformation / jobIntention / projectExperience / practicalExperience
competitionExperience / campusActivities / professionalSkills（网申版专业技能）
professionalSkillsNonOnline（非网申版专业技能）/ workExperience / internshipExperience

字段：
position（应聘岗位）/ qualification（学历）/ classRank（成绩排名）
languageClassify / languageDesc / languageSkill（+languageSkillRaw）
certificateName / certificateDesc / qualificationCertificate（+...Raw）
softwareName / softwareDesc / softwareOperation（+...Raw）
internshipStartTime / internshipEndTime（yyyy-MM）
workStartTime / workEndTime（yyyy-MM）
hobbySpecialityDesc / keyword
```

## 5. 中文名 → code 反向映射

解析用户粘贴的自然语言简历时，按 `resume-module-config.json` 中 `moduleName` / `dataFieldName` 反查 code。常见别名：

- "实习/实习经历" → `internshipExperience`；"工作/工作经历" → `workExperience`
- "项目" → `projectExperience`；"实践/社会实践" → `practicalExperience`
- "比赛/竞赛" → `competitionExperience`；"校内活动/学生工作" → `campusActivities`
- "专业技能/技能" → 非网申 `professionalSkillsNonOnline`，网申 `professionalSkills`
- "自我评价" → `selfEvaluation`；"爱好特长" → `hobbySpeciality`
- "培训" → `trainExperience`；"应聘理由" → `applicationReason`；"职业规划" → `careerPlanning`；"适合的工作" → `suitableJob`
