#!/usr/bin/env python3
"""
validate_data.py · data.js 结构化自检工具

功能：
  1. 从 COS 拉取 mock-data.js 作为"黄金标准"
  2. 解析用户生成的 data.js
  3. 递归对比：字段名、类型、数组长度约束
  4. 输出结构化校验报告（JSON），可被 agent 或 CI 消费

Usage:
    python3 validate_data.py --scene proposal --narrative pyramid --data /tmp/data.js

输出 JSON 格式：
    {
      "ok": true/false,
      "errors": [...],     # 阻断级：必须修复
      "warnings": [...]    # 建议级：可选修复
    }

退出码：0=通过，1=有 error，2=参数/解析异常
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import template_source  # noqa: E402


def extract_window_data(js_text: str) -> str:
    """
    从 data.js 中提取 window.data = {...}; 的对象体。
    支持 `window.data = {...};` 和 `const data = {...};` 两种写法。
    返回 JSON-like 字符串（JS 对象字面量）。
    """
    # 标准化：去掉 BOM / 开头注释
    js_text = js_text.strip()
    if js_text.startswith("\ufeff"):
        js_text = js_text[1:]

    # 匹配赋值语句起点
    patterns = [
        r"window\.data\s*=\s*",
        r"const\s+data\s*=\s*",
        r"var\s+data\s*=\s*",
        r"let\s+data\s*=\s*",
    ]
    start_idx = -1
    for pat in patterns:
        m = re.search(pat, js_text)
        if m:
            start_idx = m.end()
            break

    if start_idx == -1:
        return ""

    # 从 start_idx 开始，找到匹配的 {} 结尾
    depth = 0
    i = start_idx
    obj_start = -1
    while i < len(js_text):
        ch = js_text[i]
        if ch == "{":
            if depth == 0:
                obj_start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return js_text[obj_start : i + 1]
        elif ch == '"' or ch == "'":
            # 跳过字符串内容
            quote = ch
            i += 1
            while i < len(js_text):
                if js_text[i] == "\\" :
                    i += 1  # 跳过转义
                elif js_text[i] == quote:
                    break
                i += 1
        elif ch == "`":
            # 模板字符串
            i += 1
            while i < len(js_text):
                if js_text[i] == "\\":
                    i += 1
                elif js_text[i] == "`":
                    break
                i += 1
        i += 1
    return ""


def js_obj_to_json(js_obj: str) -> str:
    """
    将 JS 对象字面量转成合法 JSON（尽力而为）。
    处理：无引号 key、尾逗号、单引号、JS 表达式值。
    """
    text = js_obj

    # 1. 把单引号字符串转双引号（简化处理：非嵌套场景）
    # 这个很难完美处理，先做基础转换
    # 跳过——让 node 来处理更可靠

    # 2. 尝试用 node 的 JSON.stringify 来解析 JS 对象
    # 这是最可靠的方式，因为 data.js 本身就是合法 JS
    return text


def parse_data_with_node(js_text: str) -> Tuple[bool, Any, str]:
    """
    用 Node.js vm 隔离执行 data.js 并输出 JSON。
    支持 `window.data = {...}` / `const data = {...}` / `let data = {...}` / `var data = {...}`。
    返回 (success, parsed_dict, error_msg)
    """
    node_script = r"""
const vm = require('vm');
const fs = require('fs');
const source = fs.readFileSync(0, 'utf8');
const context = {
  window: {},
  console: { log(){}, warn(){}, error(){} },
};
context.globalThis = context;

function serializeFunctions(obj) {
  if (obj === null || obj === undefined) return obj;
  if (typeof obj === 'function') return obj.toString();
  if (Array.isArray(obj)) return obj.map(serializeFunctions);
  if (typeof obj === 'object') {
    const result = {};
    for (const [k, v] of Object.entries(obj)) {
      result[k] = serializeFunctions(v);
    }
    return result;
  }
  return obj;
}

try {
  const wrapped = `(function(){\n${source}\n; return window.data || (typeof data !== 'undefined' ? data : undefined);\n})()`;
  const data = vm.runInNewContext(wrapped, context, { timeout: 5000, displayErrors: true });
  if (!data) {
    process.stderr.write('ERROR: data is undefined after vm execution');
    process.exit(2);
  }
  process.stdout.write(JSON.stringify(serializeFunctions(data), null, 2));
} catch(e) {
  process.stderr.write('PARSE_ERROR: ' + e.message + '\n' + e.stack);
  process.exit(2);
}
"""
    try:
        result = subprocess.run(
            ["node", "-e", node_script],
            input=js_text,
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            return False, None, result.stderr.strip()
        return True, json.loads(result.stdout), ""
    except subprocess.TimeoutExpired:
        return False, None, "node execution timed out (>10s)"
    except json.JSONDecodeError as e:
        return False, None, f"JSON parse error from node output: {e}"
    except FileNotFoundError:
        return False, None, "node not found in PATH"
    except Exception as e:
        return False, None, f"unexpected error: {e}"


def get_type_desc(val: Any) -> str:
    """返回值的类型描述。"""
    if val is None:
        return "null"
    if isinstance(val, bool):
        return "boolean"
    if isinstance(val, int):
        return "number(int)"
    if isinstance(val, float):
        return "number(float)"
    if isinstance(val, str):
        # 判断是否是函数字符串
        if val.strip().startswith("function") or val.strip().startswith("(") or "=>" in val:
            return "function"
        return "string"
    if isinstance(val, list):
        return f"array[{len(val)}]"
    if isinstance(val, dict):
        return "object"
    return type(val).__name__


def compare_structure(
    mock: Any, data: Any, path: str, errors: List[str], warnings: List[str],
    *,
    array_len_strict: bool = False,
) -> None:
    """
    递归对比 mock（黄金标准）和 data（agent 生成），收集 errors / warnings。

    规则：
    - mock 有的 key，data 必须有（缺失 = error）
    - data 多余的 key → warning（可能是增强，不一定错）
    - 类型不匹配 = error
    - 数组：元素数必须 ≥ 1（空数组 = error）；长度差异 > 2× 或 < 0.5× → warning
    - 嵌套对象递归检查
    - string vs number：如果 mock 是 number 但 data 是 string（或反过来）→ error
    """
    if mock is None or data is None:
        if mock is not None and data is None:
            errors.append(f"{path}: 值为 null/undefined，mock 中为 {get_type_desc(mock)}")
        return

    mock_type = type(mock)
    data_type = type(data)

    # --- 对象 vs 对象 ---
    if isinstance(mock, dict) and isinstance(data, dict):
        # 检查缺失 key
        for key in mock:
            if key not in data:
                errors.append(f"{path}.{key}: 缺失（mock 中存在且类型为 {get_type_desc(mock[key])}）")
            else:
                compare_structure(mock[key], data[key], f"{path}.{key}", errors, warnings,
                                  array_len_strict=array_len_strict)
        # 检查多余 key
        for key in data:
            if key not in mock:
                warnings.append(f"{path}.{key}: 多余字段（mock 中不存在）")
        return

    # --- 数组 vs 数组 ---
    if isinstance(mock, list) and isinstance(data, list):
        if len(data) == 0 and len(mock) > 0:
            errors.append(f"{path}: 数组为空（mock 有 {len(mock)} 个元素）")
            return
        # 长度比较
        if len(mock) > 0:
            ratio = len(data) / len(mock)
            if ratio > 3:
                warnings.append(f"{path}: 数组长度 {len(data)} 远超 mock 的 {len(mock)}（{ratio:.1f}× 倍）")
            elif ratio < 0.3 and len(data) < len(mock):
                warnings.append(f"{path}: 数组长度 {len(data)} 远少于 mock 的 {len(mock)}")
        # 递归检查第一个元素的结构（假设数组内元素同构）
        if len(mock) > 0 and len(data) > 0:
            compare_structure(mock[0], data[0], f"{path}[0]", errors, warnings,
                              array_len_strict=array_len_strict)
        return

    # --- 类型不匹配 ---
    mock_td = get_type_desc(mock)
    data_td = get_type_desc(data)

    # 宽松匹配：number(int) 和 number(float) 互通
    if "number" in mock_td and "number" in data_td:
        return

    # 宽松匹配：function 和 string 在 compute 字段中互通
    if mock_td == "function" and data_td == "string":
        return
    if mock_td == "string" and data_td == "function":
        return

    # 宽松匹配：string 和 number 不互通（这是常见错误）
    if mock_td != data_td:
        # 如果 mock 是 object/array 而 data 不是，属于严重结构错误
        if isinstance(mock, (dict, list)) or isinstance(data, (dict, list)):
            errors.append(f"{path}: 类型不匹配（期望 {mock_td}，实际 {data_td}）")
        else:
            # 标量类型不匹配：string vs number 等
            errors.append(f"{path}: 类型不匹配（期望 {mock_td}，实际 {data_td}）")


def validate(scene: str, narrative: str, data_file: str) -> dict:
    """执行完整校验，返回结果字典。"""
    errors: List[str] = []
    warnings: List[str] = []

    # 1. 读取 data.js
    data_path = Path(data_file)
    if not data_path.is_file():
        return {"ok": False, "errors": [f"data.js 文件不存在: {data_file}"], "warnings": []}
    data_js_text = data_path.read_text(encoding="utf-8")

    # 2. 拉取 mock-data.js
    mock_rel = f"scenes/{scene}/{narrative}/mock-data.js"
    try:
        mock_js_text = template_source.fetch_text(mock_rel)
    except Exception as e:
        return {"ok": False, "errors": [f"无法拉取 mock-data.js: {mock_rel} ({e})"], "warnings": []}

    # 3. 用 node 解析两份 JS
    ok_data, data_obj, err_data = parse_data_with_node(data_js_text)
    if not ok_data:
        errors.append(f"data.js 解析失败（JS 语法错误）: {err_data}")
        return {"ok": False, "errors": errors, "warnings": warnings}

    ok_mock, mock_obj, err_mock = parse_data_with_node(mock_js_text)
    if not ok_mock:
        errors.append(f"mock-data.js 解析失败（内部错误）: {err_mock}")
        return {"ok": False, "errors": errors, "warnings": warnings}

    # 4. 递归结构对比
    compare_structure(mock_obj, data_obj, "data", errors, warnings)

    # 5. 额外检查
    # 5a. 检查中文引号（常见错误）
    # 使用 unicode 转义避免编辑器/formatter 将中文引号转成 ASCII 引号
    if re.search("[\u201c\u201d\u2018\u2019\u300c\u300d]", data_js_text):
        errors.append("发现中文引号（必须使用英文半角引号）")

    # 5b. 检查 data 赋值存在
    if not re.search(r"\b(window\.data|const\s+data|let\s+data|var\s+data)\s*=", data_js_text):
        errors.append("缺少 `window.data = ...` / `const data = ...` / `let data = ...` / `var data = ...` 赋值语句")

    # 5c. 检查 compute 字段如果 mock 中有的话
    if isinstance(mock_obj, dict):
        roi = mock_obj.get("roi", {})
        if isinstance(roi, dict) and "compute" in roi:
            data_roi = data_obj.get("roi", {}) if isinstance(data_obj, dict) else {}
            if isinstance(data_roi, dict):
                compute_val = data_roi.get("compute", "")
                if not compute_val:
                    errors.append("data.roi.compute: 为空（mock 中有可执行 JS 表达式）")
                elif isinstance(compute_val, str) and "return" not in compute_val:
                    warnings.append("data.roi.compute: 缺少 return 语句（可能无法正确计算）")

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "stats": {
            "mock_keys": count_keys(mock_obj),
            "data_keys": count_keys(data_obj),
        }
    }


def count_keys(obj: Any, depth: int = 0) -> int:
    """统计对象总 key 数（递归）。"""
    if isinstance(obj, dict):
        count = len(obj)
        for v in obj.values():
            count += count_keys(v, depth + 1)
        return count
    if isinstance(obj, list) and len(obj) > 0:
        return count_keys(obj[0], depth + 1)
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description="验证 data.js 结构是否与 mock-data.js 一致（COS 远端对比）"
    )
    p.add_argument("--scene", required=True, help="scene id")
    p.add_argument("--narrative", required=True, help="narrative id")
    p.add_argument("--data", required=True, help="agent 生成的 data.js 路径")
    p.add_argument("--json", action="store_true", help="仅输出 JSON（不打印人类可读摘要）")
    args = p.parse_args()

    result = validate(args.scene, args.narrative, args.data)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # 人类可读输出
        if result["ok"]:
            print(f"✅ PASS · {args.scene}/{args.narrative} · 结构校验通过")
            if result["warnings"]:
                print(f"   ⚠️  {len(result['warnings'])} 条建议：")
                for w in result["warnings"]:
                    print(f"      · {w}")
        else:
            print(f"❌ FAIL · {args.scene}/{args.narrative} · {len(result['errors'])} 个错误")
            for e in result["errors"]:
                print(f"   ❌ {e}")
            if result["warnings"]:
                print(f"   ⚠️  另有 {len(result['warnings'])} 条建议：")
                for w in result["warnings"]:
                    print(f"      · {w}")

        stats = result.get("stats", {})
        if stats:
            print(f"   📊 mock keys: {stats.get('mock_keys', '?')} · data keys: {stats.get('data_keys', '?')}")

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
