# workflow

探测「用户在创作链路上做到哪一步了」，并支持从任意环节断点续跑。

阶段判定由 CLI 完成，**不要凭对话记忆推断**。动作之前先跑一次 `detect`。

## 用法

```text
reelmate workflow detect [--scope studio|canvas]
reelmate workflow status [--scope studio|canvas] [--name NAME]
reelmate workflow resume --from STAGE [--scope studio|canvas] [--name NAME]
```

## 子命令说明

| 命令 | 作用 |
|---|---|
| `reelmate workflow detect` | 只读探测远端阶段游标 |
| `reelmate workflow status` | 同 detect，另附上次执行位置的本地记录 |
| `reelmate workflow resume` | 以 `--from` 指定的阶段为起点重算待办，并记录当前位置 |

## `reelmate workflow detect`

### 作用

只读探测远端阶段游标。只发 GET，不触发写操作。`stage` 是第一个未完成阶段。

### 参数

| 参数 | 必填 | 说明 |
|---|---:|---|
| `--scope studio\|canvas` | 否 | 作用域，默认 `studio` |
| `--workspace SP_ID` | 否 | 制片工坊项目 ID；省略时用当前绑定 |
| `--canvas CANVAS_ID` | 否 | 画布 ID；省略时用当前绑定 |
| `--json` | 否 | 输出 JSON |

### 示例

```bash
reelmate workflow detect --scope studio --json
reelmate workflow detect --scope canvas --canvas CANVAS_ID --json
```

## `reelmate workflow status`

### 作用

同 `detect`，另附上次执行位置的本地记录。`local_record` 不参与阶段判定。

### 参数

与 `reelmate workflow detect` 相同，另可传 `--name NAME`（本地记录名，默认 `default`）。

### 示例

```bash
reelmate workflow status --scope studio --json
```

## `reelmate workflow resume`

### 作用

以 `--from` 指定的阶段为起点重算待办，并记录当前位置。仍以实时探测的前置条件为准。

### 参数

| 参数 | 必填 | 说明 |
|---|---:|---|
| `--from STAGE` | 是 | 起点阶段，取值为五档之一 |
| `--scope studio\|canvas` | 否 | 作用域，默认 `studio` |
| `--name NAME` | 否 | 本地记录名，默认 `default` |
| `--json` | 否 | 输出 JSON |

### 示例

```bash
reelmate workflow resume --from asset --scope studio --json
```

## 五档阶段

| 阶段 | 制片工坊（studio）含义 | 画布（canvas）含义 |
|---|---|---|
| `project` | 已绑定制片工坊项目 | 已绑定画布 |
| `script` | 项目下已有剧集（剧本已导入并拆解） | 画布上已有承载剧本的文本节点 |
| `asset` | 项目下已有已定稿资产 | 画布上已有拆资产节点或图片节点 |
| `storyboard` | 剧集下已有分镜 | 画布上已有拆分镜节点或表格节点 |
| `render` | 终态：产物是否满意由用户确认，探测不替他判定完成 | 同左 |

阶段顺序固定为 `project → script → asset → storyboard → render`。`stage` 是**第一个未完成**的阶段。

## 探测来源

全部是现有只读接口，探测**只发 GET**，不触发任何写操作：

| 阶段 | studio 来源 | canvas 来源 |
|---|---|---|
| `project` | 当前工作区绑定 | 当前画布绑定 |
| `script` | `GET df/episode/list`；为空时回退 `GET df/script_project/:sp_id/split-list` | `GET df/canvas/{canvas_id}` 的 `node_list` |
| `asset` | `GET df/resources/list?status=2` | 同上 |
| `storyboard` | 对每个正式剧集查询 `GET df/episode/{ep_id}/storyboard-list`；空白占位时回退 `parse-result`，仅所有剧集都非空且成功才算完成 | 同上 |

## 参数

| 参数 | 说明 |
|---|---|
| `--scope studio\|canvas` | 作用域，默认 `studio` |
| `--from STAGE` | `resume` 的起点阶段，取值为五档之一 |
| `--workspace SP_ID` | 制片工坊项目 ID；省略时用当前绑定 |
| `--canvas CANVAS_ID` | 画布 ID；省略时用当前绑定 |
| `--name NAME` | 本地记录名，默认 `default` |
| `--json` | 输出 JSON |

## 输出

```json
{
  "scope": "studio",
  "stage": "asset",
  "completed": ["project", "script"],
  "pending": ["asset", "storyboard", "render"],
  "missing": [
    { "field": "resource", "reason": "项目下没有已定稿资产", "goto_stage": "asset" }
  ],
  "next_command": "reelmate resource extract SP_ID --dry-run --json"
}
```

`missing` 的每一项都带 `goto_stage`，指出该回到哪一档补齐。缺项回引规则固定为：

| 缺什么 | 回到 |
|---|---|
| 项目 | `project` |
| 剧本 | `script` |
| 资产 | `asset` |
| 分镜 | `storyboard` |
| 配模型 / 渲染 | `render` |

完整阶段机、HITL 与续跑规则见 [../manual/workflow/_stage-machine.md](../manual/workflow/_stage-machine.md)。不要凭对话记忆推断阶段。

## 示例

```bash
reelmate workflow detect --scope studio --json
reelmate workflow detect --scope canvas --canvas CANVAS_ID --json
reelmate workflow resume --from asset --scope studio --json
```

## 注意事项

- 阶段机、本地 `status`/`resume` 记录和 `next_command` 由客户端实现；远端探测只发只读请求。发布态以当前二进制和本命令页为执行契约。
- **探测不是错误路径**：探不到项目、剧本或资产时仍返回退出码 0，缺项通过 `data.missing` 表达。只有网络或鉴权失败才走错误 envelope。
- **探测只给建议，不自动执行**。`next_command` 是给调用方看的字符串，需要由调用方决定是否执行。
- 「资产就绪」按正式资产列表的 `status=2`（已定稿）判定，至少返回一条即完成资产档。
- `status` 里的 `local_record` 只是「上次执行到哪一档」的本地备忘，**不参与阶段判定**。
- `--scope` 在 `cache` 命令组里表示缓存清理范围（`models|env|uploads`），在本命令组里表示作用域（`studio|canvas`），两者取值不通用。
