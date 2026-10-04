# 已发布自定义接口（按 interfacePk）

## 何时使用

用户明确指向「已发布的自定义接口」，并能提供 `interfacePk` 时使用。走 `getFormDataByPk` / `getFormDataList` / `getFormDataCount` / `saveFormData` / `updateFormData` / `deleteFormData` 一族。

**与 OpenAPI 的区分**：有 `objId` 走 OpenAPI（见 [`openapi-read.md`](openapi-read.md)）；有 `interfacePk` 且用户明确是已发布自定义接口时走本族。两者同时出现且用户没指定时，先向用户消歧，不要两边试跑。

## 请求头契约（CLI 注入，Agent 不手写）

```text
Cookie: <weaver-e10-login 返回的完整原始 Cookie 串，原样透传，禁止裁剪/去重/改写>
eteamsid: <weaver-e10-login 返回的 ETEAMSID>
User-Agent: AgentType=<agentType>,IsAgent=true
```

## operation

| operation | risk | 必填 | 用途 |
| --- | --- | --- | --- |
| `ebuilder-form.custom.detail` | read | `interfacePk` + `dataId` | 按主键查详情 |
| `ebuilder-form.custom.query` | read | `interfacePk` | 分页查询 |
| `ebuilder-form.custom.count` | read | `interfacePk` | 查询总数 |
| `ebuilder-form.custom.add.prepare` | read-before-write | `interfacePk` + `datas` | 准备新增，签发 continuation |
| `ebuilder-form.custom.add.apply` | high-risk-write | `confirm` + `continuation` | 确认后执行新增 |
| `ebuilder-form.custom.update.prepare` | read-before-write | `interfacePk` + `datas` | 准备修改，签发 continuation |
| `ebuilder-form.custom.update.apply` | high-risk-write | `confirm` + `continuation` | 确认后执行修改 |
| `ebuilder-form.custom.delete.prepare` | read-before-write | `interfacePk` + `dataIds` | 准备删除（批量，字符串数组），签发 continuation |
| `ebuilder-form.custom.delete.apply` | high-risk-write | `confirm` + `continuation` | 确认后执行删除 |

### 参数说明

| 字段 | 说明 |
| --- | --- |
| `interfacePk` | 已发布自定义接口主键（必填）；由用户提供或从接口清单取得，**不要猜测** |
| `dataId` / `dataIds` | 单条详情主键 / 批量删除主键数组 |
| `datas` | 新增、修改的数据数组 |
| `mainTable` | 查询条件对象 |
| `pageNo` / `pageSize` | 分页 |
| `operationinfo` | 操作备注（可选） |

写操作同样遵循 prepare → 用户确认 → apply 两段式，continuation 有效期 10 分钟，规则与 [`openapi-write.md`](openapi-write.md) 一致。

## 处理链

1. 确认 `interfacePk`；拿不到就向用户索取，不要从接口名猜。
2. 需要字段与选项时先 `fields.get` / `options.get`（见 [`fields-browser.md`](fields-browser.md)）。
3. 读操作直接执行；写操作走 prepare → 确认 → apply。
4. 摘要输出，不粘贴超长 JSON。

## 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json ebuilder-form run ebuilder-form.custom.count --input-json '{"interfacePk":"INTERFACE_PK","mainTable":{}}'
weaver-work-cli --profile eteams --json ebuilder-form run ebuilder-form.custom.query --input-json '{"interfacePk":"INTERFACE_PK","mainTable":{},"pageNo":1,"pageSize":20}'
weaver-work-cli --profile eteams --json ebuilder-form run ebuilder-form.custom.add.prepare --input-json '{"interfacePk":"INTERFACE_PK","datas":[{"name":"示例客户"}]}'
weaver-work-cli --profile eteams --json ebuilder-form run ebuilder-form.custom.add.apply --input-json '{"continuation":"<prepare 返回的 continuation>","confirm":true}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json ebuilder-form run ebuilder-form.custom.query --input-json '{"interfacePk":"INTERFACE_PK","mainTable":{},"pageNo":1,"pageSize":20}'
```

## 失败处理

| subtype | 含义 | 处置 |
| --- | --- | --- |
| `interface_pk_required` | 缺少 `interfacePk` | 向用户索取，不要猜 |
| `confirmation` / `required` / `confirm_required` | 未显式确认 | 先向用户确认，再传 `confirm: true` |
| `continuation_invalid` / `continuation_expired` / `continuation_mismatch` | continuation 失效 | 重新 prepare |
| `continuation_actor_changed` | 登录身份变化 | 重新 prepare 并重新取得确认 |
| `field_required` / `field_invalid` / `field_forbidden` | 字段问题 | 以 `fields.get` 为准修正，不绕过 |
| `business_error` / `http_error` | 服务端或 HTTP 失败 | 保留业务消息，停止后续写入 |
| `write_uncertain` | 结果未知 | 立即停止，禁止自动重放；先只读核验 |
| `session_expired` | 登录态失效 | 恢复会话后重新 prepare |

## 红线

- 自定义接口的字段契约由发布方定义，缺失字段时向用户索取，禁止编造默认值。
- 批量删除会一次删除 `dataIds` 全部目标，confirm 前必须把完整清单念给用户确认。
- 自定义接口的返回字段取决于接口发布时的配置，**不能假设返回完整表单数据**；缺失字段按「接口未返回」处理，不要凭字段定义猜测。
- `write_uncertain` 不重试。
