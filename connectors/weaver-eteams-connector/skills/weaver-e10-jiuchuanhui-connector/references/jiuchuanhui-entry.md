# 入口：schema 与统一调用方式

## 何时使用

首次接触九氚汇模块、不确定某个 operation 是否存在、需要核对字段与风险等级，或想确认写操作是否走 prepare/apply 时。

## 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams jiuchuanhui schema
weaver-work-cli --profile eteams --json jiuchuanhui schema
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams jiuchuanhui schema
weaver-work-cli --profile eteams --json jiuchuanhui schema
```

## 输出处理

`schema` 输出全部 operation 的 name、risk 和 inputSchema。`weaver-work-cli --profile eteams jiuchuanhui schema` 是 operation、字段和风险等级的合约来源，任何调用都以它为最终依据；references 是第一信息源，`schema` 是契约校验。

## 调用方式

统一入口 `weaver-work-cli --profile eteams --json jiuchuanhui run <operation>`。输入支持两种方式：`--input-json '<json>'` 内联 JSON、`--input <path>` 从文件读取：

Windows PowerShell：

```powershell
# 内联 JSON（复杂/嵌套结构）
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.customer.get --input-json '{"id":"100001"}'
# 从文件读取 JSON
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.customer.create.prepare --input .\customer-create.json
```

macOS/Linux（bash/zsh）：

```bash
# 内联 JSON（复杂/嵌套结构）
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.customer.get --input-json '{"id":"100001"}'
# 从文件读取 JSON
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.customer.create.prepare --input ./customer-create.json
```

简单 JSON 传 `--input-json '<json>'`；复杂或多行 JSON 先写入 UTF-8 文件再传 `--input <path>`。

## 注意

- 业务输入不得包含 Cookie、ETEAMSID、Token 或内部控制字段；CLI 会拒绝这些 key。
- 写 operation 都带 `.prepare` / `.apply` 后缀；`.apply` 只接受 prepare 返回的 continuation 且 `confirm:true`。
- 不要在对话中手写 E10 原始接口路径或拼 HTTP 鉴权细节。

## 失败处理

- operation 不存在或字段不符：检查 `jiuchuanhui schema`，按合约修正，不猜字段。
- `authentication`/`session_expired`：按共享规则完成登录后再继续。
