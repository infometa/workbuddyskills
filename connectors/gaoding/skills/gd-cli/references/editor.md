# AI+ Editor

## 发现能力与使用边界

首次进入此任务分支，读取当前安装版本的帮助；构造 Action 前查询输入 Schema：

```bash
gd-cli editor --help
gd-cli editor apply --help
gd-cli editor apply --schema
```

支持的元素、Action、字段和可选值以当前 Schema 为准；操作范围、坐标/颜色语义、等待与错误处理以对应子命令 help 为准。Schema 查询无需登录或连接 Editor。不从旧示例推断能力，也不猜测不存在的字段或命令。

保持单操作者串行操作。页面包含不支持的内容时停止，让用户换用空白或专用 Page；保留原作品内容。

## 标准流程

完成标准是结构与视觉复查通过，且显式保存成功并得到公开作品 URL：

1. 查询 `gd-cli editor connect --help`，按用户目标选择 `gd-cli editor connect [target]`。不为恢复已有作品而省略目标新建 Board。只有浏览器登录、加载、编辑/保存权限和内容检查通过后才成功；连接失败时停止作图。
2. 读取 `gd-cli editor snapshot`。以最新 Snapshot 中的完整元素为基础，只改变目标字段；Update 提交完整元素，不能提交 patch。
3. 根据 Schema 和 Snapshot 构造完整、有序的 Action JSON 数组，执行 `gd-cli editor apply --input actions.json`，或用 `--input -` 从 stdin 读取。使用简短语义 ID；Connector 的方向和目标必须符合业务关系。
4. 每次 Apply 后重新读取 Snapshot。涉及布局、文字或 Connector 时，执行 `gd-cli editor screenshot --json` 并打开返回的绝对 `path` 对应的实际 PNG。文件存在或 Action 已提交都不代表渲染正确。
5. 结构和视觉复查均通过后，执行 `gd-cli editor save --json`，继续等待原命令完成，不因短暂无输出而中断或并发操作。只有保存成功才可声明作品已保存；把返回的 `workId` 和公开 `url` 交给用户，并保留 URL 中的环境参数。等待时限查 `editor save --help`。
6. 保存成功后执行 `gd-cli editor disconnect`；断开连接不代替保存。

`connect` 会替换旧 Session 并打开作品页面。连接前置检查失败会清理本次 Session，但保留浏览器页面；用户在页面中完成登录或处理访问权限后，再重新执行 `connect`。GD CLI 的 AK/SK 登录不能替代浏览器 AI+ 登录，账号密码应由用户在浏览器登录界面输入。

页面重新加载或切换作品导致 Session 断开时，重新连接预期作品并读取最新 Snapshot 后再操作。

## 复查作品

复查依据必须是 Apply 后的最新 Snapshot 和实际截图。Snapshot 用于确认元素、字段和连接关系；截图用于判断路径、文字和布局。

逐项检查，全部通过才算完成：

- 每个 Connector 的 `fromId`、`toId` 都指向预期 Shape，方向符合语义；
- 每条可见路径从 `fromId` Shape 边界开始、在 `toId` Shape 边界结束，不穿过任一端点 Shape 的填充或文字；
- 同轴相邻 Connector 也逐条检查，不能把端点穿线解释成连续线效果；
- Connector 不穿过无关 Shape，没有明显绕行、不自然折返或错误连接；
- Shape 中的文字完整可读，没有截断、溢出或意外换行；
- Shape、文字和 Connector 没有非预期重叠，必要间距真实存在；
- 整体阅读方向清楚，构图平衡，关系容易沿 Connector 追踪。

发现可执行问题时，先读取最新 Snapshot，再提交修正。Update 必须包含完整元素，不能提交 patch。若 `fromId`、`toId` 正确，但截图中的 Connector 仍穿过端点 Shape，原样提交该 Connector 的完整 Update 以触发原生路径重算；业务关系正确时不为绕开渲染问题改动关系。

修正后再次执行 `snapshot`；涉及视觉变化时再次执行 `screenshot --json` 并打开图片。存在问题就继续修正；没有可执行问题时结束复查并保存。

## 失败处理

- `LOGIN_REQUIRED`：停止作图，让用户在已打开的 AI+ 页面登录，然后重新执行 `connect`；浏览器登录不能用 `gd-cli auth` 代替。
- `EDITOR_NOT_READY`：停止并检查页面是否完成加载；重新执行 `connect`，成功前不调用写操作。
- `WORK_NOT_EDITABLE`：停止；当前用户没有该作品的编辑或保存能力。
- `EDITOR_SESSION_NOT_FOUND` 或 `EDITOR_NOT_CONNECTED`：重新连接目标作品并读取 Snapshot，不轮询旧 Session。
- `UNSUPPORTED_PAGE_CONTENT`：停止，让用户改用空白或专用 Page。
- `INVALID_ACTIONS`：根据当前 Schema、help 和最新 Snapshot 修正 Action，不原样重试。
- `APPLY_FAILED`：运行时异常已触发批次回滚；重新读取 Snapshot，确认作品处于 Apply 前状态后再决定下一步。
- `EDITOR_ROLLBACK_FAILED`：无法确认恢复到 Apply 前状态。停止所有 `apply` 和 `save`，只读取 Snapshot 或截图并报告。
- `SAVE_FAILED`：保留当前 Session，处理明确失败原因后可再次执行 `save --json`；成功前不报告已保存。
- `EDITOR_BUSY`：等待当前命令结束后再发下一条，保持串行。
- `EDITOR_RPC_TIMEOUT`：页面是否执行完成未知，Bridge 会关闭。读取类操作可重新连接同一作品后重试；`apply` 或 `save` 属于不确定写入，先重新连接同一作品并检查真实状态，再决定后续动作。无法检查原作品时停止并报告，不自动重试该写入。
- `PROTOCOL_VERSION_MISMATCH`：停止，按[更新指引](update.md)处理安装渠道，或使用协议匹配的 AI+ Editor；不绕过宿主管理。

任何写操作在超时、取消或连接中断后都可能已经提交。恢复时先观察真实状态，避免重复创建、重复 Apply 或重复 Save。
