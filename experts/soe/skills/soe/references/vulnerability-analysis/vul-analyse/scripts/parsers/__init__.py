"""
插件解析器目录。

放在此目录的每个 *.py 文件都会被 parser_registry.discover_plugins() 自动加载。
约定：每个文件用 @register_parser 装饰器注册一个或多个解析器，
     函数签名为 parse(file_path: str) -> list[dict]。

返回的 dict 字段建议遵循 STANDARD_FIELDS（见 extract_vulns.py）：
  漏洞名称 / 漏洞ID / 漏洞类型 / 漏洞描述 / 修复建议
  影响资产 / 风险域名/IP / 风险端口 / 发现时间 / 扫描工具
  CVE编号 / CNVD编号 / CNNVD编号 / CNCVE编号 / CVSS评分 / 风险等级

贡献新解析器只需 3 步：
  1. 在本目录下新建 <vendor>.py
  2. 用 @register_parser(name=..., vendor=..., file_extensions=..., detect=...) 装饰 parse 函数
  3. 用 `python3 scripts/parser_registry.py match --file <sample>` 自验证匹配
     （完整开发指南见 references/parser-development.md）

示例（最小模板）：

    from parser_registry import register_parser
    from ._common import make_record, sniff_head

    def _detect(file_path: str) -> bool:
        return b"MyScanner" in sniff_head(file_path, 4096)

    @register_parser(
        name="my_scanner_json",
        vendor="My Scanner Inc.",
        file_extensions=(".json",),
        detect=_detect,
        priority=60,
    )
    def parse(file_path: str) -> list[dict]:
        import json
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [make_record(name=v["title"], cve=v.get("cve", ""))
                for v in data.get("vulnerabilities", [])]

共享工具见 _common.py（下划线开头，不会被自动加载为插件）。
"""
