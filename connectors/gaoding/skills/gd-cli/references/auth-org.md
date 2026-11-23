# 登录与组织

1. 用 `gd-cli auth status` 检查登录状态；需要机器读取时使用 `--json`。
2. 千问办公桌面入口使用 `gd-cli auth init` 自动打开浏览器；打开失败按错误说明处理，不使用手动链接模式。普通 CLI 未登录时执行 `gd-cli auth login`，按终端提示在浏览器完成授权；无法自动打开浏览器时使用 `--no-browser`。
3. 用 `gd-cli org list` 查看当前账号可用的组织，用 `gd-cli org current` 查看当前选择。
4. 让用户从真实列表中选择，再执行 `gd-cli org switch --org <org-id>`；不要猜组织 ID。
5. 用户要求退出或登录状态失效时执行 `gd-cli auth logout`；状态失效后重新登录。

在千问办公桌面连接器中，使用平台入口 `gd-cli auth show --status` 检查 `status`；`unauthorized` 时执行 `gd-cli auth init`，请用户在自动打开的浏览器中完成授权，等待命令结束并检查为 `authorized` 后执行业务。账号展示用 `gd-cli identity whoami`。连接器沿用 CLI 的共享本地身份，凭证到期重新登录；显式 logout 会影响同一系统用户的其他入口，禁用或卸载套件不会自动退出。

不要向用户索要或回显 Bearer Token、Cookie、AK、SK 或签名，也不要读取本地凭证文件。组织不可用时先切换组织；仍无法恢复时退出后重新登录。
