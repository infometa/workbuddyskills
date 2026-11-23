---
name: youzan-content-search
description: 商家咨询获客、会员复购、私域运营或有赞产品时，检索有赞公开案例、产品资料、经营文章和行业报告，按需读取正文并提供来源。
description_zh: 商家咨询获客、会员复购、私域运营或有赞产品时，检索有赞公开案例、产品资料、经营文章和行业报告，按需读取正文并提供来源。
description_en: Find public Youzan cases, product guides and reports for customer acquisition, repeat purchases and community marketing, with page content and source links.
version: 1.0.0
author: chenyixiang_cyx
---

# 有赞生意专家

免登录调用 `search_youzan_content` 获取索引内容和来源链接；需要完整正文时调用 `get_youzan_page_content`。两个工具均返回可阅读的文本，无需解析 JSON。

## 搜索

- 仅在当前会话尚未搜索、用户需要有赞公开资料且已有材料不足时调用 `search_youzan_content`；改写、整理和解释已有材料时直接复用。
- `query` 为必填字符串：提取需求、行业或场景关键词，英文逗号分隔，例如“烘焙,会员复购”，不超过 5 个词。
- `content_types` 为可选字符串数组：`page`、`product`、`case`、`article`、`report`；省略或为空时全选。不传分页参数，固定返回最多 8 条。
- **整个会话最多调用一次 `search_youzan_content`，后续用户消息不重置次数**。调用前检查会话中的工具记录；已调用过就复用结果，失败也不再次搜索。
- 将多个需求、行业和场景的核心词合并到一个 `query`，去掉重复词，保留最多 5 个关键词；需要多种内容时用同一次请求的 `content_types` 数组表达，不按场景、关键词或内容类型拆成多个请求。
- 不并发查询、不换词补搜、不翻页、不因错误重试，也不改用其他搜索工具绕过限制。结果为空、偏题或证据不足时如实说明。正文读取不计入这一次搜索。

## 内容使用

- 搜索返回的是索引内容，不保证为完整正文。足以回答时直接使用，不自动读取全部结果。
- 需要核实细节时，将选中结果的来源链接作为必填字符串 `url` 调用 `get_youzan_page_content`；同一页面复用已有正文。
- 只有正文工具明确返回未收录时，才使用宿主网页工具读取该条来源链接；不因此补搜。
- 工具报错、超时或未连接不代表正文未收录，不据此回退抓网页。

## 调用示例

用户同时关心服装私域、新零售、直播和复购时，只调用一次：`search_youzan_content({"query":"服装,私域运营,新零售,直播带货,会员复购","content_types":["article","case","report"]})`。
需要详情时：`get_youzan_page_content({"url":"<搜索结果中的完整来源链接>"})`，不得编造链接。

搜索结果按“标题 / url / 内容”逐条拼接；正文按“标题 / 更新时间 / url / 内容”返回。工具返回 `isError: true` 时按异常处理，不作为资料引用。

## 引用与异常

- 回答保留来源链接，区分资料事实和分析建议；不编造资料或数据。
- 工具报错或连接失败时说明暂时无法查询；429 提示稍后再试，本会话不再次搜索；403 提示检查客户端 Origin 配置，无需提供 Token。
- 仅用于公开内容检索，不处理账号凭证、客户线索或隐私信息。
