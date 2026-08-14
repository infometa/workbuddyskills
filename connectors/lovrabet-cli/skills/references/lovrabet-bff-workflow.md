# Backend Function 工作流

查看和执行 Lovrabet 平台的 Backend Function。CLI 命令组保留技术标识 `bff`，用于查看详情和执行。

## 前置条件

- `bff detail` 和 `bff exec` 使用当前 CLI 认证，默认推荐 **accessKey（client-ak）**
- 需要个人脚本时使用 `personal-bff` 命令组，不要把平台正式 Backend Function 与 personal BFF 混成同一个资源

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

## 先判断 app 是否明确

`bff` 工作流和 `dataset/sql` 一样，不要默认先跑 `app list`，也不要完全跳过 app 决议。

### 可以直接进入 Detail 的场景

以下情况直接进入 `bff detail`，但不能跳过执行前的副作用与授权判断：

- 用户已经给了 `--appcode`
- 用户已经给了 `--app <name>`
- 当前任务明显沿用上文已确认的同一 app 上下文
- 用户明确说“当前应用”“默认应用”，且没有新的业务域线索

`defaultApp` 只是默认候选。Backend Function 可能按业务域拆在不同 app 中；用户提到新的业务能力或业务对象且未指定 app 时，先把 `defaultApp` 当第一个候选验证，验证不成立再扩大到应用列表。

### 需要先做应用决议的场景

以下情况才扩大到 `lovrabet app list`：

- 用户只描述了业务能力，没有说是哪个应用里的 Backend Function
- 当前没有显式 `--appcode` / `--app`，且需求包含业务域或业务能力线索
- 候选 app 可能不止一个
- 已经把 `defaultApp` 作为候选检查过，但无法确认它承载本次 Backend Function

推荐方式：

1. 有 `defaultApp` 时，先把它作为第一个候选
2. 无法确认默认候选承载本次 Backend Function 时，再 `lovrabet app list`
3. 用业务关键词挑候选 app
4. 从业务 Skill、可信 Service Tree、前序已确认上下文或可信 KB 候选定位 ENDPOINT；无法唯一定位时停止，不猜测
5. 再执行 `lovrabet bff detail`；确认是 ENDPOINT，且真实副作用来自可信技术契约、权限和用户授权明确后，才执行 `bff exec`

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
# 0. 如果默认候选验证不成立，再看应用目录
lovrabet app list

# 1. 如果不知道函数名，从业务 Skill、可信 Service Tree、
#    前序已确认上下文或可信 KB 候选定位；无法唯一定位时停止

# 2. 精确查看已知 Backend Function 的运行契约
lovrabet bff detail --name getUserInfo

# 3. 核对 ENDPOINT 类型、真实副作用、权限和授权后执行 Backend Function
lovrabet bff exec --name getUserInfo --params '{"userId":123}'

# 4. 指定 JSON 格式输出
lovrabet bff exec --name getUserInfo --params '{"userId":123}' --format json
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
- 当业务归属不清时，先验证 `defaultApp`；验证不成立再 `app list` 做应用决议，再去确认脚本，而不是直接盲猜当前 app
- `detail` 返回的版本与业务 Skill 或平台已确认契约不一致时，不执行；输出当前版本、期望版本和“能力版本未就绪”

## 参考

- [SKILL.md](../SKILL.md)
- [lovrabet-personal-bff-workflow.md](lovrabet-personal-bff-workflow.md)
- [instant-api-workflow.md](instant-api-workflow.md)
