# OpenAPI 写入（新增 / 修改 / 删除）

## 何时使用

按 `objId` 对 eBuilder 表单做新增、修改、删除时使用。**全部为高风险写操作，必须走 prepare → 用户确认 → apply 两段式。**

写入前必须先用 [`fields-browser.md`](fields-browser.md) 确认真实字段名与选项值。

## 请求头契约（CLI 注入，Agent 不手写）

```text
Cookie: <weaver-e10-login 返回的完整原始 Cookie 串，原样透传，禁止裁剪/去重/改写>
eteamsid: <weaver-e10-login 返回的 ETEAMSID>
User-Agent: AgentType=<agentType>,IsAgent=true
```

## operation

| operation | risk | 必填 | 用途 |
| --- | --- | --- | --- |
| `ebuilder-form.openapi.add.prepare` | read-before-write | `objId` + `datas` | 准备新增，签发 continuation，**不写入** |
| `ebuilder-form.openapi.add.apply` | high-risk-write | `confirm` + `continuation` | 确认后执行新增 |
| `ebuilder-form.openapi.update.prepare` | read-before-write | `objId` + `datas` | 准备修改，签发 continuation |
| `ebuilder-form.openapi.update.apply` | high-risk-write | `confirm` + `continuation` | 确认后执行修改 |
| `ebuilder-form.openapi.delete.prepare` | read-before-write | `objId` + 删除条件 | 准备删除，签发 continuation |
| `ebuilder-form.openapi.delete.apply` | high-risk-write | `confirm` + `continuation` | 确认后执行删除 |

### prepare 参数

| 字段 | 说明 |
| --- | --- |
| `objId` | 表单对象 ID（必填） |
| `datas` | 数据数组（新增/修改必填）；每项为主表字段对象，明细表按 `mapping.get` 得到的 `detail1` / `detail2` 键组织 |
| `dataId` | 删除时的数据 ID；与 `mainTable` 二选一 |
| `mainTable` | 删除条件对象，按数据 ID 删除时传 `{"id":"..."}` |
| `operationinfo` | 操作备注信息（可选） |

### apply 参数

`confirm` 必须显式为 `true`；`continuation` 必须原样回传 prepare 的返回值。continuation 有效期 **10 分钟**，绑定 operation 与提交内容。

## 处理链（缺一步即失败）

1. `context.resolve` 确认 `objId`。
2. `fields.get` / `options.get` 确认写入键与选项值；关联字段用 `browser.resolve` 解析 ID。
3. `*.prepare` → 拿 `requestPreview` 与 `continuation`；**此时未写入任何数据**。
4. 向用户摘要：目标表单、动作、字段与值、影响条数、不可逆性，取得**明确确认**。
5. `*.apply` 传 `confirm: true` 与 `continuation`。
6. 需要时用 `openapi.detail` 只读回查确认结果。

## 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json ebuilder-form run ebuilder-form.openapi.add.prepare --input-json '{"objId":"121000000000000001","datas":[{"name":"示例客户"}]}'
weaver-work-cli --profile eteams --json ebuilder-form run ebuilder-form.openapi.add.apply --input-json '{"continuation":"<prepare 返回的 continuation>","confirm":true}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json ebuilder-form run ebuilder-form.openapi.delete.prepare --input-json '{"objId":"121000000000000001","dataId":"1234567890123456789"}'
weaver-work-cli --profile eteams --json ebuilder-form run ebuilder-form.openapi.delete.apply --input-json '{"continuation":"<prepare 返回的 continuation>","confirm":true}'
```

## 失败处理

| subtype | 含义 | 处置 |
| --- | --- | --- |
| `confirmation` / `required` / `confirm_required` | 未显式确认 | 先向用户确认，再传 `confirm: true` |
| `continuation_invalid` / `continuation_expired` / `continuation_mismatch` | continuation 无效、过期或不属于当前 operation | 重新执行 prepare，**不要复用旧 continuation** |
| `continuation_actor_changed` | 当前 E10 登录身份与 prepare 时不一致 | 重新 prepare 并重新取得用户确认 |
| `delete_target_required` | 删除未指定目标 | 补 `dataId` 或 `mainTable` |
| `field_required` / `field_invalid` / `field_forbidden` | 字段缺失 / 非法 / 禁止写入 | 以 `fields.get` 为准修正；禁止换字段绕过 |
| `business_error` / `http_error` | 服务端业务或 HTTP 失败 | 保留业务消息，停止后续写入 |
| `write_uncertain` | 写请求结果未知 | **立即停止，禁止自动重放**；先做只读核验再向用户汇报 |
| `session_expired` | 登录态失效 | 引导用户断开并重新连接本连接器以重新登录，然后**重新 prepare**（旧 continuation 作废） |

## 红线

- 禁止跳过 prepare 直接 apply，禁止手工构造或跨操作复用 continuation。
- `write_uncertain` 不重试：重复提交会造成重复新增或覆盖用户刚改的数据。
- 删除不可逆：目标不明确时先询问；即使用户已明确目标也必须走 continuation 校验。
- 不得通过 `checkRight=false` 绕过权限校验。
- 写接口返回业务 `status=false` 时，真实失败原因在 `data.datajson.message`，不要被外层 `message.msg=success` 覆盖；向用户转述前先读这一层。
