---
name: pneumonia-ai-diagnosis
description: 调用肺炎AI辅助诊断模型API，支持提交胸部CT DICOM压缩包进行异步分析、查询分析结果、以及自动轮询等待结果完成。采用HMAC-SHA256签名鉴权。触发词：肺炎检测、肺炎AI、胸部CT分析、pneumonia、DICOM、肺炎查询。
description_zh: 肺炎AI辅助诊断
description_en: Pneumonia AI Diagnosis
disable: false
agent_created: true
---

# 肺炎AI辅助诊断

肺炎医疗影像AI辅助诊断模型调用Skill。基于肺炎AI模型接口，支持异步提交胸部CT DICOM压缩包进行分析，查询/轮询获取肺炎检测结果。

> **特别说明**：以下模型能力均仅限中国大陆地区科研用途售卖和使用，不得直接用于临床检测与诊疗等目的。

---

## 一、触发条件

- 用户需要提交胸部CT DICOM压缩包进行肺炎AI分析
- 用户需要查询已有的肺炎AI分析任务结果
- 用户需要自动轮询等待肺炎AI分析结果
- 用户提及"肺炎检测"、"肺炎AI"、"胸部CT分析"、"DICOM分析"等关键词

---

## 二、鉴权方式

### 2.1 签名算法

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

### 2.2 请求头参数

| Header 字段 | 必填 | 说明 |
|-------------|------|------|
| `appId` | 是 | 合作方 ID |
| `timestamp` | 是 | 秒级时间戳，服务器允许一定误差 |
| `signature` | 是 | 根据 2.1 计算出的签名 |

### 2.3 首次使用

用户首次使用时需提供 `appId` 和 `token`，如缺失则主动询问：

```
请提供以下参数以使用肺炎AI诊断接口：
1. appId（合作方ID）
2. token（密钥）
```

> **安全提示**：`token` 不得出现在前端、日志或客户端代码中，仅在服务端参与签名计算。

---

## 三、接口说明

### 3.1 肺炎 AI 提交接口

- **接口路径**：`https://pacs.qq.com/openapi/pneumoniaSubmit`
- **请求方式**：`POST`
- **Content-Type**：`multipart/form-data`
- **数据要求**：胸部 CT 序列 DICOM 文件压缩包（ZIP 格式），最大 300MB

> 默认使用正式环境地址 `https://pacs.qq.com`，如需切换环境请通过 `--host` 参数指定。

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

#### 响应字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `head` | object | 通用响应头。`code=0` 表示提交成功，`head.taskId` 为后续查询所用（格式：`{studyId}_{毫秒时间戳}`） |
| `head.code` | int | 业务状态码：`0` 成功，非 `0` 失败（详见 3.4） |
| `head.message` | string | 状态描述 |
| `head.resourceRemaining` | int | 剩余可用配额次数 |
| `head.requestId` | string | 请求唯一标识（格式：`req_{appId}_{纳秒时间戳}`） |
| `head.taskId` | string | 任务 ID（格式：`{studyId}_{毫秒时间戳}`） |
| `head.studyInstanceUID` | string | 从 DICOM 文件中读取的 Study UID |
| `head.seriesInstanceUID` | string | 从 DICOM 文件中读取的 Series UID |

#### 调用方式

使用 Bash 工具执行脚本 `@scripts/pneumonia_submit.py`：

```bash
python3 {SKILL_DIR}/scripts/pneumonia_submit.py \
  --app_id "{appId}" \
  --token "{token}" \
  --study_id "{studyId}" \
  --dicom_file "{zip文件绝对路径}" \
  [--study_date "{检查时间戳}"] \
  [--need_report "1"] \
  [--patient_id "{患者ID}"] \
  [--patient_name "{患者姓名}"] \
  [--patient_gender "{1或2}"] \
  [--patient_age "{年龄}"] \
  [--study_name "{检查项目}"]
```

> `{SKILL_DIR}` 为本Skill的安装目录，执行时替换为实际路径。

---

### 3.2 肺炎 AI 查询接口

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
| `head` | object | 通用响应头 |
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

#### 调用方式

使用 Bash 工具执行脚本 `@scripts/pneumonia_query.py`：

```bash
python3 {SKILL_DIR}/scripts/pneumonia_query.py \
  --app_id "{appId}" \
  --token "{token}" \
  --task_id "{taskId}" \
  [--need_report "1"]
```

---

### 3.3 自动轮询等待结果

提交成功后自动轮询查询接口，直到任务完成或失败。脚本会持续输出轮询进度，便于实时反馈给用户。

#### 调用方式

使用 Bash 工具执行脚本 `@scripts/pneumonia_poll.py`：

```bash
python3 {SKILL_DIR}/scripts/pneumonia_poll.py \
  --app_id "{appId}" \
  --token "{token}" \
  --task_id "{taskId}" \
  [--need_report "1"] \
  [--initial_wait 30] \
  [--interval 10] \
  [--max_attempts 300]
```

参数说明：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--initial_wait` | 30 | 首次查询前等待秒数 |
| `--interval` | 10 | 轮询间隔秒数 |
| `--max_attempts` | 300 | 最大轮询次数 |

> **持续反馈**：轮询脚本所有进度信息均带 `flush=True` 输出，支持后台运行时实时捕获。建议将脚本放入后台执行（`run_in_background`），再通过 `TaskOutput` 定期检查输出并向用户反馈最新进度，不要在轮询期间停止反馈。

---

### 3.4 业务状态码（`head.code`）

| code | 枚举名 | 含义 | 处理方式 |
|------|--------|------|----------|
| `0` | SUCCESS | 成功 | 正常展示结果 |
| `1` | PARAM_ERROR | 参数错误（如 `studyId` 为空、`dicomFile` 缺失、multipart 解析失败） | 检查请求参数是否完整 |
| `10001` | DB_ERROR | 数据库错误 | 稍后重试或联系服务方 |
| `10002` | QUOTA_INSUFFICIENT | 剩余配额不足或资源已过期 | 提醒用户续费 |
| `10003` | INVALID_TOKEN | Token 失效或签名错误 | 检查 appId/token/时间戳是否正确 |
| `10004` | INVALID_SIGNATURE | 签名验证失败或资源配置未找到 | 检查 appId/token/时间戳是否正确 |
| `10005` | CUSTOMER_CLOSED | 客户状态已关闭 | 联系服务方 |
| `90001` | DATA_FORMAT_ERROR | 数据格式错误（如 ZIP 解压失败、无有效 DICOM 文件、未找到有效图像） | 检查ZIP包和DICOM文件格式 |
| `90002` | AI_INFERENCE_ERROR | AI 引擎调用失败（上传失败、taskId 无效或任务不存在） | 检查taskId是否有效 |

---

## 四、结果展示

将分析结果结构化展示给用户：

- **肺炎表征概率**：`pneumoniaSign` 值（如 "肺炎表征 : 97.5%"）
- **感染摘要**：全肺/左肺/右肺感染占比
- **病灶详情**：每处病灶的肺叶位置、层号范围、体积、体积占比、平均CT值
- **报告链接**：如 `needReport=1`，提供 PDF 报告 URL

`pneumoniaAnalysis` 格式说明：

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
- **持续反馈**：轮询期间应持续向用户反馈进度（如轮询次数、已等待时长、当前状态），不要在轮询过程中停止反馈。建议后台运行轮询脚本并定期检查输出。
- **僵尸任务清理**：超过 24 小时未完成的任务将被系统自动标记为失败并移除，不计费。
- **taskId 格式**：提交成功后返回的 `taskId` 格式为 `{studyId}_{毫秒时间戳}`，查询时需使用完整 taskId。
- **多 taskId 查询**：查询接口支持分号分隔的多个 taskId，聚合规则为：任一未完成则整体返回"处理中"。
- **重复计费**：相同文件用不同 studyId 多次提交会生成不同 taskId，按多次计费。

---

## 六、试用与正式使用

### 正式环境凭证

当前提供的正式环境凭证（默认环境）：

| 项目 | 值 |
|------|------|
| 接口地址 | `https://pacs.qq.com` |
| APP-ID | 100002 |
| APP-TOKEN | ca27d176-d317-475f-8d1f-9cb54032a905 |

> 三个脚本默认 host 均为正式环境地址 `https://pacs.qq.com`，无需额外指定即可使用。如需切换环境请通过 `--host` 参数指定。

如需 sample 肺炎CT数据：可查询访问公开数据集，建议CT层厚＜2mm。

### 正式使用

如需长期使用，请联系 miying@tencent.com 或访问腾讯健康官网。

---

## 七、技术支持

遇到问题时请提供以下信息：

- `appId`、`requestId`、`taskId`
- 调用时间（含时区）
- 请求头与请求参数
- 错误响应体完整内容

---

## 八、验证

1. 提交任务后检查返回 `head.code` 是否为 0，且 `head.taskId` 非空
2. 查询任务后检查 `status` 字段是否为"处理完成"或"处理失败"
3. 处理完成时验证 `pneumoniaSign` 和 `pneumoniaAnalysis` 非空
4. 签名错误时检查系统时间是否与NTP同步

---

## Reference

- 完整API文档：@references/api_pneumonia.md
