# 查看链接（查看详情）

## 什么时候读取

查询、新建、修改或动作流**已经成功**之后，需要给用户一个可点击的「查看详情」入口时读取本文件。

典型场景：资产列表、资产详情、领用记录、报修记录、采购申请列表、报修 / 归还的候选资产名，以及折旧计提任务。

## 链接形态

| 形态 | 路径模板 | 是否需要解析表单 ID |
| --- | --- | --- |
| 卡片链接 | `/sp/ebdfpage/card/0/{表单ID}/{数据ID}` | 需要，经两步 tag 接口实时解析 |
| 计提任务（viewport） | `/sp/ebdfpage/viewport/1267093228679077888?calc_month={计提年月}` | 不需要，固定页面 |

CLI 同时返回 `path`（去域名路径）和 `url`（用当前登录环境地址拼好的完整链接）。优先直接用 `url`；只有在需要自行拼接域名时才用 `path`。

## 场景与数据来源

| 场景（`scene`） | 表单标识（tag） | 数据 ID 来源 |
| --- | --- | --- |
| `asset_info` | `uf_asset_info` | 资产列表 / 详情每条记录的 `id`；新建返回 `dataIds`；报修·归还候选资产的 `id` |
| `asset_use` | `uf_asset_use` | 领用记录每条 `id`；领用申请动作流返回的 `lcID` |
| `asset_return` | `uf_asset_return` | 归还申请动作流返回的 `lcID` |
| `asset_repail` | `uf_asset_repail` | 报修记录每条 `id`；报修申请动作流返回的 `lcID` |
| `asset_purch_apply` | `uf_asset_purch_apply` | 采购申请记录每条 `id`；采购申请动作流返回的 `lcID` |
| `depre_task` | 无（viewport 固定页面） | 传 `calc_month`，取自本次计提操作 |

表单 ID 由「应用标签 → 表单标签」两步接口实时解析（`weaver-asset-eb` → 上表 tag），**不写死常量、不跨环境沿用**，同环境内会复用解析结果。

建单类动作流（领用 / 归还 / 报修 / 采购）的流程 ID 直接取自该次建单返回的 **`mainTable.lcID`**：`asset.use` / `return.create` / `repair.create` / `purch` 的成功返回都会把 `mainTable`（含 `lcID`、`lcbt`、以及各自的单号如 `ghbh`）透传到顶层，无需再翻嵌套结构。单号可能为回填中（空值），此时不要重试建单。

## 输入要点

字段以 `weaver-work-cli asset schema` 为准：

- `scene`：必填，取值见上表。
- `ids`：数据 ID 数组。**一律按字符串传入**（大整数，避免精度丢失）；一次可传多个，逐条生成各自链接。
- `calc_month`：仅 `depre_task` 场景需要，格式 `YYYY-MM`。
- `anchor`：可选，覆盖默认锚点文字「查看详情」。

## 示例

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json asset run asset.viewlink --input-json '{"scene":"asset_info","ids":["EXAMPLE_ASSET_ID","EXAMPLE_ASSET_ID_2"]}'
weaver-work-cli --profile eteams --json asset run asset.viewlink --input-json '{"scene":"asset_use","ids":["EXAMPLE_USE_ID"]}'
weaver-work-cli --profile eteams --json asset run asset.viewlink --input-json '{"scene":"depre_task","calc_month":"2026-08"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json asset run asset.viewlink --input-json '{"scene":"asset_info","ids":["EXAMPLE_ASSET_ID","EXAMPLE_ASSET_ID_2"]}'
weaver-work-cli --profile eteams --json asset run asset.viewlink --input-json '{"scene":"asset_use","ids":["EXAMPLE_USE_ID"]}'
weaver-work-cli --profile eteams --json asset run asset.viewlink --input-json '{"scene":"depre_task","calc_month":"2026-08"}'
```

## 返回

- `available` 为 `true` 时，`links` 数组按传入顺序给出每条记录的 `dataId`、`path`、`url`、`anchor`。
- `available` 为 `false`（状态 `VIEWLINK_UNAVAILABLE`）时 `links` 为空，`warnings` 说明「链接暂不可用」的原因。这**不是失败**，主操作已经成功，照常回报业务结果即可。

## 展示约定

- 以**对话内纯 Markdown 链接**呈现：`[查看详情](url)`。
- **锚点文字固定为「查看详情」**，严禁加「查看详情：」前缀与冒号，严禁把完整 URL 作为纯文本直接展示。
- 禁用 widget 内链接与旧版「蓝底白字胶囊按钮」样式。
- 多条记录**逐条生成各自的链接**，不要只给首条或共用一条。
- 报修 / 归还的**候选资产名**场景使用变体：锚点即资产名称本身，如 `[笔记本电脑](url)`，传 `anchor` 覆盖。
- 回报时只展示业务中文名称，不展示内部 key（`lcID`、`lcbt`、`lybh`、`ghbh`、`id` 等仅供拼链接使用）。
- 单据 / 流程编号尚未回填时，不输出空值行；如实说明「XX 单号生成中」。

## 注意

- **链接是附加信息**：主查询 / 新建 / 修改 / 动作流已经成功后，链接解析失败只如实说明「链接暂不可用」，**绝不因此重试主操作**——重试会重复查询、重复建单、重复改动数据。
- **不要臆造表单 ID / 数据 ID**：解析不到就不给链接，不允许用相近 ID 或历史 ID 拼一个可能打不开的链接。
- **大整数精度**：表单 ID 与数据 ID 均为长整型，全程按字符串处理。
- **数据 ID 只取本次结果**：每条记录的 ID 取自本次操作返回，不复用其他查询或上一单的 ID。
- 本链接不涉及附件、图片或文件解析，无需附件安全确认。
