# 眼底多病种AI API接口规范（2026V1）

## 鉴权方式

所有接口采用 HMAC-SHA256 签名鉴权：

```
signature = Hmac-SHA256(token, appId + timestamp)
```

请求 Header 需携带：
- `signature` — 签名
- `appId` — 合作方ID（腾讯系统分配）
- `timestamp` — 毫秒级时间戳

---

## 凭证与权限（普角/超广角相互独立、权限互斥）

普角与超广角是**两套完全独立的凭证**。同一个 appId/token 只拥有其中**一种**权限（普角**或**超广角），**不能混用**——用错凭证会返回无权限或查不到结果。调用时必须按图像类型选对凭证（`aiType` 0/1/2=普角，`12`=超广角）。

要点：
- 具体的 appId/token/hospitalId 取值以 `bin/fundus_ai.py` 源码中的 `CREDENTIALS` 常量为唯一权威来源，此处不再重复列出，避免多处维护不一致；`hospitalId` == `appId`。
- 以上凭证已内置在 `bin/fundus_ai.py` 中，指定 `--ai-type` 即自动选对凭证，安装即用。
- 如需换成自有正式凭证，用 `--token`/`--app-id` 或环境变量 `FUNDUS_TOKEN`/`FUNDUS_APPID` 覆盖。
- 内置凭证为对外试用凭证，随专家包分发；如需长期正式使用可联系 miying@tencent.com。

---

## 一、检查信息上传接口（批量小图）

- **协议**：HTTPS
- **地址**：`POST https://pacs.qq.com/thirdparty/studyupload/v2/{appId}`（正式）/ `https://test.pacs.qq.com/thirdparty/studyupload/v2/{appId}`（测试）
- **数据格式**：JSON (application/json)
- **适用**：一次上传多张图片（至少1张，最多20张，总大小≤5MB）

### 请求参数

| 参数名 | 类型 | 必填 | 备注 |
|--------|------|------|------|
| studyId | string | 是 | 检查在医院侧的序列号 |
| studyName | string | 是 | 检查名称 |
| studyDate | long | 是 | 检查日期，Unix时间戳（秒） |
| studyType | int | 是 | 检查类型：2=眼底 |
| patientName | string | 否 | 患者姓名 |
| patientId | string | 否 | 患者编号 |
| patientGender | string | 否 | 0=未知 1=男 2=女 3=其他 |
| patientBirthday | string | 否 | 格式：2017-08-22 |
| images | Array(image) | 是 | 图片数组 |

### images 数据格式

| 参数名 | 类型 | 必填 | 备注 |
|--------|------|------|------|
| imageId | string | 是 | 影像编号 |
| content | string | 是 | base64编码内容 |
| url | string | 否 | 医院内网地址 |
| descPosition | string | 否 | 眼别：0=未知 1=左眼 2=右眼 |

---

## 二、检查信息上传接口（单张大图）

- **协议**：HTTPS
- **地址**：`POST https://pacs.qq.com/thirdparty/fileImageUpload/v1/{appId}`（正式）/ `https://test.pacs.qq.com/thirdparty/fileImageUpload/v1/{appId}`（测试）
- **数据格式**：form-data
- **适用**：每次上传一张大图（≤100MB）

### 请求参数

| 参数名 | 类型 | 必填 | 备注 |
|--------|------|------|------|
| studyId | text | 是 | 检查序列号 |
| studyName | text | 是 | 检查名称 |
| studyDate | text | 是 | Unix时间戳（秒） |
| studyType | text | 是 | 2=眼底 |
| patientName | text | 否 | 患者姓名 |
| patientId | text | 否 | 患者编号 |
| patientGender | text | 否 | 0=未知 1=男 2=女 3=其他 |
| patientBirthday | text | 否 | 2017-08-22 |
| imageId | text | 是 | 图片ID |
| url | text | 否 | 医院内网地址 |
| descPosition | text | 否 | 0=未知 1=左眼 2=右眼 |
| file | File | 是 | 图片文件 |
| cameraType | text | 是 | 相机类型：0=默认(自动识别) 1=欧宝 2=蔡司 |

---

## 三、查询眼底AI结果与报告

- **协议**：HTTPS
- **地址**：`POST https://pacs.qq.com/thirdparty/queryEyeAIResult/{appId}`（正式）/ `https://test.pacs.qq.com/thirdparty/queryEyeAIResult/{appId}`（测试）
- **数据格式**：JSON

### 请求参数

| 参数名 | 类型 | 必填 | 备注 |
|--------|------|------|------|
| hospitalId | string | 是 | 医疗机构唯一标识 |
| studyId | string | 是 | 检查唯一标识 |
| patientId | string | 否 | 患者唯一标识 |
| aiType | int | 是 | 0=青光眼+多病种(普角), 1=青光眼(普角), 2=多病种(普角), 12=超广角 |
| needReport | int | 是 | 0=不输出PDF报告, 1=输出PDF报告 |

### 通用返回结构

```json
{
  "code": 0,
  "message": "请求成功",
  "requestId": "xxx",
  "data": {
    "glaucomaResultList": [...],        // 青光眼AI结果（普角）
    "multipleDiseasesResultList": [...], // 多病种AI结果（普角）
    "ultraWideResult": {...},           // 超广角AI结果（aiType=12）
    "reportUrl": "https://..."          // PDF报告下载URL
  }
}
```

---

## 四、普角青光眼AI结果 (GlaucomaResult)

| 字段 | 类型 | 备注 |
|------|------|------|
| status | int | 200=成功, 0=处理中, -1=待处理, -2=失败, -3=屈光间质混浊, -4=图片不合格, 404=未找到图片 |
| eyeCategory | int | 0=左眼, 1=右眼 |
| aiResult | string | "疑似青光眼样眼底表现" 或 "未见明显青光眼样眼底表现" |

---

## 五、普角多病种AI结果 (MultipleDiseasesResult)

### 病灶描述 (MultipleDiseasesFocusDescription)

| 字段 | 类型 | 备注 |
|------|------|------|
| ratiosCD | float | 杯盘比 (C/D)，正常<0.3 |
| ratiosIN | float | 盘沿比 (I/N) |
| ratiosSN | float | 盘沿比 (S/N) |
| ratiosTN | float | 盘沿比 (T/N) |
| microaneurysms | string | 微动脉瘤：是/否 |
| bleeding | string | 出血斑：是/否 |
| hardExudation | string | 硬性渗出：是/否 |
| softExudation | string | 软性渗出：是/否 |
| proliferation | string | 增殖膜：是/否 |
| vitreous | string | 玻璃体积血：是/否 |
| wart | string | 玻璃膜疣：是/否 |

### AI结果 (MultipleDiseasesAIResult)

| 字段 | 类型 | 备注 |
|------|------|------|
| noAbnormality | string | 未见明显异常：是/否 |
| diabetic | string | 糖尿病性视网膜病变：未见/轻度/中度/重度/增殖 |
| AMD | string | 年龄相关性黄斑变性：有/无 |
| block | string | 视网膜静脉阻塞：有/无/不确定 |
| turbid | string | 屈光间质混浊：有/无 |
| hypertensive | string | 高血压眼底病变：有/无 |
| tessellatedFundus | string | 豹纹状眼底：有/无 |
| pathologicalMyopia | string | 高度近视眼底改变：有/无 |
| other | string | 其他眼底疾病：有/无 |

---

## 六、超广角眼底多病种AI结果 (UltraWideResult)

### 顶层结构

| 字段 | 类型 | 备注 |
|------|------|------|
| status | int | 200=已完成 |
| inferredDiagnoses | array | 推测诊断列表 |
| eyeScreening | object | 单眼筛查文字结论 |
| leftDetail | object | 左眼详情（体征+分割+检测） |
| rightDetail | object | 右眼详情（体征+分割+检测） |

### 推测诊断 (inferredDiagnoses[])

| 字段 | 类型 | 备注 |
|------|------|------|
| disease | string | 疾病英文标识 |
| name | string | 疾病中文名称 |
| leftValue | string | "1"=疑似, "0"=未见 |
| rightValue | string | "1"=疑似, "0"=未见 |
| checkType | string | 固定 "checkbox" |
| additional | string | 附加信息 |

### 支持的推测诊断疾病列表（22种）

| disease (英文标识) | name (中文名称) |
|---|---|
| RetinalArteryOcclusion | 视网膜动脉阻塞 |
| RetinalDetachment | 视网膜脱离 |
| RetinalHole | 视网膜裂孔 |
| RetinalChoroidalMass | 视网膜脉络膜占位（肿物） |
| RetinalPeripheralDegeneration | 视网膜周边变性区 |
| CongenitalOpticDiscAnomaly | 先天性视盘发育异常 |
| LargeCupDiscRatio | 视盘大视杯（杯盘比≥0.3） |
| OpticAtrophy | 视神经萎缩 |
| MacularEpiretinalMembrane | 黄斑前膜 |
| MacularSerousDetachment | 黄斑区浆液性视网膜脱离 |
| MacularHole | 黄斑裂孔 |
| AsteroidHyalosis | 玻璃体星状小体 |
| PosteriorVitreous | 玻璃体后脱离 |
| OtherVitreousAnomaly | 其他玻璃体异常（药物棒/气体/硅油） |
| DiabeticRetinopathyPDR | 糖尿病视网膜病变（PDR） |
| DiabeticRetinopathyNPDR | 糖尿病视网膜病变（NPDR） |
| RetinitisPigmentosa | 视网膜色素变性 |
| PathologicalMyopia | 病理性高度近视 |
| CentralRetinalVeinOcclusion | 视网膜中央静脉阻塞 |
| BranchRetinalVeinOcclusion | 视网膜分支静脉阻塞 |
| WetAgeRelatedMacularDegeneration | 湿性年龄相关黄斑变性 |
| DryAgeRelatedMacularDegeneration | 干性年龄相关黄斑变性 |
| VKH | VKH（小柳-原田综合征） |

### 筛查描述 (eyeScreening)

| 字段 | 类型 | 备注 |
|------|------|------|
| left | string | 左眼筛查文字结论 |
| right | string | 右眼筛查文字结论 |

### 47维体征分类 (leftDetail/rightDetail.others[])

值含义：1=疑似阳性, 0=未见异常, -1=不适用

| 索引 | 中文名称 | 英文标识 |
|------|---------|---------|
| 0 | 屈光介质混浊 | refractiveMediaOpacity |
| 1 | 玻璃体出血 | vitreousBlood |
| 2 | 玻璃体星状小体 | asteroidHyalosis |
| 3 | 玻璃体后脱离 | posteriorVitreous |
| 4 | 其他玻璃体异常（药物棒/气体/硅油） | otherVitreousAnomaly |
| 5 | 玻璃膜疣 | drusen |
| 6 | 黄斑视网膜下纤维膜（黄斑盘变） | macularSubretinalFibrosis |
| 7 | 黄斑近视性萎缩斑 | macularMyopicAtrophy |
| 8 | 黄斑地图样萎缩 | macularGeographicAtrophy |
| 9 | 黄斑前膜 | macularEpiretinalMembrane |
| 10 | 黄斑出血 | macularHemorrhage |
| 11 | 黄斑视网膜下出血 | macularSubretinalHemorrhage |
| 12 | 黄斑区浆液性视网膜脱离 | macularSerousDetachment |
| 13 | 黄斑裂孔 | macularHole |
| 14 | 其他黄斑病变 | otherMacularDisease |
| 15 | 视盘侧枝循环 | opticDiscCollateral |
| 16 | 视盘边界不清 | opticDiscBorderUnclear |
| 17 | 先天性视盘发育异常 | congenitalOpticDiscAnomaly |
| 18 | 视盘大视杯（杯盘比≥0.3） | largeCupDiscRatio |
| 19 | 视神经萎缩 | opticAtrophy |
| 20 | 视盘新生血管 | opticDiscNeovascularization |
| 21 | 高度近视视盘萎缩弧 | highMyopiaOpticDiscAtrophyArc |
| 22 | 高度近视视盘萎缩环 | highMyopiaOpticDiscAtrophyRing |
| 23 | 视网膜脱离 | retinalDetachment |
| 24 | 视网膜出血象限性 | retinalHaemorrhageQuadrant |
| 25 | 视网膜下出血 | retinalSubretinalHemorrhage |
| 26 | 视网膜前出血 | retinalPreretinalHemorrhage |
| 27 | 视网膜裂孔 | retinalTear |
| 28 | 视网膜纤维膜 | retinalFibrousMembrane |
| 29 | 视网膜脉络膜占位（肿物） | retinalChoroidalMass |
| 30 | 视网膜光凝斑 | retinalLaserCoagulation |
| 31 | 全视网膜光凝 | panretinalPhotocoagulation |
| 32 | 单象限性视网膜光凝斑 | singleQuadrantLaserCoagulation |
| 33 | 视网膜骨细胞样色素改变 | retinalBoneCellPigment |
| 34 | 豹纹状眼底 | tessellatedFundus |
| 35 | 晚霞状眼底 | sunsetGlowFundus |
| 36 | 出血点、出血斑 | hemorrhagicSpot |
| 37 | 硬性渗出 | hardExudate |
| 38 | 棉绒斑 | cottonWoolSpot |
| 39 | 视网膜新生血管 | retinalNeovascularization |
| 40 | 视网膜陈旧色素病灶 | retinalOldPigmentLesion |
| 41 | 视网膜周边变性区 | retinalPeripheralDegeneration |
| 42 | 其他视网膜病变 | otherRetinalDisease |
| 43 | 视网膜动脉阻塞 | retinalArteryOcclusion |
| 44 | 视网膜血管白线 | retinalVascularWhiteLine |
| 45 | 视网膜动脉硬化 | retinalArterySclerosis |
| 46 | 视网膜血管鞘-视网膜血管炎 | retinalVasculitis |

### 体征分割 (仅欧宝设备有值)

| 字段 | 类型 | 备注 |
|------|------|------|
| hemohedgeMask | string | 出血点/出血斑分割轮廓坐标JSON |
| cottonWoolSpotMask | string | 棉絮斑/棉绒斑分割轮廓坐标JSON |
| hardExudateMask | string | 硬性渗出分割轮廓坐标JSON |
| neovascularizationMask | string | 视网膜新生血管分割轮廓坐标JSON |

### 体征检测 (gzip+base64压缩JSON)

| 字段 | 类型 | 备注 |
|------|------|------|
| highMyopiaOpticDisc | string | 高度近视视盘检测 |
| macularEpiretinalMembrane | string | 黄斑前膜检测 |
| retinalFibrousMembrane | string | 视网膜纤维膜检测 |
| retinalHole | string | 视网膜裂孔检测 |
| retinalDetachment | string | 视网膜脱离检测 |
| retinalOldPigmentLesion | string | 视网膜陈旧色素病灶检测 |

---

## 错误码对照

| code | 备注 |
|------|------|
| 0 | 请求成功 |
| 1 | 参数错误 |
| 2 | 数据库开小差 |
| 10003 | 未找到数据 |
| 30008 | 检查处理中（**AI 任务尚未完成，应继续轮询**，非"检查不存在"） |
| 90001 | 无效token |
| 90002 | 无效签名 |
| 90003 | 超出最大获取次数 |

---

## aiType 使用场景对照

| aiType | 场景 | 输出字段 |
|--------|------|---------|
| 0 | 普角青光眼 + 多病种 | glaucomaResultList + multipleDiseasesResultList |
| 1 | 普角青光眼 | glaucomaResultList |
| 2 | 普角多病种 | multipleDiseasesResultList |
| 12 | 超广角多病种 | ultraWideResult |

---

## 轮询与眼别编码（实测要点）

**轮询策略**（来自官方 skill 与实测）：
- `code=30008` = AI 处理中，需**继续轮询**（不是"检查不存在"）。
- 间隔 10 秒；超广角最长 5 分钟（30 次），普角最长 3 分钟（18 次）——超广角模型更慢。
- 成功条件：`code=0` 且对应结果 `status=200`。
- 普角青光眼与多病种是**两个独立子模型**，可能一个先 `status=200`、另一个仍 `status=0`（处理中），必须轮询到两者都就绪，否则会漏掉青光眼结论。

**眼别编码（易混淆）**：上传用 `descPosition`（0未知/1左眼/2右眼），返回用 `eyeCategory`（0左眼/1右眼），两者不同。只上传单眼时，另一眼对应条目会返回 `status=404`（无图），正常忽略。

**上传接口选择**：总大小 ≤5MB 用 Base64 接口 `studyupload/v2`（官方推荐）；单张大图（>5MB，≤100MB）用 form-data 接口 `fileImageUpload/v1`。
