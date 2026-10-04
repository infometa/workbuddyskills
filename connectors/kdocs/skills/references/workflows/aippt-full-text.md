# AI 生成演示文稿（全文）

> aippt.execute 单接口全文生成链路：支持 html（两次调用 + follow_up）和 basic（一次调用，经典简约模式）两种模式，覆盖主题/文档场景

**适用场景**：用户希望通过主题描述或已有文档生成演示文稿。

**触发词**：生成PPT、生成演示文稿、做PPT、做个PPT、文档转PPT、文件转PPT、文档生成PPT、把文档做成PPT、根据文档生成演示文稿、原子化生成PPT、生成全文PPT、生成完整PPT、全文生成演示文稿、做一份完整PPT、生成整套PPT、文档生成完整PPT

## 执行流程

> **前置阅读**：执行前必须阅读 `references/aippt.md` 了解相关工具的使用方法和参数要求。
> 该流程使用 `aippt.execute` 单接口完成 PPT 生成完整链路。
> 调用前需确定两个核心参数：**task_type**（生成来源）和 **mode**（生成模式）。
> 每次调用超时设为 **1800000 毫秒**：--timeout 1800000。

### 参数决策

#### 1. 确定 task_type（根据用户输入判断）

| 场景 | task_type | input |
|---|---|---|
| 用户给出主题/描述，无文档 | `theme_ppt` | `[{type:"text", content:"用户主题"}]` |
| 用户提供了文档链接 | `doc_ppt` | `[{type:"text", content:"根据文档生成PPT"}, {type:"link_id", content:"<link_id>"}]` |

#### 2. 确定 mode（生成模式）

| mode | 名称（展示给用户） | 调用次数 | 说明 |
|---|---|---|---|
| `html` | **专业模式** / 智能布局 | 两次 + follow_up | 支持多文档；有问卷交互 |
| `basic` | **快速模式** / 经典模式 | 一次 | 经典简约；**须传 `scene_tags`/`style_tags` 各 1 个**；**不支持多文档** |

> 单页生成（`task_type=single_page`）固定 `mode=html`，不走本节路由。详见 `references/workflows/aippt-single-page.md`。

执行原则：**自上而下依次匹配，命中任一规则立即执行、终止后续判断（短路）**。

**优先级 1：全局强制约束（最高，不可绕过）**

- **条件**：用户上传 **≥2 份文档**（多个本地文件、多个云文档链接、`<referenced_files>` 含多个文件）
- **执行**：强制 `mode=html`（专业模式）；须告知用户多文档场景需使用专业模式
- 底层限制：快速模式（`basic`）不支持多文档输入

**优先级 2：用户显式意图硬路由（无强制约束时）**

2.1 直接路由【快速模式】`mode=basic`（满足任一即生效，**跳过模式确认弹窗**）：

1. 用户明确表达快速生成诉求，命中任一关键词：快点生成、快速生成、赶紧做、一键生成、2分钟生成、越快越好、不要问卷、快速模式、经典模式
2. 当前对话历史中用户**已选定快速模式**

2.2 直接路由【专业模式】`mode=html`（满足任一即生效，**跳过模式确认弹窗**）：

1. 用户明确提及：专业模式、专业一点、精细可控、智能布局、自定义大纲、详细偏好、5分钟精美PPT
2. 当前对话历史中用户**已选定专业模式**

**优先级 3：兜底（未命中以上规则）**

触发场景（满足其一）：用户仅下发简单指令（生成PPT / 做PPT / 文档转PPT 等）**无显式模式偏好**；或快速、专业两类关键词**意图冲突**无法判定。

**执行**：弹出模式选择（AskQuestion），**仅使用用户侧文案**，不暴露 `html` / `basic`：

| 选项 | 内部映射 |
|------|----------|
| 专业模式（智能布局，可问卷定制，适合精细控制） | `mode=html` |
| 快速模式（经典简约，一次生成完成） | `mode=basic` |

用户选定后，本会话后续同任务沿用该选择（快速模式归入 2.1 第 2 条，专业模式归入 2.2 第 2 条）。

向用户展示模式时**仅使用"名称"列文案**，不暴露 `html`/`basic`。确定 `mode` 后按下文 **执行流程 A** 或 **执行流程 B** 继续。

---

### 执行流程 A：html / 专业模式（两次调用）

> 前提：`mode` 已确定为 `html`（见上文 **#### 2**）。

```
步骤 1: aippt.execute(task_type=<场景对应值>, mode="html", input=<场景对应input>)
        → SSE 推进到 get_questions.done（need_interaction=true）
        → 从 payload 提取 interaction_type="follow_up"
        → 记录 session_id、checkpoint_id、interrupt_id（恢复调用必须原样回传）

步骤 2: 向用户展示 follow_up 问题（AskQuestion），收集选择
        → choice 题：单选，展示 options，可自定义（allow_custom=true）
        → multi_choice 题：多选
        → text 题：对话确认，可留空
        → 整理为 interaction_response.data.items: [{type, field, label, options/text_input}]

步骤 3: aippt.execute(task_type=<同步骤1>, mode=<同步骤1>, interaction_response={
            type: "follow_up",
            data: {
                session_id: "<来自步骤1>",
                checkpoint_id: "<来自步骤1>",
                interrupt_id: "<来自步骤1>",
                items: [...]
            }
        })
        → SSE 推进：gen_outline.start → gen_outline.done →
          style_generate.start → style_generate.done → gen_ppt.start → gen_ppt.done →
          upload_cloud.start → upload_cloud.done → finish
        → 从 upload_cloud.done payload 的 link_url 字段提取云文档链接，展示给用户
```

---

### 执行流程 B：basic / 快速模式（一次调用）

> 前提：`mode` 已确定为 `basic`（见上文 **#### 2**）。

#### 风格/场景分类（必填）

调用前须为 `text` 类型 input 项填入 `scene_tags`、`style_tags` 各恰好 1 个；`doc_ppt` 的 `options.generate_type` 按用户意图选填。预置列表与分类规则见 `references/aippt.md` → `aippt.execute` → **param_detail**（`mode=basic` 经典模式约束）。

**自动选择参考**（用户未指定 scene/style 时，内部映射，不向用户确认）：

| 主题特征 | 推荐 scene | 推荐 style |
|---|---|---|
| 工作总结、复盘、汇报 | 总结汇报 | 商务风 |
| 行业分析、调研报告 | 行业报告 | 简约风 |
| 产品发布、新品介绍 | 产品发布会 | 科技风 |
| 培训、课件、学习 | 培训课件 / 教学课件 | 简约风 |
| 答辩、毕业相关 | 毕业答辩 | 简约风 |
| 党建、政务 | 党政党建 / 政府报告 | 中国风 |
| 营销、活动 | 营销计划 / 活动策划 | 渐变风 |
| 无法归类 | 通用PPT | 商务风 |

#### SSE 事件序列（basic）

| 事件类型 | 说明 |
|---|---|
| `auth_check.start` / `.done` | 权限检查 |
| `gen_outline.start` / `.done` | 大纲生成（payload 含 `root_node` 结构化大纲） |
| `get_templates.start` / `.done` | 模板推荐（payload 含 `items` 模板列表） |
| `gen_ppt.start` / `.done` | 幻灯片生成（payload 含 `slide_file_urls`） |
| `upload_cloud.start` / `.done` | 上传云空间（payload 含 `file_id`、`file_name`、`link_url`） |
| `done` | 流程结束，`finish_reason: "stop"` |

```
步骤 0: 内部完成场景/风格分类（不向用户确认）
        → 确定 scene_tags、style_tags 各 1 个
        → doc_ppt 时按意图决定是否传 options.generate_type

步骤 1a（主题场景）: aippt.execute(task_type="theme_ppt", mode="basic", input=[{
          type: "text",
          content: "用户主题",
          scene_tags: ["总结汇报"],
          style_tags: ["商务风"]
        }])
        → auth_check → gen_outline → get_templates → gen_ppt → upload_cloud → done

步骤 1b（文档场景，默认润色改写）: aippt.execute(
          task_type="doc_ppt",
          mode="basic",
          options: { generate_type: 3 },
          input=[
            {type: "text", content: "根据文档生成PPT", scene_tags: ["总结汇报"], style_tags: ["商务风"]},
            {type: "link_id", content: "<link_id>"}
          ])
        → auth_check → gen_outline → get_templates → gen_ppt → upload_cloud → done

步骤 1c（文档场景，保持原文）: 同上，options: { generate_type: 2 }

步骤 2: 从 upload_cloud.done payload 提取 link_url，展示给用户
```
