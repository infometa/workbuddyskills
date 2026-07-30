# DescribeDAGInfo

> 分类：info-query | 测试状态：⚠️ PARAM（需要真实 STARROCKS 查询 ID）

## 功能描述

查询 DAG 信息（目前仅支持 STARROCKS 类型）。

## 统一调用格式

```bash
tccli emr DescribeDAGInfo --region <region> --version 2019-01-03 --cli-input-json file:///tmp/DescribeDAGInfo.json
```

## 必选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| InstanceID | String | 集群 ID（注意：参数名为 `InstanceID` 不是 `InstanceId`） |
| Type | String | DAG 类型，目前仅支持 `STARROCKS` |
| IDList | Array of String | 查询 ID 列表，最大长度 1，如 `["query_id"]` |

## tccli 调用示例

```bash
cat > /tmp/DescribeDAGInfo.json <<'EOF'
{
  "InstanceID": "emr-oem5vw80",
  "Type": "STARROCKS",
  "IDList": ["<STARROCKS_query_id>"]
}
EOF
tccli emr DescribeDAGInfo --region ap-guangzhou --version 2019-01-03 --cli-input-json file:///tmp/DescribeDAGInfo.json
```

## 最新实测返回

```json
{
  "Response": {
    "Error": {
      "Code": "InvalidParameter",
      "Message": "not support type: SPARK now only support STARROCKS/HIVE"
    }
  }
}
```

## 错误码

| 错误码 | 含义 |
|------|------|
| InvalidParameter | Type 不支持（仅 STARROCKS）；IDList 需要真实的查询 ID |
