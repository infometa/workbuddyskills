---
name: qingflow-skill
description: 轻流无代码平台操作技能 - 创建应用、管理表单数据、处理审批流程、查询和导出数据
version: "1.0.0"
author: "QingFlow"
description_zh: "连接轻流无代码平台，支持创建应用、管理表单数据、处理审批流程、查询与导出数据。触发关键词：轻流、创建应用、表单数据、审批流程、数据查询、数据导出。"
description_en: "Connect to QingFlow no-code platform for app creation, form data management, approval workflow handling, and data query/export. Trigger keywords: qingflow, create app, form data, approval, data query, data export."
---


# 轻流连接器 Skill

本 Skill 提供轻流无代码平台的完整操作能力，包括应用搭建、数据管理、审批流转、数据导出等。

## 认证说明

用户需提供轻流授权码（Token）进行认证。Token 通过 HTTP Header `Authorization: Bearer <token>` 传递。

- Token 获取路径：登录轻流 → 左下角头像 → 个人中心 → 账户信息 → 安全信息 → 授权码
- Token 格式以 `mcp_` 开头
- 如遇认证失败，提示用户检查 Token 是否正确或是否已过期

## 核心能力分类

### 一、身份与工作空间

#### auth_whoami - 查看当前用户信息
查询当前认证用户的身份信息，包括用户 ID、工作空间、角色权限等。**建议在每次会话开始时先调用此工具确认连接状态。**

#### workspace_list - 获取工作空间列表
获取当前用户可访问的所有工作空间列表。

**返回字段**：
| 字段 | 说明 |
|------|------|
| wsId | 工作空间 ID |
| workspaceName | 工作空间名称 |

#### workspace_get - 获取工作空间详情
获取指定工作空间的详细信息。

#### workspace_select - 选择工作空间
切换当前操作的工作空间。

---

### 二、应用管理

#### app_list - 获取应用列表
获取当前工作空间下的所有应用列表。

**返回字段**：
| 字段 | 说明 |
|------|------|
| app_id | 应用 ID |
| app_name | 应用名称 |
| app_key | 应用唯一标识（用于记录操作） |
| package_name | 所属分组名称 |

#### app_get - 获取应用详情
获取指定应用的详细信息，包括字段配置、流程配置等。

**参数说明**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| app_key | string | ✅ | 应用唯一标识 |

---

### 三、应用搭建（Builder）

#### builder_app_schema_apply - 创建/更新应用结构
创建新应用或向已有应用添加字段。**这是搭建应用的核心工具。**

**创建新应用参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| app_name | string | ✅ | 应用名称 |
| package_id | number | - | 所属分组 ID |
| color | string | - | 应用颜色（blue/red/green/yellow/purple/gray） |
| icon | string | - | 应用图标标识 |
| form | array | ✅ | 表单结构定义 |
| form[].section | string | - | 分组名称 |
| form[].rows | array | ✅ | 字段行布局，每行一个字段数组 |
| publish | boolean | - | 是否发布（默认 false） |

**添加字段参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| app_key | string | ✅ | 已有应用标识 |
| add_fields | array | ✅ | 新增字段定义 |
| publish | boolean | - | 是否发布 |

**支持的字段类型**：
| type 值 | 说明 | 额外参数 |
|---------|------|----------|
| text | 单行文本 | - |
| long_text | 多行文本 | - |
| number | 数字 | - |
| single_select | 单选 | options: string[] |
| multi_select | 多选 | options: string[] |
| datetime | 日期时间 | - |
| member | 成员 | - |
| attachment | 附件 | - |
| image | 图片 | - |

**字段通用属性**：
| 属性 | 类型 | 说明 |
|------|------|------|
| name | string | 字段名称 |
| type | string | 字段类型 |
| data_title | boolean | 是否作为数据标题字段 |
| options | string[] | 选项列表（仅 select 类型） |

**创建应用示例**：
```
调用 builder_app_schema_apply，传入：
- app_name: "请假单"
- color: "blue"
- icon: "clock"
- form: [{ section: "请假信息", rows: [[{ name: "请假标题", type: "text", data_title: true }]] }]
- publish: true
```

**添加字段示例**：
```
调用 builder_app_schema_apply，传入：
- app_key: "f2s42dnsc801"
- add_fields: [
    { name: "请假类型", type: "single_select", options: ["事假","病假","年假"] },
    { name: "开始时间", type: "datetime" },
    { name: "请假天数", type: "number" }
  ]
- publish: true
```

#### builder_package_list - 获取分组列表
获取当前工作空间的分组列表，创建应用时需要指定 package_id。

#### builder_app_get - 获取应用搭建信息
获取应用的搭建结构详情，包括字段、布局、视图等完整配置。

#### builder_app_get_fields - 获取字段列表
获取指定应用的所有字段定义。

#### builder_app_get_layout - 获取表单布局
获取应用的表单页面布局配置。

#### builder_app_get_views - 获取视图列表
获取应用的所有视图配置。

#### builder_app_get_flow - 获取流程配置
获取应用的审批流程配置。

#### builder_app_flow_apply - 配置审批流程
设置或更新应用的审批流程节点。

#### builder_app_publish_verify - 发布验证
验证应用是否满足发布条件，发布前必做。

#### builder_app_layout_apply - 更新表单布局
更新应用的表单页面布局。

#### builder_app_views_apply - 更新视图配置
创建或更新应用的视图。

#### builder_app_charts_apply - 配置图表
创建或更新应用的图表配置。

#### builder_app_custom_buttons_apply - 配置自定义按钮
创建或更新应用的自定义按钮。

#### builder_app_resolve - 解析应用配置
解析应用配置，获取完整的搭建信息。

#### builder_app_get_associated_resources - 获取关联资源
获取应用关联的其他资源（图表、按钮、流程等）。

#### builder_app_associated_resources_apply - 配置关联资源
设置应用的关联资源。

#### builder_app_release_edit_lock_if_mine - 释放编辑锁
如果当前用户持有编辑锁，释放它以便其他操作。

#### builder_app_repair_code_blocks - 修复代码块
修复应用中的代码块配置。

#### builder_app_get_buttons - 获取按钮列表
获取应用的所有按钮配置。

#### builder_app_get_charts - 获取图表列表
获取应用的所有图表配置。

#### builder_builder_tool_contract - 获取工具契约
查询 Builder 工具的详细参数格式，**遇到参数不确定时调用此工具获取准确格式**。

**参数说明**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| tool_name | string | ✅ | 工具名称（如 "app_schema_apply"） |

#### builder_solution_install - 安装解决方案
安装预置的解决方案模板。

#### builder_workspace_list - 获取工作空间列表（Builder）
获取工作空间列表，Builder 模式下使用。

#### builder_workspace_get - 获取工作空间详情（Builder）

#### builder_workspace_icon_catalog_get - 获取图标目录
获取可用的应用图标列表，创建应用时选择图标。

#### builder_button_style_catalog_get - 获取按钮样式目录
获取可用的按钮样式列表。

#### builder_role_search - 搜索角色
搜索工作空间中的角色。

#### builder_role_create - 创建角色
在工作空间中创建新角色。

#### builder_member_search - 搜索成员
搜索工作空间中的成员。

#### builder_portal_list - 获取门户列表（Builder）
获取工作空间的门户列表。

#### builder_portal_get - 获取门户详情（Builder）

#### builder_portal_apply - 创建/更新门户

#### builder_portal_delete - 删除门户

#### builder_package_get - 获取分组详情（Builder）

#### builder_package_apply - 创建/更新分组

#### builder_file_upload_local - 上传文件（Builder）
上传文件供 Builder 使用。

#### builder_auth_whoami - 认证信息（Builder）

---

### 四、数据记录管理

#### record_list - 查询记录列表
查询指定应用中的数据记录，支持过滤、排序、分页。

**参数说明**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| app_key | string | ✅ | 应用标识 |
| page_num | number | - | 页码，默认 1 |
| page_size | number | - | 每页条数，默认 20 |
| filter | object | - | 过滤条件 |

#### record_get - 获取单条记录
获取指定记录的详细信息。

#### record_insert - 新增记录
向指定应用中插入新的数据记录。

**参数说明**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| app_key | string | ✅ | 应用标识 |
| data | object | ✅ | 记录数据，key 为字段名 |

**使用示例**：
```
调用 record_insert，传入：
- app_key: "f2s42dnsc801"
- data: { "请假标题": "张三年假申请", "请假类型": "年假", "请假天数": 3 }
```

#### record_update - 更新记录
更新指定记录的数据。

#### record_delete - 删除记录
删除指定记录。

#### record_access - 数据导出（CSV）
导出应用数据为 CSV 格式。

#### record_browse_schema_get - 获取浏览页 Schema
获取记录列表的浏览页配置结构。

#### record_logs_get - 获取记录日志
获取指定记录的操作日志，用于审计追踪。

---

### 五、数据导入导出

#### record_export_start - 启动导出任务
异步导出数据，返回任务 ID。

#### record_export_status_get - 查询导出状态
查询导出任务的执行状态。

#### record_export_get - 获取导出结果
获取已完成的导出任务结果。

#### record_export_direct - 直接导出
同步直接导出数据（数据量较小时使用）。

#### record_import_start - 启动导入任务
异步导入数据。

#### record_import_status_get - 查询导入状态
查询导入任务的执行状态。

#### record_import_schema_get - 获取导入 Schema
获取导入所需的 Schema 定义。

#### record_import_template_get - 获取导入模板
下载导入模板文件。

#### record_import_verify - 验证导入数据
导入前验证数据格式。

#### record_import_repair_local - 修复导入数据
修复导入数据中的问题。

---

### 六、任务与审批流转

#### task_list - 获取待办任务列表
获取当前用户的待办任务列表。

#### task_get - 获取任务详情
获取指定任务的详细信息，包括流程节点、审批人等。

#### task_action_execute - 执行任务操作
对任务执行操作（如同意、拒绝、转交、退回等）。

**参数说明**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| task_id | string | ✅ | 任务 ID |
| action | string | ✅ | 操作类型 |
| comment | string | - | 审批意见 |

#### task_workflow_log_get - 获取流转日志
获取任务的完整流转日志。

#### task_associated_report_detail_get - 获取关联报表
获取任务关联的报表详情。

---

### 七、数据分析

#### chart_get - 获取图表数据
获取指定图表的数据，用于数据分析展示。

#### view_get - 获取视图数据
获取指定视图的数据配置和结果。

---

### 八、文件与成员

#### file_get_upload_info - 获取文件上传信息
获取文件上传所需的配置信息。

#### file_upload_local - 上传本地文件
上传本地文件到轻流。

#### record_member_candidates - 获取成员候选人
获取记录中成员字段可选的成员列表。

#### record_department_candidates - 获取部门候选人
获取记录中部门字段可选的部门列表。

#### directory_search - 搜索目录
搜索工作空间中的成员、部门等目录信息。

---

### 九、代码块

#### record_code_block_run - 运行代码块
执行应用中配置的代码块。

#### record_code_block_schema_get - 获取代码块 Schema
获取代码块的配置结构。

---

### 十、门户

#### portal_list - 获取门户列表
获取工作空间的门户列表。

#### portal_get - 获取门户详情
获取指定门户的详细配置。

---

### 十一、其他

#### feedback_submit - 提交反馈
提交用户反馈信息。

## 工作流程指引

### 场景一：创建新应用
1. 调用 `builder_package_list` 获取分组列表，确定 `package_id`
2. 调用 `builder_app_schema_apply` 创建应用，传入 `app_name`、`form`、`package_id`、`publish: true`
3. 如需添加更多字段，再次调用 `builder_app_schema_apply`，传入 `app_key` 和 `add_fields`
4. 如需配置审批流程，调用 `builder_app_flow_apply`

### 场景二：查询数据
1. 调用 `app_list` 获取应用列表，找到目标应用的 `app_key`
2. 调用 `record_list` 查询记录，可带过滤条件
3. 如需查看详情，调用 `record_get`

### 场景三：处理审批
1. 调用 `task_list` 获取待办任务
2. 调用 `task_get` 查看任务详情
3. 调用 `task_action_execute` 执行审批操作

### 场景四：导出数据
1. 小数据量：调用 `record_export_direct` 直接导出
2. 大数据量：调用 `record_export_start` → `record_export_status_get` 轮询 → `record_export_get` 获取结果

## 注意事项

- 每次会话开始建议先调用 `auth_whoami` 确认连接状态和权限
- 创建应用时，`form` 中的 `rows` 是二维数组，每个子数组代表一行，可包含多个字段实现同行排列
- `builder_app_schema_apply` 同时支持创建应用和添加字段，通过是否传 `app_key` 区分
- 遇到参数格式不确定时，调用 `builder_builder_tool_contract` 获取准确格式
- `record_insert` 的 `data` 对象，key 必须与字段名称完全匹配
- 审批操作完成后，建议调用 `task_list` 确认任务状态已更新
- 导出大量数据时使用异步导出（`record_export_start`），避免超时
- 所有操作在当前选中的工作空间下进行，可通过 `workspace_list` 和 `workspace_select` 切换
