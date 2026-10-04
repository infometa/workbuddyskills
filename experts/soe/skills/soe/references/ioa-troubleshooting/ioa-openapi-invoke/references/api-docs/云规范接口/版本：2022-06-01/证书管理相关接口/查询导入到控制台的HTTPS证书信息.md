## 1. 接口描述




获取证书管理里的HTTPS证书列表。私有化从8.7版本开始支持，调用path为：capi/WebGateway/DescribeCertificates

## 2. 输入参数


| 参数名称 | 必选 | 类型 | 描述 |
|---------|---------|---------|---------|
| CertName | 否 | String | <strong><font color="blue"></font></strong>控制台上配置的证书名称，为空时表示查询所有证书<br/>示例值：test-资源绑定2 |
| Condition | 否 | [Condition](/开放API/云规范接口/版本：2022-06-01/数据结构.md#Condition) | <strong><font color="blue"></font></strong>分页参数。若不传，则默认获取第1页，每页10条数据。 |

## 3. 输出参数

| 参数名称 | 类型 | 描述 |
|---------|---------|---------|
| Data | [DescribeCertificatePageRsp](/开放API/云规范接口/版本：2022-06-01/数据结构.md#DescribeCertificatePageRsp) | <strong><font color="blue"></font></strong>分页返回证书信息|
| RequestId | String | 唯一请求 ID，由服务端生成，每次请求都会返回（若请求因其他原因未能抵达服务端，则该次请求不会获得 RequestId）。定位问题时需要提供该次请求的 RequestId。|

## 4. 示例

### 示例1 分页查询全量证书信息

#### 输入示例

```
POST / HTTP/1.1
Host: ioa.tencentcloudapi.com
Content-Type: application/json
X-TC-Action: DescribeCertificates
<公共请求参数>

{
    "CertName": ""
}
```

#### 输出示例

```json
{
    "Response": {
        "Data": {
            "Page": {
                "Total": 2,
                "PageCount": 1,
                "PageSize": 10,
                "PageNum": 1
            },
            "Items": [
                {
                    "CertSN": "16298458079499310568",
                    "CertId": 1,
                    "Domain": [
                        "www.exaexamqeqexamqeqmple.com",
                        "*.exampleexamqeqexamqeq.com",
                        "a.bexampexamqeqexamqeqle.com",
                        "b.aexamplexamqeqexamqeqe.com",
                        "w.cexamexamqeqexamqeqple.com",
                        "q.aexamqeqweqweqweqweple.com",
                        "131231312313131313131.cn",
                        "*.example.com"
                    ],
                    "CertExpTime": "2032-04-11 11:38:49",
                    "CertName": "test-资源绑定2",
                    "IsUsed": 1,
                    "CertContent": "{\"Certificate\":{\"Data\":{\"Version\":\"\\u0003\",\"Serial Number\":\"16298458079499310568\",\"Signature Algorithm\":\"SHA256-RSA\",\"Issuer\":\"CN=*.example.com,OU=My Department,O=My Company,L=Beijing,ST=Beijing,C=CN,1.2.840.113549.1.9.1=#0c11656d61696c406578616d706c652e636f6d\",\"Validity\":{\"Not Before\":\"Thu Apr 14 11:38:49 UTC 2022\",\"Not After\":\"Sun Apr 11 11:38:49 UTC 2032\"},\"Subject\":\"CN=*.example.com,OU=My Department,O=My Company,L=Beijing,ST=Beijing,C=CN,1.2.840.113549.1.9.1=#0c11656d61696c406578616d706c652e636f6d\",\"X509v3 Extensions\":{\"X509v3 Subject Alternative Name\":\"[\\\"www.exaexamqeqexamqeqmple.com\\\",\\\"*.exampleexamqeqexamqeq.com\\\",\\\"a.bexampexamqeqexamqeqle.com\\\",\\\"b.aexamplexamqeqexamqeqe.com\\\",\\\"w.cexamexamqeqexamqeqple.com\\\",\\\"q.aexamqeqweqweqweqweple.com\\\",\\\"131231312313131313131.cn\\\",\\\"*.example.com\\\"]\"}},\"Signature Algorithm\":\"SHA256-RSA\\n9a087a433664f2b465200211b3eaa98035b1104eafd05c2906ed73b43faa2035a4d947ec7d771ff8b8a763e01e3475499b79ccf21d80c7cb93074c41d031d6a156e9fd6320f7197cd0d3e1b3b7600738f67fdcdd63120fdc375532a56a935e13db6667997c3ef349fc68d2eabb411a90bcf83a171a8181455f7364a9b13dae3573640645def5c253cf913edf0aee814cad395501177e547a0095c391bbf8038e721d92f2ed76d03ff0cbccecfd9de73662b5958b6069755c214a08eb266a34fe6bc89f027a588c523da5e4e05ecdc0d2519c89739bfb702cb1d01f401640732efcc997aa1aa747df7b4bf26a5f09b239bd2b91ef06999b85db41c0e2c21a96e1\"}}",
                    "CertType": 0,
                    "CertFileName": "example.com.cert",
                    "KeyFileName": "example.com.key",
                    "CertAddTime": "2022-10-18 11:50:18"
                },
                {
                    "CertSN": "18462019641109096447571281102490891760",
                    "CertId": 9,
                    "Domain": [
                        "*.ioa-2-gateway.woa.com",
                        "ioa-2-gateway.woa.com",
                        "*.ioa-2-gateway.woa.com"
                    ],
                    "CertExpTime": "2023-11-23 23:59:59",
                    "CertName": "网关证书",
                    "IsUsed": 1,
                    "CertContent": "{\"Certificate\":{\"Data\":{\"Version\":\"\\u0003\",\"Serial Number\":\"18462019641109096447571281102490891760\",\"Signature Algorithm\":\"SHA256-RSA\",\"Issuer\":\"CN=DigiCert Secure Site CN CA G3,O=DigiCert Inc,C=US\",\"Validity\":{\"Not Before\":\"Wed Nov 23 00:00:00 UTC 2022\",\"Not After\":\"Thu Nov 23 23:59:59 UTC 2023\"},\"Subject\":\"CN=*.ioa-2-gateway.woa.com,O=Tencent Technology (Shenzhen) Company Limited,L=Shenzhen,ST=Guangdong Province,C=CN\",\"X509v3 Extensions\":{\"X509v3 Subject Alternative Name\":\"[\\\"*.ioa-2-gateway.woa.com\\\",\\\"ioa-2-gateway.woa.com\\\",\\\"*.ioa-2-gateway.woa.com\\\"]\"}},\"Signature Algorithm\":\"SHA256-RSA\\n2f17c1ed14e39640aace23914399b27b85ef65656273ab6efb22aef8daf5ef19d9f80273b17d297ae3e3e2b7b9fcbcae8ee6d1bc9ec6f2e5ce816841cbc53764e9c5b856c6195c388d1dc34378e9f978b90f2643798749d1fbc1284159f1ed5122c8b1e97c6adc74b35623c7a317e87c88ab3e7d5cd3515e293def6aaf6bf7e800680bf90b8f58596ff38715bbebdf13da82a78cad61390ceaa06529dd668d8cda76969d6be31743da1ab7cfae44cee473a8add8d8e036018b4b1a265a33008874b8124764de0824c53fff25f2bec75dd69303e89d7333e832920e4476923e7c0a72e489e42f05fd28e93007cf2da33e04b544876923d53b01a3e6edc908d107\"}}",
                    "CertType": 0,
                    "CertFileName": "svr.crt",
                    "KeyFileName": "svr.key",
                    "CertAddTime": "2023-01-06 10:41:48"
                }
            ]
        },
        "RequestId": "pftest"
    }
}
```

### 示例2 查询单条证书信息

#### 输入示例

```
POST / HTTP/1.1
Host: ioa.tencentcloudapi.com
Content-Type: application/json
X-TC-Action: DescribeCertificates
<公共请求参数>

{
    "CertName": "test-资源绑定2"
}
```

#### 输出示例

```json
{
    "Response": {
        "Data": {
            "Page": {
                "PageCount": 1,
                "PageSize": 10,
                "PageNum": 1,
                "Total": 1
            },
            "Items": [
                {
                    "CertAddTime": "2022-10-18 11:50:18",
                    "CertExpTime": "2032-04-11 11:38:49",
                    "IsUsed": 1,
                    "CertContent": "{\"Certificate\":{\"Data\":{\"Version\":\"\\u0003\",\"Serial Number\":\"16298458079499310568\",\"Signature Algorithm\":\"SHA256-RSA\",\"Issuer\":\"CN=*.example.com,OU=My Department,O=My Company,L=Beijing,ST=Beijing,C=CN,1.2.840.113549.1.9.1=#0c11656d61696c406578616d706c652e636f6d\",\"Validity\":{\"Not Before\":\"Thu Apr 14 11:38:49 UTC 2022\",\"Not After\":\"Sun Apr 11 11:38:49 UTC 2032\"},\"Subject\":\"CN=*.example.com,OU=My Department,O=My Company,L=Beijing,ST=Beijing,C=CN,1.2.840.113549.1.9.1=#0c11656d61696c406578616d706c652e636f6d\",\"X509v3 Extensions\":{\"X509v3 Subject Alternative Name\":\"[\\\"www.exaexamqeqexamqeqmple.com\\\",\\\"*.exampleexamqeqexamqeq.com\\\",\\\"a.bexampexamqeqexamqeqle.com\\\",\\\"b.aexamplexamqeqexamqeqe.com\\\",\\\"w.cexamexamqeqexamqeqple.com\\\",\\\"q.aexamqeqweqweqweqweple.com\\\",\\\"131231312313131313131.cn\\\",\\\"*.example.com\\\"]\"}},\"Signature Algorithm\":\"SHA256-RSA\\n9a087a433664f2b465200211b3eaa98035b1104eafd05c2906ed73b43faa2035a4d947ec7d771ff8b8a763e01e3475499b79ccf21d80c7cb93074c41d031d6a156e9fd6320f7197cd0d3e1b3b7600738f67fdcdd63120fdc375532a56a935e13db6667997c3ef349fc68d2eabb411a90bcf83a171a8181455f7364a9b13dae3573640645def5c253cf913edf0aee814cad395501177e547a0095c391bbf8038e721d92f2ed76d03ff0cbccecfd9de73662b5958b6069755c214a08eb266a34fe6bc89f027a588c523da5e4e05ecdc0d2519c89739bfb702cb1d01f401640732efcc997aa1aa747df7b4bf26a5f09b239bd2b91ef06999b85db41c0e2c21a96e1\"}}",
                    "CertName": "test-资源绑定2",
                    "Domain": [
                        "www.exaexamqeqexamqeqmple.com",
                        "*.exampleexamqeqexamqeq.com",
                        "a.bexampexamqeqexamqeqle.com",
                        "b.aexamplexamqeqexamqeqe.com",
                        "w.cexamexamqeqexamqeqple.com",
                        "q.aexamqeqweqweqweqweple.com",
                        "131231312313131313131.cn",
                        "*.example.com"
                    ],
                    "CertType": 0,
                    "CertFileName": "example.com.cert",
                    "KeyFileName": "example.com.key",
                    "CertId": 1,
                    "CertSN": "16298458079499310568"
                }
            ]
        },
        "RequestId": "pftest"
    }
}
```











## 5. 错误码


| 错误码 | 描述 |
|---------|---------|
| InternalError.DatabaseException | 内部错误，数据库异常。 |
