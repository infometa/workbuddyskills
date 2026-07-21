# 脚本工具使用说明

所有脚本位于 `scripts/` 目录下，共用参数：`--namespace`、`--repo-uid`、`--repo-version-uid`、`--token`。

## search_cases.py — 批量获取用例

### FLAT模式（默认）

```shell
python scripts/search_cases.py \
  --namespace <ns> --repo-uid <repo> --repo-version-uid <ver> \
  --folder-uid <folder> --token <token> \
  --output .testbuddy/case-decay/original_cases.json
```

- 自动分页获取全部数据（默认每页100条）
- 默认同时返回 CASE 和 FOLDER；可通过 `--item-type CASE/FOLDER` 过滤
- 返回字段：`uid`, `name`, `item_type`, `description`, `pre_conditions`, `priority`, `step_type`, `steps`, `folder_uid`, `full_path`

### TREE模式（用于HTML报告树结构）

```shell
python scripts/search_cases.py \
  --namespace <ns> --repo-uid <repo> --repo-version-uid <ver> \
  --folder-uid <folder> --token <token> \
  --show-mode TREE \
  --output .testbuddy/case-decay/original_tree.json
```

- 使用 SearchCases API 的 `ShowMode=TREE` + `IncludeAncestors=true`
- 服务端通过 `ComposeItems()` 构建正确的嵌套树结构
- 返回结构：`tree`（嵌套节点，含 `children`）+ `flat_cases`（兼容平铺列表）
- 每个 folder 节点包含 `children`（子目录 + 子用例），用例节点包含完整步骤字段
- **推荐用于 HTML 报告生成**，确保目录树层级和排序与测试堂前端一致

## move_cases.py — 批量移动用例（优先使用）

```shell
python scripts/move_cases.py \
  --namespace <ns> --repo-uid <repo> --repo-version-uid <ver> \
  --target-uid <target_folder> --token <token> \
  --uids uid1,uid2,uid3 [--input file.json] [--dry-run]
```

- 使用 BatchMoveCases 接口，超过50自动分批

## delete_cases.py — 批量删除用例/目录

```shell
python scripts/delete_cases.py \
  --namespace <ns> --repo-uid <repo> --repo-version-uid <ver> \
  --token <token> --uids uid1,uid2 [--input file.json] [--dry-run] \
  [--check-empty] [--fallback-rename]
```

- `--check-empty`：删除前检查目录是否为空
- `--fallback-rename`：删除失败时降级为重命名（添加 `[空-待删除]` 前缀）
- **输入文件中只包含确定要删除的用例/目录 UID**，不要包含不需要删除的项
- 输入格式支持 UID 字符串数组 `["uid1", "uid2"]` 或对象数组 `[{"uid": "xxx", "name": "yyy"}]`

## update_cases.py — 批量更新用例

```shell
python scripts/update_cases.py \
  --namespace <ns> --repo-uid <repo> --repo-version-uid <ver> \
  --token <token> --input update_list.json [--dry-run]
```

- 采用 **read-merge-write** 策略：更新前自动 GET 原始用例数据，将输入字段 merge 到原始数据上再调用 PatchCase
- 输入文件中**只需包含 `uid` + 需要变更的字段**，未指定的字段会自动保持原值不变
- 避免 PatchCase REST API 全量更新覆盖未传入字段的问题
- 每个用例需要 2 次 API 调用（GET + PATCH），处理速度约为单次调用的一半

**输入格式**：

```json
[
  { "uid": "123", "description": "新描述" },
  {
    "uid": "456",
    "steps": [{ "content": "步骤1", "expected_result": "预期1" }]
  }
]
```

> **注意**：只传需要变更的字段。不需要变更的字段（如 name）不要包含在输入中。

## rename_cases.py — 批量重命名目录/用例

```shell
python scripts/rename_cases.py \
  --namespace <ns> --repo-uid <repo> --repo-version-uid <ver> \
  --token <token> --input rename_list.json [--dry-run]
```

- 输入文件格式：`[{"uid": "xxx", "new_name": "新名称"}]`
- 目录使用 UpdateFolder 接口，用例使用 PatchCase 接口，脚本自动选择
