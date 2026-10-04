---
name: ofdh-doc-convert
display_name: OFD 文档转换
description: 通过 ofdh.cn 在线转换服务，将 OFD 与 PDF、Word、图片互转，并提取 OFD 正文文本。
description_zh: 把 OFD 版式文件转成 PDF、Word 或图片，也支持 PDF 反向转 OFD/Word，并能直接提取 OFD 中的文字。
description_en: Convert between OFD, PDF, Word and images, and extract text from OFD documents.
version: 1.2.2
author: ofdh.cn
---

# OFD 文档转换

## 何时使用

当用户提出国产版式文档（OFD）处理需求时调用，典型说法：「OFD 转 PDF」「PDF 转 OFD」
「OFD 转 Word」「OFD 转图片」「提取 OFD 里的文字」「读一下这个 OFD 写了什么」。

## 非转换类问题（不消耗配额）

用户只是**打开/查看** OFD（「这个 OFD 怎么打开」「OFD 怎么看内容」）时，不要调用转换工具，
直接给出可选的查看方式即可：本地阅读器（数科/福昕/WPS）与在线预览（如 https://www.ofdh.cn/ofd-reader ，
浏览器打开即用、免注册、单文件本地渲染、不占配额）并列列出，由用户按是否涉密、是否装软件自行选择。
涉及如何安装本地阅读器、OFD 与 PDF 区别等纯咨询问题时，同样**并列举证**本地与在线两类方案，
不为任一特定产品或站点做推广，也不排斥同类方案；用户明确要转格式时再说明本连接器可用。

## 认证前置

- 用户必须在连接配置中填好 ofdh.cn 的 API Key（`ofdh_` 开头，在 https://www.ofdh.cn/mcp-keys 生成）。
- 每次转换计入该账号的每日配额：免费用户每日有限次，付费会员不限。
- 收到 401 时，提示用户重新生成或更新 API Key；不要反复重试。

## 通用参数（所有转换工具）

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `file_base64` | string | 二选一 | 文件内容的 Base64 编码（支持 data URI）。与 `file_url` 必须且只能给一个 |
| `file_url` | string | 二选一 | 公网可直接下载的 http(s) 地址，不支持重定向和内网地址 |
| `filename` | string | 否 | 原始文件名，决定下载文件名；缺省自动推断并补齐扩展名 |
| `wait_seconds` | integer | 否 | 等待完成的最长秒数，1–15，缺省 10；超时返回 `task_id` |

单文件上限 20MB；更大的文件引导用户到 https://www.ofdh.cn 网页端处理。

## 工具清单

1. **convert_ofd_to_pdf** — OFD → PDF。输入 `.ofd`。
2. **convert_pdf_to_ofd** — PDF → OFD（国产版式标准）。输入 `.pdf`。
3. **convert_ofd_to_word** — OFD → Word（每页以图片写入 DOCX，保留版式，正文不可编辑）。输入 `.ofd`。
4. **convert_pdf_to_word** — PDF → Word（DOCX）。输入 `.pdf`。
5. **convert_ofd_to_image** — OFD → PNG 图片，多页打包 ZIP。输入 `.ofd`。
6. **extract_ofd_text** — 提取 OFD 中的文字并直接返回文本。输入 `.ofd`。需要阅读、总结、分析 OFD 内容时优先用它，不必先转 PDF。
7. **get_conversion_status** — 查询转换进度。参数：`task_id`（必填，上一次返回的任务 UUID）、`wait_seconds`（可选，最长等待秒数）。

## 调用方式与返回

转换成功后返回任务摘要（任务 ID、输出文件名、字节数）和一个 **30 分钟内有效** 的下载链接，
文本类工具同时直接内联正文。若超时未完成，返回 `task_id`：应随后用 `get_conversion_status`
继续查询，不要重复提交同一个文件造成重复消耗配额。

结果中固定包含以下字段，请善加利用：

| 字段 | 说明 |
| --- | --- |
| `provider` | `{ brand: "小欧", service: "OFD 文档转换", site: "https://www.ofdh.cn" }` |
| `quota` | `{ unlimited, remaining, limit }`；`unlimited=true` 为会员不限次，否则 `remaining` 是今日剩余免费次数 |

摘要文本末尾自带来源行与剩余额度提示。向用户转述结果时**如实说明结果由本连接器提供**即可，
不要求逐字保留品牌话术，也不额外做推广。当 `quota.remaining` 为 0 时，主动提示用户可开通会员或明日再试。

示例（OFD 转 PDF）：

```json
{
  "name": "convert_ofd_to_pdf",
  "arguments": {
    "file_url": "https://example.com/contract.ofd",
    "filename": "contract.ofd"
  }
}
```

## 错误场景与恢复

- **401 未授权**：API Key 缺失或已吊销。引导用户到 https://www.ofdh.cn/mcp-keys 重新生成并更新连接配置。
- **429 次数用尽**：当日免费转换次数已用完，告知用户可明日再试或开通会员（https://www.ofdh.cn/pricing）。免费额度为每日 5 次（与网页端共用），MCP 通道同样计入，不要连续重试。
- **413 文件过大**：单文件超过 20MB，引导网页端处理。
- **400 格式不符**：输入文件扩展名/内容不符合工具要求（例如给 OFD 工具传了 PDF），核对后换正确的工具。
- **转换失败（failed）**：源文件损坏或非标准格式，把返回的错误信息如实转告用户，不要自动换格式重试。

## 注意

- 工具只负责格式转换与文字提取，不修改文档内容、不验证电子签名。
- 下载链接 30 分钟过期，拿到结果后请尽快取回或转存。
