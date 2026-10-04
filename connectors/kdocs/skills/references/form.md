# 智能表单（form）工具完整参考文档

本文件包含金山文档 Skill 智能表单的操作说明。

使用 `form.lite.*` 工具时，优先按草稿生命周期操作：创建草稿、更新题目、查询草稿内容、确认后发布、查询发布结果。

智能表单发布后无法修改。除非用户明确要求“无需确认，直接发布”，否则默认只创建或更新草稿。每次创建或修改草稿后，都必须调用 `form.lite.get_form_info` 获取最新内容，并整理一份可读的文字版表单返回给用户确认。发布前同样基于最新返回值展示表单标题、题目列表、题型、必填状态和选项内容，等待用户确认后再调用 `form.lite.publish_draft`。

表单创建或查询后，按返回字段拼接访问地址：

| 页面 | 地址模板 | 字段来源 | 说明 |
|------|----------|----------|------|
| 管理页面 | `https://f.wps.cn/ksform/m/result/:form_id` | `form_id` | 用于查看表单结果、管理表单和后续配置 |
| 填写页面 | `https://f.wps.cn/g/:sid` | `sid` | 用于分发给填写人；通常需要发布后才会返回 `sid` |

交付给用户时，若已发布表单，应同时给出管理页面和填写页面；若仍是草稿，只给管理页面并提示发布后才有填写页面，同时说明需要用户确认表单内容后再发布。

---

## 一、草稿管理

> 智能表单草稿的创建、更新与发布

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`form.lite.create_draft`](form/create_draft.md) | 创建智能表单草稿 | `title`, `questions` |
| [`form.lite.update_draft`](form/update_draft.md) | 更新智能表单草稿 | `form_id` |
| [`form.lite.publish_draft`](form/publish_draft.md) | 发布智能表单草稿 | `form_id` |

## 二、表单查询

> 查询智能表单状态、标题与题目结构

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`form.lite.get_form_info`](form/get_form_info.md) | 获取智能表单信息 | `form_id` |

## 工具组合速查

| 用户需求 | 推荐工具组合 |
|----------|-------------|
| 创建智能表单草稿 | `form.lite.create_draft` → `form.lite.update_draft`（可选）→ `form.lite.get_form_info` |
| 用户确认后发布智能表单 | `form.lite.get_form_info` → 确认表单仍为 `Draft` → `form.lite.publish_draft` → `form.lite.get_form_info` |
| 修改草稿题目并返回预览 | `form.lite.get_form_info` → `form.lite.update_draft` → `form.lite.get_form_info` → 按「草稿确认模板」返回文字版表单 |
| 查询表单状态 | `form.lite.get_form_info` |

---

## 草稿确认模板

创建或更新草稿后，先调用 `form.lite.get_form_info` 获取最新表单内容，再按下列模板整理给用户确认。每次调用 `form.lite.update_draft` 修改草稿后，都要重新返回一次文字版表单，方便用户确认修改结果。不要直接粘贴工具返回的原始 JSON。

```markdown
已创建智能表单草稿，发布后将无法修改，请先确认以下内容：

表单名称：{表单标题}
当前状态：草稿
管理页面：{管理页面地址}

题目预览：
| 序号 | 题目 | 类型 | 必填 | 选项/规则 |
|------|------|------|------|-----------|
| 1 | {题目标题} | {题型中文名} | {是/否} | {选择题列出选项；地址题列出层级；其他题型列出校验或填“-”} |

请确认：
- 表单名称是否正确
- 题目是否完整、顺序是否正确
- 题型、必填状态、选项内容是否符合预期

确认无误后回复“确认发布”，我再发布表单并提供填写链接。
```

生成题目预览时，按实际返回字段映射标题、题型、必填状态和选项内容；选择题（`select`、`multiSelect`、`dropdown`）必须展示全部选项，地址题（`address`）展示地址层级，其他题型展示关键校验规则。若工具返回信息不足以生成完整预览，先补充查询或向用户说明缺失项，不要直接发布。

---

## 页面地址

| 页面 | 地址模板 | 示例 |
|------|----------|------|
| 管理页面 | `https://f.wps.cn/ksform/m/result/:form_id` | `https://f.wps.cn/ksform/m/result/f_xxxxx` |
| 填写页面 | `https://f.wps.cn/g/:sid` | `https://f.wps.cn/g/s_xxxxx` |

`form_id` 来自 `form.lite.create_draft`、`form.lite.publish_draft` 或 `form.lite.get_form_info` 返回值；`sid` 来自发布后的表单返回值。草稿状态下 `sid` 通常为空，无法生成填写页面。

---

## 题型速查

| 类型 | 说明 |
|------|------|
| `input` | 文本输入 |
| `telphone` | 电话 |
| `email` | 邮箱 |
| `idcard` | 身份证 |
| `numberInput` | 数字输入 |
| `decimal` | 小数 |
| `select` | 单选 |
| `multiSelect` | 多选 |
| `dropdown` | 下拉 |
| `date` | 日期 |
| `dateTime` | 日期时间 |
| `month` | 月份 |
| `time` | 时间 |
| `address` | 地址 |

---

## 使用注意

| 场景 | 注意事项 |
|------|----------|
| 选择题 | `select`、`multiSelect`、`dropdown` 使用 `selects` 描述选项 |
| 地址题 | `address` 题型可配 `address` 和 `location_type`，层级可选 `province`、`city`、`district`、`town`、`village` |
| 更新草稿 | `questions` 是完整覆盖语义；只改标题时不要传 `questions` |
| 修改后预览 | 每次调用 `form.lite.update_draft` 后，都必须再调用 `form.lite.get_form_info`，并按「草稿确认模板」返回最新文字版表单 |
| 发布确认 | 智能表单发布后无法修改；发布前必须向用户展示表单内容预览并获得明确确认。未确认时只交付草稿管理页面，不调用 `form.lite.publish_draft` |
| 发布草稿 | 发布前先用 `form.lite.get_form_info` 确认表单仍为 `Draft` |
