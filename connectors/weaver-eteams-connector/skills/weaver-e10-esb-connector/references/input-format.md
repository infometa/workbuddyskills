# 获取动作流入参模板（esb.input-format）

## 何时使用

- 用户问「这条动作流要传哪些参数」「给我动作流 XXX 的入参格式」「触发前先看看参数模板」。
- 触发动作流前需要确认 `customParams` 结构：主表字段名、`detail1` / `detail2` 明细表形状、哪些字段是可选占位。
- 该 operation 是只读查询，无业务副作用，不需要用户确认即可调用。

## 输入要点

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `applicationId` | 是 | 动作流 ID（数字串，长整型按字符串传递）。与触发接口的 `esbFlowId` 指向同一动作流。 |

## 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json esb run esb.input-format --input-json '{"applicationId":"900000000000000001"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json esb run esb.input-format --input-json '{"applicationId":"900000000000000001"}'
```

## 输出处理

`data` 字段：

- `esbFlowId`：触发时直接使用的动作流 ID；接口未返回时回落到传入的 `applicationId`。
- `moduleSource`：调用模块来源，接口未返回时为默认值 `AISKILL`；触发时可不传，仅二开场景传 `ecode`。
- `customParams`：入参模板本体。主表在 `customParams.mainTable`，明细表按平台约定嵌套在 `mainTable` 内的 `detail1` / `detail2` 数组中，字段名随动作流定义。
- `optionalFields`：模板中取值为 `#可选` 的字段路径列表（如 `mainTable.a`、`mainTable.detail1[0].a1`），提示这些字段可以替换为真实值或删除。

组装触发参数时按模板结构原样填充业务值，不要自行新增模板外的字段。

## 注意

- 接口返回的是**模板**而非实际数据，`#可选` 是占位符，不是要传的字面值。
- 模板字段名由目标动作流定义，不同动作流结构不同；不要跨动作流套用字段名。
- 只需要字段清单时可让 Agent 从 `optionalFields` 与 `customParams` 中提取，不要原样粘贴超长 JSON。

## 失败处理

- `field_invalid`：`applicationId` 不是数字 ID，请核对动作流 ID。
- `flow_not_found`：动作流不存在或已被删除，不要重试。
- `tenant_permission_denied` / `permission_denied` / `tenant_missing`：权限或租户上下文问题，确认登录态与权限后由用户处理。
- `session_expired`：E10 登录态失效，引导用户断开并重新连接本连接器。
- 其他非成功响应：按 stderr JSON 的 `error.type` / `error.subtype` / `error.message` 说明失败原因，不要臆测返回结构。
