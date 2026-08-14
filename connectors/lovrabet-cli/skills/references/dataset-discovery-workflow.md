# Dataset Discovery Workflow

## 概述

在执行 Instant API 数据操作前，需要先找到目标数据集并了解其字段结构。

## 先不要默认查 app

`dataset` 工作流的第一步不是固定的 `app list`，而是先判断当前是否已经有明确 app 上下文。

### 直接进入数据集发现

以下情况可以直接执行 `dataset list`：

- 用户已经给了 `--appcode`
- 用户已经给了 `--app <name>`
- 当前问题明显是在上文已确认的同一 app 里继续操作
- 用户明确说“当前应用”“默认应用”，且没有新的业务域线索

`defaultApp` 只是默认候选。用户提到订单、商品、库存、客户、证照等业务对象且未显式指定 app 时，先在默认候选里按关键词查数据集；命中合理再继续，无命中或不合理再扩大到 app 目录。

### 需要先做应用决议

以下情况应先获取应用信息，再决定目标 app：

- 用户只说了业务需求，没有给 app 线索
- 当前没有显式 `--appcode` / `--app`，且需求包含业务域或数据对象线索
- 需求描述可能对应多个业务应用
- 已经在 `defaultApp` 下按关键词验证过，但没有合理数据集命中

若当前有 `defaultApp`，推荐先执行：

```bash
lovrabet dataset list --name "<关键词>"
```

默认候选无命中、弱命中或语义不合理时，再执行：

```bash
lovrabet app list
```

再根据业务关键词挑 1-2 个候选应用，执行：

```bash
lovrabet dataset list --app <name> --name "<关键词>"
```

通过数据集命中结果反向确认 app，而不是只看 app 名称猜测。

## 命令

### api-doc list/detail — 查看运行态 API 文档

写 personal BFF 或复杂数据访问说明前，先用 API 文档收敛可用接口：

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

# 按 code 过滤（服务端精确匹配）
lovrabet dataset list --code "abc123def4567890abcdef012345678"

# JSON 格式输出（AI Agent 推荐）
lovrabet dataset list --format json
```

返回字段: id, code, name, source, description, table, datasetKey, pk, **fields**

其中 `fields` 是从 `dbtableConfig.allFields` 解析出的字段名数组，可直接用于构造 `data filter` 的 `select` 和 `where` 参数，无需再调 `dataset detail`。

| Flag | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--name` | string | 否 | 按名称模糊过滤（服务端） |
| `--code` | string | 否 | 按 dataset code 精确过滤（服务端，32 位 hex） |
| `--format` | string | 否 | 输出格式：`json` / `pretty` / `table` |

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
# 0. 如果默认候选验证不成立，再看应用目录
lovrabet app list

# 1. 在候选 app 中搜索数据集
lovrabet dataset list --app crm --name "公司"

# 2. 命中后查看字段结构
lovrabet dataset detail --code 2874b19935c240659e8872e9e2416ae3

# 3. 确认字段名后，开始 Instant API 数据操作
lovrabet data filter --code 2874b19935c240659e8872e9e2416ae3 \
  --params '{"where":{"name":{"$contain":"test"}},"currentPage":1,"pageSize":20}'
```

如果当前 app 已明确，则直接：

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
5. 当业务需求不明确落在哪个 app 时，先验证 `defaultApp`；验证不成立再 `app list`，并用 `dataset list --app <name> --name <关键词>` 做验证式收敛
6. 写 personal BFF 或其他数据访问源码前，除非用户已经提供明确数据，否则先用 `api-doc`、`dataset detail`、`dataset sdk-doc` 和只读 `data` 命令确认真实结构
