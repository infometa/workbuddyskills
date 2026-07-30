# DescribeResourceSchedule

> 分类：cluster-service | 测试状态：⚠️ DEPRECATED（已废弃，请使用 DescribeYarnQueue）

## 功能描述

查询 YARN 资源调度数据信息（**已废弃**，官方建议使用 `DescribeYarnQueue` 替代）。

## 统一调用格式

```bash
tccli emr DescribeResourceSchedule --region <region> --version 2019-01-03 --cli-unfold-argument --InstanceId <InstanceId>
```

## 必选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| InstanceId | String | 集群 ID |

## tccli 调用示例

```bash
tccli emr DescribeResourceSchedule --region ap-guangzhou --version 2019-01-03 --cli-unfold-argument --InstanceId emr-oem5vw80
```

## 最新实测返回

```json
{
  "Response": {
    "Error": {
      "Code": "InvalidParameter",
      "Message": "InvalidParameter"
    }
  }
}
```

## 错误码

| 错误码 | 含义 |
|------|------|
| InvalidParameter | 已废弃接口，建议改用 `DescribeYarnQueue` |

## 备注

- 该接口已废弃，官方 API 文档明确建议使用 `DescribeYarnQueue` 查询队列信息。
- 如需查询调度器信息，推荐使用 `DescribeYarnQueue --Scheduler capacity` 或 `DescribeYarnScheduleHistory`。
