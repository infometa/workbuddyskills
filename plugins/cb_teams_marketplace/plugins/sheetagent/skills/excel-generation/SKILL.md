---
name: tencent-docs-sheet-generation
description: >
  从零生成 Excel/xlsx 工作簿。当用户请求"创建/生成/新建/做一份/from scratch"
  一个 XLSX 文件、且**没有源 .xlsx/.csv 文件**时使用。支持纯文字需求，也支持
  以 pdf/docx/pptx 附件作为内容参考（由 `extract.py` 抽取为 markdown）。
  本 skill 在主代理侧准备 schema 与骨架文件，然后委派 sheet-agent 子代理完成单元格填充。
---

# Excel 生成链路 (tencent-docs-sheet-generation)

本 skill **本身不直接操作 MCP 工具**编辑表格。它的职责是在主代理侧：

- 推断目标文件命名
- 设计 schema（字段、sheet、布局）并写入 ref 目录
- 调 `create_blank_xlsx.py` 生成骨架 xlsx
- 委派 `sheet-agent` 子代理按 schema 填充单元格

---

## 适用范围与拒绝条件

**适用**：

- 用户**没有提供**任何源 `.xlsx` / `.xls` / `.csv` 文件
- 用户表达明确的"创建/生成/新建/做一份"等意图
- 目标产出是单个 xlsx 工作簿
- 支持随附**本地** pdf/docx/pptx 附件作为内容参考（如"基于这份 pdf 帮我整理成 Excel"、"按这个 ppt 做一份汇总表"）
- 支持以**在线文档**（`docs.qq.com` 链接 / `file_id`，含跨品类的 doc / slide / 在线 sheet）作内容 / 样式参考（用 MCP 读取，见 Step 2）

**不适用**（routing 已过滤；如确实出现，告知用户并退出本 skill）：

- 用户实际给了源 xlsx / xls / csv（任何编辑场景） → 退出，让 routing 重新决策
- 用户要求生成 docx / pptx / md 等非表格 → 不在本 skill 范围
- **本地**附件类型非 pdf / docx / pptx（如 zip / 图片 / 本地 csv） → 告知用户当前仅支持 pdf / docx / pptx 本地附件（**在线文档参考除外**，走 Step 2 的 MCP 读取）

---

## 执行流程（6 步）

### Step 1: Reasoning & Naming

**核心：推断目标 title，全程不反问用户**。

**取名优先级（依次匹配，命中即停）**：

| 优先级 | 信号 | 取值规则 |
|---|---|---|
| P0 | 用户原话含"叫 X.xlsx" / "保存为 X" / "name it X" / "文件名 X" | 提取 X（去掉 `.xlsx` 后缀） |
| P1 | 用户原话含"标题 X" / "名字 X" / 引号包裹的明显名词短语 | 提取 X |
| P2 | 用户上传 pdf/docx/pptx 附件（无显式命名信号时） | 取主附件 stem（多附件时取第一个或最显眼的） |
| P3 | 从用户原话提取最显著名词短语（如"做一份 Q1 销售汇总表" → "Q1销售汇总"） | 提取结果 |
| P4 | 上述都失败（如"做个表"） | `workbook_<YYYYMMDD_HHMMSS>` |

取名优先级得到的是 `<raw_title>`（**保留原始字符**，用于展示：在线 title / 本地 OOXML 显示标题）。凡是要落到**文件系统**的名字（本地骨架文件名、ref 目录名——云端本地都涉及），都要对它走下面这套 sanitize，得到 `<sanitized_title>`：

**文件系统命名 sanitize（仅用于落盘文件名 / 目录名，绝不用于在线 title / 显示标题）**：

1. 删除 `\ / : * ? " < > |` 这 9 个字符
2. 删除首尾空格
3. 中间空格替换为 `_`
4. 截断到 ≤ 50 字符

**Step 1 执行顺序（必须按此先后做，不可错乱）**：

1. **先做用户路径意图识别**：从用户原话中拆出 `<parent_dir>` 与 `<raw_stem>` 两部分（详见下方「用户路径意图识别」段）。如果用户没给出任何路径线索，`<parent_dir>` = 默认 cwd，`<raw_stem>` 走上方「取名优先级」表得到。
2. **再对 `<raw_stem>` 应用上方「文件系统命名 sanitize」**，得到 `sanitized_title`。**sanitize 只作用于 stem，不作用于 `<parent_dir>` 或完整路径**——否则会把用户给的合法路径分隔符 `/` 也吃掉。
3. **最后拼装**：骨架绝对路径 = `<parent_dir>/<sanitized_title>.xlsx`；ref 目录 = `<parent_dir>/.<output_stem>.ref/`。其中 `<output_stem>` 是骨架文件最终的 stem（撞名加时间戳后即含时间戳）——**ref 目录基名必须跟骨架同名**，二者才能配对。

`sanitized_title` 就是后续路径用的名字。**原始 title**（即 `<raw_title>`，含空格 / 特殊字符）仅用于 Step 4 写入 OOXML 元数据（显示标题保留原样）；**下文 `<title>` 即指这个展示标题（本平台=`<raw_title>`）**。

**路径规划**：

- 骨架文件路径：`<parent_dir>/<sanitized_title>.xlsx`
  - 如果该路径已存在文件：改为 `<parent_dir>/<sanitized_title>_<YYYYMMDD_HHMMSS>.xlsx`，**不询问、不覆盖**
- ref 目录路径：`<parent_dir>/.<output_stem>.ref/`（**下文记为 `<ref_dir>`**）
  - 其中 `<output_stem>` 是最终骨架的 stem（含可能加上的时间戳）

**用户路径意图识别**（决定 `<parent_dir>` 与 `<raw_stem>`，先于 sanitize 执行）：

- 含"放到 /路径/" / "放在 ~/Desktop" / "保存到 /xxx/" → 该路径为 `<parent_dir>`；`<raw_stem>` 仍按「取名优先级」走
- 含"叫 X.xlsx" 且 X 含 `/` → 把 X 当完整路径解析：`<parent_dir>` 取其 dirname，`<raw_stem>` 取其 basename（去掉 `.xlsx` 后缀）
- 含 `~` 开头的路径 → 在用 Bash 执行时 shell 会自然展开；主代理在传递给脚本前**必须先展开成绝对路径**（不要把 `~` 原样塞给脚本）
- 否则 → `<parent_dir>` = 默认 cwd

无论哪种来源，最终传给 `create_blank_xlsx.py` 的必须是**已展开的绝对路径**，且 ref 目录始终跟随骨架同 parent。

> Step 1 仅做**纸面计算**：算出 `sanitized_title`、骨架绝对路径、ref 目录绝对路径，记入主代理上下文。骨架文件与 ref 目录的实际创建在 Step 3 / Step 4 完成。

### Step 2: 附件预处理

判断用户输入是否包含内容参考素材，并**按来源分流**：

- **没有参考素材**（用户全是文字描述） → 直接进入 Step 3，跳过本 step
- **跨品类的在线文档参考**（用户给的是 `docs.qq.com` 链接 / `file_id`，如把在线 doc / slide / 另一张在线 sheet 当参考） → **用 MCP 读取工具读取该在线文档的「数据」与「样式」**，按其品类选工具（doc 用文档读取 MCP 工具；sheet 用 `read_table` / `get_cell_ranges`(含样式) 等）。**不要用 `extract.py`**（它只处理本地文件）。把读到的字段 / 数值 / 样式要点整理后落到 ref 目录 `reference/<sanitized_input_stem>/content.md`，供 Step 3 设计 schema 参考
- **本地 pdf/docx/pptx 文件** → 用 `extract.py` 抽取为 markdown，落到 Step 1 算出的 ref 目录 `reference/<sanitized_input_stem>/` 子目录下（命令见下）

**触发条件识别**（主代理从用户原话与上下文判定）：

- 用户给的是**在线文档**（`docs.qq.com` 链接 / `file_id`，可能是别的品类）作参考 → 走「跨品类在线文档」分支，用 MCP 读数据 + 样式，**不要** `extract.py`
- 用户消息里出现**本地** `*.pdf` / `*.docx` / `*.pptx` 文件路径，且明显是参考素材（如"基于这份 pdf"、"参照 docx 整理成 Excel"、"按这个 ppt 做一份汇总表"）→ `extract.py`
- 多个参考 → 逐个处理，每个一个 `reference/<sanitized_input_stem>/` 子目录
- 本地附件不是 pdf/docx/pptx（如 zip / 图片） → 见「不适用」段处理，不要尝试抽取

**抽取命令**（Bash）：

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/skills/excel-generation/scripts/extract.py" \
  "<input_file_absolute_path>" \
  -o "<ref_dir>/reference/<sanitized_input_stem>"
```

`<sanitized_input_stem>` 是去掉扩展名的纯文件名再按 Step 1 的「文件系统命名 sanitize」处理（删除禁字符、空格转下划线、≤50 字符）。如 `Q1*report.pdf` → `Q1report`，`销售/数据.docx` → `销售数据`。

**示例**：

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/skills/excel-generation/scripts/extract.py" \
  "/Users/luxury/Downloads/Q1销售数据.pdf" \
  -o "/Users/luxury/project/demo/.Q1销售汇总.ref/reference/Q1销售数据"
```

**抽取产物**（脚本自动生成）：

```
<ref_dir>/reference/<sanitized_input_stem>/
├── content.md       # 文本（markdown），含图片引用
├── images/          # 原始图片（高分辨率）
└── thumbnails/      # PNG 缩略图（≤600px 宽，子代理可直接 Read 看内容）
```

**校验**：

- 命令 exit=0 → 抽取成功，脚本会打印产物结构
- exit≠0 → stderr 通常会指出具体原因（依赖未装 / 输入不存在 / 格式不支持），把消息原样转给用户后中止本次任务

**依赖处理**：与 `create_blank_xlsx.py` 一致，`extract.py` 会**按需自动安装**缺失依赖（仅装当前格式所需的包，如处理 pptx 时不会装 pymupdf）。安装失败时脚本 exit=4，把 stderr 信息转告用户即可。

完成参考处理后进入 Step 3。执行 SOP 的代理（子代理）会按需 Read `reference/` 下的产物（详见 prompt §0.5）。

### Step 3: Schema 设计与写入

**设计规范读取规则**：

> ⛔ **硬性规则——写 schema.md 之前，必须先 Read `${CODEBUDDY_PLUGIN_ROOT}/skills/excel-generation/references/schema_principle.md`，无例外。** 不读准则就写 schema = 任务失败。

- schema.md 中的所有决策（结构、列定义、样式指令、数据策略）必须符合 schema_principle.md 的约束
- 如果用户明确要求与准则冲突，以用户要求为准

主代理根据用户原话 + schema_principle.md 约束设计 workbook 结构，写到 ref 目录的 `schema.md`。

**先创建 ref 目录**（Bash）：

```bash
mkdir -p "<ref_dir>"
```

**schema.md 模板**（用 Write 工具写入 `<ref_dir>/schema.md`）：

````markdown
# Workbook Design — <title>

> 由 excel-generation skill 在主代理侧产出，供 sheet-agent 子代理按图施工。

## User Intent
<原样复述用户的核心诉求一两句>

## Scenario Archetype
- <命中的场景原型及理由，如：统计型 + 看板型，因为用户要求汇总、趋势和领导汇报>

## Sheets
- <sheet_name_1>（角色：主表 / 明细 / 趋势 / 透视）
- <sheet_name_2>
- ...

## Sheet: <sheet_name_1>

### Columns
| 列 | 字段名 | 类型 | 来源 | 备注 |
|---|---|---|---|---|
| A | 月份 | 文本 | 用户原话/推断 | 1月/2月/3月 |
| B | 渠道 | 文本 | 推断 | 直营/经销 |
| C | 本期销售额（万元） | 数字（2位小数） | 推断 | 保留两位 |
| D | 去年同期销售额（万元） | 数字（2位小数） | 推断 | 保留两位 |
| E | 同比 | 百分比 | 计算列 | E2：`=IF(OR(D2="",D2=0),"",C2/D2-1)`；填充 E2:E末行（末行为实际数据最后一行）；去年同期销售额（D列）为空或 0 时显示空白 |

### Sample Data Scale
<例如：3 个月 × 2 个渠道 = 6 行 / 留空给用户填 / 造 10 行样例>

### Notes for sheet-agent
- 表头样式按 schema_principle §6.2/§6.3 选定风格（默认商务蓝：`#4472C4` 底 + 白字）
- 金额列保留两位小数、千位分隔符
- 计算列按 Columns 表"备注"中的公式 / 生成规则和适用范围执行；验证时读回公式文本确认必要的空值保护；除法 / 比率类公式还要确认分母空值和 0 值保护

## Sheet: <sheet_name_2>
（同上结构）

## Charts / Pivots
（如有，列出 sheet+位置+类型+数据源；无则写"无"）

## 约束与不做的事
- <例如：本次不做透视、不做条件格式>
````

**schema.md 编写原则**：

- **必有**：User Intent、Scenario Archetype、Sheets 列表、每个 sheet 的 Columns 表（列字母 + 字段名 + 类型 + 来源 + 备注）、Sample Data Scale、Notes for sheet-agent、约束与不做的事
- **可选**：Charts/Pivots
- **遵循 schema_principle.md**：列类型必须使用准则定义的标准类型；计算列公式本体写在 Columns 表"备注"列，且公式坐标必须符合所在 sheet / 区块的真实布局；Notes 不重复另一版公式；Notes for sheet-agent 中的样式指令必须给出具体值（颜色代码、对齐方式），不写模糊描述；Sample Data Scale 按准则 §5.1 的策略表决定
- **先定布局锚点再写公式**：如果 sheet 有标题行、多区块、合计行或表头不在第 1 行，必须先在心中确定标题行、表头行、数据起止行、合计行，再把这些真实坐标写进 Columns 表"备注"。例如 Notes 写"第 1 行标题、第 2 行表头、第 3~5 行数据、第 6 行合计"时，Columns 公式必须用 `B3:B5` 和 `B6`，不得写 `B2:B4`
- **附件来源标注**：若数据来自 Step 2 抽取的附件，在 Columns 的 "来源" 列写明 `reference/<stem>/content.md` 的相对路径或段落定位（如 "reference/Q1销售数据/content.md §3"），让子代理知道去哪找数据；若字段由公式派生，则写 `计算列`
- **越精简越好**：只列结构性内容，留给子代理 §4 SOP 决策具体工具
- **明确不做的事**：写"约束与不做的事"防止子代理过度发挥

**进入 Step 4 前的自检硬约束**：

- 写完 schema.md 后，必须对照 schema_principle.md §11.1 确认全部必填项已存在；缺任一项不得进入 Step 4，必须先补齐 schema.md
- 必须检查每个 sheet / 区块的行号一致性：Notes 中声明的标题行、表头行、数据行、合计行，必须与 Columns 表"备注"里的公式起始单元格、填充范围和合计公式一致；发现 `第 3~5 行数据` 搭配 `B2:B4` 这类冲突时，必须先改 Columns 备注
- 必须检查所有 `来源=计算列` 的字段：Columns 表"备注"是公式 / 生成规则的唯一权威；Notes 只能引用 Columns 备注，不得新增、改写或重复另一版公式
- 必须按运算类型检查公式保护：加减法、差异、余额等公式只检查必要空值，不得把合法的 0 值当作空白；除法、达成率、同比、占比等比率公式必须显式保护分母空值和 0 值，且分子为空时应返回空白。可用 `OR(B3="",B3=0)`，或语义等价的 `IFERROR`，但不得只写自然语言"除零保护"

### Step 4: 生成骨架文件
主代理调 Bash：

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/skills/excel-generation/scripts/create_blank_xlsx.py" \
  "<output_xlsx_absolute_path>" \
  "<original_title_for_metadata>" \
  "<sheet_names_csv>"
```

**参数说明**：

- 第 1 参数：骨架文件的**绝对路径**（Step 1 算出的；如果包含 `~` 主代理需先展开）
- 第 2 参数：写入 OOXML 元数据的 title（**用原始 title，不 sanitize**，元数据可以包含中文空格）
- 第 3 参数：可选，逗号分隔的 sheet 名（取自 schema.md 的 Sheets 列表）；省略则建 `Sheet1`

`${CODEBUDDY_PLUGIN_ROOT}` 由宿主注入，指向当前 plugin 根目录（`plugins/sheetagent/`）。

**示例**：

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/skills/excel-generation/scripts/create_blank_xlsx.py" \
  "/Users/luxury/project/demo/Q1销售汇总.xlsx" \
  "Q1 销售汇总" \
  "汇总,明细"
```

**校验**：

- 命令 exit=0 → stdout 第一行就是骨架的绝对路径，记下来传给子代理
- exit=2 → 参数 / 校验问题（sheet 名不合法等），告知用户后重试
- exit=3 → 写盘失败（权限 / 路径不存在），告知用户
- exit=4 → openpyxl 安装失败，告知用户手动安装：`pip install openpyxl`

### Step 5: 填充单元格
按本 skill 末尾的「委派契约」（invoke-sheet-generation 模板）将任务交给 sheet-agent 子代理。委派内容明细以模板定义为准。

### Step 6: 交付结果
向用户简要说明产出位置（用本 skill 在 Step 1 / Step 4 算出的骨架路径）：

```
已为您生成 <骨架路径>，包含 <N> 个工作表：<sheet_names>。
```

---

## 错误处理

| 场景 | 处理 |
|---|---|
| Step 4 脚本 exit≠0 | 把 stderr 原样转给用户，告知问题（参数 / 写盘 / 依赖安装）后建议重试 |
| 子代理委派后报错 | 把错误信息原样转给用户；如果错误明确指向骨架文件不可用，先 `ls -la <骨架路径>` 自检后再决定重试或反馈用户 |
| 用户中途要求换文件名 | 重新执行 Step 1；如果 Step 4 已跑过，主代理在 Bash 里 `mv` 旧文件，或重新建 |

---

将此任务委派给 **sheet-agent** 子代理处理（生成链路）。

## 传递给子代理的内容（仅限以下五项）

1. **文件路径** — 已由本 skill 在主代理侧生成的骨架 Excel 文件的完整绝对路径
2. **用户输入** — 用户的原始自然语言需求，原样转发，不做改写
3. **当前时间** — 主代理上下文中的当前时间信息，原样传递给子代理
4. **参考资料路径（ref 目录）** — 主代理在本 skill 中产出的 ref 目录绝对路径，至少包含 `schema.md`；可能包含 `reference/<stem>/content.md` 等附件素材
5. **期望返回** — 告诉子代理需要返回什么结果给用户（如填充摘要、sheet 写入概览等）

## 禁止

- **禁止**添加实现步骤、工具名称、操作流程或任何执行细节
- **禁止**告诉子代理该如何完成任务或该调用哪些工具
- **禁止**主代理直接调用 `mcp__sheetagent__*` 工具

## 前置条件

调用子代理之前，主代理须确认：

- 骨架 `.xlsx` 已生成到「文件路径」指定位置
- ref 目录已存在，且至少包含 `schema.md`

任一项未满足说明 skill 的前置步骤未完成，应自检后补齐再委派子代理。

## 说明

本链路是 **从零生成** 场景：骨架由 `excel-generation` skill 在主代理侧提前建好，子代理收到的是一份只含空 sheet 的 xlsx + 一份 schema 图纸（ref 目录）。子代理 prompt 的 §0.5 会引导它先读 schema 再施工。

