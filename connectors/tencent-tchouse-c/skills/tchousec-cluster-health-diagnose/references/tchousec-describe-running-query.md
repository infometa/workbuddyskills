
# tchousec-describe-running-query

## 功能说明

调用腾讯云 TCHouse-C 的 `DescribeRunningQuery` 云 API，获取指定集群当前正在执行的查询列表。

## 接口信息

- **请求域名**：`cdwch.tencentcloudapi.com`
- **接口名称**：`DescribeRunningQuery`
- **API 版本**：`2020-09-15`
- **请求方式**：POST
- **频率限制**：20次/秒

## 输入参数

| 参数名称   | 必选 | 类型    | 描述                                 |
| ---------- | ---- | ------- | ------------------------------------ |
| InstanceId | 是   | String  | 集群实例 ID，格式如 `cdwch-xxxxxxxx` |
| Region     | 是   | String  | 地域，如 `ap-beijing`                |
| PageSize   | 否   | Integer | 每页返回条数，默认 10                |
| PageNum    | 否   | Integer | 页码，默认 1                         |

## 输出参数

| 参数名称                          | 类型    | 描述                       |
| --------------------------------- | ------- | -------------------------- |
| RunningQueryRecords               | Array   | 正在运行的查询列表         |
| RunningQueryRecords[].NodeIp      | String  | 执行节点 IP                |
| RunningQueryRecords[].OsUser      | String  | 执行用户（账户）           |
| RunningQueryRecords[].QueryIp     | String  | 请求 IP（客户端地址）      |
| RunningQueryRecords[].QueryId     | String  | 查询 ID                    |
| RunningQueryRecords[].StartTime   | String  | 查询开始时间               |
| RunningQueryRecords[].RunningMs   | Integer | 已运行时长（毫秒）         |
| RunningQueryRecords[].Sql         | String  | SQL 文本                   |
| TotalCount                        | Integer | 正在运行的查询总数         |

## 使用示例

### 请求示例

```json
{
  "Action": "DescribeRunningQuery",
  "Version": "2020-09-15",
  "Region": "ap-beijing",
  "InstanceId": "cdwch-xxxxxxxx",
  "PageSize": 10,
  "PageNum": 1
}
```

### 响应示例

```json
{
  "Response": {
    "RequestId": "c2e5deba-4234-4986-9d9a-3e4f7c97564f",
    "RunningQueryRecords": [
      {
        "NodeIp": "10.0.1.100",
        "OsUser": "etl_user",
        "QueryIp": "10.0.1.50",
        "QueryId": "abc-123-def",
        "StartTime": "2024-01-15 10:30:45",
        "RunningMs": 120500,
        "Sql": "SELECT count(*) FROM db.events WHERE event_date BETWEEN '2024-01-01' AND '2024-01-31' GROUP BY user_id"
      }
    ],
    "TotalCount": 1
  }
}
```

## 典型使用场景

- **实时诊断**：发现当前正在执行的长耗时 SQL
- **资源争抢判断**：多个大查询同时运行可能导致资源争抢
- **锁等待排查**：如果查询长时间无进展，可能存在锁等待
- **紧急处理**：对于严重影响集群的查询，可以提供 QueryId 用于 KILL 操作

## 判断策略

| 特征                    | 判断             | 建议                       |
| ----------------------- | ---------------- | -------------------------- |
| 单条查询运行超过 5 分钟 | 可能存在性能问题 | 分析该 SQL 的执行计划      |
| 多条大查询并发          | 资源争抢         | 建议错峰执行或限制并发     |
| 查询长时间无进展        | 全表扫描         | 需要添加索引或优化查询条件 |
