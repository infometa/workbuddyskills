# Input Schema（输入契约）

> 定义 resume-assistant Skill 的完整输入结构。
> 当作为子 Skill 被 `job-coach` 等 Agent 调用时，父 Skill 应按此 schema 组装输入。
> 人类用户直接使用时，Skill 内部会引导式提问补全缺失字段。

## 顶层对象

```typescript
interface ResumeAssistantInput {
  mode: "generate" | "tailor" | "rewrite" | "diff" | "score" | "refine" | "export";
  experiences: ExperienceInput;
  target_job?: TargetJob;          // tailor / score 必填
  preferences?: Preferences;
  version_control?: VersionControl;
  meta?: Meta;
}
```

---

## 1. mode（必填）

| 值 | 含义 | JD 是否必填 | 典型场景 |
|---|---|:---:|---|
| `generate` | 从零生成简历 | ❌ | 用户无现有简历，给出经历即可 |
| `tailor` | 针对具体 JD 定制 | ✅ | 用户有经历/简历，想投某个岗位 |
| `rewrite` | 改写润色现有简历（无 JD）| ❌ | 用户有简历，想改得更专业 |
| `diff` | 对比两个版本，生成 diff 报告 | ❌ | 已有多个 version_label，输出对比 |
| `score` | 对 JD 打覆盖率/差距分 | ✅ | 用户只想看匹配度，不改简历 |
| `refine` | 基于用户反馈多轮细修 | 继承 | 上一步完成后接着说"第 N 条改一下" |
| `export` | 导出 PDF / JSON Resume | ❌ | 要导出文件 |

---

## 2. experiences（必填，至少一种输入形式）

```typescript
interface ExperienceInput {
  input_format: "structured" | "freeform_text" | "legacy_resume_file";
  basic_info: BasicInfo;           // 必填
  education: Education[];          // 至少 1 条
  work_experience?: WorkExperience[];
  projects?: Project[];
  skills?: Skills;
  publications?: Publication[];
  awards?: Award[];
  raw_text?: string;               // input_format = freeform_text 时
  legacy_resume_text?: string;     // input_format = legacy_resume_file 时
}
```

### 2.1 BasicInfo

```typescript
interface BasicInfo {
  name_zh?: string;
  name_en?: string;
  email?: string;                   // 用户必须最终填写；AI 绝不编造假邮箱——用户未提供时用占位符 [邮箱待填写]
  phone?: string;                   // 用户未提供时用占位符 [电话待填写]，绝不编造假号码
  city?: string;                    // 用户未提供时用占位符 [城市]
  wechat?: string;                  // 可选；未提供时省略，不占位
  github?: string;
  linkedin?: string;
  personal_site?: string;
  // 以下仅中文简历使用，英文简历自动忽略
  gender?: "male" | "female" | "other";
  age?: number;
  political_status?: string;        // 政治面貌（可选）
  hukou?: string;                   // 户籍（可选）
  // 英文简历绝不输出以上 4 项
}
```

### 2.2 Education

```typescript
interface Education {
  school: string;                   // 必填
  degree: "bachelor" | "master" | "phd" | "associate" | "other";
  major: string;
  start_date: string;               // "2020-09"
  end_date: string;                 // "2024-06" or "present"
  gpa?: string;                     // "3.8/4.0"
  rank?: string;                    // "前 5%"
  core_courses?: string[];
  honors?: string[];
}
```

### 2.3 WorkExperience

```typescript
interface WorkExperience {
  company: string;
  title: string;                    // 实际职称（不允许改）
  department?: string;
  city?: string;
  start_date: string;
  end_date: string;                 // or "present"
  description?: string;             // 原始描述（口语 OK）
  achievements?: string[];          // bullet 列表
  tech_stack?: string[];            // 技术栈
}
```

### 2.4 Project

```typescript
interface Project {
  name: string;
  role: string;                     // 用户自述的角色（不允许 AI 升级）
  start_date: string;
  end_date: string;
  description: string;
  achievements?: string[];
  tech_stack?: string[];
  links?: { github?: string; demo?: string; paper?: string };
  scale?: string;                   // "DAU 10万" / "GMV 500 万"（如果用户提供）
}
```

### 2.5 Skills

```typescript
interface Skills {
  programming_languages?: string[];
  frameworks?: string[];
  tools?: string[];
  databases?: string[];
  cloud?: string[];
  languages?: { name: string; level: string }[]; // 外语
  certifications?: string[];
}
```

---

## 3. target_job（tailor / polish 必填）

```typescript
interface TargetJob {
  jd_content: string;               // JD 原文（纯文本；v1.0 不支持 URL/图片）
  job_title?: string;               // 可选：用户明示的岗位名（辅助 role_family 推断）
  company?: string;                 // 可选：公司名
  seniority?: "intern" | "junior" | "mid" | "senior" | "staff" | "principal";
  salary_expectation?: string;      // "25K-35K" (仅中文简历可输出)
  location_preference?: string;
}
```

---

## 4. preferences（可选）

```typescript
interface Preferences {
  template?: "star" | "project_oriented" | "skill_oriented" | "hybrid";
  // 默认：tech × generate → project_oriented
  //      tech × tailor   → hybrid
  //      biz  × *        → star
  //      design × *      → project_oriented
  length?: "1page" | "2page" | "auto";
  // 默认：en → 1page；zh → auto（经历 ≤3 年 = 1page，> 3年 = 2page）
  language?: "zh" | "en" | "both";
  // 默认：zh
  tone?: "conservative" | "standard" | "bold";
  // conservative：语气最保守（默认给应届生）
  // standard：标准职场语气
  // bold：较大胆的主动语气（需用户经历充分）
  include_photo?: boolean;          // 仅中文简历；默认 false
  include_expected_salary?: boolean; // 仅中文简历；默认 false
  font_preference?: "serif" | "sans-serif";
  // 默认：zh → sans-serif（思源宋体类）；en → serif（Times / Garamond）
}
```

---

## 5. version_control（可选 · v0.2 升级）

> **v0.2 变更**：吸收 `srbhr/Resume-Matcher` 的 `is_master` + `parent_id` + `processing_status` 三字段，支持"**master-first 派生模式**"。`base_version_id` 字段被保留但标记为 `@deprecated`，新代码用 `parent_id` 替代。详见 [`../../docs/requirements/AI简历助手/需求说明/融合吸收点.md` § B1](../../../../docs/requirements/AI简历助手/需求说明/融合吸收点.md)。

```typescript
interface VersionControl {
  /** 用户可读的版本别名，如 "字节-AI-Engineer-2026Q2"；不填自动生成 */
  version_label?: string;

  /** 🆕 v0.2：是否为主档简历（master）。全局唯一，由系统维护
   *  - 默认：创建第一份简历时自动为 true
   *  - 后续派生版本为 false
   *  - 用户调用 mode=promote 可手动切换 master */
  is_master?: boolean;

  /** 🆕 v0.2：父版本 ID（派生版本指向的 master 或上一个版本）
   *  - master 版本此字段为 null
   *  - 所有 tailored 版本必有 parent_id 指向 _master 或另一个 tailored */
  parent_id?: string | null;

  /** @deprecated v0.2 起使用 parent_id 替代。为兼容 v0.1 的 API 调用临时保留 */
  base_version_id?: string;

  /** 🆕 v0.2：处理状态机（用于 master 自动推进判定）
   *  - "pending": 请求已接收，未开始处理
   *  - "processing": LLM 生成中
   *  - "ready": 生成成功，可用
   *  - "failed": 生成失败
   *  当 master 卡在 processing/failed > 24h，Skill 自动提升下一个 ready 版本为 master */
  processing_status?: "pending" | "processing" | "ready" | "failed";

  /** 是否保留历史版本（默认 true）*/
  keep_history?: boolean;

  /** 用户备注本版本目的 */
  notes?: string;
}
```

### 5.1 运行时规则（v0.2 新增）

| 规则 | 说明 |
|---|---|
| **Master 唯一性** | Skill 读取 `_manifest.json` 时检查：同一时刻只有 1 份 `is_master: true`。发现冲突时主动告警。|
| **Master 自动推进** | 当前 master 若 `processing_status` 为 `failed` / `processing` 超 24h，下次 `mode=generate/rewrite` 自动选择最新的 `ready` 版本提升为 master。 |
| **Master 不可直删** | `mode=delete` 对 `is_master: true` 的版本必须拒绝，除非用户同时传 `--promote-next <version_id>`。 |
| **List 默认过滤** | `mode=list` 默认不显示 master（对普通用户，master 是"底座"不是工作产出），加 `--include-master` 才显示。|
| **Parent 指向校验** | 创建派生版本时，必须验证 `parent_id` 指向的版本存在且状态为 `ready`。|

---

## 6. meta（可选）

```typescript
interface Meta {
  caller?: string;                  // "user" | "job-coach" | "mock-interview" ...
  trace_id?: string;                // 上游 Agent 传的追踪 ID
  locale?: "zh-CN" | "en-US";       // UI 语言
  strict_mode?: boolean;            // true = 更严的 provenance 检查
}
```

---

## 7. 最小可用输入示例

### 7.1 generate 模式（最简）

```json
{
  "mode": "generate",
  "experiences": {
    "input_format": "structured",
    "basic_info": {
      "name_zh": "张三",
      "email": "zhangsan@example.com",
      "phone": "13800138000",
      "city": "北京"
    },
    "education": [{
      "school": "某某大学",
      "degree": "bachelor",
      "major": "计算机科学与技术",
      "start_date": "2020-09",
      "end_date": "2024-06"
    }],
    "projects": [{
      "name": "校园社交 App",
      "role": "全栈开发",
      "start_date": "2023-03",
      "end_date": "2023-09",
      "description": "做了一个校内社交 App，用了 React 和 Spring Boot",
      "tech_stack": ["React", "Spring Boot", "MySQL"]
    }]
  }
}
```

### 7.2 tailor 模式（含 JD）

```json
{
  "mode": "tailor",
  "experiences": { /* 同上 */ },
  "target_job": {
    "job_title": "大模型算法工程师",
    "company": "字节跳动",
    "jd_content": "岗位职责：1、负责大语言模型的训练、微调与推理优化；2、参与 RAG 系统设计与落地；任职要求：1、熟悉 PyTorch / Transformers；2、有 LLM 微调或 Agent 开发经验优先..."
  },
  "preferences": {
    "template": "hybrid",
    "language": "both",
    "tone": "standard"
  },
  "version_control": {
    "version_label": "v1-bytedance-llm"
  }
}
```

---

## 8. 校验规则

| 规则 | 违反处理 |
|---|---|
| `mode` 必填且为枚举值 | 报错拒绝 |
| `basic_info.email` 若提供则格式必须合法（含 @） | 格式非法 → 报错提示用户更正；**未提供 → 用占位符 `[邮箱待填写]`，不报错** |
| `basic_info.phone` 若提供则格式合法（手机号或座机）| 格式非法 → 警告；**未提供 → 用占位符 `[电话待填写]`，不报错** |
| `education` 至少 1 条 | 报错拒绝 |
| `experiences` 经历 + 项目 合计 ≥ 1 条 | 报错，提示补充 |
| `tailor` / `polish` 模式必须有 `target_job.jd_content` | 报错拒绝 |
| `jd_content` 长度 ≥ 50 字符 | 警告，建议补全 |
| 若 `language = en`，basic_info 的 `age/gender/political_status/hukou` 自动忽略 | 警告展示 |
| 若 `strict_mode = true`，所有 `medium` 风险也强制用户审核 | — |
