# 登录与组织

1. 用 `gd-cli auth status` 检查登录状态；需要机器读取时使用 `--json`。
2. 未登录时执行 `gd-cli auth login`，按终端提示在浏览器完成授权；无法自动打开浏览器时使用 `--no-browser`。
3. 用 `gd-cli org list` 查看当前账号可用的组织，用 `gd-cli org current` 查看当前选择。
4. 让用户从真实列表中选择，再执行 `gd-cli org switch --org <org-id>`；不要猜组织 ID。
5. 用户要求退出或登录状态失效时执行 `gd-cli auth logout`；状态失效后重新登录。

不要向用户索要或回显 Bearer Token、Cookie、AK、SK 或签名。组织不可用时先切换组织；仍无法恢复时退出后重新登录。
