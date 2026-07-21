---
name: anydev
description: 使用 anydev(云研发) 的 CLI 命令为用户查询模板、查询仓库、创建环境、查询状态、查看日志、开启 SSH、调整云研发环境配置、锁定环境和部署项目到云研发环境。只要用户提到 anydev 云研发、创建环境、查模板、选模板、选仓库、查状态、查日志、开启 SSH、部署、发布、调整云研发环境配置、锁定环境、上传文件到环境，都应该使用这个 skill。
version: 0.9.0
---

# anydev

**作用**：使用 anydev(云研发) 的 CLI 命令为用户查询模板、查询仓库、创建环境、查询状态、查看日志、开启 SSH、调整云研发环境配置、锁定环境和部署项目到云研发环境。只要用户提到 anydev 云研发、创建环境、查模板、选模板、选仓库、查状态、查日志、开启 SSH、部署、发布调整、云研发环境配置、锁定环境、上传文件到环境，都应该使用这个 skill。

## 1. 概述与核心规则

### 1.1 何时使用
下面这些场景直接使用这个 skill：
- 用户说"帮我创建环境"
- 用户给出 `templateUid` 或模板分享链接，希望创建环境
- 用户想先查询某个模板详情、确认模板配置是否可创建
- 用户希望指定代码仓库或分支创建环境
- 用户想查询环境创建状态或失败日志
- 用户明确要求开启云研发SSH
- 用户说"部署到环境"、"发布项目"、"上传文件到环境"
- 用户想在远端环境执行命令
- 用户想修改环境名称
- 用户想调整云研发配置
- 用户想锁定环境

### 1.2 固定规则
始终遵守这些规则：
- [重要]any命令需要使用anydev作为替换，如果list工具没找到需要使用ls命令去真正的查找,描述信息在version.md,后续的所有any命令需要使用anydev,后续的any命令需要替换成对应的命令,windows需要使用powershell执行命令，对于windows使用powershell执行命令的时候， -d 里面的双引号需要用反斜线 et. -d '{\"templateUid\":\"6\"}'
- ssh前需要调用any dev env ssh -d '{"envId":"env-xxx"}',并且ssh链接需要使用域名链接,端口默认为36000,如果尝试ssh链接失败,需要提示用户去ioa进行一次链接,如果ioa链接失败,则需要进行诊断修复,或者联系o2000进行排查
- [重要]列表查询会发生输出超长而发生截断,禁止直接输出截断的环境列表,必需要提前做好关键字段的提取,输出的格式可以查询doc/api.md
- 鉴权统一通过 `any login` 完成
- 业务动作统一通过 `any dev ...` 命令执行，参数通过 `-d` 传入 JSON
- 用户要求查看指定模板详情时，必须执行 `any dev env template query`
- 查询模板详情后，优先整理核心字段给用户，不要直接整段转储原始响应
- 只允许创建 `serverType=cvm` 的 CPU 环境
- 用户指定仓库时，必须先通过 `any dev git projects` 校验
- 用户指定分支时，必须先通过 `any dev git branches` 校验
- 创建环境只负责创建，环境详情统一通过 `any dev env status` 获取
- 环境状态轮询间隔固定为 10 秒
- [重要] **调整 CPU/内存会导致环境重启**，执行 `any dev env adjust exec` 前必须明确告知用户以下信息并等待用户确认后才能执行：
  1. 调整 CPU/内存会导致环境重启，重启期间环境不可用
  2. 正在运行的任务和服务会被中断，仅 `/data` 和 `/root` 目录数据会保留
  3. 未经用户确认，禁止执行 adjust exec 命令
- [重要] **部署完成后应尝试锁定环境**：已成功部署但未锁定的环境需要执行 `any dev env convert` 尝试锁定。判断环境是否锁定根据 `any dev env list` 返回值中的 `resourceType` 字段：`1` 为已锁定，`0` 为未锁定。锁定失败时需提示用户配额不足信息（见 3.9 锁定环境流程）
- 出现无法解决的问题提示用户：`如您有任何疑问，可随时联系 O2000 技术支持`

### 1.3 不要做的事
- 不要在用户要求查模板时跳过 `any dev env template query` 直接猜模板内容
- 不要对 `gpu` 或 `vm` 模板执行创建环境
- 不要在仓库未校验前直接执行创建环境
- 不要在无法可靠提取 `templateUid` 时擅自猜测
- 不要虚构不存在的 CLI 命令或返回字段
- 数据被截断需要重新获取执行命令获取,通过管道方式进行关键信息提取,禁止直接输出截断的列表


## 2. 鉴权

### 2.1 前置条件
执行 `any dev` 相关命令前，默认要求用户已完成 `any login`。

### 2.2 鉴权流程
1. 先执行 `any login`，根据返回结果判断是否已授权
2. 如果未授权，引导用户完成 `any login` 授权流程
3. 确认授权成功后，再执行后续的 `any dev *` 等命令



## 3. 执行流程与规范

### 3.1 最少收集信息
创建环境只需要这三类输入：

1. **模板**（优先级固定）
   - 用户直接给出 `templateUid`
   - 用户给出模板分享链接，并能稳定提取 `templateUid`
   - 未指定时，执行 `any dev env template recommend -d '{}'`，默认取第一个 `serverType=cvm` 的推荐模板
   - *如果不能稳定提取 `templateUid`，不要猜，直接要求补充。*

2. **仓库** (`gitUrl` 可选)
   - 没提仓库，不传 `gitUrl`
   - 提了仓库，先执行 `any dev git projects -d '{"page":1,"perPage":20,"search":""}'` 校验
   - 仓库不在列表里，告知"不在可选仓库列表中"

3. **分支** (`branch` 可选)
   - 没提分支，不传 `branch`
   - 提了分支，先执行 `any dev git branches -d '{"gitUrl":"...","page":1,"perPage":20}'` 校验
   - 分支不存在直接告诉用户

4. **环境名称** (`envName` 可选)
   - 用户指定了环境名称，创建时传入 `envName`
   - 未指定则不传，使用默认名称

单独查询模板详情时：
- 已知 `templateUid`：直接执行 `any dev env template query -d '{"templateUid":"..."}'`
- 只有模板分享链接：先稳定提取 `templateUid`，再执行查询
- 不能稳定提取 `templateUid`：直接要求补充，不要猜
- 如果查询结果显示 `serverType!=cvm`，要明确告知"CLI 环境创建仅支持 CPU 模板"

### 3.2 标准执行流程
**流程 A：只说"帮我创建环境"**
1. 确认 `any login` 已完成
2. 执行 `any dev env template recommend -d '{}'` 取第一个 `serverType=cvm` 的推荐模板
3. 执行 `any dev env create -d '{"templateUid":"..."}'`
4. 取返回中的 `instanceId`
5. 每 10 秒执行 `any dev env status -d '{"instanceId":"..."}'`
6. 成功结束，失败执行 `any dev env logs -d '{"envId":"...","offset":0,"length":200}'`

**流程 B：指定模板，不指定仓库**
1. 确认 `any login` 已完成
2. 确定 `templateUid`
3. 执行 `any dev env create -d '{"templateUid":"..."}'` -> 取 `instanceId`
4. 每 10 秒轮询 `any dev env status` -> 失败查 logs

**流程 C：指定模板和仓库(及分支)**
1. 确认 `any login` 已完成
2. 确定 `templateUid`
3. 执行 `any dev git projects -d '{...}'` 校验仓库
4. 如果有分支，执行 `any dev git branches -d '{...}'` 校验分支
5. 执行 `any dev env create -d '{"templateUid":"...","gitUrl":"...","branch":"..."}'` -> 取 `instanceId`
6. 每 10 秒轮询 `any dev env status` -> 失败查 logs

**流程 D：只查询模板详情**
1. 确认 `any login` 已完成
2. 确定 `templateUid`
3. 执行 `any dev env template query -d '{"templateUid":"..."}'`
4. 提炼模板核心字段并反馈给用户
5. 如果用户下一步要创建环境，再继续走创建流程

### 3.3 模板查询结果处理
执行 `any dev env template query` 后，优先关注这些字段：
- `templateUid`：模板唯一标识
- `templateName`：模板名称
- `serverType`：模板类型，重点区分 `cvm`/`gpu`/`vm`
- `templateType`：系统模板或个人模板等
- `imageUrl`：镜像
- `startCommand`：启动命令
- `languages`：语言版本
- `vsCodePlugins`：推荐插件
- 预置仓库与分支
- 预置区域
- 预置机型/配置
- 模板分享范围

模板查询后的判断规则：
1. 如果模板为空，直接告知模板不存在或当前用户无权限
2. 如果 `serverType!=cvm`，明确告知该模板可查看，但不能通过 CLI 创建环境
3. 如果存在预置仓库，不要自动替用户覆盖；只有用户明确指定仓库时才做仓库校验
4. 如果用户接着要创建环境，继续复用本次查询得到的 `templateUid`，不要重复猜测模板
5. 如果用户只是想了解模板，优先输出摘要，不要展开全部原始字段
6. 如果用户没有指定模板且推荐列表里没有 `serverType=cvm` 的模板，直接告知当前没有可用的 CPU 模板

### 3.4 部署流程

部署是指将用户的项目构建、打包并上传到云研发环境，然后在远端启动服务。

**流程 E：部署项目到环境**

#### 步骤 1：确定目标环境
- 如果用户指定了环境 ID，直接使用
- 如果用户没有指定，执行 `any dev env list -d '{}'` 查询用户的环境列表，让用户选择，或按流程 A/B/C 创建新环境

#### 步骤 2：检查 agent 状态
1. 执行 `any dev env agent status -e <envId>` 查询 agent 状态
2. 如果 `agentStatus` 为 `running`，进入步骤 3
3. 如果 `agentStatus` 不是 `running`，执行 `any dev env agent init -e <envId>` 初始化
4. 初始化后每 10 秒执行 `any dev env agent status -e <envId>` 轮询，直到 `agentStatus` 变为 `running`

#### 步骤 3：构建项目
- 根据项目类型执行对应的构建命令（如 `npm run build`、`go build`、`mvn package` 等）
- 构建产物打包为压缩包（如 `tar -czf deploy.tar.gz -C <构建产物目录> .`）

#### 步骤 4：上传压缩包
- 执行 `any dev env agent upload -e <envId> <本地压缩包路径> <远端目标文件路径>`
- `<dest>` 必须是完整的文件路径（如 `/data/workspace/deploy.tar.gz`），不能以 `/` 结尾

#### 步骤 5：远端解压并启动服务
- 执行解压命令（含 `-` 开头参数必须用 `--` 分隔）：
  ```bash
  any dev env agent exec -e <envId> -- tar -xzf /data/workspace/deploy.tar.gz -C /data/workspace/app
  ```
- 执行启动命令（必须使用脚本方式启动，因为 exec 无法直接传递重定向、引号等 shell 特殊字符）：
  1. **在本地创建启动脚本**，然后通过 `upload` 上传到远端：
     ```bash
     # 本地创建启动脚本
     cat > /tmp/start.sh << 'EOF'
     #!/bin/bash
     nohup /usr/bin/python3 /data/workspace/app/main.py > /data/workspace/app/nohup.out 2>&1 &
     EOF

     # 上传脚本到远端
     any dev env agent upload -e <envId> /tmp/start.sh /data/workspace/app/start.sh
     ```
     > **注意**：不要使用 `bash -c "echo ..."` 方式写入脚本，因为 exec 的引号会被本地 shell 吃掉，导致远端实际写入内容为空。
  2. 执行脚本启动服务：
     ```bash
     any dev env agent exec -e <envId> -- bash /data/workspace/app/start.sh
     ```
- 启动脚本示例（写到 `/data/workspace/app/start.sh`）：
  - Node.js：`nohup /opt/codev/nodejs/bin/node /data/workspace/app/index.js > /data/workspace/app/nohup.out 2>&1 &`
  - Go：`nohup /data/workspace/app/server > /data/workspace/app/nohup.out 2>&1 &`
  - Python：`nohup /usr/bin/python3 /data/workspace/app/main.py > /data/workspace/app/nohup.out 2>&1 &`
- **重要**：远端环境中运行时依赖可能未安装或不在默认 PATH 中，需先确认是否可用，不可用则先安装：
  - **node**：检查 `/opt/codev/nodejs/bin/node` 是否存在；若不存在，通过 `source /etc/profile` 后使用 `node`，或执行安装命令（如 `curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && apt-get install -y nodejs`）
  - **python3**：检查 `/usr/bin/python3` 是否存在；若不存在，执行安装命令（如 `apt-get update && apt-get install -y python3`）
  - **go**：检查 `/usr/local/go/bin/go` 是否存在；若不存在，执行安装命令（如下载官方二进制包解压到 `/usr/local/go`）
  - **其他依赖**：同理，先用 `which <命令>` 或检查常见路径确认是否存在，不存在则先安装

#### 步骤 6：验证部署结果
- 可通过 `any dev env agent exec -e <envId> ps aux` 查看进程是否启动
- 可通过 `any dev env agent exec -e <envId> cat /data/workspace/app/nohup.out` 查看启动日志

#### 步骤 7：锁定环境
部署成功后，应检查环境是否已锁定，未锁定则尝试锁定：
1. 执行 `any dev env list -d '{}'` 查询环境列表，通过 `resourceType` 字段判断锁定状态（`1` 为已锁定，`0` 为未锁定）
2. 如果环境未锁定（`resourceType=0`），执行 `any dev env convert -d '{"envId":"evnIns-xxx"}'` 尝试锁定
3. 锁定成功则提示用户环境已锁定
4. 锁定失败则提示：⚠️ 您的环境锁定配额不足，环境未锁定。若连续 7 天无连接，环境将自动休眠。您可解锁无需锁定的环境以释放锁定配额，或者联系O2000增加锁定配额。

### 3.5 部署注意事项
- exec 执行的启动命令必须使用 `nohup` 和 `&` 后台运行，否则 exec 会阻塞直到进程退出
- upload 的目标路径必须是完整文件路径，不能以 `/` 结尾，不能是已存在的目录
- 当远端命令包含 `-` 开头的参数时，需用 `--` 分隔 CLI flag 和远端命令（如 `exec -e xxx -- ls -la /data`）
- 若目标目录不存在，agent 会自动创建；若目标文件已存在则覆盖
- **[重要] exec 命令的参数传递限制**：
  - exec 传入的命令会经过本地 shell 和远端 shell 两层解析，中间引号、转义等特殊字符无法可靠传递
  - **引号会被本地 shell 吃掉**，导致 `bash -c "echo hello"` 远端实际执行时引号丢失（输出为空）
  - **重定向 `>`、管道 `|`、变量 `$`、后台 `&`** 等特殊字符会被本地或远端 shell 错误解析
  - **正确做法**：对于包含引号、重定向、管道、变量、nohup 等复杂命令，必须在本地创建脚本文件后通过 `upload` 上传到远端，再执行脚本
  - **不要使用 `bash -c "echo ... > file"` 写入脚本**，这种方式引号会被吃掉，实际写入内容为空
  - 远端环境中运行时依赖可能未安装或不在默认 PATH 中，需先确认是否可用，不可用则先安装（见步骤 5 中的说明）

### 3.6 失败与状态处理
**状态轮询规则**：
- `running`：创建成功，停止轮询
- `failed`：停止轮询，立刻查日志
- `deleted`：停止轮询，并告知环境已不存在
- 未进入终态：继续轮询

**失败处理规则**：
1. 输出 `any dev env status` 的核心字段
2. 执行 `any dev env logs`
3. 优先总结最后一段日志
4. 如果是仓库权限、分支不存在、工蜂授权缺失，明确指出位置

**SSH 规则**：
- 只有用户明确提出"开启 SSH""连接环境""打开本地 IDE"时，才执行 `any dev env ssh`。
- 如果用户只是创建环境，不主动做 SSH 操作。
- 如果用户无法连接，需要提醒用户通过 IOA 点击 IDE 链接环境；仅支持有 IOA 的环境，或者用户自行配置公钥。

### 3.7 回复格式
**查询模板详情时**按这个结构输出：
1. 模板 UID
2. 模板名称
3. `serverType`
4. `templateType`
5. 镜像 / 启动命令
6. 是否带预置仓库或预置分支
7. 是否适合继续用 CLI 创建
8. 如果不适合创建，给出原因

**创建环境或查状态时**按这个结构输出：
1. 模板来源
2. 是否使用仓库
3. 是否做了仓库或分支校验
4. 实际调用的命令顺序
5. 是否已完成 `any login`
6. 创建结果
7. 当前状态
8. 如果失败，补日志摘要

### 3.8 锁定环境流程

锁定环境可防止环境因长期无连接而自动休眠。

**流程 A：用户主动要求锁定环境**

1. 确认 `any login` 已完成
2. 确定目标环境的 `envId`
3. 执行 `any dev env convert -d '{"envId":"evnIns-xxx"}'` 锁定环境
4. 返回 `code=200` 表示锁定成功，提示用户环境已锁定
5. 锁定失败则提示：⚠️ 您的环境锁定配额不足，环境未锁定。若连续 7 天无连接，环境将自动休眠。您可解锁无需锁定的环境以释放锁定配额，或者联系O2000增加锁定配额。

**流程 B：部署后自动检查并锁定**

部署流程（3.4 步骤 7）中已包含，部署成功后自动检查环境锁定状态，未锁定则尝试锁定。

**判断环境是否已锁定**：
- 执行 `any dev env list -d '{}'` 查询环境列表
- 返回值中 `resourceType` 字段：`1` 为已锁定，`0` 为未锁定

### 3.9 调整配置流程

调整配置是指查询云研发环境的资源配置，并根据需要调整 CPU/内存或扩容磁盘。

**流程 A：查询当前环境配置**

1. 执行 `any dev env status -d '{"instanceId":"evnIns-xxx"}'` 查询当前环境配置（名称/类型/域名/CPU/内存/磁盘）
2. 执行 `any dev env adjust range -d '{"envId":"evnIns-xxx"}'` 判断是否支持缩扩容，不支持则输出原因并结束
3. 展示可调范围表（CPU/内存/磁盘的当前值/最小值/最大值）+ 配额剩余表
4. 询问用户是否需要调整：①调整CPU/内存（流程B）②扩容磁盘（流程C）③不需要

**流程 B：调整 CPU / 内存**

1. 执行 `any dev env adjust range -d '{"envId":"evnIns-xxx"}'` 查询可调范围和配额，不支持则输出原因并结束
2. 校验目标值（步长1核/1G，不超最大值；模板绑平台授权则引导去 IOA，流程结束）
3. 展示变更对比表 + ⚠️ **重启警告（必须明确告知用户，必须等用户确认后才能继续）**：
   - **调整 CPU/内存会导致环境重启，重启期间环境不可用**
   - **正在运行的任务和服务会被中断，仅 `/data` 和 `/root` 目录数据会保留**
   - 必须使用 `ask_followup_question` 或明确等待用户回复"确认"后，才能继续执行下一步
   - 如果用户未确认，不得执行 adjust exec 命令
4. 用户确认后，执行 `any dev env adjust exec -d '{"envId":"evnIns-xxx","cvmConfig":{"cpu":32000,"memory":64000}}'`，每 10 秒轮询 `any dev env status -d '{"instanceId":"evnIns-xxx"}'` 直到终态
5. 输出结果：成功→变更表+配额更新 / 失败→`any dev env logs -d '{"envId":"evnIns-xxx","offset":0,"length":200}'`查日志+建议 / 取消→配置不变

**流程 C：扩容磁盘**

1. 执行 `any dev env adjust range -d '{"envId":"evnIns-xxx"}'` 查询磁盘可扩容范围（当前/最大/步长10G），不支持则再执行 `any dev env disk resize check -d '{"envId":"evnIns-xxx"}'` 获取磁盘专项范围
2. 校验目标值（必须 > 当前值、≤ 最大值、10G 步长）
3. 展示变更对比表 + 无需重启提示，用户确认后继续
4. 执行 `any dev env disk resize exec -d '{"envId":"evnIns-xxx","size":110}'`，每 10 秒轮询 `any dev env status -d '{"instanceId":"evnIns-xxx"}'` 检查磁盘值变化
5. 输出结果：成功→扩容完成 / 失败→原因+建议 / 取消→配置不变




## 4. 命令参考

当前主要使用这些命令,只能使用any dev：
对于windwos -d 的json格式需要使用反斜线，例如：-d '{\"templateUid\":\"6\"}'

**1. 查询推荐模板**
```bash
any dev env template recommend -d '{}'
```

**2. 查询模板详情**
```bash
any dev env template query -d '{"templateUid":"6"}'
```

**3. 查询可选仓库**
```bash
any dev git projects -d '{"page":1,"perPage":20,"search":""}'
```

**4. 查询仓库分支**
```bash
any dev git branches -d '{"gitUrl":"https://git.woa.com/example/project.git","page":1,"perPage":20}'
```

**5. 创建环境**
可在创建时通过 `envName` 指定环境名称，不指定则使用默认名称。
```bash
any dev env create -d '{"templateUid":"6","gitUrl":"https://git.woa.com/example/project.git","branch":"master"}'
```

**6. 查询环境列表**
会发生截断,禁止直接输出截断的环境列表,必需要提前做好关键字段的提取,输出的格式可以查询/data/workspace/codev/.codebuddy/anydev/doc/api.md,需要提取出id,envName,status,environmentIp,resourceType进行展示
其中serverType:cvm对应cpu容器,gpu对应gpu容器,vm对应cvm环境,cvd对应云桌面
resourceType:1为已锁定,0为未锁定

```bash
any dev env list -d '{"search":"","bs":""}'
```

**7. 查询环境状态**
```bash
any dev env status -d '{"instanceId":"env-xxx"}'
```

**8. 查询环境日志**
```bash
any dev env logs -d '{"envId":"env-xxx","offset":0,"length":200}'
```

**9. 开启 SSH**
只有用户明确要求连接环境时才执行。出现无法连接的场景下提示用户，需要在 IOA 上点击 IDE 链接环境，只支持有 IOA 的环境进行连接，或者自行配置公钥。
```bash
any dev env ssh -d '{"envId":"env-xxx"}'
```

**10. 初始化环境 agent**
在远端环境启动 agent 进程，获取 token 用于后续 exec / upload 操作。
```bash
any dev env agent init -e evnIns-xxx
```

**11. 查询 agent 状态**
查询远端 agent 运行状态。`agentStatus` 为 `running` 表示可用，为 `unreachable` 表示不可达需要先初始化。详细字段说明见 `/data/workspace/codev/.codebuddy/anydev/doc/api.md`。
```bash
any dev env agent status -e evnIns-xxx
```

**12. 远端执行命令**
在远端环境执行命令。当命令包含 `-` 开头参数时需用 `--` 分隔。部署场景下启动服务必须使用脚本方式（见下方说明）。

**exec 参数传递限制**：exec 传入的命令会经过本地和远端两层 shell 解析，引号、重定向等特殊字符无法可靠传递，复杂命令必须先写脚本再执行。

```bash
# ✅ 正确：简单命令
any dev env agent exec -e evnIns-xxx echo hello world

# ✅ 正确：含 - 开头参数，用 -- 分隔
any dev env agent exec -e evnIns-xxx -- ls -la /data
any dev env agent exec -e evnIns-xxx -- mkdir -p /data/workspace/app
any dev env agent exec -e evnIns-xxx -- tar -xzf /data/workspace/deploy.tar.gz -C /data/workspace/app

# ✅ 正确：含引号的 URL 参数（引号可以保护 URL 中的特殊字符）
any dev env agent exec -e evnIns-xxx -- curl -s "http://127.0.0.1:8080/"

# ✅ 正确：复杂命令（含 nohup/重定向/管道等）使用本地创建脚本 + upload 方式
# 步骤1: 本地创建启动脚本
cat > /tmp/start.sh << 'EOF'
#!/bin/bash
nohup /usr/bin/python3 /data/workspace/app/main.py > /data/workspace/app/nohup.out 2>&1 &
EOF
# 步骤2: upload 脚本到远端
any dev env agent upload -e evnIns-xxx /tmp/start.sh /data/workspace/app/start.sh
# 步骤3: 执行脚本
any dev env agent exec -e evnIns-xxx -- bash /data/workspace/app/start.sh
```

**❌ 错误用例**（以下写法在实际执行中会失败）：
```bash
# ❌ 错误：bash -c 的引号被本地 shell 吃掉，远端实际执行 bash -c echo（输出为空）
any dev env agent exec -e evnIns-xxx -- bash -c "echo hello"
any dev env agent exec -e evnIns-xxx -- bash -c 'echo hello'

# ❌ 错误：重定向 > 被本地 shell 解析，nohup 收到不完整参数，报 "missing operand"
any dev env agent exec -e evnIns-xxx -- nohup /usr/bin/python3 /data/workspace/app/main.py > /data/workspace/app/nohup.out 2>&1 &

# ❌ 错误：bash -c "echo ..." 写入脚本，引号被本地 shell 吃掉，远端实际写入内容为空
any dev env agent exec -e evnIns-xxx -- bash -c "echo '#!/bin/bash' > /data/workspace/app/start.sh"
any dev env agent exec -e evnIns-xxx -- bash -c "echo 'nohup ...' >> /data/workspace/app/start.sh"

# ❌ 错误：node 不在远端默认 PATH 中，报 "node: command not found"
any dev env agent exec -e evnIns-xxx -- nohup node /data/app/index.js > nohup.out 2>&1 &

# ❌ 错误：含 - 开头参数未用 -- 分隔，报 unknown shorthand flag: 'p' in -p
any dev env agent exec -e evnIns-xxx mkdir -p /data/workspace/app
any dev env agent exec -e evnIns-xxx tar -xzf /data/deploy.tar.gz -C /data/workspace/app
```

**13. 上传文件到环境**
将本地文件上传到远端环境。`<dest>` 必须是完整文件路径，不能以 `/` 结尾，不能是已存在的目录。
```bash
any dev env agent upload -e evnIns-xxx /tmp/deploy.tar.gz /data/workspace/deploy.tar.gz
```

**14. 更新环境信息**
修改环境名称等基本信息。
```bash
any dev env info update -d '{"envId":"evnIns-xxx","envName":"新环境名"}'
```

**15. 锁定环境**
锁定环境可防止环境因长期无连接而自动休眠。部署成功后应检查环境锁定状态，未锁定则尝试锁定。
判断环境是否锁定根据 `any dev env list` 返回值中的 `resourceType` 字段：`1` 为已锁定，`0` 为未锁定。
锁定失败时需提示用户配额不足信息。
```bash
any dev env convert -d '{"envId":"evnIns-xxx"}'
```


**15. 查询环境 CPU/内存可调整范围**
查询指定环境的 CPU 和内存可调整范围（最小值、最大值、步长、当前值），以及资源配额剩余信息。调整前必须先执行此命令获取可调整范围。
限制说明：仅 `cvm` 和 `gpu` 类型环境支持；临时 GPU 环境不支持；热更新/迁移任务进行中不支持；环境状态仅 `running`、`stopped`、`queuing`、`queue_start` 允许调整。
CPU 单位：毫核（1000=1 核），内存单位：MB（1000=1G）。
```bash
any dev env adjust range -d '{"envId":"evnIns-xxx"}'
```

**16. 执行环境 CPU/内存调整**
根据指定的目标 CPU 和内存值调整环境配置。调整前必须先通过 `adjust range` 获取可调整范围。
限制说明：`cvmConfig` 不能为空；CPU 和内存不能同时等于当前值；目标值必须在 min~max 范围内；目标值必须按步长（1000）对齐。调整后环境会重启，需等待恢复 `running` 状态。
```bash
# 升配到 32C64G
any dev env adjust exec -d '{"envId":"evnIns-xxx","cvmConfig":{"cpu":32000,"memory":64000}}'

# 降配到 16C32G
any dev env adjust exec -d '{"envId":"evnIns-xxx","cvmConfig":{"cpu":16000,"memory":32000}}'
```

**17. 查询环境磁盘扩容可调整范围**
查询指定环境的磁盘扩容可调整范围（当前值、最大值、步长），以及已扩容大小和母机剩余可扩容空间。扩容前必须先执行此命令获取可调整范围。
限制说明：仅 `cvm` 类型环境支持磁盘扩容；仅 `running` 状态支持；磁盘不可缩小（min=current）；步长固定 10G。
```bash
any dev env disk resize check -d '{"envId":"evnIns-xxx"}'
```

**18. 执行环境磁盘扩容**
根据指定的目标磁盘大小执行扩容操作。扩容前必须先通过 `disk resize check` 获取可调整范围。
限制说明：目标值必须大于当前值；目标值必须按步长（10G）对齐；目标值不能超过可扩容上限。
```bash
# 扩容到 110G
any dev env disk resize exec -d '{"envId":"evnIns-xxx","size":110}'

# 扩容到 200G
any dev env disk resize exec -d '{"envId":"evnIns-xxx","size":200}'
```


---

# API 参考

# CLI 命令请求响应参考

本文档记录了 anydev skill 中使用的所有 CLI 命令的参数说明与真实响应示例。

## 1. any login
**用户登录授权**

执行后 CLI 会输出授权链接，用户完成授权后自动获取并缓存鉴权信息

### 命令
```bash
any login
```

## 2. any dev env template recommend
**获取推荐模板列表**

**参数:**
无参数。

### 命令
```bash
any dev env template recommend -d '{}'
```

### 响应 (节选)
```json
{
  "code": 200,
  "data": {
    "all": [
      {
        "templateUid": "6",
        "templateName": "标准通用模板",
        "imageName": "系统镜像",
        "imageUrl": "mirrors.tencent.com/devcloud/codev-tlinux3:0.1.3",
        "languages": [
          "golang 1.20.4",
          "nodejs 18.12.0"
        ],
        "vsCodePlugins": [
          "Vue.volar",
          "remotessh"
        ],
        "startCommand": "npm install",
        "serverType": "cvm",
        "templateType": "system",
        "isOwner": false,
        "creator": "zilchzhong",
        "version": "v202308090007"
      }
    ]
  }
}
```

## 3. any dev env template query
**查询模板详情**

**参数:**
| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `templateUid` | string | **是** | 模板 uid |

### 命令
```bash
any dev env template query -d '{"templateUid":"6"}'
```

### 响应 (节选)
```json
{
  "code": 200,
  "message": "",
  "data": {
    "template": {
      "templateUid": "6",
      "templateName": "标准通用模板",
      "serverType": "cvm",
      "templateType": "system",
      "version": "v202308090007"
    },
    "presetValue": {
      "envConfType": {
        "enable": true,
        "notUpdateEnable": false,
        "items": [
          {
            "name": "标准型 （配置：CPU 16核； 内存 32G；硬盘 100G ）",
            "id": 1,
            "value": ""
          }
        ]
      }
    }
  }
}
```

## 4. any dev git projects
**查询用户代码仓库（支持通过 search 参数搜索）**

**参数:**
| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `page` | int32 | **是** | 第几页 |
| `perPage` | int32 | **是** | 每页大小 |
| `search` | string | 否 | 查询关键字 |
| `archived` | bool | 否 | 归档状态，默认不区分归档状态 |
| `orderBy` | string | 否 | 排序字段，可选: `name`、`updated`(默认) |

### 命令
```bash
any dev git projects -d '{"page":1,"perPage":5,"search":"aiResource"}'
```

### 响应
```json
{
  "code": 0,
  "message": "",
  "data": {
    "total": 1,
    "items": [
      {
        "id": 1644361,
        "public": false,
        "name": "aiResource",
        "nameWithNamespace": "clouddev/aiResource",
        "path": "aiResource",
        "pathWithNamespace": "clouddev/aiResource",
        "sshUrlToRepo": "git@git.woa.com:clouddev/aiResource.git",
        "httpUrlToRepo": "http://git.woa.com/clouddev/aiResource.git",
        "httpsUrlToRepo": "https://git.woa.com/clouddev/aiResource.git",
        "webUrl": "http://git.woa.com/clouddev/aiResource",
        "createdAt": "2026-01-27T09:18:26+0000",
        "lastActivityAt": "2026-02-05T08:19:26+0000",
        "limit": false
      }
    ]
  }
}
```

## 5. any dev git branches
**查询仓库分支**

**参数:**
| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `gitUrl` | string | **是** | git仓库的 url，如 `https://git.woa.com/CodevPro/codev.git` |
| `search` | string | 否 | 查询关键字 |
| `page` | int32 | 否 | 页数 (默认 1) |
| `perPage` | int32 | 否 | 页面大小 (默认 20) |
| `orderBy` | string | 否 | 排序字段，如 `name`、`updated`(默认) |

### 命令
```bash
any dev git branches -d '{"gitUrl":"https://git.woa.com/clouddev/aiResource.git","page":1,"perPage":1}'
```

### 响应
```json
{
  "code": 200,
  "message": "",
  "data": {
    "total": 1,
    "items": [
      {
        "name": "master",
        "protected": true,
        "created_at": "2026-01-27T09:19:02+0000",
        "description": ""
      }
    ]
  }
}
```

## 6. any dev env create
**创建云研发环境**

限制说明：
- 仅支持创建 `serverType=cvm` 的 CPU 模板环境
- `gpu` 与 `vm` 模板即使可查询，也不能通过该命令创建
- 不要让用户填写 `tenantId`
- 不要让用户填写 `envVariables`

**参数:**
| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `templateUid` | string | **是** | 环境模板 Uid，且必须是 CPU 模板 |
| `gitUrl` | string | 否 | 代码仓库 Url |
| `branch` | string | 否 | 分支名 |
| `envName` | string | 否 | 环境名称（不指定则使用默认名称） |
| `tenantId` | int32 | 否 | 租户 ID |


### 命令
```bash
# 使用默认名称创建
any dev env create -d '{"templateUid":"6"}'

# 创建时指定环境名称
any dev env create -d '{"templateUid":"6","envName":"我的测试环境"}'
```

### 响应
```json
{
  "code": 200,
  "message": "",
  "data": {
    "instanceId": "evnIns-6k6dbhhfz9la",
    "paasEnvId": "xiyouliao-2dvjbrqtoa"
  }
}
```

## 7. any dev env status
**查询环境运行状态**

**参数:**
| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `instanceId` | string | **是** | 环境 id 主键（优先使用该字段查询） |
| `envId` | string | 否 | 环境 id 主键（效果同 instanceId，后端暂未优先使用） |
| `paasEnvId` | string | 否 | paas 环境 ID（若 instanceId 为空，则采用此字段查询） |
| `force` | bool | 否 | 销毁环境时使用，为 true 时强制销毁（不受锁定限制） |

### 命令
```bash
any dev env status -d '{"instanceId":"evnIns-6k6dbhhfz9la"}'
```

### 响应 (节选)
```json
{
  "code": 200,
  "message": "",
  "data": {
    "envId": "evnIns-6k6dbhhfz9la",
    "gitUrl": "",
    "status": "running",
    "createdTime": "2026-03-20 09:32:24",
    "paasEnvId": "xiyouliao-2dvjbrqtoa",
    "environmentIp": "21.214.193.144",
    "envDomains": {
      "dynamics": "21.214.193.144.devcloud.woa.com",
      "fix": "xiyouliao-any525-test.devcloud.woa.com"
    },
    "serverType": "cvm",
    "templateInfo": {
      "templateUid": "6",
      "templateName": "标准通用模板-lxcfs",
      "imageName": "系统镜像"
    },
    "envName": "我的开发环境",
    "gitUrls": [],
    "cpu": 16000,
    "memory": 32000,
    "disk": 100,
    "environmentHost": "21.6.64.18"
  }
}
```

## 8. any dev env logs
**查询环境创建日志**

**参数:**
| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `envId` | string | **是** | 环境主键 ID |
| `offset` | int32 | **是** | 偏移量 |
| `length` | int32 | **是** | 请求长度 |
| `taskUid` | string | 否 | 任务 uid |

### 命令
```bash
any dev env logs -d '{"envId":"evnIns-6k6dbhhfz9la","offset":0,"length":2}'
```

### 响应
```json
{
  "code": 200,
  "message": "",
  "data": {
    "total": 27,
    "logMessage": [
      "2026-03-20 09:32:23,INFO,2988a3ee901423299c28ccbfeb29af3c,收到创建请求",
      "2026-03-20 09:32:23,INFO,2988a3ee901423299c28ccbfeb29af3c,tag:codev,调度成功,cluster:cls-jb3dsl4s,namespace:codev-2,node:21.6.64.18,diskType:localplus,baseName:,baseVersion:0,baseHostDir:"
    ]
  }
}
```

## 9. any dev env list
**查询环境列表**

**参数:**
| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `search` | string | 否 | （已废弃）查询关键字 |
| `bs` | string | 否 | 根据模板的 bs 筛选环境 |

### 命令
```bash
any dev env list -d '{"search":"","bs":""}'
```

### 响应 (节选)
```json
{
  "code": 200,
  "message": "",
  "data": [
    {
      "id": "evnIns-6k6dbhhfz9la",
      "gitUrl": "",
      "status": "running",
      "createdTime": "2026-03-20 09:32:24",
      "paasEnvId": "xiyouliao-2dvjbrqtoa",
      "serverType": "cvm",
      "templateUid": "6",
      "envName": "我的开发环境",
      "cpu": 16000,
      "memory": 32000,
      "resourceType": 1
    }
  ]
}
```

### 响应字段说明

**`resourceType`** — 环境锁定状态：
| 值 | 说明 |
| :--- | :--- |
| `0` | 未锁定（若连续 7 天无连接，环境将自动休眠） |
| `1` | 已锁定（环境不会被自动休眠） |

## 10. any dev env agent init
**初始化环境 agent**

在远端环境中启动 agent 进程，获取 token 用于后续 exec / upload 操作。若已初始化则复用已有 token。

**参数 (flag):**
| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `-e` / `--envId` | string | **是** | 环境 ID |

### 命令
```bash
any dev env agent init -e evnIns-69rg14n8avx2
```

### 响应
```json
{
  "code": 200,
  "data": {
    "taskId": "exec-xiyouliao-2aaf4f4c0a-6ohomyn6n5mm",
    "token": "6oc28eoe45na",
    "status": "waiting"
  }
}
```

---

## 11. any dev env agent status
**查询 agent 运行状态**

查询远端 agent 进程的运行状态和版本信息。

**参数 (flag):**
| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `-e` / `--envId` | string | **是** | 环境 ID |

### 命令
```bash
any dev env agent status -e evnIns-69rg14n8avx2
```

### 响应
```json
{
  "code": 200,
  "message": "",
  "data": {
    "agentStatus": "running",
    "version": "0.0.1",
    "source": "agent"
  }
}
```

### 响应字段说明

**`agentStatus`** — agent 进程状态：
| 值 | 说明 |
| :--- | :--- |
| `running` | agent 正常运行，可执行 exec / upload |
| `unreachable` | agent 不可达（进程未启动或已崩溃），此时会额外返回 `initStatus` 和 `taskId` |

**`initStatus`** — 初始化任务状态（仅当 `agentStatus` 为 `unreachable` 时返回）：
| 值 | 说明 |
| :--- | :--- |
| `waiting` | 等待执行 |
| `running` | 正在执行中 |
| `successed` | 执行成功 |
| `failed` | 执行失败 |
| `timeout` | 执行超时 |

**`source`** — 响应数据来源：
| 值 | 说明 |
| :--- | :--- |
| `agent` | 从 agent 直接获取 |
| `initTask` | 从后端初始化任务记录查询 |

---

## 12. any dev env agent exec
**远程执行命令**

通过 WebSocket 连接远端 agent 执行命令。

**参数 (flag):**
| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `-e` / `--envId` | string | **是** | 环境 ID |
| `--timeout` | int | 否 | 命令超时时间（秒），默认 0 表示不限制 |

### 参数传递机制

exec 传入的命令会经过本地 shell 和远端 shell 两层解析。CLI 将 `--` 后面的所有参数用空格拼接为单个字符串，然后发送给远端 agent 执行。由于经过两层 shell 解析，中间的引号、转义等特殊字符无法可靠传递。

**关键限制**：
- **引号会被本地 shell 吃掉**：`bash -c "echo hello"` 在本地 shell 解析后引号丢失，远端实际执行 `bash -c echo hello`，其中 `bash -c` 只取第一个参数 `echo` 作为命令，输出为空
- **重定向 `>`、管道 `|`、后台 `&`**：被本地 shell 或远端 shell 错误解析
- **变量 `$`**：被本地 shell 展开

### 注意事项

> **1. 含 `-` 开头参数必须用 `--` 分隔**
>
> ```bash
> # ✅ 正确：用 -- 分隔后，-la 不会被 cobra 解析
> any dev env agent exec -e evnIns-xxx -- ls -la /data
>
> # ❌ 错误：-la 被 CLI 当作自身 flag，报错 unknown shorthand flag: 'l' in -la
> any dev env agent exec -e evnIns-xxx ls -la /data
> ```

> **2. 复杂命令（含引号/重定向/nohup等）必须使用脚本方式**
>
> ```bash
> # ✅ 正确：先写脚本再执行
> any dev env agent exec -e evnIns-xxx -- bash -c "echo '#!/bin/bash' > /data/workspace/app/start.sh"
> any dev env agent exec -e evnIns-xxx -- bash -c "echo 'nohup /usr/bin/python3 /data/workspace/app/main.py > /data/workspace/app/nohup.out 2>&1 &' >> /data/workspace/app/start.sh"
> any dev env agent exec -e evnIns-xxx -- bash /data/workspace/app/start.sh
> ```

> **3. 远端环境运行时依赖**
>
> 远端环境中运行时依赖可能未安装或不在默认 PATH 中，需先确认是否可用，不可用则先安装：
> - node: 检查 `/opt/codev/nodejs/bin/node` 是否存在，或 `source /etc/profile` 后使用 `node`；若不存在则需安装
> - python3: 检查 `/usr/bin/python3` 是否存在；若不存在则需安装（如 `apt-get update && apt-get install -y python3`）
> - go: 检查 `/usr/local/go/bin/go` 是否存在；若不存在则需安装（如下载官方二进制包解压到 `/usr/local/go`）
> - 其他依赖: 同理，先用 `which <命令>` 确认是否存在，不存在则先安装

### 命令
```bash
# 简单命令
any dev env agent exec -e evnIns-69rg14n8avx2 echo hello world

# 含 - 开头参数
any dev env agent exec -e evnIns-69rg14n8avx2 -- ls -la /data
any dev env agent exec -e evnIns-69rg14n8avx2 -- mkdir -p /data/workspace/app

# 带超时
any dev env agent exec -e evnIns-69rg14n8avx2 --timeout 3 sleep 60

# 含引号的参数（如 URL）
any dev env agent exec -e evnIns-69rg14n8avx2 -- curl -s "http://127.0.0.1:8080/"
```

### ❌ 错误用例
```bash
# ❌ bash -c 的引号被本地 shell 吃掉，远端实际执行 bash -c echo（输出为空）
any dev env agent exec -e evnIns-xxx -- bash -c "echo hello"

# ❌ 重定向 > 被本地 shell 解析，nohup 收到不完整参数，报 "missing operand"
any dev env agent exec -e evnIns-xxx -- nohup /usr/bin/python3 /data/app/main.py > /data/app/nohup.out 2>&1 &

# ❌ bash -c 中包含重定向，引号丢失后命令结构被远端 shell 破坏
any dev env agent exec -e evnIns-xxx -- bash -c "nohup node /data/app/index.js > /data/app/nohup.out 2>&1 &"

# ❌ node 不在远端默认 PATH 中
any dev env agent exec -e evnIns-xxx -- nohup node /data/app/index.js > nohup.out 2>&1 &
# 报错：node: command not found

# ❌ python3 -c 的引号被本地 shell 吃掉，报 syntax error
any dev env agent exec -e evnIns-xxx -- python3 -c "print('hello')"

# ❌ 含 - 开头参数未用 -- 分隔
any dev env agent exec -e evnIns-xxx mkdir -p /data/workspace/app
# 报错：unknown shorthand flag: 'p' in -p
```

### 响应
直接输出命令的 stdout，如：
```
hello world
```

---

## 13. any dev env agent upload
**上传文件到远端环境**

通过 WebSocket 将本地文件上传到远端环境指定路径。支持大文件分片传输（32KB/片）。

**参数 (flag + positional):**
| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `-e` / `--envId` | string | **是** | 环境 ID |
| `<src>` | string | **是** | 本地源文件路径（支持 `~` 展开，不支持目录） |
| `<dest>` | string | **是** | 远端目标**文件**路径（必须包含文件名，不能以 `/` 结尾，不能是已存在的目录） |

> **重要**：`<dest>` 必须是完整的文件路径（如 `/tmp/test.txt`），不能是目录路径（如 `/tmp/`）。若目标目录不存在，agent 会自动创建。若目标文件已存在则覆盖。

### 命令
```bash
any dev env agent upload -e evnIns-69rg14n8avx2 /tmp/upload_test.txt /tmp/upload_test.txt

# ~ 路径自动展开
any dev env agent upload -e evnIns-69rg14n8avx2 ~/test.txt /tmp/test.txt
```

> **`<dest>` 路径规则**：
>
> ```bash
> # ✅ 正确：完整的文件路径
> any dev env agent upload -e evnIns-xxx /tmp/test.txt /tmp/test.txt
>
> # ✅ 正确：目标目录不存在时 agent 会自动创建
> any dev env agent upload -e evnIns-xxx /tmp/test.txt /root/newdir/test.txt
>
> # ❌ 错误：目标路径以 / 结尾（目录路径），报错 "上传目标路径必须包含文件名，不能是目录路径"
> any dev env agent upload -e evnIns-xxx /tmp/test.txt /tmp/
>
> # ❌ 错误：目标路径是已存在的目录（如 /tmp），报错 "上传目标路径必须是文件路径，不能是已存在目录"
> any dev env agent upload -e evnIns-xxx /tmp/test.txt /tmp
>
> # ❌ 错误：源路径是目录，报错 "当前仅支持上传单个文件"
> any dev env agent upload -e evnIns-xxx /tmp/ /data/test.txt
> ```

### 响应
```json
{
  "status": "completed",
  "path": "/tmp/upload_test.txt"
}
```

---

## 14. any dev env ssh
**开启环境 SSH 连接**

> 注：`keyName` 保持空字符串即可；如果不指定特定 IDE 版本，不能传递 `ideVersion`（或传空字符串），否则后端会抛出 `parse int failed` 的报错。

**参数:**
| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `envId` | string | **是** | 环境 id |
| `keyName` | string | **是** | key 名称（为空时传 `""`） |
| `ideName` | string | **是** | 打开 ide 名称（例如 `VSCode`） |
| `ideVersion` | string | 否 | 选填，打开的 ide 版本 |

### 命令
```bash
any dev env ssh -d '{"envId":"evnIns-6k6dbhhfz9la","keyName":"","ideName":"VSCode"}'
```

### 响应 (节选)
```json
{
  "code": 200,
  "message": "",
  "data": {
    "CodeBuddyCN": "codebuddycn://vscode-remote/codebuddy-remote-ssh+root@xiyouliao-any525-test.devcloud.woa.com:36000/data/workspace/?windowId=_blank",
    "GoLand": "jetbrains-gateway://connect#idePath=/codev/ide/GO/GoLand-2023.3.2&...",
    "VSCode": "vscode://vscode-remote/ssh-remote+root@xiyouliao-any525-test.devcloud.woa.com:36000/data/workspace/?windowId=_blank"
  }
}
```

---

## 15. any dev env info update
**更新环境信息**

更新环境的名称等基本信息。

**参数:**
| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `envId` | string | **是** | 环境 ID |
| `envName` | string | 否 | 新的环境名称 |

### 命令
```bash
any dev env info update -d '{"envId":"evnIns-6k6dbhhfz9la","envName":"新环境名"}'
```

### 响应
```json
{
  "code": 200,
  "message": "",
  "data": {}
}
```

## 16. any dev env adjust range
**查询环境 CPU/内存可调整范围**

查询指定环境的 CPU 和内存可调整范围（最小值、最大值、步长、当前值），以及资源配额剩余信息。

限制说明：
- 仅 `cvm` 和 `gpu` 类型环境支持调整
- 临时 GPU 环境不支持调整
- 热更新任务进行中、迁移任务进行中时不支持调整
- 环境状态仅 `running`、`stopped`、`queuing`、`queue_start` 允许调整

**参数:**
| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `envId` | string | **是** | 环境主键 ID（长度至少 1） |

### 命令
```bash
any dev env adjust range -d '{"envId":"evnIns-6k6dbhhfz9la"}'
```

### 响应
```json
{
  "code": 200,
  "message": "",
  "data": {
    "envId": "evnIns-6k6dbhhfz9la",
    "envName": "我的开发环境",
    "serverType": "cvm",
    "status": "running",
    "supported": true,
    "cpu": {
      "current": 16000,
      "min": 1000,
      "max": 32000,
      "step": 1000
    },
    "memory": {
      "current": 32000,
      "min": 1000,
      "max": 64000,
      "step": 1000
    },
    "cpuQuotaRest": {
      "quota": 48000,
      "lockQuota": 0
    },
    "memoryQuotaRest": {
      "quota": 96000,
      "lockQuota": 0
    },
    "diskQuotaRest": {
      "quota": 500,
      "lockQuota": 0
    },
    "mountStorage": false,
    "isTemporaryGpu": false
  }
}
```

### 响应字段说明

**`cpu` / `memory`** — `CliEnvResourceRange` 资源可调整范围：

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| `current` | int32 | 当前值（CPU 单位：毫核，1000=1 核；内存单位：MB，1000=1G） |
| `min` | int32 | 可调整最小值（固定为步长值 1000，即 1 核 / 1G） |
| `max` | int32 | 可调整最大值（根据资源配额动态计算） |
| `step` | int32 | 调整步长（固定 1000，即 1 核 / 1G） |

**`cpuQuotaRest` / `memoryQuotaRest` / `diskQuotaRest`** — `CliEnvQuotaRest` 配额剩余：

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| `quota` | int32 | 剩余申请额度 |
| `lockQuota` | int32 | 剩余锁定额度 |

**`isTemporaryGpu`** — 是否为临时 GPU 环境（临时 GPU 不支持调整）。

---

## 17. any dev env adjust exec
**执行环境 CPU/内存调整**

根据指定的目标 CPU 和内存值调整环境配置。调整前建议先通过 `adjust range` 命令获取可调整范围。

限制说明：
- `cvmConfig` 不能为空
- CPU 和内存不能同时等于当前值（未发生变化）
- 目标值必须在 `adjust range` 返回的 min~max 范围内
- 目标值必须按步长（1000）对齐

**参数:**
| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `envId` | string | **是** | 环境主键 ID |
| `envConfigTypeId` | int32 | 否 | 环境配置类型 ID |
| `cvmConfig` | object | **是** | CVM 目标配置 |
| `cvmConfig.cpu` | int32 | **是** | 目标 CPU 值（单位：毫核，1000=1 核） |
| `cvmConfig.memory` | int32 | **是** | 目标内存值（单位：MB，1000=1G） |

### 命令
```bash
# 升配 16C32G → 32C64G
any dev env adjust exec -d '{"envId":"evnIns-6k6dbhhfz9la","cvmConfig":{"cpu":32000,"memory":64000}}'

# 降配回 16C32G
any dev env adjust exec -d '{"envId":"evnIns-6k6dbhhfz9la","cvmConfig":{"cpu":16000,"memory":32000}}'
```

### 响应
```json
{
  "code": 200,
  "message": "",
  "data": ""
}
```

> **注意**: 调整后环境会重启，需等待环境恢复 `running` 状态后才能继续操作。

---

## 18. any dev env disk resize check
**查询环境磁盘扩容可调整范围**

查询指定环境的磁盘扩容可调整范围（当前值、最大值、步长），以及已扩容大小和母机剩余可扩容空间。

限制说明：
- 仅 `cvm` 类型环境支持磁盘扩容
- 仅 `running` 状态支持
- `DiskQuotaResize.Enabled` 必须为 true
- 母机剩余磁盘空间（`DiskRemain`）必须大于 0

**参数:**
| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `envId` | string | **是** | 环境主键 ID（长度至少 1） |

### 命令
```bash
any dev env disk resize check -d '{"envId":"evnIns-6k6dbhhfz9la"}'
```

### 响应
```json
{
  "code": 200,
  "message": "",
  "data": {
    "envId": "evnIns-6k6dbhhfz9la",
    "envName": "我的开发环境",
    "serverType": "cvm",
    "status": "running",
    "supported": true,
    "disk": {
      "current": 100,
      "min": 100,
      "max": 500,
      "step": 10
    },
    "diskQuotaRest": {
      "quota": 500,
      "lockQuota": 0
    },
    "mountStorage": false,
    "resized": 0,
    "diskRemain": 400
  }
}
```

### 响应字段说明

**`disk`** — `CliEnvResourceRange` 磁盘可调整范围：

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| `current` | int32 | 当前磁盘大小（单位：G，含已扩容） |
| `min` | int32 | 最小值（等于 current，磁盘不可缩小） |
| `max` | int32 | 最大值（= current + diskRemain） |
| `step` | int32 | 步长（固定 10G） |

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| `resized` | int32 | 已扩容大小（G） |
| `diskRemain` | int32 | 母机剩余可扩容大小（G） |

---

## 19. any dev env disk resize exec
**执行环境磁盘扩容**

根据指定的目标磁盘大小执行扩容操作。扩容前建议先通过 `disk resize check` 命令获取可调整范围。

限制说明：
- 目标值必须大于当前值
- 目标值必须按步长（10G）对齐
- 目标值不能超过可扩容上限（max）

**参数:**
| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `envId` | string | **是** | 环境主键 ID（长度至少 1） |
| `size` | uint32 | **是** | 目标磁盘大小（单位：G，必须大于 0） |

### 命令
```bash
# 扩容到 110G（当前 100G + 10G 步长）
any dev env disk resize exec -d '{"envId":"evnIns-6k6dbhhfz9la","size":110}'

# 扩容到 200G
any dev env disk resize exec -d '{"envId":"evnIns-6k6dbhhfz9la","size":200}'
```

### 响应
```json
{
  "code": 200,
  "message": "",
  "data": ""
}
```

---

## 20. any dev env convert
**锁定环境**

锁定环境可防止环境因长期无连接而自动休眠。部署成功后应检查环境锁定状态，未锁定则尝试锁定。
判断环境是否锁定根据 `any dev env list` 返回值中的 `resourceType` 字段：`1` 为已锁定，`0` 为未锁定。

**参数:**
| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `envId` | string | **是** | 环境主键 ID |

### 命令
```bash
any dev env convert -d '{"envId":"evnIns-6wg5mvzmdl3o"}'
```

### 响应（成功）
```json
{
  "code": 200,
  "data": "evnIns-6wg5mvzmdl3o"
}
```

### 锁定失败处理

锁定失败时（如配额不足），需提示用户：

> ⚠️ 您的环境锁定配额不足，环境未锁定。若连续 7 天无连接，环境将自动休眠。您可解锁无需锁定的环境以释放锁定配额，或者联系O2000增加锁定配额。