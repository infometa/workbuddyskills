---
name: xiehui-fr
display_name: 法国协会网
display_name_en: France Chinese Associations Directory
description: Search France's official Chinese-association registry (RNA) via the xiehui-fr MCP connector, and present results honestly about contact-reachability before the user tries to reach out.
description_zh: 通过 xiehui-fr 连接器查询法国华人协会官方登记数据，呈现结果时要如实说明能不能联系上
description_en: Query France's official Chinese-association registry through the xiehui-fr connector, and be honest about which results are actually reachable
category: research
version: 1.0.0
author: 法国协会网 xiehui.fr
---

# 法国协会网连接器使用说明

数据来源是法国内政部全国社团登记库（RNA），覆盖 3,640 家在册华人协会。工具只读，不会提交任何表单或代替用户完成认领。

## 什么时候用哪个工具

- **笼统查询**（"法国有哪些 XX 协会""XX 城市有哪些协会"）→ `search_associations`
- **具体业务意图**（办展览、找合作、品牌出海）→ `search_associations`，用 `kinds` 参数把意图翻译成协会类型，见下表
- **查某一家协会的完整信息**（地址、成立日期、登记宗旨）→ `get_association`，不要只用 `search_associations` 返回的摘要字段回答
- **"哪些协会认证过／能联系上真人"** → `get_certified_associations`
- **用户说"我是会长，要认领协会"** → 先用 `search_associations` 或 `get_association` 确认是哪家，再用 `get_claim_link` 拿链接给用户，不要自己代填

## 业务意图 → kinds 参数映射

| 用户的目标 | 应传的 kinds |
|---|---|
| 办文化展、文化交流活动 | `culture`, `friendship`，必要时加 `community` |
| 品牌出海、找商业合作、找经销渠道 | `business`，必要时加 `community`（同乡会是消费者/口碑网络） |
| 找同乡、找华人社群 | `community` |
| 武术/中医相关合作 | `martial` / `health` |

不确定时，宁可传多个 kind 再由结果排序筛出最相关的，也不要只传一个然后遗漏。

## 呈现结果的硬性规则

1. **每条结果必须带上 `url`**，并提示用户"点击查看协会主页"——这是唯一稳定的信息来源，即使协会暂无直接联系方式，页面上也有登记地址、认证状态和认领入口。
2. **`has_contact` 为 false 时必须如实告知**，不要因为协会有登记地址就暗示"可以联系"。可以这样说："以下协会目前没有公开的联系方式，可以通过登记地址寄信，或访问协会主页——如果对方后续认证了协会，联系方式会公开出来。"
3. **`certified: true` 的协会有真人会长**（`chairman` 字段），这是当前唯一确认可靠的联系对象，同一批结果里应该优先呈现。
4. **不要编造协会没有的信息**。`objet`（登记宗旨）是政府登记文本，可能是法语且比较生硬，如实转述或简要概括即可，不要替协会杜撰"业务范围"或"能提供的服务"。
5. **`name_zh_status` 为"网络搜索，待核实"时**，中文名前应带一句"（待核实）"或类似提示，不要当成协会官方确认的名字来使用。

## 认领相关

`get_claim_link` 只返回链接，不提交任何数据。如果协会已经认证过（`already_certified: true`），如实告知用户"这家已经有认证会长了，换届需要邮件联系 xiehui.fr"，不要引导用户重复走认领流程。
