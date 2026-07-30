# InquirePriceRenewEmr

> 分类：cluster-resource | 测试状态：⚠️ PARAM（仅支持包年包月集群）

## 功能描述

集群续费询价。

## 统一调用格式

```bash
tccli emr InquirePriceRenewEmr --region <region> --version 2019-01-03 --cli-input-json file:///tmp/InquirePriceRenewEmr.json
```

## 必选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| InstanceId | String | 待续费集群 ID |
| TimeSpan | Integer | 续费时长，1 表示续费一个月 |
| Placement | Object | 实例所在的位置，`{"Zone": "ap-guangzhou-3", "ProjectId": 0}` |
| PayMode | Integer | 实例计费模式，**仅支持 1（包年包月）** |

## 可选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| TimeUnit | String | 时间单位：`m` 表示月份 |
| Currency | String | 货币种类：`CNY` 表示人民币 |

## tccli 调用示例

```bash
cat > /tmp/InquirePriceRenewEmr.json <<'EOF'
{
  "InstanceId": "emr-oem5vw80",
  "TimeSpan": 1,
  "PayMode": 1,
  "Placement": {
    "Zone": "ap-guangzhou-3",
    "ProjectId": 0
  }
}
EOF
tccli emr InquirePriceRenewEmr --region ap-guangzhou --version 2019-01-03 --cli-input-json file:///tmp/InquirePriceRenewEmr.json
```

## 最新实测返回

```json
{
  "Response": {
    "Error": {
      "Code": "InvalidParameter.InvalidClusterId",
      "Message": "invalid parameter of clusterId"
    }
  }
}
```

## 错误码

| 错误码 | 含义 |
|------|------|
| InvalidParameter.InvalidClusterId | 需要包年包月集群 ID（按量付费集群无法续费询价） |
| MissingParameter | 缺少必传参数 `PayMode` |
