# InquiryPriceRenewInstance

> 分类：cluster-resource | 测试状态：⚠️ PARAM（缺少 PayMode）

## 功能描述

续费询价。

## 统一调用格式

```bash
tccli emr InquiryPriceRenewInstance --region <region> --version 2019-01-03 --cli-input-json file:///tmp/InquiryPriceRenewInstance.json
```

## 必选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| TimeSpan | Integer | 续费时长，1 表示续费一个月 |
| PayMode | Integer | 实例计费模式，**仅支持 1（包年包月）** |

## 可选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| ResourceIds | Array of String | 待续费节点资源 ID 列表，如 `["emr-vm-xxxxxxxx"]`（通过 DescribeClusterNodes 获取） |
| TimeUnit | String | 时间单位：`m` 表示月份 |
| Currency | String | 货币种类：`CNY` |
| Placement | Object | 位置信息 `{"Zone":"ap-guangzhou-3","ProjectId":0}` |
| ModifyPayMode | Integer | 是否按量转包年包月：0 否 / 1 是 |
| NeedDetail | Boolean | 是否返回详细价格 |

## tccli 调用示例

```bash
cat > /tmp/InquiryPriceRenewInstance.json <<'EOF'
{
  "TimeSpan": 1,
  "PayMode": 1,
  "ResourceIds": ["emr-vm-xxxxxxxx"],
  "Placement": {
    "Zone": "ap-guangzhou-3",
    "ProjectId": 0
  }
}
EOF
tccli emr InquiryPriceRenewInstance --region ap-guangzhou --version 2019-01-03 --cli-input-json file:///tmp/InquiryPriceRenewInstance.json
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
| InvalidParameter.InvalidClusterId | 需要包年包月集群，且 ResourceIds 需为真实节点资源 ID |
