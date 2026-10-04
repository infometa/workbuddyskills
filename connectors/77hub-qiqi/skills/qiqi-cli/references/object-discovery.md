# 对象、候选值与工作视图发现

## 选择发现路径

1. 不知道对象类型时，用 `objects` 按业务关键词取得当前 profile 的候选。
2. 已知对象但字段类型、时间语义或引用关系不清楚时，用 `describe fields <ObjectType>`。
3. 只有名称、单号或人名片段时，用 `seek` 获取跨对象有限候选。
4. 枚举或引用字段需要规范值时，用 `query values <ObjectType.field>`。
5. 需要工作台预置视图时，用 `describe view` 发现，再用 `query view <viewId>` 执行。
6. 已有稳定 `RecordRef` 时，用 `records get <RecordRef>` 读取完成任务所需的可见字段。

列表查询不属于本文件范围。对象目录和缓存只产生候选，不证明当前服务端授权；租户之间可能有相似显示名但不同对象、字段和允许值，不凭经验跳过当前 qiqi 发现。

## 字段与候选值

`describe fields` 是当前公开根字段的语义权威；它与列表默认展示字段解决不同问题。

- 用户用对象别名、单据类型名或企业自定义叫法描述一类业务记录时，用 `objects <text>` 定位可能承载该业务事实的 ObjectType；再结合对象标题、类型和上下文确认。
- 已定位 ObjectType 后，用户给出界面字段名、表单字段显示名或栏目显示名时，用 `describe fields <ObjectType> --query <text>` 做字段模糊搜索；后续查询或写入只使用返回的 canonical `fieldName`。
- 已有 canonical `fieldName` 或已从模糊搜索确认字段时，用 `describe fields <ObjectType> --field <fieldName>` 精确定位字段语义，不用 `--query` 重新扩展解释。
- 用户刚调整模板、标题或明确表示“界面上有但没查到”时，再加 `--refresh` 重新拉取字段与词汇；普通查询不要为了保险无条件刷新。
- 时间字段读取 `temporalKind`、`format` 和 `example`。
- 枚举字段用 `query values` 取得完整枚举值，不把中文标题或短编码直接当值。
- 引用字段先确认允许的对象类型，再用 `query values` 取得稳定记录 ID；不要把引用显示名直接当 ID。
- 布尔值固定使用小写 `true/false`，不调用 `query values`。
- 列表、结构化字段和引用字段不因重复读取样例而变成完整展开结果。
- 当前描述没有声明必填、可编辑或默认值时，不从样例推断这些属性。

## 候选与唯一性

`seek` 只搜索当前身份有权访问且已经接入的来源。即使只返回一条，也不能证明全系统唯一。

- 只读展示可用对象类型、标题、编码和 `RecordRef` 帮助用户消歧。
- 写操作必须使用用户给定的稳定引用、唯一业务编码或其它可验证关系确认目标。
- 无法证明唯一时请求用户选择，不默认使用第一条。

## Views 与单记录

`describe view` 列出当前身份可见的工作台视图及其输出定义，`query view` 执行其中某一个。View 独立于 ObjectType，筛选语义由服务端定义；不要把视图标题或样例反推成对象状态条件，也不要猜测清单中未出现的 `viewId`。何时选用视图而不是 `query list`，以技能正文的能力路由为准。

`records get` 返回当前用户可见的业务字段；省略显式字段时，服务端会按当前记录生效的表单配置选择详情字段，但不保证返回所有隐藏字段或动态动作。需要动作时另用 `describe actions`，需要附件时另用 `records attachments`。
