# 认证与只读访问

需要已由宿主准备好的 CLI；本文件只处理账号授权与实际使用。

1. 执行 `superun-ai auth status`；CONFIGURED 时复用已有凭据。缺凭据时执行 `superun-ai auth login`，由 CLI 调用系统默认浏览器完成登录，等待同一登录流程返回。业务命令已自动启动登录时，继续等待原命令，不另开一次 `auth login`。登录链接不是业务预览：不得用 WorkBuddy 内置浏览器、WebView、`present_files` 或其他宿主页面工具打开，也不从内置浏览器提取 Token/PAT。PAT 导入使用用户终端隐藏输入或安全 stdin，不索取聊天明文。随后用 `superun-ai session list --limit 1` 验证只读访问，空列表正常；不创建测试项目。
2. 认证成功后自动恢复原 sessionId、interactionId 和任务目标；已有项目不重新 create。认证或依赖仍缺失时保持原任务，明确需要用户处理的具体事项。

CLI 未能自动打开浏览器时，可在当前允许的本机 Shell 中用系统默认浏览器命令打开 CLI 返回的原始登录 URL：macOS 使用 `open`，Windows 使用 `rundll32 url.dll,FileProtocolHandler`，Linux 使用 `xdg-open`。URL 通过参数数组或安全引用传递，保留原 uuid，不修改系统默认浏览器设置、不重新生成登录链接。当前环境无法拉起本机浏览器时，提示用户复制同一链接到自己的默认浏览器，保留原登录命令等待回执；不能改用宿主内置浏览器，也不能声称已经打开。
