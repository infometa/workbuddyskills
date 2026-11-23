# Dataset Discovery Workflow

## 概述

在执行 Instant API 数据操作前，需要先找到目标数据集并了解其字段结构。

按已知线索选择筛选参数：数据集名称用 `--name`，物理表名用 `--table-name`，数据集 code 用 `--code`。下面按名称验证应用的示例，在已知物理表名时可将 `--name "<关键词>"` 换成 `--table-name "<表名前缀>"`。

## 应用选择

应用选择统一遵循[默认应用与应用发现](../guides/app-resolution.md)：未指定目标时先查默认 AppCode（顶层 `appcode` 或 `defaultApp` 解析结果）；仅在成功查询无合理匹配、核对筛选条件且用户未限定范围后，才扩大只读发现。认证、权限或连接错误不触发跨应用重试。

`--app` / `--appcode` 只对本次命令生效。临时选择其他应用后，后续每条 `detail`、`data` 或执行命令都必须显式携带该目标；资源标识必须与发现它的 AppCode 配对，不能依靠上一条命令改变默认值。

## 命令

### api-doc list/detail — 查看运行态 API 文档

写 Personal Backend Function 或复杂数据访问说明前，先用 API 文档收敛可用接口：

```bash
lovrabet api-doc list --category dataset
lovrabet api-doc list --keyword aggregate
lovrabet api-doc detail --code dataset_data_filter
```

`api-doc` 是只读文档发现命令，不是通用 HTTP fetch；不要把它替代成任意路径调用。

### dataset list — 列出数据集

```bash
# 列出全部
lovrabet dataset list

# 按名称过滤（服务端模糊匹配）
lovrabet dataset list --name "订单"

# 仅按物理表名前缀过滤，无需同时提供 --name 或 --code
lovrabet dataset list --table-name crm_product

# 同时限定数据集名称和物理表名（AND）
lovrabet dataset list --name "商品" --table-name crm_product

# 按 code 过滤（服务端精确匹配）
lovrabet dataset list --code "abc123def4567890abcdef012345678"

# JSON 格式输出（AI Agent 推荐）
lovrabet dataset list --format json
```

返回字段: id, code, name, source, description, table, datasetKey, pk, **fields**

其中 `fields` 是从 `dbtableConfig.allFields` 解析出的字段名数组，可直接用于构造 `data filter` 的 `select` 和 `where` 参数，无需再调 `dataset detail`。

| Flag | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--name` | string | 否 | 按数据集名称包含匹配（服务端） |
| `--table-name` | string | 否 | 透传为 `tableName`，按物理表名前缀匹配（服务端） |
| `--code` | string | 否 | 按 dataset code 精确过滤（服务端，32 位 hex） |
| `--format` | string | 否 | 输出格式：`json` / `pretty` / `table` |

`--name`、`--table-name`、`--code` 均为可选参数：可只传任意一个，也可不传筛选参数；多个参数同时传入时按 AND 组合，不会互相覆盖。不传或传空字符串时不增加对应筛选条件。

`--table-name` 使用服务端 SQL LIKE 前缀匹配，不保证精确命中或唯一结果。例如 `crm_product` 也可能命中 `crm_product_detail`；`%` 和 `_` 保留 SQL LIKE 通配符含义，其中 `_` 可匹配任意单个字符。核对返回的 `table`、`name` 和 `code` 后再选择目标数据集，不要直接取第一条。

### dataset detail — 查看数据集结构

```bash
lovrabet dataset detail --code <datasetCode>

# 返回 CLI 归一化 JSON 结构
lovrabet dataset detail --code <datasetCode> --format json
```

| Flag | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--code` | string | **是** | 数据集 code（32 位 hex UUID） |
| `--format` | string | 否 | 输出格式：`json` / `pretty` / `compress` |

返回内容:
- **字段列表** — name, displayName, type, dbType, pk, required, description, options
- **关联信息** — `relations` 直接透出接口返回的原始关联信息；结构以服务端返回为准，CLI 不做补全推断
- **操作列表** — name, method, path（getList, getOne, create, update, delete 等）
- **统计** — fieldCount, operationCount

当运行态详情接口未返回 `fields` / `properties` 时，CLI 会从 `dataset list` 兜底字段名，保证 `fieldCount` 和字段名可用于 `data filter`；此时类型、必填、选项等详细字段属性可能为空。

### dataset sdk-doc — 查看 SDK 使用文档

```bash
lovrabet dataset sdk-doc --code <datasetCode>
```

`dataset sdk-doc` 只接受 32 位数据集 code，不接受数字 ID。返回为空时，CLI 会给出稳定的空文档提示。

## 典型工作流

```bash
# 0. 仅当满足上述扩大只读发现的条件时，查看应用目录
lovrabet app list

# 1. 在候选 app 中搜索数据集
lovrabet dataset list --app crm --name "公司"

# 2. 命中后在同一应用查看字段结构
lovrabet dataset detail --app crm --code 2874b19935c240659e8872e9e2416ae3

# 3. 确认字段名后，在同一应用执行 Instant API 数据操作
lovrabet data filter --app crm --code 2874b19935c240659e8872e9e2416ae3 \
  --params '{"where":{"name":{"$contain":"test"}},"currentPage":1,"pageSize":20}'
```

如果使用配置中的默认应用，则直接：

```bash
# 1. 搜索数据集
lovrabet dataset list --name "公司"

# 2. list 已返回 fields 数组，可直接用于构造查询
#    如果需要字段类型等详细信息，再调 detail
lovrabet dataset detail --code 2874b19935c240659e8872e9e2416ae3

# 3. 确认字段名后，开始 Instant API 数据操作
lovrabet data filter --code 2874b19935c240659e8872e9e2416ae3 \
  --params '{"where":{"name":{"$contain":"test"}},"currentPage":1,"pageSize":20}'
```

## 注意事项

1. 使用 `--format json` 获取结构化输出，便于程序解析
2. `dataset list` 返回的 `fields` 数组包含所有字段名，多数场景下无需额外调 `detail`
3. `dataset detail` 返回的字段兼容 v1（properties）和 v2（fields）两种数据集格式；运行态接口未给完整字段时会兜底字段名
4. 数据集的 code 是 32 位 hex UUID，是所有 `data *` 命令的必填参数
5. 已明确目标但它不是配置中的默认应用时，在每条命令中显式指定 `--appcode` 或 `--app`
6. 写 Personal Backend Function 或其他数据访问源码前，除非用户已经提供明确数据，否则先用 `api-doc`、`dataset detail`、`dataset sdk-doc` 和只读 `data` 命令确认真实结构
