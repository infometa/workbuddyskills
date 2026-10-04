# 合同审查 — 详细操作指南

本文档为合同审查的详细操作指南，由 SKILL.md 引用。执行审查流程时阅读本文档。

## 阶段 1：引导上传

**识别输入类型**，然后按对应方式处理：

- **具体文件路径**：直接进入文件验证流程。
- **目录路径**（如 `test-file/review/`、`~/contracts/`）：`ls <目录>` 列出文件，筛选 `.pdf`、`.docx`、`.doc`，向用户确认「找到以下 N 份文件，确认吗？」后上传。路径名本身（包含 `review`、`contract` 等英文词）不影响意图判断，关键是用户要求「审查/检查」这些文件。
- **未提供路径**：引导「请提供合同文件路径（PDF/Word，最多 5 份，每份 ≤10M），也可提供目录路径。」

**不支持的格式**：如果扩展名不在 `.pdf`、`.docx`、`.doc` 内，告知用户转换为 PDF 或 Word 后再提供，**不要尝试自行转换**。

审查尺度（默认不问，除非用户主动提及）：`0` 严格（默认）、`1` 中立、`2` 宽松。

上传文件后创建任务：

```bash
python3 scripts/tencent_esign.py call CreateBatchContractReviewTask '{"ResourceIds":["<id1>","<id2>"],"PolicyType":0}'
```

返回 `TaskIds` 数组，每个文件对应一个 TaskId，取出完整数组备用。

## 阶段 2：等待所有文件审查完成

**必须使用 `review-batch` 一次性处理全部任务**，不要用 `wait-review` 逐个处理（会导致后续任务结果丢失）：

```bash
python3 scripts/tencent_esign.py review-batch '["yD1xxx","yD2xxx"]' '["合同A.pdf","合同B.docx"]'
```

第二个参数为文件名列表（与 TaskIds 顺序一一对应），用于在结果中显示友好的文件名而非 TaskId。文件名从上传步骤获取（即用户提供的原始文件名）。

审查通常需要 1-3 分钟，长文档可能更久。如果用户希望查看进度，可对每个 task_id 调用 `review-progress-url`。

## 阶段 3：展示所有文件的审查结果

`review-batch` 返回结构（`failed: true` 的任务不影响其他文件）：

```json
{
  "results": [
    {
      "task_id": "yD1xxx",
      "failed": false,
      "total_risk_count": 5,
      "high_risk_count": 2,
      "_downloaded_files": ["/path/to/skill/downloads/合同A_审查批注.docx", "/path/to/skill/downloads/合同A_审查摘要.xlsx"],
      "_links_block": "📊 [在线查看...]\n📝 批注文件已下载到本地：`...`（请前往该目录查看）\n📋 审查摘要（Excel）已下载到本地：`...`（请前往该目录查看）"
    },
    {
      "task_id": "yD2xxx",
      "failed": true,
      "error": "审查失败原因"
    }
  ],
  "_downloaded_files": ["/path/to/skill/downloads/合同A_审查批注.docx", "..."],
  "_links_output": "（所有文件链接拼好的完整块）"
}
```

### 第一阶段：迁移并输出所有文件的链接

若顶层 `_downloaded_files` 非空，先按 `common_guide.md`「文件下载与迁移」把文件迁移到工作区 `downloads/`。然后输出顶层 `_links_output` 字段（其中本地路径行替换为迁移后的最终路径，其余原样输出）。每个成功文件固定 3 行（①在线查看——链接、②带批注文件、③摘要 Excel——自动下载成功时为本地路径，失败时为原下载链接或获取失败提示）。

**🪟 必须在交付文本输出前调用 `present_files`**：本地路径交付场景下（`review-batch` 返回的顶层 `_downloaded_files` 非空，且迁移到工作区 `downloads/` 成功；或迁移失败回退到技能目录原始路径），**调用一次 `present_files`**，传入**所有本地批注文件与摘要 Excel 的绝对路径数组**，让客户端把每个文件渲染成可下载卡片（图标/文件名/大小/点击下载）。`_links_output` 中的本地路径行仍照常输出作为伴随描述，但**主展示由 `present_files` 渲染的卡片承担**。**严禁漏调**（漏调退化为纯文本路径、用户看不到可下载文件入口）；`present_files` 调用失败按"在线链接回退"静默兜底，不向用户解释。

若某行显示「获取失败」，告知用户选择刷新链接重试。

### 第二阶段：逐文件获取并展示风险详情

完成第一阶段后，对每个 `failed == false` 的文件依次执行：

```bash
python3 scripts/tencent_esign.py wait-review <task_id>
```

`wait-review` 输出分为两部分：
1. **第一行 JSON**：含 `_has_more`、`_total` 等元数据（用于判断是否有更多）
2. **后续纯文本**：已预渲染好的概览 + Markdown 风险表格（含翻页提示）

**展示规则**：

1. 输出「文件 {序号}（{文件名}）：」作为标题
2. 将 JSON 后面的纯文本部分（概览 + 表格）**原样输出**

纯文本部分已是最终呈现格式（含概览行、表头、数据行、翻页提示），脚本负责排序和截断，模型只负责原样传递。

**用户要求查看更多**时，使用 `--offset` 翻页：

```bash
python3 scripts/tencent_esign.py wait-review <task_id> --offset 10
```

原样输出 JSON 后面的纯文本部分。

3. **结尾引导**（所有文件展示完毕后统一给出）：

原样输出 `review-batch` 返回的 `_next_steps` 字段值。

刷新链接：重新执行 `review-batch '<原来的 task_ids JSON 数组>' '<文件名列表>'`（脚本会重新调导出接口获取新链接并自动下载），迁移后输出 `_links_output`。

查看审查记录：执行 `review-list-url`，原样输出返回的 `_links_md`。

## 阶段 4：获取审查列表（用户主动查询）

用户主动输入「审查列表」「审查记录」「审查历史」时，无需先执行审查流程，直接鉴权后调用：

```bash
python3 scripts/tencent_esign.py review-list-url
```

返回 `_links_md` 字段，**原样输出**即可。

---

## 阶段 5：重新审查（可选）

引导补充审查方向，将要求写入 `Comment` 字段：

```bash
python3 scripts/tencent_esign.py call CreateBatchContractReviewTask '{"ResourceIds":["<同一批文件的id>"],"PolicyType":0,"Comment":"用户补充的审查要求"}'
```

取新返回的完整 `TaskIds` 数组，重新执行 `review-batch` 进入阶段 2→3 流程。

## 阶段 6：按建议重新起草（可选）

整合风险建议为起草需求，追问「还有其他补充吗？没有请回复「立即起草」」，确认后进入合同起草流程。
