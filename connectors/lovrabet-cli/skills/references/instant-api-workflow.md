# Instant API Workflow

## 概述

通过运行态 CLI 对数据集记录进行增删改查和聚合统计。`Instant API` 分组下的所有 `data` 子命令共享统一接口：

```bash
lovrabet data <command> --code <datasetCode> --params '<json>'
```

- `--code`：数据集 code（路由标识，必填）
- `--params`：JSON 请求体，直接透传给运行态 API

## data 之前如何确定 app

`data` 子命令本身只依赖 `dataset code`，但这个 `dataset code` 总是来自某个具体 app。

因此决策顺序应该是：

1. 先判断当前 app 是否已明确
2. 当前 app 明确时，直接 `dataset list --name ...`
3. 当前 app 不明确但有 `defaultApp` 时，先 `dataset list --name <关键词>` 验证默认候选
4. 默认候选无命中、弱命中或语义不合理时，再 `app list`
5. 再用 `dataset list --app <name> --name <关键词>` 收敛到正确 app
6. 拿到 `dataset code` 后，再执行 `data filter/getOne/create/batchCreate/update/delete`

不要直接在 app 未决议的情况下盲目构造 `data` 命令。

## 架构说明

7 个 data 子命令对应 7 个运行态 API 端点：

| 子命令 | 说明 | 风险等级 |
|--------|------|----------|
| `filter` | 条件查询（分页） | read |
| `getOne` | 按 ID 获取单条 | read |
| `aggregate` | 聚合统计（分组、求和、计数等） | read |
| `create` | 新建记录 | write |
| `batchCreate` | 批量新建同一数据集记录 | write |
| `update` | 更新记录 | write |
| `delete` | 删除记录（需 `--yes`） | high-risk-write |

`--params` JSON 就是 API 请求体，无额外封装。

### Backend Function HOOK

Backend Function HOOK 绑定到某个 Dataset 的一个具体 Instant API operation 及 BEFORE/AFTER 节点。Agent 不直接调用 HOOK；HOOK 是否已绑定必须来自可信业务 Skill 或平台已确认契约。绑定已确认时，执行对应的 `data` 命令会进入 Instant API 请求管线；服务端成功解析并加载绑定脚本时，HOOK 会在同一管线中执行。

`--dry-run` 不会触发 HOOK，它只预览 CLI 将发送的请求。基础访问权限由平台 RBAC 控制；HOOK 仅用于补充个性化校验和处理。已成功加载并执行的 BEFORE HOOK 失败时会阻止对应 Instant API 主操作；绑定查询或脚本加载异常会记录日志并跳过 HOOK，补充逻辑可能被跳过，因此不得把 HOOK 作为必须强制执行的合规或业务校验唯一保障。AFTER HOOK 失败时不能据此断言主操作已回滚，也不能直接重试。对于写操作，先按业务唯一键只读回查主记录和必要的后置结果，再依据可信的事务、幂等或可重试契约决定下一步。

### 超长整数标识

运行态数据中的 BIGINT 标识可能超过 JavaScript 安全整数范围。CLI 会在首次解析响应时把这类整数字面量保留为字符串，避免相邻标识被舍入成同一个值；`--params` 中超过安全范围的整数也会按字符串传递。业务编排仍应把商品、SKU、品牌等标识当作不透明字符串，不对标识执行算术、`Number(...)` 或 `parseInt(...)`。已经被其他工具解析成不安全 `number` 的值无法靠后续 `tostring` 恢复，应重新从无损边界读取。

## 各命令详解

### data filter — 条件查询

`where`、`select`、`orderBy`、`currentPage`、`pageSize` 必须放在同一个 `--params` JSON 对象中。它们不是独立 CLI flags；禁止使用 `--where`、`--select`、`--order-by`、`--current-page`、`--page`、`--page-size`。

```bash
# 查全部（默认第一页）
lovrabet data filter --code <code> --params '{"orderBy":[{"id":"asc"}],"currentPage":1,"pageSize":20}'

# 带条件
lovrabet data filter --code <code> --params '{"where":{"status":{"$eq":"active"}},"orderBy":[{"id":"asc"}],"currentPage":1,"pageSize":20}'

# 翻页：完整复制上一页参数，只递增 currentPage
lovrabet data filter --code <code> --params '{"where":{"status":{"$eq":"active"}},"orderBy":[{"id":"asc"}],"currentPage":2,"pageSize":20}'

# 完整示例：条件 + 分页 + 排序 + 选字段
lovrabet data filter --code <code> --params '{
  "where": {"$and":[{"status":{"$eq":"active"}},{"amount":{"$gte":100}}]},
  "select": ["id","name","status"],
  "orderBy": [{"id":"desc"}],
  "currentPage": 1,
  "pageSize": 20
}'
```

**--params 结构：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `where` | object | 查询条件 |
| `select` | string[] | 返回字段列表 |
| `orderBy` | object[] | 稳定排序，例如按唯一字段 `[{"id":"asc"}]` |
| `currentPage` | number | 页码，从 1 开始 |
| `pageSize` | number | 每页条数；翻页时保持不变 |

翻页时必须保持 `where`、`select`、`orderBy`、`pageSize` 不变，只递增 `currentPage`。分页查询优先使用唯一且稳定的排序字段，避免跨页重复或遗漏。查询后可投影记录和分页元数据：

```bash
lovrabet data filter --code <code> --params '{"where":{"status":{"$eq":"active"}},"orderBy":[{"id":"asc"}],"currentPage":2,"pageSize":20}' --format compress --jq '.data.result | {tableData, paging}'
```

确认 `paging.currentPage`、`paging.pageSize` 与请求一致，并检查 `tableData` 是否满足 `where`。条件未生效或返回形状异常时，本次结果不可作为业务结论；先修正查询，不要把未过滤内容解释为完整业务事实。

### data getOne — 单条查询

```bash
lovrabet data getOne --code <code> --params '{"id":123}'
```

### data aggregate — 聚合统计

对数据集进行分组、求和、计数、平均值等聚合操作。

`aggregate` 仅支持单个 `DB_TABLE` 数据集；`METADATA` 数据集不支持 `aggregate` 或 Custom SQL。JOIN、跨表统计、数据库特有函数或 `aggregate` 无法表达的查询，应在编码前显式选择已有且契约可信的 Custom SQL；不要在运行时静默切换，也不要动态拼接 SQL。

```bash
# 按状态分组求总金额
lovrabet data aggregate --code <code> --params '{
  "aggregate": [{"column": "amount","type":"SUM","alias":"total"}],
  "groupBy": ["status"]
}'

# 按地区统计活跃订单数
lovrabet data aggregate --code <code> --params '{
  "aggregate": [{"column": "id","type":"COUNT","alias":"cnt"}],
  "groupBy": ["region"],
  "where": {"status":{"$eq":"active"}}
}'

# 多维聚合：按状态和地区分组，求总金额并按聚合结果排序
lovrabet data aggregate --code <code> --params '{
  "aggregate": [{"column": "amount","type":"SUM","alias":"total"}],
  "groupBy": ["status","region"],
  "having": {"status":{"$notNull":true}},
  "orderBy": [{"total":"desc"}]
}'
```

**--params 结构：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `aggregate` | object[] | **必填**。聚合定义列表 |
| `groupBy` | string[] | 分组字段 |
| `where` | object | 聚合前过滤（与 filter 相同的 where 语法） |
| `having` | object | 聚合后过滤；使用与 `where` 相同的对象结构，字段必须是真实数据集字段，不支持聚合别名 |
| `select` | string[] | 随聚合结果返回的原始字段 |
| `orderBy` | object[] | 排序；可以引用聚合输出别名，如 `[{"total":"desc"}]` |
| `currentPage` | number | 页码 |
| `pageSize` | number | 每页条数 |

`aggregate[].column` 必须使用真实数据集字段；`aggregate[].alias` 只定义返回结果字段名，不会成为新的数据集字段。

| 位置 | 聚合别名 | 约束 |
|------|----------|------|
| `aggregate[].alias` | 支持 | 仅定义返回结果字段名 |
| `select` | 不支持 | 使用真实数据集字段 |
| `where` | 不支持 | 使用真实数据集字段 |
| `having` | 不支持 | 使用真实数据集字段 |
| `groupBy` | 不支持 | 使用真实数据集字段 |
| `orderBy` | 支持 | 可以引用聚合输出别名 |

需要按聚合结果过滤且 `aggregate` 无法用真实字段表达时，使用已有且契约可信的 Custom SQL。不要在运行时静默切换到 Custom SQL，也不要动态拼接 SQL。

**聚合类型：**

| type | 说明 | 示例 |
|------|------|------|
| `SUM` | 求和 | `{"column": "amount","type":"SUM","alias":"total"}` |
| `COUNT` | 计数 | `{"column": "id","type":"COUNT","alias":"cnt"}` |
| `COUNT` (distinct) | 去重计数 | `{"column": "id","type":"COUNT","alias":"cnt","distinct":true}` |
| `AVG` | 平均值 | `{"column": "score","type":"AVG","alias":"avg_score"}` |
| `AVG` (rounded) | 带精度平均值 | `{"column": "score","type":"AVG","alias":"avg","round":true,"precision":2}` |

### data create — 新建记录

```bash
# 预览
lovrabet data create --code <code> --params '{"name":"test","amount":100}' --dry-run

# 执行
lovrabet data create --code <code> --params '{"name":"test","amount":100}'
```

### data batchCreate — 批量新建同一数据集记录

```bash
# 预览
lovrabet data batchCreate --code <code> --params '[{"name":"a"},{"name":"b"}]' --dry-run

# 执行
lovrabet data batchCreate --code <code> --params '[{"name":"a"},{"name":"b"}]'
```

`--params` 可以是 JSON 数组，也可以是 `{"items":[...]}`。该命令适合同一数据集多条新增，用于减少请求次数。

不要把 `batchCreate` 当作正式业务流程入口。跨多个数据集、upsert、依赖顺序、频率保护、幂等恢复或 handoff 结果要求，应封装在 Backend Function/CLI service 中，再由内部按需使用 `batchCreate`。Backend Function 写入类执行仍需先确认业务授权、Studio 权限和人工确认语义；CLI 将 `bff exec` 标记为 `read`，不等同于免审批写入。

### data update — 更新记录

```bash
# 单条预览
lovrabet data update --code <code> --params '{"id":123,"status":"completed"}' --dry-run

# 单条执行
lovrabet data update --code <code> --params '{"id":123,"status":"completed"}'

# 批量预览
lovrabet data update --code <code> --params '{"id":[1,2,3],"status":"completed"}' --dry-run

# 批量执行
lovrabet data update --code <code> --params '{"id":[1,2,3],"status":"completed"}'
```

`id` 支持单值或数组。数组不能为空，id 必须是正整数或数字字符串，一次最多 1000 条。批量更新成功时 CLI 会用稳定 envelope 表达结果：`operation:"update"`、`mode:"batch"`、`ids`、`total`、`result`。为兼容当前运行时 metadata 路径，批量数组 id 会在实际请求体和 dry-run 预览中序列化为逗号字符串，例如 `id:"1,2,3"`；用户输入仍使用数组。底层服务端批量回查仍在 follow-up 中。

### data delete — 删除记录

```bash
# 预览
lovrabet data delete --code <code> --params '{"id":123}' --dry-run

# 执行（需确认）
lovrabet data delete --code <code> --params '{"id":123}' --yes
```

## where 查询语法

| 操作符 | 含义 | 示例 |
|--------|------|------|
| `$eq` | 等于 | `{"status":{"$eq":"active"}}` |
| `$ne` | 不等于 | `{"status":{"$ne":"deleted"}}` |
| `$gte/$gteq/$lte/$lteq` | 比较 | `{"amount":{"$gte":100}}` |
| `$contain` | 包含匹配 | `{"name":{"$contain":"test"}}` |
| `$startWith` | 前缀匹配 | `{"name":{"$startWith":"pre"}}` |
| `$endWith` | 后缀匹配 | `{"name":{"$endWith":"suf"}}` |
| `$notNull` | 非空判断 | `{"app_code":{"$notNull":true}}` |
| `$in` | 包含 | `{"status":{"$in":["active","pending"]}}` |
| `$and` | AND 组合 | `{"$and":[cond1, cond2]}` |
| `$or` | OR 组合 | `{"$or":[cond1, cond2]}` |

## aggregate 参数结构（与 SDK 对齐）

```json
{
  "select": ["category_id"],
  "aggregate": [
    { "type": "SUM", "column": "amount", "alias": "total_amount", "round": true, "precision": 2 }
  ],
  "where": { "status": { "$eq": "active" } },
  "groupBy": ["category_id"],
  "having": { "category_id": { "$notNull": true } },
  "orderBy": [{ "total_amount": "desc" }],
  "currentPage": 1,
  "pageSize": 20
}
```

## 错误处理

- 缺少认证 → `Error: No authentication configured`
- `--params` 不是合法 JSON → `Error: Invalid JSON for --params: ...`
- 数据集不存在 → API 返回错误
- 非交互模式下 delete 未加 `--yes` → 高风险保护拦截
