# AppKey 与分享

AppKey 是终端用户通道（SSE / WebSocket 对话、分享页）调用应用时用的密钥。应用发布过一次才会有 key。

```bash
adp app key get --app-id <id> --format json            # 默认打码：前4位…后4位
adp app key get --app-id <id> --reveal --format json   # result.appKey 是完整明文
adp app key list --app-id <id> --reveal
```

- 用户要拿 key 去集成时用 `--reveal`。拿到后直接交给用户或写入用户指定的环境变量，不要回显到日志、提交到仓库或贴进对话摘要。
- 启停、删除用 `--key <后4位以上>` 指定，不需要粘贴完整 key：`adp app key disable --key Wezw`。
- 应用至少保留一个启用的 key（`AppKeyLastEnabled`）。`disable` / `delete` 在 `--dry-run` 时也会先读 key 列表，最后一把启用的 key 直接报这个错。轮换时先 `create`，再禁用旧的。
- `create` 报 `AppKeyNotCreated` 表示平台没保存新 key（部分账号只允许一个 key），继续用现有 key。
- 查一个 key 属于哪个应用：`printf %s "$KEY" | adp app key lookup --stdin`。
- `adp chat` 会自动读取 AppKey，不需要手动传。

## 分享

```bash
adp app share-url --app-id <id> --yes --format json     # result.shareUrl：公开对话链接
adp conversation share create --app-id <id> --record-id <提问记录ID> --record-id <回复记录ID>
adp conversation share get --share-id <id>
adp app shared list --space-id <id> --query 助手          # 企业共享应用目录
```

- `share-url` 每次都会换一条新链接，旧链接可能失效。只在用户要链接时调用，并告诉用户之前的链接可能不能用了。
- 分享会话没有删除接口，拿到分享 ID 的人都能看。分享前和用户确认内容可以公开。
- 记录 ID 来自对话流：提问和回复各有一个 `RecordId`。快照里 `type: "thought"` 是模型思考，展示给用户时通常跳过。

## A2A 地址

```bash
adp app a2a-url --app-id <id> --format json               # 默认打码
adp app a2a-url --app-id <id> --refresh --yes --reveal    # 生成或轮换，旧地址立即失效
```

发布后 A2A 地址不会自动生成：没跑过 `--refresh` 时 `a2a-url` 返回空的 `a2aUrl`（`generated: false`），这不是发布失败。第一次需要 `--refresh --yes` 生成；之后再 `--refresh` 会轮换地址，旧地址立即失效，所以只在第一次或用户明确要轮换时用。

- A2A 地址里的 `agt_…` 段等同凭证，和 AppKey 一样：只在用户要接入时才 `--reveal`，不要写进日志或回复里的其他地方。
- 必须先 `adp deploy` 发布，否则报 `AppNotReleased`。轮换会让已接入的调用方失效，先问用户。
