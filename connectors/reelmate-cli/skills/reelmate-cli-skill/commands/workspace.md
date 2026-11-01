# workspace

工作区支持两种创作模式；`creation_mode=1` 表示制片工坊，`creation_mode=2` 表示无限画布。CLI 默认创建制片工坊工作区，画面比例默认 `9:16`（竖屏）。

## 用法

```text
reelmate workspace create NAME [--space SPACE_ID] [--set creation_mode=1|2] [--set sp_type=1|2|3] [--set ratio=9:16|16:9] [--set group_ids=GROUP] [--dry-run]
reelmate workspace list [--space SPACE_ID]
reelmate workspace info WORKSPACE_ID
reelmate workspace edit WORKSPACE_ID NAME
reelmate workspace delete WORKSPACE_ID
reelmate workspace use WORKSPACE_ID [--global]
reelmate workspace show
```

## 子命令说明

| 命令 | 作用 |
| `reelmate workspace create NAME` | 创建工作区 |
|---|---|
| `reelmate workspace list` | 查看当前空间工作区 |
| `reelmate workspace info WORKSPACE_ID` | 查看工作区详情 |
| `reelmate workspace edit WORKSPACE_ID NAME` | 修改工作区名称 |
| `reelmate workspace delete WORKSPACE_ID` | 删除工作区 |
| `reelmate workspace use WORKSPACE_ID` | 绑定当前工作区 |
| `reelmate workspace show` | 查看当前绑定 |

## `reelmate workspace create NAME`

### 作用

创建工作区。未显式覆盖时创建制片工坊工作区，画面比例为 `9:16`。

### 参数

- `NAME`（必填）：工作区名称，也可使用 `--name NAME`。
- `--space SPACE_ID`（必填或可自动解析）：目标空间。
- `--set creation_mode=1|2`：覆盖创作模式；问用户只写制片工坊、无限画布。默认 `1`（制片工坊）。
- `--set sp_type=1|2|3`：剧目类型。问用户只按此顺序写名称：国内仿真人剧、海外仿真人剧、2D/3D动漫；不要带 `sp_type` 或数字，也不要列出 Web「自定义」。选完后对应提交 `2`/`3`/`1`。必填。
- `--set ratio=9:16|16:9`：覆盖画面比例；问用户写 `9:16 竖屏`、`16:9 横屏`，提交仍用 `9:16` / `16:9`。默认 `9:16`。
- `--set group_ids=GROUP`：覆盖所属成员组，包括 `0` 和数字组 ID；传入后不再查询成员组。不传时 CLI 读取 `GET /web/v1/df/novel/member-groups`：不可跨组且 `current_group_id` 是真实组时提交该组；可跨组、接口失败、没有数据，以及不可跨组但 `current_group_id` 为空或 `0` 时，提交 `0`（团队直属）。后一种情况要选别的组，必须自行传入 `--set group_ids`。不要为此再问用户。空字符串会被拒绝。
- `--dry-run`：只输出将提交的创建参数（含解析后的 `group_ids`），不发送创建请求。创建参数里没有 `team_id`；空间仍用 `--space` 对应的请求头。
- `--idempotency-key KEY`、`--json`：幂等键和输出格式。

### 输出

返回 `workspace_id`、名称、`space_id` 和 `creation_mode`。

### 示例

```bash
reelmate workspace create demo --space SPACE_ID --set creation_mode=1 --set sp_type=1 --set ratio=16:9 --dry-run --json
reelmate workspace create demo --space SPACE_ID --set creation_mode=1 --set sp_type=1 --set ratio=16:9 --json
reelmate workspace create canvas-demo --space SPACE_ID --set creation_mode=2 --set sp_type=2 --set ratio=9:16 --json
```

## `reelmate workspace list`

### 作用

列出当前空间中的工作区。单页 50 条，与 Web 的团队项目列表页一致。

所有列表命令的分页口径一致：**默认只取第一页**，`--set page=N` 逐页取、`--set page_size=N` 改单页条数、`--set all=true` 按服务端总数一次取完。输出带 `count`（服务端总数）、`page`、`page_size`、`has_more`、`next_page`；`has_more=true` 时不要把这份列表当成全量去做批量操作或判断某条记录不存在。

### 参数

- `--space SPACE_ID`：指定空间。
- `--set page=N` / `--set page_size=N` / `--set all=true`：分页。
- `--json`：输出 JSON。

### 输出

返回工作区名称、ID、所属空间和画布摘要。

### 示例

```bash
reelmate workspace list --space SPACE_ID --json
```

## `reelmate workspace info WORKSPACE_ID`

### 作用

查询工作区详情。

### 参数

- `WORKSPACE_ID`（必填）：目标工作区。
- `--workspace WORKSPACE_ID`：也可通过选项提供 ID。
- `--space SPACE_ID`、`--json`：作用域和输出格式。

### 输出

返回工作区详情和关联画布信息。`--json` 的 `data` 里除绑定字段外还带 `sp_type` 与 `ratio`（服务端未返回时这两个键不出现，不要把缺失当成 `0`）。

`sp_type` 是选模型和提示词模板的前提。问用户只按此顺序写名称：国内仿真人剧、海外仿真人剧、2D/3D动漫；不要带 `sp_type` 或数字。选完后对应提交 `2`/`3`/`1`。`episode prompt-templates` 与 `model list` 的 id 空间按它隔离，**必须读出来再用，不能按项目名推断**；`workspace edit` 只改名称，建完的项目改不了 `sp_type`。

### 示例

```bash
reelmate workspace info WORKSPACE_ID --json
```

## `reelmate workspace edit WORKSPACE_ID NAME`

### 作用

修改工作区名称。

### 参数

- `WORKSPACE_ID`、`NAME`（必填）：工作区 ID 和新名称。
- `--name NAME`：也可使用选项提供新名称。
- `--space SPACE_ID`、`--idempotency-key KEY`：作用域和幂等键。

### 输出

返回更新后的工作区摘要。

### 示例

```bash
reelmate workspace edit WORKSPACE_ID renamed --idempotency-key KEY --json
```

## `reelmate workspace delete WORKSPACE_ID`

### 作用

删除工作区。

### 参数

- `WORKSPACE_ID`（必填）：目标工作区。
- `--space SPACE_ID`、`--idempotency-key KEY`：作用域和幂等键。

### 输出

返回删除结果。

### 示例

```bash
reelmate workspace delete WORKSPACE_ID --idempotency-key KEY --json
```

## `reelmate workspace use WORKSPACE_ID`

### 作用

将工作区绑定到当前项目；`--global` 时写入用户级配置。

### 参数

- `WORKSPACE_ID`（必填）：要绑定的工作区。
- `--global`：写入 `REELMATE_CONFIG_DIR`，否则写入项目根 `.reelmate/workspace.json`。

### 输出

返回绑定后的工作区摘要。

### 示例

```bash
reelmate workspace use WORKSPACE_ID
reelmate workspace use WORKSPACE_ID --global
```

## `reelmate workspace show`

### 作用

查看当前项目或用户级绑定。

### 参数

- `--json`：输出 JSON。

### 输出

返回绑定的工作区、空间、团队和可用画布信息。

### 示例

```bash
reelmate workspace show --json
```

## 注意事项

- 作用域优先级为显式 flag、环境变量、项目绑定、用户级绑定，最后回退到凭据缓存空间。
- 常用变量为 `REELMATE_WORKSPACE_ID`、`REELMATE_SPACE_ID` 和 `REELMATE_CONFIG_DIR`。
