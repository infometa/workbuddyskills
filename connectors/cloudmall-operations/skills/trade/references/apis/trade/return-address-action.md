# 交易域 — 退货地址写操作契约

> 概念知识：`references/domains/trade-concepts.md`；运营流程：`references/flows/trade-appointment.md`
> **先读现值**：编辑前用 `return-address-query.md` 的 detail 读原值（原始手机号/行政区编码）；删除前核对不是默认地址。更新为局部合并语义：省略或 null 保留旧值，空字符串会覆盖。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读。
> 能力索引（前缀 `ops.trade.`）：写 return-address.create 🟡 · return-address.update 🟡 · return-address.delete 🔴

---

## ✅ 创建退货地址 — ops.trade.return-address.create

用途：建立可供售后审核选择的退货地址（🟡）。`name`、`contactName`、`contactPhone`、`provinceCode`、`province`、`cityCode`、`city`、`detailAddress` 均为必填；姓名上限分别为 30/50 字符，详细地址最多 200 字符，手机号严格为大陆手机号格式；港澳两级行政区的 `districtCode` 与 `district` 可为空字符串。完整地址和联系人必须用户给出，不回填脱敏手机号。

| 字段 | 类型 | 必填、默认与约束 | 业务含义 / 来源 |
|---|---|---|---|
| name | string | 必填；非空白，最多 30 字符 | 仓库/地址名称 |
| contactName | string | 必填；非空白，最多 50 字符 | 收货联系人 |
| contactPhone | string | 必填；^1[3-9]\d{9}$ | 完整大陆手机号，禁止传脱敏值 |
| provinceCode | string | 必填；非空白 | 省行政区编码 |
| province | string | 必填；非空白 | 省名称，与编码对应 |
| cityCode | string | 必填；非空白 | 市行政区编码 |
| city | string | 必填；非空白 | 市名称，与编码对应 |
| districtCode | string | 可选，港澳可为空字符串 | 区县编码 |
| district | string | 可选，港澳可为空字符串 | 区县名称 |
| detailAddress | string | 必填；非空白，最多 200 字符 | 道路门牌等详细地址 |
| isDefault | boolean | 可选，创建默认 false | true 会清除其他地址默认标记 |

所有联系人与地址内容来自用户；确认是否设为默认。创建返回无业务数据/无新 ID；执行后分页检索并用名称、联系人及地区逐项匹配，必要时读详情，唯一定位后才交给售后审核。不得假设同名地址唯一；失败或超时先检索防重复创建。来源：`CreateReturnAddressRequest`、`ReturnAddressServiceImpl.create`、前端 `CreateReturnAddressRequest`。

```json
{
  "capability": "ops.trade.return-address.create",
  "input": {
  "name": "杭州售后仓",
  "contactName": "售后仓",
    "contactPhone": "13800138000",
  "provinceCode": "330000",
  "province": "浙江省",
  "cityCode": "330100",
  "city": "杭州市",
  "districtCode": "330106",
  "district": "西湖区",
  "detailAddress": "文三路 100 号",
    "isDefault": true
  },
  "summary": "创建退货地址"
}
```

---

## ✅ 编辑退货地址 — ops.trade.return-address.update

用途：变更已存在的退货地址（🟡）。更新实现逐字段合并非 null 值，省略字段保留旧值；先读详情并提交明确变更。`contactPhone` 如传入必须符合大陆手机号格式，禁止传脱敏值。

| 字段 | 类型 | 必填、默认与约束 | 业务含义 / 来源 |
|---|---|---|---|
| id | string | 必填，十进制字符串 | 地址检索/详情中的 id |
| name | string | 可选；最多 30 字符 | 仓库/地址名称 |
| contactName | string | 可选；最多 50 字符 | 收货联系人 |
| contactPhone | string | 可选；^1[3-9]\d{9}$ | 完整大陆手机号，禁止传脱敏值 |
| provinceCode | string | 可选；无额外格式校验 | 省行政区编码 |
| province | string | 可选；无额外格式校验 | 省名称，与编码对应 |
| cityCode | string | 可选；无额外格式校验 | 市行政区编码 |
| city | string | 可选；无额外格式校验 | 市名称，与编码对应 |
| districtCode | string | 可选；港澳可为空字符串 | 区县编码 |
| district | string | 可选；港澳可为空字符串 | 区县名称 |
| detailAddress | string | 可选；最多 200 字符 | 道路门牌等详细地址 |
| isDefault | boolean | 可选；省略保留现值 | true 会清除其他地址默认标记 |

**局部更新真实受支持**：`ReturnAddressConvert.mergeToEntity` 对每个字段仅在非 null 时合并，所以省略或 null 保留旧值；空字符串不是 null，可能覆盖原文本，Agent 不用空串清空姓名、联系人、省市和详细地址。只发送已确认变更，省略或 null 保留旧值，不能用于清空。变更行政区时名称与编码成对更新；港澳区县可按真实资料传空字符串。`isDefault=true` 会撤销其他默认；false 仅取消当前默认，不自动补选新默认。返回无业务数据，回读同一 id 比较变更字段；超时先回读。前端编辑表单定义了完整对象，但不改变 Java 的局部合并语义。来源：`UpdateReturnAddressRequest`、`ReturnAddressConvert.mergeToEntity`、`ReturnAddressServiceImpl.update`。

```json
{
  "capability": "ops.trade.return-address.update",
  "input": {
    "id": "7000000000000000001",
    "name": "杭州售后仓",
    "contactName": "售后仓",
    "contactPhone": "13800138000",
    "provinceCode": "330000",
    "province": "浙江省",
    "cityCode": "330100",
    "city": "杭州市",
    "districtCode": "330106",
    "district": "西湖区",
  "detailAddress": "文三路 101 号",
    "isDefault": true
  },
  "summary": "编辑退货地址"
}
```

---

## ✅ 删除退货地址 — ops.trade.return-address.delete

用途：移除不再使用的非默认退货地址（🔴）。仅输入 `id`；先读取并向用户确认地址名称及停用影响，当前未开放恢复能力。

| 字段 | 类型 | 必填、默认与约束 | 业务含义 / 来源 |
|---|---|---|---|
| id | string | 必填，十进制字符串 | 地址检索/详情中的 id |

先读详情确认名称、地址及 `isDefault=false`；默认地址在运行时禁止删除，需要先明确指定其他默认地址。实现未查询售后引用，不能声称系统已证明没有在用售后；用户需明确确认停用业务影响。返回无业务数据；回读同一 id 返回不存在，或在完整列表中确认移除后，才报告地址已删除。当前能力不提供恢复操作，不能承诺不可恢复的存储语义。删除检查默认地址，不等于证明没有售后引用。来源：`ReturnAddressServiceImpl.delete` 的默认检查与删除实现。

```json
{
  "capability": "ops.trade.return-address.delete",
  "input": {
    "id": "7000000000000000001"
  },
  "summary": "删除退货地址"
}
```
