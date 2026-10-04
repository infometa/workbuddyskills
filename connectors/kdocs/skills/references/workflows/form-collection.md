# 表单收集

> 根据用户需求设计并创建智能表单，发布后生成填写链接

**适用场景**：用户需要创建信息收集表单（报名、登记、问卷等），希望获得可分享的填写链接

**触发词**：表单收集、收集表、问卷、报名表单、登记表单、信息登记、宠物登记、活动报名

- 用户需要创建可分享的表单用于收集信息

**工具链**：AI 设计题目 → `form.lite.create_draft` → `form.lite.publish_draft` → 返回填写链接

## 涉及工具

| 工具 | 服务 | 用途 |
|------|------|------|
| `form.lite.create_draft` | form | 创建表单草稿（含题目） |
| `form.lite.publish_draft` | form | 发布草稿为正式表单 |

## 执行流程

**步骤 1**：根据用户场景设计题目列表，推断表单标题和 questions 结构（题型参考 `references/form.md`）

**步骤 2**：将设计的题目返回给用户确认，格式：
"已为你设计好「{title}」表单，包含以下题目：{questions}，确认创建？"
→ 用户要求调整则修改后再次确认，用户确认则进入下一步

**步骤 3**：`form.lite.create_draft(title, questions)` 创建草稿 → 验证返回 `form_id` 非空且 `type == "Draft"`

**步骤 4**：`form.lite.publish_draft(form_id)` 发布 → 验证返回 `type == "Release"` 且 `sid` 非空

**步骤 5**：返回给用户：
- 管理页面：`https://f.wps.cn/ksform/m/result/{form_id}`
- 填写页面：`https://f.wps.cn/g/{sid}`
