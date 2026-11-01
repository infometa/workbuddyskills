# Lambda 应用定义与版本

用于保存、维护、复用 Lambda 定义。以下命令按 CLI `0e868c3` 核对，使用原生 CLI；这些动作不会投递计算任务。示例 ID、名称、文件都替换为本次真实目标。

## 项目、来源与回执

项目沿用 `--project` > 已保存项目 > 团队智能体项目；`--agent-project` 强制团队项目，与 `--project` 互斥。示例用显式项目以绑定应用归属。正式创建/导入可准备缺失的团队项目，查询和 dry-run 不创建。

定义来源三选一：`--yaml-file <文件>`、`--yaml-cos cos://<桶>/<单个.yaml>`、`--yaml-text '<完整YAML>'`。文件可用 `-` 从 stdin 读取，最多 1 MiB。支持的 Task/workflow/schema 应保留真实镜像、输入输出与依赖，不能把任意脚本当成已支持的定义。

`app create/update` 和静态 `lambda validate` 读取 COS YAML 时使用已保存的 `config.EnvironmentId` 作为来源权限上下文；这些 app 命令没有 `--environment`。不要为读取一次定义静默改配置；可在已授权范围取得本地 YAML 后用 `--yaml-file`。`--for-run` 的来源上下文使用它解析出的执行环境。

保存回执中的 `ProjectId`（有返回时）、`ApplicationId`、`ApplicationVersionId`、定义 hash，以及 CLI 的 ClientToken。应用显示名、公共 AppId、ApplicationId、ApplicationVersionId 不能互换。保存/导入时未指定 token，CLI 会生成并记录；丢失响应后恢复同一请求应保留参数和 `--client-token`，不要改参数复用旧 token，也不要无依据重复创建。

## 静态校验与执行校验

```sh
omics lambda validate --yaml-file lambda.yaml --project <项目ID> -o json
omics lambda validate --yaml-file lambda.yaml --project <项目ID> --for-run --environment <环境ID> -o json
```

默认做服务端静态校验和应用导入预览；`--for-run` 对完整 Task/workflow 增加执行权限、环境与输入可达性校验。只有后者接受 `--environment`；省略它时只读查询组织默认 CLI 环境，不继承保存的普通项目执行环境。两者均不保存应用、不创建项目/环境、不投递任务。上下文缺失、`Ready=false` 或 `ValidationPerformed=false` 不代表通过；静态通过也不代表能在指定环境运行。

## 创建应用与保存新版本

```sh
omics app create --name <新应用名称> --yaml-file lambda.yaml --project <项目ID> --dry-run -o json
omics app create --name <新应用名称> --yaml-file lambda.yaml --project <项目ID> -o json
```

`--type` 默认且目前只支持 `LAMBDA`。`--name` 是外部应用名称，与 YAML 内部任务名分开。dry-run 检查服务端预览，第二条才保存；已有创建授权时按同一目标继续，不因预览本身再次索要授权。应用创建成功不能写成计算或科学验收成功。

更新前读取当前版本，编辑该版本的定义，再携带它作为并发条件：

```sh
omics app show --app <ApplicationId> --project <项目ID> --format json
omics app update --app <ApplicationId> --expected-version <刚读取的ApplicationVersionId> --yaml-file updated.yaml --project <项目ID> --dry-run -o json
omics app update --app <ApplicationId> --expected-version <同一ApplicationVersionId> --yaml-file updated.yaml --project <项目ID> -o json
```

`update` 保存新的不可变版本，`--expected-version` 必填。冲突说明当前版本已变化：重新读取并比较差异，按本次修改目标合并后再决定保存；不能仅换成新 ID 盲目重试，也不能用旧版本号替代版本 ID。记录返回的新版本，运行时用 `run --app ... --version <新版本ID>` 固定它。

## 读取与导出

```sh
omics app show --app <ApplicationId> --version <ApplicationVersionId> --project <项目ID> --format schema-yaml > schema.yaml
omics app show --app <ApplicationId> --version <ApplicationVersionId> --project <项目ID> --format task-yaml > task.yaml
omics app show --app <ApplicationId> --version <ApplicationVersionId> --project <项目ID> --format workflow-yaml > workflow.yaml
```

按实际应用选一种格式：schema 用于参数定义，单任务用 task，多步骤用 workflow；多步不能强行导出单 Task。省略 `--version` 时 CLI 解析一次当前版本。导出 YAML 时不要加 `-o json`，否则 stdout 变成 JSON；版本与 hash 提示在 stderr。可执行导出仍须检查真实输入，不能把导出的示例参数当成本次用户数据。

## 从运行冻结快照创建应用

```sh
omics app create-from-run --run <RunUuid> --name <新应用名称> --project <源运行项目ID> --output-policy PER_RUN --dry-run -o json
omics app create-from-run --run <RunUuid> --name <新应用名称> --project <源运行项目ID> --output-policy PER_RUN -o json
```

来源是同项目的直接 Lambda Run 冻结快照，`--run` 接受 RunUuid，不接受 TES JobId。CLI 读取快照并携带 ExecutionHash 绑定来源；快照缺失不能以猜测的本地 YAML 冒充。该动作既不修改旧运行，也不重新运行。

`PER_RUN` 为默认策略，按服务端规则为输出路径引入运行隔离（`${runId}`）；检查预览后的输出定义。`PRESERVE` 保留原输出地址，后续多次运行可能写同一位置，只在本次确需保留且覆盖范围清楚时选用。两者都不会复制既有产物或证明旧运行输出通过验收。

## 导入公共应用固定版本

```sh
omics list public-apps -o json
omics app import-public --public-app <公共AppId> --version <公共ApplicationVersionId> --name <新私有名称> --project <目标项目ID> -o json
```

`--public-app` 来自公共列表的 AppId；合集先选具体子应用。该入口目前仅支持 Lambda，将固定公共版本复制到当前项目，产生新的私有 ApplicationId。省略 `--version` 时解析一次当前公共版本；记录实际来源和新应用回执。

`import-public` 没有 `--dry-run`，执行就是导入；不要给它追加该 flag，也不要把本地打印命令称作服务端预览。用户仅要求运行公共应用时直接使用 `run --public-app`，无需先导入。重复调用前先查导入结果或复用原 client token，避免生成同名副本。
