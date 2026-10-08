本文按 C SDK v2.0.0 正式版整理，示例统一使用 `td_` 前缀 API。旧版 `ta_*` 接口、`ta_user_del()` 等命名仅适用于 1.x 历史项目；新项目请不要继续使用旧接口名。

推荐方案为 `logging_consumer + LogBus`。`batch_consumer` 仍可用于特定场景，但存在内存缓存丢数风险；`debug_consumer` 仅用于接入调试；`async_batch_consumer` 属于历史兼容方案，新项目不再推荐。

# 一、环境配置

当前正式版为 `v2.0.0`，源码下载地址：[源代码](https://github.com/ThinkingDataAnalytics/c-sdk)。如需从源码编译，请参考服务端C-SDK编译流程。新建 C 项目后，将 SDK 头文件和编译产物引入工程。

```c
#include <thinkingdata.h>
```

#### logging_consumer样例代码

```c
#include <stdio.h>
#include <string.h>
#include <time.h>

#include <thinkingdata.h>

int main(void) {
    struct TDAnalytics *ta = NULL;
    struct TDConsumer *consumer = NULL;
    TDConfig *config = td_init_config();
    TDProperties *properties = NULL;
    const char *log_directory = "./log";
    const char *account_id = "user_10001";
    const char *distinct_id = "device_10001";

    if (config == NULL) {
        return 1;
    }

    TD_ASSERT(TD_OK == td_add_string("file_path", log_directory, strlen(log_directory), config));
    TD_ASSERT(TD_OK == td_add_int("rotate_mode", HOURLY, config));
    TD_ASSERT(TD_OK == td_add_int("file_size", 1024, config));

    if (TD_OK != td_init_consumer(&consumer, config)) {
        td_free_properties(config);
        fprintf(stderr, "Failed to initialize consumer.\n");
        return 1;
    }
    td_free_properties(config);

    if (TD_OK != td_init(consumer, &ta)) {
        td_consumer_free(consumer);
        fprintf(stderr, "Failed to initialize SDK.\n");
        return 1;
    }

    properties = td_init_properties();
    if (properties == NULL) {
        td_free(ta);
        td_consumer_free(consumer);
        return 1;
    }

    TD_ASSERT(TD_OK == td_add_string("#ip", "192.168.1.1", strlen("192.168.1.1"), properties));
    TD_ASSERT(TD_OK == td_add_string("channel", "logbus", strlen("logbus"), properties));
    TD_ASSERT(TD_OK == td_add_int("amount", 30, properties));
    TD_ASSERT(TD_OK == td_add_bool("is_success", TD_TRUE, properties));
    TD_ASSERT(TD_OK == td_add_date("pay_time", time(NULL), 0, properties));

    TD_ASSERT(TD_OK == td_track(account_id, distinct_id, "order_paid", properties, ta));

    td_free_properties(properties);
    td_free(ta);
    td_consumer_free(consumer);
    return 0;
}
```

#### batch_consumer样例代码

> `batch_consumer` 适用于中小数据量、链路稳定且可以接受内存缓存的场景。新项目仍然优先推荐 `logging_consumer + LogBus`。

```c
#include <stdio.h>
#include <string.h>
#include <time.h>

#include <thinkingdata.h>

int main(void) {
    struct TDAnalytics *ta = NULL;
    struct TDConsumer *consumer = NULL;
    TDConfig *config = td_init_config();
    TDProperties *properties = NULL;
    const char *appid = "APPID";
    const char *server_url = "https://receiver.example.com";

    if (config == NULL) {
        return 1;
    }

    TD_ASSERT(TD_OK == td_add_string("push_url", server_url, strlen(server_url), config));
    TD_ASSERT(TD_OK == td_add_string("appid", appid, strlen(appid), config));
    TD_ASSERT(TD_OK == td_add_int("batch_size", 20, config));
    TD_ASSERT(TD_OK == td_add_int("max_cache_size", 50, config));

    if (TD_OK != td_init_consumer(&consumer, config)) {
        td_free_properties(config);
        fprintf(stderr, "Failed to initialize consumer.\n");
        return 1;
    }
    td_free_properties(config);

    if (TD_OK != td_init(consumer, &ta)) {
        td_consumer_free(consumer);
        fprintf(stderr, "Failed to initialize SDK.\n");
        return 1;
    }

    properties = td_init_properties();
    if (properties == NULL) {
        td_free(ta);
        td_consumer_free(consumer);
        return 1;
    }

    TD_ASSERT(TD_OK == td_add_int("amount", 30, properties));
    TD_ASSERT(TD_OK == td_add_date("pay_time", time(NULL), 0, properties));
    TD_ASSERT(TD_OK == td_track("account_id", "distinct_id", "order_paid", properties, ta));

    td_free_properties(properties);
    td_flush(ta);
    td_free(ta);
    td_consumer_free(consumer);
    return 0;
}
```

#### debug_consumer样例代码

> `debug_consumer` 只用于接入联调。严禁在生产环境使用。

```c
#include <stdio.h>
#include <string.h>

#include <thinkingdata.h>

int main(void) {
    struct TDAnalytics *ta = NULL;
    struct TDConsumer *consumer = NULL;
    TDConfig *config = td_init_config();
    TDProperties *properties = NULL;
    const char *appid = "APPID";
    const char *server_url = "https://receiver.example.com";

    td_enableLog(1);

    if (config == NULL) {
        return 1;
    }

    TD_ASSERT(TD_OK == td_add_int("debug_mode", 0, config));
    TD_ASSERT(TD_OK == td_add_string("device_id", "123456789", strlen("123456789"), config));
    TD_ASSERT(TD_OK == td_add_string("push_url", server_url, strlen(server_url), config));
    TD_ASSERT(TD_OK == td_add_string("appid", appid, strlen(appid), config));

    if (TD_OK != td_init_consumer(&consumer, config)) {
        td_free_properties(config);
        fprintf(stderr, "Failed to initialize consumer.\n");
        return 1;
    }
    td_free_properties(config);

    if (TD_OK != td_init(consumer, &ta)) {
        td_consumer_free(consumer);
        fprintf(stderr, "Failed to initialize SDK.\n");
        return 1;
    }

    properties = td_init_properties();
    if (properties == NULL) {
        td_free(ta);
        td_consumer_free(consumer);
        return 1;
    }

    TD_ASSERT(TD_OK == td_add_string("#device_id", "123456789", strlen("123456789"), properties));
    TD_ASSERT(TD_OK == td_track("account_id", "distinct_id", "debug_test", properties, ta));

    td_free_properties(properties);
    td_free(ta);
    td_consumer_free(consumer);
    return 0;
}
```

# 二、工作原理

#### **C SDK支持几种工作模式？分别适用于什么场景？**

当前面向新项目时，可以按"推荐模式"和"历史兼容模式"理解：

1. `logging_consumer`：正式环境推荐模式。数据先落本地文件，再由 LogBus 传输，可靠性最高。
2. `batch_consumer`：受限可用模式。适合中小流量、网络稳定、可接受内存缓存风险的场景。
3. `debug_consumer`：调试模式。只用于接入联调，不用于生产环境。
4. `async_batch_consumer`：历史兼容模式。仅旧项目维护时参考，新项目不再推荐。

#### **如何获取上报地址和APP_ID？**

项目管理者可以在 TE 后台进入"项目管理 > 项目配置 > 接入配置"获取 `APPID` 与上报地址。

- 云服务环境：使用平台提供的 HTTPS 上报地址。
- 私有化环境：建议为数据接入地址绑定域名并配置 HTTPS 证书。
- 内网联调场景：请直接使用运维确认后的内网地址，不要把公网地址硬编码进生产配置。

#### **logging_consumer的工作原理是什么？有哪些配置参数？**

`logging_consumer` 在 SDK 侧负责把数据可靠写入本地文件，LogBus 负责监听目录并完成上传。业务线程与网络传输解耦，因此正式环境更稳健。

| 参数 | 描述 | 默认值 | 取值范围 | 备注 |
|------|------|--------|----------|------|
| `file_path` | 日志文件写入目录 | 无 | 字符串 | 必填，建议映射到持久化磁盘 |
| `rotate_mode` | 日志切分模式 | `HOURLY` | `HOURLY` / `DAILY` | 配合日志量选择 |
| `file_prefix` | 日志文件名前缀 | 无 | 字符串 | 用于区分业务或实例 |
| `file_size` | 按文件大小切分阈值 | `0` | 整数 | 单位 MB，`0` 表示不按大小切分 |

#### **batch_consumer的工作原理是什么？有哪些配置参数？**

`batch_consumer` 在内存中聚合数据，达到阈值后再发起网络请求。若网络失败，数据会先留在内存缓存中；当缓存超过上限时，最旧批次会被丢弃。

| 参数 | 描述 | 默认值 | 取值范围 | 备注 |
|------|------|--------|----------|------|
| `batch_size` | 单批次上报条数 | `20` | 整数 | 批次越大，单次请求耗时越高 |
| `timeout` | 请求超时时长 | `30` | 整数 | 单位秒 |
| `max_cache_size` | 最大缓存批次数 | `50` | 整数 | 达到上限后会淘汰最旧批次 |
| `appid` | 项目 APPID | 无 | 字符串 | 必填 |
| `push_url` | 数据上报地址 | 无 | 字符串 | 必填，建议 HTTPS |

#### **debug_consumer的工作原理是什么？有哪些配置参数？**

`debug_consumer` 逐条发起请求，并对数据格式做更严格的校验。由于每条数据都会走网络请求，因此只能在联调阶段使用。

| 参数 | 描述 | 默认值 | 取值范围 | 备注 |
|------|------|--------|----------|------|
| `push_url` | 数据上报地址 | 无 | 字符串 | 必填 |
| `appid` | 项目 APPID | 无 | 字符串 | 必填 |
| `timeout` | 请求超时时长 | `30` | 整数 | 单位秒 |
| `device_id` | Debug 设备标识 | 无 | 字符串 | 需在 TE 后台配置同一设备 ID |
| `debug_mode` | 是否入库 | `0` | `0` / `1` | `0` 表示入库，`1` 表示仅校验不入库 |

# 三、常见问题

#### **使用 logging_consumer 有哪些注意事项？**

- 推荐和 LogBus 配合使用，这是服务端正式环境的标准方案。
- `file_path` 应指向具备写权限且可持久化的目录，容器环境建议挂载外部卷。
- 磁盘容量需要有监控和清理策略，避免写满后无法继续落盘。
- 不同进程不要写同一个日志文件；多进程场景请拆分目录或文件前缀。
- 网络文件系统（如 NFS）需要重点评估写入时延和抖动，避免成为瓶颈。

#### **logging_consumer 是否支持多线程？是否支持多进程？**

支持多线程。SDK 内部会保证单进程内的线程安全。不支持多个进程同时写入同一个日志文件。多进程场景请为每个进程分配独立文件或目录。

#### **logging_consumer 是否存在丢数风险？如何避免？**

存在边界风险，主要来自磁盘写满、宿主机异常退出、容器未挂载持久化卷等情况。建议：

1. 监控日志目录容量并设置归档或清理策略。
2. 根据写入量设置合理的切分策略，避免单文件过大。
3. 容器部署时把日志目录映射到宿主机或持久化存储。
4. 关闭进程前调用 `td_free()` 和 `td_consumer_free()`，确保资源正常释放。

#### **batch_consumer 为什么会存在丢数风险？如何避免？**

因为 `batch_consumer` 依赖内存缓存，进程崩溃、宿主机异常退出或持续网络失败都可能导致未发送数据丢失。建议：

1. 正式环境优先使用 `logging_consumer + LogBus`。
2. 如果必须使用 `batch_consumer`，适度提高 `max_cache_size`，但要同步评估内存占用。
3. 不要把 `batch_size` 调得过大，避免单次发送时间过长。
4. 在进程退出前显式调用 `td_flush()`。

#### **batch_consumer 适合在什么场景下使用？**

它更适合中小数据量、部署链路简单、网络稳定且可接受少量缓存风险的场景。

#### **debug_consumer 为什么在生产环境禁用？**

因为它会逐条发送并做严格校验，连接开销高、吞吐低，还可能放大线上日志噪音，只适合开发联调。

#### **什么时候需要调用 `ta_free()` 方法？**

`ta_free()` 是 1.x 的旧函数名，v2 对应为 `td_free()`。在程序正常结束前调用 `td_free()`，随后调用 `td_consumer_free()`，确保 SDK 内部资源与缓存被正确释放。

#### **在程序中调用了 `ta_track()` 或者 `ta_user_set()` 方法， 为什么在 TE 后台没有看到数据？**

`ta_track()` / `ta_user_set()` 为旧版命名，v2 对应 `td_track()` / `td_user_set()`。排查顺序建议如下：

- 检查 `push_url` 和 `appid` 是否匹配。
- 如果使用 `batch_consumer`，确认是否达到 `batch_size`，或是否已经手动调用 `td_flush()`。
- 检查错误数据和校验日志。
- 检查事件时间是否超出服务端接收范围。
- 检查项目是否启用了埋点方案限制、历史通道或 IP 白名单。

#### **上报数据中为什么没有 "#ip"？**

服务端 SDK 不会自动采集客户端 IP。若需要地理位置解析，请在事件属性中显式设置 `#ip`：

```c
TDProperties *properties = td_init_properties();
TD_ASSERT(TD_OK == td_add_string("#ip", "192.168.1.1", strlen("192.168.1.1"), properties));
TD_ASSERT(TD_OK == td_track("account_id", "distinct_id", "order_paid", properties, ta));
```

# 四、预置属性、特殊类型上报

以下预置属性会出现在 C SDK 事件中，其中 `#ip` 需要业务侧手动设置，其余地理信息由平台根据 IP 衍生。

| 属性名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| `#ip` | IP 地址 | 文本 | 需要业务手动设置 |
| `#country` | 国家 | 文本 | 根据 IP 解析 |
| `#country_code` | 国家代码 | 文本 | 根据 IP 解析 |
| `#province` | 省份 | 文本 | 根据 IP 解析 |
| `#city` | 城市 | 文本 | 根据 IP 解析 |
| `#lib` | SDK 类型 | 文本 | 平台自动补充 |
| `#lib_version` | SDK 版本 | 文本 | 平台自动补充 |

#### **C SDK 如何上报对象和对象组类型？**

复杂类型的完整说明可参考服务端 SDK 复杂类型上报。基本示例如下：

```c
TDProperties *properties = td_init_properties();
TDProperties *object = td_init_custom_properties("object");
TDProperties *group_item = td_init_custom_properties("group_item");

TD_ASSERT(TD_OK == td_add_string("key", "value", strlen("value"), object));
TD_ASSERT(TD_OK == td_add_property(object, properties));

TD_ASSERT(TD_OK == td_add_string("name", "item_1", strlen("item_1"), group_item));
TD_ASSERT(TD_OK == td_append_properties("object_arr", group_item, properties));
```

#### **某属性首次上报为空值，应该如何上报？**

对象组可以通过"空对象"方式上报，数组可以通过"空数组"方式上报：

对象组：

```c
TDProperties *properties = td_init_properties();
TDProperties *obj = td_init_custom_properties("obj");
TD_ASSERT(TD_OK == td_append_properties("obj_array", obj, properties));
```

列表：

```c
TDProperties *properties = td_init_properties();
TD_ASSERT(TD_OK == td_append_array("array", NULL, 0, properties));
```

对象、数值、文本、时间、布尔类型不支持直接上报 `NULL`。如需表达空值，请不要传该属性，让数据表中保持空值状态。

#### **公共属性**

服务端公共属性不适合承载用户级强变更字段。多线程或多用户并发场景下，建议只在公共属性中放置区服、渠道、部署环境等相对稳定的信息，其余内容放入事件属性或用户属性。

#### **时区**

如事件时间不是 UTC+8 且需要显式携带时区偏移，可在属性中增加 `#zone_offset`，其值为数值类型的小时偏移量。例如 UTC+0 可传 `0`。

#### **可更新事件**

集群环境下，可更新事件可能出现近时间戳乱序。若业务强依赖顺序，建议在属性中增加一个数值型顺序字段，例如 `order`，并结合事务属性做幂等控制：

```c
TDProperties *properties = td_init_properties();
TD_ASSERT(TD_OK == td_add_int("order", 2, properties));
TD_ASSERT(TD_OK == td_add_int("status", 5, properties));
TD_ASSERT(TD_OK == td_track_update("account_id", "distinct_id", "UPDATABLE_EVENT", "event_id", properties, ta));
```

# 五、异常报错

#### **batch_consumer 能否获取上报失败的数据？**

SDK 不直接暴露失败缓存队列。失败数据会先留在内存缓存中，达到上限后最旧批次会被淘汰。因此更稳妥的做法仍然是使用 `logging_consumer + LogBus`，把持久化和传输解耦。

#### **由于客户服务器环境不一致，C SDK工程中的 curl 和 pcre 两个库文件编译报错，如何处理？**

`curl` 和 `pcre` 都是独立的开源依赖。遇到平台兼容问题时，建议按目标环境重新下载源码并编译：

- `curl`：https://curl.se
- `pcre`：http://www.pcre.org

#### **sdk编译windows版本也依赖pthread库吗？**

如果当前工程要求兼容 `c89` / `c90`，请避免继续依赖需要更高线程支持的历史方案，优先改用 `logging_consumer`；如果必须保留直传能力，再评估 `batch_consumer` 的兼容性。

#### **C SDK 中使用的 libcurl 库是否会导致死锁或崩溃？**

在网络较差的环境下，`libcurl` 超时配置不当可能引发异常信号问题。建议显式设置超时并关闭超时信号：

```c
if (timeout_seconds > 0) {
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, timeout_seconds);
    curl_easy_setopt(curl, CURLOPT_NOSIGNAL, 1);
}
```

#### **CentOS 上报https地址报错：curl_easy_perform() failed: SSL connect error，如何处理？**

这通常是 `curl` 侧的 SSL 环境问题，常见处理方式包括：

1. 升级系统中的 `nss` / OpenSSL 相关依赖。
2. 更新 CA 证书链。
3. 确认服务端证书与域名绑定是否正确。
4. 在内网排障阶段，可先用 `curl` 单独验证目标地址的 TLS 握手是否正常。