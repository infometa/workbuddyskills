---
name: intelligent-kanban
tags: [data-analysis]
user-invocable: false
description: |
  基于 WeData 搭建交互式运营看板（HtmlContent 承载页面/组件 DSL，SqlSlots 承载 Datasets）。中英文环境通用。
  触发词：看板/仪表盘/驾驶舱/大盘/监控视图 | dashboard/cloud dashboard/platform dashboard/cockpit/operation board/KPI board（复合词皆算）
       | **复合表达**：平台/云端/AI/发布/分享/嵌出 + 仪表盘/dashboard；AI dashboard / 智能仪表盘 / LLM dashboard / GPT dashboard / 生成式 dashboard / Agent dashboard / 大模型仪表盘 / 智能体仪表盘。
  ⚠️ 路由：
    - 数据分析场景内，含「看板 / 仪表盘 / dashboard」任一字样，或上述英文/复合表达 + 创建/搭建/生成/create/build/generate/make → **必走本 skill**。
    - 平台/云端/AI/发布/分享/嵌出等只是限定词，不改变统一进入本 skill 的路由。
  🛑 反路由：查/看/取数/列出/统计（未同时出现看板/仪表盘/dashboard 时）；query/show/list/count/fetch → `intelligent-query`。
---

# 当前环境
- **工作空间 文件夹**（workspace_folder）：可以在SystemMessage中找到 或者 在整个上下文中最近一次的user对话中找到，<user_info>标签内有定义“Workspace Folder”的值， 如果找不到就取默认值`~/.wedata`

# 智能看板搭建（声明式 Spec 架构）

LLM 唯一编写 `kanban_spec.py`（约 80–150 行），取数 / SQL / 切片 / DSL / Dataset 入库全部由 runner 完成。

---

## 🛑 P0 硬约束（违反 = 执行失败）

> 「流程类」代码无法兜底，必须 LLM 显式遵循；「数据类」DSL/runner 已构造期 raise，按报错文本改即可。

| # | 类 | 规则 |
|---|---|------|
| 1 | 流程 | **必须 spec 模式**：构造 `Spec(...)` + 调 `build_kanban(spec)`；禁止手写 `df_to_slot_data`/`write_kanban_outputs` 调用链 |
| 2 | 流程 | **reference/ 默认只读**：业务个性化走 `Chart.chart_config` 透传 / DSL widget extras，禁为单个 spec 改 reference |
| 3 | 数据 | **raw_sql 列序契约**：用工厂 `raw_sql(title=..., sql=..., slot_columns=[...], kind=...)`（内部自动 `escape_hatch=True`）；`slot_columns` 顺序与 `SELECT` 严格一致；`FROM`/`JOIN` 后表名按 `route_hint.connection_type` 分派：**lakehouse/StarRocks/Doris 三段 `catalog.db.table`；MySQL/PG/GaussDB 两段 `db.table`**（禁占位名 `_kb_src`/`main_data`） |
| 4 | 流程 | **图表多样性**：`Spec.charts` ≥ 5 种不同 `chart_type`（用户明确只要某几种除外） |
| 5 | 数据 | **同环比用 Compare**：禁 `chart('line', metrics=[..., 'mom_xxx'])` 假装；必须 `compare(dim=time_dim(...), metric=..., kinds=['mom'])` |
| 6 | 流程 | **Step E 不主动发布**：runner 已自动调 `UpdateAiKanBan` 保存/更新 PREVIEW 并 print 追问语；禁主动调 `SaveAiKanBan` 发布态、禁 turn-id、禁二次总结，等用户输入走 Step G |
| 7 | 流程 | **修改必走 spec 重跑**：禁手改 `kanban_save_params.json` / `kanban_dsl.json`，改 spec 重跑 `build_kanban`（runner 自动保存/更新 PREVIEW，三端统一入库 DSL+Dataset） |
| 8 | 流程 | **发布/预览 helper 分离**：「保存/发布/上线/确认发布」→ `save_to_kanban_list()`（只调 `SaveAiKanBan`，入参仅 `WorkspaceId + AccessKey`，写发布态）；「保存预览/更新预览/同步预览」→ `update_to_kanban_list()`（只调 `UpdateAiKanBan`，携带 DSL/Datasets/元信息写 PREVIEW）；禁裸调 wedatacli + 拼 stdin JSON |
| 9 | 流程 | **不要查 `workspace_id`**：spec 省略该字段即可（wedatacli 自动注入）；禁 `env \| grep workspace` / `cat ~/.wedata/*` / `echo $TENCENTCLOUD_WORKSPACE_ID` 等探测 |
| 10 | 数据 | **DSL 报错按文本改**：看到 `[DSL] Chart "..." (kind=...) ...` 直接按报错文本改 spec（dsl raise 文案已带正例与修法），不改 reference / 不写新脚本 |
| 11 | 流程 | **stop 后发布/预览保存最高优先级**：Pre-routing 命中 → 必须直跳 Step G；禁误判为 Step F 重跑、禁追问、禁闲聊 |
| 12 | 数据 | **数据保真自适应**：能聚合不截断、要截断必配 `order_by`、时间型降粒度、分类基数爆炸换 kind；DSL 构造期硬约束 + Runner 软兜底（500 行/900 单元格/100 类目） |
| 13 | 流程 | **prefetch 单次原则**：每轮最多调 1 次；exit 2/3 必须直接 stop，严禁自行换关键词/扩词/翻译/拆意图重跑（唯一例外：用户回复选定表后重跑） |
| 14 | 流程 | **spec 落地位置**：文件名固定 `kanban_spec.py`，路径固定 `<workspace_folder>/.kanban_output/kanban_spec.py`（与产物同根：`kanban_save_params.json` / `kanban_dsl.json` / 数据快照 CSV）；禁写 plugin 目录/cwd 根/`/tmp`；Step F 直接覆盖同一路径 |
| 15 | 数据 | **OLAP 数据源必须走 raw_sql**：Step B `route_hint.sql_type=3`（MySQL/PG/GaussDB/StarRocks/Doris）时：① `Spec.charts` 所有项必须走 `raw_sql(title=..., sql=..., slot_columns=[...], kind=...)`，SQL 用**目标数据源原生方言**手写；② **`compare(...)` 也禁用**（内部展开会引入 `spark_safe_*`），改用 `raw_sql(kind='line', sql='WITH agg AS (...) SELECT time, curr, (curr-LAG(curr) OVER (ORDER BY time))/NULLIF(LAG(curr) OVER (ORDER BY time),0)*100 AS prev_pct FROM agg', slot_columns=['time','curr','prev_pct'])` 手写同环比；③ `Spec.kpis` 可保留 `kpi(expr, label)` 但 `expr` 只允许通用聚合（`SUM/COUNT/AVG/MIN/MAX` + 目标方言函数），禁 `spark_safe_*` / `percentile_approx`；④ `FROM/JOIN` 后表名严格按目标方言段数（MySQL/PG/GaussDB 两段 `db.table`；StarRocks/Doris 三段 `catalog.db.table`）——**cache key 双端已按尾两段归一**，段数任选一致的写法都能命中 prefetch 缓存。违反 runner 写盘前 raise。lakehouse（`sql_type=1`）路径不受影响 |
| 16 | 流程 | **禁臆断数据源不支持**：支持性判定**唯一**以 `prefetch_table.py` 输出为准——`route_hint.sql_type ∈ {1,3}` 即支持；只有脚本显式返回 `status:"route_invalid"` / `status:"not_found"` / `status:"cross_source_not_allowed"` 才是"不支持"。MySQL/PostgreSQL/GaussDB/StarRocks/Doris 全部属于 `sql_type=3` 支持路径。**作用域**：本条只约束「看板创建 / 修改流程」（Step A→G）中的对外表达；未跑 `prefetch_table.py` 或未拿到 `route_hint` 前**禁**出现「不支持 PostgreSQL / PG / MySQL / OLAP / 该数据源类型」「当前看板不支持…」「建议改用 lakehouse」等结论。若脚本已返回明确错误状态，可原样透传该状态给用户 |
| 17 | 流程 | **prefetch 成功即直进 Step C→D**：`prefetch_table.py` exit=0 拿到 schema JSON 后，本轮必须依序完成「Step B 数据概览表 → Step C 布局摘要 → Step D 写 spec + 跑 build_kanban」一次性交付，中途禁 stop / 追问 / 换工具探数。**禁裸调 `wedatacli query-data` / `wedatacli query-sql` / `wedatacli get data` 等取数子命令做数据探查**（这类命令仅 runner 内部使用）；需要看真实分布只有一种合法做法：直接把该 SQL 写进 `raw_sql(...)` chart，由 runner 通过取数链路统一执行 |

---

## 🎯 P0-10 速查（DSL 不 raise 的真陷阱）

> ⚠️ **作用域**：`spark_safe_*` / `DATEDIFF` 仅适用 lakehouse（`sql_type=1`）。OLAP（`sql_type=3`）遵 P0-15：raw_sql 用目标方言手写，禁 `spark_safe_*` / `percentile_approx`。

**时间列零返工门禁（lakehouse）**：
- `Spec.source.columns` 必须整列带 `type`；`time_dim()`/`compare()` 会在 `Spec` 构造期从裸列名回填时间类型：`date/date32` → `date`，`timestamp/datetime` 系列 → `timestamp`；缺 `type` 时默认按 `string` 处理。
- `type='date/timestamp/datetime'`：常规趋势/同环比优先 DSL（`time_dim`/`compare`）；**不要**因旧版 DuckDB `try_strptime(DATE,...)` 经验盲目改 `raw_sql`，也不要把真实类型伪装成 `string`。若必须写 lakehouse `raw_sql`，物理日期列用原生 `DATE_FORMAT(date_col,'yyyy-MM')`，不要套 `spark_safe_date_format`。
- `type='string'`：自写 metric/raw_sql 里的时间提取、比较、`DATEDIFF` 先包 `spark_safe_to_timestamp(col)`；禁 `TO_TIMESTAMP`。
- 8/14 位紧凑日期字符串：不要直接用 `time_dim`；改 `raw_sql` 显式 `spark_safe_to_timestamp_extended(col)` 后再分桶。
- 10/13 位 Unix 字符串或数值时间戳：不要依赖 `time_dim` 自动解析；需要分桶时用 `raw_sql` 显式 `FROM_UNIXTIME(col)`（毫秒先 `/1000`）后再格式化。
- `raw_sql` 不走 DSL 类型传播；时间函数、`slot_columns` 与本地 DuckDB 兼容由 SQL 自己负责。
- 🛑 **`spark_safe_*` 白名单仅 6 个**：`to_timestamp/to_date/datediff/date_format/week_format/to_timestamp_extended`；禁止发明 `spark_safe_now/spark_safe_year/spark_safe_unix_timestamp`。

**🕒 lakehouse `DATEDIFF`**（DSL raise，仅一种形态）：`DATEDIFF(end, start)` 返回 end-start 天数；`string` 列先包 `spark_safe_to_timestamp`；Unix 秒/毫秒先显式 `FROM_UNIXTIME` 转时间。❌ 全 raise：`DATEDIFF(DAY,...)` / `DATE_DIFF(...)`。⚠️ 历史数据集不宜用 `CURRENT_TIMESTAMP` 锚点，完整模板见 [kanban_spec_example.py](./kanban_spec_example.py) 第 5.17 节。**OLAP 对应**：MySQL `TIMESTAMPDIFF(DAY,s,e)`；PG/GaussDB `(e::date-s::date)`；StarRocks/Doris `datediff(e,s)`。

> 💡 **OLAP raw_sql 本地兼容**：runner 已内置 `DATE_FORMAT` 常见日期粒度格式、`TO_CHAR / TIMESTAMPDIFF / STR_TO_DATE / x::type` → DuckDB 自动翻译或原生通过（仅本地体检，远端 sqlSlots 保持目标方言原文）。看到 stderr 有 `[runner] OLAP → DuckDB` 相关日志属正常，**不要**改 spec。

**软告警告知项**（看到**不要**改 spec，runner 已自动处理）：`order_by` 含聚合→重写为实际输出别名；`kpi(...)` 传 `emoji/span/slot_key`→静默丢弃；`title` 含 emoji + `emoji=`→自动去重；raw_sql 中 `CURRENT_TIMESTAMP` / `NOW()` 在本地体检期自动改写为 `current_localtimestamp()`（远端目标方言保持原文），可直接使用不必因本地报错放弃时间过滤（历史数据集仍遵上文警示改用快照日锚点）。

**硬告警必改项**：runner 输出 `❌ [本轮 string 时间列解析失败清单]` → 把 `time_col` 换成 `Spec.source.columns` 里的 DATE/TIMESTAMP 列；无真 DATE 列时改走 `raw_sql`。

**Spec 重写门禁**：若报 `[DSL] Spec 全局契约预检失败`，必须按清单**一次性修完全部项**再重跑；重点看 `scatter` 只认 `x/y/category`、`time_dim` 排序别名为 `<col>_<gran>`、普通 DSL 禁窗口/嵌套聚合（累计/自算同环比改 `raw_sql + WITH`）。

**🔍 列引用强校验**（DSL raise）：`source.columns` 为 dict 时，`kpi/dim/metric/compare` expr 列名必须已声明；报错时二选一：①拼错→对照 Step B 改 expr；②漏写→补回 `source.columns`（带 `type`）。raw_sql / `kpi(from_sql=)` 不校验。

---
## 📐 数据保真自适应（P0-12 速查）

**4 原则**：① 能聚合不截断 ② 要截断必配 `order_by` ③ 时间型降粒度 ④ 基数爆炸换 kind。**DSL 构造期 raise（违反报错带修法）+ Runner 软兜底（500 行/900 单元格/100 类目阈值，触发时按 Top 截断非随机抽样）**。

| kind | 推荐写法 |
|------|---------|
| `scatter` | N≤500 全量；>500 加 `limit=500, order_by='-y'`；>50K 用 CASE WHEN 分桶聚合（dims[0] 必数值；裸列仅当 `source.columns` 已声明 `type='double/decimal/bigint/int'` 时合法，纯字符串列名场景写 `dim('price * 1.0', alias='price')`） |
| `table` | 优先 `[category, time_dim('time','month')]` 聚合；无聚合 runner 自动 LIMIT 50 |
| `parallel` | 前 N-1 维用 `AVG/SUM` 聚合，最后一维分类 |
| `graph` 边模式 | `limit=30, order_by='-value'` |
| `heatmap` | 两维基数 ≤ 30 直出；高基数先 SQL 降粒度或 raw_sql + CTE Top30 |
| `treemap`/`sunburst` | 单层 ≤ 100；多层用路径 |
| `boxplot` | lakehouse：C≤20 直出；20~100 可用 raw_sql + `percentile_approx`；OLAP：遵循 P0-15，用目标方言分位函数/近似方案，禁 `percentile_approx`；>100 换 `bar` |
| 时间趋势 `line`/`candlestick` | `time_dim(...,'month'/'week')` 降粒度，**不要** `limit` |

> 反例代码见 [kanban_spec_pitfalls.py](kanban_spec_pitfalls.py) 反例 14~22；DSL raise 已含修法，按需查阅。

---

## 🔗 多表场景

用户明提 ≥2 数据来源 → 多表：`Spec.source` 为主表，其他表走 `raw_sql` chart（runner 自动注册为 DuckDB 伴随视图）。硬约束：Step B 一条 `prefetch_table.py --tables "t1,t2,..."` 搞定（拆调用违 P0-13）；raw_sql 表名分派同 P0-3。三种写法（独立展示 / JOIN / UNION）见 [kanban_spec_example.py](./kanban_spec_example.py) 第 7.5 节。

> 💡 runner 打 `🔗 多表伴随视图已注册：xxx` 是多表生效信号；`Catalog "xxx" does not exist` 软告警原样重跑即愈。

---

> 🛑 **概念二分**：预览 = 入库 PREVIEW 态（runner 每次 `build_kanban` 后自动调 `UpdateAiKanBan` 保存/更新，三端统一预览源）；发布 = 写发布态（用户明说「保存/发布/上线/确认发布」时才调 `SaveAiKanBan`）。单次取数→`intelligent-query`；看板 / 仪表盘 / dashboard（含平台、云端、AI、发布、分享、嵌出等复合诉求）→ 本 skill。

---

## 🚦 Pre-routing · stop 后意图识别门（强制）

Step E/F 的 stop 之后，每收到一条新消息，回答前必走一遍词表（子串匹配、大小写/中英文同效）：

| 优先级 | 命中词（任一） | 走向 |
|---|---|---|
| **P0，发布** | 保存/发布/上线/确认发布/发布到看板列表/入库/加到仪表盘；save/publish/release | **Step G1** |
| **P0，预览** | 保存预览/更新预览/同步预览/推送预览；preview/update preview/sync preview/push preview | **Step G2** |
| P1 | 改/换/加/删/调整/重新生成/换风格/换颜色/加指标；modify/change/add/remove/adjust/regenerate/restyle | **Step F** |
| P2 | 看板/驾驶舱/大盘/仪表盘 + 表名或业务词；dashboard/cockpit/board + table/biz term（首次创建） | **Step A → E** |

**他裁**：P0+P1 默认 P0；「先改 x 再发布/保存/更新」只走 F；同时命中“发布”和“预览”默认发布（G1）；都不命中 → 常规对话（本轮禁主动调 helper / 重跑 `build_kanban` / 裸调 wedatacli）。

**P0 命中后三件事**：调 helper → 贴 `AccessKey` 1–2 行总结 → stop。禁：重跑 `build_kanban` / 裸调 wedatacli 与 Save/Update RPC / 「好的正在为您保存」「保存还是更新？」等客套追问。

---

## 主流程（Step A → G）

> 🌐 **语言一致性**：跟随用户主语言（表名/列名/SQL 标识符例外，永远原样）；单轮面向用户的字面量必同一语言（禁斩杆/括号并列）。Spec 的 `title/label/emoji` 同步。
>
> **标题对照**（中/EN任取一列）：`Step A · 需求理解` = `Requirements`；`Step B · 数据分析` = `Data Analysis`；`Step C · 布局摘要` = `Layout`；`Step D · 生成看板` = `Build`；`Step E · 验收与总结` = `Summary`。
>
> **字段对照**：`数据来源/主题/同环比口径` = `Source/Topic/Compare`；表头 `数据源\|时间字段\|关键维度\|关键指标` = `Source\|Time\|Dims\|Metrics`；`看板内容概览/数据特征提示/无` = `Overview/Data Notes/none`。默认 `按月 mom，待 Step B 确认` = `monthly mom, TBD`；追问 `请告知数据来源` = `Please specify data source`。

### Step A · 需求理解

🛑 **输出契约**：
- ✅ 先打小标题（取上方对照表 Step A 行），再进 Step B
- ✅ 标题下 1–3 行 bullet：① `**数据来源**：<原词原样>`（禁翻译） ② `**主题**：<...>` ③ `**同环比口径**：<...>`（未指定 → 用对照表默认值）
- ✅ **进 Step B 二元判定**（机械）：能抠出≥1 token（三段式/中英文裸名/模糊业务词）→ 直接进 Step B，原始 token 喂 `prefetch_table.py`；完全无数据线索 → 按对照表追问语 stop
- ❌ 禁 LLM 自判业务词「够不够具体」；禁跳 Step B；禁从历史推断表名；禁人工切多意图

> **P0**：表名解析已下沉到 `prefetch_table.py`，LLM **不要**自行调 `wedatacli search` 找表。

### Step B · 数据分析（对外标题；内部完成 schema 拉取 + 取数预取，无需暴露给用户）

**唯一允许的命令**（原样复制，把 `<用户原始输入>` 替换为用户给的表名/业务词，**支持三段式 / 中文 / 英文裸名 / 多意图`,、，与以及`分隔**；脚本内部已做表名解析 + Schema 拉取 + 后台预取 CSV，三件事一次完成）：

```bash
# 任选其一执行（已以重要性排序：先 KANBAN_REFERENCE_DIR、后 CODEBUDDY_PLUGIN_ROOT）：
export KANBAN_REFERENCE_DIR="<reference_dir>" && export WEDATA_WORKSPACE_FOLDER="<workspace_folder>" && python3 "$KANBAN_REFERENCE_DIR/prefetch_table.py" --tables "<用户原始输入>" 2>&1
# 或（DataBuddy / WorkBuddy plugin 根目录）：
export CODEBUDDY_PLUGIN_ROOT="<plugin_root>" && export WEDATA_WORKSPACE_FOLDER="<workspace_folder>" && \
_REF=""; for sub in "scenarios/data-analysis/skills/intelligent-kanban/reference" "l3-skill-scenario/intelligent-kanban/reference" "intelligent-kanban/reference"; do \
  [ -d "$CODEBUDDY_PLUGIN_ROOT/$sub" ] && _REF="$CODEBUDDY_PLUGIN_ROOT/$sub" && break; \
done; \
[ -n "$_REF" ] || { echo "❌ 未在 CODEBUDDY_PLUGIN_ROOT 下找到 intelligent-kanban/reference 目录" >&2; exit 1; }; \
python3 "$_REF/prefetch_table.py" --tables "<用户原始输入>" 2>&1
```

> `<reference_dir>` = 当前 skill 目录同级的 `reference/` 绝对路径（包含 `prefetch_table.py` / `kanban_runner.py` / `kanban_dsl.py` 的目录）；`<plugin_root>` = DataBuddy 沙箱下 plugin 根目录。两个参数按当前环境实际值填入后原样执行，不要探查 env。

**三种返回处理**（按脚本退出码 + stdout 内容分发）：

| 退出码 | stdout | LLM 行为 |
|---|---|---|
| **0** | `prefetch_table.py` 输出的 schema JSON | 进入 Step C：每张表给 3 行简报 → 写 spec |
| **2** | `{"status":"need_disambiguation","ambiguous":[{"query":"...","candidates":[...]}],"resolved":["catalog.db.table",...]?}` | **直接 stop**：先（若有 `resolved`）一行告知"已锁定: <三段式列表>"，再把每个 query 的候选**原样**展示给用户（每个子意图一组，列出 `full_name` + `comment`），等用户选；用户回复后**把已锁定 + 用户选定一起重跑同一条命令**。**禁止**自行换关键词再跑一次 prefetch |
| **3** | `{"status":"not_found","missing":["..."],"resolved":["catalog.db.table",...]?}` | **直接 stop**：先（若有 `resolved`）一行告知"已识别: <三段式列表>"，再 `未找到 "<query1>" / "<query2>"，请确认或直接给 catalog.db.table`。**严禁**自行翻译/扩词/猜表名再跑 prefetch（如把"零售"换成 retail/sales/order 试探） |
| 其它 | stderr 第一行 | stop 透传给用户 |

> 🧭 **消歧回复机械处理**：用户回复序号/表名后，只做映射并重跑上述 `prefetch_table.py`；**禁止**在重跑前按候选表的 `connection_type`、catalog 前缀、`comment` 里出现的 "PostgreSQL/MySQL/OLAP" 等字样或经验白名单判断能否创建看板。**唯一**判据是重跑后脚本的退出码与 `route_hint`（P0-16）。
>
> 📌 **`resolved` 字段**：多意图部分已锚定、其他仍歧义/缺失时，脚本仍按"一票否决"返 exit 2/3，但通过 `resolved` 透出已锚定的三段式。LLM 展示给用户（避免重复），用户补全后一起用作下一次 `--tables` 输入。

> 🛡️ **`route_hint` 路由（必看）**：
> - `sql_type=1`（lakehouse: SPARK/DLC）：LLM 无感知，直走 DSL
> - `sql_type=3`（OLAP: MySQL/PG/GaussDB/StarRocks/Doris）：遵 P0-15，所有 chart 走 `raw_sql` 且用目标方言
>
> 跨源混用由 prefetch 硬闸门拦截（exit 2 提示拆分）。

🛑 **硬约束**：
- 唯一找表/拉 schema/预取入口 = 上述 `prefetch_table.py`；禁裸调 `wedatacli search`、禁绕道脚本、禁 `cat`/`ls`/`echo $CODEBUDDY_PLUGIN_ROOT` 探查
- 失败只读 stderr **首个完整错误块**（含 `[DSL]` / `[Runner]` / `[OLAP sqlSlots 硬拦截]` 等 tag 前缀后的所有修法行）→ 按提示重跑同一条命令（不换工具、不拆调用）
- 多表/多意图必须一条命令搞定（拆调用让缓存 miss）
- 🚫 **P0-13 单次原则**：每轮最多一次 prefetch；exit 2/3 一律 stop 等用户。反例：`--tables "零售"`→exit 3 后换为 `"retail"`/`"sales,order,..."`/`"product"` 重跑都不允许（每多一次调用浪费 4–9s + 冗余后台 fork）
- 🚧 **必输出门槛**（exit=0 后**强制**，缺任一项即视为 Step B 未完成、禁止进入 Step C）：
  1. 打印 `**Step B · 数据分析**`（英文：`**Step B · Data Analysis**`）标题；对外仅出现「数据分析」或「Data Analysis」之一，禁 Schema/prefetch 等内部术语
  2. 紧跟以对照表「数据概览」开头 + **一张 Markdown 表**（每表一行，表头取对照表）；各列规范：
     - 数据源列：完整三段式（如 `DataLakeCatalog.default.tiny_orders`），禁 `<br/>` 换行
     - 时间字段列：`<col> · <type>`；无时间列填对照表「无」对应词
     - 维度列：离散列 `col:type`，`, ` 分隔，≤4 个（优先类目/地域/状态/ID）
     - 指标列：数值列 `col:type`，≤4 个（优先金额/数量/比率）；无数值列用 `count(<主键>)` 兜底
- ✅ `Spec.source.columns` 必须**列与类型双完整**：`name` 逐列**从 prefetch 返回原样抄入**（禁只抄用得上的字段，禁改列名，禁漏列——列缺失会触发 DuckDB sniffer fallback 至 VARCHAR 保底，`SUM(数值列)` 报 `sum(VARCHAR)` binder error）；`type` 保持原始表达式（如 `decimal(20,2)`、`bigint`、`string`，禁自行简化为 `decimal`/`int`）。选定 `time_col` / `time_type`（仅填 string/date/timestamp/unix；schema 里的 `datetime` 在 `time_type` 中按 timestamp 填）；若时间列 `columns[].type` 是 `date/timestamp/datetime`，保持真实类型，交给 `time_dim/compare` 自动回填，禁为绕过本地体检改假 `string`
- ❌ 禁罗列整张 schema 表（那是 `Spec.source.columns` 的事）；❌ 禁"prefetch 命令已完成 → 直接 Step C"——schema JSON 拿到后必须先渲染「数据概览」表
- 🎯 **用户诉求锁定回执**（数据概览表下方**贴 1 行**，Step C 之前最后一句，不换行不解释）：`🎯 主诉求=<用户原句核心动词短语，≤12字> · 主图型=<line|bar|pie|scatter|radar|funnel|gauge|heatmap|candlestick|table 中选 1>`；用户点名具体字段/指标时同行追加 ` · 必用字段=<列表>`；表 schema 缺该字段时追加 ` · 字段回退=<用户词>→<实际列名>`（chart title 保留用户原词，SQL 用实际列，禁 `SELECT AS <用户词>` 造字段幻觉）。**主图型判定**（无命中默认 `bar`；多命中按下表**从上到下**取首个）：`趋势/走势/变化/每月/月度/时序/trend → line` · `漏斗/流失/转化/环节 → funnel` · `散点/相关性/xx与xx的关系 → scatter` · `达成/达标/完成率/进度 → gauge` · `K线/波动/箱线/分位 → candlestick|boxplot` · `热力/交叉分布 → heatmap` · `占比/份额/构成 → pie|treemap` · `多维对比/雷达 → radar` · `列一下/名单/明细 → table` · `排行/最高/Top → bar`。回执落地后 Step C 表必满足：① 至少 1 张图 `kind` = 主图型；② 必用字段每一个都要出现在某张图的 `metrics/dims` 列
- 分析空间由 `~/.wedata/config.json:analysisSpaceKey` 固化注入，**禁**自行 `export TENCENTCLOUD_ANALYSIS_SPACE_KEY` 或在报错里建议用户改空间

> ⚠️ Spec **不要**手写 `CAST/TRY_CAST` 兜底 'null' 字面量——runner 已在 `_open_duck` 用 `read_csv(columns=..., nullstr=['null','NULL','None','\N',''])` 统一处理。

> ⚠️ **GROUP BY 维度 NULL 自动过滤**：runner 对走 GROUP BY 的图表自动追加 `<dim_sql_expr> IS NOT NULL`，消除时间列解析失败/分类 NULL/LAG 假同环比/多列 GROUP BY 污染四类静默失真。逃生口：`Dim(expr=..., description='__keep_null__')` 显式保留 NULL 桶。

### Step C · 设计看板布局

🔫 **内化检查**（脑内执行，只输出布局摘要）：写表前选型查 [kanban_spec_example.py](./kanban_spec_example.py) 第 5 节「选型决策表」（A~Q 17 行）；metric 字段必须能在 Step B 「关键指标/维度」中找到，对账失败直接换 kind。

🎯 **聚焦收敛**（脑内自检，防"1 诉求→8 张图"发散）：按 Step B 回执行 `主诉求 / 主图型` 分档控图数：
- **单诉求**（用户只提 1 个业务问题：趋势/排行/达成/明细/分布/漏斗）：**总图数 ≤ 5**（1~2 张主图 + 1~2 张辅图 + 1 组 KPI），主图型占比 ≥ 40%
- **双诉求**（"X 和 Y"/"看 X 也看 Y"）：**总图数 ≤ 7**，每条诉求至少 1 张对应主图型
- **复合看板**（用户原句含 `看板/大盘/驾驶舱/多维/全域/综合/dashboard`）：本条不生效，按用户期望展开
- **反模式**：主图型未在回执里出现时不主动加 `radar/heatmap/candlestick/boxplot/gauge`；不把趋势拆成饼图+雷达、排行拆成多张明细表

🔗 **回执一致性**（Step C 表格落地前脑内做，NO 则改表，不 stop 不重跑 prefetch）：主图型在 `kind` 列出现 ≥ 1 次；必用字段每一个都在 `dims/metrics` 列出现（缺字段走回执行的字段回退）；若发生字段回退，Step E 一句话总结加一行 `用户词=<X> · 实际列名=<Y>（表内无 <X>，用同义列 <Y>，如需精确对齐请提供含 <X> 的表）`

🧠 **准入题清单**（脑内自检，DSL 已 raise 的硬契约不重复列，仅列 DSL 不 raise 的业务语义题；任一 NO 即换 kind，**不输出给用户**）：

| 场景 | 必答准入题 |
|------|-------------------------------|
| `radar` | 能列出 ≥3 个业务有意义的 `normalize='max-norm'` 数值轴？ |
| `funnel` | 同一表能拆出 ≥2 个语义**递减**的阶段？首阶段是转化起点全量基线（不带 where 预筛），各阶段计量口径一致？ |
| `radar`/`heatmap` 分组基数 | 分组维度实际 NDV ≥ 3？否则改 `bar`/`table`（低于 3 无对比意义或单元格退化） |
| lakehouse 时间趋势/同环比 | `source.columns` 已带真实 `date/timestamp/datetime` 类型？是则用 DSL `time_dim/compare`，不要因本地体检经验改 `raw_sql` |
| 时间维 `order_by` | 引用 `time_dim(col, gran)` 时用 `<col>_<gran>`（如 `time_day`）而非裸 `<gran>`？ |
| `scatter order_by` | 散点实际输出别名固定为 `x/y/category`；排序写 `order_by='-y'`，不要写 `SUM(...)` 或 metric alias |
| `line` 时间趋势内构 | 主图 line 时优先**双轴/多序列同图**（如销售额+订单数双线），别拆成两张独立折线；聚焦少量核心指标 |
| `table` 明细内构 | 主图 table 时 `dims` 必须含实体主键/业务 ID（如 `customer_id`/`order_id`），禁只按地域/类目/时间等**汇总维度**分组代替明细 |

> 其它陷阱（boxplot 聚合 / scatter 裸分类轴 / candlestick 一字 K / parallel 行级混轴 / dim 含聚合 / scatter limit 无 order_by 等）DSL 构造期已 raise，直接按报错文本改 spec。

🛑 **输出契约**：唯一交付物 = `**Step C · 布局摘要**`（英文：`**Step C · Layout**`）标题 + 6 列表格（`# / kind / title / dims / metrics / span`），列全所有图，在 Step D 之前输出。**禁**：一句话概述代替表格；输出对账过程或 ✅ 短语。

**输出模板**（`dims`/`metrics` 列写自然语言简写，严格 DSL 在 Step D）：

```
**Step C · 布局摘要**（共 N 张图，覆盖 M 种 chart_type）

- **KPI**：总额 / 用户数 / 转化率 / 毛利率
- **图表**：

| # | kind     | title           | dims                  | metrics                       | span |
|---|----------|------------------|-----------------------|-------------------------------|------|
| 1 | line     | 日趋势           | time(day)             | SUM(sales)                    | 4    |
| 2 | bar      | TopN 类目        | category              | SUM(sales) ↓ Top10            | 2    |
| 3 | pie      | 类目占比         | category              | SUM(sales)                    | 2    |
| 4 | radar    | 类目多维         | category              | 4× normalize 数值轴            | 2    |
| 5 | gauge    | 毛利率           | —                     | 派生比率 (with target)         | 2    |
| 6 | compare  | 月度环比         | time(month)           | SUM(sales) · mom              | 2    |
| 7 | table    | 类目月销         | category, time(month) | SUM(sales) ↓                  | 4    |
```

输出完表立即进 Step D，不要额外解释/贴 spec/贴 SQL。

可用 `kind` 16 种（参考，**不要**在 Step C 输出里复述）：`line / bar / pie / scatter / radar / funnel / gauge / heatmap / candlestick / treemap / sankey / boxplot / sunburst / graph / parallel / table`

### Step D · 生成看板

本步只负责「写 spec → 跑 runner → 终端输出 `🎉 看板创建完成并已写入 PREVIEW`」，看到追问语后立即进 Step E；若输出 `❌ 看板本地产物已生成，但 PREVIEW 入库失败` 则按错误修复并重跑，不进入 Step E。

🚨 **runner Traceback 自愈回归**（仅当 runner **未输出** `🎉 看板创建完成并已写入 PREVIEW` 且抛出 `Traceback` 中断时触发；每类最多重跑 1 次 `build_kanban`；禁死循环 / 禁 stop 追问 / 禁裸调 wedatacli 探数 / 禁重跑 prefetch）：
- `ValueError: [SQL 体检失败]` → 按告警文本"错误"行改 spec（① 若是 `sum(VARCHAR)` / 列名/别名错，检查 `Spec.source.columns` 是否与 prefetch 返回列名/类型/**列数**完全一致；② 若是 Spark 独家函数报错，改用 `raw_sql(..., escape_hatch=True)`），重跑一次
- `ValueError: [Runner] <kind> 需要 dims/metrics ...` → 按报错要求补齐 dims/metrics 或换 kind，重跑一次
- `LATERAL_COLUMN_ALIAS_IN_WINDOW` / `UNRESOLVED_COLUMN.WITH_SUGGESTION`（Spark 兼容）→ SELECT 别名下移到 WITH/CTE 或把 LAG(...) 内表达式原样重写，重跑一次
- `❌ [本轮 string 时间列解析失败清单]` 失败率 ≥ 60%（**且导致 raise**）→ ① 换 `Spec.source.columns` 里真 `date/timestamp` 列做 `time_col`；② 或该列外包 `spark_safe_to_timestamp(col)` 走 `raw_sql`；schema 无真日期列且用户要月/日粒度时用现有列（如 `order_year || '-Q' || order_quarter`、`substr(dt,1,6)`）构造时间轴，chart title 保留用户原词
- 重跑仍报同类 → 原样透传给用户后 stop，禁反复重试

> ✅ **runner 已输出 `🎉 看板创建完成并已写入 PREVIEW` 时不重跑**：即使伴随 `⚠️ 数据语义校验告警` / `❌ ERROR: 共 N 个核心图表数据为空` / `WARN: <slot> 仅含表头无数据行` 等**软告警**，均为本地 sample 体检提示（prefetch sample 可能天然为空），远端 PREVIEW 已入库、用户拿到可用看板，agent 直接进 Step E，把告警**原样透传**给用户（Step E 一句话总结加一行"本地体检提示 N 项软告警：xxx；远端 PREVIEW 已入库可预览"），禁自作主张删图或改 kind

🛑 **输出契约**：必须先打 `**Step D · 生成看板**`（英文：`**Step D · Build**`）标题；下方仅允许 ① 执行命令 ② runner 原始输出。**禁提及任何 `<workspace_folder>/.kanban_output/` 下的本地文件名或路径**（包括但不限于 `kanban_spec.py` / `kanban_save_params.json` / `kanban_dsl.json` / 快照 CSV），也不要输出“Spec 文件已创建”/“Spec created”之类提示（产物就是看板链接本身，中间产物不展示）。禁末尾追加总结/验收文字。

**唯一允许的 LLM 产物模板**（文件名固定 `kanban_spec.py`，位置固定 `<workspace_folder>/.kanban_output/kanban_spec.py`，Step F 覆盖同名以保幂等）：

```python
# spec 落在 <workspace_folder>/.kanban_output/kanban_spec.py；5 件套产物同目录（含 kanban_dsl.json DSL 描述层）。
import os, sys
# reference 目录多档解析：显式目录 > plugin 根下新版、旧版、WorkBuddy 布局
_REF = os.environ.get('KANBAN_REFERENCE_DIR', '').strip()
if not _REF or not os.path.isdir(_REF):
    _PLUGIN_ROOT = os.environ.get('CODEBUDDY_PLUGIN_ROOT', '')
    for _cand in (
        os.path.join(_PLUGIN_ROOT, 'scenarios', 'data-analysis', 'skills', 'intelligent-kanban', 'reference'),
        os.path.join(_PLUGIN_ROOT, 'l3-skill-scenario', 'intelligent-kanban', 'reference'),
        os.path.join(_PLUGIN_ROOT, 'intelligent-kanban', 'reference'),
    ):
        if _PLUGIN_ROOT and os.path.isdir(_cand):
            _REF = _cand
            break
if not _REF or not os.path.isdir(_REF):
    raise SystemExit('❌ 无法定位 intelligent-kanban/reference 目录；请设置 KANBAN_REFERENCE_DIR 或 CODEBUDDY_PLUGIN_ROOT')
sys.path.insert(0, _REF)

from kanban_dsl import (
    Spec, source, kpi, metric, chart, compare, raw_sql,
    Dim, dim, time_dim, Metric,
)
from kanban_runner import build_kanban

SPEC = Spec(
    title='🏢 XXX 驾驶舱',
    # ✅ 省略 workspace_id（wedatacli 自动注入），禁自行查 env / 目录
    source=source(
        table='catalog.db.table',
        columns=[{'name':'time','type':'string'}, {'name':'amount','type':'double'}],
        time_col='time', time_type='string',
    ),
    kpis=[
        kpi('SUM(amount)', '总额', prefix='￥', format=',.0f'),
        kpi('COUNT(DISTINCT user_id)', '用户数', format=',.0f'),
        # 跨表 KPI（主表无该字段）传 from_sql 即可，runner 合并为子查询一次性执行：
        # kpi('SUM(oi.price)', '商品总额',
        #     from_sql='cat.db.orders o JOIN cat.db.items oi ON o.id=oi.oid',
        #     prefix='￥', format=',.0f'),
    ],
    charts=[
        chart('line', '日趋势',
              dims=[time_dim('time','day')],
              metrics=['SUM(amount)'],
              emoji='📈', span=4),
        chart('bar', 'TopN 类目',
              dims=['category'], metrics=['SUM(amount)'],
              order_by='-SUM(amount)', limit=10, emoji='📊', span=2),
        chart('radar', '类目多维',
              dims=['category'],
              metrics=[
                  metric('SUM(amount)', label='金额', normalize='max-norm'),
                  metric('COUNT(*)',    label='单数', normalize='max-norm'),
                  metric('AVG(amount)', label='均值', normalize='max-norm'),
              ],
              span=2, emoji='🎯'),
        chart('gauge', '完成率',
              metrics=[
                  metric('SUM(done)*100.0/NULLIF(SUM(total),0)',
                         label='完成率', format='.1f', suffix='%', target=100.0),
              ],
              span=2, emoji='⏱️'),
        compare(title='月度环比',
                dim=time_dim('time','month'),
                metric=metric('SUM(amount)', label='金额'),
                kinds=['mom'], span=3, emoji='📊'),
        chart('table', '类目月销榜',
              dims=['category', time_dim('time','month')],
              metrics=[metric('SUM(amount)', label='金额')],
              order_by='-SUM(amount)', span=4, emoji='📋'),
    ],
    theme='retail',
)

if __name__ == '__main__':
    build_kanban(SPEC)
```

**执行（spec 写盘后允许且仅允许执行下面一条命令，任选其一）**：
```bash
# 优先：显式指定 reference 目录
export KANBAN_REFERENCE_DIR="<reference_dir>" && export WEDATA_WORKSPACE_FOLDER="<workspace_folder>" && export KANBAN_OUTPUT_DIR="<workspace_folder>/.kanban_output" && mkdir -p "<workspace_folder>/.kanban_output" && ln -sf /bin/bash /bin/sh 2>/dev/null; python3 "<workspace_folder>/.kanban_output/kanban_spec.py" 2>&1
# 或（DataBuddy 沙箱默认目录结构）
export CODEBUDDY_PLUGIN_ROOT="<plugin_root>" && export WEDATA_WORKSPACE_FOLDER="<workspace_folder>" && export KANBAN_OUTPUT_DIR="<workspace_folder>/.kanban_output" && mkdir -p "<workspace_folder>/.kanban_output" && ln -sf /bin/bash /bin/sh 2>/dev/null; python3 "<workspace_folder>/.kanban_output/kanban_spec.py" 2>&1
```

> 📌 **路径说明**：spec 与产物**同根**落在 `<workspace_folder>/.kanban_output/` 下（已依赖 session 目录，WorkBuddy / DataBuddy 两端统一）。spec 文件路径固定 `<workspace_folder>/.kanban_output/kanban_spec.py`，无需 `cd` 切换目录。`kanban_dsl.json` 是本地完整排障态（含 `Datasets`）；PREVIEW/发布入库请求源是 `kanban_save_params.json`（`HtmlContent` 为不含 `Datasets` 的页面/组件 DSL，`SqlSlots` 为已 Base64 的 lowerCamelCase Dataset 数组）。

🛑 执行前/失败后**原样重跑上述命令**，禁前置探查/试导入/pip install/查 env（runner 已内置 `_ensure_duckdb()` 三级兜底，用户视角只看「runner 执行 → 🎉 看板创建完成并已写入 PREVIEW」）。

失败处理：读 stderr **首个完整错误块**（含 `[DSL]` / `[Runner]` / `❌ [OLAP sqlSlots ...]` / `[本轮 string 时间列解析失败清单]` 等 tag 前缀后的所有修法行）→ 按提示改 spec → 重跑同一条命令；禁改 `reference/`，禁绕道写新脚本。

### Step E · 验收与总结

PREVIEW 保存/更新完成后输出**唯一一段**概览（标题取对照表「看板内容概览」对应词）即结束，等用户输入。

🛑 **输出契约**：
- ✅ 顶层标题取对照表 Step E 行；下方一段精炼描述 + 图表列表，回答「展示什么 / 帮看清什么 / 同环比口径」（EN 时对应 `what to show / what to see / compare basis`）
- ✅ **看板链接必贴**：runner 输出里含 `→ https://.../dashboard/aiBoard/<AccessKey>...` 一行时，**必须**将该链接原样贴入本段概览末尾（Markdown 链接形式，标题取「打开看板」/`Open dashboard`），供用户点击跳转 DataBuddy 控制台查看。runner 未打印链接（例如缺 workspaceId/regionId）时，退化为一行「AccessKey: `<AccessKey>`」告知用户
- ✅ 若 runner 输出含 `🔄 [自动降级]` / `⚠️  [软告警]` 行 → **原样抄入**小节，小节名取对照表「数据特征提示」对应词，**禁解释/翻译/扩写**
- ❌ 禁输出 ✅ 自检/验收确认/「Spec 构造无异常」「charts=N 种」等内部校验项
- ❌ 禁在正文提及任何 `<workspace_folder>/.kanban_output/` 下的本地文件名或路径（`kanban_spec.py` / `kanban_save_params.json` / `kanban_dsl.json` / 快照 CSV 等）。产物对用户而言只有看板链接，中间产物属于内部实现不暴露
- ❌ 禁主动调 `SaveAiKanBan`·`save_to_kanban_list` 发布态；runner 已自动调 `UpdateAiKanBan` 保存/更新 PREVIEW 并 print 追问语，不要重复

### Step F · 修改（任何变更指令统一走这里）

用户任何修改类指令（颜色/标题/布局/换 kind/增删组件/调 KPI/换风格等）唯一流程：**改 spec → 重跑 `build_kanban(SPEC)`** → runner 自动保存/更新 PREVIEW + print 发布追问语 → stop 等用户。

**强约束**：
- 🛑 复用已有 `AccessKey`：spec 不传任何 file_id 即可（runner 自动读 `kanban_save_params.json` 里的 AccessKey 走 UpdateAiKanBan 覆盖）
- 🛑 禁手改 `kanban_save_params.json` / `kanban_dsl.json`，必须由 runner 产生；入库以 `UpdateAiKanBan.SqlSlots` 的 `Datasets[]` lowerCamelCase 字段为准，`HtmlContent` 只承载页面/组件 DSL
- 🛑 runner 已自动保存/更新后端 PREVIEW；**禁本轮主动覆盖发布态**，等用户回复「保存/发布/上线/确认发布」再走 G1

### Step G · 用户发布 / 预览保存指令处理

> 仅在 Pre-routing 命中 P0 后进入。本轮输出严格遵守 Pre-routing “三件事 + 禁止清单”。

#### G1. 发布到 AI 看板列表   ·   触发：保存 / 发布 / 上线 / 确认发布 等

```python
import os, sys
_REF = os.environ.get('KANBAN_REFERENCE_DIR', '').strip()
if not _REF or not os.path.isdir(_REF):
    _PLUGIN_ROOT = os.environ.get('CODEBUDDY_PLUGIN_ROOT', '') or os.getcwd()
    for _cand in (
        os.path.join(_PLUGIN_ROOT, 'scenarios', 'data-analysis', 'skills', 'intelligent-kanban', 'reference'),
        os.path.join(_PLUGIN_ROOT, 'l3-skill-scenario', 'intelligent-kanban', 'reference'),
        os.path.join(_PLUGIN_ROOT, 'intelligent-kanban', 'reference'),
        os.path.join(os.getcwd(), 'reference'),
    ):
        if os.path.isdir(_cand):
            _REF = _cand
            break
if not _REF or not os.path.isdir(_REF):
    raise SystemExit('❌ 无法定位 intelligent-kanban/reference 目录；请设置 KANBAN_REFERENCE_DIR 或 CODEBUDDY_PLUGIN_ROOT')
sys.path.insert(0, _REF)
from kanban_runner import _B  # builder helper 命名空间

result = _B['save_to_kanban_list']()  # 入参可省略，默认从 <workspace_folder>/.kanban_output 推断；只调 SaveAiKanBan
if result['status'] == 'success':
    if result.get('dashboard_url'):
        print(f'✅ 已发布：AccessKey={result["access_key"]} → {result["dashboard_url"]}')
    else:
        print(f'✅ 已发布：AccessKey={result["access_key"]}')
else:
    print(f'❌ 失败：{result["error"]}')
```

输出后立即 stop。

#### G2. 保存 / 更新 PREVIEW   ·   触发：保存预览 / 更新预览 / 同步预览 / 推送预览 等

> 特别提醒：**不要**重跑 `build_kanban(SPEC)`——上一轮 Step D/F 已生成最新 `kanban_save_params.json`；本 helper 只调 `UpdateAiKanBan`，不会覆盖发布态。

```python
import os, sys
_REF = os.environ.get('KANBAN_REFERENCE_DIR', '').strip()
if not _REF or not os.path.isdir(_REF):
    _PLUGIN_ROOT = os.environ.get('CODEBUDDY_PLUGIN_ROOT', '') or os.getcwd()
    for _cand in (
        os.path.join(_PLUGIN_ROOT, 'scenarios', 'data-analysis', 'skills', 'intelligent-kanban', 'reference'),
        os.path.join(_PLUGIN_ROOT, 'l3-skill-scenario', 'intelligent-kanban', 'reference'),
        os.path.join(_PLUGIN_ROOT, 'intelligent-kanban', 'reference'),
        os.path.join(os.getcwd(), 'reference'),
    ):
        if os.path.isdir(_cand):
            _REF = _cand
            break
if not _REF or not os.path.isdir(_REF):
    raise SystemExit('❌ 无法定位 intelligent-kanban/reference 目录；请设置 KANBAN_REFERENCE_DIR 或 CODEBUDDY_PLUGIN_ROOT')
sys.path.insert(0, _REF)
from kanban_runner import _B  # builder helper 命名空间

result = _B['update_to_kanban_list']()  # 入参可省略，默认从 <workspace_folder>/.kanban_output 推断；只调 UpdateAiKanBan
if result['status'] == 'success':
    if result.get('dashboard_url'):
        print(f'✅ 已保存预览：AccessKey={result["access_key"]} → {result["dashboard_url"]}')
    else:
        print(f'✅ 已保存预览：AccessKey={result["access_key"]}')
else:
    print(f'❌ 失败：{result["error"]}')
```

输出后立即 stop。

---

## DSL API 速查（L3 颗粒度）

```python
# 数据源
source(table=..., columns=[...], time_col=..., time_type=..., where=..., limit=10_000)

# 维度
dim('product_type')                                              # 裸列名
dim('CASE WHEN p<20 THEN "L" ELSE "H" END', alias='price_tier')  # SQL 表达式
time_dim('time','month')                                         # 时间分桶；裸列类型从 source.columns 自动回填
# ⚠️ time_dim 输出别名 = `<col>_<gran>`（如 `time_day`）不是 `<gran>`；order_by 写 `'-time_day'`，禁 `'-day'`

# 度量
metric('SUM(sales)', label='销售额')
metric('SUM(a)/NULLIF(SUM(b),0)*100', label='转化率', format='.1f', suffix='%')  # 派生比率
metric('MIN(price)', role='low')                                                    # K 线角色
metric('SUM(x)', normalize='max-norm', label='X')                                   # 雷达归一化
# string 时间列：所有时间提取/比较必包 spark_safe_to_timestamp(col)，禁 TO_TIMESTAMP
metric('AVG(DATEDIFF(spark_safe_to_timestamp(end), spark_safe_to_timestamp(start)))', label='平均时长')

# KPI
kpi('SUM(amount)', '总额', prefix='¥', format=',.0f')
kpi('COUNT(DISTINCT id)', '用户数', format=',.0f')

# 图表（16 类共用 dims+metrics）
chart(kind, title,                  # title 不写 emoji，emoji 只走 emoji= 参数
      dims=[...], metrics=[...],
      span=2, emoji='', order_by='-SUM(x)|alias|-1',
      limit=10, stacked=False, dual_axis=[1], smooth=True,
      extras={...})                                          # 透传 echarts
# ↑ chart() 不接受 from_sql=/sql=；多表 JOIN / 手写 SELECT 请改用下面的 raw_sql()

# 逃生口（OLAP sql_type=3 必用；lakehouse 复杂 SQL 可用）
raw_sql(title='标题', kind='line',
        sql='SELECT month, SUM(amt) AS amt FROM <按 P0-3 写表名> GROUP BY month ORDER BY month',
        slot_columns=['month','amt'],   # 顺序必须与 SELECT 严格一致
        span=4, emoji='📈')

# 同环比
compare(title='...', dim=time_dim(...),
        metric=metric('SUM(...)', label='...'), kinds=['mom'|'yoy'|'wow'])
```

---

## 常见图表数据约定（L3 统一抽象）

> 以下列出的 **dims/metrics 数量、角色、表达式限制** 均为 `kanban_dsl.py` 里 `Chart._CONTRACTS` 的硬契约：
> 违反会在构造 `Chart(...)` 那一刻报 `[DSL] ...`，不会拖到 runner / SQL / 前端。

| 图表 | dims | metrics | 硬契约（写错即报） |
|------|------|---------|--------------------|
| `kpi` | — | `Spec.kpis=[kpi(expr,label,...)]` | label 必填；expr 必须含聚合或为常量；跨表/JOIN 聚合传 `from_sql='cat.db.t1 a JOIN cat.db.t2 b ON ...'` |
| `line/bar` | dims[0]=分组（+可选 group） | n 度量 → n 系列 | dims ∈ [1,2]；metrics ≥ 1 |
| `pie` | dims[0]=分组 | 单度量 | dims ∈ [1,1]；metrics ∈ [1,1] |
| `scatter` | dims[0]=x，dims[1?]=color | metrics[0]=y | dims ∈ [1,2]；metrics ∈ [1,1]；**行级 limit 必配 order_by**；dims[0] 禁裸分类 |
| `radar` | dims[0]=分组 | ≥3 个度量，label=轴名，normalize='max-norm' | dims ∈ [1,1]；**metrics ≥ 3** |
| `funnel` | — | 每度量一个阶段，label=阶段名 | dims = 0；**metrics ≥ 2** |
| `gauge` | — | metrics[0]，用 metric.target 设上限 | dims = 0；metrics ∈ [1,1]；**metric.target 必填**（比率型给 100.0 / 绝对值给用户目标数） |
| `heatmap` | dims[0]=x, dims[1]=y | metrics[0]=值 | dims ∈ [2,2]；metrics ∈ [1,1] |
| `candlestick` | dims[0]=时间轴 | 4 度量 role='open/close/low/high' | dims ∈ [1,1]；metrics = 4 且**四个角色齐备** |
| `treemap/sunburst` | dims=路径（多级） | metrics[0]=值 | dims ≥ 1；metrics ∈ [1,1] |
| `sankey` | dims[0,1]=source/target | metrics[0]=权重 | dims ∈ [2,2]；metrics ∈ [1,1] |
| `boxplot` | dims[0]=分组 | metrics[0]=**行级数值表达式** | dims ∈ [1,1]；**metrics[0].expr 不能含 SUM/AVG/COUNT/MIN/MAX**（runner 内部已做 percentile_approx） |
| `graph` | dims=[节点] 或 [source,target] | 边模式 metrics[0] 必填 | dims ∈ [1,2]；metrics ∈ [0,1]；**边模式（dims=2）必配 limit** |
| `parallel` | dims[0..-2]=轴, dims[-1]=分类 | — | **dims ≥ 3**；metrics = 0；**前 N-1 维必聚合 或 配 limit**（禁行级表达式） |
| `table` | dims=列序 | metrics 可选聚合列 | dims ≥ 1；**显式 limit 必配 order_by**（无聚合时 runner 自动 LIMIT 50） |

### ⚠️ 常见误用

👉 22 类反例代码集中在 [kanban_spec_pitfalls.py](kanban_spec_pitfalls.py) `if False:` 区块（文件头按报错关键字索引）——DSL raise 文本已含修法，**多数无需查阅**，仅在 stderr 出现 `[DSL] ...` 时按需定位。

---

## 🛡️ 兜底 / 关键文件

DSL + runner + builder 三层已拦 40+ 类陷阱。LLM 只需：`[DSL] ...` 按报错改 spec；`⚠️ [Runner][软告警]` 忽略；`🔄 [自动降级]` 原样抄入 Step E。

- [kanban_spec_example.py](kanban_spec_example.py) **必读**：正例骨架（16 类 kind + 多表 7.5 节）
- [kanban_spec_pitfalls.py](kanban_spec_pitfalls.py) 按需：`[DSL] ...` 时按文件头索引 grep
- [reference/kanban_dsl.py](reference/kanban_dsl.py) 只读 DSL API；看板创建/修改流程不读不改其余 reference（维护 skill 时以 reference 为唯一真源）

---

## 🧬 DSL 描述层（第一版协议 · 三端统一入库源）

> LLM **无需感知**：DSL 生成、落盘、入库覆盖全部在 runner 内部完成，spec 形态零变化，看板创建/修改流程不需读写 `kanban_dsl.json`。此章节仅作维护/排障参考。

**产物**：`<workspace_folder>/.kanban_output/kanban_dsl.json`（Meta + UiSettings + Pages[Widgets/PageLayout] + Datasets，本地排障完整态），生成时刻 `Meta.Status='DRAFT'` / `Meta.KanbanVersion=1`。

**入库映射（三端 studio / databuddy / ai 看板列表统一使用）**：
- `UpdateAiKanBan.HtmlContent` = base64(不含 `Datasets` 的页面/组件 DSL)（不再是 HTML 原文），写入后端 PREVIEW
- `UpdateAiKanBan.SqlSlots` = base64(`Datasets` 数组)，是唯一 Dataset 入库源，写入后端 PREVIEW
- `SaveAiKanBan` 发布入参只传 `WorkspaceId + AccessKey`，后端从同 `AccessKey` 的 PREVIEW 同步 `HtmlContent` / `SqlSlots` / `DisplayName` / `ExecuteResourceId` / `RefreshSchedule` / `SessionTag` 到发布态
- `Datasets[]` 内部字段是第一版 lowerCamelCase 协议：`key/sql/metrics/dimensions/data/columns/refreshInterval/sqlType/dataSourceId/connectionType`；生成端按服务端同口径在 `data` 总量超过 128KB 时整体剥离 `data`
- 覆盖动作由 emitter 内 `_patch_save_params_with_dsl` 完成，`kanban_save_params.json` 里 HtmlContent/SqlSlots 已是 PREVIEW 入库形态；runner 每次 `build_kanban` 成功后自动调用 `UpdateAiKanBan` 写后端 PREVIEW（无 `AccessKey` 时由后端创建 PREVIEW 并返回 `AccessKey`）。

**发布语义**：`Meta.Status='DRAFT'` 只表示本地生成态；运行态以 `GetAiKanBan.Status/ViewStatus/Version` 为准。`UpdateAiKanBan` 只用于保存/更新 PREVIEW；用户明说「保存/发布/上线/确认发布」→ Step G1（`save_to_kanban_list()`，只调 `SaveAiKanBan` 且只提交 `WorkspaceId + AccessKey`）同步 PREVIEW 到发布态；用户明说「保存预览/更新预览/同步预览」→ Step G2（`update_to_kanban_list()`，只调 `UpdateAiKanBan`）不覆盖发布态。

**排障**：若终端未打印 `📄 DSL 描述层已生成: .../kanban_dsl.json` 或打印 `❌ 预览态同步失败` / `❌ 看板本地产物已生成，但 PREVIEW 入库失败` → runner 未成功写入 PREVIEW，会影响三端入库预览；按报错文本改 spec 重跑即可。

- [reference/kanban_dsl_emitter.py](reference/kanban_dsl_emitter.py) 只读 DSL emitter 实现；触点仅两处：runner 编译循环里的 `_dsl_widget_records` 收集 + `write_kanban_outputs` 之后的 `emit_dsl` 调用。
