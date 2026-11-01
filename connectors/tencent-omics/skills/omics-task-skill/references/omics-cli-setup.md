# CLI 准备与目标选择

## 安装与能力探测

先执行 `omics version` 和本次命令的 `--help`。未安装时依据 [CLI 发布仓库](https://cnb.cool/tencenthealthcareomics/omics-platform-cli) 选择本机系统/架构的安装包；不自动卸载旧版本或执行未经检查的安装脚本。wrapper 可通过 `OMICS_CLI_PATH` 或 `--cli-path` 指定真实可执行文件。

Lambda 提交需确认 run help 有 `--lambda-file`、`--override-file`、`--project`、`--agent-project`、`--environment`、`--dry-run`；指定北京/上海还需 `--region` 与服务端多地域支持；多步覆盖还需步骤名说明。旧客户端缺少任一所需能力时说明版本不兼容，不拼装未知 flags。

## 登录

执行 `omics whoami` 并检查实际返回的身份或错误内容；仅 exit 0 不足以证明已登录。登录缺失时使用当前 help 支持的 `omics login` 完成用户浏览器授权；无图形主机按 CLI 的真实授权方式操作，不复制认证文件或输出凭据。登录后的业务错误不能通过无限重复登录来掩盖。

## 项目和环境

`omics config show -o json` 可读取已有偏好，但字段不全不等于 Lambda 不可用。新版项目优先级是本次 `--project/-p` > 保存项目 > 已认证团队的智能体项目。`--agent-project` 强制团队默认，和显式项目互斥。默认团队资源在查询/预览阶段不创建。

执行环境：新版 run 可用 `--region ap-guangzhou`、`ap-beijing` 或 `ap-shanghai` 选择地域；环境和地域都省略时默认广州。显式 `--environment` 使用实际地域；同时传入地域不一致时直接报错。NF/WDL 只选择该地域已有、就绪且有 CFS 的适用环境；Lambda 正式提交可复用或创建该地域的组织默认 CLI 环境。各地域默认环境独立，团队共用同一个智能体项目。保存 EnvironmentId 或 region 不决定新版运行位置；`--agent-project` 也不意味着清掉环境选择。

为一次运行优先使用临时参数。只有用户要求保存偏好时才 `config set`，从实际 `list region/project/env/cos-bucket` 结果核对参数；该旧命令可能要求完整四项配置。不能静默选第一个项目，或写入固定试用环境/桶。

CLI `4be200e` 的 `cos upload/ls/download/quota` 使用本次显式环境；未指定环境和桶时解析广州的组织默认 CLI 环境及默认盘；北京/上海使用实际 `--environment`，忽略 config 中历史环境/桶，不回写 config。保存项目仍参与权限检查，坏项目不静默回退。普通 COS 校验所选环境关联，显式 AgentBucket 由服务端解析真实归属，个人盘不传环境。仅显式环境且未指定桶时，使用该环境默认盘或唯一有效关联桶；不能自动取多个桶中的第一个。正式上传可准备默认资源，上传 `--dry-run` 和所有读取不创建资源。

上传成功后保存单目标 `TargetCOSPath`（文件或目录根）、多目标 `Targets[]`、逐文件 `Results[].COSPath` 和实际存储上下文；预览地址不代表对象已存在。后续提交显式复用本次环境，NF/WDL 仍须选择已有且有 CFS 的适用环境。`list cos-bucket/volume` 同样在省略环境时只读查询组织默认 CLI 环境。COS YAML 来源、定义管理和传统 Notebook 按各自 help 处理，不能把所有命令的目标规则混用。

## 失败处理

缺少权限、配额、默认资源或执行环境时报告服务端实际原因。Lambda 预览的 `NOT_CREATED` / `Ready=false` 表示资源尚未就绪；已授权正式提交可按服务端流程创建并等待。查询失败保持未查明，不改投其他项目。所有交付中区分未执行、本地参数检查、服务端预览与真实运行成功。
