# InquiryPriceScaleOutInstance

> 分类：cluster-resource | 测试状态：⚠️ PARAM（缺少 CoreCount）

## 功能描述

扩容询价。

## 统一调用格式

```bash
tccli emr InquiryPriceScaleOutInstance --region <region> --version 2019-01-03 --cli-input-json file:///tmp/InquiryPriceScaleOutInstance.json
```

## 必选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| TimeUnit | String | 计费单位：按量 `s` / 包年包月 `m` |
| TimeSpan | Integer | 时长，按量固定3600，包月如 `1` |
| ZoneId | Integer | 可用区 ID，如 `100003`（通过 DescribeZones 获取） |
| PayMode | Integer | 0 按量 / 1 包年包月 |
| InstanceId | String | 集群 ID |
| CoreCount | Integer | 扩容的 Core 节点数量 |
| TaskCount | Integer | 扩容的 Task 节点数量 |

## 可选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| Currency | String | 货币种类：`CNY` |
| RouterCount | Integer | 扩容的 Router 节点数量 |
| MasterCount | Integer | 扩容的 Master 节点数量 |
| ResourceBaseType | String | 资源类型 |
| ComputeResourceId | String | 计算资源 ID |
| HardwareResourceType | String | 硬件资源类型 |

## tccli 调用示例

```bash
cat > /tmp/InquiryPriceScaleOutInstance.json <<'EOF'
{
  "TimeUnit": "s",
  "TimeSpan": 3600,
  "ZoneId": 100003,
  "PayMode": 0,
  "InstanceId": "emr-oem5vw80",
  "CoreCount": 1,
  "TaskCount": 0,
  "Currency": "CNY"
}
EOF
tccli emr InquiryPriceScaleOutInstance --region ap-guangzhou --version 2019-01-03 --cli-input-json file:///tmp/InquiryPriceScaleOutInstance.json
```

## 最新实测返回

```json
{
  "Response": {
    "Error": {
      "Code": "MissingParameter",
      "Message": "请求缺少必传参数 `CoreCount` 。"
    }
  }
}
```

## 错误码

| 错误码 | 含义 |
|------|------|
| MissingParameter | 缺少必传参数 `CoreCount` |
