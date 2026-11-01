---
{
  "name": "omics-sandbox-skill",
  "description": "通过 Omics CLI 的 Agent Sandbox 执行生命科学脚本、数据探索、统计分析、绘图和结果核验，完成文件上传、沙箱执行及产物下载。适用于需要云端临时分析环境的任务；已有 Jupyter 实例或 ipynb 操作使用 Notebook 技能。",
  "description_zh": "使用组学沙箱准备输入、执行分析、传输文件并核验结果，按授权管理实例生命周期。",
  "description_en": "Use Omics sandboxes to prepare inputs, run analyses, transfer files, verify outputs and manage the authorized instance lifecycle.",
  "version": "1.0.3",
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

沙箱使用固定 CLI 的原生命令，例如 macOS/Linux 的 `"$OMICS_CLI_PATH" sandbox list -o json`，Windows 的 `& $env:OMICS_CLI_PATH sandbox list -o json`。不需要 Python wrapper。Windows 传文件按 references/sandbox-cli.md 使用本机任务工作目录与相对路径，避免盘符冒号被误识别为远端。
<!-- END CONNECTOR BINDING -->

# 组学沙箱分析

使用原生 `omics sandbox` 完成可复现的生命科学分析。根据用户的数据、问题与交付目标编写或复用脚本，在沙箱执行，取回并核验实际产物。保留用户指定的实例、数据范围、方法和输出格式；用户已授权本次云分析时，在该范围内完成创建、执行和收尾，不逐步重复询问。

执行路径遵循“默认 Lambda → 组装自定义/适配 Lambda → 云沙箱 → 本地兜底”的优先级：Lambda 模板不匹配时先考虑输入适配或组装自定义 Lambda；当需要交互式探索、依赖难以固定或 Lambda 通道受阻时切换至云沙箱，若云沙箱亦不可用则由本地环境兜底。已选定沙箱时，同样跟踪用户明确预算及全部准备、失败尝试、计算和传输开销；未指定数值不捏造固定费用、并发数或重试次数。下一步将超出已确认范围时暂停新的有成本执行并提供具体方案；同一故障未修复且没有新证据时继续取证，不盲目重复运行。

## 确定分析与执行环境

先检查 `omics version`、`omics sandbox --help` 和 `omics whoami`。缺少命令时报告需要更新 CLI；认证失效时使用 CLI 的 `omics login` 流程，不索取或读取认证文件。

```sh
omics sandbox templates -o json
omics sandbox list -o json
```

按本次返回的 `TemplateId`、`Tools`、`Available` 和资源规格选择模板；进入沙箱后核对实际工具版本。模板名称不代表固定软件版本或计算能力。优先使用任务指定且状态适合的实例；需要新实例时按本次授权创建。沙箱属于当前登录身份，无需项目、托管环境或 COS 桶配置，也不接收 Lambda 的项目选择参数。

操作前按需读取 [CLI 与文件、执行、生命周期](references/sandbox-cli.md)。保存真实 `SandboxId`，只有 `RUNNING` 才执行命令。创建或恢复响应不明确时先查询状态，不能重复创建来解决等待超时。

## 准备并执行分析

先检查数据格式、规模、样本与特征标识、分组和参考版本，再选择分析方法与依赖。生命科学数据的样本对齐、统计单位、缺失值、单位和结果校验见 [分析与核验](references/analysis-and-verification.md)；读取与本任务有关的部分。

在 `/mnt/workspace` 下使用任务独立目录，放置输入副本、脚本、参数、结果和执行记录。同一身份同地域的多个沙箱共享个人盘，不能仅因切换实例就复用同名输出目录。`sandbox cp` 每次传一个普通文件，目录先打包；上传会覆盖远端同名文件，下载使用新的本地路径。

脚本应显式接收输入、参数和输出目录，保存需要复现的依赖版本与随机种子。先用数据摘要检查字段与规模，复用适用的历史验证；首次大规模或耗时不确定时选择代表性子集试跑，说明固定开销、可能的非线性与估计区间，不为每次已验证分析重复试跑。使用子集时记录选择方式，不能把子集结果写成全量结论。依赖缺失时根据所选模板和任务范围解决，新增依赖尽量使用任务独立环境，记录来源与版本；模板无法满足规模或工具要求时说明具体限制。

```sh
omics sandbox exec --id <SandboxId> --cwd /mnt/workspace/<任务目录> \
  --timeout 20m --client-token <本次执行UUID> -- \
  python analysis.py --input input.csv --output-dir results
```

示例中的 ID、路径、程序及参数须来自本次任务。所有 CLI 选项放在 `--` 前。执行前持久保存请求清单：SandboxId、UUID、实际命令、cwd、env、timeout，以及输入和脚本的 SHA256；执行后保存 stdout、stderr 与退出码，不将凭据写入记录。需要管道或重定向时使用 CLI 支持的单字符串脚本形式，并保护本机 shell 引号。

`exec` 是非交互执行，结束后才返回日志。调用工具的等待时限需覆盖 `--timeout` 及 CLI 收尾时间。提交或等待结果不明确时，只用同一个 token 和完全相同的请求恢复；修改请求或明确重新执行时换新 token。仅剩 ID/token、无法还原原请求时，先查命令摘要和产物；仍不明则报告状态未知，补齐原请求或确认新执行范围，不猜参数重试。非零返回可能来自程序、提交、查询或日志读取，先分类，不因日志读取失败直接重跑。

## 核验并交付

命令退出成功后，读取生成文件并执行与分析方法对应的校验：表格结构和样本数、标识对应、有限数值、统计量范围、图形是否可打开及其标签单位。对用户给定的校验脚本或已有应用 checker，先确认其适用于本次参数和输出契约，再实际运行；校验器不适用或缺依赖时记录未验证原因。

把最终表格、图形、必要的中间结果、脚本和参数通过 `sandbox cp` 下载到新的本地目录，核对文件内容或校验和。交付应包含：

- 实际 `SandboxId`、模板与工具版本、输入来源、执行参数和方法。
- 下载产物的可点击路径、主要结果及其对应数据或图表。
- 执行、下载、内容核验各自的结果，以及失败、未执行或未验证部分。

退出码为 0、文件存在和科学结论成立是不同证据层次；没有完成相应核验时不宣称结果已验证。沙箱结果核验本身不替代 Lambda 应用的发布或平台验收记录。

取回所需结果后按用户授权暂停或关闭本次实例；已有共享任务实例按原约定保留。`stop` 会终止命令并回收系统盘，个人盘保留；退订个人盘不是任务收尾步骤。
