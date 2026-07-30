# EMR 只读查询 — 统一调用模板

> 当前连接器主路径统一为官方 `tccli`。目标不是再造签名脚本，而是把 **48 个当前可直接 tccli 调用的只读接口**收敛成一致的调用套路：**先看 help → 判断简单/复杂 → 直接展开或走 skeleton 文件**。

---

## 一、统一调用模板

### 模板 A：简单参数直接展开

```bash
tccli emr <Action> --region <region> --version 2019-01-03 --cli-unfold-argument --Param1 value1 --Param2 value2
```

适用：标量参数、无嵌套对象、无复杂数组。

### 模板 B：复杂参数通过 JSON 文件

```bash
tccli emr <Action> --generate-cli-skeleton > /tmp/<Action>.json
# 编辑 /tmp/<Action>.json

tccli emr <Action> --region <region> --version 2019-01-03 --cli-input-json file:///tmp/<Action>.json
```

适用：`Filters`、`FlowParam`、`ResourceSpec`、对象数组、对象嵌套。

---

## 二、标准工作流

### 1）看参数

```bash
tccli emr <Action> help
tccli emr <Action> help --detail
```

### 2）生成官方骨架（推荐）

```bash
tccli emr <Action> --generate-cli-skeleton
```

### 3）执行调用

```bash
tccli emr <Action> --region ap-guangzhou --version 2019-01-03 ...
```

---

## 三、高频示例

### 集群列表

```bash
tccli emr DescribeInstancesList --region ap-guangzhou --version 2019-01-03 --cli-unfold-argument --DisplayStrategy clusterList --Limit 100
```

### 集群节点

```bash
tccli emr DescribeClusterNodes --region ap-guangzhou --version 2019-01-03 --cli-unfold-argument --InstanceId emr-oem5vw80 --NodeFlag all
```

### Spark 查询

```bash
tccli emr DescribeSparkQueries --region ap-guangzhou --version 2019-01-03 --cli-unfold-argument --InstanceId emr-oem5vw80 --StartTime 1751277600 --EndTime 1751364000 --Offset 0 --Limit 20
```

### 流程状态（复杂参数）

```bash
tccli emr DescribeClusterFlowStatusDetail --generate-cli-skeleton > /tmp/DescribeClusterFlowStatusDetail.json
# 编辑 FlowParam 等字段

tccli emr DescribeClusterFlowStatusDetail --region ap-guangzhou --version 2019-01-03 --cli-input-json file:///tmp/DescribeClusterFlowStatusDetail.json
```

### 询价（复杂参数）

```bash
tccli emr InquiryPriceCreateInstance --generate-cli-skeleton > /tmp/InquiryPriceCreateInstance.json
# 编辑 ZoneId / TimeUnit / ResourceSpec / Software 等字段

tccli emr InquiryPriceCreateInstance --region ap-guangzhou --version 2019-01-03 --cli-input-json file:///tmp/InquiryPriceCreateInstance.json
```

---

## 四、结果与错误处理

### 成功输出
- `tccli` 默认输出 JSON
- 优先摘要展示关键字段，再附上 `RequestId`

### 失败输出
- 重点看 `Response.Error.Code` 与 `Response.Error.Message`
- 参数问题先回到 `help --detail`
- 复杂结构问题先回到 skeleton

---

## 五、分类索引

| 分类 | 数量 | 查阅目录 |
|------|------|----------|
| 集群资源 | 10 | `references/cluster-resource/` |
| 集群服务 | 2 | `references/cluster-service/` |
| 用户管理 | 2 | `references/user-management/` |
| 信息查询 | 23 | `references/info-query/` |
| 扩缩容 | 4 | `references/autoscaling/` |
| 配置 | 1 | `references/configuration/` |
| 其他 | 2 | `references/misc/` |
| YARN 调度 | 2 | `references/yarn-schedule/` |
| Serverless HBase | 2 | `references/sl-hbase/` |

每个接口文件都保留：功能描述、必选参数、可选参数、tccli 示例、最新实测状态、错误码。

---

## 六、统一结论

- 连接器层面：`cli.json` 已切换为官方 `tccli` 安装 / 认证 / 状态检查路径。
- Skill 层面：绝大多数接口统一使用 `tccli emr <Action>`，不再把 `tc_api.py` 当作主入口。
- 文档层面：复杂参数统一推荐 `--generate-cli-skeleton` + `file:///tmp/<Action>.json`。
