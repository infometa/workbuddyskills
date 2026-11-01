# material

同一命令组覆盖两条创作路径，**按作用域分派**。两条路径的实体、必填字段和后端接口都不同，不可混用。

| 参数组合 | 走向 | 实体 | 必填字段 |
|---|---|---|---|
| `--canvas` + `--node` | `POST canvas/:canvas_id/materials` | 画布节点素材 | `node_id` + `material_type`(1-5) + `source` |
| `--storyboard` + `--episode` | `storyboard/:storyboard_id/info/*` | 分镜素材 `storyboard_info` | `file_id` + `category`(1图/2视/3音) + `name` + `episode_id` |

同时给出 `--canvas` 与 `--storyboard` 时报 usage，要求二选一。都不给时：`add` 按画布绑定推断；`list` / `get` / `delete` / `confirm` / `batch-add` 走制片工坊，缺 `--storyboard` 或 `--episode` 时返回 `needs_input`。

发布态以当前二进制帮助、本命令页和结构化错误为执行依据；文档未登记的字段不得猜测。

## 用法

```text
reelmate material add FILE_ID --canvas CANVAS_ID --node NODE_ID [--material-type TYPE] [--source SOURCE]
reelmate material add --storyboard SB_ID --episode EP_ID --set file_id=FILE_ID --set category=1 --set name=NAME [--set skip_confirm=true]
reelmate material batch-add --storyboard SB_ID --episode EP_ID --set @materials.json
reelmate material list --storyboard SB_ID --episode EP_ID
reelmate material get INFO_ID --storyboard SB_ID --episode EP_ID
reelmate material delete --storyboard SB_ID --episode EP_ID --set 'info_ids=["info-1"]'
reelmate material confirm --storyboard SB_ID --episode EP_ID --set 'info_ids=["info-1"]'
```

写命令接受 `--idempotency-key`，可用 `--dry-run` 预演（不发写请求，退出码 0）。

## 子命令说明

| 命令 | 作用 |
|---|---|
| `reelmate material add` | 注册画布节点素材，或挂载分镜素材 `storyboard_info` |
| `reelmate material batch-add` | 批量挂载分镜素材 |
| `reelmate material list` | 列出分镜素材 |
| `reelmate material get` | 查询单个分镜素材详情 |
| `reelmate material delete` | 删除分镜素材 |
| `reelmate material confirm` | 确认或取消确认分镜素材 |

## `reelmate material add`

### 作用

注册画布节点素材，或挂载分镜素材 `storyboard_info`。同一命令按作用域分派，两条路径的实体、必填字段和后端接口都不同，不可混用。

### 画布作用域

把已上传且审核通过的文件注册为画布素材；指定 `--node` 时同时追加到节点的 `params.referenceAssets`。

#### 参数

- `FILE_ID`（必填）：已上传文件的 `file_id`。
- `--node NODE_ID`：素材归属节点。
- `--canvas CANVAS_ID`：目标画布。
- `--material-type`：`image`/`video`/`audio`/`text`/`file`，也可用 `1`-`5`。这不是制片工坊的 `category`。
- `--source`：`ai` 或 `upload`，也可用 `1` 或 `2`；默认 `upload`。
- `--metadata JSON`、`--workspace`、`--space`、`--json`。

#### 示例

```bash
reelmate material add FILE_ID --node NODE_ID \
  --material-type image --source upload \
  --canvas CANVAS_ID --workspace WORKSPACE_ID --space SPACE_ID --json
```

### 制片工坊作用域

分镜素材挂在分镜下，实体是 `storyboard_info`，主键是 `info_id`。路径：`POST /web/v1/df/storyboard/:id/info/add`。

#### 参数（与画布侧完全分开，不要合成一张表）

- `--storyboard`、`--episode`：作用域，二者都要。
- `--set file_id=`：已上传文件。也可把 `FILE_ID` 放在位置参数。
- `--set category=`：`1` 图 / `2` 视 / `3` 音。不是 `--material-type` 的 1-5，两者不可互换。
- `--set name=`：素材名称。
- `--set skip_confirm=true`：素材直接进入定稿态；不带时保持未定稿，需再调 `confirm`。

`skip_confirm` 与 `resource confirm` 是**同一条「未定稿 ↔ 定稿」状态机的两个侧面**，不是两套机制。素材侧用 `skip_confirm` / `material confirm`，项目资产侧用 `resource confirm`。

#### 示例

```bash
reelmate material add --storyboard SB_ID --episode EP_ID --set file_id=FILE_ID --set category=1 --set name=NAME --json
```

## `reelmate material batch-add`

### 作用

批量挂载分镜素材。路径：`POST .../info/batch-add`。JSON 对象内用 `materials` 数组。结果分 `succeeded` 与 `failed` 两组；有失败时退出码非 0。

### 参数

- `--storyboard SB_ID`、`--episode EP_ID`：作用域，二者都要。
- `--set @materials.json`：对象内用 `materials` 数组。
- `--idempotency-key`、`--dry-run`、`--json`。

### 示例

```json
{
  "materials": [
    {"file_id": "F-1", "category": 1, "name": "角色定妆", "skip_confirm": true},
    {"file_id": "F-2", "category": 2, "name": "开场镜头"}
  ]
}
```

```bash
reelmate material batch-add --storyboard SB_ID --episode EP_ID --set @materials.json --json
```

## `reelmate material list`

### 作用

列出分镜素材。路径 `GET storyboard/:id/info-list`。

### 参数

- `--storyboard SB_ID`、`--episode EP_ID`：作用域，二者都要。
- `--set page=N` / `--set page_size=N` / `--set all=true`：分页。`page` 与 `page_size` 在这个接口上都是必填的，CLI 与 Web 一样传 `page=1`、`page_size=1000`。默认只取第一页，`--set page=N` 逐页取、`--set page_size=N` 改单页条数、`--set all=true` 按服务端总数一次取完；输出带 `count`、`page`、`page_size`、`has_more`、`next_page`，`has_more=true` 时不要当成全量用。
- `--json`：输出 JSON。

### 示例

```bash
reelmate material list --storyboard SB_ID --episode EP_ID --json
```

## `reelmate material get`

### 作用

查询单个分镜素材详情。路径 `GET storyboard/:id/info/:info_id/detail`。

### 参数

- `INFO_ID`（必填）：分镜素材主键。
- `--storyboard SB_ID`、`--episode EP_ID`：作用域，二者都要。
- `--json`：输出 JSON。

### 示例

```bash
reelmate material get INFO_ID --storyboard SB_ID --episode EP_ID --json
```

## `reelmate material delete`

### 作用

删除分镜素材。路径 `POST storyboard/:id/info-delete`，支持批量 `info_ids`。

### 参数

- `--storyboard SB_ID`、`--episode EP_ID`：作用域，二者都要。
- `--set 'info_ids=["info-1"]'`：要删除的素材 ID。
- `--idempotency-key`、`--dry-run`、`--json`。

### 示例

```bash
reelmate material delete --storyboard SB_ID --episode EP_ID --set 'info_ids=["info-1"]' --json
```

## `reelmate material confirm`

### 作用

确认或取消确认分镜素材。路径 `POST storyboard/:id/info-confirm`（确认与取消确认同一路径，用参数区分）。

### 参数

- `--storyboard SB_ID`、`--episode EP_ID`：作用域，二者都要。
- `--set 'info_ids=["info-1"]'`：要确认的素材 ID。
- `--idempotency-key`、`--dry-run`、`--json`。

### 示例

```bash
reelmate material confirm --storyboard SB_ID --episode EP_ID --set 'info_ids=["info-1"]' --json
```

---

## 注意事项

- 先使用 `reelmate upload PATH --json` 获取 `FILE_ID`，并确认文件已通过审核。
- Web 端历史素材抽屉当前展示图片、视频和音频；画布侧文本和文件可以注册但暂不展示。
- 素材与资产是三层不同实体，任何一层都不能替代另一层：

| 层 | 实体 | 命令组 | ID |
|---|---|---|---|
| 分镜级 | `storyboard_info` | **`material --storyboard`（本篇）** | `info_id` |
| 项目级 | `resource` | `resource` | `resource_id` |
| 跨项目 | `user_knowledge` | `asset-lib` | `uk_id` |
