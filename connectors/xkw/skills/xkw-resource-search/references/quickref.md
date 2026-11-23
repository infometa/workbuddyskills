# 学科网 MCP 调用速查

本文件是**调用前速查**：参数怎么放、每个工具怎么调、高频示例。
需要查字段含义见 [公共参数](params.md)；需要查返回结构与错误码见 [返回与错误](internals.md)。

## 速查

- 所有参数放在 `arguments.requestDto` 内。
- **`courseware`**：必传 `scenario`（`1` 课件 / `2` 教案 / `3` 两者），不省略。
- **`pastExamPaper` / `modelExamPaper`**：必传 `scenario`（`1` 中考 / `2` 高考 / `3` 两者），不省略。
- **`examPaper`**：`scenario` 可选；未传时不限考试场景。
- **`studyGuide` / `assignment` / `resource`**：不用 `scenario`；用 `keywords` + 结构化筛选。
- 通用上限：`size` 单次最多 **20**，未指定时传 **5**。
- **`keywords` 不要写「中考」**：和 `area` 一起用时结果会清零，改由 `scenario=1` 表达。`keywords` 只放学科和主题（`数学`、`勾股定理`）。

## 调用格式

下面 JSON 示例均为 MCP `tools/call` 的 `params` 内容，参数统一放在 `arguments.requestDto`。实际调用遵循宿主展示的工具输入 Schema。

`X-Client-Id`、`X-User-Id`、`X-Request-Id` 由调用方或中台放在 HTTP Header 中，用于请求上下文和调用记录。它们不放入工具参数，也不由模型猜测或生成用户身份。

## 直接调用示例

### 课件和教案：courseware

查课件传 `scenario=1`，查教案传 `2`，两类都要传 `3`。这不是考试场景。省略或传其他值时服务不自动限定类型，本 Skill 必须填写有效值。

找“浮力”课件：

```json
{"name":"courseware","arguments":{"requestDto":{"keywords":"浮力","scenario":1,"size":5}}}
```

找“浮力”教案：

```json
{"name":"courseware","arguments":{"requestDto":{"keywords":"浮力","scenario":2,"size":5}}}
```

### 学案和作业：studyGuide、assignment

两个工具固定查询各自分类及全部下级分类，通常省略 `typeId`、`includeSubtypes`。

```json
{"name":"studyGuide","arguments":{"requestDto":{"keywords":"浮力","size":5}}}
```

```json
{"name":"assignment","arguments":{"requestDto":{"keywords":"一元一次方程","size":5}}}
```

`studyGuide` 只允许省略 `typeId` 或传 `"4103"`；`assignment` 只允许省略或传 `"4104"`，都不接受子类 ID。`includeSubtypes` 无论省略、真、假，都不改变这两个工具包含全部子类的范围。仅传 `includeSubtypes=true` 也可以，但没有必要。

### 通用资源：resource

未限定资料类型时，按关键词查询，结果可能包含多种分类：

```json
{"name":"resource","arguments":{"requestDto":{"keywords":"浮力","size":5}}}
```

需要精确查询子类时，用 `searchMetadata` 确认真实分类编号。例如学习任务单分类确认是 `410302` 后：

```json
{"name":"resource","arguments":{"requestDto":{"keywords":"浮力","typeId":"410302","size":5}}}
```

查询整个题集分支，包括试题汇编、专项训练、综合训练：

```json
{"name":"resource","arguments":{"requestDto":{"keywords":"一元一次方程","typeId":"4106","includeSubtypes":true,"size":5}}}
```

`typeId` 默认只筛当前分类；`includeSubtypes=true` 时展开当前分类及全部下级分类，必须同时提供 `typeId`。编号和课程限制以实时字典为准。`resource` 不使用 `scenario`，不能靠该参数区分课件、教案或中高考场景。已明确五类资源时优先专项工具，不用通用检索绕过专项工具的服务异常。

### 普通试卷：examPaper

查期中、期末、单元等试卷候选，或未限定中高考真题、模拟卷时使用：

```json
{"name":"examPaper","arguments":{"requestDto":{"keywords":"期末 数学","grade":"八年级","subjectId":2,"size":5}}}
```

不传 `scenario` 时，本工具固定为「试卷」类型（不排除真题和模拟卷）。新增版本支持 `scenario=1` 中考场景、`2` 高考场景、`3` 两者；未传或其他值时保持原查询范围。仅增加场景过滤，不设置真题工具的统考条件，也不包含模拟卷场景集合。当前没有 `paperType`；要真题、模拟卷仍使用对应专用工具。“期末”“单元”等词在此只是标题关键词。

下面示例要求服务已部署新增场景筛选，并在工具说明中声明支持。旧版 Schema 也存在 `scenario` 字段，不能仅凭字段存在判断能力已上线：

```json
{"name":"examPaper","arguments":{"requestDto":{"keywords":"数学","scenario":1,"size":5}}}
```

### 中高考真题：pastExamPaper

根据 `scenario` 设置中考或高考场景。

找中考数学真题：

```json
{"name":"pastExamPaper","arguments":{"requestDto":{"keywords":"数学","scenario":1,"size":5}}}
```

带地区时同理，场景只由 `scenario` 表达，`keywords` 不重复写「中考」：

```json
{"name":"pastExamPaper","arguments":{"requestDto":{"keywords":"数学","scenario":1,"area":"长沙市","size":5}}}
```

`keywords="中考数学"` + `area="长沙市"` 会返回 **0 条**（参数写法问题，不是库里没有）。

`scenario=1` 为中考、`2` 为高考、`3` 为两者。未指定中考或高考时传 `3`，不要省略；省略或传其他值时下游不附加考试场景条件。

### 中高考模拟卷：modelExamPaper

本工具有独立的模拟卷场景筛选，可以作为“试卷”类工具使用。中考、高考模拟卷的具体场景由服务端组装，模型只需传 `scenario`，不传内部编号。

找高考数学模拟卷：

```json
{"name":"modelExamPaper","arguments":{"requestDto":{"keywords":"数学","scenario":2,"size":5}}}
```

场景用法同真题：`1` 中考、`2` 高考、`3` 两者。未限定中高考范围时传 `3`。普通年级的练习卷或单元测试卷，不自动当成中高考模拟卷，按实际需求选择 `examPaper` 或 `assignment`。

### 两个场景都要时

三个试卷工具在支持对应筛选的版本中，`scenario=3` 都表示两个场景合并后排序取前 N 条。前 N 条可能全属于一种场景，这不等于另一种场景未参加查询。

用户要求“中考、高考各两份真题”，分别调用：

```json
{"name":"pastExamPaper","arguments":{"requestDto":{"keywords":"数学","scenario":1,"size":2}}}
```

```json
{"name":"pastExamPaper","arguments":{"requestDto":{"keywords":"数学","scenario":2,"size":2}}}
```

真题与模拟卷都要时，分别调用 `pastExamPaper`、`modelExamPaper`。保留用户明确的关键词和筛选条件，按 `documentId` 去重；返回不足时说明实际数量。

## 连续追问示例

工具每次只处理本次传入的参数，不保存对话筛选条件。根据当前需求重新构造 `requestDto`，保留仍适用的条件；更换学科、年级或教材后，先核对关联 ID，不复用不再适用的编号。

例如用户先要高考数学真题：

```json
{"name":"pastExamPaper","arguments":{"requestDto":{"keywords":"数学","scenario":2,"size":5}}}
```

接着说“改找高一数学课件”，新的年级和资料类型已经明确，应使用课件工具的场景含义：

```json
{"name":"courseware","arguments":{"requestDto":{"keywords":"数学","grade":"高一","subjectId":2,"scenario":1,"size":5}}}
```

再说“换成教案”，保留高一、数学和数量，调整课件工具的场景：

```json
{"name":"courseware","arguments":{"requestDto":{"keywords":"数学","grade":"高一","subjectId":2,"scenario":2,"size":5}}}
```

如果又改为其他学科，更新关键词，并重新核对此前选择的学科、课程、教材、章节及知识点 ID。用户仍要求的版本等限定需要继续满足；不能为避免参数冲突而静默丢弃。学案和作业通常省略 `typeId`、`includeSubtypes`，不照搬前一个工具的分类参数。

用户要求“再来几份”时，按两步走：① 先把同条件的 `size` 加到最多 20，按 `documentId` 排除已展示项；② 仍不够就传 `page=2`、`page=3` 翻页（**`page` 是有效参数**，`searchInfo.page` 会回显）。

`page` 的上限约为 `total / size`，超过会返回 500「服务器异常」（不是参数错误，重试也不会成功）。资源工具不支持 `offset`，别用。
