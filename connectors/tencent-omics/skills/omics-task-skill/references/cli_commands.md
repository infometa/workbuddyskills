# 任务 CLI 参考

以下使用 hosted CLI 的任务及存储上下文能力，使用时先读本机 `--help`；存储命令须支持 `--environment`，下载还需核对 `--recursive` 和 `-o json`。命令中的示例名称、ID、输入与版本需要使用真实值，不自动代入公共演示数据。

## 查询与项目

```sh
omics whoami
omics config show -o json
omics list public-apps -o json
omics list public-apps --parent-app <合集AppId> -o json
omics list apps --agent-project -o json
omics list versions --app <ApplicationId> -o json
omics list templates --app <ApplicationId> --with-content -o json
```

公共列表的 AppId 与项目应用的 ApplicationId 不可混用；合集需选择具体子应用。`list apps`、状态、诊断使用同一项目参数；没有显式项目时采用 config 项目或团队项目。`list versions/templates` 按 ApplicationId 只读定位有权限的来源，不支持额外项目参数。列表没有结果不证明有权创建/访问其他项目。

## WDL / Nextflow

```sh
omics run --wdl <源码目录> --main <入口.wdl> --name <批次名> --input <参数.json> --project <项目ID> --environment <环境ID> -o json
omics run --nf cos://<已授权桶>/<源码前缀>/ --name <批次名> --nf-version <实际支持版本> --input <参数.json> --agent-project --environment <环境ID> -o json
omics run --public-app <公共AppId> --project <项目ID> --input <参数.json> -o json
omics run --app <ApplicationId> --version <ApplicationVersionId> --project <项目ID> --input <参数.json> -o json
```

- NF/WDL 的执行环境只选择已有、就绪且有 CFS 的适用环境；可用 `--region ap-beijing` / `--region ap-shanghai` 限定地域，环境和地域都省略时默认广州，找不到直接报错，不新建无 CFS 环境。显式 `--environment` 使用实际地域；同时传 `--region` 时必须匹配。
- WDL 支持已有应用的 `--update` 及关联版本选项；NF 新源码应按已核对命令新建，不能假设同一更新接口可用。
- COS NF 新建需指定支持的引擎版本；公共 NF 可由新版服务端选择支持版本，`--nf-version` 也可显式覆盖。
- 公共应用新版自动识别 WDL/NEXTFLOW/LAMBDA，`--app-type` 只作可选类型校验。
- `--input` 与 `--template` 不能同时作为参数来源；模板适用范围、必填字段、类型错误按实际返回修正。
- NF 可按真实目标使用 `--nf-resume`、`--nf-config`、`--nf-profile`、`--nf-report`、`--volume-id`；不能把恢复缓存等同整次重跑成功。
- 不给 NF/WDL 加 Lambda 的 `--dry-run` / `--output-prefix`。核对基线没有 `--output-dir` flag；应用输出通过真实参数定义和运行回执确认。

## Lambda

完整 YAML 按 SKILL.md 的单 Task / steps 覆盖示例提交：

```sh
omics run --lambda-file lambda.yaml --override-file override.yaml --agent-project --dry-run -o json
```

正式提交去掉 `--dry-run`，保留其余目标、输入与输出参数。一次命令选择北京或上海可用 `omics run --lambda-file lambda.yaml --region ap-beijing -o json` 或将地域改为 `ap-shanghai`；公共/项目应用同样支持 `--region`。环境和地域都省略时默认广州，显式环境则采用其实际地域；同时指定的地域不匹配会报错。Lambda 按选定地域复用或创建组织默认 CLI 环境，各地域独立，团队智能体项目保持共用，其归属及定义存储仍在广州；实际计算地域读取执行环境 `Region`，不使用项目 `Region` 推断。预览只查询，不创建环境。`--lambda-cos` 指向单个 YAML 对象，按对应命令的授权上下文读取；run 的远端步骤覆盖使用本次执行环境，不为了读取来源改 config。定义导入/静态校验另有保存来源环境规则。`--lambda-text` 是完整定义文本；来源互斥。

已注册应用先读取 schema 与版本；支持的 `--param key=value`、`--param-json` 和 `--input` 用于该应用的参数对象，不用在直接 YAML。公共 Lambda 保持 `--public-app` 来源，私有 Lambda 保持 `--app` 来源。多步骤已注册应用使用其公开 schema，不能套用单 Task flags 或 steps override。`--use-example` 仅在用户明确需要官方示例时使用。

输出可加 `--output-prefix cos://<执行环境关联桶>/<目录>/`；省略时使用实际执行环境盘。记录返回的实际 ProjectId/EnvironmentId/Region、RunUuid/RunGroupId、ExpectedOutputs、client token 和最终 YAML/应用版本，不伪造输出链接。

创建、更新、导出定义，从运行创建应用、导入公共版本及静态/执行校验，见 [Lambda 应用管理](lambda-app-management.md)。该新版 `app` 命令用于 Lambda 定义/版本，不同于旧文档中移除的通用查询入口。导出运行定义可用 `omics run-definition --run <RunUuid> --format workflow-yaml --project <ID>`（单 Task 按实际格式选择）；原样重跑 `omics retry` 会创建新任务，仅在本次请求包含重跑时执行。修改参数重跑应从冻结定义与真实参数准备，不修改旧运行。

### Lambda 托管输入的地域适配

CLI 在确定 Lambda 新运行的实际执行环境后，按该环境的 `Region`，自动替换 `inputs[].url` 中桶名精确为 `tencent-ailab-healthcare-gz-1252949230` 的 `cos://` 地址。直接 Task、workflow 各步骤以及项目/公共应用的默认值、示例值和参数输入均适用。当前统一目录下只替换桶名，保留对象 key；先按本次 `--region` / `--environment` 解析实际环境，返回真实 `EnvironmentId` / `Region`，再改桶并提交，不为匹配数据桶切换环境。

平台维护的 Lambda 资产统一使用 `omics-lambda-apps/` 前缀；目录外的旧资产归入 `omics-lambda-apps/<旧key>`。采用已更新的应用/skill 输入地址，不对历史记录批量补前缀。`--app` / `--public-app` 提交保留原应用及版本关联，CLI 通过通用输入覆盖传入替换后的单任务/多步骤 URL，不改成无应用关联的 YAML 提交。地域判断和改桶由 CLI 执行；API 仅接收通用覆盖参数，不自动按地域切桶。

本期仅支持北京、上海、广州。为兼容旧应用，CLI 仅在北京或上海环境中，对内置迁移清单内的旧对象/目录补上 `omics-lambda-apps/` 后再改桶；已在该目录下不重复添加，清单外 key 不补目录。广州环境保留原地址，地址转换器对其他或空地域不改地址；当前运行地域选择只支持广州、北京、上海。不得把这个兼容规则扩展成任意路径的全局替换。

| 实际执行环境地域 | 使用的托管输入桶 |
| --- | --- |
| 广州 `ap-guangzhou` | `tencent-ailab-healthcare-gz-1252949230`（原地址不变） |
| 北京 `ap-beijing` | `tencent-ailab-healthcare-bj-1252949230` |
| 上海 `ap-shanghai` | `tencent-ailab-healthcare-sh-1252949230` |

例如，同一 `cos://tencent-ailab-healthcare-gz-1252949230/omics-lambda-apps/<对象key>` 在北京环境提交后，其执行输入为 `cos://tencent-ailab-healthcare-bj-1252949230/omics-lambda-apps/<对象key>`。`run --dry-run` 和 `lambda validate --for-run` 使用相同规则，核对响应中的 `EffectiveTaskYaml` / `WorkflowYaml` 及实际 `EnvironmentId` / `Region`；运行后以 `run-definition` 的冻结输入为准。未知或未返回的地域不推测目标桶。

此行为不修改本地 YAML 或保存的应用定义，也不替换命令/脚本字符串、内联 `content`、输出路径、其他桶或 NF/WDL 输入；普通 `cos upload/ls/download` 继续使用实际传入地址。静态 `lambda validate` 和创建/更新应用不做运行地域替换；`omics retry` 沿用原运行冻结的输入，不按当前偏好重新改桶。需要变更执行环境时，按新目标重新预览并提交新运行。

来源清单或脚本参数中的 URL 可能只用于记录原始来源，并不是实际读取地址。按具名输入及消费代码区分两者；保留这些来源记录和有校验和绑定的内联 manifest，不为了地域一致手工全局替换。实际下载位置以本次执行定义中的 `inputs[].url` 为准。

## 上传与结果

需要先创建/修复托管环境、查询容量或区分个人盘和环境盘时，见 [环境与存储管理](environment-storage.md)。选择北京或上海运行时，上传、列表和下载显式复用运行预览/环境创建返回的 `EnvironmentId`，不要把省略环境的广州默认盘当作其他地域目标。

```sh
omics cos upload <本地文件> --prefix <前缀> -o json
omics cos upload <本地文件> --environment <环境ID> --prefix <前缀> --dry-run -o json
omics cos upload <本地文件> --environment <环境ID> --bucket <已授权桶> --prefix <前缀> -o json
omics cos ls cos://<实际桶>/<前缀>/ --environment <实际EnvironmentId> -o json
omics cos download cos://<实际桶>/<文件> ./results/<文件> --environment <实际EnvironmentId> -o json
omics cos download cos://<实际桶>/<目录>/ ./results/ --recursive --environment <实际EnvironmentId> -o json
```

上传指定环境但省略桶时，先选该环境默认盘，无默认盘时选唯一有效关联 COS 桶；多个桶必须用 `--bucket` 选择，零桶或查询失败不回退其他环境。未指定环境和桶时，使用服务端组织默认 CLI 环境及其默认盘，不继承 config 的历史环境/桶；保存项目仍参与权限检查，不可用时不得回退。已授权正式上传可准备尚不存在的默认资源，预览和读取只读；默认资源不存在或未就绪时报告原因，不把预览当作上传成功。

上传成功后，单个文件或目录采用顶层 `TargetCOSPath`；目录根路径可直接绑定 DIRECTORY 输入，无需从子文件地址截取或猜路径。多个上传参数按 `Targets[]` 对应 FILE/DIRECTORY；`Results[].COSPath` 保留逐文件回执。先检查失败数量和每项状态，再保存实际 `EnvironmentId`、`Region`、`Bucket`；`ProjectId` 仅在真实返回时采用，不能从桶名推导。上传预览也可返回目标地址，但文件尚未上传。`Results[].DownloadCommand` 可用于取回成功文件。

普通 COS 显式 `--environment` 无需持久 config，但仍校验桶关联；存储环境与后续执行环境应来自实际结果。AgentBucket 由服务端识别归属，个人盘示例应去掉 `--environment`，环境盘显式值必须匹配归属。读取不会创建资源；`cos ls -p` 是 prefix，不能当作项目。文件用单文件下载，目录用 `--recursive`；下载回执中的 `COSPath` / `LocalPath` 用于核对实际落点，仍需检查内容。签名地址不进入可公开日志或版本库。

```sh
omics status <RunGroupId> --project <项目ID> -o json
omics debug --run <RunUuid> --project <项目ID> --with-stdout -o json
omics debug --run <RunUuid> --job <JobId> --project <项目ID> --with-stdout -o json
```

后续命令显式使用提交或状态返回的实际 `ProjectId`，不要依赖运行后可能变化的 config。优先复用 `NextActions`：程序使用 `Executable` / `Args`，人工复制匹配本机 Shell 的 `Command`。交付完整下载命令和本地目标，不仅是存储前缀。`ExpectedOutputs` 是预期位置；需核对最终发布记录，计算完成不等于归档完成。`status -o json` 保持数组、`debug -o json` 保持对象，按各自实际上下文和产物字段读取。

NF 可按需追加 `--with-trace` / `--with-reports`。Lambda 的具体取证能力以实际返回为准；取证为空或不支持不等于运行成功。按调用阶段与作业ID核对错误，只有平台成功、输出可读与科学语义检查都通过才报告任务完成。
