项目编译需要安装 `cmake`、`make`，建议使用较新的稳定版本。静态库编译时的目标架构必须和项目编译时采用的架构保持一致，例如 `ARM` 或 `x86_64`。当前仓库 `master` 分支默认要求 `CMake 3.12` 及以上版本。需要特别注意：SDK 对 C 标准的兼容性是按 Consumer 区分的，不是所有模式都统一兼容同一个 C 标准。

## 一、源码编译

本次源码编译环境采用：CentOS 9.7（x86_64）Make 4.3（x86_64）CMake 3.26.5（x86_64）

### 下载项目

```shell
git clone https://github.com/ThinkingDataAnalytics/c-sdk.git
```

### 修改 CMakeLists.txt 文件

进入项目文件夹后，按实际需要修改 `CMakeLists.txt`。当前仓库中包含四种 Consumer 的编译配置，但默认只启用了 `logging_consumer`；其他 Consumer 配置块默认是注释状态。

生产环境建议一次只保留一种 Consumer 配置，避免生成多个模式的库文件后在接入时发生混淆。

当前 `master` 分支中各 Consumer 对应的 C 标准和依赖如下：

| Consumer | 当前脚本中的 C 标准 | 额外依赖 | 说明 |
|----------|---------------------|----------|------|
| `logging_consumer` | Windows/非 Windows 都是 `C89` | Windows 需要 `pcre` | 默认启用，正式环境推荐 |
| `batch_consumer` | Windows/非 Windows 都是 `C99` | `curl` | 适合中小流量场景 |
| `debug_consumer` | Windows/非 Windows 都是 `C99` | `curl` | 仅用于调试，不建议生产使用 |
| `async_batch_consumer` | Windows 是 `C99`；非 Windows 是 `C89` | `curl`，非 Windows 还需要 `pthread` | 历史异步直传模式 |

因此，"最新版 SDK 兼容 `C89`"这句话只适用于默认的 `logging_consumer`，不能直接推广到所有 Consumer。

### 生成 Makefile 文件

`CMakeLists.txt` 修改完成后，在项目根目录执行如下命令。命令成功后会生成 `Makefile`。

```shell
cmake CMakeLists.txt
```

### 生成静态库文件

在 `Makefile` 同级目录执行如下命令：

```shell
make
```

需要注意：

- 默认情况下，只会生成当前启用的 Consumer 对应静态库。
- 如果手动把四段 Consumer 配置全部打开，理论上会生成四个静态库文件，但生产环境不建议这样做。
- 当前仓库中的典型库文件命名如下：
  - `libthinkingdata.a`：写日志文件模式，对应 `logging_consumer`
  - `libthinkingDataAsyncBatch.a`：异步上报模式，对应 `async_batch_consumer`
  - `libthinkingDataBatch.a`：批量上报模式，对应 `batch_consumer`
  - `libthinkingDataDebug.a`：调试上报模式，对应 `debug_consumer`

## 二、常见问题

### 编译 c-sdk 源码报错：curl/curl.h: No such file or directory

原因：除 `logging_consumer` 之外，其余直传类 Consumer 都依赖第三方库 `curl`；如果系统中未安装 curl 开发库，就会报这个错误。

解决：CentOS 系统安装 curl 开发库：`sudo yum install libcurl-devel`

### 项目链接静态库报错：lib/libthinkingDataBatch.a(http_client.c.o): In function `ta_http_post`:

原因：`batch_consumer`、`debug_consumer`、`async_batch_consumer` 都会链接 `curl`；如果业务项目链接阶段没有显式带上 `curl`，就会出现相关符号找不到的问题。

解决：项目编译时用 `-l` 指定链接 `curl`，例如：`gcc demo.c -o demo -lcurl`

### 使用 AsyncBatchConsumer 模式项目编译报错：/usr/bin/ld: lib/libthinkingDataAsyncBatch.a(async_batch_consumer.c.o): undefined reference to symbol 'pthread_create@@GLIBC_2.2.5'

原因：`AsyncBatchConsumer` 为异步上报模式，非 Windows 环境下除了 `curl` 之外还依赖 `pthread`。如果业务项目链接时没有显式链接线程库，就会报这个错误。

解决：项目编译时同时指定 `curl` 和 `pthread`，例如：`gcc demo.c -o demo -lcurl -lpthread`

### 到底该如何理解 C 标准兼容性？

如果你是新项目接入方，可以按下面的方式理解：

1. 如果使用默认推荐的 `logging_consumer`，当前仓库脚本按 `C89` 编译。
2. 如果使用 `batch_consumer` 或 `debug_consumer`，当前仓库脚本按 `C99` 编译。
3. 如果使用 `async_batch_consumer`，当前仓库脚本在不同平台上的 C 标准配置并不完全一致，不能简单概括为统一兼容 `C89` 或统一兼容 `C99`。
4. 所以在文档、FAQ 或客户答复中，更准确的表述应当是"兼容性与所选 Consumer 有关"，不要直接笼统写成"整个 SDK 统一兼容 `C89`"。