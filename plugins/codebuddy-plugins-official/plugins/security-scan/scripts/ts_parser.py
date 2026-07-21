#!/usr/bin/env python3
"""
AST 解析工具（双引擎：tree-sitter 优先 + 内置正则 fallback）

多语言代码结构分析工具。优先使用 tree-sitter 进行精确 AST 解析，
tree-sitter 不可用时自动降级为内置正则解析器，保证流水线不中断。

用途：
  1. check               — 检查解析器可用性（tree-sitter / fallback）
  2. setup               — 引导安装 tree-sitter + 语言包（初始化阶段调用）
  3. refine-sinks         — 精化 Sink 定位（验证 Grep 粗定位结果，提取完整调用上下文）
  4. persist              — 批量解析并持久化到 project-index.db（深度探索阶段）
  5. cached-query         — 从 project-index.db 查询缓存的 AST 结果

依赖：
  - 核心：无（纯 Python 标准库即可运行）
  - 增强：pip install tree-sitter tree-sitter-languages（精确 AST，setup 命令引导安装）

设计原则：
  - tree-sitter 优先：完整 AST 解析，处理多行参数、嵌套泛型、链式调用等复杂场景
  - 内置 fallback：tree-sitter 不可用时自动降级，保证流水线不中断
  - 一次解析、多次查询：persist 命令将结果持久化到 SQLite，后续阶段直接查库
  - 毫秒级解析，适合 Agent 编排的 CLI 调用模式
  - 输出 JSON，供 index_db.py write 直接消费
"""

import argparse
import hashlib
import importlib
import json
import os
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


# ─── 语言映射 ──────────────────────────────────────────────

LANG_EXT_MAP = {
    ".java": "java",
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".mts": "typescript",
    ".cts": "typescript",
    ".go": "go",
    ".php": "php",
    ".rb": "ruby",
    ".rs": "rust",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".cs": "c_sharp",
    ".swift": "swift",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".vue": "javascript",
}


def _detect_language(file_path):
    """根据文件扩展名检测语言"""
    ext = Path(file_path).suffix.lower()
    return LANG_EXT_MAP.get(ext)


# ═══════════════════════════════════════════════════════════
# Tree-sitter 引擎（精确模式）
# ═══════════════════════════════════════════════════════════

_ts_available = None   # None = 未检测, True/False = 检测结果
_ts_languages = {}     # lang_name -> Language object


def _check_tree_sitter():
    """检测 tree-sitter 是否可用，缓存结果"""
    global _ts_available, _ts_languages
    if _ts_available is not None:
        return _ts_available
    try:
        from tree_sitter import Parser  # noqa: F401
        _ts_available = True
    except ImportError:
        _ts_available = False
        return False

    # 方式1: tree-sitter-languages 合集包
    try:
        from tree_sitter_languages import get_language  # noqa: F401
        for our_name in ("java", "python", "javascript", "typescript", "tsx",
                         "go", "php", "ruby", "rust", "c", "cpp", "c_sharp",
                         "swift", "kotlin"):
            try:
                _ts_languages[our_name] = get_language(our_name)
            except Exception:
                pass
        if _ts_languages:
            return True
    except ImportError:
        pass

    # 方式2: 各语言独立包
    _mod_map = {
        "python": "tree_sitter_python", "java": "tree_sitter_java",
        "javascript": "tree_sitter_javascript", "typescript": "tree_sitter_typescript",
        "tsx": "tree_sitter_typescript", "go": "tree_sitter_go",
        "php": "tree_sitter_php", "ruby": "tree_sitter_ruby",
        "rust": "tree_sitter_rust", "c": "tree_sitter_c",
        "cpp": "tree_sitter_cpp", "c_sharp": "tree_sitter_c_sharp",
        "swift": "tree_sitter_swift", "kotlin": "tree_sitter_kotlin",
    }
    for our_name, mod_name in _mod_map.items():
        try:
            mod = importlib.import_module(mod_name)
            if hasattr(mod, 'language'):
                from tree_sitter import Language
                _ts_languages[our_name] = Language(mod.language())
            elif hasattr(mod, 'LANGUAGE'):
                _ts_languages[our_name] = mod.LANGUAGE
        except Exception:
            pass

    if not _ts_languages:
        _ts_available = False
    return _ts_available


def _get_ts_parser(lang):
    """获取配置好语言的 tree-sitter Parser，失败返回 None"""
    if not _check_tree_sitter() or lang not in _ts_languages:
        return None
    try:
        try:
            from tree_sitter_languages import get_parser
            return get_parser(lang)
        except (ImportError, Exception):
            pass
        from tree_sitter import Parser
        p = Parser()
        p.language = _ts_languages[lang]
        return p
    except Exception:
        return None


def _ts_extract_functions(source_bytes, parser, lang):
    """使用 tree-sitter 提取函数签名"""
    tree = parser.parse(source_bytes)
    functions = []
    _FUNC_TYPES = {
        "python": ("function_definition",), "java": ("method_declaration", "constructor_declaration"),
        "javascript": ("function_declaration", "method_definition", "arrow_function"),
        "typescript": ("function_declaration", "method_definition", "arrow_function"),
        "tsx": ("function_declaration", "method_definition", "arrow_function"),
        "go": ("function_declaration", "method_declaration"),
        "php": ("function_definition", "method_declaration"),
        "ruby": ("method", "singleton_method"), "rust": ("function_item",),
        "c": ("function_definition",), "cpp": ("function_definition",),
        "c_sharp": ("method_declaration", "constructor_declaration"),
        "swift": ("function_declaration",), "kotlin": ("function_declaration",),
    }
    target_types = set(_FUNC_TYPES.get(lang, ("function_definition",)))

    def walk(node, cls=None):
        cur_cls = cls
        if node.type in ("class_declaration", "class_definition", "class_specifier",
                         "interface_declaration", "struct_item"):
            for ch in node.children:
                if ch.type in ("identifier", "name", "type_identifier"):
                    cur_cls = ch.text.decode('utf-8', errors='replace')
                    break

        if node.type in target_types:
            info = _ts_func_info(node, lang, source_bytes, cur_cls)
            if info:
                functions.append(info)

        for ch in node.children:
            walk(ch, cur_cls)

    walk(tree.root_node)
    return functions


def _ts_func_info(node, lang, source_bytes, cls):
    """从 tree-sitter 节点提取函数信息"""
    name = params = ret = None
    mods, annots = [], []
    for ch in node.children:
        t = ch.text.decode('utf-8', errors='replace') if ch.text else ""
        if ch.type in ("identifier", "name", "property_identifier") and name is None:
            name = t
        elif ch.type in ("parameters", "formal_parameters", "parameter_list",
                         "method_parameters", "function_parameters"):
            params = t
        elif ch.type in ("type", "return_type", "type_annotation", "simple_type", "generic_type"):
            ret = t
        elif ch.type in ("modifiers", "modifier"):
            mods.extend(t.split())
        elif ch.type in ("decorator", "annotation", "marker_annotation"):
            annots.append(t)
    if name is None and node.type == "arrow_function" and node.parent:
        for sib in node.parent.children:
            if sib.type in ("identifier", "property_identifier"):
                name = sib.text.decode('utf-8', errors='replace')
                break
    if name is None:
        return None
    return {
        "name": name, "class": cls, "params": params or "()",
        "returnType": ret, "modifiers": mods or None, "annotations": annots or None,
        "startLine": node.start_point[0] + 1, "endLine": node.end_point[0] + 1,
    }


def _ts_extract_calls(source_bytes, parser, lang, filter_callee=None):
    """使用 tree-sitter 提取调用表达式"""
    tree = parser.parse(source_bytes)
    calls, seen = [], set()

    def walk(node):
        if node.type in ("call_expression", "method_invocation", "function_call"):
            info = _ts_call_info(node, source_bytes)
            if info:
                key = (info["callee"], info["line"])
                if key not in seen:
                    seen.add(key)
                    if filter_callee is None or filter_callee.lower() in info["callee"].lower():
                        calls.append(info)
        for ch in node.children:
            walk(ch)

    walk(tree.root_node)
    return calls


def _ts_call_info(node, source_bytes):
    """从 tree-sitter 调用节点提取信息"""
    callee = receiver = args = None
    full = node.text.decode('utf-8', errors='replace')[:200]
    for ch in node.children:
        if ch.type in ("argument_list", "arguments"):
            args = ch.text.decode('utf-8', errors='replace')
        elif ch.type in ("member_expression", "field_expression", "field_access"):
            callee = ch.text.decode('utf-8', errors='replace')
            parts = callee.rsplit('.', 1)
            if len(parts) == 2:
                receiver = parts[0]
        elif ch.type in ("identifier", "property_identifier", "name") and callee is None:
            callee = ch.text.decode('utf-8', errors='replace')
    if callee is None:
        idx = full.find('(')
        callee = full[:idx].strip() if idx > 0 else None
    if callee is None:
        return None
    base = callee.split('.')[-1] if '.' in callee else callee
    if base in _CALL_EXCLUDE_KEYWORDS:
        return None
    return {"callee": callee, "receiver": receiver, "args": args or "()",
            "line": node.start_point[0] + 1, "fullExpression": full}


# ═══════════════════════════════════════════════════════════
# 内置正则解析器（Fallback 模式）
# ═══════════════════════════════════════════════════════════
#
# 解析策略：
#   1. 预处理：剥离字符串字面量和注释，避免误匹配
#   2. 正则 + 状态机提取函数签名、调用表达式
#   3. 花括号/缩进匹配确定作用域边界
# ═══════════════════════════════════════════════════════════


class SourcePreprocessor:
    """源码预处理器：标记字符串和注释区域，返回 clean source 和区域映射"""

    @staticmethod
    def preprocess(source, lang):
        """
        返回 (cleaned_source, regions)
        - cleaned_source: 将字符串内容和注释替换为空格（保持行号和偏移量对齐）
        - regions: [(start, end, type)] 类型为 'string' 或 'comment'
        """
        regions = []
        cleaned = list(source)  # 可变字符列表
        i = 0
        n = len(source)

        while i < n:
            # 单行注释
            if source[i:i+2] == '//' and lang != 'python':
                start = i
                while i < n and source[i] != '\n':
                    cleaned[i] = ' '
                    i += 1
                regions.append((start, i, 'comment'))
                continue

            # Python 注释
            if source[i] == '#' and lang == 'python':
                start = i
                while i < n and source[i] != '\n':
                    cleaned[i] = ' '
                    i += 1
                regions.append((start, i, 'comment'))
                continue

            # 多行注释 /* ... */
            if source[i:i+2] == '/*':
                start = i
                i += 2
                while i < n - 1 and source[i:i+2] != '*/':
                    if source[i] != '\n':
                        cleaned[i] = ' '
                    i += 1
                if i < n - 1:
                    cleaned[i] = ' '
                    cleaned[i+1] = ' '
                    i += 2
                cleaned[start] = ' '
                cleaned[start+1] = ' '
                regions.append((start, i, 'comment'))
                continue

            # Python 三引号字符串
            if lang == 'python' and (source[i:i+3] in ('"""', "'''")):
                quote = source[i:i+3]
                start = i
                i += 3
                while i < n - 2 and source[i:i+3] != quote:
                    if source[i] != '\n':
                        cleaned[i] = ' '
                    i += 1
                if i < n - 2:
                    for j in range(3):
                        cleaned[i+j] = ' '
                    i += 3
                for j in range(3):
                    if start + j < n:
                        cleaned[start+j] = ' '
                regions.append((start, i, 'string'))
                continue

            # 字符串字面量（单引号、双引号、反引号模板字符串）
            if source[i] in ('"', "'", '`'):
                quote_char = source[i]
                start = i
                cleaned[i] = ' '
                i += 1
                while i < n:
                    if source[i] == '\\':
                        cleaned[i] = ' '
                        i += 1
                        if i < n:
                            cleaned[i] = ' '
                            i += 1
                        continue
                    if source[i] == quote_char:
                        cleaned[i] = ' '
                        i += 1
                        break
                    if source[i] == '\n' and quote_char != '`':
                        break
                    if source[i] != '\n':
                        cleaned[i] = ' '
                    i += 1
                regions.append((start, i, 'string'))
                continue

            i += 1

        return ''.join(cleaned), regions

    @staticmethod
    def is_in_string_or_comment(offset, regions):
        """检查偏移量是否在字符串或注释区域内"""
        for start, end, _ in regions:
            if start <= offset < end:
                return True
        return False


# ─── 花括号匹配器 ──────────────────────────────────────────

def _find_matching_brace(source, open_pos):
    """找到匹配的右花括号位置（跳过字符串和注释中的花括号）"""
    depth = 0
    i = open_pos
    n = len(source)
    while i < n:
        if source[i] == '{':
            depth += 1
        elif source[i] == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def _offset_to_line(source, offset):
    """偏移量转行号（1-based）"""
    return source[:offset].count('\n') + 1


def _line_to_offset(source, line_1based):
    """行号（1-based）转该行起始偏移量"""
    line_num = 0
    for i, c in enumerate(source):
        if line_num == line_1based - 1:
            return i
        if c == '\n':
            line_num += 1
    return len(source)


# ─── 函数提取 ──────────────────────────────────────────────

# 各语言的函数匹配正则
_FUNC_PATTERNS = {}


def _build_func_patterns():
    """构建各语言的函数匹配正则表达式"""
    if _FUNC_PATTERNS:
        return

    # Java / C# / Kotlin 方法
    _FUNC_PATTERNS["java"] = re.compile(
        r'(?P<annots>(?:\s*@\w+(?:\([^)]*\))?)*)\s*'  # 注解
        r'(?P<mods>(?:(?:public|private|protected|static|final|abstract|synchronized|native|default|override)\s+)*)'  # 修饰符
        r'(?P<ret>[\w<>\[\]?,.\s]+?)\s+'  # 返回类型
        r'(?P<name>\w+)\s*'  # 方法名
        r'(?P<params>\([^)]*\))\s*'  # 参数列表
        r'(?:throws\s+[\w,.\s]+\s*)?'  # throws
        r'(?=\{)',  # 后跟 {
        re.MULTILINE
    )
    _FUNC_PATTERNS["c_sharp"] = _FUNC_PATTERNS["java"]

    # Java / C# 构造函数
    _FUNC_PATTERNS["java_ctor"] = re.compile(
        r'(?P<annots>(?:\s*@\w+(?:\([^)]*\))?)*)\s*'
        r'(?P<mods>(?:(?:public|private|protected)\s+)*)'
        r'(?P<name>[A-Z]\w*)\s*'
        r'(?P<params>\([^)]*\))\s*'
        r'(?:throws\s+[\w,.\s]+\s*)?'
        r'(?=\{)',
        re.MULTILINE
    )

    # Python
    _FUNC_PATTERNS["python"] = re.compile(
        r'(?P<decorators>(?:\s*@[\w.]+(?:\([^)]*\))?\s*\n)*)'  # 装饰器
        r'^(?P<indent>\s*)'  # 缩进
        r'(?:async\s+)?def\s+'  # def / async def
        r'(?P<name>\w+)\s*'  # 函数名
        r'(?P<params>\([^)]*\))\s*'  # 参数
        r'(?:->\s*(?P<ret>[^:]+))?\s*:',  # 返回类型
        re.MULTILINE
    )

    # JavaScript / TypeScript
    _FUNC_PATTERNS["javascript"] = re.compile(
        r'(?:'
        r'(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s*(?P<name1>\w+)?\s*(?P<params1>\([^)]*\))'
        r'|'
        r'(?:(?:export\s+)?(?:const|let|var)\s+)?(?P<name2>\w+)\s*[=:]\s*(?:async\s+)?(?:\([^)]*\)|(?P<params2a>\w+))\s*(?::\s*[\w<>\[\]|&,.\s]+\s*)?=>'
        r'|'
        r'(?P<name3>\w+)\s*(?P<params3>\([^)]*\))\s*(?::\s*[\w<>\[\]|&,.\s]+\s*)?\{'
        r')',
        re.MULTILINE
    )
    _FUNC_PATTERNS["typescript"] = _FUNC_PATTERNS["javascript"]
    _FUNC_PATTERNS["tsx"] = _FUNC_PATTERNS["javascript"]

    # Go
    _FUNC_PATTERNS["go"] = re.compile(
        r'^func\s+'
        r'(?:\((?P<recv>[^)]+)\)\s+)?'  # 接收器
        r'(?P<name>\w+)\s*'
        r'(?P<params>\([^)]*\))\s*'
        r'(?P<ret>[^{]*?)\s*\{',
        re.MULTILINE
    )

    # PHP
    _FUNC_PATTERNS["php"] = re.compile(
        r'(?P<mods>(?:(?:public|private|protected|static|abstract|final)\s+)*)'
        r'function\s+'
        r'(?P<name>\w+)\s*'
        r'(?P<params>\([^)]*\))\s*'
        r'(?::\s*(?P<ret>[\w?|\\]+)\s*)?'
        r'(?=\{)',
        re.MULTILINE
    )

    # Ruby
    _FUNC_PATTERNS["ruby"] = re.compile(
        r'^(?P<indent>\s*)'
        r'def\s+'
        r'(?:self\.)?'
        r'(?P<name>\w+[?!=]?)\s*'
        r'(?P<params>\([^)]*\))?\s*$',
        re.MULTILINE
    )

    # Rust
    _FUNC_PATTERNS["rust"] = re.compile(
        r'(?P<attrs>(?:\s*#\[[\w(,="\s]+\]\s*)*)'
        r'(?P<mods>(?:(?:pub(?:\([^)]*\))?|async|const|unsafe|extern\s*"[^"]*")\s+)*)'
        r'fn\s+'
        r'(?P<name>\w+)\s*'
        r'(?:<[^>]*>\s*)?'  # 泛型
        r'(?P<params>\([^)]*\))\s*'
        r'(?:->\s*(?P<ret>[^{]+?)\s*)?'
        r'(?:where\s+[^{]+?\s*)?'
        r'(?=\{)',
        re.MULTILINE
    )

    # C / C++
    _FUNC_PATTERNS["c"] = re.compile(
        r'^(?P<ret>[\w*\s]+?)\s+'
        r'(?P<name>\w+)\s*'
        r'(?P<params>\([^)]*\))\s*'
        r'(?=\{)',
        re.MULTILINE
    )
    _FUNC_PATTERNS["cpp"] = re.compile(
        r'(?:(?:virtual|static|inline|explicit|override|const|constexpr|noexcept|template\s*<[^>]*>)\s+)*'
        r'(?P<ret>[\w*&:<>,\s]+?)\s+'
        r'(?P<name>(?:\w+::)*\w+)\s*'
        r'(?P<params>\([^)]*\))\s*'
        r'(?:const\s*)?'
        r'(?:override\s*)?'
        r'(?:noexcept\s*)?'
        r'(?=\{)',
        re.MULTILINE
    )

    # Swift
    _FUNC_PATTERNS["swift"] = re.compile(
        r'(?P<attrs>(?:\s*@\w+(?:\([^)]*\))?\s*)*)'
        r'(?P<mods>(?:(?:public|private|internal|fileprivate|open|static|class|override|mutating|final)\s+)*)'
        r'func\s+'
        r'(?P<name>\w+)\s*'
        r'(?:<[^>]*>\s*)?'
        r'(?P<params>\([^)]*\))\s*'
        r'(?:(?:throws|rethrows)\s+)?'
        r'(?:->\s*(?P<ret>[^{]+?)\s*)?'
        r'(?=\{)',
        re.MULTILINE
    )

    # Kotlin
    _FUNC_PATTERNS["kotlin"] = re.compile(
        r'(?P<annots>(?:\s*@\w+(?:\([^)]*\))?\s*)*)'
        r'(?P<mods>(?:(?:public|private|protected|internal|open|abstract|override|final|suspend|inline|operator|infix)\s+)*)'
        r'fun\s+'
        r'(?:<[^>]*>\s*)?'  # 泛型
        r'(?:[\w.]+\.\s*)?'  # 扩展函数接收器
        r'(?P<name>\w+)\s*'
        r'(?P<params>\([^)]*\))\s*'
        r'(?::\s*(?P<ret>[^{=]+?)\s*)?'
        r'(?=[{=])',
        re.MULTILINE
    )


def _fb_extract_functions(source, cleaned, regions, lang):
    """Fallback：从源码中提取函数/方法签名"""
    _build_func_patterns()
    functions = []

    if lang == "python":
        functions = _extract_python_functions(source, cleaned, regions)
    elif lang in ("java", "c_sharp"):
        functions = _extract_brace_lang_functions(source, cleaned, regions, lang)
    elif lang in ("javascript", "typescript", "tsx"):
        functions = _extract_js_functions(source, cleaned, regions, lang)
    elif lang in _FUNC_PATTERNS:
        functions = _extract_generic_functions(source, cleaned, regions, lang)

    return functions


def _extract_python_functions(source, cleaned, regions):
    """Python 函数提取（基于缩进的作用域）"""
    pattern = _FUNC_PATTERNS["python"]
    functions = []
    lines = source.split('\n')

    for m in pattern.finditer(cleaned):
        if SourcePreprocessor.is_in_string_or_comment(m.start(), regions):
            continue

        name = m.group("name")
        params = m.group("params")
        ret = m.group("ret")
        decorators_text = m.group("decorators").strip()

        # def 行号（用匹配末尾 : 的位置定位，因为 m.start() 可能包含装饰器/空行）
        def_line = _offset_to_line(source, m.end() - 1)  # 1-based, 指向 def 行的冒号
        start_line = def_line
        if decorators_text:
            dec_lines = decorators_text.count('\n') + 1
            start_line = def_line - dec_lines

        # 从原始源码 def 行计算缩进（正则的 indent 组可能因装饰器匹配偏移不准）
        def_line_text = lines[def_line - 1] if def_line - 1 < len(lines) else ""
        func_indent_len = len(def_line_text) - len(def_line_text.lstrip())
        end_line = def_line
        for i in range(def_line, len(lines)):  # 0-based index = def_line 即 def 行下一行
            line = lines[i]
            stripped = line.lstrip()
            if stripped == '' or stripped.startswith('#'):
                continue
            line_indent = len(line) - len(stripped)
            if line_indent <= func_indent_len and stripped:
                # 检查是否是装饰器或 else/elif/except/finally（不算结束）
                if not stripped.startswith(('@', 'else', 'elif', 'except', 'finally')):
                    break
            end_line = i + 1

        # 解析装饰器
        annotations = []
        if decorators_text:
            annotations = [d.strip() for d in decorators_text.split('\n') if d.strip()]

        # 检查是否属于某个类
        class_name = _find_python_class_at(lines, start_line - 1, func_indent_len)

        functions.append({
            "name": name,
            "class": class_name,
            "params": params,
            "returnType": ret.strip() if ret else None,
            "modifiers": None,
            "annotations": annotations if annotations else None,
            "startLine": start_line,
            "endLine": end_line,
        })

    return functions


def _find_python_class_at(lines, func_line_idx, func_indent):
    """查找 Python 函数所属的类"""
    if func_indent == 0:
        return None
    for i in range(func_line_idx - 1, -1, -1):
        line = lines[i]
        stripped = line.lstrip()
        if not stripped or stripped.startswith('#'):
            continue
        line_indent = len(line) - len(stripped)
        if line_indent < func_indent and stripped.startswith('class '):
            match = re.match(r'class\s+(\w+)', stripped)
            if match:
                return match.group(1)
            break
        if line_indent < func_indent:
            break
    return None


def _extract_brace_lang_functions(source, cleaned, regions, lang):
    """花括号语言（Java, C#）函数提取"""
    functions = []
    pattern = _FUNC_PATTERNS.get(lang)
    ctor_pattern = _FUNC_PATTERNS.get("java_ctor")

    # 先找类定义（用于关联方法）
    classes = _find_class_declarations(cleaned, regions, lang)

    for m in pattern.finditer(cleaned):
        if SourcePreprocessor.is_in_string_or_comment(m.start(), regions):
            continue

        name = m.group("name")
        params = m.group("params")
        ret_raw = m.group("ret").strip() if m.group("ret") else None
        mods_raw = m.group("mods").strip() if m.group("mods") else ""
        annots_raw = m.group("annots").strip() if m.group("annots") else ""

        # 排除控制流关键字（if/while/for/switch/catch 等误匹配）
        if name in ("if", "else", "while", "for", "switch", "catch", "try",
                     "return", "new", "throw", "class", "interface", "enum"):
            continue

        # 排除返回类型为控制流关键字的
        if ret_raw and ret_raw in ("if", "else", "while", "for", "switch", "class"):
            continue

        start_line = _offset_to_line(source, m.start())

        # 查找函数体结束（匹配花括号）
        brace_pos = source.find('{', m.end() - 1)
        end_line = start_line
        if brace_pos >= 0:
            close = _find_matching_brace(cleaned, brace_pos)
            if close >= 0:
                end_line = _offset_to_line(source, close)

        # 解析修饰符
        modifiers = mods_raw.split() if mods_raw else None

        # 解析注解
        annotations = None
        if annots_raw:
            annotations = re.findall(r'@\w+(?:\([^)]*\))?', annots_raw)

        # 查找所属类
        class_name = _find_class_for_offset(classes, m.start())

        functions.append({
            "name": name,
            "class": class_name,
            "params": params,
            "returnType": ret_raw,
            "modifiers": modifiers,
            "annotations": annotations,
            "startLine": start_line,
            "endLine": end_line,
        })

    # 构造函数
    if ctor_pattern:
        for m in ctor_pattern.finditer(cleaned):
            if SourcePreprocessor.is_in_string_or_comment(m.start(), regions):
                continue
            name = m.group("name")
            # 确认是构造函数（名称首字母大写且是某个类名）
            class_name = _find_class_for_offset(classes, m.start())
            if class_name and name == class_name:
                start_line = _offset_to_line(source, m.start())
                brace_pos = source.find('{', m.end() - 1)
                end_line = start_line
                if brace_pos >= 0:
                    close = _find_matching_brace(cleaned, brace_pos)
                    if close >= 0:
                        end_line = _offset_to_line(source, close)

                mods_raw = m.group("mods").strip() if m.group("mods") else ""
                annots_raw = m.group("annots").strip() if m.group("annots") else ""

                functions.append({
                    "name": name,
                    "class": class_name,
                    "params": m.group("params"),
                    "returnType": None,
                    "modifiers": mods_raw.split() if mods_raw else None,
                    "annotations": re.findall(r'@\w+(?:\([^)]*\))?', annots_raw) if annots_raw else None,
                    "startLine": start_line,
                    "endLine": end_line,
                })

    # 按行号排序去重
    seen = set()
    unique = []
    for f in sorted(functions, key=lambda x: x["startLine"]):
        key = (f["name"], f["startLine"])
        if key not in seen:
            seen.add(key)
            unique.append(f)

    return unique


def _extract_js_functions(source, cleaned, regions, lang):
    """JavaScript / TypeScript 函数提取"""
    functions = []

    # 策略 1: function 声明
    func_decl_pattern = re.compile(
        r'(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s*(\w+)?\s*(\([^)]*\))',
        re.MULTILINE
    )
    for m in func_decl_pattern.finditer(cleaned):
        if SourcePreprocessor.is_in_string_or_comment(m.start(), regions):
            continue
        name = m.group(1) or "<anonymous>"
        params = m.group(2)
        start_line = _offset_to_line(source, m.start())
        brace_pos = cleaned.find('{', m.end())
        end_line = start_line
        if brace_pos >= 0 and brace_pos - m.end() < 50:
            close = _find_matching_brace(cleaned, brace_pos)
            if close >= 0:
                end_line = _offset_to_line(source, close)

        functions.append({
            "name": name,
            "class": None,
            "params": params,
            "returnType": None,
            "modifiers": None,
            "annotations": None,
            "startLine": start_line,
            "endLine": end_line,
        })

    # 策略 2: 箭头函数 / 变量赋值函数
    arrow_pattern = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*[=:]\s*(?:async\s+)?'
        r'(\([^)]*\)|\w+)\s*'
        r'(?::\s*[\w<>\[\]|&,.()\s]+?\s*)?'
        r'=>',
        re.MULTILINE
    )
    for m in arrow_pattern.finditer(cleaned):
        if SourcePreprocessor.is_in_string_or_comment(m.start(), regions):
            continue
        name = m.group(1)
        params = m.group(2) if m.group(2).startswith('(') else f"({m.group(2)})"
        start_line = _offset_to_line(source, m.start())

        # 箭头函数体可能是表达式或花括号块
        after_arrow = cleaned[m.end():m.end()+200].lstrip()
        end_line = start_line
        if after_arrow.startswith('{'):
            brace_pos = cleaned.find('{', m.end())
            if brace_pos >= 0:
                close = _find_matching_brace(cleaned, brace_pos)
                if close >= 0:
                    end_line = _offset_to_line(source, close)
        else:
            # 表达式体，找到分号或换行
            semi = cleaned.find(';', m.end())
            if semi >= 0:
                end_line = _offset_to_line(source, semi)

        functions.append({
            "name": name,
            "class": None,
            "params": params,
            "returnType": None,
            "modifiers": None,
            "annotations": None,
            "startLine": start_line,
            "endLine": end_line,
        })

    # 策略 3: 类方法（class 内的 method）
    method_pattern = re.compile(
        r'(?:(?:public|private|protected|static|async|get|set|readonly|abstract|override)\s+)*'
        r'(\w+)\s*(\([^)]*\))\s*'
        r'(?::\s*[\w<>\[\]|&,.()\s]+?\s*)?'
        r'\{',
        re.MULTILINE
    )
    # 找类声明
    class_pattern = re.compile(r'class\s+(\w+)', re.MULTILINE)
    class_ranges = []
    for cm in class_pattern.finditer(cleaned):
        if SourcePreprocessor.is_in_string_or_comment(cm.start(), regions):
            continue
        brace_pos = cleaned.find('{', cm.end())
        if brace_pos >= 0:
            close = _find_matching_brace(cleaned, brace_pos)
            if close >= 0:
                class_ranges.append((cm.group(1), brace_pos, close))

    for m in method_pattern.finditer(cleaned):
        if SourcePreprocessor.is_in_string_or_comment(m.start(), regions):
            continue
        name = m.group(1)
        if name in ("if", "else", "while", "for", "switch", "catch", "try",
                     "return", "new", "throw", "class", "function", "import",
                     "export", "const", "let", "var", "typeof", "instanceof"):
            continue

        # 检查是否在类内
        class_name = None
        for cls_name, cls_start, cls_end in class_ranges:
            if cls_start < m.start() < cls_end:
                class_name = cls_name
                break

        if class_name is None:
            continue  # 不在类内的已由策略1/2覆盖

        start_line = _offset_to_line(source, m.start())
        brace_pos = cleaned.find('{', m.end() - 1)
        end_line = start_line
        if brace_pos >= 0:
            close = _find_matching_brace(cleaned, brace_pos)
            if close >= 0:
                end_line = _offset_to_line(source, close)

        functions.append({
            "name": name,
            "class": class_name,
            "params": m.group(2),
            "returnType": None,
            "modifiers": None,
            "annotations": None,
            "startLine": start_line,
            "endLine": end_line,
        })

    # 去重
    seen = set()
    unique = []
    for f in sorted(functions, key=lambda x: x["startLine"]):
        key = (f["name"], f["startLine"])
        if key not in seen:
            seen.add(key)
            unique.append(f)

    return unique


def _extract_generic_functions(source, cleaned, regions, lang):
    """通用花括号语言函数提取（Go, PHP, Ruby, Rust, C, C++, Swift, Kotlin）"""
    pattern = _FUNC_PATTERNS.get(lang)
    if not pattern:
        return []

    functions = []

    for m in pattern.finditer(cleaned):
        if SourcePreprocessor.is_in_string_or_comment(m.start(), regions):
            continue

        name = m.group("name")
        params = m.group("params") if "params" in m.groupdict() and m.group("params") else "()"
        ret = None
        if "ret" in m.groupdict() and m.group("ret"):
            ret = m.group("ret").strip()
            if ret == '':
                ret = None

        # 排除关键字
        if name in ("if", "else", "while", "for", "switch", "case", "return",
                     "class", "struct", "enum", "interface", "import", "package"):
            continue

        start_line = _offset_to_line(source, m.start())

        # 函数体结束
        if lang == "ruby":
            # Ruby 用 end 关键字
            end_line = _find_ruby_end(source, start_line)
        else:
            brace_pos = cleaned.find('{', m.end() - 1)
            end_line = start_line
            if brace_pos >= 0 and brace_pos - m.end() < 20:
                close = _find_matching_brace(cleaned, brace_pos)
                if close >= 0:
                    end_line = _offset_to_line(source, close)

        modifiers = None
        if "mods" in m.groupdict() and m.group("mods"):
            mods = m.group("mods").strip()
            if mods:
                modifiers = mods.split()

        annotations = None
        annot_key = "annots" if "annots" in m.groupdict() else ("attrs" if "attrs" in m.groupdict() else None)
        if annot_key and m.group(annot_key):
            raw = m.group(annot_key).strip()
            if raw:
                if lang == "rust":
                    annotations = re.findall(r'#\[[^\]]+\]', raw)
                elif lang in ("swift", "kotlin"):
                    annotations = re.findall(r'@\w+(?:\([^)]*\))?', raw)

        class_name = None
        if lang == "go" and "recv" in m.groupdict() and m.group("recv"):
            recv = m.group("recv").strip()
            parts = recv.split()
            if len(parts) >= 2:
                class_name = parts[-1].strip('*')
            elif len(parts) == 1:
                class_name = parts[0].strip('*')

        functions.append({
            "name": name,
            "class": class_name,
            "params": params,
            "returnType": ret,
            "modifiers": modifiers,
            "annotations": annotations,
            "startLine": start_line,
            "endLine": end_line,
        })

    return functions


def _find_ruby_end(source, start_line):
    """查找 Ruby 方法的 end 行"""
    lines = source.split('\n')
    if start_line - 1 >= len(lines):
        return start_line
    start_indent = len(lines[start_line - 1]) - len(lines[start_line - 1].lstrip())
    for i in range(start_line, len(lines)):
        stripped = lines[i].strip()
        if stripped == 'end':
            line_indent = len(lines[i]) - len(lines[i].lstrip())
            if line_indent <= start_indent:
                return i + 1
    return len(lines)


def _find_class_declarations(cleaned, regions, lang):
    """查找类声明及其范围"""
    if lang == "java":
        pattern = re.compile(
            r'(?:public|private|protected|abstract|final|static)?\s*'
            r'(?:class|interface|enum)\s+(\w+)',
            re.MULTILINE
        )
    elif lang == "c_sharp":
        pattern = re.compile(
            r'(?:public|private|protected|internal|abstract|sealed|static|partial)?\s*'
            r'(?:class|interface|enum|struct|record)\s+(\w+)',
            re.MULTILINE
        )
    else:
        return []

    classes = []
    for m in pattern.finditer(cleaned):
        if SourcePreprocessor.is_in_string_or_comment(m.start(), regions):
            continue
        name = m.group(1)
        brace_pos = cleaned.find('{', m.end())
        if brace_pos >= 0:
            close = _find_matching_brace(cleaned, brace_pos)
            if close >= 0:
                classes.append((name, m.start(), close))
    return classes


def _find_class_for_offset(classes, offset):
    """查找偏移量所在的最内层类"""
    best = None
    for name, start, end in classes:
        if start <= offset <= end:
            if best is None or (end - start) < (best[2] - best[1]):
                best = (name, start, end)
    return best[0] if best else None


# ─── 调用表达式提取 ────────────────────────────────────────

# 通用调用表达式正则（方法调用、函数调用）
_CALL_PATTERN = re.compile(
    r'(?:'
    r'(?P<recv>[\w.]+(?:\[\w*\])*)\s*\.\s*(?P<method>\w+)'  # obj.method(...)
    r'|'
    r'(?P<func>\w+)'  # func(...)
    r')\s*(?P<args>\([^)]*\))',
    re.MULTILINE
)

# 应排除的「调用」关键字
_CALL_EXCLUDE_KEYWORDS = frozenset({
    "if", "else", "while", "for", "switch", "catch", "return", "new",
    "throw", "class", "function", "def", "import", "from", "export",
    "const", "let", "var", "typeof", "instanceof", "assert", "print",
    "elif", "except", "finally", "with", "as", "pass", "raise",
    "yield", "await", "async", "package", "case", "default",
})


def _fb_extract_calls(source, cleaned, regions, lang, filter_callee=None):
    """Fallback：从源码中提取调用表达式"""
    calls = []
    seen = set()

    for m in _CALL_PATTERN.finditer(cleaned):
        if SourcePreprocessor.is_in_string_or_comment(m.start(), regions):
            continue

        recv = m.group("recv")
        method = m.group("method")
        func = m.group("func")
        args_text = m.group("args")

        if method:
            callee = f"{recv}.{method}"
            receiver = recv
        elif func:
            if func in _CALL_EXCLUDE_KEYWORDS:
                continue
            callee = func
            receiver = None
        else:
            continue

        line = _offset_to_line(source, m.start())
        key = (callee, line)
        if key in seen:
            continue
        seen.add(key)

        full_expr = source[m.start():m.end()][:200]

        call_info = {
            "callee": callee,
            "receiver": receiver,
            "args": args_text,
            "line": line,
            "fullExpression": full_expr,
        }
        calls.append(call_info)

    if filter_callee:
        pattern_lower = filter_callee.lower()
        calls = [c for c in calls if pattern_lower in c["callee"].lower()]

    return calls


# ═══════════════════════════════════════════════════════════
# 统一调度层：自动选择 tree-sitter 或 fallback
# ═══════════════════════════════════════════════════════════

def _parse_source(file_path):
    """读取文件，返回 (source, lang)"""
    lang = _detect_language(file_path)
    if lang is None:
        return None, None
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read(), lang
    except Exception:
        return None, lang


def extract_functions(source, lang):
    """提取函数 — tree-sitter 优先"""
    parser = _get_ts_parser(lang)
    if parser:
        try:
            return _ts_extract_functions(source.encode('utf-8'), parser, lang), "tree-sitter"
        except Exception:
            pass
    cleaned, regions = SourcePreprocessor.preprocess(source, lang)
    return _fb_extract_functions(source, cleaned, regions, lang), "regex-fallback"


def extract_calls(source, lang, filter_callee=None):
    """提取调用 — tree-sitter 优先"""
    parser = _get_ts_parser(lang)
    if parser:
        try:
            return _ts_extract_calls(source.encode('utf-8'), parser, lang, filter_callee), "tree-sitter"
        except Exception:
            pass
    cleaned, regions = SourcePreprocessor.preprocess(source, lang)
    return _fb_extract_calls(source, cleaned, regions, lang, filter_callee), "regex-fallback"


# ═══════════════════════════════════════════════════════════
# 持久化层：解析结果 → project-index.db
# ═══════════════════════════════════════════════════════════

AST_CACHE_SCHEMA = """
CREATE TABLE IF NOT EXISTS ast_functions (
    id INTEGER PRIMARY KEY AUTOINCREMENT, file_path TEXT NOT NULL,
    name TEXT NOT NULL, class_name TEXT, params TEXT, return_type TEXT,
    modifiers TEXT, annotations TEXT, start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL, parser_engine TEXT NOT NULL,
    UNIQUE(file_path, name, start_line)
);
CREATE TABLE IF NOT EXISTS ast_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT, file_path TEXT NOT NULL,
    callee TEXT NOT NULL, receiver TEXT, args TEXT, line INTEGER NOT NULL,
    full_expression TEXT, parser_engine TEXT NOT NULL,
    UNIQUE(file_path, callee, line)
);
CREATE TABLE IF NOT EXISTS ast_refined_sinks (
    id INTEGER PRIMARY KEY AUTOINCREMENT, file_path TEXT NOT NULL,
    line INTEGER NOT NULL, ast_verified INTEGER NOT NULL DEFAULT 0,
    reason TEXT, enclosing_func TEXT, func_range_start INTEGER,
    func_range_end INTEGER, call_expression TEXT, param_variables TEXT,
    parser_engine TEXT NOT NULL, UNIQUE(file_path, line)
);
CREATE TABLE IF NOT EXISTS ast_parse_meta (
    file_path TEXT PRIMARY KEY, language TEXT NOT NULL, parser_engine TEXT NOT NULL,
    function_count INTEGER DEFAULT 0, call_count INTEGER DEFAULT 0,
    parsed_at TEXT NOT NULL, file_hash TEXT
);
CREATE INDEX IF NOT EXISTS idx_ast_functions_file ON ast_functions(file_path);
CREATE INDEX IF NOT EXISTS idx_ast_calls_file ON ast_calls(file_path);
CREATE INDEX IF NOT EXISTS idx_ast_calls_callee ON ast_calls(callee);
CREATE INDEX IF NOT EXISTS idx_ast_refined_sinks_file ON ast_refined_sinks(file_path);
"""


def _connect_db(db_path, readonly=False):
    """连接 SQLite 数据库，启用 WAL 模式和 busy_timeout，带重试机制。"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if readonly:
                uri = f"file:{db_path}?mode=ro"
                conn = sqlite3.connect(uri, uri=True)
            else:
                conn = sqlite3.connect(db_path)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=15000")
            return conn
        except sqlite3.OperationalError as e:
            if "locked" in str(e) and attempt < max_retries - 1:
                import time
                time.sleep(1 * (attempt + 1))
                continue
            raise


def _ensure_ast_tables(db_path):
    conn = _connect_db(db_path)
    conn.executescript(AST_CACHE_SCHEMA)
    conn.commit()
    conn.close()


def _persist_parse_results(db_path, file_path, lang, functions, calls, engine, file_hash):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    conn = _connect_db(db_path)
    try:
        conn.execute("DELETE FROM ast_functions WHERE file_path=?", (file_path,))
        conn.execute("DELETE FROM ast_calls WHERE file_path=?", (file_path,))
        for f in functions:
            conn.execute(
                "INSERT OR REPLACE INTO ast_functions (file_path,name,class_name,params,return_type,modifiers,annotations,start_line,end_line,parser_engine) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (file_path, f["name"], f.get("class"), f.get("params"), f.get("returnType"),
                 json.dumps(f.get("modifiers")) if f.get("modifiers") else None,
                 json.dumps(f.get("annotations")) if f.get("annotations") else None,
                 f["startLine"], f["endLine"], engine))
        for c in calls:
            conn.execute(
                "INSERT OR REPLACE INTO ast_calls (file_path,callee,receiver,args,line,full_expression,parser_engine) VALUES (?,?,?,?,?,?,?)",
                (file_path, c["callee"], c.get("receiver"), c.get("args"),
                 c["line"], c.get("fullExpression", "")[:500], engine))
        conn.execute(
            "INSERT OR REPLACE INTO ast_parse_meta (file_path,language,parser_engine,function_count,call_count,parsed_at,file_hash) VALUES (?,?,?,?,?,?,?)",
            (file_path, lang, engine, len(functions), len(calls), now, file_hash))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


# ─── 命令: refine-sinks ──────────────────────────────────

def cmd_refine_sinks(args):
    """精化 Sink 定位：验证 Grep 粗定位结果，提取完整调用上下文。"""
    source, lang = _parse_source(args.file)
    if lang is None:
        print(json.dumps({"status": "fallback", "file": args.file, "reason": f"unsupported_extension:{Path(args.file).suffix}", "refinedSinks": []}))
        return
    if source is None:
        print(json.dumps({"status": "fallback", "file": args.file, "reason": "read_error", "refinedSinks": []}))
        return

    sinks = []
    if args.sinks_json:
        sinks = json.loads(args.sinks_json)
    elif args.lines:
        sinks = [{"line": int(l.strip())} for l in args.lines.split(",") if l.strip()]

    functions, engine = extract_functions(source, lang)
    cleaned, regions = SourcePreprocessor.preprocess(source, lang)
    lines = source.split('\n')
    refined = []

    for sink in sinks:
        target_line = sink.get("line", 0)
        if target_line <= 0 or target_line > len(lines):
            refined.append({**sink, "astVerified": False, "reason": "invalid_line"})
            continue
        line_content = lines[target_line - 1]
        line_offset = _line_to_offset(source, target_line)
        if SourcePreprocessor.is_in_string_or_comment(line_offset, regions):
            refined.append({**sink, "astVerified": False, "reason": "in_string_or_comment", "lineContent": line_content.strip()[:200]})
            continue
        enclosing_func = None
        for func in functions:
            if func["startLine"] <= target_line <= func["endLine"]:
                if enclosing_func is None or (func["endLine"] - func["startLine"]) < (enclosing_func["endLine"] - enclosing_func["startLine"]):
                    enclosing_func = func
        func_name = func_start = func_end = None
        if enclosing_func:
            func_name = enclosing_func["name"]
            if enclosing_func["class"]:
                func_name = f"{enclosing_func['class']}.{func_name}"
            func_start, func_end = enclosing_func["startLine"], enclosing_func["endLine"]
        param_vars = _extract_identifiers_from_line(line_content)
        refined.append({**sink, "astVerified": True, "enclosingFunction": func_name,
            "functionRange": [func_start, func_end] if func_start else None,
            "callExpression": line_content.strip()[:300], "paramVariables": param_vars[:10], "actualLine": target_line})

    print(json.dumps({"status": "ok", "file": args.file, "language": lang, "parserEngine": engine,
        "refinedSinks": refined, "count": len(refined), "verified": sum(1 for s in refined if s.get("astVerified"))}, ensure_ascii=False))


def _extract_identifiers_from_line(line):
    """从代码行中提取标识符（排除关键字和类名）"""
    # 提取所有标识符
    ids = re.findall(r'\b([a-z_]\w*)\b', line)
    # 排除常见关键字
    exclude = _CALL_EXCLUDE_KEYWORDS | {
        "true", "false", "null", "none", "nil", "this", "self", "super",
        "void", "int", "long", "float", "double", "string", "boolean",
        "byte", "char", "short", "bool", "str", "list", "dict", "set",
    }
    return list(dict.fromkeys(i for i in ids if i not in exclude))


# ─── 命令: check ──────────────────────────────────────────

def cmd_check(args):
    """检查解析器可用性"""
    _check_tree_sitter()
    ts_langs = sorted(_ts_languages.keys()) if _ts_available else []
    all_langs = sorted(set(LANG_EXT_MAP.values()))
    print(json.dumps({
        "parserType": "tree-sitter" if _ts_available and ts_langs else "regex-fallback",
        "treeSitterInstalled": bool(_ts_available),
        "treeSitterLanguages": ts_langs,
        "fallbackAvailable": True,
        "availableLanguages": all_langs,
        "missingTreeSitterLanguages": [l for l in all_langs if l not in ts_langs] if _ts_available else all_langs,
        "note": (f"tree-sitter active with {len(ts_langs)} languages"
            if _ts_available and ts_langs
            else "tree-sitter not installed, using regex fallback (run 'setup' to install)"),
    }, ensure_ascii=False))


# ─── 命令: setup ──────────────────────────────────────────

def _pip_install(packages, extra_args=None):
    """尝试 pip install，返回 (success, error_msg, strategy_used)。

    安装策略（按优先级依次尝试）：
      1. 直接 pip install
      2. pip install --user（用户级安装）
      3. pip install --break-system-packages（PEP 668 环境）
    """
    strategies = [
        ("direct", []),
        ("user", ["--user"]),
        ("break-system-packages", ["--break-system-packages"]),
    ]
    last_error = ""
    for strategy_name, strategy_args in strategies:
        cmd = [sys.executable, "-m", "pip", "install", "--quiet"] + strategy_args + (extra_args or []) + list(packages)
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if r.returncode == 0:
                return True, None, strategy_name
            last_error = r.stderr.strip()[:300]
            # 如果不是 externally-managed-environment 错误，不需要继续尝试
            if "externally-managed-environment" not in last_error.lower():
                return False, last_error, strategy_name
        except Exception as e:
            last_error = str(e)[:300]
    return False, last_error, "all_failed"


def cmd_setup(args):
    """引导安装 tree-sitter + 语言包"""
    global _ts_available, _ts_languages
    _check_tree_sitter()
    if _ts_available and len(_ts_languages) >= 10:
        print(json.dumps({"status": "already_installed", "treeSitterLanguages": sorted(_ts_languages.keys()),
            "message": f"tree-sitter already available with {len(_ts_languages)} languages"}))
        return
    install_results = {}
    fail_reason = None

    # 策略 1: 安装 tree-sitter + tree-sitter-languages 合集包
    for pkg in ["tree-sitter", "tree-sitter-languages"]:
        success, error, strategy = _pip_install([pkg])
        install_results[pkg] = {"success": success, "error": error, "strategy": strategy}
        if not success and not fail_reason:
            fail_reason = error

    # 策略 2: 合集包失败时，尝试各语言独立包
    if not install_results.get("tree-sitter-languages", {}).get("success"):
        for pkg in ["tree-sitter-python", "tree-sitter-java", "tree-sitter-javascript",
                     "tree-sitter-go", "tree-sitter-c", "tree-sitter-cpp"]:
            success, error, strategy = _pip_install([pkg])
            install_results[pkg] = {"success": success, "strategy": strategy}

    # 重新检测
    _ts_available = None
    _ts_languages = {}
    _check_tree_sitter()
    ts_langs = sorted(_ts_languages.keys()) if _ts_available else []

    # 构建失败原因描述
    if not (_ts_available and ts_langs) and fail_reason:
        if "externally-managed-environment" in (fail_reason or "").lower():
            fail_reason = "Python 环境受系统保护（PEP 668），所有安装策略均已尝试但未成功"
        elif "no module" in (fail_reason or "").lower():
            fail_reason = "pip 模块不可用"

    print(json.dumps({
        "status": "installed" if _ts_available and ts_langs else "fallback_only",
        "treeSitterInstalled": bool(_ts_available), "treeSitterLanguages": ts_langs,
        "installResults": install_results, "fallbackAvailable": True,
        "failReason": fail_reason if not (_ts_available and ts_langs) else None,
        "message": (f"tree-sitter installed with {len(ts_langs)} languages"
            if _ts_available and ts_langs
            else f"tree-sitter install failed ({fail_reason or 'unknown'}), regex fallback will be used"),
    }, ensure_ascii=False))


# ─── 命令: persist ────────────────────────────────────────

def cmd_persist(args):
    """批量解析并持久化到 project-index.db"""
    db_path = str(Path(args.batch_dir) / "project-index.db")
    if not os.path.exists(db_path):
        print(json.dumps({"error": f"Database not found: {db_path}"}))
        sys.exit(1)
    _ensure_ast_tables(db_path)
    files = []
    if args.files:
        files = [f.strip() for f in args.files.split(",") if f.strip()]
    elif args.file_list:
        with open(args.file_list, "r") as f:
            files = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    max_files = args.max_files or 100
    if len(files) > max_files:
        files = files[:max_files]
    # 读已有 hash
    conn = _connect_db(db_path, readonly=True)
    conn.row_factory = sqlite3.Row
    existing = {}
    try:
        for row in conn.execute("SELECT file_path, file_hash FROM ast_parse_meta"):
            existing[row["file_path"]] = row["file_hash"]
    except Exception:
        pass
    conn.close()
    processed = skipped = 0
    errors = []
    eng_used = "regex-fallback"
    for fp in files:
        if not os.path.exists(fp):
            errors.append({"file": fp, "reason": "file_not_found"})
            continue
        source, lang = _parse_source(fp)
        if lang is None or source is None:
            errors.append({"file": fp, "reason": "unsupported_or_read_error"})
            continue
        h = hashlib.md5(source.encode('utf-8', errors='replace')).hexdigest()
        if not getattr(args, 'force', False) and fp in existing and existing[fp] == h:
            skipped += 1
            continue
        try:
            funcs, eng = extract_functions(source, lang)
            calls, _ = extract_calls(source, lang)
            if eng == "tree-sitter":
                eng_used = "tree-sitter"
            _persist_parse_results(db_path, fp, lang, funcs, calls, eng, h)
            processed += 1
        except Exception as e:
            errors.append({"file": fp, "reason": str(e)[:200]})
    print(json.dumps({"status": "ok", "processed": processed, "skipped": skipped,
        "errors": errors, "parserEngine": eng_used, "dbPath": db_path,
        "message": f"Parsed {processed} files, skipped {skipped} unchanged"}, ensure_ascii=False))


# ─── 命令: cached-query ──────────────────────────────────

def cmd_cached_query(args):
    """从 project-index.db 查询缓存的 AST 结果"""
    db_path = str(Path(args.batch_dir) / "project-index.db")
    if not os.path.exists(db_path):
        print(json.dumps({"error": f"Database not found: {db_path}"}))
        sys.exit(1)
    conn = _connect_db(db_path, readonly=True)
    conn.row_factory = sqlite3.Row
    try:
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        if "ast_functions" not in tables:
            print(json.dumps({"error": "AST cache tables not found. Run 'persist' first."}))
            return
        p = args.preset
        lim = args.limit or 200
        ff = getattr(args, 'filter_file', None)
        fc = getattr(args, 'filter_callee', None)
        tl = getattr(args, 'target_line', None)

        if p == "functions":
            q = "SELECT * FROM ast_functions WHERE file_path=? ORDER BY start_line" if ff else "SELECT * FROM ast_functions ORDER BY file_path, start_line LIMIT ?"
            rows = conn.execute(q, (ff,) if ff else (lim,)).fetchall()
            result = {"functions": [dict(r) for r in rows], "count": len(rows)}
        elif p == "calls":
            if ff and fc:
                rows = conn.execute("SELECT * FROM ast_calls WHERE file_path=? AND callee LIKE ? ORDER BY line", (ff, f"%{fc}%")).fetchall()
            elif ff:
                rows = conn.execute("SELECT * FROM ast_calls WHERE file_path=? ORDER BY line", (ff,)).fetchall()
            elif fc:
                rows = conn.execute("SELECT * FROM ast_calls WHERE callee LIKE ? ORDER BY file_path, line LIMIT ?", (f"%{fc}%", lim)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM ast_calls ORDER BY file_path, line LIMIT ?", (lim,)).fetchall()
            result = {"calls": [dict(r) for r in rows], "count": len(rows)}
        elif p == "refined-sinks":
            q = "SELECT * FROM ast_refined_sinks WHERE file_path=? ORDER BY line" if ff else "SELECT * FROM ast_refined_sinks ORDER BY file_path, line LIMIT ?"
            rows = conn.execute(q, (ff,) if ff else (lim,)).fetchall()
            result = {"refinedSinks": [dict(r) for r in rows], "count": len(rows)}
        elif p == "parse-summary":
            meta = conn.execute("SELECT * FROM ast_parse_meta ORDER BY parsed_at DESC").fetchall()
            tf = conn.execute("SELECT COUNT(*) as c FROM ast_functions").fetchone()["c"]
            tc = conn.execute("SELECT COUNT(*) as c FROM ast_calls").fetchone()["c"]
            result = {"files": [dict(r) for r in meta], "fileCount": len(meta), "totalFunctions": tf, "totalCalls": tc,
                "parserEngines": list(set(r["parser_engine"] for r in meta))}
        elif p == "function-for-line":
            if not ff or not tl:
                result = {"error": "Requires --filter-file and --target-line"}
            else:
                rows = conn.execute("SELECT * FROM ast_functions WHERE file_path=? AND start_line<=? AND end_line>=? ORDER BY (end_line-start_line) ASC LIMIT 1", (ff, tl, tl)).fetchall()
                result = {"function": dict(rows[0]) if rows else None, "found": bool(rows)}
        elif p == "callers-of":
            if not fc:
                result = {"error": "Requires --filter-callee"}
            else:
                rows = conn.execute("SELECT * FROM ast_calls WHERE callee LIKE ? ORDER BY file_path, line LIMIT ?", (f"%{fc}%", lim)).fetchall()
                result = {"callers": [dict(r) for r in rows], "count": len(rows)}
        else:
            result = {"error": f"Unknown preset: {p}. Available: functions, calls, refined-sinks, parse-summary, function-for-line, callers-of"}
        print(json.dumps(result, ensure_ascii=False))
    finally:
        conn.close()


# ─── CLI 入口 ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="AST 解析工具（双引擎：tree-sitter 优先 + 内置正则 fallback）",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    subparsers.add_parser("check", help="检查解析器可用性")
    subparsers.add_parser("setup", help="安装 tree-sitter + 语言包")

    p = subparsers.add_parser("refine-sinks", help="精化 Sink 定位")
    p.add_argument("--file", required=True)
    p.add_argument("--sinks-json", help="Sink JSON")
    p.add_argument("--lines", help="行号列表")

    p = subparsers.add_parser("persist", help="批量解析并持久化到 DB")
    p.add_argument("--batch-dir", required=True, help="扫描批次目录")
    p.add_argument("--files", help="文件列表（逗号分隔）")
    p.add_argument("--file-list", help="文件列表文件")
    p.add_argument("--max-files", type=int)
    p.add_argument("--force", action="store_true", help="强制重新解析")

    p = subparsers.add_parser("cached-query", help="查询缓存的 AST 结果")
    p.add_argument("--batch-dir", required=True, help="扫描批次目录")
    p.add_argument("--preset", required=True, help="查询类型: functions/calls/refined-sinks/parse-summary/function-for-line/callers-of")
    p.add_argument("--filter-file", help="按文件过滤")
    p.add_argument("--filter-callee", help="按调用目标过滤")
    p.add_argument("--target-line", type=int, help="目标行号")
    p.add_argument("--limit", type=int, help="结果数量限制")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    cmds = {
        "check": cmd_check, "setup": cmd_setup,
        "refine-sinks": cmd_refine_sinks, "persist": cmd_persist,
        "cached-query": cmd_cached_query,
    }
    cmds[args.command](args)


if __name__ == "__main__":
    main()
