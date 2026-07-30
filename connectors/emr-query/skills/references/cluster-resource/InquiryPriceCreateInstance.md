# InquiryPriceCreateInstance

> 分类：cluster-resource | 测试状态：⚠️ PARAM（缺少 Software）

## 功能描述

创建实例询价。

## 统一调用格式

```bash
tccli emr InquiryPriceCreateInstance --region <region> --version 2019-01-03 --cli-input-json file:///tmp/InquiryPriceCreateInstance.json
```

## 必选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| TimeUnit | String | 计费单位：按量 `s` / 包年包月 `m` |
| TimeSpan | Integer | 时长，按量固定3600，包月如 `1` |
| Currency | String | 货币种类：`CNY` |
| PayMode | Integer | 0 按量 / 1 包年包月 |
| SupportHA | Integer | 0 不高可用 / 1 高可用 |
| Software | Array of String | 部署组件列表，如 `["hdfs-2.8.5","yarn-2.8.5","zookeeper-3.6.1","openldap-2.4.44","knox-1.2.0"]` |

## 可选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| Placement | Object | 位置信息 `{"Zone":"ap-guangzhou-3","ProjectId":0}` |
| ResourceSpec | Object | 资源规格 |
| ProductId | Integer | 产品ID，如 30(EMR-V2.6.0) |

## tccli 调用示例

```bash
cat > /tmp/InquiryPriceCreateInstance.json <<'EOF'
{
  "TimeUnit": "s",
  "TimeSpan": 3600,
  "PayMode": 0,
  "Currency": "CNY",
  "SupportHA": 0,
  "Software": ["hdfs-2.8.5", "yarn-2.8.5", "zookeeper-3.6.1", "openldap-2.4.44", "knox-1.2.0"],
  "Placement": {
    "Zone": "ap-guangzhou-3",
    "ProjectId": 0
  }
}
EOF
tccli emr InquiryPriceCreateInstance --region ap-guangzhou --version 2019-01-03 --cli-input-json file:///tmp/InquiryPriceCreateInstance.json
```

## 最新实测返回

```json
{
  "Response": {
    "Error": {
      "Code": "MissingParameter",
      "Message": "请求缺少必传参数 `Software` 。"
    }
  }
}
```

## 错误码

| 错误码 | 含义 |
|------|------|
| MissingParameter | 缺少必传参数 `Software` |
