# 新解析器开发指南

vul-analyse 采用**插件化注册机制**，新增厂商解析器无需修改 `extract_vulns.py` 或 `cfg.yaml`，只需 3 步。

## 第 1 步：在 `scripts/parsers/` 下新建 `<vendor>.py`

```python
# scripts/parsers/my_scanner.py
from parser_registry import register_parser
from ._common import make_record, sniff_head, normalize_severity


def _detect(file_path: str) -> bool:
    """嗅探文件头，判断是否为本解析器能处理的格式"""
    head = sniff_head(file_path, 4096)
    return b"MyScanner" in head


@register_parser(
    name="my_scanner_json",           # 全局唯一标识
    vendor="My Scanner Inc.",         # 厂商名（人读）
    file_extensions=(".json",),       # 支持的扩展名
    detect=_detect,                   # 精细识别函数（可选但推荐）
    description="解析 My Scanner JSON 报告",
    priority=60,                      # 优先级 0-100，越大越先匹配
)
def parse(file_path: str) -> list[dict]:
    """解析报告，返回标准 16 字段 dict 列表"""
    import json
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    results = []
    for item in data.get("vulnerabilities", []):
        results.append(make_record(
            name=item.get("title", ""),
            cve=item.get("cve", ""),
            severity=item.get("severity", ""),
            desc=item.get("description", ""),
            fix=item.get("fix", ""),
            scanner="My Scanner",
        ))
    return results
```

## 第 2 步：装饰器参数说明

| 参数 | 必填 | 说明 |
|---|:---:|---|
| `name` | ✅ | 全局唯一标识，建议 `<vendor>_<format>`，如 `nessus_xml` |
| `vendor` | ✅ | 厂商名（人读），如 `Tenable Nessus` |
| `file_extensions` | ✅ | 支持的扩展名元组，如 `(".json", ".ndjson")` |
| `detect` | 推荐 | 精细识别函数，读文件头判断格式特征 |
| `priority` | 推荐 | 匹配优先级 0-100，默认 50。国际厂商建议 70-80 |
| `description` | 可选 | 简要描述，CLI `list` 命令会展示 |

## 第 3 步：自验证

```bash
# 列出已注册解析器，确认新解析器在列表中
python3 scripts/parser_registry.py list

# 用样例文件测试匹配
python3 scripts/parser_registry.py match --file /path/to/sample.json

# 端到端验证：用 extract_vulns.py 处理样例
python3 scripts/extract_vulns.py /path/to/sample.json -o /tmp/out.json
```

## 16 个标准字段

`make_record` 工具函数会构造符合规范的标准记录。详见 [standard_fields.md](standard_fields.md)。

## `_common` 模块工具

| 函数 | 用途 |
|---|---|
| `make_record(name, cve, severity, desc, fix, scanner, ...)` | 构造标准 16 字段记录 |
| `sniff_head(path, n_bytes=4096)` | 读取文件前 N 字节用于格式嗅探 |
| `normalize_severity(level)` | 严重度归一化（critical/high/medium/low/info） |
| `cvss_to_severity(score)` | CVSS 数值 → 等级名称 |
| `extract_cves_from_text(text)` | 从描述中正则提取 CVE 编号 |

## 兼容性

- **插件解析器优先**：插件命中即用，不再走 cfg.yaml
- **回退机制**：插件未命中时自动回退到 cfg.yaml 配置驱动解析器
- **零侵入**：不修改 `extract_vulns.py` 主文件，新增解析器只动 `parsers/` 目录

## 命名约定

- 文件名：小写 + 下划线，与 `name` 前缀一致（`nessus.py` ↔ `nessus_xml`）
- name 字段：`<vendor>_<format>`，全局唯一
- vendor 字段：官方品牌名（含大小写），便于 CLI 输出对人友好
