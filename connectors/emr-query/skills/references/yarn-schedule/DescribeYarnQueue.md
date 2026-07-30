# DescribeYarnQueue

> 分类：yarn-schedule | 测试状态：✅ OK（2026-06-30 实测成功）

## 功能描述

获取资源调度中的队列信息

## 统一调用格式

```bash
tccli emr DescribeYarnQueue --region <region> --version 2019-01-03 --cli-input-json file:///tmp/payload.json
```

## 必选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| InstanceId | String | 集群ID |
| Scheduler | String | 调度器类型:capacity |

## 可选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| 无 |

## tccli 调用示例

```bash
cat > /tmp/DescribeYarnQueue.json <<'EOF'
{
  "InstanceId": "emr-oem5vw80",
  "Scheduler": "capacity"
}
EOF
tccli emr DescribeYarnQueue --region ap-guangzhou --version 2019-01-03 --cli-input-json file:///tmp/DescribeYarnQueue.json
```

## 最新实测返回

```json
{
  "Queue": "...",
  "RequestId": "dcaa341d-b494-454a-bdb8-ea230569e10d"
}
```

## 错误码

| 类型 | 说明 |
|------|------|
| 无特殊错误码 | 2026-06-30 实测调用成功；若凭证或资源级权限不足，实际调用时仍可能返回 `AuthFailure.*` / `UnauthorizedOperation`。 |
