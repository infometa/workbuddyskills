# 托管环境与存储管理

用于托管环境的查询、创建恢复、删除，以及环境盘容量查询。使用原生 CLI，不把环境 ID、项目 ID 和桶名互换。环境命令不接受 `--project` / `--agent-project`；跨地域操作先确认当前客户端与服务端支持北京、上海、广州。

## 查已有环境和可用能力

```sh
omics env list -o json
omics env list --region <地域> -o json
omics list cos-bucket --environment <EnvironmentId> -o json
```

`omics list env` 是同一列表入口；地域省略时先用保存的 region，无保存值才查询所有可见地域。使用真实 `EnvironmentId`、`Region`、`DefaultDataBucket`，检查 `Available`、`Status` 和 `EngineCapabilities`。其中 `LambdaAvailable`、`NextflowAvailable`、`WdlAvailable`、`FileTransferAvailable` 分开判断；桶数量、环境存在和资源已就绪不是同一结论。

`list cos-bucket` 和 `list volume` 未传 `--environment` 时只读查询组织默认 CLI 环境，不继承 config 中保存的历史环境；默认环境不存在则报错，查询不创建资源。已确定目标时显式传同一个环境 ID，无需改 config。

列表与运行回执的 `UploadCommand` 绑定实际环境；有默认盘就用它，无默认盘且只有一个有效关联 COS 桶时可直接给出该桶。多个桶时读取 `UploadBucketChoices` 并选择本次已授权目标，不取第一个；零桶或查询失败时看 `UploadMessage` 与 `BucketListCommand`，`<bucket>` 仍是待填写占位符，不能直接执行。显式环境无可用目标时不回退到保存的其他环境或默认盘。

## 创建与等待

```sh
omics env create --name <环境名称> --region <地域> --set-context=false -o json
```

`--region` 支持 `ap-guangzhou`、`ap-beijing`、`ap-shanghai`，例如 `omics env create --name beijing-cli --region ap-beijing --set-context=false -o json`。创建共享托管环境和默认环境盘，初始不带 CFS。默认 `--wait=true`，等待 Lambda 与文件传输可用，默认超时 20 分钟；这不代表 Nextflow/WDL 已就绪。需要 NF/WDL 时使用已有含 CFS 的适用环境，或通过已有环境管理入口配置 CFS，再复核能力；本版本没有文档化的 `env add-cfs` 命令。

`omics run` 不需要预先执行 `env create`：未指定环境时，Lambda 按 `--region` 复用或创建该地域的组织默认 CLI 环境；未指定地域则默认广州。各地域默认环境独立，团队智能体项目不按地域拆分。NF/WDL 仍只选择已有、有 CFS 的适用环境。`--dry-run` 和只读查询不创建资源。

`--set-context` 默认 true，就绪后会保存环境、默认桶和地域；地域改变时还会清空已保存项目。上例明确关闭它，适合一次性创建。只有用户要保存新的 CLI 偏好时才启用它；`--default` 是设该地域组织默认 CLI 环境的另一个开关，默认 false，不能与保存本地上下文混为一谈。

需要快速取得回执可加 `--wait=false`；此时返回创建已接受的 `EnvironmentId` / `WorkflowUuid`，不会等待就绪，也不会执行后续本地上下文保存。保留 stderr 中的 ClientToken 和创建流程 ID。token 可显式传入 `--client-token`（16–128 字符）；响应丢失时复用同一请求 token，已有流程未完成不要重新创建环境。等待超时后后台仍可能继续，先用环境列表查状态。

## 恢复失败的创建流程

```sh
omics env retry --environment <失败EnvironmentId> --workflow <该环境失败WorkflowUuid> -o json
omics env list --region <该环境地域> -o json
```

先定位并解决失败原因，再复用对应环境及其当前失败流程重试。`env retry` 返回已接受，不等于就绪；它不修改本地默认环境或项目，也不用于重试删除。无法从现有回执或服务响应取得正确 WorkflowUuid 时，先查明流程，不猜 ID、不新建替代资源。

## 删除指定环境

```sh
omics env delete --environment <待删除EnvironmentId> --confirm-data-deletion -o json
```

仅适用于 `env create` 或团队默认环境流程创建的共享托管环境；旧模式托管、标准和纳管环境使用原管理入口。删除会停止该环境任务、回收资源，CFS 和环境盘数据可能永久删除。操作前将具体环境和需删除的数据范围与用户请求对齐，保存用户要求保留的数据；已有明确删除授权无需重复确认。

必须显式给出 ID 和 `--confirm-data-deletion`；它不从 config/default 猜目标。`DELETING` 只代表后台正在执行，不是删除完成。对同一 ID 再次执行可查询既有删除进度或重试当前失败的删除流程，依本次删除授权继续；不要改用 `env retry`。该命令不会修改本地配置或创建替代环境，配置仍引用旧环境时按实际错误处理，不静默切目标。

## 个人盘、环境盘与普通 COS

| 类型 | 创建与归属 | 数据操作与生命周期 |
| --- | --- | --- |
| 个人盘（PERSONAL） | 随沙箱创建绑定，归属于用户身份；同身份、同地域沙箱共享 | 挂载在沙箱工作区；数据命令用实际桶，省略 `--environment`。停止/删除沙箱不等于删除个人盘；退订存储是另一项可能影响多个沙箱及数据的操作 |
| 环境盘（ENVIRONMENT） | 随托管环境创建，绑定 EnvironmentId；不是每个项目一块 | Lambda 默认产物和环境文件传输使用该环境盘；显式环境必须匹配归属。删除所属环境可能同时删除数据 |
| 普通 COS 桶 | 已有且与目标环境关联的 COS 资源 | 文件传输与输出位置按实际桶和环境权限处理，不套用个人盘生命周期 |

CLI 通过服务端识别 AgentBucket 归属；从列表、创建或运行回执取得真实桶，不按前缀猜名称。没有单独的 `agent-drive create`、`agent-bucket create` 或个人盘创建命令。沙箱及个人盘生命周期按智能体沙箱与个人盘管理规范处理；只有处理沙箱请求时才使用，不为查询容量自动创建沙箱。

## 查询环境盘容量

```sh
omics cos quota -o json
omics cos quota --environment <本次EnvironmentId> -o json
omics cos quota --bucket <已授权托管桶名> -o json
```

本版本 `cos quota` 支持 `--environment/-e`、`--bucket/-b`，不接受项目参数。两者都省略时只读解析组织默认 CLI 环境及默认环境盘，忽略 config 中历史环境/桶；保留保存项目的权限检查。显式环境使用该环境默认盘或可明确确定的唯一有效关联桶；显式网盘桶由服务端核对真实归属，环境冲突直接报错。

保存项目不可用、没有默认环境或目标不可访问时报告实际错误；不为只读容量问题自动改配置、创建资源或改查另一个桶。前面 `env create --set-context=false` 的新环境应通过 `--environment` 明确选择，不能假设它已成为组织默认环境。

读取实际返回的 `Bucket`、`State`、`UsedBytes`、`QuotaBytes`、`EffectiveQuotaBytes`，容量单位是 bytes，目标容量与已生效容量分开报告。该接口查询托管环境盘，不能据此报告个人盘总容量、整个团队存储汇总或账单费用；`UsedBytes` 不是计费金额。个人盘容量以有权限的实际沙箱/个人盘回执或管理入口为依据，不编造扩容或配额子命令。
