# 支持的扫描器报告格式

vul-analyse 支持 20+ 主流漏扫产品的报告格式。解析器分两类：
- **插件解析器**（`scripts/parsers/*.py`）：通过 `@register_parser` 装饰器自动注册，优先匹配
- **配置驱动解析器**（`scripts/cfg.yaml`）：内置兼容层，未命中插件时回退

## 国内厂商

| 厂商/工具 | 格式 | 解析器 | 注册方式 |
|---|---|---|---|
| 绿盟 RSAS（主机） | HTML | `lv_meng_host_html_parser` | cfg.yaml |
| 绿盟 RSAS（站点/Web） | HTML | `lv_meng_domain_html_parser` / `lv_meng_web_vuln_html_parser` | cfg.yaml |
| 绿盟 RSAS（漏洞详情） | HTML | `lv_meng_04_vuln_info_parser` | cfg.yaml |
| 绿盟 RSAS（Excel） | XLSX | `nsfocus_rsas_excel_parser` | cfg.yaml |
| 深信服 SIP | XLSX | `sxf_parser` | cfg.yaml |
| 悬镜 XMIRROR | XLSX | `xuanjing_parser` | cfg.yaml |
| 明鉴 WEB 扫描 | HTML | `mingjian_html_parser` | cfg.yaml |
| 等保扫描 | XLSX | `dengbao_parser` | cfg.yaml |
| 奇安信 SecVSS | XLSX | `qianxin_secvss_parser` | cfg.yaml |
| 启明星辰天镜 | HTML | `venus_tianjing_html_parser` | cfg.yaml |
| 华云安 灵洞 Ai.Vul | HTML | `huaun_lingdong_html_parser` | cfg.yaml |
| 长亭 xray 社区版 | NDJSON | `xray_json_parser` | cfg.yaml |
| 长亭 洞鉴企业版 | JSON | `dongjian_json_parser` | cfg.yaml |

## 国际厂商（插件化）

| 厂商/工具 | 格式 | 解析器 name | priority |
|---|---|---|:---:|
| Tenable Nessus | .nessus / NessusClientData_v2 XML | `nessus_xml` | 80 |
| Aqua Trivy | JSON（Vulnerabilities + Misconfigurations + Secrets） | `trivy_json` | 75 |
| Anchore Grype | JSON（CVSS v3 + fix state） | `grype_json` | 74 |
| Snyk | JSON（SCA/Container + Code SARIF 子集） | `snyk_json` | 73 |
| Greenbone OpenVAS / GVM | XML | `openvas_xml` | 70 |

## 通用格式

| 格式 | 解析器 | 用途 |
|---|---|---|
| 通用 Excel | `generic_excel_parser` / `specific_excel_parser` | 标题模糊匹配 |
| 通用 JSON | `json_parser` | 自适应字段映射 |
| 通用 XML | `xml_parser` | 自适应字段映射 |
| 多文件聚合 | `zip_aggregator` | ZIP 内多份报告合并 |

## 优先级规则

匹配顺序（高到低）：

1. **插件解析器按 priority 降序匹配**（80 → 70）
2. **插件解析器若 detect 函数返回 True 立即命中**
3. **未命中则回退到 cfg.yaml 配置驱动解析器**
4. **cfg.yaml 也未命中时报错并提示用户**

## 自查命令

```bash
python3 scripts/parser_registry.py list                    # 列出所有已注册解析器
python3 scripts/parser_registry.py match --file <path>     # 测试某文件会被哪个解析器命中
```

## 添加新解析器

详见 [parser-development.md](parser-development.md)。
