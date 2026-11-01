# deeplink

离线生成网页深链，不读取凭据、不发网络请求。默认只打印 URL，使用 `--open` 才调用本机打开器。

## 用法

```text
reelmate deeplink canvas [--canvas CANVAS_ID] [--episode EPISODE_ID]
reelmate deeplink task [--task-id TASK_ID]
reelmate deeplink pricing
reelmate deeplink credits
reelmate deeplink project --set sp_id=SP_ID [--set creation_mode=1|2]
reelmate deeplink episode --set sp_id=SP_ID [--episode EP_ID] [--navigation-source SOURCE]
reelmate deeplink asset --set sp_id=SP_ID [--set resource_type=1|2|3|4]
reelmate deeplink asset-lib
reelmate deeplink asset-confirm --set sp_id=SP_ID --name SCRIPT_FILE_NAME --set episode_total=NUMBER
reelmate deeplink asset-extract --set sp_id=SP_ID --name SCRIPT_FILE_NAME --set episode_total=NUMBER
reelmate deeplink asset-result --set sp_id=SP_ID --name SCRIPT_FILE_NAME --set episode_total=NUMBER
```

## 子命令说明

| 命令 | 作用 |
|---|---|
| `reelmate deeplink canvas` | 生成画布页面深链 |
| `reelmate deeplink task` | 生成任务中心深链 |
| `reelmate deeplink pricing` | 生成充值弹窗深链（积分不足充值引导） |
| `reelmate deeplink credits` | 生成积分明细入口深链（剧厂首页；登录后点右上角积分查看消耗） |
| `reelmate deeplink project` | 生成项目总览页深链，并按创作模式落到制片工坊或无限画布 tab |
| `reelmate deeplink episode` | 生成项目的剧集列表页，或带 `--episode` 时生成单集分镜页深链 |
| `reelmate deeplink asset` | 生成当前项目资产页深链 |
| `reelmate deeplink asset-lib` | 生成我的资产库深链（跨项目） |
| `reelmate deeplink asset-confirm` | 生成资产确认页深链 |
| `reelmate deeplink asset-extract` | 生成资产确认页深链（兼容命令名） |
| `reelmate deeplink asset-result` | 生成资产主形态图片结果页深链 |

## `reelmate deeplink canvas`

### 作用

生成带画布上下文的网页 URL。

### 参数

- `--canvas CANVAS_ID`：画布 ID。
- `--episode EPISODE_ID`：画布所属剧集 ID。
- `--navigation-source SOURCE`：网页导航来源。
- `--data-center sz|eus|eop|sgp`：网页域映射。
- `--open`：生成后调用本机打开器。

### 输出

输出不含 token 的画布 URL。

### 示例

```bash
reelmate deeplink canvas --canvas CANVAS_ID --episode EPISODE_ID \
  --navigation-source project-overview --open
```

## `reelmate deeplink task`

### 作用

生成任务中心深链。

### 参数

- `--task-id TASK_ID`：任务 ID。
- `--data-center sz|eus|eop|sgp`：网页域映射。
- `--open`：生成后调用本机打开器。

### 输出

输出任务中心 URL。

### 示例

```bash
reelmate deeplink task --task-id TASK_ID
```

## `reelmate deeplink pricing`

### 作用

生成充值弹窗深链，不需要项目 ID，也不读取登录凭据。打开当前机房对应域名的站点根路径，查询串固定为 `action=open_pricing_popup`、本机 `device_id`、`client_source=cli`、`integration_type=plugin`、`plugin_ver`（当前 CLI 版本）。设备号无法读取时命令失败，不输出缺参链接。

### 参数

- `--data-center sz|eus|eop|sgp`：网页域映射。
- `--open`：生成后调用本机打开器。

### 输出

`https://<网页域>/?action=open_pricing_popup&device_id=<设备号>&client_source=cli&integration_type=plugin&plugin_ver=<版本>`。参数顺序固定，不按字母重排。

### 示例

```bash
reelmate deeplink pricing --data-center eus
```

缺少必填上下文时命令返回 `kind=usage` 且 `raw.needs_input=true` 的澄清信号，`raw.missing` 会列出 `sp_id`、`name` 或 `episode_total`，不会生成缺参数的半成品 URL。

## `reelmate deeplink credits`

### 作用

生成积分明细入口深链。Web 积分扣除明细是顶栏弹窗，没有独立消耗页；本命令打开 `/home`，登录后点击右上角积分查看「消耗」。不要用 `deeplink pricing` 冒充扣除明细。

### 参数

- `--data-center sz|eus|eop|sgp`：网页域映射。
- `--open`：生成后调用本机打开器。

### 示例

```bash
reelmate deeplink credits --json
```

## `reelmate deeplink project`

### 作用

生成项目总览页深链。页面 `/series-manage/<sp_id>?tab=workshop|canvas`。

Web 总览页的剧集双 tab 读 `query.tab`：`workshop` 定位到「制片工坊」，`canvas` 定位到「无限画布」。不要用手拼 tab，也不要把这条链接当成剧集列表（剧集列表仍走 `deeplink episode` 的 `/episode-list`）。

`--set creation_mode=` 取 `workspace info` 的 `data.creation_mode`：`1`（或缺省）生成 `tab=workshop`，`2` 生成 `tab=canvas`。也可用 `--set tab=workshop|canvas`，或展示名「制片工坊」「无限画布」。显式 `tab` 优先于 `creation_mode`。

### 参数

- `--set sp_id=SP_ID`：项目 ID。也可用 `--workspace SP_ID` 或环境变量 `REELMATE_PROJECT_ID`；都没有时读取当前工作区绑定。
- `--set creation_mode=1|2`：项目创作模式。制片工坊 `1`，无限画布 `2`。
- `--set tab=workshop|canvas`：总览页 tab；省略时由 `creation_mode` 推导，再缺省为 `workshop`。
- `--data-center sz|eus|eop|sgp`、`--open`。

### 示例

```bash
reelmate deeplink project --set sp_id=SP_ID --set creation_mode=1 --json
reelmate deeplink project --workspace SP_ID --set creation_mode=2 --json
```

## `reelmate deeplink episode`

### 作用

生成项目的剧集列表页，或单集分镜页深链。

不带 `--episode` 时页面是 `/episode-list?sp_id=<sp_id>&tab=workshop`（Web `episodeList`；不要用 `/series-manage/<sp_id>?tab=workshop`，也不要用 `projectId`）。带 `--episode EP_ID` 时页面是 `/series-manage/episode/<ep_id>?navigationSource=project-overview`，打开后进入该集分镜页；未显式传 `--navigation-source` 时默认 `project-overview`。不要手拼 URL。

### 参数

- `--set sp_id=SP_ID`：制片工坊项目 ID。也可用 `--workspace SP_ID`。
- `--episode EP_ID`：剧集 ID。也可用 `--set ep_id=EP_ID`。传入后生成该集分镜页，而不是剧集列表。
- `--navigation-source SOURCE`：标记网页导航来源；单集分镜页省略时默认 `project-overview`。
- `--data-center sz|eus|eop|sgp`、`--open`。

### 示例

```bash
reelmate deeplink episode --set sp_id=SP_ID --json
reelmate deeplink episode --workspace SP_ID --episode EP_ID --json
```

## `reelmate deeplink asset`

### 作用

生成当前项目的资产页深链。该页面与 `asset-lib` 不同：它带有项目 ID，打开后直接进入项目资产列表；不带 `resource_type` 时默认打开角色页。

### 参数

- `--set sp_id=SP_ID`：制片工坊项目 ID。也可用 `--workspace SP_ID`。
- `--set resource_type=1|2|3|4`：资产类型，`1=角色`、`2=场景`、`3=道具`、`4=参考视频`；省略时默认为 `1`。
- `--data-center sz|eus|eop|sgp`、`--open`。

### 示例

```bash
reelmate deeplink asset --workspace SP_ID --set resource_type=1 --json
```

## `reelmate deeplink asset-confirm`

### 作用

生成资产确认页深链。页面 `/series-manage/asset-confirm?sp_id=<sp_id>&name=<script_file_name>&episodeTotal=<number>`。

### 参数

- `--set sp_id=SP_ID`：制片工坊项目 ID。也可用 `--workspace SP_ID`。
- `--name SCRIPT_FILE_NAME`：必填，传剧本文件名并保留扩展名；也可用 `--set name=...`。
- `--set episode_total=NUMBER`：必填，传 `episode split-list` 返回的正整数剧集数；兼容 `episodeTotal` 键。
- `--data-center sz|eus|eop|sgp`、`--open`。

### 示例

```bash
reelmate deeplink asset-confirm --workspace SP_ID \
  --name SCRIPT_FILE_NAME --set episode_total=NUMBER --json
```

## `reelmate deeplink asset-extract`

### 作用

生成资产确认页深链（兼容命令名），与 `asset-confirm` 相同。

### 参数

与 `reelmate deeplink asset-confirm` 相同。

### 示例

```bash
reelmate deeplink asset-extract --workspace SP_ID \
  --name SCRIPT_FILE_NAME --set episode_total=NUMBER --json
```

## `reelmate deeplink asset-result`

### 作用

生成资产主形态图片结果页深链。页面 `/series-manage/asset-extract?sp_id=<sp_id>&name=<script_file_name>&episodeTotal=<number>`。

### 参数

与 `reelmate deeplink asset-confirm` 相同。

### 示例

```bash
reelmate deeplink asset-result --workspace SP_ID \
  --name SCRIPT_FILE_NAME --set episode_total=NUMBER --json
```

## `reelmate deeplink asset-lib`

### 作用

生成「我的资产库」深链。资产库是**跨项目**的，因此不接受项目 ID。项目级资产的确认入口是 `asset-confirm`，两者不是同一个页面。

### 参数

- `--data-center sz|eus|eop|sgp`：网页域映射。
- `--open`：生成后调用本机打开器。
- `--json`：输出 JSON。不接受项目 ID。

### 示例

```bash
reelmate deeplink asset-lib --json
```

## 注意事项

- `CANVAS_ID`、`EPISODE_ID`、`TASK_ID` 和 `SP_ID` 必须来自已有命令结果，CLI 不会凭空生成业务 ID。
- URL 不包含 token 或语言前缀；该命令不验证网页链接是否能打开。
- 页面路径依据技术方案 3.13 节的前端路由表与真实页面验证。`asset-confirm` 使用页面实际要求的 `sp_id`、`name`、`episodeTotal`；其它路由维持各自的前端 query 命名。
