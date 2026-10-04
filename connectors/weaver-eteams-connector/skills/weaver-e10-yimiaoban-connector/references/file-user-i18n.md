# 文件上传 / 媒体预览 / 用户状态 / i18n 标签

## 何时使用

发图/发文件前把本地文件传到 E10 文件服务；给图片/视频拼可访问的预览与下载链接；查某人各端在线状态；翻译 IM 里的 i18n 标签 id。

| operation | 用途 |
| --- | --- |
| `im.file.upload` | 上传本地文件（module=im），返回 fileObj + 消息对象形态（供 `img`/`file` 引用） |
| `im.file.preview` | 生成图片/视频预览与下载 URL（需登录态访问；图片支持 small/large/original） |
| `im.file.download` | 把消息里的图片/视频/文件**下载到本地**（需登录态；父目录须存在、拒绝覆盖） |
| `im.user.state` | 查指定人员各在线设备状态（sub_state 强制 0 不订阅） |
| `im.i18n.labels` | 批量翻译国际化标签 id → 当前语言文案 |

## 输入要点

- `file.upload`：`file` 本地路径 + 可选 `name`/`shareGroup`（发群消息用）/`shareUsers`（uid 数组，发单聊用）/`permission`。旧名 `filePath`（= `file`）与 `shareGroups`（= `shareGroup`）仍兼容，但**与新名同时出现且取值不一致会返回 `alias_conflict`**（不要依赖静默覆盖）。返回 `fileObj`、`img`、`file` 两种消息对象形态；发消息也可以直接传本地路径让 CLI 内部上传。
- `file.preview`：需要 `fileId` + `msgid` + `kind`(img/video) + 场景（`groupId` 或 `toUid`+`toCid`）；`imgFormat` small/large/original。返回的是**绝对地址**（含 baseUrl），但需要登录态才能访问，直接嵌 Markdown 会 401。
- `file.download`：`fileId` + `msgid` + `output`（明确的本地文件路径）+ 场景（`groupId` 或 `toUid`+`toCid`）；可选 `kind`（img/video/file，默认 img）、`imgFormat`（默认 small，要原图传 original）。父目录必须存在，目标文件已存在会拒绝覆盖；下载内容若是图片且扩展名与文件头不符会自动纠正（如实际为 PNG 时 `.jpg` → `.png`，返回 `renamedFrom`）。
- 用户状态：`users` uid 数组（不要写成 `uids`）+ 可选 `devType` 过滤；`mask` 控制返回字段（默认 7）。解析失败的 uid 需确认后传 `removeFailed:true` 跳过。
- 上传/预览涉及**本地文件**：必须先与用户确认文件内容可能进入大模型上下文、并会上传到 E10 文件服务。
- `file.download` 会把 E10 上的附件/媒体落到本地磁盘：下载前同样要与用户确认目标路径，下载完成后才可把本地文件当作可查看内容（不要先假装看过）。

## 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json im run im.file.upload --input-json '{"file":"C:\\tmp\\方案.docx","name":"方案.docx"}'
weaver-work-cli --profile eteams --json im run im.file.download --input-json '{"fileId":"FILE1","msgid":"1788334281700000004","kind":"img","groupId":"1788334281700000004","output":"C:\\tmp\\photo.png"}'
weaver-work-cli --profile eteams --json im run im.i18n.labels --input-json '{"ids":["1001","1002"]}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json im run im.file.upload --input-json '{"file":"/tmp/方案.docx","name":"方案.docx"}'
weaver-work-cli --profile eteams --json im run im.file.download --input-json '{"fileId":"FILE1","msgid":"1788334281700000004","kind":"img","groupId":"1788334281700000004","output":"/tmp/photo.png"}'
weaver-work-cli --profile eteams --json im run im.i18n.labels --input-json '{"ids":["1001","1002"]}'
```

## 输出处理

- `file.upload` 返回两种形态：`fileObj`（含 id/name/type/size，图片含宽高）与可直接嵌入消息的 img/file 对象。
- `file.download` 返回落地后的 `output`（可能因扩展名纠正与入参不同）、`size`，以及纠正时的 `renamedFrom`。
- 消息拉取里已经自带媒体 URL，一般不需要单独调 `file.preview`（仅当历史消息缺 URL 或要换规格时用）；要真正看到内容用 `file.download`。
- 下载的本地文件路径可直接用 Markdown 图片语法展示（如 `![a.png](绝对路径)`）。

## 失败处理

- 文件不存在/过大/类型不支持：按业务错误信息告知用户。
- 上传到一半网络中断：CLI 不会假装成功，重试需重新 upload（上传本身无副作用）。
- 下载失败（401/HTTP 非 200）：按错误信息告知用户先断开并重新连接本连接器完成登录；`output_exists` 时换路径，不覆盖既有文件。
- 只读/上传操作无确认链；认证失败参照共享规则。
