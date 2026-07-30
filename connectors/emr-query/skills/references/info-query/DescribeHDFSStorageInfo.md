# DescribeHDFSStorageInfo

> 分类：info-query | 测试状态：✅ OK（2026-06-30 实测成功）

## 功能描述

查询HDFS存储文件数量

## 统一调用格式

```bash
tccli emr DescribeHDFSStorageInfo --region <region> --version 2019-01-03 --cli-input-json file:///tmp/payload.json
```

## 必选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| InstanceId | String | 集群ID |

## 可选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| 无 |

## tccli 调用示例

```bash
cat > /tmp/DescribeHDFSStorageInfo.json <<'EOF'
{
  "InstanceId": "emr-oem5vw80",
  "StartTime": 1782718065,
  "EndTime": 1782804465
}
EOF
tccli emr DescribeHDFSStorageInfo --region ap-guangzhou --version 2019-01-03 --cli-input-json file:///tmp/DescribeHDFSStorageInfo.json
```

## 最新实测返回

```json
{
  "SampleTime": 0,
  "RequestId": "f487e8dc-0c56-4b9a-a24d-e775d016dd31"
}
```

## 错误码

| 类型 | 说明 |
|------|------|
| 无特殊错误码 | 2026-06-30 实测调用成功；若凭证或资源级权限不足，实际调用时仍可能返回 `AuthFailure.*` / `UnauthorizedOperation`。 |
