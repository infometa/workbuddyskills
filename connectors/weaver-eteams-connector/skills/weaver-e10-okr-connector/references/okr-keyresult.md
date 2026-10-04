# 关键成果保存（okr-keyresult）

关键成果（KR）的新建与修改共用一对 operation，**是否新建由有没有传 `kr_id` 决定**。

| operation | 风险 | 作用 |
| --- | --- | --- |
| `okr.kr.save.prepare` | read-before-write | 归一化输入、生成预览与 continuation，**不写入** |
| `okr.kr.save.apply` | high-risk-write | 提交关键成果保存（新建或修改） |

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `kr_id` | 关键成果 ID | **不传=新建，传了=修改** |
| `object_id` | 目标 ID | 必填，关键成果所属目标 |
| `name` | string | 关键成果名称，必填 |
| `principalid` | 人员 ID | 责任人，默认当前登录用户 |
| `participants` | 人员 ID 或数组 | 参与人（**仅标准版链路**） |
| `target_value` | number | 目标值 |
| `actual_value` | number | 实际值 |
| `weight` | number | 权重 |
| `progress` | number | 进度 0-100 |
| `score` | number | 分数 |
| `range` | `[开始,结束]` 或 `"开始,结束"` | 起止日期 `yyyy-MM-dd` |
| `kr_unit` | string | 单位（**仅 ebuilder 链路**） |
| `confidence` | number | 信心指数（**仅 ebuilder 链路**） |
| `risk` | `"1"`/`"2"`/`"3"` | 风险指数：1-正常 2-有风险 3-已延期（**仅 ebuilder 链路**） |
| `confirm` / `continuation` | - | 仅 `apply` 需要 |

## 链路差异

- **标准版链路**：写入 `/api/workrelate/goal/fs/krForm/saveForm` 的 `baseInfo`；新建不传 `id`，修改传 `id`。`kr_unit`/`confidence`/`risk` 属于 ebuilder 字段，被忽略后记入 `meta.notes`。
- **ebuilder 链路**：按有无 `kr_id` 选择 `okr_createKeyResult` 或 `okr_updateKeyResult`；`participants` 属于标准版字段，被忽略后记入 `meta.notes`。

## 确认链

1. `okr.kr.save.prepare` 返回 `preview`（关键成果名称、所属目标、责任人、目标值/实际值、权重、起止日期、操作=新建或修改）与 `continuation`。
2. 用户明确确认后调 `okr.kr.save.apply`，传 `confirm=true`、`continuation`，以及 `object_id` 与 `name`（schema 必需）。
3. continuation 绑定 `baseUrl`/`profile`/`userId`，10 分钟有效；内容指纹变化返回 `validation/target_changed`，需重新 prepare。

## 调用示例

新建关键成果：

```text
weaver-work-cli --profile eteams --json okr run okr.kr.save.prepare --input-json '{"object_id":"<目标ID>","name":"后端接口开发","target_value":53,"actual_value":20,"weight":100,"progress":37,"range":["2026-01-01","2026-12-31"]}'
```

用户确认后提交：

```text
weaver-work-cli --profile eteams --json okr run okr.kr.save.apply --input-json '{"object_id":"<目标ID>","name":"后端接口开发","confirm":true,"continuation":"<prepare 返回的 continuation>"}'
```

修改已有关键成果（带 `kr_id`）：

```text
weaver-work-cli --profile eteams --json okr run okr.kr.save.prepare --input-json '{"kr_id":"<关键成果ID>","object_id":"<目标ID>","name":"后端接口开发","progress":80}'
```

## 失败处理

- 写入请求发出后连接中断 → `partial/write_uncertain`，禁止自动重试；先通过 `okr.get`（标准版）或 `okr.kr.list`（ebuilder）复核。
- ebuilder 链路要批量核对关键成果时，用 `okr.kr.list` 按 `object_id` 分页查询。

## 注意

- **源资料只提供关键成果的新建与编辑接口，没有删除接口**，因此 CLI 不提供删除关键成果的 operation，不要尝试拼接口。
- `range` 传反（开始晚于结束）会被拒绝；`risk` 只接受 1/2/3。
- 结果不确定时先只读回查，不要重放写请求。
