# 通用辅助（general-helpers）

## 何时使用

用户表达辅助解析意图：按名称查事项 ID、按姓名查人员 ID、查询当前人员信息、校验事项权限、查询企业工商照面、按字段 ID 获取字段信息、自定义浏览字段选项查询。

## 可用 operation

| Operation | 风险 | 输入要点 |
|---|---|---|
| `jiuchuanhui.entity.id.by-name` | 只读 | `mainTable`: `{moduleType, name}` |
| `jiuchuanhui.user.id.by-name` | 只读 | `mainTable.employeeName` |
| `jiuchuanhui.user.current-profile` | 只读 | 无入参；每轮会话优先取一次并复用 |
| `jiuchuanhui.entity.permission.judge` | 只读 | `mainTable`: `{moduleType, entityId, opType}` |
| `jiuchuanhui.company.business-profile.query` | 只读 | `mainTable.companyName` |
| `jiuchuanhui.field.info.by-ids` | 只读 | `mainTable.fieldids` |
| `jiuchuanhui.browser-option.search` | 只读 | `pathParams.customBrowserType` 必填，`params.searchValue` 可选 |

## 输入要点

- `moduleType`：事项模块类型，必须精确匹配：`customer`（客户）/`saleChance`（商机）/`clue`（线索）/`administrativeDivision`（行政区域）；`name` 为事项名称（必填）。传错值会静默返回“未查询到相关事项”。
- 行政区划也走按名称查事项 ID：`moduleType: "administrativeDivision"`、`name` 传城市名；返回全路径 ID，可写缓存。
- `browser-option.search` 是 RelateBrowser 字段的选项查询入口：用 `customBrowserType` 指定浏览类型，返回自定义浏览选项供选择。需已知 `customBrowserType`（自定义浏览类型标识），通过「通过字段id获取字段信息」接口（`jiuchuanhui.field.info.by-ids`）获取 RelateBrowser 字段定义中的 `browser_type` 作为 `customBrowserType`。 常见类型：`customBrowser_industrybrowser`（行业）。
- 选项字段（Select/RadioBox/CheckBox）传 ID；`RelateBrowser` 字段通过 `browser-option.search` 查询对应类型选项。

## 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.user.id.by-name --input-json '{"mainTable":{"employeeName":"魏思雨"}}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.entity.id.by-name --input-json '{"mainTable":{"moduleType":"customer","name":"示例科技有限公司"}}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.user.current-profile --input-json '{}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.browser-option.search --input-json '{"pathParams":{"customBrowserType":"customBrowser_industrybrowser"},"params":{"searchValue":"科技"}}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.user.id.by-name --input-json '{"mainTable":{"employeeName":"魏思雨"}}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.entity.id.by-name --input-json '{"mainTable":{"moduleType":"customer","name":"示例科技有限公司"}}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.user.current-profile --input-json '{}'
weaver-work-cli --profile eteams --json jiuchuanhui run jiuchuanhui.browser-option.search --input-json '{"pathParams":{"customBrowserType":"customBrowser_industrybrowser"},"params":{"searchValue":"科技"}}'
```

## 输出处理

- `user.id.by-name` / `entity.id.by-name` 返回业务 ID，供后续写操作或关联使用。
- `user.current-profile` 返回当前人员 ID，可作为默认 `manager`/负责人/操作人。

## 注意

- 查询无结果时说明实际条件并停止，不得放宽条件猜测重试。
- `entity.permission.judge` 的 `moduleType` 仅确认支持 `customer`（转移）与 `contactPlan`（联系记录）；是否支持 `saleChance`/`clue` 等其它类型须以动作流实际返回为准，返回不支持/校验失败时应如实反馈用户，不得臆造支持范围。
- `field.info.by-ids` 的 `fieldids` 传字段 ID（逗号分隔多个）。

## 失败处理

- 参数缺失/不支持：说明具体问题并停止。
