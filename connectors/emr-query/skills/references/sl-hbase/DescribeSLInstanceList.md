# DescribeSLInstanceList

> 分类：sl-hbase | 测试状态：✅ OK（2026-06-30 实测成功）

## 功能描述

Serverless HBase 查询实例列表。

## 统一调用格式

```bash
tccli emr DescribeSLInstanceList --region <region> --version 2019-01-03 --cli-unfold-argument --DisplayStrategy <DisplayStrategy> --Offset <Offset> --Limit <Limit>
```

## 必选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| DisplayStrategy | String | 实例筛选策略。`clusterList` 查询除已销毁外的实例；`monitorManage` 查询除已销毁、创建中、创建失败外的实例 |

## 可选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| Offset | Integer | 页编号，默认0 |
| Limit | Integer | 每页数量，默认10，最大100 |
| OrderField | String | 排序字段：`clusterId`/`addTime`/`status` |
| Asc | Integer | 0 升序 / 1 降序 |
| Filters | Array | 过滤器，如 `[{"Name":"ClusterId","Values":["emr-xxx"]}]` |

## tccli 调用示例

```bash
tccli emr DescribeSLInstanceList --region ap-guangzhou --version 2019-01-03 --cli-unfold-argument --DisplayStrategy clusterList --Limit 5
```

## 最新实测返回

```json
{
  "TotalCnt": 0,
  "InstancesList": [],
  "RequestId": "3e701933-715c-424e-b6e7-aefea0061edb"
}
```

## 错误码

| 错误码 | 含义 |
|------|------|
| 无特殊错误码 | 2026-06-30 实测调用成功；若无 SL-HBase 实例则返回空列表 |
