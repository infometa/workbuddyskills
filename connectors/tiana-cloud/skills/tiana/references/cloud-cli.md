# CLI 命令与恢复

以下 JSON 管理输出需使用配套修复后的 CLI 发行版，执行前查看对应 `--help` 确认 `--json`。当前版本缺少参数时报告需要升级，不把表格解析伪装成稳定 JSON。

```sh
tiana status --json
tiana sqlite list --json
tiana sqlite show INSTANCE --json
tiana sqlite create NAME --wait
tiana git list --json
tiana git show INSTANCE --json
tiana git create NAME --wait
tiana sqlite shell INSTANCE -f schema.sql --format json
```

`sqlite/git list --json` 自动取完全部匹配页，返回完整的 `data.items`；空集合为数组，分页失败不报告部分列表成功。

创建默认只返回异步受理回执；`--wait` 等待已绑定的原始任务和实例状态。记录完整实例 ID、Job ID、Operation ID。管理 JSON 使用 `status/data/error` 信封，默认变更返回 `accepted`，等待已确认完成返回 `succeeded`；`unknown` 不等于失败，保留目标和操作身份，只查询而不盲目重发。新列表/详情的任务 ID、配额和时间值保留十进制字符串精度。不要从实例名称推断另一条创建请求的身份。

如果创建请求中断且仍有待完成记录，保持产品、名称和原始参数重试，CLI 复用请求 ID。若之前已成功返回，再次执行 create 是新请求。遇到未解决的其他待完成操作，应先调查原操作，不删除本地记录来强行创建。

删除使用 `sqlite/git delete INSTANCE`；默认需要终端确认。仅在用户已授权相应删除时使用 `--force`。`--wait` 等待删除操作成功，不等于物理存储已经回收完毕。

SQLite 分支操作使用 [SQLite 分支](../../tiana-sqlite/references/branches-cli.md)。`branch list --json` 自动取完所有匹配页，返回 `data.items`；`--after` 仅指定起始游标，`--search` 在所有页保持一致。创建和删除默认只报告受理。分支创建没有本地待完成请求恢复机制，不能套用上面的实例创建重试规则；结果未知时先核实，保留原 Operation ID。分支查询和连接用 `sqlite show/shell INSTANCE --branch NAME`，省略时选择默认分支（固定 ID `main`）。

应用列表使用 `tiana web list`；脚本可用 `tiana web list --json` 取得全部分页的 `data.items`，保存真实 `id`。列表只包含当前账号拥有的应用；名称可以重复，不能仅凭同名断定是原应用。

Serverless Web 候选命令为 `web create NAME [-m DESCRIPTION] [--entry ENTRY] [--database-instance-id DB_ID] [--git-instance-id GIT_ID] --json`、`web publish ID --dir DIST --json`、`web status ID [--publish-id PUBLISH_ID] --json`。执行前核验配套 CLI/平台版本，尚未发布的候选不能视为线上能力。MGR 生成 `data.id` 与绑定的 Web 实例，保存真实 ID；创建结果未知时沿用本地待完成记录与相同参数恢复。Web 与 SQLite/Git 统一使用实例额度，没有单独 app 配额。

发布经 Gateway 业务管控 channel，接受有效且作用域覆盖目标的 Endpoint、Instance、Group、Tenant Token。CLI 优先使用互斥的 TIANA_TOKEN / TIANA_TOKEN_FILE，否则使用已登录账号 access token；不读取实例 Token 缓存，显式凭据拒绝时不回退。MGR 项目元数据仍通过登录账号读取。CLI 内部将目录打包为含空 `web.yaml` 和 `data/` 的单个 `.tweb`；普通文件可以发布，Site 包装使用 MGR 项目参数；不生成或读取旧清单。发布回执确认 S3 上传，不等待激活；记录 publish_id 和 SHA256，随后查询激活状态。结果未知时只查询、不自动重放 PUT；404 回执消失表示未知，检查 current 内容。没有 --version、upload 或 reload 命令，详细边界见[应用要求](../../tiana-web/references/csr-apps.md)。

登录 JSON 的 `pending_auth:true` 表示待批准；`NO_PENDING_AUTH` / `pending_auth:false` 仅表示无待恢复授权。缺少 `logged_in` 或 `pending_auth` 时该状态未核实，不能推断已退出或丢失授权。用 `status --json` 核实当前账号；配额不可用时仍可能返回已核实的 `logged_in:true`。目录失败按 `LOCAL_STATE_UNAVAILABLE` 修复 XDG 路径/权限，锁占用先等待，过期才重新 start，拒绝不自动再次授权。

本地配置根目录为 `$XDG_CONFIG_HOME/tiana`，未设置时为 `~/.config/tiana`；凭据、登录 pending、命令 pending、发布回执及更新检查状态共用该根目录。`LEGACY_PENDING_COMMAND` 表示旧平台目录仍有未完成命令：停止旧 CLI 进程，保留原参数、账号和请求身份，将错误中的旧路径设置为 `TIANA_PENDING_COMMAND_FILE`，在每个恢复调用中传递并执行原命令。不要另发创建或删除本地记录；恢复完成后取消该覆盖，使用新默认目录。旧发布回执保留在原目录，不自动迁移或删除。

登录使用 `login --start --no-open --json` 和 `login --resume --json`，详见[开始使用](getting-started.md)。退出登录使用 `tiana logout`，会清理当前 origin 的账号凭据和未完成登录，不删除旧实例凭据文件。

SQL 写入中断、输出丢失或响应未知时，先用只读查询确认，不自动重放。账号、配额、网络、证书或资源状态错误均不通过创建新数据库解决。

Web 删除使用 `tiana web delete WEB_ID`，默认需要终端确认。仅在用户明确授权删除该应用后使用 `--force`；推荐核对 `web list --json` 的实际 ID，不依赖可能重名的名称。删除涵盖 Web 实例与当前归档，关联的 SQLite、Git 保留。

`--wait --json` 等待源站清理完成；不加 `--wait` 只表示删除已受理。空应用、上传中和已发布的应用均可删除；本地仍有未完成的 CLI 创建操作时，先按原请求恢复该操作。已接受的删除由 Control 的实例生命周期清理固定 S3 对象，MGR 只跟踪确认状态；公开缓存副本按缓存策略失效。中断不取消服务端删除。响应未知、输出失败或停止等待后，保留 CLI 待完成记录，使用同一命令或已解析的实际 ID 恢复，禁止重新按名称选择别的资源。删除回执不含持久化清理错误码；长时间处于 deleting 时检查服务端清理日志，`--wait` 会继续等待，必要时停止等待后排查，不伪称已经物理清空。

项目 entry 仅在 create 指定，省略后也不能改为 Site；没有 style 参数。`web serve ID --dir DIST` 从 MGR 读取固定入口。可编辑参数使用 `web update ID --expected-revision REV [--name NAME] [--description DESCRIPTION] [--database-instance-id DB_ID] [--git-instance-id GIT_ID] [--source-commit FULL_HASH]`。清空关联使用 --clear-database、--clear-git、--clear-source-commit；清空 Git 时同时清空已有 commit。更新不发布文件，publish 不修改项目参数。
