---
name: zxygj-business-query
display_name: 装修云管家业务查询
display_name_en: ZXYGJ Business Query
description: 查询装修云管家中的客户、订单和其他业务对象；当用户提出业务数据查询、记录检索或对象字段问题时使用。
description_zh: 查询装修云管家中的客户、订单和其他业务对象。
description_en: Query customers, orders, and other business objects in ZXYGJ.
allowed-tools: get_current_user, list_business_objects, identify_business_object, get_object_describe, query_records_by_fields, get_record_by_id
version: 1.0.0
author: 装修云管家
---

# 装修云管家业务查询

本连接器只提供只读查询。所有结果都受当前登录账号的企业、数据范围和字段权限约束。

## 工具

- `get_current_user`：返回当前授权企业、用户和权限范围。身份可能影响结果，或用户询问当前连接账号时调用。
- `list_business_objects`：列出当前企业可查询的业务对象。用户不知道准确对象名称，或识别无结果时调用。
- `identify_business_object`：根据中文名称、API 名称或自然语言句子识别业务对象。可以传入 `objectApiNames` 限制候选范围。
- `get_object_describe`：读取对象的真实字段 API 名、类型、选项和可用操作符。构造字段查询前必须调用。
- `query_records_by_fields`：按字段条件分页查询记录，可选择返回字段、获取总数和设置一个排序字段。
- `get_record_by_id`：已知业务对象 API 名和记录 ID 时读取单条记录。

## 标准查询流程

1. 使用 `identify_business_object` 识别用户所说的业务对象。只有需要浏览全部对象时才先调用 `list_business_objects`。
2. 检查 `resolutionStatus`：
   - `RESOLVED`：使用返回的 `apiName` 继续。
   - `AMBIGUOUS`：向用户展示少量候选并请用户选择，不得自行猜测。
   - `NO_MATCH`：调用 `list_business_objects` 获取可用对象，再根据实际列表帮助用户澄清。
   - `UNAVAILABLE`：说明识别服务暂不可用，建议稍后重试或让用户提供准确对象名称。
3. 调用 `get_object_describe` 获取真实字段、字段类型、选项和操作符。
4. 仅使用描述结果中存在的字段 API 名与操作符构造 `query_records_by_fields` 参数。
5. 汇总返回结果时说明查询条件和分页范围；不要声称已读取未返回的记录。

## 参数规则

- `companyid` 通常省略。只有用户明确指定企业时才传入，并且必须与当前授权企业一致。
- `pageno` 从 1 开始，默认 1。
- `size` 默认 10，最大 50。需要更多结果时分页调用，不得把单页大小设为 50 以上。
- `selectFields` 只能包含 `get_object_describe` 返回的字段 API 名。
- `filters[].fieldName` 和 `orders[].fieldName` 必须来自对象描述。
- `filters[].operator` 必须是对应字段支持的操作符，例如 `eq`、`ne`、`like`、`in`、`gt`、`gte`、`lt`、`lte`、`between` 或 `empty`；以工具实际返回为准。
- 当前最多设置一个排序条件。
- 已知记录 ID 时优先使用 `get_record_by_id`，无需先执行列表查询。

## 安全与错误恢复

- 本连接器没有新增、修改或删除工具，不要暗示已经改变业务数据。
- 不得猜测对象 API 名、字段 API 名、枚举值或记录 ID。
- 不得通过切换或伪造 `companyid` 尝试访问其他企业。
- 如果返回未授权、Token 失效或登录过期，提示用户在 WorkBuddy 中重新连接“装修云管家”，然后重试。
- 如果参数无效，重新读取对象描述并按实际字段与操作符修正；不要反复提交相同错误参数。
- 如果后端暂时不可用，保留用户原始查询条件并建议稍后重试。

## 示例

用户说“查询本月金额超过十万元的订单”时：

1. 调用 `identify_business_object`，`query` 使用用户原句。
2. 对象唯一收敛后，调用 `get_object_describe`。
3. 从描述中找到日期字段和金额字段的真实 API 名，并确认它们支持所需操作符。
4. 调用 `query_records_by_fields`，传入本月日期范围、金额大于 100000、所需展示字段，以及用户要求的排序。
5. 用业务可读名称汇总结果，并说明当前页和匹配总数（若请求了 `needCount`）。
