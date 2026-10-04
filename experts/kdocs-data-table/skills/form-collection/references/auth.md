# 认证详情与故障排除

> 何时打开：`auth login` 失败需手动获取 Token / 需要诊断认证状态 / 需要退出登录。日常使用无需阅读。

## 诊断与退出

| 操作 | 命令 |
|------|------|
| 查看状态 | `kdocs-cli auth status` |
| 退出登录 | `kdocs-cli auth logout` |

## 浏览器授权流程

`kdocs-cli auth login` 只生成本次 `auth_code` 并打开授权引导页，WPS 登录地址由引导页生成。用户在引导页点击“取消”后，服务端会结束本次授权，CLI 在下一次轮询收到 `409` 后立即退出；如需继续授权，请重新执行 `kdocs-cli auth login`。

## 企业账号受控

本 Skill 及配套的 `kdocs-cli` 仅支持 **WPS 个人账号**。出现以下情况时，按企业账号受控处理：

- 浏览器中登录了 WPS 企业账号，且 `kdocs-cli auth login` 持续等待或最终失败
- 授权或工具调用返回 `403` / 授权被拒绝、`403001` / 企业账户限制

此时立即停止重试，先退出浏览器中的 WPS 企业账号并切换到个人账号，再运行 `kdocs-cli auth login`。不要在同一企业账号登录状态下反复授权。WPS 企业账号用户请使用 [WPS365 CLI](https://github.com/wps365-open/cli)。

## 手动获取 Token（login 失败时的兜底方案）

当 `kdocs-cli auth login` 因环境问题执行失败时，引导用户手动获取：

1. 用户在浏览器访问 https://www.kdocs.cn/latest（需已登录 WPS 个人账号）
2. 点击页面右上角个人头像旁的主菜单 → 选择「金山文档Skill」入口 → 复制 Token
3. 用户将 Token 提供给 Agent
4. Agent 保存到密钥链：`kdocs-cli auth set-token "<TOKEN>"`
