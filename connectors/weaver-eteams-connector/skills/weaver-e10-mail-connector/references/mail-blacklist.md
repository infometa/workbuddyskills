# 黑名单（prepare → apply 确认链）

风险等级：`write`。新增/删除均走 prepare→apply 确认链。

## 操作字段

| operation | 字段 |
|---|---|
| `mail.blacklist.operate.prepare` | `operateType`（`add` / `delete`）、`mailAddress`（add 时必填）、`id`（delete 时按 id）、`confirm`、`continuation` |
| `mail.blacklist.operate.apply` | 同上（apply 必带 `continuation` + `confirm:true`） |

## 流程

```text
weaver-work-cli --profile eteams --json mail run mail.blacklist.operate.prepare --input-json '{"operateType":"add","mailAddress":"spam@example.com"}'
# 返回 continuation（含操作类型与目标）
weaver-work-cli --profile eteams --json mail run mail.blacklist.operate.apply --input-json '{"continuation":"<PREPARE_CONTINUATION>","confirm":true}'
```

- `add`：需 `mailAddress`（邮箱地址）。
- `delete`：需 `id`（黑名单记录 id）或对应 `mailAddress`；CLI 按源接口约定解析。

## 要点

- prepare 输出摘要（操作类型 + 目标），apply 前 CLI 重新校验 continuation 与上下文。
- 删除为即时写，确认目标。
- 写请求已发出后遇到不确定结果，停止重试，按共享 `high-risk-write.md` 处理。
