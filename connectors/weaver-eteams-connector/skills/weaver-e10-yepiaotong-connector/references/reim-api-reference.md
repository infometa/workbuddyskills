# 报销 CLI operation 参考文档

> 本文件说明各报销 CLI operation 的入参、返回字段和填单用法。
> 实际调用必须通过 `weaver-work-cli --profile eteams --json invoice run <operation>` 执行。认证由 `weaver-work-cli auth` 管理，不要手动传 token / eteamsId。

---

## 0. 文件ID转发票识别

CLI operation：`invoice.reim.file-ocr.preview`

当用户提供了 `fileId`（文件/附件ID）时，调用此 CLI 一步完成识别，直接返回标准化发票数据。

### 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json invoice run invoice.reim.file-ocr.preview --input-json '{"fileIds":["1290156133724692482","1290156133724692483"]}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json invoice run invoice.reim.file-ocr.preview --input-json '{"fileIds":["1290156133724692482","1290156133724692483"]}'
```

### 返回示例

```json
{
  "code": 200,
  "msg": "接口返回成功",
  "status": true,
  "data": [
    {
      "fileId": "1290156133724692482",
      "fileName": "a3b998b49d7cf7d2f9e77f13751d44ee.png",
      "status": "success",
      "errorMsg": "识别成功",
      "invoiceId": "1290156159548506113",
      "invoiceType": "机动车销售统一发票",
      "invoiceTypeCode": 6,
      "amount": "263500.00",
      "consumeContent": "机动车销售统一发票",
      "invoiceDate": "2025-03-11",
      "invoiceNumber": "00393118",
      "buyerName": "杭州杭港地铁五号线有限公司",
      "sellerName": "特斯拉汽车销售服务（杭州）有限公司",
      "expenseType": "日常消费"
    }
  ],
  "fail": false
}
```

### 返回字段说明


| 字段                | 说明                          |
| ----------------- | --------------------------- |
| `fileId`          | 原始文件/附件ID                   |
| `fileName`        | 文件名                         |
| `status`          | 识别状态：`"success"` 或 `"fail"` |
| `errorMsg`        | 识别结果消息                      |
| `invoiceId`       | 发票唯一ID（后续匹配和填单使用）           |
| `invoiceType`     | 发票类型名称                      |
| `invoiceTypeCode` | 发票类型编码                      |
| `amount`          | 发票金额                        |
| `consumeContent`  | 消费内容/商品名称                   |
| `invoiceDate`     | 开票日期（yyyy-MM-dd）            |
| `invoiceNumber`   | 发票号码                        |
| `buyerName`       | 购方公司名称                      |
| `sellerName`      | 销方公司名称                      |
| `expenseType`     | 费用类型名称                      |


> 返回的发票数据结构与 `invoice.list` 一致，可直接用于后续匹配和填单流程。

### 多 fileId 处理

用户可能提供逗号拼接的多个 fileId（如 `"id1,id2,id3"`），按逗号切割后组装为数组传入 `fileIds` 即可，CLI 会批量处理并返回每个文件的识别结果。

### 异常处理


| 场景                        | 处理方式             |
| ------------------------- | ---------------- |
| 某个文件识别失败（`status="fail"`） | 跳过该文件，用成功的发票继续流程 |
| 全部文件识别失败                  | 提示用户识别失败，无法继续    |


---

## 1. 获取发票数据

CLI operation：`invoice.list`（个人票夹）/ `invoice.enterprise.list`（企业票夹）

### 入参

CLI 已固定 `flag`（个人票夹=0 / 企业票夹=6），默认 `sreim="3"`、`bill_type=0`、`req_type=1`、`page_size=10`、`start_pos=0`。**不要传 `flag`。** 用户未要求查全部发票或凭证时，也不要传 `sreim` / `bill_type`。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `page_size` | Integer | 否 | 每页条数，默认 `10`，建议不超过 `20` |
| `start_pos` | Integer | 否 | 分页起始位置，默认 `0` |
| `date_begin` / `date_end` | Integer | 否 | 开票日期范围（**秒级时间戳**）。用户未指定日期时，默认最近一周 |
| `create_tm_begin` / `create_tm_end` | Integer | 否 | 录入/创建日期范围（**秒级时间戳**），仅用户明确说录入/创建日期时使用 |
| `content` | String | 否 | 消费内容关键词（如 `"滴滴"`、`"住宿"`） |
| `number` | String | 否 | 发票号码精确匹配 |
| `types` | Array\<Integer\> | 否 | 发票类型 ID 数组（见下方映射表） |

不支持 `fylxs`、`consumption_tm_begin`、`consumption_tm_end`；日期筛选一律用 `date_begin` / `date_end`。

### 时间戳计算

> **所有日期参数的秒级时间戳由 AI 按内联公式直接计算（UTC+8 时区）。**
> 完整公式和 Fallback 见 [reim-workflow.md - 时间戳内联计算](reim-workflow.md#时间戳内联计算零工具调用)。

示例（最近一周，只传必要字段）：

```json
{
  "page_size": 10,
  "start_pos": 0,
  "date_begin": 1785513600,
  "date_end": 1786982399
}
```

> 上方示例中的时间戳仅为示意，实际使用时由 AI 按内联公式动态计算。

### 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json invoice run invoice.list --input-json '{"page_size":10,"start_pos":0,"date_begin":1785513600,"date_end":1786982399}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json invoice run invoice.list --input-json '{"page_size":10,"start_pos":0,"date_begin":1785513600,"date_end":1786982399}'
```

### 预筛选入参（先获取到事前申请时使用）

> **前提：开票日期一定不早于事前申请日期。** CLI 用 `date_begin` / `date_end`（开票日期，秒级时间戳）筛选。

如果已有事前申请数据，利用事前申请的 `createTime` 来缩小查询范围：

- `date_begin` = 最早事前申请 createTime 对应的秒级时间戳
- `date_end` = 当前日期 23:59:59 对应的秒级时间戳

### 返回示例

CLI 信封中列表在 `data.items`。下面是单条发票的票面结构（对应 `items[]` 元素，不是顶层 `infos`）：

```json
{
  "infos": [
    {
      "info": {
        "id": "1301239558731259905",
        "fid": "1301239558731259905",
        "code": "",
        "number": "26467000000088899841",
        "ext": "{\"ttax\":\"54\",\"trate\":\"6.0\",\"pcontact\":\"海南省三亚市海棠区海棠北路36号亚特兰蒂斯酒店 0898-88986666\",\"totalBig\":\"玖佰伍拾肆\",\"title\":\"电子发票（普通发票）\",\"bbank\":\"\",\"content\":\"*生产生活服务*水上乐园门票\",\"issuer\":\"张怡\",\"products\":[{\"tprice\":\"54\",\"taxClassifyCode\":\"3070101000000000000\",\"price\":\"900.00\",\"qty\":\"1\",\"name\":\"*生产生活服务*水上乐园门票\",\"no\":\"1\",\"trate\":\"6.0\",\"amount\":\"900\",\"smodel\":\"\",\"muint\":\"张\"}],\"province\":\"海南省\",\"bcontact\":\"上海市闵行区三鲁公路3419号021-52262600\",\"pbank\":\"462601500018800030539\",\"comment\":\"0808+5737268\",\"category\":\"电子发票（普通发票）\",\"corp_seal\":\"1\"}",
        "rb": { "trace": "", "ret": 0, "lang": "53512" },
        "fylx": "897092516517920775",
        "total": 0,
        "currency": "CNY",
        "currencyName": "人民币",
        "empId": "9080972482706531342",
        "province": "海南省",
        "modify_info": {
          "ctm": 1786168444,
          "utm": 1786168444,
          "cstm": 1786118400,
          "source": 4
        },
        "comm_info": {
          "pro": {
            "cname": "电子发票（普通发票）",
            "type": 33,
            "date": "2026-08-08",
            "status": 0
          },
          "price": {
            "amount": "900",
            "total": "954",
            "treim": ""
          },
          "buyer": {
            "tcode": "9131000070322836XD",
            "company": "上海泛微网络科技股份有限公司"
          },
          "payer": {
            "tcode": "91460200348073438U",
            "company": "海南亚特兰蒂斯商旅发展有限公司亚特兰蒂斯酒店"
          }
        },
        "relative_fids": [],
        "bill_type": 0
      },
      "ret": { "trace": "", "ret": 0, "message": "执行成功", "lang": "53512" },
      "is_valid": 0
    }
  ],
  "res_base": { "trace": "", "ret": 0, "message": "执行成功", "lang": "53512" }
}
```

### 返回字段说明

> **⚠️ `ext` 是 JSON 字符串，使用前需先 `JSON.parse(ext)` 解析。**

| 字段路径 | 对应标准字段名 | 说明 |
| --- | --- | --- |
| `info.fid` | `invoiceId` | 发票唯一 ID（后续匹配和填单使用） |
| `info.number` | `invoiceNumber` | 发票号码 |
| `info.code` | — | 发票代码 |
| `info.comm_info.pro.cname` | `invoiceType` | 发票类型名称 |
| `info.comm_info.pro.type` | `invoiceTypeCode` | 发票类型编码（见下方分类说明） |
| `info.comm_info.pro.date` | `invoiceDate` | 开票日期（yyyy-MM-dd） |
| `info.comm_info.pro.status` | — | 发票状态（**8=全额红冲，必须过滤掉**） |
| `info.comm_info.price.total` | `amount` | 价税合计（发票金额） |
| `info.comm_info.price.amount` | — | 不含税金额 |
| `info.comm_info.buyer.company` | `buyerName` | 购方公司名称 |
| `info.comm_info.payer.company` | `sellerName` | 销方公司名称 |
| `info.fylx` | — | 费用类型 ID（需根据 ID 查找对应 `expenseType` 名称） |
| `info.province` | — | 省份 |
| `info.modify_info.cstm` | — | 消费日期（秒级时间戳） |
| `info.modify_info.source` | — | 来源（4=邮箱等） |
| `ext`（解析后）`.content` | `consumeContent` | 消费内容/商品名称 |
| `ext`（解析后）`.products` | — | 商品明细列表 |
| `ext`（解析后）`.province` | — | 省份 |
| `ext`（解析后）`.comment` | — | 备注 |
| `ext`（解析后）`.issuer` | — | 开票人 |
| `ext`（解析后）`.pcontact` | — | 销售方地址及电话 |
| `ext`（解析后）`.bcontact` | — | 购买方地址及电话 |

### ext 字段详细结构

`ext` 是 JSON 字符串，解析后结构如下：

```json
{
  "ttax": "54",
  "trate": "6.0",
  "pcontact": "海南省三亚市海棠区海棠北路36号亚特兰蒂斯酒店 0898-88986666",
  "totalBig": "玖佰伍拾肆",
  "title": "电子发票（普通发票）",
  "bbank": "",
  "content": "*生产生活服务*水上乐园门票",
  "issuer": "张怡",
  "products": [
    {
      "tprice": "54",
      "taxClassifyCode": "3070101000000000000",
      "price": "900.00",
      "qty": "1",
      "name": "*生产生活服务*水上乐园门票",
      "no": "1",
      "trate": "6.0",
      "amount": "900",
      "smodel": "",
      "muint": "张"
    }
  ],
  "province": "海南省",
  "bcontact": "上海市闵行区三鲁公路3419号021-52262600",
  "pbank": "462601500018800030539",
  "comment": "0808+5737268",
  "category": "电子发票（普通发票）"
}
```

### 数据过滤规则（重要，前置处理）

> **⚠️ 获取到发票数据后，必须先过滤掉不允许报销的发票，再进行后续分类和填单。**

| 过滤条件 | 字段路径 | 值 | 说明 |
| --- | --- | --- | --- |
| **全额红冲发票** | `info.comm_info.pro.status` | `8` | 该发票已被全额红冲，**必须过滤掉，不允许报销** |

过滤后的发票才进入后续的 invoiceTypeCode 分类和填单流程。

---

### invoiceTypeCode 分类（重要）

返回的 `info.comm_info.pro.type` 按值分为两类，**填单时处理方式完全不同**：

| 分类 | type 值 | 说明 | 填单位置 |
| --- | --- | --- | --- |
| **发票** | 除 17/18/57/58 以外的所有值 | 正式发票，每张独立成一行明细 | `EinvoiceComponent` + `single=false`（相关发票字段） |
| **相关凭证** | 17, 18, 57, 58 | 行程单、小票/水单、电子支付凭证、其他支付凭证，不能独立成行 | `EinvoiceComponent` + `single=true`（相关凭证字段） |

**关键规则：相关凭证必须与发票配对，放在同一行明细中，不能单独成行。**

详细的配对和填单规则见 [form-fill-rules.md](reim-form-fill-rules.md#发票与相关凭证分类)

### 发票类型 ID 映射表

> 用于 `types` 入参筛选，`info.comm_info.pro.type` 返回值也对应此表。

| ID | 名称 |
| --- | --- |
| 1 | 增值税专用发票 |
| 2 | 增值税普通发票 |
| 3 | 增值税电子普通发票 |
| 4 | 增值税普通发票(卷票) |
| 5 | 增值税电子普通发票（通行费） |
| 6 | 机动车销售统一发票 |
| 7 | 二手车销售统一发票 |
| 8 | 定额发票 |
| 9 | 出租车发票 |
| 10 | 机打发票 |
| 11 | 可报销的其他发票 |
| 12 | 火车票 |
| 13 | 过路费发票 |
| 14 | 船票发票 |
| 15 | 客运汽车发票 |
| 16 | 航空运输电子客票行程单 |
| 17 | 小票/水单 |
| 18 | 滴滴行程单（支付凭证，非增值税发票） |
| 19 | 完税证明 |
| 21 | 地铁发票 |
| 22 | 区块链发票 |
| 28 | 增值税电子专用发票 |
| 31 | 火车票退票凭证 |
| 32 | 电子发票（增值税专用发票） |
| 33 | 电子发票（普通发票） |
| 34 | 票据汇总单 |
| 35 | 通用（电子）发票 |
| 36 | 门诊收费票据（电子） |
| 37 | 非税收入统一票据（电子） |
| 39 | 海关缴款书 |
| 40 | 出口转内销发票 |
| 41 | 出口转内销海关缴款书 |
| 42 | 出口转内销电子专用发票 |
| 43 | 收购发票 |
| 44 | 免税自产农产品普通发票 |
| 45 | 其他普通发票 |
| 46 | 代扣代缴完税凭证 |
| 47 | 电子发票（铁路电子客票） |
| 48 | 电子发票（航空运输电子客票行程单） |
| 49 | 纸质增值税专用发票（全电纸质专票） |
| 50 | 纸质增值税普通发票（全电纸质普票） |
| 51 | 非大陆发票 |
| 52 | 电子发票（铁路电子客票退票凭证） |
| 53 | 电子发票（机动车销售统一发票） |
| 54 | 电子发票（二手车销售统一发票） |
| 55 | 货物运输电子收款凭证 |
| 56 | 全电发票通行费 |
| 57 | 支付凭证 |
| 58 | 其他票据凭证 |

> **相关凭证类型**（不能独立成行，填单时放入"相关凭证"字段）：17（小票/水单）、18（滴滴行程单——注意：滴滴开具的增值税电子普通发票 type=3，是正式发票可独立成行；type=18 仅指滴滴的支付行程凭证）、57（支付凭证）、58（其他票据凭证）

---

## 2. 查询事前申请流程列表

CLI operation：`invoice.reim.requests.list`

### 入参

#### 分页参数


| 参数         | 类型      | 必填  | 默认值 | 说明      |
| ---------- | ------- | --- | --- | ------- |
| `pageNo`   | Integer | 是   | 1   | 页码，从1开始 |
| `pageSize` | Integer | 是   | 20  | 每页条数    |


#### 筛选条件


| 参数                   | 类型     | 说明                   | 示例              |
| -------------------- | ------ | -------------------- | --------------- |
| `requestname`        | String | 流程标题模糊搜索             | `"差旅"`, `"交通费"` |
| `cusCreateDateStart` | String | 发起日期-开始 (yyyy-MM-dd) | `"2026-07-01"`  |
| `cusCreateDateEnd`   | String | 发起日期-结束 (yyyy-MM-dd) | `"2026-07-31"`  |


### 推荐默认入参

```json
{
  "pageNo": 1,
  "pageSize": 20
}
```

### 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json invoice run invoice.reim.requests.list --input-json '{"pageNo":1,"pageSize":20}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json invoice run invoice.reim.requests.list --input-json '{"pageNo":1,"pageSize":20}'
```

### 预筛选入参（先获取到发票时使用）

> **前提：事前申请日期一定在开票日期之前。**

如果已有发票数据，利用发票的 `invoiceDate` 来缩小事前申请查询范围：

```json
{
  "pageNo": 1,
  "pageSize": 20,
  "cusCreateDateStart": "2026-04-21",
  "cusCreateDateEnd": "2026-07-30"
}
```

- `cusCreateDateEnd` = 最晚发票 invoiceDate（事前申请不会晚于开票日期）
- `cusCreateDateStart` = 最早发票 invoiceDate 往前推 90 天（合理的事前申请窗口期）

### 返回示例

```json
{
  "code": 200,
  "msg": "接口返回成功",
  "status": true,
  "data": [
    {
      "requestid": "1298294241967177729",
      "workflowid": "1181057526276915214",
      "requestname": "交通费报销-后端开发111-2026-07-31",
      "requestnametitle": "交通费报销-后端开发111-2026-07-31 (相关客户:, 相关项目:, 承担主体: , 流程编号:Weaver-FYBX202607000069, 报销总金额:14.47 , 费用承担公司:)",
      "flowStatus": 6,
      "creatorId": "1201729946891231232",
      "creatorName": "后端开发111",
      "creatorSubCompanyId": "1169438875220598808",
      "creatorDepartmentId": "1201729461554241537",
      "createTime": "2026-07-31 15:24:45",
      "requestMark": "Weaver-FYBX202607000069",
      "userDepartmentId": "1201729461554241537",
      "nodeid": "1181057741029220917"
    }
  ],
  "fail": false
}
```

### 返回字段说明


| 字段                    | 说明                     |
| --------------------- | ---------------------- |
| `requestid`           | 事前申请流程ID（用于匹配绑定和填单）    |
| `workflowid`          | 工作流ID（用于获取表单结构）        |
| `requestname`         | 流程标题                   |
| `requestnametitle`    | 标题纯文本（含扩展信息：客户、项目、金额等） |
| `flowStatus`          | 流程状态（6=已完成）            |
| `creatorId`           | 发起人ID                  |
| `creatorName`         | 发起人姓名                  |
| `creatorDepartmentId` | 发起人部门ID                |
| `creatorSubCompanyId` | 发起人分部ID                |
| `createTime`          | 发起时间                   |
| `requestMark`         | 流程编号                   |
| `nodeid`              | 当前节点ID                 |


---

## 3. 获取报销单表单字段结构

CLI operation：`invoice.reim.form.structure`

### 入参


| 参数           | 类型     | 必填  | 说明           |
| ------------ | ------ | --- | ------------ |
| `workflowId` | String | 是   | 工作流ID        |
| `nodeId`     | String | 否   | 节点ID，默认 `1` |


### 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json invoice run invoice.reim.form.structure --input-json '{"workflowId":"1181057526276915214"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json invoice run invoice.reim.form.structure --input-json '{"workflowId":"1181057526276915214"}'
```

### 返回示例

```json
{
  "code": 200,
  "msg": "接口返回成功",
  "status": true,
  "data": {
    "mainFormId": "1181057741029226975",
    "mainFields": [
      {
        "fieldId": "1181057741029227445",
        "fieldName": "申请人",
        "fieldType": "Employee",
        "single": true,
        "marked": true
      },
      {
        "fieldId": "1181057741029227446",
        "fieldName": "部门",
        "fieldType": "Department",
        "single": true,
        "marked": true
      },
      {
        "fieldId": "1181057741029227447",
        "fieldName": "报销日期",
        "fieldType": "DateComponent",
        "single": true,
        "marked": false
      },
      {
        "fieldId": "1181057741029227448",
        "fieldName": "相关人员",
        "fieldType": "Text",
        "single": true,
        "marked": false
      },
      {
        "fieldId": "1181057741029227454",
        "fieldName": "报销方式",
        "fieldType": "Select",
        "single": true,
        "marked": false,
        "options": [
          {"optionId": "1181057741029227903", "optionName": "银行（个人报销）", "optionValue": "7"},
          {"optionId": "1181057741029227900", "optionName": "冲销借款", "optionValue": "4"},
          {"optionId": "1181057741029227904", "optionName": "银行（付公司）", "optionValue": "6"}
        ]
      },
      {
        "fieldId": "1181057741029227456",
        "fieldName": "报销事由",
        "fieldType": "TextArea",
        "single": false,
        "marked": false
      },
      {
        "fieldId": "1181057741029227470",
        "fieldName": "相关流程",
        "fieldType": "Workflow",
        "single": false,
        "marked": true
      }
    ],
    "subTables": [
      {
        "subFormId": "1181057741029227992",
        "subFormName": "费用明细",
        "subFields": [
          {
            "fieldId": "1181057741029227449",
            "fieldName": "相关客户",
            "fieldType": "Ebuilder",
            "single": true,
            "marked": true
          },
          {
            "fieldId": "1181057741029227450",
            "fieldName": "相关项目",
            "fieldType": "Ebuilder",
            "single": true,
            "marked": true
          },
          {
            "fieldId": "1181057741029227459",
            "fieldName": "实报金额",
            "fieldType": "Money",
            "single": true,
            "marked": false
          },
          {
            "fieldId": "1181057741029227463",
            "fieldName": "费用类型（科目）",
            "fieldType": "RelateBrowser",
            "single": true,
            "marked": true
          },
          {
            "fieldId": "1181057741029227464",
            "fieldName": "费用说明",
            "fieldType": "Text",
            "single": false,
            "marked": false
          },
          {
            "fieldId": "1181057741029227465",
            "fieldName": "附件数",
            "fieldType": "NumberComponent",
            "single": true,
            "marked": false
          },
          {
            "fieldId": "1181057741029227467",
            "fieldName": "费用日期",
            "fieldType": "DateComponent",
            "single": true,
            "marked": false
          }
        ]
      }
    ]
  },
  "fail": false
}
```

### 字段类型对照表


| fieldType         | 说明         | fieldValue 格式 | 示例                      |
| ----------------- | ---------- | ------------- | ----------------------- |
| `Employee`        | 员工选择       | 用户ID          | `"1201729946891231232"` |
| `Department`      | 部门选择       | 部门ID          | `"1201729461554241537"` |
| `DateComponent`   | 日期         | yyyy-MM-dd    | `"2026-08-04"`          |
| `Text`            | 单行文本       | 文本字符串         | `"差旅报销"`                |
| `TextArea`        | 多行文本       | 文本字符串         | `"详细说明..."`             |
| `Select`          | 下拉选择       | optionValue 值 | `"7"`                   |
| `Money`           | 金额         | 数字字符串         | `"820.00"`              |
| `NumberComponent` | 数字         | 数字字符串         | `"5"`                   |
| `Workflow`        | 关联流程       | 流程requestId   | `"1298294241967177729"` |
| `RelateBrowser`   | 关联浏览       | 关联数据ID        | `"2087459027187551811"` |
| `Ebuilder`        | Ebuilder关联 | 关联数据ID        | `"2087459027187551811"` |


---

## 4. 模糊搜索字段关联值

CLI operation：`invoice.reim.field.search`

用于 `marked = true` 的字段，通过名称关键词查找对应的数据ID。

### 入参


| 参数             | 类型     | 必填  | 说明            |
| -------------- | ------ | --- | ------------- |
| `keywords`     | String | 是   | 搜索关键词         |
| `fieldId`      | String | 是   | 目标字段的 fieldId |
| `workflowId`   | String | 是   | 工作流ID         |
| `nodeId`       | String | 否   | 默认由 CLI 填充 |


### 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json invoice run invoice.reim.field.search --input-json '{"keywords":"强","fieldId":"1250065066476052720","workflowId":"1250064959163990031"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json invoice run invoice.reim.field.search --input-json '{"keywords":"强","fieldId":"1250065066476052720","workflowId":"1250064959163990031"}'
```

### 返回示例

```json
{
  "code": 200,
  "msg": "接口返回成功",
  "status": true,
  "data": [
    {
      "name": "袁强强",
      "id": "2765669800318484102",
      "value": "2765669800318484102"
    }
  ],
  "fail": false
}
```

### 使用策略


| 返回结果数 | 处理方式                                   |
| ----- | -------------------------------------- |
| 1个    | 直接使用 `value` 作为 `fieldValue`           |
| 多个    | 展示候选列表让用户选择                            |
| 0个    | 缩短关键词重试；仍无结果则 `fieldValue` 留空，提示用户手动填写 |


---

## 5. 获取报销单工作流ID

CLI operation：`invoice.reim.workflow.resolve`

根据事前申请流程ID获取对应的报销单工作流ID；若无事前申请则返回候选报销单工作流列表。

### 入参


| 参数           | 类型          | 必填  | 说明                         |
| ------------ | ----------- | --- | -------------------------- |
| `requestIds` | ArrayString | 是   | 事前申请流程ID列表。无事前申请时传空数组 `[]` |


### 场景A：有事前申请

**命令：**

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json invoice run invoice.reim.workflow.resolve --input-json '{"requestIds":["1299854672520364033"]}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json invoice run invoice.reim.workflow.resolve --input-json '{"requestIds":["1299854672520364033"]}'
```

**返回：**

```json
{
  "code": 200,
  "msg": "接口返回成功",
  "status": true,
  "data": {
    "requestWorkflowMap": {
      "1299854672520364033": {
        "workFlowId": "1250064959163990031",
        "workFlowName": "差旅事前申请"
      }
    }
  },
  "fail": false
}
```

**返回字段说明：**


| 字段                                           | 说明                                              |
| -------------------------------------------- | ----------------------------------------------- |
| `requestWorkflowMap`                         | 事前申请ID → 对应报销单工作流的映射                            |
| `requestWorkflowMap[requestId].workFlowId`   | 对应的报销单工作流ID（用于 `invoice.reim.form.structure` 和 work_flow_id） |
| `requestWorkflowMap[requestId].workFlowName` | 报销单流程名称                                         |


### 场景B：无事前申请

**命令：**

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json invoice run invoice.reim.workflow.resolve --input-json '{"requestIds":[]}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json invoice run invoice.reim.workflow.resolve --input-json '{"requestIds":[]}'
```

**返回：**

```json
{
  "code": 200,
  "msg": "接口返回成功",
  "status": true,
  "data": {
    "candidateWorkflows": [
      {
        "workFlowId": "1255675973064196097",
        "workFlowName": "报销流程666【活动版本V1】"
      },
      {
        "workFlowId": "1250064959163990031",
        "workFlowName": "差旅事前申请"
      }
    ]
  },
  "fail": false
}
```

**返回字段说明：**


| 字段                                  | 说明         |
| ----------------------------------- | ---------- |
| `candidateWorkflows`                | 候选报销单工作流列表 |
| `candidateWorkflows[].workFlowId`   | 报销单工作流ID   |
| `candidateWorkflows[].workFlowName` | 报销单流程名称    |


### 使用策略


| 场景                              | 处理方式                           |
| ------------------------------- | ------------------------------ |
| 有事前申请 → 所有事前申请对应同一 workFlowId   | 创建 1 个报销单                      |
| 有事前申请 → 事前申请对应不同 workFlowId     | 按 workFlowId 分组，**每组各创建一个报销单** |
| 无事前申请 → candidateWorkflows 只有1个 | 创建 1 个报销单                      |
| 无事前申请 → candidateWorkflows 有多个  | 将发票按匹配分配到各工作流，**每组各创建一个报销单**   |


---

## 5.5 获取当前人员及上级信息

CLI operation：`invoice.reim.employee-superiors`

获取当前登录人员的基本信息及其所有上级人员列表。**用于填写表单中"报销人上级"、"承担人直接上级"和"承担人所有上级"字段（均为必填）。**

### 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json invoice run invoice.reim.employee-superiors --input-json '{}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json invoice run invoice.reim.employee-superiors --input-json '{}'
```

### 入参

无。

### 返回示例

```json
{
  "code": 200,
  "msg": "接口返回成功",
  "status": true,
  "data": {
    "currentEmployee": {
      "id": "1201729946891231232",
      "name": "后端开发111"
    },
    "allSuperiors": [
      {
        "id": "1201729946891231111",
        "name": "部门经理张三"
      },
      {
        "id": "1201729946891231222",
        "name": "总监李四"
      }
    ]
  },
  "fail": false
}
```

### 返回字段说明

| 字段 | 说明 |
| --- | --- |
| `currentEmployee.id` | 当前人员 ID（**字符串**，避免雪花 ID 超过 JS 安全整数精度） |
| `currentEmployee.name` | 当前人员名称 |
| `allSuperiors` | 所有上级列表（含直接上级和间接上级），每项含 `id` 和 `name` |
| `allSuperiors[0]` | 第一个元素即为直接上级 |
| `allSuperiors[].id` | 上级人员 ID（**字符串**） |

### 填单字段对应关系

| 表单字段 | 取值方式 |
| --- | --- |
| 报销人上级 | `allSuperiors[0].id`（直接上级 ID，直接赋值） |
| 承担人直接上级 | `allSuperiors[0].id`（直接上级 ID，直接赋值） |
| 承担人所有上级 | `allSuperiors` 中所有 `id` 用逗号拼接（如 `"id1,id2,id3"`） |

---

## 5.6 获取发票明细行预填信息

CLI operation：`invoice.reim.row-info`

根据发票 ID 获取该发票在明细行中应填写的费用日期、费用说明、关联凭证、费用科目。**返回值优先级高于 AI 自行推断**。

### 入参


| 参数          | 类型     | 必填  | 说明                 |
| ----------- | ------ | --- | ------------------ |
| `cdzt`      | String | 否   | 当前用户/人员 ID，不传则 CLI 使用当前登录用户 |
| `requestid` | String | 否   | 事前申请流程 ID（无可不传或留空） |
| `invoiceId` | String | 是   | 发票 ID |


### 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json invoice run invoice.reim.row-info --input-json '{"invoiceId":"1297093330645237792","requestid":""}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json invoice run invoice.reim.row-info --input-json '{"invoiceId":"1297093330645237792","requestid":""}'
```

### 返回字段


| 字段          | 说明               | 对应明细行字段                                  |
| ----------- | ---------------- | ---------------------------------------- |
| `date`      | 费用日期             | 费用日期/发生日期                                |
| `fysm`      | 费用说明             | 费用说明/摘要                                  |
| `itinerary` | 关联凭证 ID（多个用逗号拼接） | 相关凭证（`EinvoiceComponent`, `single=true`） |
| `subjectId` | 费用科目 ID          | 费用类型（科目）                                 |


### 返回示例

```json
{
  "code": 200,
  "status": true,
  "data": {
    "date": "2026-07-29",
    "fysm": "交通运输服务",
    "itinerary": "1298798990831518001",
    "subjectId": "100502270000000006"
  }
}
```

### 使用场景与优先级

- **调用时机**：Step 4 组装明细行时，对每张发票调用 `invoice.reim.row-info`
- **优先级**：此 CLI 返回的 `date`、`fysm`、`itinerary`、`subjectId` 四个值**优先于 AI 自行推断的值**
- **容错**：如果某个字段为空/null，则回退到 AI 推断逻辑
- **itinerary 处理**：如果 `itinerary` 有值（可能逗号分隔多个 ID），直接填入相关凭证字段（`EinvoiceComponent`+`single=true`），**替代原有的凭证配对逻辑**

---

## 5.7 获取发票详情（交通类发票行程信息）

CLI operation：`invoice.get`

根据发票 ID 获取发票完整详情。**主要用途：交通类发票获取出发地、目的地，用于生成费用说明。**

### 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json invoice run invoice.get --input-json '{"fid":"1301956959986835460"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json invoice run invoice.get --input-json '{"fid":"1301956959986835460"}'
```

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `fid` | String | 与 `number` 二选一 | 发票 fid |
| `number` | String | 与 `fid` 二选一 | 发票号码 |


### 调用时机

**仅当发票为交通类时调用**。判断条件（满足任一）：

- `expenseType` 包含"交通"、"出行"、"打车"、"出租车"
- `consumeContent` 包含"客运服务费"、"运输服务"
- `invoiceTypeCode` 为 17（行程单）或 57（客运凭证）等交通相关类型
- `sellerName` 包含"滴滴"、"享道"、"高德"、"曹操"等出行平台

### 返回值关键字段

从 `infos[].info` 中提取：


| 字段路径                                                  | 说明      | 示例                   |
| ----------------------------------------------------- | ------- | -------------------- |
| `from`                                                | 出发地     | `"仁济医院南院区门诊部(南门)南侧"` |
| `to`                                                  | 目的地     | `"浦江瑞和城柒街区30号"`      |
| `ext` (JSON字符串) → `passengersService[].from`          | 出发地（详细） | `"仁济医院南院区门诊部(南门)南侧"` |
| `ext` (JSON字符串) → `passengersService[].to`            | 目的地（详细） | `"浦江瑞和城柒街区30号"`      |
| `ext` (JSON字符串) → `passengersService[].transportType` | 交通方式    | `"出租车"`              |


> **优先取 `info.from` 和 `info.to`**（顶层字段），如为空则从 `ext.passengersService[0]` 中提取。

### 出发地/目的地精简规则

原始地址可能很长，需要精简后使用：


| 原始值                  | 精简后              |
| -------------------- | ---------------- |
| `"仁济医院南院区门诊部(南门)南侧"` | `"仁济医院南院"`       |
| `"浦江瑞和城柒街区30号"`      | `"浦江瑞和城"`        |
| `"上海虹桥国际机场T2航站楼出发层"` | `"虹桥机场T2"`       |
| `"北京南站"`             | `"北京南站"`（已够短，保留） |


精简原则：

- 去掉括号及括号内内容（如 `(南门)`）
- 去掉"侧"、"层"、"出发层"、"到达层"等方位后缀
- 去掉门牌号（如 `30号`、`3419号`）
- 保留核心地标名称，控制在 **10 个字以内**

### 返回示例（精简）

```json
{
  "infos": [
    {
      "info": {
        "id": "1301956959986835460",
        "from": "仁济医院南院区门诊部(南门)南侧",
        "to": "浦江瑞和城柒街区30号",
        "ext": "{...\"passengersService\":[{\"from\":\"仁济医院南院区门诊部(南门)南侧\",\"to\":\"浦江瑞和城柒街区30号\",\"transportType\":\"出租车\"}]...}"
      }
    }
  ]
}
```

---

## 6. 生成报销单流程

CLI operation：`invoice.reim.flow.create.prepare` → 用户确认 → `invoice.reim.flow.create.apply`

> **⚠️ 禁止重复创建：同一组发票数据只能创建一次。创建成功后，修改报销单请用 `invoice.reim.flow.update.prepare/apply`，不要再次调用 create。**

将填单结构化 JSON 作为 operation 顶层入参提交到 CLI，生成报销单流程。不要再包一层通用 `payload`。

### 入参

入参即 Step 4 组装的完整填单 JSON（结构定义见 [form-fill-rules.md](reim-form-fill-rules.md#最终输出结构)），字段会在 `inputSchema.properties` 中逐项暴露，并作为请求体（JSON Body）提交到 E10。


| 字段                  | 类型     | 必填  | 说明                               |
| ------------------- | ------ | --- | -------------------------------- |
| `work_flow_id`      | String | 是   | 目标报销流程的工作流ID                     |
| `mainFormId`        | String | 是   | 报销单主表formId（来自 `invoice.reim.form.structure`） |
| `request_name`      | String | 是   | 流程标题                             |
| `main_fields`       | Array  | 是   | 主表字段值列表                          |
| `detail_rows`       | Array  | 是   | 明细表行数据                           |
| `need_user_confirm` | Array  | 否   | 需用户确认的字段                         |
| `unable_to_fill`    | Array  | 否   | 无法自动填写的字段                        |


### 命令

将 Step 4 的 JSON 作为 operation 顶层输入写入文件，先 prepare，用户确认后再 apply。

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json invoice run invoice.reim.flow.create.prepare --input .\reim-create.json
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json invoice run invoice.reim.flow.create.prepare --input ./reim-create.json
```

顶层输入示例：

```json
{
  "work_flow_id": "1181057526276915214",
  "mainFormId": "1181057741029226975",
  "request_name": "交通费报销-后端开发111-2026-08-04（共1笔）",
  "main_fields": [
    {"fieldId": "1181057741029227445", "value": "1201729946891231232", "fieldName": "申请人"},
    {"fieldId": "1181057741029227447", "value": "2026-08-04", "fieldName": "报销日期"},
    {"fieldId": "1181057741029227454", "optionValue": "7", "fieldName": "报销方式"}
  ],
  "detail_rows": [
    {
      "dataIndex": 1,
      "subFormId": "1181057741029227992",
      "invoiceId": "1295366637717012482",
      "fields": [
        {"fieldId": "1181057741029227459", "value": "108.2", "fieldName": "实报金额"},
        {"fieldId": "1181057741029227467", "value": "2026-07-30", "fieldName": "费用日期"}
      ]
    }
  ],
  "need_user_confirm": [],
  "unable_to_fill": []
}
```

### 返回示例

```json
{
  "code": 200,
  "msg": "接口返回成功",
  "status": true,
  "data": {
    "requestId": "1300266422434136064"
  }
}
```

### 返回字段说明


| 字段               | 说明                   |
| ---------------- | -------------------- |
| `data.requestId` | 创建成功的报销单流程 requestId |


### 创建成功后

`invoice.reim.flow.create.apply` 返回 `requestId`、`requestName` 和 `viewUrl`。用 Markdown 链接展示给用户，锚文本用流程标题，链接用 CLI 返回的 `viewUrl`，不要自己拼接地址。

```markdown
报销单已创建成功！点击查看：[交通费报销-后端开发111-2026-08-04（共1笔）](viewUrl)
```

---

## 7. 更新报销单流程

CLI operation：`invoice.reim.flow.update.prepare` → 用户确认 → `invoice.reim.flow.update.apply`

更新已创建的报销流程表单。支持三种操作的任意组合，互不阻断：

- **修改主表字段** — 更新主表中的字段值
- **修改/新增明细行字段** — 更新或新增明细表中的行数据
- **删除指定明细行** — 按明细表ID + 行号删除

### 入参


| 字段                 | 类型          | 必填  | 说明                                            |
| ------------------ | ----------- | --- | --------------------------------------------- |
| `requestId`        | Long        | 是   | 要更新的流程 requestId（`invoice.reim.flow.create.apply` 返回的 requestId） |
| `mainFormId`       | String      | 是   | 报销单主表ID（来自 `invoice.reim.form.structure` 返回的 `mainFormId`） |
| `deleteDetailRows` | Array       | 否   | 要删除的明细行，见下方格式                                 |
| `main_fields`      | ArrayObject | 否   | 需要更新的主表字段列表                                   |
| `detail_rows`      | ArrayObject | 否   | 需要更新/新增的明细行数据                                 |


#### deleteDetailRows 格式

**推荐使用对象数组**（精确指定明细表）：

```json
"deleteDetailRows": [
  {"subFormId": "1169534588649275663", "dataIndex": 1},
  {"subFormId": "1169534588649275663", "dataIndex": 3}
]
```


| 字段          | 类型      | 说明                             |
| ----------- | ------- | ------------------------------ |
| `subFormId` | String  | 明细表ID，指定从哪个明细表删除               |
| `dataIndex` | Integer | 行号（1-based），传 `-1` 表示删除该明细表全部行 |


也支持**简写整数数组**（删除所有明细表中对应行）：`[1, 3]` 或 `[-1]`（删全部）

#### 字段对象（main_fields / detail_rows.fields 通用）


| 字段               | 类型      | 必填  | 说明                           |
| ---------------- | ------- | --- | ---------------------------- |
| `fieldId`        | String  | 是   | 字段ID                         |
| `fieldName`      | String  | 否   | 字段名称（便于理解，不参与逻辑）             |
| `value`          | String  | 否   | 字段值（与 optionValue 二选一）       |
| `optionValue`    | String  | 否   | 选项型字段的 optionId（与 value 二选一） |
| `unable_to_fill` | Boolean | 否   | `true` 表示该字段无法填写，跳过          |
| `need_search`    | Boolean | 否   | `true` 表示该字段需要搜索确认，跳过        |


#### detail_rows 行对象


| 字段          | 类型          | 必填  | 说明                |
| ----------- | ----------- | --- | ----------------- |
| `subFormId` | String      | 是   | 明细表ID，表示该行属于哪个明细表 |
| `dataIndex` | Long        | 是   | 明细行号（1-based），第几行 |
| `fields`    | ArrayObject | 是   | 该行中要更新的字段列表       |


### 执行顺序

> **删除操作先于表单更新执行，但删除失败不会阻断表单更新。**

### 命令

将以下 JSON 作为 operation 顶层输入写入文件，先 `invoice.reim.flow.update.prepare`，用户确认后再 `.apply`。

### 顶层输入示例

#### 场景1：同时删除明细第2行 + 修改主表 + 更新第1行明细

```json
{
  "requestId": 1300266422434136064,
  "mainFormId": "1169534588649275463",
  "deleteDetailRows": [
    {"subFormId": "1169534588649275663", "dataIndex": 2}
  ],
  "main_fields": [
    {"fieldId": "1169534588649275901", "fieldName": "申请日期", "value": "2026-08-05"}
  ],
  "detail_rows": [
    {
      "subFormId": "1169534588649275663",
      "dataIndex": 1,
      "fields": [
        {"fieldId": "1169534588649275988", "fieldName": "货物或应税劳务、服务名称", "value": "1297537820896575492"},
        {"fieldId": "1169534588649275989", "fieldName": "金额", "value": "500.00"}
      ]
    }
  ]
}
```

#### 场景2：仅删除某个明细表的第1行和第3行

```json
{
  "requestId": 1300266422434136064,
  "mainFormId": "1169534588649275463",
  "deleteDetailRows": [
    {"subFormId": "1169534588649275663", "dataIndex": 1},
    {"subFormId": "1169534588649275663", "dataIndex": 3}
  ]
}
```

#### 场景3：删除某个明细表全部行

```json
{
  "requestId": 1300266422434136064,
  "mainFormId": "1169534588649275463",
  "deleteDetailRows": [
    {"subFormId": "1169534588649275663", "dataIndex": -1}
  ]
}
```

#### 场景4：仅修改明细行

```json
{
  "requestId": 1300266422434136064,
  "mainFormId": "1169534588649275463",
  "detail_rows": [
    {
      "subFormId": "1169534588649275663",
      "dataIndex": 1,
      "fields": [
        {"fieldId": "1169534588649275988", "fieldName": "货物或应税劳务、服务名称", "value": "1297537820896575492"}
      ]
    }
  ]
}
```

### 返回示例

```json
{
  "code": 200,
  "status": true,
  "msg": "更新成功",
  "data": {
    "requestId": "1300266422434136064",
    "deleteDetailSuccess": true,
    "updateFormSuccess": true
  }
}
```

### 返回字段说明


| 字段                         | 说明                                        |
| -------------------------- | ----------------------------------------- |
| `data.requestId`           | 流程 requestId                              |
| `data.deleteDetailSuccess` | 明细行删除结果（仅当传了 deleteDetailRows 时返回）        |
| `data.deleteDetailMsg`     | 删除失败原因（仅失败时返回）                            |
| `data.updateFormSuccess`   | 表单更新结果（仅当有 main_fields 或 detail_rows 时返回） |
| `data.updateFormMsg`       | 更新失败原因（仅失败时返回）                            |


### 注意事项

- `mainFormId` 来自 `invoice.reim.form.structure` 返回的 `mainFormId`，每次调用 `invoice.reim.flow.update.prepare/apply` 必传
- `dataIndex` 是 **1-based**（从1开始），对应明细表中的第1行、第2行...
- `subFormId` 是明细表ID，一个流程表单可能有多个明细表，需准确指定
- 删除操作先于表单更新执行，删除失败不阻断表单更新
- `fieldName` 仅用于可读性，不参与业务逻辑
- 如果只删除不修改，只传 `requestId` + `deleteDetailRows` 即可
- `value` 为空、`unable_to_fill=true`、`need_search=true` 的字段会被自动跳过
