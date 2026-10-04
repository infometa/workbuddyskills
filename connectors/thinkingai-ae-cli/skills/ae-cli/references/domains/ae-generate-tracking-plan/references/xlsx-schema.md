# AE Tracking Plan xlsx Format Contract (internal reference)

> **Terminology**: 格式契约 = format contract | 必填列 = required column | 合并单元格 = merged cells | 表头 = header | Sheet 名 = sheet name | 数据静默不落库 = data silently discarded | 采集端 = platform/collection side | 事件数据 = event data | 公共事件属性 = super property | 用户数据 = user data | 用户ID体系 = ID mapping rule

> `src/xlsx/{read,write}.ts` implementation basis. **Skill does NOT read this document.**

官方模板：`tracking-plan-template/TE官方模板_dataTrackSample.xlsx`（从 AE 后台
`/downloads/zh/dataTrackSample.xlsx` 下载）。所有字段规则以此模板为准，行业模板
（电商/卡牌/社交/阅读）做读取兼容，不做 writer 适配。

---

## 写 xlsx 必须遵守的 3 条硬规则（端到端验证过）

以下任一违反 → `excel-save` 返回 `return_code=0 success`，但**数据静默不落库**：

### 规则 1. 必填列 header 带 `（必填）` 后缀
- `事件名（必填）`、`属性名（必填）`、`属性类型（必填）`
- 没有 `（必填）`，后端会丢弃整张 sheet 的数据

### 规则 2. `#事件数据` 的事件字段列（A-D）跨多行必须**合并单元格**
- 同一事件有多个属性时，A-D 列在 row N 到 row M 之间用 `mergeCells('A{N}:A{M}')` 合并
- 否则后端按行级字符串匹配，报错 `事件名重复`
- 官方模板就是合并单元格，SheetJS 读出来 row2+ 的 event 字段为 `null`（这是合并单元格的副作用）

### 规则 3. 工作簿必须存在 `#用户ID体系` sheet
- 即使只写一行 header 也行（内容可以全空）
- 缺失整张 sheet → 后端丢弃整份方案

---

## Sheet 清单

工作簿的 `#` 前缀 sheet 是数据 sheet，AE 后端只读这几张；其它（`接入必知`、
`数据类型设计原则` 等）是说明文档，**写 xlsx 时不需要生成**。

| Sheet | 含义 | 写 xlsx 策略 |
|---|---|---|
| `#事件数据` | 事件 × 属性展开（见规则 2） | 生成并合并 A-D 列 |
| `#公共事件属性` | 公共属性定义 | 逐行生成 |
| `#用户数据` | 用户属性定义（含更新方式） | 逐行生成 |
| `#用户ID体系` | 系统预置属性说明 | **仅写 header 占位**（见规则 3） |

### `#事件数据` 列定义（A→I）

| 列 | 列名 | 必填 | 对应字段 |
|---|---|---|---|
| A | `事件名（必填）` | ✅ | `eventName` / `Event.event_name` |
| B | `事件显示名` | 否 | `displayName` |
| C | `事件说明` | 否 | `eventDesc` |
| D | `事件标签` | 否 | `eventTag` |
| E | `采集端` | 否 | `platform`（见下） |
| F | `属性名（必填）` | ✅ | 属性 `name`（允许 `父.子`） |
| G | `属性显示名` | 否 | 属性 `displayName` |
| H | `属性类型（必填）` | ✅ | 类型中文值，见类型表 |
| I | `属性说明` | 否 | 属性 `desc` |

**采集端列（E）的值**：
| `platform` 值 | xlsx 写入值 |
|---|---|
| `client` | `client` |
| `server` | `server` |
| `both` | `client,server` |
| `undefined` | （留空） |

**行语义**：一行一对 `(event, property)`。同一事件多属性时，A-E 按事件字段填写，F-I 按属性变化，
A-E 在 writer 里用 `mergeCells` 合并。

**property-less 事件**（罕见）：仍写一行，A-D 填事件字段，E-H 全空。AE 接受，
但不推荐——建议至少给一个有语义的属性（例如 `user_logout` 加 `session_duration_ms`）。

### `#公共事件属性` 列定义（A→D）

| 列 | 列名 | 必填 |
|---|---|---|
| A | `属性名（必填）` | ✅ |
| B | `属性显示名` | 否 |
| C | `属性类型（必填）` | ✅ |
| D | `属性说明` | 否 |

### `#用户数据` 列定义（A→F）

| 列 | 列名 | 必填 |
|---|---|---|
| A | `属性名（必填）` | ✅ |
| B | `属性显示名` | 否 |
| C | `属性类型（必填）` | ✅ |
| D | `更新方式` | 否（默认视为 `user_set`） |
| E | `属性说明` | 否 |
| F | `属性标签` | 否 |

**D 列直接填英文 canonical 值**：`user_set` / `user_setOnce` / `user_add`，不翻译中文。

---

## 类型枚举

### PropType（canonical ↔ 各语言显示值）

> Writer 按 `draft.meta.lang` 输出对应语言列的值。

| canonical（draft.json） | zh | en | ja | ko | 读取额外兼容（alias） |
|---|---|---|---|---|---|
| `string` | `文本` | `String` | `ストリング` | `String` | `字符串` / `string` / `文字列` / `テキスト` / `텍스트` / `문자열` |
| `number` | `数值` | `Number` | `数値` | `Number` | `number` / `숫자` |
| `bool` | `布尔` | `Boolean` | `ブール値` | `Boolean` | `boolean` / `Bool` / `ブール` / `부울` |
| `datetime` | `时间` | `Date` | `時間` | `Date` | `datetime` / `DateTime` / `Time` / `日時` / `날짜시간` / `time` |
| `object` | `对象` | `Row` | `オブジェクト` | `Row` | `object` / `Object` |
| `array_row` | `对象组` | `Array Row` | `オブジェクトグループ` | `Array Row` | `object[]` / `Object Array` / `オブジェクト配列` / `object_array` / `객체 배열` |
| `array_string` | `列表` | `List` | `リスト` | `List` | `string[]` / `String Array` / `配列` / `string_array` / `리스트` |

> 旧值兼容（2026-07-15 前生成的 xlsx）：`en` 旧值 `string`/`number`/`boolean`/`datetime`/`object`/`object[]`/`string[]`，
> `ja` 旧值 `オブジェクト配列`/`配列`，`ko` 旧值 `time`/`object_array`/`string_array` 在 reader 中仍可识别。

### UpdateType（用户属性 `更新方式`）

| canonical | 语义 |
|---|---|
| `user_set` | 覆盖赋值（默认） |
| `user_setOnce` | 仅首次赋值 |
| `user_add` | 数值累加 |

xlsx 里填写英文 canonical 值本身，不翻译。

官方文档提及 `user_append`（字符串数组追加），样本中无实例，暂不实现。

---

## Reader 兼容规则（从 xlsx → Draft）

- `.claude` 之外工作簿里只读 `#` 前缀 sheet
- header 规范化：strip `（必填）` / `(必填)` 后缀，把 `名称` 归一化为 `名`
- `#事件数据` 合并单元格读出来是 null → 用"继承上一行 event_name"策略还原
- 属性列空、类型列空、prose / instruction 行 → skip
- 行业模板额外前置列（`事件模块` / `属性分类`）通过 header 名查找，忽略不识别的列

### 行业模板已知差异（只读取，不写入）

| 模板 | 额外列 | 类型 alias | 其它 |
|---|---|---|---|
| 卡牌游戏 | `事件模块` / `属性分类` | `字符串` | 部分类型列空 |
| 电商 | 部分 header 为空字符串（WPS 生成副作用） | — | 按列位置推断 |
| 社交聊天 | `事件模块` / `属性分类` | `数量` | `更新方式` 含多行注释 |
| 阅读类 | `事件模块` / `属性分类` | `字符串` | 同上 |

写 xlsx 时**不**生成这些行业扩展列，统一输出官方 schema。

---

## 开放问题（记一下，不影响 v1）

1. ~~AE 后端是否区分 `object`（单对象）与 `array_row`（对象数组）~~ —— 已确认：AE 支持，wiki/te-docs/raw/preparations-before-data-ingestion.md 明确区分两种类型
2. `user_append` updateType 是否真的可用 —— 待构造测试
3. 严格错误码 —— 所有校验失败目前都是 `return_code=0 success` + 静默丢弃，无法从响应区分成功/失败；UI 上传才显示错误文案
