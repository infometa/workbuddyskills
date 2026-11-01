# omics-run-diagnosis

保留 OmicsSkill 原诊断 skill 与 E01–E11 知识库，取证实现从私有 JSON-RPC wrapper 迁到受支持的 `omics status/debug` CLI。新增 Lambda 定位、分阶段日志与结果核验说明。没有引入替代诊断服务或额外云运行。

## 来源与适配依据

- 原始 skill：OmicsSkill `master@9e59d7d` 的同名目录。
- CLI 合同：`omics-platform-cli-source` 的 `feature/hosted-environment-agent-bucket@d61562e`。
- 项目优先级及只读解析：`cmd/agent_context.go`；状态数组：`cmd/status.go`；批次/单运行 JSON、Lambda 实际环境、日志错误及截断：`cmd/debug.go`；输出目的地：`cmd/lambda_run.go`；存储读取：`cmd/cos_ls.go`、`cmd/cos_download.go`、`cmd/cos_scope.go`。

脚本不读取认证文件、不手工调用固定域名/API、不接收 Uin，也不自动安装或登录。认证、服务地址、项目和访问权限由当前 CLI 处理。服务地址不是运行环境，`--env prod/dev` 不能映射成 `--environment`。

## 脚本接口

仅依赖 Python 3 标准库与兼容的 `omics` 可执行文件。从 skill 目录运行：

```bash
python3 scripts/query_run_log.py --run-uuid RUN_UUID --project PROJECT_ID --with-stdout
python3 scripts/query_run_log.py --run-group-id GROUP_ID --agent-project
python3 scripts/query_run_log.py --status --run-group-id GROUP_ID --project PROJECT_ID
python3 scripts/query_run_log.py --run-uuid RUN_UUID --agent-project --print-command
```

沿用 `--run-uuid` / `--run-group-id` 参数，但两者现为严格互斥。旧 `--run-uin` / `--env` 会明确报参数错误，避免静默查询另一身份/服务。CLI 选择优先级为 `--omics-cli` > `OMICS_CLI_PATH` > PATH 中 `omics`；已指定路径不可执行时直接失败，不回退。子进程使用 argv、不经过 shell；没有项目参数时原样委托 CLI 的 config/团队选择规则。

输出版本为 `schema_version: 2`，`response` 保留 CLI 对象/数组结构（状态查询的空记录也可能是 `null`），新增 `cli_exit_code`、`collection` 及必要的错误文本。旧消费者需要从 `response.Logs` 的私有接口结构迁到 SKILL 描述的 `Status/Calls/JobLogs`。CLI 非零退出仍保留有效部分 JSON；0 仅表示查询正常返回，日志级错误仍可存在。启动失败返回 127，超时返回 124，JSON 无效/形态不符返回非零；CLI 失败码原样保留（进程信号归一为 1）。

输出对常见认证键、HTTP 认证头、URL query/userinfo 做脱敏，保留诊断状态、对象路径和非敏感日志。它不是任意日志的完整隐私检测器，分享前仍需审阅。默认不请求带签名 URL 的 Nextflow HTML 报告；确需查看时使用当前 CLI 的相应选项，在可信环境内处理，不将签名链接复制到报告。

## 验证

```bash
python3 -m unittest discover -s tests -v
```

离线测试覆盖参数互斥、作用域透传、状态数组、Lambda job 取证、部分 JSON/非零退出、抓取错误与截断、超时/缺 CLI、敏感输出处理，以及真实 fake CLI 子进程（含空认证目录、带空格的可执行文件路径和 shell 特殊字符）。固定路径与 PATH 同名 CLI 并存时，验证显式参数/环境变量优先且指定路径失效不会改用 PATH。测试不登录、不读真实认证、不调用云 API、不创建资源。

实用边界：CLI 当前批次列表有分页上限；日志默认只取部分失败作业并可截断，`--job` 用于继续取证。平台和存储读取仍需使用者权限。离线验证不替代真实部署版本、登录身份和任务权限下的运行验收。
