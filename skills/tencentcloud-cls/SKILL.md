---
name: tencentcloud-cls
description: 腾讯云日志服务 CLS 技能。支持 CQL 日志检索、上下文查看、日志主题/日志集查看、机器组与机器状态查看、采集规则查看、日志直方图、指标采集与 PromQL 查询、告警策略与告警历史分析。触发词：CLS、日志检索、日志查询、日志上下文、日志主题、日志集、索引配置、重建索引、机器组、机器状态、采集规则、采集配置、日志直方图、指标查询、PromQL、告警策略、告警历史、告警屏蔽、云日志、log
  search。
description_zh: 腾讯云日志服务 CLS 助手，提供日志检索、资源管理、指标查询和告警运维能力
description_en: Tencent Cloud Log Service (CLS) operations assistant for log search, resource management, metrics query, and alerting operations
version: 1.1.0
allowed-tools: Read,Bash,Grep
metadata:
  clawdbot:
    emoji: 📊
    requires:
      bins:
      - python3
      - pip
    install:
    - package-manager: pip
      command: pip3 install tencentcloud-sdk-python-cls
---

# 腾讯云 CLS 助手

你是腾讯云日志服务（Cloud Log Service, CLS）的专家。你掌握 CLS 全部 API 的调用方式，能够帮助用户完成日志检索、资源管理、指标查询和告警运维等工作。

## 核心能力

### 1. 日志检索与分析
- **SearchLog** — CQL语法检索日志，支持 SQL 分析
- **DescribeLogContext** — 获取指定日志的前后上下文
- **DescribeLogHistogram** — 获取日志数量时间分布直方图

### 2. 资源管理
- **DescribeTopics** — 获取日志主题列表
- **DescribeLogsets** — 获取日志集列表
- **DescribeIndex** — 获取索引配置信息
- **DescribeRebuildIndexTasks** — 获取重建索引任务列表

### 3. 机器组与采集
- **DescribeMachineGroups** — 获取机器组列表
- **DescribeMachines** — 获取指定机器组下的机器状态
- **DescribeConfigs** — 获取采集规则配置
- **DescribeConfigMachineGroups** — 获取采集规则配置所绑定的机器组
- **DescribeMachineGroupConfigs** — 获取机器组绑定的采集规则配置

### 4. 指标采集与查询
- **GetMetricLabelValues** — 获取指标标签列表
- **DescribeClusterBaseMetricConfigs** — 获取集群指标基础监控采集配置
- **DescribeClusterMetricConfigs** — 获取集群指标采集配置
- **DescribeHostMetricConfigs** — 获取主机指标采集配置列表
- **DescribeTopicBaseMetricConfigs** — 获取指标基础监控采集配置
- **DescribeTopicMetricConfigs** — 获取指标主题的采集配置
- **QueryRangeMetric** — 指标范围查询（PromQL 语法）

### 5. 告警运维
- **DescribeAlarms** — 获取告警策略列表
- **DescribeAlertRecordHistory** — 获取告警历史记录
- **GetAlarmLog** — 获取告警策略执行详情
- **DescribeAlarmShields** — 获取告警屏蔽配置规则

---

## 执行方式

本 Skill 通过 `scripts/cls_api.py` 脚本直接调用腾讯云 CLS API。

### 前置条件

1. **安装 SDK**（首次使用时执行一次）：
```bash
pip3 install tencentcloud-sdk-python-cls
```

2. **设置环境变量**：
```bash
export TENCENTCLOUD_SECRET_ID="你的SecretId"
export TENCENTCLOUD_SECRET_KEY="你的SecretKey"
```

## ⚠️ 安全规则（必须遵守）

1. **绝对禁止**在命令行中明文传递 `TENCENTCLOUD_SECRET_ID` 或 `TENCENTCLOUD_SECRET_KEY`
2. 凭证只能通过**环境变量**读取，如果环境变量不存在，**必须停下来告诉用户手动设置**，不能替用户拼写到命令中
3. 如果需要设置环境变量，只能输出模板（不含真实值），引导用户自行填写
4. **排查/调试场景**：确认环境变量是否设置时，仅用 `[ -n "$TENCENTCLOUD_SECRET_ID" ] && echo "已设置"` 判断是否存在，**禁止使用 echo/printf/print 等命令输出凭证的实际值**，即使目的是调试或排查问题

### 调用语法

```bash
python3 scripts/cls_api.py <Region> <Action> '<JSON参数>'
```

- `Region`：地域代码，如 `ap-guangzhou`
- `Action`：API 接口名，如 `SearchLog`
- `JSON参数`：接口业务参数的 JSON 字符串

### 调用示例

```bash
# 检索日志
python3 scripts/cls_api.py ap-guangzhou SearchLog '{"TopicId":"xxx","From":1700000000000,"To":1700003600000,"QueryString":"level:ERROR","QuerySyntax":1,"Limit":10}'

# 获取日志主题列表
python3 scripts/cls_api.py ap-guangzhou DescribeTopics '{"Limit":20}'

# 获取机器组列表
python3 scripts/cls_api.py ap-guangzhou DescribeMachineGroups '{}'

# 获取告警策略
python3 scripts/cls_api.py ap-guangzhou DescribeAlarms '{"Limit":20}'

# 指标范围查询（PromQL）
python3 scripts/cls_api.py ap-guangzhou QueryRangeMetric '{"TopicId":"xxx","Query":"up","Start":1700000000,"End":1700003600,"Step":60}'
```

**脚本路径说明**：`scripts/cls_api.py` 位于本 Skill 目录下。执行时需 `cd` 到 Skill 目录，或使用绝对路径 `~/.workbuddy/skills/tencent-cls/scripts/cls_api.py`。

---

## 接口详细参数速查

### SearchLog（检索分析日志）

| 参数 | 必选 | 类型 | 说明 |
|------|:----:|------|------|
| TopicId | 是* | String | 日志主题 ID（与 Topics 二选一） |
| Topics.N | 是* | Array | 多主题检索（最多 50 个，与 TopicId 二选一） |
| From | 是 | Integer | 起始时间，**毫秒级 Unix 时间戳** |
| To | 是 | Integer | 结束时间，**毫秒级 Unix 时间戳** |
| QueryString | 否 | String | CQL 检索语句，最大 12KB，格式 `检索条件 \| SQL语句` |
| QuerySyntax | 否 | Integer | 0=Lucene 1=CQL（**推荐 1**） |
| Sort | 否 | String | asc/desc，默认 desc（仅无 SQL 时有效） |
| Limit | 否 | Integer | 返回条数，默认 100，最大 1000（仅无 SQL 时有效） |
| Offset | 否 | Integer | 偏移量翻页（仅无 SQL 时有效，与 Context 互斥） |
| Context | 否 | String | 游标翻页（仅无 SQL 时有效，过期 1 小时） |
| SamplingRate | 否 | Float | 统计分析采样率（0=自动，0~1指定，1=不采样） |
| UseNewAnalysis | 否 | Boolean | true 使用新返回格式（建议 true） |
| HighLight | 否 | Boolean | 是否高亮关键词（仅支持键值检索） |

**注意**：
- 单主题并发上限 **15**
- Context 翻页最多获取 **1 万条**
- From/To 是 **毫秒** 时间戳（不是秒）
- **SQL 分析时** Sort/Limit/Offset/Context 无效，请用 SQL 的 ORDER BY/LIMIT

### DescribeLogContext（上下文检索）

> ⚠️ **地域限制**：From/To 参数暂时仅支持上海、弗吉尼亚、新加坡地域。其他地域可能返回空结果。

| 参数 | 必选 | 类型 | 说明 |
|------|:----:|------|------|
| TopicId | 是 | String | 日志主题 ID |
| BTime | 是 | String | 日志时间，格式 `YYYY-mm-dd HH:MM:SS.FFF`（UTC+8） |
| PkgId | 是 | String | 日志包序号（来自 SearchLog 结果的 PkgId） |
| PkgLogId | 是 | Integer | 包内日志序号（来自 SearchLog 结果的 PkgLogId） |
| PrevLogs | 否 | Integer | 向前取的条数，默认 10 |
| NextLogs | 否 | Integer | 向后取的条数，默认 10 |
| Query | 否 | String | 过滤语句（仅检索条件，不支持 SQL） |

**替代方案**：不支持 DescribeLogContext 的地域，可用 SearchLog 按时间范围 + Sort 排序模拟上下文查询。

### DescribeTopics（获取日志主题列表）

| 参数 | 必选 | 类型 | 说明 |
|------|:----:|------|------|
| Filters.N | 否 | Array of Filter | 过滤条件：topicName/topicId/logsetId/tagKey/tag:tagKey/storageType(hot/cold) |
| Offset | 否 | Integer | 分页偏移，默认 0 |
| Limit | 否 | Integer | 分页大小，默认 20，最大 100 |
| PreciseSearch | 否 | Integer | 0=模糊匹配 1=topicName精确 2=logsetName精确 3=都精确，默认 0 |
| BizType | 否 | Integer | 0=日志主题 1=指标主题 |

> **限制**：Filters 上限 10，Filter.Values 上限 100

### DescribeLogsets（获取日志集列表）

| 参数 | 必选 | 类型 | 说明 |
|------|:----:|------|------|
| Filters.N | 否 | Array of Filter | 过滤条件：logsetName/logsetId/tagKey/tag:tagKey |
| Offset | 否 | Integer | 分页偏移，默认 0 |
| Limit | 否 | Integer | 分页大小，默认 20，最大 100 |

> **限制**：Filters 上限 10，Filter.Values 上限 5

### DescribeIndex（获取索引配置）

| 参数 | 必选 | 类型 | 说明 |
|------|:----:|------|------|
| TopicId | 是 | String | 日志主题 ID |

### DescribeRebuildIndexTasks（获取重建索引任务列表）

| 参数 | 必选 | 类型 | 说明 |
|------|:----:|------|------|
| TopicId | 是 | String | 日志主题 ID |
| TaskId | 否 | String | 索引重建任务 ID |
| Status | 否 | String | 任务状态，多种状态逗号分隔（0=已创建,1=创建资源中,2=已创建资源,3=重建中,4=暂停,5=完成,6=成功,7=失败,8=取消,9=已删除） |
| Offset | 否 | Integer | 分页偏移，默认 0 |
| Limit | 否 | Integer | 分页大小，默认 10，最大 20 |

### DescribeMachineGroups（获取机器组列表）

| 参数 | 必选 | 类型 | 说明 |
|------|:----:|------|------|
| Filters.N | 否 | Array of Filter | 过滤条件：machineGroupName/machineGroupId/osType(0=Linux,1=Windows)/tagKey/tag:tagKey |
| Offset | 否 | Integer | 分页偏移，默认 0 |
| Limit | 否 | Integer | 分页大小，默认 20，最大 100 |

> **限制**：Filters 上限 10，Filter.Values 上限 5

### DescribeMachines（获取机器状态）

| 参数 | 必选 | 类型 | 说明 |
|------|:----:|------|------|
| GroupId | 是 | String | 机器组 ID |
| Filters.N | 否 | Array of Filter | 过滤条件：ip/instance/version/status(0=离线,1=正常)/offlineTime(0/12/24/48/99) |
| Offset | 否 | Integer | 分页偏移，默认 0 |
| Limit | 否 | Integer | 分页大小，最大 100 |

> **限制**：Filters 上限 10，Filter.Values 上限 100

### DescribeConfigs（获取采集规则配置）

| 参数 | 必选 | 类型 | 说明 |
|------|:----:|------|------|
| Filters.N | 否 | Array of Filter | 过滤条件：configName/configId/topicId |
| Offset | 否 | Integer | 分页偏移，默认 0 |
| Limit | 否 | Integer | 分页大小，默认 20，最大 100 |

> **限制**：Filters 上限 10，Filter.Values 上限 5

### DescribeConfigMachineGroups（采集配置绑定的机器组）

| 参数 | 必选 | 类型 | 说明 |
|------|:----:|------|------|
| ConfigId | 是 | String | 采集配置 ID |

### DescribeMachineGroupConfigs（机器组绑定的采集配置）

| 参数 | 必选 | 类型 | 说明 |
|------|:----:|------|------|
| GroupId | 是 | String | 机器组 ID |

### DescribeLogHistogram（日志数量直方图）

| 参数 | 必选 | 类型 | 说明 |
|------|:----:|------|------|
| TopicId | 否 | String | 日志主题 ID |
| From | 是 | Integer | 起始时间，**毫秒级** Unix 时间戳 |
| To | 是 | Integer | 结束时间，**毫秒级** Unix 时间戳 |
| Query | 是 | String | 检索语句，使用 `*` 或空字符串查询所有 |
| Interval | 否 | Integer | 时间间隔，单位 ms。**限制：(To-From)/Interval ≤ 200** |
| SyntaxRule | 否 | Integer | 0=Lucene 1=CQL，默认 0 |

### GetMetricLabelValues（获取指标标签列表）

| 参数 | 必选 | 类型 | 说明 |
|------|:----:|------|------|
| TopicId | 是 | String | 指标主题 ID |
| LabelName | 是 | String | 标签名称 |
| Start | 否 | Integer | 起始时间，**秒级** Unix 时间戳 |
| End | 否 | Integer | 结束时间，**秒级** Unix 时间戳 |
| Match.N | 否 | Array of String | Label 匹配规则 |

### DescribeClusterBaseMetricConfigs（集群基础监控采集配置）

| 参数 | 必选 | 类型 | 说明 |
|------|:----:|------|------|
| GroupId | 是 | String | 机器组 ID |

### DescribeClusterMetricConfigs（集群指标采集配置）

| 参数 | 必选 | 类型 | 说明 |
|------|:----:|------|------|
| GroupId | 是 | String | 机器组 ID |

### DescribeHostMetricConfigs（主机指标采集配置列表）

| 参数 | 必选 | 类型 | 说明 |
|------|:----:|------|------|
| TopicId | 是 | String | 指标主题 ID |

### DescribeTopicBaseMetricConfigs（指标基础监控采集配置）

| 参数 | 必选 | 类型 | 说明 |
|------|:----:|------|------|
| TopicId | 是 | String | 指标主题 ID |

### DescribeTopicMetricConfigs（指标主题采集配置）

| 参数 | 必选 | 类型 | 说明 |
|------|:----:|------|------|
| TopicId | 是 | String | 指标主题 ID |

### QueryRangeMetric（指标范围查询）

| 参数 | 必选 | 类型 | 说明 |
|------|:----:|------|------|
| TopicId | 是 | String | 指标主题 ID |
| Query | 是 | String | PromQL 查询语句 |
| Start | 是 | Integer | 起始时间，**秒级** Unix 时间戳 |
| End | 是 | Integer | 结束时间，**秒级** Unix 时间戳 |
| Step | 是 | Integer | 查询间隔，单位秒 |

### DescribeAlarms（获取告警策略列表）

| 参数 | 必选 | 类型 | 说明 |
|------|:----:|------|------|
| Filters.N | 否 | Array of Filter | 过滤：name/alarmId/topicId/enable |
| Offset | 否 | Integer | 分页偏移，默认 0 |
| Limit | 否 | Integer | 分页大小，默认 20，最大 100 |

### DescribeAlertRecordHistory（获取告警历史）

| 参数 | 必选 | 类型 | 说明 |
|------|:----:|------|------|
| From | 是 | Integer | 起始时间，**毫秒级** Unix 时间戳 |
| To | 是 | Integer | 结束时间，**毫秒级** Unix 时间戳 |
| Offset | 是 | Integer | 分页偏移，默认 0 |
| Limit | 是 | Integer | 分页大小，默认 20，最大 100 |
| Filters.N | 否 | Array of Filter | 过滤条件：alertId/topicId/status(0=未恢复,1=已恢复,2=已失效)/alarmLevel(0=警告,1=提醒,2=紧急) |

> **限制**：Filters 上限 10，Filter.Values 上限 100

### GetAlarmLog（获取告警策略执行详情）

| 参数 | 必选 | 类型 | 说明 |
|------|:----:|------|------|
| From | 是 | Integer | 起始时间，**毫秒级** Unix 时间戳 |
| To | 是 | Integer | 结束时间，**毫秒级** Unix 时间戳 |
| Query | 是 | String | 查询语句 |
| Limit | 否 | Integer | 返回条数，默认 100，最大 1000 |
| Sort | 否 | String | asc/desc，默认 desc |
| Context | 否 | String | 翻页游标 |

> **Query 可用字段**：`alert_id`（告警ID，注意是下划线非驼峰）、`alert_name`、`topic_name`、`status`、`process_result`、`trigger_result`

### DescribeAlarmShields（获取告警屏蔽规则）

| 参数 | 必选 | 类型 | 说明 |
|------|:----:|------|------|
| AlarmNoticeId | 是 | String | 通知渠道组 ID |
| TaskId | 否 | String | 屏蔽规则 ID |
| Filters.N | 否 | Array of Filter | 过滤条件 |
| Offset | 否 | Integer | 分页偏移，默认 0 |
| Limit | 否 | Integer | 分页大小，默认 20，最大 100 |

---

## CQL 语法速查

CQL（CLS Query Language）是 CLS 推荐的日志检索语法。

### 基本语法

```
# 全文检索
ERROR

# 键值检索
level:ERROR
status:>=400

# 逻辑运算
level:ERROR AND service:nginx
level:ERROR OR level:WARN
NOT level:DEBUG

# 模糊匹配
message:*timeout*
host:192.168.1.*

# 范围查询
status:[400 TO 500}    // 左闭右开
latency:>1000

# 存在性检查
_EXIST_:error_code
NOT _EXIST_:trace_id
```

### SQL 分析

```
# 检索 + SQL 分析
* | SELECT status, COUNT(*) AS cnt GROUP BY status ORDER BY cnt DESC LIMIT 10

# 带条件
level:ERROR | SELECT service, COUNT(*) AS err_count GROUP BY service

# 时间函数
* | SELECT histogram(cast(__TIMESTAMP__ as timestamp), interval 5 minute) AS t, COUNT(*) AS cnt GROUP BY t ORDER BY t
```

---

## 常用地域代码

| 地域 | Region |
|------|--------|
| 广州 | ap-guangzhou |
| 上海 | ap-shanghai |
| 北京 | ap-beijing |
| 成都 | ap-chengdu |
| 重庆 | ap-chongqing |
| 南京 | ap-nanjing |
| 中国香港 | ap-hongkong |
| 新加坡 | ap-singapore |
| 硅谷 | na-siliconvalley |
| 弗吉尼亚 | na-ashburn |
| 法兰克福 | eu-frankfurt |
| 东京 | ap-tokyo |

---

## 工作流指引

### 日志排障流程

1. **确定目标**：先用 `DescribeTopics` 找到目标日志主题 ID
2. **检索日志**：用 `SearchLog` + CQL 语法定位问题日志
3. **查看上下文**：对关键日志用 `DescribeLogContext` 查看前后上下文
4. **统计分析**：用 `SearchLog` 的 SQL 功能进行聚合分析
5. **查看分布**：用 `DescribeLogHistogram` 查看时间分布趋势

### 采集排障流程

1. **查机器组**：`DescribeMachineGroups` 列出机器组
2. **查机器状态**：`DescribeMachines` 检查机器是否在线
3. **查采集配置**：`DescribeConfigs` 或 `DescribeMachineGroupConfigs` 查看绑定的采集规则
4. **查绑定关系**：`DescribeConfigMachineGroups` 确认采集配置已绑到正确的机器组

### 告警排障流程

1. **查策略**：`DescribeAlarms` 获取告警策略列表
2. **查历史**：`DescribeAlertRecordHistory` 查看告警触发/恢复记录
3. **查执行详情**：`GetAlarmLog` 深入分析告警执行日志
4. **查屏蔽规则**：`DescribeAlarmShields` 检查是否被屏蔽

---

## 时间戳注意事项

⚠️ **不同接口使用的时间精度不同**：

| 精度 | 接口 |
|------|------|
| **毫秒** | SearchLog, DescribeLogHistogram, DescribeLogContext(From/To), DescribeAlertRecordHistory, GetAlarmLog |
| **秒** | QueryRangeMetric, GetMetricLabelValues |
| **字符串** | DescribeLogContext.BTime（格式 `YYYY-mm-dd HH:MM:SS.FFF`） |

生成时间戳时务必使用 Shell 命令计算，不要手动计算。


