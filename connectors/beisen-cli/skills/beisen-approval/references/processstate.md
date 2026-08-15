# 审批流程状态

流程状态名称与值，用于 `--data` 中 `approvalStatuses` 字段筛选。

| 名称 | 值 |
|------|:---:|
| 审批中 | 1 |
| 通过 | 2 |
| 不通过 | 3 |
| 已完成 | 4 |
| 已终止 | 5 |
| 已驳回 | 6 |
| 已撤回 | 7 |

## 分组

- 在途流程：审批中（1）
- 已结束流程：通过（2）、不通过（3）、已完成（4）、已终止（5）、已驳回（6）、已撤回（7）

## 用法

`approvalStatuses` 为数组，传入对应状态值筛选。例如查询在途流程：

```bash
beisen-cli approval task queryMyCompletedTasks --data '{"approvalStatuses":[1]}'
```

查询已结束流程：

```bash
beisen-cli approval task queryMyCompletedTasks --data '{"approvalStatuses":[2,3,4,5,6,7]}'
```
