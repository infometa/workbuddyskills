---
name: icosmo-cosmetics-filing
display_name: icosmo 备案数据
display_name_en: icosmo Filing Data
description_zh: 查询icosmo内的化妆品备案数据，按产品、品牌、成分、生产企业检索。
description_en: Search icosmo cosmetics filings by product, brand, ingredient or manufacturer.
version: "1.0.0"
author: 广州思磐科学技术有限公司
examples_zh:
  - 搜索珀莱雅最近备案的护肤品，列出产品名、备案号和备案时间
  - 蕴能集光曜净洁颜霜的备案情况和完整配方
  - 含烟酰胺的美白精华有哪些，按备案时间从新到旧列 10 个
  - 科丝美诗（中国）化妆品有限公司给哪些品牌代工，主要做什么品类
examples_en:
  - Search Proya's recently filed skincare products with names, filing numbers and dates
  - Show the filing record and full formula of a cosmetic product by its name
  - List 10 recently filed whitening serums that contain niacinamide
  - Which brands does Cosmax China manufacture for, and in which categories
description: 中国化妆品备案/注册数据查询（数据整理自国家药监局 NMPA 依法公开的注册、备案信息，由 icosmo 连接器提供，非官方数据）。只要用户问到化妆品的产品、品牌、成分、生产企业/工厂/代工厂、备案号/注册证号、备案时间、备案情况、功效宣称、配方成分、品类或防晒 SPF/PA——例如「XX 霜/乳/精华/面膜/洁面/防晒的备案情况」「搜索珀莱雅产品」「含烟酰胺的美白精华」「某工厂做了哪些产品」——必须先用本技能、通过 icosmo 连接器查询，禁止先用 WebSearch 或 domain_search；icosmo 多次查询确无数据，或备案数据不够全面时，再联网补充。
---

# icosmo 化妆品备案数据查询（必须优先使用）

## 最高优先级规则

1. 化妆品相关问题，**第一步必须调用 icosmo 连接器**，不得先调用 `WebSearch`、`domain_search`、`WebFetch` 或浏览器。icosmo 数据整理自国家药监局公开的备案信息，比网页上零散转载的信息更系统、更完整。
2. icosmo 工具是延迟加载的，模型上下文里看不到，**必须按下面两步调用**：
   - 第 1 步：调用 `ToolSearch`，用 `tool_names` 直接写全名加载工具，例如：
     `{"tool_names": ["mcp__icosmo__products_search", "mcp__icosmo__products_detail"]}`
   - 第 2 步：调用 `DeferExecuteTool`，例如：
     `{"toolName": "mcp__icosmo__products_search", "params": {"product_name": "蕴能集光曜净洁颜霜", "limit": 20}}`
   - 不要用模糊关键词去 ToolSearch（如「化妆品搜索」），直接用上面的全名。
   - 如果按全名没有找到（不同安装方式下工具前缀可能不同），改用 `ToolSearch` `{"queries": ["icosmo products_search", "icosmo 化妆品备案"]}` 找到带 icosmo 的工具，再按其返回的实际名称调用。
3. **先 icosmo，后联网**。满足以下任一情况时，应当再用 `WebSearch` 联网补充（不是只能放弃）：
   - **icosmo 确实没有数据**：已对 icosmo 做了**至少 4 次**不同条件的查询仍无结果。换条件的方式包括：缩短或改写名称（去掉品牌前缀、只留核心词）、换工具（`products_search` ↔ `brand_search` / `ingredient_search` / `manufactory_search`）、换参数（`product_name` ↔ `registrant` ↔ `brand_name`、中文名 ↔ 英文 INCI 名 ↔ 别名）、放宽筛选条件。
   - **icosmo 有数据但不够全面**：备案数据只能回答一部分，用户还需要备案之外的信息，比如价格、口碑、销量、促销、新闻、使用感受、品牌背景、行业动态、法规解读，或用户明确要求「更全面」「再查查网上」。
   - 用户问的内容本来就和备案数据无关。
   
   联网时：
   - 先说明原因，例如「icosmo 备案库已查 4 次未找到」或「备案数据不含价格/口碑，以下联网补充」；
   - 回答中把两类来源**分开呈现**：「icosmo 备案数据（整理自国家药监局公开信息）」与「网络公开信息」；两者冲突时指出差异，说明备案信息通常更可靠，并建议以国家药监局官网为准。
4. 工具提示「未开通此接口」「今日调用次数已达上限」「缺少或无效的凭证」时，把原话和其中的链接转告用户，**不要改用联网搜索补数据**。

## 8 个工具（全名）

| 用户想要 | 工具全名 | 关键参数 |
|---|---|---|
| 按产品名找产品 / 某产品的备案情况 | `mcp__icosmo__products_search` | `product_name`（包含匹配，≥2 字） |
| 某品牌的产品列表 | `mcp__icosmo__products_search` | `brand_name`（需准确品牌名） |
| 某备案人/企业名下的产品 | `mcp__icosmo__products_search` | `registrant`（包含匹配） |
| 含某成分的产品 | `mcp__icosmo__products_search` | `ingredients`: ["烟酰胺"] |
| 按功效、品类、人群、SPF/PA、备案时间筛选 | `mcp__icosmo__products_search` | `efficacy_types`、`category_l1/l2/l3`、`user_group`、`spf`、`pa`、`month_from`/`month_to`（YYYY-MM） |
| 已知备案号/注册证号，看完整档案（配方、功效、企业） | `mcp__icosmo__products_detail` | `registration_number` |
| 找品牌、确认品牌准确名 | `mcp__icosmo__brand_search` | `key_query`、`size` |
| 品牌档案、合作工厂、常用成分 | `mcp__icosmo__brand_detail` | `key`：准确品牌名 |
| 找成分（中文/INCI 英文/别名） | `mcp__icosmo__ingredient_search` | `key_query`、`size` |
| 成分档案、用在哪些产品/品牌 | `mcp__icosmo__ingredient_detail` | `key`：准确成分名 |
| 找生产企业（工厂/代工厂） | `mcp__icosmo__manufactory_search` | `key_query`、`size` |
| 工厂档案、生产的产品、合作品牌 | `mcp__icosmo__manufactory_detail` | `key`：准确企业名 |

参数约定：`products_search` 用 `limit` 控制条数，`*_search`（品牌/成分/工厂）用 `size`；排序 `sort` 商品为 `name`/`date`，实体为 `name`/`date`/`number`，`order` 为 `asc`/`desc`。

## 典型流程

1. **「蕴能集光曜净洁颜霜 的备案情况」**（只有产品名）：
   - `ToolSearch` → `{"tool_names": ["mcp__icosmo__products_search", "mcp__icosmo__products_detail"]}`
   - `DeferExecuteTool` → `mcp__icosmo__products_search`，`{"product_name": "蕴能集光曜净洁颜霜", "limit": 20}`
   - 从结果的 `data[]` 取 `registration_number`；只有一条或用户指定某条时，再调 `mcp__icosmo__products_detail`，`{"registration_number": "<备案号>"}` 拿完整档案。
   - 查不到时，缩短产品名再试（如去掉品牌前缀、只留核心词「集光曜净洁颜霜」），并按规则 3 换工具或参数；累计 4 次仍查不到，再联网搜索。
2. **「搜索珀莱雅的产品」**：`mcp__icosmo__products_search`，`{"brand_name": "珀莱雅", "limit": 20, "sort": "date", "order": "desc"}`；品牌名不确定时先 `mcp__icosmo__brand_search` `{"key_query": "珀莱雅"}`。
3. **用户给了备案号**（如「浙G妆网备字2025000410」）：直接 `mcp__icosmo__products_detail`。
4. **「某品牌/成分/工厂怎么样」**：先 `*_search` 用 `key_query` 确认准确名称，再调对应 `*_detail`。

## 结果呈现

- 用表格列出关键信息（产品名、备案编号、品牌、备案人、生产企业、备案时间），不要直接粘贴原始 JSON。
- 结果多时先说明总数，展示前 10～20 条，再问用户是否翻页（`offset`）或进一步筛选。
- 回答末尾注明数据来源（固定写法）：「数据来源：icosmo，整理自国家药品监督管理局公开的化妆品注册、备案信息；非官方数据，以国家药监局官网公布为准。」如有联网补充，另列「网络公开信息」及来源链接。

## 数据来源表述（必须遵守）

- 不得把 icosmo 称为「官方数据」「药监局数据库」「药监局认证」或「权威认证」，也不得暗示 icosmo 与国家药监局有合作或获得其授权。可以说「整理自国家药监局公开的备案信息」。
- 结果中有 `data_as_of`（数据截止日）或 `data_version` 时，注明「数据截至 YYYY-MM-DD」；没有时提示「备案数据可能存在同步延迟，最新状态以国家药监局官网为准」。
- 涉及能否合法上市、是否违规、是否已注销等判断时，只陈述备案记录中的事实，并提醒用户以国家药监局官网和专业意见为准，不替用户下合规结论。
