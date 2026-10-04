# 资产折旧计提

## 什么时候读取

用户要执行某月资产折旧计提时读取本文件。

## Operation

`asset.depre`（风险 `high-risk-write`）。必须 `prepare -> apply`：第一次调用不带 `confirm` 做折旧设置读取与计提月份预检（动作流 `deprePrecheck`），返回 continuation 与预检结果；用户确认后第二次调用带 `confirm:true` 与 `continuation` 执行折旧任务创建。

## 输入要点

以 `weaver-work-cli asset schema` 为准。必填：`calc_month`（格式 `YYYY-MM`，须早于当前月份）。可选：`company_ids`（当前登录人所属分部 ID，大整数按字符串传）。折旧方案与是否分组计提来自 `zgjasset_depre_setting` 配置，由 CLI 在 prepare 阶段读取。

- 计提类型（`task_mode`）由折旧设置的「是否分组计提」自动推导：分组计提开启 → 按分部计提（1）；关闭 → 全量计提（0）。**无需用户传入**。
- 分组计提开启时，CLI 自动取「当前登录人所属分部 ID」：优先用输入的 `company_ids`，否则按登录会话的分部名称解析；解析不到会明确报错（不臆造 ID），此时请提供 `company_ids`。
- prepare 阶段会按预检返回的可计提条件（无符合条件资产 / 已存在关联业务记录 / 后续周期已结提）判断，命中则停止，不进入 apply。

## 示例

Windows PowerShell：

```powershell
# prepare（折旧设置读取 + 计提月份预检，返回 continuation）
weaver-work-cli --profile eteams --json asset run asset.depre --input-json '{"calc_month":"2026-08"}'
# apply（用户确认后）
weaver-work-cli --profile eteams --json asset run asset.depre --input-json '{"continuation":"PREPARE_CONTINUATION","confirm":true}'
```

macOS/Linux（bash/zsh）：

```bash
# prepare（折旧设置读取 + 计提月份预检，返回 continuation）
weaver-work-cli --profile eteams --json asset run asset.depre --input-json '{"calc_month":"2026-08"}'
# apply（用户确认后）
weaver-work-cli --profile eteams --json asset run asset.depre --input-json '{"continuation":"PREPARE_CONTINUATION","confirm":true}'
```

## 返回

`apply` 成功返回折旧任务 `dataIds`、`count`、`calc_month`、`is_group_calc` 与 `task_mode`。

## 注意

- `calc_month` 必须早于当前月份；预检不通过（如月份非法、命中不可计提条件）时 prepare 会报错，不进入 apply。
- `apply` 建任务按契约写 `calc_month` + `task_mode`（由是否分组推导）+ `is_group_calc` + `task_status`（固定 0）；分组计提开启时才附 `company_ids`，关闭时整项省略（不传空串）。
- 折旧字段映射依赖 `zgjasset_depre_setting` 配置；若实际部署的配置字段与默认假设不同，apply 可能返回业务错误，此时停止并向用户说明，不要重复提交。
- 出现 `partial/write_uncertain` 时停止，先做一次只读回查，不要重复提交 apply。
