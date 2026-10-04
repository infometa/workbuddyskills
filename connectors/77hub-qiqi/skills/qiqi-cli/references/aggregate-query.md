# 聚合查询

`query aggregate <ObjectType>` 在服务端做合计或分组统计，返回与 `query list` 同形的 page。金额、日期按与 `query list` 相同的公开格式写出。它支持两种互斥输入模式：常用参数模式适合扁平 AND 条件与度量互比，结构化输入模式适合跨字段 OR、NOT 或必须显式写出的度量引用。

不要用分页 `query list` 拉明细再在本地加总。按表体汇总时，ObjectType 传表体对象，不要把 `includes` 塞进 aggregate。过滤字段的类型、操作符和值写法与 `query list` 相同，见 [list-query.md](list-query.md)。

## 最短查询

无分组时固定 1 行（having 不满足则为空页）：

```shell
qiqi query aggregate ReceiptItem --measure count id --measure sum amount --format json
```

## 选择输入模式

使用以下规则选择模式：

1. 条件只需要按 AND 组合、having 只比较字面量或本请求别名时，使用可重复的 `--where` / `--having`。
2. 同一字段匹配多个值时，在常用模式中使用 `in`，不要为 OR 改用多个 `--where`。
3. 出现跨字段 OR、NOT 或需要显式度量引用时，整条查询改用 `--input <path|->`。
4. `--input` 不能与 `--group-by`、`--measure`、`--where`、`--having`、`--order-by`、`--offset` 或 `--limit` 混用；`ObjectType` 始终是命令行位置参数。

## 常用参数模式

语法核心：

```text
qiqi query aggregate <ObjectType>
  [--group-by <field>]...
  --measure <fn> <field>...
  [--where <field> <operator> [values...]]...
  [--having <alias> <operator> [values...]]...
  [--order-by <field-or-alias> <asc|desc>]...
  [--offset <n>]
  [--limit <n>]
```

`--where` 先过滤明细，`--having` 只过滤聚合后的度量别名：

```shell
qiqi query aggregate Reimburse --group-by billStatus --measure count id --measure sum amount --where businessDate ge 2026-01-01 --having sum_amount gt 0 --limit 20 --format json
```

度量互比时，右操作数若恰好等于本请求某个度量别名，按度量引用绑定：

```shell
qiqi query aggregate Reimburse --measure sum originAmount --measure max amount --having sum_originAmount ne max_amount --dry-run
```

聚合函数只允许 `count` / `sum` / `avg` / `min` / `max` / `count_distinct`。`--measure` 恰好两个 token：函数和字段点路径。自动别名是 `{fn}_{field}`，字段路径里的 `.` 换成 `_`。例如 `sum amount` → `sum_amount`，`max contractSubjectMatterItem.originRcWriteBackAmount` → `max_contractSubjectMatterItem_originRcWriteBackAmount`。

`--having` 左操作数必须是本请求度量别名。`--having amount gt 0` 非法，因为 `amount` 是源字段。常用模式里，右操作数若恰好等于本请求某个度量别名，按度量引用绑定；否则保持文本字面量。

根字段 `id` 不能作为 `--group-by`。

## 结构化输入模式

`--input <path|->` 读取 UTF-8 JSON：`<path>` 表示文件，`-` 表示从 stdin 读取到 EOF。输入必须是单个 JSON object，且只能包含：

- `groupBy`
- `measures`
- `where`
- `having`
- `orderBy`
- `offset`
- `limit`

不得在 JSON 中声明 `objectType`。`--input` 禁止靠撞名猜测：字面量用 JSON 字符串，度量互比必须写 `{"measure":"<alias>"}`。

```json
{
  "measures": [
    {"fn": "sum", "field": "quotedAmount", "as": "quotedAmount"},
    {"fn": "sum", "field": "writtenAmount", "as": "writtenAmount"}
  ],
  "having": {"quotedAmount": {"ne": {"measure": "writtenAmount"}}}
}
```

保存为 UTF-8 `aggregate.json` 后执行：

```shell
qiqi query aggregate Reimburse --input aggregate.json --format json
```

也可以把同一个 JSON object 直接写入 stdin：

```text
command: qiqi query aggregate Reimburse --input - --dry-run
stdin（UTF-8 JSON，写入后结束输入）:
{"measures":[{"fn":"count","field":"id","as":"count_id"}]}
```

`--input -` 与 `--credential-stdin` 不能同时使用，因为二者会争用同一个 stdin。此时应使用已登录 Profile、把查询保存为文件，或改用其它受支持的调用凭证来源；不得把凭证明文写入命令行。

结构化 `where` 语法与 `query list` 相同，见 [list-query.md](list-query.md)。

## 预算、分页与完整性

- 度量最多 20 个，分组字段最多 5 个。
- 有分组：`limit` 默认 20，上限 200。
- 无分组：`limit` 只能为 1。
- 成功响应是 `rows/total/offset/limit/hasMore/objectType`。有分组时 `total` 是桶数，不是明细行数。

## 验证与错误边界

`--dry-run` 在认证和网络前输出最终 params，只证明客户端结构有效，不证明对象、字段、权限、字段类型、操作符兼容性或服务端执行有效。

没有查到桶可能来自筛选、having、权限、对象不可用或数据不存在。没有额外证据时只报告“当前范围未查到”，不要断言全系统不存在。
