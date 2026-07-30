# DescribeEMREventList

> 分类：info-query | 测试状态：✅ OK（2026-06-30 实测成功）

## 功能描述

查询EMR事件数据

## 统一调用格式

```bash
tccli emr DescribeEMREventList --region <region> --version 2019-01-03 --cli-input-json file:///tmp/payload.json
```

## 必选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| InstanceId | String | 集群ID |

## 可选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| Offset | Integer | 分页 |
| Limit | Integer | 分页大小 |

## tccli 调用示例

```bash
cat > /tmp/DescribeEMREventList.json <<'EOF'
{
  "InstanceId": "emr-oem5vw80",
  "StartTime": 1782718065,
  "EndTime": 1782804465,
  "Offset": 0,
  "Limit": 20
}
EOF
tccli emr DescribeEMREventList --region ap-guangzhou --version 2019-01-03 --cli-input-json file:///tmp/DescribeEMREventList.json
```

## 最新实测返回

```json
{
  "EventList": [],
  "RequestId": "540304dd-913f-491a-93c5-532589aae987"
}
```

## 错误码

| 类型 | 说明 |
|------|------|
| 无特殊错误码 | 2026-06-30 实测调用成功；若凭证或资源级权限不足，实际调用时仍可能返回 `AuthFailure.*` / `UnauthorizedOperation`。 |
