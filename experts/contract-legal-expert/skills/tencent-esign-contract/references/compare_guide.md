# 合同对比 — 详细操作指南

本文档为合同对比的详细操作指南，由 SKILL.md 引用。执行对比流程时阅读本文档。

## 阶段 1：引导上传

**识别输入类型**，然后按对应方式处理：

- **给出两个具体文件路径**：直接进入文件验证流程，第一个作为原版，第二个作为新版。
- **给出目录路径**（如 `test-file/compare/`）：`ls <目录>` 列出文件，筛选 `.pdf`、`.docx`、`.doc`，若恰好 2 份则向用户确认原版/新版对应关系后上传；多于 2 份则列出让用户指定哪两份对比。路径名本身（包含 `compare`、`diff` 等英文词）不影响意图判断。
- **未提供路径**：引导「请提供需要对比的两份合同文件——原版和新版（支持 PDF/Word 格式）。」

**不支持的格式**：如果扩展名不在 `.pdf`、`.docx`、`.doc` 内，告知用户转换为 PDF 或 Word 后再提供，**不要尝试自行转换**。

上传两份文件获取两个 ResourceId，然后创建对比任务：

```bash
python3 scripts/tencent_esign.py call CreateContractComparisonTask '{"OriginFileResourceId":"<origin_id>","DiffFileResourceId":"<diff_id>"}'
```

## 阶段 2：对比处理中

```bash
python3 scripts/tencent_esign.py wait-compare <TaskId> "<原文件名>"
```

对比通常几秒到一分钟内完成。可调 `compare-progress-url <task_id>` 获取进度链接，有值时告知用户可点击查看。

`wait-compare` 会在对比完成后自动获取三个链接并放入返回结果的 `_links_block` 字段。可选第二参数为原文件名（建议传用户提供的原始合同文件名，从上传步骤获取）；下载文件按「原文件名_对比报告 / 原文件名_差异明细」命名，未传时回退为「对比任务_<任务ID前缀>_对比报告 / 差异明细」。

## 阶段 3：对比完成展示

**概览**：从 `Response` 取值，输出「共发现 **{TotalDiffCount}** 处差异：新增 {AddDiffCount} 处、修改 {ChangeDiffCount} 处、删除 {DeleteDiffCount} 处。」

**链接**：`wait-compare` 返回结果里已包含 `_links_block` 字段和 `_downloaded_files`（已下载文件的本地路径数组）。若 `_downloaded_files` 非空，先按 `common_guide.md`「文件下载与迁移」把文件迁移到工作区 `downloads/`，再输出 `_links_block`（本地路径行替换为迁移后的最终路径，其余原样输出）。每个对比任务固定 3 行（①在线预览——链接、②PDF报告、③Excel明细——自动下载成功时为本地路径，失败时为原下载链接或获取失败提示）。

**🪟 必须在交付文本输出前调用 `present_files`**：本地路径交付场景下（`wait-compare` 返回的 `_downloaded_files` 非空，且迁移到工作区 `downloads/` 成功；或迁移失败回退到技能目录原始路径），**调用一次 `present_files`**，传入**所有本地批注报告（PDF）与差异明细（Excel）的绝对路径数组**，让客户端把每个文件渲染成可下载卡片（图标/文件名/大小/点击下载）。`_links_block` 中的本地路径行仍照常输出作为伴随描述，但**主展示由 `present_files` 渲染的卡片承担**。**严禁漏调**（漏调退化为纯文本路径、用户看不到可下载文件入口）；`present_files` 调用失败按"在线链接回退"静默兜底，不向用户解释。

若某行显示「获取失败」，用户可选择「刷新链接」重试。

**获取差异详情**（`wait-compare` 不含具体内容，需额外调用）：

```bash
python3 scripts/tencent_esign.py call DescribeContractComparisonTask '{"TaskId":"<task_id>","ShowDetail":true}'
```

`ComparisonDetail` 数组解析（严格按此路径取值）：

1. `resp = json.loads(output)`
2. `details = resp["Response"]["ComparisonDetail"]`
3. 遍历 `details`，每项通过 `item["ComparisonType"]`、`item["OriginText"]`、`item["DiffText"]`、`item["PageNumber"]` 取值

**差异明细表格**：

| 序号 | 类型 | 原文 | 修改后 | 页码 |
|------|------|------|--------|------|

`ComparisonType` 中文映射：`"add"` → 新增、`"change"` → 修改、`"delete"` → 删除。删除类型「修改后」列显示「—」，新增类型「原文」列显示「—」。

展示规则：≤10 条全部展示；>10 条展示前 5 条，提示「还有 N 条差异，是否展开？或直接下载 Excel 明细。」

**结尾引导**：

原样输出 `wait-compare` 返回的 `_next_steps` 字段值。

刷新链接：执行 `compare-links <task_id> "<原文件名>"`（脚本会重新调导出接口获取新链接并自动下载，文件名规则同 wait-compare），迁移后输出 `_links_block`。

查看对比记录：执行 `compare-list-url`，原样输出返回的 `_links_md`。

## 阶段 4：获取对比列表（用户主动查询）

用户主动输入「对比列表」「对比记录」「对比历史」时，无需先执行对比流程，直接鉴权后调用：

```bash
python3 scripts/tencent_esign.py compare-list-url
```

返回 `_links_md` 字段，**原样输出**即可。
