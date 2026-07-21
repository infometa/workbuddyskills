#!/usr/bin/env python3
"""
VMCore 分析报告生成器 — Markdown + 命令引用
=============================================
将 Markdown 格式的分析报告渲染为 HTML，支持从命令日志中引用 crash 命令输出。

核心优势：
  - AI 输出 Markdown，减少结构化开销（~20% token 节省）
  - crash 命令输出通过引用标记 @cmd[command] 从日志中自动填充，
    避免 AI 重复输出已有的命令结果（~25% token 节省）
  - 命令日志由 MCP 服务端自动记录（零 AI token 开销），也支持 CLI 手动记录
  - 综合预计节省 40-50%+ 的 AI 输出 token

用法:
    # 基本用法
    python3 crash_report_generator.py -i report.md -o report.html

    # 带命令日志（启用命令引用填充）
    python3 crash_report_generator.py -i report.md -l crash_cmd_log_TIME.jsonl -o report.html

    # 手动记录命令输出到日志（仅在 MCP 自动日志不可用时使用）
    python3 crash_report_generator.py --log-cmd crash_cmd_log_TIME.jsonl --cmd "sys" --output "crash> sys\\n..."

    # 查看 Markdown 格式说明
    python3 crash_report_generator.py --format-help

Markdown 格式约定:
    - 标准 Markdown 语法（标题、段落、代码块、表格、列表等）
    - 命令引用：@cmd[command] 或 @cmd[command]{lines=N} 表示引用日志中的命令输出
    - 特殊块：:::alert{level=warning}, :::highlight, :::causal-chain, :::summary-box
    - 元数据：YAML front matter（可选）
"""

import json
import sys
import os
import re
import argparse
from datetime import datetime
from html import escape
from collections import OrderedDict

# ============================================================================
# CSS 样式
# ============================================================================

CSS_STYLES = """
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  margin: 0; padding: 20px; background: #f5f5f5; color: #333; line-height: 1.6;
}
.container {
  max-width: 1200px; margin: 0 auto; background: #fff;
  border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); padding: 40px;
}
h1 { color: #1a1a2e; border-bottom: 3px solid #e94560; padding-bottom: 15px; font-size: 1.8em; }
h2 { color: #16213e; border-left: 4px solid #e94560; padding-left: 12px; margin-top: 35px; font-size: 1.4em; }
h3 { color: #0f3460; margin-top: 25px; font-size: 1.15em; }
h4 { color: #533483; margin-top: 20px; }
table { border-collapse: collapse; width: 100%; margin: 15px 0; font-size: 0.9em; }
th { background: #16213e; color: #fff; padding: 10px 12px; text-align: left; }
td { padding: 8px 12px; border-bottom: 1px solid #eee; }
tr:hover { background: #f8f9fa; }
pre {
  background: #1a1a2e; color: #e0e0e0; padding: 15px; border-radius: 6px;
  overflow-x: auto; font-size: 0.85em; line-height: 1.5; white-space: pre-wrap; word-wrap: break-word;
}
code { font-family: "Fira Code", "Consolas", monospace; }
p code, li code, td code {
  background: #f0f0f0; color: #d63384; padding: 1px 5px; border-radius: 3px; font-size: 0.9em;
}
.summary-box code {
  background: transparent; color: inherit; padding: 0; border-radius: 0; font-size: inherit; font-weight: inherit; font-family: inherit;
}
.summary-box pre code {
  background: transparent; color: #e0e0e0; padding: 0; font-weight: normal;
}
pre code { color: #e0e0e0; }
.highlight { background: #fff3cd; padding: 12px 16px; border-radius: 6px; margin: 15px 0; border-left: 4px solid #ffc107; font-weight: bold; }
.alert { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 15px; border-radius: 6px; margin: 15px 0; }
.info { background: #d1ecf1; border: 1px solid #bee5eb; color: #0c5460; padding: 15px; border-radius: 6px; margin: 15px 0; }
.warning { background: #fff3cd; border: 1px solid #ffc107; color: #856404; padding: 15px; border-radius: 6px; margin: 15px 0; }
.success { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 15px; border-radius: 6px; margin: 15px 0; }
.tag { display: inline-block; background: #e94560; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; margin-right: 5px; }
.tag-blue { background: #0f3460; }
.tag-gray { background: #6c757d; }
.causal-chain { background: #f8f9fa; border: 2px solid #dee2e6; border-radius: 8px; padding: 20px; margin: 20px 0; }
.causal-chain .step { padding: 10px 15px; margin: 5px 0; border-left: 3px solid #e94560; background: white; border-radius: 0 4px 4px 0; }
.causal-chain .arrow { text-align: center; color: #e94560; font-size: 1.5em; margin: 2px 0; }
.summary-box { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin: 20px 0; }
.summary-box h3 { color: white; }
.metric { display: inline-block; background: rgba(255,255,255,0.15); padding: 8px 15px; border-radius: 6px; margin: 5px; }
.section-divider { border: none; height: 2px; background: linear-gradient(to right, #e94560, transparent); margin: 30px 0; }
.cmd-ref-label { color: #888; font-size: 0.8em; margin-bottom: 2px; }
ol { padding-left: 24px; }
ol li { margin: 4px 0; }
ul { padding-left: 24px; }
ul li { margin: 4px 0; }
"""


# ============================================================================
# 命令日志管理
# ============================================================================

class CommandLog:
    """管理 crash 命令输出日志（JSONL 格式）"""

    def __init__(self, log_path=None):
        self.log_path = log_path
        self._cache = OrderedDict()  # cmd -> output (保留最后一次执行的结果)
        if log_path and os.path.exists(log_path):
            self._load()

    def _load(self):
        """加载 JSONL 日志文件"""
        with open(self.log_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    cmd = entry.get('cmd', '').strip()
                    output = entry.get('output', '')
                    if cmd:
                        self._cache[cmd] = output
                except json.JSONDecodeError:
                    continue

    # Shell 噪音正则：匹配 crash pipe 命令执行时 shell 产生的函数导入错误
    _SHELL_NOISE_RE = re.compile(
        r'^sh:\s+\S+:\s+line\s+\d+:\s+syntax error.*$|'
        r'^sh:\s+error importing function definition for\s+.*$',
        re.MULTILINE
    )

    @classmethod
    def _strip_shell_noise(cls, output):
        """过滤命令输出中的 shell 噪音（如 bash 函数导入错误）"""
        if not output:
            return output
        cleaned = cls._SHELL_NOISE_RE.sub('', output)
        # 清理多余的连续空行（噪音行被移除后留下的）
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        return cleaned.strip()

    def get(self, cmd, lines=None):
        """获取命令输出，支持行数限制

        Args:
            cmd: crash 命令字符串
            lines: 可选，限制输出行数（从头开始取）

        Returns:
            命令输出字符串，未找到时返回 None
        """
        # 精确匹配
        output = self._cache.get(cmd)

        # 模糊匹配：忽略前后空格和 "crash>" 前缀
        if output is None:
            normalized = cmd.strip()
            if normalized.startswith('crash>'):
                normalized = normalized[6:].strip()
            for cached_cmd, cached_output in self._cache.items():
                cached_normalized = cached_cmd.strip()
                if cached_normalized.startswith('crash>'):
                    cached_normalized = cached_normalized[6:].strip()
                if cached_normalized == normalized:
                    output = cached_output
                    break

        if output is None:
            return None

        # 过滤 shell 噪音
        output = self._strip_shell_noise(output)

        if lines and lines > 0:
            output_lines = output.split('\n')
            if len(output_lines) > lines:
                output = '\n'.join(output_lines[:lines]) + f'\n... (共 {len(output_lines)} 行，已截取前 {lines} 行)'

        return output

    @staticmethod
    def append_entry(log_path, cmd, output):
        """追加一条命令记录到日志文件"""
        os.makedirs(os.path.dirname(log_path) or '.', exist_ok=True)
        entry = {
            'cmd': cmd,
            'output': output,
            'ts': datetime.now().isoformat()
        }
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')


# ============================================================================
# Markdown 解析器
# ============================================================================

def e(text):
    """HTML escape"""
    if text is None:
        return ""
    return escape(str(text))


def render_inline(text):
    """处理行内 Markdown 格式：`code`、**bold**、*italic*"""
    if not text:
        return ""
    # 转义 HTML
    text = e(text)
    # `code` → <code>
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    # **bold** → <strong>
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    # *italic* → <em> (但不匹配已被 ** 处理的)
    text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', text)
    return text


def parse_front_matter(md_text):
    """解析 YAML front matter，返回 (metadata_dict, remaining_text)"""
    if not md_text.startswith('---'):
        return {}, md_text

    end = md_text.find('\n---', 3)
    if end == -1:
        return {}, md_text

    yaml_block = md_text[3:end].strip()
    remaining = md_text[end + 4:].strip()

    # 简单的 key: value 解析（不依赖 PyYAML）
    meta = {}
    for line in yaml_block.split('\n'):
        line = line.strip()
        if ':' in line:
            key, _, value = line.partition(':')
            meta[key.strip()] = value.strip().strip('"').strip("'")

    return meta, remaining


def parse_tags(tag_str):
    """解析标签字符串，如 '[Ubuntu Jammy](blue) [Soft Lockup]()' → list of {text, color}"""
    tags = []
    for m in re.finditer(r'\[([^\]]+)\]\(([^)]*)\)', tag_str):
        tags.append({'text': m.group(1), 'color': m.group(2) or ''})
    return tags


class MarkdownToHtml:
    """Markdown → HTML 转换器，支持命令引用和特殊块"""

    def __init__(self, cmd_log=None):
        self.cmd_log = cmd_log or CommandLog()
        self.html_parts = []

    def convert(self, md_text):
        """将 Markdown 文本转换为 HTML body"""
        _meta, md_text = parse_front_matter(md_text)
        lines = md_text.split('\n')
        self.html_parts = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # 空行
            if not line.strip():
                i += 1
                continue

            # 特殊块 ::: 开始
            if line.strip().startswith(':::'):
                i = self._parse_directive_block(lines, i)
                continue

            # 标题
            heading_match = re.match(r'^(#{1,4})\s+(.+)$', line)
            if heading_match:
                level = len(heading_match.group(1))
                title_text = heading_match.group(2)
                self.html_parts.append(f'<h{level}>{render_inline(title_text)}</h{level}>')
                # h2 后加分隔线（与 v1 一致）
                i += 1
                continue

            # 分隔线
            if re.match(r'^---+\s*$', line):
                self.html_parts.append('<hr class="section-divider">')
                i += 1
                continue

            # 命令引用：@cmd[command] 或 @cmd[command]{lines=N}
            cmd_ref_match = re.match(r'^@cmd\[(.+?)\](?:\{lines=(\d+)\})?\s*$', line.strip())
            if cmd_ref_match:
                i = self._render_cmd_ref(cmd_ref_match, i)
                continue

            # 代码块 ```
            if line.strip().startswith('```'):
                i = self._parse_code_block(lines, i)
                continue

            # 表格
            if '|' in line and i + 1 < len(lines) and re.match(r'^[\s|:-]+$', lines[i + 1]):
                i = self._parse_table(lines, i)
                continue

            # 有序列表
            if re.match(r'^\d+\.\s', line.strip()):
                i = self._parse_ordered_list(lines, i)
                continue

            # 无序列表
            if re.match(r'^[-*+]\s', line.strip()):
                i = self._parse_unordered_list(lines, i)
                continue

            # 普通段落
            i = self._parse_paragraph(lines, i)

        return '\n'.join(self.html_parts)

    def _render_cmd_ref(self, match, i):
        """渲染命令引用"""
        cmd = match.group(1)
        lines_limit = int(match.group(2)) if match.group(2) else None

        output = self.cmd_log.get(cmd, lines=lines_limit)
        if output is not None:
            self.html_parts.append(
                f'<div class="cmd-ref-label">crash&gt; {e(cmd)}</div>'
                f'<pre><code>{e(output)}</code></pre>'
            )
        else:
            # 日志中未找到，显示占位提示
            self.html_parts.append(
                f'<pre><code>crash&gt; {e(cmd)}\n[命令输出未在日志中找到]</code></pre>'
            )
        return i + 1

    def _parse_code_block(self, lines, i):
        """解析 ``` 代码块"""
        opening = lines[i].strip()
        # 提取语言标记（可选）
        _lang = opening[3:].strip()  # noqa: F841 — reserved for future syntax highlighting
        code_lines = []
        i += 1
        while i < len(lines):
            if lines[i].strip().startswith('```'):
                i += 1
                break
            code_lines.append(lines[i])
            i += 1
        code_text = '\n'.join(code_lines)
        self.html_parts.append(f'<pre><code>{e(code_text)}</code></pre>')
        return i

    def _parse_table(self, lines, i):
        """解析 Markdown 表格"""
        # 表头
        header_cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
        i += 1  # 跳过分隔行
        i += 1

        html = '<table>\n<tr>'
        for h in header_cells:
            html += f'<th>{render_inline(h)}</th>'
        html += '</tr>\n'

        # 表体
        while i < len(lines) and '|' in lines[i] and lines[i].strip():
            cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
            html += '<tr>'
            for cell in cells:
                html += f'<td>{render_inline(cell)}</td>'
            html += '</tr>\n'
            i += 1

        html += '</table>'
        self.html_parts.append(html)
        return i

    def _parse_ordered_list(self, lines, i):
        """解析有序列表"""
        html = '<ol>\n'
        while i < len(lines):
            m = re.match(r'^\d+\.\s+(.+)$', lines[i].strip())
            if not m:
                break
            # 检查是否有续行（缩进的行）
            item_text = m.group(1)
            i += 1
            while i < len(lines) and lines[i].startswith('   ') and not re.match(r'^\d+\.\s', lines[i].strip()):
                item_text += '\n' + lines[i].strip()
                i += 1
            html += f'<li>{render_inline(item_text)}</li>\n'
        html += '</ol>'
        self.html_parts.append(html)
        return i

    def _parse_unordered_list(self, lines, i):
        """解析无序列表"""
        html = '<ul>\n'
        while i < len(lines):
            m = re.match(r'^[-*+]\s+(.+)$', lines[i].strip())
            if not m:
                break
            item_text = m.group(1)
            i += 1
            while i < len(lines) and lines[i].startswith('  ') and not re.match(r'^[-*+]\s', lines[i].strip()):
                item_text += '\n' + lines[i].strip()
                i += 1
            html += f'<li>{render_inline(item_text)}</li>\n'
        html += '</ol>' if False else '</ul>'
        self.html_parts.append(html)
        return i

    def _parse_paragraph(self, lines, i):
        """解析段落（连续的非空行）"""
        para_lines = []
        while i < len(lines):
            line = lines[i]
            if not line.strip():
                break
            # 碰到新的块级元素时结束段落
            stripped = line.strip()
            is_block_start = (
                stripped.startswith('#')
                or stripped.startswith('```')
                or stripped.startswith(':::')
                or stripped.startswith('---')
                or re.match(r'^@cmd\[', stripped)
                or (re.match(r'^\d+\.\s', stripped) and not para_lines)
                or (re.match(r'^[-*+]\s', stripped) and not para_lines)
                or (
                    '|' in line
                    and i + 1 < len(lines)
                    and re.match(r'^[\s|:-]+$', lines[i + 1])
                )
            )
            if is_block_start:
                break
            para_lines.append(line)
            i += 1

        if para_lines:
            text = ' '.join(l.strip() for l in para_lines)
            self.html_parts.append(f'<p>{render_inline(text)}</p>')
        return i

    def _parse_directive_block(self, lines, i):
        """解析 ::: 指令块（alert、highlight、causal-chain、summary-box）"""
        opening = lines[i].strip()
        # 解析指令名和参数
        # ::: alert{level=warning}  或  ::: highlight  或  ::: summary-box
        m = re.match(r'^:::\s*(\S+?)(?:\{(.+?)\})?\s*$', opening)
        if not m:
            i += 1
            return i

        directive = m.group(1)
        params_str = m.group(2) or ''
        params = {}
        if params_str:
            for pair in params_str.split(','):
                if '=' in pair:
                    k, _, v = pair.partition('=')
                    params[k.strip()] = v.strip().strip('"').strip("'")

        # 收集块内容
        block_lines = []
        i += 1
        while i < len(lines):
            if lines[i].strip() == ':::':
                i += 1
                break
            block_lines.append(lines[i])
            i += 1

        block_text = '\n'.join(block_lines)

        if directive == 'alert':
            level = params.get('level', 'warning')
            icon = {"alert": "🔴", "warning": "⚠️", "info": "ℹ️", "success": "✅"}.get(level, "")
            title = params.get('title', '')
            title_html = f'<strong>{icon} {e(title)}</strong>' if title else f'{icon}'
            # 块内文本作为正文
            body_html = render_inline(block_text.strip())
            self.html_parts.append(f'<div class="{e(level)}">{title_html} {body_html}</div>')

        elif directive == 'highlight':
            self.html_parts.append(f'<div class="highlight">{render_inline(block_text.strip())}</div>')

        elif directive == 'summary-box':
            # summary-box 内部支持子 Markdown 解析
            inner = MarkdownToHtml(self.cmd_log)
            inner_html = inner.convert(block_text)
            self.html_parts.append(f'<div class="summary-box">{inner_html}</div>')

        elif directive == 'causal-chain':
            self._render_causal_chain(block_text)

        elif directive == 'meta':
            # 元数据块，提取标题行用于报告头部
            meta_html = self._render_meta_block(block_text, params)
            self.html_parts.append(meta_html)

        else:
            # 未知指令，作为普通 div
            inner = MarkdownToHtml(self.cmd_log)
            inner_html = inner.convert(block_text)
            self.html_parts.append(f'<div class="{e(directive)}">{inner_html}</div>')

        return i

    def _render_causal_chain(self, block_text):
        """渲染因果链块"""
        steps = []
        for line in block_text.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
            # 格式：1. **标题**：详情  或  - **标题**：详情
            m = re.match(r'^(?:\d+\.\s+|[-*]\s+)?\*?\*?(.+?)\*?\*?[：:]\s*(.+)$', line)
            if m:
                steps.append({'title': m.group(1).strip('*'), 'detail': m.group(2)})
            else:
                # 没有标题格式，整行作为步骤
                steps.append({'title': '', 'detail': line})

        html = '<div class="causal-chain">\n'
        for idx, step in enumerate(steps):
            num = chr(0x2460 + idx) if idx < 20 else str(idx + 1)
            title_part = f'<strong>{num} {e(step["title"])}</strong>：' if step['title'] else f'<strong>{num}</strong> '
            html += f'<div class="step">{title_part}{render_inline(step["detail"])}</div>\n'
            if idx < len(steps) - 1:
                html += '<div class="arrow">↓</div>\n'
        html += '</div>'
        self.html_parts.append(html)

    def _render_meta_block(self, block_text, params):
        """渲染元数据块为报告头部"""
        meta = {}
        for line in block_text.strip().split('\n'):
            if ':' in line:
                key, _, value = line.partition(':')
                meta[key.strip()] = value.strip()

        report_time = meta.get('report_time', params.get('time', datetime.now().strftime('%Y-%m-%d %H:%M')))
        vmcore_id = meta.get('vmcore_id', params.get('id', 'unknown'))
        tool = meta.get('tool', params.get('tool', 'crash + AiCrasher MCP'))

        return f"""
<h1>🔍 VMCore 深度分析报告</h1>
<p><strong>分析时间</strong>: {e(report_time)} &nbsp;|&nbsp;
   <strong>VMCore ID</strong>: {e(vmcore_id)} &nbsp;|&nbsp;
   <strong>分析工具</strong>: {e(tool)}</p>
"""


# ============================================================================
# 主渲染函数
# ============================================================================

def render_report(md_text, cmd_log=None):
    """将 Markdown 文本渲染为完整 HTML 报告"""
    converter = MarkdownToHtml(cmd_log)
    body_html = converter.convert(md_text)

    # 从 front matter 提取 vmcore_id 用于标题
    meta, _ = parse_front_matter(md_text)
    vmcore_id = meta.get('vmcore_id', '')

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VMCore 分析报告 - {e(vmcore_id)}</title>
<style>
{CSS_STYLES}
</style>
</head>
<body>
<div class="container">
{body_html}
</div>
</body>
</html>
"""


# ============================================================================
# Markdown 格式说明文档
# ============================================================================

FORMAT_HELP = r"""
Markdown 报告格式说明 (v2)
==========================

## 基本结构

报告使用标准 Markdown 格式，带可选的 YAML front matter：

```markdown
---
vmcore_id: "16330271/ins-dehdympf"
report_time: "2026-03-19 17:22"
tool: "crash + AiCrasher MCP"
---

::: meta
report_time: 2026-03-19 17:22
vmcore_id: 16330271/ins-dehdympf
tool: crash + AiCrasher MCP
:::

# 🔍 VMCore 深度分析报告

## 一、基本信息

| 项目 | 详情 |
|------|------|
| 内核版本 | `5.15.0-151-generic` |
| Panic 类型 | Soft Lockup |

## 二、问题摘要

::: summary-box
### 🎯 核心结论
系统发生了 soft lockup...
:::

## 三、分析过程

### 3.1 基线收集

通过 `analyze_crash` 创建调试会话并收集基线诊断信息。

@cmd[sys]

从 `sys` 输出确认：256 核 KVM 虚拟机...

@cmd[bt]

### 3.2 全局 CPU 状态扫描

| 关键函数 | 出现行数 | 含义 |
|---------|---------|------|
| `native_flush_tlb_multi` | 32 | 32 个 CPU 卡在 TLB flush |

::: highlight
32 个 CPU 卡在 `native_flush_tlb_multi`
:::

## 四、根因分析

::: alert{level=alert}
**根因**：256 核 KVM 大规格虚拟机上 TLB flush IPI 连锁阻塞
:::

::: causal-chain
1. **业务触发**：约 31 个 python3 进程通过 madvise() 请求 THP
2. **同步 Compaction**：defrag=madvise 直接在进程上下文执行规整
3. **TLB Flush IPI 风暴**：大量并发 compaction 产生 IPI 风暴
:::

## 七、推荐方案

::: alert{level=info}
建议将 THP defrag 从 madvise 调整为 defer
:::
```

## 命令引用语法

### 基本引用
引用 crash 命令日志中的输出（避免重复输出已有内容）：

    @cmd[sys]
    @cmd[bt]
    @cmd[bt -a | grep -c native_flush_tlb_multi]

### 限制行数
只显示前 N 行：

    @cmd[log | tail -n 100]{lines=20}
    @cmd[bt -a]{lines=50}

## 特殊块语法

### 提示框
    ::: alert{level=warning,title=关键异常}
    这是警告内容
    :::

    level 可选值: alert(红), warning(黄), info(蓝), success(绿)

### 高亮块
    ::: highlight
    32 个 CPU 卡在 `native_flush_tlb_multi`
    :::

### 摘要框
    ::: summary-box
    ### 🎯 核心结论
    内容...
    :::

### 因果链
    ::: causal-chain
    1. **业务触发**：描述...
    2. **连锁阻塞**：描述...
    :::

### 元数据块
    ::: meta
    report_time: 2026-03-19 17:22
    vmcore_id: 16330271/ins-dehdympf
    :::

## 优势

| 特性 | 说明 |
|-----|------|
| 格式 | 标准 Markdown，直接可读 |
| 命令输出 | @cmd[] 引用 MCP 自动记录的日志，零额外 AI token |
| AI 输出量 | ~3,300 tokens（相比直接嵌入命令输出节省 ~50%+） |
| 灵活性 | 自由格式，支持丰富的特殊块语法 |

## 注意事项

1. 所有文本自动 HTML escape，防止 XSS
2. `backtick` 标记会渲染为 `<code>` 标签
3. **bold** 和 *italic* 格式均支持
4. 表格必须有分隔行（---|---）
5. @cmd[] 必须独占一行
6. ::: 指令块的结束标记 ::: 也必须独占一行
"""


# ============================================================================
# CLI 入口
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="VMCore 分析报告生成器：Markdown + 命令引用 → HTML",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  # 生成报告（crash_cmd_log_TIME.jsonl 由 MCP 服务端自动生成）\n"
            "  python3 crash_report_generator.py -i report.md -l crash_cmd_log_TIME.jsonl -o report.html\n\n"
            "  # 手动记录命令输出（仅在 MCP 自动日志不可用时使用）\n"
            "  python3 crash_report_generator.py --log-cmd crash_cmd_log_TIME.jsonl --cmd 'sys' --output '...'\n\n"
            "  # 查看格式说明\n"
            "  python3 crash_report_generator.py --format-help\n"
        )
    )

    # 报告生成参数
    parser.add_argument("-i", "--input", help="输入 Markdown 文件路径")
    parser.add_argument("-o", "--output", help="输出 HTML 文件路径")
    parser.add_argument("-l", "--log", help="crash 命令日志文件路径 (JSONL 格式)")

    # 命令日志记录参数
    parser.add_argument("--log-cmd", help="追加命令记录到指定日志文件")
    parser.add_argument("--cmd", help="要记录的 crash 命令")
    parser.add_argument("--cmd-output", dest="cmd_output_text", help="命令的输出内容")

    # 帮助
    parser.add_argument("--format-help", action="store_true", help="显示 Markdown 格式说明")

    args = parser.parse_args()

    # 显示格式说明
    if args.format_help:
        print(FORMAT_HELP)
        return

    # 命令日志记录模式
    if args.log_cmd and args.cmd:
        output_text = args.cmd_output_text or ''
        # 也支持从 stdin 读取
        if not output_text and not sys.stdin.isatty():
            output_text = sys.stdin.read()
        CommandLog.append_entry(args.log_cmd, args.cmd, output_text)
        print(f"✅ 已记录命令: {args.cmd} ({len(output_text)} chars)")
        return

    # 报告生成模式
    if not args.input:
        parser.print_help()
        sys.exit(1)

    input_path = os.path.abspath(args.input)
    if not os.path.exists(input_path):
        print(f"错误：输入文件不存在: {input_path}", file=sys.stderr)
        sys.exit(1)

    # 加载命令日志
    cmd_log = CommandLog(args.log if args.log else None)

    # 读取 Markdown
    with open(input_path, 'r', encoding='utf-8') as f:
        md_text = f.read()

    # 确定输出路径
    if args.output:
        output_path = os.path.abspath(args.output)
    else:
        input_dir = os.path.dirname(input_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        output_path = os.path.join(input_dir, f"crash_report_{timestamp}.html")

    # 渲染并写入
    html = render_report(md_text, cmd_log)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    # 统计命令引用
    cmd_refs = re.findall(r'@cmd\[(.+?)\]', md_text)
    resolved = sum(1 for c in cmd_refs if cmd_log.get(c) is not None)

    file_size = os.path.getsize(output_path)
    md_size = os.path.getsize(input_path)
    print(f"✅ 报告已生成: {output_path}")
    print(f"   Markdown 输入: {md_size:,} bytes")
    print(f"   HTML 输出: {file_size:,} bytes")
    print(f"   放大比率: {file_size / md_size:.1f}x")
    if cmd_refs:
        print(f"   命令引用: {len(cmd_refs)} 个 (已填充 {resolved}, 未找到 {len(cmd_refs) - resolved})")


if __name__ == "__main__":
    main()
