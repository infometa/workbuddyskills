# 审账待办处理流程（code=AUDIT）

## Step 1：执行审账前检查

```shell
zijizhang-cli todo before_set_month_audited '<year>' '<month>' --uid='<uid>'
```

## Step 2：根据 state 分支处理

### state=不能提交审账

- 向用户展示返回的 `reason`，告知当前无法提交审账
- 流程终止，不执行任何写操作

### state=需要确认

📌 **需要用户确认**：
1. 向用户展示返回的 `reason`
2. 询问："询问是否确认同意"
3. **等待用户回复"确认/是"后**，才能执行下方命令

✅ 用户确认后执行：
```shell
zijizhang-cli todo set_month_audited '<year>' '<month>' --uid='<uid>'
```
❌ 用户不同意，提示联系客服

### state=可以提交审账

- 直接执行提交审账：
```shell
zijizhang-cli todo set_month_audited '<year>' '<month>' --uid='<uid>'
```
