---
name: ikuai-router
version: 0.1.1
display_name: 爱快路由器管理
display_name_en: iKuai Router Management
description: 通过 ikuai-router MCP 工具管理用户局域网内的爱快（iKuai）路由器。当用户询问路由器状态、在线设备、DNS/DHCP/VLAN/NAT、VPN（WireGuard、OpenVPN、IPSec、L2TP、PPTP）、防火墙/ACL、限速、无线、路由、日志，或希望修改这些配置时使用。
description_zh: 通过 ikuai-router MCP 工具管理用户局域网内的爱快（iKuai）路由器。当用户询问路由器状态、在线设备、DNS/DHCP/VLAN/NAT、VPN（WireGuard、OpenVPN、IPSec、L2TP、PPTP）、防火墙/ACL、限速、无线、路由、日志，或希望修改这些配置时使用。
description_en: Manage the user's iKuai router on the local network through the ikuai-router MCP tools. Use when the user asks about router status, online devices, DNS/DHCP/VLAN/NAT, VPN (WireGuard, OpenVPN, IPSec, L2TP, PPTP), firewall/ACL, bandwidth limits, wireless, routing or logs, or wants to change any of these settings.
---

# 爱快路由器（iKuai Router）

本连接器通过 6 个 MCP 工具封装 `ikuai-cli` v1.0.18，对接局域网内的爱快路由器。凭证（路由器地址 + 开放 API 令牌）由 WorkBuddy 注入，**绝不要让用户把令牌粘贴到对话里**。

## 工具一览

| 工具 | 用途 | 访问路由器 |
| --- | --- | --- |
| `ikuai_system_status` | CPU、内存、运行时长、WAN IP、固件版本、流量 | 是 |
| `ikuai_online_users` | 当前在线设备（分页） | 是 |
| `ikuai_logs` | 按类别读日志：system、dhcp、pppoe、auth、arp、web、ddns、notice、wireless、url-visits | 是 |
| `ikuai_help` | 查看任意命令路径的 --help，用于发现子命令和参数 | 否 |
| `ikuai_run` | 执行其他命令，带安全门禁（见下文） | 是 |
| `ikuai_connector_info` | 内置 CLI 版本、凭证是否配置、路由器地址 | 否 |

新会话先检查连接器配置。凭证未配置时，引导用户通过连接器表单填写管理地址和 API 令牌，不要求用户在对话中提交令牌。配置齐全且当前任务需要读取设备信息时，再调用 `ikuai_system_status` 验证业务访问。若返回 `network_error`，表示访问失败，需根据具体错误核查地址、端口、路由、访问策略或设备服务状态；若返回 `auth_error`，表示认证未通过，应核查令牌有效性及授权配置，并引导用户按需重新连接。无法访问设备时，明确说明未获得实时数据。

## 使用 `ikuai_run`

命令按分段传入，参数逐个传入：

```json
{ "command": ["vpn", "wireguard", "list"], "args": ["--page", "1", "--page-size", "50"] }
{ "command": ["network", "dns", "proxy", "create"], "args": ["--domain", "example.com", "--dns-addr", "8.8.8.8", "--parse-type", "ipv4"] }
{ "command": ["users", "online", "kick", "12"] }
```

规则：

1. **先查再猜。** 不确定参数时，先用 `ikuai_help` 查该命令路径。各领域的命令速查在 `references/` 下（network.md、security.md、vpn.md、users.md、system.md 等），里面是每条命令的真实参数名。
2. **写操作先预览。** 任何 create/set/update/delete/enable/disable/kick 等操作首次调用只做 dry-run，返回 `{method, url, body}` 且 `dry_run: true`。请用自然语言告诉用户将要改什么，得到明确同意后再以 `confirm: true` 重新调用。**第一次调用绝不能设 confirm: true。**
3. **不要传** `--data`、`--raw`、`--format`、`--dry-run`、`--yes`，这些由服务端管理；确认后的删除操作会自动补 `--yes`。
4. **已屏蔽的操作**（需在 Web 后台完成）：固件升级、删除备份、修改管理员密码、内核参数、远程管理设置、磁盘管理、删除接口。用户提出时请说明原因并指引其到 Web 后台。
5. **分页。** list 类命令支持 `--page` / `--page-size`。默认每页较少，在断定"不存在"之前先把 page_size 调大（最大 200）。
6. **返回格式。** 成功为 `{ ok: true, result: <JSON> }`，列表通常是 `{ data: [...], total: N }`。失败为 `{ ok: false, error: <类型>, message, hint }`，按 hint 处理。

## 意图映射

- "有哪些设备在线" → `ikuai_online_users`
- "踢掉 / 断开 X" → 先用 `ikuai_online_users` 按 IP、MAC 或主机名找到会话 ID，再 `ikuai_run` 执行 `users online kick <ID>`（先预览，后确认）
- "DNS / DHCP / NAT / 端口映射 / VLAN" → `network …`（见 references/network.md）
- "防火墙 / 黑名单 / URL 过滤 / ACL" → `security …`（references/security.md）
- "VPN / WireGuard / OpenVPN" → `vpn …`（references/vpn.md）
- "限速 / 带宽" → `qos …`（references/qos.md）
- "日志" → `ikuai_logs`，选对应类别
- "定时重启 / 备份 / 远程管理 / 管理员账号" → `system …`（references/system.md），注意上面的屏蔽项

## 回答方式

用用户的语言概括结果，不要直接倾倒原始 JSON（除非用户要求）。展示设备或规则列表时只保留关键字段（名称、IP/MAC、是否启用、备注）。若用户接下来可能对某项操作，附上其 ID。

修改完成后确认做了什么，并建议一个验证步骤（例如重新列出该资源）。如果改动可能影响用户自身的连接（WAN、LAN、当前网段的 DHCP、用户正在使用的 VPN），在用户确认前主动提醒。
