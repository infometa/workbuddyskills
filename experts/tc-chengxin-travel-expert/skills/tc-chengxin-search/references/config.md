# 同程专家运行配置

本专家自带查询脚本和授权 CLI，不依赖连接器；缺少授权组件时重新安装完整专家包，不要求用户进入「连应用」或提供 API Key。

授权统一使用 `tc-chengxin-auth`。桌面只执行一次 `--start`，脚本尝试打开浏览器并限时轮询；用户无需回复“已登录”，不调用 `--poll`。手机/小程序/无头云端或打开失败时，把登录链接放入最终回复并结束本轮；用户回复后只用 `--check` 一次。凭证只保存在当前执行环境。

查询统一使用 `tc-chengxin-analysis` 包装器；它自动注入 Token、`callerChannel=workbuddy` 和 `channel=workbuddy`。`surface` 由共享客户端识别决定，手机为 `mobile`、明确 PC 为 `desktop`；无明确客户端标识的云端/无头环境采用移动兼容输出，不代表已确认用户使用手机。不要手动覆盖这些参数。

优先读取 WorkBuddy 提供的 `WORKBUDDY_CLIENT_TYPE`，结合实际操作系统和 Linux 图形会话判断执行环境；不能为了打开侧边栏而伪造客户端标识。明确 PC 且脚本运行在 macOS、Windows 或有图形会话的 Linux 时可唤起本机浏览器；真正无头的云端 Linux 只展示登录链接。

网关使用专家内置 CLI 的生产配置 `https://wx.17u.cn/skills/gateway`。不在用户工作区临时切换网关。

默认输出到当前工作区 `outputs`。如宿主指定 `CHENGXIN_WORKBUDDY_OUTPUT_DIR`，使用该真实工作区路径；Windows 使用原生路径，不使用字面量 `$PWD`。

环境允许文件预览时按分析 Skill 的清单交付；文件工具不可用时如实说明，不公开上传或改写 HTML。聊天交付精选MD。
