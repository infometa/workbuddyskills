# resume-assistant · 共享上下文（所有 mode 必读）

> **定位**：把 `SKILL.md` v0.2 里所有与具体 mode 无关的通用内容集中到本文件。
> `SKILL.md`（Router）只保留触发条件 + mode 路由 + 最小铁律；mode 细节各自独立。
>
> **阅读顺序**：Skill 激活时 → `SKILL.md` → 本文件 → [`DATA_CONTRACT.md`](../DATA_CONTRACT.md) → 对应 `modes/<mode>.md`。

---

## 一、15 条核心原则（v0.3.2 定稿）

> **v0.2 关键变化**：三维度 Provenance（#1-#3）、Master-First 版本管理（#7）、AI 文风审计（#3）、User/System 数据分层（#12）。
>
> **v0.3.1 关键变化**：新增 #14 — 用户上传的原始简历文件（PDF/Word/任何源文件）永不被修改，所有改写产出新文件。
>
> **v0.3.2 关键变化**：新增 #15 — Preflight 不可跳过（模板 / 长度 / 语言三选项一次问完，可选 fallback 启发式 + 顶部注释行声明）；视觉排版能力扩展（Pandoc + JSON Resume 双桥梁）；战略附录默认产出（Strengths/Gap/面试 Tips/CL Hooks）。

1. **防幻觉第一维 · 不编造事实**：用户原始素材里**没有**的数字/项目/技术栈，AI **绝不能**补。
   任何推断都必须标记 `provenance: "inferred-with-caveat"` + `hallucination_risk: "high"` + 强制用户审核。
   详见 [`../references/provenance-rules.md`](../references/provenance-rules.md)。
2. **防幻觉第二维 · 合法改写**：只允许 `references/provenance-rules.md §2.3` 列出的 11 种 `rewrite_action`；任何其他动作视为违规。
3. **防幻觉第三维 · 防 AI 味**：输出的每条 bullet 都过 [`../references/ai-phrase-blacklist.md`](../references/ai-phrase-blacklist.md) 的中英双语黑名单。
   中文："赋能 / 打造 / 夯实 / 抓手 / 闭环 / 心智 / 颗粒度 / 组合拳" 等 20+ 词；
   英文："spearheaded / orchestrated / leveraged / utilized / synergy / paradigm / cutting-edge" 等 53 词。命中 ≥6 次必须强制修改。
4. **可追溯性**：每条生成的 bullet 都能回到用户原始素材片段（`from_field` + `text` 引文）+ 改写动作清单。
5. **中英双版不是翻译**：两套招聘规范下的独立重写（中文含完整教育/期望薪资等字段；英文省年龄/性别/照片，动词开头，1 页）。
6. **JD 关键词分级对齐**：`hard_skills`（权重 0.7-1.0）/ `soft_skills`（0.3-0.5）/ `industry_terms`（0.5-0.9），
   按 `role_family`（tech / biz / design / ops）加载不同词典；tech 内部若检出 AI 信号，进一步细分为 6 种 `ai_archetype`。
   数据源统一为 [`../references/keyword-taxonomy.json`](../references/keyword-taxonomy.json)（说明见同名 `.md`）。
7. **Master-First 版本管理**：首份简历自动成为 `_master/`（全局唯一 `is_master: true`），
   所有 per-JD 定制版都是派生版（`parent_id` 指向 master）。Master 卡死（failed/processing > 24h）自动推进下一个 ready 版本；Master 不可直删。详见 [`../references/output-schema.md`](../references/output-schema.md)。
8. **全中文教练反馈**：术语双语（Provenance / ATS / XYZ / STAR 保留英文，解释用中文）。
9. **量化数据是命门**：每条 bullet 检查是否含数字；无量化且原始素材也无数字 → 生成 `____%` 占位符让用户填，**绝不编**。
   **联系信息同样禁止编造**：姓名/电话/邮箱/微信/地址等个人联系字段，若用户未提供，一律用占位符（`[电话待填写]` / `[邮箱待填写]` / `[姓名]`），**绝不编造假号码或假邮箱**。input-schema 中 `email: 必填` 的含义是"用户必须最终填写"，不是"AI 可以补一个假的"。所有占位符必须在 Step 8 高亮列出，提示用户在投递前替换真实信息。
10. **文化适配**：中文"吃苦耐劳 / 能加班" → 英文简历**不对应任何 bullet**（文化差异，美国禁止在简历体现此类软技能）。
11. **用户审核环节不可跳过**：所有 `hallucination_risk ≥ medium` 的条目 + AI 文风命中 ≥6 次的 bullet 必须逐项展示给用户二次确认。
12. **User/System 数据分层**：永不自动修改用户数据（`experiences/` / `resume-output/_master/` / `.resume-assistant/profile.yml`）；
    系统文件（`SKILL.md` / `references/*` / `scripts/*`）可随 Skill 升级。详见 [`../DATA_CONTRACT.md`](../DATA_CONTRACT.md)。
13. **作为子 Skill 被调用时输出同样结构化**：`result.json` + `_manifest.json` schema 在 v1.0 起锁定，不随版本改 breaking change。
14. **v0.3.1 — 用户上传源文件只读**：用户用 `@file.pdf` 引用或附件上传的任何简历源文件（PDF/Word/Markdown/纯文本）一律视为只读底稿。
    - 文本层 PDF：允许用 `pdfplumber` / `pdftotext` / `PyMuPDF` 提取；提取后字段标 `provenance: "pdf-extracted-needs-confirmation"`；**必须经用户逐段确认后**才升级为 `user-confirmed-from-pdf` 进入 master
    - 扫描件 / 图片 PDF：拒绝处理（OCR 对数字字段幻觉率高），让用户复制粘贴文本
    - 所有改写产出写入 `resume-output/`；**原文件位置与内容永不被修改 / 删除 / 覆盖**
    - PDF 反爬水印（如 BOSS 直聘按 X 坐标散落字符）必须先按 char-level X 坐标过滤后再提取
15. **🆕 v0.3.2 — Preflight 不可跳过 + 显式偏好声明**：所有"生成 / 改写 / 定制"类 mode（`generate` / `tailor` / `rewrite`）开始前**一次性**问 3 个问题：模板（STAR / 项目导向 / 技能导向 / 混合）、长度（1 页 / 2 页 / auto）、语言（zh / en / both）。
    - 用户回 `a/b/c` / 自然语言 / "默认"均可
    - 用户说"默认" → 按 [`../references/preflight-questions.md`](../references/preflight-questions.md) §3 启发式自动选择
    - 自动选择时**必须**在产出 markdown 顶部插入注释行：`<!-- preflight: template=X · length=Y · language=Z · auto-selected: true -->`
    - **NEVER** 跳过 preflight 直接生成；**NEVER** 一次只问一个问题（3 轮浪费）；**NEVER** 在 fallback 产出物中省略顶部注释行

---

## 二、通用工作流骨架（所有 mode 共享的 8 步）

各 mode 只会强调差异步骤，**缺省步骤继承本骨架**。

```
┌────────────────────────────────────────────────────────────────┐
│ Step 0  mode 确认                                              │
│   generate / rewrite / tailor / diff / score / refine / export │
│   用户说法模糊时追问（未指定 JD 默认 generate；有 JD 默认 tailor）│
├────────────────────────────────────────────────────────────────┤
│ Step 0.5 Preflight 三选项（v0.3.2）                            │
│   仅在 generate / tailor / rewrite 时执行（其他 mode 跳过）    │
│   ⚠️ generate 模式：必须先完成 Step 0.1 信息收集，              │
│      再执行 Preflight（fallback 启发式依赖经历信息）            │
│   一次性问：template / length / language                       │
│   用户回"默认"→ 启发式 fallback + 顶部注释行声明               │
│   规则：references/preflight-questions.md                      │
├────────────────────────────────────────────────────────────────┤
│ Step 1  experiences 输入校验                                   │
│   basic_info 必需 / education 必需 / experience 或 projects ≥1 │
│   太简略 → 启发式追问（"这段经历有没有量化数据？用了什么技术？"）│
├────────────────────────────────────────────────────────────────┤
│ Step 2  JD 解析（mode 需要 JD 时执行）                         │
│   run: python3 scripts/parse_jd.py --jd-file X [--role-family Y]│
│   输出：role_family / seniority / ai_archetype /              │
│        hard_skills / soft_skills / industry_terms + 权重      │
├────────────────────────────────────────────────────────────────┤
│ Step 3  role_family × archetype 绑定                           │
│   从 JD 标题 + 关键词分布 → tech / biz / design / ops          │
│   若 tech 且命中 AI 信号 → 挂载对应 archetype 的 framing_hint   │
│   切换不同的措辞库与量化示例                                     │
├────────────────────────────────────────────────────────────────┤
│ Step 4  简历生成 / 改写（language 驱动）                        │
│   - zh：中文 rubric + 中文量化范例 + 完整字段                   │
│   - en：XYZ 公式 + action verb + 1 页硬约束 + 去敏感字段        │
│   - both：骨架一致 + LLM 分别填内容 + 一致性检查                 │
│   模板：star / project_oriented / skill_oriented / hybrid      │
├────────────────────────────────────────────────────────────────┤
│ Step 5  三维度 Provenance 审计                                 │
│   维度一：每条 bullet vs 用户素材 ngram 比对 → 防编造           │
│   维度二：改写动作分类（查 provenance-rules.md 11 种 action）   │
│   维度三：AI 文风黑名单扫描                                     │
│     run: python3 scripts/audit_ai_flavor.py --file <md>        │
│     (--exit-on warn 可在 CI/批量场景用)                        │
│   任何维度违规 → 强制用户审核 或 按 auto_fix_ai_flavor 自动修复 │
├────────────────────────────────────────────────────────────────┤
│ Step 6  JD 关键词覆盖率验证（需要 JD 时执行）                   │
│   coverage_before（master）vs coverage_after（定制版）          │
│   目标：定制版 ≥ 80%；未达 → 列出缺失关键词建议用户补素材        │
├────────────────────────────────────────────────────────────────┤
│ Step 7  输出组装（Master-First 目录）                           │
│   首次 → 写入 resume-output/_master/                            │
│   tailor/rewrite → 写入 resume-output/<version_label>/          │
│                    + diff-report.html vs 其 parent              │
│   tailor 默认追加 strategic-appendix.md（v0.3.2）              │
│     规格：references/strategic-appendix-spec.md                │
│   每次都更新 resume-output/_manifest.json                       │
├────────────────────────────────────────────────────────────────┤
│ Step 8  用户审核环节（强制不可跳过）                            │
│   展示所有 hallucination_risk ≥ medium 的条目                  │
│   + AI 文风命中 ≥6 次的 bullet                                │
│   用户逐项回复"属实 / 需修改 / 删除"                           │
│   全部审核完成后标记 review_status: "approved"                 │
│   并把 version_control.processing_status 置为 "ready"          │
└────────────────────────────────────────────────────────────────┘
```

---

## 三、输入契约（摘要）

完整 schema 见 [`../references/input-schema.md`](../references/input-schema.md)。核心字段：

| 字段 | 必填 | 说明 |
|---|:---:|---|
| `mode` | ✅ | `generate` / `rewrite` / `tailor` / `diff` / `score` / `refine` / `export` |
| `experiences` | ✅ | 经历数据（`structured` YAML / `freeform_text` / `legacy_resume_file`）|
| `target_job.jd_content` | tailor/score 必填 | JD 原文（纯文本；暂不支持 URL/截图）|
| `preferences.template` | 可选 | `star` / `project_oriented` / `skill_oriented` / `hybrid` |
| `preferences.language` | 可选 | `zh` / `en` / `both`（默认 `zh`）|
| `preferences.length` | 可选 | `1page` / `2page` / `auto`（默认 `auto`）|
| `preferences.auto_fix_ai_flavor` | 可选 | `aggressive` / `report_only`（默认） / `off` |
| `version_control.parent_id` | 可选 | 从哪个基础版本派生（首版留空自动创建 `_master`）|
| `version_control.is_master` | 可选 | 强制指定是否为主档（通常由系统维护）|
| `version_control.base_version_id` | @deprecated | v0.1 兼容字段，新代码用 `parent_id` |

---

## 四、输出契约（摘要 · Master-First）

完整 schema 见 [`../references/output-schema.md`](../references/output-schema.md)。核心产出：

```
<workspace>/resume-output/
├── _master/                          主档（全局唯一 is_master=true）
│   ├── resume-zh.md
│   ├── resume-en.md
│   ├── result.json
│   └── provenance-audit.json
├── <version_label>/                  派生版（parent_id="_master"）
│   ├── resume-zh.md + resume-en.md + HTML
│   ├── result.json
│   ├── diff-report.html              # vs parent 的 diff
│   ├── jd-match-report.md            # 仅 tailor/score mode
│   └── provenance-audit.json
└── _manifest.json                    版本树清单（全局索引）
```

---

## 五、7 条核心禁区（附 why）

这里只列真正需要"外部规则覆盖 LLM 默认行为"的禁区。其余注意事项分散在各 mode 文件里——但这 7 条无论在哪个 mode 都不能打折扣。

1. **不编造用户素材里没有的数字/项目/技术栈。**
   简历里的每一个数字和项目，HR 都可以在面试 5 分钟内追问穿底——编造的内容会立刻让候选人失去信任，损失远超 JD 匹配度增益。遇到 JD 想要但用户没有的数据：用 `____` 占位符 + 在 gap report 里列出，让用户决定是否补充真实素材。

2. **不把"参与"自动升级为"主导"（或类似的角色夸大）。**
   这种"擦边升级"是中文简历最常见的造假模式。HR 看出来后直接标"不诚信"。只有用户原始素材支持更高角色（如原文含"我独立交付了"），才能升级语气；且必须先告知用户再改写。完整的合法改写动作列表见 `provenance-rules.md §2.3`。

3. **不大量使用 AI 味套话（命中 ≥6 次必须修改）。**
   "赋能 / 打造 / 抓手 / 夯实 / 闭环 / spearheaded / leveraged / orchestrated" 等词会让简历立刻被识别为 AI 生成，降低 HR 信任度。完整黑名单见 `ai-phrase-blacklist.json`；自动审计用 `scripts/audit_ai_flavor.py`。

4. **不把中式软技能（吃苦耐劳/服从安排/能加班）写进英文简历。**
   中西方职场文化差异大：这类表达在英文简历里是负分项，甚至可能触碰美国/新加坡劳工法律中"overtime obligation"的敏感地带。正确做法：直接删除，无需替换。

5. **不跳过 Provenance 三维度审计（Step 5）和用户审核（Step 8）。**
   这两步是唯一让用户在"AI 改写"和"面试被追问"之间还有一次纠错机会的防线。审计跳过 = 用户在不知情下签发了 AI 可能已经夸大的内容。

6. **不修改用户上传的原始文件（PDF / Word / Markdown）。**
   用户把文件传给 AI 改简历，心理预期是"AI 帮我生成新版本，不动原文"。原文被覆盖是极难恢复的用户体验灾难。所有改写产出写入 `resume-output/`，原文件只读。

7. **不在 PDF 用户逐段确认（`pdf-extracted-needs-confirmation` → `user-confirmed-from-pdf`）前进入改写流程。**
   PDF 提取有字符错位、BOSS 水印散落等问题，未经确认的内容进入改写等于在错误素材上叠加错误——两层错误放大后在简历里无法追溯。逐段确认是把"AI 读的内容"和"用户说的内容"对齐的唯一机会。

> 其余更细的 per-mode 禁区（例如 tailor 不覆盖 master、refine 不改动未被点名 bullet）见对应 mode 文件的"独有的 NEVER"段落。

---

## 六、资源索引

### 根目录（Skill 启动必读）

| 文件 | 用途 |
|---|---|
| [`../SKILL.md`](../SKILL.md) | Router 总入口（触发判定 + mode 路由）|
| [`../DATA_CONTRACT.md`](../DATA_CONTRACT.md) | User Layer / System Layer 数据分层（写操作前必读）|
| 本文件 | 15 条核心原则 + 通用工作流 + 输入输出契约 + NEVER 清单 |

### modes/（按激活 mode 选读）

| 文件 | 场景 |
|---|---|
| [`generate.md`](generate.md) | 从 0 写一份新简历（未指定 JD）|
| [`rewrite.md`](rewrite.md) | 基于已有 master 简历润色改写（不绑特定 JD）|
| [`tailor.md`](tailor.md) | 基于 master 针对某个 JD 做定制（**最常用主流程**）|
| [`diff.md`](diff.md) | 生成两个版本间的 diff 报告 |
| [`score.md`](score.md) | 给现有简历对某 JD 打覆盖率/差距分 |
| [`refine.md`](refine.md) | 基于用户反馈做多轮细修 |
| [`export.md`](export.md) | v0.4 规划：ATS 友好 PDF 导出 |

### references/（按需加载）

| 文件 | 用途 | 何时读 |
|---|---|---|
| [`../references/input-schema.md`](../references/input-schema.md) | 输入字段完整定义 | Step 1 |
| [`../references/output-schema.md`](../references/output-schema.md) | 输出 JSON schema + `_manifest.json` | Step 7 |
| [`../references/keyword-taxonomy.md`](../references/keyword-taxonomy.md) | 关键词分类词典（人类可读）| Step 2/3/6 |
| [`../references/keyword-taxonomy.json`](../references/keyword-taxonomy.json) | 词典数据源（parse_jd.py 读）| Step 2 |
| [`../references/provenance-rules.md`](../references/provenance-rules.md) | 三维度防幻觉追溯规则 | Step 5/8 必读 |
| [`../references/ai-phrase-blacklist.md`](../references/ai-phrase-blacklist.md) | AI 文风黑名单说明 | Step 5 维度三 |
| [`../references/ai-phrase-blacklist.json`](../references/ai-phrase-blacklist.json) | 黑名单数据源（audit_ai_flavor.py 读）| Step 5 维度三 |
| [`../references/preflight-questions.md`](../references/preflight-questions.md) | **🆕 v0.3.2** Preflight 三选项问询脚本 + fallback 启发式 | Step 0.5 |
| [`../references/ats-rules.md`](../references/ats-rules.md) | **🆕 v0.3.2** ATS 兼容规则（清单 / 节标题 / 关键词频控 / 报告模板）| Step 6（关键词覆盖率）+ export 渲染约束 |
| [`../references/bullet-formulas.md`](../references/bullet-formulas.md) | **🆕 v0.3.2** X-Y-Z + STAR + CAR + Power Verbs + 量化策略 + 缺数策略 | Step 4（写 bullet）+ Step 5 维度二 |
| [`../references/strategic-appendix-spec.md`](../references/strategic-appendix-spec.md) | **🆕 v0.3.2** 简历后 4 段附录规格（tailor 默认产出）| tailor mode Step 7 |
| [`../references/inspirations.md`](../references/inspirations.md) | **🆕 v0.3.2** 吸收账本（每条规则可追溯到来源 skill 第几行）| Skill 维护时读 |

### scripts/

| 脚本 | 用途 |
|---|---|
| [`../scripts/parse_jd.py`](../scripts/parse_jd.py) | JD 解析：关键词 + role_family + seniority + AI archetype |
| [`../scripts/audit_ai_flavor.py`](../scripts/audit_ai_flavor.py) | AI 文风审计（Provenance 维度三）|
| [`../scripts/export_pdf.sh`](../scripts/export_pdf.sh) | **🆕 v0.3.2** Pandoc 一键导出 PDF（三主题 + 引擎降级链）|

### assets/

| 文件 | 用途 |
|---|---|
| [`../assets/resume-template-zh.md`](../assets/resume-template-zh.md) | 中文简历 Markdown 模板 |
| [`../assets/resume-template-en.md`](../assets/resume-template-en.md) | 英文简历 Markdown 模板 |
| [`../assets/themes/ats-safe.css`](../assets/themes/ats-safe.css) | **🆕 v0.3.2** Pandoc 默认主题（ATS 严格安全 · v0.3.2 实装）|
| `../assets/themes/modern.css` | v0.3.2 占位 → v0.4 完善 |
| `../assets/themes/compact.css` | v0.3.2 占位 → v0.4 完善 |

---

## 七、降级原则（v0.3.2 棘轮迭代 2 新增）

> 单源工具失败时的统一兜底链。**任何降级必须在 transcript / `provenance-audit.json` 显式记录** ——禁止静默 fallback。

| 失败工具 | 一级降级 | 二级降级 | 兜底 |
|---|---|---|---|
| `scripts/parse_jd.py`（关键词 / archetype 推断）| 让用户手动指定 `role_family`（tech/biz/design/ops）| 跳过 archetype 切措辞库；用 generic framing | 写 `provenance-audit.json.degraded.parse_jd=true` 提示用户 |
| `scripts/audit_ai_flavor.py`（AI 味维度三）| 主 Agent 内联跑黑名单匹配（仅 references/ai-phrase-blacklist.json 关键词）| 仅按命中数计数不分级 | WARN 用户 + 写 `degraded.ai_flavor=lite_inline` |
| `scripts/export_pdf.sh` 全失败 | 用浏览器打印（先生成 HTML） | 走路径 B JSON Resume 上传外部 | export.md §十用户回路菜单（让用户选）|
| `pdfplumber` / `pdftotext` 提取失败 | 改用 `PyMuPDF` | 让用户复制粘贴文本（铁律 #14）| 拒绝继续 `mode=tailor`，进入 `mode=generate` |
| `references/keyword-taxonomy.json` 加载失败 | 用脚本内嵌的 minimal taxonomy（仅 hard_skills 5 类）| 跳过 Step 6 关键词覆盖率验证 | 在 `jd-match-report.md` 标 `coverage=unavailable` |
| 用户拒绝 Preflight（铁律 #15 fallback）| 按 `references/preflight-questions.md §3` 启发式自动选 | — | 顶部注释行强制标 `auto-selected: true` |

**全部失败兜底**：所有自动化路径都崩溃时（极端情况），不要硬塞内容给用户——降级到对话式追问，让用户人工提供缺失信息后从 Step 1 重新开始。
