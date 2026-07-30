# InquiryPriceUpdateInstance

> 分类：cluster-resource | 测试状态：⚠️ PARAM（需要目标变配规格配置）

## 功能描述

变配询价。

## 统一调用格式

```bash
tccli emr InquiryPriceUpdateInstance --region <region> --version 2019-01-03 --cli-input-json file:///tmp/InquiryPriceUpdateInstance.json
```

## 必选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| TimeUnit | String | 计费单位：按量 `s` / 包年包月 `m` |
| TimeSpan | Integer | 时长，按量固定3600，包月如 `1` |
| PayMode | Integer | 0 按量 / 1 包年包月 |
| UpdateSpec | Object | 节点变配的目标配置（UpdateInstanceSettings 结构） |

## 可选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| Placement | Object | 位置信息 `{"Zone":"ap-guangzhou-3","ProjectId":0}` |
| Currency | String | 货币种类：`CNY` |
| ResourceIdList | Array of String | 批量变配资源 ID 列表 |

## tccli 调用示例

```bash
cat > /tmp/InquiryPriceUpdateInstance.json <<'EOF'
{
  "TimeUnit": "s",
  "TimeSpan": 3600,
  "PayMode": 0,
  "Currency": "CNY",
  "Placement": {
    "Zone": "ap-guangzhou-3",
    "ProjectId": 0
  },
  "UpdateSpec": {
    "Memory": 8,
    "CPUCores": 4,
    "ResourceId": "emr-vm-xxxxxxxx",
    "InstanceType": "S5.LARGE8"
  },
  "ResourceIdList": ["emr-vm-xxxxxxxx"]
}
EOF
tccli emr InquiryPriceUpdateInstance --region ap-guangzhou --version 2019-01-03 --cli-input-json file:///tmp/InquiryPriceUpdateInstance.json
```

## 最新实测返回

```json
{
  "Response": {
    "Error": {
      "Code": "MissingParameter",
      "Message": "请求缺少必传参数 `PayMode` 。"
    }
  }
}
```

## 错误码

| 错误码 | 含义 |
|------|------|
| MissingParameter | 缺少必传参数 `PayMode` |
