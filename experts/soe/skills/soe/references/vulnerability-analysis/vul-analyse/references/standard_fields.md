# 漏洞信息标准字段说明

本文档定义了漏洞信息归一化后的 16 个标准字段，所有类型的漏扫报告都将被归一化到这些字段。

---

## 标准字段列表

| 序号 | 字段名 | 类型 | 说明 | 示例 |
|------|--------|------|------|------|
| 1 | 漏洞名称 | string | 漏洞的名称/标题 | Apache Log4j2 远程代码执行漏洞 |
| 2 | 漏洞ID | string | 漏洞唯一标识（部分报告可能无此字段） | SYS-2024-0001 |
| 3 | 漏洞类型 | string | 漏洞分类 | 远程代码执行、SQL注入、XSS |
| 4 | 漏洞描述 | string | 漏洞的详细描述信息 | 描述文本 |
| 5 | 修复建议 | string | 修复/缓解方案 | 升级至 Log4j 2.17.1 及以上版本 |
| 6 | 影响资产 | string | 受影响的资产/组件名称 | Apache Log4j2 2.0-2.14.1 |
| 7 | 风险域名/IP | string | 存在漏洞的主机域名或 IP 地址 | 10.0.1.100, example.com |
| 8 | 风险端口 | string | 漏洞涉及的端口号 | 8080, 443 |
| 9 | 发现时间 | string | 漏洞被扫描发现的时间 | 2024-12-01 10:30:00 |
| 10 | 扫描工具 | string | 使用的扫描工具名称 | 绿盟RSAS、深信服SIP、明鉴WEB扫描器 |
| 11 | CVE编号 | string | CVE 漏洞编号 | CVE-2021-44228 |
| 12 | CNVD编号 | string | CNVD 漏洞编号 | CNVD-2021-95914 |
| 13 | CNNVD编号 | string | CNNVD 漏洞编号 | CNNVD-202112-799 |
| 14 | CNCVE编号 | string | CNCVE 漏洞编号 | CNCVE-202112-001 |
| 15 | CVSS评分 | string | CVSS 漏洞评分（0-10） | 10.0 |
| 16 | 风险等级 | string | 风险等级分类 | 紧急/高危/中危/低危/信息 |

---

## 风险等级标准化

不同扫描工具的风险等级表述可能不同，统一映射如下：

| 标准等级 | 数值范围 (CVSS) | 其他常见表述 |
|---------|----------------|-------------|
| 紧急 | 9.0 - 10.0 | Critical, 严重, emergency |
| 高危 | 7.0 - 8.9 | High, 高风险, high |
| 中危 | 4.0 - 6.9 | Medium, 中风险, medium |
| 低危 | 0.1 - 3.9 | Low, 低风险, low |
| 信息 | 0.0 | Info, 提示, 安全, info, safe |

---

## 支持的报告格式和解析器

| 解析器名称 | 文件类型 | 厂商/来源 | 识别特征 |
|-----------|---------|----------|---------|
| qianxin_secvss_parser | Excel | 奇安信网神SecVSS | 含 "SFID编号"+"漏洞编号" 列 |
| nsfocus_rsas_excel_parser | Excel | 绿盟RSAS | 含 "漏洞名称"+"主机IP"+"CVSS评分"+"服务" 列 |
| generic_excel_parser | Excel | 通用 | 含 vulname, severity, description 列 |
| specific_excel_parser | Excel | 通用 | 含 vulname_desc, risk_level_detail 列 |
| sxf_parser | Excel | 深信服 | 含 "漏洞名称", "SFID编号" 列 |
| xuanjing_parser | Excel | 悬镜 | 含 "XMIRROR编号", "影响组件数" 列 |
| dengbao_parser | Excel | 等保 | 含 "危险程度", "影响IP", "出现次数" 列 |
| venus_tianjing_html_parser | HTML | 启明星辰天镜 | 含 "天镜脆弱性扫描与管理系统" |
| huaun_lingdong_html_parser | HTML | 华云安灵洞 | 含 "灵洞 Ai.Vul" |
| lv_meng_host_html_parser | HTML | 绿盟(主机) | window.data + 主机报表 |
| lv_meng_04_vuln_info_parser | HTML | 绿盟(04) | window.data + vulns_info |
| lv_meng_domain_html_parser | HTML | 绿盟(站点) | 站点报表 |
| lv_meng_web_vuln_html_parser | HTML | 绿盟(Web) | 站点报表 |
| mingjian_html_parser | HTML | 明鉴 | 明鉴漏洞扫描系统 |
| xray_json_parser | JSON(NDJSON) | 长亭xray社区版 | 含 plugin, detail 字段 |
| dongjian_json_parser | JSON | 长亭洞鉴企业版 | 含 report_info, vulnerabilities 字段 |
| json_parser | JSON | 通用 | .json 文件 |
| xml_parser | XML | 通用 | .xml 文件 |
