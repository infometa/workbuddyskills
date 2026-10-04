---
name: ckjr-users
description: 查询已授权创匠店铺的学员列表，按手机号、学员 ID、日期和会员条件筛选。
---

使用 `users_list` 查询当前授权店铺的学员。OAuth 登录和店铺选择确定后台管理员 `adminUserId`；工具参数 `userId` 是后台显示的学员编码 ID。

默认 `page=1`、`limit=10`，每页最多 100。只根据用户要求查询相应页面，不能自动遍历所有页或承诺整店导出。

按用户提供的条件选择以下参数，直接放在 `users_list` 的参数对象中，不添加 `filters` 包装层；未指定的筛选条件省略。

| 筛选条件 | 参数名 | 传值说明 |
| --- | --- | --- |
| 学员手机号 | `mobile` | 字符串 |
| 学员编码 ID | `userId` | 字符串，使用后台显示的学员编码 ID |
| 学员真实姓名 | `userRealName` | 字符串 |
| 学员昵称 | `userNickname` | 字符串 |
| 推荐人手机号 | `reMobile` | 字符串 |
| 推荐人编码 ID | `reId` | 字符串，使用推荐人的学员编码 ID |
| 推荐人真实姓名 | `reUserRealName` | 字符串 |
| 推荐人昵称 | `reUserNickname` | 字符串 |
| 微信号 | `fromWeChat` | 字符串；新调用使用此拼写 |
| 会员子类型 | `subType` | 字符串，使用当前店铺的会员子类型值 |
| 账号状态 | `loginType` | 整数：`0` 全部、`1` 待注册、`2` 正常（已登录过） |
| 是否绑定企业微信 | `isBindWecom` | 整数：`1` 是、`0` 否；不限时省略 |
| 开始日期 / 结束日期 | `regist_time` / `end_time` | `YYYY-MM-DD` 字符串，默认按注册时间筛选 |
| 日期类型 | `timeType` | 整数，沿用后台日期类型；`1` 注册时间、`2` 成为 VIP 时间 |
| VIP 开始日期 / 结束日期（兼容参数） | `becomeVip_time` / `becomeVip_end_time` | `YYYY-MM-DD` 字符串，不能与 `regist_time` / `end_time` 混用；`timeType` 只能省略或为 `2` |

例如，按学员真实姓名查询第一页时调用 `users_list`，参数为：

```json
{"userRealName":"张三","page":1,"limit":10}
```

姓名和昵称使用各自的字段，不要把同一个搜索词同时填入姓名和昵称字段，否则会缩小匹配范围。

微信号旧参数 `formWeChat` 仍兼容。新调用只传 `fromWeChat`；若两者同时传入，非空值必须相同，否则返回 `invalid_parameters`。空字符串视为未指定筛选条件。

不要传入 `total`、`companyId`、`adminUserId`、`chainStoreId`、`isAll` 或上游地址。`storeId` 只能缩小授权范围，门店账号不能指定其他门店。切换店铺需要重新授权。

成功必须同时满足 `ok=true`、HTTP 成功和上游 `business_code=200`。`data` 保留上游完整信封，因此学员页在 `data.data.users.data`、总数在 `data.data.total`；`pagination` 同时提供分页元数据。金额为十进制字符串。汇报范围和本页条数，不能将一页描述为全量结果。

工具失败时说明受控错误码和 `trace_id`，授权失效需重新连接；不要反复重试或索要用户的密码、Token。保留上游脱敏结果，避免在回答中不必要地展示完整个人资料。
