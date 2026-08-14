# Dataset And Data Workflow Guide

## 目的

把“业务需求 -> 应用决议 -> 数据集定位 -> Instant API 数据操作”收成一条稳定流程，避免直接盲猜 `dataset code` 或 app。

## 推荐流程

1. 先判断 app 是否明确  
   不明确时，先看 [app-resolution.md](app-resolution.md)

2. 需要写 personal BFF 或知识库内容时，先做发现

```bash
lovrabet api-doc list --category dataset
lovrabet api-doc detail --code dataset_data_filter
```

如果用户已经给了明确字段和值，可以直接使用用户提供的数据；否则先确认真实 API 和数据结构。

3. 定位数据集

```bash
lovrabet dataset list --name "<关键词>"
```

如需限定候选 app：

```bash
lovrabet dataset list --app <name> --name "<关键词>"
```

4. 看数据集结构

```bash
lovrabet dataset detail --code <datasetCode>
```

5. 需要 SDK 调用示例时读取数据集 SDK 文档

```bash
lovrabet dataset sdk-doc --code <datasetCode>
```

6. 拿到 `datasetCode` 后，再进入 `data` 子命令

```bash
# 第 1 页：过滤、稳定排序和分页都放进一个 --params JSON
lovrabet data filter --code <datasetCode> --params '{"where":{"status":{"$eq":"active"}},"orderBy":[{"id":"asc"}],"currentPage":1,"pageSize":20}'

# 第 2 页：复制上一页参数，只递增 currentPage
lovrabet data filter --code <datasetCode> --params '{"where":{"status":{"$eq":"active"}},"orderBy":[{"id":"asc"}],"currentPage":2,"pageSize":20}'

lovrabet data getOne --code <datasetCode> --params '<json>'
lovrabet data create --code <datasetCode> --params '<json>'
lovrabet data batchCreate --code <datasetCode> --params '[{"name":"a"},{"name":"b"}]'
lovrabet data update --code <datasetCode> --params '<json>'
lovrabet data delete --code <datasetCode> --params '<json>' --yes
```

`data filter` 的 `where`、`select`、`orderBy`、`currentPage`、`pageSize` 都是 `--params` JSON 字段。不要使用 `--where`、`--select`、`--order-by`、`--current-page`、`--page`、`--page-size`；CLI 会拒绝这些误用。翻页时保持筛选条件、返回字段、排序和 `pageSize` 不变，只递增从 1 开始的 `currentPage`。分页查询应使用唯一且稳定的排序字段，避免跨页重复或遗漏。

查询后核对记录和分页元数据：

```bash
lovrabet data filter --code <datasetCode> --params '{"where":{"status":{"$eq":"active"}},"orderBy":[{"id":"asc"}],"currentPage":1,"pageSize":20}' --format compress --jq '.data.result | {tableData, paging}'
```

必须确认 `paging.currentPage`、`paging.pageSize` 与请求一致，并检查 `tableData` 是否满足 `where`。条件未生效、分页元数据不符或返回形状异常时，本次查询结果不可作为业务结论；先检查 `--params`，必要时执行 `lovrabet data filter --help`。

`data update` 的 `id` 可传单值或数组；批量更新示例：`--params '{"id":[1,2,3],"status":"done"}'`。数组不能为空，一次最多 1000 条。批量数组 id 会在实际请求体和 dry-run 预览中使用逗号字符串兼容运行时解析，用户仍按数组输入。

## 什么时候只用 `dataset list`

以下情况只用 `dataset list` 就够：

- 用户只是问“有哪些数据集”
- 用户只是想按名称搜索数据集
- 只需要数据集 code 和字段名数组

## 什么时候必须看 `dataset detail`

以下情况必须补一轮 `dataset detail`：

- 要确认字段类型
- 要确认字段是否可写
- 要确认主键 / 操作列表
- 要给 `data create/batchCreate/update` 组参数

## 什么时候看 `dataset sdk-doc`

以下场景补一轮 `dataset sdk-doc`：

- 需要在 personal BFF 或其他可交付源码中调用运行态 SDK
- 需要确认 SDK 参数结构，而不只是字段名
- 要把数据访问方式写进可交付源码或文档

## Dataset 回退准入

Dataset Detail + Instant API 是简单低风险事实查询的直接路径，例如读取单条记录、列举明细或做不承载业务判定的基础统计；这类请求不强制查询 KB，也不需要包装成 Custom SQL 或 Backend Function。

以下任务不能直接回退到原始 Dataset 字段：

- **稳定规则**：已有已发布且契约可信的确定性能力定义固定口径时，必须复用该入口，不重新拼字段实现同一规则。当前类型包括但不限于业务 Skill、已治理 Dataset / Instant API（含 `filter`、`getOne`、`aggregate`）、Custom SQL 和 Backend Function；Service Tree 只用于定位承载规则的入口，不单独作为规则事实源。
- **高风险确定性判断**：审批、合规、价格异常、权限、资质等结论必须使用已确认的确定性能力；没有匹配能力时，只对受影响范围输出“不判定”，并说明缺少的能力契约。
- **副作用未知的操作**：即使 CLI risk 显示为 `read`，也要先确认真实业务写入、外部调用和不可逆动作。

Dataset Detail 只证明字段与操作契约，不会自动把原始数据推导提升为稳定业务规则。

### 正式规则与分析性推导

- 用户询问正式业务规则时，Dataset 原始字段只能返回已经确认的直接事实；缺少可信规则契约时，对正式结论输出“不判定”，并说明缺少的规则语义、适用范围或执行入口。
- 只有用户明确要求估算、探索或情景分析时，才可基于 Dataset 做分析性推导。输出必须展示使用字段、公式和假设，明确它不是平台正式规则，也不得把它作为自动写入、审批、退款或其他高风险业务动作的唯一依据。
- 规则语义必须来自可信业务 Skill 或平台已确认契约；Dataset Instant API、Custom SQL 和 Backend Function 只是执行载体，能力类型或 Detail 成功本身不证明规则可信。
- 高风险操作仍需满足服务端 RBAC、业务授权和用户确认；`--dry-run` 仅预览请求，不能替代授权、确认或执行后核验。

## `data` 的使用原则

`data` 命令只依赖 `datasetCode`，不直接做 app 决议。  
所以不要在 app 未确定、dataset 未确认时直接构造 `data filter/getOne/create/batchCreate/update/delete`。

## Instant API 与 HOOK

Backend Function HOOK 不是 Agent 可直接执行的端点。它绑定到某个 Dataset 的一个具体 Instant API operation 及 BEFORE/AFTER 节点；当绑定关系来自可信业务 Skill 或平台已确认契约时，Agent 执行对应的 `data` 命令。服务端成功解析并加载绑定脚本时，HOOK 会在同一请求管线中执行。`dataset detail` 不保证返回 HOOK 绑定、输入输出或失败语义，缺少可信绑定契约时不能靠执行请求试探。

`--dry-run` 只预览 CLI 请求，不触发 HOOK。基础访问权限由平台 RBAC 控制；HOOK 仅用于补充个性化校验和处理。已成功加载并执行的 BEFORE HOOK 失败时会阻止对应 Instant API 主操作；绑定查询或脚本加载异常会记录日志并跳过 HOOK，补充逻辑可能被跳过，因此不得把 HOOK 作为必须强制执行的合规或业务校验唯一保障。AFTER HOOK 失败时不能据此断言主操作已回滚。对写操作的返回错误、超时或 AFTER HOOK 失败，先按业务唯一键只读回查主记录和必要的后置结果，再依据可信的事务、幂等或可重试契约决定是否重试。

## 批量新增的边界

`lovrabet data batchCreate` 只适合“同一数据集多条新增”，用于减少请求次数。参数必须是 JSON 数组，或 `{"items":[...]}`：

```bash
lovrabet data batchCreate --code <datasetCode> --params '[{"name":"a"},{"name":"b"}]' --dry-run
lovrabet data batchCreate --code <datasetCode> --params '[{"name":"a"},{"name":"b"}]'
```

使用前仍要先做 `dataset detail`，确认字段可写、必填字段和业务唯一键。执行后按业务唯一键只读核对，避免“请求结果未知”时重复写入。

不要在执行时直接用 `data batchCreate` 绕过 Backend Function 业务编排。只要写入涉及多个数据集、upsert、依赖顺序、幂等、失败恢复或 handoff 结果，就应调用业务级 `bff exec`，由函数或 CLI service 内部决定是否使用批量新增。Backend Function 写入类执行仍需先确认业务授权、Studio 权限和人工确认语义；CLI 将 `bff exec` 标记为 `read`，不等同于免审批写入。

## 高风险动作

删除前先预览：

```bash
lovrabet data delete --code <datasetCode> --params '<json>' --dry-run
lovrabet data delete --code <datasetCode> --params '<json>' --yes
```

## 常见错误

### 只有业务描述，没有 dataset code

不要直接问运行态接口。先：

1. 决议 app
2. `dataset list --name`
3. `dataset detail`

### app 不明确但直接跑 `data *`

这通常是在跳过应用决议。先退回去做 app + dataset 定位。

### 把过滤或分页字段写成独立 flag

`--where`、`--page-size` 等写法不会表达 `data filter` 请求体。把所有过滤、排序和分页字段放入一个 `--params` JSON；不要删掉错误 flag 后执行空参数查询。

### 返回了明显未过滤的数据

不要把返回内容直接当成“系统里确实存在这些记录”。先核对 `data.result.paging`、抽查 `data.result.tableData` 是否满足 `where`，再修正查询或查看 `lovrabet data filter --help`。
