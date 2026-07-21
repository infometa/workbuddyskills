---
name: pdfkit-py
description: 'Pure-Python PDF toolkit with 50 commands covering reading, editing, conversion, forms, encryption, OCR, and IR. Trigger on: PDF 阅读, 编辑, 转换, 合并, 拆分, 加密, 签名, OCR, 表单, 水印, 书签, 压缩, 裁剪, 旋转, pdfkit.'
description_zh: PDF全能工具箱，覆盖阅读分析、自然语言编辑、格式转换、表单处理、加密签名、OCR、IR等全场景
description_en: 'All-in-one PDF toolkit: read, edit, convert, fill forms, encrypt, sign, OCR, and IR — 50 commands powered by pure Python'
allowed-tools: Bash, Read, Write, Glob
argument-hint: <操作描述或 PDF 文件路径>
---

# pdfkit — AI 原生 PDF 处理工具

你是 pdfkit 的使用专家。用户描述 PDF 处理需求时，你负责选择正确的命令、参数并执行。

## ⚠️ 环境初始化（看到本段请立即执行）

**立即运行以下命令完成环境初始化，不要跳过，不要先检查。**

根据操作系统选择：

- **macOS / Linux**：
  ```bash
  bash ./scripts/setup.sh
  ```
- **Windows**（PowerShell）：
  ```powershell
  cmd /c ".\scripts\setup.bat"
  ```

脚本会自动检测 Python 3.10+，如果系统未安装会自动下载独立 Python 运行时（无需管理员权限）。
如果失败，向用户报告错误。成功后本段会被自动删除。

<!-- END_SETUP -->

## 定位 CLI

skill 加载时会提供 base directory，CLI 入口在 `./scripts/pdfkit.py`。

根据操作系统，venv 中的 Python 路径不同：

- **macOS / Linux**：`<basedir>/scripts/venv/bin/python3`
- **Windows**：`<basedir>\scripts\venv\Scripts\python.exe`

```bash
# macOS / Linux
/path/to/pdfkit-py/scripts/venv/bin/python3 /path/to/pdfkit-py/scripts/pdfkit.py help

# Windows（PowerShell）—— 必须用 & 调用运算符
& "\path\to\pdfkit-py\scripts\venv\Scripts\python.exe" "\path\to\pdfkit-py\scripts\pdfkit.py" help
```

所有命令用 base directory 拼上对应平台的 venv python 路径和 `scripts/pdfkit.py` 的绝对路径调用。
简写为 `pdfkit.py <command>` 时，实际执行的是上述完整路径。

### Windows PowerShell 注意事项

1. **必须使用 `&`（调用运算符）**：PowerShell 中执行带引号路径的程序时，必须在最前面加 `&`，否则会报 `UnexpectedToken` 错误。
2. **JSON 参数中的引号**：PowerShell 中 JSON 参数**不能用单引号包裹**（单引号在 PowerShell 中是字面字符串，但嵌套双引号仍需转义）。推荐将复杂 JSON 写入文件后用 `--config` 传入。
3. **如果 venv 不存在**：先运行 `.\scripts\setup.bat` 初始化环境。

```powershell
# ✅ 正确的 Windows PowerShell 调用方式
& "C:\Users\xxx\.codebuddy\skills\pdfkit-py\scripts\venv\Scripts\python.exe" "C:\Users\xxx\.codebuddy\skills\pdfkit-py\scripts\pdfkit.py" split --input "D:\docs\file.pdf" --output_dir "D:\docs\output" --mode ranges --ranges "[[0,2]]"

# ❌ 错误：没有 & 运算符
"C:\...\python.exe" "C:\...\pdfkit.py" split ...
```

**参数不确定时**：运行 `pdfkit.py <command> help` 查看完整参数说明。

## 字体

字体由 `font_manager` 模块自动管理，**无需手动指定**：

- 内置 NotoSansSC-Regular 字体，在 setup 时自动从 CDN 下载到 `<basedir>/fonts/`
- 内置字体主要覆盖简体中文 + 常用 CJK，**不要假设它能覆盖所有语言、emoji、特殊符号或罕见字形**
- 内置字体不存在时，自动搜索本机系统字体（macOS: PingFang/STHeiti, Linux: NotoSansCJK/wqy, Windows: 微软雅黑/宋体）
- 搜索结果缓存，不会重复扫描
- 用户通过 `--font_path` 指定时，使用用户指定的

### 字体处理规则

- 如果用户明确提到字体、字形、乱码、缺字、显示不对、英文/其他语言不显示、emoji/符号显示异常等问题，**不要默认继续使用内置字体**
- 这类场景下，优先去本机系统里搜索能覆盖目标文本的字体，再用该字体重试
- 如果自动选择的字体显示仍异常，继续换本机其他候选字体，而不是直接告诉用户“字体不支持”
- 只有在本机确实找不到可用字体时，才向用户说明缺少对应字形覆盖

## 用户输入

$ARGUMENTS

如果用户未提供具体参数，先问：需要处理哪个 PDF 文件？要做什么操作？

## 全局选项

| Flag | 说明 |
|------|------|
| `--config <file.json>` | 从 JSON 文件加载复杂参数（CLI 参数优先级高于 config 文件） |

输出格式统一为 JSON：`{"ok": true, "data": {...}}` / `{"ok": false, "error": "..."}`

**页码从 0 开始**：用户说"第 1 页"→ 参数 `0`。

## 坐标系规范

**所有命令统一使用 PyMuPDF 坐标系**：

- **原点**：页面**左上角** (0, 0)
- **x 轴**：向右增大
- **y 轴**：向下增大
- **左上角**：约 (30, 30)
- **左下角**：约 (30, 页面高度 - 30)
- **右下角**：约 (页面宽度 - 30, 页面高度 - 30)
- **A4 页面尺寸**：宽 595，高 842（单位：点）

> ⚠️ 注意：这与 PDF 原生坐标系（y=0 在底部）**相反**。所有命令内部已自动处理转换，用户只需按上述规范传入坐标。
>
> 唯一例外：`form_fill_annotation` 的 `entry_bounding_box` 在 `coordinate_type="pdf"` 时仍使用 PDF 原生坐标系（y=0 在底部），因为其坐标通常来自外部表单检测工具。

## 可选依赖

核心依赖在 setup 脚本首次运行时已安装。以下依赖**按需安装**——**当命令执行报错提示缺少某个包时，你应该自动用 venv 内的 pip 安装它，然后重试原命令，不要把安装指引丢给用户。**

### Python 可选包

pip 路径：

- **macOS / Linux**：`./scripts/venv/bin/pip install <包名>`
- **Windows**：`.\scripts\venv\Scripts\pip.exe install <包名>`

| 包名 | 涉及命令 | 安装命令 |
|------|---------|---------|
| `camelot-py[cv]` | extract_table（lattice/stream 方法） | `pip install "camelot-py[cv]"` |
| `tabula-py` | extract_table（tabula 方法） | `pip install tabula-py` |
| `pdf2docx` | pdf_to_word（pdf2docx 方法） | `pip install pdf2docx` |
| `pikepdf` | compress（高级压缩优化） | `pip install pikepdf` |
| `pix2tex` | formula_detect（model 方法） | `pip install pix2tex` |

**安装流程**：执行命令 → 报错含 `ModuleNotFoundError` 或 `ImportError` → 用 venv pip 安装对应包 → 重试原命令。

### 系统外部工具

无需预装。**当命令执行报错提示缺少以下工具时，你应该自动执行对应的安装命令，安装完成后重试原命令，不要把安装指引丢给用户，也不要先反问用户要不要安装。**

| 工具 | 用途 | 涉及命令 | macOS 安装 | Windows 安装 | Linux 安装 |
|------|------|---------|-----------|-------------|-----------|
| `gs` | PDF 压缩 | compress | `brew install ghostscript` | `winget install ArtifexSoftware.GhostScript --accept-package-agreements --accept-source-agreements` | `sudo apt install -y ghostscript` |
| `tesseract` | OCR 识别 | smart_edit, edit_scanned, ocr_locate, search_text, extract_text | `brew install tesseract` | `winget install UB-Mannheim.TesseractOCR --accept-package-agreements --accept-source-agreements` | `sudo apt install -y tesseract-ocr` |
| `tesseract-lang` | OCR 中文语言包 | 同上（涉及中文 PDF 时需要） | `brew install tesseract-lang` | 安装 tesseract 时已包含 | `sudo apt install -y tesseract-ocr-chi-sim` |
| `soffice` | 格式转换 | convert, pdf_to_word | `brew install --cask libreoffice` | `winget install TheDocumentFoundation.LibreOffice --accept-package-agreements --accept-source-agreements` | `sudo apt install -y libreoffice` |

**安装流程**：执行命令 → 报错含"未找到 xxx 命令"或"语言包缺失" → 根据当前 OS 执行上表对应安装命令 → 重试原命令。

**OCR 特别规则**：

- 只要用户意图是编辑扫描件、OCR 定位、OCR 搜索、扫描件提取文本，且命令报缺少 `tesseract` 或语言包，就直接安装，不要询问用户是否安装
- 对应命令包括：`smart_edit`（扫描件路径）、`edit_scanned`、`ocr_locate`、`search_text --engine ocr`、`extract_text --ocr_fallback`
- 用户说“修改扫描件”“改图片里的字”“识别扫描 PDF”“OCR 找字”时，默认视为允许安装 OCR 依赖
- 只有安装命令本身失败、缺少管理员权限、或系统包管理器不可用时，才向用户报告阻塞点

---

## 命令详解（50 个命令）

## 阅读与分析 (13)

### page_count — 获取 PDF 页数

```bash
pdfkit.py page_count --input doc.pdf
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入 PDF 路径 |

### extract_text — 提取文本

> 💡 **支持自动 OCR 降级**：添加 `--ocr_fallback` 参数后，**纯扫描件页面**（完全无文字层）会自动使用 OCR 提取文字。
> **混合型页面**（有文字层 + 嵌入图片）仅提取文字层文本，图片上的文字**不会**被 OCR 提取。
> 不加 `--ocr_fallback` 时，扫描件页面会返回空并给出提示。

```bash
# 基本用法（仅提取文字层）
pdfkit.py extract_text --input doc.pdf --pages '[0,1]'

# 自动 OCR 降级（推荐：一次调用覆盖所有场景）
pdfkit.py extract_text --input scan.pdf --pages '[0]' --ocr_fallback

# 指定输出格式
pdfkit.py extract_text --input doc.pdf --format html --output /tmp/out.html
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入 PDF 路径 |
| `--pages` | 页码列表 JSON，如 `[0,1,3]` |
| `--output` | 输出文件路径 |
| `--format` | 输出格式，默认 `text`。可选 `text` / `dict` / `blocks` / `words` / `html` |
| `--ocr_fallback` | 自动 OCR 降级，默认 `False`。仅对纯扫描件页面（无文字层）自动 OCR，混合型页面中图片上的文字不提取（需要 tesseract） |
| `--lang` | OCR 语言，默认 `eng+chi_sim`（仅 `--ocr_fallback` 时生效） |

### to_images — 页面转图片

```bash
pdfkit.py to_images --input doc.pdf --output_dir /tmp/imgs/ --dpi 300
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入 PDF 路径 |
| `--output_dir` | **必填** 输出目录 |
| `--pages` | 页码列表 JSON |
| `--dpi` | 分辨率，默认 `150` |
| `--format` | 图片格式，默认 `png`。可选 `png` / `jpeg` |

### long_image — 多页拼接长图

```bash
pdfkit.py long_image --input doc.pdf --output /tmp/long.png
pdfkit.py long_image --input doc.pdf --output /tmp/long.png --pages '[0,1,2]' --gap 10
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入 PDF 路径 |
| `--output` | **必填** 输出图片路径 |
| `--pages` | 页码列表 JSON |
| `--dpi` | 分辨率，默认 `150` |
| `--gap` | 页间距像素，默认 `0` |

### extract_images — 提取内嵌图片

```bash
pdfkit.py extract_images --input doc.pdf --output_dir /tmp/imgs/
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入 PDF 路径 |
| `--output_dir` | **必填** 输出目录 |
| `--pages` | 页码列表 JSON |
| `--min_size` | 最小尺寸（像素），默认 `100` |

### extract_table — 提取表格

```bash
pdfkit.py extract_table --input doc.pdf --format markdown
pdfkit.py extract_table --input doc.pdf --pages '[0]' --format csv --output /tmp/table.csv
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入 PDF 路径 |
| `--pages` | 页码列表 JSON |
| `--format` | 输出格式，默认 `json`。可选 `csv` / `json` / `markdown` |
| `--output` | 输出文件路径 |
| `--method` | 提取方法，默认 `auto`。可选 `auto` / `lattice` / `stream` |
| `--header` | 是否将第一行作为表头，默认 `False`（原样输出所有行）。有表头行的表格传 `--header` |

### layout_analyze
```bash
pdfkit.py layout_analyze --input doc.pdf --pages '[0]' --detail full
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入 PDF 路径 |
| `--pages` | 页码列表 JSON |
| `--detail` | 详细程度，默认 `basic`。可选 `basic` / `full` |

### ocr_locate — OCR 定位文字

> 需要 `tesseract`

```bash
pdfkit.py ocr_locate --input scan.pdf --page 0 --text "合同编号"
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入 PDF 路径 |
| `--page` | 页码，默认 `0` |
| `--text` | 要定位的文字 |
| `--lang` | OCR 语言，默认 `eng+chi_sim` |

### chat_pdf — PDF 问答上下文提取

```bash
pdfkit.py chat_pdf --input doc.pdf --question "主要结论是什么"
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入 PDF 路径 |
| `--question` | 问题 |
| `--pages` | 页码列表 JSON |
| `--max_context_chars` | 最大上下文字数，默认 `8000` |

### chunk_pdf — 文档分块

```bash
pdfkit.py chunk_pdf --input doc.pdf --strategy paragraph
pdfkit.py chunk_pdf --input doc.pdf --strategy fixed --chunk_size 500 --overlap 100
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入 PDF 路径 |
| `--strategy` | 分块策略，默认 `paragraph`。可选 `page` / `paragraph` / `fixed` / `semantic` |
| `--chunk_size` | 块大小，默认 `1000` |
| `--overlap` | 重叠字数，默认 `200` |
| `--pages` | 页码列表 JSON |

### formula_detect — 数学公式检测

```bash
pdfkit.py formula_detect --input paper.pdf --pages '[0,1]'
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入 PDF 路径 |
| `--pages` | 页码列表 JSON |
| `--method` | 检测方法，默认 `heuristic`。可选 `heuristic` / `model` |

### reading_order — 阅读顺序检测

```bash
pdfkit.py reading_order --input doc.pdf --pages '[0]'
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入 PDF 路径 |
| `--pages` | 页码列表 JSON |

### schema_extract — Schema 结构化提取

```bash
pdfkit.py schema_extract --input invoice.pdf \
  --schema '{"invoice_no":"string","date":"string","items":[{"name":"string","amount":"number"}]}'
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入 PDF 路径 |
| `--schema` | **必填** 目标结构 JSON |
| `--pages` | 页码列表 JSON |

---

## 编辑与修改 (10)

### smart_edit — 智能编辑（自动判断文字层/扫描件）

```bash
# 替换文本（所有页）
pdfkit.py smart_edit --input doc.pdf --output out.pdf \
  --edits '[{"type":"replace_text","find":"旧文本","replace":"新文本","page":-1}]'

# 添加文本
pdfkit.py smart_edit --input doc.pdf --output out.pdf \
  --edits '[{"type":"add_text","text":"新文本","x":100,"y":200,"page":0}]'

# 预览模式
pdfkit.py smart_edit --input doc.pdf --output out.pdf --dry_run \
  --edits '[{"type":"replace_text","find":"旧","replace":"新"}]'
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入 PDF 路径 |
| `--output` | **必填** 输出 PDF 路径 |
| `--edits` | **必填** 编辑操作列表 JSON |
| `--dry_run` | 预览模式，不实际修改，默认 `False` |

edits 支持的操作类型：

| type | 字段 |
|------|------|
| `replace_text` | `find`, `replace`, `page`（-1=所有页），`color`（可选，[r,g,b] 0-1 范围） |
| `add_text` | `text`, `x`, `y`（坐标原点在页面**左上角**，y 向下增大；左上角≈y:30，左下角≈y:页高-30）, `page`, `font_size`（默认12）, `color`（可选，[r,g,b] 0-1 范围，如红色 [1,0,0]） |
| `delete_text` | `find`, `page` |
| `replace_image` | `page`, `image_index`, `new_image`（图片路径） |

### pymupdf_edit — 文字层文本编辑

```bash
pdfkit.py pymupdf_edit --input doc.pdf --output out.pdf \
  --edits '[{"find":"旧","replace":"新","page":0}]'
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入 PDF 路径 |
| `--output` | **必填** 输出 PDF 路径 |
| `--edits` | **必填** 编辑操作列表 JSON |

### edit_scanned — 扫描件编辑

> 需要 `tesseract`

```bash
pdfkit.py edit_scanned --input scan.pdf --output out.pdf \
  --page 0 --find "旧文本" --replace "新文本" --font fonts/DroidSansFallback.ttf
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入 PDF 路径 |
| `--output` | **必填** 输出 PDF 路径 |
| `--page` | 页码，默认 `0` |
| `--find` | **必填** 查找文本 |
| `--replace` | **必填** 替换文本 |
| `--font` | 字体路径（中文需指定） |
| `--lang` | OCR 语言，默认 `eng+chi_sim` |

### search_text — 文本搜索

```bash
pdfkit.py search_text --input doc.pdf --find "关键词"
pdfkit.py search_text --input doc.pdf --find "关键词" --page 0 --engine fuzzy
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入 PDF 路径 |
| `--find` | **必填** 搜索文本 |
| `--page` | 页码，默认 `-1`（全部页） |
| `--engine` | 搜索引擎，默认 `auto`。可选 `pymupdf` / `pdfplumber` / `fuzzy` / `ocr` / `auto` |

### overlay_text — 文本覆盖

```bash
pdfkit.py overlay_text --input doc.pdf --output out.pdf \
  --overlays '[{"page":0,"bbox":[100,30,300,60],"text":"覆盖文本","font_size":12}]'
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入 PDF 路径 |
| `--output` | **必填** 输出 PDF 路径 |
| `--overlays` | **必填** 覆盖配置列表 JSON `[{page, bbox, text, font_size, color, bg_color}]`。bbox 格式 `[x0,y0,x1,y1]` 使用统一坐标系（左上角原点，y↓） |

### pdf_create — 创建 PDF

```bash
pdfkit.py pdf_create --output report.pdf \
  --elements '[{"type":"heading","text":"标题"},{"type":"paragraph","text":"正文"}]' \
  --font_path fonts/DroidSansFallback.ttf

pdfkit.py pdf_create --output report.pdf \
  --elements '[{"type":"heading","text":"报告"},{"type":"paragraph","text":"内容"}]' \
  --page_size A4 --watermark '{"text":"草稿"}'
```

| Flag | 说明 |
|------|------|
| `--output` | **必填** 输出 PDF 路径 |
| `--elements` | **必填** 元素列表 JSON `[{type, text, ...}]` |
| `--page_size` | 页面大小，默认 `A4`。可选 `A4` / `A3` / `letter` / `legal` |
| `--orientation` | 方向，默认 `portrait` |
| `--font_path` | 字体路径（中文需指定） |
| `--margins` | 边距 JSON |
| `--header` | 页眉 JSON |
| `--footer` | 页脚 JSON |
| `--watermark` | 水印 JSON |
| `--title` | 文档标题 |
| `--author` | 作者 |

### watermark — 添加水印

```bash
# 自动搜索字体（推荐）
pdfkit.py watermark --input doc.pdf --output out.pdf --text "机密"

# 指定字体
pdfkit.py watermark --input doc.pdf --output out.pdf \
  --text "机密" --font_path /path/to/font.ttf

# 密集模式 + 自定义样式
pdfkit.py watermark --input doc.pdf --output out.pdf \
  --text "CONFIDENTIAL" --mode dense --opacity 0.1 --angle 30
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入 PDF 路径 |
| `--output` | **必填** 输出 PDF 路径 |
| `--text` | **必填** 水印文本 |
| `--font_path` | 字体路径（不指定则自动搜索） |
| `--mode` | 水印模式，默认 `sparse`。可选 `sparse` / `dense` |
| `--font_color` | 字体颜色，默认 `#CCCCCC` |
| `--angle` | 旋转角度，默认 `45` |
| `--opacity` | 透明度，默认 `0.15` |
| `--font_size` | 字号，默认 `50` |
| `--x_gap` | dense 模式水平间距，默认 `200` |
| `--y_gap` | dense 模式垂直间距，默认 `150` |

### add_page_numbers — 添加页码

```bash
pdfkit.py add_page_numbers --input doc.pdf --output out.pdf
pdfkit.py add_page_numbers --input doc.pdf --output out.pdf \
  --position bottom_right --format "第 {page} 页 / 共 {total} 页" \
  --font_path fonts/DroidSansFallback.ttf
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入 PDF 路径 |
| `--output` | **必填** 输出 PDF 路径 |
| `--position` | 位置，默认 `bottom_center`。可选 `bottom_center` / `bottom_left` / `bottom_right` / `top_center` / `top_left` / `top_right` |
| `--format` | 格式字符串，默认 `"{page} / {total}"` |
| `--start_number` | 起始页码，默认 `1` |
| `--font_size` | 字号，默认 `10` |
| `--font_color` | 颜色 JSON，默认 `[0,0,0]` |
| `--margin` | 边距（点），默认 `36` |
| `--pages` | 页码列表 JSON |
| `--font_path` | 字体路径（中文页码需指定） |

### remove_headers_footers — 清除页眉页脚

```bash
# 仅识别
pdfkit.py remove_headers_footers --input doc.pdf --extract_only

# 清除
pdfkit.py remove_headers_footers --input doc.pdf --output clean.pdf
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入 PDF 路径 |
| `--output` | 清除模式下必填，输出路径 |
| `--pages` | 页码列表 JSON |
| `--header_ratio` | 页眉区域比例，默认 `0.08` |
| `--footer_ratio` | 页脚区域比例，默认 `0.08` |
| `--extract_only` | 仅识别不清除，默认 `False` |

---

## 组织与变换 (10)

### compress — 压缩 PDF

```bash
pdfkit.py compress --input doc.pdf --output out.pdf --quality ebook
pdfkit.py compress --input doc.pdf --output out.pdf --target_size_mb 5
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入 PDF 路径 |
| `--output` | **必填** 输出 PDF 路径 |
| `--quality` | 压缩质量，默认 `ebook`。可选 `screen` / `ebook` / `printer` / `prepress` |
| `--target_size_mb` | 目标大小（MB） |

### split — 拆分 PDF

```bash
pdfkit.py split --input doc.pdf --output_dir /tmp/split/
pdfkit.py split --input doc.pdf --output_dir /tmp/split/ --mode ranges --ranges '[[0,2],[3,5]]'
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入 PDF 路径 |
| `--output_dir` | **必填** 输出目录 |
| `--mode` | 拆分模式，默认 `each`。可选 `each`（每页一个） / `ranges`（按范围） |
| `--ranges` | 范围 JSON `[[0,2],[3,5]]`，`mode=ranges` 时使用 |

### merge — 合并 PDF

```bash
pdfkit.py merge --inputs '["a.pdf","b.pdf"]' --output merged.pdf
```

| Flag | 说明 |
|------|------|
| `--inputs` | **必填** 输入文件列表 JSON |
| `--output` | **必填** 输出 PDF 路径 |

### rotate — 旋转页面

```bash
pdfkit.py rotate --input doc.pdf --output out.pdf --angle 90
pdfkit.py rotate --input doc.pdf --output out.pdf --angle 180 --pages '[0,2]'
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入 PDF 路径 |
| `--output` | **必填** 输出 PDF 路径 |
| `--angle` | 旋转角度，默认 `90`。可选 `90` / `180` / `270` / `-90` / `-180` / `-270` |
| `--pages` | 页码列表 JSON |

### crop — 裁剪页面

```bash
# 裁剪第一页，保留左上角 400x500 区域
pdfkit.py crop --input doc.pdf --output out.pdf --left 0 --top 0 --right 400 --bottom 500
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入 PDF 路径 |
| `--output` | **必填** 输出 PDF 路径 |
| `--left` | 裁剪区左边界 x，默认 `0` |
| `--top` | 裁剪区上边界 y，默认 `0`（页面顶部） |
| `--right` | 裁剪区右边界 x，默认 `612` |
| `--bottom` | 裁剪区下边界 y，默认 `792`（页面底部） |
| `--pages` | 页码列表 JSON |

坐标使用统一坐标系（左上角原点，y↓）。

### convert — 格式转换

```bash
pdfkit.py convert --input doc.pdf --output doc.docx --to_format docx
pdfkit.py convert --input doc.html --output doc.pdf --to_format pdf
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入文件路径 |
| `--output` | **必填** 输出文件路径 |
| `--from_format` | 源格式，默认 `auto`。可选 `auto` / `pdf` / `docx` / `html` / `md` / `images` |
| `--to_format` | 目标格式。可选 `pdf` / `docx` / `html` / `md` / `images` |

### pdf_to_word — PDF 转 Word

```bash
pdfkit.py pdf_to_word --input doc.pdf --output doc.docx
pdfkit.py pdf_to_word --input doc.pdf --output doc.docx --pages '[0,5]'
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入 PDF 路径 |
| `--output` | **必填** 输出 Word 路径 |
| `--pages` | 页码范围 JSON `[start, end]` |
| `--method` | 转换方法，默认 `auto`。可选 `auto` / `pdf2docx` / `libreoffice` |

### bookmarks — 书签管理

```bash
# 获取书签
pdfkit.py bookmarks --action get --input doc.pdf

# 设置书签
pdfkit.py bookmarks --action set --input doc.pdf --output out.pdf \
  --bookmarks '[{"level":1,"title":"第一章","page":0},{"level":2,"title":"1.1 节","page":2}]'
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入 PDF 路径 |
| `--action` | 操作，默认 `get`。可选 `get` / `set` |
| `--output` | `action=set` 时必填，输出路径 |
| `--bookmarks` | 书签列表 JSON `[{"level":1,"title":"...","page":0}]` |
| `--mode` | 设置模式，默认 `replace`。可选 `replace` / `append` |

---

## 安全与表单 (8)

### encrypt — 加密

```bash
pdfkit.py encrypt --input doc.pdf --output out.pdf --user_password "secret"
pdfkit.py encrypt --input doc.pdf --output out.pdf \
  --user_password "read" --owner_password "admin" --allow_print --allow_copy
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入 PDF 路径 |
| `--output` | **必填** 输出 PDF 路径 |
| `--user_password` | **必填** 用户密码 |
| `--owner_password` | 所有者密码 |
| `--allow_print` | 允许打印，默认 `True` |
| `--allow_modify` | 允许修改，默认 `False` |
| `--allow_copy` | 允许复制，默认 `False` |

### decrypt — 解密

```bash
pdfkit.py decrypt --input encrypted.pdf --output out.pdf --password "secret"
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入 PDF 路径 |
| `--output` | **必填** 输出 PDF 路径 |
| `--password` | **必填** 密码 |

### form_detect — 检测表单

```bash
pdfkit.py form_detect --input form.pdf
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入 PDF 路径 |
| `--extract_structure` | 提取表单结构，默认 `True` |

### form_fill — 填写表单

```bash
pdfkit.py form_fill --input form.pdf --output filled.pdf \
  --fields '[{"field_id":"name","value":"张三"},{"field_id":"date","value":"2026-01-01"}]'
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入 PDF 路径 |
| `--output` | **必填** 输出 PDF 路径 |
| `--fields` | **必填** 字段值列表 JSON `[{"field_id":"...","value":"..."}]` |

### form_fill_annotation — 注释方式填表

```bash
pdfkit.py form_fill_annotation --input form.pdf --output filled.pdf \
  --form_fields '[{"page":0,"x":100,"y":200,"text":"张三","font_size":12}]'
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入 PDF 路径 |
| `--output` | **必填** 输出 PDF 路径 |
| `--coordinate_type` | 坐标类型，默认 `pdf`。可选 `pdf` / `image` |
| `--pages` | 页码列表 JSON |
| `--form_fields` | **必填** 填写字段列表 JSON |

### flatten — 扁平化

```bash
pdfkit.py flatten --input form.pdf --output flat.pdf
pdfkit.py flatten --input doc.pdf --output flat.pdf --flatten_annotations --pages '[0,1]'
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入 PDF 路径 |
| `--output` | **必填** 输出 PDF 路径 |
| `--flatten_forms` | 扁平化表单，默认 `True` |
| `--flatten_annotations` | 扁平化注释，默认 `True` |
| `--pages` | 页码列表 JSON |

### redact — 涂黑脱敏

```bash
# 按文本涂黑
pdfkit.py redact --input doc.pdf --output out.pdf \
  --redactions '[{"type":"text","text":"身份证号","page":-1}]'

# 按区域涂黑
pdfkit.py redact --input doc.pdf --output out.pdf \
  --redactions '[{"type":"area","rect":[100,200,300,230],"page":0}]'

# 按正则涂黑
pdfkit.py redact --input doc.pdf --output out.pdf \
  --redactions '[{"type":"regex","pattern":"\\d{18}","page":-1}]'
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入 PDF 路径 |
| `--output` | **必填** 输出 PDF 路径 |
| `--redactions` | **必填** 涂黑规则列表 JSON |
| `--fill_color` | 填充颜色 JSON，默认 `[0,0,0]`（黑色） |

redactions 支持的类型：

| type | 字段 |
|------|------|
| `text` | `text`, `page`（-1=所有页） |
| `area` | `rect` `[left, top, right, bottom]`, `page` |
| `regex` | `pattern`, `page` |

### sign_pdf — 数字签名

```bash
pdfkit.py sign_pdf --input doc.pdf --output signed.pdf \
  --signature '{"text":"张三","position":"bottom_right"}'

pdfkit.py sign_pdf --input doc.pdf --output signed.pdf \
  --signature '{"image":"seal.png","position":[400,50],"width":150,"height":60}' \
  --pages '[0]'
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入 PDF 路径 |
| `--output` | **必填** 输出 PDF 路径 |
| `--signature` | **必填** 签名配置 JSON |
| `--pages` | 页码列表 JSON |

signature 字段：

| 字段 | 说明 |
|------|------|
| `image` | 签章图片路径 |
| `text` | 签名文字 |
| `position` | `"bottom_right"` 等预设位置，或 `[x, y]` 坐标 |
| `width` | 宽度，默认 `150` |
| `height` | 高度，默认 `60` |
| `font_size` | 字号，默认 `10` |
| `opacity` | 透明度，默认 `1.0` |

---

## IR 中间表示 (5)

### ir_export — 导出 PDF 结构为 JSON

```bash
pdfkit.py ir_export --input doc.pdf --output structure.json
pdfkit.py ir_export --input doc.pdf --output structure.json --include_images --include_fonts
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入 PDF 路径 |
| `--output` | **必填** JSON 输出路径 |
| `--pages` | 页码列表 JSON |
| `--include_images` | 包含图片数据，默认 `False` |
| `--include_fonts` | 包含字体信息，默认 `False` |

### ir_import — 从 JSON 重建 PDF

```bash
pdfkit.py ir_import --input structure.json --output rebuilt.pdf
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** IR JSON 路径 |
| `--output` | **必填** 输出 PDF 路径 |

### ir_inspect — 结构摘要

```bash
pdfkit.py ir_inspect --input doc.pdf
pdfkit.py ir_inspect --input doc.pdf --pages '[0]'
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入 PDF 路径 |
| `--pages` | 页码列表 JSON |

### ir_modify — 精准修改

```bash
pdfkit.py ir_modify --input doc.pdf --output out.pdf \
  --operations '[{"type":"replace_text","page":0,"find":"旧文本","replace":"新文本"}]'
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入 PDF 路径 |
| `--output` | **必填** 输出 PDF 路径 |
| `--operations` | **必填** 操作列表 JSON |

operations 支持的类型：

| type | 字段 |
|------|------|
| `replace_text` | `page`, `find`, `replace` |
| `replace_image` | `page`, `image_index`, `new_image`（图片路径） |
| `add_annotation` | `page`, `annot_type`（如 `freetext`）, `rect` `[x,y,x2,y2]`, `content` |

### ir_diff — 对比差异

```bash
pdfkit.py ir_diff --left old.pdf --right new.pdf
pdfkit.py ir_diff --left old.pdf --right new.pdf --output diff.json --text_only
```

| Flag | 说明 |
|------|------|
| `--left` | **必填** 左侧 PDF 路径 |
| `--right` | **必填** 右侧 PDF 路径 |
| `--output` | 输出路径 |
| `--text_only` | 仅对比文本，默认 `False` |

---

## 元工具 (4)

### detect_type — 检测页面类型

```bash
pdfkit.py detect_type --input doc.pdf
pdfkit.py detect_type --input doc.pdf --pages '[0,1]'
```

| Flag | 说明 |
|------|------|
| `--input` | **必填** 输入 PDF 路径 |
| `--pages` | 页码列表 JSON |

### exec_python — 沙箱执行 Python

> 最后手段，仅当现有命令无法完成时使用。

```bash
pdfkit.py exec_python --code 'import fitz; doc=fitz.open("doc.pdf"); print(len(doc))'
```

| Flag | 说明 |
|------|------|
| `--code` | **必填** Python 代码 |
| `--timeout` | 超时秒数，默认 `120` |

### layout_engine — 排版引擎

内部使用，一般不直接调用。

---

## 扩展机制（Extension）

当内置的命令无法满足复杂需求时（如多步骤批处理流程、特殊格式转换、业务定制逻辑等），可以通过**扩展脚本**来扩充能力。

### 工作原理

扩展脚本放在 skill basedir 的 `../pdfkit-extension/scripts/` 目录下，与内置命令遵循**完全相同的接口约定**（COMMAND、DESCRIPTION、PARAMS、handler），由 `pdfkit.py` 自动发现和注册。

```
/path/to/skills/                        ← skill basedir 的父目录
├── pdfkit-py/                          ← pdfkit skill 目录（skill basedir）
│   ├── scripts/
│   │   ├── pdfkit.py                   ← 入口（自动扫描扩展）
│   │   └── pdfkit/commands/            ← 内置 50 个命令
│   └── ...
└── pdfkit-extension/                   ← 扩展目录（用户创建，与 pdfkit-py 同级）
    └── scripts/
        ├── batch_watermark.py          ← 扩展脚本 1
        ├── invoice_extract.py          ← 扩展脚本 2
        └── ...
```

### 查看可用扩展

```bash
pdfkit.py extension --help
```

### 使用扩展命令

扩展命令可以像内置命令一样直接调用：

```bash
# 直接调用
pdfkit.py batch_watermark --input_dir /tmp/pdfs --text "机密"

# 通过 extension 子命令调用
pdfkit.py extension batch_watermark --input_dir /tmp/pdfs --text "机密"

# 查看扩展命令帮助
pdfkit.py batch_watermark help
```

### 创建扩展脚本

1. 创建扩展目录：
```bash
mkdir -p <skill basedir>/../pdfkit-extension/scripts
```

2. 复制模板：
```bash
cp <skill basedir>/scripts/pdfkit/extension_template.py \
   <skill basedir>/../pdfkit-extension/scripts/my_script.py
```

3. 编辑脚本，修改 `COMMAND`、`DESCRIPTION`、`PARAMS` 和 `handler` 函数。

### 扩展脚本模板结构

```python
COMMAND = "my_extension"              # 命令名
DESCRIPTION = "我的自定义 PDF 扩展"     # 描述
CATEGORY = "extension"                # 分类
PARAMS = [
    {"name": "input", "type": "str", "required": True, "help": "输入 PDF"},
    {"name": "output", "type": "str", "required": True, "help": "输出 PDF"},
]

def handler(params):
    # 处理逻辑...
    return {"message": "done", "output": params["output"]}
```

### 适用场景

| 场景 | 说明 |
|------|------|
| 批量处理流程 | 如批量加水印、批量压缩、批量转格式 |
| 多步骤组合 | 如先提取 → 处理 → 重新生成的 pipeline |
| 业务定制 | 如发票批量解析、合同模板填充、报告自动生成 |
| 实验性功能 | 在内置命令基础上做定制化调整 |

### 执行策略

遇到复杂 PDF 任务时：

1. **先查看是否有可复用的扩展**：`pdfkit.py extension --help`
2. **有现成扩展** → 直接调用
3. **没有现成扩展但内置命令可组合完成** → 拆解为多个内置命令依次执行
4. **需要新扩展** → 为用户创建扩展脚本到 `../pdfkit-extension/scripts/`

---

## 执行规范

1. **先理解需求**：分析用户描述，确定操作和参数
2. **参数确认**：关键参数缺失时先问用户
3. **不确定参数时**：运行 `pdfkit.py <command> help` 查看完整参数说明
4. **路径处理**：输入用用户路径，输出未指定时给合理默认值（同目录，或 macOS/Linux 用 `/tmp/`、Windows 用 `%TEMP%`）
5. **复杂 JSON 参数**：优先写入文件后用 `--config` 传入
6. **页码从 0 开始**：用户说"第 1 页"→ 参数 `0`
7. **错误处理**：
   - 依赖缺失 → 提示安装
   - 加密 PDF → 提示用户提供密码
   - 扫描件文本为空 → 建议用 `edit_scanned` 或 `ocr_locate`
8. **复合操作**：拆解后依次执行（如「提取第 3-5 页并转图片」= split + to_images）

## 场景速查

| 用户说 | 你执行 |
|--------|--------|
| 多少页 | `page_count` |
| 提取文字 / 读取内容 | `extract_text`（扫描件加 `--ocr_fallback`） |
| 转图片 / 截图 | `to_images` |
| 拼长图 | `long_image` |
| 提取图片 | `extract_images` |
| 提取表格 | `extract_table` |
| 分析布局 | `layout_analyze` |
| OCR / 识别扫描件文字 | `ocr_locate` |
| 问答 / 总结 | `chat_pdf` |
| 分块 / RAG | `chunk_pdf` |
| 公式检测 | `formula_detect` |
| 阅读顺序 | `reading_order` |
| 按格式提取 / 结构化 | `schema_extract` |
| 替换文字 / 编辑 PDF | `smart_edit` |
| 添加文字 / 文字标记 / 盖章文字 | `smart_edit`（`add_text` 类型） |
| 修改扫描件 | `edit_scanned` |
| 搜索文字 | `search_text` |
| 叠加文字 | `overlay_text` |
| 创建 PDF / 生成报告 | `pdf_create` |
| 加水印 | `watermark` |
| 加页码 | `add_page_numbers` |
| 去页眉页脚 | `remove_headers_footers` |
| 压缩 / 缩小体积 | `compress` |
| 拆分 | `split` |
| 合并 | `merge` |
| 旋转 | `rotate` |
| 裁剪 | `crop` |
| 转 Word | `pdf_to_word` |
| 格式转换 | `convert` |
| 书签 / 目录 | `bookmarks` |
| 加密 / 设置密码 | `encrypt` |
| 解密 / 去除密码 | `decrypt` |
| 检测表单 | `form_detect` |
| 填写表单 | `form_fill` |
| 坐标填表 | `form_fill_annotation` |
| 扁平化 | `flatten` |
| 涂黑 / 脱敏 / 隐藏信息 | `redact` |
| 签名 / 盖章 | `sign_pdf` |
| 查看结构 | `ir_inspect` |
| 导出结构 | `ir_export` |
| 从结构重建 | `ir_import` |
| 精准修改 | `ir_modify` |
| 对比两个 PDF | `ir_diff` |
| 检测页面类型 | `detect_type` |
| 自定义脚本 | `exec_python` |
| 复杂/批量任务 | 先 `pdfkit.py extension --help` 查看扩展，无则创建扩展脚本 |
