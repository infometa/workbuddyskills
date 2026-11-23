# Backend Function 工作流

查看和执行 Lovrabet 平台的 Backend Function。CLI 命令组保留技术标识 `bff`，用于查看详情和执行。

## 前置条件

- `bff detail` 和 `bff exec` 使用当前 CLI 认证，默认推荐 **accessKey（client-ak）**
- 需要个人脚本时使用 `personal-bff` 命令组，不要把平台正式 Backend Function 与 Personal Backend Function 混成同一个资源

## Backend Function 类型边界

- **ENDPOINT**：独立业务端点，是运行态可以主动 `detail`、并在条件满足时 `exec` 的候选。
- **COMMON**：只供其他 Backend Function 内部依赖，不是业务 Agent 可直接执行的入口。
- **HOOK**：绑定到某个 Dataset 的一个具体 Instant API operation 及 BEFORE/AFTER 节点，是该请求管线中的执行扩展，不是独立业务入口。

运行态只主动发现和直接调用 ENDPOINT；Agent 不直接执行 `bff detail` 或 `bff exec` 来消费 HOOK。HOOK 是否已绑定必须来自可信业务 Skill 或平台已确认契约；绑定已确认时，Agent 执行对应的 `data` 命令。服务端成功解析并加载绑定脚本时，HOOK 会在同一 Instant API 请求管线中执行。COMMON 仅作为 ENDPOINT 或 HOOK 的内部依赖。未知函数名不能用 COMMON 或 HOOK 代替，也不能猜测。

## HOOK 执行与失败边界

- BEFORE HOOK 可以校验或调整输入。已成功加载并执行的 BEFORE HOOK 失败时，平台会阻止对应 Instant API 主操作，Agent 应报告失败，不继续假定数据已写入。
- 基础访问权限由平台 RBAC 控制；HOOK 仅用于补充个性化校验和处理。绑定查询或脚本加载异常会记录日志并跳过 HOOK，补充逻辑可能被跳过，因此不得把 HOOK 作为必须强制执行的合规或业务校验唯一保障。
- AFTER HOOK 在 Instant API 主操作执行后运行。AFTER HOOK 失败时，不能据此断言主操作已回滚，也不能在缺少原子回滚、幂等或明确可重试契约时直接重试。
- 对 `create`、`batchCreate`、`update` 或 `delete` 的返回错误、超时或 AFTER HOOK 失败，先按业务唯一键只读回查主记录和必要的后置结果；只有确认未落地且重试契约可信时才重试。
- `--dry-run` 只预览 CLI 请求，不进入真实 Instant API 请求管线，也不会触发 HOOK。

## 应用与能力定位

应用选择统一遵循[默认应用与应用发现](../guides/app-resolution.md)：未指定目标时先查默认 AppCode（顶层 `appcode` 或 `defaultApp` 解析结果）；仅在成功查询无合理匹配、核对筛选条件且用户未限定范围后，才扩大只读发现。认证、权限或连接错误不触发跨应用重试。

从业务 Skill、可信 Service Tree、前序已确认上下文或可信 KB 候选定位能力，同时核对所属 AppCode；只有应用明确仍不足以直接执行，能力标识、参数与副作用契约也必须明确。缺少可信标识时停止，不猜测，也不通过跨应用逐个执行来探测。

`--app` / `--appcode` 只对本次命令生效。临时选择其他应用后，后续每条 `detail`、`data` 或执行命令都必须显式携带该目标；资源标识必须与发现它的 AppCode 配对，不能依靠上一条命令改变默认值。

## bff detail — 查看 Backend Function 详情

```bash
lovrabet bff detail --name <functionName>
```

| Flag | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--name` | string | **是** | 已知的 Backend Function ENDPOINT 名称，精确匹配 |

**输出**：`appCode`、函数名、描述、版本和更新时间。该命令按 `appCode + functionName` 查询运行态 ENDPOINT，但响应不返回输入输出、函数类型、参数约束，不返回副作用或授权契约，也不返回平台函数 ID、函数源码或依赖源码。

因此 `detail` 成功只确认当前应用可以解析该 ENDPOINT 及其基础元数据。用户可以明确提供参数值、执行意图和执行授权；缺失的参数结构、输入输出和真实副作用必须来自可信业务 Skill 或平台已确认契约。技术契约无法补齐时保持未知，不自动执行。

不提供 `bff list` 只能降低函数资产被批量枚举的暴露面，不能替代授权判断。当前 Backend Function Detail/Exec 接口按应用维度鉴权，不等于按具体 `functionName` 独立鉴权；Agent 仍须独立核对函数名来源、业务授权和真实副作用。知道或猜到函数名不代表可以查看元数据或执行。运行态只发现并消费已绑定的业务能力，不获取函数源码或依赖源码。

## 内部数据集权限与执行身份

- 普通用户执行 Backend Function 时，内部每次 Dataset 操作都按当前 AK 用户、目标应用、目标数据集和实际动作校验权限。一个数据集获准，不会让同一脚本中的其他数据集自动获准；读权限也不代表可以创建、修改或删除。
- `context.client.models.byTable(...)` 与按 `datasetCode` 访问遵循同一权限规则，表名解析成功不代表已经获得操作权限。
- 多角色按服务端授予的实际动作权限判断；任一有效角色授予该动作即可获得该动作权限，不取“第一个角色”。角色权限与 `SELF` 数据范围是不同维度，不能把某个角色或入口授权当作全部记录可见。
- 经主数据集已配置的关联字段、选项标签、子表或子表单读取子数据时，沿用主数据集授权；独立调用子数据集模型或 `byTable` 时，仍检查子数据集自身的动作权限。
- 用户上下文由服务端传递，任务的系统执行标记也由可信服务端设置并限定到当前应用。CLI 参数、脚本入参或缺少用户不能把普通请求变成系统执行；不传入伪造的用户、角色、管理员或免鉴权标记。
- 收到 `permission_denied`（业务码 `202`，HTTP 状态可能为 `401`）时停止并核对目标数据集和动作授权，不自动重新登录、换 AK 或换入口重试。`auth_required` / 业务码 `201` 才属于认证失败。动作对应关系见[角色与权限](../guides/role-and-permission-workflow.md)。

## bff exec — 执行 Backend Function

```bash
# 无参数执行
lovrabet bff exec --name <functionName>

# 带参数执行
lovrabet bff exec --name <functionName> --params '{"key":"value"}'
```

| Flag | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--name` | string | **是** | Backend Function 名称（`export default function` 后的函数名） |
| `--params` | string | 否 | 执行参数，JSON 格式 |

**CLI 风险元数据**：`read`。这只描述命令注册信息，不代表 ENDPOINT 的真实副作用；脚本仍可能产生业务写入、外部调用或不可逆动作。

副作用、权限或确认语义不明确时，不自动执行。

**输出**：Backend Function 返回值，格式由 `--format` 控制。

## 典型工作流

```bash
# 0. 已按应用选择规则确认目标 AppCode；下列 <appcode> 均指同一目标

# 1. 如果不知道函数名，从业务 Skill、可信 Service Tree、
#    前序已确认上下文或可信 KB 候选定位；无法唯一定位时停止

# 2. 精确查看已知 Backend Function 的运行契约
lovrabet bff detail --appcode <appcode> --name getUserInfo

# 3. 核对 ENDPOINT 类型、真实副作用、权限和授权后执行 Backend Function
lovrabet bff exec --appcode <appcode> --name getUserInfo --params '{"userId":123}'

# 4. 指定 JSON 格式输出
lovrabet bff exec --appcode <appcode> --name getUserInfo --params '{"userId":123}' --format json
```

## Agent 读取 app-config

Agent 执行 Skill 需要 app-config value 时，统一调用：

```bash
lovrabet app-config get <key> --format compress
```

不要为了读取配置创建或复用 Backend Function。value 只在当前任务内消费，不写入文件、缓存、日志或其他命令参数；除非用户明确要求查看具体值，最终答复默认不重复展示。

## 注意

- `--name` 即 Backend Function 中 `export default function` 后的 `functionName`，精确匹配
- `--params` 必须是合法 JSON 字符串
- 需要 app-config value 时直接调用 `lovrabet app-config get <key>`；不要创建取配置 Backend Function，也不要把 value 通过 `--params` 传给 Backend Function
- `lovrabet` 没有 `bff list` 命令，也不通过列表接口在本地按名称筛选；函数名必须来自用户明确输入、业务 Skill、可信 Service Tree、前序已确认上下文或可信 KB 候选
- 运行态发现业务能力，不枚举函数实现资产；稳定规则由业务 Skill 或可信 Service Tree 绑定到已发布 ENDPOINT
- `detail` 成功只证明 ENDPOINT 存在，不代表已经获得执行授权
- Detail 或执行失败时报告真实错误；不将失败当作无匹配而切换应用重试
- `detail` 返回的版本与业务 Skill 或平台已确认契约不一致时，不执行；输出当前版本、期望版本和“能力版本未就绪”

## 参考

- [SKILL.md](../SKILL.md)
- [lovrabet-personal-bff-workflow.md](lovrabet-personal-bff-workflow.md)
- [instant-api-workflow.md](instant-api-workflow.md)
