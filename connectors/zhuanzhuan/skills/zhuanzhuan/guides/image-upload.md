# 图片上传与识别入参

估价回收涉及图片时，先按图片来源分流，再构造 `recognize_model` 的图片参数。

## 图片分流

- 用户明确提供 HTTP(S) 图片 URL：不要上传，原样放入 `picUrls`。
- 本地文件或聊天附件：调用免登录上传接口，取得 `fileIdStr` 后放入 `picFileIds`。
- 同时存在 URL 和本地文件：分别放入 `picUrls` 和 `picFileIds`，两类图片合计不超过 10 张。
- 当前环境无法读取附件或发起 HTTP 请求：请用户提供可访问的图片 URL，或改用文字描述商品；不要伪造 ID 或 URL。

不要把本地路径、`data:image/...`、blob 地址或上传返回的文件 ID 放入 `picUrls`。

## 本地图片上传

### 请求契约

- **Method**：`POST`
- **URL**：`https://app.zhuanzhuan.com/api/zaimcp/imageUpLoad`
- **Content-Type**：`multipart/form-data`
- **认证**：免登录，不添加 Authorization、Cookie 或 MCP Token
- **文件大小**：单张最大 10 MiB

表单只传一个字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `multipartFile` | file | 是 | 图片二进制；保留带后缀的文件名，并尽量提供正确的图片 MIME 类型 |


### curl 示例

把绝对路径替换为实际图片路径。每个本地文件只上传一次。

```bash
curl -sS -X POST "https://app.zhuanzhuan.com/api/zaimcp/imageUpLoad" \
  -F "multipartFile=@/absolute/path/photo.jpg;type=image/jpeg"
```

### FormData 示例

使用宿主的文件对象，不要手动设置 multipart 的 `Content-Type`，让运行时自动生成 boundary。

```javascript
const formData = new FormData();
formData.append("multipartFile", imageFile, imageFile.name);

const response = await fetch(
  "https://app.zhuanzhuan.com/api/zaimcp/imageUpLoad",
  { method: "POST", body: formData }
);
const result = await response.json();
```

## 上传响应

成功响应由网关包装，可能使用 `respCode` / `respData`，也可能使用 `code` / `data`。成功码必须为 `0`，业务数据中必须存在 `fileIdStr`：

```json
{
  "respCode": 0,
  "respData": {
    "fileIdStr": "2089553228894048257"
  }
}
```

处理规则：

1. 只读取 `respData.fileIdStr` 或 `data.fileIdStr`。
2. 缺少 `fileIdStr`、成功码非 `0`、HTTP 非成功状态或响应无法解析时，均视为上传失败。
3. 禁止回退读取数字类型 `fileId`；JavaScript Number 可能使 64 位 ID 丢失精度。
4. 不向用户展示文件 ID、上传原始响应、存储地址或内部参数。

多张本地图片逐张上传，按原顺序收集每次返回的 `fileIdStr`。上传失败的图片不要产生占位 ID，也不要为了“结果更干净”重复上传已成功的图片。

## 识别入参

调用 `recognize_model` 时：

- `picFileIds`：只放本次免登录上传接口返回的 `fileIdStr`，必须是带引号的字符串数组。
- `picUrls`：只放用户明确提供的 HTTP(S) 图片 URL。
- `query`：可补充用户真实描述；不要添加用户未说明的型号、容量、成色或故障情况。
- `picFileIds` 与 `picUrls` 合计最多 10 个。

本地图片上传成功后的正确示例：

```json
{
  "picFileIds": ["2089553228894048257"],
  "query": "帮我识别型号并估价"
}
```

多个上传结果的正确示例：

```json
{
  "picFileIds": [
    "2089553228894048257",
    "2089553228894048258"
  ]
}
```

禁止以下写法：

```json
{
  "picFileIds": [2089553228894048257],
  "picUrls": ["2089553228894048257"]
}
```

原因：`picFileIds` 中的 JSON Number 可能失真，文件 ID 也不是图片 URL。

## 失败处理

- 上传接口失败：停止本地图片识别，请用户重新提供图片、提供可访问 URL 或补充文字型号。
- 识别接口提示 `picFileIds` 类型错误：改为字符串数组后最多重试一次；不要重新上传已成功图片。
- 识别接口不接受 `picFileIds`：停止图片识别，不要改用旧 mediaproxy 接口、拼接图片 URL 或凭视觉猜测型号。
- 图片超过 10 MiB：可在环境具备安全压缩能力时压缩后重新上传；否则请用户提供较小图片。
