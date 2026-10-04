# Organization Shortcut 共享规则与索引

> 先阅读 [`../../ihr-shared/SKILL.md`](../../ihr-shared/SKILL.md)。本文件只描述多个 shortcut 共用的 Agent 规则和返回约定；具体参数、公开 JSON 字段和业务返回必须读取对应的命令 reference。

## 共享输入规则

1. `companyId`、`userId` 和权限范围来自登录态/session，不是公开输入，不能放进 flags 或 JSON。
2. `--json`/`--stdin` 与分项 flags 互斥；无参数命令明确不支持 JSON/stdin。JSON 模式使用与 flags 相同的公开字段名，别名以命令 reference 为准。
3. 分页命令的用户页码从 `1` 开始，每页条数默认值和上限写在命令自己的八列表中。Agent 不自动翻页；用户需要更多数据时重新确认范围和页码。
4. `criteria`、`orders` 只表示公开 JSON 条件/排序 carrier；必须是合法 JSON 数组或对象。不要把未公开对象、路径或服务端字段名带入输入。
5. 空值、重复 alias、类型错误和超出范围的值先在本地修正或报错；不要绕过 shortcut 直接调用后端、命令行 HTTP 工具或自写 HTTP client。

## Shortcut 返回约定

成功时共享 envelope 的稳定外层是：

```json
{
  "success": true,
  "command": "<result-command>",
  "request": {},
  "response": {}
}
```

失败时仍由共享运行时产生统一错误 envelope；退出码和 stdout/stderr 规则见各命令的“运行契约”。业务 `response` 的形状、数据路径、分页统计字段、稳定字段和 `PARTIAL` 边界只在命令 reference 中说明。raw code/ID 原样保留，输出前执行全局数据保护。

## CODE_TYPE、选项与主数据边界

- `CODE_TYPE` 是业务 code，不等于展示 label。固定值在命令 reference 的“枚举/格式/单位”列中列出；动态值只按协议值提交，需要按名称选择时先查询已公开的选项命令并做唯一匹配。
- 汇报关系树的动态选项固定通过 `staff +flexMetaValueList --code-value-id Enum.DirectManagerType --filter-disable` 获取；从 `response.data[]` 的 `displayName` 精确匹配到 `codeValue` 后，再调用 `organization +reportToTree`。无匹配停止，多匹配必须让用户确认，停用项不可使用。
- Interface Meta 可以记录其他动态选项的事实来源，但不自动替代 Agent 编排。找不到公开入口就按未提供处理，而不是调用未公开接口。
- 主数据类型和 ID 展示由 [`ihr-master-data`](../../ihr-master-data/SKILL.md) 统一处理：当前调用公共 shortcut 时先使用 canonical type，再 `+search` 做名称/编码到 ID 的唯一候选或消歧；格式化时按响应字段声明的类型去重，每种类型一次 `+batch-get`，使用 `displayName`/`code`，未命中保留 raw ID。公共 shortcut 只保证 canonical type，不要把 alias 当作可执行保证。
- Organization shortcut 不把 raw code/ID 改写成 label/name，不改变业务 `response` 的字段或顺序。主数据解析是调用方的补充步骤，不是 shortcut 的隐式副作用。

## 命令索引

| 命令 | 输入/结果摘要 | 独立契约 |
| --- | --- | --- |
| `organization +positions` | 职位筛选；`PAGE_RESULT` | [positions](ihr-organization-positions.md) |
| `organization +companySites` | 地点/地区筛选；`PAGE_RESULT` | [company sites](ihr-organization-company-sites.md) |
| `organization +orgTree` | 组织树筛选；`TREE` | [org tree](ihr-organization-org-tree.md) |
| `organization +costCenters` | 条件/排序筛选；`PAGE_RESULT` | [cost centers](ihr-organization-cost-centers.md) |
| `organization +costCenterGroups` | 无业务参数；`LIST` | [cost center groups](ihr-organization-cost-center-groups.md) |
| `organization +gradeLevels` | 职层条件；`LIST`（不承诺分页） | [grade levels](ihr-organization-grade-levels.md) |
| `organization +gradeLevelSortList` | 无业务参数；`LIST` | [grade-level sort list](ihr-organization-grade-level-sort-list.md) |
| `organization +gradeSequences` | 序列条件；`LIST`（不承诺分页） | [grade sequences](ihr-organization-grade-sequences.md) |
| `organization +gradeSequenceList` | 无业务参数；`LIST` | [grade-sequence list](ihr-organization-grade-sequence-list.md) |
| `organization +gradeSystems` | 体系条件；`LIST`（不承诺分页） | [grade systems](ihr-organization-grade-systems.md) |
| `organization +gradeSystemTree` | 职级树筛选；`TREE` | [grade-system tree](ihr-organization-grade-system-tree.md) |
| `organization +gradeSystemSetting` | 无业务参数；`OBJECT` | [grade-system setting](ihr-organization-grade-system-setting.md) |
| `organization +jobCategories` | 无业务参数；`LIST` | [job categories](ihr-organization-job-categories.md) |
| `organization +jobTitles` | 条件/排序筛选；`PAGE_RESULT` | [job titles](ihr-organization-job-titles.md) |
| `organization +positionGrades` | 职级分组条件；`LIST`（不承诺分页） | [position grades](ihr-organization-position-grades.md) |
| `organization +positionGradeList` | 可选序列 ID；`LIST` | [position-grade list](ihr-organization-position-grade-list.md) |
| `organization +reportToTree` | 员工与汇报类型；`TREE` | [report-to tree](ihr-organization-report-to-tree.md) |

## 不在本索引中的能力

编制 metadata command 的 schema 和逐命令公开契约见 [`ihr-organization-headcount.md`](ihr-organization-headcount.md)。未注册 metadata 和未公开接口均不在本 Skill 中虚构执行入口；汇报类型选项按上面的 Staff 公开命令解析。
