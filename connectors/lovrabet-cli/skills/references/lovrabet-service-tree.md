# Service Tree 业务服务树

Service Tree 把底层 `data` / `sql` / `bff` 命令封装成业务命令，例如：

```bash
lovrabet crm customer list --status active
lovrabet crm customer detail 10001
```

本地 registry 位于 `~/.lovrabet/service.json`。首期 manifest 文件通常由 Git 管理，再通过 `service import` 安装到本机。

## 本地管理命令

```bash
lovrabet service validate --file ./lovrabet-services/crm.service.json
lovrabet service validate --file ~/.lovrabet/service.json
lovrabet service import --file ./lovrabet-services/crm.service.json --dry-run
lovrabet service import --file ./lovrabet-services/crm.service.json
lovrabet service import --file ~/.lovrabet/service.json --dry-run
lovrabet service list
lovrabet service detail --service crm
lovrabet service export --service crm --file ./lovrabet-services/crm.service.json
lovrabet service remove --service crm
```

`service validate` 只校验 JSON 协议，不写入本地 registry。`service validate/import --file` 同时接受单个 Service Tree manifest 和本地 registry 文件（`~/.lovrabet/service.json`）；传入 registry 时会逐个校验或导入其中保存的原始 manifest。`service import` 会把 manifest 标准化后写入 `~/.lovrabet/service.json`，同一个服务再次导入会替换旧版本。`service export` 从本地 registry 导出 Git 可管理的单个 manifest 文件。`service remove` 只移除本机 registry 条目，不删除 Git 中的 manifest 文件，也不会访问服务端。

## 意图识别与主动发现

当用户说的是业务目标，而不是底层 CLI 命令时，Agent 应先检查本机是否已经导入对应的业务语义服务。典型业务目标包括“查我的需求”“看项目评论”“列出待处理订单”“客户详情”“库存预警”“工单跟进”等。

首选发现命令：

```bash
lovrabet service list --format compress
```

`service list` 是本地只读命令，不需要访问服务端。Agent 应使用返回的服务编码、服务名称、服务说明、命令路径、命令说明和 flags 描述来匹配用户意图。匹配明确时，再查看完整服务定义：

```bash
lovrabet service detail --service <service> --format compress
```

`service detail` 只读取本地 registry 中已导入的 manifest、标准化绑定和来源信息，不是服务端实时契约。对本地文件来源，返回的 `version`、`importedAt`、`source.path` 和 `source.hash` 可用于核对版本与来源；其他来源应使用与来源类型匹配的来源、新鲜度和兼容性证据，字段缺失本身不是拒绝理由。它可以验证本机路由，却不能证明绑定目标仍已发布、参数未变化或副作用明确；执行前还要使用目标能力支持的可信契约验证通道，并只使用该通道实际返回的字段。

Service Tree 只负责定位入口，不单独证明稳定业务规则已经固化。若绑定目标是 Dataset，稳定规则还必须由业务 Skill、已治理 Dataset 契约或其他平台已确认契约承载；缺少规则契约时只能用于简单低风险事实查询。

完成契约、真实副作用和用户授权判断后，才执行匹配到的动态业务命令：

```bash
lovrabet <service> [...resourcePath] <action> [flags] --format compress
```

Service Tree 精确命中时，先把已经绑定的执行入口只作为候选路由。取得与来源类型匹配的来源、新鲜度和兼容性证据，并确认与当前可信业务 Skill 或平台契约没有冲突后，才复用该入口。本地文件来源可以使用 `version`、`importedAt` 和 `source.hash`；后续来源使用各自适配器提供的证据，不把当前字段组合固化为永久门禁。无法确认来源或适用范围时，不得仅凭精确命中执行稳定规则。执行前仍要核对绑定目标、真实副作用和用户授权。

出现弱命中、多个候选或术语边界不清时，先用 `kb search` 做语义消歧。KB 召回只生成候选；Service Tree 候选先用本地 `service detail` 核对绑定，再使用目标能力支持的可信契约验证通道。消歧后仍有多个合理候选时，再列给用户确认。

Service Tree 未命中不是失败条件，也不代表业务能力不存在。本地 registry 可能只注册少量高频服务。没有合理匹配时：

1. 先区分简单低风险事实、稳定规则和高风险确定性判断。
2. 简单低风险事实可以继续做 app、Dataset 决议，并使用只读 Instant API。
3. 稳定规则或高风险确定性判断不得直接退化为 Dataset 字段拼装；没有可信能力时输出局部“不判定”，并说明缺少的能力契约。
4. 只有现有上下文、KB 和只读发现都不能收敛时，才向用户询问一个最关键的补充信息。

用户已经显式给出 `datasetCode`、`sqlCode`、Backend Function 标识，或明确要求执行底层 `data/sql/bff` 命令时，不需要额外跑 Service Tree 发现，直接进入对应 Detail。`--appcode` / `--app` 只是应用上下文，不应单独阻止业务服务发现。

## 推荐 Manifest 写法

推荐使用树状结构：`service` 定义服务入口，`resources` 定义业务对象，`actions` 定义动作。最终命令格式是：

```text
lovrabet <service> <resource path> <action>
```

最小示例：

```json
{
  "service": "crm",
  "name": "CRM",
  "description": "Customer relationship business commands.",
  "app": "app-xxxxxxxx",
  "resources": {
    "customer": {
      "name": "Customer",
      "datasetCode": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "actions": {
        "list": {
          "description": "List customers.",
          "flags": {
            "status": "where.status.$eq",
            "keyword": {
              "to": "where.customer_name",
              "op": "$contain",
              "description": "Customer keyword."
            }
          },
          "defaults": {
            "currentPage": 1,
            "pageSize": 20,
            "orderBy": [{ "updated_at": "desc" }]
          }
        },
        "detail": {
          "description": "Get one customer by id.",
          "action": "getOne",
          "args": ["id"],
          "map": {
            "id": {
              "target": "id",
              "transform": "number"
            }
          }
        }
      }
    }
  }
}
```

上面会注册两个业务命令：

```bash
lovrabet crm customer list --status active --keyword 科技
lovrabet crm customer detail 10001
```

等价的底层能力分别是：

```bash
lovrabet data filter --code aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa --params '{"where":{"status":{"$eq":"active"},"customer_name":{"$contain":"科技"}},"currentPage":1,"pageSize":20,"orderBy":[{"updated_at":"desc"}]}'
lovrabet data getOne --code aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa --params '{"id":10001}'
```

## 顶层字段

| 字段 | 说明 |
| --- | --- |
| `service` | 服务编码，进入命令路径，例如 `crm`。也兼容 `{ "code": "crm", "name": "CRM" }`。 |
| `name` / `description` | 展示名称和说明，会出现在 help、schema、doctor 中。 |
| `app` | 单应用快捷绑定。可写 appcode 或应用名。 |
| `apps` | 多应用绑定表，例如 `{ "crm": "app-xxx", "order": { "appcode": "app-yyy", "env": "prod" } }`。 |
| `appBindings` | 兼容旧命名，语义同 `apps`。 |
| `defaults` | 服务级默认底层参数，会被资源和动作继承。 |
| `resources` | 业务对象树。每个节点可继续嵌套 `resources`。 |

不要把 `service` 写成 appcode。一个服务可能串联多个应用，`service` 应表达业务域，例如 `crm`、`order`、`store-ops`。

## Resource 字段

| 字段 | 说明 |
| --- | --- |
| `name` / `description` | 业务对象展示信息。 |
| `appRef` | 引用 `apps` / `appBindings` 里的应用别名。只有多应用时通常需要写。 |
| `datasetCode` | 数据集 code，推荐优先使用。 |
| `datatable` / `table` | 物理表名。未写 `datasetCode` 时，运行时会按表名解析 dataset code。 |
| `defaults` / `params` | 资源级默认底层参数，例如分页、排序、固定条件。 |
| `actions` | 该业务对象上的动作，例如 `list`、`mine`、`detail`、`create`。 |
| `resources` | 子业务对象。用于 `lovrabet crm customer contact list` 这类更深路径。 |

## Action 字段

| 字段 | 说明 |
| --- | --- |
| `description` | 命令说明。 |
| `action` | 动作简写。默认 `filter`，可写 `getOne`、`create`、`update`、`delete`，也可写 `sql.exec`、`bff.exec`。 |
| `kind` / `command` | `action` 的展开写法，例如 `{ "kind": "data", "command": "filter" }`。 |
| `datasetCode` / `datatable` | 覆盖资源继承的数据集定位。 |
| `sqlCode` | SQL 执行编码，配合 `action: "sql.exec"` 使用。 |
| `functionName` | Backend Function ENDPOINT 名称，配合 `action: "bff.exec"` 使用。 |
| `args` | 位置参数。字符串简写会自动变成必填参数。 |
| `flags` | 可选参数。推荐对象写法。 |
| `defaults` / `params` | 动作级默认底层参数。 |
| `map` / `mapTo` | 显式映射规则。`map` 是推荐短名，`mapTo` 兼容旧名。 |
| `risk` | 风险等级。只读可省略；写入用 `write`，删除/不可逆操作用 `high-risk-write`。 |

Backend Function 动作示例：

```json
{
  "description": "Process an order.",
  "action": "bff.exec",
  "functionName": "processOrder",
  "params": { "source": "service-tree" }
}
```

## flags 和 map

`flags` 推荐对象写法：

```json
{
  "flags": {
    "status": "where.status.$eq",
    "ownerId": {
      "to": "where.owner_id",
      "op": "$eq",
      "type": "number",
      "transform": "number"
    },
    "startDate": {
      "to": "where.created_at",
      "op": "$gte"
    }
  }
}
```

对外使用时，camelCase flag 会自动转成 kebab-case：

```bash
lovrabet crm customer list --owner-id 12 --start-date 2026-01-01
```

`map` 适合位置参数、上下文和固定值：

```json
{
  "args": ["id"],
  "map": {
    "id": { "target": "id", "transform": "number" },
    "context.userId": { "target": "where.owner_id", "operator": "$eq", "transform": "number" },
    "const.deleted": { "target": "where.deleted", "operator": "$eq", "value": 0 }
  }
}
```

未带前缀的 `map` key 会按名字自动匹配 `args` 或 `flags`；匹配不到时按 `flags.<name>` 处理。显式来源仍支持 `flags.`、`args.`、`context.`、`ctx.` 和 `const.`。

## 数据集定位

data target 推荐直接配置 `datasetCode`。如果只配置 `datatable` / `table`，动态命令执行时会在当前 app 的数据集列表中按物理表名解析 dataset code；解析失败时命令会停止，并提示补充 `datasetCode` 或确认表名。

## 发现与诊断

导入后的业务服务会出现在 CLI 发现面：

```bash
lovrabet service list --format compress
lovrabet service detail --service <service> --format compress
lovrabet --help
lovrabet schema --format compress
lovrabet doctor
```

`lovrabet service list/detail` 是 Agent 根据业务意图主动发现本机动态服务的轻量入口；`lovrabet --help` 会列出本地已导入服务及其多级业务命令；`lovrabet schema` 会把动态业务命令作为机器可读 command schema 导出；`lovrabet doctor` 会展示本机 registry 路径、加载状态、服务数、命令数和每个服务的 manifest 来源文件。

动态命令仍走 Lovrabet CLI 的统一 runner：认证、appcode 决议、已发布应用访问限制、risk、dry-run、`--format` 和 `--jq` 都会生效。manifest 的应用绑定只提供默认值；用户显式传入的 `--appcode`、`--app`、`--env` 优先。

## 兼容旧格式

旧版 `commands` 数组仍然可用，但不再作为推荐写法：

```json
{
  "service": { "code": "crm", "name": "CRM" },
  "commands": [
    {
      "path": "customer list",
      "description": "List customers.",
      "target": {
        "kind": "data",
        "command": "filter",
        "datasetCode": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
      }
    }
  ]
}
```

新配置优先使用 `resources/actions`，因为它能自然表达业务对象层级，也避免在 JSON key 或 `path` 里用空格拼命令。

## 边界

- Service Tree 本地 registry 是运行态发现和执行入口，不是服务端配置中心。
- `service import/export` 只管理本机 `~/.lovrabet/service.json`，不会上传服务端。
- 动态命令不会绕过应用发布状态和当前 AK 权限。
- Runtime registry 只消费 manifest 中已经绑定的目标，不枚举 SQL、函数源码或其他实现资产。
