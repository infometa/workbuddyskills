# LogBus2 Usage Guide

> **Terminology**: 日志同步工具 = log sync tool | 数据格式转换 = data format conversion | 数据源 = data source | 磁盘空间 = disk space | 本地磁盘队列 = local disk queue | Kafka = Kafka message queue | 文件存放目录 = file storage directory | 传输速度 = transfer speed | 内存占用 = memory usage | 数据分流 = data routing (to multiple projects) | 神策数据 = Sensors Analytics data format | CPU 限制 = CPU limit | 带宽占用 = bandwidth usage | 网络条件 = network conditions | 磁盘 IO = disk IO | 监听文件 = watched/monitored files | 重试 = retry | 断点续传 = resume from breakpoint | 数据校验 = data validation | 黑名单 = blacklist (filter out events/properties) | 白名单 = whitelist (filter in events/properties) | 字段过滤 = field filtering | 数据脱敏 = data masking

## 一、简介

LogBus2 是数数科技在原 LogBus 基础上，使用 Go 语言重新开发的日志同步工具。相比 LogBus1，具有以下优势：

- **内存占用更低**：减少至原先的五分之一（约 100-200M）
- **传输速度更快**：提升至 3-5万条/秒
- **运行更稳定**：logbus1在一些特殊场景下，文件缓存区修复难度较高
- **部署更简单**：无需 JDK 环境，直接运行

## 二、使用前准备

1. **数据格式转换**：将需要传输的数据转换成 TE 的数据格式，支持 TA 格式和神策格式
2. **确定数据源**：确定文件存放目录或 Kafka 地址与 topic
3. **磁盘空间**：相比 LogBus1，LogBus2 去掉了本地磁盘队列，磁盘占用更小

## 三、应用场景

- 使用数数服务端 SDK 中 LogConsumer 模式的用户
- 对数据准确性及维度要求较高的场景
- 需要传输大批量历史数据
- 需要数据分流到多个项目的场景
- 需要对接神策数据的场景

## 四、性能指标

| 指标 | 说明 |
|------|------|
| 传输速度 | 3-5万条/秒（单个LogBus） |
| 内存占用 | 约 100-200M |
| CPU 限制 | 支持 cpu_limit 配置 |
| 带宽占用 | 峰值约 70Mbps |

> 传输效率受网络条件、磁盘 IO、系统分配资源、监听文件数量等因素影响。

## 五、支持环境

| 操作系统 | 架构 | 说明 |
|----------|------|------|
| Linux | amd64 | 推荐 |
| Linux | arm64 | 支持 |
| Windows | amd64 | 支持 |
| macOS | amd64 | 支持 |
| Docker | - | 宿主机持久化 |
| K8S | - | 支持 Helm 部署 |

下载地址：[官网下载](https://docs-v2.thinkingdata.cn/?version=latest&code=logbus2_installation&lan=en-US)

## 六、配置指南

### 文件数据源配置

```json
{
    "push_url": "http://RECEIVER_URL",
    "cpu_limit": 4,
    "datasource": [
        {
            "type": "file",
            "file_patterns": ["/data/log/*.log"],
            "app_id": "your_app_id",
            "http_compress": "gzip",
            "unit_remove": "day",
            "offset_remove": 7
        }
    ]
}
```

### Kafka 数据源配置

```json
{
    "datasource": [
        {
            "type": "kafka",
            "topic": "topic1,topic2",
            "consumer_group": "consumer_group_name",
            "brokers": ["localhost:9092"],
            "auto_commit": false,
            "app_id": "your_app_id"
        }
    ],
    "push_url": "http://RECEIVER_URL"
}
```

### 多项目数据分流配置

```json
{
    "datasource": [
        {
            "file_patterns": ["/data/log/*.log"],
            "app_id": "default_app_id",
            "app_pipe": {
                "attribute": "#lib_version",
                "id_map": {
                    "app_id_1": "1.0.0",
                    "app_id_2": "2.0.0"
                },
                "default": "app_id_1"
            }
        }
    ],
    "push_url": "http://RECEIVER_URL"
}
```

### 告警配置

```json
{
    "alert": {
        "enabled": true,
        "receiver": "feishu_robot",
        "extra": "logbus_instance_1",
        "out_cfg": {
            "feishu_robot_hook": "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
        }
    }
}
```

## 七、常用操作命令

### 环境检查

```bash
./logbus env
```

### 启动服务

```bash
./logbus start
```

### 停止服务

```bash
./logbus stop
```

### 查看同步进度

```bash
./logbus progress
```

### 升级版本

```bash
./logbus stop
./logbus update
./logbus start
```

### 查看传输速度

查看 `logbus/log/transporter.log` 确认发送效率。

## 八、配置参数详解

### 全局配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| push_url | string | - | Receiver 地址，必填 |
| cpu_limit | int | - | CPU 核心限制 |
| ignore_app_id_verify | bool | false | 是否跳过 appid 和 push_url 校验 |

### 数据上报配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| batch | int | 1000 | 数据发送条数条件，最小10，最大100000 |
| interval_seconds | int | 2 | 数据发送时间间隔，最大60秒 |
| send_thread_num | int | 3 | 数据上报线程数 |
| http_timeout | string | 30s | HTTP 请求超时时间 |
| http_compress | string | - | HTTP 压缩协议，支持 gzip/snappy |

### 文件数据源配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| file_patterns | []string | - | 文件 glob 匹配模式，必填 |
| traverse_dir_interval | string | 30s | 扫描目录间隔时间 |

### Kafka 数据源配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| topic | string | - | Kafka topic，支持多 topic（逗号分隔） |
| brokers | []string | - | Kafka broker 地址 |
| consumer_group | string | - | 消费者组 |
| auto_commit | bool | false | 是否自动提交 |
| protocol | string | none | 认证协议：plain/scramsha256/scramsha512/iam/none |
| fetch_count | int | 1000 | 一次性拉取数据条数 |

### 文件删除配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| offset_remove | int | - | 删除周期 |
| unit_remove | string | d | 删除单位：d(天)/h(小时) |
| RemoveDirs | bool | false | 是否删除文件夹，不建议配置，可能导致服务端写入异常 |

## 九、注意事项

### 文件操作相关

> **禁止对 LogBus 监听的文件进行重命名操作**，否则会导致数据丢失或数据重复。

### 监听文件要求

- LogBus 监听路径下文件必须是纯净的数据文件
- 不能有 gz/.iso/.rpm/.zip/.bz/.rar/.bz2 后缀的文件
- LogBus-v2 默认会绕过这些文件

### 多实例运行

- 可运行多个 LogBus，但多个 LogBus 不能监听相同路径下的文件上报到同一个项目

### Kafka 消费优化

- 消费者线程数建议与分区数相等
- 避免单个 LogBus 消费 hash 模余结果一致的分区
- 可通过增加分区数和 LogBus 消费者数来加快消费

### 数据补报注意事项

- 如果是历史数据，建议开启历史通道
- 及时关注 Kafka 集群是否有数据积压
- 补数据建议发送到单独的 topic，避免与正式数据混淆

## 十、常见问题

### 如何确认网络是否通畅？

```bash
curl 数据接收地址/health-check
```

### 如何确认 APPID 是否正确？

```bash
curl "数据接收地址/check_appid?appid=目标APPID"
```

返回 `{"code":0}` 即为正常。

### 数据重复的原因？

1. 是否对已同步完成的文件进行重命名
2. 源数据文件中数据是否有重复
3. 是否执行了 reset 操作

### 传输较慢怎么办？

1. 调大 `send_thread_num` 发送线程数
2. 开启 HTTP 压缩：`http_compress: "gzip"`
3. 检查网络延迟、带宽，建议 LogBus 与 Receiver 在同一内网
4. 检查是否有限制 CPU、内存

### Kafka 消费较慢怎么办？

1. 增加 LogBus 实例
2. 调大单个 LogBus 的 `send_thread_num`
3. 增加分区数
4. 最佳策略：LogBus 消费者线程数 = 分区数

### 读取策略差异导致上报延迟？

如果服务端数据存在多进程同时写入数据到不同文件的情况，logbus2老版本会出现串行读取的情况，导致部分实时写入的文件没有实时上报，新版本已兼容此场景。

```bash
# 停止 LogBus
./logbus stop

# 升级 LogBus
./logbus update

# 重启 LogBus
./logbus start
```

## 十一、最佳实践建议

### 部署建议

1. **资源规划**：根据数据量合理配置 CPU 和内存
2. **网络优化**：LogBus 与 Receiver 部署在同一内网
3. **监控告警**：配置告警通知，及时发现异常

### 配置建议

1. **压缩传输**：建议开启 gzip 压缩，减少网络传输量
2. **文件清理**：配置自动删除策略，避免磁盘空间不足
3. **线程配置**：根据数据量调整发送线程数

### 运维建议

1. **版本升级**：定期关注发版记录，及时升级
2. **日志留存**：合理配置日志留存时间
3. **进程监控**：对 LogBus 进程进行监控