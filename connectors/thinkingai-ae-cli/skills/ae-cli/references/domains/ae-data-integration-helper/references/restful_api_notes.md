# RESTful API Usage Notes

> **Terminology**: 数据上报 = data ingestion / tracking | 集群 = TE cluster | 请求方式 = request method | 数据压缩 = data compression | 异常处理 = error handling | 数据格式校验 = data format validation | 重试 = retry | 并发 = concurrency | 请求超时 = request timeout | 兜底策略 = fallback strategy

ThinkingData provides a RESTful API for uploading data to the TE cluster via HTTP POST. See the official guide: [RESTful API User Guide](https://docs-v2.thinkingdata.cn/?version=latest&lan=en-US&code=restful_api). This document covers RESTful API usage notes and best practices.

#### 使用场景

由于 Restful API 无法像 SDK 或 Logbus 一样具备失败重试等容错能力，因此**建议应用于数据上报调试、数据格式验证等测试场景，或者少量数据一次性上报、低频上报场景。**

上述场景以外，建议使用 Logbus 等更具保障的集成工具，详见 [LogBus2 使用指南](https://docs-v2.thinkingdata.cn/?version=latest&code=logbus2_installation&lan=en-US)。

#### 请求方式

Restful API 提供了 `form-data` 和 `raw` 两种请求方式，两种方式主要功能一致，但请求接口、传参方式等存在差异。

| 请求方式 | 接口 | 支持数据压缩 | 支持Debug模式 |
|----------|------|--------------|---------------|
| form-data | http://YOUR_SERVER_URL/sync_data | 否 | 是 |
| raw | http://YOUR_SERVER_URL/sync_json | 是 | 是 |

#### 异常处理

**如果将 Restful API 用于生产场景，请务必处理网络请求异常、上报失败等异常情况，采用重试等兜底策略，避免造成数据丢失。**

根据请求返回的 code 可以判断请求是否成功， `"code": 0` 代表成功：

```json
{
    "code": 0
}
```

`"code": -1` 或其它非 0 值代表失败，可以根据 `msg` 分析失败原因：

```json
{
    "code": -1,
    "msg": "数据格式错误，非json格式"
}
```

#### QPS

Restful API 对应的 `sync_data` 和 `sync_json` 接口本身对并发并无限制，但集群连接数存在上限。若并发过高致使集群连接达到上限，将导致请求失败。

请求中的数据量和数据长度会影响集群处理请求的时长和资源：

- 单条请求中的数据量越大，请求处理耗时越长。如果请求中数据量过大，容易引发请求超时、集群连接打满等异常情况。
- 相同数据量前提下，数据平均长度越大，请求体越大，请求处理消耗内存资源越大。如果请求中数据量和数据平均长度都比较大，可能引发集群收数组件 OOM。

**因此，单条请求中的数据量需要控制在合理范围，建议不超过 1000 条。如果平均数据长度较大，需要减小请求中的数据量。**

#### debug 参数

debug 参数用于对数据格式、内容进行完整校验，默认值为 0，集群处理请求时只会对数据 JSON 格式、关键字段做简单校验。如果传入 `debug = 1`，集群会对数据内容进行完整校验并返回结果。

由于开启 debug 模式后数据校验产生更大资源开销，集群的数据接收和处理性能将受到影响。

**因此，debug 模式仅用于测试调试，请勿在生产环境中使用。**

Restful API 的两种请求方式都支持传入 debug 参数，传参方式详见 [Restful API 使用指南](https://docs-v2.thinkingdata.cn/?version=latest&lan=en-US&code=restful_api)。

#### client 参数

client 参数用于标识是否将数据作为客户端上报数据处理。如果传入 `client = 1`，集群会将数据作为客户端上报数据处理，集群会记录请求中的 IP 信息并存入 `#ip` 属性，并将 IP 解析结果写入 `#country`，`#country_code`，`#province`，`#city` 属性。

Restful API 的两种请求方式都支持传入 client 参数，传参方式详见 [Restful API 使用指南](https://docs-v2.thinkingdata.cn/?version=latest&lan=en-US&code=restful_api)。

#### 数据压缩

Raw 请求方式支持数据压缩，在 Header 中添加 `compress` 参数可以开启数据压缩并指定压缩格式，例如 `compress=gzip` 。开启数据压缩能够减少传输流量，但会对集群的数据接收与处理性能产生一定影响。

由于不同编程语言的压缩解压实现可能存在兼容性问题，建议优先选择 gzip 格式，并在正式投入使用前进行测试调试。