# 商户域 — 渠道追踪写操作契约

> 概念知识：`references/domains/merchant-concepts.md`；运营流程：`references/flows/merchant-channel.md`；现值读取（追踪单分页/详情/自定义渠道字典）先读 `channel-trace-query.md`。
> 写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读现态再决定下一步。**导入为文件型 multipart 传输形态**。
> 能力索引：channel-trace.add 新增追踪单 · channel-trace.edit 编辑追踪单 · channel-trace.update-status 启停追踪单 · channel-trace.custom-channel.add 新增自定义渠道 · channel-trace.import 渠道追踪导入 🔴

---

## ✅ 新增追踪单 — ops.merchant.channel-trace.add

- 🟡 常规写

### 入参（add 不传 id）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pushName | String | 是 | 推广名称，≤200 字 |
| channelType | Integer | 是 | 渠道类型：**1=门店推广、2=其他渠道**（自定义渠道取 custom-channels 出参映射） |
| pushPageType | Integer | 否 | 投放页面类型 |
| pushPageInfo | String | 否 | 投放页面 **JSON 字符串**——装修链接选择器对象（与装修组件跳转链接同构，多态，按 `type` 字段分支，值域 15 个：`page`{path} / `action`{action:"coupon-code-redeem"} / `product`{productId,productName,productThumb,path} / `category`{categoryId,categoryName,path} / `miniprogram`{appId,path} / `halfscreen`{appId,path} / `webview`{path} / `copy`{text} / `anchor`{anchorId,anchorName} / `decoration`{pageId,pageName} / `live` / `activity`{activityId,activityName,activityType} / `customer`{path,benefitName} / `distribution`{path} / `ai-assistant`{path}）。**服务端不校验其结构**（仅导出时解析 `path` 键生成小程序路径）；编辑时从 detail 回填原文透传（前端也是 parse→表单→stringify 原样回传），**不要自行构造** |
| channelConfigId | String | 否 | 渠道配置 ID |
| firstLevelName ~ fifthLevelName | String | 否 | 五级层级归因名称 |
| isElectronicLabel | Boolean | 否 | 是否电子标签 |
| posterConfig | String | 否 | 海报配置 **JSON 字符串**（编辑海报配置时必传完整对象），内部结构：`posterMainTitle`（分享主标题，必填）/ `posterSubTitle`（分享副标题）/ `promotionText`（推广文案）/ `posterImg`（海报主图 URL——先经素材中心上传 COS 取裸 URL，服务端入库前自动剥除签名参数，回显时重新生成临时签名 URL） |

### 出参（原始返回）

`Result<Long>`（新追踪单 ID，十进制字符串）。

### 调用示例

```json
{"capability":"ops.merchant.channel-trace.add","input":{"pushName":"双11朋友圈投放","channelType":1},"summary":"新建双11朋友圈投放的追踪单"}
```

---

## ✅ 编辑追踪单 — ops.merchant.channel-trace.edit

- 🟡 常规写；入参同 add（`id` 额外必填），`pushPageInfo`/`posterConfig` 从 detail 回填原文透传，不要自行构造。

### 调用示例

```json
{"capability":"ops.merchant.channel-trace.edit","input":{"id":"7700012345678901234","pushName":"双11朋友圈投放-改名","channelType":1},"summary":"把这条追踪单改名"}
```

---

## ✅ 启停追踪单 — ops.merchant.channel-trace.update-status

- 🟡 可逆写
- **对象定位**：按用户明确的 ID 或推广名称核对详情；查询结果唯一不等于用户已选定。未提供有效名称、名称不匹配或只有说明文字时，列出候选业务信息请用户选定，不把唯一启用单当成默认目标。
- **意图冲突**：指令同时含「只读/仅查询」与「停用/启用」时，先澄清允许的动作；能力支持写不代表用户已撤销只读限制。可逆和执行授权均不替代对象匹配，明确目标后再按当前运行时审批模式提交并回读。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 追踪单 ID |
| useStatus | Integer | ✅ | 使用状态：**1=启用、0=停用** |

### 调用示例

```json
{"capability":"ops.merchant.channel-trace.update-status","input":{"id":"7700012345678901234","useStatus":0},"summary":"停用这条追踪单"}
```

---

## ✅ 新增自定义渠道 — ops.merchant.channel-trace.custom-channel.add

- 🟡 常规写（扩展渠道类型字典）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| channelName | String | ✅ | 自定义渠道名称 |

### 调用示例

```json
{"capability":"ops.merchant.channel-trace.custom-channel.add","input":{"channelName":"KOL合作渠道"},"summary":"加一个 KOL 合作的自定义渠道"}
```

---

## ✅ 渠道追踪导入 — ops.merchant.channel-trace.import

- 🔴 批量写（部分成功语义，逐项报告）
- **传输形态**：multipart 文件型——file part = Excel（.xlsx，≤10MB）；模板从管理后台「渠道追踪-导入-下载模板」获取。

### multipart 入参

| part | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | 渠道追踪 Excel（.xlsx，≤10MB） |

### 出参（原始数据）

- `ImportResultVO`（totalCount/successCount/failureCount/hasFailureDetail/failureDetailUrl——部分成功语义，逐项报告）。

### 调用示例

```json
{"capability":"ops.merchant.channel-trace.import","input":{"file":"uploads/批量导入模板.xlsx", "fileType":"excel"},"summary":"导入这批渠道追踪 Excel；文件由客户端 multipart 提供"}
```
