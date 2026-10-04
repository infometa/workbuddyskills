# AI PPT（aippt）工具完整参考文档

本文件包含金山文档 Skill 中 **AI PPT** 相关工具的使用指南。

**适用范围**：`aippt.execute` 通用技能路由接口，支持通过主题描述或已有文档生成演示文稿。

---

## 通用说明

### AI PPT 工具概述

AI PPT 仅包含一个通用接口 `aippt.execute`，通过 `task_type` 参数路由到不同的生成流水线：

| task_type | 场景 | input 构成 |
|---|---|---|
| `theme_ppt` | 用户给出主题描述，AI 联网研究后生成 | `[{type:"text", content:"主题"}]` |
| `doc_ppt` | 用户提供文档（链接 / link_id），基于文档内容生成 | `[{type:"text", content:"指令"}, {type:"link_id", content:"<link_id>"}]` |

### 关键行为

- 每次调用返回 SSE 流，当步骤事件携带 `need_interaction: true` 时 SSE 关闭，需收集用户输入后再次调用
- `input` 与 `interaction_response` 互斥，不同时传
- 最终结果提取方式：从 `upload_cloud.done` payload 的 `link_url` 字段获取
- 每次调用超时设为 1800000 毫秒：--timeout 1800000

### 文档引用方式
文档转 PPT 场景下，`input` 数组中的文档引用使用 `link_id`。

---

## 一、PPT 生成

### 1. aippt.execute

#### 功能说明

`aippt.execute` 是 AI PPT 的**通用技能路由接口**，通过 `task_type` 参数路由到不同的生成流水线。

**已支持的能力：**

| task_type | 名称 | 场景 |
|---|---|---|
| `theme_ppt` | 主题生成 PPT | 用户输入一句话主题，AI 联网研究后生成 |
| `doc_ppt` | 文档生成 PPT | 用户已有文档（金山文档链接 / link_id），AI 基于文档内容生成 |
| `single_page` | 单页生成幻灯片 | 用户输入主题，AI 生成单页 HTML 幻灯片 |

**调用协议：**

每次调用返回一个 SSE 流，推送若干步骤事件（`*.start` / `*.done`）。
当某个事件携带 `need_interaction: true` 时，SSE 流关闭，调用方
收集用户输入后通过 `interaction_response` 发起下一次调用。
如此循环，直到 `*.done` 事件携带最终结果。

不同能力的调用次数不同：有的能力一次调用即可完成，有的需要多轮交互。
具体的调用次数、`input` 内容、`interaction_response` 结构、
以及中间步骤序列，均由各能力自行定义，详见 `response_detail`。

- 每次调用超时设为 1800000 毫秒
- 最后的 `*.done` 事件携带最终生成结果：从 `upload_cloud.done` 取 `link_url`


#### 调用约束

- **前置检查**：首次调用必须明确选择 task_type，并按该 skill 的交互事件继续恢复调用
- **前置检查**（mode=basic）：经典模式（mode=basic）必须在 text 类型 input 项传入 scene_tags 与 style_tags，各恰好 1 个预置标签；禁止省略、禁止传空数组 []、禁止自造标签


**幂等性**：否 — 为流式生成任务，重复调用可能创建重复产物；重试前先确认是否已有进行中或已完成结果


> `input` 与 `interaction_response` 互斥，不同时传
> SSE 流中 `need_interaction: true` 出现时，记录 payload 后等待用户输入，再次调用
> 最终结果从 `upload_cloud.done` payload 的 `link_url` 字段获取云文档链接
> 收到 need_interaction=true 时先收集用户答案，再发起下一次调用，避免空恢复请求
> `mode` 参数在首次和恢复调用中保持一致

#### 调用示例

首次调用 — 主题生成：

```json
{
  "task_type": "theme_ppt",
  "mode": "html",
  "input": [
    {
      "type": "text",
      "content": "长颈鹿主题的儿童科普 PPT"
    }
  ]
}
```

首次调用 — 文档生成：

```json
{
  "task_type": "doc_ppt",
  "mode": "html",
  "input": [
    {
      "type": "text",
      "content": "根据文档生成PPT"
    },
    {
      "type": "link_id",
      "content": "co4Kyv9Ofayq"
    }
  ]
}
```

单页生成幻灯片 — 一次调用完成：

```json
{
  "task_type": "single_page",
  "mode": "html",
  "input": [
    {
      "type": "text",
      "content": "人工智能"
    }
  ],
  "options": {
    "width": 1280,
    "height": 720
  }
}
```

经典模式 — 主题生成（必填 scene_tags / style_tags，各 1 个）：

```json
{
  "task_type": "theme_ppt",
  "mode": "basic",
  "input": [
    {
      "type": "text",
      "content": "AI发展趋势",
      "scene_tags": [
        "总结汇报"
      ],
      "style_tags": [
        "科技风"
      ]
    }
  ]
}
```

经典模式 — 文档生成（默认改写，generate_type=3）：

```json
{
  "task_type": "doc_ppt",
  "mode": "basic",
  "options": {
    "generate_type": 3
  },
  "input": [
    {
      "type": "text",
      "content": "根据文档生成PPT",
      "scene_tags": [
        "行业报告"
      ],
      "style_tags": [
        "商务风"
      ]
    },
    {
      "type": "link_id",
      "content": "co4Kyv9Ofayq"
    }
  ]
}
```

经典模式 — 文档生成（保持原文，generate_type=2）：

```json
{
  "task_type": "doc_ppt",
  "mode": "basic",
  "options": {
    "generate_type": 2
  },
  "input": [
    {
      "type": "text",
      "content": "尽量保持原文生成PPT",
      "scene_tags": [
        "总结汇报"
      ],
      "style_tags": [
        "简约风"
      ]
    },
    {
      "type": "link_id",
      "content": "co4Kyv9Ofayq"
    }
  ]
}
```

恢复调用 — 提交 follow_up 答案（所有 task_type 通用，下面以 doc_ppt，mode 为 html 为例）：

```json
{
  "task_type": "doc_ppt",
  "mode": "html",
  "interaction_response": {
    "type": "follow_up",
    "data": {
      "session_id": "9dbea4d8-b9f7-419c-a4ad-208d4515b8d5",
      "checkpoint_id": "419e8c77-5442-459e-87eb-2637ba53e132",
      "interrupt_id": "45caf5dc-2dd4-48a7-9ba3-8ba2edc67cdd",
      "items": [
        {
          "type": "choice",
          "field": "制作目标",
          "label": "制作目标",
          "options": [
            "内部技术培训宣讲"
          ]
        },
        {
          "type": "multi_choice",
          "field": "重点方面",
          "label": "重点方面",
          "options": [
            "生物特性",
            "文化关联"
          ]
        },
        {
          "type": "text",
          "field": "补充说明",
          "label": "补充说明",
          "text_input": "重点突出接入步骤"
        }
      ]
    }
  }
}
```


#### 参数说明

- `task_type` (string, 必填): 技能类型，决定执行哪条生成流水线。
枚举值：`theme_ppt`（主题生成 PPT）/ `doc_ppt`（文档生成 PPT）/ `single_page`（单页生成幻灯片）

- `mode` (string, 可选): 生成模式。`html`（HTML 渲染）/ `basic`（经典简约模式，一次调用完成）。默认 `html`。
`basic` 时须在 `input` 的 `text` 项传入 `scene_tags`、`style_tags` 各 1 个（必填，见 `param_detail`）。

- `input` (array[object], 可选): 技能输入内容数组，每项为 `{type, content, ...}` 对象。与 `interaction_response` 互斥。
type 枚举：
- `text`：文本指令或主题描述
- `link_id`：分享链接 ID

当 `mode` 为 `basic` 时，`text` 类型的 input 项**必须**携带：
- `scene_tags`：场景标签数组，**恰好 1 个**，取值见 `param_detail`
- `style_tags`：风格标签数组，**恰好 1 个**，取值见 `param_detail`

- `interaction_response` (object, 可选): 用户对交互问卷的回答，与 `input` 互斥。
结构固定为 `{type, data}`，其中 `type` 和 `data` 的内容因 skill 而异，
详见 `response_detail` 中各 skill 的说明。

- `options` (object, 可选): 生成选项。
- `task_type=single_page` 时必须传入，固定为 `{"width": 1280, "height": 720}`
- `task_type=doc_ppt` 且 `mode=basic` 时可选传入 `generate_type`：用户明确要求保持原文 → `2`；否则默认 `3` 或不传


### `mode=basic` 经典模式约束

**必填**（写入 `text` 类型 input 项）：

| 字段 | 要求 |
|---|---|
| `scene_tags` | 数组，**恰好 1 个**，取值只能来自预置场景列表 |
| `style_tags` | 数组，**恰好 1 个**，取值只能来自预置风格列表 |

**预置场景**：财务系统、生产管理、教学课件、毕业答辩、培训课件、企业招聘、企业宣传、企业文化、企业培训、党政党建、政府报告、商业计划书、活动策划、营销计划、行业报告、产品发布会、竞聘述职、通用PPT、总结汇报

**预置风格**：简约风、商务风、渐变风、中国风、小清新、可爱卡通、科技风

**分类规则**：用户已指定则映射到最接近预置标签；未指定则内部自动选择（禁止向用户二次确认）；禁止省略字段或传 `[]`。完整流程见 `references/workflows/aippt-full-text.md` 执行流程 B。

**`doc_ppt` 选填** `options.generate_type`：用户明确要求保持原文 → `2`；否则 `3` 或不传。


#### 返回值说明

```json
// 最终结果在 upload_cloud.done：
{
  "id": "skill-xxx",
  "delta": {
    "type": "upload_cloud.done",
    "payload": {
      "file_id": "100249092919",
      "file_name": "AI发展趋势.pptx",
      "link_url": "https://www.kdocs.cn/l/clq08Q2vM2Ec"
    }
  },
  "is_partial": false
}

```

SSE 流通过 `message` 事件推送步骤状态，最终以 `finish` 事件结束。
当某步骤事件携带 `need_interaction: true` 时，SSE 流关闭，需要收集用户输入后再次调用。

---


## 工具速查表

| # | 工具名 | 分类 | 功能 | 必填参数 |
|---|--------|------|------|----------|
| 1 | `aippt.execute` | generate | AI PPT 通用执行接口，按 task_type 路由生成 | `task_type` |

## 附录

### 错误处理

| 情况 | 说明 |
|------|------|
| SSE error 事件 | 包含错误码和描述，检查 task_type 和 input 参数是否正确 |
| 超时 | 单次调用上限 1800000 毫秒，超时需重新发起 |
| 云空间已满 | PPT 已成功生成，但云空间不足无法自动保存。响应 `data.pptx_url` 含临时下载链接。根据 `message` 判断是个人还是企业空间，按下方对应模板回复用户 |

#### 云空间已满 — 回复模板

根据 `message` 中包含「个人」还是「企业」选择对应模板。将模板中的 `{主题名}` 替换为实际生成的 PPT 主题，`{下载链接}` 替换为 `data.pptx_url`。

**个人云空间已满：**

```
✅ {主题名}幻灯片已生成！

💾 暂存提示：您的云空间已满，文件暂时保存在本地
🔗 临时下载链接（24小时内有效）：[点击下载]({下载链接})

📌 云空间已满，按以下步骤释放空间：
1. WPS客户端 → 我的 → 云空间管理
2. 删除不需要的文件
3. 重新生成PPT，文件将自动同步
```

**企业云空间已满：**

```
✅ {主题名}幻灯片已生成！

💾 暂存提示：您的企业云空间已满，文件暂时保存在本地
🔗 临时下载链接（24小时内有效）：[点击下载]({下载链接})

💡 同步至云端（任选一种）：
1. 自行清理：前往「WPS客户端 → 我的 → 云空间管理」删除不需要的文件
2. 申请扩容：联系企业管理员释放空间
清理/扩容后返回此页面，重新生成PPT，文件将自动同步
```
