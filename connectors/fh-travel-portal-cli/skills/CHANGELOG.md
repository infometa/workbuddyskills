# 更新日志

## 1.0.2

首次发布。国内、国际机票查询，登录后出页面，并跳转飞鹤商旅完成预订。
登录由脚本打开系统默认浏览器。Windows：`cmd /d /s /c` + `windowsVerbatimArguments` 打开默认浏览器，spawn 失败再 rundll32；loopback 回调 `Connection: close` 并 await 关闭；正常路径不打印完整授权 URL。技能要求不要把授权地址发到对话；登录结束后先 auth-status，有 token 不要因非 0 退出码重复登录。
