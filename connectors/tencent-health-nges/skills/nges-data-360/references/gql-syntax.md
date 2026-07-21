# 重楼 GQL 查询语法参考（数据洞察版）

重楼 GQL 是**自定义的类 GraphQL 语法**，不是标准 GraphQL。本文件聚焦数据洞察所需的**只读查询**能力：过滤、排序、分页、聚合、分组、关联、系统变量/函数。写操作（insert/update/delete）不在本 Skill 范围。

> 本文示例中的对象名/字段名（如 `visit`、`visit_date`、`status:"done"`）仅用于**演示语法结构**，不代表真实 schema。实际对象的字段名与枚举值以 `GetObjectsByNames` 返回为准（拜访/会议/用户行为的真实字段见 [common-scenarios.md](common-scenarios.md)）。

## 目录

- 基本查询结构
- 过滤条件（运算符 / 逻辑组合 / 全文检索）
- 排序、分页、去重
- 聚合统计（函数 / 全表聚合 / 分组 having）
- 别名、子查询、获取所有字段
- 关联查询（嵌套 / 点号联查 / 子对象聚合）
- 系统变量与系统函数
- 数据类型对照表

---

## 基本查询结构

可省略 `query` 关键字。最外层第一个字段为元数据对象名。

```gql
{visit(_limit: 10) {id name create_time}}
```

---

## 过滤条件（_where）

`_where` 或直接简写 `字段: 值`（多条件隐式 AND）：

```gql
{visit(status: "done", visit_type: "F2F") {id status}}
{visit(_where: {status: "done"}) {id status}}
```

### 比较运算符

| 运算符 | 说明 | 示例 |
|--------|------|------|
| `_eq` | 等于（默认） | `status: {_eq: "done"}` 或 `status: "done"` |
| `_neq` | 不等于 | `status: {_neq: "draft"}` |
| `_gt`/`_gte` | 大于/大于等于 | `visit_date: {_gte: 1717171200}` |
| `_lt`/`_lte` | 小于/小于等于 | `visit_date: {_lt: 1719763200}` |
| `_like` | 模糊匹配 | `name: {_like: "%张%"}` |
| `_ilike` | 忽略大小写模糊 | `name: {_ilike: "%abc%"}` |
| `_like_any` | 多值模糊（OR） | `name: {_like_any: ["%张%","%李%"]}` |
| `_in` | 属于集合 | `belong_territory: {_in: ["T1","T2"]}` |
| `_nin` | 不属于集合 | `id: {_nin: ["123"]}` |
| `_between` | 区间（闭区间） | `visit_date: {_between: [1717171200,1719763200]}` |
| `_is_null` | 是否为 null | `owner: {_is_null: false}` |
| `_include_any` | 数组含任一 | `tags: {_include_any: ["a"]}` |
| `_include_all` | 数组含全部 | `tags: {_include_all: ["a","b"]}` |

### 逻辑运算符

| 运算符 | 说明 | 示例 |
|--------|------|------|
| 隐式 AND | 同对象多字段默认 AND | `{status:"done", visit_type:"F2F"}` |
| `_and` | 显式 AND | `_and:[{a:1},{b:2}]` |
| `_or` | 或 | `_or:[{status:"done"},{status:"closed"}]` |
| `_not` | 非 | `_not:{owner:{_is_null:true}}` |

```gql
{
  visit(_where: {
    _and: [
      {visit_date: {_gte: 1717171200}}
      {_or: [{status: "done"}, {status: "closed"}]}
    ]
  }) {id status visit_date}
}
```

### 全文检索（_ft_search）

需字段建有 GIN_FT 索引，使用**索引名**（非字段名）。检索语法：`&`(与) `|`(或) `!`(非) `<->`(相邻) `()`(分组)。

```gql
{visit(_where: {idx_ft_summary: {_ft_search: "学术 & 推广"}}) {id summary}}
```

---

## 排序、分页、去重

```gql
{visit(_order_by: {visit_date: _desc, id: _asc}, _limit: 20, _offset: 0) {id visit_date}}
{visit(_distinct_on: [owner], _order_by: {owner: _asc, visit_date: _desc}) {owner visit_date}}
```

> `_offset = (页码 - 1) × _limit`。

---

## 聚合统计

### 聚合函数

| 函数 | 说明 | 示例 |
|------|------|------|
| `_count` | 计数 | `_count(id)` |
| `_sum` | 求和 | `_sum(amount)` |
| `_avg` | 平均 | `_avg(amount)` |
| `_max`/`_min` | 最大/最小 | `_max(visit_date)` |
| `_distinct_count` | 去重计数 | `_distinct_count(hcp_id)` |
| `_string_agg` | 拼接文本 | `_string_agg(name, "、")` |
| `_array_agg` | 聚合为数组 | `_array_agg(owner, true)` |

> ⚠️ **返回字段名不带下划线**：GQL 写 `_count`/`_sum`/`_avg`，返回 JSON 是 `count`/`sum`/`avg`。用别名可避免混淆：`cnt: _count(id)` → 返回 `cnt`。

### 全表聚合（_aggregate，同时返回总数+数据）

```gql
{visit(_where: {status: "done"}, _limit: 20) {
  _aggregate { _count }
  id visit_date
}}
```

返回：`{"visit": {"_aggregate": {"count": 1646}, "_data": [...]}}`

### 分组聚合（_group_by + _having）

```gql
{visit(
  _where: {visit_date: {_gte: 1717171200}}
  _group_by: [owner]
  _having: {_count(id): {_gt: 5}}
  _order_by: {cnt: _desc}
) {
  owner
  cnt: _count(id)
  latest: _max(visit_date)
}}
```

---

## 别名、子查询、获取所有字段

```gql
# 别名
{visit(_limit: 5) {visit_id: id, when: visit_date, cnt: _count(id)}}

# 子查询：__ 标记子查询，主查询用 $__N 引用
{
  visit(id: {_in: $__1}, _limit: 50) {id status}
  __1: visit_item(product_id: "P100") {visit_id}
}

# 获取所有物理字段（不含关联/公式/汇总虚拟字段）
{visit(_limit: 1) {_all}}
# 需要虚拟字段时显式列出
{visit(_limit: 1) {_all, owner_info {name}, total_amount}}
```

---

## 关联查询

> 关联字段（虚拟字段名）来自 `GetObjectsByNames` 返回的 `relations`，不要猜。

```gql
# 嵌套查询子对象（一对多）+ 子对象过滤
{visit(_limit: 10) {
  id visit_date
  visit_items(_where: {status: "done"}, _limit: 5) {id product_id}
}}

# 子对象数量聚合
{visit(_limit: 10) {
  id
  visit_items { _aggregate { _count } }
}}

# 点号联查（仅一对一关联可扁平化）
{visit(_limit: 10) {id visit_date owner_info.name owner_info.uin}}
```

---

## 系统变量

| 变量 | 类型 | 说明 |
|------|------|------|
| `$_uin` | string | 当前用户 uin |
| `$_territory` | string | 当前用户岗位 code |
| `$_territory_all` | []string | 本岗及**所有下属岗位** code |
| `$_org` | string | 当前组织 code |
| `$_org_all` | []string | 本组织及下属组织 code |
| `$_now` | int64 | 当前秒级时间戳 |

> ⚠️ **数据范围通常不用这些变量手写**：重楼按角色配置了**行权限**，执行查询时会自动注入数据范围过滤（Rep 自动只看自己、DSM/RSM 自动看团队）。默认**直接查询、不加 `owner`/`belong_territory`**。这些变量只在需要**主动收窄**时备用（如管理者只看自己 `owner: $_uin`）。详见 [roles-and-data-scope.md](roles-and-data-scope.md)。

```gql
# 仅在需要主动收窄范围时才这样写：
# 管理者只看自己
{visit(owner: $_uin, _limit: 20) {id actual_date}}
# 手动表达"本岗及下属"（一般无需，行权限已覆盖）
{visit(belong_territory: {_in: $_territory_all}, _limit: 50) {id owner}}
```

---

## 系统函数（只读分析常用）

```gql
# 把秒级时间戳格式化为日期，用于按天/按月分组
{visit(_limit: 100) {
  day: _func("to_char", _func("to_timestamp", visit_date), "YYYY-MM-DD")
  cnt: _count(id)
}}
```

`_func` 白名单常用：`to_char`、`to_timestamp`、`length`、`upper`/`lower`、`coalesce`、`round`、`abs`、`cast`。

---

## 数据类型对照表（过滤/比较取值用）

| value_type | GQL 值写法 | 示例 |
|-----------|-----------|------|
| INT | 整数不加引号 | `age: 25` |
| TEXT | 双引号 | `name: "张三"` |
| DATETIME | **秒级**时间戳不加引号 | `visit_date: {_gte: 1717171200}` |
| SELECT_ONE | 选项的 value（双引号） | `status: "done"` |
| SELECT_MANY | 逗号分隔无空格 | `tags: "a,b,c"` |
| SELECT_ONE_INT | 选项整数 value | `level: 2` |
| BOOL | `true`/`false` 不加引号 | `is_valid: true` |
| FLOAT/NUMERIC/MONEY | 数字不加引号 | `amount: {_gte: 100.5}` |
| ARRAY | 数组字面量 | `ids: {_include_any: [1,2]}` |
| JSON | 三引号包裹 | `cfg: """{"k":"v"}"""` |

> **虚拟字段**（`AUTO_NUMBER`/`FORMULA`/`ROLLUP_SUMMARY`）：可查询/可参与返回，但 `_all` 不含，需显式列出；不可用于写入。

> **日期再强调**：库里存的是**秒**。把"本月""最近 7 天"换算成秒级时间戳区间再过滤，别用毫秒。
