# Custom SQL 查询工作流

查看和执行 Custom SQL。Custom SQL 在 Lovrabet 平台上创建，CLI 用于查看详情和执行。

## 前置条件

- `sql detail` 和 `sql exec` 使用当前 CLI 认证，默认推荐 **accessKey（client-ak）**

## 应用与能力定位

应用选择统一遵循[默认应用与应用发现](../guides/app-resolution.md)：未指定目标时先查默认 AppCode（顶层 `appcode` 或 `defaultApp` 解析结果）；仅在成功查询无合理匹配、核对筛选条件且用户未限定范围后，才扩大只读发现。认证、权限或连接错误不触发跨应用重试。

从业务 Skill、可信 Service Tree、前序已确认上下文或可信 KB 候选定位能力，同时核对所属 AppCode；只有应用明确仍不足以直接执行，能力标识、参数与副作用契约也必须明确。缺少可信标识时停止，不猜测，也不通过跨应用逐个执行来探测。

`--app` / `--appcode` 只对本次命令生效。临时选择其他应用后，后续每条 `detail`、`data` 或执行命令都必须显式携带该目标；资源标识必须与发现它的 AppCode 配对，不能依靠上一条命令改变默认值。

## sql detail — 查看 Custom SQL 详情

```bash
lovrabet sql detail --sqlcode <code>

# 返回原始完整 API 响应
lovrabet sql detail --sqlcode <code> --verbose
```

| Flag | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--sqlcode` | string | **是** | Custom SQL 标识字段 `sqlCode`，格式：`xxxxxxxx-xxxxxxxx`（8 位 hex + 8 位 hex） |
| `--verbose` | boolean | 否 | 返回完整原始对象 |

**输出**：Custom SQL 名称、SQL 内容和关联的数据库等。

Custom SQL 只有在标识来源可信、所属应用匹配且 Detail 实际返回的名称、数据库和 SQL 内容与当前任务一致时，才作为稳定查询规则复用。`sql detail` 不单独提供参数约束或副作用契约；缺失信息仍视为未知。Custom SQL 已存在或 `detail` 成功本身不代表业务口径正确，也不代表已经获得执行授权。

SQL 内容属于敏感实现资产。当前 `sql detail` 会按真实接口返回 SQL 内容，Agent 只用于当前任务的契约核对，不写入 KB、业务 Skill、日志或全量规则目录，最终答复默认不回显；用户明确要求查看时，也只能在服务端授权成功后按最小必要范围展示。不提供 `sql list` 只能降低批量枚举和暴露面，不能替代服务端资源级授权；`detail` 与 `exec` 仍需按当前 AK、应用和具体 Custom SQL 独立鉴权，知道或猜到 `sqlCode` 不代表有权查看或执行。

## sql exec — 执行 Custom SQL

运行态执行的唯一契约是 `sqlCode` + `params`。`sql detail` 只用于当前任务核对；执行始终使用已确认的 `sqlCode` 和当前 Custom SQL 契约定义的业务参数。标识无法唯一确认、参数无效或执行失败时，报告真实错误并停止。

```bash
# 无参数执行
lovrabet sql exec --sqlcode <code>

# 带参数执行
lovrabet sql exec --sqlcode <code> --params '{"status":"active"}'
```

| Flag | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--sqlcode` | string | **是** | Custom SQL 标识字段 `sqlCode`，格式：`xxxxxxxx-xxxxxxxx` |
| `--params` | string | 否 | 查询参数，JSON 格式 |

**CLI 风险元数据**：`read`。这只反映命令注册，不代表真实副作用。Custom SQL 可能包含业务写入、`DROP`、`TRUNCATE` 等破坏性语句；执行前必须核对 SQL 内容、权限和用户授权，副作用不明确时不自动执行。

**输出**：查询结果数据，格式由 `--format` 控制。

## 典型工作流

```bash
# 0. 已按应用选择规则确认目标 AppCode；下列 <appcode> 均指同一目标

# 1. 如果不知道 sqlCode，从业务 Skill、可信 Service Tree、
#    前序已确认上下文或可信 KB 候选定位；无法唯一定位时停止

# 2. 查看 Custom SQL 详情，核对名称、数据库和 SQL 内容
lovrabet sql detail --appcode <appcode> --sqlcode 2305f915-dd48cd4c

# 3. 核对契约、参数和数据范围后执行 Custom SQL
lovrabet sql exec --appcode <appcode> --sqlcode 2305f915-dd48cd4c --params '{"status":"active"}'

# 4. 指定 JSON 格式输出，便于程序解析
lovrabet sql exec --appcode <appcode> --sqlcode 2305f915-dd48cd4c --params '{"status":"active"}' --format json
```

## 注意

- Custom SQL 标识字段 `sqlCode` 的格式为 `{8位hex}-{8位hex}`，如 `2305f915-dd48cd4c`
- `--params` 必须是合法 JSON 字符串
- `lovrabet` 没有 `sql list` 命令；`sqlCode` 必须来自用户明确输入、业务 Skill、可信 Service Tree、前序已确认上下文或可信 KB 候选
- 运行态发现业务能力，不枚举 Custom SQL 实现资产；基础事实查询优先使用已治理 Dataset，稳定规则由业务 Skill 或可信 Service Tree 绑定到可信契约对应的 Custom SQL
- 不知道 `sqlCode` 时不猜测，也不从 Dataset 原始字段重写已有稳定规则
- Detail 或执行失败时报告真实错误；不将失败当作无匹配而切换应用重试
- `--params` 只传当前 Custom SQL 契约定义的业务参数

## 参考

- [SKILL.md](../SKILL.md)
- [instant-api-workflow.md](instant-api-workflow.md)
