# mode: export · 导出 + 视觉排版美化（v0.3.2 实装）

> **前置**：先读 [`_shared.md`](_shared.md)。
>
> **状态**：✅ **v0.3.2 实装最小可用版**（Pandoc PDF + JSON Resume Schema 双路径）；v0.4 继续打磨主题与脚本健壮性。

---

## 一、设计哲学：内容是我们的，排版借力外部

我们的产品边界明确：**内容生产 + Provenance** 是我们的护城河，**视觉模板**不是。

但用户对"出 PDF / 美化排版"的诉求是真实的，我们提供**两条桥接路径**——把 Markdown 主资产**转换**为可视化产物，**不**自研模板引擎。

```
                          resume-output/<v>/resume-zh.md
                                     │
                  ┌──────────────────┼──────────────────┐
                  │                                       │
        ┌─────────▼──────────┐               ┌────────────▼──────────────┐
        │  路径 A：Pandoc    │               │  路径 B：JSON Resume       │
        │  本地一键导出      │               │  外部编辑器渲染            │
        │                    │               │                            │
        │  • ATS-safe 主题   │               │  • 转 JSON Resume schema   │
        │  • Modern 主题     │               │  • 用户上传 rxresu.me       │
        │  • Compact 主题    │               │    或 jsonresume.org/themes│
        │                    │               │  • 在线选 13+ 主题         │
        │  脚本：scripts/    │               │  AI 直接生成 JSON           │
        │  export_pdf.sh     │               │  写入 resume-{lang}.json    │
        └────────────────────┘               └─────────────────────────────┘
                  │                                       │
                  ▼                                       ▼
         resume-{lang}.pdf                  resume-{lang}.json + 用户外部渲染
```

| 维度 | 路径 A（Pandoc）| 路径 B（JSON Resume）|
|---|---|---|
| 立即可用 | ✅ 一行命令出 PDF | ⚠️ 需用户在外部站点选模板 |
| 主题数量 | 我们提供 3 套 | 13+（社区生态）|
| 离线可用 | ✅ | ❌（需访问 reactive-resume / jsonresume.org）|
| ATS-safe 主题 | ✅ 默认 | ⚠️ 取决于用户选的主题 |
| 视觉炫酷度 | 基本干净 | ✅ 显著美观 |
| 用户上传简历隐私 | ✅ 全程本地 | ⚠️ 需上传到外部站点 |

**默认建议**：路径 A（ATS-safe 主题）出投递版 PDF；用户想要好看的版本，再走路径 B。

---

## 二、触发条件

- "导出 PDF / 我要把简历打印出来 / 生成投递版"
- "我要好看的视觉版本 / 想要漂亮的简历"
- 明确 `mode: "export"`

---

## 三、输入

```yaml
mode: export
version_control:
  version_id: <某版本目录>     # 默认最新 ready 的派生版；无则 _master
export:
  format: pdf | json | both    # pdf=路径A · json=路径B · both=两个都出
  theme: ats-safe | modern | compact  # 仅 format=pdf 时使用 · 默认 ats-safe
  language: zh | en | both     # 默认继承该 version 已有的语言
  output_filename: <可选>      # 默认 resume-{lang}-{theme}.pdf
```

---

## 四、与通用骨架的差异

export 是**纯渲染**步骤，不动内容：

| Step | 差异 |
|---|---|
| Step 0 | mode 已定 |
| Step 1 | 读目标 version 的 `resume-{lang}.md`；不追问内容 |
| **Step 2-6** | **全部跳过**（不解析 JD / 不改写 / 不审计 AI 味）|
| Step 7 | 渲染到 `resume-output/<version_id>/resume-{lang}-{theme}.pdf` 或 `.json`；并在 `_manifest.json.versions[*].file_paths` 里补上路径 |
| **Step 8** | **跳过**（只是渲染，无内容审核必要）|

---

## 五、路径 A：Pandoc 本地导出

### §5.1 三套内置主题

| 主题 | 用途 | 风格 |
|---|---|---|
| **ats-safe**（默认）| 投递主用 · ATS 通过率优先 | 单列 / 黑白 / 衬线字体 / 无装饰 |
| **modern** | 投设计感 / 创业公司 / 出海简历 | 单列 / 顶部彩条 / 无衬线字体 / 极简图标可选 |
| **compact** | 经验密集 / 强行 1 页 | 紧凑边距 / 小字号 / 单列 |

> 🚧 **modern / compact 在 v0.3.2 是占位**：CSS 文件已留位置，主体效果靠 v0.4 打磨。**ats-safe 是首发可用的主题**。

### §5.2 一键命令（脚本：[`../scripts/export_pdf.sh`](../scripts/export_pdf.sh)）

```bash
bash scripts/export_pdf.sh \
  --version v3_tailor_byte_llm_algo \
  --lang zh \
  --theme ats-safe \
  --output resume-zh-投字节算法岗.pdf
```

脚本内部用 Pandoc + 主题 CSS：

```bash
pandoc "resume-output/$VERSION/resume-$LANG.md" \
  --from gfm \
  --to pdf \
  --pdf-engine wkhtmltopdf \
  --css "themes/$THEME.css" \
  -o "resume-output/$VERSION/$OUTPUT"
```

**前置依赖检测**：脚本启动时检测 `pandoc` + `wkhtmltopdf`，缺失时给清晰安装提示（macOS 用 `brew install pandoc wkhtmltopdf`）。

**降级链**：
1. `pandoc + wkhtmltopdf`（推荐）
2. `pandoc + tectonic`（LaTeX 路径，需要会处理中文字体）
3. `pandoc + chrome --headless`（如果 wkhtmltopdf 装不上）

### §5.3 主题 CSS 位置

```
<skill-root>/
└── assets/themes/
    ├── ats-safe.css     # v0.3.2 实装
    ├── modern.css       # v0.3.2 占位（基础可用，待 v0.4 打磨）
    └── compact.css      # v0.3.2 占位
```

CSS 内置 ATS-safe 硬约束（来自 [`../references/ats-rules.md`](../references/ats-rules.md) §1）：单列 / 无浮动 / 无图片 / 标准字体 / 0.6-1in 边距 / 9-12pt 字号。

---

## 六、路径 B：JSON Resume Schema 桥接

### §6.1 为什么用 JSON Resume

[`jsonresume.org`](https://jsonresume.org) 是 2014 年开始的开源简历 schema 标准，社区有 **13+ 套渲染主题**（elegant / kendall / flat / paper / 等）；著名开源工具 **Reactive Resume** 也兼容这套 schema。

用户拿到 JSON 后可在以下任一处直接渲染：
- `https://registry.jsonresume.org/<your-github-username>` （需绑 GitHub）
- `https://rxresu.me/` （Reactive Resume，自部署 / SaaS 都行）
- 本地 `npx resume-cli serve` 选主题

### §6.2 JSON 生成方式

路径 B 由 AI 直接完成转换，无需调用外部脚本：

1. 读 `resume-output/<version>/result.json`（结构化数据）
2. 按 JSON Resume schema v1.0.0 字段映射：
   - `basics` ← basic_info
   - `work` ← experience
   - `projects` ← projects
   - `education` ← education
   - `skills` ← skills（按硬技能/软技能分组）
   - `languages` ← preferences.language 推导
3. 将生成的 JSON 内容写入 `resume-output/<version>/resume-{lang}.json`

### §6.3 用户后续操作（脚本会打印提示）

```
✅ 已生成 resume-output/<version>/resume-en.json

下一步选其一：
1. 上传到 https://rxresu.me/ → 点 "Import" → 选模板 → 下载 PDF
2. 部署到 GitHub Gist + 访问 https://registry.jsonresume.org/{your-username}
3. 本地：npx resume-cli serve → 浏览器访问 http://localhost:4000
```

> ⚠️ **隐私提示**：路径 B 需要用户把简历数据上传到外部服务。如果隐私敏感，**坚持用路径 A**。

---

## 七、ATS 友好的硬约束（无论哪条路径都生效）

> 完整规则见 [`../references/ats-rules.md`](../references/ats-rules.md)

- 单列布局（绝不用多列表格）
- 无图片 / 图标 / 装饰字符
- 日期格式统一：`YYYY-MM` 或 `MM/YYYY`
- 字体：Helvetica / Arial / Calibri / Times New Roman
- 无页眉页脚（除非用户明确要求页码）
- 标题用白名单词（Work Experience / Education / Skills / ...）

**`ats-safe.css` 已硬编码这些规则；用户如果改主题但仍要 ATS 通过，建议同时出一份 `ats-safe.pdf` 作"投递版"。**

---

## 八、输出 manifest 更新

每次 export 后追加 `_manifest.json` 该版本的 `file_paths`：

```json
{
  "versions": [
    {
      "version_id": "v3_tailor_byte_llm_algo",
      "file_paths": {
        "resume_md_zh": "resume-output/v3.../resume-zh.md",
        "resume_pdf_zh_ats_safe": "resume-output/v3.../resume-zh-ats-safe.pdf",
        "resume_pdf_zh_modern": "resume-output/v3.../resume-zh-modern.pdf",
        "resume_json_en": "resume-output/v3.../resume-en.json"
      },
      "export_history": [
        {"timestamp": "2026-04-27T15:32:00+08:00", "format": "pdf", "theme": "ats-safe", "lang": "zh"},
        {"timestamp": "2026-04-27T15:35:00+08:00", "format": "json", "theme": null, "lang": "en"}
      ]
    }
  ]
}
```

---

## 九、NEVER

- **NEVER** 在 export 阶段修改简历内容（哪怕主题要"截短到 1 页"也不应自动删 bullet——应回到 `mode=refine` 让用户决定）
- **NEVER** 用 CSS 绝对定位 / 浮动复杂布局（ATS 扫不到）
- **NEVER** 把姓名 / 邮箱嵌进图片里
- **NEVER** 默认开启路径 B（JSON 上传外部）——必须用户显式说"我要好看的"才走
- **NEVER** 自创主题主色（v0.3.2 三套主题已够用，不增加复杂度）
- **NEVER** 把 PDF 写到 User Layer（永远写 `resume-output/<version>/`）

---

## 十、用户回路

如果用户触发 export 但前置依赖未装（pandoc / wkhtmltopdf 都没有）：

```
检测到本机缺少 PDF 渲染依赖（pandoc + wkhtmltopdf）。

可选项：
1. 我帮你打印 macOS 安装命令（brew install pandoc wkhtmltopdf · 约 30 秒）
2. 用浏览器打印代替（我先帮你生成 resume-zh.html，你用 Chrome → 打印 → 存为 PDF）
3. 走路径 B（生成 JSON，上传 rxresu.me 选模板出 PDF · 视觉更好）
```

让用户选，**不要默认安装系统依赖**。
