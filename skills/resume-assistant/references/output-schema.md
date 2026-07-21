# Output Schema（输出契约）

> 定义 resume-assistant Skill 的输出结构。
> `result.json` 在 v1.0 起锁定，不做 breaking change（父 Agent 稳定依赖）。
>
> **v0.2 升级**：吸收 `srbhr/Resume-Matcher` 的 master-first 模式，新增 `_master/` 独立目录 + `_manifest.json` 版本清单。所有派生版本都通过 `parent_id` 指向 master。详见 [`融合吸收点.md § B1`](../../../../docs/requirements/AI简历助手/需求说明/融合吸收点.md)。

## 输出目录结构（v0.2 升级）

```
<workspace>/resume-output/
├── _master/                          🆕 主档（全局唯一 is_master=true）
│   ├── resume-zh.md
│   ├── resume-en.md
│   ├── resume-zh.html
│   ├── resume-en.html
│   ├── result.json
│   └── provenance-audit.json
│
├── <version_label_1>/                # 派生版（parent_id = "_master"）
│   ├── resume-zh.md
│   ├── resume-en.md
│   ├── resume-zh.html
│   ├── resume-en.html
│   ├── result.json
│   ├── diff-report.html              # vs master 的 diff（每份派生版必有）
│   ├── jd-match-report.md            # JD 关键词匹配诊断
│   └── provenance-audit.json
│
├── <version_label_2>/
│   └── ...
│
└── _manifest.json                    🆕 版本清单 + 派生树
```

**关键变化**：

| v0.1（扁平） | v0.2（master-first） |
|---|---|
| `./resume-output/<version>/` 所有版本平级 | `_master/` 独立目录 + 派生版指向它 |
| 无 `_manifest.json` | `_manifest.json` 维护版本树 + 状态 |
| diff 仅当有 `base_version_id` 才生成 | 所有派生版**必**有 `diff-report.html`（vs master）|
| `version_control` 只有 `base_version_id` | `is_master` + `parent_id` + `processing_status` |

不同 mode 产出文件差异（v0.2 更新）：

| mode | resume-*.md/html | result.json | diff-report | jd-match-report | provenance-audit | 写入位置 |
|---|:---:|:---:|:---:|:---:|:---:|---|
| `generate`（首次） | ✅ | ✅ | ❌ | ❌ | ✅ | `_master/` |
| `generate`（已有 master） | ✅ | ✅ | ❌ | ❌ | ✅ | 拒绝 —— 改用 `rewrite` |
| `tailor` | ✅ | ✅ | ✅ vs master | ✅ | ✅ | `<version_label>/` |
| `rewrite` | ✅ | ✅ | ✅ | ⚠️ 有 JD 才生成 | ✅ | `_master/` 或指定 version |
| `refine` | ✅ | ✅ | ✅ vs 前一轮 | ⚠️ | ✅ | 同 parent 的 version |
| `compare` | ❌ | ✅ | ✅ | ⚠️ 每版本一份 | ❌ | 独立 report |
| `diff` | ❌ | ✅ | ✅ | ❌ | ❌ | 独立 report |

同时**每次写入都强制更新** `_manifest.json`。

---

## _manifest.json（🆕 v0.2 新增）

全局版本清单与派生关系索引。结构如下：

```json
{
  "schema_version": "0.2",
  "skill_name": "resume-assistant",
  "master_version_id": "_master",
  "last_updated_at": "2026-04-24T14:30:00+08:00",
  "versions": [
    {
      "version_id": "_master",
      "version_label": "主档简历",
      "is_master": true,
      "parent_id": null,
      "processing_status": "ready",
      "language": "both",
      "created_at": "2026-04-24T10:00:00+08:00",
      "updated_at": "2026-04-24T10:00:00+08:00",
      "target_job": null,
      "file_paths": {
        "zh_md": "_master/resume-zh.md",
        "en_md": "_master/resume-en.md",
        "result_json": "_master/result.json"
      }
    },
    {
      "version_id": "bytedance-ai-engineer-2026q2",
      "version_label": "字节-AI-Engineer-2026Q2",
      "is_master": false,
      "parent_id": "_master",
      "processing_status": "ready",
      "language": "both",
      "created_at": "2026-04-24T14:30:00+08:00",
      "updated_at": "2026-04-24T14:30:00+08:00",
      "target_job": {
        "company": "字节跳动",
        "role": "AI Engineer",
        "role_family": "tech",
        "jd_hash": "sha256:a3f5c..."
      },
      "file_paths": {
        "zh_md": "bytedance-ai-engineer-2026q2/resume-zh.md",
        "en_md": "bytedance-ai-engineer-2026q2/resume-en.md",
        "result_json": "bytedance-ai-engineer-2026q2/result.json",
        "diff_report": "bytedance-ai-engineer-2026q2/diff-report.html",
        "jd_match_report": "bytedance-ai-engineer-2026q2/jd-match-report.md"
      },
      "metrics": {
        "keyword_coverage": 0.82,
        "ats_score": null,
        "provenance_risk": "low"
      }
    }
  ]
}
```

### 维护规则（吸收自 `DATA_CONTRACT.md`）

1. **原子读写**：Skill 更新 manifest 时必须"读全量 → 改内存对象 → 一次写回"，防止 race condition
2. **schema_version 前向兼容**：Skill 升级时自动迁移旧 schema，不报错
3. **用户可手改**：用户直接编辑 manifest 是允许的，Skill 读入时要容忍字段缺失
4. **Master 唯一性**：读入时若发现多份 `is_master: true` —— 保留 `updated_at` 最新的，其余降级并告警

---

## 1. result.json（子 Skill 契约）

```typescript
interface ResumeResult {
  schema_version: "1.0";
  skill_name: "resume-assistant";
  skill_version: string;
  generated_at: string;              // ISO 8601
  version_label: string;
  mode: "generate" | "tailor" | "polish" | "compare";
  review_status: "pending" | "partial" | "approved" | "rejected";

  inputs_echo: {                     // 输入回显（去敏感）
    mode: string;
    has_jd: boolean;
    preferences: Preferences;
    version_control: VersionControl;
  };

  role_family?: "tech" | "biz" | "design" | "ops";
  inferred_seniority?: "intern" | "junior" | "mid" | "senior" | "staff" | "principal";

  resume: {
    zh?: ResumeContent;              // 视 language 偏好输出
    en?: ResumeContent;
  };

  jd_match?: {                       // tailor / polish 模式输出
    total_keywords: number;
    matched_keywords: number;
    coverage_ratio: number;          // 0.0 - 1.0
    coverage_by_category: {
      hard_skills: number;
      soft_skills: number;
      industry_terms: number;
    };
    missing_keywords: {
      keyword: string;
      weight: number;
      suggestion: string;            // "建议补充 XX 经历"
    }[];
  };

  provenance: {
    audit_file: "provenance-audit.json";
    stats: {
      total_bullets: number;
      risk_distribution: {
        none: number;
        low: number;
        medium: number;
        high: number;
      };
      requires_review_count: number;
      placeholder_count: number;
    };
  };

  diff?: {                           // 有 base_version 时
    report_file: "diff-report.html";
    stats: {
      added_bullets: number;
      removed_bullets: number;
      modified_bullets: number;
      score_before?: number;
      score_after?: number;
    };
  };

  files: {
    path: string;                    // 相对 resume-output/<version_label>/ 的路径
    type: "markdown" | "html" | "json";
    language?: "zh" | "en";
    purpose: string;
  }[];

  next_suggestions: string[];        // 给用户或父 Agent 的下一步建议
  warnings: string[];                // 非致命警告
  errors: string[];                  // 应为空；否则说明流程未完成
}
```

### 1.1 ResumeContent（简历内容对象）

```typescript
interface ResumeContent {
  language: "zh" | "en";
  word_count: number;
  estimated_pages: number;           // 按 A4 标准排版估算
  sections: {
    basic_info: object;              // 按 input-schema 字段子集
    summary?: string;                // 个人简介（可选）
    education: EducationRendered[];
    work_experience?: WorkExperienceRendered[];
    projects?: ProjectRendered[];
    skills?: object;
    awards?: string[];
    publications?: string[];
  };
  template_used: "star" | "project_oriented" | "skill_oriented" | "hybrid";
  ats_score?: number;                // 0-100（预估 ATS 通过率，仅 en）
}

interface WorkExperienceRendered {
  company: string;
  title: string;
  city?: string;
  start_date: string;
  end_date: string;
  bullets: {
    bullet_id: string;               // 与 provenance-audit.json 对应
    text: string;
  }[];
}

interface ProjectRendered {
  name: string;
  role: string;
  start_date: string;
  end_date: string;
  tech_stack?: string[];
  bullets: { bullet_id: string; text: string }[];
}

interface EducationRendered {
  school: string;
  degree: string;
  major: string;
  start_date: string;
  end_date: string;
  extras?: string[];                 // GPA / 排名 / 课程 / 荣誉
}
```

---

## 2. provenance-audit.json

完整 schema 见 [provenance-rules.md](provenance-rules.md) §5。

---

## 3. jd-match-report.md（Markdown）

### 章节结构

```markdown
# JD 关键词匹配诊断报告

**版本**：v1-bytedance-llm
**目标岗位**：字节跳动 - 大模型算法工程师
**生成时间**：2026-04-23 16:30

## 一、总体匹配度

- 总体覆盖率：**82%** ✅（目标 ≥ 80%）
- hard_skills 覆盖率：91% ✅
- industry_terms 覆盖率：75% ⚠️
- soft_skills 覆盖率：60%（参考值，不纳入目标）

## 二、已命中关键词（15/18）

| 关键词 | 权重 | 出现位置 |
|---|:---:|---|
| PyTorch | 0.95 | 项目 1 / 技能 |
| LLM | 0.95 | 项目 2 / 个人简介 |
| ...

## 三、未命中关键词（3/18）

| 关键词 | 权重 | 建议 |
|---|:---:|---|
| RLHF | 0.85 | ⚠️ 您原始素材未提及；如有相关经验请补充 |
| Agent | 0.85 | ⚠️ 未命中 |
| vector_db | 0.80 | ⚠️ 未命中 |

## 四、可选的补强动作

- [ ] 补充 RLHF 相关经历（如有）
- [ ] 是否使用过 LangChain / AutoGPT？
```

---

## 4. diff-report.html

- 左右分栏：左 = base 版本，右 = 当前版本
- bullet 级红删 / 绿增 / 黄改
- 每条修改旁边显示 `rationale`（改写动作清单）
- 页眉统计：`+12 lines  -5 lines  ~8 lines`
- 颜色方案：
  - 绿 `#d4edda` = 新增
  - 红 `#f8d7da` = 删除
  - 黄 `#fff3cd` = 修改

---

## 5. resume-zh.md（中文简历模板）

见 [../assets/resume-template-zh.md](../assets/resume-template-zh.md)。

## 6. resume-en.md（英文简历模板）

见 [../assets/resume-template-en.md](../assets/resume-template-en.md)。

---

## 7. 被父 Skill 调用时的最小返回

父 Skill（如 `job-coach`）只关心：

```json
{
  "schema_version": "1.0",
  "review_status": "approved",
  "version_label": "v1-bytedance-llm",
  "files": [
    { "path": "resume-zh.md", "type": "markdown", "language": "zh", "purpose": "primary-resume" },
    { "path": "resume-en.md", "type": "markdown", "language": "en", "purpose": "bilingual-resume" }
  ],
  "jd_match": { "coverage_ratio": 0.82 },
  "provenance": { "stats": { "requires_review_count": 0 } }
}
```

即可做后续决策（如是否触发模拟面试）。
