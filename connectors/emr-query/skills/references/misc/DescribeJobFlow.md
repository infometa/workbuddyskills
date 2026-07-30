# DescribeJobFlow

> 分类：misc | 测试状态：⚠️ PARAM（需要真实 JobFlowId）

## 功能描述

查询流程作业状态。

## 统一调用格式

```bash
tccli emr DescribeJobFlow --region <region> --version 2019-01-03 --cli-unfold-argument --JobFlowId <JobFlowId>
```

## 必选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| JobFlowId | Integer | `RunJobFlow` 返回的流程任务 ID |

## 可选参数

| 参数 | 类型 | 说明 |
|------|------|------|
| 无 | - | 无 |

## tccli 调用示例

```bash
cat > /tmp/DescribeJobFlow.json <<'EOF'
{
  "JobFlowId": 1
}
EOF
tccli emr DescribeJobFlow --region ap-guangzhou --version 2019-01-03 --cli-input-json file:///tmp/DescribeJobFlow.json
```

## 最新实测返回

```json
{
  "Response": {
    "Error": {
      "Code": "InvalidParameter.InvalidJobFlow",
      "Message": "Invalid Job Flow"
    }
  }
}
```

## 错误码

| 错误码 | 含义 |
|------|------|
| InvalidParameter.InvalidJobFlow | 需要真实存在的 `JobFlowId`，占位值会直接报错 |

## 备注

`JobFlowId` 必须来自真实的 `RunJobFlow` 结果；当前 skill 仅支持查询，不负责创建流程作业。
