# 一、环境配置

```shell
#下载
pip(3) install ThinkingDataSdk
#更新
pip(3) install --upgrade ThinkingDataSdk
```

Python SDK 最低兼容 Python 2.7.5、建议使用 2.7.9 以上版本，以下基于SDK版本2.1.3进行说明。

#### demo

```python
from tgasdk.sdk import *

#运行日志开关，默认False
TGAnalytics.enableLog(True)
#初始化
consumer = LoggingConsumer(log_directory="/Users/blank/Downloads/pytest")
# consumer = BatchConsumer(server_uri="上报地址", appid="项目appid")
# consumer = AsyncBatchConsumer(server_uri="上报地址", appid="项目appid")
# consumer = DebugConsumer(server_uri="上报地址", appid="项目appid", device_id="123456789")
te = TGAnalytics(consumer)
#数据上报
account_id = "11111"  # 账户id
distinct_id = "ABD"  # 访客id
testProperties = {
    "#time": datetime.datetime.now(),  # 设置事件时间，不填默认取当前时间
    "#ip": "123.123.123.123",  # 设置ip，默认不上报
    "#zone_offset": 8,  # 设置时区
    "a": "123",  # 文本
    "b": 123,  # 数值
    "c": False,  # 布尔
    "e": datetime.datetime.now(),  # 时间
    "f": ["123", "123"],  # 列表
    "g": {  # 对象
        "g1": "123",  # 对象内只识别普通属性，如果嵌套对象/对象组对应属性最终以文本入库
    },
    "h": [  # 对象组
        {
            "h1": "123",  # 对象组内每个对象只识别普通属性，如果嵌套对象/对象组对应属性最终以文本入库
        },
        {
            "h1": "321",
        }
    ],
}

try:
    # 上报用户属性
    te.user_set(account_id=account_id, distinct_id=distinct_id, properties=testProperties)
    # 上报事件名为test的事件
    te.track(account_id=account_id, distinct_id=distinct_id, event_name="test", properties=testProperties)
except Exception as e:
    raise TGAIllegalDataException(e)

te.flush()
# te.close()  # 关闭sdk前自动调用flush()
```

# 二、工作原理

#### **Python SDK支持几种工作模式？分别适用于什么场景？**

Python SDK 支持以下四种工作模式：

1. **LoggingConsumer** 批量实时将数据写入本地文件，文件可以按每天、每小时或指定文件大小分割，需要搭配 LogBus 上报数据。优点在于数据的储存与上报解耦，数据持久化存储不容易丢失；缺点在于需要另外部署 LogBus 进行上报，LogBus会占用一部分系统资源。
2. **BatchConsumer** 批量实时地向TA服务器传输数据，不需要搭配上报工具。优点在于使用简单无需搭配上报工具；缺点在于数据没有持久化存储，仅在内存中做缓存，如果网络不稳定缓存数据超过缓存区上限后会丢失数据。
3. **AsyncBatchConsumer** 异步批量实时地向TA服务器传输数据，其余同BatchConsumer
4. **DebugConsumer** 逐条发送数据，服务端会对数据进行严格校验，当某个属性不符合规范时整条数据都不会入库，当数据格式错误时会打印详细错误信息。DebugConsumer 推荐在开发调试阶段使用，禁止生产环境使用。

#### **如何获取上报地址和APP_ID？**

项目管理者可以在数数WEB界面，选择具体项目后，进入项目管理 - 项目配置 - 接入配置界面获取项目appid。上报地址分为公网地址和私网地址，其中公网地址适用于客户端数据上报，以及公网环境下的服务端数据接入，如在公网设置上报域名，则咨询做该配置的运维工程师；私网地址适用于内网环境下的数据接入和测试，内网上报地址为集群每个节点的8991端口。

#### **LoggingConsumer的工作原理是什么？有哪些配置参数？**

原理：上报操作会先写入缓存，大于buffer_size（默认5条）才会写入磁盘，不满足写入条件时想要将数据写入文件需要自行调用flush方法。可多线程执行但本身是同步方法，多线程也要等锁执行反而浪费性能。写入文件时会加文件锁所以不能多进程写入同一个文件。

LoggingConsumer 常用配置参数如下表：

| 参数 | 描述 | 默认值 | 参数类型 | 是否必填 | 备注 |
|------|------|--------|----------|----------|------|
| log_directory | 日志文件路径 | - | String | 是 | 多级目录会自动创建 |
| rotate_mode | 日志按时间切分 | DAILY | Enum | 否 | Enum('ROTATE_MODE', ('DAILY', 'HOURLY')) |
| file_prefix | 日志文件名前缀 | 空 | String | 否 | 多实例时填写防止多进程写入同一个文件报错 |
| log_size | 日志按大小切分 | 0 | Integer | 否 | 单位为MB，值为0时不切分，不建议使用 |
| buffer_size | 缓存大小 | 5 | Integer | 否 | 单位为条，超过时从内存写到日志 |

#### **BatchConsumer的工作原理是什么？有哪些配置参数？**

原理：上报操作会写入缓存，当上报数据数量大于batch（默认20）或因网络通信失败等问题未上报数据导致cache_buffer不为空时调用flush，不满足条件需要自行调用flush方法。如果通信失败会存入cache_buffer，长时间通信失败导致 未成功发送总条数 / batch大于max_cache_size时会丢弃最早的batch条数据。

BatchConsumer 常用配置参数如下表：

| 参数 | 描述 | 默认值 | 参数类型 | 是否必填 | 备注 |
|------|------|--------|----------|----------|------|
| server_uri | 上报地址 | - | String | 是 | |
| appid | 项目appid | - | String | 是 | |
| batch | 批次大小，达到阈值触发数据上报 | 20 | Integer | 否 | 最大200 |
| timeout | http请求超时时长 | 30000 | Integer | 否 | 单位为毫秒 |
| compress | 数据是否压缩 | True | Boolean | 否 | |
| max_cache_size | 内存保留数据批次数 | 50 | Integer | 否 | |

#### **AsyncBatchConsumer的工作原理是什么？有哪些配置参数？**

原理：上报操作会写入缓存，当上报数据数量大于flush_size或每隔interval秒调用flush。flush时如果通信失败会重试3次，依旧失败会放回队列等下次上报，长时间通信失败导致超出 queue_size时会丢弃最早的flush_size条数据。

AsyncBatchConsumer 常用配置参数如下表：

| 参数 | 描述 | 默认值 | 参数类型 | 是否必填 | 备注 |
|------|------|--------|----------|----------|------|
| server_uri | 上报地址 | - | String | 是 | |
| appid | 项目appid | - | String | 是 | |
| interval | 数据上报间隔 | 3 | Integer | 否 | 单位为秒 |
| flush_size | 批次大小，达到阈值触发数据上报 | 20 | Integer | 否 | |
| queue_size | 发送线程队列大小 | 100000 | Integer | 否 | 单位为条 |

#### **DebugConsumer的工作原理是什么？有哪些配置参数？**

原理：每条数据都直接走http请求上报数据，不用调flush。数据格式会进行严格校验。

DebugConsumer 常用配置参数如下表：

| 参数 | 描述 | 默认值 | 参数类型 | 是否必填 | 备注 |
|------|------|--------|----------|----------|------|
| server_uri | 上报地址 | - | String | 是 | |
| appid | 项目appid | - | String | 是 | |
| timeout | http请求超时时长 | 30000 | Integer | 否 | 单位为ms |
| write_data | 数据是否入库 | True | Boolean | 否 | |
| device_id | 设备ID | 空 | String | 否 | |

# 三、常见问题

#### **使用 LoggingConsumer 有哪些注意事项？**

- **搭配Logbus上报**
  - LoggingConsumer + LogBus为数数标准的数据上报方案，LoggingConsumer使得数据持久化，数据得到不丢失的保障；LogBus为数据传输作保证，同时将数据持久化和上报解耦。
- **文件写权限**
  - 写入日志目录需要有写入和读取的权限，通常Windows环境会有写入权限问题。
- **磁盘空间**
  - 磁盘空间保证充裕，并可以合理在LogBus上配置删除策略。
- **磁盘性能NFS情况**
- **UUID**
  - 建议添加UUID，防止网络抖动及极端情况造成数据重复，但会稍微消耗效率，也可在LogBus侧打开。
- **多进程写不同文件**
  - 支持多进程写不同文件，但要保证不同进程的处理逻辑没有依赖关系（如不同服务器的用户行为写到不同日志）
- **容器环境**
  - 将数据写入路径映射到外部磁盘，防止容器关闭数据文件丢失

#### **LoggingConsumer 是否支持多线程？是否支持多进程？**

支持多线程，不支持多进程写同一个文件。

#### **LoggingConsumer 性能指标如何？**

4C16G下2w/s，不同平台不同Python版本有上下浮动

#### **LoggingConsumer 是否存在丢数风险？如何避免？**

如果磁盘写满或者服务器宕机可能导致数据丢失，建议：

1. 定期检查写入日志路径磁盘剩余容量
2. 降低buffer_size参数值，增加内存刷写频率，但会导致频繁IO，需结合具体场景综合考虑

#### **BatchConsumer 为什么会存在丢数风险？如何避免？**

`BatchConsumer`在内存中维护了两个队列，一个batch 大小的队列负责存放单批次数据，一个batch*max_cache_size大小的队列负责存放因为网络原因发送失败的批次数据队列。因为`BatchConsumer`基于内存存储，所以当发生内存溢出或者服务器宕机时，内存中未发送的数据会全部丢失，建议：

1. 使用LoggingConsumer + LogBus搭配进行数据上报
2. 提高max_cache_size参数值大小，在网络发生异常导致数据发送失败时，可以在内存中存储更多的数据，但是会导致服务器内存使用值增加，需结合具体场景综合考虑
3. batch参数不宜设置过大，可能会导致单次发送数据时间增加，会增加发生网络错误的概率

#### **BatchConsumer 性能指标如何？适合在什么场景下使用？**

内网环境下适合在并发数据量较低、保证网络的环境下使用（比如与TE集群内网打通）。

#### **DebugConsumer 为什么在生产环境禁用？**

DebugConsumer上传数据时，每条数据都会进行post发送，生产环境使用会频繁创建连接影响效率。

#### **什么时候需要调用 `close()` 方法？**

程序需要正常结束时调用，close()方法会将内存中的数据进行写入文件或发送。

#### **在程序中调用了 `track()` 或者 `user_set()` 方法， 为什么在 TE 后台没有看到数据？**

请依次检查以下情况：

- 检查上报地址和appid
- 数据太少，未触发上报
- 错误数据
- 数据时间
- 历史通道
- 埋点方案

#### **上报数据中为什么没有 "#ip"？**

服务端的#ip需要单独上报，层级与#distinct_id、#event_name、#time、properties等同级。

# 四、预置属性、特殊类型上报

#### **Python SDK 如何上报对象和对象组类型？**

Python SDK 1.7.0及以上版本支持上报对象和对象组类型，代码示例请参考服务端SDK复杂类型上报。

#### **公共属性**

服务端的公共属性无法精确到用户级，在多线程情况下报了用户级属性数据可能会导致用户数据对不上。仅建议在公共属性内放区服id等不会产生大变化的字段，其余均放入普通属性。

#### **时区**

默认时区以数数服务器为准，如果要实现时区偏移需上报#zone_offset字段。假设填0且事件时间为2023-04-17 01:02:03，偏移到东八区会以事件时间2023-04-17 09:02:03进行分析。

# 五、异常报错

1. **Pip 安装 Python SDK 失败，报错："ERROR: Could not find a version that satisfies the requirement ThinkingDataSdk (from version: none) ERROR: No matching distribution found for ThinkingDataSdk"**

这是pip安装的常见问题，通常可以通过升级 pip 版本或更改 pip 源解决。

2. **调用 user_set() 报错："error = year=1899 is before 1900; the datetime strftime() methods require year >= 1900"**

Python SDK 里用 strftime() 函数做时间转换，不支持1900年之前的时间。

3. **调用 track() 报错："gevent.Hub.LoopExit: This operation would block forever"**

这个是客户使用了Python三方库gevent的报错，网上有很多相关资料和方案，可以协助客户分析，不属于Python SDK的异常。

4. **BatchConsumer上报报错："Data transmission failed due to ConnectionError(ProtocolError('Connection aborted.', BadStatusLine('No status line received - the server has closed the connection',)),)"**

这个报错来自 Python SDK 用于网络请求的内部类 _HttpServices 的 send() 函数，通常由于网络抖动导致。BatchConsumer 的 __cache_buffer 缓存区不会移除上报失败的数据，会在下一次继续上报，所以网络抖动不会导致数据丢失。