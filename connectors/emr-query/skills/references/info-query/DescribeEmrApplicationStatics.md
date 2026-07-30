# DescribeEmrApplicationStatics

> 分类：info-query | 测试状态：✅ OK（2026-06-30 实测成功）

## 功能描述

查询YARN任务统计信息

## 统一调用格式

```bash
tccli emr DescribeEmrApplicationStatics --region <region> --version 2019-01-03 --cli-input-json file:///tmp/payload.json
```

## 必选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| InstanceId | String | 集群ID |
| StartTime | Integer | 起始时间戳 |
| EndTime | Integer | 结束时间戳 |

## 可选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| Queue | String | 队列名,如default |
| Users | String[] | 用户名列表,如["hadoop"] |
| ApplicationTypes | String[] | ["SPARK","MAPREDUCE","TEZ"] |

## tccli 调用示例

```bash
cat > /tmp/DescribeEmrApplicationStatics.json <<'EOF'
{
  "InstanceId": "emr-oem5vw80",
  "StartTime": 1782718065,
  "EndTime": 1782804465
}
EOF
tccli emr DescribeEmrApplicationStatics --region ap-guangzhou --version 2019-01-03 --cli-input-json file:///tmp/DescribeEmrApplicationStatics.json
```

## 最新实测返回

```json
{
  "Statics": [],
  "TotalCount": 0,
  "Queues": [],
  "Users": [],
  "ApplicationTypes": [],
  "RequestId": "ebf17158-e28e-493c-bbc9-44bc1ec8cad0"
}
```

## 错误码

| 类型 | 说明 |
|------|------|
| 无特殊错误码 | 2026-06-30 实测调用成功；若凭证或资源级权限不足，实际调用时仍可能返回 `AuthFailure.*` / `UnauthorizedOperation`。 |
