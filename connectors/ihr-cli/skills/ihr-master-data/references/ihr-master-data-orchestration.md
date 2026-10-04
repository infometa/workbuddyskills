# 跨 Domain 主数据编排

## 输入名称转 ID

1. 先读取目标业务公开 Command 契约：metadata command 使用其 schema，Shortcut 使用对应 reference/help。
2. 以随包 Master Data Registry 或 `ihr-cli master-data --help` 确认当前运行版本支持的 canonical type；当前可读目录见 [ihr-master-data-lookup.md](ihr-master-data-lookup.md#支持的主数据类型)。
3. 从公开契约的原始字段 Meta 读取类型：普通字段读取 `type`，`LIST` 递归读取 `items`，`OBJECT` 递归读取 `fields`。没有明确类型的开放字段不按名称猜测。
4. 字段类型必须匹配 Registry canonical type 或 alias；alias 先归一为 canonical type。未注册类型保持 raw，不调用 Master Data Resolver。
5. Flex 类型与固定 Meta 不一致时，使用对应 Domain Schema Provider 的映射结果；例如后端 `JOBCATEGORY` 映射为 canonical `JOB_CATEGORY`。映射失败时保持 raw，不猜类型。
6. 目标业务存在数据权限范围时，从业务公开 Command 契约取得该业务查询实际使用的 `permissionCode`。存在多个候选功能点时，由 Domain Skill 按目标业务命令的真实权限逻辑选择，Resolver 不自动取第一项。
7. 字段要求主数据 ID 且用户给的是名称/编码时，调用 `master-data +search`；有明确 permissionCode 时同时传 `--permission-code`。
8. 唯一精确候选可直接使用；多个候选要向用户展示最小必要的名称、编码、路径等信息后消歧。
9. 把选定 ID 写入业务命令，业务命令本身仍保持 raw contract。

这是强制路由：不要为了找部门 ID 改用 `organization +orgTree`、部门 nameMap、raw interface 或后端内部接口。统一 Resolver 才负责 canonical ID、数据权限 scope、同名路径消歧和缓存。

示例：查询研发3组考勤日报时，先解析 `DEPARTMENT` 得到数字部门 ID，再调用考勤业务命令。

## 输出 ID 格式化

1. 只在最终答案需要面向人阅读时处理。
2. 从业务公开 Command 契约的响应字段 Meta 识别字段类型：普通字段读取 `type`，`LIST` 递归读取 `items`，`OBJECT` 递归读取 `fields`。
3. 只收集能够匹配 Registry canonical type 或 alias 的字段；alias 先归一为 canonical type，再按 type 收集并去重 ID。未注册类型保持 raw。
4. Flex 字段使用 Domain Schema Provider 已映射的类型和返回表示；响应已是可信名称时不再 BatchGet。
5. 每种 type 调用一次 `master-data +batch-get`。来源业务有明确 permissionCode 时，必须传入与原业务查询相同的 `--permission-code`。
6. 生成最终自然语言答案时展示名称；不要替换或修改原业务命令的 raw response。
7. 缺失或无权限的 ID 原样保留，并输出 warning；不能让格式化失败导致原业务查询失败。

已确认需要格式化时，不要用 `organization +jobCategories`、组织列表或逐条 Search 代替 BatchGet；这些绕行会复制 Provider 选择、权限和错误处理规则。

## 不调用的场景

- 用户已经提供合法 ID。
- 下游步骤只需要 ID。
- 响应已经包含可信名称。
- 字段 Meta 没有声明已注册的 canonical 主数据类型，且 Domain Schema Provider 也没有提供明确映射。
- 只是查询 Staff/Organization 业务数据；这时仍调用对应业务 Skill。

Domain Skill 决定何时解析、字段类型映射和使用哪个业务 permissionCode；统一 Resolver 决定如何调用 Provider、缓存、权限 scope 和错误分类。
