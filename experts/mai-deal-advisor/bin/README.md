# 工具说明

这些脚本用于交付前自检。它们只读取本地文件或公开 HKEX 端点。

## 数字出处检查

```bash
grounding_gate.py draft.md
```

退出码 `1` 代表草稿里有数字需要补一手来源，或需要明确标为待确认。

## 持股表勾稽

```bash
recon_gate.py cap_table.xlsx
```

退出码 `1` 代表持股表存在分母不一致、疑似重复披露或比例异常。

## 港股公告查询

```bash
hkexnews_fetch.py 00700
```

返回指定港股代码和日期区间内的公告日期、标题和 URL。

`.txt` 和 `.md` 文件不需要额外依赖。`.xlsx` 需要 `openpyxl`；`.docx` 需要 `python-docx`。
