# 记录列表查询

`query list <ObjectType>` 返回当前身份可见的记录页。它支持两种互斥输入模式：常用参数模式适合扁平 AND 条件，结构化输入模式适合 OR、NOT、嵌套条件和递归 includes。工作台预置视图不在本文件范围。

## 最短查询与字段范围

对象和目标已经明确时，可以直接省略 `--fields`：

```shell
qiqi query list Reimburse --limit 20 --format json
```

省略 `--fields` 时，服务端使用与 `describe list <ObjectType>` 同源、同序的默认 LIST 字段解析结果。`describe list` 用于预览这些字段和少量样例，不是执行查询的前置步骤。

- `describe list` 与默认 `query list` 使用相同字段 resolver，但描述和查询各自存在字段数量上限，极端情况下数量可能不同。
- 默认响应中的 `fields` FieldTable 是本次实际返回字段的权威说明。
- 显式传入 `--fields` 时，只请求给定字段，不自动补充默认列表字段。
- 过滤字段不必同时出现在投影中；需要向用户证明过滤结果时再将其加入 `--fields`。
- 需要固定结果结构、减少输出或进行批量分析时，优先显式指定完成任务所需的最小字段集合。
- `--fields` 优先使用一个逗号分隔字符串；在 PowerShell 中也把完整字段列表包进引号，例如 `--fields "id,name"`。

`describe fields <ObjectType>` 用于确认根过滤字段的类型、引用和时间语义；`describe list` 主要描述常用展示投影。两者不能互相替代。

## 关闭 fields 返回

`query list` 默认每次都返回 `fields`。字段范围已经确定后，用 `--no-fields` 让本次响应不再带它：

```shell
qiqi query list Reimburse --fields "id,amount,businessDate" --limit 20 --format json
qiqi query list Reimburse --fields "id,amount,businessDate" --offset 20 --limit 20 --no-fields --format json
```

适用场景是同一字段范围内的翻页与重复查询：首次查询（或 `describe list`）已经给出字段范围，后续再返回 `fields` 只是重复信息。

- `--no-fields` 只改变响应形态，不改变查询的字段范围，也不改变每行返回哪些 key。
- 它可以与 `--input` 同用，但 `--input` JSON 中不得声明 `includeFields`。
- 加上 `--no-fields` 后 `--format table` 会用 `fieldName` 作表头，不再显示中文标题；需要中文标题时不要加这个参数。
- 省略 `--fields` 的默认投影同样可以使用 `--no-fields`，但此时应已从首次查询或 `describe list` 确认过字段范围。

## 选择输入模式

使用以下规则选择模式：

1. 条件只需要按 AND 组合时，使用可重复的 `--where`。
2. 同一字段匹配多个值时，在常用模式中使用 `in`，不要为 OR 改用多个 `--where`。
3. 出现跨字段 OR、NOT、嵌套组合或递归 includes 时，整条查询改用 `--input <path|->`。
4. `--input` 不能与 `--fields`、`--where`、`--order-by`、`--offset` 或 `--limit` 混用；`ObjectType` 始终是命令行位置参数。`--no-fields` 不受此限制，两种模式都能加。

## 常用参数模式

语法核心：

```text
qiqi query list <ObjectType>
  [--fields <field,...>]
  [--where <field> <operator> [values...]]...
  [--order-by <field> <asc|desc>]...
  [--offset <n>]
  [--limit <n>]
  [--no-fields]
```

多个 `--where` 永远按输入顺序以 AND 组合：

```shell
qiqi query list Reimburse --fields "id,amount,businessDate" --where amount between 100 1000 --where businessDate ge 2026-07-01 --order-by businessDate desc --order-by id asc --limit 20 --format json
```

同字段 OR 使用 `in`：

```shell
qiqi query list Reimburse --fields "id,billStatus" --where billStatus in BillStatus.draft BillStatus.submitted --limit 20 --format json
```

公共操作符及值数量：

- 等值：`eq/ne` 各 1 个值。
- 比较：`gt/ge/lt/le` 各 1 个值。
- 文本：`contains/begin/end` 各 1 个值；`contains` 是唯一包含操作符，不使用 `like`。
- 集合：`in/notin` 接受 1～100 个值。
- 范围：`between` 恰好 2 个值。
- 空值：`isnull/notnull` 不传值。

这些是 CLI 接受的公共语法，不代表每个字段都支持全部操作符。服务端根据字段 metadata 校验“字段类型 × 操作符”，并在不兼容时返回该字段允许的操作符。

## 结构化输入模式

`--input <path|->` 读取 UTF-8 JSON：`<path>` 表示文件，`-` 表示从 stdin 读取到 EOF。输入必须是单个 JSON object，且只能包含：

- `fields`
- `where`
- `orderBy`
- `includes`
- `offset`
- `limit`

不得在 JSON 中声明 `objectType` 或 `includeFields`：前者是命令行位置参数，后者用命令行的 `--no-fields`。跨字段 OR 与 NOT 示例：

```json
{
  "fields": ["id", "description", "billStatus"],
  "where": {
    "OR": [
      {"billStatus": "BillStatus.submitted"},
      {
        "NOT": [
          {"description": {"contains": "测试"}}
        ]
      }
    ]
  },
  "orderBy": [
    {"field": "businessDate", "direction": "desc"},
    {"field": "id", "direction": "asc"}
  ],
  "offset": 0,
  "limit": 20
}
```

保存为 UTF-8 `query.json` 后执行：

```shell
qiqi query list Reimburse --input query.json --format json
```

也可以把同一个 JSON object 直接写入 stdin：

```text
command: qiqi query list Reimburse --input - --dry-run
stdin（UTF-8 JSON，写入后结束输入）:
{"fields":["id","code"],"where":{"code":{"contains":"RB"}},"limit":20}
```

`--input -` 与 `--credential-stdin` 不能同时使用，因为二者会争用同一个 stdin。此时应使用已登录 Profile、把查询保存为文件，或改用其它受支持的调用凭证来源；不得把凭证明文写入命令行。

结构化 `where` 必须遵循以下唯一语法：

- `{"field": "value"}` 表示 `eq`。
- `{"field": null}` 表示 `isnull`。
- 其它谓词写为 `{"field": {"operator": operand}}`。
- `AND/OR` 的值是非空节点数组；`NOT` 的值是恰好包含一个节点的数组。
- 普通 operand 必须是 JSON string；布尔、整数、小数和时间也分别写成 `"true"`、`"100"`、`"123.450"` 和规范时间文本。
- `in/notin/between` 的 operand 是有界 JSON string array。
- `notnull` 写为 `{"field": {"notnull": null}}`。
- 不使用显式 `{"eq": ...}` 或 `{"isnull": ...}`；分别使用字符串和 JSON null 简写。
- 单个节点不能依靠多个字段成员隐式表达 AND；应显式使用大写 `AND`。

`includes` 用于随根记录展开 metadata 已确认的集合关系。根查询先按根级 `where/orderBy/offset/limit` 取得记录页，服务端再批量查询各根记录的子记录，并按父记录身份回挂为嵌套数组。

- `relation` 是根对象或当前子对象上的真实集合关系，不是任意 JOIN。
- `fields/where/orderBy` 只作用于该层子记录；子级 `where` 不会筛掉不满足条件的根记录。
- 下级 `includes` 可以继续展开真实子关系，并复用相同的字段、过滤、权限和复杂度规则。
- `includes` 只负责读取关系数据，不提供聚合，也不表达“根记录存在某类子记录”的筛选语义。

已验证的报销单明细展开示意：

```json
{
  "fields": ["id", "code"],
  "includes": [
    {
      "relation": "reimburseItems",
      "fields": ["id", "amount"],
      "where": {"amount": {"gt": "0"}}
    }
  ],
  "limit": 20
}
```

`includes` 受关系真实性、字段权限、递归深度、结果行数和响应大小限制；任一层不满足约束时应整体失败，不把部分结果当作完整结果。

## 基础字段类型

先用 `describe fields <ObjectType>` 确认实际字段类型，再选择值和操作符：

- 字符串：值保持原始文本；常用 `eq/ne/contains/begin/end/in/notin`。
- 整数与数值：使用十进制文本；常用等值、比较、集合和 `between`。金额精度由服务端 metadata 校验。
- 布尔：只使用小写 `true/false`，常用 `eq/ne`。
- 枚举：先用 `query values` 取得完整枚举值，例如 `BillStatus.submitted`，再使用等值或集合操作符。
- 引用：先用 `query values` 取得稳定记录 ID，不使用显示名称代替 ID；常用等值、集合和空值操作符。
- 日期：使用严格 `YYYY-MM-DD`，并且必须是实际存在的自然日；例如 `2024-02-29` 合法，`2026-02-30` 会被拒绝而不会自动滚动到三月。
- 时间点：使用带 `Z` 或显式 offset、毫秒精度以内的 RFC3339；不使用无 offset 的本地时间。
- 空值：字段允许为空时使用 `isnull/notnull`，不要用空字符串代替 null。
- 列表字段不是普通标量过滤目标；查询子关系使用结构化 includes，或查询 metadata 已提供的计数字段。

CLI 在常用模式中保留 argv 原始 UTF-8 文本，不读取 metadata，也不猜测 boolean、number 或时间类型；最终转换和合法性由服务端完成。

## 排序、分页与完整性

- 需要跨页读取时使用可复现的稳定排序；业务排序字段可能重复时追加稳定唯一字段作为次级排序。
- 持续读取 `offset/limit` 分页，直到 `hasMore` 明确为 `false`。
- 不把 `describe list` 样例、第一页或终端截取内容当成全集；`total` 只能说明当前筛选范围的记录数，需要逐条分析时仍须读取全部分页。
- offset 分页期间数据持续变化可能造成跨页重复或遗漏；任务要求严格快照一致性时，应说明当前能力边界，不能仅靠重试假装获得快照。
- 收到 `77hub.large-output` 时，打开 `uri` 或读取 `path` 指向的完整 JSON；`summary` 只用于定位主集合、对象和分页，不能替代完整内容。
- 权限不可见、分页未结束、过滤口径未确认或完整输出未读取时，不声称完成全量统计。
- `query list` 的结果单位是记录，不提供聚合语义；需要合计、分组或度量互比时使用 `query aggregate`，见 [aggregate-query.md](aggregate-query.md)。不要用分页 list 假装全量汇总。

## 验证与错误边界

`--dry-run` 在认证和网络前输出最终 params，只证明客户端结构有效，不证明对象、字段、权限、字段类型、操作符兼容性或服务端执行有效。

没有查到记录可能来自筛选、权限、对象不可用或数据不存在。没有额外证据时只报告“当前范围未查到”，不要断言全系统不存在。
