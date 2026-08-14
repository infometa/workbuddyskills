# personal BFF 工作流

`personal-bff` 用于当前用户在当前应用下维护个人 ENDPOINT 脚本。第一阶段支持 `list`、`detail`、`create`、`update`、`exec`；不提供删除命令。

## 什么时候用

- 需要把多步只读查询包装成稳定函数
- 需要先验证一个轻量业务接口的返回形状，再交给下游调用

若已有平台正式 BFF，优先复用 `bff detail/exec`。personal BFF 更适合个人工作流、验证和 Agent 生成的轻量端点。

## BFF 内访问 Dataset

脚本通过 `` context.client.models[`dataset_${datasetCode}`] `` 获取 Dataset accessor。当前支持 `create`、`batchCreate`、`update`、`delete`、`getOne`、`findOne`、`getList`、`filter` 和 `aggregate`。

能由 Dataset Instant API 表达时，优先直接调用对应方法。只有 Instant API 无法表达需求，且已有契约可信的 Custom SQL 时，才使用 `context.client.sql.execute({ sqlCode, params })`。能力选择应在编码前完成；不得先执行 `aggregate`，再因权限、参数或运行错误静默回退 Custom SQL。

同一数据集批量新增时，向 `batchCreate` 直接传非空对象数组；`batchCreate` 返回新记录 ID 数组，顺序与输入一致。不要把 `lovrabet data batchCreate` 兼容的 `{"items":[...]}` 包装传给 BFF Dataset accessor。批量更新仍调用 `update({ id, ...fields })`，其中 `id` 可以是单值或数组；不存在 `batchUpdate()`，也不要把多条更新记录数组直接传给 `update`。批量数量不得超过运行时上限（默认 1000 条）。示例字段必须替换为已确认的真实数据集字段：

```js
const createdIds = await model.batchCreate([
  { order_id: params.orderId, sku_code: "A" },
  { order_id: params.orderId, sku_code: "B" },
]);

await model.update({
  id: [1, 2, 3],
  status: "DONE",
});
```

调用 `aggregate` 时仅支持单个 `DB_TABLE` 数据集；`METADATA` 数据集不支持 `aggregate` 或 Custom SQL。`aggregate[].column`、`select`、`where`、`having` 和 `groupBy` 必须使用真实数据集字段；`aggregate[].alias` 只定义输出字段名，只有 `orderBy` 可以引用聚合输出别名。JOIN、跨表统计、数据库特有函数，或需要按聚合结果过滤且无法用真实字段表达时，在编码阶段显式选择已有且契约可信的 Custom SQL，不要动态拼接 SQL。

```js
export default async function statsByCity(params, context) {
  const datasetCode = "sales_order";
  const model = context.client.models[`dataset_${datasetCode}`];

  const aggregateResult = await model.aggregate({
    aggregate: [{ column: "amount", type: "SUM", alias: "total_amount" }],
    where: { status: { $eq: "active" } },
    groupBy: ["city"]
  });

  return aggregateResult.tableData;
}
```

`aggregate` 返回 `{ tableData, paging, tableColumns? }`；业务记录从 `aggregateResult.tableData` 读取，不要按 Custom SQL 的数组返回值处理。

## 查看

```bash
lovrabet personal-bff list --format compress
lovrabet personal-bff detail --id <id> --format compress
```

更新前先 `personal-bff detail`，确认函数名、脚本内容、描述和版本。

## 创建

脚本来自本地 UTF-8 JavaScript 或 TypeScript 文件。`--name` 必须是合法 JavaScript identifier。

```bash
lovrabet personal-bff create --name loadOrders --file ./load-orders.js --dry-run
lovrabet personal-bff create --name loadOrders --file ./load-orders.js
```

可选：

```bash
lovrabet personal-bff create \
  --name loadOrders \
  --description "Load active orders for dashboard" \
  --source-session-id <sessionId> \
  --file ./load-orders.js \
  --dry-run
```

## 更新

```bash
lovrabet personal-bff detail --id <id> --format compress
lovrabet personal-bff update --id <id> --file ./load-orders-v2.js --dry-run
lovrabet personal-bff update --id <id> --name loadActiveOrders --description "v2" --file ./load-orders-v2.js
```

`update` 至少要提供 `--name`、`--description`、`--file` 或 `--source-session-id` 之一。

## 执行

`exec` 会运行用户脚本，执行前必须确认目标脚本 ID、输入参数和已知副作用：

```bash
lovrabet personal-bff exec --id <id> --params '{"status":"active"}' --format compress
```

不传 `--params` 时默认 `{}`。传入值必须是 JSON 对象。

## 与下游调用配合

接入下游调用前先执行 personal BFF，并保存返回形状摘要：

```bash
lovrabet personal-bff exec --id <id> --params '{"status":"active"}' --format compress
```

确认字段、空态和错误形状后，再按下游调用方的契约完成接入。
