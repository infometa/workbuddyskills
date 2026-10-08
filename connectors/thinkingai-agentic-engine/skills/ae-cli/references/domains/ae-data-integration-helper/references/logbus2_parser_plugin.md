# LogBus2 Data Parser Plugin

> **Terminology**: 数据转译插件 = data parser/translation plugin | 自定义数据解析器 = custom data parser | 数据格式转换 = data format conversion | gRPC 插件 = gRPC plugin | 批量处理 = batch processing | 分隔符 = separator / delimiter | 拼接 = concatenate | proto 文件 = .proto file (Protocol Buffers) | 告警功能 = alerting | 无限重试 = infinite retry | 错误数据 = malformed/error data | 标准 TA 格式 = standard ThinkingAnalytics data format

> Logbus2 from version 2.1.0.0 supports custom data parsers for converting source data formats that differ from the TE data format. This is equivalent to Logbus1's Custom Interceptor feature.

## 一、准备工作

### 数据格式

1. gRPC插件服务端接收数据进行批量处理，多条数据以Logbus2配置参数 parser.separator（默认 :: )拼接
2. 单条数据则拼接文件名称或者Kafka的topic名称，以配置参数 parser.index_separator（默认 |ta| ）拼接

示例：

```python
# 文件名称为：event.log
# 原始数据2条：
{"user_id": "abc", "distinct_id": "123"}
{"user_id": "def", "distinct_id": "456"}

# gRPC插件服务端接收到的数据为：
event.log|ta|{"user_id": "abc", "distinct_id": "123"} ::event.log|ta|{"user_id": "def", "distinct_id": "456"}
```

gRPC插件服务端返回数据格式，以parser.separator拼接转换为标准ta格式的数据：

```python
# 返回数据应为：
{"#account_id": "abc", "#distinct_id": "123"}::{\"#account_id\": \"def\", \"distinct_id\": \"456\"}
```

错误处理：
- 返回非正确json数据，则主程序会跳过错误行
- 返回非标准ta数据，则数据上报会产生错误
- 返回第二个参数为error，则会进行无限重试，防止错误数据进入te集群。可搭配告警功能，提前预知错误信息。

### proto文件

parser.proto 文件用于生成各语言的 gRPC 服务端代码。

### Java

1. JDK 8+ (Logbus部署环境和开发环境保持一致)、Maven
2. 下载 protobuf 编译工具：https://github.com/protocolbuffers/protobuf/releases
3. 下载 grpc-java 编译工具：https://repo.maven.apache.org/maven2/io/grpc/protoc-gen-grpc-java/

编译步骤：

```shell
# 生成ParserGrpc.java文件
protoc --plugin=protoc-gen-grpc-java=protoc-gen-grpc-java-1.51.0-osx-aarch_64.exe  --grpc-java_out=/ta/path/ -I=/ta/path/ /ta/path/parser.proto

# 生成ParserOuterClass.java文件
protoc --experimental_allow_proto3_optional -I /ta/path/ --java_out=/ta/path/ /ta/path/parser.proto
```

### Python

1. Python3.6+
2. 安装三方库：

```shell
pip3 install grpcio-tools==1.48.2 -i https://pypi.tuna.tsinghua.edu.cn/simple
pip3 install grpcio-health-checking==1.48.2 -i https://pypi.tuna.tsinghua.edu.cn/simple
```

编译步骤：

```shell
python -m grpc_tools.protoc -I /ta/path/ --python_out=/ta/path/ --grpc_python_out=/ta/path/ /ta/path/parser.proto
```

## 二、gRPC服务端开发

### Java版本（所需版本JDK 8+）

Maven依赖：

```xml
<dependencies>
    <dependency>
        <groupId>com.google.protobuf</groupId>
        <artifactId>protobuf-java</artifactId>
        <version>3.19.4</version>
    </dependency>
    <dependency>
        <groupId>io.grpc</groupId>
        <artifactId>grpc-all</artifactId>
        <version>1.51.0</version>
    </dependency>
</dependencies>
```

开发转译逻辑demo：

```java
package org.interceptor.logbus2.service;

import org.interceptor.logbus2.proto.ParserGrpc;
import org.interceptor.logbus2.proto.ParserOuterClass;
import com.google.protobuf.ByteString;
import io.grpc.Server;
import io.grpc.ServerBuilder;
import io.grpc.stub.StreamObserver;
import java.util.*;

public class Demo extends ParserGrpc.ParserImplBase {

    // 对应logbus2参数parser.separator，多条数据之间自定义的分隔符，默认 ::
    private static final String separator = ":ta:";
    
    // 对应logbus2参数parser.index_separator，单条数据，索引与数据之间的分隔符，默认 |ta|
    private static final String indexSeparator = "\\|ta\\|";
    
    // 对应logbus2参数parser.batch_separator，用于数据一条转多条的分隔符，默认 0x01
    private static final String batchSeparator = new String(new byte[]{0x01}, StandardCharsets.UTF_8);
    
    public static String parseData(final String rawData) {
        try {
            // 处理逻辑：将接收到的数据中的test字符转为product，并将数据增加为3条返回
            String parseData = JSON.toJSONString(JSON.parseObject(rawData.replaceAll("test", "product"), TaDataDo.class));
            return parseData + batchSeparator + parseData + batchSeparator + parseData;
        } catch (Exception e) {
            e.printStackTrace();
            return null;
        }
    }
    
    @Override
    public void parse(ParserOuterClass.Request request, StreamObserver<ParserOuterClass.Response> responseObserver) {
        String content = request.getContent().toStringUtf8();
        String[] datas = content.split(separator);
        List<String> responseList = new ArrayList<>();
        
        for (String data : datas) {
            try {
                String[] split = data.split(indexSeparator);
                responseList.add(parseData(split[1]));
            } catch (Exception e) {
                responseList.add("{}");
                e.printStackTrace();
            }
        }
        String join = String.join(separator, responseList);
        
        ParserOuterClass.Response response = ParserOuterClass.Response.newBuilder().setContent(ByteString.copyFrom(join.getBytes())).build();
        responseObserver.onNext(response);
        responseObserver.onCompleted();
    }

    public static void main(String[] args) throws InterruptedException {
        int availablePort = RandomUtils.nextInt(10000, 12000);
        Server server = null;
        for (int i = availablePort; i < 60000; i++) {
            try {
                server = ServerBuilder.forPort(i)
                        .maxInboundMessageSize(100 * 1024 * 1024)
                        .addService(new Demo())
                        .build()
                        .start();
                break;
            } catch (IOException e) {
                // Port unavailable, try the next one
            }
        }
        assert server != null;
        // ‼️重要：此行输出信息供logbus获取，格式不能变动
        System.out.println("1|1|tcp|127.0.0.1:" + server.getPort() + "|grpc");
        server.awaitTermination();
    }
}
```

### Python版本

```python
import random
from concurrent import futures
import socket
import sys
import json
import grpc
import parser_pb2
import parser_pb2_grpc
from grpc_health.v1.health import HealthServicer
from grpc_health.v1 import health_pb2, health_pb2_grpc

separator = ":ta:"
index_separator = "|ta|"

class ParserServicer(parser_pb2_grpc.ParserServicer):
    def Parse(self, request, context):
        data = request.content
        result = parser_pb2.Response()
        data_list = data.decode('utf-8').split(separator)
        return_data_list = []
        for data in data_list:
            try:
                raw_data_list = data.replace('\r\n', '').split(index_separator)
                parse_data = json.loads(raw_data_list[1])
                new_parse_data = {}
                new_parse_data["properties"] = parse_data.copy()
                new_parse_data["#account_id"] = parse_data["ACCOUNTID"]
                new_parse_data["#distinct_id"] = parse_data["OSTYPE"]
                new_parse_data["#type"] = "track"
                new_parse_data["#ip"] = parse_data["IP"]
                new_parse_data["#uuid"] = parse_data["UID"]
                new_parse_data["#time"] = parse_data["LOGTM"]
                new_parse_data["#event_name"] = "event_" + str(parse_data["CODE"])
                return_data_list.append(json.dumps(new_parse_data))
            except Exception as ve:
                return_data_list.append('{}')
        result.content = separator.join(return_data_list).encode('utf-8')
        return result

def serve():
    health = HealthServicer()
    health.set("plugin", health_pb2.HealthCheckResponse.ServingStatus.Value('SERVING'))
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10), options=[
         ('grpc.max_send_message_length', 4 * 1024 * 1024),
         ('grpc.max_receive_message_length', 4 * 1024 * 1024),
    ])
    parser_pb2_grpc.add_ParserServicer_to_server(ParserServicer(), server)
    health_pb2_grpc.add_HealthServicer_to_server(health, server)
    port = get_open_port_in_random_range()
    server.add_insecure_port(f'127.0.0.1:{port}')
    server.start()
    try:
        # ‼️重要：此行输出信息供logbus获取，格式不能变动
        print(f'1|1|tcp|127.0.0.1:{port}|grpc')
        sys.stdout.flush()
        while True:
            time.sleep(60*60*24)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()
```

## 三、本地gRPC调试

创建本地调试 gRPC 客户端，服务端启动后再启动客户端发送消息。

### Java客户端

```java
public class ProtoClient {
    private static final String indexSeparator = "|ta|";

    public static void main(String[] args) {
        String event = "{\"#type\":\"track\",\"#time\":\"2023-09-05 18:58:17.021\",\"#event_name\":\"test\",\"#account_id\":\"test\",\"properties\":{\"#lib\":\"tga_python_sdk\"}}";

        ManagedChannel channel = ManagedChannelBuilder.forAddress("127.0.0.1", 12345)
                .usePlaintext()
                .build();
        ParserGrpc.ParserBlockingStub stub = ParserGrpc.newBlockingStub(channel);
        ParserOuterClass.Request request = ParserOuterClass.Request.newBuilder()
                .setContent(ByteString.copyFrom(("ta.log"+ indexSeparator + event).getBytes()))
                .build();

        try {
            ParserOuterClass.Response response = stub.parse(request);
            System.out.println("Server Response: " + response.getContent().toStringUtf8());
        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            channel.shutdown();
        }
    }
}
```

### Python客户端

```python
import grpc
import parser_pb2
import parser_pb2_grpc

def send_grpc_request():
    channel = grpc.insecure_channel('127.0.0.1:12345')
    stub = parser_pb2_grpc.ParserStub(channel)
    event = '{"#type":"track","#time":"2023-09-04 16:46:06.055","#event_name":"test","#distinct_id":"test"}'
    request = parser_pb2.Request(content=f'1.log|ta|{event}'.encode('utf-8'))
    response = stub.Parse(request)
    print("Response received:", response.content)

if __name__ == '__main__':
    send_grpc_request()
```

## 四、配置

### Logbus2配置文件

```json
{
  "datasource": [
    {
      "file_patterns": ["/path/server_log/*log"],
      "app_id": "debug-appid",
      "parser": {
        "cmd": "java -jar /path/lib/xxx.jar",
        "depend_sh": "true",
        "separator": ":ta:",
        "hand_shake": {
          "protocol_version": 1,
          "magic_cookie_key": "LogBus",
          "magic_cookie_value": "v2"
        }
      }
    }
  ],
  "push_url": "http://push_url"
}
```

> 注：注释部分启动前要去除

## 五、FAQ

1. **启动时报错：Unrecongnized remote plugin message......latest protocol**

原因：程序使用的proto生成文件非最新，Logbus客户端校验失败

解决：参考准备工作部分，重新根据proto文件生成java类或python文件

2. **日志中报错：Parser return data is invalid: length is changed**

原因：目前版本Logbus2转译插件会校验数据转译前后条数是否相同，如果不同会导致校验失败

解决：确认转译前后数据条数是否相同，如果需要一转多功能，请使用parser.batch_separator进行数据拼接

3. **Logbus日志中报错：rpc error: code = Canceled desc = stream terminated by RST_STREAM with error code: CANCEL**

同时Java程序报错：io.grpc.StatusRuntimeException: RESOURCE_EXHAUSTED: gRPC message exceeds maximum size

原因：转译程序设置的传输数据字节数过小，导致logbus和Java转移程序RPC通信传输数据失败

解决：增加程序中的最大传输字节数，Java设置：maxInboundMessageSize(100*1024*1024)

4. **启动时报错：plugin [parser] start failed: fork/exec /bin/sh: bad file descriptor**

原因：由于插件编译器兼容性问题当前无法在mac环境运行

解决：需在linux / windows环境运行