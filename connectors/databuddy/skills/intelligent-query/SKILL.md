---
name: intelligent-query
tags: [data-analysis]
user-invocable: false
description: 用户只是询问一些简单的数据查询的问题时使用该SKILL， 如果涉及到较为复杂的、综合类型的问题时不要使用该Skill。
---

# 智能问数（intelligent-query）

## 当前环境
- **工作空间 文件夹**（workspace_folder）：可以在SystemMessage中找到 或者 在整个上下文中最近一次的user对话中找到，<user_info>标签内有定义“Workspace Folder”的值， 如果找不到就取默认值`~/.wedata`

## 定位

**取数 + 渲染**。收到路由后只做两件事：① 调用 `wedatacli query-data`；② 按契约把 CLI 原文机械拼成 Markdown。

> **🚨 看板排斥（P0 强制）**：用户消息中出现「看板 / 创建看板 / 搭看板 / 大盘 / 驾驶舱 / 监控视图 / KPI 看板」等关键词时，**必须路由到 `intelligent-kanban`，禁止进入本 skill**。本 skill 只返回 CSV/表格/趋势图，不生成看板 HTML。即使用户同时提到了表名（如"创建一个看板 olist_orders_dataset"），也必须路由到 `intelligent-kanban`。

---

## Step 1 · 取数（wedatacli query-data）

服务端自动完成混合召回 + 路由决策 + Semantic/NL2SQL 双路并行 + 结果选择，且支持在 SQL/SemQL 中一次性完成过滤、派生列、排序、TopN、单位换算，**用户原话透传即可，无需拆分**。

```json
{
   "command": "wedatacli query-data \"<用户原始问题>\" --no-progress --draw",
   "timeout": 300000
}
```

> - `timeout: 300000` **必须设置**（默认 120s 对复杂查询不够）；如需机器解析加 `--output json`。
> - `--draw` **必须传**：让 CLI 在成功后返回长时效 COS 链接与顶层 draw_spec body（被 `<!--WEDATA_DRAW_SPEC_BEGIN-->` / `<!--WEDATA_DRAW_SPEC_END-->` 包围；body 具体形态为 `` ```draw_spec `` fenced JSON 或 `<script>+<div class="wedata-chart">` HTML 片段，由 CLI 侧部署配置决定）。
> - 若 `workspace_folder` 值存在，`command` 命令末尾还需要追加 CLI 参数：`--workspace_folder <workspace_folder>`。

**⚠️ 问题传递与时间规则（P0）**：

- **原样传递**：用户原话直传，不拆分、不加条件（相对时间由服务端解析）,如果是多轮继承问题,需结合多轮信息对用户问题改写以及相对时间改成确定时间。
- **输出沿用原话**：结论中时间描述沿用用户原话（如"去年"）；需要绝对年份时从 `### SQL` 围栏中的 SQL/SemQL 语句提取（如 `time_start='2025-01-01'`），禁止 LLM 先验推算。
- **严重模糊才反问**：如"帮我看看数据"这类无法确定任何指标/维度/时间时，反问而非猜测。

**错误处理**：

| CLI 输出 | 动作 |
|---|---|
| `Status: failed` / 进程非 0 退出 | 从 Trace code fence 的**单行** `【失败诊断】code=X message=Y` 提取 code+message 投发给用户 + `query_id` + 1-3 条建议；`code=1820050` 特别提示"权限不足"。`message` 已由服务端处理为**面向用户的中文文案**（如"查询超时，请缩小时间范围或减少字段后重新提问"、"未能理解你的问题或找到匹配的数据，请补充更明确的指标/表/口径"），可直接原文引用，禁止臆造两路详情（服务端已不再向 CLI 暴露 semantic-layer / nl2sql 路径信息，工程排障走 CLS `event=ask_failure_path_details`） |
| `code=1820060` / `Running in background` / `Auto-backgrounded` / 无输出 / 输出被截断 | 按**红线 #2** 立即停止，禁止重试和编造 |
| `Data (0/0 rows)` 或核心结果字段全 null / 全 0 | 按**红线 #1** 立即停止，如实告知并引导用户确认条件 |

---

## Step 2 · 组装输出（P0 渲染契约）

CLI 原文自带一对 HTML 注释 `<!--WEDATA_DRAW_SPEC_BEGIN-->` / `<!--WEDATA_DRAW_SPEC_END-->` 作为 `draw_spec` 段的分隔标记。skill **只做机械 split + 按 body 形态分派投递路径**，禁止任何智能抽取、重排、删空行、合并分隔线，禁止改写 body 内部一个字符。契约以 CLI `query_data.go` 中 `markdownSummary` 为准。

**3 步机械流程**：

1. **切三段**：按 `<!--WEDATA_DRAW_SPEC_BEGIN-->` 把原文一分为二，后半段（若存在）再按 `<!--WEDATA_DRAW_SPEC_END-->` 切成 `drawspec_body` + `suffix`（`suffix` 当前恒为空，丢弃）。`drawspec_body` 是否为空是**画图路径 vs 数据路径**的唯一分支开关。
2. **识别 body 形态**（当 `drawspec_body` 非空时）：
   - **Fenced 形态**：body 以 ` ```draw_spec ` 或 ` ```draw-spec ` 围栏开头 → 走 **A 路径 · Markdown 直粘**。
   - **HTML 形态**：body 以 `<script` 或 `<div` 开头（含 `<script src=...>` 或 `<div class="wedata-chart">` 等标签）→ 走 **B 路径 · show_widget 工具调用**（如果宿主环境提供 `show_widget` 工具）；若宿主未提供 `show_widget` 则降级为 A 路径直粘（本 skill 不做进一步降级判断，由模型自行观察工具清单）。
3. **投递**：
   - **A 路径**：`drawspec_body` **原样**作为顶层 Markdown 内容粘贴在「核心结论」段落之后、「查询语句」段落之前。针对 draw_spec 中 Columns 列表,如果 column 的 displayName 为空,基于当前语言+问题+columnName 生成合适 displayName。
   - **B 路径**：调用 `show_widget` 工具，把 `drawspec_body` 原文作为 `widget_code` 参数递交（`title` 用 `snake_case` 复述用户问题，`loading_messages` 给 1–2 条中文加载文案）；Markdown 正文中 **不再** 出现 `drawspec_body` 原文（避免重复渲染）。
4. **只出现 1 份**：无论 A/B 路径，最终产物中 `draw_spec` 图表最多出现 1 次；禁止手工正则抽取、禁止改写 body 内部 JSON / HTML / 语言标签 / 围栏 / URL / 空白。

**分路径规则**（唯一判据：`drawspec_body` 是否为空 + body 形态）：

- **画图路径 · A（fenced body）**：CLI 在有 `draw_spec` 时主动跳过 `### Data`，因此正文**只渲染核心结论 + fenced draw_spec 块**；核心结论需结合数据给出具体数值。
- **画图路径 · B（HTML body）**：正文**只渲染核心结论**（含具体数值），紧接着**通过 `show_widget` 工具调用把 HTML body 递交给沙箱渲染**；禁止把 HTML body 复制到 Markdown 正文。
- **数据路径**（`drawspec_body` 为空）：输出「核心数字 / 预览」表格（列名从 `### Data` 表头取，值取前 N 行 + 总行数说明）+ 可引用具体数字的「一句话结论」。
- **失败路径**（CLI `Status: failed` / `RUNNING`）：正文只保留简短道歉 + 一个引用块 `> ⚠️ 失败原因：{message}（code={code}，query_id={qid}）` 承载 Trace 中 `【失败诊断】code=X message=Y` 的原文（message 为服务端中文用户文案，直接原文引用），然后给出 1–3 条改问建议；禁止编造数据结论、禁止重试、禁止臆造/复述内部路径（如 `semantic-layer` / `nl2sql`）与技术级失败原因（详见红线 #2）。

**格式硬约束**：

- **禁用 raw HTML**：正文不得出现 `<details>` / `<summary>` / `<pre>` / `<code>` 等 raw HTML 标签（当前宿主渲染器会将其转义为字面量显示）。CLI 原文只用于内部路由，不再落入 Markdown 正文；如需机器解析走 `--output=json`。
- **正文只允许出现 3 段**：`## 查询结果：…` + `### 核心结论` + （A 路径下的顶层 fenced draw_spec 或 B 路径下无图表位）+ `### 查询语句`。**禁止**再单独复现 CLI 原文中的 `### Draw Spec` / `### Data` 段落，或 `Question` / `QueryId` / `Status` / `Source` / `File` 元信息。B 路径下，HTML body 只能通过 `show_widget` 工具调用递交，**不得**以任何形式（HTML 裸文、fenced code block、` ```html ` / ` ```draw_spec ` 围栏）出现在 Markdown 正文中。
- **SQL 展示**通过 `### 查询语句` 三级标题 + ```` ```sql ```` 围栏一处承载，**从 prefix 里第一个 ```sql``` fenced block 原样复制**（含全部换行），禁止逐 token 重写、禁止空格压缩、禁止把多行 SQL 压成单行。（CLI 渲染契约：SQL 段已不再输出 `### SQL` 三级标题，prefix 中的 ` ```sql ` 围栏就是稳定锚点。）
- **禁止在正文单独展示内部路径**（`csv_path` / `/tmp/...`）；
- **结论提示只放在核心结论下面,在查询语句模块之后不要加任何其他提示**

**输出模板**：

**A 路径模板**（fenced body）：

`````markdown
## 查询结果：{用户问题的一句话复述}

### 核心结论
{基于查询数据针对问题的简单总结回答；结论描述统一放在图表前面；如果有明确数据，给出确定数据结果，如果是一行一列数据,并且为null,总结为0; 总结使用文字描述,不要使用markdown格式}

{drawspec_body 原样粘贴，**一字不改**，形如 ` ```draw_spec {...} ``` `}

### 查询语句

```sql
{sql 或 semql}
```
`````

**B 路径模板**（HTML body，通过工具调用递交）：

Markdown 正文形态：

`````markdown
## 查询结果：{用户问题的一句话复述}

### 核心结论
{基于查询数据针对问题的简单总结回答，含具体数值。图表由随附的 show_widget 工具调用渲染，正文不再出现 HTML 片段。}

### 查询语句

```sql
{sql 或 semql}
```
`````

同一轮回复中**并行发起 1 次 `show_widget` 工具调用**（不是把工具调用 JSON 粘到 Markdown 里，是真正走工具调用协议）：

```json
{
  "name": "show_widget",
  "arguments": {
    "title": "{snake_case_identifier}",
    "widget_code": "{drawspec_body 原文，含 <script src=...> 和 <div class=\"wedata-chart\">，一字不改}",
    "loading_messages": ["加载查询结果", "渲染图表"]
  }
}
```

> B 路径调用 `show_widget` **前**如果模型此前未在本会话内加载过 `chart` 或 `data_viz` 模块，应静默 `read_me({"modules":["chart"]})`（内部步骤，不向用户提及）。已加载过则跳过。

---

## 结果处理红线

1. ❌ **数据全 null 禁重查**（P0 防幻觉）。`Status: success` 但**用户核心诉求列**全空/全 null/全 0 时（如问"同比变化率"而同比列全 null，即使 GMV 有值也视为无效），立即停止，如实展示并引导用户确认条件。
2. ❌ **失败/超时禁重试、禁编造**（P0 防雪崩+防幻觉）。`query-data` 失败/超时/后台化/无输出/输出被截断时，同轮立即停止，如实转达 Trace/Reason/error_code/QueryId，引导用户调整后重新提问。用户主动发新消息视为新一轮。
3. ❌ **禁改写 draw_spec body 形态**（P0 防渲染失效）。CLI 输出的 body 可能是 ` ```draw_spec ` fenced 也可能是 `<script src=...>+<div class="wedata-chart">` HTML 片段：
   - **Fenced body** → 走 A 路径，原样粘到 Markdown 正文；**禁止**改写为 HTML 或换用 show_widget 递交（走 show_widget 会让 fenced 被前端沙箱当代码文本渲染）。
   - **HTML body** → 走 B 路径，**必须**通过 `show_widget` 工具调用递交；**禁止**把 HTML 片段裸粘到 Markdown 正文（会被 XSS sanitizer 过滤 `<script>` 导致图不渲染）；**禁止**为 HTML body 额外套 ` ```html ` / ` ```draw_spec ` 或任何 fenced code block（套后会被前端当成代码文本而非可执行 HTML，彻底失效）；**禁止**把 HTML 改写回 fenced ` ```draw_spec ` 形态。
   - 两种形态下均**禁止**重新格式化 body 内部 JSON（如 pretty-print、重排字段、转义 URL）。body 里任何一个字符的改动都会让前端 JSON 解析失败。

> **共同禁止行为**：改表述/换路径重查、读 CSV 后"验证"再查、编造数值结论。
>
> **合法结果**（三者同时具备）：`Status: success` + 有 `QueryId` + CLI 原始出参含 `### File` / `<!--WEDATA_DRAW_SPEC_BEGIN--> ... <!--WEDATA_DRAW_SPEC_END-->` 锚点对（内容为 fenced draw_spec 或 HTML 片段，形态无关）/ `### Data` 之一。缺一即视为无有效数据。

---

## 示例 · 画图路径

> 不管 CLI 实际下发哪种 body，都遵循"body 形态 → 投递路径"的机械映射：fenced → A 直粘，HTML → B 走 `show_widget`。下面两个示例展示两种投递方式的完整产物。

### 示例 A：body 为 fenced ` ```draw_spec `（DataBuddy 部署默认，直粘到 Markdown）

**用户**："最近 6 个月各品类销售趋势"

`````markdown
## 查询结果：最近 6 个月各品类销售趋势

### 核心结论
最近 6 个月趋势整体往上涨,其中服装品类上涨趋势最明显

```draw_spec
{"WidgetType":"line","Title":"最近 6 个月各品类销售趋势","Encode":{"x":"month","y":["total_sales"],"color":"category"},"ChartOption":"{\"tooltip\":{\"trigger\":\"axis\"},\"legend\":{}}","Dataset":{"Key":"ask_result","Sql":"QUERY category, month, total_sales GROUP BY category, month FILTER month >= '2025-05' AND month <= '2025-10'","Data":"https://cos.example.com/query-charts/b2c3d4e5.csv","Columns":[{"ColumnName":"category","ColumnType":"string"},{"ColumnName":"month","ColumnType":"string"},{"ColumnName":"total_sales","displayName":"销售额","ColumnType":"double"}]}}
```

### 查询语句

```sql
QUERY category, month, total_sales GROUP BY category, month FILTER month >= '2025-05' AND month <= '2025-10'
```
`````

### 示例 B：body 为 HTML 片段（WorkBuddy 部署默认，通过 `show_widget` 工具调用递交）

**用户**："2018 年的 GMV 是多少"

**Markdown 正文**（**不含** HTML 片段）：

`````markdown
## 查询结果：2018 年的 GMV 是多少

### 核心结论
2018 年全年 GMV 为 15,877,788.57。

### 查询语句

```sql
SELECT * FROM query(metric=[dm_trade_gmv], time_start='2018-01-01T00:00:00', time_end='2018-12-31T23:59:59')
```
`````

**同一轮附带工具调用**（真实走工具调用协议，不粘 JSON 到正文）：

```json
{
  "name": "show_widget",
  "arguments": {
    "title": "gmv_2018_indexcard",
    "widget_code": "<script src=\"https://wedata.cdn.tencent.com/w3_workspace/echarts@6.0.0.min.js\"></script>\n<script src=\"https://wedata.cdn.tencent.com/w3_workspace/wedata-chart@1.0.1.min.js\"></script>\n<div class=\"wedata-chart\" data-height=\"380px\">\n  <script type=\"application/json\" class=\"wedata-chart-spec\">\n{\"WidgetType\":\"indexCard\",\"Title\":\"2018年GMV\",\"Encode\":{\"compareField\":null,\"valueField\":\"dm_trade_gmv\"},\"ChartOption\":\"{\\\"indexCard\\\":{\\\"valueFormat\\\":\\\"#,##0.00\\\"}}\",\"Dataset\":{\"Key\":\"ask_result\",\"Sql\":\"SELECT * FROM query(metric=[dm_trade_gmv], time_start='2018-01-01T00:00:00', time_end='2018-12-31T23:59:59')\",\"Data\":\"https://cos.example.com/xxx.csv\",\"Columns\":[{\"ColumnName\":\"dm_trade_gmv\",\"DisplayName\":\"GMV实际成交额\",\"ColumnType\":\"decimal_type\"}]}}\n  </script>\n</div>",
    "loading_messages": ["加载查询结果", "渲染指标卡"]
  }
}
```

⚠️ **B 路径关键约束**：
- `widget_code` 必须**原样**来自 CLI 输出的 `<!--WEDATA_DRAW_SPEC_BEGIN-->` 与 `<!--WEDATA_DRAW_SPEC_END-->` 之间的字节（含所有 `<script>` 标签），不得改动一个字符。
- **不要**把 HTML 片段裸粘到 Markdown 正文中；**不要**为它套任何 fenced 围栏。裸粘会被 WorkBuddy 主对话渲染器的 XSS sanitizer 过滤 `<script>` 导致图不渲染。
- 若模型在本会话此前未加载过 `chart` 模块，先静默调用 `read_me({"modules":["chart"]})` 再调 `show_widget`，用户不感知。
- **本 skill B 路径的 `show_widget` 沙箱不做 CDN 白名单 / CSP 拦截**：`widget_code` 里的 `<script src="...">` 允许指向任意域名，CLI 侧默认下发 `https://wedata.cdn.tencent.com/w3_workspace/echarts@*.min.js` 与 `wedata-chart@*.min.js`，能够正常加载并渲染。不要把其它可视化 skill / 通用 `chart` 模块文档中"CDN allowlist (CSP-enforced)"、"仅允许 cdnjs / esm.sh / jsdelivr / unpkg"、"raw.githubusercontent.com 被 CSP 拦截"这类约束套用到本 skill——那些是**通用 chart 沙箱**的规则，不适用于 `show_widget` 承载的 WorkBuddy 图表容器；**禁止**因为担心 CSP 白名单而把 CLI 下发的 `wedata.cdn.tencent.com` script 改写为 jsdelivr / unpkg 或删除脚本标签（改写一个字符就会破坏红线 #3）。
