# 进程退出码

本页是跨命令复用的进程退出码参考。错误输出统一为 envelope，`kind` 表示错误类别，进程退出码表示脚本应采取的动作；具体后端业务码仍以响应中的 `code` 为准。处理具体失败时读取 `error.kind`、`error.message` 和 `error.raw`，参数语义查对应的 `commands/*.md`；编写 shell 分支时再看 [管道错误处理](pipes/error-handling.md)。

| 退出码 | 含义 | 处理 |
|---:|---|---|
| 0 | 成功 | 继续 |
| 1 | 一般失败 | 检查 stderr |
| 2 | 参数错误 | 修正命令 |
| 3 | 鉴权失败 | 执行 `reelmate login`，检查账号或令牌 |
| 4 | 任务失败 | 查看任务详情；仅 `retryable=true` 时重试 |
| 5 | 任务取消 | 确认取消原因后重新提交 |
| 6 | 等待超时 | 增大 `--timeout` 或继续用 `task get` 查询 |
| 7 | 积分不足 | 查询 `credits balance`；充值入口用 `deeplink pricing`（剧厂首页，按当前环境解析域名，不要手拼 URL）；Agent 对用户可见文案见 [_hard-gate.md](workflow/_hard-gate.md)「余额不足（用户可见）」；补充额度后由 Agent 续跑，勿默认贴 shell |
| 8 | 内容审核未通过 | 根据审核原因更换或修正素材，不要自动重试 |
| 9 | 画布版本冲突 | 先 `canvas get` 读取最新版本，再重新组织写操作 |
| 10 | 节点锁竞争 | 等待协作者释放锁，或稍后重试 |

未知错误和输出失败使用退出码 `1`。收到 Ctrl-C 时任务按“取消”处理，退出码为 `5`。

`error.kind=permission` 属于退出码 `1`，不是 `3`。处理方式见 [_hard-gate.md](workflow/_hard-gate.md) 的「权限拒绝」：把 `error.message` 原样写入用户可见回复后停止，不要当成未登录去执行 `login`。

当 `retryable=false` 时不要自动重试；写操作即使网络超时也不要盲目重放，先用 `get` 或任务查询确认服务端状态。日志和 JSON 中不得出现 access token、cookie 或密码。
