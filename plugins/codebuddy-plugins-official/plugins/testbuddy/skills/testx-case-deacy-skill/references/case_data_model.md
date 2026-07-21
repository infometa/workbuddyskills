# Case数据模型参考

基于 `protocols/fc/testx/case/case.proto` 中的 Case message 定义和 `model/case.go` 中的 Case struct：

## 核心字段

| 字段               | Proto类型           | DB列                                   | 说明                   |
| ------------------ | ------------------- | -------------------------------------- | ---------------------- |
| `uid`              | `string`            | `uuid` (varchar 50)                    | 用例唯一标识，不可变   |
| `name`             | `string`            | `name` (varchar 255)                   | 用例名称               |
| `description`      | `string`            | `description` (longtext)               | 用例描述               |
| `priority`         | `Priority` (enum)   | `priority` (varchar 20)                | 优先级: P0/P1/P2/P3    |
| `pre_conditions`   | `string`            | `pre_conditions` (longtext)            | 前置条件               |
| `step_type`        | `StepType` (enum)   | `step_type` (char 10)                  | 步骤类型: STEP 或 TEXT |
| `steps`            | `repeated CaseStep` | `testcase_testcasestep` 表             | 结构化步骤列表         |
| `step_text`        | `CaseStep`          | `testcase_testcasesteptext` 表         | 文本描述步骤           |
| `owner`            | `string`            | `owner` (varchar 400)                  | 负责人                 |
| `labels`           | `repeated Label`    | `testcase_testcaselabel_case` 多对多表 | 标签                   |
| `folder_uid`       | `string`            | 通过 `parent_id` 关联                  | 所属目录               |
| `repo_version_uid` | `string`            | `case_repo_version_id`                 | 所属用例库版本         |
| `is_folder`        | `bool`              | `is_folder` (bool)                     | 是否为目录节点         |
| `review_state`     | `ReviewState`       | `status` (varchar 10)                  | 评审状态               |

## CaseStep 结构

| 字段              | 类型     | 说明                       |
| ----------------- | -------- | -------------------------- |
| `id`              | `string` | 步骤ID                     |
| `content`         | `string` | 步骤描述                   |
| `expected_result` | `string` | 预期结果                   |
| `nid`             | `string` | 步骤编号（用于自动化绑定） |

## 关键约束

1. **用例名称**：varchar(255)，不为空，同一目录下不可重名
2. **UUID**：全局唯一，创建后不可变，用于跨版本追踪
3. **软删除**：使用 `is_delete` 标记删除（soft_delete:flag），删除后可从回收站恢复
4. **树形结构**：通过 `parent_id`、`level`、`path` 维护 PET (Path Enumeration Tree) 结构
5. **扩展字段**：`CaseExtensions` 记录执行次数 `run_times`、关联缺陷数 `bug_count`
