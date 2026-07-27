# 简历附件解析 prompt（Stage B 新人路径 + 活水简历上传，共用）

> 两个入口共用本 prompt，把简历解析成 `experiences.before_tencent`：
> 1. **Stage B · 新人路径**：员工尚无任何自评（入职 < 半年）时引导上传。
> 2. **活水简历上传**：活水推荐前（liveflow §1.3），用户选择"上传一份简历"时——**不论是否已有自评**，把简历里的前雇主 / 项目经历补进画像，下次不用再传。
>
> 两个入口的解析逻辑、字段映射、隐私处理完全一致，唯一区别是引导话术的上下文（新人 vs 活水）。

---

## 引导话术（先发给用户）

```
看起来你还没有正式的自评数据（入职可能还不到半年）。
我可以从两个方式之一了解你的过去经历：

A. 你把本人简历直接拖进对话（PDF / Word / Markdown 都行）
   → 我会自动从中提炼"教育 / 工作 / 项目"经历，纳入画像
   → 简历原件不会留在云端，只在本地解析

B. 不方便上传也可以
   → 我会用 2-3 个简短问题对话采集

要走 A 还是 B？
```

---

## Prompt 主体

变量：`{resume_text}` — Read 工具读出的简历纯文本

```
你拿到的是一名腾讯新员工的本人简历，请提炼成结构化「入司前经历」。

【简历原文】
{resume_text}

【输出要求】

输出严格 JSON：

{
  "from_source": "resume_upload",
  "educations": [
    { "school": "...", "major": "...", "degree": "学士|硕士|博士|MBA",
      "start": "YYYY-MM", "end": "YYYY-MM", "gpa": "..." }
  ],
  "work_experiences": [
    { "company": "...", "position": "...", "start": "YYYY-MM", "end": "YYYY-MM | 至今",
      "summary": "<一段话原文摘要>", "key_outcomes": ["..."] }
  ],
  "intern_experiences": [...],
  "project_experiences": [
    { "name": "...", "role": "...", "start": "YYYY-MM", "end": "YYYY-MM",
      "summary": "...", "tech_stack": ["..."] }
  ],
  "self_intro_keywords": ["..."]   // 简历自我介绍 / 概述里的关键词
}

【提炼规则】

1. **不要编造**：简历里没写的字段留 null 或空数组，不要补全
2. **不要美化**：summary 直接保留原文措辞
3. **时间格式**：YYYY-MM；如果只有年份补 "01"
4. **顺序**：按时间倒序排列
5. **去除隐私**：身份证号 / 电话 / 邮箱 / 家庭住址不要写入 JSON
6. **学位简化**：本科 → 学士，硕士研究生 → 硕士
7. **技术栈识别**：从项目描述里抽具体语言/框架，不抽行业名词

【特别约束】

- 输出严格 JSON，不带 markdown 包裹
- 简历中的私人评价（性格描述、爱好等）一律不入 JSON
- 涉及具体业绩数字的项目原文照抄到 summary（保留可信度）
```

---

## 集成到主流程

### 入口一 · Stage B（新人路径）

在 SKILL.md Stage B 步骤中调用：

```
B1. 用户选择上传简历
B2. CodeBuddy 用 Read 工具读取附件 → resume_text
B3. 用本 prompt 调 LLM → 拿到 before_tencent JSON
B4. 写入 raw/resume.txt（原文）+ 写入 profile.experiences.before_tencent
B5. 提示用户："简历原文已在本地，不会上云。从中提炼到的经历是这些，对吗？"
B6. 用户确认 → 进 Stage C 反问（动机 + 卡点）补全画像
```

### 入口二 · 活水简历上传（liveflow §1.3 触发）

当用户在活水推荐前选择"上传简历"时，被路由到此解析（**不新起一套逻辑，复用 B2-B5**）：

```
R1. 用户把简历拖进对话
R2. Read 附件 → resume_text
R3. 用本 prompt 调 LLM → before_tencent JSON（from_source="resume_upload"）
R4. 合并写入已有 profile.experiences.before_tencent（work_experiences / project_experiences）；
    profile.data_path 若原为 self_assess，则标记为已叠加 resume_upload（不覆盖自评主干）；
    简历原文写 raw/resume.txt（P0 仅本地）。
R5. 一句话确认："简历里的前雇主和项目经历我已经存进你的画像了，下次不用再传。这就给你推岗位。"
R6. 回流 liveflow，进 Step 1（此时画像已含简历经历）。
```

> **关键区别**：活水入口下用户**通常已有自评**，简历经历是**补充**（叠加到 before_tencent），不覆盖自评驱动的司内经历主干。新人入口下则是画像的主要经历来源。
