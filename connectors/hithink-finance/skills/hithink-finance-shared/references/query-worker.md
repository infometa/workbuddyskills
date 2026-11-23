# 本地查询 worker

现有远端命令默认透明复用当前系统用户、构建和环境的本地worker。首次按需启动，后续命令复用模块与HTTP连接，空闲约120秒退出；每条请求重新读取配置和凭据。帮助、认证、维护和数据库命令在前台；market history显式--source remote可复用。

```bash
hithink-finance worker status --format json
hithink-finance worker stop --format json
```

status只读、不启动worker、不联网。state=running表示可连接；absent表示没有当前兼容实例；starting/unreachable/unavailable的running=null表示尚未确认；stopping等待现有任务完成。stop作用于当前兼容实例。进程环境HITHINK_FINANCE_NO_WORKER=1使用普通路径。

CA/OpenSSL等相对进程路径按调用目录解析；自定义Node加载器等目录敏感配置按目录隔离。依赖声明与shrinkwrap参与构建标识；修改依赖后运行npm run build，使旧worker与新构建隔离。

启动/握手失败且任务未发送时使用普通路径。发送后断线返回WORKER_RESULT_UNKNOWN，不自动重放，应检查输出文件后明确重试。WORKER_BUSY表示队列满或正在停止。请求期限包含排队，Ctrl+C取消当前任务。CLI_BUILD_NOT_READY表示本地构建未完成，应先成功运行npm run build。
