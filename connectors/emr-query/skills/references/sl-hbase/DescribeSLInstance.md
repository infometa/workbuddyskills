# DescribeSLInstance

> 分类：sl-hbase | 测试状态：⚠️ RESOURCE（需要真实 SL-HBase 实例 ID）

## 功能描述

Serverless HBase 查询实例信息。

## 统一调用格式

```bash
tccli emr DescribeSLInstance --region <region> --version 2019-01-03 --cli-unfold-argument --InstanceId <SLInstanceId>
```

## 必选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| InstanceId | String | Serverless HBase 实例 ID |

## 可选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| 无 | - | 无 |

## tccli 调用示例

```bash
cat > /tmp/DescribeSLInstance.json <<'EOF'
{
  "InstanceId": "emr-oem5vw80"
}
EOF
tccli emr DescribeSLInstance --region ap-guangzhou --version 2019-01-03 --cli-input-json file:///tmp/DescribeSLInstance.json
```

## 最新实测返回

```json
{
  "Response": {
    "Error": {
      "Code": "ResourceNotFound.InstanceNotFound",
      "Message": "Instance not found"
    }
  }
}
```

## 错误码

| 错误码 | 含义 |
|------|------|
| ResourceNotFound.InstanceNotFound | 需要真实存在的 SL-HBase 实例 ID |
