# 发现与配置（discovery-config）

## 何时使用

用户表达缓存/配置相关意图：初始化或刷新九氚汇配置缓存、应用发现、表单发现、字段发现、字段选项、接口配置详情、接口标识转配置 ID、文件预览。

## 可用 operation

| Operation | 风险 | 输入要点                                                                                                                                                   |
|---|---|--------------------------------------------------------------------------------------------------------------------------------------------------------|
| `jiuchuanhui.app.discovery` | 只读 | `tag`（默认 `jch-crm-project`）                                                                                                                            |
| `jiuchuanhui.form.discovery` | 只读 | `tag`、`appId`                                                                                                                                          |
| `jiuchuanhui.field.options` | 只读 | `fieldName`（必填,传入字段ID）、`sourceType`（必填，值为 `FORM`）；可选 `objId`（不传默认按 `uf_jch_customer` 表单发现）、`groupId`（可省略自动发现，来自 `app.discovery` tag=`jch-crm-project`） |
| `jiuchuanhui.rest.cfg.detail` | 只读 | `apid`、`id`（cfgId）                                                                                                                                     |
| `jiuchuanhui.config.id.by.pk` | 只读 | `mainTable.interface_pk`                                                                                                                               |
| `jiuchuanhui.file.preview` | 只读（文件预览） | `fileId` 必填，可选 `fieldId`/`appId`/`customParam`                                                                                                         |
| `jiuchuanhui.get-rest-cfg-detail` | 只读 | `apid`、`id`（cfgId）                                                                                                                                     |

## 输入要点

- 九氚汇配置缓存放 `~/.weaver-e10-jiuchuanhui-connector/{tenantKey}/{userId}/`：主缓存 `weaver-e10-jiuchuanhui-connector.json`（`discovery`/`ebuilder`/`options`/`region`），接口配置 `config/{pk}.json`。
- 创建/更新类接口读 `config/{pk}.json.detail` 的 `mainFields`/`detailFields`；搜索类读 `searchParams`；选项字段优先读字段 `optionList`。
- 缓存缺失或用户要求刷新时，调用 CLI operation `jiuchuanhui.cache.init`（应用发现 -> objId -> 版本校验 >= 1.5.11 -> cfgId -> 接口配置 -> 关联数据 -> 字段选项 -> 搜索参数 -> 行政区划），再继续业务调用。缓存初始化和刷新**已暴露为 CLI operation `jiuchuanhui.cache.init`**（risk: local-file-write，无需 prepare/apply 确认链）；也可在仓库根运行 `node src/shortcuts/jiuchuanhui/scripts/cache-init.mjs`（薄包装）。
- 文件预览：`fileId` 为必填；涉及本地文件/远程 URL 解析时先提醒用户文件内容可能进入大模型上下文或发送到文件服务。
- `file.preview` 返回的 `loadUrl`/`previewLink` 带临时签名（约 7 天），过期需重新调用获取，不要硬编码或长期缓存下载地址；附件 ID 从表单数据字段获取，字段无附件时返回空数组，无需调用本接口。
- `jiuchuanhui.field.options`参数fieldName传入的是字段的id
## 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.app.discovery --input-json '{"tag":"jch-crm-project"}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.form.discovery --input-json '{"tag":"uf_jch_customer","appId":"APP_ID"}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.field.options --input-json '{"fieldName":"FIELD_ID","sourceType":"FORM","objId":"OBJ_ID","groupId":"APP_ID"}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.file.preview --input-json '{"fileId":"FILE_ID"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.app.discovery --input-json '{"tag":"jch-crm-project"}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.form.discovery --input-json '{"tag":"uf_jch_customer","appId":"APP_ID"}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.field.options --input-json '{"fieldName":"FIELD_ID","sourceType":"FORM","objId":"OBJ_ID","groupId":"APP_ID"}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.file.preview --input-json '{"fileId":"FILE_ID"}'
```

## 输出处理

- `app.discovery` 返回 `data[0].appId`；`form.discovery` 优先取 `formId` 非空且非 `"0"` 的记录 `id` 为 `objId`；`field.options` 返回选项数组 `{lable, lableTitle, value}`。

## 注意

- 选项字段必须先取选项 ID 再传值（Select/RadioBox/CheckBox 传 `value`，不传 `lable` 中文名）。
- `field.options` 的 `fieldName` 参数实际传字段元数据 ID（fieldid，纯数字），**不是** `data_key` 名称。传错会返回空数组。
- `rest.cfg.detail` 与 `get-rest-cfg-detail` 都用于读取接口配置详情，Agent 按上下文选一个即可，不需要两个都调。

## 失败处理

- 版本校验 < `1.5.11`：停止业务调用并告知用户。
- 缓存缺失：先执行初始化/单项刷新，再重试业务调用。
