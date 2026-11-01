# credits

查询积分余额、流水和生成前试算。试算不会扣费。

## 用法

```text
reelmate credits balance [--json]
reelmate credits log [--set key=value] [--json]
reelmate credits flows --set tab=income|consume|transfer [--set key=value ...] [--json]
reelmate credits estimate --set key=value [--set key=value ...] [--json]
```

## 子命令说明

| 命令 | 作用 |
|---|---|
| `reelmate credits balance` | 查询当前积分余额 |
| `reelmate credits log` | 查询积分流水（旧接口） |
| `reelmate credits flows` | 查询积分流水（Web 端「团队积分明细」各 tab 真正使用的接口） |
| `reelmate credits estimate` | 生成前试算消耗 |

## `reelmate credits balance`

### 作用

查询当前账号积分余额。

### 参数

- `--json`：输出 JSON。

### 输出

返回积分余额和配额信息。

### 示例

```bash
reelmate credits balance --json
```

## `reelmate credits log`

### 作用

查询积分流水。

### 参数

- `--set key=value`（可重复）：分页或筛选字段。
- `--json`：输出 JSON。

### 输出

返回积分流水列表。

### 示例

```bash
reelmate credits log --set page=1 --set page_size=20 --json
```

## `reelmate credits flows`

### 作用

查询积分流水，命中的接口和 Web 端「团队积分明细」页面的获取/消耗/流转三个 tab 是**同一个**接口（`GET /web/v1/user/credits-dashboard/flows`）。`reelmate credits log` 命中的是另一个更老的接口（`/web/v1/user/credits-log`），两者字段语义不同，不能混用：

| | `credits log`（旧） | `credits flows`（新，同 Web 消耗页） |
|---|---|---|
| 方向 | `event_type`（`1`=获取、`2`=消耗）+ 无符号 `val` | 带符号 `points`（消耗为负、获取为正） |
| 板块 | 无 | `section`（角色/场景/道具等） |
| 任务 ID | 无 | `rm_task_id`（业务任务 ID）、`volc_task_id`（仅火山/Seedance 任务非空） |

### 参数

- `--set tab=`（必填）：`income`（获取）、`consume`（消耗）或 `transfer`（流转）。CLI 只校验非空，具体取值交给服务端判断。
- `--set page=`、`--set page_size=`（可选）：分页。
- `--json`：输出 JSON。

### 用法：核对某次工作流的消耗

流水按时间段估算不可靠——同一账号在流水里可能混着其它项目、其它并发任务的记录。精确核对「实扣」的唯一可靠方法：用本轮成功返回的全部生成 `task_id`（`resource generate`、`node generate`、`storyboard batch-generate` 等），去匹配 `credits flows --set tab=consume --json` 返回的 `rm_task_id`，对匹配到的条目取 `points` 的绝对值求和。`rm_task_id` 为空、缺失或不等于本轮任务号的行不得计入实扣。禁止按时间段、`feature_name`、消耗页邻近行或任务回包 `points` 冒充实扣。

完成总结只在全匹配时输出「积分消耗」：T 为本轮生成 `task_id` 条数，M 为命中 `rm_task_id` 的条数。仅当 T≥1 且 M=T 时写「实扣 N（匹配到 T/T 条生成任务）；当前余额 B」。M<T（含部分命中、全部未入账）或 T=0 时整行不输出，禁止改写成「预估」、禁止实扣与预估并列，也不为完成总结再跑 `credits estimate`。

本轮没有任何生成 `task_id`（例如只建项、只导入已有图片）时 T=0，不输出「积分消耗」，仍要输出积分明细链接。`resource add`/`confirm-record`/`subject save-from-resource` 等动作在流水里没有对应记录，不计入 T。完成总结字段见 [_hard-gate.md](../manual/workflow/_hard-gate.md)。付费动作确认前使用统一账单展示预计消耗；`source=unavailable` 时明确展示不可估算原因。禁止把预估写成「实扣」。Agent 文本类同样只在 M=T 时写实扣。积分明细链接本轮执行 `reelmate deeplink credits --json`，固定文案「请点击以下链接，前往剧厂 Web 产品端查询积分扣除明细」。

### 示例

```bash
reelmate credits flows --set tab=consume --set page=1 --set page_size=20 --json
```

## `reelmate credits estimate`

### 作用

生成统一积分账单，不会扣费。图片和视频调用 Web 同源的 `POST /web/v1/ai/point-calculate`；资产提取、资产匹配和拆分镜复刻 Web 当前公式及首次权益；缺失资产提示词补全标为暂估。当前 Web 无可靠价格的动作返回 `source=unavailable`，不会用 0 冒充报价。完成总结不使用本命令填未匹配流水。

### 参数

三条入口，三选一：

- **生成同源**：`--set kind=`（或 `node_type`）+ `--set mode=` + `--set model=`（展示名）以及 `qty` / `ratio` / `resolution` / `duration`。TGI 2 等支持画质的模型，CLI 按生成规则缺省补 `quality=medium` 和对应 `width`/`height`。CLI 按 Web `AlgCode` 映射，文生视频是 `text_to_video`，不是提交体里的 `tomoviee_text_to_video`。
- **预演同源（推荐）**：把生成命令 `--dry-run --json` 返回的 `data.credits_estimate` 原样传入。相同参数的一批业务对象用 `business_count`；不同参数或不同模型的分组用 `requests[]`，每项包含 `alg_code`、`params` 和 `count`。CLI 会逐组询价并汇总。
- **场景公式**：`--set scenario=`。支持 `asset_extract`、`asset_match`、`script_split`、`asset_prompt_completion`、`asset_prompt`。所需字段如下：

| 场景 | 参数 | 来源 |
|---|---|---|
| `asset_extract` | `word_count` | `web_formula`，含首次提取权益 |
| `asset_match` | `text` 或 `script_content` | `web_formula`，按 JavaScript 字符数，含首次匹配权益 |
| `script_split` | `text`、`language`、`prompt_tpl_id`；可选 `route_type` / `storyboard_mode` | `web_formula`，读取 Web 动态计价规则 |
| `asset_prompt_completion` | `selected_actionable_count` | `provisional`，按当前 Web 暂行展示规则 |
| `asset_prompt` | 无 | `unavailable`，Web 已隐藏旧价格 |

剧集拆分不消耗积分，没有预估场景。不要为 `episode split` 调用 `credits estimate`，也不要展示积分预估或积分消耗；该命令返回的 `task_id` 不计入完成总结 T。

批量资产匹配是组合任务，提交后服务端会自动拆分镜，所以 `script_split` 必须在提交资产匹配前估算。官方来源的 `prompt_tpl_id` 取所选官方模板 ID（即 `match-resources` 提交的 `prompt_type`），匹配后 `episode get` 回读的 `prompt_tpl_id` 与之相同。团队一步流在提交前取不到可验证的计价模板 ID，报告不可预估；不能把团队 `uk_id` / 工作流 `workflow_id` 当作计价模板 ID，不猜值。剧集字段明确为 `0` 时传 `prompt_tpl_id=0` 使用 Web 默认计价。

也可使用原始透传：未传 `kind`/`node_type` 时，`--set alg_code=` + `--set params=`（JSON 字符串）。`alg_code` 必须是 Web `AlgCode` 或 dry-run 的 `credits_estimate.alg_code`，禁止抄生成提交体的 `tomoviee_*`。

`--json`：输出 JSON。`--set` 至少一个。

### 输出

表格含 `SOURCE`、`AVAILABLE`、`TOTAL_COST`、`BUSINESS_COUNT`，不可估算时还有 `REASON`。`--json` 的 `data` 是统一账单：`available`、`source`、`business_count`、`qty`、`total_cost`、`line_items[]`，可选 `min` / `max`、权益和原因字段。每条 `line_items[]` 给出参数、计数、单价和小计。

确认前按 `source` 选择说法：`point_calculate` / `web_formula` 只写「预计消耗」，禁止写出 `point_calculate`、`source`、「报价来源」或「Web 同源」。`provisional` 写「暂估消耗」并展示原因，`unavailable` 明确写「当前 Web 无可验证积分预估」。`total_cost=0` 仍显示 0 和权益状态，不隐藏结果，也不解释成免费。

### 示例

```bash
reelmate credits estimate --set kind=video --set mode=text2video --set model=天幕2.1 \
  --set qty=1 --set ratio=16:9 --set resolution=720p --set duration=5 --json

reelmate credits estimate --set kind=image --set mode=text2image --set model='TGI 2' \
  --set qty=1 --set business_count=6 --set ratio=16:9 --set resolution=2K --json

reelmate credits estimate --set alg_code=text_to_video \
  --set 'params="{\"ai_model_mark\":\"天幕2.1\",\"qty\":1,\"ratio\":\"16:9\",\"resolution\":\"720p\",\"duration\":5}"' \
  --json

reelmate credits estimate --set @credits-estimate.json --json

reelmate credits estimate --set scenario=asset_match --set text='本集完整剧本文本' --json

reelmate credits estimate --set scenario=script_split --set text='本集完整剧本文本' \
  --set language=zh --set prompt_tpl_id=PROMPT_TPL_ID --set storyboard_mode=true --json
```

## 注意事项

- 试算不会扣费。
- 积分不足会返回配额类错误，并在提示中给出余额查询入口。
- `log` 和 `flows` 是两个不同的后端接口，字段不能混用：`log` 是无符号 `val` + `event_type` 方向枚举，`flows` 是带符号的 `points`；要和 Web 端「团队积分明细」页面对齐，用 `flows`。
