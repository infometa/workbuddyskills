# 发票浏览按钮字段数据

## 什么时候读取

用户要把业票通发票填入 E10 流程表单的发票浏览按钮控件，或要求"生成发票字段结构化数据""流程填单发票对象数据"时读取本文件。

## Operation

| Operation | 风险 | 输入 |
| --- | --- | --- |
| `invoice.browse-field.data` | read | `fid`、`fids` 或已取得的 `detail` 响应三选一 |

## 业务用途

E10 流程填单时，发票字段使用浏览按钮控件，填值必须传入包含完整票面信息的 JSON 对象，不能传简单文本。CLI 根据 `fid` 自动完成详情查询和 JSON 转换。

## 命令

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json invoice run invoice.browse-field.data --input-json '{"fid":"12345"}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json invoice run invoice.browse-field.data --input-json '{"fid":"12345"}'
```

多张发票：

Windows PowerShell：

```powershell
weaver-work-cli --profile eteams --json invoice run invoice.browse-field.data --input-json '{"fids":["12345","67890"]}'
```

macOS/Linux（bash/zsh）：

```bash
weaver-work-cli --profile eteams --json invoice run invoice.browse-field.data --input-json '{"fids":["12345","67890"]}'
```

## 目标 JSON 结构

下表定义每个发票对象的字段。`D` 代指发票详情响应中的 `infos[].info`。

| 键 | 类型 | 来源 | 说明 |
|---|---|---|---|
| `optionId` / `id` / `fid` | string | `D.fid` | 三者取相同值，发票唯一标识。 |
| `type` | integer | `D.comm_info.pro.type` | 票种编码。 |
| `typeName` | string | `D.comm_info.pro.cname`；缺失时按 `type` 查[票种名称表](#票种编码与名称) | 票种中文名称。 |
| `number` | string | `D.number` | 发票号码。 |
| `code` | string | `D.code` | 发票代码；无代码票种取空串。 |
| `content` / `name` | string | `"{typeName}-{number}"` 拼接 | 显示用摘要，两者取相同值。 |
| `total` | string | `D.comm_info.price.total` | 价税合计，单位元。 |
| `ttax` | string | `D.ext` → `ttax` | 票面税额。 |
| `seller` | string | `D.comm_info.payer.company` | 销售方名称。 |
| `sellerId` | string | `D.comm_info.payer.tcode` | 销售方税号。 |
| `buyer` | string | `D.comm_info.buyer.company` | 购买方名称。 |
| `buyerId` | string | `D.comm_info.buyer.tcode` | 购买方税号。 |
| `incDate` | string | `D.comm_info.pro.date` | 开票日期 `yyyy-MM-dd`。 |
| `incDateTimestamp` | integer | `incDate` 转 UTC+8 零时毫秒时间戳 | 空时取 `0`。 |
| `validStatus` | string | `D.comm_info.pro.valid` 查[查验状态表](#查验状态) | 查验状态文本。 |
| `source` | string | `D.modify_info.source` 查[录入来源表](#录入来源) | 录入来源文本。 |
| `invoiceStatus` | integer | `D.comm_info.pro.status` | 发票状态；`0` 正常。 |
| `del` | integer | `D.modify_info.del` | 删除状态；`0` 正常。 |
| `currency` / `currencyName` | string | `D.currency` / `D.currencyName` | 默认 `"CNY"` / `"人民币"`。 |
| `taxRate` | string | `D.ext` → `taxRate` 或 `products[0].taxRate` | 税率，如 `"13.000"`。 |
| `consumeContent` | string | `D.ext` → `products` 各项 `productName` 拼接 | 消费内容。 |
| `fylx` | string | `D.fylx` | 费用类型 ID；缺失取 `"0"`。 |
| `inputDate` | string | `D.modify_info.createDate` | 录入日期 `yyyy-MM-dd HH:mm:ss`。 |
| `incTotal` | integer | 固定 `0` | 预留字段。 |
| `reimingMoney` | string | `D.comm_info.price.reimingMoney` | 报销中金额；缺失取空串。 |
| `reimedMoney` | string | `D.comm_info.price.reimedMoney` | 已报销金额；缺失取空串。 |
| `notReimMoney` | string | `total - reimedMoney - reimingMoney` | 无报销数据时等于 `total`。 |
| `reimDate` | string | 报销日期 | 缺失取空串。 |
| `reimProcess` | string | 报销流程 ID | 缺失取空串。 |

缺失字段统一按类型填充：字符串用空串 `""`，数值用 `0`。

## 枚举映射表

### 票种编码与名称

优先使用详情响应中的 `cname`。仅当 `cname` 缺失时按以下表查找。

| `type` | `typeName` |
|---:|---|
| 1 | 增值税专用发票 |
| 2 | 增值税普通发票 |
| 3 | 增值税电子普通发票 |
| 4 | 卷式发票 |
| 5 | 通行费增值税电子普通发票 |
| 6 | 机动车销售统一发票 |
| 7 | 定额发票 |
| 8 | 客运汽车票 |
| 9 | 航空运输电子客票行程单 |
| 10 | 火车票 |
| 11 | 出租车票 |
| 12 | 其他 |
| 13 | 汽车通行费发票 |
| 14 | 船票 |
| 22 | 二手车销售统一发票 |
| 28 | 增值税电子专用发票 |
| 32 | 电子发票（增值税专用发票） |
| 33 | 电子发票（普通发票） |
| 47 | 医疗收费票据 |
| 48 | 财政非税收入统一票据 |
| 49 | 海关进口增值税专用缴款书 |
| 50 | 电子发票服务平台纸质普票 |
| 52 | 完税凭证 |
| 53 | 国际小票 |
| 54 | 银行回单 |
| 56 | 代扣代缴税收缴款凭证 |

未匹配的 `type` 使用 `"未知票种"`。

### 查验状态

| `valid` | `validStatus` |
|---:|---|
| 0 | 未查验 |
| 1 | 有效已查验 |
| 2 | 有效未查验 |
| 3 | 查验失败 |
| 4 | 发票无效 |
| 5 | 票面校验不一致 |

### 录入来源

| `source` | 文本 |
|---:|---|
| 1 | 微信 |
| 2 | 支付宝 |
| 4 | 邮箱 |
| 5 | 拍照 |
| 6 | 扫码 |
| 7 | 手动 |
| 9 | 查验录入 |
| 10 | 企业微信 |
| 11 | 公众号 |
| 12 | 企业台账 |
| 13 | 文件 |
| 14 | Excel |
| 15 | 短信 |
| 16 | 链接录入 |

未匹配的 `source` 使用空串。

## 输出示例

```json
{
  "optionId": "1307869223054704650",
  "id": "1307869223054704650",
  "fid": "1307869223054704650",
  "type": 32,
  "typeName": "电子发票（增值税专用发票）",
  "number": "26932000001429154341",
  "code": "",
  "content": "电子发票（增值税专用发票）-26932000001429154341",
  "name": "电子发票（增值税专用发票）-26932000001429154341",
  "total": "368269.14",
  "ttax": "42367.25",
  "seller": "宁波市北仑亮峰精密机械制造有限公司",
  "sellerId": "91330206744967935K",
  "buyer": "宁波海伯集团有限公司",
  "buyerId": "913302041443146316",
  "incDate": "2026-08-25",
  "incDateTimestamp": 1787587200000,
  "validStatus": "有效已查验",
  "source": "邮箱",
  "invoiceStatus": 0,
  "del": 0,
  "currency": "CNY",
  "currencyName": "人民币",
  "taxRate": "13.000",
  "consumeContent": "*金属制品*主齿轮",
  "fylx": "0",
  "inputDate": "2026-08-26 10:40:33",
  "incTotal": 0,
  "reimingMoney": "",
  "reimedMoney": "",
  "notReimMoney": "368269.14",
  "reimDate": "",
  "reimProcess": ""
}
```

## 输出处理

成功时 `data.items` 是浏览按钮可用对象数组。如果批量详情中有部分发票失败，operation 返回 `meta.status="PARTIAL"`，成功项仍在 `data.items`，失败项在 `data.errors`。Agent 回复用户时只展示成功数量、失败数量和关键发票字段；不要粘贴完整大 JSON。

## 边界与错误处理

- 详情查询固定 `mask=0`、`userFlag=1`、`isDelFlag=1`。
- `ext` 为 JSON 字符串，解析失败时 `ttax`、`taxRate`、`consumeContent` 取空串，不中断记录生成。
- 批量 fid 中部分查询失败时，成功项正常输出，失败项出现在 `errors` 数组中。

## 注意

该 operation 由 CLI 封装，Agent 只需调用 `invoice.browse-field.data` 或 `invoice.get`，不能直接 `curl` E10 接口，也不需要运行旧源码里的 Python 脚本。
