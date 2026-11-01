---
name: kd100-mcp-quickstart
description: 当用户需要查询快递物流轨迹、根据单号识别快递公司、预估快递送达时效或运费时使用本技能。本连接器仅包含快递100官方 MCP 的 5 个查询/预估类工具:query_trace、auto_number、estimate_price、estimate_time、estimate_time_with_logistic,不提供寄件下单能力。查询与预估均可直接调用。
---

# 快递100 MCP 快速使用

## 适用场景

- 用户报一个快递单号,想查最新物流轨迹
- 用户只有一个单号,不知道是哪家快递公司寄的
- 用户想知道从 A 地寄到 B 地大概多久能到 / 大概多少钱(寄件前的查询预估)

## MCP 工具一览(共 5 个)

| 工具名 | 用途 | 必填参数 | 备注 |
|---|---|---|---|
| `query_trace` | 按快递单号查实时物流轨迹 | `kuaidiNum`(快递单号) | `phone` 仅顺丰速运、中通必填,其余运力可不传 |
| `auto_number` | 按快递单号识别可能的快递公司 | `kuaidiNum`(快递单号) | 返回候选公司列表;用于不确定 `com` 编码时先识别再查轨迹 |
| `estimate_price` | 预估某快递公司的运费 | `kuaidicom`、`sendAddr`、`recAddr`、`weight` | 预估报价,与实际下单运费可能不一致 |
| `estimate_time` | 预估快递送达所需时间(寄件前) | `kuaidicom`、`from`、`to` | 可选 `orderTime`、`expType`(业务类型如"标准快递") |
| `estimate_time_with_logistic` | 预估在途快递的到达时间 | `kuaidicom`、`from`、`to`、`orderTime`、`logistic` | 用于在途件;`logistic` 传 `query_trace` 返回的历史轨迹 JSON 数组,`orderTime` 取最早轨迹时间 |

完整参数 schema 随 MCP 服务下发,以工具 describe 返回为准。

## 调用流程

1. **只有单号、不知道哪家快递 → 先 `auto_number` 再 `query_trace`**
   - 调用 `auto_number(kuaidiNum)` 拿候选公司列表,让用户确认或按首位候选,再用 `query_trace` 查轨迹
2. **查询轨迹**
   - 直接调 `query_trace`;顺丰/顺丰快运/中通需向用户索要收寄件人手机号(后 4 位或完整号均可,视接口要求)
3. **寄件前预估**
   - 用户要"从 A 到 B 寄 X kg":先用 `estimate_time` + `estimate_price` 给时效和报价参考
   - 没指定快递公司时,先给常见运力(顺丰/京东/圆通/中通/韵达等)的报价对比,让用户挑
4. **在途件到达预估**
   - 用户已有在途单号时:先 `query_trace` 拿轨迹 → 再调 `estimate_time_with_logistic` 预判到达时间

## 关键参数提示

- `kuaidicom`(快递公司编码,一律小写):`yuantong`(圆通)、`zhongtong`(中通)、`shunfeng`(顺丰)、`shunfengkuaiyun`(顺丰快运)、`jtexpress`(极兔)、`shentong`(申通)、`yunda`(韵达)、`ems`(EMS)、`jd`(京东)、`kuayue`(跨越)、`debangkuaidi`(德邦快递)、`youzhengguonei`(邮政国内)、`emsguoji`(EMS-国际件)、`youzhengguoji`(国际包裹)、`lianbangkuaidi`(联邦快递)等
- `estimate_price` 的地址参数是 `sendAddr`/`recAddr`(如"北京海淀区");`estimate_time` 系列是 `from`/`to`(如"北京市海淀区"),不要混用
- `weight`:默认 kg,不传默认 1kg
- `phone`:顺丰速运、顺丰快运、中通查轨迹必填;用户未提供时先询问,不要猜测

## 认证

- 用户需在 WorkBuddy 连接器市场中点「连接」,填入企业授权 key
- key 路径:快递100企业管理后台 → 「授权参数」
- 凭证仅存于本机 `~/.workbuddy/`,不经过 WorkBuddy 云端
- 401/403 时直接报错原文,提示用户重新连接,不要猜测原因

## 风险与回退

| 风险 | 处理 |
|---|---|
| `estimate_price` 报价 ≠ 实际运费 | 明确告知是预估;部分公司偏远/超重差异可能 >50%,实际以快递公司结算为准 |
| 单号不存在 / 查无轨迹 | 原文反馈错误,不要猜"可能在途中";可先用 `auto_number` 校验单号是否属于该公司 |
| 顺丰/中通缺手机号查不到 | 提示用户补充收寄件人手机号后重试 |
| Key 过期或欠费 | 提示用户到企业管理后台更新 key 或充值 |
| 用户要求在线寄件 | 说明本连接器不含下单能力,引导至快递100开放平台/官方寄件产品 |
