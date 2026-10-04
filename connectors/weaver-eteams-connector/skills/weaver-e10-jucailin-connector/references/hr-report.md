# 人事报表查询

## 何时使用

查询部门/岗位/职务/职类人数、流失离职人数、占编人员明细、人员流动明细、人员属性合计时使用。全部为只读操作。

与[数据源查询](hr-datasource.md)的区别：这些报表有各自独立的接口路径和参数结构，不用 `formId` + `queryDto` 的形式。

## 输入要点

| operation | 必填 | 说明 |
| --- | --- | --- |
| `ehr.hr.report.dept.table` | 无 | 部门人数，按人数从大到小 |
| `ehr.hr.report.posi.table` | 无 | 岗位人数 |
| `ehr.hr.report.job.table` | 无 | 职务人数，需「职务人员统计」权限 |
| `ehr.hr.report.jobtype.table` | 无 | 职务类别人数 |
| `ehr.hr.report.change.dept.table` | `type` | 流失/离职/解聘/退休人数，`type` 取 `loss`/`dismiss`/`quit`/`retire` |
| `ehr.hr.est.emp.table` | `cfgId`,`dataType`,`month` | 组织编制占编人员明细 |
| `ehr.hr.est.dc.emp.table` | `id`,`cfgId`,`dataType`,`month` | 控编维度占编人员明细 |
| `ehr.hr.turn.emp.table` | `startDate`,`endDate`,`dataType` | 人员流动明细名单 |
| `ehr.hr.props.sa` | 无 | 人员属性合计的高级搜索条件定义 |
| `ehr.hr.props.table` | 无 | 人员属性合计报表 |

前四个报表共用人员范围过滤：`hiredate`、`location`、`personnelStatus`、`subcompany`、`department`。**名称筛选字段名各不相同**：部门用 `departmentName`，岗位用 `positionName`，职务用 `jobName`，职务类别用 `jobTypeName`。

`ehr.hr.report.change.dept.table` 只有 `changeDate`/`subcompany`/`department`，**没有** `personnelStatus`、`hiredate`、`location`。

## 命令

部门人数：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json ehr run ehr.hr.report.dept.table --input-json '{"departmentName":"研发"}'
```

macOS/Linux（bash/zsh）：

```bash
printf '%s\n' '{"departmentName":"研发"}' | weaver-work-cli --profile eteams --json ehr run ehr.hr.report.dept.table --input -
```

人员流动明细：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json ehr run ehr.hr.turn.emp.table --input-json '{"startDate":"2026-01-01","endDate":"2026-03-31","dataType":"join_emp_count"}'
```

macOS/Linux（bash/zsh）：

```bash
printf '%s\n' '{"startDate":"2026-01-01","endDate":"2026-03-31","dataType":"join_emp_count"}' | weaver-work-cli --profile eteams --json ehr run ehr.hr.turn.emp.table --input -
```

## 输出处理

- 分页信息在 `meta.page`。`dept.table`、`posi.table`、`job.table`、`jobtype.table` 的 `pageSize` 被页面配置固定为 100，全量数据必须递增 `current` 翻页。
- `props.table` 的 `calcLevel` 缺省按 `department`；`total` 与 `department` 粒度相同，`subcompany` 按分部聚合。

## 注意

- **占编人员查询的 ID 必须先解析**：`est.emp.table` 的 `cfgId`、`est.dc.emp.table` 的 `id` 与 `cfgId`，都必须先从对应数据源（`estCalc=754217732232708751`、`estDcCalc=754217732232709056`）的记录中取得，禁止编造或使用默认值。
- `turn.emp.table` 的 `dataType` 决定名单口径：`begin_emp_count` 是**起始日前一天**在职人数，`end_emp_count` 是期末，`join_emp_count` 入职，`dismiss_emp_count` 离职，`org_in_emp_count` 调入，`org_out_emp_count` 调出。
- `job.table` 需要「职务人员统计」查看权限，无权限时返回业务失败，不要反复重试。
- 报表含组织与人员统计信息，回复用户时给结论与关键数字，不要原样粘贴完整表格 JSON。
- 涉及附件、图片或文件内容解析时，必须先说明文件内容可能进入大模型上下文，获得用户**明确确认**后才继续。

## 失败处理

- `est_dc_id_required` / `cfg_id_required`：占编查询缺少必需 ID，请先从数据源取记录。
- `date_range_invalid`：`turn.emp.table` 的 `startDate` 晚于 `endDate`。
- `enum_invalid`：`type`、`dataType`、`calcLevel` 取值不在允许集合内。
- 权限不足返回业务失败，先确认账号是否具备对应报表的查看权限。
