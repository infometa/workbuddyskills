---
name: testx-case-deacy-skill
description: 使用脚本和mcp工具获取智研-测试堂-测试用例-指定目录下的测试用例，并按用户给出的整改约束条件，调整用例，最终解决对测试用例资产的用例腐化。
1. 必须给出测试用例的目录链接;
2. 必须给出测试用例的整改约束条件，例如：某个iwiki链接、某个tapd链接、一段文本等;
3. 调整用例归属或目录结构时，优先使用move工具移动用例到目标目录，非必要不使用create和delete;
4. 获取数据时同时获取目录（FOLDER），通过folder_uid维护目录-用例映射关系，用例调整后同步维护目录（清理空目录）;
5. 调整完成后必须先生成可视化HTML确认报告供用户审批，获取用户确认后才能执行实际操作;
---

# 测试堂用例腐化处理

本 skill 基于智研-测试堂-测试用例-指定目录下的用例，结合用户给出的整改约束条件，调整用例，最终解决对测试用例资产的用例腐化。

## 引用文档

| 文件                              | 说明                                             |
| --------------------------------- | ------------------------------------------------ |
| `references/case_data_model.md`   | Case 数据模型、字段定义、关键约束                |
| `references/script_usage.md`      | 五个脚本工具的参数与用法                         |
| `references/diagnosis_rules.md`   | 腐化检测维度、严重度分级、相似用例检测与合并规则 |
| `references/execution_steps.md`   | 第七步执行操作、第八步结果验证的详细说明         |
| `references/report_template.html` | 第六步 HTML 可视化确认报告模板                   |

## 前置准备

### 智研个人access_token获取

从上下文中获取，如果没有，则引导用户进入智研测试堂访问控制（https://zhiyan.woa.com/permission/#/access-token/private），点击个人账号，创建或复制已有token，输入到上下文中

### 脚本工具

本 skill 提供五个脚本工具，位于 `scripts/` 目录下：

| 脚本                      | 用途                                          |
| ------------------------- | --------------------------------------------- |
| `scripts/search_cases.py` | 批量获取用例和目录（支持分页）                |
| `scripts/update_cases.py` | 批量更新用例（PatchCase）                     |
| `scripts/move_cases.py`   | 批量移动用例到指定目录                        |
| `scripts/delete_cases.py` | 批量删除用例/目录（非空检查+降级重命名+分批） |
| `scripts/rename_cases.py` | 批量重命名目录/用例                           |

> 详细参数请参考 `references/script_usage.md`

---

## 完整用例防腐流程

### 第一步：解析用例目录信息

从链接中解析四个关键参数：

```
https://zhiyan.woa.com/testx/{$namespace}/cases/#/testx/.../repos/{$repo_uid}/vers/{$repo_version_uid}/folders/{$folder_uid}/in-page
```

- `namespace`：项目命名空间（number类型）
- `repo_uid`：用例库UID
- `repo_version_uid`：用例库版本UID
- `folder_uid`：目录UID

### 第二步：批量获取原始数据（用例 + 目录）

使用 `scripts/search_cases.py` 获取指定目录下的所有数据。支持两种模式：

#### 2.0 FLAT模式（默认，用于诊断分析）

获取平铺列表，包含用例和目录节点：

```shell
python scripts/search_cases.py \
  --namespace <namespace> \
  --repo-uid <repo_uid> \
  --repo-version-uid <repo_version_uid> \
  --folder-uid <folder_uid> \
  --token <access_token> \
  --output .testbuddy/case-decay/original_cases.json
```

**或者**使用`testx-MCP-Server`mcp工具`search_cases`获取。

#### 2.1 TREE模式（用于HTML报告树结构）

获取服务端组装的树形结构，用于生成 HTML 报告中的正确目录树：

```shell
python scripts/search_cases.py \
  --namespace <namespace> \
  --repo-uid <repo_uid> \
  --repo-version-uid <repo_version_uid> \
  --folder-uid <folder_uid> \
  --token <access_token> \
  --show-mode TREE \
  --output .testbuddy/case-decay/original_tree.json
```

> **原理**：`--show-mode TREE` 会使用 SearchCases API 的 `ShowMode=TREE` + `IncludeAncestors=true`，
> 服务端通过 `ComposeItems()` 直接构建嵌套树结构（参考 `case.go → SearchCases()`），
> 返回的每个 Folder 包含 `Folders`（子目录）和 `Cases`（子用例），确保树结构正确。

TREE模式返回格式：

```json
{
  "status": "success",
  "tree": {
    "uid": "folder_uid",
    "name": "目录名",
    "type": "folder",
    "children": [
      { "uid": "...", "name": "子目录", "type": "folder", "children": [...] },
      { "uid": "...", "name": "用例名", "type": "case", "description": "...", "steps": [...], ... }
    ]
  },
  "flat_cases": [...]
}
```

#### 2.2 构建目录-用例映射（仅FLAT模式需要）

根据每条记录的 `item_type` 和 `folder_uid` 字段，构建**目录-用例映射表**：

```
folder_uid_A/（FOLDER）
├── case_uid_1（CASE）
├── case_uid_2（CASE）
└── folder_uid_B/（FOLDER）
    └── case_uid_3（CASE）
```

> **推荐**：HTML报告生成时优先使用 TREE 模式获取树结构，避免客户端自行拼接导致的树结构不正确问题。

### 第三步：获取用例防腐约束条件

1. 从上下文中获取`测试用例的整改约束条件`（iwiki链接、tapd链接、一段文本等），如果没有，则提示用户输入
2. 如果用户输入链接，则调用对应mcp工具获取链接内容作为约束条件

### 第四步：用例腐化诊断

结合 Case 模型结构（见 `references/case_data_model.md`），对每个用例进行腐化诊断。

> 详细的检测维度、严重度分级请参考 `references/diagnosis_rules.md`

### 第五步：相似用例检测与合并

> 详细的相似度计算、合并规则请参考 `references/diagnosis_rules.md`

### 第六步：生成可视化 HTML 确认报告

完成诊断和合并分析后，**生成一个可交互的 HTML 文件**作为确认报告，供用户审批。

#### 6.0 获取树结构数据

使用 `scripts/search_cases.py --show-mode TREE` 获取服务端组装的正确树形结构，作为 HTML 报告的目录树基础：

```shell
python scripts/search_cases.py \
  --namespace <namespace> \
  --repo-uid <repo_uid> \
  --repo-version-uid <repo_version_uid> \
  --folder-uid <folder_uid> \
  --token <access_token> \
  --show-mode TREE \
  --output .testbuddy/case-decay/original_tree.json
```

> **重要**：HTML 报告中的树结构必须基于 TREE 模式返回的数据构建，而非客户端通过 folder_uid 自行拼接。
> 这确保目录层级和排序与智研测试堂前端完全一致。

#### 6.1 空目录检测

遍历目录-用例映射表，模拟执行所有移动和删除操作后，检查哪些目录变为空目录：

- 如果某目录下的所有用例都被移动或删除，该目录标记为「待清理」
- 空目录需用户确认后才执行删除

#### 6.2 生成 HTML 确认报告

读取 `references/report_template.html` 模板，将分析结果填充到 `REPORT_DATA` 变量中，生成 `.testbuddy/case-decay/report.html` 文件。

**REPORT_DATA 数据结构**：

```json
{
  "meta": {
    "generated_at": "生成时间",
    "folder_path": "/根目录路径",
    "namespace": "项目namespace",
    "repo_uid": "用例库UID",
    "repo_version_uid": "版本UID",
    "folder_uid": "目录UID"
  },
  "stats": {
    "add":    { "folders": 0, "cases": 0 },
    "rename": { "folders": 0, "cases": 0 },
    "update": { "folders": 0, "cases": 0 },
    "move":   { "folders": 0, "cases": 0 },
    "delete": { "folders": 0, "cases": 0 },
    "merge":  { "folders": 0, "cases": 0 }
  },
  "tree": { ... }
}
```

**tree 节点结构**：

```json
{
  "uid": "节点UID",
  "name": "节点名称",
  "type": "folder 或 case",
  "operation": "none|add|rename|update|move|delete|merge",
  "reason": "操作原因",
  "extra": {
    "old_name": "（重命名时）原名称",
    "from_folder": "（移动时）来源目录名",
    "to_folder": "（移动时）目标目录名",
    "merged_with": [{"uid": "用例UID", "name": "用例名称"}],
    "child_handling": "（删除目录时）子节点处理说明"
  },
  "detail": {
    "priority": "P0|P1|P2|P3",
    "description": "用例描述",
    "pre_conditions": "前置条件",
    "step_type": "STEP 或 TEXT",
    "steps": [
      { "id": "步骤ID", "content": "步骤描述", "expected_result": "预期结果" }
    ],
    "step_text": { "content": "文本步骤内容", "expected_result": "文本预期结果" },
    "folder_path": "所在目录路径（面包屑格式，用 / 分隔）"
  },
  "changes": {
    "name":           { "old": "原名称", "new": "新名称" },
    "priority":       { "old": "P2",     "new": "P1" },
    "description":    { "old": "原描述", "new": "新描述" },
    "pre_conditions": { "old": "原前置", "new": "新前置" },
    "steps":          { "old": [{"content":"...", "expected_result":"..."}], "new": [{"content":"...", "expected_result":"..."}] },
    "folder_path":    { "old": "根目录 / 旧父目录", "new": "根目录 / 新父目录" }
  },
  "children": [ ... ]
}
```

**operation 取值说明**：

| operation | 含义                                                                                                                                    | extra 中的额外信息                                                |
| --------- | --------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| `none`    | 无变化                                                                                                                                  | -                                                                 |
| `add`     | 新增                                                                                                                                    | `reason`: 新增原因                                                |
| `rename`  | 重命名                                                                                                                                  | `old_name`: 原名称                                                |
| `update`  | 更新内容                                                                                                                                | `reason`: 更新原因（如补全步骤/描述）                             |
| `move`    | 移动（移动目录时统一按 `update` 处理：operation 设为 `update`，extra 中附带 `from_folder`、`to_folder`，stats 中计入 update 而非 move） | `from_folder`, `to_folder`                                        |
| `delete`  | 删除                                                                                                                                    | `reason`: 删除原因；目录还需 `child_handling`                     |
| `merge`   | 合并                                                                                                                                    | `merged_with`: 被合并的用例对象列表，每个对象包含 `uid` 和 `name` |

**detail 字段（仅 type=case 时填充）**：

| 字段             | 类型     | 说明                                                                              |
| ---------------- | -------- | --------------------------------------------------------------------------------- |
| `priority`       | `string` | 用例优先级：P0/P1/P2/P3                                                           |
| `description`    | `string` | 用例描述（当前值）                                                                |
| `pre_conditions` | `string` | 前置条件（当前值）                                                                |
| `step_type`      | `string` | 步骤类型：STEP（结构化步骤）或 TEXT（文本步骤）                                   |
| `steps`          | `array`  | 结构化步骤列表，每项含 `id`、`content`（步骤描述）、`expected_result`（预期结果） |
| `step_text`      | `object` | 文本步骤，含 `content`（步骤内容）和 `expected_result`（预期结果）                |
| `folder_path`    | `string` | 所在目录路径，面包屑格式，用 `/` 分隔                                             |

> **注意**：`detail` 中的字段值应为**当前最终值**（即应用操作后的值）。若有 `update`/`rename` 操作，`detail` 填写调整后的新值。

**changes 字段（仅有字段变更时填充）**：

| 字段             | 类型                       | 说明                                                       |
| ---------------- | -------------------------- | ---------------------------------------------------------- |
| `name`           | `{old, new}`               | 名称变更（rename 操作时）                                  |
| `priority`       | `{old, new}`               | 优先级变更                                                 |
| `description`    | `{old, new}`               | 描述变更                                                   |
| `pre_conditions` | `{old, new}`               | 前置条件变更                                               |
| `steps`          | `{old: [...], new: [...]}` | 步骤变更，old/new 各为步骤数组                             |
| `folder_path`    | `{old, new}`               | 所在目录变更（移动用例时），old/new 为面包屑格式的目录路径 |

> **注意**：`changes` 中只包含**实际发生变更的字段**，未变更的字段不需填入。在 HTML 报告中，有 `changes` 的字段会以**内联变更**方式展示修改前后的对比：
>
> - **名称**：原名称删除线+灰化，新名称在下方绿色高亮框中展示，变更部分用黄色标记
> - **描述**、**前置条件**等文本字段：原值删除线+灰化，新值在下方绿色边框块中展示，变更部分用黄色高亮标记（基于字符级 LCS diff）
> - **步骤**字段：变更/删除的原步骤行删除线+灰化，紧接其下展示变更后的步骤行（绿色背景），序号列带"修改"/"新增"标签，步骤内容用 diff 高亮标记变更部分
> - **优先级**：原优先级删除线+灰化，箭头 → 新优先级（绿色外框高亮）
> - **目录移动**：原目录删除线+灰化（带"原目录"红色标签），新目录紫色醒目高亮边框（带"📦 新目录"标签）

#### 6.3 生成报告文件

1. 读取 `references/report-template.html` 模板内容
2. 将 `__REPORT_DATA_PLACEHOLDER__` 替换为实际的 JSON 数据
3. 写入 `.testbuddy/case-decay/report.html`
4. 使用 `preview_url` 工具在 IDE 中打开预览

#### 6.4 同时生成操作数据文件

将详细的操作数据写入 JSON 文件供第七步执行使用：

- `.testbuddy/case-decay/move_cases.json` — 待移动用例列表
- `.testbuddy/case-decay/update_cases.json` — 待更新用例列表
- `.testbuddy/case-decay/delete_cases.json` — 待删除用例UID列表
- `.testbuddy/case-decay/rename_folders.json` — 待重命名目录列表
- `.testbuddy/case-decay/delete_folders.json` — 待清理空目录UID列表
- `.testbuddy/case-decay/merge_cases.json` — 待合并用例组列表

> **【重要】操作数据文件生成规则**：
>
> 1. **update_cases.json**：**只包含 `operation=update` 或 `operation=merge`（保留用例）的用例**，不包含 `operation=none` 的用例。
>    - 每个用例对象**只包含 `uid` + 需要变更的字段**（如 `description`、`steps`、`pre_conditions`），不需要变更的字段（如 `name`）不要包含。
>    - 脚本会自动 GET 原始数据并 merge，确保不会覆盖未指定的字段。
>    - 示例：`[{"uid": "123", "description": "新描述"}]`（只更新描述，名称等字段保持不变）
> 2. **delete_cases.json**：**只包含 `operation=delete` 的用例 UID**，不包含其他操作类型的用例。
>    - 格式为 UID 字符串数组：`["uid1", "uid2"]`
> 3. **merge_cases.json**：合并组列表，每组包含 `target_uid`（保留用例）、`delete_uids`（待删除的重复用例）和 `merged_data`（合并后的数据）。
>    - `merged_data` 中**只包含相对于原 target 用例有变更的字段**。

**输出提示**：`请在 HTML 报告中确认调整方案，回复「确认执行」后开始操作。`

### 第七步：用户确认与执行

> **必须等待用户确认后才能执行**。详细执行步骤参考 `references/execution_steps.md`

执行顺序：**先移动 → 再更新 → 删除用例 → 重命名目录 → 清理空目录**

### 第八步：结果验证与执行报告

> 详细验证步骤参考 `references/execution_steps.md`

重新获取数据验证，输出最终执行报告。
