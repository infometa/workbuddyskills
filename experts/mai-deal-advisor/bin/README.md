# 工具说明

这些脚本用于交付前自检。它们只读取本地文件或公开 HKEX 端点。

`data_boundary: local_only` 表示用户文件、生成产物和运行记录不回传 MAI。港股公告查询会在用户确认后向港交所披露易发送股票代码和日期范围，并应记录到运行清单的 `external_queries`。

## 数字出处检查

```bash
python3 bin/grounding_gate.py draft.md
```

支持 `.md`、`.txt`、`.csv`、`.xlsx`、`.docx` 和文本型 `.pdf`。

- 退出码 `0`：检查完成，未发现拦截项。
- 退出码 `1`：发现数字需要补一手来源，或需要明确标为待确认。
- 退出码 `2`：文件不支持、打不开或没有完成检查。

## 持股表勾稽

```bash
python3 bin/recon_gate.py cap_table.xlsx
```

支持 `.md`、`.txt`、`.csv`、`.xlsx` 和 `.docx`。

- 退出码 `0`：识别到持股表并完成检查，未发现问题。
- 退出码 `1`：发现分母不一致、疑似重复披露或比例异常。
- 退出码 `2`：没有识别到可校验的持股表，或文件未完成检查。

## 公式和评分复算

```bash
python3 bin/calculation_gate.py outputs/report-draft.md
```

支持 `.md`、`.txt` 和 `.csv` 中使用 `+`、`-`、`*`、`/`、`×`、`÷` 与 `=` 写出的显式公式。

- 退出码 `0`：识别到公式并完成复算，未发现不一致。
- 退出码 `1`：识别到错误公式或无法计算的除零表达式。
- 退出码 `2`：未识别到可复算公式、文件不支持或无法读取。

## 港股公告查询

```bash
python3 bin/hkexnews_fetch.py 00700
```

返回指定港股代码和日期区间内的公告日期、标题和 URL。它执行一次查询，不提供后台持续监控。

- 退出码 `0`：查询完成，包括确认的零结果。
- 退出码 `2`：代码、日期、网络或结果完整性存在问题。

## SVG 结构校验

```bash
python3 bin/svg_validate.py outputs/deal-structure-diagram.svg
```

检查 XML、viewBox、活动内容、外部资源、inline 样式、最低图形与文字元素、重复 id 和失效 marker 引用。退出码 `0` 只代表结构校验通过，仍须打开产物预览检查文字、节点和连线是否重叠；输入文件不存在或不可读时返回 `2`。

`.txt`、`.md` 和 `.csv` 不需要额外依赖。`.xlsx` 需要 `openpyxl`；`.docx` 需要 `python-docx`；`.pdf` 来源检查需要 `pypdf`。
