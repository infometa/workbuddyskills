# 开放实验平台 AI 模型调用接口文档（肺炎 AI）V2.0

**特别说明**：以下模型能力均仅限中国大陆地区科研用途售卖和使用，不得直接用于临床检测与诊疗等目的。

- 支持模型（需鉴权）：
  1. 肺炎 AI 检测（异步模式）

本接口采用异步模式：先通过 **提交接口** 上传胸部 CT DICOM 压缩包，获取 `taskId`；再通过 **查询接口** 轮询获取分析结果。计费由服务端后台轮询器在 AI 分析完成后自动扣减，提交时不预留配额。

---

## 一、鉴权方式

### 1.1 签名算法

采用 HMAC-SHA256 签名算法，计算公式如下：

```
signature = HMAC-SHA256(token, appId + timestamp)
```

| 参数 | 说明 | 备注 |
|------|------|------|
| `appId` | 合作方 ID | 由系统分配 |
| `token` | 密钥 | 由系统分配，需妥善保管 |
| `timestamp` | 时间戳 | 当前时间的秒级时间戳 |
| `signature` | 签名 | 根据上述公式计算得出 |

### 1.2 请求头参数

| Header 字段 | 必填 | 说明 |
|-------------|------|------|
| `appId` | 是 | 合作方 ID |
| `timestamp` | 是 | 秒级时间戳，服务器允许一定误差 |
| `signature` | 是 | 根据 1.1 计算出的签名 |

### 1.3 签名生成示例

#### Python

```python
import hmac, hashlib, time

appId = "your_app_id"
token = "your_token"
timestamp = str(int(time.time()))
message = (appId + timestamp).encode("utf-8")
signature = hmac.new(token.encode("utf-8"), message, hashlib.sha256).hexdigest()
```

#### Java

```java
String appId = "your_app_id";
String token = "your_token";
String timestamp = String.valueOf(System.currentTimeMillis() / 1000);
Mac mac = Mac.getInstance("HmacSHA256");
mac.init(new SecretKeySpec(token.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
byte[] raw = mac.doFinal((appId + timestamp).getBytes(StandardCharsets.UTF_8));
StringBuilder sb = new StringBuilder();
for (byte b : raw) sb.append(String.format("%02x", b));
String signature = sb.toString();
```

---

## 二、计费规则

1. **计费原则**：采用异步计费模式，提交时仅做资源有效性校验（不预留配额），由服务端后台轮询器在 AI 分析完成后自动扣减配额。
2. **计费单位**：每个 `taskId`（任务ID）代表一次计费。
3. **失败不扣费**：引擎处理失败（如图像不合格、超时等）不会扣减配额。
4. **防重复扣费**：系统通过数据库唯一键机制保障同一 taskId 仅扣费一次。
5. **重复请求**：相同文件使用不同 `studyId` 多次提交，将生成不同 `taskId`，按多次计费。

---

## 三、接口说明

### 3.1 通用响应头（`head`）

所有响应共享统一的头结构：

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | int | 业务状态码：`0` 成功，非 `0` 失败（详见 3.6） |
| `message` | string | 状态描述 |
| `resourceRemaining` | int | 剩余可用配额次数 |
| `requestId` | string | 请求唯一标识，便于排查（格式：`req_{appId}_{纳秒时间戳}`） |
| `taskId` | string | 任务 ID（格式：`{studyId}_{毫秒时间戳}`） |
| `studyInstanceUID` | string | 从 DICOM 文件中读取的 Study UID |
| `seriesInstanceUID` | string | 从 DICOM 文件中读取的 Series UID |

---

### 3.2 肺炎 AI 提交接口

- **接口路径**：`https://pacs.qq.com/openapi/pneumoniaSubmit`
- **请求方式**：`POST`
- **Content-Type**：`multipart/form-data`
- **数据要求**：胸部 CT 序列 DICOM 文件压缩包（ZIP 格式），最大 300MB

#### 请求参数

通过 `multipart/form-data` 表单提交：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `studyId` | string | 是 | 检查 ID，唯一标识一次检查 |
| `dicomFile` | file | 是 | DICOM 文件压缩包（ZIP 格式），最大 300MB |
| `studyDate` | string | 否 | 检查时间的秒级时间戳（为空时使用服务器当前时间） |
| `needReport` | string | 否 | 是否需要输出报告：`0` 不需要（默认），`1` 需要 |
| `patientId` | string | 否 | 患者 ID |
| `patientName` | string | 否 | 患者姓名（用于报告） |
| `patientGender` | string | 否 | 患者性别：`0` 未知，`1` 男，`2` 女 |
| `patientAge` | string | 否 | 患者年龄（整数） |
| `studyName` | string | 否 | 检查项目（如"胸部CT"），为空时使用 DICOM 中的 StudyDescription |

#### DICOM 文件处理逻辑

系统收到 ZIP 包后会执行以下处理：
1. 解压 ZIP，跳过目录、隐藏文件（以 `.` 开头）和系统文件（如 `__MACOSX`）
2. 按 `SeriesInstanceUID` 对 DICOM 文件分组
3. 过滤图片数量 ≤ 10 张的序列
4. 选取图像数量最多的序列进行分析
5. 提取 `StudyInstanceUID`、`SeriesInstanceUID`、`StudyDescription`

#### 响应字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `head` | object | 通用响应头（见 3.1）。`code=0` 表示提交成功，`head.taskId` 为后续查询所用（格式：`{studyId}_{毫秒时间戳}`） |

#### 请求示例（cURL）

```bash
curl -X POST "https://pacs.qq.com/openapi/pneumoniaSubmit" \
  -H "appId: your_app_id" \
  -H "timestamp: 1714000000" \
  -H "signature: a3b2c1d4..." \
  -F "studyId=STUDY_001" \
  -F "studyDate=1714000000" \
  -F "needReport=1" \
  -F "patientName=张三" \
  -F "patientGender=1" \
  -F "patientAge=50" \
  -F "studyName=胸部CT" \
  -F "dicomFile=@chest_ct.zip"
```

#### 响应示例（提交成功）

```json
{
  "head": {
    "code": 0,
    "message": "success",
    "resourceRemaining": 9999,
    "requestId": "req_100001_1714000000123456789",
    "taskId": "STUDY_001_1714000000123",
    "studyInstanceUID": "1.2.840.113619.2.55.3.604688.12345",
    "seriesInstanceUID": "1.2.840.113619.2.55.3.604688.67890"
  }
}
```

#### 响应示例（数据格式错误）

```json
{
  "head": {
    "code": 90001,
    "message": "DICOM文件解压失败: 打开zip文件失败: ...",
    "resourceRemaining": 9999,
    "requestId": "req_100001_1714000000123456789",
    "taskId": "STUDY_001_1714000000123",
    "studyInstanceUID": "",
    "seriesInstanceUID": ""
  }
}
```

---

### 3.3 肺炎 AI 查询接口

- **接口路径**：`https://pacs.qq.com/openapi/pneumoniaQuery`
- **请求方式**：`POST`
- **Content-Type**：`application/json`

#### 请求参数（Body，JSON）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `taskId` | string | 是 | 提交时返回的 `head.taskId`（支持多个 taskId 以英文分号 `;` 分隔） |
| `studyId` | string | 否 | 检查唯一标识（可选） |
| `needReport` | string | 否 | 是否需要报告：`0` 不需要，`1` 需要 |

#### 响应字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `head` | object | 通用响应头（见 3.1） |
| `studyId` | string | 任务标识（与 `taskId` 一致） |
| `status` | string | AI 分析状态（见下表） |
| `pneumoniaSign` | string | AI 肺炎表征结果（仅处理完成时返回，格式：`肺炎表征 : XX.X%`） |
| `pneumoniaAnalysis` | string | AI 肺炎分析结果，格式化的病灶详情文本（仅处理完成时返回） |
| `reportUrl` | string | AI 分析 PDF 报告 URL（仅 `needReport=1` 且处理完成时返回） |

#### `status` 状态值

| status | 含义 | 说明 |
|--------|------|------|
| 待处理 | 任务已接收，尚未开始处理 | 请稍后重试查询 |
| 处理中 | AI 正在分析中 | 请稍后重试查询 |
| 处理完成 | 分析成功，已返回结果 | 读取 `pneumoniaSign` 和 `pneumoniaAnalysis` |
| 处理失败 | 分析失败或 taskId 无效 | 不计费，`head.message` 为 "taskId无效或任务不存在" |

#### `pneumoniaSign` 格式说明

当 `status` 为"处理完成"时，`pneumoniaSign` 返回肺炎表征描述及风险概率：

```
肺炎表征 : 97.5%
```

概率计算公式：`risk = (1 - probabilities[2]) * 100`，保留一位小数。

#### `pneumoniaAnalysis` 格式说明

当 `status` 为"处理完成"时，`pneumoniaAnalysis` 返回格式化的分析结果，包含两部分：

**第一部分**：全肺感染比例摘要

```
占全肺6.2%; 左肺 肺炎占3.1%; 右肺 肺炎占9.3%
```

若无感染则为：`该患者无肺炎感染`

**第二部分**：病灶详情列表

```
共3处肺炎感染:
（1）右肺上叶【99 / 182】，体积77657mm³，占右肺体积6.6%，平均CT值-603HU
（2）右肺下叶【157 / 210】，体积49177mm³，占右肺体积4.2%，平均CT值-511HU
（3）右肺中叶【181 / 206】，体积4668mm³，占右肺体积0.4%，平均CT值-495HU
```

各字段含义：
- `占全肺X.X%`：全肺感染体积占比
- `左肺 肺炎占X.X%`：左肺感染体积占比
- `右肺 肺炎占X.X%`：右肺感染体积占比
- `（N）`：病灶序号
- `[位置]`：病灶所在肺叶（左肺上叶/左肺下叶/右肺上叶/右肺中叶/右肺下叶）
- `【起始层 / 结束层】`：病灶在 CT 序列中的层号范围
- `体积Xmm³`：病灶体积
- `占[左/右]肺体积X.X%`：病灶占对应侧肺的体积比
- `平均CT值XHU`：病灶区域的平均 CT 值

#### 多 taskId 查询

支持传入多个 taskId（以英文分号 `;` 分隔），聚合规则：
- 任一 taskId 还在处理中（待处理/处理中）→ 整体返回 `status = "处理中"`
- 全部完成（处理完成/处理失败）→ 合并成功结果，`pneumoniaSign`、`pneumoniaAnalysis`、`reportUrl` 以 JSON 对象格式返回（key 为 taskId）

#### 请求示例（cURL）

```bash
curl -X POST "https://pacs.qq.com/openapi/pneumoniaQuery" \
  -H "Content-Type: application/json" \
  -H "appId: your_app_id" \
  -H "timestamp: 1714000060" \
  -H "signature: b4c3d2e5..." \
  -d '{
    "taskId": "STUDY_001_1714000000123",
    "needReport": "1"
  }'
```

#### 响应示例（处理完成）

```json
{
  "head": {
    "code": 0,
    "message": "success",
    "resourceRemaining": 9999,
    "requestId": "req_100001_1714000060987654321",
    "taskId": "STUDY_001_1714000000123",
    "studyInstanceUID": "",
    "seriesInstanceUID": ""
  },
  "studyId": "STUDY_001_1714000000123",
  "status": "处理完成",
  "pneumoniaSign": "肺炎表征 : 97.5%",
  "pneumoniaAnalysis": "占全肺6.2%; 左肺 肺炎占3.1%; 右肺 肺炎占9.3%\n\n共3处肺炎感染:\n（1）右肺上叶【99 / 182】，体积77657mm³，占右肺体积6.6%，平均CT值-603HU\n（2）右肺下叶【157 / 210】，体积49177mm³，占右肺体积4.2%，平均CT值-511HU\n（3）右肺中叶【181 / 206】，体积4668mm³，占右肺体积0.4%，平均CT值-495HU",
  "reportUrl": "https://miying.qq.com/webserver/pacsStudyReport?pacsStudyId=STUDY_001_1714000000123&studyType=4&engine=10&timestamp=1714000060123&token=abc123..."
}
```

#### 响应示例（处理中）

```json
{
  "head": {
    "code": 0,
    "message": "success",
    "resourceRemaining": 10000,
    "requestId": "req_100001_1714000030111222333",
    "taskId": "STUDY_001_1714000000123",
    "studyInstanceUID": "",
    "seriesInstanceUID": ""
  },
  "studyId": "STUDY_001_1714000000123",
  "status": "处理中",
  "pneumoniaSign": "",
  "pneumoniaAnalysis": "",
  "reportUrl": ""
}
```

#### 响应示例（处理失败）

```json
{
  "head": {
    "code": 90002,
    "message": "taskId无效或任务不存在",
    "resourceRemaining": 10000,
    "requestId": "req_100001_1714000090111222333",
    "taskId": "INVALID_TASK_ID",
    "studyInstanceUID": "",
    "seriesInstanceUID": ""
  },
  "studyId": "INVALID_TASK_ID",
  "status": "处理失败",
  "pneumoniaSign": "",
  "pneumoniaAnalysis": "",
  "reportUrl": ""
}
```

#### 响应示例（多 taskId 查询 - 全部完成）

```json
{
  "head": {
    "code": 0,
    "message": "success",
    "resourceRemaining": 9998,
    "requestId": "req_100001_1714000090111222333",
    "taskId": "STUDY_001_1714000000123;STUDY_002_1714000000456",
    "studyInstanceUID": "",
    "seriesInstanceUID": ""
  },
  "studyId": "STUDY_001_1714000000123;STUDY_002_1714000000456",
  "status": "处理完成",
  "pneumoniaSign": "{\"STUDY_001_1714000000123\":\"肺炎表征 : 97.5%\",\"STUDY_002_1714000000456\":\"肺炎表征 : 45.2%\"}",
  "pneumoniaAnalysis": "{\"STUDY_001_1714000000123\":\"占全肺6.2%; ...\",\"STUDY_002_1714000000456\":\"该患者无肺炎感染\"}",
  "reportUrl": "{\"STUDY_001_1714000000123\":\"https://miying.qq.com/...\"}"
}
```

---

### 3.4 推荐轮询策略

肺炎 AI 处理时间通常在 **3~10 分钟**（取决于 CT 序列数量），建议：

1. 提交成功后等待 **30 秒** 开始首次查询
2. 每次查询间隔 **10 秒**
3. 最大轮询次数 **300 次**（总时长约 50 分钟，覆盖绝大多数场景）
4. 当 `status` 为"处理完成"或"处理失败"时停止轮询
5. **轮询期间持续反馈**：每次查询后向用户反馈当前进度（轮询次数、已等待时长、状态），不要停止反馈
6. 超过 300 次仍未完成时，告知用户任务仍在处理中，可凭 `taskId` 继续查询；任务最长有效期为 **24 小时**

---

### 3.5 业务状态码（`head.code`）

| code | 枚举名 | 含义 |
|------|--------|------|
| `0` | SUCCESS | 成功 |
| `1` | PARAM_ERROR | 参数错误（如 `studyId` 为空、`dicomFile` 缺失、multipart 解析失败） |
| `10001` | DB_ERROR | 数据库错误 |
| `10002` | QUOTA_INSUFFICIENT | 剩余配额不足或资源已过期 |
| `10003` | INVALID_TOKEN | Token 失效或签名错误 |
| `10004` | INVALID_SIGNATURE | 签名验证失败或资源配置未找到 |
| `10005` | CUSTOMER_CLOSED | 客户状态已关闭 |
| `90001` | DATA_FORMAT_ERROR | 数据格式错误（如 ZIP 解压失败、无有效 DICOM 文件、未找到有效图像） |
| `90002` | AI_INFERENCE_ERROR | AI 引擎调用失败（上传失败、taskId 无效或任务不存在） |

---

## 四、调用示例

### 4.1 Python 完整示例

```python
import hmac, hashlib, time, json, requests

APP_ID = "your_app_id"
TOKEN  = "your_token"
HOST   = "https://pacs.qq.com"

# 1. 提交任务
timestamp = str(int(time.time()))
signature = hmac.new(
    TOKEN.encode("utf-8"),
    (APP_ID + timestamp).encode("utf-8"),
    hashlib.sha256,
).hexdigest()

headers = {
    "appId": APP_ID,
    "timestamp": timestamp,
    "signature": signature,
}

files = {"dicomFile": ("chest_ct.zip", open("chest_ct.zip", "rb"), "application/zip")}
data = {
    "studyId": "STUDY_001",
    "studyDate": str(int(time.time())),
    "needReport": "1",
    "patientName": "张三",
    "patientGender": "1",
    "patientAge": "50",
    "studyName": "胸部CT",
}

resp = requests.post(f"{HOST}/openapi/pneumoniaSubmit",
                     headers=headers, files=files, data=data, timeout=600)
result = resp.json()
print("提交结果:", result)
task_id = result["head"]["taskId"]

# 2. 轮询查询
import time as t
t.sleep(30)  # 首次等待30秒

for i in range(300):
    timestamp = str(int(time.time()))
    signature = hmac.new(
        TOKEN.encode("utf-8"),
        (APP_ID + timestamp).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    headers = {
        "Content-Type": "application/json",
        "appId": APP_ID,
        "timestamp": timestamp,
        "signature": signature,
    }
    body = {"taskId": task_id, "needReport": "1"}
    resp = requests.post(f"{HOST}/openapi/pneumoniaQuery",
                         headers=headers, json=body, timeout=30)
    data = resp.json()

    status = data.get("status", "")
    print(f"轮询 {i+1}: status={status}")

    if status in ("处理完成", "处理失败"):
        print(json.dumps(data, ensure_ascii=False, indent=2))
        break

    t.sleep(10)  # 每10秒查询一次
```

---

## 五、注意事项

- **密钥安全**：`token` 不得出现在前端、日志或客户端代码中；仅在服务端参与签名。
- **时间戳对齐**：本地时钟需与 NTP 同步，时间戳与服务器偏差过大将导致鉴权失败。
- **文件格式**：DICOM 文件需打包为 ZIP 格式上传，ZIP 内不应包含非 DICOM 文件（如 `__MACOSX`、隐藏文件等）。
- **文件大小**：ZIP 包不超过 300 MB（服务端 multipart 限制）。
- **序列要求**：ZIP 包中至少需包含一个图像数量 > 10 张的 CT 序列，否则系统将回退到使用全部图像。
- **并发控制**：请根据签约并发阈值控制 QPS，避免触发限流。
- **配额监控**：请关注 `resourceRemaining`，及时续费。配额在 AI 分析完成后由后台异步扣减，提交时的 `resourceRemaining` 值可能略有延迟。
- **处理时间**：肺炎 AI 分析需要较长时间（3~10 分钟），请勿在提交后立即查询，建议等待 30 秒后开始轮询。
- **僵尸任务清理**：超过 24 小时未完成的任务将被系统自动标记为失败并移除，不计费。
- **taskId 格式**：提交成功后返回的 `taskId` 格式为 `{studyId}_{毫秒时间戳}`，查询时需使用完整 taskId。

---

## 六、技术支持

遇到问题时请提供以下信息：

- `appId`、`requestId`、`taskId`
- 调用时间（含时区）
- 请求头与请求参数
- 错误响应体完整内容

---

## 七、试用与正式使用

### 正式环境凭证

当前提供的正式环境凭证（脚本默认 host）：

| 项目 | 值 |
|------|------|
| 接口地址 | `https://pacs.qq.com` |
| APP-ID | 100002 |
| APP-TOKEN | ca27d176-d317-475f-8d1f-9cb54032a905 |

> 三个脚本（submit/query/poll）的 `--host` 参数默认值均为 `https://pacs.qq.com`，无需额外指定即可连接正式环境。

如需 sample 肺炎CT数据：可查询访问公开数据集，建议CT层厚＜2mm。

### 正式使用

如需长期使用，请联系 miying@tencent.com 或访问腾讯健康官网。

---

**文档版本**：V2.0（肺炎 AI 专版）
**更新日期**：2026-05-22
