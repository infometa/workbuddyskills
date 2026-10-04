# 学员详情

使用 `users_detail` 查询一个学员的脱敏详情，参数为 `userId`（学员 `users.userId` 的后台编码 ID）。这个 ID 是学员身份，不是 OAuth 授权的后台管理员 `adminUserId`。

该工具要求 `users:detail` 权限；管理员身份和店铺范围来自 OAuth，不能传 `companyId`、`adminUserId` 或店铺覆盖参数。工具不会刷新微信关注状态，也不会返回 openid、完整手机号、余额和完整自定义资料。
