---
name: wangxiaobao-html-to-pdf
description: 将HTML文件转换为高质量PDF。当用户需要将HTML文件（本地文件或URL）转为PDF时触发此技能。触发词包括：HTML转PDF、生成PDF、导出PDF、convert HTML to PDF、HTML to PDF、把HTML生成PDF、PDF导出。支持完整保留CSS样式、渐变、Grid/Flex布局、背景色等。
agent_created: true
---

# HTML to PDF

## Overview

将HTML文件（本地文件或HTTP URL）转换为高质量PDF，使用Playwright无头Chromium渲染引擎，完整保留CSS渐变、Grid/Flex布局、背景色、字体等样式。适用于包含复杂样式的HTML报告、海报、数据可视化页面等场景。

## Prerequisites

运行此技能需要：
- Python 3.8+
- Playwright + Chromium

如未安装，先执行：
```bash
pip install playwright
python3 -m playwright install chromium
```

## CLI 参数

```bash
python3 scripts/html2pdf.py <source> [output] [options]
```

| 参数 | 说明 |
|------|------|
| `source` | HTML文件路径或HTTP/HTTPS URL（必填） |
| `output` | 输出PDF路径（可选，默认与HTML同名.pdf） |
| `--width` | 页面宽度（如 `210mm`、`1200px`） |
| `--height` | 页面高度（如 `297mm`、`1697px`） |
| `--format` | 标准纸张：`A4`（默认）、`A3`、`Letter` 等 |
| `--landscape` | 横向模式（A4横向 = 297×210mm） |

**页面尺寸优先级**：`--width/--height` > `--landscape` > `--format`

## Workflow

### Step 1: 确认输入

确认用户提供的HTML文件路径或URL：
- 本地文件：使用文件路径（如 `/path/to/report.html` 或 `report.html`）
- URL：完整的HTTP/HTTPS地址（如 `https://example.com/page.html`）

### Step 2: 选择页面尺寸

根据HTML设计宽度选择合适的PDF页面尺寸：

| 场景 | 参数 | 说明 |
|------|------|------|
| 标准报告/A4纵向 | （默认） | A4 210×297mm |
| 宽屏报告/A4横向 | `--landscape` | A4 横向，适合宽屏HTML |
| 与HTML设计宽完全匹配 | `--width 1200px --height 1697px` | 自定义尺寸，1:1无缩放 |
| 其他标准纸张 | `--format A3` | 支持 A3/A2/Letter 等 |

### Step 3: 执行转换

```bash
# 基本用法（A4纵向）
python3 scripts/html2pdf.py report.html

# 指定输出路径
python3 scripts/html2pdf.py report.html ./output.pdf

# A4 横向（适合宽屏报告）
python3 scripts/html2pdf.py report.html --landscape

# 自定义页面尺寸（与HTML设计宽完全匹配）
python3 scripts/html2pdf.py report.html --width 1200px --height 1697px

# 其他标准纸张
python3 scripts/html2pdf.py report.html --format A3
```

### Step 4: 验证并交付

1. 确认PDF文件已生成（检查文件大小 > 0）
2. 使用 `deliver_attachments` 工具交付PDF给用户
3. 在回复中说明文件名、大小、保存位置

## PDF参数

默认配置：
- **纸张格式**：A4（可通过 `--format` / `--landscape` / `--width+--height` 修改）
- **边距**：上15mm / 下15mm / 左10mm / 右10mm
- **打印背景**：是（完整保留CSS背景色、渐变）
- **页眉页脚**：关闭

## 排版一致性建议

为确保PDF与HTML排版完全一致：
1. **使用自定义尺寸**：`--width 1200px --height 1697px`（匹配HTML设计宽度）
2. **或在HTML中添加打印CSS**：
   ```css
   @page { size: 1200px 1697px; margin: 0; }
   @media print {
     body { margin: 0; -webkit-print-color-adjust: exact; }
     .card { break-inside: avoid; }
   }
   ```
3. **A4横向**：`--landscape` 适合大多数宽屏报告

## Troubleshooting

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 报错 `playwright` 未找到 | Python环境未安装playwright | 运行 `pip install playwright && python3 -m playwright install chromium` |
| PDF内容不全 | 页面JS未加载完成 | 增大 `wait_for_timeout` 的等待时间（默认5秒） |
| 中文字体缺失 | 系统未安装中文字体 | HTML中使用系统字体栈（PingFang SC / Microsoft YaHei） |
| 文件路径含中文报错 | 路径编码问题 | 使用绝对路径，确保路径格式正确 |
| PDF排版与HTML不一致 | 页面尺寸不匹配 | 使用 `--width/--height` 指定与HTML设计宽一致的尺寸 |
