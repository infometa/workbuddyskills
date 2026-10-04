# tchousec-describe-event-tasks

## 功能说明

调用腾讯云 TCHouse-C 的 `DescribeEventTasks` 云 API，获取指定集群产生的事件任务（告警、维护、安全隐患等）。

## 接口信息

- **请求域名**：`cdwch.tencentcloudapi.com`
- **接口名称**：`DescribeEventTasks`
- **API 版本**：`2020-09-15`
- **请求方式**：POST
- **频率限制**：20次/秒

## 输入参数

| 参数名称    | 必选 | 类型           | 描述                                                                                     |
| ----------- | ---- | -------------- | ---------------------------------------------------------------------------------------- |
| InstanceId  | 是   | String         | 集群实例 ID，格式如 `cdwch-xxxxxxxx`                                                     |
| Region      | 是   | String         | 地域，如 `ap-guangzhou`                                                                  |
| EventTaskId | 否   | Integer        | 过滤指定的事件任务 ID                                                                    |
| PageNumber  | 否   | Integer        | 页码，默认为 1                                                                           |
| PageSize    | 否   | Integer        | 每页数量（支持 10/20/30/50/100/200），默认为 100                                         |
| EventCode   | 否   | String         | 事件名称过滤，如 `DiskHigh`                                                              |
| Status.N    | 否   | Array of Int   | 状态过滤：1-待处理；2-已预约；3-处理中；4-已结束；5-处理中；-1-已忽略；-2-已删除         |
| StartTime   | 否   | String         | 创建时间范围开始（格式：`YYYY-MM-DD HH:MM:SS`），最大支持查询 180 天                     |
| EndTime     | 否   | String         | 创建时间范围结束（格式：`YYYY-MM-DD HH:MM:SS`）                                         |
| SortField   | 否   | String         | 排序字段：`event_code`（事件类型）/ `create_time`（触发时间）/ `end_time`（完成时间）    |
| SortOrder   | 否   | String         | 排序顺序：`asc` / `desc`                                                                |

## 输出参数

| 参数名称                           | 类型    | 描述                                                                 |
| ---------------------------------- | ------- | -------------------------------------------------------------------- |
| TotalCount                         | Integer | 事件任务总数                                                         |
| EventTasks                         | Array   | 事件任务列表                                                         |
| EventTasks[].EventTaskId           | Integer | 事件任务 ID                                                          |
| EventTasks[].EventCode             | String  | 事件代码（见下方事件类型表）                                         |
| EventTasks[].EventNameDescribe     | String  | 事件名称中文描述                                                     |
| EventTasks[].EventDetail           | String  | 事件详情描述（包含原因和建议操作）                                   |
| EventTasks[].EventPriority         | Integer | 事件优先级（数字越小越紧急）                                         |
| EventTasks[].Status                | Integer | 状态：1-待处理；2-已预约；3-处理中；4-已结束；-1-已忽略              |
| EventTasks[].CreateTime            | String  | 事件创建时间                                                         |
| EventTasks[].FinishTime            | String  | 事件完成时间                                                         |
| EventTasks[].IP                    | String  | 关联的节点 IP（如有）                                                |
| EventTasks[].NeedAuthorization     | Integer | 是否需要用户授权：1-需要；2-已授权                                   |
| EventTasks[].OperationType         | Array   | 可执行的操作类型列表                                                 |
| EventTasks[].HandleUser            | String  | 处理人 UIN                                                           |

## 事件类型说明

| EventCode              | 事件名称         | 严重程度 | 说明                                                       |
| ---------------------- | ---------------- | -------- | ---------------------------------------------------------- |
| `DiskHigh`             | 磁盘使用率过高   | 🔴 高    | 节点磁盘使用率超过告警阈值                                 |
| `AbnormalInstanceDisk` | 实例硬盘异常     | 🔴 高    | 底层硬盘突发故障，可能导致 IO 异常                         |
| `InstanceDiskAlter`    | 实例硬盘预警     | 🟡 中    | 硬盘存在坏盘隐患或使用寿命即将耗尽                         |
| `InstanceRisk`         | 实例运行隐患     | 🟡 中    | 底层服务器存在软硬件隐患，可能导致性能抖动或宕机           |
| `InstanceMaintenance`  | 实例维护升级     | 🟢 低    | 底层服务器需要在线维护升级                                 |
| `EmptyPassword`        | 空密码安全隐患   | 🟡 中    | default 账户使用空密码或弱密码                             |

## 使用示例

### 请求示例

```json
{
  "Action": "DescribeEventTasks",
  "Version": "2020-09-15",
  "Region": "ap-guangzhou",
  "InstanceId": "cdwch-xxxxxxxx",
  "PageNumber": 1,
  "PageSize": 20,
  "Status": [1, 3],
  "SortField": "create_time",
  "SortOrder": "desc"
}
```

### 响应示例

```json
{
  "Response": {
    "TotalCount": 2,
    "EventTasks": [
      {
        "EventTaskId": 7,
        "EventCode": "InstanceDiskAlter",
        "EventNameDescribe": "实例硬盘预警",
        "EventDetail": "检测到节点当前底层服务器的本地硬盘存在坏盘隐患或使用寿命即将耗尽，可能导致实例 I/O 异常或磁盘掉线等数据层面异常。为尽快修复异常，需要您授权我们进行后台处理。",
        "EventPriority": 3,
        "Status": 1,
        "CreateTime": "2026-06-01T10:52:31+08:00",
        "FinishTime": "",
        "IP": "10.0.0.1",
        "NeedAuthorization": 2,
        "OperationType": ["OnlineMaintenanceForDisk", "ShutdownForLocal"],
        "HandleUser": ""
      },
      {
        "EventTaskId": 5,
        "EventCode": "EmptyPassword",
        "EventNameDescribe": "default账户使用空密码",
        "EventDetail": "检测到该实例存在安全隐患，创建集群时的默认 default 账户使用了空密码或弱密码，建议您及时对 default 账户密码进行增强。",
        "EventPriority": 3,
        "Status": 1,
        "CreateTime": "2026-05-28T19:16:50+08:00",
        "FinishTime": "",
        "IP": "",
        "NeedAuthorization": 1,
        "OperationType": ["ModifyPassword"],
        "HandleUser": ""
      }
    ],
    "RequestId": "141981e2-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
  }
}
```

## 典型使用场景

- **告警排查**：用户收到告警通知后，查询具体的事件详情和影响范围
- **健康巡检**：定期检查是否有未处理的事件任务，评估集群健康状态
- **故障定位**：通过事件的 IP 字段定位具体受影响的节点
- **历史回溯**：查询指定时间范围内的事件历史，分析问题是否反复出现
- **安全审计**：检查是否存在安全隐患类事件（如空密码）

## 注意事项

- `StartTime` 和 `EndTime` 最大支持查询 180 天的历史数据
- `EventDetail` 字段包含了事件的详细描述和建议操作，可直接展示给用户
- 状态为 1（待处理）的事件需要重点关注
- `NeedAuthorization=2` 表示需要用户授权后平台才能执行修复操作
