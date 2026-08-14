# App Resolution Guide

## 目的

在执行 `dataset`、`data`、`sql`、`bff` 之前，先判断当前任务是否需要做“应用决议”。

应用决议的目标只有一个：确定这次操作应该落在哪个已发布、可运行态访问的 app 上。不要把它和“刷新配置”“同步应用列表”混在一起。

这份指引面向 AI / Agent。重点不是“会不会查 app”，而是“如何把 app 决议做得足够准”。

## 直接使用当前应用的场景

满足以下任一条件时，直接进入业务命令，不先跑 `lovrabet app list`：

1. 用户已经显式给了 `--appcode`
2. 用户已经显式给了 `--app <name>`
3. 当前问题明显延续上文，且 app 上下文没有变化
4. 用户明确说“当前应用”“默认应用”，且没有新的业务域线索

`defaultApp` 只是弱候选，不是强上下文。不要因为配置里存在 `defaultApp` 就直接认定它正确；也不要一上来就跳到全量 `app list`。未显式指定 app 时，先在默认候选里按关键词验证数据集是否匹配。

## 必须先做应用决议的场景

出现以下情况时，才扩大到：

```bash
lovrabet app list
```

`app list` 默认只返回已发布应用。未发布应用即使在 `app list --include-unpublished` 中可见，也只用于排查，不作为 `dataset` / `data` / `sql` / `bff` 的候选。

典型场景：

1. 用户只给了业务需求，没有给 app 线索
2. 当前没有显式 `--appcode` / `--app`，且需求里有业务域、对象名或数据集线索
3. 需求可能落在多个 app 中
4. 用户明确要求“先看看有哪些应用”
5. 已经在 `defaultApp` 下按关键词验证过，但没有合理数据集命中

## 标准决议流程

1. 先看是否已有明确 app 上下文
2. 没有明确上下文但有 `defaultApp` 时，先验证默认候选：

```bash
lovrabet dataset list --name "<关键词>"
```

3. 如果默认候选命中的数据集名称、字段、描述贴合需求，继续使用默认候选
4. 如果默认候选无命中、弱命中或语义不合理，再 `lovrabet app list`
5. 根据业务关键词先挑 1-3 个候选 app
6. 用候选 app 做一次验证式收敛：

```bash
lovrabet dataset list --app <name> --name "<关键词>"
```

7. 命中后再进入 `dataset detail`、`data *`、`sql *`、`bff *`

## AI 如何挑候选 app

不要只盯着 `name`。应综合看这些信息：

1. `name`
   - 业务域关键词是否直接匹配
   - 是否是用户原话中的简称、系统名、团队名

2. `description` / `appDesc`
   - 是否明确描述了业务边界
   - 是否包含目标对象、场景、部门、流程关键词

3. 当前上下文
   - 用户前文是否一直在说某个业务域
   - 默认候选 app 是否已经稳定服务于这个业务域

4. 验证结果
   - 默认候选下的 `dataset list --name "<关键词>"` 是否能命中
   - `dataset list --app <name> --name "<关键词>"` 是否能命中
   - 命中的数据集名称、字段是否真的贴合需求

## 推荐评分思路

可以按下面的优先级判断：

1. **强匹配**
   - app 名称直接命中业务关键词
   - description 明确描述同一业务域

2. **中匹配**
   - 名称不完全一致，但 description 或 owner / status 信息支持它是对的
   - 在 `dataset list` 中命中相关数据集

3. **弱匹配**
   - 只有名称模糊相关
   - 没有 description 支撑
   - `dataset list` 验证也不明显

弱匹配不要直接拍板。

## 优先使用 description 的场景

以下场景只看 app 名很容易误判，应主动参考 description：

- 名称过短，例如 `crm`、`erp`、`oms`
- 多个 app 名称都很接近
- app 名称偏内部缩写，业务语义不直接
- 用户用自然语言描述需求，而不是产品名

如果 `app list --format json` 返回里带有 `description` / `appDesc`，优先把它作为候选排序的重要依据。

## 不确定时如何处理

当候选 app 仍然有 2 个以上都合理时，不要硬选一个。

应先给出 1-2 个最可能的候选，并说明理由，然后询问用户确认。推荐表达方式：

```text
我现在更怀疑是这两个应用：
1. crm：description 更接近客户资料/跟进场景
2. oms：名称和订单流程更接近

我可以先按 crm 继续查数据集；如果你指的是订单侧应用，我再切到 oms。
```

如果已经有验证结果，也应带上：

```text
我先在 crm 里搜到“客户档案”“联系人”两个数据集，在 oms 里没有明显命中。
我先按 crm 继续。
```

## 何时可以直接默认继续

满足下面任一条件，可以默认继续，不必反问用户：

- 当前只有一个强匹配候选
- 当前 `defaultApp` 下的数据集验证结果与需求语义一致，且没有冲突迹象
- 已经通过 `dataset list` 验证出明显命中

## 何时必须问用户

出现以下情况时，应主动确认：

- 两个以上候选都能自圆其说
- `dataset list` 在多个 app 下都有命中
- 用户给的是组织/部门语义，而不是系统语义
- 当前默认 app 与本次需求明显可能冲突

## 不要这样做

- 不要每次都机械地先跑 `app list`
- 不要只看 app 名就直接认定目标 app
- 不要忽略 `description` / `appDesc`
- 不要在候选不明确时静默硬选一个继续执行高影响操作
- 不要因为本地配置里没有 app 信息，就判定该 app 不存在
- 不要把远端 app 目录重新写回 `.lovrabet.json`

## 当前架构要点

- 应用目录来源：远端接口 + 本地 cache
- 本地配置只保存用户意图：`defaultApp`、顶层 `appcode`
- `defaultApp` 是默认候选；未显式指定 app 时先验证它，验证不成立再扩大搜索
- `lovrabet app list`：远端优先
- `lovrabet app pull`：只做手动刷新 cache
- 当前目录尚未绑定应用时，用 `lovrabet workspace init --app <name>` 建立绑定；已有绑定时用 `lovrabet workspace use --app <name>` 修改。跨环境操作时带上和 `app list` 相同的 `--env`
