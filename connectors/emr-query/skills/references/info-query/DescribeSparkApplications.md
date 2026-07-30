# DescribeSparkApplications

> 分类：info-query | 测试状态：⚠️ PARAM（当前示例值返回 InvalidClusterId）

## 功能描述

获取 Spark 任务列表。

## 统一调用格式

```bash
tccli emr DescribeSparkApplications --region <region> --version 2019-01-03 --cli-input-json file:///tmp/DescribeSparkApplications.json
```

## 必选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| InstanceId | String | 集群 ID |
| StartTime | Integer | 查询开始时间戳 |
| EndTime | Integer | 查询结束时间戳 |
| PageSize | Integer | 每一页条数 |
| Page | Integer | 第几页 |

## 可选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| 无 | - | 无（注意：该接口分页参数为 `Page` / `PageSize`，非 `Offset` / `Limit`） |

## tccli 调用示例

```bash
cat > /tmp/DescribeSparkApplications.json <<'EOF'
{
  "InstanceId": "emr-oem5vw80",
  "StartTime": 1782718065,
  "EndTime": 1782804465,
  "PageSize": 10,
  "Page": 1
}
EOF
tccli emr DescribeSparkApplications --region ap-guangzhou --version 2019-01-03 --cli-input-json file:///tmp/DescribeSparkApplications.json
```

## 最新实测返回

```json
{
  "Response": {
    "Error": {
      "Code": "InvalidParameter.InvalidClusterId",
      "Message": "Invalid ClusterId"
    }
  }
}
```

## 错误码

| 错误码 | 含义 |
|------|------|
| InvalidParameter.InvalidClusterId | 当前示例值不足以通过校验；调用前需确认该接口使用的实际 Spark 集群标识 |

## 备注

调用前先用 `tccli emr DescribeInstancesList` 获取当前可访问集群，再用 `tccli emr DescribeSparkApplications help --detail` 复核该接口期望的集群标识字段含义。
