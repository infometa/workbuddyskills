# Omics Platform CLI 命令参考（v4 · 7 命令边界）

> 本文档提供 omics-platform-cli **白名单 7 条**一级命令的完整参数说明、行为矩阵和示例。
> 详细实现请参考源码仓库 omics-platform-cli 源码仓库。
>
> ⚠️ **能力边界**：CLI v4 起对外暴露的一级命令严格限定为以下 7 条；
> 旧 `omics app *` 命令族（list / list-public / templates / file *）已废除，
> 查询语义迁移到 `omics list`，模板/文件操作内化到 `omics run` 内部链路。

---

## 目录

1. [命令总览](#1-命令总览)
2. [login — OAuth 登录](#2-login--oauth-登录)
3. [whoami — 当前登录用户](#3-whoami--当前登录用户)
4. [config — 本地配置](#4-config--本地配置)
5. [list — 只读查询](#5-list--只读查询)
6. [run — 唯一运行入口](#6-run--唯一运行入口)
7. [status — 任务状态](#7-status--任务状态)
8. [debug — 异步失败取证（三段式）](#8-debug--异步失败取证三段式)
9. [认证机制 & 配置文件](#9-认证机制--配置文件)
10. [退出码说明](#10-退出码说明)
11. [废弃命令对照表](#11-废弃命令对照表)

---

## 1. 命令总览

```
omics                                            # 根命令
├── login                                        # OAuth 浏览器登录
├── whoami                                       # 当前登录用户
├── version                                      # CLI 版本号（工具命令，非业务白名单）
├── config
│   ├── set     [-r ... -p ... -e ... -b ...]   # 交互式 / 显式入参；写盘前服务校验
│   ├── show    [-o table|json]                 # 显示当前本地配置
│   └── clear                                   # 删除本地配置
├── list
│   ├── public-apps   [--tag <T>] [--type WDL|NEXTFLOW] [--keyword <kw>] [--parent-app <合集AppId>] [-o ...]
│   │                 # 列平台公共应用，按 AppTag 分组展示；--parent-app 展开合集
│   ├── apps          [--type WDL|WDL_GRAPH|NEXTFLOW] [-o ...]
│   │                 # 列 config 项目下的应用
│   ├── versions      --app <appId> [--type RELEASE|HISTORY] [--limit N] [-o ...]
│   │                 # v6：列指定应用的版本（form C 运行前必经）
│   └── templates     --app <appId> [--version <verId>] [--with-content] [--limit N] [-o ...]
│                     # v6.1：列指定应用的运行参数模板（form B/C 运行前必经）
├── run                                         # 四选一：--wdl / --nf / --public-app / --app
│   │                                           # form A/C 不传 --input/--template → 仅靠 WDL Default 跑（baseline）
│   │                                           # form B 不传 --input/--template → 自动取第一个 InputTemplate（兜底）
│   │                                           # form B + NEXTFLOW → 必传 --nf-version <version>
│   │                                           # 通用：--version <VerId> 指定版本；缺省自动选最新
│   │                                           # 通用：--template <Id> 用服务端模板（与 --input 互斥）
│   │                                           # form A 专属：--release-name <name> 把新 HISTORY 发布为 RELEASE
│   ├── --wdl <path>          # form A：本地 WDL（必配 --name；失败可 --update <appId> 复用空白应用）
│   ├── --nf <cos-path>       # form D：COS 上的 Nextflow（必配 --name + --nf-version）
│   ├── --public-app <appId>  # form B：公共应用（合集子应用必传 --public-app-name）
│   └── --app <appId>         # form C：项目内已有应用
├── status [<rgId>] [-o ...]                    # 列批次 / 列子任务（固定走 config 项目）
└── debug
    ├── <runGroupId>                            # 段 1：列该批次失败子任务
    ├── --run <runUuid>                         # 段 2：单子任务现场（Status + Calls + JobLogs）
    └── --run <runUuid> --job <jobId>           # 段 3：精确钻取 Job
```

**关键设计原则**：

- **CLI 是能力的唯一合法出口**——SKILL 必须通过这 7 条命令操作平台
- **运行类操作必须二次确认**（由 SKILL 层负责，CLI 不做）
- **不再自动选默认项目/默认环境**：`region/projectId/environmentId` 必须显式 `omics config set`
- **状态/失败诊断严格走 status 与 debug 命令**——不再有任何"直调后端 API"的旁路

---

## 2. login — OAuth 登录

```bash
omics login
```

行为：CLI 启动 `localhost:18000` 监听，打开浏览器到 OAuth 授权页，用户完成授权后回调本地 → 写入 token。

> ⚠️ 仅在用户**本机终端**执行；SKILL 跑在远程 agent（容器 / SSH）里无法接收 `localhost` 回调，
> 应该引导用户自己跑而不是替用户调。

退出码：0 成功 / 非 0 失败（端口被占、授权超时等）。

---

## 3. whoami — 当前登录用户

```bash
omics whoami
```

输出：当前 session uin、用户昵称、token 剩余有效期。
退出码：0 已登录 / 2 未登录或 session 过期。

---

## 4. config — 本地配置

配置文件：`~/.omics-platform-cli/omics_config.json`，含 `Region / ProjectId / ProjectName / EnvironmentId / EnvironmentName / CosBucketName`。

### 4.1 `omics config set`

```bash
omics config set [-r ap-guangzhou] [-p prj-xxx] [-e env-xxx] [-b my-bucket]
```

- 缺任意一项 → 进入**交互式**逐项提示
- 写盘前调服务校验：`DescribeProjects` / `DescribeEnvironments` / `DescribeAssociatedCosBuckets`
- 任一校验不通过 → 非零退出 + stderr 列可选项

> ⚠️ **SKILL 永远不主动调 set**——它是交互式命令，远程 agent 无法替用户输入；
> 同时 SKILL 也不应猜测 / 编造 ID。

### 4.2 `omics config show`

```bash
omics config show -o json
```

JSON 字段：`Region / ProjectId / ProjectName / EnvironmentId / EnvironmentName / CosBucketName`。
任一字段为空 → 退出码 1。

### 4.3 `omics config clear`

```bash
omics config clear
```

删除本地配置文件；不影响 token。

---

## 5. list — 只读查询

### 5.1 `omics list public-apps`（按 AppTag 分组）

```bash
omics list public-apps [-o table|json]
omics list public-apps --tag <tagName> [-o ...]
omics list public-apps --type WDL|NEXTFLOW [-o ...]
omics list public-apps --keyword <kw> [-o ...]
omics list public-apps --parent-app <collectionAppId> [-o ...]
```

#### 数据流

```
CommonAppService.DescribeCommonApp(空 req, Limit=PageSize)
        ↓
全部 CommonApp[]（含 AppTags []string）
        ↓
客户端聚合（cmd/list_public_apps.go::groupPublicAppsByTag）
  1. 收集所有 AppTags 去重 + 字典序排序
  2. 多 Tag 应用在每个组下重复出现（用户体验优先）
  3. 无 Tag 应用归入"未分类"组（始终最后）
  4. TotalApps 用 AppId 集合去重统计
        ↓
table（按 Tag 分组打印）/ JSON（{Tags, TotalApps, Groups[]}）
```

#### 参数表

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `--tag` | string | 否 | 业务标签精确匹配（CLI 客户端按字符串比对 AppTags） |
| `--type` | enum | 否 | WDL / NEXTFLOW；叠加在 tag 之上的二级过滤 |
| `--keyword` | string | 否 | service 端 LIKE 搜索 |
| `--parent-app` | string | 否 | 展开合集；非空时 service 端屏蔽 type/keyword/tag |
| `-o` | enum | 否 | table（默认）/ json |

#### JSON 输出形态

```json
{
  "Tags": ["WGS", "RNA-seq", "未分类"],
  "TotalApps": 6,
  "Groups": [
    {
      "Tag": "WGS",
      "Count": 3,
      "Apps": [
        {
          "AppId": "cm-aaa-bbb",
          "AppName": "Sentieon-Germline",
          "AppType": "WDL",
          "AppDesc": "...",
          "SourceEntrypoint": "main.wdl",
          "AppGroupType": "",
          "AppTags": ["WGS"],
          "NextflowVersion": []
        }
      ]
    },
    { "Tag": "RNA-seq", "Count": 2, "Apps": [...] },
    { "Tag": "未分类",  "Count": 1, "Apps": [...] }
  ]
}
```

#### Table 输出形态

```
══════════════════════════════════════════════════════════
[Tag: WGS]  3 个应用
──────────────────────────────────────────────────────────
APP_ID         NAME                 TYPE      GROUP            ENTRYPOINT       DESC
cm-aaa-bbb     Sentieon-Germline    WDL                        main.wdl         ...
...

══════════════════════════════════════════════════════════
全部 Tag: [WGS RNA-seq 未分类]
公共应用总数: 6（去重后）
══════════════════════════════════════════════════════════
```

#### 合集（APP_COLLECTION）展开

```bash
omics list public-apps --parent-app cm-collection-xxx -o json
```

- 当 `--parent-app` 非空时，CLI 调 `client.FetchPublicSubApplications(parentAppId)`，
  service 端屏蔽 type/keyword/tag，返回该合集下全部子应用（Limit=PageSize=999）
- 子应用的 `AppGroupType` 不再是 `APP_COLLECTION`，可直接 `omics run --public-app <子AppId>`

### 5.2 `omics list apps`（项目内应用）

```bash
omics list apps [-o table|json]
omics list apps --type WDL [-o ...]
```

固定走 `omics_config.json::ProjectId`，**不支持 `-p`**；要切项目请重新 `omics config set`。

JSON 关键字段：`ApplicationId / Name / Type / VersionCount / Entrypoint / CreateTime`。

#### SKILL 主要使用场景

1. **form C 选 ApplicationId**：用户说"跑我项目里那个 sentieon 应用"时帮其挑 ID
2. **form B 同名预检**：导入公共应用前比对 `Name == candidateName`，避免污染应用列表

### 5.3 `omics list versions`（应用版本列表 · v6 新增）

```bash
omics list versions --app <appId> [-o table|json]
omics list versions --app <appId> --type RELEASE [-o json]
omics list versions --app <appId> --type HISTORY --limit 10 [-o json]
```

**参数**：

| flag        | 必填 | 说明                                                |
| ----------- | ---- | --------------------------------------------------- |
| `--app`     | 是   | 应用 ApplicationId                                  |
| `--type`    | 否   | 过滤 `RELEASE` / `HISTORY`；默认全部                 |
| `--limit`   | 否   | 返回条数上限（默认 50）                              |
| `-o/--output` | 否 | `table` / `json`；推荐 `json` 给 SKILL 解析          |

**JSON 输出形态**：

```json
{
  "ApplicationId": "app-xxxx",
  "TotalCount": 4,
  "Versions": [
    {
      "Type": "RELEASE",
      "ApplicationVersionId": "ver-aaaaaaaa",
      "Name": "v2.0",
      "Entrypoint": "main.wdl",
      "CreateTime": "2026-06-01 10:11:12",
      "CreatorName": "alice"
    },
    { "Type": "HISTORY", "ApplicationVersionId": "ver-bbbbbbbb",
      "Entrypoint": "main.wdl", "CreateTime": "..." },
    ...
  ]
}
```

**关键字段**：

- `Type`：`RELEASE`（已通过 `--release-name` 发布命名的版本）/ `HISTORY`（每次保存生成的快照，无业务名）
- `ApplicationVersionId`：可直接传给 `omics run --version <Id>` 指定该版本运行
- `Name`：仅 RELEASE 有有意义；HISTORY 的 Name 字段为空
- `CreateTime`：版本入库时间；服务端按 sid 倒序，所以列表第一条就是最新

**SKILL 主要使用场景**：

1. **form C 运行前必经**：让用户从清单中拍板要跑哪个版本（详见 SKILL.md §4.5）
2. **form A `--update` 后**：查询本次新生成的版本是否已发布命名
3. **梳理版本演进**：用户问"这个应用都更新过几次"

### 5.4 `omics list templates`（应用运行参数模板列表 · v6.1 新增）

```bash
omics list templates --app <appId> [-o table|json]
omics list templates --app <appId> --version <verId> [-o json]
omics list templates --app <appId> --with-content [-o json]
```

**参数**：

| flag             | 必填 | 说明                                                          |
| ---------------- | ---- | ------------------------------------------------------------- |
| `--app`          | 是   | 应用 ApplicationId                                            |
| `--version`      | 否   | 按 ApplicationVersionId 过滤；缺省列全部版本下的模板             |
| `--limit`        | 否   | 返回条数上限（默认 50）                                        |
| `--with-content` | 否   | 附带每条模板的 Content（多调一次 GetInputTemplateFile）         |
| `-o/--output`    | 否   | `table` / `json`；推荐 `json` 给 SKILL 解析                     |

**JSON 输出**：

```json
{
  "ApplicationId": "app-xxxx",
  "VersionFilter": "",
  "TotalCount": 2,
  "Templates": [
    {
      "InputTemplateId": "tmpl-aaaa",
      "Name": "default",
      "Description": "默认参数模板",
      "ApplicationVersionId": "0",
      "Creator": "alice",
      "CreatorId": "1234",
      "Content": "{ \"foo\": \"bar\" }",
      "ContentValid": true
    },
    { "InputTemplateId": "tmpl-bbbb", "Name": "broken-tmpl",
      "ContentValid": false, "ContentReason": "Content 为空" }
  ]
}
```

**关键字段**：

- `InputTemplateId`：传给 `omics run --template <Id>` 即可使用该模板的内容作为运行参数 override
- `ContentValid`（仅 `--with-content` 时）：`false` 表示模板不可用，SKILL 应从候选中剔除
- `ApplicationVersionId`：模板绑定的应用版本（"0" 表示未发布版本下的通用模板）

**SKILL 主要使用场景**：

1. **form B / form C 运行前必经**：list templates → 用户拍板 → run --template <Id>（详见 SKILL.md §4.5）
2. 模板列表为空 / 全部 ContentValid=false → 引导用户改走 `--input <local.json>`
3. 排查"这个应用预设了哪些参数"

---

## 6. run — 唯一运行入口

```bash
omics run [--wdl <path> | --nf <cos-path> | --public-app <AppId> | --app <ApplicationId>] \
          [--input <inputJsonPath>] [--template <InputTemplateId>] \
          [--name <runName>] [--main <mainWdl>] \
          [--update <appId>] [--public-app-name <name>] [--nf-version <ver>] \
          [--version <VersionId>] \
          [--release-name <verName>] [--release-desc <desc>] \
          [-o table|json]
```

**版本管理 flag（v5/v6）**：

| flag | 适用形态 | 说明 |
|---|---|---|
| `--version <Id>` | A/C/D | 指定要运行的应用版本；缺省自动选最新（优先 RELEASE） |
| `--release-name <name>` | A | 仅在 `--update` 路径有意义；触发服务端 ReleaseApplicationVersion，把本次 SaveApplicationFiles 生成的新 HISTORY 版本发布为 RELEASE 并以此命名（应用维度内唯一） |
| `--release-desc <desc>` | A | 配合 `--release-name`：发布版本的描述（可选） |

**参数模板 flag（v6.1）**：

| flag | 适用形态 | 说明 |
|---|---|---|
| `--template <Id>` | B / C | SKILL 通过 `list templates` 让用户拍板后传入；CLI 调 GetInputTemplateFile 拉模板内容作为 override |
| `--input <path>`  | A / C / D（NF 必填） | 本地 JSON 作为 override；与 `--template` 互斥 |

> **`--release-name` 失败语义**：文件已成功保存（HISTORY 已入库），仅"发布命名"这一步失败时 CLI 仅给 stderr 警告，不阻塞后续 RunApplication；用户仍可通过返回的 HISTORY VersionId 运行该版本。
>
> **`--template` 失败语义**：CLI 报 `INVALID_INPUT_TEMPLATE`（拉取失败/Content 为空/非合法 JSON），SKILL 应回 list templates 让用户重选，或改用 `--input`。

### 6.1 形态分流

| flag | 形态 | 必备 | 说明 |
|---|---|---|---|
| `--wdl <path>` | A：本地 WDL | `--name` | 上传整目录 → ValidateApplication → CreateApplication（首次）/ SaveApplicationFiles（--update）；--update + --release-name 可把新 HISTORY 发布为 RELEASE |
| `--nf <cos-path>` | D：COS NF | `--name` + `--nf-version` | 服务端从 CosSource 直读源码新建 NF 应用；不支持 --update |
| `--public-app <AppId>` | B：公共应用 | 见 6.2 | ImportCommonApplication → 自动取第一个 InputTemplate → baseline+override → RunApplication |
| `--app <ApplicationId>` | C：项目内已有应用 | — | 直接 RunApplication；建议先 `list versions` 让用户选 `--version`（v6 强制） |

三者互斥（CLI 强校验）。

### 6.2 form B 的两个关键 flag

#### `--public-app-name`

| 情形 | 行为 |
|---|---|
| 用户明传 | 直接作为 `CommonAppNewName` |
| 不传 + 独立公共应用 | CLI 探测公共应用列表用 `AppName` 兜底 |
| 不传 + 合集子应用 | service 端 `DescribeCommonApp` 默认 `f_parent_app_id=''` 过滤导致探测不到 → CLI **直接报错**，要求显式传 |

#### `--nf-version`

| 情形 | 是否必填 | 报错码 |
|---|---|---|
| `AppType == NEXTFLOW` | **必填** | `MISSING_NF_VERSION`（含候选 `NextflowVersion[]`） |
| `AppType == WDL` | 传了被忽略 + 提示 | — |
| form A / form C | 传了拒绝 | `--nf-version 仅 form B 下生效` |

### 6.3 参数合并模式（baseline + override）

```text
                ValidateApplication.Inputs[].Default
                          │
                          ▼
               ┌──────────────────────┐
               │  baseline (map)      │   ← WDL 中显式声明的默认值
               └──────────┬───────────┘
                          │ Merge（浅覆盖）
               ┌──────────▼───────────┐
               │  override (map)      │   ← form B：自动 InputTemplate
               │                      │     form A/C：用户 --input 本地 JSON
               │                      │     都没传：override 为空
               └──────────┬───────────┘
                          ▼
               ┌──────────────────────┐
               │  finalParsed         │
               │  ├─ 必填全有值？ ✅ → RunApplication.Input
               │  └─ 缺失 / 类型错？❌ → PARAM_MERGE_FAILED
               └──────────────────────┘
```

`PARAM_MERGE_FAILED` JSON 报错关键字段：

- `Error`：固定 `"PARAM_MERGE_FAILED"`
- `ApplicationId` / `WorkflowName`
- `Specs[]` / `Baseline` / `UserOverride` / `FinalParsed`
- `Report.MissingRequired[]` / `EmptyRequired[]` / `ExtraFields[]` / `TypeErrors[]`
- `PartialSkeleton`：CLI 拼好的可保存即用 JSON
- `Hint[]`：下一步重跑命令模板

### 6.4 form A 整改重试（`--update`）

首次失败后 CLI stderr 给出已创建的空白 ApplicationId；重跑时**必带** `--update <appId>` 复用，避免重复建空壳：

```bash
# 首次（失败）
omics run --wdl ./pipelines/wgs/ --name wgs-2026q2 --input /tmp/run.json
# stderr: ❌ WDL Validate 未通过 ...
#         💡 应用已创建（app-aaaa-bbbb），重跑请加 --update app-aaaa-bbbb

# 修复后重跑
omics run --wdl ./pipelines/wgs/ --name wgs-2026q2 --input /tmp/run.json --update app-aaaa-bbbb
```

### 6.5 form B 内部链路（CLI 自动完成）

```
ImportCommonApplication(CommonAppUuid=AppId, CommonAppNewName=...)
   ↓ ApplicationId
DescribeInputTemplates(ApplicationId)
   ↓ InputTemplates[0]
GetInputTemplateFile(InputTemplateId)
   ↓ JSON Content
PARAM_MERGE_FAILED 检查（baseline + override）
   ↓ 通过
RunApplication(ApplicationId, Input=finalParsed)
   ↓
RunGroupId
```

---

## 7. status — 任务状态

```bash
omics status [-o table|json]              # 列 config 项目下全部批次
omics status <rgId> [-o table|json]       # 列指定批次的子任务
```

固定走 `omics_config.json::ProjectId`，不支持跨项目。

### JSON 字段

#### 列批次（不传位置参数）

```json
[
  {
    "RunGroupId": "rg-aaaa-bbbb",
    "Name": "wgs-2026q2",
    "Status": "Succeeded",
    "TotalRun": 5,
    "RunStatusCounts": [{"Status": "Succeeded", "Count": 5}],
    "ExecutionTime": {"SubmitTime": "...", "StartTime": "...", "EndTime": "..."}
  }
]
```

#### 列子任务（传 rgId）

```json
[
  {
    "RunUuid": "uuid-xxx",
    "RunGroupId": "rg-aaaa-bbbb",
    "UserDefinedId": "sample_NA12878",
    "Status": "Failed",
    "ExecutionTime": {...},
    "ErrorMessage": "exited with return code 137"
  }
]
```

---

## 8. debug — 异步失败取证（三段式 · v6 按 AppType 分流）

```bash
omics debug <runGroupId>                  # 段 1（含 AppType 列）
omics debug --run <runUuid>               # 段 2（CLI 自动按 AppType 分流采集）
omics debug --run <uuid> --job <jobId>    # 段 3
```

### 设计原则（v6）

- **CLI 端只取证不做规则匹配**——症状判断由 SKILL 模型对照 `references/runtime_error_kb.md` 决策快速表完成
- **按应用类型差异化采集**：
  - `WDL` / `WDL_GRAPH` 分支：Status + Calls + JobLogs(stderr) + PodEvents；输出清空 `Status.Command` / `Status.Meta`
  - `NEXTFLOW` 分支       ：以上 + `NextflowLog`（顶层 `nextflow.log`）；输出清空 `Status.Output`
- 三种形态严格互斥：`<runGroupId>` 与 `--run` 不可同传；`--job` 仅在 `--run` 下生效
- 段 2/3 默认会自动钻取最多 8 个失败 call 的 stderr + Pod 事件（NF 颗粒更细，从 5 提到 8）
- AppType 识别：`--type` flag > `Status.RunType` > 段 1 用 `ApplicationId` 反查 `list apps`

### 可选 flag

| flag | 作用 | 默认 |
|---|---|---|
| `--with-stdout` | 钻取作业时同时拉 stdout（默认仅 stderr）；NF 顶层也会拉 `stdout.log` | off |
| `--with-trace` | 仅 NF；额外拉 `execution_trace.txt` | off |
| `--with-reports` | 仅 NF；输出 4 个 HTML 报告的 `CosSignedUrl`（**不下载内容**） | off |
| `--type WDL\|NEXTFLOW` | 强制覆盖自动识别；正常无需传 | 自动 |

### 内部链路

| 段 | 调用的 service 接口 | 目的 |
|---|---|---|
| 1 | `RunService.DescribeRuns(RunGroupId)` + `ApplicationService.DescribeApplications`（反查 AppType） | 列子任务，标 Failed |
| 2-共用 | `RunService.GetRunStatus + GetRunCalls + 自动钻 N 个失败 call → JobService.GetRunJobLog(stderr) + MonitorService.DescribeKubernetesEvents(PLAN, JobId)` | 单子任务现场 |
| 2-NF 额外 | `RunService.GetRunMetadataFile(Key="nextflow.log")` → `CosSignedUrl` → `httpGet` 截尾（头 8KB + 尾 56KB） | NF 顶层日志 |
| 3 | 同段 2，但按 `JobId` 过滤 | 精确钻取 |

> ⚠️ 历史教训：`RunService.DescribeRunLogs` 不能用——它强校验 `req.RunUin` 必填且与 run.Uin 一致；
> CLI 走 session uin 鉴权，无 RunUin 入口，必失败。
> 已在 2026-06 第 4 次清理中**全量替换为 GetRunJobLog + DescribeKubernetesEvents**。

### 段 1 输出 JSON 关键字段

```json
{
  "RunGroupId": "rg-...",
  "ProjectId":  "...",
  "TotalRuns":  3,
  "FailedCount": 2,
  "FailedRunUuids": ["uuid-A", "uuid-B"],
  "Runs": [
    {
      "RunUuid": "uuid-A",
      "Status":  "Failed",
      "AppType": "NEXTFLOW",          // ← 新增（v6）
      "ApplicationId": "...",
      "ErrorMessage": "..."
    }
  ]
}
```

### 段 2/3 输出 JSON 关键字段

```jsonc
{
  "ProjectId": "...",
  "EnvironmentId": "...",
  "RunUuid": "...",
  "AppType": "NEXTFLOW",              // ← 必填，WDL / NEXTFLOW
  "JobIdFilter": "",
  "Status": {
    "RunType": "NEXTFLOW",
    "Status":  "Failed",
    "JobId":   "...",
    "ErrorMessage": "...",
    "Input":   "...",
    "Command": "...",                 // 仅 NF；WDL 分支已被 CLI 清空
    "Output":  ""                     // NF 分支已被 CLI 清空
  },

  // === NF 专属字段（WDL 分支不输出） ===
  "NextflowLog": "...",               // 顶层 nextflow.log，已截尾（头 8KB + 尾 56KB）
  "NextflowLogTruncated": true,
  "NextflowLogError": "",
  "ExecutionTrace": "",               // --with-trace
  "ExecutionTraceError": "",
  "StdoutLog": "",                    // --with-stdout（顶层 stdout.log）
  "StdoutLogTruncated": false,
  "StdoutLogError": "",
  "ReportUrls": {                     // --with-reports（key→signed URL，不下载内容）
    "execution_report.html": "https://...",
    "execution_timeline.html": "https://...",
    "execution_trace.txt":   "https://...",
    "pipeline_dag.html":     "https://..."
  },
  "ReportUrlsError": "",

  // === 共用 ===
  "Calls": [
    {
      "JobId": "plan-yyy",
      "CallName": "wgs.align",
      "Status": "Failed",
      "ErrorMessage": "...",
      "Runtime": "{\"cpu\":4,\"memory\":\"8G\"}",
      "WorkDir": "cos://..."
    }
  ],
  "JobLogs": [
    {
      "JobId": "plan-yyy",
      "CallName": "wgs.align",
      "Status": "Failed",
      "Runtime": "{\"cpu\":4,\"memory\":\"8G\"}",   // ← v6 新增（透传）
      "WorkDir": "cos://...",                       // ← v6 新增（透传）
      "Stderr": "...",
      "StderrTruncated": true,
      "StderrError": "",
      "Stdout": "",                                 // ← v6 新增（仅 --with-stdout）
      "StdoutTruncated": false,
      "StdoutError": "",
      "PodEvents": [
        { "Type": "Warning", "Reason": "OOMKilled", "Count": 2, "Message": "..." }
      ],
      "PodEventsError": ""
    }
  ]
}
```

### 6 条关键守则（v6）

1. **不要替用户做症状判断 + 自动改代码**：看到 OOMKilled 不要直接改 memory，要先告诉用户"目测内存不足，要把 memory 从 4G 调到 16G，确认吗"
2. **stderr / NF stdout 截尾策略**：头 4KB + 尾 24KB；**`NextflowLog` 配额加大**：头 8KB + 尾 56KB（NF 排障最高优先级输入）
3. **段 2 默认最多自动钻 8 个失败 call**——NF process 颗粒更细，多看几个找共性
4. **`Calls[]` 量大时先按 `Status==Failed` 过滤再消费**
5. **不过滤 `Reason=FailedMount`**：前端 UI 为简洁会过滤，但这是存储/CSI 挂载故障的关键信号，AI 排障必须保留
6. **NF 排障主战场是 `NextflowLog` 末尾**：若它指向具体 task hash（如 `[a1/b2c3d4]`），在 `Calls[]` 里按 `WorkDir` 末段反查具体 `JobId`，再用段 3 钻取

---

## 9. 认证机制 & 配置文件

| 项 | 路径 | 说明 |
|---|---|---|
| Token | `~/.omics-platform-cli/token.json` | OAuth 访问令牌，由 `omics login` 写入 |
| 本地配置 | `~/.omics-platform-cli/omics_config.json` | Region / ProjectId / EnvironmentId / CosBucketName |
| 鉴权机制 | session uin（`X-Session-Id` + Cookie） | 部分服务端接口要求显式 `req.RunUin` 字段，CLI 拿不到 → 必失败（不可绕过，已用替代接口） |

---

## 10. 退出码说明

| 退出码 | 含义 | SKILL 处理 |
|---|---|---|
| 0 | 成功 | 解析 stdout |
| 1 | 业务错误 | 转述 stderr；如果是"未配置"错误，引导用户在本机跑 `omics config set` |
| 2 | 鉴权失败 | 引导用户在本机跑 `omics login`，不要循环重试 |

---

## 11. 废弃命令对照表

> 下表所有命令在 CLI v4 起**不再对外暴露**；SKILL 调用时会被 argparse 当场拒绝。

| 旧命令 | 替代方案 | 说明 |
|---|---|---|
| `omics app list` | `omics list apps` | 迁移到 list 命令族 |
| `omics app list-public` | `omics list public-apps` | 迁移；输出按 AppTag 分组 |
| `omics app templates` | 内化到 `omics run` | form B 自动取第一个 InputTemplate |
| `omics app file list / get / update` | 内化到 `omics run --update` | 整目录覆盖 + 内部乐观锁回退 |
| `omics project list` | `omics config set` 校验链 | 项目选择由 config set 内置完成 |
| `omics run-app` | `omics run --public-app` / `--app` | 合并到 run |
| `omics status -p <project>` | 先 `omics config set` 切项目再 `status` | status 固定走 config 项目 |

---

> 文档版本：v4 · 7 命令边界（2026-06-01）
> 关联：[SKILL.md](../SKILL.md) / [CONTRACT.md](../CONTRACT.md) / [runtime_error_kb.md](runtime_error_kb.md)
