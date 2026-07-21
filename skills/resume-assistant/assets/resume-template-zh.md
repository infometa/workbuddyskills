# 中文简历模板（Markdown · A4 标准排版）

> 本模板用于 Step 7「输出组装」生成 `resume-zh.md`。
> 占位符以 `{{VAR}}` 形式注入；可选字段用 `{{?VAR}}` 标记——若 inputs 为空则整行删除。
> **联系信息字段（PHONE/EMAIL/CITY）均为 `{{?VAR}}`**：用户未提供时，渲染为占位文本（`[电话待填写]` / `[邮箱待填写]` / `[城市]`），**绝不编造假数据**。AI 生成时，缺失字段统一用 `[字段名待填写]` 格式；Step 8 必须高亮列出所有此类占位符。
> 简历风格：简洁商务风（蓝色主色调 `#1E6FD9`，渲染 HTML 时套用），字号建议 10-11pt 正文 / 13-14pt 标题。
>
> 中文简历规范参考：超级简历 WonderCV + 51Job + 拉勾 · 国内主流三段式（基础信息 / 教育背景 / 工作与项目经历 / 技能）。

---

# {{NAME_ZH}}

**{{?AGE}} 岁｜{{?GENDER_ZH}}｜{{?CITY}}｜{{?PHONE}}｜{{?EMAIL}}**
{{?GITHUB_LINE}}{{?LINKEDIN_LINE}}{{?PERSONAL_SITE_LINE}}

{{?SUMMARY_SECTION}}

---

## 教育背景

{{#each EDUCATION}}
**{{SCHOOL}}** · {{DEGREE_ZH}} · {{MAJOR}}  `{{START_DATE}} – {{END_DATE}}`

{{?GPA_LINE}}{{?RANK_LINE}}{{?CORE_COURSES_LINE}}{{?HONORS_LINE}}

{{/each}}

---

{{#if WORK_EXPERIENCE_EXISTS}}
## 工作经历

{{#each WORK_EXPERIENCE}}
**{{COMPANY}} · {{TITLE}}** {{?DEPARTMENT_INLINE}} · {{CITY}} `{{START_DATE}} – {{END_DATE}}`

{{#each BULLETS}}
- {{TEXT}}
{{/each}}

{{?TECH_STACK_LINE}}

{{/each}}
{{/if}}

---

## 项目经历

{{#each PROJECTS}}
**{{NAME}}** · {{ROLE}} `{{START_DATE}} – {{END_DATE}}` {{?LINKS_INLINE}}

{{?SCALE_LINE}}

{{#each BULLETS}}
- {{TEXT}}
{{/each}}

**技术栈**：{{TECH_STACK_CSV}}

{{/each}}

---

## 专业技能

{{#if SKILLS.programming_languages}}
- **编程语言**：{{SKILLS.programming_languages_csv}}
{{/if}}
{{#if SKILLS.frameworks}}
- **框架 / 工具**：{{SKILLS.frameworks_csv}}
{{/if}}
{{#if SKILLS.databases}}
- **数据库**：{{SKILLS.databases_csv}}
{{/if}}
{{#if SKILLS.cloud}}
- **云 / 基础设施**：{{SKILLS.cloud_csv}}
{{/if}}
{{#if SKILLS.languages}}
- **语言**：{{SKILLS.languages_formatted}}
{{/if}}
{{#if SKILLS.certifications}}
- **证书**：{{SKILLS.certifications_csv}}
{{/if}}

---

{{#if AWARDS}}
## 荣誉与获奖

{{#each AWARDS}}
- {{ITEM}}
{{/each}}
{{/if}}

{{#if PUBLICATIONS}}
## 论文 / 专利

{{#each PUBLICATIONS}}
- {{ITEM}}
{{/each}}
{{/if}}

---

## 求职意向

**目标岗位**：{{TARGET_JOB_TITLE}}
{{?TARGET_CITY_LINE}}
{{?EXPECTED_SALARY_LINE}}

---

<!--
【中文简历格式规范（Skill 内部对齐用，渲染时删除）】

1. 字段顺序（国内主流，按重要度递减）：
   基础信息 → 教育背景 → 工作经历（社招）/ 项目经历（应届）→ 专业技能 → 荣誉 → 求职意向

2. 可出现的个人信息（按用户偏好选）：
   姓名、年龄、性别、城市、电话、邮箱、GitHub、LinkedIn、个人网站、微信（慎）
   政治面貌、户籍、民族 —— 默认不出现，除非用户明确要求
   照片 —— 默认不出现，include_photo=true 才放右上角

3. 日期格式：YYYY.MM 或 YYYY-MM，不混用。"至今" 用 "present"。

4. 经历 bullet 长度：每条 ≤ 40 个汉字 / ≤ 70 个英文字符。

5. 量化：每条 bullet 至少含 1 个数字；无量化则用占位符（provenance-rules §1.3）。

6. 一页 vs 两页：
   - 毕业 ≤ 3 年：强制 1 页
   - 毕业 > 3 年：建议 2 页，超过 2 页必须压缩
-->
