# DescribeInsightList

> 分类：info-query | 测试状态：✅ OK（2026-06-30 实测成功）

## 功能描述

获取洞察结果

## 统一调用格式

```bash
tccli emr DescribeInsightList --region <region> --version 2019-01-03 --cli-input-json file:///tmp/payload.json
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
| Offset | Integer | 分页 |
| Limit | Integer | 分页大小 |

## tccli 调用示例

```bash
cat > /tmp/DescribeInsightList.json <<'EOF'
{
  "InstanceId": "emr-oem5vw80",
  "StartTime": 1782718065,
  "EndTime": 1782804465,
  "PageSize": 10,
  "Page": 1
}
EOF
tccli emr DescribeInsightList --region ap-guangzhou --version 2019-01-03 --cli-input-json file:///tmp/DescribeInsightList.json
```

## 最新实测返回

```json
{
  "TotalCount": 0,
  "ResultList": null,
  "RequestId": "b240ec0d-3a36-4463-8b0a-753b7d0125e4"
}
```

## 错误码

| 类型 | 说明 |
|------|------|
| 无特殊错误码 | 2026-06-30 实测调用成功；若凭证或资源级权限不足，实际调用时仍可能返回 `AuthFailure.*` / `UnauthorizedOperation`。 |
