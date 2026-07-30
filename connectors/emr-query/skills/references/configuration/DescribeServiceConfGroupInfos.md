# DescribeServiceConfGroupInfos

> 分类：configuration | 测试状态：✅ OK（2026-06-30 实测成功）

## 功能描述

描述服务配置组信息。

## 统一调用格式

```bash
tccli emr DescribeServiceConfGroupInfos --region <region> --version 2019-01-03 --cli-unfold-argument --InstanceId <InstanceId> --ServiceName <ServiceName> --ConfGroupName <ConfGroupName> --PageNo <PageNo> --PageSize <PageSize>
```

## 必选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| InstanceId | String | 集群 ID |
| ServiceName | String | 组件名，如 `HDFS` |
| ConfGroupName | String | 配置组名称，如 `hdfs-master-defaultGroup`（可通过 DescribeServiceNodeInfos 获取） |
| PageNo | Integer | 页码，从1开始 |
| PageSize | Integer | 页大小 |

## tccli 调用示例

```bash
tccli emr DescribeServiceConfGroupInfos --region ap-guangzhou --version 2019-01-03 --cli-unfold-argument --InstanceId emr-oem5vw80 --ServiceName HDFS --ConfGroupName hdfs-master-defaultGroup --PageNo 1 --PageSize 10
```

## 最新实测返回

```json
{
  "TotalCount": 209,
  "ConfItemKVList": [
    {
      "Name": "YWxsdXhpby56b29rZWVwZXIuYWRkcmVzcw==",
      "Value": "MTcyLjE2LjQ4LjExOjIxODEs...",
      "InFile": "core-site.xml"
    }
  ],
  "RequestId": "9cdcca24-0d0c-4ce5-b26f-bc1034cfd3bc"
}
```

## 错误码

| 错误码 | 含义 |
|------|------|
| MissingParameter | 缺少必传参数 `ServiceName` / `ConfGroupName` |
