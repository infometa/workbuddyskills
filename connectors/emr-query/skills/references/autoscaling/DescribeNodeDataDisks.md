# DescribeNodeDataDisks

> 分类：autoscaling | 测试状态：⚠️ PARAM（需要真实 CVM 实例 ID）

## 功能描述

查询节点数据盘信息。

## 统一调用格式

```bash
tccli emr DescribeNodeDataDisks --region <region> --version 2019-01-03 --cli-unfold-argument --InstanceId <InstanceId> --CvmInstanceIds '["<CvmInstanceId>"]'
```

## 必选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| InstanceId | String | EMR 集群实例 ID |
| CvmInstanceIds | Array of String | 节点 CVM 实例 ID 列表，如 `["ins-xxxxxxxx"]` |

## 可选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| Filters | Array | 过滤条件 |
| InnerSearch | String | 模糊搜索 |
| Limit | Integer | 每页数量，默认100，最大100 |
| Offset | Integer | 数据偏移值 |
| Scene | String | 场景值：`ModifyDiskExtraPerformance` 调整数据盘额外性能 |

## tccli 调用示例

```bash
tccli emr DescribeNodeDataDisks --region ap-guangzhou --version 2019-01-03 --cli-unfold-argument --InstanceId <emr-xxx> --CvmInstanceIds '["ins-xxxxxxxx"]'
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
| MissingParameter | 缺少必传参数 `CvmInstanceIds` |
| InvalidParameter.InvalidClusterId | 需要传统 CVM 型集群（TKE 型集群无 CVM 实例 ID） |

## 备注

- 需要的是 **CVM 实例 ID**（如 `ins-xxxxxxxx`），非 EMR 节点资源 ID（`emr-vm-xxxxxxxx`）。
- TKE 型 EMR 集群节点无 CVM 实例 ID，使用 `DescribeClusterNodes` 返回的 `EmrResourceId` 不可用于此接口。
