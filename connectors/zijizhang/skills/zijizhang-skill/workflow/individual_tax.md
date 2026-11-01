# 个税待办处理流程（code=GS）

`GS` 待办可能同时存在多个月份，需逐一处理。对每条 `GS` 待办（每个月份）执行以下流程：

## Step 1：查询当月个税申报状态

调用 `month_gs_report_info` 查询该月个税申报状态：

```shell
zijizhang-cli tax month_gs_report_info '<year>' '<month>' --uid='<uid>'
```

## Step 2：根据 state 分支处理

### state=待确认个税税额

📌 **需要用户确认**：
1. 向用户展示税额明细（总额、每人应缴金额）
2. 询问："是否同意确认缴纳上述个税？"
3. **等待用户回复"同意/确认/是"后**，才能执行下方命令

✅ 用户同意后执行：
```shell
zijizhang-cli tax agree_gs_tax_rate '<year>' '<month>' 1 --uid='<uid>'
```
❌ 用户不同意时执行：
 ```shell
zijizhang-cli tax disagree_gs_tax_rate '<year>' '<month>' --uid='<uid>'
```

### state=银行余额不足

📌 **需要用户确认**：
1. 告知用户对公银行账户余额不足
2. 询问："对公户是否已足够缴纳个税？"
3. **等待用户回复"确认/是"后**，才能执行下方命令

✅ 用户确认后执行：
```shell
zijizhang-cli tax agree_gs_tax_rate '<year>' '<month>' 3 --uid='<uid>'
```
❌ 用户表示尚未充足时，提示用户先充值对公账户，本次跳过

### state=线下缴款

📌 **需要用户确认**：
1. 询问："是否已完成线下缴款"
2. **等待用户回复"确认/是"后**，才能执行下方命令

✅ 用户确认后执行：
```shell
zijizhang-cli tax agree_gs_tax_rate '<year>' '<month>' 3 --uid='<uid>'
```
❌ 用户表示尚未缴款，提示用户完成线下缴款后再操作，本次跳过

### state=缴款中

- 告知用户缴款任务正在处理中，等待结果，无需任何操作

### 其他 state

- 不做任何操作，告知用户当前状态，跳过
