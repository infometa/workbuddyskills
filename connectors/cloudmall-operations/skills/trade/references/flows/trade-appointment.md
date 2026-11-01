# 交易域 — 运营流程：到店预约、退货地址与交易设置

> 到店预约台账处置、预约全局配置、退货地址维护、交易设置与订单/售后备注。
> 概念知识见 `references/domains/trade-concepts.md`，状态与枚举见 `references/domains/trade-enums.md`；执行闭环见 `trade-core.md`。
> 对应契约：`appointment-query.md` / `appointment-action.md`、`return-address-query.md` / `return-address-action.md`、`trade-setting-query.md` / `trade-setting-action.md`、`aftersale-action.md`（售后备注）。
> 全部写操作遵守入口 SKILL.md 的风险档位与确认纪律。

---

## 预约

`ops.trade.appointment.search` 取得唯一 ID、状态与时间。待确认选 confirm/reject，待到访选 confirm-visit/no-show；实际到访和爽约须用户确认，不从当前时间自动推定。写后用原 appointmentNo 检索，移除旧 status 等可能排除新状态的条件，并核对同一 ID；没有预约详情能力，不编造 detail 调用。看板必须提供 `timeDimension`，日历不是单笔处置依据。见 [预约查询契约](../apis/trade/appointment-query.md) 与 [预约写契约](../apis/trade/appointment-action.md)。预约全局配置先 `config.get` 读现值，提交完整目标状态（保存为非 null 字段级合并，未传保留旧值）；提醒未送达核对 `reminder-log.search`（failed 记录）与 `reminder-log.detail`（contentJson 已脱敏）；导出走 `appointment.export`（URL 型）。

## 退货地址

search/list-all 定位、detail 核实后更新；只发送已确认变更，省略或 null 保留旧值，不能用于清空。新建无业务返回；使用 ops.trade.return-address.search 逐页读取，以 name/contactName/province/city/district/detailAddress 核对唯一新增记录（list-all 不返回 name，不能代替此步骤），取得 ID 后查详情；不能唯一定位则停止后续操作。删除前核对不是默认地址，向用户明确无法由当前能力证明无历史引用，确认不用后删除；不声称系统已做引用检查。见 [退货地址查询契约](../apis/trade/return-address-query.md) 与 [退货地址写契约](../apis/trade/return-address-action.md)。

## 交易设置与备注

- 超时配置与交易设置：交易侧超时/赠品仓按 [交易设置查询契约](../apis/trade/trade-setting-query.md) 先读现值再全量提交；配置变更可事后用 operation-log 能力审计。用户要求改售后侧规则时按 `trade-aftersale-config.md` 的售后配置能力走。
- 订单备注覆盖原值；售后 remark.update 覆盖单条备注，remark.add 追加流水。按用户真实意图选择，覆盖前读原值，追加后核对新增记录。
