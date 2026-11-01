# market

剧本广场命令组。

## 用法

```text
reelmate market list [--set key=value]
reelmate market get NM_ID
reelmate market character NM_ID
reelmate market episode NM_ID [--set start_episode_no=N] [--set end_episode_no=N]
reelmate market mine [--set key=value]
```

## 子命令说明

| 命令 | 作用 |
|---|---|
| `reelmate market list` | 查看剧本广场列表 |
| `reelmate market get` | 查看指定剧本详情 |
| `reelmate market character` | 查看指定剧本角色 |
| `reelmate market episode` | 查看指定剧本分集信息 |
| `reelmate market mine` | 查看当前账号的我的剧本 |

所有已接入命令都支持 `--space SPACE_ID` 和 `--json` / `--ndjson`。`--json` 保留完整结果，不会用表格投影替换原始响应。

## `reelmate market list`

### 作用

查看剧本广场列表。

### 参数与输出

| 参数 | 必填 | 说明 |
|---|---|---|
| `page` | 否 | 页码；CLI 默认 `1` |
| `page_size` | 否 | 每页数量；CLI 默认 `20` |
| `keyword` | 否 | 文本搜索关键字 |
| `category_id` | 否 | 分类 ID |
| `tag_ids` | 否 | 多个标签 ID 用逗号分隔；也可在 JSON 输入中传数组 |

表格输出 `NM_ID`、`TITLE`、`CATEGORY_NAME`、`AUTHOR_NAME`、`STATUS`、`EPISODE_TOTAL`。

### 示例

```bash
reelmate market list --set page=2 --set page_size=20 --set keyword='悬疑' --set tag_ids='tag-a,tag-b' --set category_id=cat-1
```

## `reelmate market get`

### 作用

查看指定剧本详情。不接受 `--set`。位置参数是剧本广场返回的 `nm_id`。

### 参数与输出

表格输出 `NM_ID`、`TITLE`、`CATEGORY_NAME`、`STATUS`、`EPISODE_TOTAL`、`PREVIEW_EPISODE_NUM`、`LEVEL`、`SCORE`。

### 示例

```bash
reelmate market get NM_ID --json
```

## `reelmate market character`

### 作用

查看指定剧本角色。不接受 `--set`。位置参数是 `NM_ID`。

### 参数与输出

表格输出 `NM_ID`、`CHARACTER_ID`、`CHARACTER_NUM`、`NAME`、`TYPE`。

### 示例

```bash
reelmate market character NM_ID
```

## `reelmate market episode`

### 作用

查看指定剧本分集信息。位置参数是 `NM_ID`。

### 参数与输出

支持 `start_episode_no` 和 `end_episode_no`，用于限定返回的分集区间。表格输出 `CHAPTER_NO`、`CHAPTER_TITLE`、`EPISODE_NO`、`EPISODE_TITLE`、`LOCKED`。

### 示例

```bash
reelmate market episode NM_ID --set start_episode_no=1 --set end_episode_no=10 --json
```

## `reelmate market mine`

### 作用

查看当前账号的我的剧本。返回的是小说项目 `nt_id`，不能与广场 `nm_id` 混用。

### 参数与输出

支持筛选参数：`status`、`draft_status`、`script_name`、`nt_ids`、`page`、`page_size`、`order`、`task_type`、`task_progress`、`special_status`、`group_id`、`agent_lock`。表格输出 `NT_ID`、`TITLE`、`STATUS`。

### 示例

```bash
reelmate market mine --json
```

## 注意事项

- `get`、`character`、`episode` 的位置参数是剧本广场返回的 `nm_id`；`mine` 返回的是小说项目 `nt_id`，两者不能混用。
- 远程请求或业务失败会转为 CLI 错误。
