# 查询日程列表 / 详情 / 总数

## 何时使用

查看日程列表、按关键字或时间范围找日程、查询单条日程详情、查询日程总数时使用。全部为只读操作，也作为更新/删除前的辅助查询。

## operation 清单

| operation | 用途 | 必填 |
| --- | --- | --- |
| `calendar.list` | 分页查询日程列表，支持时间范围与关键字筛选 | 无（全部可选） |
| `calendar.get` | 按日程数据 ID 查询单条完整信息 | `id` |
| `calendar.count` | 查询日程总数量 | 无 |

## 输入要点

- `calendar.list` 可选字段：`start_time`/`end_time`（`yyyy-MM-dd HH:mm`）、`keywork`（关键字，字段名拼写为 `keywork` 非 `keyword`）、`page_no`（默认 1）、`page_size`（默认 10）。
- `calendar.get` 必填 `id`：日程数据 ID，来自 `calendar.list` 返回的 `agenda[].id`。
- `calendar.count` 无入参。

## 命令

查询列表（Windows PowerShell）：

```powershell
weaver-work-cli --profile eteams --json calendar run calendar.list --input-json '{"page_no":1,"page_size":10}'
```

查询列表（macOS/Linux bash/zsh）：

```bash
printf '%s\n' '{"page_no":1,"page_size":10}' | weaver-work-cli --profile eteams --json calendar run calendar.list --input -
```

按关键字检索：

```powershell
weaver-work-cli --profile eteams --json calendar run calendar.list --input-json '{"keywork":"项目周会"}'
```

查询详情：

```powershell
weaver-work-cli --profile eteams --json calendar run calendar.get --input-json '{"id":"1304552516098269190"}'
```

查询总数：

```powershell
weaver-work-cli --profile eteams --json calendar run calendar.count --input-json '{}'
```

## 输出处理

- `calendar.list` 业务数据在 `data.actionData.responseData.customData.mainTable`，含 `count`（总数）、`pageNo`、`pageSize`、`hasNext`、`agenda[]`（列表）。`agenda[]` 元素含 `id`/`agn_name`/`participates`（姓名数组）/`start_time`/`end_time`/`agn_desc`/`location`。
- **`pageNo`/`pageSize` 仅为回显值**，可能与实际入参不一致（实测传入 `page_size=20` 却回显成 `pageNo:20 / pageSize:1`）。这是 ESB 响应回显层的**显示瑕疵**，**不影响实际分页与返回的 `count`/`agenda` 数据**。正确分页以实际入参的 `page_no`/`page_size` 为准，回显值忽略即可，**不当作接口 bug，也不要求修复**。
- `calendar.get` 业务数据在 `data.datajson.datas[0].mainTable`，含完整字段。ID 不存在时 `datas` 为空数组。
- `calendar.count` 业务数据在 `data.datajson.datas`（数字）。
- 选项类字段（`agn_type`/`priority`/`start_reminder`/`remind_type` 等）返回 `[{name,id}]` 数组，展示取 `name`，写入取 `id`。

## 注意

- `calendar.list` 返回的 `participates` 是参与人**姓名**数组，写入时需要人员 ID（交 weaver-e10-hrm-connector 解析）。
- 列表默认一页（1/10），`hasNext=true` 时提示用户是否翻页。
- 涉及附件、图片或文件内容解析时，必须先说明文件内容可能进入大模型上下文，获得用户明确确认后才继续。

## 已知回显瑕疵（忽略，不当作 bug）

- **现象**：`calendar.list` 响应中回显的 `pageNo`/`pageSize` 与实际入参不符（例如入参 `page_size=20`，回显成 `pageNo:20 / pageSize:1`）。
- **性质**：ESB 响应回显层的展示瑕疵，仅影响这两个回显字段的显示值，对实际分页行为、返回数据条数（`count`）与列表内容（`agenda`）无任何影响。
- **处置**：调用方与维护者**一律忽略**该回显值，以实际入参 `page_no`/`page_size` 为准；**不将其登记为缺陷、不要求后端修复、不在 CLI 层做规避**。

## 失败处理

- `id_invalid`：`calendar.get` 的 `id` 不是合法日程 ID。
- 结果为空：列表 `agenda` 为空数组、详情 `datas` 为空数组，向用户说明未查到，不视为接口失败。
- 返回 `business_error` 或 404：先运行 `calendar.app.check` 判断应用是否安装。
