# 一、环境配置

SDK（当前版本1.2.7）下载路径：https://github.com/ThinkingDataAnalytics/cpp-server-sdk

测试在不同运行环境中的兼容性问题：

| 系统环境 | IDE | 编译器 | 是否可以正常运行 |
|----------|-----|--------|------------------|
| Windows | Visual Studio | msvc | ✅ |
| Windows | Clion | MinGW | ✅ |
| Windows | VSCode | MinGW | ✅ |
| Mac | Clion | Clang(g++) | ✅ |
| Mac | VSCode | Clang(g++) | ✅ |
| Linux | - | g++ | ✅ |

修改 `CMakeLists.txt` 文件，编译loggerConsumer。(原始CMakeLists文件中包含三种模式的Consumer，项目需要使用哪一种Consumer就将哪部分的注释打开，实际生产环境只建议使用loggerConsumer)

C++SDK的标准为c++11、SDK版本为1.2.7（如果直接使用数数编译好的头文件和库文件时不兼容报错。可以使用自己的编译器版本自行编译）。

#### 初始化

导入头文件：

```cpp
#include "../include/ThinkingAnalyticsAPI.h"
#include "../include/TALoggerConsumer.h"
#include "../include/TADebugConsumer.h"
#include "../include/TABatchConsumer.h"
```

#### LoggerConsumer初始化样例代码

```cpp
//定义getLoggerConsumer() 方法，返回LoggerConsumer对象
unique_ptr<TAConsumer> getLoggerConsumer() {
    LoggerConsumer::Config config = LoggerConsumer::Config("H:/log", 20, 10,LoggerConsumer::HOURLY);
    config.fileNamePrefix = "te";
    config.rotateMode = LoggerConsumer::HOURLY;
    unique_ptr<TAConsumer> ptr(new LoggerConsumer(config));
    return ptr;
}

// 实际项目main方法中创建te对象
//unique_ptr<TAConsumer> consumer = getDebugConsumer();
unique_ptr<TAConsumer> consumer = getLoggerConsumer();
//unique_ptr<TAConsumer> consumer = getBatchConsumer();
ThinkingDataAnalytics te(*consumer, false);
```

`LOG_DIRECTORY`为写入本地的文件夹地址。

#### BatchConsumer初始化样例代码

```cpp
unique_ptr<TAConsumer> getBatchConsumer() {
    unique_ptr<TAConsumer> ptr(new TABatchConsumer("appId", "serverUrl", 20, true, "/test/cert.pem"));
    return ptr;
}
```

#### DebugConsumer初始化样例代码

```cpp
unique_ptr<TAConsumer> getDebugConsumer() {
    unique_ptr<TAConsumer> ptr(new TADebugConsumer("appId", "serverUrl", "", "123456789"));
    return ptr;
}
```

#### 初始化te对象后上报各个类型数据

```cpp
//上传事件
TaSDK::PropertiesNode event_properties;
event_properties.SetString("name1", "XZ_debug");//上报字符串类型属性
event_properties.SetNumber("test_number_int", 3);//上报数值类型属性
event_properties.SetBool("test_bool", true);//上报布尔类型属性
//上报列表型属性SetList
std::vector<std::string> list;
list.emplace_back("item11");
list.emplace_back("item21");
event_properties.SetList("test_list1", list);
//上报对象类型属性SetObject
PropertiesNode properties;
properties.SetString("name2", "logBugs");
properties.SetString("#uuid", "1234567890");
properties.SetNumber("test_number_int", 3);
properties.SetNumber("test_number_double", 3.14);
event_properties.SetObject("obj", properties);
te.track(accountId, distincId, eventName, event_properties);
//上传用户属性
TaSDK::PropertiesNode userSet_properties;
userSet_properties.SetString("userName", "test");
te.user_set(accountId, distincId, userSet_properties);
// 调用flush接口数据会立即写入文件，生产环境注意避免频繁调用flush引发IO或网络开销问题
// 一般情况不需要手动调用
te.flush();
te.close();
return 0;
```

# 二、工作原理

#### **C++ SDK支持几种工作模式？分别适用于什么场景？**

C++ SDK 支持以下3种工作模式：

1. **LoggerConsumer** 批量实时将数据写入本地文件，文件可以按每天、每小时或指定文件大小分割，需要搭配 LogBus 上报数据。优点在于数据的储存与上报解耦，数据持久化存储不容易丢失；缺点在于需要另外部署 LogBus 进行上报，LogBus会占用一部分系统资源。
2. **BatchConsumer** 批量实时地向TA服务器传输数据，不需要搭配上报工具。优点在于使用简单无需搭配上报工具；缺点在于数据没有持久化存储，仅在内存中做缓存，如果网络不稳定缓存数据超过缓存区上限后会丢失数据。
3. **DebugConsumer** 逐条发送数据，服务端会对数据进行严格校验，当某个属性不符合规范时整条数据都不会入库，当数据格式错误时会打印详细错误信息。DebugConsumer 推荐在开发调试阶段使用，禁止生产环境使用。

#### **如何获取上报地址和APP_ID？**

项目管理者可以在数数WEB界面，选择具体项目后，进入项目管理 - 项目配置 - 接入配置界面获取APP_ID及数据上报地址。如果WEB页面上没有数据上报地址，需要咨询项目管理者。上报地址分为公网地址和私网地址：

- 公网地址：适用于客户端数据上报，以及公网环境下的服务端数据接入
- 私网地址：适用于内网环境下的数据接入和测试，内网上报地址为集群每个节点的8991端口

#### **LoggerConsumer的工作原理是什么？有哪些配置参数？**

上报操作会写入缓存，超过bufferSize（默认20条数据）才会写入磁盘，不满足写入条件的数据需要自行调用flush方法。写入文件时会加文件锁所以不能多进程写入同一个文件。

LoggerConsumer 常用配置参数如下表：

| 参数 | 描述 | 默认值 | 取值范围 | 备注 |
|------|------|--------|----------|------|
| logDir | 日志文件写入的路径 | 无 | 字符串 | 多级目录会自动创建 |
| rotateMode | 日志切分模式 | DAILY | HOURLY、DAILY | |
| fileNamePrefix | 日志文件名前缀 | 无 | 字符串 | |
| fileSize | 日志切分大小 | 0（不切分） | INT | 单位为MB |
| bufferSize | 缓冲区大小，达到阈值进行内存刷写到日志 | 20 | INT | 单位为数据条数 |

#### **BatchConsumer的工作原理是什么？有哪些配置参数？**

BatchConsumer 工作原理详细介绍：上报操作会写入缓存，当上报数据数量大于batchSize（默认20）或因网络通信失败等问题未上报数据导致cacheBuffer不为空时调用flush，不满足条件需要自行调用flush方法。flush时如果通信失败会重试3次，失败后存入cacheBuffer，长时间通信失败导致 未成功发送总条数 / batchSize大于maxCacheSize时会丢弃最早的batchSize条数据。

BatchConsumer 常用配置参数如下表：

| 参数 | 描述 | 默认值 | 取值范围 | 备注 |
|------|------|--------|----------|------|
| batchSize | 批次大小，达到阈值触发数据上报 | 20 | INT | 单位为数据条数 |

#### **DebugConsumer的工作原理是什么？有哪些配置参数？**

原理：每条数据都直接走http请求上报数据，不用调flush。数据格式会进行严格校验。

# 三、常见问题

#### **使用 LoggerConsumer 有哪些注意事项？**

- **搭配Logbus上报**
  - LoggerConsumer + LogBus为数数标准的数据上报方案，LoggerConsumer使得数据持久化，数据得到不丢失的保障；LogBus为数据传输作保证，同时将数据持久化和上报解耦。
- **文件写权限**
  - 写入日志目录需要有写入和读取的权限，通常Windows环境会有写入权限问题。
- **磁盘空间**
  - 磁盘空间保证充裕，并可以合理在LogBus上配置删除策略。
- **磁盘性能NFS情况**
  - NFS磁盘就是通过网络连接到本地计算机的一种远程文件系统，它可以让用户在本地计算机上像访问本地磁盘一样访问NFS磁盘上的文件和目录。在使用此类磁盘时，需要关注写入速率及网络波动导致的数据异常写入的问题。
- **UUID**
  - 建议添加UUID，防止网络抖动及极端情况造成数据重复，但会稍微消耗效率，也可在LogBus侧打开。如不添加则默认在集群receiver组件处添加。
- **多进程写不同文件**
  - 支持多进程写不同文件，但要保证不同进程的处理逻辑没有依赖关系（如不同服务器的用户行为写到不同日志）
- **容器环境**
  - 将数据写入路径映射到外部磁盘，防止容器关闭数据文件丢失。

#### **LoggerConsumer 是否支持多线程？**

不支持多线程写同一个文件。TALoggerConsumer的 add()方法中用m_flush_mutex.lock()排他锁对文件加锁。可以多线程写入不同文件或写入不同目录，避免异常。

#### **LoggerConsumer 性能指标如何？**

**测试环境**

```cpp
Kernel Version: 3.10.0-1160.42.2.el7.x86_64
Operating System: CentOS Linux 7 (Core)
OSType: linux
Architecture: x86_64
CPUs: 4
Total Memory: 15.25GiB
```

**测试场景**

启动服务端代码，开启10个子线程，使用**log_consumer每个线程持续**track5分钟，**track接口调用速率为每秒钟10万次**，获取当前进程的cpu占用率，内存占用率。

**测试结果**

5分钟实际写入数据量为16066600条，平均每秒钟写入53555条数据。track期间：cpu均值在67%左右，4核总均值在268%左右浮动；memory均值稳定在4.1M左右，无内存泄漏的产生。

#### **LoggerConsumer 是否存在丢数风险？如何避免？**

如果磁盘写满或者服务器宕机可能导致数据丢失，建议：

1. 定期检查写入日志路径磁盘剩余容量
2. 降低batchSize参数值，增加内存刷写频率，但会导致频繁IO，需结合具体场景综合考虑

#### **BatchConsumer 为什么会存在丢数风险？如何避免？**

`BatchConsumer`在内存中维护了一个batchSize 大小的队列负责存放单批次数据。因为`BatchConsumer`基于内存存储，所以当发生内存溢出或者服务器宕机时，内存中未发送的数据会全部丢失，建议：

1. 使用LoggerConsumer + LogBus搭配进行数据上报
2. batchSize参数不宜设置过大，可能会导致单次发送数据时间增加，会增加发生网络错误的概率

批量实时地向 TE 服务器传输数据，不需要搭配传输工具。**在长时间网络中断情况下，有数据丢失的风险，不建议在正式环境中使用。优点在于使用简单无需搭配上报工具；缺点在于数据没有持久化存储，仅在内存中做缓存，如果网络不稳定缓存数据超过缓存区上限后会丢失数据。**

#### **BatchConsumer 性能指标如何？适合在什么场景下使用？**

BatchConsumer适合中小数据量，且日志上报服务器和TE集群内网打通时使用。

#### **DebugConsumer 为什么在生产环境禁用？**

逐条发送数据，服务端会对数据进行严格校验，当某个属性不符合规范时整条数据都不会入库，当数据格式错误时会打印详细错误信息。DebugConsumer 仅适用开发调试阶段，不适合在正式环境使用。

#### **什么时候需要调用 `close()` 方法？**

程序需要正常结束时调用，close()方法会将内存中的数据进行写入文件或发送。close() 函数会调用 flush() 上报或写入缓存的数据，并关闭和释放相应资源。一种常见的错误用法是在每次调用 flush() 后调用 close()，这样会导致下一次调用 flush() 时报错，除非每次对SDK重新初始化。

#### **在程序中调用了 `track()` 或者 `user_set()` 方法， 为什么在 TE 后台没有看到数据？**

请依次检查以下情况：

- **检查上报地址和appid**
  - curl https://push_url/health-check，上报地址正常会返回`ok`
  - curl https://push_url/check_appid?appid=目标APPID，上报地址和appid匹配会返回`{"code":0}`
- **数据太少，未触发上报**
  - 对于BatchConsumer和LoggerConsumer需要达到batchSize才会真正触发数据写入或数据上报
  - 也可以手动调用flush方法触发数据上报，但不建议频繁主动调用flush
- **错误数据**
  - 可以在WEB界面查看错误数据原因
- **数据时间**
  - 服务端数据接收事件上限：相对服务器时间的前三年至后3天
  - 客户端数据接收事件上限：相对服务器时间的前10天至后3天
- **历史通道**
  - 当在项目管理中开启历史通道后，上报10天前的历史数据时会被ETL直接搬运到HDFS历史通道，才能入库可供查询
- **埋点方案**
  - 在项目管理中设置了埋点方案且在数据处理规则中选择了`不在埋点方案中的事件:不允许入库`后，将无法上报不再埋点方案中的数据，可在错误数据中查看
- **白名单**
  - 在项目管理中设置了IP白名单后，将只有白名单内的IP才能上报数据，白名单生效存在10分钟的延迟

#### **首次上报属性业务为空（对象组为例该如果上报 如果是{}会识别成该字段为列表）如何正确上报？**

上报为各个语言的Null类型。

#### **事件时间默认值？如何将自定义的时间赋值给#time？**

默认为ThinkingDataAnalytics::track() 时的服务器当前时间。自定义的时间赋值给#time参考前面上报样例代码。

#### **SDK的线程模型？是异步的还是阻塞？**

SDK 主要作用是对于数据格式的组织，以及缓冲区落盘。**线程模型是阻塞式的**，在 flush 函数调用时触发。

#### **SDK中有 GBK 转 UTF8 的 C++ 标准函数么？对比javaSDK的timer，C++SDK中有支持吗？**

目前都没有集成这些功能，后续新版本SDK会新增。

#### **ubuntu 20.04 默认 cmake 版本是 3.16.1，C++SDK的编译选项是 cmake_minimum_required(VERSION 3.22)。必须指定 cmake 到 3.22 以上版本么？**

理论上是可以的，可先用低版本的编译器尝试。或者自行用低版本的编译器编译SDK源码。

#### **客户项目代码和 C++SDK的兼容性问题**

**数数C++SDK的c++标准为c++11。**SDK库引用了 set(CMAKE_CXX_STANDARD 11)，使用该SDK必须引用 set(CMAKE_CXX_STANDARD 11)。若客户项目引入代码的c++标准较低，引入c++11标准的SDK会出现一堆报错，即项目有些代码是不支持 C++11。需要保证代码的c++标准高于11。

#### **使用debug/batch consumer的方式上报数据至https协议的receiver url时返回-1，报错Unsupported protocol**

`SERVER_URL`: 数据上传的 URL

- 如果您对接的是云服务，填入: https://global-receiver-ta.thinkingdata.cn
- 如果您使用私有化部署版本，请为数据采集地址绑定域名，**并配置 HTTPS 证书**：https://数据采集地址绑定域名

# 四、属性类型、预置属性

#### **C++ SDK 如何上报对象和对象组类型？**

C++ SDK支持上报对象和对象组类型。可参考上面logger consumer上报各个数据类型的样例代码。代码示例请参考服务端SDK复杂类型上报。

#### **某属性首次上报为空值，应该如何上报？**

对象组为例，如果是[]会识别成该字段为列表，需要设为[{}]。

#### **上报数据中为什么没有 "#ip"？**

服务端的#ip需要单独上报，层级与#distinct_id、#event_name、#time、properties等同级。

#### **公共属性**

服务端的公共属性无法精确到用户级，在多线程情况下报了用户级属性数据可能会导致用户数据对不上。仅建议在公共属性内放区服id等不会产生大变化的字段，其余均放入普通属性。

#### **时区**

如果数据事件时间不是utc8又对时区偏移有需求，可以在普通属性内增加#zone_offset这个时区字段，假设事件时间是utc0就给时区字段赋值数值类型的0即可。

#### **用户属性**

1. 对于一般的用户属性，您可以调用 `user_set` 来进行设置。使用该接口上传的属性将会覆盖原有的属性值，如果之前不存在该用户属性，则会新建该用户属性，类型与传入属性的类型一致：

```cpp
TaSDK::PropertiesNode userSet_properties;
userSet_properties.SetString("userName", "A");
te.user_set(accountId, distincId, userSet_properties);

userSet_properties.SetString("userName", "B");
te.user_set(accountId, distincId, userSet_properties); // userName 会变为 "B"
```

2. 如果您要上传的用户属性只要设置一次，则可以调用`user_setOnce`来进行设置，当该属性之前已经有值的时候，将会忽略这条信息：

```cpp
TaSDK::PropertiesNode userSetOnce_properties;
userSetOnce_properties.SetString("user_one_name", "A");
te.user_setOnce(accountId, distincId, userSetOnce_properties);

userSetOnce_properties.SetString("user_one_name", "B");
te.user_setOnce(accountId, distincId, userSetOnce_properties); // user_one_name 仍为 "A"
```

3. 当您要上传数值型的属性时，您可以调用`user_add`来对该属性进行累加操作，如果该属性还未被设置，则会赋值 0 后再进行计算：

```cpp
TaSDK::PropertiesNode userAdd_properties;
userAdd_properties.SetNumber("cash", 30);
te.user_add(accountId, distincId, userAdd_properties);

userAdd_properties.SetNumber("cash", 60);
te.user_add(accountId, distincId, userAdd_properties); // cash 会变为 90
```

4. 您可以调用 `user_append` 对数组类型的用户属性进行追加操作：

```cpp
TaSDK::PropertiesNode userAppend_properties;
vector<string> userAppenListValue;
userAppenListValue.push_back("11");
userAppenListValue.push_back("33");
userAppend_properties.SetList("arr1", userAppenListValue);
te.user_append(accountId, distincId, userAppend_properties); // arr1 为 ["11", "33"]

TaSDK::PropertiesNode userAppend_properties_new;
vector<string> userAppenListValueNew;
userAppenListValueNew.push_back("22");
userAppenListValueNew.push_back("33");
userAppend_properties_new.SetList("arr1", userAppenListValueNew);
te.user_append(accountId, distincId, userAppend_properties_new); // arr1 为 ["11", "33", "22", "33"]
```

#### **可更新事件**

在服务器为集群模式下，毫秒级别的可更新事件可能会乱序消费导致最终更新结果不达到预期。遇到这种情况时可以在可更新事件中properties内加一个普通属性指定这条数据的序号，比如属性 order为数值类型的1，然后在properties外增加预置属性#transaction_property，值设置为 "order"，入库时会根据 order的大小来判断是否要入库，order大于1更新，小于等于1则丢弃。

```cpp
// updatable event
eventName = "update_event";
string updateEventId = "update_001";
TaSDK::PropertiesNode update_event_properties;
update_event_properties.SetString("price", "100");
update_event_properties.SetString("status", "3");
te.track_update(accountId, distincId, eventName, updateEventId, update_event_properties);

TaSDK::PropertiesNode update_event_new_properties;
update_event_new_properties.SetString("status", "5");
te.track_update(accountId, distincId, eventName, updateEventId, update_event_new_properties); // status 变为 5，price 仍为 100
```

# 五、异常报错