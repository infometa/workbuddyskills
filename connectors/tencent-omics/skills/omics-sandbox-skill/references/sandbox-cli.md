# 沙箱 CLI 操作

本技能使用 `omics sandbox`。以安装版本的子命令 `--help` 和本次服务端返回为准，不需要额外 Python wrapper、SSH 或凭据桥接。

## 发现与创建

```sh
omics sandbox templates -o json
omics sandbox list -o json
omics sandbox create --name <任务名称> --template <Available模板ID> -o json
```

`templates` 是只读查询。按 `Tools` 和 `Description` 匹配任务，要求 `Available=true`，读取 `CpuLimit`、`MemoryLimit` 等实际配置。CPU、内存通常省略以使用模板规格；显式指定时须与模板一致。`--disk` 是系统盘规格，不是个人盘容量。不要根据模板名字猜 GPU、软件包或镜像版本。

`create` 返回单个沙箱对象；`list` 返回数组，空列表也可能为 `null`。保存 `SandboxId`，不用 `InstanceId`、`SpaceId` 或名称代替。创建/恢复默认等待最多 120 秒至 `RUNNING`；`--wait=false` 只表示请求被接受。等待超时先查询：名称不是创建幂等键，重复请求可能产生多个实例。

| 实际状态 | 操作 |
| --- | --- |
| `CREATING` / `RESUMING` | 等待并回查，不重复创建 |
| `RUNNING` | 可以执行命令 |
| `PAUSED` | 按任务需要 `resume`，等待 `RUNNING` |
| `NONE` / `STOPPED` 且仍在列表 | 可 `resume`；系统盘可能重新初始化 |
| `STOPPING` | 等待后台清理 |
| `ERROR` | 读取 `StopReason` 并处理具体原因 |
| 已删除或已回收、不在列表 | 旧 ID 不可执行/传输/恢复；有需要时新建实例访问保留个人盘 |

## 输入与结果传输

AgentBucket 个人盘自动绑定到沙箱，挂载为 `/mnt/workspace`。同一登录身份同地域的多个沙箱共享该盘；不同 OneID 用户不会仅因云账号相同就共用个人盘。

```sh
omics sandbox exec --id <SandboxId> -- mkdir -p /mnt/workspace/<任务目录>
omics sandbox cp ./input.csv <SandboxId>:/mnt/workspace/<任务目录>/input.csv
omics sandbox cp ./analysis.py <SandboxId>:/mnt/workspace/<任务目录>/analysis.py
omics sandbox cp <SandboxId>:/mnt/workspace/<任务目录>/results/summary.csv ./downloads/<新目录>/summary.csv
```

上述命令中的占位符须替换为实际值；任务目录应唯一且避免 shell 特殊字符。`cp` 源与目标恰好一端是 `<SandboxId>:/mnt/workspace/...`，另一端是本机路径。只支持单个普通文件，不支持递归目录；远端路径不能包含 `.` 或 `..` 目录段。本地文件名含冒号时写成 `./文件名`；路径含空格时引用整个参数。

上传覆盖远端同名文件；下载拒绝覆盖已有本地文件。下载目标若为已有目录，会沿用远端文件名，否则按完整目标路径处理。`cp --timeout` 控制本次传输时限。

Windows 当前版本会把 `C:\...` / `D:\...` 盘符路径中的冒号识别为远端分隔符。先切换到实际本地任务目录，再给 `cp` 传相对路径；远端仍使用 `/mnt/workspace/...`。以下 PowerShell 示例假定已将本次选定 CLI 的完整路径放入 `OMICS_CLI_PATH`，并用真实沙箱 ID 与任务目录替换示例值：

```powershell
Set-Location -LiteralPath 'D:\analysis\current-task'
$sandbox = '<实际SandboxId>'
$taskDir = '<本次远端任务目录名>'
& $env:OMICS_CLI_PATH sandbox cp '.\input.csv' "${sandbox}:/mnt/workspace/$taskDir/input.csv"
& $env:OMICS_CLI_PATH sandbox cp "${sandbox}:/mnt/workspace/$taskDir/results/summary.csv" '.\downloads\summary.csv'
```

下载前准备本地 `downloads` 目录并选择尚不存在的目标文件。PowerShell 使用以上完整命令行，不照搬 Shell 示例的反斜线续行符；连接器场景沿用其绑定的 CLI 路径，不能重新按 PATH 选择同名 CLI。

多文件结果可以在远端打包再下载，例如在实际任务目录执行：

```sh
omics sandbox exec --id <SandboxId> --cwd /mnt/workspace/<任务目录> -- \
  tar -czf results.tar.gz results
omics sandbox cp <SandboxId>:/mnt/workspace/<任务目录>/results.tar.gz ./downloads/<新目录>/results.tar.gz
```

解压到新的本地目录后核对清单、大小和校验和，再打开关键文件。传输不要求计算实例正在运行，但 ID 必须未删除且仍绑定有效个人盘。系统盘和 `/tmp` 无法通过 `sandbox cp` 传输；必须保留的输入与结果写到个人盘。

## 执行语义与恢复

```sh
omics sandbox exec --id <SandboxId> --cwd /mnt/workspace/<任务目录> \
  --timeout 20m --client-token <本次执行UUID> -- \
  python analysis.py --input input.csv --output-dir results
```

每次执行生成并保存一个 UUID；相同请求的恢复使用原 UUID。`--cwd` 必须是远端已存在的绝对目录，默认 `/mnt/workspace`。`--env KEY=VALUE` 可重复，后写的同名变量覆盖前者；不把凭据写进示例、记录或命令日志。

远端命令有两种传参方式：

- `--` 后多个参数逐个保留内容，不再展开变量、通配符、管道和重定向。
- `--` 后一个字符串按 shell 脚本执行。需要 shell 语法时在本机用单引号保护整段脚本，例如 `-- 'wc -l < input.csv > line-count.txt'`。

远端不加载交互 shell 初始化文件；需要已有 conda 等环境时显式初始化。没有 stdin/TTY，也不实时输出日志，不使用交互式程序等待输入。绘图脚本写图形文件，使用工具支持的非交互后端。

本机执行工具应为 `--timeout` 之外留出至少 90 秒日志收尾时间；取消确认可能再需 10 秒。超时或 Ctrl+C 会尝试取消已取得命令 ID 的请求，以实际平台响应判断远端是否终止。

网络中断、提交或查询结果不明时，仅以原 token 和完全相同的 `--id`、命令、cwd、env、timeout 恢复同一次执行。修改脚本内容或请求参数后视为新执行，使用新 token。不要先改输入文件再重试旧请求。

执行前把完整请求和输入/脚本 SHA256 保存到任务记录中。当前 CLI 没有仅凭 token 查询或恢复执行的子命令，`logs` 也不保证包含完整原请求。只剩 ID/token 时，先按原 SandboxId 查询摘要和取回已知产物；不能把旧 token 搬到另一个 RUNNING 实例。无法还原请求且产物也不足以判定时，说明状态未知，补齐原请求或确认一次新执行的范围；不推测性重试。

退出码与 stderr 一起判断：程序自身可以返回 2；只在出现实际鉴权错误（例如 `[OMICS_AUTH_REQUIRED]`）时进入登录流程。日志读取失败也可能使成功命令返回非零，先核对命令摘要与已生成的产物，不能据此直接重复分析。

## 生命周期与日志

```sh
omics sandbox logs --id <SandboxId> --limit 50 -o json
omics sandbox logs --id <SandboxId> --limit 50 --before <NextBeforeEventId> -o json
omics sandbox pause --id <SandboxId>
omics sandbox resume --id <SandboxId> -o json
omics sandbox stop --id <SandboxId> --force
```

`logs` 读取已采集的生命周期事件和命令摘要，支持已删除 ID，返回 `Logs` 和 `NextBeforeEventId`；游标为空时结束分页。它不返回客户 stdout/stderr，不代表日志一定齐全。分析过程的 stdout/stderr 应在 `exec` 返回时保存。

暂停前等本次命令结束。`pause` 不延长实例到期时间；状态变为 `PAUSED` 后释放运行名额，恢复时重新占用运行名额。`resume` 可能恢复原系统盘，也可能为仍存在的停止记录创建新系统盘。程序和依赖应可从保留盘中的脚本与版本记录恢复。

用户已授权完成后关闭本次实例时，用 `stop --force` 跳过 CLI 交互；它与 `rm`、`delete` 同义，会终止命令并回收系统盘。返回已接受时继续按状态确认，不能把它当作已经删除。只处理本次目标实例。

受控命令执行期间会续期，完成后按平台闲置策略回收；`list` 和 `logs` 不续期，不承诺暂停可以永久保留实例或固定费用。普通关闭保留个人盘；`unsubscribe-storage` 是可能删除数据的个人盘退订操作，不纳入此工作流。
