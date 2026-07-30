# DescribeNodeSpec

> 分类：info-query | 测试状态：✅ OK（2026-06-30 实测成功）

## 功能描述

查询节点规格

## 统一调用格式

```bash
tccli emr DescribeNodeSpec --region <region> --version 2019-01-03 --cli-input-json file:///tmp/payload.json
```

## 必选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| ZoneId | Integer | 可用区ID |
| CvmPayMode | Integer | 0按量/1包年包月/99全部 |
| NodeType | String | Master/Core/Task/Router/All |
| TradeType | Integer | 0旧计费/1新计费 |
| ProductId | Integer | 产品ID |
| SceneName | String | 场景名,如Hadoop-Default |

## 可选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| 无 |

## tccli 调用示例

```bash
cat > /tmp/DescribeNodeSpec.json <<'EOF'
{
  "ZoneId": 100007,
  "CvmPayMode": 0,
  "NodeType": "All",
  "TradeType": 1,
  "ProductId": 53,
  "SceneName": "Hadoop-Default"
}
EOF
tccli emr DescribeNodeSpec --region ap-guangzhou --version 2019-01-03 --cli-input-json file:///tmp/DescribeNodeSpec.json
```

## 最新实测返回

```json
{
  "NodeSpecs": [],
  "RequestId": "db699f7c-6788-45c1-a8b9-6d0c6b3396d9"
}
```

## 错误码

| 类型 | 说明 |
|------|------|
| 无特殊错误码 | 2026-06-30 实测调用成功；若凭证或资源级权限不足，实际调用时仍可能返回 `AuthFailure.*` / `UnauthorizedOperation`。 |
