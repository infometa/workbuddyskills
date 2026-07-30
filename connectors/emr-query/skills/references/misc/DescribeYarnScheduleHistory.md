# DescribeYarnScheduleHistory

> 分类：misc | 测试状态：✅ OK（2026-06-30 实测成功）

## 功能描述

查询YARN资源调度历史（旧）

## 统一调用格式

```bash
tccli emr DescribeYarnScheduleHistory --region <region> --version 2019-01-03 --cli-input-json file:///tmp/payload.json
```

## 必选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| InstanceId | String | 集群ID |
| StartTime | Integer | 起始时间戳 |
| EndTime | Integer | 结束时间戳 |
| SchedulerType | String | 调度器类型:capacity |

## 可选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| 无 |

## tccli 调用示例

```bash
cat > /tmp/DescribeYarnScheduleHistory.json <<'EOF'
{
  "InstanceId": "emr-oem5vw80",
  "StartTime": 1782718065,
  "EndTime": 1782804465,
  "SchedulerType": "capacity"
}
EOF
tccli emr DescribeYarnScheduleHistory --region ap-guangzhou --version 2019-01-03 --cli-input-json file:///tmp/DescribeYarnScheduleHistory.json
```

## 最新实测返回

```json
{
  "Tasks": null,
  "Total": 0,
  "SchedulerNameList": [
    "Capacity Scheduler",
    "Fair Scheduler"
  ],
  "StateList": [
    0,
    1,
    2,
    -1
  ],
  "RequestId": "be46258d-263a-41aa-8d6c-bfb6113777c4"
}
```

## 错误码

| 类型 | 说明 |
|------|------|
| 无特殊错误码 | 2026-06-30 实测调用成功；若凭证或资源级权限不足，实际调用时仍可能返回 `AuthFailure.*` / `UnauthorizedOperation`。 |
