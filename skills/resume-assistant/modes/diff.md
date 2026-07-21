# mode: diff · 生成两个版本间的 diff 报告

> **前置**：先读 [`_shared.md`](_shared.md)。本文件只讲 diff 的差异。

## 触发条件

- 用户说："对比一下我这两个版本的简历 / 这次改动了哪些地方"
- 用户提供 `version_control.left_version_id` 和 `right_version_id`
- 明确 `mode: "diff"`

## 输入

- `left_version_id`：左侧（较早/base）版本 ID，默认 `_master`
- `right_version_id`：右侧（较新/head）版本 ID，必填
- 两个 version 都必须已存在于 `_manifest.json`

## 与骨架的差异

这个 mode 基本绕过通用 8 步骨架，只跑对比逻辑：

| Step | 差异 |
|---|---|
| Step 0 | mode 已定 |
| **Step 1-4** | **全部跳过**（不改写内容，只读）|
| Step 5 | 不修改内容 → 不触发 Provenance 审计；但要在报告里**显示**两侧的 AI 文风审计摘要（如已存在）|
| **Step 6** | **跳过** |
| Step 7 | 只生成 `resume-output/<right_version_label>/diff-report.html`（若该目录已存在则覆盖该单文件）|
| Step 8 | 不需用户审核内容（只是展示工具）|

## diff 报告内容要求

- **字段级变更**：按 `basic_info / education / experience / projects / skills` 分段对比
- **bullet 级 diff**：高亮 新增 / 删除 / 修改（修改以左右对照展示）
- **关键词覆盖变化**（若两侧都有 JD 挂载）：添加了哪些 JD 关键词，丢失了哪些
- **AI 文风审计变化**：两侧的 `error/warn/info` 数量对比
- **Provenance 改写动作变化**：`rewrite_actions` 分类分布对比

## diff 独有的 NEVER

- **NEVER** 修改任何 resume 内容（diff 是只读操作）
- **NEVER** 更新 `_manifest.json`（纯展示）
- **NEVER** 生成新 version（diff 不创建 lineage 节点）

## 成功判定

- `diff-report.html` 生成成功，浏览器打开可见
- 两侧版本 ID 均已校验存在
