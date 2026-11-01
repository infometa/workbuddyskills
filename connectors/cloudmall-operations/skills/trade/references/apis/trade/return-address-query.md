# 交易域 — 退货地址查询契约

> 概念知识：`references/domains/trade-concepts.md`；创建/编辑/删除写操作见 `return-address-action.md`；运营流程：`references/flows/trade-appointment.md`
> 所有 ID 均为十进制字符串。退货地址用于售后审核时指定退回地址；**列表接口对联系电话脱敏，详情接口返回原始值用于编辑回填**——不能把脱敏值回写。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引（前缀 `ops.trade.`）：查询 return-address.search · return-address.detail · return-address.list-all

---

## ✅ 退货地址分页 — ops.trade.return-address.search

用途：分页浏览退货地址摘要。只接受分页字段；前端类型中的开放映射只是预留，不能传名称、地区或任意自定义筛选键。

| 字段 | 类型 | 必填、默认与约束 | 业务含义 / 来源 |
|---|---|---|---|
| pageNum | integer | 可选，默认 1，最小 1 | 页码 |
| pageSize | integer | 可选，默认 20，1～100 | 每页条数 |

`ReturnAddressVO` 记录含 `id/name/contactName/contactPhone/province/city/district/detailAddress/addressType/isDefault`；`contactPhone` 已脱敏，不能用于更新；列表没有行政区编码，编辑地区需读详情。`addressType` 由创建实现固定为 `RETURN`。来源：`ReturnAddressPageQuery`、`ReturnAddressServiceImpl.page`、`ReturnAddressConvert.toVO`；运营类型的开放映射仅预留，无额外筛选字段。

```json
{
  "capability": "ops.trade.return-address.search",
  "input": {
    "pageNum": 1,
    "pageSize": 20
  },
  "summary": "查询退货地址"
}
```

---

## ✅ 退货地址详情 — ops.trade.return-address.detail

用途：读取一个地址的完整行政区划和联系人资料，用于编辑前回填。仅输入十进制字符串 `id`；结果包含敏感联系方式，不得向用户复述。

| 字段 | 类型 | 必填、默认与约束 | 业务含义 / 来源 |
|---|---|---|---|
| id | string | 必填，十进制字符串 | 地址检索/详情中的 id |

`ReturnAddressDetailVO` 提供列表字段及 `provinceCode/cityCode/districtCode`；`contactPhone` 为原始完整值，只用于经确认的编辑核验，不主动向用户复述。所有 ID 保持文本。不存在时报错。来源：`ReturnAddressServiceImpl.detail`、`ReturnAddressConvert.toDetailVO`。

```json
{
  "capability": "ops.trade.return-address.detail",
  "input": {
    "id": "7000000000000000001"
  },
  "summary": "查询退货地址详情"
}
```

---

## ✅ 退货地址全量 — ops.trade.return-address.list-all

用途：取得可供售后审核选择的退货地址集合。无输入；只用于从真实地址中选择 `returnAddressId`，不能创建地址。

| 字段 | 类型 | 必填、默认与约束 | 业务含义 / 来源 |
|---|---|---|---|
| 无 | — | input 使用空对象 | 不接受附加筛选 |

`ReturnAddressListAllVO[]` 每项 `id/contactName/contactPhone/fullAddress/isDefault`，没有 `name` 与行政区编码；`fullAddress` 是省市区与详细地址的拼接，手机号脱敏。将选中项 `id` 作为售后审核的 `returnAddressId`，不从拼接文本反推各级编码。来源：`ReturnAddressConvert.toListAllVO/buildFullAddress`，运营售后审核选择器类型。

```json
{
  "capability": "ops.trade.return-address.list-all",
  "input": {},
  "summary": "查询全部退货地址"
}
```
