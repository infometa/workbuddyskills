---
{
  "name": "omics-task-skill",
  "description": "通过 Omics CLI 提交和核验 WDL/Nextflow/Lambda 任务，管理 Lambda 应用定义及托管环境，查询环境盘容量；支持已有项目或团队智能体项目，以及单任务和多步骤 Lambda 输入覆盖。",
  "description_zh": "通过 Omics CLI 管理 Lambda 应用、环境与容量，查询和提交工作流，跟踪运行并核验结果。",
  "description_en": "Use the Omics CLI to manage Lambda applications, environments and storage capacity, inspect and submit workflows, track runs and verify outputs.",
  "version": "1.1.3",
  "author": "Tencent Healthcare Omics"
}
---

## 本连接器的 CLI 与平台绑定

本包使用正式通道，连接 `omics.qq.com`。安装器使用稳定地址，安装和 `omics update` 获取该通道当前版本。CLI 可独立更新；不锁定 CLI 版本、源码提交或安装器摘要。

macOS/Linux：

```sh
export OMICS_CLI_PATH="$HOME/.local/bin/omics"
"$OMICS_CLI_PATH" version
```

Windows PowerShell：

```powershell
function Get-OmicsUserPath([string]$p){if([string]::IsNullOrWhiteSpace($p)){return};$p=$p.Replace('/','\').TrimEnd('\');if($p-match'^[A-Za-z]:\\'){$a=$p.Substring(3).Split('\')}elseif($p.StartsWith('\\')){$a=$p.Substring(2).Split('\');if($a.Count-lt 2){return}}else{return};foreach($s in $a){if([string]::IsNullOrWhiteSpace($s)-or$s-eq'.'-or$s-eq'..'-or$s-match'[<>:"|?*\x00-\x1f]'-or$s.EndsWith(' ')-or$s.EndsWith('.')){return}};return $p}
function Get-OmicsUserHome{foreach($v in @($env:USERPROFILE,[Environment]::GetFolderPath('UserProfile','DoNotVerify'),$HOME)){$r=Get-OmicsUserPath $v;if($r){return $r}};throw 'Cannot resolve a fully qualified Windows user profile'}
function Get-OmicsLocalAppData{foreach($v in @($env:LOCALAPPDATA,[Environment]::GetFolderPath('LocalApplicationData','DoNotVerify'))){$r=Get-OmicsUserPath $v;if($r){return $r}};return (Join-Path (Get-OmicsUserHome) 'AppData\Local')}
$d=Get-OmicsLocalAppData;$env:LOCALAPPDATA=$d;$p=Join-Path $d 'Microsoft\WindowsApps\omics.exe';
$env:OMICS_CLI_PATH=$p
& $env:OMICS_CLI_PATH version
```

后续将每条命令开头的 `omics` 替换为当前平台的 `"$OMICS_CLI_PATH"` 或 `& $env:OMICS_CLI_PATH`。不同 Shell 不一定继承变量，每次重新设置；不能直接使用 PATH 中的同名命令而切换通道。需要 Python wrapper 时，在同一进程设置 `OMICS_CLI_PATH`；原生 CLI 无需 Python。

登录态和配置仍位于用户目录的 `.omics-platform-cli/auth.json` 与 `.omics-platform-cli/omics_config.json`。status 只读，不安装或更新；不要读取、打印或迁移凭据。以下来源技能正文保持原样；安装路径、更新方式和平台地址以上述通道说明为准。

上述绑定覆盖本技能正文、references 中的示例，以及 CLI help/NextActions 返回的后续命令。调用返回的 argv/Executable 时同样使用此处固定二进制，不直接执行裸 `omics`。PowerShell 使用完整命令行或其原生续行方式，不照搬 Shell 示例中的反斜线续行。

任务技能可直接使用上述固定 CLI。使用 `scripts/omics_cli.py` 时在同一子进程环境设置 `OMICS_CLI_PATH`；原生 CLI 已支持但 wrapper 未封装的子命令直接调用固定 CLI，不能假造 wrapper 参数。
<!-- END CONNECTOR BINDING -->

# 组学平台任务操作

使用用户机器上的 Omics CLI 完成应用查询、定义管理、环境与存储管理、任务提交和结果核验。本技能是操作指南；具体科学算法、镜像、输入输出要求来自用户选定应用。

## 先确认 CLI 与目标

运行 `omics version`、本次子命令的 `--help`，并通过 `omics whoami` 的实际返回确认登录。旧客户端可能缺少 Lambda、项目选择或多步覆盖；缺少能力时报告需要升级，不猜参数、不改用固定旧项目或环境。登录与安装见 [准备说明](references/omics-cli-setup.md)。

已核对的命令形态：`omics whoami` 是文本输出，不加 `-o json`；`omics status <RunGroupId> -o json` 返回**运行数组**，按 `RunUuid` 选中本次记录；单个运行用 `omics debug --run <RunUuid> -o json`。不要给 `status` 加 `--run`，也不要把数组按对象读取 `Status`。查询时保留本次 `--project`，优先执行回执中的 `NextActions`。

项目选择：本次 `--project/-p` > config 保存项目 > 已认证团队的智能体项目。`--agent-project` 忽略保存项目，且与 `--project` 互斥。显式/已保存项目无权限时报告错误；查询与预览不创建默认资源。提交后保存实际返回的 `ProjectId`、`EnvironmentId`、`Region`；后续 `status`、`debug`、`list apps` 用实际 `ProjectId` 显式定位，避免保存偏好变化导致查错项目。版本/模板查询按 ApplicationId 定位来源，不追加其未支持的项目参数。

执行环境独立于项目：`omics run --region ap-guangzhou/ap-beijing/ap-shanghai` 可选择广州、北京或上海；环境和地域都省略时默认广州。显式 `--environment` 使用该环境实际地域，同时传 `--region` 时必须一致，冲突直接报错。NF/WDL 只选择该地域已有、就绪且有 CFS 的适用环境，找不到直接失败；Lambda 正式提交可复用或创建该地域的组织默认 CLI 环境，并等待就绪。各地域默认环境独立，团队智能体项目仍只有一个，其项目归属及定义存储继续在广州，不因地域重复创建；计算地域以实际执行环境的 `Region` 为准，不能用项目 `Region` 代替。新版运行路径不继承 config.EnvironmentId 或保存地域，不能为一次切换重写共享配置。存储上传、列目录和下载使用实际 `--environment`；Notebook 与定义来源仍按各自命令处理，不能混用目标规则。

用户已明确授权本次运行且输入、目标与费用范围清楚时，展示实际命令和摘要后执行；缺少授权或关键目标不清才询问。取消、清理、覆盖应用、修改持久配置和重跑依照本次授权，不因前一步失败自动扩大操作。实际配额与权限按服务端返回处理，不预设固定试用桶、首个项目或环境。

大规模、耗时不确定、多方法或需要重跑时，读取 [运行预算与失败恢复](references/execution-budget.md)：优先复用适用的历史验证，必要时做代表性试跑，并累计准备、失败尝试、计算和传输的开销。按用户明确预算与实际阶段决定下一步，不设固定并发/失败次数；Lambda 默认 `timeoutSeconds: 0` 或省略，仅保留用户明确的正数期限。执行路径遵循“默认 Lambda → 组装自定义/适配 Lambda → 云沙箱 → 本地兜底”的优先级，当上层路径不适用或受阻时按序降级并说明原因；普通已授权执行无需逐步确认。

- **长任务/GPU排队静默等待准则**：当调用 `omics wait` 或后台轮询等待 GPU/计算节点调度时，保持静默等待（单次 `omics wait --timeout` 设为足够时长如 600s–1200s），**严禁在同一轮回复中连续输出多段重复的“仍在排队/已等待 X 分钟”进度小结**，避免刷屏；待任务状态发生实质变化或全部完成后，再一次性输出结构化交付报告。
- **默认输入本地直读准则**：各 Skill 已在包内 `examples/`、`defaults/` 或 `assets/homepage/` 内置首页默认测试输入与默认多步交付工作流 YAML。审阅默认输入或提交默认全流程时，直接读取本地内置文件，**严禁向 403 私有桶裸发公网 HTTPS 下载，也严禁仅为了“查看默认输入内容”额外提交搬运 Lambda**。

## 应用定义、环境与存储管理

- 创建/更新/导出 Lambda 应用、从运行保存应用、导入公共版本，或执行 `lambda validate` 时，读 [Lambda 应用管理](references/lambda-app-management.md)。区分只读校验、保存新版本与投递任务；更新需当前 `ApplicationVersionId`，不能绕过并发冲突。
- 列举/创建/重试/删除托管环境，或查询环境盘容量时，读 [环境与存储管理](references/environment-storage.md)。环境创建默认保存本地上下文；一次性操作显式使用 `--set-context=false`。个人盘与环境盘的生命周期和查询入口不同。

## 按来源选择运行方式

| 来源 | 入口 | 输入与注意事项 |
| --- | --- | --- |
| 本地 WDL | `omics run --wdl <文件或目录> --name <名称>` | `--input` JSON；目录有歧义时指定 `--main`；已有应用更新才用 `--update` |
| COS Nextflow | `omics run --nf <cos://桶/源码前缀/> --name <名称> --nf-version <版本>` | 源码先上传；`--input` 为真实参数；支持的引擎与缓存卷按目标环境核对 |
| 项目应用 | `omics run --app <ApplicationId>` | 先查真实类型、版本与输入定义；使用 `--version` 固定版本 |
| 公共应用 | `omics run --public-app <AppId>` | 先展开合集选择子应用；新版自动识别类型，`--app-type` 仅可选校验 |
| 完整 Lambda YAML | `omics run --lambda-file <lambda.yaml>` | 单 Task 或 workflow；也可选 `--lambda-cos` / `--lambda-text`，来源互斥 |

详细 NF/WDL、公共/项目 Lambda 应用参数与结果处理见 [命令参考](references/cli_commands.md)。`--dry-run` 是 Lambda 服务端校验/预览，不是 NF/WDL 通用试跑；打印命令也不代表经过预览。

## 完整 Lambda：覆盖、预览、提交

先读取所选应用的 SKILL、完整 YAML 与真实输入，保留镜像版本、命令、依赖和输出定义。不要把微型演示输入当用户数据。

官方封装默认按计算阶段无公网设计。权重、参考库、注释、MSA 和外部服务响应先在提交端准备，记录来源、版本、取得时间及 SHA256，再作为具名 `inputs` 传入；软件依赖在镜像构建时固定。缺文件时报出所需输入，不在计算中自动下载、安装或切换在线服务。实时服务无法预先准备的部分须明确标记为能力边界。平台搬运 COS 输入和发布输出属于计算之外的数据传输；平台 SUCCESS、本地联网拦截测试和真实无网执行是不同证据，按 [Lambda 验收说明](references/lambda-acceptance.md#默认无公网与离线证据) 分别记录。

CLI 在确定本次实际执行环境后，将 Lambda 输入中平台托管桶 `tencent-ailab-healthcare-gz-1252949230` 的结构化 URL 自动替换为北京/上海环境对应的桶；广州或其他地域保留原地址，无需手工改模板或配置桶。当前统一目录下的对象 key 保持不变，已确认清单中的旧地址按兼容规则补目录。直接 YAML、项目/公共应用的单任务和多步骤输入均适用，应用提交保留原应用关联；预览及 `lambda validate --for-run` 返回替换后的执行定义。仅此源桶的 Lambda 输入适用，其他桶、NF/WDL、输出及普通上传下载不变。地域映射与核对方式见 [Lambda 托管输入的地域适配](references/cli_commands.md#lambda-托管输入的地域适配)。

单 Task 覆盖文件按输入 `name` 覆盖：

```yaml
inputs:
  - name: input
    url: cos://<已授权存储>/<真实输入>
```

多步骤覆盖需要真实步骤名，再指定该步骤的输入名：

```yaml
steps:
  - name: prepare
    inputs:
      - name: samples
        url: cos://<已授权存储>/<样本表>
  - name: analyze
    inputs:
      - name: request
        content: '{"mode":"summary"}'
```

示例中的名称必须替换为原 YAML 已有的名称。URL/content/from 互斥，未替换的内部输入保留 `from`；复用既有产物时，按实际支持的覆盖语义将该输入改为已发布 URL。不能只改 URL 却保留冲突的 `from`，也不能以为覆盖输入就会自动跳过上游步骤。不把通用任务级 flag 用于未指定步骤的 workflow。确认 CLI help 支持按 `steps[].name` 合并。

多步定义是可组合的步骤和依赖图。中间失败、调整参数或追加分析时，鼓励从原定义抽取一个步骤或需要继续的子图，绑定已成功发布且兼容的上游产物，只执行受影响的部分；无需为每个步骤另建模板。按 [多步续跑与增量分析](references/lambda-continuation.md) 检查失效范围、组合子图并保留来源。现有 `scripts/compose_lambda_continuation.py` 可从冻结定义和真实回执生成单 Task 或剩余 workflow；它不依赖尚未部署的后台覆盖能力，也不提交运行。

```sh
omics run --lambda-file lambda.yaml --override-file override.yaml --agent-project --dry-run -o json
```

也可改为 `--project <实际项目>`，按需要追加 `--region ap-beijing` / `--region ap-shanghai`，或 `--environment <实际环境>`；省略目标选择时保持上面的优先级。检查解析后的项目、环境、输入、镜像和输出位置。默认资源未创建时可能返回 `Ready=false` / `NOT_CREATED`，这是未就绪，不能报告预览通过。 新版 CLI 会以 `Code=CONTEXT_NOT_READY`、`Ready=false`、`ValidationPerformed=false` 标识这类首次预览；用户已授权本次运行且其他输入完整时，可以按原参数正式提交以准备默认资源。其他校验错误仍须先修正，不能一概忽略 dry-run 失败。

正式提交使用相同参数并去掉 `--dry-run`；首次默认资源创建与等待属于本次正式运行。发生超时先查已有 RunUuid/请求记录，不重复投递。直接 YAML 不接收应用 schema 的 `--param`、`--param-json`、`--input`；已注册 Lambda 应用则依自身 schema 提供参数，不能套用多步 YAML override。

`--output-prefix` 只用于 Lambda，省略时结果写入执行环境的环境盘；显式普通 COS 桶必须关联该执行环境。读取返回的 `ExpectedOutputs` / `ExpectedOutput` 与最终运行结果，不能拼造地址。

## 上传、取证与交付

上传前锁定本次项目与执行环境，所有上传和提交显式复用该环境。已选环境时直接用 `omics cos upload <文件> --environment <本次EnvironmentId> --prefix <前缀> -o json`，采用成功回执的 `TargetCOSPath`（单文件或目录根），多个上传参数按 `Targets[]` 匹配，逐文件核对 `Results[]`；核对上传回执的 `EnvironmentId` / `Region` 与运行预览相同。没有用户指定环境时，可从 Lambda 预览或上传回执解析默认环境，一旦取得 ID 就固定到后续命令。若上传落到另一环境，保留错误，在原目标重传或说明需变更目标；不能为适配已传桶而静默切换执行环境。未指定环境/桶时解析组织默认 CLI 环境盘，忽略 config 中历史环境/桶；项目选择不会自动改变显式上传目标，无需先查桶名或修改 config。无现有默认资源时正式上传可准备默认环境盘，`--dry-run` 不创建；已有目标不可用不改投默认盘。NF/WDL 先选有 CFS 的已有环境再上传。不要上传凭据、未授权矩阵或未脱敏日志。

```sh
omics status <RunGroupId> --project <返回的ProjectId> -o json
omics debug --run <RunUuid> --project <返回的ProjectId> --with-stdout -o json
```

环境列表和提交回执的 `UploadCommand` 会指出本次上传目标；按 `Placeholders` 补齐本地路径或仍待选择的桶，不推测桶名。无默认盘时，唯一有效关联桶可直接使用；多个桶从 `UploadBucketChoices` 选择，缺桶或查询失败按 `UploadMessage` / `BucketListCommand` 处理，不执行未填的 `<bucket>`，也不改投其他环境。结束查询优先使用 `Artifacts[].DownloadCommand`，覆盖顶层输出及已发布的步骤产物；目录命令自带 `--recursive`，不能把 `Expected` 或 `Unconfirmed` 当作可下载。

优先使用 CLI 返回的 `NextActions` 完整命令；程序调用用其中的 `Executable` / `Args`，复制执行用匹配本机 Shell 的 `Command`。结果下载使用实际产物 URI，普通 COS 传本次 `EnvironmentId`，个人盘不传环境。手工下载的命令格式为 `omics cos download <实际cos://产物地址> <本地目标> --environment <实际环境ID> -o json`，目录追加 `--recursive`，个人盘省略 `--environment`。向用户交付可直接执行的完整下载命令及本地目标路径，不只给前缀；预期输出地址不代表已发布。Lambda 必须区分输入准备、用户计算、结果发布与最终回执；计算成功但发布失败不能报告整次运行成功。需要诊断时按 [取证知识库](references/runtime_error_kb.md) 的实际信号分析，区分事实与假说。

每条提交、查询、上传或下载命令先把完整 stdout、stderr 分别保存到本次证据目录并记录退出码，再解析 JSON；不经 `head`、`tail` 或字符截断，也不把 `2>&1` 混入 JSON。界面可展示摘要，原回执保留完整。未知提交结果与失败终态的处理不同：**复用原 `--client-token` 只恢复同一次请求的回执，不重启失败 Run**。需要重跑时读取 [运行恢复与重跑](references/lambda-recovery.md)，原样重跑用 `omics retry --run <原RunUuid> --project <实际ProjectId> -o json`；修改定义后以新请求提交。只有新 RunUuid 及后续实际状态能证明重跑，返回原 RunUuid 不能称“恢复运行”。

交付实际运行标识、版本、参数、产物地址、日志证据与输出语义核验。退出码或文件存在不等于科学结果正确。记录失败与未执行部分。

### Lambda 的运行与验收结论

将预览就绪、平台运行成功、输出验收通过分开报告。`SUCCESS` 只能证明平台运行完成；完整验收还需要核对本次冻结定义、每个步骤的日志与输出发布回执，下载真实产物，并通过适合当前入口和输入的结果校验器。缺少校验器、校验器只覆盖其他模式或证据不完整时，明确写“平台成功，输出待验收”，不能写“已验证”。

用 `omics run-definition --run <RunUuid> --project <本次项目> --format json` 取得服务端冻结定义。提交时保存原始 YAML、输入/覆盖参数和运行标识；源文件身份由服务端 `SourceAudit.rawSha256` 对照提交字节确认，实际执行内容以冻结 Task/workflow 为准。具名输入输出按名称匹配，多步按步骤名及完整依赖图匹配：服务端排序和已定义默认值不属于内容变化；命令参数顺序、镜像、资源、输入内容、输出合同和依赖关系不能忽略。多步输出按“步骤名 + 输出名”绑定该步骤回执，不把工作流导出别名当作步骤输出名。详细判定与仓库验收入口见 [Lambda 验收说明](references/lambda-acceptance.md)。

复用历史验收结论时，应用版本、最终定义及输入参数、运行与目标、通用验收器和应用校验配置均须对应当前内容。YAML、校验器或校验依据变化后重新核验，不能因为版本号未变就沿用旧“已验收”。示例通过只覆盖该示例及所用模式，应用已记录的科学能力 gap 仍单独保留。

## 可选 Python wrapper

`scripts/omics_cli.py` 构造 argv 并调用当前 CLI，不读取认证文件、不直接调用后端 API。可直接使用已核对的原生 CLI；wrapper 未封装的现有子命令不要伪造为“不存在”。`--print-command` 仅展示命令，`run --dry-run` 才请求真实 Lambda 预览。详细兼容范围见 [CONTRACT.md](CONTRACT.md)。
