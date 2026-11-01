# subject

主体库是**角色跨镜一致性**的载体：生成模型按 `subject_id` 保持同一角色在不同分镜里长得一样。

## 用法

```text
reelmate subject list
reelmate subject create --set name=NAME [--set key=value ...]
reelmate subject create --set 'subjects=[{"name":"A"},{"name":"B"}]'
reelmate subject save-from-resource SP_ID RESOURCE_ID --set name=NAME --set generate_id=GENERATE_ID --set subject_type=TYPE --set 'files=["FILE_ID"]' --set 'business_list=[3]'
reelmate subject get SUBJECT_ID
reelmate subject edit SUBJECT_ID --set key=value ...
reelmate subject delete SUBJECT_ID
reelmate subject batch-details --set 'subject_ids=["s-1","s-2"]'
reelmate subject from-resource [SP_ID] --set type=TYPE --set name=NAME [--set confirm=true]
reelmate subject from-resource [SP_ID] --set @assets.json [--set confirm=true]
reelmate subject status --set 'business_ids=["b-1","b-2"]'
reelmate subject reset --set ep_id=EP_ID --set kind=match|parse
```

## 子命令说明

| 命令 | 作用 |
|---|---|
| `reelmate subject list` | 列出主体 |
| `reelmate subject create` | 创建主体，支持单条与批量 |
| `reelmate subject save-from-resource` | 把既有项目资产的指定生成记录保存为主体，不新建资产 |
| `reelmate subject get` | 查询单个主体详情 |
| `reelmate subject edit` | 修改主体 |
| `reelmate subject delete` | 删除主体 |
| `reelmate subject batch-details` | 批量查询主体详情 |
| `reelmate subject from-resource` | 建资产的同时建主体（GUI 里的「一键存为角色」），可选追加定稿 |
| `reelmate subject status` | 批量查主体审核状态，按审核中 / 通过 / 驳回三态呈现 |
| `reelmate subject reset` | 匹配重置（`kind=match`）或解析重置（`kind=parse`） |
| `reelmate subject review` | 保留入口；当前无对应前端接口，需到主体管理页面完成审核 |

## `reelmate subject list`

### 作用

列出主体。使用 `asset/actor/list`。

### 参数与输出

`--json` 输出完整列表。主体 ID 从返回里读取，不要凭记忆或从表格文本猜。

### 示例

```bash
reelmate subject list --json
```

## `reelmate subject create`

### 作用

创建主体，支持单条与批量。必填字段只有 `name`，其余字段一律透传。该命令维持原有 `df/subject/resource*` 契约，不用于把既有项目资产保存为主体。

批量走 `subjects` 数组，走的是服务端的 batch 接口而不是循环单条。

### 参数与输出

单条用 `--set name=NAME`，其余 `--set` 透传。批量用 `--set 'subjects=[{"name":"A"},{"name":"B"}]'`。写操作支持 `--dry-run` 与 `--idempotency-key`。

### 示例

```bash
reelmate subject create --set name=沈赫 --json
reelmate subject create --set 'subjects=[{"name":"沈赫"},{"name":"沈宇"}]' --json
```

## `reelmate subject save-from-resource`

### 作用

把已经存在的项目资产及用户选中的生成记录保存为主体，对应 `POST /web/v1/subject/resource`。请求通过 `sp_res_id` 绑定原资产，不创建重复资产。

它与另外两条命令的边界如下：

| 命令 | 是否新建资产 | 用途 |
|---|---:|---|
| `subject create` | 否 | 按原主体 CRUD 契约直接创建主体 |
| `subject from-resource` | 是 | 从输入素材同时新建资产和主体 |
| `subject save-from-resource` | 否 | 把已有 `resource_id` 的指定生成记录保存为主体 |

### 参数与输出

`SP_ID` 和 `RESOURCE_ID` 是前两个位置参数；`SP_ID` 也可由 `--workspace` 提供。以下字段全部必填：

| 字段 | 含义 |
|---|---|
| `name` | 主体名称 |
| `generate_id` | 用户已确认的生成记录 ID |
| `subject_type` | `0` 至 `5` 的主体分类；角色为 `1` |
| `files` | 与该生成记录对应的非空 `file_id` 数组 |
| `business_list` | 非空厂商编号数组；Seedance 为 `[3]` |

只额外接受接口已登记的 `mate_data`、`src_subject_id`。支持 `--dry-run` 与 `--idempotency-key`。

```bash
reelmate subject save-from-resource SP_ID RESOURCE_ID \
  --set name=叶辰 --set generate_id=GENERATE_ID \
  --set subject_type=1 --set 'files=["FILE_ID"]' \
  --set 'business_list=[3]' --json
```

## `reelmate subject get`

### 作用

查询单个主体详情。

### 参数与输出

位置参数 `SUBJECT_ID` 必填。`--json` 输出完整主体数据。

### 示例

```bash
reelmate subject get SUBJECT_ID --json
```

## `reelmate subject edit`

### 作用

修改主体。

### 参数与输出

位置参数 `SUBJECT_ID` 必填，`--set key=value` 透传未登记字段。写操作支持 `--dry-run` 与 `--idempotency-key`。

### 示例

```bash
reelmate subject edit SUBJECT_ID --set name=NAME --json
```

## `reelmate subject delete`

### 作用

删除主体。会改变远端数据，执行前确认目标。

### 参数与输出

位置参数 `SUBJECT_ID` 必填。写操作支持 `--dry-run` 与 `--idempotency-key`。

### 示例

```bash
reelmate subject delete SUBJECT_ID --json
```

## `reelmate subject batch-details`

### 作用

批量查询主体详情。

### 参数与输出

`--set 'subject_ids=["s-1","s-2"]'` 指定要查询的主体。

### 示例

```bash
reelmate subject batch-details --set 'subject_ids=["s-1","s-2"]' --json
```

## `reelmate subject from-resource`

### 作用

建资产的同时建主体（GUI 里的「一键存为角色」），可选追加定稿。一次调用同时产生资产和主体两个实体，返回体里 `resource_id` 与 `subject_id` 都要取。

它只用于从输入素材新建资产。对于已经存在的 `resource_id`，先按业务入口完成定稿；需要绑定用户选中的具体生成记录时，再使用 `subject save-from-resource`，不要用本命令重复创建资产。

入参与 `resource add` 同构（`type` + `name`，其余透传），批量同样走 `resources` 数组：

| 入参形态 | 走的接口 |
|---|---|
| 单条 | `resources/create-with-subject` |
| `resources` 数组 | `resources/batch-create-with-subject` |

带 `--set confirm=true` 时，在创建之后追加一次**资产定稿**（`resources/batch-confirm`）。定稿是 `resource` 侧的状态机动作，与 `reelmate resource batch-confirm` 共用同一条后端路径，不是主体侧的另一套机制。

### 参数与输出

单条：`--set type=TYPE --set name=NAME [--set confirm=true]`。批量：`--set @assets.json`。`SP_ID` 可省略并使用当前绑定。写操作支持 `--dry-run` 与 `--idempotency-key`。

### 示例

```bash
reelmate subject from-resource SP_ID --set type=character --set name=沈赫 --set confirm=true --json
reelmate subject from-resource SP_ID --set @assets.json --dry-run --json
```

## `reelmate subject status`

### 作用

批量查主体审核状态，按审核中 / 通过 / 驳回三态呈现。入参是 `business_ids` 数组，打到 `POST df/resources/subject-status`。

每条主体归入三态之一：

| 状态 | 含义 | 后续动作 |
|---|---|---|
| `reviewing` | 审核中 | 等待，可重复查询 |
| `approved` | 通过 | 可用于生成 |
| `rejected` | 驳回 | 人工申诉，**驳回不可自动重试** |

表格有 `STATUS` 列；`--json` 每项带 `status`，并把原始响应放在 `raw`。审核时长与驳回原因字段尚未文档化，拿不到时不要编造原因。

找不到已知状态字段时该条标为 `unknown`，**不要默认当成 approved**。整批全被驳回时作为错误抛出：`error.kind=moderation`、`retryable=false`。

### 参数与输出

`--set 'business_ids=["b-1","b-2"]'` 指定要查询的主体业务 ID。

### 示例

```bash
reelmate subject status --set 'business_ids=["b-1","b-2"]' --json
```

## `reelmate subject reset`

### 作用

匹配重置（`kind=match`）或解析重置（`kind=parse`）。一条命令承接两个动作，用 `--set kind=` 区分：

| kind | 后端路径 |
|---|---|
| `match` | `POST df/episode/:ep_id/resources/match-reset` |
| `parse` | `POST df/episode/:ep_id/parse-reset` |

`kind=match` 与 `reelmate resource match-reset` 共用同一条后端路径、同一处实现常量；两条命令并存是有意的（资产视角 vs 主体视角）。`kind` 取值非法时返回 usage，并列出 `match` 与 `parse`。

### 参数与输出

`--set ep_id=EP_ID` 与 `--set kind=match|parse` 必填。`kind=parse` 对应网页「重新拆解分镜」，请求体只有 `sp_id`（来自 `--workspace`），`ep_id` 只走路径；`kind` 和 `ep_id` 放进 body 会被服务端判 `740011`。写操作支持 `--dry-run` 与 `--idempotency-key`。

### 示例

```bash
reelmate subject reset --set ep_id=EP_ID --set kind=match --json
reelmate subject reset --set ep_id=EP_ID --set kind=parse --dry-run --json
```

## `reelmate subject review`

### 作用

保留入口；当前无对应前端接口，需到主体管理页面完成审核。

### 参数与输出

当前没有可调用的前端接口。不要把本命令当作已验证的审核写操作。

### 示例

```bash
reelmate subject review --help
```

## 三个 ID 不能混用

| ID | 实体 | 来源命令 |
|---|---|---|
| `subject_id` | 主体 | `subject list` / `subject create` |
| `resource_id` | 项目级资产 | `resource add` / `resource list` |
| `uk_id` | 跨项目资产库资产 | `asset-lib` |

## 注意事项

- **主体审核是异步且有失败态**。`from-resource` 返回成功不代表审核通过，必须再查 `subject status`。
- **驳回不可自动重试**。驳回项 `kind=moderation`、`retryable=false`；Agent 不得把驳当 `internal` 无脑重试，否则会触发风控。
- 所有写子命令都支持 `--dry-run` 与 `--idempotency-key`。
- `subject list` 使用 `asset/actor/list`；`subject create` 及其余旧 CRUD 使用已登记的 `df/subject/resource*`；只有 `subject save-from-resource` 使用当前前端的 `subject/resource`。发布契约没有声明这些列表是同一存储；调用方不得自行假设或混用 ID。
- 所有 ID 都要从上一步命令的 `--json` 返回里读取，不要凭记忆或从表格文本猜。
