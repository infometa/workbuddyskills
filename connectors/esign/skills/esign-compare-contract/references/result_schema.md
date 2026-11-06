# 比对结果协议 v2

生成 JSON 前读取本文件。输入是模型生成的业务数据，输出由本地脚本补充汇总和证据检查信息。脚本使用 Python 标准库，无第三方 Python 包依赖。

## 输入

顶层仅允许以下四个字段，全部必填：

| 字段 | 类型 | 说明 |
|---|---|---|
| `schema_version` | string | 固定 `2.0` |
| `files` | object | `base` 和 `compare`，两份文件的显示名称，不填写本地绝对路径或下载 URL |
| `coverage` | object | 实际比对范围与限制 |
| `differences` | array | 逐条差异，按条款顺序列出，ID 唯一 |

### coverage

| 字段 | 类型 | 说明 |
|---|---|---|
| `status` | string | `complete`：已经核对并比较本次选定文件的全部正文；`partial`：存在未读取、未比较或无法确认的范围 |
| `base_scope` | string | 基准件实际覆盖范围，如“选定文件正文第一至十条及其中的价格表” |
| `compare_scope` | string | 比对件实际覆盖范围 |
| `limitations` | string[] | 缺页、扫描不清、输出截断，以及影响结论的未纳入材料等。`partial` 必须有具体限制；完整覆盖但个别数字存疑也应记录 |

`complete` 不表示原 PDF/DOCX 的全部视觉元素已比较，也不能仅由抽取命令成功推导。缺失但仅被引用、且本次用户未提供的外部文件写入限制；若缺失导致某项影响不确定，在相应条目提问。已知正文内容尚未比较时必须是 `partial`。

### differences 每项

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 唯一非空标识，如 `D001` |
| `operation` | string/null | `add` 新增、`delete` 删除、`modify` 修改、`replace` 替换；仅不确定项允许 `null`，表示无法确认操作 |
| `classification` | string | `material`、`non_material`、`uncertain` 三选一 |
| `base_location` | string | 基准位置；没有该侧原文时为空串 |
| `compare_location` | string | 比对位置；没有该侧原文时为空串 |
| `before` | string | 基准连续原文，新增为空串 |
| `after` | string | 比对连续原文，删除为空串 |
| `analysis` | string | 具体变化和影响，完整自然句 |
| `basis` | string | 内部分类依据，不在报告逐项重复展示；不填写无来源的法律结论或法条 |
| `questions` | string[] | 待核实信息；不确定项至少一条，其他项可为空 |

不要输出 `move`，也不要把“结构／关键要素／语义”当成影响分类。

脚本检查：

- 新增：`before` 为空、`after` 非空；删除反之。修改／替换须有两侧引用。
- 非空引用必须在对应的实际抽取正文中命中；只统一 CRLF／CR／LF 换行编码，保留空格、制表符与换行边界；不忽略数字、否定词、单位、标点或大小写。
- OCR 一侧不可读时，可以用 `operation: null`、`classification: uncertain`、可读侧真实引用及明确的问题；不可读侧留空，不把“无法识别”填成原文。整份文件没有正文则停止，不生成报告。
- 无原文侧的位置必须为空；有原文侧必须有可复核位置。位置准确性仍需模型或人工核对，脚本不校验页码真实性。
- 重复 ID 或同位置、同引用的重复差异拒绝；不同位置的重复条款不自动合并。
- 完整比对且明细为空时，要求两份抽取正文仅统一换行编码后相同。不相同则补齐差异；不能为了通过验证谎报部分比对。
- 不允许额外字段、猜测相似度、模型手填计数或旧 `meta/overview/detail` 外壳。

## 输出

保留全部输入字段，追加：

```json
{
  "overview": {
    "result": "differences_found",
    "total": 3,
    "counts": {"material": 1, "non_material": 1, "uncertain": 1}
  },
  "evidence_check": {
    "method": "newline-normalized-contiguous-substring",
    "base_sha256": "由脚本计算的正文摘要",
    "compare_sha256": "由脚本计算的正文摘要",
    "note": "仅验证引用在所提供的抽取正文中存在；不证明抽取完整、位置正确或语义判断准确。"
  }
}
```

`overview.result`：

- `differences_found`：覆盖标记完整且有差异。
- `no_text_changes`：覆盖标记完整且抽取正文仅统一换行编码后相同，无明细。
- `partial`：覆盖不全，有无差异都不能得出全文一致结论。

这些是脚本输出字段，不能再次当作未经校验的输入。修改报告时使用原输入 payload 重跑；证据摘要仅标识此次提供给脚本的文本，不证明文件来源或合法性。

## 命令和错误

在技能目录执行：

```bash
python3 scripts/validate_compare_result.py \
  --input-file assets/example_result.json \
  --base-text-file assets/example_base.txt \
  --compare-text-file assets/example_compare.txt \
  --output-json '/本次工作目录/compare_result.json'
```

成功退出码为 0，stdout 输出完整已校验 JSON；指定的文件同时写入。失败退出码非 0，错误信息在 stderr；不能发布本轮旧输出。每次使用独立目录，退出失败时忽略可能残留或只完成部分写入的文件。

脚本允许仅 stdout、不指定输出文件；不会上传正文、保存远端记录或生成 `recordId`。对 Markdown 中的原文、文件名等做转义，避免把合同里的 HTML 和链接变成报告的执行内容。

## 结果展示顺序

完整结果先展示按合同顺序排列的全部差异明细，再按影响分类总结。新增或删除只展示有内容的一侧；空分类和空待确认模块不显示。`coverage`、证据指纹、分类依据在内部保留；实际影响结论的读取缺口才显示，不输出固定范围或技术声明。

只要总结时只给必要结论，不输出完整明细。是否生成文件由[结果交付规则](result-delivery.md)决定；不要将脚本兼容的Markdown输出选项当作当前平台的交付要求或默认入口。
