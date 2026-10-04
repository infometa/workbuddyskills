# SDK Usage Notes

> **Terminology**: 上报模式 = upload mode | 缓存上报 = batch/buffered upload | 批量上报策略 = batch upload strategy | 上报失败处理 = upload failure handling | 属性类型 = property type | 预置属性 = preset property (`#` prefix) | 自定义属性 = custom property | 时间校准 = time calibration | 自动采集事件 = auto-track event | 数据加密 = data encryption | LoggerConsumer = writes events to local log files (recommended for production) | BatchConsumer = uploads events in batches with retry | DebugConsumer = debug-only consumer (NOT for production) | 公共属性 = super property (公共事件属性; never "超级属性") | 动态公共属性 = dynamic super property | 多端上报 = multi-platform tracking | 用户割裂 = user fragmentation | 时区偏移 = timezone offset (`#zone_offset`)

# 一、客户端 SDK

1. **上报模式**
  - 生产环境请使用 `Normal` 模式；
  - `Debug` 和 `Debug_Only` 模式仅用于测试阶段调试，请勿在生产环境和正式阶段使用；

2. **缓存上报策略**
  - Android、iOS 原生 SDK 以及底层调用 Android、iOS SDK 的游戏引擎 SDK 和跨平台 SDK，默认采用数据缓存和批量上报策略，上报时机默认 30条/30秒，即设备本地缓存达到 30 条数据或每隔 30 秒触发数据上报。可以在 TE Web "项目管理"页面调整上报频率，但如果上报过于频繁（比如 1条/1秒）会导致客户端系统 CPU、内存、网络等开销增加，引发设备过热、卡顿等问题。
  - JS、小游戏/小程序 SDK 默认不开启本地缓存，数据会直接上报，也可以在 SDK 设置开启本地缓存和批量上报功能；
  - 对原生SDK，在Normal模式下，调用`track()`方法不会立刻触发数据上报，会根据缓存上报策略上报；如果希望数据立刻上报，可以调用 `flush()` 方法触发。

3. **上报失败处理**
  - 对于开启本地缓存情况，上报失败的数据会在本地保存并在下次触发上报条件时重新上报；
  - 如果未开启本地缓存，可以通过callback 对上报失败的情况自定义处理方式，避免数据丢失；

4. **属性类型**
  - 对于 TE 预置属性（比如 `#account_id`、`#time` 、`#ip` 等），属性类型是 TE 系统固定设置的，预置属性清单详见预置属性与系统字段。
  - 对于自定义属性（除 TE 预置属性外的属性），属性类型是 TE 系统根据属性值自动识别的，第一条携带该属性的数据中的属性值决定了属性的类型；
  - 如果上报数据中属性值与 TE 系统的属性类型不一致，系统会尝试强制转换，如果转换成功该属性会入库，如果转换失败**该属性会被丢弃**；
  - 建议关注上报管理中的异常入库，及时识别异常数据和修复；如果对数据质量要求较高，也可以上传埋点方案，并参考项目数据处理规则设置数据处理规则，确保属性类型和预期一致；
  - 元数据管理工具支持修改属性类型，需要注意，**修改类型后属性值会被清空置为NULL**。

5. **时间校准**
  - 建议开启时间校准功能，避免由于设备系统时间不准确导致数据时间偏差，影响后续分析；
  - 客户端上报，TE 接收前10天至后3天时间范围的数据，超出时间范围的**数据会被丢弃**；
  - 只需要在 SDK 初始化后做一次时间校准，不需要多次校准；
  - 时间校准方式建议优先用服务器时间戳校准，如果失败再用 NTP 校准作为备选，不要同时使用两种方式校准。

6. **自动采集事件**
  - SDK 初始化后建议在完成时间校准后立刻开启自动采集，以及时生成 `ta_app_install` `ta_app_start`等自动采集事件，避免自动采集事件生成滞后；

7. **敏感信息采集**
  - 由于法律要求，通常需要向用户展示隐私协议并获取许可后才能初始化 TE SDK 开启数据采集，请遵循各国法律和各应用商店要求披露和采集敏感信息；
  - Android SDK 会采集 `Android ID` 等信息，可以在配置文件中设置屏蔽。

8. **关键数据上报**
  - 付费、生成订单等关键数据建议从服务端上报，避免客户端上报延迟或丢失；
  - 从客户端上报的重要数据，可以调用 `flush()` 立即触发上报。

9. **数据加密**
  - 客户端 SDK 支持开启数据加密
  - 需要在 AE 集群配置密钥，具体配置流程请咨询客户成功人员；
  - 客户端 SDK 示例（Android）：
    ```kotlin
    val config = TDConfig.getInstance(context, APP_ID, SERVER_URL)
    config.enableEncrypt(1, "publicKey")  // 开启加密
    ```

10. **应用出海**
  - 如果应用投放海外，建议 TE 集群就近部署，避免跨墙等原因影响数据上报；
  - 如果应用全球投放，或数据需要从海外上报至部署在国内的 TE 集群，建议在应用主要投放地区就近部署一组或多组转接点，避免数据丢失和延迟；
  - 对于 SAAS 客户，TE SAAS 已经在全球多地部署转接点，请使用 TE SAAS 的海外上报地址 `https://global-receiver-ta.thinkingdata.cn`。

# 二、服务端 SDK

1. **上报模式**
  - 服务端SDK建议用LoggerConsumer配合Logbus上报，避免数据丢失；
  - 如果用BatchConsumer需要处理上报失败返回的异常，部分SDK不返回异常，具体可参考[SDK代码](https://github.com/ThinkingDataAnalytics)；
  - 正式环境不能使用DebugConsumer；

2. **缓存上报策略**
  - 由于性能原因，LoggerConsumer将数据批量写入文件，BatchConsumer将数据批量上报；
  - BatchConsumer 调用 `track()`不会立刻触发上报，对需要立即上报的关键数据可以调用 `flush()` ；

3. **上报失败处理**
  - 对于网络波动导致的上报失败，BatchConsumer 会重试上报3次，3次失败后会抛弃数据并返回错误信息，需要自行处理错误，详见各SDK源码；
  - 使用BatchConsumer如果网络长时间中断，当缓存数据数量大于缓存区上限时（batch*max_cache_size），会开始丢弃最早的数据，**导致缓存数据丢失**；

4. **关闭SDK**
  - 当程序退出需要关闭SDK，否则会**导致缓存数据丢失**；
  - 服务器非正常重启导致SDK异常退出，会**导致缓存数据丢失**；
  - 不同SDK关闭的方法不同，比如`close()`、`ta_free()`，详见SDK接口文档；

5. **公共属性和动态公共属性**
  - 公共属性的功能适合在客户端SDK采集用户级信息，服务端SDK不建议使用公共属性功能；

6. **IP、国家、地区信息**
  - TE 数据中的国家地区信息根据数据的ip信息解析，客户端上报 TE 会自动获取和存储IP信息，服务端上报需要在数据中添加"#ip"后 TE 才会处理；

7. **多线程和多进程**
  - 服务端SDK基本都支持多线程，`track()`方法中会做加锁处理，可以通过SDK源码确认；
  - 对于多进程情况，如果使用 LoggerConsumer，每个进程的数据要写入独立文件或独立文件夹，如果写入同一个文件会**导致数据错乱**；

8. **时区信息**
  - 客户端SDK上报数据中会自动带有设备系统的时区信息，服务端SDK数据需要自行添加"#zone_offset"属性上报时区信息。

# 三、多端上报

多端上报场景下的常见问题和解决方案详见多端上报最佳实践。

1. **用户 ID 一致**
  - 从多端上报时，需要保证同一个用户数据 `#distinct_id`和 `#account_id` 一致，否则可能会**导致用户割裂**；
  - 如果使用单账号多设备分析体系，需要保证数据的`#account_id`相同且数据中带有`#distinct_id`，避免出现用户被割裂为多个 TE 用户的情况；

2. **多端时间对齐**
  - 客户端SDK会上报时区偏移"#zone_offset"，默认取设备系统时区，部分SDK支持传参指定；
  - 服务端SDK不会自动上报时区偏移"#zone_offset"，需要在properties中手动添加上报。

3. **避免重复上报**
  - 避免多端上报相同事件，导致数据重复

4. **关键数据上报**
  - 付费、生成订单等关键数据建议从服务端上报，避免客户端延迟或丢失。