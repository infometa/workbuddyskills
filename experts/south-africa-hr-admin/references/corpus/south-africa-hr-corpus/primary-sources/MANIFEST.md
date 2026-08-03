# 核心法源清单（Primary Sources Manifest）

本目录用于存放南非人力资源与行政相关的**官方法案原文**，供逐字引用与合规审计。
语料库（../ 各板块 .md）是「提炼版」，本目录是「权威源」——正式引用请以这里归档的原文为准。

> **重要**：SAFLII 对自动化抓取有反爬限制（常返回 403）。`fetch_primary_sources.py`
> 会尝试下载，但在受限网络下可能失败；失败时请按下方「人工下载」步骤获取。

---

## 1. BCEA — Basic Conditions of Employment Act 75 of 1997
- **官方编号**：Act No. 75 of 1997（含后续修正案）
- **主管**：Department of Employment and Labour
- **SAFLII 检索**：https://www.saflii.org/cgi-bin/sinodisp/za/search?query=Basic+Conditions+of+Employment+Act+75+of+1997
- **官网**：https://www.labour.gov.za/

## 2. LRA — Labour Relations Act 66 of 1995
- **官方编号**：Act No. 66 of 1995（含 2014 / 2018 等修正案）
- **主管**：Department of Employment and Labour
- **SAFLII 检索**：https://www.saflii.org/cgi-bin/sinodisp/za/search?query=Labour+Relations+Act+66+of+1995
- **官网**：https://www.labour.gov.za/

## 3. EEA — Employment Equity Act 55 of 1998
- **官方编号**：Act No. 55 of 1998（2022 修正案 Act 47 of 2023，2025-01-01 生效）
- **主管**：Department of Employment and Labour
- **SAFLII 检索**：https://www.saflii.org/cgi-bin/sinodisp/za/search?query=Employment+Equity+Act+55+of+1998
- **官网**：https://www.labour.gov.za/employment-equity

## 4. B-BBEE — Broad-Based Black Economic Empowerment Act 53 of 2003
- **官方编号**：Act No. 53 of 2003（2013 修正案 Act 46 of 2013）+ Codes of Good Practice
- **主管**：Department of Trade, Industry and Competition（B-BBEE Commission）
- **SAFLII 检索**：https://www.saflii.org/cgi-bin/sinodisp/za/search?query=Broad-Based+Black+Economic+Empowerment+Act+53+of+2003
- **委员会**：https://www.bbbeecommission.co.za/
- **Codes of Good Practice**：https://www.gov.za/

## 5. COIDA — Compensation for Occupational Injuries and Diseases Act 130 of 1993
- **官方编号**：Act No. 130 of 1993（2026 修正）
- **主管**：Compensation Fund（Department of Employment and Labour）
- **SAFLII 检索**：https://www.saflii.org/cgi-bin/sinodisp/za/search?query=Compensation+for+Occupational+Injuries+and+Diseases+Act+130+of+1993
- **在线系统**：https://cfonline.labour.gov.za/

---

## 人工下载步骤（当脚本失败 / 网络受限时）

1. 打开对应 SAFLII 检索链接，点击结果中的「[ZA] Act」进入法文页。
2. 在法文页选「Download」或复制全文，保存为 `primary-sources/raw/<法案简称>.txt`（或 .html）。
3. 建议同时保存 Government Gazette 编号与发布日期，便于版本溯源。
4. 备选权威源：各法案主管部委官网（见上）、gov.za 法规库。

## 归档建议

```
primary-sources/
├── MANIFEST.md                  # 本文件
├── fetch_primary_sources.py     # 一键下载脚本
├── key-provisions.md            # 关键条款离线速查（已由语料提炼）
└── raw/                         # 下载的官方法文原文
    ├── bcea-75-of-1997.txt
    ├── lra-66-of-1995.txt
    ├── eea-55-of-1998.txt
    ├── bbbee-53-of-2003.txt
    └── coida-130-of-1993.txt
```
