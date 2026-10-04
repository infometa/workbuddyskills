# doc block（块级读写）

在线文档（`fileSuffix=otl`）的内容以块（block）为单位读写。所有块命令都接 `--id <DOC_ID>`。

## 命令

| 命令 | 必填参数 | 说明 |
|------|---------|------|
| `doc block list` | `--id` | 列出文档全部块；可选 `--block-id` 限定子树 |
| `doc block insert` | `--id --element` | 插入新块；可选 `--parent-block-id`/`--index` 定位 |
| `doc block update` | `--id --operations` | 按 `blockId` 更新内容或属性 |
| `doc block delete` | `--id --operations --yes` | 按 `blockId` + 范围删除（⚠️ 不可恢复，须用户确认后加 `--yes`） |
| `doc block replace` | `--id --start --end --content` | 替换指定范围内的块（先删后插，破坏性编辑，执行前应向用户确认范围）；可选 `--parent-block-id` 指定操作的父块 |

## doc block list

```bash
yzj-cli doc block list --id <DOC_ID>
yzj-cli doc block list --id <DOC_ID> --block-id <PARENT_BLOCK_ID>
```

返回结构：`data.blocks[]`，每个块含 `id`、`type`、`attrs`、`content[]`（内联节点数组）。

## doc block insert 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| `--id <DOC_ID>` | 是 | 文档 ID |
| `--element` | 是 | 块内容 JSON 数组（见下方块类型） |
| `--parent-block-id` | 否 | 父块 ID，默认 `"doc"`（文档根） |
| `--index` | 否 | 插入位置索引，`-1`=末尾（默认），`0`=开头，`1`=第二个位置，以此类推 |

> ⚠️ 向 `doc create` 新建的文档插入内容时，首块不得是与 `--title` 相同的一级标题——该标题已作为节点标题展示。详见下方 heading 块类型的「标题去重」说明。

### 块类型

`--element` 接受 JSON 数组，每个元素是一个块对象。

**标题：**

```json
{"type": "heading", "attrs": {"level": 1}, "content": [{"type": "text", "content": "标题文本"}]}
```
`level` 取值 1-6。

> ⚠️ **标题去重**：当向通过 `doc create --title "X"` 创建的文档插入内容时，第一个块**不得**是 `level: 1` 且文本与 `--title` 相同的标题块——该标题已作为节点标题展示，重复插入会导致文档出现两个标题。应直接从正文（paragraph）或二级及以下标题（`level >= 2`）开始插入。

**段落：**

```json
{"type": "paragraph", "content": [{"type": "text", "content": "段落文本"}]}
```

**列表：**

```json
// 无序列表
{"type": "paragraph", "attrs": {"listAttrs": {"type": 1, "styleType": 1, "level": 0}}, "content": [...]}
// 有序列表
{"type": "paragraph", "attrs": {"listAttrs": {"type": 2, "styleType": 4, "level": 0}}, "content": [...]}
// 任务列表
{"type": "paragraph", "attrs": {"listAttrs": {"type": 3, "styleType": 7, "level": 0}}, "content": [...]}
```

**代码块：**

```json
{"type": "codeBlock", "attrs": {"lang": 4}, "content": [{"type": "text", "content": "code here"}]}
```
`lang` 常用值：1=plaintext, 4=python, 5=shell, 16=java, 19=javascript, 22=yaml, 33=nginx

**引用块：**

```json
{"type": "blockQuote", "content": [...]}
```

**表格：**

```json
{"type": "table", "attrs": {"borderStyle": 2}, "content": [{"type": "tableRow", "content": [...]}]}
```

### 内联节点属性

text 节点的 `attrs` 支持内联样式：

```json
{"type": "text", "attrs": {"bold": true}, "content": "粗体文本"}
```

| 属性 | 说明 |
|------|------|
| `bold` | 加粗 |
| `italic` | 斜体 |
| `underline` | 下划线 |
| `strike` | 删除线 |

可组合使用：`{"attrs": {"bold": true, "italic": true}, "content": "粗斜体"}`

## doc block update 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| `--id <DOC_ID>` | 是 | 文档 ID |
| `--operations` | 是 | 更新操作 JSON 数组（结构见下） |

`--operations` 每个元素必须包含：

| 字段 | 必填 | 说明 |
|------|------|------|
| `operation` | 是 | `update_content`（替换内联内容）/ `update_attrs`（替换块属性） |
| `blockId` | 是 | 目标块 ID（必须是具体块，**不能传 `"doc"`**，先 `block list` 获取） |
| `content` | `update_content` 时必填 | 新的内联节点数组，与 insert 的 `content[]` 同结构 |
| `attrs` | `update_attrs` 时必填 | 新的块属性对象，如 `{"level": 3}` |

> ⚠️ 缺 `operation` 字段时后端返回 500。必须按上方 schema 传齐。

### update 示例

替换某段文字内容：

```bash
yzj-cli doc block update --id <DOC_ID> --operations "[{\"operation\":\"update_content\",\"blockId\":\"<BLOCK_ID>\",\"content\":[{\"type\":\"text\",\"content\":\"更新后的段落\"}]}]"
```

把某标题从 H2 改成 H3：

```bash
yzj-cli doc block update --id <DOC_ID> --operations "[{\"operation\":\"update_attrs\",\"blockId\":\"<BLOCK_ID>\",\"attrs\":{\"level\":3}}]"
```

返回结构：`data.results`（base64 编码的块快照，可忽略）。

## doc block delete 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| `--id <DOC_ID>` | 是 | 文档 ID |
| `--operations` | 是 | 删除操作 JSON 数组（结构见下） |

`--operations` 每个元素必须包含：

| 字段 | 必填 | 说明 |
|------|------|------|
| `blockId` | 是 | **父块 ID**（删除目标的容器），不是被删块本身 |
| `startIndex` | 是 | 父块 `content[]` 中的起始索引（从 0 开始，半开区间） |
| `endIndex` | 是 | 父块 `content[]` 中的结束索引（不含；`endIndex - startIndex` = 删除的子节点数） |

> ⚠️ 仅传 `blockId` 不带 `startIndex` / `endIndex` 时，后端返回 400 `Invalid parameter: startIndex or endIndex is invalid`。三个字段必须齐全。
>
> ⚠️ **语义易错点**：`blockId` 指向**容器**而非被删块。若把目标块自身 ID 填入 `blockId` + `startIndex:0, endIndex:1`，实际只会清空该块内部的 inline 子节点（块本身仍在）。删除整个块必须以**父块**为 `blockId`，按该块在父块 `content[]` 中的索引范围传 `startIndex`/`endIndex`。

### delete 示例

**删除顶层某个块**（以 `doc` 根块为父）。先用 `doc block list --id <DOC_ID>` 查 `data.blocks[0].content[]`，找到目标块索引 N：

```bash
# 假设 list 显示 doc 根块的 content = [title, paragraph, heading, paragraph]
# heading 在索引 2，删除它（blockId=doc 根块，startIndex=2, endIndex=3）
yzj-cli doc block delete --id <DOC_ID> --operations "[{\"blockId\":\"doc\",\"startIndex\":2,\"endIndex\":3}]" --yes
```

**删除嵌套块**（以父块 ID 为容器）。先 `doc block list --id <DOC_ID> --block-id <父块ID>` 找到目标在父块中的索引 N：

```bash
yzj-cli doc block delete --id <DOC_ID> --operations "[{\"blockId\":\"<父块ID>\",\"startIndex\":N,\"endIndex\":N+1}]" --yes
```

返回结构：`data.success_list`（base64 编码的成功块 ID）、`data.fail_list`（base64 编码的错误详情）。失败时用 `echo <base64> | base64 -d` 解码查看。

## doc block replace 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| `--id <DOC_ID>` | 是 | 文档 ID（必须是 otl 类型） |
| `--start <N>` | 是 | 删除起始索引（包含，**必须 >= 1**；index=0 是文档标题节点，不可删除） |
| `--end <N>` | 是 | 删除结束索引（不包含，必须 > start） |
| `--content <JSON>` | 是 | 替换后插入的块节点 JSON 数组，结构与 `doc block insert --element` **完全一致**（见下方） |
| `--parent-block-id` | 否 | 操作的父块 ID，默认 `"doc"`（文档根块） |

### content 格式说明

`--content` 接受与 `--element` 相同结构的 JSON 数组，每个元素为一个块节点对象。块类型与内联节点格式同本文「块类型」章节（heading / paragraph / codeBlock / blockQuote / table 等）。

```json
[
  {"type": "heading", "attrs": {"level": 2}, "content": [{"type": "text", "content": "新章节标题"}]},
  {"type": "paragraph", "content": [{"type": "text", "content": "新章节内容。"}]}
]
```

### 关键约束

- `--start` 必须 >= 1（文档根块 index=0 是文档标题节点，不允许删除）
- `--end` 必须 > `--start`（删除范围至少包含一个块）
- `--content` 可为空数组 `[]`（纯删除无插入），但此时建议直接用 `doc block delete`
- 破坏性编辑，执行前必须先 `doc block list` 确认索引范围和目标内容，并向用户确认替换范围
- 与 `doc block update` 的区别：`update` 修改单块内容/属性且块数量不变；`replace` 删掉一段块再插入新块，适合块数量会变化或整节重写的场景

### replace 示例

先查看文档块结构，确认索引：

```bash
yzj-cli doc block list --id <DOC_ID>
```

假设 doc 根块的子节点为 `[title, h2, para, para, h2, para]`，要把索引 1-4（第一个 H2 及其两个段落）替换为新内容：

```bash
yzj-cli doc block replace --id <DOC_ID> --start 1 --end 4 \
  --content '[{"type":"heading","attrs":{"level":2},"content":[{"type":"text","content":"新章节"}]},{"type":"paragraph","content":[{"type":"text","content":"新内容。"}]}]'
```

在非根块下进行替换（指定父块）：

```bash
yzj-cli doc block replace --id <DOC_ID> --parent-block-id <PARENT_BLOCK_ID> --start 0 --end 2 \
  --content '[{"type":"paragraph","content":[{"type":"text","content":"替换后的内容"}]}]'
```

> ⚠️ 破坏性编辑：执行前必须向用户展示将被替换的块范围（索引 + 文本预览），获得明确确认后再执行。

## Windows 引号转义

Windows cmd / PowerShell 不支持单引号包裹 JSON，所有示例统一使用双引号 + 内部 `\"` 转义。Linux / macOS bash 可改用单引号提高可读性：

```bash
# bash
yzj-cli doc block update --id <DOC_ID> --operations '[{"operation":"update_content","blockId":"<BLOCK_ID>","content":[{"type":"text","content":"更新后的段落"}]}]'
```

## 危险操作

- `doc block delete` — **不可恢复**，执行前必须向用户展示目标块（块类型 + 文本预览）与 `blockId`，获得明确确认。
