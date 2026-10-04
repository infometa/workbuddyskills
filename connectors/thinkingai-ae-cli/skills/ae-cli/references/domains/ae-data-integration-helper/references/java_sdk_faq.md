# 一、环境配置

当前文档统一按 Java SDK v3.x 新 API 编写，示例面向技术开发人员，可直接作为接入模板参考。已过期：`cn.thinkingdata.tga.javasdk` 包、`ThinkingDataAnalytics` / `LoggerConsumer` / `BatchConsumer` / `DebugConsumer` 类，以及 `user_set`、`user_add`、`track_first`、`track_update`、`track_overwrite` 等 snake_case 方法。根据参考文档的更新日志，截至 2026-01-07 最新发布版本为 v3.0.4-beta.1；其中 fastjson1、lzo、lz4 已不再支持。生产环境请优先固定已验证版本，并在升级前对照更新日志完成回归验证。

Java SDK 最低兼容 JDK 8。Java 的常用 IDE 有 **IntelliJ IDEA**、**Eclipse**、**NetBeans** 等，本文示例使用 **IntelliJ IDEA**。使用 Maven 集成 SDK，请在 `pom.xml` 中添加依赖。若需最新版本，请以官方文档或更新日志为准：

```xml
<dependencies>
    <!-- others... -->
    <dependency>
        <groupId>cn.thinkingdata</groupId>
        <artifactId>thinkingdatasdk</artifactId>
        <version>3.0.2</version>
    </dependency>
</dependencies>
```

#### TDLoggerConsumer 样例代码

```java
import cn.thinkingdata.analytics.TDAnalytics;
import cn.thinkingdata.analytics.TDLoggerConsumer;

import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class LoggerExample {
    public static void main(String[] args) {
        TDAnalytics ta = null;
        try {
            // 初始化 SDK，LOG_DIRECTORY 为本地日志目录
            ta = new TDAnalytics(new TDLoggerConsumer("LOG_DIRECTORY"), true);

            Map<String, Object> properties = new HashMap<>();
            properties.put("#ip", "192.168.1.1");
            properties.put("channel", "te");
            properties.put("age", 1);
            properties.put("is_success", true);
            properties.put("birthday", new Date());

            Map<String, Object> object = new HashMap<>();
            object.put("key", "value");
            properties.put("object", object);

            List<Map<String, Object>> objectArray = new ArrayList<>();
            objectArray.add(object);
            properties.put("object_arr", objectArray);

            List<String> tags = new ArrayList<>();
            tags.add("value");
            properties.put("arr_string", tags);

            ta.track("account_id", "distinct_id", "payment", properties);

            Map<String, Object> userProperties = new HashMap<>();
            userProperties.put("user_name", "TE");
            ta.userSet("account_id", "distinct_id", userProperties);

            // 仅在需要立即落盘时调用，避免高频 flush 带来额外 IO 开销
            ta.flush();
        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            if (ta != null) {
                try {
                    ta.close();
                } catch (Exception e) {
                    e.printStackTrace();
                }
            }
        }
    }
}
```

#### TDBatchConsumer 样例代码

```java
import cn.thinkingdata.analytics.TDAnalytics;
import cn.thinkingdata.analytics.TDBatchConsumer;

import java.util.Date;
import java.util.HashMap;
import java.util.Map;

public class BatchExample {
    public static void main(String[] args) {
        TDAnalytics ta = null;
        try {
            ta = new TDAnalytics(new TDBatchConsumer("SERVER_URL", "APP_ID"));

            String distinctId = "ABCDEFG123456789";
            String accountId = "TA_10001";

            Map<String, Object> properties = new HashMap<>();
            properties.put("#time", new Date());
            properties.put("#ip", "192.168.1.1");
            properties.put("product_name", "商品A");
            properties.put("price", 30);
            properties.put("order_id", "abc_123");

            ta.track(accountId, distinctId, "payment", properties);

            // Batch 模式通常依赖批量阈值或定时机制触发发送
            ta.flush();
        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            if (ta != null) {
                try {
                    ta.close();
                } catch (Exception e) {
                    e.printStackTrace();
                }
            }
        }
    }
}
```

#### TDDebugConsumer 样例代码

```java
import cn.thinkingdata.analytics.TDAnalytics;
import cn.thinkingdata.analytics.TDDebugConsumer;

import java.util.HashMap;
import java.util.Map;

public class DebugExample {
    public static void main(String[] args) {
        TDAnalytics ta = null;
        try {
            TDAnalytics.enableLog(true);
            ta = new TDAnalytics(new TDDebugConsumer("SERVER_URL", "APP_ID", "DEBUG_DEVICE_ID"));

            Map<String, Object> properties = new HashMap<>();
            properties.put("product_name", "shoes");
            properties.put("price", 199);

            ta.track("account_id", "distinct_id", "payment", properties);
        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            if (ta != null) {
                try {
                    ta.close();
                } catch (Exception e) {
                    e.printStackTrace();
                }
            }
        }
    }
}
```

> 开启 Debug 模式需要两步：
> 1. 在代码中使用 `TDDebugConsumer` 并传入 `DEBUG_DEVICE_ID`。
> 2. 在 TE 后台"数据 > 埋点管理 > Debug 数据"中配置同一个 Debug 设备 ID。只有已配置的设备才能真正开启 Debug 模式。

# 二、工作原理

#### **Java SDK支持几种工作模式？分别适用于什么场景？**

Java SDK v3.x 常见的三种工作模式如下：

1. **TDLoggerConsumer**：将数据批量写入本地日志，再由 LogBus 负责传输。适合生产环境、需要更高可恢复性和更稳妥丢数控制的场景，也是官方更推荐的服务端接入方案。
2. **TDBatchConsumer**：直接批量发送数据到 TA 服务端，接入简单，但缓存仅保存在内存中。适合中小流量、网络质量稳定、可以接受一定重试与缓存上限约束的场景。
3. **TDDebugConsumer**：逐条发送并进行严格校验，便于接入验证和实时调试。仅建议在开发调试阶段使用，严禁用于生产环境。

#### **如何获取上报地址和APP_ID？**

项目管理者可以在数数 Web 界面选择具体项目后，进入"项目管理 > 项目配置 > 接入配置"获取 APP_ID 及数据上报地址。上报地址通常分为公网地址和私网地址：

- 公网地址：适用于客户端上报，以及公网环境下的服务端接入。
- 私网地址：适用于内网环境下的数据接入和测试。如果使用私有化部署，建议为数据接入地址绑定域名并配置 HTTPS 证书；如果是云服务，请直接使用平台提供的接入地址。

#### **LoggerConsumer的工作原理是什么？有哪些配置参数？**

v3.x 对应实现为 `TDLoggerConsumer`。事件先写入内存缓存，达到阈值后再刷写到本地日志文件；若开启自动刷新，也会按固定时间间隔刷写。该模式线程安全，但单个实例的调用默认是同步的；如果多个线程频繁竞争同一个实例，吞吐提升通常有限。生产环境中推荐配合 LogBus 使用，将"落盘"和"上传"解耦。

`TDLoggerConsumer.Config` 常用参数如下：

| 参数 | 描述 | 默认值 | 取值范围 | 备注 |
|------|------|--------|----------|------|
| `logDirectory` | 日志文件写入目录 | 无 | 字符串 | 多级目录会自动创建 |
| `rotateMode` | 日志切分模式 | `DAILY` | `HOURLY`、`DAILY` | 按小时或按天切分 |
| `lockFileName` | 文件锁名称 | 无 | 字符串 | 如无明确需求，不建议启用 |
| `filenamePrefix` | 日志文件名前缀 | 无 | 字符串 | 便于多实例或多业务区分文件 |
| `interval` | 自动 flush 间隔 | `3` | 整数 | 与 `autoFlush` 配合使用，单位秒 |
| `fileSize` | 文件大小切分阈值 | `0` | 整数 | 单位 MB，`0` 表示不按大小切分 |
| `bufferSize` | 内存缓冲区大小 | `8192` | 整数 | 单位字节 |
| `autoFlush` | 是否自动刷写 | `false` | 布尔值 | 仅在确有实时性要求时开启 |

#### **BatchConsumer的工作原理是什么？有哪些配置参数？**

v3.x 对应实现为 `TDBatchConsumer`。事件先写入内存队列，满足批量阈值或触发 `flush()` 时再发送到服务端；网络发送失败会进入重试与缓存逻辑。它的优点是接入简单，不依赖 LogBus；缺点是缓存只存在于内存中，服务异常退出或长时间网络问题都可能导致数据丢失，因此不建议作为高可靠生产方案的首选。

`TDBatchConsumer.Config` 常用参数如下：

| 参数 | 描述 | 默认值 | 取值范围 | 备注 |
|------|------|--------|----------|------|
| `batchSize` | 单批发送条数阈值 | `20` | 整数 | 达到阈值后触发发送 |
| `interval` | 自动发送间隔 | `3` | 整数 | 与 `autoFlush` 配合使用，单位秒 |
| `compress` | 数据压缩格式 | `gzip` | `gzip`、`none` | `lzo`、`lz4` 已在新版本中不再支持 |
| `timeout` | 网络请求超时时长 | `30000` | 整数 | 单位毫秒 |
| `autoFlush` | 是否自动发送 | `false` | 布尔值 | 根据业务实时性要求开启 |
| `maxCacheSize` | 失败批次缓存上限 | `50` | 整数 | 默认最多缓存 `20 * 50` 条数据 |
| `isThrowException` | 发送失败时是否抛异常 | `true` | 布尔值 | 建议保留默认值，便于业务侧感知风险 |

#### **DebugConsumer的工作原理是什么？有哪些配置参数？**

旧版 `DebugConsumer` 已过期，v3.x 对应实现为 `TDDebugConsumer`。该模式逐条通过 HTTP 请求发送数据，并在服务端进行严格校验；适合联调阶段快速定位字段格式、事件命名和数据合法性问题。

`TDDebugConsumer` 常用参数如下：

| 参数 | 描述 | 默认值 | 取值范围 | 备注 |
|------|------|--------|----------|------|
| `serverUrl` | 数据接入地址 | 无 | 字符串 | 需要与项目配置匹配 |
| `appId` | 项目 APP_ID | 无 | 字符串 | 可在项目配置页获取 |
| `deviceId` | Debug 设备 ID | 无 | 字符串 | 需在 TE 后台配置为 Debug 设备 |

调试时建议同时打开 SDK 日志：

```java
TDAnalytics.enableLog(true);
```

# 三、常见问题

#### **使用 LoggerConsumer 有哪些注意事项？**

- **搭配 LogBus 上报**
  - `TDLoggerConsumer + LogBus` 是更推荐的服务端接入组合，既能保证本地持久化，也能降低应用进程直接承担传输压力。
- **文件写权限**
  - 日志目录需要具备稳定的读写权限，Windows 或容器环境下尤其要提前验证目录权限和挂载策略。
- **磁盘空间**
  - 生产环境需要持续监控日志目录的剩余容量，并在 LogBus 或外部清理策略中配置保留与删除规则。
- **磁盘性能与 NFS**
  - 如果日志目录位于 NFS 等网络文件系统，需要重点评估写入延迟、吞吐和网络抖动带来的影响。
- **去重标识**
  - 建议补充可用于幂等控制的字段，降低极端网络场景下的重复数据风险。
- **多进程写入策略**
  - 可以多进程写不同文件或不同目录，但不要让多个进程写同一个日志文件。
- **容器环境**
  - 建议将日志目录映射到容器外部持久化存储，避免容器销毁后数据一并丢失。

#### **LoggerConsumer 是否支持多线程？是否支持多进程？**

支持多线程。SDK 的相关写入和 flush 逻辑具备线程安全保证，但单个实例默认仍是同步调用模型，多线程共享同一个实例未必能显著提升吞吐。不支持多个进程写同一个文件。若多个进程同时写同一日志文件，可能触发 `OverlappingFileLockException`。正确做法是让不同进程写入不同文件或不同目录。

#### **LoggerConsumer 性能指标如何？**

具体的性能测试报告请查看 Server-Java-sdk 性能测试报告。

#### **LoggerConsumer 是否存在丢数风险？如何避免？**

如果磁盘写满、宿主机异常宕机、日志未及时刷盘或日志目录不可用，仍然存在丢数风险。建议：

1. 定期检查日志目录磁盘容量与 inode 使用情况。
2. 根据业务实时性合理调整 `bufferSize` 与 `autoFlush`，不要盲目追求极大缓存。
3. 程序退出前确保调用 `close()`，给 SDK 留出刷盘时间。
4. 在容器或弹性环境中，将日志目录放到持久化存储。

#### **BatchConsumer 为什么会存在丢数风险？如何避免？**

`TDBatchConsumer` 基于内存维护待发送队列和失败重试缓存。只要数据还未成功发送到服务端，就仍然存在因进程退出、内存溢出、长时间网络异常或缓存上限被打满而丢失的风险。建议：

1. 生产环境优先使用 `TDLoggerConsumer + LogBus`。
2. 根据网络质量和流量规模合理调大 `maxCacheSize`，但同时评估内存占用。
3. 不要把 `batchSize` 设得过大，以免单批发送时间过长、重试成本变高。
4. 在需要降低内存驻留时间时开启 `autoFlush`。
5. 对 `NeedRetryException` 做业务级处理，而不是简单吞掉异常。

#### **BatchConsumer 性能指标如何？适合在什么场景下使用？**

具体的性能测试报告请查看 Server-Java-sdk 性能测试报告。`TDBatchConsumer` 更适合中小数据量、网络稳定、接入简单优先且能接受内存缓存局限的场景；如果你需要更高可靠性，仍然建议优先评估 `TDLoggerConsumer + LogBus`。

#### **DebugConsumer 为什么在生产环境禁用？**

因为 Debug 模式逐条发送并严格校验，每条请求都会增加额外网络与校验开销，吞吐和稳定性都不适合作为生产链路。

#### **什么时候需要调用 `close()` 方法？**

在应用准备正常退出时调用。`close()` 会尝试将缓存中的数据继续刷盘或发送，是避免尾部数据丢失的必要步骤。建议在应用生命周期的关闭钩子中统一执行。

#### **在程序中调用了 `track()` 或者 `userSet()` 方法， 为什么在 TE 后台没有看到数据？**

请依次检查以下情况：

- **检查上报地址和 APP_ID**
  - `curl https://push_url/health-check`，返回 `ok` 代表接入地址可达。
  - `curl https://push_url/check_appid?appid=目标APPID`，返回 `{"code":0}` 代表接入地址和 APP_ID 匹配。
- **数据太少，尚未触发写入或发送**
  - `TDLoggerConsumer` 和 `TDBatchConsumer` 都依赖缓存阈值、自动刷新或手动 `flush()` 才会真正落盘/上报。
  - `flush()` 可以用于排查问题，但不建议在生产代码中高频调用。
- **错误数据**
  - 可以在 Web 界面查看错误数据原因。
- **数据时间**
  - 服务端数据接收时间范围上限为相对服务器时间前三年至后三天。
  - 客户端数据接收时间范围上限为相对服务器时间前十天至后三天。
- **历史通道**
  - 若项目启用了历史通道，上报十天前的历史数据时，需要确认是否已正确进入历史通道链路。
- **埋点方案**
  - 如果项目开启了埋点方案，并设置"不在埋点方案中的事件：不允许入库"，那么不在方案内的事件会被直接拦截。
- **白名单**
  - 如果项目配置了 IP 白名单，需要确认当前上报来源 IP 是否已在白名单内；白名单生效通常存在短暂延迟。

#### **上报数据中为什么没有 #ip？**

请优先检查以下几点：

- `#ip` 是否被显式写入事件属性中。
- `#ip` 的值是否为合法 IP。
- 当前是否误用了历史代码中的旧版自定义封装。对于 v3.x SDK，建议直接按照官方示例将 `#ip` 写入事件属性 `Map<String, Object>`，不要继续沿用旧版手工拼装报文的写法。

# 四、预置属性、特殊类型上报

#### **Java SDK 如何上报对象和对象组类型？**

Java SDK 1.9.0 及以上版本支持对象和对象组类型。v3.x 中可继续按对象和 `List<Map<String, Object>>` 的方式组织属性，复杂类型示例可参考服务端 SDK 复杂类型上报。

#### **某属性首次上报为空值，应该如何上报？**

对象组：

```java
Map<String, Object> properties = new HashMap<>();

List<Map<String, Object>> arrayRowTest = new ArrayList<>();
// 至少放入一个空对象，避免被识别成普通列表类型
arrayRowTest.add(new HashMap<>());

properties.put("array_row_test", arrayRowTest);
// 上报逻辑...
```

列表：

```java
Map<String, Object> properties = new HashMap<>();

List<String> arrayTest = new ArrayList<>();
properties.put("array_test", arrayTest);
// 上报逻辑...
```

对象、数值、文本、时间、布尔类型属性都不支持直接上传 `null`。如果该字段当前无值，请不要传该属性，让结果在数据表中保持为空。

#### **公共属性**

服务端公共属性无法精确到用户级别。多线程或并发请求场景下，如果把用户级字段放进公共属性，容易出现用户维度错配。建议只在公共属性中放入稳定且全局一致的字段，例如区服 ID、部署环境、服务节点标识等；用户级、请求级、事件级字段应直接放在本次事件属性中。

#### **时区**

如果事件时间不是 UTC+8，且希望保留原始时区偏移信息，可以在普通属性内增加 `#zone_offset` 字段。例如事件时间是 UTC+0，则可以将 `#zone_offset` 设为数值 `0`。

#### **可更新事件**

在集群环境中，可更新事件如果存在毫秒级并发更新，可能出现乱序消费，导致最终结果不符合预期。遇到这类场景时，建议在事件属性中增加一个用于排序的普通属性，例如 `order`，并在事件中设置事务属性，让服务端按顺序决定是否覆盖。示例：

```java
Map<String, Object> properties = new HashMap<>();
properties.put("status", 2);
properties.put("order", 1);
properties.put("#transaction_property", "order");

ta.trackUpdate("account_id", "distinct_id", "order_status_changed", "event_id_1", properties);
```

# 五、异常报错

#### **多进程写文件出现 OverlappingFileLockException 异常，如何处理？**

`TDLoggerConsumer` 不支持多个进程写同一个文件。出现该异常时，应调整为"多进程写不同文件"或"多进程写不同目录"，不要通过重试硬顶。

#### **track() 报异常 "exception : cn.thinkingdata.tga.javasdk.exception.InvalidArgumentException: The supported data type including: Number, String, Date, Boolean,List. Invalid property: xxx"，如何处理？**

如果异常类名仍然来自 `cn.thinkingdata.tga.javasdk.exception`，说明当前项目仍在使用旧版 SDK 或旧版 API。建议直接升级到 v3.x，并统一替换为新包名 `cn.thinkingdata.analytics` 以及 camelCase 方法。同时检查属性值类型是否符合要求。支持的常见类型包括字符串、数值、布尔、时间、对象、对象组和数组；不支持的类型请先在业务侧转换后再上报。

#### **应该如何处理 NeedRetryException？**

当 SDK 在发送数据时连续重试失败，可能抛出 `NeedRetryException`。这通常意味着网络链路、服务端可达性或接入配置存在问题。建议：

1. 记录异常并打出关键信息，不要直接吞掉。
2. 结合监控判断是短时网络抖动还是持续故障。
3. 持续异常时，优先暂停高频上报或切换为更稳妥的链路，避免缓存持续打满。
4. 故障恢复后再逐步恢复业务流量。

#### **BatchConsumer 能否获取上报失败的数据？**

SDK 本身不会直接暴露一份"失败数据列表"供业务侧读取。失败批次通常由内部缓存和重试机制处理，超过缓存上限后会发生丢弃。因此如果你对失败可追溯性要求较高，应优先使用落盘方案，而不是依赖内存缓存。

#### **用线程池上报发现线程队列堆积，线程池被阻塞，什么原因？如何处理？**

如果多个线程频繁共享同一个 `TDAnalytics` 实例进行上报，内部同步控制会让发送顺序与调用顺序保持一致，但也会带来阻塞和堆积。处理方式通常有两种：

1. 如果不同线程之间没有严格顺序依赖，可按线程或按分片拆分多个 SDK 实例。
2. 如果场景更关注稳定性和削峰能力，可改用 `TDLoggerConsumer + LogBus`。

#### **调用数据上报接口(track、userSet等)时报错 NullPointerException**

请重点检查传入的属性 `Map` 是否包含 `null` 键或 `null` 值。业务代码在组装属性前，应该先做空值过滤；对于"没有值"的字段，直接不传，不要显式放入 `null`。