---
name: ihr-master-data
description: "iHR360 主数据引用解析：名称/编码转 ID，或把业务结果中的 STAFF/DEPARTMENT/职位等一组 ID 批量格式化为名称时必须使用。已有 ID 列表的格式化直接走 master-data batch-get，不逐条调用 Staff/Organization，也不替代业务查询。"
metadata:
  requires:
    bins: ["ihr-cli"]
  cliHelp: "ihr-cli master-data --help"
---

# iHR360 主数据

**CRITICAL — 开始前 MUST 先阅读 [`../ihr-shared/SKILL.md`](../ihr-shared/SKILL.md)，其中包含共享运行规则、鉴权配置和 JSON 协议。**

业务命令保持 raw request/response。只有在以下场景调用本 Skill：

1. 用户给名称或编码，但目标业务接口字段需要主数据 ID。
2. 最终答案面向人阅读，业务结果只有主数据 ID，需要按类型去重后批量格式化。

用户已经提供 ID、下游仍只需要 ID、或响应已包含可信名称时，不解析。

使用 `ihr-cli master-data +search/+get/+batch-get`；逐命令契约分别见 [search](references/ihr-master-data-search.md)、[get](references/ihr-master-data-get.md) 和 [batch-get](references/ihr-master-data-batch-get.md)，完整类型/参数表见 [ihr-master-data-lookup.md](references/ihr-master-data-lookup.md)，跨 Domain 编排见 [ihr-master-data-orchestration.md](references/ihr-master-data-orchestration.md)。业务字段的主数据语义以目标业务公开 Command 契约为准：metadata command 从其 schema 读取字段 Meta，Shortcut 从对应 reference/help 读取公开字段类型；普通字段读取 `type`，`LIST` 递归读取 `items`，`OBJECT` 递归读取 `fields`。只有该类型能匹配 Master Data Registry 的 canonical type 或 alias 时才解析，未注册类型不得调用 Master Data 命令。Flex 类型与固定 Meta 不一致时，由对应 Domain 的 Schema Provider 映射并归一为 canonical 类型。

这三个命令均为 `TENANT_SCOPED + CONFIRM_REQUIRED`。只有用户当前请求已经明确要求名称/编码与 ID 的解析或格式化，或已经确认把该解析作为当前业务查询步骤时，才执行对应命令；如果解析只是 Agent 自行推断出的附加步骤，先确认。不得把“通常安全”或 reference 自声明当作 `AUTO_ALLOWED` 的放宽证据。

目标业务存在数据权限范围时，Domain Skill 必须从该业务公开 Command 契约中取得业务查询实际使用的 `permissionCode`，并原样传给 Master Data 命令。不要按命令名称推导权限，也不要由 Resolver 自动选择 `functionCodes` 的第一项。

主数据引用解析只有这一组统一命令入口。需要把部门名称转成 `departmentId` 时必须使用 `master-data +search --type DEPARTMENT`，不能改用 `organization +orgTree`；需要把 `JOB_CATEGORY`、职位等 ID 显示成名称时必须按类型使用一次 `master-data +batch-get`，不能改用 Organization 列表拼装另一套映射。

业务查询已经成功并给出一组 ID 时，直接对去重后的 ID 执行一次 `master-data +batch-get`。不要重新查询业务数据，不要逐条调用 `staff +get/+search`，也不要用 shell 循环、管道或 raw interface 自己实现分块；分块和 PARTIAL/warnings 由 Resolver 负责。
