# 无限画布：一键生成剧本并持续对话

从用户的一句话意图开始，定位或创建无限画布，创建文本节点并默认使用 TG Chat 5.5 生成剧本；用户继续修改时新建文本节点、连接上一轮结果并再次生成。

契约：[_hard-gate.md](_hard-gate.md)、[_hitl-present.md](_hitl-present.md)、[_bootstrap.md](_bootstrap.md)、[_models.md](_models.md)。

## 步骤表

| 步 | 包 | 完成谓词 |
|---|---|---|
| 1/5 | 登录并探测画布 | `workflow detect --scope canvas` 已执行；且下列之一成立：已有画布经用户确认、已从 `workspace list` 选定无限画布项目、或确认没有可复用画布因而转入第 2 步新建 |
| 2/5 | 创建画布项目 | 已绑定 `WORKSPACE_ID` 与 `CANVAS_ID`，或本步因已有画布跳过。创作模式固定为无限画布（`creation_mode=2`），复述展示名、不询问制片工坊还是无限画布；未列出已有无限画布项目并经用户放弃前不得 `workspace create`；新建时按 [_bootstrap.md](_bootstrap.md) 先预检 `project.create`，通过后再完成 `hitl.project-create`（剧目类型、画面比例，展示名与 Web 新建项目一致） |
| 3/5 | 选择文本模型 | `TEXT_MODEL` 取自当次 `model search 'TG Chat'` 中 `type`/`types` 含 `file` 且 `visible=true` 的展示名；含 TG Chat 5.5 时直接采用，不向用户确认模型 |
| 4/5 | 首轮生成 | 任务终态成功且节点返回非空文本；交付画布深链，不要输出剧本文本 |
| 5/5 | 持续对话 | 每轮新节点 + `pipeline` 连线 + 生成成功；交付画布深链，不要输出剧本文本 |

## 1. 探测画布

按 [_bootstrap.md](_bootstrap.md) 确认登录。然后：

```bash
reelmate workflow detect --scope canvas --json
```

若返回可用的 `workspace_id` 和 `canvas_id`，向用户确认是否在该画布继续。确认后记下当次 `WORKSPACE_ID` 与 `CANVAS_ID`，再 detect 一次后进入第 3 步：

```bash
reelmate workflow detect --scope canvas --workspace WORKSPACE_ID --json
```

定位不到画布时，按 [_bootstrap.md](_bootstrap.md) 执行 `workspace list`，只把 `creation_mode=2` 的无限画布项目（名称和 ID）列给用户。用户选定后记下 `WORKSPACE_ID` 并进入第 3 步。没有候选或用户明确要新建时进入第 2 步。已绑定的制片工坊项目（`creation_mode=1`）不能直接拿来写无限画布。项目和画布都拿到之前不创建节点、不提交生成。

## 2. 创建画布项目

按 [_bootstrap.md](_bootstrap.md) 先预检 `project.create`，通过后再完成 `hitl.project-create`（创作模式钉死无限画布并复述；剧目类型、画面比例用网页展示名），创建工作区，再创建画布。未先列出已有无限画布项目并经用户放弃前，不得 `workspace create`。`CANVAS_ID` 和 `EPISODE_ID` 取当次 JSON。

## 3. 选择文本模型

按 [_models.md](_models.md) 用 `model search 'TG Chat'` 现查。目录没有可用文本模型时停止。筛完后的展示名含 TG Chat 5.5 时直接采用，不走 HITL、不弹选择器、不列回退列表。目录没有该项时停止，不改推其它模型。本步不是 [_hard-gate.md](_hard-gate.md) 的确认项。

## 4. 首轮生成

用户意图记为 `USER_PROMPT`。

```bash
reelmate node create text --workspace WORKSPACE_ID --canvas CANVAS_ID \
  --set name='剧本-第1轮' --set prompt=USER_PROMPT --set model=TEXT_MODEL \
  --idempotency-key NODE_KEY_1 --json
reelmate node generate text --workspace WORKSPACE_ID --canvas CANVAS_ID --node NODE_ID_1 \
  --set ai_model_mark=TEXT_MODEL --set prompt=USER_PROMPT \
  --idempotency-key TASK_KEY_1 --json
reelmate task wait TASK_ID_1 --timeout 30m --json
reelmate task get TASK_ID_1 --json
reelmate node get NODE_ID_1 --workspace WORKSPACE_ID --canvas CANVAS_ID --json
```

`NODE_ID_1` 取创建结果，`TASK_ID_1` 取生成结果。`node create` 只建节点，但必须同时写入 `prompt` 和 `model`。后续 `node generate text --node` 会在创建任务前合并写回同一组参数；写回失败时不提交。超时先查原任务，不重复提交。

`done_when`：任务终态成功，且节点返回非空文本。交付规则与第 5 步相同：只给画布深链，不要输出剧本文本。

## 5. 持续对话

每一轮新建文本节点，不覆盖上一轮。第 N 轮输入为 `FOLLOW_UP_PROMPT`，上一轮节点为 `NODE_ID_PREV`：

```bash
reelmate node create text --workspace WORKSPACE_ID --canvas CANVAS_ID \
  --set name='剧本-第N轮' --set prompt=FOLLOW_UP_PROMPT --set model=TEXT_MODEL \
  --idempotency-key NODE_KEY_N --json
reelmate node --workspace WORKSPACE_ID --canvas CANVAS_ID \
  --left NODE_ID_PREV --right NODE_ID_N --semantic pipeline --json
reelmate node generate text --workspace WORKSPACE_ID --canvas CANVAS_ID --node NODE_ID_N \
  --set ai_model_mark=TEXT_MODEL --set prompt=FOLLOW_UP_PROMPT \
  --idempotency-key TASK_KEY_N --json
reelmate task wait TASK_ID_N --timeout 30m --json
reelmate node get NODE_ID_N --workspace WORKSPACE_ID --canvas CANVAS_ID --json
```

已有关系不会重复创建。需要为同一新节点增加多个上下文来源时，`--right` 只能有一个：

```bash
reelmate node --workspace WORKSPACE_ID --canvas CANVAS_ID \
  --left-add SOURCE_NODE_ID --right NODE_ID_N --semantic reference --json
```

用户要拆资产、拆分镜、上传剧本或出片时走交接段，整句不得当作 `FOLLOW_UP_PROMPT`。

每轮 `done_when` 后只交付画布深链（下面这条命令的 `links[0].href` 或 `data.href`）、`NODE_ID`、`TASK_ID`。不要输出剧本文本，不要把剧本正文写入聊天或 `outputs/` 之外的文件。

```bash
reelmate deeplink canvas --canvas CANVAS_ID --episode EPISODE_ID \
  --navigation-source project-overview --json
```

不返回任务深链。另按 [_hard-gate.md](_hard-gate.md) 输出固定完成总结（积分消耗仅当流水全匹配时输出，积分明细链接始终保留）。`needs_input` 只按 `missing[]` 追问，不因此新建项目或重复提交已成功的任务。

## 交接：拆资产 / 拆分镜 / 上传剧本 / 出片

本段不是第 6 步，不改上面 5/5 分母。只在路由命中交接、且本画布已有生成成功的文本节点时执行。

剧本源只取**最新一次** `task wait` 成功的文本节点：本会话已有成功节点时用最新一轮 `NODE_ID`；否则从当前画布节点列表取最近一次生成成功的文本节点。不要问用户选哪一轮，不要回溯旧节点。

```bash
reelmate node get NODE_ID --workspace WORKSPACE_ID --canvas CANVAS_ID --json
```

优先读 `text_result.content`，为空再读 `node get` 返回的等价文本字段，不编造路径。节点为空或 `task wait` 未成功时停止交接，不 `upload`，不把残缺正文写入聊天。

把生成正文写入当前工作目录 `outputs/script.txt`（`outputs/` 不存在则创建；文件已存在则覆盖）。不要把剧本文本写入聊天。

然后用**同一个** `WORKSPACE_ID`（即当前无限画布项目）进入制片四环节：

```bash
reelmate workflow detect --scope studio --workspace WORKSPACE_ID --json
```

禁止加载 [gui-script-video-project.md](gui-script-video-project.md)，禁止 `workspace create`，禁止另建 `creation_mode=1` 项目。按 [gui-script-video.md](gui-script-video.md) 只加载当前阶段文件。主路径：`upload` `outputs/script.txt` → `episode split` → `episode batch-create`。不要用只填名字的单集 `episode add`。环节 3 读 [gui-script-video-asset.md](gui-script-video-asset.md)，环节 4 读 [gui-script-video-storyboard.md](gui-script-video-storyboard.md) 的 1/3、2/3；分镜拆解成功后必须走 `hitl.shot-result-confirm`，未确认不得 `storyboard batch-generate`。
