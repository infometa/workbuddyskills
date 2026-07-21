# AI 生成演示文稿（全文）

> aippt.execute 单接口全文生成链路：两次调用完成需求澄清与生成，支持主题/文档两种来源，固定使用 html 模式

**适用场景**：用户希望通过主题描述或已有文档生成演示文稿。

**触发词**：生成PPT、生成演示文稿、做PPT、做个PPT、文档转PPT、文件转PPT、文档生成PPT、把文档做成PPT、根据文档生成演示文稿

## 执行流程

> **前置阅读**：执行前必须阅读 `references/aippt.md` 了解相关工具的使用方法和参数要求。
> 该流程使用 `aippt.execute` 单接口完成 PPT 生成完整链路。
> 调用前需确定两个核心参数：**skill_type**（生成来源），**mode** 固定为 `html`。
> 两次调用完成全部步骤：首次调用触发 follow_up 问题，收集用户选择后发起第二次调用，服务端自动完成大纲、风格美化、生成并返回云文档链接。
> 每次调用超时设为 **1800000 毫秒**。约每页 60 秒。

### 参数决策

#### 1. 确定 skill_type（根据用户输入判断）

| 场景 | skill_type | input |
|---|---|---|
| 用户给出主题/描述，无文档 | `theme_ppt` | `[{type:"text", content:"用户主题"}]` |
| 用户提供了文档链接 | `doc_ppt` | `[{type:"text", content:"根据文档生成PPT"}, {type:"v7_file_id", content:"<link_id>"}]` |

> `v7_file_id`：从金山文档链接路径末尾提取 link_id（如 `https://365.kdocs.cn/l/xxxxx` 中的 `xxxxx`），无需先调用 get_share_info。

#### 2. mode（固定值）

始终使用 `mode="html"`，无需向用户确认。 

### 执行流程

```
步骤 1: aippt.execute(skill_type=<场景对应值>, mode="html", input=<场景对应input>)
        → SSE 推进到 get_questions.done（need_interaction=true）
        → 从 payload 提取 interaction_type="follow_up"
        → 记录 session_id、checkpoint_id、interrupt_id（恢复调用必须原样回传）

步骤 2: 向用户展示 follow_up 问题（AskQuestion），收集选择
        → choice 题：单选，展示 options，可自定义（allow_custom=true）
        → multi_choice 题：多选
        → text 题：对话确认，可留空
        → 整理为 interaction_response.data.items: [{type, field, label, options/text_input}]

步骤 3: aippt.execute(skill_type=<同步骤1>, mode="html", interaction_response={
            type: "follow_up",
            data: {
                session_id: "<来自步骤1>",
                checkpoint_id: "<来自步骤1>",
                interrupt_id: "<来自步骤1>",
                items: [...]
            }
        })
        → SSE 推进：gen_outline.start → gen_outline.done →
          style_generate.start → style_generate.done → gen_ppt.start → gen_ppt.done → finish
        → 从 gen_ppt.done payload 的 doc_url 字段提取云文档链接，展示给用户
```
