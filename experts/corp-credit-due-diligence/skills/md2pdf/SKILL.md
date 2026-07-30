---
name: md2pdf
description: 将 Markdown 文档转换为带专业排版和中文支持的 PDF。流程为 Markdown → 带样式 HTML → PDF（用无头 Chromium 打印）。适用于把报告、文档等 .md 文件导出为可交付的 PDF，环境无需 pandoc/wkhtmltopdf/latex。
---

# Skill: md2pdf

## 功能

把 Markdown 转换为排版精良、**完整支持中文**的 PDF：

```
Markdown ──(python-markdown)──> 带样式 HTML ──(playwright/Chromium 打印)──> PDF
```

输出特性：A4 版面、红/蓝/朴素三套主题、红底白字表头 + 斑马纹表格、引用框、关键文字加粗高亮、页脚页码，并可选生成**封面页**、**目录页**与 **PDF 书签（侧边栏可跳转）**。

## 为什么用这条链路

经实测，常见的 CI/容器/桌面环境通常：
- **没有** pandoc / wkhtmltopdf / weasyprint / latex，只有 Python `markdown` 库；
- `playwright-cli` 全局命令不可用，且其封装默认找 `chrome` channel 会报错；
- 因此最稳妥的方式是 **python-markdown 渲染 HTML + 直接调底层 playwright 库用自带 chromium 打印**。

## 适用环境

本技能为跨平台设计，支持 Linux / macOS / Windows。各平台差异主要体现在：
- **Python 命令**：Linux/macOS 通常为 `python3`，Windows 常为 `python`。
- **playwright 安装位置**：脚本会自动探测多个常见位置（含环境变量 `PLAYWRIGHT_NODE_MODULES`）；找不到时按"常见问题"设置环境变量。
- **字体安装方式**：按下方 setup 第 3/4 步，依发行版/包管理器选择对应命令。

## 依赖与一次性准备（setup）

首次使用前，确保以下四项就绪（命令幂等，可重复执行）：

### 1) Python markdown 库（所有平台）

```bash
pip install markdown 2>/dev/null || python3 -m pip install markdown
```

### 2) Chromium 内核（playwright 自带，约 110MB，仅需装一次）

脚本会自动探测 playwright 的 `node_modules` 位置；Chromium 内核需用 playwright 自带命令安装：

```bash
# 通用（推荐）
npx playwright install chromium

# 若已知 playwright 的 node_modules 路径，也可直接调用其 cli.js
# node <playwright的node_modules>/playwright/cli.js install chromium
```

### 3) 中文字体（缺失会导致 PDF 中文显示为方块！）

> 必装，否则中文渲染为方块。按你的包管理器选择：

```bash
# RHEL/CentOS/Fedora 系 (dnf)
dnf install -y google-noto-sans-cjk-ttc-fonts google-noto-serif-cjk-ttc-fonts && fc-cache -f

# Debian/Ubuntu 系 (apt-get)
apt-get install -y fonts-noto-cjk && fc-cache -f

# macOS (Homebrew，系统通常已有中文字体；缺时可装)
brew install --cask font-noto-sans-cjk-sc font-noto-serif-cjk-sc && fc-cache -f 2>/dev/null || true

# Windows：系统自带中文字体，通常无需额外安装
```

### 4) 彩色 emoji 字体（缺失会导致 ✅⚠️❌⭐ 等 emoji 显示为方块/空白！）

```bash
# RHEL/CentOS/Fedora 系
dnf install -y google-noto-emoji-color-fonts && fc-cache -f

# Debian/Ubuntu 系
apt-get install -y fonts-noto-color-emoji && fc-cache -f

# macOS：系统自带 Apple Color Emoji，通常无需额外安装

# Windows：系统自带 Segoe UI Emoji，通常无需额外安装
```

> 脚本会自动检测中文字体与 emoji 字体，缺失时打印警告并给出安装命令，但不会自动安装。
> CSS 的 `font-family` 链尾已内置 `"Noto Color Emoji"`，装好字体后 emoji 即可彩色渲染，无需改脚本。

## 调用方式

> 路径以**技能包内的相对路径**表示。`<skill_dir>` 指 `skills/md2pdf` 目录。

```bash
# Linux / macOS
python3 <skill_dir>/scripts/md2pdf.py <input.md> [选项]

# Windows
python <skill_dir>\scripts\md2pdf.py <input.md> [选项]
```

### 参数

| 参数 | 说明 | 默认 |
|---|---|---|
| `input` | 输入 `.md` 文件路径（必填） | — |
| `-o, --output` | 输出 PDF 路径 | 与输入同名 `.pdf` |
| `--title` | 文档标题（PDF 元信息） | 输入文件名 |
| `--theme` | 配色：`red` / `blue` / `plain` | `red` |
| `--footer` | 页脚文字 | 同标题 |
| `--cover` | 生成封面页 | 否 |
| `--subtitle` | 封面副标题（配合 `--cover`） | 空 |
| `--meta` | 封面元信息，形如 `"报告类型=xxx;数据来源=yyy;密级=机密"`（`;` 分隔，`=` 分键值，支持中文） | 空（开启封面时自动补「生成时间」） |
| `--toc` | 生成目录页（基于 H1/H2/H3） | 否 |
| `--bookmarks` / `--no-bookmarks` | PDF 书签（侧边栏大纲） | 默认开启 |
| `--keep-html` | 保留中间 HTML 文件 | 否 |

### 示例

```bash
# 最简
python3 scripts/md2pdf.py 报告.md

# 指定输出、标题、蓝色主题、自定义页脚
python3 scripts/md2pdf.py 报告.md \
  -o ./out/业务报告.pdf \
  --title "业务机会分析报告" --theme blue \
  --footer "业务机会分析报告（机密）"
```

成功时输出：`[md2pdf] 完成 ✅  <路径>  (<大小> KB)`。

## 工作原理（脚本内部）

1. **渲染 HTML**：`markdown` 库 + 扩展（tables / fenced_code / sane_lists / nl2br / attr_list），套用内联 CSS 主题。
2. **封面 / 目录注入**：`--cover` 时注入居中封面页（标题+副标题+元信息表）；`--toc` 时扫描 H1/H2/H3 注入带锚点的目录页，二者均自动分页。
3. **定位 playwright**：按以下优先级查找含 playwright 的 `node_modules`：
   1. 环境变量 `PLAYWRIGHT_NODE_MODULES`（最高优先级）
   2. 本脚本同目录及上级目录的 `node_modules`（随技能包分发时）
   3. 各平台常见安装位置（`~/.bg-agent/node/node_modules`、`~/.cache/ms-playwright`、`/usr/lib/node_modules`、`/usr/local/lib/node_modules`、Windows 的 `%LOCALAPPDATA%\ms-playwright` 等）
4. **打印 PDF**：生成临时 Node 脚本，调 `chromium.launch()` → `page.goto(file://…)` → `page.pdf()`，A4、`printBackground`、带页脚页码。开启书签时用 `tagged:true`+`outline:true`，Chromium 依 H1/H2/H3 层级**自动生成 PDF 书签**，无需额外工具。
5. **字体自检**：`fc-list :lang=zh` 为空时告警缺中文字体；`fc-list` 中无 emoji 字体时告警缺彩色 emoji 字体。CSS `font-family` 链尾已内置 `"Noto Color Emoji"`，装好字体即彩色渲染。

## 常见问题

- **中文是方块** → 未装中文字体，按 setup 第 3 步装好对应字体后重跑。
- **emoji（✅⚠️❌⭐等）是方块/空白** → 未装彩色 emoji 字体，按 setup 第 4 步装好对应字体后重跑。
- **找不到 chromium** → 执行 `npx playwright install chromium`。
- **找不到 playwright 库** → 设置环境变量指向含 playwright 的 `node_modules` 目录：
  ```bash
  # Linux / macOS
  export PLAYWRIGHT_NODE_MODULES=/path/to/node_modules

  # Windows (PowerShell)
  $env:PLAYWRIGHT_NODE_MODULES = "C:\path\to\node_modules"
  ```
- **想要图片/复杂排版** → 直接在 Markdown 用标准语法即可，Chromium 会按 HTML 真实渲染。

## 适用 / 不适用

- ✅ 适用：报告、说明文档、清单等 `.md` → 交付级 PDF（中文场景），支持封面页、目录页、PDF 书签。
- ❌ 不适用：需要复杂分栏、脚注、交叉引用、目录页码（点线对齐+页号）等高级排版（可后续扩展 CSS 或改用专业排版工具）。
