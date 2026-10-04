# 东证期货知识百科 MCP 接口参考

本 Skill 使用两个 MCP server：

- `orientfutures_mobile_knowledge_base`：知识书目、目录和章节正文；
- `orientfutures_mobile_market_data`：单一实际期货合约的行情码表静态资料。

以下内容来自服务运行时实际注册的 Schema。运行时 Schema 是最终依据；工具未注册或签名发生变化时，不沿用本文件中的旧参数。

## 一、知识 MCP

知识 MCP 当前注册三个原子检索工具、一个查询级可视化组合工具和独立业务链接展示工具，没有关键词搜索、现行规则或计算工具。

### `knowledge_base_list_books`

列出可用期货知识书目。每条新的知识查询链路从这里开始。

- 入参：空对象 `{}`。
- 输出：`books[]`。
- 每本书字段：
  - `key: string`
  - `name: string`
  - `sectionCount: integer`

后续工具的 `book_key` 必须来自本次响应。通用期货知识使用与 `futures-derivatives-basics` / “期货及衍生品基础”匹配的书目；MACD、RSI、KDJ、BOLL、移动平均等技术分析体系使用与 `technical-analysis-financial-markets` 匹配的书目。两者都必须先从本次真实书目结果确认，不得跳过发现步骤。

### `knowledge_base_get_book_toc`

浏览整本书或指定根节点下的目录。

| 参数 | 必填 | 类型与限制 |
| --- | --- | --- |
| `book_key` | 是 | 非空字符串，来自 `knowledge_base_list_books` |
| `root` | 否 | 目录返回的章节键，格式 `^\d{1,6}(/\d{1,6})*$` |
| `depth` | 否 | 整数 1～6；相对 `root` 的最大目录深度 |

输出字段：

- 必有：`book`、`totalSizeBytes`、`sections`；
- 按请求可能返回：`root`、`depth`；
- `sections[]` 每项包含 `key`、`title`、`level`、`selfSizeBytes`、`subtreeSizeBytes`、`childCount`，并可递归包含 `children[]`。

用 `subtreeSizeBytes` 判断正文读取粒度。章节键必须来自实际目录，不得依据标题或示例键自行构造。
目录结果的 `presentation.status` 固定为 `not_applicable`，不返回可组合的 `evidenceRef`；目录仅用于定位正文，绝不画成知识体系图。

### `knowledge_base_get_section_content`

读取一个章节自身或其子树的 Markdown 正文。

| 参数 | 必填 | 类型与限制 |
| --- | --- | --- |
| `book_key` | 是 | 来自书目列表 |
| `section` | 是 | 字符串；逐字复用目录返回的 `key`并保留前导零，格式 `^\d{1,6}(/\d{1,6})*$` |
| `view` | 否 | `subtree` 或 `self`；默认 `subtree` |
| `max_bytes` | 否 | 整数 1000～200000；默认 50000 |

该工具没有 `depth` 入参。

响应至少包含 `book`、`section`、`title`、`titlePath`、`view`、`oversized`；还可能包含 `sectionCount`、`sizeBytes`、`markdown`、`subtreeSizeBytes`、`maxBytes`、`selfSizeBytes`、`hint`、`children`。

当 `oversized=true` 时，`markdown` 会被主动省略。根据 `children`、`hint` 和目录下钻，或改用 `view="self"`；不能把它解释为知识不存在。

### `knowledge_visual_compose`

唯一入参 dashboard_spec，1～8 个证据绑定区块，字段见 [公共渲染契约](../workbuddy-visual-rendering/references--dashboard-spec.md)。只使用本轮 evidenceRef 和 evidenceBindings，不读共享文件、不手填实际数值。

返回 composition_id、composition_status、evidence_refs、ignored_evidence_count、publication、provenance 和 presentation。无有效块时不展示 Widget。旧参数拒绝，知识正文不能推导个人进度。

## 二、行情 MCP：单一合约静态资料

行情 MCP 仅用于一个已确认实际合约的搜索和静态字段。技术指标公式目录、实时/历史指标结果均不属于本 Skill 工具范围，数据需求转综合查询；不得恢复理论加实盘快照分支。

### 公共类型

- 市场：`domestic_futures`、`foreign_futures`。
- 合约键：`{ code: string, market?: FuturesMarket }`。
- 只传基础展示代码；`market` 仅用于消除市场歧义。
- `future_types`：`normal`、`index`、`main`、`nearby`、`spd`、`ips`、`foreign_option`。
- `main_types`：`none`、`sub`、`main`。
- 交易所枚举来自当前期货码表与运行时 Schema，不用国内静态示例限制已支持的市场。

### `futures_search_instruments`

按代码、名称或拼音缩写搜索期货对象。

| 参数 | 必填 | 类型与限制 |
| --- | --- | --- |
| `markets` | 是 | 至少一个市场枚举 |
| `keyword` | 是 | 非空字符串 |
| `limit` | 否 | 默认 20，范围 1～1000 |
| `offset` | 否 | 默认 0，非负整数 |
| `future_types` | 否 | 对象类型枚举数组；实际合约使用 `["normal"]` |

结果只包含期货字段。用本次返回的代码、名称、市场、交易所和类型消歧；多个候选不能自动选第一个。

### `futures_get_instrument_info`

查询 1～100 个展示代码的静态信息；本 Skill 每次只查询一个已确认实际合约。

| 参数 | 必填 | 类型与限制 |
| --- | --- | --- |
| `codes` | 是 | 1～100 项，每项至少含 `code`，可选项内 `market` |
| `market` | 否 | 请求级市场提示，只用于消歧 |

服务端从码表缓存解析后端代码、交易所和资产类型。不得给代码增加交易所或供应商后缀。

### `quote_list_parameter_options`

列出高级行情参数的权威值和中文标签。本 Skill 只在 `futures_list_instruments.fields` 的字段名未知时使用。

| 参数 | 必填 | 本 Skill 使用值 |
| --- | --- | --- |
| `domain` | 是 | `futures` |
| `parameter` | 是 | `fields` |
| `usage` | 否 | `instrument_list`；缺省值虽然是 `all`，本 Skill 应显式限定用途 |
| `query` | 否 | 1～100 字符的字段含义搜索词 |

输出为 `domain`、`parameter`、`usage`、`total_count`、`matched_count`、`options`。每个 `options` 项包含：

- `value`
- `label`
- `description`
- `applicable_tools`

只使用 `applicable_tools` 表明适用于 `futures_list_instruments` 的 `value`。

### `futures_list_instruments`

筛选、分页、排序期货对象。本 Skill 只在已确认代码和市场后，用它精确核对或补充同一合约。

| 参数 | 必填 | 类型与限制 |
| --- | --- | --- |
| `market` | 是 | 市场枚举 |
| `fields` | 否 | 最多 256 项，格式 `^[a-z][a-z0-9_]*$`；必须来自参数选项工具的实际返回 |
| `sort_by` | 否 | 默认 `sort_weight`；必须是实际可排序字段 |
| `sort_direction` | 否 | `asc` 或 `desc`，默认 `asc` |
| `offset` | 否 | 默认 0，非负整数 |
| `limit` | 否 | 默认 100，范围 1～1000 |
| `return_total_count` | 否 | 布尔值，默认 `true` |
| `keywords` | 否 | 非空字符串数组 |
| `codes` | 否 | 最多 500 个合约键 |
| `exchanges` | 否 | 交易所枚举数组 |
| `index_code` | 否 | 一个合约键 |
| `night_trading` | 否 | 布尔值 |
| `future_types` | 否 | 对象类型枚举数组 |
| `main_types` | 否 | 主力类型枚举数组 |
| `product_codes` | 否 | 品种代码数组，大小写由服务端码表解析 |

格式合法不代表字段可用。字段未知时先调用 `quote_list_parameter_options`；无法确认时省略 `fields`，不得猜测。

### `futures_get_product_list`

查询期货品种、交易所和夜盘属性。

- 必填：`markets`，至少一个期货市场。
- 仅在合约响应已经返回可匹配的品种代码或名称时补充对应品种。
- 品种夜盘属性不等于具体交易时段，不能据此回答开收盘时间。

## 三、行情业务工具输出边界

除 `quote_list_parameter_options` 外，上述行情业务工具的 Schema 将外层响应定义为：

- `backendId`
- `domain`
- `capability`
- `data`

外层另含 semantics、provenance 和 presentation；data 按 capability 定义结构，并允许透传上游字段。当前查询仍以实际返回的字段和语义为准：

1. 只能解释本次响应实际出现且含义明确的字段；
2. 不把一次观测到的字段结构写成永久接口承诺；
3. 不从合约代码推导品种、月份或交易所；
4. 不补造上市日、到期日、最后交易日、交割日、交易状态、交易单位、报价单位、最小变动价位、交割方式或交易时段；
5. 原始字段的单位、时间编码或枚举含义不清时，不自行翻译成用户事实。

码表保证金按 [三层口径](../modules/fees-and-margin.md) 处理：long_margin_ratio、short_margin_ratio、margin_type 是字段发现方向，只有本轮目录与真实响应确认后才使用。报价单位/币种使用受信任原值，不由 CNY 猜元/吨；图中不显示“单位未提供”等占位，也不编造单位。未知单位使计算不可比时仍披露计算限制。

## 四、失败语义

- 工具未注册：能力未暴露给当前 Agent，不等于业务无数据。
- Transport、连接或超时：MCP 不可达。
- `isError`：按工具错误信息区分参数、权限和业务数据问题。
- 成功但列表为空：当前条件无匹配，不等于对象永久不存在。
- 字段为空：不按 0 处理，也不等于“不适用”。
- 字段不存在或含义不明确：停止对应事实输出，保留能够独立确认的其他结果。
- 只读调用失败：允许用相同参数重试一次；再次失败后停止该分支。

## `business_links_show`

独立业务链接工具，HTTP MCP Apps 在内容流直接展示固定入口。必填 `action_ids`（当前工具 Schema 中的合法 ID，非空且不重复）；可选 `catalog_version`，省略使用当前版本。拒绝额外参数，不接受 URL、文案、HTML 或 evidenceRef。

返回 `protocol_version`、`catalog_version`、`delivery_id`、`action_ids`、`state=prepared`；固定展示数据通过工具结果 `_meta.business_links` 交给 `ui://of/business-links/v1`，模型不读取或复制该 UI 数据。不调用知识后端、不读取官网、不执行业务；prepared 不证明可见或已打开。失败/未知处理与场景位置见业务链接 Component。
