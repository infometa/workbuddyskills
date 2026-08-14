# Custom SQL 与 Backend Function 工作流

## 目的

统一 `sql` / `bff` 命令组的使用方式，避免在 app 未明确、Custom SQL / Backend Function 标识未确认时直接执行。

## 共同原则

`sql` 命令组用于消费 Custom SQL；Custom SQL 和 Backend Function 都不是“先猜再试”的能力。

运行时复用既有能力的标准顺序：

1. 先判断 app 是否明确
2. 不明确时，先做应用决议
3. 从用户明确输入、业务 Skill 固定契约、可信 Service Tree、前序已确认上下文或可信 KB 候选确认 `sqlCode` / Backend Function ENDPOINT `functionName`
4. 先执行 `detail`，只核对该命令实际返回的字段；缺失契约继续视为未知
5. 判断真实副作用、权限和用户授权，条件满足时才执行 `exec`

Detail 成功只证明能力存在，不代表可以自动执行。副作用、权限或确认语义不明确时，不自动执行。

`sql detail` 返回 Custom SQL 的名称、数据库和 SQL 内容；`bff detail` 返回 Backend Function ENDPOINT 名称、描述、版本和更新时间等元数据。它们都不会替业务 Skill 补齐参数结构、业务口径和真实副作用契约。

运行态只消费已发布且契约可信的业务能力，当前类型包括但不限于已治理 Dataset / Instant API（含 `filter`、`getOne`、`aggregate`）、Custom SQL 和 Backend Function。Lovrabet Runtime CLI 尚未提供 Flow 运行态入口，因此 Flow 当前不可消费；未暴露可信入口、输入输出或副作用契约的能力不猜测命令，只对受影响范围输出“不判定”。

## Custom SQL 工作流

1. app 不明确时，按 [app-resolution.md](app-resolution.md) 决议：有 `defaultApp` 先验证默认候选，验证不成立再扩大到应用列表：

```bash
# 默认候选验证不成立时
lovrabet app list
```

2. 如果没有 `sqlCode`，从业务 Skill、可信 Service Tree、前序已确认上下文或可信 KB 候选定位；仍无法唯一定位时停止，不猜测
3. 先看详情：

```bash
lovrabet sql detail --sqlcode <code>
```

4. 核对应用、查询口径、参数和数据范围；条件满足时才执行：

```bash
lovrabet sql exec --sqlcode <code> --params '<json>'
```

## Backend Function 工作流

1. app 不明确时，按 [app-resolution.md](app-resolution.md) 决议：有 `defaultApp` 先验证默认候选，验证不成立再扩大到应用列表：

```bash
# 默认候选验证不成立时
lovrabet app list
```

2. 如果没有函数信息，从业务 Skill、可信 Service Tree、前序已确认上下文或可信 KB 候选定位；仍无法唯一定位时停止，不猜测
3. 先看详情：

```bash
lovrabet bff detail --name <functionName>
```

4. `bff detail` 成功可确认当前应用能按名称解析该运行态 Backend Function ENDPOINT，但不会返回输入输出、函数类型或副作用契约；参数结构、输入输出和真实副作用由可信业务 Skill 或平台已确认契约补齐，参数值、执行意图和执行授权可由用户明确提供；条件满足时才执行：

```bash
lovrabet bff exec --name <functionName> --params '<json>'
```

运行态只主动发现和直接调用 ENDPOINT。HOOK 绑定到 Dataset 的一个具体 Instant API operation 及 BEFORE/AFTER 节点；Agent 不直接调用 HOOK，而是在可信契约确认绑定关系后执行对应 `data` 命令。基础访问权限由平台 RBAC 控制；HOOK 仅用于补充个性化校验和处理。服务端成功解析并加载绑定脚本时，HOOK 在同一请求管线中执行；已执行的 BEFORE HOOK 失败会阻止主操作。绑定查询或脚本加载异常会记录日志并跳过 HOOK，补充逻辑可能被跳过，因此不得把 HOOK 作为必须强制执行的合规或业务校验唯一保障。AFTER HOOK 失败时不能据此断言主操作已回滚或直接重试，应先按业务唯一键只读回查。

## app-config value 查询

`lovrabet app-config get <key>` 按当前 appCode 和 key 查询运行态 app-config value：

```bash
lovrabet app-config get example_api_key --format compress
```

命令的 `data` 直接返回 value；该值可能包含敏感信息，不要写入本地配置、缓存、日志、`--params` 或业务 Skill 入参。

示例 key 仅用于说明；实际执行必须使用用户或业务 Skill 明确给出的 key，不能猜测或默认使用示例 key。Agent 执行 Skill 时同样调用该 CLI 获取 value，不创建取配置 Backend Function；value 只在当前任务内消费，除非用户明确要求，否则最终答复不重复展示。

## personal BFF 工作流

personal BFF 是当前用户在当前应用下维护的个人脚本，适合做轻量数据编排，或先验证一个临时业务接口的返回形状。

标准顺序：

1. `lovrabet personal-bff list` 查当前用户已有脚本
2. `lovrabet personal-bff detail --id <id>` 查看现有脚本后再更新
3. 从本地脚本文件 `create` 或 `update`
4. `lovrabet personal-bff exec --id <id> --params '<json>' --format compress` 确认返回形状
5. 再把结果形状用于下游调用或交付说明

```bash
lovrabet personal-bff create --name loadOrders --file ./load-orders.js --dry-run
lovrabet personal-bff exec --id <id> --params '{"status":"active"}' --format compress
```

执行前确认目标脚本 ID、输入参数和已知副作用；执行后核对返回字段、空态和错误形状。

## 复杂业务写入与频率保护

多数据集写入、跨步骤依赖、upsert、执行时需要 handoff 结果或需要幂等恢复的业务动作，优先封装在 Backend Function 中，再通过 `lovrabet bff exec` 调用。Agent 不应在执行时直接拼多次 `data create` 或 `data batchCreate` 绕过业务入口。Backend Function 写入类执行仍需先确认业务授权、Studio 权限和人工确认语义；CLI 将 `bff exec` 标记为 `read`，不等同于免审批写入。

推荐 Backend Function 入参包含业务级 `requestId` 或 `idempotencyKey`。函数内部按业务唯一键先只读核对，确认不存在再写入；遇到频率保护、超时或客户端没有拿到成功结果时，等待后再次只读核对，确认没有落地再重试。只有同一数据集多条新增时，函数或 CLI service 内部才适合使用 `batchCreate` 减少请求次数。

Backend Function 返回值应包含 handoff 所需结果：已创建记录、已复用记录、失败步骤、是否可重试和 traceId。这样 Agent 拿到的是业务结果，而不是一串低层写接口的临场拼装结果。

## 什么时候可以跳过 app 决议

以下情况可以直接进入 `sql detail` 或 `bff detail`，但不能跳过执行前的风险与授权判断：

- 用户已经给了 `--appcode`
- 用户已经给了 `--app <name>`
- 当前对话已经明确在某个 app 上下文中继续
- 用户明确说“当前应用”“默认应用”，且没有新的业务域线索

`defaultApp` 只是默认候选，不是强上下文。Custom SQL 和 Backend Function 经常按业务域分布在不同 app 中；用户提到新的业务域或业务对象且未指定 app 时，先把 `defaultApp` 当第一个候选验证，验证不成立再扩大到应用列表。

## 不要这样做

- 不要在不知道 `sqlCode` 的情况下直接跑 `sql exec`
- 不要在不知道函数名的情况下直接跑 `bff exec`
- 不要在 app 未明确时直接默认当前 app 一定对

## 推荐配合命令

- app 决议：`lovrabet app list`
- Custom SQL 标识来源：用户明确输入、业务 Skill、可信 Service Tree、前序已确认上下文或可信 KB 候选
- Backend Function 标识来源：用户明确输入、业务 Skill、可信 Service Tree、前序已确认上下文或可信 KB 候选
- personal BFF：`lovrabet personal-bff list/detail/create/update/exec`
