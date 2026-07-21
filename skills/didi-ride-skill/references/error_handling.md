# 错误处理指南

本文档说明 didi-ride-skill skill 使用过程中可能遇到的错误及解决方案。

> `<skill-dir>` 代表 didi-ride-skill 技能的安装根目录（即 SKILL.md 所在目录），可通过 `openclaw skills info didi-ride-skill` 获取。

## 目录

- [错误处理指南](#错误处理指南)
  - [目录](#目录)
  - [mcporter Missing KEY parameter](#mcporter-missing-key-parameter)
  - [SSE error / apiKey 占位符泄漏](#sse-error--apikey-占位符泄漏)
  - [mcporter.json 校验错误](#mcporterjson-校验错误invalid_type--failed-to-parse-json)
  - [taxi_create_order 调用失败](#taxi_create_order-调用失败)
  - [Unknown MCP server 错误](#unknown-mcp-server-错误)
  - [统一错误码表](#统一错误码表)
  - [参数错误排查](#参数错误排查statuscode400--backend-call-failed)
  - [常见问题 (FAQ)](#常见问题-faq)
  - [获取帮助](#获取帮助)

***

## mcporter Missing KEY parameter

mcporter 报 `Missing KEY parameter` 时，**不代表 MCP Key 已失效**，禁止直接向用户索要 Key。

可能原因（按概率排序逐一排查）：

1. **`$DIDI_MCP_KEY` 环境变量未展开**：`MCP_URL` 赋值时用了单引号（`'$DIDI_MCP_KEY'`）而非双引号，导致变量字面量传入。确认调用命令中 `MCP_URL` 使用双引号包裹，然后重试。
2. **当前 shell 未注入环境变量**：openclaw 在每次 agent run 启动时自动注入 `DIDI_MCP_KEY`，但手动在终端直接运行 mcporter 时该变量不存在。执行 `echo $DIDI_MCP_KEY` 验证——若为空，在终端手动 `export DIDI_MCP_KEY=<key>` 后重试，或改在 openclaw agent 环境中调用。
3. **mcporter.json 配置异常**：若当前目录下 `config/mcporter.json` 或 `~/.mcporter/mcporter.json` 存在且格式异常，mcporter 会在启动阶段直接崩溃（报 `invalid_type` 或 `Failed to parse JSON`），所有命令不可用。**不要删除该文件**（可能包含用户其他应用的配置），改用 `--config` 绕过——见 SKILL.md §3.2 第 3 条。
4. **Key 本身确实无效**：若以上均排除，执行 `openclaw config get skills.entries.didi-ride-skill.apiKey` 确认 Key 已配置，若返回空则按 `### 3.9 MCP KEY 与配置` 流程重新配置。

***

## SSE error / apiKey 占位符泄漏

mcporter 报 `SseError: SSE error: Invalid content type, expected "text/event-stream"` 时，最常见根因是把 OpenClaw 的哨兵值 `__OPENCLAW_REDACTED__` 当成真实 Key 拼进了 MCP URL。

**症状**：

- 拼出来的 URL 实际是 `https://mcp-dev.didichuxing.com/mcp-servers?key=__OPENCLAW_REDACTED__`
- 服务端把它当成无效 Key 拒绝，返回 HTML / 纯文本错误页（不是 SSE 流）
- mcporter 收到非 `text/event-stream` 响应直接抛 `SseError`

**为什么会拼错**：误以为 `openclaw config get skills.entries.didi-ride-skill.apiKey` 配上 `--raw` / `awk` / `sed` 之类的手段能拿到真实 Key 字面量。实际上：

> `openclaw config get`（含 `--raw`）**永远不会**返回真实 Key 字面量。`__OPENCLAW_REDACTED__` 是"已配置"的哨兵值，不是 Key 本身。真实 Key 由 OpenClaw 在每次 agent run 启动时注入到环境变量 `DIDI_MCP_KEY`，调用方只能通过 `$DIDI_MCP_KEY` 使用。

**修复步骤**：

1. 自检环境变量是否注入：

   ```bash
   printenv DIDI_MCP_KEY >/dev/null && echo env_ok || echo env_missing
   ```

2. 若 `env_ok`：把 URL 拼接改回 SKILL.md §3.2 第 4 条的固定写法，不要再尝试从 config 提取 Key：

   ```bash
   MCP_URL="https://mcp-dev.didichuxing.com/mcp-servers?key=$DIDI_MCP_KEY"
   mcporter call "$MCP_URL" <tool> --args '...'
   ```

3. 若 `env_missing`：当前不在 openclaw agent run 上下文里（例如手动终端调用），按 SKILL.md §3.9 引导用户重新配置；或临时 `export DIDI_MCP_KEY=<key>` 后重试。

**禁止**：

- 禁止用 `openclaw config get ... --raw` / `awk` / `sed` / `jq` 等任何手段尝试从配置提取 Key 字面量
- 禁止把 `__OPENCLAW_REDACTED__` 出现在任何 URL / header / 参数中
- 禁止在见到本错误时向用户索要新的 Key——Key 可能完全有效，只是用错了

***

## mcporter.json 校验错误（`invalid_type` / `Failed to parse JSON`）

mcporter 启动时报 `invalid_type, expected record` 或 `Failed to parse JSON` 等校验错误时，说明当前目录的 `config/mcporter.json` 或 `~/.mcporter/mcporter.json` 存在且内容异常（格式不正确、空文件、或 AI 之前错误创建的）。

**格式错误的 mcporter.json 会阻止 mcporter 所有命令执行**，包括 URL 直连模式。

**解决方法**（不要删除用户的 mcporter.json，可能包含其他应用配置）：

```bash
# 创建一个空的合法配置用于绕过
echo '{"mcpServers":{}}' > /tmp/.mcporter-empty.json
# 后续所有 mcporter 命令加 --config 参数
mcporter --config /tmp/.mcporter-empty.json call "$MCP_URL" <tool> --args '...'
```

本 skill 使用 URL 直连模式，不依赖 mcporter.json。**禁止创建或修改 `config/mcporter.json`**。

***

## taxi_create_order 调用失败

调用 `taxi_create_order` 时若返回 `Streamable HTTP error: Unexpected content type: text/plain; charset=utf-8`，按以下方式处理。

1. **停止当前打车流程**（不要继续重试或切换 tool，也不要向用户索要新的 Key）；
2. 向用户输出以下**固定文案**（原样复制，不要改写）：

   > 未开通DiDi MCP 免密支付的用户，需要到 DiDi MCP 官网开通免密支付，审核完成后，即可调用全部的打车接口能力

> ⚠️ 见到该字面量直接进入本章节处理，输出固定文案并停止流程，不要自行扩展解释。

***

## Unknown MCP server 错误

mcporter 报 `Unknown MCP server 'xxx'` 时，根据 `xxx` 的值判断：

- **`xxx` 是工具名**（如 `Unknown MCP server 'maps_textsearch'`）：说明命令格式不对。第一个位置参数必须是完整 URL（`"$MCP_URL"`），第二个位置参数才是 tool name。检查是否遗漏了 URL、或 URL 变量未定义。
- **`xxx` 是自定义名称**（如 `Unknown MCP server 'didi-mcp'`）：说明使用了 `--server` 标志。**本 skill 禁止使用 `--server` 标志**——它需要已注册的命名 server，而 didi-ride-skill 始终使用 URL 直连模式。去掉 `--server xxx` 参数后重试。

***

## 统一错误码表

所有 MCP 工具返回的统一错误码对照：

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| `-32001` | 命中限流 | 请等待一段时间后重试（配额限制按时间窗口重置） |
| `-32002` | 鉴权失败（`auth failed`） | Key 存在但无效或已过期，执行 `### 3.9 MCP KEY 与配置` 的引导流程（含发送二维码） |
| `-32010` | 参数验证失败 | 检查参数格式，确保所有值为字符串 |
| `-32011` | 订单不存在 | 确认订单ID正确 |
| `-32021` | 预估结果过期 | 重新调用价格预估获取新的 traceId |
| `-32030` | 不支持订单类型 | 该类型订单不支持此操作 |
| `-32031` | 订单未支付 | 订单未进入支付状态 |
| `-32040` | 订单已经取消过了 | 订单已被取消，无需重复操作 |
| `-32041` | 订单无法被取消 | 司机已接单或订单已完成，无法通过 API 取消 |
| `-32050` | 内部错误 | 稍后重试，如持续失败请联系客服 |
| `-32060` | 支付失败 | 检查支付账户状态或更换支付方式 |

***

## 参数错误排查（`StatusCode=400` / `backend call failed`）

mcporter 返回 `backend call failed: ... StatusCode=400` 时，**根因几乎都是参数问题**（mcporter 不会展示 MCP Server 返回的具体错误原因，只给出 StatusCode）。按以下顺序逐项排查：

1. **参数名拼写**——最常见根因。典型错误对照：

   | 错误写法 | 正确写法 | 所属工具 |
   |----------|----------|----------|
   | `keyword` | `keywords`（复数） | `maps_textsearch`、`maps_place_around` |
   | `region` / `province` | `city` | `maps_textsearch`、`maps_direction_transit` |
   | `origin` / `destination` | `from_lat`/`from_lng`/`from_name` 与 `to_lat`/`to_lng`/`to_name`（六字段） | `taxi_estimate`、`taxi_generate_ride_app_link` |
   | `order` / `orderId` | `order_id`（snake_case） | `taxi_query_order`、`taxi_cancel_order`、`taxi_get_driver_location` |
   | `traceId` | `estimate_trace_id` | `taxi_create_order` |

2. **必填参数缺失**——例如 `maps_textsearch` 的 `city` 必填（即使已提供坐标也不能省）。

3. **类型错误**——`--args` JSON 对象内**所有参数值必须是字符串**：
   - 经纬度 `"39.908858"` ✅，不是 `39.908858` ❌
   - `product_category` 填 `"1"` ✅，不是 `1` ❌

4. **城市名完整格式**——`"北京市"` ✅，`"北京"` ❌。

5. **自检手段**——如果以上都核对过仍失败，执行 `mcporter list "$MCP_URL"` 查看工具的完整函数签名，逐字段比对。

> ⚠️ **不要因为看到 `StatusCode=400` 就怀疑 mcporter 工具坏了**。这个报错 99% 是参数问题，不是 mcporter 或网络问题。

***

## 常见问题 (FAQ)

**Q: 为什么说"我要上班"没反应？**
A: 需要先配置 `assets/PREFERENCE.md` 中的家和公司地址，以及上班场景的车型偏好。

**Q: 预估价格和实际价格不一致？**
A: 预估价格为参考值，实际费用以行程完成后为准。

**Q: 如何查看历史订单？**
A: 当前 API 仅支持查询 MCP 渠道未完成订单，历史订单请在滴滴 App 中查看。

**Q: 支持哪些城市？**
A: 支持滴滴服务覆盖的所有中国大陆城市。

***

## 获取帮助

如果以上方案无法解决问题，请：

1. 检查 [workflow.md](./workflow.md) 确认操作流程
2. 访问 <https://mcp.didichuxing.com> 获取最新文档
