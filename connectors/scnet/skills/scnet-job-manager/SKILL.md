---
name: scnet-job-manager
description: SCNet作业管理，包含用户队列的查询，提交作业，查询作业详情，监控作业，取消作业，上传文件到SCNet平台文件系统等功能。当用户提及队列与作业相关，先加载 scnet-main 并按其集群前置规则决定是否进入本技能。
---

# scnet-job-manager | SCNet作业管理
本技能用于SCNet平台的作业管理，包含用户队列的查询，提交作业，查询作业详情，监控作业，取消作业，上传文件等功能。


## 何时调用该技能
需要查询用户队列（选择队列），需要查询某个作业(job)的详细，需要监控作业状态时，先加载同一连接器的主 Skill（`../scnet-main/SKILL.md`，本轮已加载则沿用），按其规则进入本技能。
执行下面的认证检查或业务命令前，先检查主 Skill 的空资源结论；本轮已确认没有集群且结论尚未解除时，返回主 Skill 的空资源引导，不运行认证检查、`clusters` 命令或其他集群查询来再次确认。没有这个结论时，按主 Skill 的集群前置规则和本技能原有步骤执行。其他会话记忆中的账号、团队、集群、地址或脚本不能替代本轮参数和当前连接结果。

## 技能依赖

执行需要认证的命令前，优先使用本地环境变量中的 SCNET_AK、SCNET_SK、SCNET_USER。任意一项缺失、为空或仅含空白时，由 scripts/run.py 内部调用普通函数 get_skill_auth() 获取认证信息，不用返回给前端。该函数读取本机 WorkBuddy 保存的 access token，调用 userinfo 接口，将返回的 ak、sk、userName 映射到当前脚本进程的 SCNET_AK、SCNET_SK、SCNET_USER，并创建原有 SCNetJobClient。它不是 MCP 工具，无需额外调用 MCP；认证失败时停止后续业务并说明实际错误。

可通过可选环境变量 `SCNET_USERINFO_URL` 指定 `get_skill_auth()` 请求的 userinfo 完整接口地址，例如 `http://10.0.33.193/acx/user/v1/oauth/userinfo`。地址须为 HTTP(S)，不包含用户名、密码、查询参数或 fragment，不要填写 `?access_token=`，token 由脚本自动附加。未设置时使用 `SCNET_BASE_URL`拼接 `/acx/user/v1/oauth/userinfo`。该变量仅用于接口认证分支，不影响原有三个环境变量的完整性判断，也不会自动切换业务接口地址。

命令入口相对本文件固定为 `scripts/run.py`，直接按下文命令调用。

`./scripts`: 与`SKILL.md`同层级，包含所有脚本
`./scripts/run.py`: 命令执行入口

无需查阅、搜索`scripts`目录中技能的具体实现，也不得通过读取源码来诊断执行错误。只能按照本技能文档中提供的命令和参数调用能力。

## 技能要求
执行此技能的能力时，需要以下认证参数：
access_key: 用户的SCNet平台密钥，用于身份验证，对应环境变量`SCNET_AK`
secret_key: 用户的SCNet平台密钥，用于身份验证，对应环境变量`SCNET_SK`
user: 用户的SCNet平台用户名，用于身份验证，对应环境变量`SCNET_USER`
以上参数用于脚本认证，AK、SK、access token 不输出到前端、对话或记忆。

环境变量检查、认证来源选择、读取本地凭据和 userinfo 换取凭据均静默执行，不在执行前的说明、进度消息或最终回复中播报。不要输出“环境变量未配置，脚本会自动走本机认证”等内部实现说明。需要说明进度时，只描述用户的业务目标，例如“正在查询你的作业”或“正在查询可用集群”；执行完成后展示实际结果。认证失败或需要用户操作时，简要说明实际失败原因和必要的下一步，不暴露密钥，也不把认证失败解释为没有作业或资源；用户明确询问认证原理或排障细节时，再按问题解释。

以上三个参数分别对应环境变量中的SCNET_AK,SCNET_SK,SCNET_USER。你先在当前本地shell中检查这三个值；三项都完整时，按下方原有命令通过 --access-key、--secret-key、--user 传入对应环境变量的值。任意一项缺失、为空或仅含空白时，将示例中的 --access-key access_key --secret-key secret_key --user user 整组省略，保留其他业务参数，由脚本调用 get_skill_auth()，不再询问用户密钥。不得传入占位符或混用部分环境变量凭据与接口凭据。完整的环境变量凭据被拒绝时，按实际错误处理，不自动切换认证来源。注意，环境变量直接在当前shell中检查，不要调用工具在远端获取；平台用户名使用 SCNET_USER，接口认证时由 userName 映射。


## 访问密钥申请与继续

认证失败时暂停业务，不进入下方各功能的通用失败保底；按以下规则处理。

1. 脚本返回 `ACCESS_KEYS_REQUIRED` 时，由本 Skill 展示申请引导；其他认证错误按实际原因处理，不引导为申请密钥。

   > 暂未获取到访问密钥，请前往 [访问密钥管理](https://www.scnet.cn/ui/console/index.html?open_in_browser=true#/personal/auth-manage) 注册并申请 AK/SK。完成后请回到 WorkBuddy，在当前对话中说“继续”，我会重新检查并继续之前的任务。

2. 在当前会话保留原任务、已确认参数、执行进度及已有 job_id，不保存或索要 AK/SK、token。上下文缺失时只询问缺少的业务参数。
3. 用户说“继续”“申请好了”或“开通了”后，先核对执行进度：已完成步骤不重做，已有 job_id 则查询或监控；提交结果不明则先核实，无法确认时告知用户，不因“继续”而重新提交。
4. 沿用原参数执行因认证失败而未执行的步骤，重新认证成功后继续。原 OAuth 分支仍省略整组认证参数，让脚本重新读取 WorkBuddy token 并请求 userinfo，以实际结果为准；仍缺密钥则重复申请引导并等待。

## 技能术语
集群（cluster）: SCNet平台上的计算集群，平台包含多个集群，每个集群的标识是集群名称（clusterName，例如 华东一区【昆山】）与集群ID（clusterID，例如 11250）。集群ID与集群名称绑定，技能内部调用时，通过集群ID流转，但输出给用户必须调整为集群名称。

队列（queue\partition）: 每个集群中包含多个队列，用户可以在该队列提交作业。队列的概念也被称之为partition。在这个技能中，我们用queue和队列来表示partition。队列包含多个节点与核心，每个队列都有处于空闲状态的节点/核心。

作业（job）：用户提交到队列中的Slurm计算任务，每个作业都有一个唯一的作业ID。作业将运行在指定集群的某个队列上。注意，所有作业相关的操作都需要指定集群ID。你需要从上下文中推断所选择的集群ID，若未指定，则需要询问。

## 技能功能

### 查询用户集群与集群info
支持用户查询SCNet（超算互联网）平台上的集群信息，以及集群名与clusterID的对应关系。
```bash
set PYTHONIOENCODING=utf-8 && python3 scripts/run.py clusters --access-key access_key --secret-key secret_key --user user
```
可以用该功能查询用户的可用集群，以及每个集群的名称与ID。
如果命令返回非零退出码或输出`"success": false`，表示集群查询流程失败，不得将其解释为用户没有可用集群；应向用户说明错误阶段与错误信息，并尝试采用工具`list_remote_shell_clusters`。


### 查询用户队列
支持用户查询SCNet（超算互联网）平台上的队列，并在确认没有任何可用队列时提供资源推荐选项。必须按照以下顺序执行。

#### 1. 确认要查询的集群
如果当前会话已经确定工作集群，则该步跳过，使用该集群的cluster_id执行后续流程。若没有，则参考查询用户集群的步骤，确认目标集群id。

#### 2. 查询目标集群的队列

确定 `cluster_id` 后执行：

```bash
set PYTHONIOENCODING=utf-8 && python3 scripts/run.py queues --access-key access_key --secret-key secret_key --user user --cluster-id cluster_id
```

队列查询只能归入以下三个互斥结果之一：

##### 查询成功且存在队列

- 如果当前工具存在 `show_resource_cards`，必须调用该工具展示所有可选队列；不得遗漏查询到的队列，同名队列可以合并。
- 如果没有 `show_resource_cards`，使用 Markdown 展示所有可选队列。
- 任何时刻都禁止自行为用户选择队列，即使只查询到一个队列，也要交由用户选择。队列涉及费用，必须由用户决定。
- 只要查询到了队列，即使只有一个队列，也应该进入展示流程，不要再用`sinfo`命令做补充。
- 等待用户明确选择队列后，才能进入提交作业等后续流程。

##### 查询成功但没有队列

只有命令明确表示查询成功且队列列表为空，才能认定当前集群没有可用队列，并进入此分支。

1. 使用 `scnet_remote_shell_execute` 工具执行 `sinfo` 命令查询，若查询到队列，按照查询成功的分支进行处理。
2. 如果 `sinfo` 同样成功但没有队列，激活订单查询 MCP，读取环境变量 `ORDER_ID` 的值，将该值作为 `orderId` 参数调用工具 `scnet_order_query_order_status`。不得重新向用户索取或自行编造订单 ID。
3. 如果订单状态在配置中，则提醒用户免费队列配置中，请等待5分钟后再询问，并结束当前会话；若是其他状态，则进行两个动作：
    3.1 提示用户免费队列开通失败，请寻求管理员的帮助
    3.2 向用户推荐其他计算资源，提示用户可点击开通。执行以下命令，查询该集群的推荐资源：

    ```bash
    set PYTHONIOENCODING=utf-8 && python3 scripts/run.py recommend-resources --keywords keyWords --region cluster_id
    ```
    `--keywords` 为可选参数，根据用户的计算任务提取关键词，例如VASP等；无法确定时省略。`--region` 必须使用当前已确认的集群 ID。

   调用工具`show_recommand_resource_cards`展示推荐资源（包含更多资源的链接），若该工具不可加载或不存在，则用markdown格式展示。

4. 如果上述步骤有工具不可用，则跳过该步。已提示免费队列配置中，用户再请求的情况下，或是用户自己开通资源的情况下，重新执行队列查询逻辑。

##### 执行失败

命令返回非零退出码、输出 `"success": false`、响应无法解析或请求异常，均属于执行失败。

1. 记录并识别失败阶段、退出状态和错误信息，检查`cluster_id` 是否完整、是否与上下文一致。
2. 如果 `scnet_remote_shell_execute` 工具可用，使用 `sinfo` 作为队列查询的保底逻辑。
3. 基于`sinfo`的结果，执行上述链路的结果。


### 提交作业
支持用户提交作业到SCNet（超算互联网）平台。
目前仅支持用户提供工作目录workdir，与工作目录下的slurm脚本文件名filename后进行提交。注意需要指明脚本文件要在工作目录下。
支持两种提交方式：
1. 若scnet远程命令工具`scnet_remote_shell_execute`可用，那么优先使用该工具，使用命令`sbatch xx.slurm`远程提交提交作业，并设置工具的超时时间参数`timeoutSeconds`为90s，这是最推荐的方式，不会带来额外负担，应该优先尝试。

2. 若该工具不可以用，则采用以下方式：根据上下文判断用户采用的应用，如果指明了应用，例如VASP、QE等，则需要指定应用名称appname，否则该参数可以不携带。特别的，多个软件的复杂计算场景下（例如生信分析），appname可以是miniconda。

```bash
set PYTHONIOENCODING=utf-8 && python3 scripts/run.py submit-job --access-key access_key --secret-key secret_key --user user --cluster-id cluster_id --workdir workdir --filename filename --appname appname
```

任意一种提交成功时，返回data中包含作业的job_id，你需要将这个ID记住，并告知用户。
**注意**：如果方式1提交时，返回提交超时，则此时不能认为作业提交失败，也不要立刻重试提交，避免出现作业重复提交的情况。应以30s为间隔，每30s使用工具`scnet_remote_shell_execute`调用命令`squeue`查看有无作业提交，若3次均未能查到，则重试提交。

### 查询作业详情
支持用户查询SCNet（超算互联网）平台上某个作业的详情信息。
调用前，确保已经知晓作业的ID与所提交集群的ID。

```bash
set PYTHONIOENCODING=utf-8 && python3 scripts/run.py job-info --access-key access_key --secret-key secret_key --user user --cluster-id cluster_id --job-id job_id
```

返回结果中会包含这些核心字段：
- `jobStatus`  作业状态
- `jobName`   作业名称
- `jobId`     作业ID
- `queue`     作业提交到的队列
- `duration`  作业运行时间


### 监控作业状态
支持用户监控SCNet（超算互联网）平台上某个作业的状态。
调用前，确保已经知晓作业的ID与所提交集群的ID。

Slurm作业监控必须使用本技能的`monitor-job`能力或`trigger_job_monitor_handoff`工具。这两者是唯一允许的作业监控方法。其他任何监控方式都禁止使用，包括`squeue`、`sacct`或类似调度器shell命令。`squeue`与`sacct`只能查看作业状态快照，不能进行监控，不得用它们替代作业监控。

```bash
set PYTHONIOENCODING=utf-8 && python3 scripts/run.py monitor-job --access-key access_key --secret-key secret_key --user user --cluster-id cluster_id --job-id job_id
```
优先使用该命令进行监控。如果该命令报错或不可用，且智能体存在工具`trigger_job_monitor_handoff`，则必须调用`trigger_job_monitor_handoff`工具进行监控。


### 取消作业
支持用户取消SCNet（超算互联网）平台上某个作业。
调用前，确保已经知晓作业的ID与所提交集群的ID。

```bash
set PYTHONIOENCODING=utf-8 && python3 scripts/run.py cancel-job --access-key access_key --secret-key secret_key --user user --cluster-id cluster_id --job-id job_id
```

### 上传文件到SCNet（超算互联网）平台

支持用户上传本地文件到SCNet（超算互联网）平台的指定路径。**注意，上传文件前，先确认文件是否已经存在于集群上，如果是，直接在集群上操作即可，不要重复上传。**
调用前，确保已经知晓要上传的目标平台路径remote_path与所提交集群的ID。注意，local-file参数需要指定到具体文件，但remote-path参数只能指定到目录，一般是上下文中的SCNet工作目录。cover参数有cover与uncover两个选项，表示是否覆盖文件，默认是cover。

```bash
set PYTHONIOENCODING=utf-8 && python3 scripts/run.py upload-file --access-key access_key --secret-key secret_key --user user --cluster-id cluster_id --local-file local_file --remote-path remote_path --cover cover
```

## 注意事项
调用该技能时，确保编码采用utf-8，否则可能会出现乱码，导致文本解析错误。
如果中文文本返回乱码，需要检查编码是否采用utf-8，并指定编码运行python命令。

若命令执行失败，不得转而查看 `scripts` 内部实现。必须按照对应功能记录的执行失败流程处理：优先使用文档明确允许的保底能力，保留真实错误语义；若仍不能完成，则向用户说明失败阶段、已尝试的保底方式和所需协助。不得把执行失败解释为查询结果为空，也不得伪造成功结果。
