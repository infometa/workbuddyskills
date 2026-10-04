# 单条流程共享（workflow.sharePrepare / workflow.shareApply）

## 什么时候读取

用户要把**单条**流程共享给人员 / 部门 / 分部 / 群组 / 角色 / 岗位 / 所有人（"把这条流程共享给 X / 让 X 也能看这条流程"）时读取本文件。批量共享见 `workflow-batch.md`。

## Operation

| Operation | 风险 | 固定规则 |
| --- | --- | --- |
| `workflow.sharePrepare` | read-before-write | 解析共享对象名称转 ID、取安全级别默认值，不写入；产出 continuation |
| `workflow.shareApply` | high-risk-write | 提交流程共享（addRequestShare2）；必须 `confirm: true` + continuation |

## 确认链

1. `sharePrepare` → 向用户摘要目标 `requestId` / 共享对象解析结果 / 安全级别范围 / 风险。
2. 等用户**明确确认**。
3. `shareApply` 带 `confirm: true` 与 `continuation`（**无需重复传 shareObjects / 安全级别，continuation 已携带**）。
4. 返回 `partial/write_uncertain` 时**立即停止**，先只读回查，**不自动重放**。

## 输入

- `requestId`（数字或仅数字字符串）或 `group` + `index` 定位流程；`requestId` 必须来自查询索引，模型不能自己编。
- `shareObjects`：共享对象 JSON 数组字符串，每项 `{"type": <类型>, "name": <名称>}`；`all` 不需要 `name`。
- `minSeclevel`：最小安全级别（与默认值取大），仅用户明确要求限制时传。
- `maxSeclevel`：最大安全级别（与默认值取小），仅用户明确要求限制时传。
- `continuation`（仅 Apply）：Prepare 返回的短句柄（形如 `wc-1a2b3c4d5e6f7a8b`），载荷由 CLI 托管在本机状态目录；原样回传，禁止解析、手工构造 / 修改 / 复用。
- `confirm`（仅 Apply）：固定为 `true`。

## 共享对象类型

| type | 共享对象 | name 说明 |
| --- | --- | --- |
| `user` | 人员 | 必填，姓名自动转 ID |
| `dept` | 部门 | 必填，部门名自动转 ID |
| `subcompany` | 分部 | 必填，分部名自动转 ID |
| `group` | 群组 | 必填，群组名自动转 ID |
| `role` | 角色 | 必填，角色名自动转 ID |
| `position` | 岗位 | 必填，岗位名自动转 ID |
| `all` | 所有人 | 不需要 name，直接 `{"type":"all"}` |

名称自动转 ID；`name` 也支持 `"名称(ID)"`（如 `"张三(1001)"`）：此时**直接采用括号里的 ID、不再搜名称**，多命中澄清后按该形式回传即可。多命中返回候选列表让用户确认，禁止静默全选（不允许把同名多人全部设为共享对象）；0 命中报错提示核对名称。

## 示例

### 共享给一个人 + 一个部门 + 所有人

Windows PowerShell：

```powershell
Set-Content -Encoding utf8 -LiteralPath .\share.json -Value @'
{
  "requestId": "1307945196792242242",
  "shareObjects": ["{\"type\":\"user\",\"name\":\"张三\"}","{\"type\":\"dept\",\"name\":\"产品研发中心\"}","{\"type\":\"all\"}"]
}
'@
weaver-work-cli --profile eteams --json workflow run workflow.sharePrepare --input .\share.json
```

macOS/Linux（bash/zsh）：

```bash
cat > ./share.json <<'JSON'
{
  "requestId": "1307945196792242242",
  "shareObjects": ["{\"type\":\"user\",\"name\":\"张三\"}","{\"type\":\"dept\",\"name\":\"产品研发中心\"}","{\"type\":\"all\"}"]
}
JSON
weaver-work-cli --profile eteams --json workflow run workflow.sharePrepare --input ./share.json
```

确认后提交：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json workflow run workflow.shareApply --input-json '{"confirm":true,"continuation":"<sharePrepare 返回的句柄，形如 wc-1a2b3c4d5e6f7a8b>"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json workflow run workflow.shareApply --input-json '{"confirm":true,"continuation":"<sharePrepare 返回的句柄，形如 wc-1a2b3c4d5e6f7a8b>"}'
```

### 按列表序号定位 + 限制安全级别范围

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json workflow run workflow.sharePrepare --input-json '{"index":3,"shareObjects":["{\"type\":\"user\",\"name\":\"张三\"}"],"minSeclevel":"1","maxSeclevel":"3"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json workflow run workflow.sharePrepare --input-json '{"index":3,"shareObjects":["{\"type\":\"user\",\"name\":\"张三\"}"],"minSeclevel":"1","maxSeclevel":"3"}'
```

## 返回

- `sharePrepare` 返回共享对象解析结果、安全级别默认值与 `continuation`；不写入。
- `shareApply` 透传 addRequestShare2 响应：`{code, status, msg, fail, data: [{sourceId, result, msg}, ...]}`（单条 data 数组 1 个元素，`result=true/false` 表示是否共享成功，`msg` 含原因）；或返回 `partial/write_uncertain`。
- 按退出码 / `error.type` / `error.subtype` / `error.message` 判断成败，不盲目重试。

## 注意

- 这不是 `workflow.operatePrepare` 的参数（operate 无共享动作）。
- `requestId` 必须来自查询索引；`shareObjects` 名称多命中必须澄清，禁止静默全选。
- `continuation` 是 CLI 托管的短句柄（形如 `wc-1a2b3c4d5e6f7a8b`），Agent 只原样回传，禁止解析、手工构造 / 修改 / 复用；`confirm` 必须且只能为 `true`。
- Apply 被重复执行、且上一次已经成功时，返回 `ok:true` + `data.status = "ALREADY_APPLIED"`（含 `previousResult`；若上一次是"服务端已成功回执、只是没来得及写回结果"，还会给出 `requestId`）——**这不是失败**，本次没有重复写入，按上一次结果汇报即可，不要重跑 Prepare。
- Apply 报 `validation/continuation_busy` 时，说明句柄正被另一次执行占用、**上一次还没发出任何写入**：**稍后原样重试同一条命令**即可，不必重跑 Prepare、也不要换句柄。
- Apply 报 `validation/continuation_consumed` 时，说明占用该句柄的那次执行停在无法判定的旧状态：先只读核对目标流程是否已生效，确认没生效才重跑 Prepare。
- 安全级别范围仅在用户明确要求限制时传 `minSeclevel` / `maxSeclevel`。
- 写操作遇登录失效 / 超时 / 断连返回 `partial/write_uncertain`，**禁止自动重放**，先只读回查确认状态，不得重复提交。
- 同一操作连续 2 次失败必须停止。
- 不写任何凭据（Cookie / ETEAMSID / Token / 操作员标识由 CLI 托管）。
