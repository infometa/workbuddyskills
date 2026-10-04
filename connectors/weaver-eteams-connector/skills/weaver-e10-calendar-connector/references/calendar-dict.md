# 查询日程类型 / 紧急程度（字典）

## 何时使用

创建或更新日程前，需要确认 `agn_type`（日程类型）或 `priority`（紧急程度）的可选值、拿选项 ID 时使用。全部为只读操作。

## operation 清单

| operation | 用途 | 必填 |
| --- | --- | --- |
| `calendar.type.list` | 查询日程类型选项列表（`agn_type` 可选值） | 无 |
| `calendar.priority.list` | 查询日程紧急程度选项列表（`priority` 可选值） | 无 |

## 输入要点

- 可选 `type_name` / `priority_name`：按名称筛选。**不可传空字符串**（会返回空列表），查询全部时省略此字段。
- 可选 `pageNo`（默认 1）、`pageSize`（默认 10）。

## 命令

查询全部类型（Windows PowerShell）：

```powershell
weaver-work-cli --profile eteams --json calendar run calendar.type.list --input-json '{}'
```

查询全部类型（macOS/Linux bash/zsh）：

```bash
printf '%s\n' '{}' | weaver-work-cli --profile eteams --json calendar run calendar.type.list --input -
```

查询全部紧急程度：

```powershell
weaver-work-cli --profile eteams --json calendar run calendar.priority.list --input-json '{}'
```

## 输出处理

- 业务数据在 `data.datajson.datas[]`，每个元素是 `mainTable`。
- 类型 `mainTable` 含 `id`/`type_name`/`type_code`/`is_enable`/`is_default`/`type_desc`。
- 紧急程度 `mainTable` 含 `id`/`priority_name`/`is_enable`/`default_priority`。
- **写入时 `agn_type` / `priority` 传返回的 `id`**；`type_code` 仅供展示，不可作为选项值传入。

## 注意

- `is_enable="0"` 的选项已禁用，通常不用于新建日程。
- `is_default="1"` / `default_priority="1"` 为系统默认项。
- 选项列表可会话内缓存复用，无需每次写操作前重复查询。

## 失败处理

- `enum_invalid`：筛选名或分页参数非法。
- 返回空列表：确认没有传空字符串筛选名。
